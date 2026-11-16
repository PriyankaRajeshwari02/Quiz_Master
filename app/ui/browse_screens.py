"""Semester -> Subject -> Module -> Test list screens.

Each screen receives the rows chosen on the earlier screens (as plain dicts)
so it can draw its breadcrumb and its Back button.
"""
import tkinter as tk

from app import database, results
from app.quiz import QUESTIONS_PER_TEST, TEST_COUNT
from app.ui import theme
from app.ui.theme import BaseScreen, Tile


def _title(body, text, subtitle=""):
    theme.make_label(body, text, 20, "bold").pack(anchor="w")
    if subtitle:
        theme.make_label(body, subtitle, 11, color=theme.MUTED).pack(anchor="w", pady=(2, 0))
    spacer = tk.Frame(body, bg=theme.BG, height=14)
    spacer.pack()


def _count_text(count):
    return f"{count} questions" if count else "Coming soon"


class SemesterScreen(BaseScreen):
    COLUMNS = 4

    def __init__(self, parent, app):
        super().__init__(parent, app)
        body = self.build_header()
        _title(body, "Choose your semester",
               "Semesters without questions yet are marked Coming soon.")

        grid = tk.Frame(body, bg=theme.BG)
        grid.pack(fill="x")
        for column in range(self.COLUMNS):
            grid.grid_columnconfigure(column, weight=1, uniform="semester")

        for index, row in enumerate(database.get_semesters()):
            semester = dict(row)
            has_content = semester["question_count"] > 0
            tile = Tile(grid, semester["name"], _count_text(semester["question_count"]),
                        command=lambda s=semester: app.show_subjects(s),
                        enabled=has_content, align="center")
            tile.grid(row=index // self.COLUMNS, column=index % self.COLUMNS,
                      padx=8, pady=8, sticky="nsew")


class SubjectScreen(BaseScreen):
    def __init__(self, parent, app, semester):
        super().__init__(parent, app)
        body = self.build_header(crumbs=semester["name"], back=app.show_semesters)
        _title(body, f"{semester['name']}: choose a subject")

        for row in database.get_subjects(semester["semester_id"]):
            subject = dict(row)
            has_content = subject["question_count"] > 0
            Tile(body, f"{subject['code']}   {subject['name']}",
                 _count_text(subject["question_count"]),
                 command=lambda s=subject: app.show_modules(semester, s),
                 enabled=has_content).pack(fill="x", pady=5)


class ModuleScreen(BaseScreen):
    def __init__(self, parent, app, semester, subject):
        super().__init__(parent, app)
        crumbs = f"{semester['name']}  \u203a  {subject['name']}"
        body = self.build_header(crumbs=crumbs, back=lambda: app.show_subjects(semester))
        _title(body, f"{subject['name']}: choose a module")

        for row in database.get_modules(subject["subject_id"]):
            module = dict(row)
            # A module needs at least one full test worth of questions.
            playable = module["question_count"] >= QUESTIONS_PER_TEST
            Tile(body, f"Module {module['module_number']}:  {module['title']}",
                 _count_text(module["question_count"]),
                 command=lambda m=module: app.show_tests(semester, subject, m),
                 enabled=playable).pack(fill="x", pady=5)


class TestListScreen(BaseScreen):
    COLUMNS = 5

    def __init__(self, parent, app, semester, subject, module):
        super().__init__(parent, app)
        crumbs = (f"{semester['name']}  \u203a  {subject['name']}  \u203a  "
                  f"Module {module['module_number']}")
        body = self.build_header(
            crumbs=crumbs, back=lambda: app.show_modules(semester, subject))
        _title(body, module["title"],
               f"{TEST_COUNT} mock tests, {QUESTIONS_PER_TEST} questions each "
               f"(pool of {module['question_count']} questions).")

        status = results.get_test_status(app.user["user_id"], module["module_id"])

        grid = tk.Frame(body, bg=theme.BG)
        grid.pack(fill="x")
        for column in range(self.COLUMNS):
            grid.grid_columnconfigure(column, weight=1, uniform="test")

        for number in range(1, TEST_COUNT + 1):
            info = status.get(number)
            if info:
                times = "time" if info["attempts"] == 1 else "times"
                subtitle = f"Best {info['best']:.0f}%  \u00b7  taken {info['attempts']} {times}"
            else:
                subtitle = "Not attempted"
            tile = Tile(grid, f"Test {number}", subtitle,
                        command=lambda n=number: app.start_quiz(semester, subject, module, n),
                        align="center")
            tile.grid(row=(number - 1) // self.COLUMNS, column=(number - 1) % self.COLUMNS,
                      padx=8, pady=8, sticky="nsew")