"""QuizMaster desktop application.

Run this file to open the quiz:

    python main.py
"""

import tkinter as tk
from tkinter import messagebox

from database import CATEGORIES, Database, DatabaseError
from quiz import QuizError, QuizSession, validate_student_name


# One set of colours and fonts keeps every screen consistent.
BG = "#E8EEF5"
HEADER_BG = "#1F4E79"
CARD_BG = "#FFFFFF"
PRIMARY = "#1F4E79"
PRIMARY_ACTIVE = "#163A5C"
TEXT = "#1C2833"
MUTED = "#5D6D7E"
SUCCESS = "#0E6655"
LINE = "#D5DDE8"

FONT_TITLE = ("Segoe UI", 24, "bold")
FONT_HEADING = ("Segoe UI", 16, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 10)
FONT_BUTTON = ("Segoe UI", 11, "bold")


class QuizMasterApp:
    """Owns the window and switches between the four screens."""

    def __init__(self, db_path=None):
        self.db = Database(db_path)
        self.session = None
        self.student_name = ""
        self.last_summary = None

        self.root = tk.Tk()
        self.root.title("QuizMaster")
        self.root.geometry("780x600")
        self.root.minsize(720, 560)
        self.root.configure(bg=BG)
        self._center_window()

        self.container = tk.Frame(self.root, bg=BG)
        self.container.pack(fill="both", expand=True)
        self.show_welcome()

    def run(self):
        self.root.mainloop()

    def _center_window(self):
        self.root.update_idletasks()
        width, height = 780, 600
        x_pos = max((self.root.winfo_screenwidth() - width) // 2, 0)
        y_pos = max((self.root.winfo_screenheight() - height) // 2, 0)
        self.root.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

    def _clear(self):
        """Remove the current screen before showing the next one."""
        self.root.unbind("<Return>")
        for widget in self.container.winfo_children():
            widget.destroy()

    def _header(self, subtitle):
        header = tk.Frame(self.container, bg=HEADER_BG, height=104)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="QuizMaster",
            font=FONT_TITLE,
            bg=HEADER_BG,
            fg="white",
        ).pack(anchor="w", padx=32, pady=(16, 0))
        tk.Label(
            header,
            text=subtitle,
            font=FONT_SMALL,
            bg=HEADER_BG,
            fg="#D6E4F0",
        ).pack(anchor="w", padx=32)

    def _card(self):
        outer = tk.Frame(self.container, bg=BG)
        outer.pack(fill="both", expand=True, padx=36, pady=24)
        card = tk.Frame(outer, bg=CARD_BG, highlightbackground=LINE, highlightthickness=1)
        card.pack(fill="both", expand=True)
        return card

    def _button(self, parent, text, command, primary=True):
        background = PRIMARY if primary else "#5C6B7A"
        active = PRIMARY_ACTIVE if primary else "#465360"
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=FONT_BUTTON,
            bg=background,
            fg="white",
            activebackground=active,
            activeforeground="white",
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            bd=0,
        )

    def show_welcome(self):
        """Screen A: ask for the student name."""
        self.session = None
        self._clear()
        self._header("A simple quiz for computer science practice")

        card = self._card()
        content = tk.Frame(card, bg=CARD_BG)
        content.pack(expand=True)

        tk.Label(
            content,
            text="Welcome",
            font=FONT_HEADING,
            bg=CARD_BG,
            fg=TEXT,
        ).pack(pady=(8, 6))
        tk.Label(
            content,
            text="Enter your name to begin.",
            font=FONT_BODY,
            bg=CARD_BG,
            fg=MUTED,
        ).pack(pady=(0, 18))

        self.name_var = tk.StringVar(value=self.student_name)
        entry = tk.Entry(
            content,
            textvariable=self.name_var,
            font=("Segoe UI", 13),
            width=32,
            relief="solid",
            bd=1,
            justify="center",
        )
        entry.pack(ipady=6)
        entry.focus_set()

        self._button(content, "Start Quiz", self.start_quiz).pack(pady=22)
        self.root.bind("<Return>", lambda _event: self.start_quiz())

    def start_quiz(self):
        name, error = validate_student_name(self.name_var.get())
        if error:
            messagebox.showwarning("Name required", error)
            return
        self.student_name = name
        self.show_categories()

    def show_categories(self):
        """Screen B: choose exactly one category."""
        self._clear()
        self._header(f"Hello, {self.student_name}")

        card = self._card()
        content = tk.Frame(card, bg=CARD_BG)
        content.pack(expand=True, fill="x", padx=48)

        tk.Label(
            content,
            text="Select a category",
            font=FONT_HEADING,
            bg=CARD_BG,
            fg=TEXT,
        ).pack(anchor="w", pady=(28, 6))
        tk.Label(
            content,
            text="You will answer 10 questions from the category you choose.",
            font=FONT_BODY,
            bg=CARD_BG,
            fg=MUTED,
            wraplength=560,
            justify="left",
        ).pack(anchor="w", pady=(0, 16))

        self.category_var = tk.StringVar(value="")
        for category in CATEGORIES:
            tk.Radiobutton(
                content,
                text=category,
                variable=self.category_var,
                value=category,
                font=FONT_BODY,
                bg=CARD_BG,
                fg=TEXT,
                activebackground=CARD_BG,
                selectcolor="#EAF2FA",
                anchor="w",
                padx=8,
                pady=6,
            ).pack(fill="x", pady=3)

        buttons = tk.Frame(content, bg=CARD_BG)
        buttons.pack(anchor="w", pady=22)
        self._button(buttons, "Continue", self.begin_quiz).pack(side="left")
        self._button(buttons, "Back", self.show_welcome, primary=False).pack(side="left", padx=10)

    def begin_quiz(self):
        category = self.category_var.get().strip()
        if category not in CATEGORIES:
            messagebox.showwarning("Category required", "Please select a category.")
            return
        try:
            questions = self.db.get_questions(category)
        except DatabaseError as exc:
            messagebox.showerror("Database error", str(exc))
            return
        if not questions:
            messagebox.showerror(
                "No questions",
                "No questions were found for this category.",
            )
            return
        try:
            self.session = QuizSession(self.student_name, category, questions)
        except QuizError as exc:
            messagebox.showerror("Quiz error", str(exc))
            return
        self.show_question()

    def show_question(self):
        """Screen C: show one question and four options."""
        question = self.session.current_question()
        number = self.session.question_number()
        total = self.session.total_questions

        self._clear()
        self._header(self.session.category)
        card = self._card()

        top = tk.Frame(card, bg=CARD_BG)
        top.pack(fill="x", padx=28, pady=(22, 8))
        tk.Label(
            top,
            text=f"Question {number} of {total}",
            font=FONT_HEADING,
            bg=CARD_BG,
            fg=PRIMARY,
        ).pack(anchor="w")

        tk.Label(
            card,
            text=question["question"],
            font=("Segoe UI", 13),
            bg=CARD_BG,
            fg=TEXT,
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=28, pady=(8, 16))

        # An empty value means nothing is selected yet.
        self.choice = tk.StringVar(value="")
        options = tk.Frame(card, bg=CARD_BG)
        options.pack(fill="x", padx=28)
        for key in ("A", "B", "C", "D"):
            tk.Radiobutton(
                options,
                text=f"{key}.  {question['option_' + key.lower()]}",
                variable=self.choice,
                value=key,
                font=FONT_BODY,
                bg=CARD_BG,
                fg=TEXT,
                activebackground=CARD_BG,
                selectcolor="#EAF2FA",
                anchor="w",
                justify="left",
                wraplength=540,
                padx=6,
                pady=4,
            ).pack(fill="x", pady=2)

        button_text = "Submit" if number == total else "Next"
        self._button(card, button_text, self.go_next).pack(anchor="w", padx=28, pady=22)

    def go_next(self):
        """Save the selected option. Stay on the question if none is selected."""
        try:
            finished = self.session.answer_current(self.choice.get())
        except QuizError as exc:
            messagebox.showwarning("Selection required", str(exc))
            return

        if finished:
            self.show_result()
        else:
            self.show_question()

    def show_result(self):
        """Screen D: show the score and store this attempt."""
        summary = self.session.summary()
        self.last_summary = summary
        try:
            self.db.save_result(
                summary["username"],
                summary["category"],
                summary["score"],
                summary["total_questions"],
                summary["percentage"],
            )
            saved_note = "Your result has been saved."
        except DatabaseError as exc:
            saved_note = f"The result could not be saved. {exc}"

        self._clear()
        self._header("Quiz complete")
        card = self._card()

        tk.Label(
            card,
            text="Your Result",
            font=FONT_HEADING,
            bg=CARD_BG,
            fg=TEXT,
        ).pack(anchor="w", padx=28, pady=(20, 10))

        table = tk.Frame(card, bg=CARD_BG)
        table.pack(anchor="w", padx=28)
        rows = [
            ("Student name", summary["username"]),
            ("Category", summary["category"]),
            ("Total questions", str(summary["total_questions"])),
            ("Correct answers", str(summary["correct"])),
            ("Incorrect answers", str(summary["incorrect"])),
            ("Final score", f"{summary['score']} / {summary['total_questions']}"),
            ("Percentage", f"{summary['percentage']:.2f}%"),
        ]
        for row_number, (label, value) in enumerate(rows):
            tk.Label(
                table,
                text=label,
                font=FONT_BODY,
                bg=CARD_BG,
                fg=MUTED,
                width=20,
                anchor="w",
            ).grid(row=row_number, column=0, sticky="w", pady=3)
            tk.Label(
                table,
                text=value,
                font=("Segoe UI", 12, "bold"),
                bg=CARD_BG,
                fg=TEXT,
                anchor="w",
                justify="left",
                wraplength=360,
            ).grid(row=row_number, column=1, sticky="w", padx=(12, 0), pady=3)

        tk.Label(
            card,
            text=summary["message"],
            font=FONT_BODY,
            bg=CARD_BG,
            fg=SUCCESS,
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=28, pady=(16, 4))
        tk.Label(
            card,
            text=saved_note,
            font=FONT_SMALL,
            bg=CARD_BG,
            fg=MUTED,
        ).pack(anchor="w", padx=28)

        buttons = tk.Frame(card, bg=CARD_BG)
        buttons.pack(anchor="w", padx=28, pady=20)
        self._button(buttons, "Restart Quiz", self.show_welcome).pack(side="left")
        self._button(buttons, "Exit", self.root.destroy, primary=False).pack(side="left", padx=10)


def main():
    try:
        app = QuizMasterApp()
    except DatabaseError as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Database error", str(exc))
        root.destroy()
        return
    app.run()


if __name__ == "__main__":
    main()
