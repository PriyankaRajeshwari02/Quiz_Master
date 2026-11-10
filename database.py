"""SQLite storage for QuizMaster.

This module creates the local database, inserts sample questions once,
fetches questions for a category, and saves each completed quiz result.
"""

import os
import sqlite3
from datetime import datetime


# Store the database file next to this script, not in the current folder.
# That way the app still finds questions.db if it is started from another path.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "questions.db")

CATEGORIES = [
    "Python Programming",
    "Database Management System (DBMS)",
    "Computer Networks",
]

# Each tuple is one sample question:
# category, question, option_a, option_b, option_c, option_d, correct_answer
SAMPLE_QUESTIONS = [
    (
        "Python Programming",
        "Which keyword is used to define a function in Python?",
        "func",
        "define",
        "def",
        "function",
        "C",
    ),
    (
        "Python Programming",
        "What is the data type of the value 3.14 in Python 3?",
        "int",
        "float",
        "double",
        "char",
        "B",
    ),
    (
        "Python Programming",
        "Which of the following is a mutable data type?",
        "tuple",
        "str",
        "list",
        "int",
        "C",
    ),
    (
        "Python Programming",
        "What does len() return when it is called on a list?",
        "The last item",
        "The number of items",
        "The memory address",
        "The first item",
        "B",
    ),
    (
        "Python Programming",
        "Which symbol starts a single-line comment in Python?",
        "//",
        "/*",
        "#",
        "--",
        "C",
    ),
    (
        "Python Programming",
        "Which collection stores data as key-value pairs?",
        "list",
        "tuple",
        "set",
        "dict",
        "D",
    ),
    (
        "Python Programming",
        "What is the result of the expression 10 // 3 in Python 3?",
        "3.33",
        "3",
        "4",
        "1",
        "B",
    ),
    (
        "Python Programming",
        "Which statement is used to handle runtime errors?",
        "try and except",
        "if and else",
        "for and else",
        "switch and case",
        "A",
    ),
    (
        "Python Programming",
        "Which list method adds one item at the end of a list?",
        "add()",
        "push()",
        "append()",
        "insert()",
        "C",
    ),
    (
        "Python Programming",
        "Which statement about Python is correct?",
        "Every variable must be declared with a type",
        "Python is an interpreted language",
        "Code blocks are written inside curly braces",
        "Indentation is optional",
        "B",
    ),
    (
        "Database Management System (DBMS)",
        "What does SQL stand for?",
        "Structured Query Language",
        "Simple Query Language",
        "Sequential Query Language",
        "Standard Question Language",
        "A",
    ),
    (
        "Database Management System (DBMS)",
        "Which key uniquely identifies each row in a table?",
        "Foreign key",
        "Primary key",
        "Alternate key",
        "Composite attribute",
        "B",
    ),
    (
        "Database Management System (DBMS)",
        "Which command removes a table definition from the database?",
        "DELETE TABLE",
        "REMOVE TABLE",
        "DROP TABLE",
        "ERASE TABLE",
        "C",
    ),
    (
        "Database Management System (DBMS)",
        "A foreign key is used to:",
        "Encrypt the values in a column",
        "Refer to the primary key of another table",
        "Sort all rows automatically",
        "Store only numeric data",
        "B",
    ),
    (
        "Database Management System (DBMS)",
        "Which of the following is a DDL command?",
        "INSERT",
        "UPDATE",
        "CREATE",
        "SELECT",
        "C",
    ),
    (
        "Database Management System (DBMS)",
        "What is the main purpose of normalization?",
        "Increase repeated data",
        "Reduce redundancy and improve consistency",
        "Remove all keys from a table",
        "Store every column in one table",
        "B",
    ),
    (
        "Database Management System (DBMS)",
        "Which join returns only the rows that match in both tables?",
        "INNER JOIN",
        "CROSS JOIN",
        "FULL OUTER JOIN",
        "NATURAL UNION",
        "A",
    ),
    (
        "Database Management System (DBMS)",
        "What does COMMIT do in a transaction?",
        "Undoes the current transaction",
        "Permanently saves the current transaction",
        "Deletes the database file",
        "Grants a user permission",
        "B",
    ),
    (
        "Database Management System (DBMS)",
        "Which constraint rejects a missing value in a column?",
        "DEFAULT",
        "NOT NULL",
        "CHECK",
        "INDEX",
        "B",
    ),
    (
        "Database Management System (DBMS)",
        "A candidate key is best described as:",
        "An attribute, or set of attributes, that can uniquely identify a row",
        "A key copied from another database product",
        "A key that always allows duplicate values",
        "A temporary name of a view",
        "A",
    ),
    (
        "Computer Networks",
        "How many layers are there in the OSI model?",
        "4",
        "5",
        "6",
        "7",
        "D",
    ),
    (
        "Computer Networks",
        "IP addressing belongs to which OSI layer?",
        "Physical",
        "Data Link",
        "Network",
        "Session",
        "C",
    ),
    (
        "Computer Networks",
        "Which protocol is connection-oriented and reliable?",
        "UDP",
        "IP",
        "TCP",
        "ICMP",
        "C",
    ),
    (
        "Computer Networks",
        "What is the default port number of HTTP?",
        "21",
        "22",
        "25",
        "80",
        "D",
    ),
    (
        "Computer Networks",
        "What is the main job of DNS?",
        "Translate domain names to IP addresses",
        "Encrypt email messages",
        "Assign MAC addresses",
        "Compress transferred files",
        "A",
    ),
    (
        "Computer Networks",
        "Which device forwards frames using MAC addresses?",
        "Hub",
        "Switch",
        "Repeater",
        "Modem",
        "B",
    ),
    (
        "Computer Networks",
        "UDP is best described as:",
        "Connectionless and without delivery guarantee",
        "Connection-oriented and reliable",
        "A routing protocol",
        "An email protocol",
        "A",
    ),
    (
        "Computer Networks",
        "SMTP is primarily used for:",
        "Transferring files",
        "Sending email",
        "Web browsing",
        "Resolving host names",
        "B",
    ),
    (
        "Computer Networks",
        "A subnet mask is used to:",
        "Separate the network and host parts of an IP address",
        "Encrypt every packet",
        "Replace the MAC address",
        "Store web pages",
        "A",
    ),
    (
        "Computer Networks",
        "Which OSI layer provides end-to-end communication between processes?",
        "Network",
        "Transport",
        "Data Link",
        "Physical",
        "B",
    ),
]


class DatabaseError(Exception):
    """Raised when the database cannot be created or updated."""


class Database:
    """Creates tables and runs the SQL used by the quiz screens."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._create_tables()
        self._seed_questions()

    def _connect(self):
        """Open a connection. Callers should use it as a context manager."""
        try:
            connection = sqlite3.connect(self.db_path)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not open the database: {exc}") from exc
        connection.row_factory = sqlite3.Row
        return connection

    def _create_tables(self):
        """Create the questions and results tables if they do not exist."""
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS questions (
                        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        question TEXT NOT NULL,
                        option_a TEXT NOT NULL,
                        option_b TEXT NOT NULL,
                        option_c TEXT NOT NULL,
                        option_d TEXT NOT NULL,
                        correct_answer TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS results (
                        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        category TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        total_questions INTEGER NOT NULL,
                        percentage REAL NOT NULL,
                        quiz_date TEXT NOT NULL
                    )
                    """
                )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not create the tables: {exc}") from exc

    def _seed_questions(self):
        """Insert sample questions only when the questions table is empty.

        Checking the row count prevents duplicate questions on every startup.
        """
        self._validate_sample_questions()
        try:
            with self._connect() as connection:
                row = connection.execute("SELECT COUNT(*) AS total FROM questions").fetchone()
                if row["total"] > 0:
                    return

                connection.executemany(
                    """
                    INSERT INTO questions (
                        category, question, option_a, option_b,
                        option_c, option_d, correct_answer
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    SAMPLE_QUESTIONS,
                )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not insert sample questions: {exc}") from exc

    def _validate_sample_questions(self):
        """Stop early if a sample question was typed incorrectly."""
        for item in SAMPLE_QUESTIONS:
            category = item[0]
            answer = item[6]
            if category not in CATEGORIES:
                raise DatabaseError(f"Unknown sample category: {category}")
            if answer not in ("A", "B", "C", "D"):
                raise DatabaseError("Sample answers must be A, B, C, or D.")

    def get_questions(self, category):
        """Return every question for one category, in insertion order."""
        if category not in CATEGORIES:
            raise DatabaseError("Please select a valid category.")
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT question_id, category, question,
                           option_a, option_b, option_c, option_d,
                           correct_answer
                    FROM questions
                    WHERE category = ?
                    ORDER BY question_id
                    """,
                    (category,),
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not load questions: {exc}") from exc
        return [dict(row) for row in rows]

    def save_result(self, username, category, score, total_questions, percentage):
        """Store one completed attempt and return its new result id."""
        quiz_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO results (
                        username, category, score, total_questions,
                        percentage, quiz_date
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (username, category, score, total_questions, percentage, quiz_date),
                )
                return cursor.lastrowid
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not save the result: {exc}") from exc

    def count_questions(self):
        """Return the number of stored questions. Useful for checking setup."""
        try:
            with self._connect() as connection:
                row = connection.execute("SELECT COUNT(*) AS total FROM questions").fetchone()
                return row["total"]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not count questions: {exc}") from exc
