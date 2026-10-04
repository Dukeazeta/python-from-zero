"""Build the course pages from the lesson content files.

Each lesson lives in content/lessons/NNNN-slug.html as a fragment:

    <!--meta
    { "title": "...", "nav_title": "...", "track": "Python basics", "intro": "...",
      "minutes": 30, "needs": "...", "summary": "...", "concepts": ["..."],
      "sources": [{"title": "...", "url": "...", "note": "..."}] }
    -->
    <section id="topic" data-nav="Label"> ... </section>

Inside a fragment:
    {{cite:2}}          a superscript link to source 2 in the meta list
    {{lesson:0005}}     a link to lesson 0005, using its title

The builder writes lessons/NNNN-slug.html, index.html, and the data the course
app uses (app/data/curriculum.json, app/data/quizbank.json).

Run:  python tools/build.py
"""

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "lessons"
OUT = ROOT / "lessons"
DATA = ROOT / "app" / "data"

TRACKS = [
    ("Python basics", "From your first line of code to writing your own functions."),
    ("Algorithms", "How to think about speed, and the patterns behind most interview problems."),
    ("Projects", "Real programs for your portfolio, built step by step."),
]

WORDMARK = (
    '<svg viewBox="0 0 24 24" aria-hidden="true"><rect width="24" height="24" rx="6" fill="#2e2e2e"/>'
    '<path d="M7 8l4 4-4 4" fill="none" stroke="#fdfcfb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M13 16h4" stroke="#fdfcfb" stroke-width="2" stroke-linecap="round"/></svg>'
)
ICON_CLOCK = (
    '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.5"/>'
    '<path d="M8 4.75V8l2.25 1.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
)
ICON_SCREEN = (
    '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="3" width="12" height="9" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.5"/>'
    '<path d="M5.5 14h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
)


def load_lessons():
    lessons = []
    for path in sorted(CONTENT.glob("*.html")):
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*(.*)$", raw, re.S)
        if not m:
            raise SystemExit(f"{path.name}: missing <!--meta {{...}} --> block")
        meta = json.loads(m.group(1))
        lesson_id, slug = path.stem.split("-", 1)
        meta.update(id=lesson_id, slug=slug, file=f"{lesson_id}-{slug}.html", url=f"{lesson_id}-{slug}", body=m.group(2))
        for key in ("title", "nav_title", "track", "intro", "minutes", "needs", "summary", "concepts", "sources"):
            if key not in meta:
                raise SystemExit(f"{path.name}: meta is missing '{key}'")
        lessons.append(meta)
    return lessons


def render_body(lesson, by_id):
    body = lesson["body"]

    def cite(m):
        n = int(m.group(1))
        if n < 1 or n > len(lesson["sources"]):
            raise SystemExit(f"{lesson['id']}: cite {n} has no source")
        return f'<sup class="cite"><a href="#src-{n}" aria-label="Source {n}">{n}</a></sup>'

    def link(m):
        target = by_id.get(m.group(1))
        if not target:
            raise SystemExit(f"{lesson['id']}: link to unknown lesson {m.group(1)}")
        return f'<a href="{target["url"]}">Lesson {int(target["id"])}: {html.escape(target["nav_title"])}</a>'

    body = os_variants(body)
    body = re.sub(r"\{\{cite:(\d+)\}\}", cite, body)
    body = re.sub(r"\{\{lesson:(\d{4})\}\}", link, body)

    # Number the quizzes so the app can track them for spaced review.
    counter = iter(range(1, 1000))
    body = re.sub(r'<div class="quiz"(?![^>]*data-qid)',
                  lambda m: f'<div class="quiz" data-qid="{lesson["id"]}-q{next(counter)}"', body)
    body = re.sub(r'<section id="([\w-]+)" data-nav="([^"]+)">', r'<section class="part" id="\1" data-nav="\2">', body)
    return body


# ---------- Windows / Mac / Linux versions (shown by assets/os.js) ----------
# Shortcuts a lesson can use:
#   {{py}}         python on Windows, python3 on Mac and Linux
#   {{venv-py}}    the virtual environment's Python: .venv\Scripts\python or .venv/bin/python
#   {{mod}}        the shortcut key: Ctrl, or Cmd on a Mac
#   {{os-switch}}  a Windows / Mac / Linux switch
# Terminal lines written for Windows (a prompt like ...folder> or PS C:\Users\you>) get Mac and
# Linux versions automatically.
def os_span(windows, mac, linux=None):
    linux = mac if linux is None else linux
    if mac == linux:
        return f'<span data-os="windows">{windows}</span><span data-os="mac linux">{mac}</span>'
    return f'<span data-os="windows">{windows}</span><span data-os="mac">{mac}</span><span data-os="linux">{linux}</span>'


def unix_command(cmd):
    """A Windows terminal command, as typed on Mac or Linux."""
    cmd = cmd.replace(".venv\\Scripts\\python", ".venv/bin/python")
    cmd = re.sub(r"^(\s*)python(?=\s|$)", r"\1python3", cmd)
    cmd = re.sub(r"^(\s*)mkdir (?!-p)", r"\1mkdir -p ", cmd)
    return cmd.replace("\\", "/")


def terminal_line(m):
    folder, cmd = m.group(1), m.group(2)
    home = folder == "PS C:\\Users\\you"
    name = "~ " if home else (folder.lstrip(".") + " " if folder else "")
    windows = f'<span class="prompt">{folder}&gt;</span>{cmd}'
    mac = f'<span class="prompt">{name}%</span>{unix_command(cmd)}'
    linux = f'<span class="prompt">{name}$</span>{unix_command(cmd)}'
    return os_span(windows, mac, linux)


def os_variants(body):
    body = body.replace("{{py}}", os_span("python", "python3"))
    body = body.replace("{{venv-py}}", os_span(".venv\\Scripts\\python", ".venv/bin/python"))
    body = body.replace("{{mod}}", os_span("Ctrl", "Cmd", "Ctrl"))
    body = body.replace("{{os-switch}}", '<div class="os-switch"></div>')
    prompt = r'<span class="prompt">((?:\.\.\.[\w-]+)|(?:PS C:\\Users\\you)|)&gt;</span>([^\n<]*)'
    return re.sub(r'<pre class="code">.*?</pre>', lambda block: re.sub(prompt, terminal_line, block.group(0)), body, flags=re.S)



def nav_items(body):
    return re.findall(r'<section class="part" id="([\w-]+)" data-nav="([^"]+)">', body)


def practice_section(lesson):
    return f'''
<section class="part" id="practice" data-nav="Practice">
  <div class="col">
    <h2>Practice on your weak spots</h2>
    <p>Your tutor can write extra exercises for this lesson, aimed at the things you've found hardest so far. They're checked by real tests, like the ones above.</p>
    <div class="ai-practice" data-lesson="{lesson["id"]}">
      <p class="ai-offline small quiet">Personal practice needs the course app. Start it with the <strong>Python from zero</strong> shortcut on your Desktop, then reload this page.</p>
    </div>
  </div>
</section>
'''


def lesson_end(lesson, prev, nxt):
    sources = "\n".join(
        f'        <li id="src-{i}"><a href="{html.escape(s["url"])}">{s["title"]}</a>{(". " + s["note"]) if s.get("note") else ""}</li>'
        for i, s in enumerate(lesson["sources"], 1)
    )
    prev_link = (f'<a href="{prev["url"]}"><span class="quiet">Back to</span> Lesson {int(prev["id"])}</a>'
                 if prev else '<a href="../"><span class="quiet">Back to</span> Course home</a>')
    next_link = (f'<a href="{nxt["url"]}">Lesson {int(nxt["id"])}: {html.escape(nxt["nav_title"])}</a>'
                 if nxt else '<a href="../">Course home</a>')
    return f'''
<div class="col lesson-end">
  <div class="finish card" data-lesson="{lesson["id"]}">
    <h3>Finished this lesson?</h3>
    <p class="quiet">Marking it done saves your progress and schedules review questions for your next warm-ups.</p>
    <button type="button" class="btn btn-primary finish-btn">Mark Lesson {int(lesson["id"])} as done</button>
    <p class="finish-msg small" aria-live="polite"></p>
  </div>
  <div class="sources" id="sources">
    <h3>Sources</h3>
    <ol>
{sources}
    </ol>
  </div>
  <nav class="pager" aria-label="Lesson navigation">
    {prev_link}
    {next_link}
  </nav>
</div>
'''


def render_lesson(lesson, index, lessons, by_id):
    body = render_body(lesson, by_id)
    if lesson.get("practice", True):
        # Practice goes before the final section (usually "Next").
        last = body.rfind('<section class="part"')
        body = body[:last] + practice_section(lesson) + "\n" + body[last:]
    items = nav_items(body)
    switcher = "\n".join(f'    <a href="#{sid}">{html.escape(label)}</a>' for sid, label in items)
    prev = lessons[index - 1] if index > 0 else None
    nxt = lessons[index + 1] if index + 1 < len(lessons) else None
    scripts = ["sections.js", "quiz.js"]
    if "pastecheck" in body:
        scripts.append("pastecheck.js")
    scripts += ["pyrunner.js", "tutor.js"]
    script_tags = "\n".join(f'<script src="../assets/{s}"></script>' for s in scripts)
    number = int(lesson["id"])
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lesson {number}: {html.escape(lesson["title"])}</title>
<meta name="description" content="Python from zero, lesson {number}: {html.escape(lesson["summary"][:150])}">
<link rel="stylesheet" href="../assets/style.css">
<link rel="icon" href="../favicon.ico" sizes="any">
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<script src="../assets/os.js"></script>
<script src="../assets/theme.js"></script>
</head>
<body data-lesson="{lesson["id"]}" data-track="{html.escape(lesson["track"])}">
<!-- Generated by tools/build.py from content/lessons/{lesson["id"]}-{lesson["slug"]}.html. Edit that file, not this one. -->

<header class="topbar">
  <a class="wordmark" href="../">
    {WORDMARK}
    Python from zero
  </a>
  <span class="where">Lesson {number} <span class="long">of {len(lessons)} · {html.escape(lesson["track"])}</span> · <a href="../reference/">Reference</a></span>
</header>

<main>

<div class="hero">
  <h1>{html.escape(lesson["title"])}</h1>
  <p class="intro">{lesson["intro"]}</p>
  <div class="badges">
    <span class="badge">{ICON_CLOCK}About {lesson["minutes"]} minutes</span>
    <span class="badge">{ICON_SCREEN}{html.escape(lesson["needs"])}</span>
  </div>
</div>

<div class="switcher-wrap" style="margin-top: 28px">
  <nav class="switcher" aria-label="Lesson sections">
{switcher}
  </nav>
</div>

<div class="col review-slot" id="review" hidden></div>
{body}
{lesson_end(lesson, prev, nxt)}
</main>
{script_tags}
</body>
</html>
'''


def render_index(lessons):
    groups = []
    for track, blurb in TRACKS:
        spaced = ' class="spaced"' if groups else ''
        items = [l for l in lessons if l["track"] == track]
        if not items:
            continue
        lis = "\n".join(
            f'''        <li class="lesson-row" data-lesson="{l["id"]}">
          <a href="lessons/{l["url"]}"><span class="num">{int(l["id"])}</span><span class="t">{html.escape(l["nav_title"])}</span></a>
          <span class="meta">{l["minutes"]} min</span>
        </li>'''
            for l in items
        )
        groups.append(f'''      <h2{spaced}>{html.escape(track)}</h2>
      <p class="quiet">{html.escape(blurb)}</p>
      <ol class="lesson-list">
{lis}
      </ol>''')
    first = lessons[0]
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Python from zero</title>
<meta name="description" content="A beginner course from your first line of Python to algorithms and core CS projects.">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<script src="assets/theme.js"></script>
</head>
<body data-page="home">
<!-- Generated by tools/build.py. -->

<header class="topbar">
  <a class="wordmark" href="./">
    {WORDMARK}
    Python from zero
  </a>
  <span class="where"><a href="reference/">Reference</a></span>
</header>

<main>
  <div class="hero">
    <h1>Python from zero to algorithms</h1>
    <p class="intro">{len(lessons)} short lessons that start at your very first line of code and build, one idea at a time, toward solving algorithm problems and building real computer science projects.</p>
    <div class="badges" style="margin-top: 32px">
      <a class="btn btn-primary continue-btn" href="lessons/{first["url"]}">Start Lesson 1</a>
    </div>
    <p class="home-status small quiet" aria-live="polite"></p>
  </div>

  <section class="part" style="padding-top: 80px">
    <div class="col">
{chr(10).join(groups)}

      <h2 class="spaced">Reference</h2>
      <div class="card on-cloud">
        <h3><a href="reference/">Reference sheets</a></h3>
        <p class="quiet">Syntax, terminal commands, algorithm patterns and every new word, on a few printable pages.</p>
      </div>
    </div>
    <footer class="site-footer"><a href="privacy">Privacy</a><a href="terms">Terms</a><span class="social"><a class="x-link" href="https://x.com/_dukedev" target="_blank" rel="me noopener" aria-label="DUKE (@_dukedev) on X"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a></span></footer>
  </section>
</main>
<script src="assets/tutor.js"></script>
<script src="assets/profile-card.js"></script>
</body>
</html>
'''


def strip_tags(fragment):
    text = re.sub(r"<script.*?</script>", " ", fragment, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_quizzes(lesson, body):
    out = []
    for m in re.finditer(r'<div class="quiz" data-qid="([^"]+)"[^>]*>(.*?)<p class="why">(.*?)</p>\s*</div>', body, re.S):
        qid, inner, why = m.groups()
        q = re.search(r'<p class="q">(.*?)</p>', inner, re.S)
        opts = re.findall(r'<button class="opt"( data-correct)?>(.*?)</button>', inner, re.S)
        if not q or len(opts) < 2:
            raise SystemExit(f"{qid}: quiz is malformed")
        if sum(1 for c, _ in opts if c) != 1:
            raise SystemExit(f"{qid}: quiz needs exactly one data-correct option")
        question = re.sub(r"^\s*\d+\.\s*", "", q.group(1).strip())
        out.append({
            "qid": qid, "lesson": lesson["id"], "question": question,
            "options": [{"html": o.strip(), "correct": bool(c)} for c, o in opts],
            "why": why.strip(),
        })
    return out


def main():
    lessons = load_lessons()
    by_id = {l["id"]: l for l in lessons}
    OUT.mkdir(exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    curriculum, quizbank = [], []
    for i, lesson in enumerate(lessons):
        page = render_lesson(lesson, i, lessons, by_id)
        if "—" in page:
            raise SystemExit(f"{lesson['id']}: contains an em dash")
        (OUT / lesson["file"]).write_text(page, encoding="utf-8")
        body = render_body(lesson, by_id)
        quizbank += extract_quizzes(lesson, body)
        curriculum.append({
            "id": lesson["id"], "file": lesson["file"], "url": lesson["url"], "title": lesson["title"],
            "nav_title": lesson["nav_title"], "track": lesson["track"], "summary": lesson["summary"],
            "concepts": lesson["concepts"], "minutes": lesson["minutes"],
            "exercises": re.findall(r'<div class="canvas exercise" id="([\w-]+)"', body),
            "text": strip_tags(body)[:14000],
        })
    (ROOT / "index.html").write_text(render_index(lessons), encoding="utf-8")
    (DATA / "curriculum.json").write_text(json.dumps(curriculum, indent=1, ensure_ascii=False), encoding="utf-8")
    (DATA / "quizbank.json").write_text(json.dumps(quizbank, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Built {len(lessons)} lessons, {len(quizbank)} quiz questions.")


if __name__ == "__main__":
    main()
