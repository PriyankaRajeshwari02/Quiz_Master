"""Colours, fonts and small widgets shared by every screen.

Every screen builds itself from the helpers in this file, so changing a
colour here changes the whole app.
"""

import sys
import tkinter as tk

BG = "#F4F6FB"
CARD = "#FFFFFF"
PRIMARY = "#3B5BDB"
PRIMARY_DARK = "#2F4AC0"
HOVER = "#EEF2FF"
TEXT = "#1F2937"
MUTED = "#6B7280"
SUCCESS = "#2F9E44"
DANGER = "#E03131"
BORDER = "#D9DEE8"
DISABLED_BG = "#E9ECF2"
DISABLED_FG = "#9AA1AE"

FONT_FAMILY = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"


def font(size=11, weight="normal"):
    return (FONT_FAMILY, size, weight)


def make_label(parent, text, size=11, weight="normal", color=TEXT, bg=None, **options):
    return tk.Label(parent, text=text, font=font(size, weight), fg=color,
                    bg=bg or parent.cget("bg"), **options)


_BUTTON_STYLES = {
    "primary": {"bg": PRIMARY, "fg": "white", "hover": PRIMARY_DARK, "border": PRIMARY},
    "secondary": {"bg": CARD, "fg": PRIMARY, "hover": "#E7ECFF", "border": BORDER},
}


def make_button(parent, text, command, kind="primary"):
    style = _BUTTON_STYLES[kind]
    button = tk.Button(
        parent, text=text, command=command, font=font(11, "bold"),
        bg=style["bg"], fg=style["fg"],
        activebackground=style["hover"], activeforeground=style["fg"],
        relief="flat", bd=0, padx=18, pady=9, cursor="hand2",
        highlightthickness=1, highlightbackground=style["border"])
    button.bind("<Enter>", lambda e: button.config(bg=style["hover"]))
    button.bind("<Leave>", lambda e: button.config(bg=style["bg"]))
    return button


def make_entry(parent, show=None):
    return tk.Entry(
        parent, font=font(12), show=show or "", relief="flat", bg="white",
        fg=TEXT, insertbackground=TEXT, highlightthickness=1,
        highlightbackground=BORDER, highlightcolor=PRIMARY, width=32)


def make_card(parent):
    return tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER)


def labeled_entry(parent, text, show=None):
    """A small caption with a text box under it. Returns the Entry."""
    make_label(parent, text, 10, "bold", MUTED, CARD).pack(anchor="w")
    entry = make_entry(parent, show)
    entry.pack(fill="x", ipady=6, pady=(2, 12))
    return entry


class Tile(tk.Frame):
    """A clickable card with a title and a small line under it.

    Used for semesters, subjects, modules and tests. A disabled tile is
    greyed out and ignores clicks (used for 'Coming soon').
    """

    def __init__(self, parent, title, subtitle="", command=None,
                 enabled=True, align="w"):
        self._normal_bg = CARD if enabled else DISABLED_BG
        super().__init__(parent, bg=self._normal_bg, highlightthickness=1,
                         highlightbackground=BORDER,
                         cursor="hand2" if enabled else "arrow")
        self.command = command
        self.enabled = enabled
        self.title_text = title

        anchor = "w" if align == "w" else "center"
        justify = "left" if align == "w" else "center"
        title_color = TEXT if enabled else DISABLED_FG
        sub_color = MUTED if enabled else DISABLED_FG

        wrap = 260 if align != "w" else 640
        self._labels = [make_label(self, title, 13, "bold", title_color, self._normal_bg,
                                   wraplength=wrap, justify=justify, anchor=anchor)]
        sub = None
        if subtitle:
            sub = make_label(self, subtitle, 10, "normal", sub_color, self._normal_bg,
                             wraplength=wrap, justify=justify, anchor=anchor)
            self._labels.append(sub)

        if align == "w":
            # One compact row: title on the left, the small note on the right.
            self._labels[0].pack(side="left", padx=18, pady=14)
            if sub:
                sub.pack(side="right", padx=18, pady=14)
        else:
            self._labels[0].pack(anchor=anchor, padx=18, pady=(16, 2 if sub else 16), fill="x")
            if sub:
                sub.pack(anchor=anchor, padx=18, pady=(0, 16), fill="x")

        if enabled:
            for widget in [self] + self._labels:
                widget.bind("<Button-1>", self._on_click)
                widget.bind("<Enter>", lambda e: self._paint(HOVER))
                widget.bind("<Leave>", lambda e: self._paint(self._normal_bg))

    def _paint(self, colour):
        self.config(bg=colour)
        for label in self._labels:
            label.config(bg=colour)

    def _on_click(self, _event):
        if self.enabled and self.command:
            self.command()


class BaseScreen(tk.Frame):
    """Parent class of every screen: gives it the top bar and a body area."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.body = None

    def build_header(self, crumbs="", back=None):
        """Top bar (name, My Progress, Logout), optional Back + breadcrumb.

        Returns the empty body frame for the screen to fill.
        """
        bar = tk.Frame(self, bg=PRIMARY)
        bar.pack(fill="x")
        make_label(bar, "QuizMaster", 16, "bold", "white", PRIMARY).pack(
            side="left", padx=24, pady=14)

        user = self.app.user
        if user:
            self._bar_button(bar, "Logout", self.app.logout)
            if user["role"] == "student":
                self._bar_button(bar, "My Progress", self.app.show_progress)
            make_label(bar, f"Hi, {user['full_name']}", 11, "normal",
                       "white", PRIMARY).pack(side="right", padx=12)

        if crumbs or back:
            nav = tk.Frame(self, bg=BG)
            nav.pack(fill="x", padx=40, pady=(18, 0))
            if back:
                make_button(nav, "\u2190 Back", back, "secondary").pack(
                    side="left", padx=(0, 14))
            make_label(nav, crumbs, 11, color=MUTED).pack(side="left")

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=40, pady=20)
        return self.body

    @staticmethod
    def _bar_button(bar, text, command):
        button = tk.Button(bar, text=text, command=command, font=font(10, "bold"),
                           bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK,
                           activeforeground="white", relief="flat", bd=0,
                           padx=12, pady=6, cursor="hand2")
        button.pack(side="right", padx=(0, 18))
        return button