
"""The main window. It owns the logged-in user and switches between screens."""

import sqlite3
import tkinter as tk
from tkinter import messagebox

from app import database, results
from app.quiz import TEST_COUNT, QuizError, QuizSession, select_test_questions
from app.ui import theme
from app.ui.admin_screens import AdminPlaceholderScreen
from app.ui.auth_screens import LoginScreen, SignupScreen
from app.ui.browse_screens import (ModuleScreen, SemesterScreen, SubjectScreen,
                                   TestListScreen)
from app.ui.progress_screen import ProgressScreen
from app.ui.quiz_screens import QuizScreen, ResultScreen


class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QuizMaster")
        self.geometry("1000x720")
        self.minsize(860, 620)
        self.configure(bg=theme.BG)
        self.user = None          # set after login: user_id, username, full_name, role
        self._screen = None
        self.show_login()

    # ----- the one place where screens are swapped -----
    def _leave_ok(self):
        """Ask the current screen if it is fine to leave (a quiz in progress is not)."""
        check = getattr(self._screen, "confirm_leave", None)
        return check() if check else True

    def _show(self, screen_class, *args):
        if self._screen is not None:
            if not self._leave_ok():
                return
            self._screen.destroy()
        self._screen = screen_class(self, self, *args)
        self._screen.pack(fill="both", expand=True)

    # ----- login / logout -----
    def show_login(self):
        self._show(LoginScreen)

    def show_signup(self):
        self._show(SignupScreen)

    def login_success(self, user):
        self.user = user
        if user["role"] == "admin":
            self.show_admin()
        else:
            self.show_semesters()

    def logout(self):
        if not self._leave_ok():          # a quiz is running: ask first
            return
        self.user = None
        self.show_login()

    # ----- student flow: browsing -----
    def show_semesters(self):
        if self._need_login():
            return
        self._show(SemesterScreen)

    def show_subjects(self, semester):
        if self._need_login():
            return
        self._show(SubjectScreen, semester)

    def show_modules(self, semester, subject):
        if self._need_login():
            return
        self._show(ModuleScreen, semester, subject)

    def show_tests(self, semester, subject, module):
        if self._need_login():
            return
        self._show(TestListScreen, semester, subject, module)

    # ----- student flow: taking a test -----
    def start_quiz(self, semester, subject, module, test_number):
        if self._need_login():
            return
        try:
            pool = database.get_module_questions(module["module_id"])
            questions = select_test_questions(pool, module["module_id"], test_number)
            session = QuizSession(questions)
        except (QuizError, sqlite3.Error) as error:
            messagebox.showerror("Cannot start this test", str(error))
            return
        self._show(QuizScreen, semester, subject, module, test_number, session)

    def finish_quiz(self, semester, subject, module, test_number, session):
        """Save the result and show it. Returns False if saving failed."""
        try:
            results.save_attempt(self.user["user_id"], module["module_id"],
                                 test_number, session)
        except (QuizError, sqlite3.Error) as error:
            messagebox.showerror("Could not save your result", str(error))
            return False

        def again(number):
            return lambda: self.start_quiz(semester, subject, module, number)

        actions = [("Retake this test", again(test_number), "secondary"),
                   ("Back to tests",
                    lambda: self.show_tests(semester, subject, module), "secondary")]
        if test_number < TEST_COUNT:
            actions.append(("Next test \u2192", again(test_number + 1), "primary"))

        summary = {"heading": f"Test {test_number} result", "score": session.score,
                   "total": session.total, "percentage": session.percentage}
        crumbs = (f"{semester['name']}  \u203a  {subject['name']}  \u203a  "
                  f"Module {module['module_number']}  \u203a  Test {test_number}")
        self._show(ResultScreen, crumbs,
                   lambda: self.show_tests(semester, subject, module),
                   summary, session.review_items(), actions)
        return True

    # ----- student flow: My Progress -----
    def show_progress(self):
        if self._need_login():
            return
        self._show(ProgressScreen)

    def show_attempt(self, attempt):
        """Re-open the answers and reasons of an old attempt."""
        try:
            items = results.get_attempt_review(attempt["attempt_id"], self.user["user_id"])
        except (PermissionError, sqlite3.Error) as error:
            messagebox.showerror("Cannot open this attempt", str(error))
            return
        summary = {
            "heading": f"{attempt['subject_code']}  \u00b7  Module {attempt['module_number']}"
                       f"  \u00b7  Test {attempt['test_number']}",
            "score": attempt["score"], "total": attempt["total"],
            "percentage": attempt["percentage"]}
        self._show(ResultScreen, "My Progress  \u203a  Review", self.show_progress,
                   summary, items,
                   [("Back to My Progress", self.show_progress, "primary")])

    # ----- admin -----
    def show_admin(self):
        self._show(AdminPlaceholderScreen)

    def _need_login(self):
        """Send the user to Login if somehow nobody is logged in."""
        if self.user is None:
            self.show_login()
            return True
        return False