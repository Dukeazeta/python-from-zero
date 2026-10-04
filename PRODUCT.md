# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML, CSS and JavaScript generated from lesson sources by `tools/build.py` (standard library only). In-page Python runs in Pyodide (jsDelivr CDN) inside a Web Worker with a 6-second stop. The course app (`app/server.py`, standard library only) serves the pages with clean addresses, stores progress in SQLite (`app/data/course.db`), schedules spaced review, offers optional Sign in with Google, and calls the Gemini Interactions API (key in `.env`). It runs on a learner's own computer or on a small web server (`deploy/`).

## Users

People learning Python from absolute zero, with no other programming language, who want to reach job-ready problem solving. Typically a few hours a week, on a Windows, Mac or Linux computer, sometimes reading on a phone.

## Product Purpose

A self-paced course that takes a total beginner from their first line of Python to solving LeetCode-style algorithm problems and building core CS projects from the project-based-learning list (Game of Life, Tic-Tac-Toe AI, a simple interpreter, Write Yourself a Git). Success is job-ready problem solving and portfolio projects, not finishing pages.

## Positioning

Each lesson is one small, finishable step with a real feedback loop: quizzes answered from memory and Python that actually runs and is checked in the page, followed by the same work done in a real file on the learner's machine.

## Operating Context

Lessons are written once, reviewed by hand and revisited for review; reference sheets are printed or skimmed. RESOURCES.md lists the sources lessons cite. CONTRIBUTING.md holds the writing rules.

## Capabilities and Constraints

- 40 lessons in three tracks: Python basics (1 to 18), Algorithms (19 to 34), Projects (35 to 40). One source file per lesson in content/lessons/; shared components in assets/.
- Every exercise has hidden tests and a reference solution; `tools/verify.py` proves each solution passes and each starter fails (129 exercises at launch).
- AI tutor (Gemini): explain-my-mistake hints, generated practice exercises (validated in the browser before showing), lesson-aware chat. Spaced review uses the quiz bank and works without AI.
- Lesson pages are fixed and human-reviewed; the AI adapts around them and never rewrites them.
- Python exercises need an internet connection the first time a page loads Pyodide.
- Exercise code runs in a Web Worker and is stopped after 6 seconds, so infinite loops can't freeze the page.
- Claims in lessons cite primary sources listed in RESOURCES.md.

## Brand Commitments

- Visual reference: the Heptabase style (https://styles.refero.design/style/7368cfab-6313-4e50-97e5-c3318c52e7fe, from heptabase.com), matched as closely as possible. Recorded in DESIGN.md.
- Voice: plain, direct, encouraging without hype. No em dashes in copy.

## Evidence on Hand

No learner results, testimonials or metrics exist. Never invent progress, scores or quotes.

## Product Principles

1. Assume zero prior knowledge; define every new word the first time it appears.
2. One idea per step, sized to fit in working memory.
3. Feedback is immediate and honest; mistakes are part of the lesson, not failures.
4. Every lesson ties back to the mission: algorithms and core CS projects.
5. Reviewable later: lessons and reference sheets should still read well months on.

## Accessibility & Inclusion

Readable at 390px phone width and on desktop. Keyboard-usable editor and quizzes. Prints cleanly.
