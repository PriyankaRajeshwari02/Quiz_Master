"""Login and Sign up screens."""

import sqlite3
import tkinter as tk

from app import auth
from app.ui import theme
from app.ui.theme import BaseScreen


class _AuthCard(BaseScreen):
    """Shared layout: a centred white card with a title, fields and a message line."""

    def __init__(self, parent, app, title, subtitle):
        super().__init__(parent, app)
        self.build_header()
        self.body.pack_forget()                      # we use our own centred layout
        wrapper = tk.Frame(self, bg=theme.BG)
        wrapper.pack(expand=True)
        self.card = theme.make_card(wrapper)
        self.card.pack(padx=20, pady=20, ipadx=34, ipady=22)
        theme.make_label(self.card, title, 20, "bold", bg=theme.CARD).pack(pady=(10, 2))
        theme.make_label(self.card, subtitle, 11, color=theme.MUTED, bg=theme.CARD).pack(
            pady=(0, 20))

    def add_message_line(self):
        self.message = theme.make_label(self.card, "", 10, color=theme.DANGER,
                                        bg=theme.CARD, wraplength=300, justify="left")
        self.message.pack(anchor="w", pady=(0, 8))

    def show_error(self, text):
        self.message.config(text=text)


class LoginScreen(_AuthCard):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Welcome back", "Log in to continue your revision")
        self.username = theme.labeled_entry(self.card, "USERNAME")
        self.password = theme.labeled_entry(self.card, "PASSWORD", show="\u2022")
        self.add_message_line()

        theme.make_button(self.card, "Log in", self.submit).pack(fill="x")
        link = theme.make_label(self.card, "New here? Create an account", 10, "bold",
                                theme.PRIMARY, theme.CARD, cursor="hand2")
        link.pack(pady=(14, 4))
        link.bind("<Button-1>", lambda e: app.show_signup())

        self.username.bind("<Return>", lambda e: self.password.focus_set())
        self.password.bind("<Return>", lambda e: self.submit())
        self.after(100, self.username.focus_set)

    def submit(self):
        try:
            user = auth.login(self.username.get(), self.password.get())
        except auth.AuthError as error:
            self.show_error(str(error))
            return
        except sqlite3.Error:
            self.show_error("Database problem. Please restart the app.")
            return
        self.app.login_success(user)


class SignupScreen(_AuthCard):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Create your account", "Students only. It takes 20 seconds")
        self.full_name = theme.labeled_entry(self.card, "FULL NAME")
        self.username = theme.labeled_entry(self.card, "USERNAME")
        self.password = theme.labeled_entry(self.card, "PASSWORD (6+ characters)", show="\u2022")
        self.confirm = theme.labeled_entry(self.card, "CONFIRM PASSWORD", show="\u2022")
        self.add_message_line()

        theme.make_button(self.card, "Sign up", self.submit).pack(fill="x")
        link = theme.make_label(self.card, "Already have an account? Log in", 10, "bold",
                                theme.PRIMARY, theme.CARD, cursor="hand2")
        link.pack(pady=(14, 4))
        link.bind("<Button-1>", lambda e: app.show_login())

        self.full_name.bind("<Return>", lambda e: self.username.focus_set())
        self.username.bind("<Return>", lambda e: self.password.focus_set())
        self.password.bind("<Return>", lambda e: self.confirm.focus_set())
        self.confirm.bind("<Return>", lambda e: self.submit())
        self.after(100, self.full_name.focus_set)

    def submit(self):
        if self.password.get() != self.confirm.get():
            self.show_error("The two passwords do not match.")
            return
        try:
            auth.register_student(self.username.get(), self.full_name.get(),
                                  self.password.get())
            user = auth.login(self.username.get(), self.password.get())
        except auth.AuthError as error:
            self.show_error(str(error))
            return
        except sqlite3.Error:
            self.show_error("Database problem. Please restart the app.")
            return
        self.app.login_success(user)       # signed up and straight in