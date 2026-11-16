import os
import tempfile
import unittest

from app import auth, importer
from app.database import get_connection, init_db


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "test.db")
        init_db(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_signup_then_login(self):
        auth.register_student("Priyanka", "Priyanka R", "secret123", self.db)
        user = auth.login("priyanka", "secret123", self.db)   # username not case sensitive
        self.assertEqual(user["role"], "student")

    def test_password_is_not_stored_in_plain_text(self):
        auth.register_student("riya", "Riya", "secret123", self.db)
        with get_connection(self.db) as c:
            row = c.execute("SELECT password_hash, salt FROM users").fetchone()
        self.assertNotIn("secret123", row["password_hash"])
        self.assertEqual(len(row["salt"]), 32)

    def test_same_password_gets_different_hash_for_each_user(self):
        auth.register_student("riya", "Riya", "secret123", self.db)
        auth.register_student("mohit", "Mohit", "secret123", self.db)
        with get_connection(self.db) as c:
            hashes = [r[0] for r in c.execute("SELECT password_hash FROM users")]
        self.assertNotEqual(hashes[0], hashes[1])

    def test_wrong_password_and_unknown_user_give_same_message(self):
        auth.register_student("riya", "Riya", "secret123", self.db)
        messages = set()
        for args in (("riya", "wrongpass"), ("nobody", "secret123")):
            with self.assertRaises(auth.AuthError) as ctx:
                auth.login(*args, db_path=self.db)
            messages.add(str(ctx.exception))
        self.assertEqual(len(messages), 1)

    def test_duplicate_username_rejected(self):
        auth.register_student("riya", "Riya", "secret123", self.db)
        with self.assertRaises(auth.AuthError):
            auth.register_student("RIYA", "Other", "secret456", self.db)

    def test_input_validation(self):
        for username, name, pwd in [("ab", "X", "secret123"),
                                    ("bad name!", "X", "secret123"),
                                    ("riya", "", "secret123"),
                                    ("riya", "Riya", "123")]:
            with self.assertRaises(auth.AuthError):
                auth.register_student(username, name, pwd, self.db)

    def test_signup_can_never_create_admin(self):
        auth.register_student("riya", "Riya", "secret123", self.db)
        self.assertFalse(auth.admin_exists(self.db))
        self.assertEqual(auth.login("riya", "secret123", self.db)["role"], "student")

    def test_admin_role_and_permission_check(self):
        auth.create_admin("boss", "Boss", "adminpass", self.db)
        auth.register_student("riya", "Riya", "secret123", self.db)
        auth.require_admin(auth.login("boss", "adminpass", self.db))      # allowed
        with self.assertRaises(PermissionError):
            auth.require_admin(auth.login("riya", "secret123", self.db))  # blocked


class TestImporterValidation(unittest.TestCase):
    good = {"q": "x?", "options": ["a", "b", "c", "d"], "answer": "A", "explanation": "because"}

    def test_good_question_passes(self):
        self.assertIsNone(importer.validate_question(self.good))

    def test_bad_questions_are_caught(self):
        bad_versions = [
            {**self.good, "explanation": "  "},
            {**self.good, "answer": "E"},
            {**self.good, "options": ["a", "b", "c"]},
            {**self.good, "options": ["a", "a", "c", "d"]},
            {**self.good, "q": ""},
        ]
        for bad in bad_versions:
            self.assertIsNotNone(importer.validate_question(bad))


if __name__ == "__main__":
    unittest.main()