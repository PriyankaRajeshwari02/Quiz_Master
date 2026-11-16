"""Database layer for QuizMaster.

Holds the schema, a safe connection helper and the read queries used by the
student screens. Writing questions is done by importer.py; users by auth.py.
"""

import os
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "quizmaster.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    full_name     TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'student'
                  CHECK (role IN ('student', 'admin')),
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS semesters (
    semester_id INTEGER PRIMARY KEY CHECK (semester_id BETWEEN 1 AND 8),
    name        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_id INTEGER NOT NULL REFERENCES semesters(semester_id),
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS modules (
    module_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id    INTEGER NOT NULL REFERENCES subjects(subject_id),
    module_number INTEGER NOT NULL,
    title         TEXT NOT NULL,
    UNIQUE (subject_id, module_number)
);

CREATE TABLE IF NOT EXISTS questions (
    question_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id      INTEGER NOT NULL REFERENCES modules(module_id),
    question       TEXT NOT NULL,
    option_a       TEXT NOT NULL,
    option_b       TEXT NOT NULL,
    option_c       TEXT NOT NULL,
    option_d       TEXT NOT NULL,
    correct_answer TEXT NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
    explanation    TEXT NOT NULL CHECK (length(trim(explanation)) > 0),
    UNIQUE (module_id, question)
);

CREATE TABLE IF NOT EXISTS attempts (
    attempt_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(user_id),
    module_id   INTEGER NOT NULL REFERENCES modules(module_id),
    test_number INTEGER NOT NULL CHECK (test_number BETWEEN 1 AND 10),
    score       INTEGER NOT NULL,
    total       INTEGER NOT NULL,
    percentage  REAL NOT NULL,
    taken_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempt_answers (
    attempt_id      INTEGER NOT NULL REFERENCES attempts(attempt_id),
    question_id     INTEGER NOT NULL REFERENCES questions(question_id),
    selected_option TEXT NOT NULL,
    is_correct      INTEGER NOT NULL,
    PRIMARY KEY (attempt_id, question_id)
);
"""


@contextmanager
def get_connection(db_path=None):
    """Open a connection, commit on success, roll back on error, ALWAYS close.

    (sqlite3's own `with connection:` does not close the connection, which
    is why we use this helper instead.)
    """
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")  # OFF by default in SQLite
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db(db_path=None):
    """Create all tables and the 8 semester rows. Safe to call every launch."""
    with get_connection(db_path) as connection:
        connection.executescript(SCHEMA)
        for number in range(1, 9):
            connection.execute(
                "INSERT OR IGNORE INTO semesters (semester_id, name) VALUES (?, ?)",
                (number, f"Semester {number}"),
            )


# ---------- read queries used by the student screens ----------

def get_semesters(db_path=None):
    """All 8 semesters with how many questions each one has (0 = coming soon)."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT s.semester_id, s.name, COUNT(q.question_id) AS question_count
            FROM semesters s
            LEFT JOIN subjects sub ON sub.semester_id = s.semester_id
            LEFT JOIN modules m ON m.subject_id = sub.subject_id
            LEFT JOIN questions q ON q.module_id = m.module_id
            GROUP BY s.semester_id
            ORDER BY s.semester_id
            """
        ).fetchall()


def get_subjects(semester_id, db_path=None):
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT sub.subject_id, sub.code, sub.name,
                   COUNT(q.question_id) AS question_count
            FROM subjects sub
            LEFT JOIN modules m ON m.subject_id = sub.subject_id
            LEFT JOIN questions q ON q.module_id = m.module_id
            WHERE sub.semester_id = ?
            GROUP BY sub.subject_id
            ORDER BY sub.code
            """,
            (semester_id,),
        ).fetchall()


def get_modules(subject_id, db_path=None):
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT m.module_id, m.module_number, m.title,
                   COUNT(q.question_id) AS question_count
            FROM modules m
            LEFT JOIN questions q ON q.module_id = m.module_id
            WHERE m.subject_id = ?
            GROUP BY m.module_id
            ORDER BY m.module_number
            """,
            (subject_id,),
        ).fetchall()


def get_module_questions(module_id, db_path=None):
    """The module's full question pool, in a fixed order (by question_id)."""
    with get_connection(db_path) as connection:
        return connection.execute(
            "SELECT * FROM questions WHERE module_id = ? ORDER BY question_id",
            (module_id,),
        ).fetchall()