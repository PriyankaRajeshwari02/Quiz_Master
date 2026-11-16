"""Import syllabus JSON files (data/syllabus/semN.json) into the database.

Safe to run many times: existing questions are skipped, new ones are added,
subject/module titles are refreshed. Bad questions are rejected with a clear
message instead of crashing the whole import.
"""

import glob
import json
import os

from app.database import BASE_DIR, get_connection, init_db

SYLLABUS_DIR = os.path.join(BASE_DIR, "data", "syllabus")
RECOMMENDED_MIN = 30   # fewer questions than this -> warning
LETTERS = ["A", "B", "C", "D"]


class ImportDataError(Exception):
    """The file itself is unusable (bad JSON, missing semester, ...)."""


def validate_question(q):
    """Return an error string, or None if the question is fine."""
    if not isinstance(q, dict):
        return "question is not an object"
    if not str(q.get("q", "")).strip():
        return "question text is empty"
    options = q.get("options")
    if not isinstance(options, list) or len(options) != 4:
        return "needs exactly 4 options"
    if any(not str(o).strip() for o in options):
        return "an option is empty"
    if len({str(o).strip().lower() for o in options}) != 4:
        return "two options are identical"
    if q.get("answer") not in LETTERS:
        return "answer must be one of A, B, C, D"
    if not str(q.get("explanation", "")).strip():
        return "explanation is missing (it is compulsory)"
    return None


def import_file(path, db_path=None):
    """Import one JSON file. Returns a report dict."""
    report = {"file": os.path.basename(path), "added": 0, "skipped": 0,
              "errors": [], "warnings": []}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise ImportDataError(f"{report['file']}: cannot read file ({error})") from error

    semester = data.get("semester")
    if semester not in range(1, 9):
        raise ImportDataError(f"{report['file']}: 'semester' must be 1 to 8")

    init_db(db_path)
    with get_connection(db_path) as connection:
        for subject in data.get("subjects", []):
            code, name = subject.get("code"), subject.get("name")
            if not code or not name:
                report["errors"].append("a subject is missing code or name")
                continue

            row = connection.execute(
                "SELECT subject_id FROM subjects WHERE code = ?", (code,)).fetchone()
            if row:
                subject_id = row["subject_id"]
                connection.execute(
                    "UPDATE subjects SET name = ?, semester_id = ? WHERE subject_id = ?",
                    (name, semester, subject_id))
            else:
                subject_id = connection.execute(
                    "INSERT INTO subjects (semester_id, code, name) VALUES (?, ?, ?)",
                    (semester, code, name)).lastrowid

            for module in subject.get("modules", []):
                number, title = module.get("number"), module.get("title")
                if not isinstance(number, int) or not title:
                    report["errors"].append(f"{code}: a module is missing number or title")
                    continue

                row = connection.execute(
                    "SELECT module_id FROM modules WHERE subject_id = ? AND module_number = ?",
                    (subject_id, number)).fetchone()
                if row:
                    module_id = row["module_id"]
                    connection.execute(
                        "UPDATE modules SET title = ? WHERE module_id = ?", (title, module_id))
                else:
                    module_id = connection.execute(
                        "INSERT INTO modules (subject_id, module_number, title) VALUES (?, ?, ?)",
                        (subject_id, number, title)).lastrowid

                for index, q in enumerate(module.get("questions", []), start=1):
                    problem = validate_question(q)
                    if problem:
                        report["errors"].append(
                            f"{code} module {number}, question {index}: {problem}")
                        continue
                    a, b, c, d = (str(o).strip() for o in q["options"])
                    cursor = connection.execute(
                        """INSERT OR IGNORE INTO questions
                           (module_id, question, option_a, option_b, option_c, option_d,
                            correct_answer, explanation)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (module_id, q["q"].strip(), a, b, c, d,
                         q["answer"], q["explanation"].strip()))
                    if cursor.rowcount:
                        report["added"] += 1
                    else:
                        report["skipped"] += 1

                total = connection.execute(
                    "SELECT COUNT(*) AS n FROM questions WHERE module_id = ?",
                    (module_id,)).fetchone()["n"]
                if 0 < total < RECOMMENDED_MIN:
                    report["warnings"].append(
                        f"{code} module {number}: only {total} questions "
                        f"(recommended {RECOMMENDED_MIN}+)")
    return report


def import_all(db_path=None, directory=SYLLABUS_DIR):
    """Import every semN.json file in the syllabus folder."""
    reports = []
    for path in sorted(glob.glob(os.path.join(directory, "sem*.json"))):
        try:
            reports.append(import_file(path, db_path))
        except ImportDataError as error:
            reports.append({"file": os.path.basename(path), "added": 0, "skipped": 0,
                            "errors": [str(error)], "warnings": []})
    return reports


if __name__ == "__main__":
    # Run from the project folder:  python -m app.importer
    for report in import_all():
        print(f"{report['file']}: {report['added']} added, {report['skipped']} already present")
        for line in report["errors"]:
            print("  ERROR  :", line)
        for line in report["warnings"]:
            print("  WARNING:", line)