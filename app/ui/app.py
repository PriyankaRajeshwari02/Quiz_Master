"""The main window. It owns the logged-in user and switches between screens."""

import tkinter as tk
from tkinter import messagebox

from app.ui import theme
from app.ui.admin_screens import AdminPlaceholderScreen
from app.ui.auth_screens import LoginScreen, SignupScreen
from app.ui.browse_screens import (ModuleScreen, SemesterScreen, SubjectScreen,
                                   TestListScreen)


class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QuizMaster")
        self.geometry("1000x700")
        self.minsize(860, 620)
        self.configure(bg=theme.BG)
        self.user = None          # set after login: user_id, username, full_name, role
        self._screen = None
        self.show_login()

    # ----- the one place where screens are swapped -----
    def _show(self, screen_class, *args):
        if self._screen is not None:
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
        self.user = None
        self.show_login()

    # ----- student flow -----
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

    def start_quiz(self, semester, subject, module, test_number):
        # The quiz screen is built in the next step.
        messagebox.showinfo(
            "Coming next",
            f"Test {test_number} of Module {module['module_number']} will open here.\n"
            "The quiz screen is the next thing we build.")

    def show_progress(self):
        messagebox.showinfo("Coming next", "My Progress is built in the next step.")

    # ----- admin -----
    def show_admin(self):
        self._show(AdminPlaceholderScreen)

    def _need_login(self):
        """Send the user to Login if somehow nobody is logged in."""
        if self.user is None:
            self.show_login()
            return True
        return False