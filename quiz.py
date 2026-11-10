"""Quiz rules for QuizMaster.

The screens in main.py collect input. This module decides whether an
answer is valid, updates the score, and builds the final result.
"""


class QuizError(Exception):
    """Raised when the student tries to continue without a valid answer."""


class QuizSession:
    """Tracks one attempt from the first question to the result."""

    def __init__(self, username, category, questions):
        if not username or not str(username).strip():
            raise QuizError("A student name is required.")
        if not questions:
            raise QuizError("No questions are available for this category.")

        self.username = str(username).strip()
        self.category = category
        self.questions = questions
        self.index = 0
        self.score = 0

    @property
    def total_questions(self):
        return len(self.questions)

    def question_number(self):
        """Return the 1-based number of the question on screen."""
        return self.index + 1

    def is_complete(self):
        return self.index >= self.total_questions

    def current_question(self):
        if self.is_complete():
            raise QuizError("There are no more questions in this quiz.")
        return self.questions[self.index]

    def answer_current(self, selected_option):
        """Check one answer, add 1 to the score if it is correct, then move on.

        Returns True when this answer finishes the quiz.
        """
        if self.is_complete():
            raise QuizError("This quiz is already complete.")

        selected = (selected_option or "").strip().upper()
        if selected not in ("A", "B", "C", "D"):
            raise QuizError("Please select an option before continuing.")

        correct = self.current_question()["correct_answer"].strip().upper()
        if selected == correct:
            self.score += 1

        # Moving the index also prevents the same question from being skipped
        # or answered a second time.
        self.index += 1
        return self.is_complete()

    def summary(self):
        """Return the values shown on the result screen."""
        total = self.total_questions
        percentage = round((self.score / total) * 100, 2) if total else 0.0
        return {
            "username": self.username,
            "category": self.category,
            "total_questions": total,
            "correct": self.score,
            "incorrect": total - self.score,
            "score": self.score,
            "percentage": percentage,
            "message": performance_message(percentage),
        }


def performance_message(percentage):
    """Choose a short remark from the percentage score."""
    if percentage >= 80:
        return "Excellent. You have a strong understanding of this topic."
    if percentage >= 60:
        return "Good work. Revise a few points and you will do even better."
    if percentage >= 40:
        return "Fair attempt. Spend more time revising this category."
    return "Needs improvement. Please revise the basics and try again."


def validate_student_name(name):
    """Return (clean_name, error_message). error_message is None when valid."""
    clean_name = (name or "").strip()
    if not clean_name:
        return None, "Please enter your name."
    if len(clean_name) > 40:
        return None, "Please enter a name with 40 characters or fewer."
    return clean_name, None
