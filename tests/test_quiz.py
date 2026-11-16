import os
import tempfile
import unittest
from collections import Counter

from app import auth, database, importer, results
from app.quiz import QuizError, QuizSession, select_test_questions

SYLLABUS_DIR = os.path.join(database.BASE_DIR, "data", "syllabus")


class TestSelection(unittest.TestCase):
    def setUp(self):
        self.pool = [{"question_id": i} for i in range(1, 51)]   # 50 questions

    def ids(self, test_number):
        return [q["question_id"] for q in select_test_questions(self.pool, 1, test_number)]

    def test_each_test_has_10_distinct_questions(self):
        for t in range(1, 11):
            ids = self.ids(t)
            self.assertEqual(len(ids), 10)
            self.assertEqual(len(set(ids)), 10)

    def test_same_test_always_gives_same_questions(self):
        self.assertEqual(self.ids(3), self.ids(3))

    def test_pool_order_does_not_matter(self):
        shuffled = list(reversed(self.pool))
        a = [q["question_id"] for q in select_test_questions(shuffled, 1, 4)]
        self.assertEqual(a, self.ids(4))

    def test_tests_1_to_5_cover_whole_pool_without_repeats(self):
        everything = [i for t in range(1, 6) for i in self.ids(t)]
        self.assertEqual(sorted(everything), list(range(1, 51)))

    def test_every_question_appears_exactly_twice_in_10_tests(self):
        counts = Counter(i for t in range(1, 11) for i in self.ids(t))
        self.assertEqual(set(counts.values()), {2})

    def test_second_half_is_a_different_mix(self):
        self.assertNotEqual(self.ids(1), self.ids(6))

    def test_small_pool_is_rejected(self):
        with self.assertRaises(QuizError):
            select_test_questions(self.pool[:5], 1, 1)

    def test_bad_test_number_is_rejected(self):
        for bad in (0, 11):
            with self.assertRaises(QuizError):
                select_test_questions(self.pool, 1, bad)


def make_question(i, correct="A"):
    return {"question_id": i, "question": f"Q{i}", "option_a": "a", "option_b": "b",
            "option_c": "c", "option_d": "d", "correct_answer": correct,
            "explanation": f"because {i}"}


class TestSession(unittest.TestCase):
    def test_score_and_percentage(self):
        session = QuizSession([make_question(1), make_question(2), make_question(3, "B"),
                               make_question(4, "C")])
        for letter in ("A", "B", "B", "D"):      # right, wrong, right, wrong
            session.answer_current(letter)
            if not session.is_last:
                session.next_question()
        self.assertEqual(session.score, 2)
        self.assertEqual(session.percentage, 50.0)
        self.assertTrue(session.is_finished)

    def test_cannot_continue_without_answering(self):
        session = QuizSession([make_question(1), make_question(2)])
        with self.assertRaises(QuizError):
            session.next_question()

    def test_invalid_option_rejected(self):
        session = QuizSession([make_question(1)])
        with self.assertRaises(QuizError):
            session.answer_current("E")

    def test_review_contains_reason_for_every_question(self):
        session = QuizSession([make_question(1), make_question(2)])
        session.answer_current("B")
        session.next_question()
        session.answer_current("A")
        review = session.review_items()
        self.assertEqual([r["is_correct"] for r in review], [False, True])
        self.assertTrue(all(r["explanation"] for r in review))


class TestResultsWithRealData(unittest.TestCase):
    """Uses the real sem5.json, so it also proves Module 1 works end to end."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "test.db")
        importer.import_all(self.db, SYLLABUS_DIR)
        auth.register_student("riya", "Riya", "secret123", self.db)
        auth.register_student("mohit", "Mohit", "secret123", self.db)
        self.riya = auth.login("riya", "secret123", self.db)["user_id"]
        self.mohit = auth.login("mohit", "secret123", self.db)["user_id"]
        subject = database.get_subjects(5, self.db)[0]
        self.module = database.get_modules(subject["subject_id"], self.db)[0]
        self.pool = database.get_module_questions(self.module["module_id"], self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def take_test(self, user_id, test_number, answer_all_correct):
        questions = select_test_questions(self.pool, self.module["module_id"], test_number)
        session = QuizSession(questions)
        for q in questions:
            session.answer_current(q["correct_answer"] if answer_all_correct else "A")
            if not session.is_last:
                session.next_question()
        return results.save_attempt(user_id, self.module["module_id"], test_number,
                                    session, self.db)

    def test_module_1_has_50_questions(self):
        self.assertEqual(len(self.pool), 50)

    def test_save_status_progress_and_review(self):
        attempt_id = self.take_test(self.riya, 1, True)
        self.take_test(self.riya, 1, False)           # second try, worse score
        status = results.get_test_status(self.riya, self.module["module_id"], self.db)
        self.assertEqual(status[1]["attempts"], 2)
        self.assertEqual(status[1]["best"], 100.0)    # best score is kept
        self.assertNotIn(2, status)                   # Test 2 never attempted
        self.assertEqual(len(results.get_user_attempts(self.riya, self.db)), 2)
        review = results.get_attempt_review(attempt_id, self.riya, self.db)
        self.assertEqual(len(review), 10)
        self.assertTrue(all(r["is_correct"] and r["explanation"] for r in review))

    def test_user_cannot_view_someone_elses_attempt(self):
        attempt_id = self.take_test(self.riya, 2, True)
        with self.assertRaises(PermissionError):
            results.get_attempt_review(attempt_id, self.mohit, self.db)

    def test_unfinished_quiz_cannot_be_saved(self):
        questions = select_test_questions(self.pool, self.module["module_id"], 1)
        session = QuizSession(questions)
        session.answer_current("A")
        with self.assertRaises(QuizError):
            results.save_attempt(self.riya, self.module["module_id"], 1, session, self.db)


if __name__ == "__main__":
    unittest.main()