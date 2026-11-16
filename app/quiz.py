"""Quiz logic: which 10 questions go in which test, and a running quiz session.

No screens and no database here, so it is easy to test.
"""

import random

TEST_COUNT = 10            # mock tests per module
QUESTIONS_PER_TEST = 10    # questions in one test
HALF = TEST_COUNT // 2     # tests 1-5 use shuffle 1, tests 6-10 use shuffle 2
LETTERS = ("A", "B", "C", "D")


class QuizError(Exception):
    """Raised for invalid quiz actions."""


def select_test_questions(pool, module_id, test_number):
    """Pick the 10 questions of one mock test from a module's question pool.

    Rules:
      * The same (module, test number) ALWAYS gives the same 10 questions,
        so a student can compare Test 3 today with Test 3 next week.
      * Tests 1-5 use one fixed shuffle of the pool (no repeats among them).
      * Tests 6-10 use a second, different shuffle.
      * With a 50-question pool every question appears exactly twice.
    """
    if not 1 <= test_number <= TEST_COUNT:
        raise QuizError(f"Test number must be 1 to {TEST_COUNT}.")
    if len(pool) < QUESTIONS_PER_TEST:
        raise QuizError(
            f"This module needs at least {QUESTIONS_PER_TEST} questions "
            f"(it has {len(pool)}).")

    ordered = sorted(pool, key=lambda q: q["question_id"])
    round_number = 0 if test_number <= HALF else 1
    # A string seed gives the same shuffle on every computer and every run.
    random.Random(f"quizmaster-{module_id}-{round_number}").shuffle(ordered)

    start = ((test_number - 1) % HALF) * QUESTIONS_PER_TEST
    return [ordered[(start + i) % len(ordered)] for i in range(QUESTIONS_PER_TEST)]


def performance_message(percentage):
    if percentage >= 90:
        return "Excellent! You are exam ready for this module."
    if percentage >= 75:
        return "Very good. Revise the few questions you missed."
    if percentage >= 50:
        return "Good effort. Read the explanations and try again."
    return "Needs work. Study the module and retake this test."


class QuizSession:
    """One student taking one test: tracks the current question and answers."""

    def __init__(self, questions):
        if not questions:
            raise QuizError("A quiz needs at least one question.")
        self.questions = list(questions)
        self.index = 0
        self.answers = {}          # question_id -> selected letter

    # ----- progress -----
    @property
    def total(self):
        return len(self.questions)

    @property
    def current_question(self):
        return self.questions[self.index]

    @property
    def is_last(self):
        return self.index == self.total - 1

    @property
    def is_finished(self):
        return len(self.answers) == self.total

    # ----- actions -----
    def answer_current(self, letter):
        if letter not in LETTERS:
            raise QuizError("Choose one of A, B, C or D.")
        self.answers[self.current_question["question_id"]] = letter

    def has_answered_current(self):
        return self.current_question["question_id"] in self.answers

    def next_question(self):
        if not self.has_answered_current():
            raise QuizError("Select an option before continuing.")
        if self.is_last:
            raise QuizError("This is the last question.")
        self.index += 1

    # ----- results -----
    @property
    def score(self):
        return sum(1 for q in self.questions
                   if self.answers.get(q["question_id"]) == q["correct_answer"])

    @property
    def percentage(self):
        return round(self.score * 100 / self.total, 1)

    def review_items(self):
        """Everything the result screen needs: your answer, right answer, reason."""
        items = []
        for number, q in enumerate(self.questions, start=1):
            selected = self.answers.get(q["question_id"])
            items.append({
                "number": number,
                "question": q["question"],
                "options": {"A": q["option_a"], "B": q["option_b"],
                            "C": q["option_c"], "D": q["option_d"]},
                "selected": selected,
                "correct": q["correct_answer"],
                "is_correct": selected == q["correct_answer"],
                "explanation": q["explanation"],
            })
        return items