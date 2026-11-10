# QuizMaster

QuizMaster is a desktop quiz application for a college practical. A student enters a name, chooses one subject, answers multiple-choice questions one at a time, and sees a score at the end. Every completed attempt is stored in a local SQLite database.

## Features

- Welcome screen with a student name field
- Three categories: Python Programming, Database Management System (DBMS), and Computer Networks
- One question at a time, with four options and a single selection
- The Next button stays on the current question until an option is selected
- Automatic score, percentage, and a short performance message
- Local `questions.db` file created automatically on first launch
- Sample questions inserted only when the questions table is empty
- Restart and Exit buttons on the result screen

## Technology stack

- Python 3
- Tkinter for the graphical interface
- SQLite3 for database storage
- SQL for creating tables, inserting data, and reading data

No external packages are required. Tkinter and SQLite3 come with a standard Python installation.

## Project structure

```text
QuizMaster/
    main.py         Application window and screens
    database.py     Database creation, questions, and saved results
    quiz.py         Answer checking and score calculation
    README.md       This file
    questions.db    Created automatically when the app starts
```

## How to run on Windows

1. Install Python 3 from [python.org](https://www.python.org/downloads/windows/) if it is not already installed. During setup, keep **tcl/tk and IDLE** selected so Tkinter is available.
2. Open PowerShell or Command Prompt.
3. Move into this project folder and start the app:

```powershell
cd C:\Users\priya\Quiz_Master
python main.py
```

If the `python` command is not recognized, use the Windows launcher instead:

```powershell
py -3 main.py
```

You can also run the file by its full path:

```powershell
python C:\Users\priya\Quiz_Master\main.py
```

The database file is created beside `main.py`. The current folder does not change where `questions.db` is stored.

## How a quiz works

1. Enter a name and click **Start Quiz**.
2. Select one category and click **Continue**.
3. Choose one option and click **Next**. The last question uses **Submit**.
4. Read the result. Click **Restart Quiz** for another attempt, or **Exit** to close the window.
