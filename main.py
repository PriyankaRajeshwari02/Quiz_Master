"""QuizMaster entry point. Run with:  python main.py"""

from app import database, importer
from app.ui.app import QuizApp


def main():
    database.init_db()                       # create tables on first run
    for report in importer.import_all():     # load/refresh data/syllabus/*.json
        for line in report["errors"]:
            print("IMPORT ERROR:", line)
    QuizApp().mainloop()


if __name__ == "__main__":
    main()