"""Saving and reading test attempts (used by Result, Test list, My Progress)."""

from datetime import datetime

from app.database import get_connection
from app.quiz import QuizError, QuizSession


def save_attempt(user_id, module_id, test_number, session, db_path=None):
    """Store a finished quiz and every answer. Returns the new attempt_id."""
    if not isinstance(session, QuizSession) or not session.is_finished:
        raise QuizError("Answer every question before submitting.")

    with get_connection(db_path) as connection:
        attempt_id = connection.execute(
            """INSERT INTO attempts
               (user_id, module_id, test_number, score, total, percentage, taken_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, module_id, test_number, session.score, session.total,
             session.percentage, datetime.now().isoformat(timespec="seconds")),
        ).lastrowid
        correct = {q["question_id"]: q["correct_answer"] for q in session.questions}
        connection.executemany(
            """INSERT INTO attempt_answers
               (attempt_id, question_id, selected_option, is_correct)
               VALUES (?, ?, ?, ?)""",
            [(attempt_id, question_id, letter, int(letter == correct[question_id]))
             for question_id, letter in session.answers.items()],
        )
    return attempt_id


def get_test_status(user_id, module_id, db_path=None):
    """For the Test list screen: {test_number: {'attempts': n, 'best': pct}}.

    Tests never attempted are simply missing from the dict.
    """
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """SELECT test_number, COUNT(*) AS attempts, MAX(percentage) AS best
               FROM attempts WHERE user_id = ? AND module_id = ?
               GROUP BY test_number""",
            (user_id, module_id),
        ).fetchall()
    return {r["test_number"]: {"attempts": r["attempts"], "best": r["best"]}
            for r in rows}


def get_user_attempts(user_id, db_path=None):
    """For My Progress: newest attempt first, with subject and module names."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """SELECT a.attempt_id, a.test_number, a.score, a.total,
                      a.percentage, a.taken_at,
                      m.module_number, m.title AS module_title,
                      s.code AS subject_code, s.name AS subject_name
               FROM attempts a
               JOIN modules m ON m.module_id = a.module_id
               JOIN subjects s ON s.subject_id = m.subject_id
               WHERE a.user_id = ?
               ORDER BY a.attempt_id DESC""",
            (user_id,),
        ).fetchall()


def get_attempt_review(attempt_id, user_id, db_path=None):
    """Re-open the review of an old attempt. Only the owner can see it."""
    with get_connection(db_path) as connection:
        owner = connection.execute(
            "SELECT user_id FROM attempts WHERE attempt_id = ?", (attempt_id,)
        ).fetchone()
        if owner is None or owner["user_id"] != user_id:
            raise PermissionError("You can only view your own attempts.")
        rows = connection.execute(
            """SELECT q.question, q.option_a, q.option_b, q.option_c, q.option_d,
                      q.correct_answer, q.explanation,
                      aa.selected_option, aa.is_correct
               FROM attempt_answers aa
               JOIN questions q ON q.question_id = aa.question_id
               WHERE aa.attempt_id = ?
               ORDER BY q.question_id""",
            (attempt_id,),
        ).fetchall()

    return [{
        "number": number,
        "question": r["question"],
        "options": {"A": r["option_a"], "B": r["option_b"],
                    "C": r["option_c"], "D": r["option_d"]},
        "selected": r["selected_option"],
        "correct": r["correct_answer"],
        "is_correct": bool(r["is_correct"]),
        "explanation": r["explanation"],
    } for number, r in enumerate(rows, start=1)]