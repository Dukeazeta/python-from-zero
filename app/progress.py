"""One person's progress: a JSON document kept in the course database (see store.py).

Tracks:
  lessons    when each lesson was started and finished, and how each exercise went
  cards      one card per quiz question, for spaced review (a Leitner box system)
  mistakes   recent wrong answers, failed checks and errors, which the tutor uses
  chats      the conversation with the tutor on each lesson
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

# Days until a question comes back, by box. Right on the first try moves a card up a
# box (longer gap); a wrong pick sends it back to box 1 (comes back tomorrow).
INTERVALS = {1: 1, 2: 3, 3: 7, 4: 16, 5: 35}
MAX_MISTAKES = 300
MAX_CHAT = 40
SECTIONS = {"lessons": dict, "cards": dict, "mistakes": list, "chats": dict}


def today():
    return date.today().isoformat()


def now():
    return datetime.now().isoformat(timespec="seconds")


def normalise(data):
    """Fill in missing sections, and reject anything that isn't a progress document."""
    if not isinstance(data, dict):
        raise ValueError("That isn't a progress file.")
    for key, kind in SECTIONS.items():
        data.setdefault(key, kind())
        if not isinstance(data[key], kind):
            raise ValueError("That isn't a progress file.")
    return data


def load_file(path):
    """Read an old-style progress.json (from before accounts), or None if there isn't one."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        return normalise(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, ValueError):
        return None


class Progress:
    """Wraps a progress document. `saver` is called with the document after every change."""

    def __init__(self, data, saver=None):
        self.data = normalise(data)
        self.saver = saver

    def save(self):
        if self.saver:
            self.saver(self.data)

    def lesson(self, lesson_id):
        return self.data["lessons"].setdefault(lesson_id, {"started": now(), "exercises": {}, "quizzes": {}})

    # ---------- Recording events ----------
    def record_exercise(self, ev):
        lesson = self.lesson(ev["lesson"])
        ex = lesson["exercises"].setdefault(ev["id"], {"attempts": 0, "solved": None, "practice": bool(ev.get("practice"))})
        if ev.get("kind") == "check":
            ex["attempts"] += 1
            if ev.get("passed") and not ex["solved"]:
                ex["solved"] = now()
        failed = ev.get("kind") == "check" and not ev.get("passed")
        if failed or ev.get("error"):
            self._mistake(ev["lesson"], "exercise", ev["id"], describe_failure(ev))
        self.save()

    def record_quiz(self, ev):
        qid = ev.get("qid")
        if not qid:
            return
        first_try = bool(ev.get("firstTry"))
        if not ev.get("review"):
            self.lesson(ev["lesson"])["quizzes"][qid] = {"firstTry": first_try, "at": now()}
        card = self.data["cards"].get(qid)
        if card is None:
            box = 2 if first_try else 1
        elif ev.get("review") or card["due"] <= today():
            box = min(card["box"] + 1, 5) if first_try else 1
        else:
            box = card["box"]
        due = (date.today() + timedelta(days=INTERVALS[box])).isoformat()
        hist = (card or {}).get("history", [])[-9:] + [{"at": now(), "firstTry": first_try}]
        self.data["cards"][qid] = {"box": box, "due": due, "lesson": qid.split("-")[0], "history": hist}
        if not first_try:
            picks = ", ".join(ev.get("wrongPicks") or [])
            self._mistake(qid.split("-")[0], "quiz", qid, f"Quiz: \"{ev.get('question', '')[:160]}\" picked wrong answer(s): {picks}")
        self.save()

    def record_paste(self, ev):
        if not ev.get("pass"):
            self._mistake(ev["lesson"], "terminal", ev.get("id", ""), f"Terminal output didn't match. {ev.get('why', '')} Pasted: {ev.get('pasted', '')[:300]}")
            self.save()

    def _mistake(self, lesson_id, kind, item, detail):
        self.data["mistakes"].append({"at": now(), "lesson": lesson_id, "kind": kind, "item": item, "detail": detail[:600]})
        del self.data["mistakes"][:-MAX_MISTAKES]

    def complete(self, lesson_id):
        lesson = self.lesson(lesson_id)
        first = not lesson.get("completed")
        lesson["completed"] = lesson.get("completed") or now()
        self.save()
        return first

    # ---------- Reading ----------
    def due_cards(self, current_lesson, limit=4):
        due = [(qid, c) for qid, c in self.data["cards"].items()
               if c["due"] <= today() and c.get("lesson") != current_lesson]
        due.sort(key=lambda item: (item[1]["box"], item[1]["due"]))
        return [qid for qid, _ in due[:limit]]

    def recent_mistakes(self, lesson_id=None, limit=15):
        items = self.data["mistakes"]
        if lesson_id:
            items = [m for m in items if m["lesson"] <= lesson_id]
        return items[-limit:]

    def completed(self):
        return sorted(k for k, v in self.data["lessons"].items() if v.get("completed"))

    def chat(self, lesson_id):
        return self.data["chats"].setdefault(lesson_id, [])

    def add_chat(self, lesson_id, role, text):
        log = self.chat(lesson_id)
        log.append({"role": role, "text": text, "at": now()})
        del log[:-MAX_CHAT]
        self.save()

    def lesson_summary(self, lesson_id):
        lesson = self.data["lessons"].get(lesson_id, {})
        exercises = lesson.get("exercises", {})
        quizzes = lesson.get("quizzes", {})
        return {
            "started": lesson.get("started"),
            "completed": lesson.get("completed"),
            "exercises": exercises,
            "quizzes_first_try": sum(1 for q in quizzes.values() if q["firstTry"]),
            "quizzes_answered": len(quizzes),
            "mistakes": [m for m in self.data["mistakes"] if m["lesson"] == lesson_id][-20:],
        }


def describe_failure(ev):
    if ev.get("error"):
        last = ev["error"].strip().splitlines()[-1] if ev["error"].strip() else ev["error"]
        return f"Exercise {ev['id']}: error {last}"
    fails = [r for r in (ev.get("results") or []) if not r.get("ok")]
    if fails:
        f = fails[0]
        if f.get("error"):
            return f"Exercise {ev['id']}: test '{f['label']}' crashed: {f['error'].strip().splitlines()[-1]}"
        return f"Exercise {ev['id']}: test '{f['label']}' expected {f['expected']} but got {f['got']}"
    return f"Exercise {ev['id']}: didn't pass"
