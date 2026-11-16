"""Admin screens. For now only a placeholder; the real panel comes later."""

from app.ui import theme
from app.ui.theme import BaseScreen


class AdminPlaceholderScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        body = self.build_header()
        theme.make_label(body, "Admin dashboard", 20, "bold").pack(anchor="w")
        theme.make_label(
            body,
            "You are logged in as an admin.\n"
            "Adding and editing questions from inside the app is coming in a later step.\n"
            "For now, add questions through the JSON files in data/syllabus.",
            11, color=theme.MUTED, justify="left").pack(anchor="w", pady=(8, 0))