"""My Progress: your statistics and every test you have taken."""

import tkinter as tk
from datetime import datetime

from app import results
from app.ui import theme
from app.ui.theme import BaseScreen
from app.ui.widgets import ClickableRow, ScrollableFrame, score_colour


def _pretty_date(iso_text):
    try:
        return datetime.fromisoformat(iso_text).strftime("%d %b %Y, %I:%M %p")
    except ValueError:
        return iso_text


def _stat_card(parent, label, value):
    card = theme.make_card(parent)
    theme.make_label(card, value, 20, "bold", theme.PRIMARY, theme.CARD).pack(
        padx=20, pady=(14, 0))
    theme.make_label(card, label, 10, "normal", theme.MUTED, theme.CARD).pack(
        padx=20, pady=(0, 14))
    return card


class ProgressScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        body = self.build_header(crumbs="My Progress", back=app.show_semesters)
        theme.make_label(body, "My Progress", 20, "bold").pack(anchor="w", pady=(0, 10))

        attempts = [dict(row) for row in results.get_user_attempts(app.user["user_id"])]
        if not attempts:
            theme.make_label(
                body, "You have not taken any test yet.\n"
                      "Pick a semester, open a module and take your first test.",
                11, color=theme.MUTED, justify="left").pack(anchor="w")
            return

        average = sum(a["percentage"] for a in attempts) / len(attempts)
        best = max(a["percentage"] for a in attempts)
        modules = len({(a["subject_code"], a["module_number"]) for a in attempts})

        stats = tk.Frame(body, bg=theme.BG)
        stats.pack(fill="x", pady=(0, 14))
        for column in range(4):
            stats.grid_columnconfigure(column, weight=1, uniform="stat")
        for column, (label, value) in enumerate([
                ("Tests taken", str(len(attempts))),
                ("Average score", f"{average:.0f}%"),
                ("Best score", f"{best:.0f}%"),
                ("Modules practised", str(modules))]):
            _stat_card(stats, label, value).grid(row=0, column=column, padx=6, sticky="nsew")

        theme.make_label(body, "Click any test to see its answers and reasons again",
                         10, color=theme.MUTED).pack(anchor="w", pady=(0, 6))
        scroll = ScrollableFrame(body)
        scroll.pack(fill="both", expand=True)
        for attempt in attempts:
            ClickableRow(
                scroll.inner,
                title=f"{attempt['subject_code']}  \u00b7  Module {attempt['module_number']}: "
                      f"{attempt['module_title']}",
                subtitle=f"Test {attempt['test_number']}   \u00b7   "
                         f"{_pretty_date(attempt['taken_at'])}   \u00b7   "
                         f"{attempt['score']}/{attempt['total']}",
                value=f"{attempt['percentage']:.0f}%",
                value_colour=score_colour(attempt["percentage"]),
                command=lambda a=attempt: app.show_attempt(a),
            ).pack(fill="x", pady=4, padx=(0, 4))