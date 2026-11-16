"""Extra widgets used by the Quiz, Result and My Progress screens."""

import tkinter as tk

from app.ui import theme

WARNING = "#E8590C"
SUCCESS_BG = "#E6F4EA"
DANGER_BG = "#FDECEC"


def score_colour(percentage):
    """Green for 75% and above, orange for 50%+, red below."""
    if percentage >= 75:
        return theme.SUCCESS
    if percentage >= 50:
        return WARNING
    return theme.DANGER


class ScrollableFrame(tk.Frame):
    """A frame that scrolls vertically. Put your widgets inside `.inner`."""

    def __init__(self, parent, bg=theme.BG):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            window, width=e.width))

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_all("<MouseWheel>", self._on_wheel)

    def _on_wheel(self, event):
        if self.winfo_exists():
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def destroy(self):
        self.unbind_all("<MouseWheel>")
        super().destroy()

    def clear(self):
        for child in self.inner.winfo_children():
            child.destroy()
        self.canvas.yview_moveto(0)


class ClickableRow(tk.Frame):
    """A full-width row: title and small line on the left, a big value on the right."""

    def __init__(self, parent, title, subtitle, value, value_colour, command):
        super().__init__(parent, bg=theme.CARD, highlightthickness=1,
                         highlightbackground=theme.BORDER, cursor="hand2")
        left = tk.Frame(self, bg=theme.CARD)
        left.pack(side="left", padx=18, pady=12)
        self._labels = [
            theme.make_label(left, title, 12, "bold", theme.TEXT, theme.CARD, anchor="w"),
            theme.make_label(left, subtitle, 10, "normal", theme.MUTED, theme.CARD, anchor="w"),
            theme.make_label(self, value, 16, "bold", value_colour, theme.CARD),
        ]
        self._labels[0].pack(anchor="w")
        self._labels[1].pack(anchor="w", pady=(2, 0))
        self._labels[2].pack(side="right", padx=22)

        self._parts = [self, left] + self._labels
        for widget in self._parts:
            widget.bind("<Button-1>", lambda e: command())
            widget.bind("<Enter>", lambda e: self._paint(theme.HOVER))
            widget.bind("<Leave>", lambda e: self._paint(theme.CARD))

    def _paint(self, colour):
        for widget in self._parts:
            widget.config(bg=colour)