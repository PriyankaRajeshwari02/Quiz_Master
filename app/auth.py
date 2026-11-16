"""Authentication for QuizMaster: signup, login, roles.

Passwords are never stored. We store a salted PBKDF2 hash instead.
Students sign up from the app; an admin can only be created with
`python -m app.auth` (so nobody can make themselves admin from the UI).
"""

import getpass
import hashlib
import hmac
import os
import re
import sqlite3
from datetime import datetime

from app.database import get_connection, init_db

ITERATIONS = 200_000
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.]{3,20}$")
MIN_PASSWORD_LENGTH = 6


class AuthError(Exception):
    """Raised for any signup/login problem; the message is safe to show."""


def hash_password(password, salt_hex=None):
    """Return (hash_hex, salt_hex). A new random salt is made if none given."""
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return digest.hex(), salt.hex()


def _create_user(username, full_name, password, role, db_path):
    username = (username or "").strip().lower()
    full_name = (full_name or "").strip()

    if not USERNAME_PATTERN.match(username):
        raise AuthError("Username must be 3-20 characters: letters, numbers, _ or .")
    if not full_name:
        raise AuthError("Please enter your full name.")
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")

    password_hash, salt = hash_password(password)
    try:
        with get_connection(db_path) as connection:
            connection.execute(
                """INSERT INTO users
                   (username, full_name, password_hash, salt, role, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (username, full_name, password_hash, salt, role,
                 datetime.now().isoformat(timespec="seconds")),
            )
    except sqlite3.IntegrityError:
        raise AuthError("That username is already taken.") from None


def register_student(username, full_name, password, db_path=None):
    """Public signup. The role is ALWAYS 'student'."""
    _create_user(username, full_name, password, "student", db_path)


def create_admin(username, full_name, password, db_path=None):
    """Only called from the command line, never from a UI screen."""
    _create_user(username, full_name, password, "admin", db_path)


def login(username, password, db_path=None):
    """Return the user as a dict, or raise AuthError."""
    username = (username or "").strip().lower()
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

    # Same message for "no such user" and "wrong password" on purpose.
    if row is None:
        raise AuthError("Invalid username or password.")
    attempt_hash, _ = hash_password(password or "", row["salt"])
    if not hmac.compare_digest(attempt_hash, row["password_hash"]):
        raise AuthError("Invalid username or password.")

    return {
        "user_id": row["user_id"],
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
    }


def require_admin(user):
    """Call at the top of every admin function (not just hiding buttons)."""
    if not user or user.get("role") != "admin":
        raise PermissionError("Admin access required.")


def admin_exists(db_path=None):
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS n FROM users WHERE role = 'admin'"
        ).fetchone()
    return row["n"] > 0


if __name__ == "__main__":
    # Run from the project folder:  python -m app.auth
    init_db()
    print("Create an admin account")
    name = input("Full name: ")
    user = input("Username: ")
    pwd = getpass.getpass("Password: ")
    try:
        create_admin(user, name, pwd)
        print("Admin created.")
    except AuthError as error:
        print("Could not create admin:", error)