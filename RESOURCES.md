# Python for Core CS Resources

## Knowledge

- [Book: _Automate the Boring Stuff with Python_, 3rd ed., by Al Sweigart, chapter 1 "Python Basics"](https://automatetheboringstuff.com/3e/chapter1.html)
  Free online (Creative Commons). Written for people with no programming experience. Chapter 1 covers expressions, operators, integers, floats and strings, variables, print(), input() and error messages ("Errors are okay!"). Use for: the primary reading in the first beginner lessons, and the vocabulary those lessons use. Verified 2026-10-03. Lesson 0001's quote ("Error messages don't damage your computer...") and its "decades of programming experience" paraphrase were checked word for word against the live page on 2026-10-03; both sit in the section anchored `#calibre_link-1407` ("Entering Expressions into the Interactive Shell"), inside the "Errors Are Okay!" box.
- [The Python Tutorial (official docs)](https://docs.python.org/3/tutorial/index.html)
  The primary source for language syntax and semantics. Use for: every "how does Python do X" question. Chapters 3 to 5 cover nearly everything early algorithm lessons need. Verified 2026-10-03 (docs show Python 3.14; everything in early lessons also works on the local 3.12).
- [Python Tutorial ch. 4: More Control Flow Tools](https://docs.python.org/3/tutorial/controlflow.html)
  `if`/`elif`/`else`, `for`, `range()`, `def`. Use for: Lesson 0001 and any loop or function question. Verified.
- [Project Based Learning: Python section](https://github.com/practical-tutorials/project-based-learning#python)
  The project list the course grew from. For this course only the Miscellaneous section matters (interpreter, Git, blockchain, search engine, Game of Life, Tic-Tac-Toe AI, Snake). Use for: picking portfolio builds once fundamentals and DSA basics are in place. Verified.
- [Robert Heaton: Programming Projects for Advanced Beginners](https://robertheaton.com/2018/12/08/programming-projects-for-advanced-beginners/)
  Index of the Heaton projects in the repo (ASCII art, Game of Life, Tic-Tac-Toe minimax, photomosaics, Snake). Aimed exactly at people past basic exercises. Use for: the first portfolio projects. Verified.
- [LeetCode](https://leetcode.com/problemset/)
  The practice judge. Use for: submitting solutions after solving them locally. Blocks automated fetching, so problem statements in lessons are restated rather than quoted.
- [NeetCode roadmap](https://neetcode.io/roadmap)
  Ordered map of algorithm patterns (NeetCode 150) with video explanations. Use for: sequencing DSA lessons once Python basics are in. Site verified to exist; roadmap contents not yet read.
- [Problem Solving with Algorithms and Data Structures using Python (Miller and Ranum, Runestone)](https://runestone.academy/ns/books/published/pythonds3/index.html)
  Free interactive textbook on DSA in Python. Main reading for the algorithms track (Lessons 19 to 34): Big O, stacks, queues, recursion, sorting, linked lists, trees, heaps, graphs, DP. Table of contents and chapter pages verified 2026-10-04.
- [Python Wiki: TimeComplexity](https://wiki.python.org/moin/TimeComplexity)
  Costs of list, set and dict operations in CPython. Use for: any Big O claim about built-in operations. Verified 2026-10-04.
- [Pro Git book](https://git-scm.com/book/en/v2) and [GitHub Docs](https://docs.github.com/en/get-started/start-your-journey/hello-world)
  Lesson 35 (Git and GitHub) and Lesson 40 (Git internals). Verified 2026-10-04.
- Project briefs from the project-based-learning list, all verified 2026-10-04: [Robert Heaton's Game of Life](https://robertheaton.com/2018/07/20/project-2-game-of-life/), [Tic-Tac-Toe AI 3a](https://robertheaton.com/2018/10/09/programming-projects-for-advanced-beginners-3-a/) and [3b](https://robertheaton.com/2018/10/09/programming-projects-for-advanced-beginners-3-b/), [Snake](https://robertheaton.com/2018/12/02/programming-project-5-snake/), [Ruslan Spivak's Let's Build A Simple Interpreter](https://ruslanspivak.com/lsbasi-part1/) (parts 1 to 6), [Write yourself a Git](https://wyag.thb.lt/).
- [Gemini API docs: Interactions API and models](https://ai.google.dev/gemini-api/docs/interactions)
  For maintaining the course app's tutor (app/gemini.py). Current recommended model at build time: gemini-3.8-flash. Verified 2026-10-04.

## Wisdom (Communities)

- [Python Discord](https://www.pythondiscord.com/)
  Large, moderated, beginner-friendly server with dedicated help channels and 100+ volunteer Helpers. Use for: getting code reviewed, being stuck on a concept. Verified.
- [r/learnpython](https://www.reddit.com/r/learnpython/)
  Beginner Python subreddit. Use for: "is this idiomatic?" questions. Blocks automated fetching.
- LeetCode problem Discussion / Solutions tabs
  Use for: comparing your solution against others after you have solved it yourself.

## Gaps
- NeetCode roadmap contents can't be read by automated fetches; lessons link to it without quoting its topic order.
- LeetCode problem pages block automated fetches; problem statements in lessons are restated, not quoted, and checked against well-known examples.
