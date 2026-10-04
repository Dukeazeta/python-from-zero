# Contributing

Fixes, clearer explanations, new exercises and bug reports are all welcome. Open an issue first for anything big, such as a new lesson or a change to how the app works.

## How the lessons are written

The course is for people who have never programmed, so the writing follows a few firm rules:

- **Comparison first, term second.** Each new idea opens with an everyday, real-life comparison in an "In real life" box (`<div class="analogy">`), before the technical word or any code.
- **Assume nothing.** Define every new word the first time it's used, and add it to that section's "New words" list. No "if you know JavaScript" comparisons.
- **Only point back to what was taught.** Write "from Lesson N" only if Lesson N really covers it. If a lesson needs something new, introduce it there.
- **Plain and short.** Short sentences, plain words, British spelling. No em dashes. No hype ("the key insight", "the heart of", "powerful"), no closing lines that repeat the point, and no praise like "Nice work". The AI tutor follows the same rules (see `STYLE` in `app/tutor.py`).
- **Cite what you rely on.** Facts that come from a source get a `{{cite:N}}` pointing at the lesson's source list.
- **Every operating system.** Write terminal steps for Windows and let the build add Mac and Linux versions (see below), or mark text with `data-os="windows"`, `data-os="mac"` or `data-os="linux"`.
- **LeetCode problems are restated** in our own words, never copied.

## Editing a lesson

Lesson sources are in `content/lessons/NNNN-slug.html`. Don't edit `lessons/`, which is generated. Each source starts with a `<!--meta ... -->` block (title, intro, minutes, concepts, sources) and is made of `<section id="..." data-nav="Label">` blocks. The docstring at the top of `tools/build.py` describes the format.

Shortcuts inside a lesson:

| Write | Becomes |
|---|---|
| `{{cite:2}}` | a link to source 2 in the lesson's source list |
| `{{lesson:0005}}` | a link to Lesson 5, with its title |
| `{{py}}` | `python` on Windows, `python3` on Mac and Linux |
| `{{venv-py}}` | `.venv\Scripts\python` or `.venv/bin/python` |
| `{{mod}}` | Ctrl, or Cmd on a Mac |
| `{{os-switch}}` | a Windows / Mac / Linux switch |

Terminal lines written for Windows, with a prompt like `<span class="prompt">...folder&gt;</span>`, get Mac and Linux versions automatically.

## Exercises

An exercise is a `<div class="canvas exercise">` with a starter in a `<textarea class="code">`, tests in `<script type="text/python" class="tests">` (one `check(label, got, expected)` per line), and a reference solution in `<script type="text/python" class="solution">`. The comment at the top of `assets/pyrunner.js` lists the test helpers: `printed()`, `source()`, `run([...])`, plus optional setup code and input lines.

Every exercise needs a solution that passes its tests and a starter that doesn't. `tools/verify.py` checks both.

## Building and testing

```bash
python tools/build.py      # rebuild lessons/, index.html and the app's lesson data
python tools/verify.py     # every exercise: solution passes, starter fails
python tools/test_app.py   # the server end to end, with a stand-in for Google sign-in
```

Run all three before opening a pull request. To try the app without a Gemini key, start it with `TUTOR_FAKE_AI=1` (canned tutor replies) and `COURSE_DATA_DIR=.test-data` (a throwaway database).

The app uses only Python's standard library. Please keep it that way, so anyone can run it with nothing to install.
