"""The Quiz screen (one question at a time) and the Result / Review screen."""

import tkinter as tk
from tkinter import messagebox

from app.quiz import LETTERS, performance_message
from app.ui import theme
from app.ui.theme import BaseScreen
from app.ui.widgets import DANGER_BG, SUCCESS_BG, ScrollableFrame, score_colour


class _OptionRow(tk.Frame):
    """One answer choice: a letter badge and the option text. Click to select."""

    def __init__(self, parent, letter, on_pick):
        super().__init__(parent, bg=theme.CARD, highlightthickness=1,
                         highlightbackground=theme.BORDER, cursor="hand2")
        self.badge = theme.make_label(self, letter, 11, "bold", theme.PRIMARY,
                                      theme.CARD, width=3)
        self.badge.pack(side="left", padx=(12, 4), pady=10)
        self.text = theme.make_label(self, "", 12, "normal", theme.TEXT, theme.CARD,
                                     wraplength=620, justify="left", anchor="w")
        self.text.pack(side="left", fill="x", expand=True, padx=(4, 12), pady=10)
        for widget in (self, self.badge, self.text):
            widget.bind("<Button-1>", lambda e: on_pick(letter))

    def set_text(self, text):
        self.text.config(text=text)

    def set_selected(self, selected):
        if selected:
            self.config(bg=theme.HOVER, highlightbackground=theme.PRIMARY,
                        highlightthickness=2)
            self.badge.config(bg=theme.PRIMARY, fg="white")
            self.text.config(bg=theme.HOVER)
        else:
            self.config(bg=theme.CARD, highlightbackground=theme.BORDER,
                        highlightthickness=1)
            self.badge.config(bg=theme.CARD, fg=theme.PRIMARY)
            self.text.config(bg=theme.CARD)


class QuizScreen(BaseScreen):
    """Shows one question at a time. Keys A-D (or 1-4) pick, Enter goes next."""

    def __init__(self, parent, app, semester, subject, module, test_number, session):
        super().__init__(parent, app)
        self.session = session
        self.finished = False
        self._context = (semester, subject, module, test_number)

        crumbs = (f"{semester['name']}  \u203a  {subject['name']}  \u203a  "
                  f"Module {module['module_number']}  \u203a  Test {test_number}")
        body = self.build_header(
            crumbs=crumbs,
            back=lambda: app.show_tests(semester, subject, module))

        self.progress_label = theme.make_label(body, "", 12, "bold", theme.PRIMARY)
        self.progress_label.pack(anchor="w")
        self.bar = tk.Canvas(body, height=8, bg=theme.BORDER, highlightthickness=0)
        self.bar.pack(fill="x", pady=(6, 14))
        self.bar.bind("<Configure>", lambda e: self._draw_bar())

        card = theme.make_card(body)
        card.pack(fill="x")
        self.question_label = theme.make_label(card, "", 14, "bold", theme.TEXT, theme.CARD,
                                               wraplength=700, justify="left", anchor="w")
        self.question_label.pack(anchor="w", padx=24, pady=(22, 14))
        options = tk.Frame(card, bg=theme.CARD)
        options.pack(fill="x", padx=24, pady=(0, 20))
        self.rows = {}
        for letter in LETTERS:
            row = _OptionRow(options, letter, self._choose)
            row.pack(fill="x", pady=4)
            self.rows[letter] = row

        footer = tk.Frame(body, bg=theme.BG)
        footer.pack(fill="x", pady=(16, 0))
        self.next_button = theme.make_button(footer, "Next", self._next)
        self.next_button.pack(side="right")
        self.message = theme.make_label(footer, "", 10, color=theme.DANGER)
        self.message.pack(side="right", padx=16)
        theme.make_label(footer, "Tip: press A, B, C or D, then Enter.", 10,
                         color=theme.MUTED).pack(side="left")

        self._key_id = self.winfo_toplevel().bind("<Key>", self._on_key, add="+")
        self._load_question()

    # ----- showing the current question -----
    def _load_question(self):
        session = self.session
        question = session.current_question
        self.progress_label.config(
            text=f"Question {session.index + 1} of {session.total}")
        self.question_label.config(text=question["question"])
        texts = {"A": question["option_a"], "B": question["option_b"],
                 "C": question["option_c"], "D": question["option_d"]}
        chosen = session.answers.get(question["question_id"])
        for letter, row in self.rows.items():
            row.set_text(texts[letter])
            row.set_selected(letter == chosen)
        self.next_button.config(text="Submit test" if session.is_last else "Next")
        self.message.config(text="")
        self._draw_bar()

    def _draw_bar(self):
        self.bar.delete("all")
        width = self.bar.winfo_width()
        done = (self.session.index + 1) / self.session.total
        self.bar.create_rectangle(0, 0, width * done, 8, fill=theme.PRIMARY, width=0)

    # ----- user actions -----
    def _choose(self, letter):
        self.session.answer_current(letter)
        for key, row in self.rows.items():
            row.set_selected(key == letter)
        self.message.config(text="")

    def _next(self):
        if not self.session.has_answered_current():
            self.message.config(text="Select an option first.")
            return
        if self.session.is_last:
            self._submit()
        else:
            self.session.next_question()
            self._load_question()

    def _submit(self):
        semester, subject, module, test_number = self._context
        self.finished = True              # so leaving this screen needs no warning
        saved = self.app.finish_quiz(semester, subject, module, test_number, self.session)
        if not saved:
            self.finished = False         # saving failed: stay and let her try again

    def _on_key(self, event):
        key = event.keysym.upper()
        if key in LETTERS:
            self._choose(key)
        elif key in ("1", "2", "3", "4"):
            self._choose(LETTERS[int(key) - 1])
        elif key in ("RETURN", "KP_ENTER"):
            self._next()

    # ----- leaving the screen -----
    def confirm_leave(self):
        """Called by the app before it swaps this screen for another one."""
        if self.finished or not self.session.answers:
            return True
        leave = messagebox.askyesno(
            "Leave this test?", "Your answers in this test will be lost. Leave anyway?")
        if leave:
            self.finished = True          # already confirmed: do not ask twice
        return leave

    def destroy(self):
        try:
            self.winfo_toplevel().unbind("<Key>", self._key_id)
        except tk.TclError:
            pass
        super().destroy()


def render_review(container, items, only_wrong=False):
    """Draw every question with your answer, the right answer and the reason."""
    for item in items:
        if only_wrong and item["is_correct"]:
            continue
        card = theme.make_card(container)
        card.pack(fill="x", pady=6, padx=(0, 4))

        top = tk.Frame(card, bg=theme.CARD)
        top.pack(fill="x", padx=18, pady=(14, 4))
        theme.make_label(top, f"Q{item['number']}", 11, "bold", theme.MUTED,
                         theme.CARD).pack(side="left")
        verdict = "\u2713 Correct" if item["is_correct"] else "\u2717 Wrong"
        colour = theme.SUCCESS if item["is_correct"] else theme.DANGER
        theme.make_label(top, verdict, 11, "bold", colour, theme.CARD).pack(side="right")

        theme.make_label(card, item["question"], 12, "bold", theme.TEXT, theme.CARD,
                         wraplength=680, justify="left", anchor="w").pack(
            anchor="w", padx=18, pady=(0, 8))

        for letter in LETTERS:
            text = f"{letter}.  {item['options'][letter]}"
            background, foreground = theme.CARD, theme.TEXT
            if letter == item["correct"]:
                background, foreground = SUCCESS_BG, theme.SUCCESS
                text += "     \u2713 correct answer"
            if letter == item["selected"] and not item["is_correct"]:
                background, foreground = DANGER_BG, theme.DANGER
                text += "     \u2190 your answer"
            elif letter == item["selected"]:
                text += "     \u2190 your answer"
            theme.make_label(card, text, 11, "normal", foreground, background,
                             wraplength=660, justify="left", anchor="w",
                             padx=10, pady=5).pack(fill="x", padx=18, pady=2)

        reason = tk.Frame(card, bg=theme.BG)
        reason.pack(fill="x", padx=18, pady=(10, 16))
        theme.make_label(reason, "Reason", 10, "bold", theme.PRIMARY, theme.BG).pack(
            anchor="w", padx=12, pady=(8, 0))
        theme.make_label(reason, item["explanation"], 11, "normal", theme.TEXT, theme.BG,
                         wraplength=650, justify="left", anchor="w").pack(
            anchor="w", padx=12, pady=(2, 10))


class ResultScreen(BaseScreen):
    """Score card on top, then every question with its reason underneath.

    Used right after a test AND when re-opening an old attempt from My Progress.
    `actions` is a list of (button text, command, 'primary' or 'secondary').
    """

    def __init__(self, parent, app, crumbs, back, summary, items, actions):
        super().__init__(parent, app)
        self.items = items
        body = self.build_header(crumbs=crumbs, back=back)

        percentage = summary["percentage"]
        card = theme.make_card(body)
        card.pack(fill="x")
        left = tk.Frame(card, bg=theme.CARD)
        left.pack(side="left", padx=24, pady=16)
        theme.make_label(left, summary["heading"], 11, "bold", theme.MUTED, theme.CARD).pack(
            anchor="w")
        theme.make_label(left, f"{summary['score']} / {summary['total']}", 30, "bold",
                         score_colour(percentage), theme.CARD).pack(anchor="w")
        theme.make_label(left, f"{percentage:.0f}%   \u00b7   {performance_message(percentage)}",
                         11, "normal", theme.TEXT, theme.CARD, wraplength=360,
                         justify="left").pack(anchor="w", pady=(2, 0))

        buttons = tk.Frame(card, bg=theme.CARD)
        buttons.pack(side="right", padx=20)
        for text, command, kind in actions:
            theme.make_button(buttons, text, command, kind).pack(side="left", padx=4)

        controls = tk.Frame(body, bg=theme.BG)
        controls.pack(fill="x", pady=(14, 4))
        theme.make_label(controls, "Answers and reasons", 14, "bold").pack(side="left")
        self.only_wrong = tk.BooleanVar(value=False)
        tk.Checkbutton(controls, text="Show only the ones I got wrong",
                       variable=self.only_wrong, command=self._render,
                       font=theme.font(10), bg=theme.BG, fg=theme.TEXT,
                       activebackground=theme.BG, selectcolor="white",
                       cursor="hand2").pack(side="right")

        self.scroll = ScrollableFrame(body)
        self.scroll.pack(fill="both", expand=True)
        self._render()

    def _render(self):
        self.scroll.clear()
        if self.only_wrong.get() and all(item["is_correct"] for item in self.items):
            theme.make_label(self.scroll.inner, "Nothing wrong here. Perfect score!", 12,
                             "bold", theme.SUCCESS).pack(pady=30)
            return
        render_review(self.scroll.inner, self.items, self.only_wrong.get())