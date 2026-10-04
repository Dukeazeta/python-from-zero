"""Check every exercise in the built lessons.

For each exercise with tests, this runs the reference solution through the same test
harness the browser uses (copied out of assets/pyrunner.js) and confirms that:
  - the solution passes every test, and
  - the starter code does NOT pass (so the exercise actually asks for something).

Run:  python tools/verify.py            (all lessons)
      python tools/verify.py 0005 0006  (some lessons)
"""

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_harness():
    js = (ROOT / "assets" / "pyrunner.js").read_text(encoding="utf-8")
    block = js.split("/*HARNESS-START*/", 1)[1].split("/*HARNESS-END*/", 1)[0]
    code = re.search(r"String\.raw`(.*?)`;", block, re.S).group(1)
    ns = {}
    exec(code, ns)
    return ns["_session"]




def exercises(page):
    for m in re.finditer(r'<div class="canvas exercise" id="([\w-]+)"([^>]*)>', page):
        ex_id, attrs = m.group(1), m.group(2)
        rest = page[m.end():]
        starter = re.search(r'<textarea class="code"[^>]*>(.*?)</textarea>', rest, re.S)
        tests = re.search(r'<script type="text/python" class="tests">(.*?)</script>', rest, re.S)
        solution = re.search(r'<script type="text/python" class="solution">(.*?)</script>', rest, re.S)
        setup = re.search(r'<script type="text/python" class="setup">(.*?)</script>', rest, re.S)
        nxt = re.search(r'<div class="canvas exercise"', rest)
        limit = nxt.start() if nxt else len(rest)
        inputs = re.search(r"data-inputs='([^']*)'", attrs)
        yield {
            "id": ex_id,
            "starter": html.unescape(starter.group(1)) if starter and starter.start() < limit else "",
            "tests": tests.group(1) if tests and tests.start() < limit else None,
            "solution": solution.group(1).strip("\n") + "\n" if solution and solution.start() < limit else None,
            "inputs": json.loads(html.unescape(inputs.group(1))) if inputs else [],
            "setup": setup.group(1).strip("\n") + "\n" if setup and setup.start() < limit else None,
        }


def passes(session, src, inputs, tests, setup=None):
    res = json.loads(session(src, json.dumps(inputs), tests, setup))
    ok = res["err"] is None and res["results"] and all(r["ok"] for r in res["results"])
    return ok, res


def main(only):
    session = load_harness()
    problems, count = [], 0
    for page_path in sorted((ROOT / "lessons").glob("*.html")):
        lesson_id = page_path.name[:4]
        if only and lesson_id not in only:
            continue
        page = page_path.read_text(encoding="utf-8")
        for ex in exercises(page):
            if ex["tests"] is None:
                continue
            count += 1
            label = f"{page_path.name} #{ex['id']}"
            if ex["solution"] is None:
                problems.append(f"{label}: no reference solution")
                continue
            ok, res = passes(session, ex["solution"], ex["inputs"], ex["tests"], ex["setup"])
            if not ok:
                detail = res["err"] or [r for r in res["results"] if not r["ok"]]
                problems.append(f"{label}: solution FAILS: {detail}")
            ok_starter, _ = passes(session, ex["starter"], ex["inputs"], ex["tests"], ex["setup"])
            if ok_starter:
                problems.append(f"{label}: starter already passes the tests")
    for p in problems:
        print("PROBLEM", p)
    print(f"Checked {count} exercises: {count - len(problems)} fine, {len(problems)} problem(s).")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(set(sys.argv[1:])))
