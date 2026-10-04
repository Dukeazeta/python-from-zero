# Python from zero

A free, 40-lesson course that takes someone who has never programmed to solving LeetCode-style algorithm problems and building portfolio projects. Python runs right in the browser, and an optional AI tutor (Google Gemini) explains mistakes, writes extra practice and answers questions.

Every idea opens with an everyday comparison before the technical word, and the writing is kept short and plain.

## What's inside

- **Python basics (Lessons 1 to 18):** values and maths, the terminal, variables, input, decisions, loops, lists, strings, functions, dictionaries, sets, debugging, grids, classes, and modules with virtual environments.
- **Algorithms (19 to 34):** Big O, then one lesson per pattern: hashing, two pointers, sliding window, stacks, binary search, recursion, sorting, linked lists, trees, BFS, heaps, graphs, backtracking and dynamic programming. About 45 real LeetCode problems, in LeetCode's own format.
- **Projects (35 to 40):** Git and GitHub, Conway's Game of Life, an unbeatable Tic-Tac-Toe AI (minimax), Snake in the terminal, a small interpreter, and your own mini Git.
- **Reference sheets** for the basics and the algorithm patterns.

## Features

- **Exercises that check themselves:** 129 exercises run real Python in the browser through [Pyodide](https://pyodide.org) and are tested on the spot. Nothing to install for the first lessons.
- **Spaced review:** quiz questions come back as warm-ups, sooner if you got them wrong.
- **AI tutor (optional):** "Explain my mistake" gives hints, not answers; personal practice sets are aimed at your recent mistakes, and each one is checked by running it before you see it; plus a chat on every lesson. Replies stream in as they're written.
- **Accounts (optional):** Sign in with Google, so progress follows you between devices. Without it, progress is saved on your own computer.
- **Windows, Mac and Linux:** terminal lessons show the right steps for your computer.
- **Light and dim themes**, readable on phones, and no tracking.
- **Small and dependency free:** the app is about 1,500 lines of Python using only the standard library, with SQLite for storage.

## Quick start

You need Python 3.12 or newer.

```bash
git clone https://github.com/Dukeazeta/python-from-zero.git
cd python-from-zero
python app/server.py          # Mac and Linux: python3 app/server.py
```

The course opens at http://localhost:8765. On Windows you can also double-click `Start Python from zero.bat`.

**To turn on the AI tutor**, copy `.env.example` to `.env`, put a key from [Google AI Studio](https://aistudio.google.com/apikey) in `GEMINI_API_KEY`, and restart the app. The key stays on the server and is never sent to the browser.

## Going further

- [docs/sign-in.md](docs/sign-in.md): add Sign in with Google.
- [docs/deploy-google-cloud.md](docs/deploy-google-cloud.md): put the course online on Google Cloud's free tier, with https, daily backups and a launch checklist.
- [CONTRIBUTING.md](CONTRIBUTING.md): how lessons are written, built and tested.

## How it's put together

| Path | What |
|---|---|
| `content/lessons/` | Lesson sources. Edit these, then run `python tools/build.py`. |
| `lessons/`, `index.html` | Pages generated from the sources. |
| `reference/` | Printable reference sheets. |
| `assets/` | Styles and scripts: in-browser Python (`pyrunner.js`), quizzes, the tutor and account menu (`tutor.js`), themes, and the Windows/Mac/Linux switch. |
| `app/` | The course server: lessons, progress (`store.py`, SQLite), Google sign-in (`auth.py`), the tutor's prompts (`tutor.py`) and the Gemini client (`gemini.py`). |
| `tools/` | `build.py` builds the pages, `verify.py` checks every exercise, and `test_app.py` tests the server end to end. |
| `deploy/` | Packing and installing on a Linux server. |
| `privacy.html`, `terms.html` | Drafts to fill in before running a public copy. |

```bash
python tools/build.py      # rebuild pages after editing lessons
python tools/verify.py     # every exercise's solution passes and its starter doesn't
python tools/test_app.py   # sign-in, accounts, limits and security, against a stand-in for Google
```

## Running your own copy

The site's footer links to the author's X profile, and the preview card's details are at the top of `assets/profile-card.js`. Change them, along with the bracketed details in `privacy.html` and `terms.html`, if you host the course yourself.

## Credits

The lessons are original writing that points learners to these free resources, each cited where it's used: [Automate the Boring Stuff with Python](https://automatetheboringstuff.com/3e/) by Al Sweigart, [the official Python tutorial](https://docs.python.org/3/tutorial/), [Problem Solving with Algorithms and Data Structures using Python](https://runestone.academy/ns/books/published/pythonds3/index.html) by Miller and Ranum, [Pro Git](https://git-scm.com/book/en/v2), Robert Heaton's [Programming Projects for Advanced Beginners](https://robertheaton.com/2018/12/08/programming-projects-for-advanced-beginners/), Ruslan Spivak's [Let's Build A Simple Interpreter](https://ruslanspivak.com/lsbasi-part1/) and [Write yourself a Git](https://wyag.thb.lt/). The projects come from the [Project Based Learning](https://github.com/practical-tutorials/project-based-learning) list. LeetCode problem statements are restated in the course's own words.

The visual style is inspired by [Heptabase](https://heptabase.com).

## License

- **Code** (everything outside `content/`, `lessons/` and `reference/`): [MIT](LICENSE).
- **Lessons and reference sheets:** [CC BY-NC-SA 4.0](LICENSE-CONTENT.md). Share and adapt them with credit, not for commercial use, and under the same license.

Made by [Duke Azeta](https://x.com/_dukedev).
