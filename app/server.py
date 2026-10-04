"""The course app: serves the lessons, saves progress and runs the AI tutor.

On your own computer, start it with the Desktop shortcut, or from the course folder:
    python app/server.py
Then open http://localhost:8765. Close the window to stop it.

It can also run on a web host, where people sign in with Google (see README.md).

Settings come from the .env file in the course folder, or from environment variables:
    GEMINI_API_KEY        your key from https://aistudio.google.com/apikey
    GEMINI_MODEL          which Gemini model to use (default gemini-3.8-flash)
    GOOGLE_CLIENT_ID      turns on "Sign in with Google" (with GOOGLE_CLIENT_SECRET)
    GOOGLE_CLIENT_SECRET
    PUBLIC_URL            the address people use, e.g. https://python.example.com
                          (default http://localhost:8765)
    ALLOWED_EMAILS        who may sign in, comma separated (empty: any Google account)
    OWNER_EMAIL           this account receives the progress saved before sign-in existed
    TUTOR_DAILY_LIMIT     AI requests per person per day (default 100 with sign-in, else no limit)
    TUTOR_TOTAL_DAILY_LIMIT  AI requests per day for everyone together (default 2000 with sign-in)
    TRUST_PROXY           1 when a web host's proxy sits in front (reads the visitor's address
                          from X-Forwarded-For, for rate limits)
    HOST, PORT            where to listen (default 127.0.0.1 and 8765)
    COURSE_DATA_DIR       folder for course.db (default app/data)
"""

import hmac
import itertools
import time
import traceback
import json
import mimetypes
import os
import re
import secrets
import socket
import sys
import threading
import webbrowser
from datetime import date, datetime
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import auth  # noqa: E402
import tutor  # noqa: E402
from gemini import FakeGemini, Gemini, GeminiError  # noqa: E402
from progress import load_file, normalise  # noqa: E402
from store import SESSION_DAYS, Store  # noqa: E402

# Only these parts of the course folder are served to the browser. Your .env and
# the database are never sent.
PUBLIC = ("index.html", "privacy.html", "terms.html", "lessons/", "assets/", "reference/", "favicon.ico")


def load_env(path):
    values = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    return values


SETTINGS = ("GEMINI_", "TUTOR_", "GOOGLE_", "PUBLIC_URL", "ALLOWED_EMAILS", "OWNER_EMAIL", "HOST", "PORT", "COURSE_",
            "TRUST_PROXY")
ENV = {**load_env(ROOT / ".env"), **{k: v for k, v in os.environ.items() if k.startswith(SETTINGS)}}

HOST = ENV.get("HOST") or "127.0.0.1"
PORT = int(ENV.get("COURSE_PORT") or ENV.get("PORT") or "8765")
PUBLIC_URL = (ENV.get("PUBLIC_URL") or f"http://localhost:{PORT}").rstrip("/")
CLIENT_ID = ENV.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = ENV.get("GOOGLE_CLIENT_SECRET", "")
AUTH = bool(CLIENT_ID and CLIENT_SECRET)
SECURE = PUBLIC_URL.startswith("https://")
# The __Host- prefix makes browsers refuse the cookie unless it's Secure and site-wide.
SESSION_COOKIE = "__Host-pfz_session" if SECURE else "pfz_session"
STATE_COOKIE = "pfz_signin"
ALLOWED = {e.strip().lower() for e in ENV.get("ALLOWED_EMAILS", "").split(",") if e.strip()}
OWNER_EMAIL = ENV.get("OWNER_EMAIL", "").strip().lower()
DAILY_LIMIT = int(ENV.get("TUTOR_DAILY_LIMIT") or (100 if AUTH else 0))
TOTAL_LIMIT = int(ENV.get("TUTOR_TOTAL_DAILY_LIMIT") or (2000 if AUTH else 0))
TRUST_PROXY = ENV.get("TRUST_PROXY") == "1"

# Sent with every response. The page only loads code from this site and the Pyodide CDN,
# fonts from Google Fonts, and profile pictures from Google.
CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' https://cdn.jsdelivr.net 'wasm-unsafe-eval'",
    "worker-src 'self' blob: https://cdn.jsdelivr.net",   # Pyodide's module loads inside our worker
    "connect-src 'self' https://cdn.jsdelivr.net",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: https://*.googleusercontent.com https://pbs.twimg.com",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
])
SECURITY_HEADERS = [
    ("Content-Security-Policy", CSP),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("X-Frame-Options", "DENY"),
    ("Cross-Origin-Opener-Policy", "same-origin"),
    ("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()"),
]


class RateLimiter:
    """Allows `limit` requests per `window` seconds for each key (a visitor's address or an account)."""

    def __init__(self, limit, window):
        self.limit, self.window, self.hits, self.lock = limit, window, {}, threading.Lock()

    def allow(self, key):
        now = time.time()
        with self.lock:
            recent = [t for t in self.hits.get(key, []) if t > now - self.window]
            allowed = len(recent) < self.limit
            if allowed:
                recent.append(now)
            self.hits[key] = recent
            if len(self.hits) > 20000:  # forget quiet visitors so memory stays small
                self.hits = {k: v for k, v in self.hits.items() if v and v[-1] > now - self.window}
            return allowed


SIGN_IN_LIMIT = RateLimiter(20, 600)   # sign-ins per visitor address, per 10 minutes
SAVE_LIMIT = RateLimiter(240, 60)      # progress saves and other changes per account, per minute
AI_LIMIT = RateLimiter(8, 60)          # tutor requests per account, per minute
# Tests point these at a stand-in for Google.
AUTH_URL = ENV.get("GOOGLE_AUTH_URL") or auth.AUTH_URL
TOKEN_URL = ENV.get("GOOGLE_TOKEN_URL") or auth.TOKEN_URL
LOCAL_USER = "local"
AVATAR_NAME = re.compile(r"[a-z]{2,12}-[a-z]{2,12}")
PICTURE_HOSTS = re.compile(r"https://[a-z0-9-]+\.googleusercontent\.com/[^\s\"'<>]+$")

CURRICULUM = json.loads((HERE / "data" / "curriculum.json").read_text(encoding="utf-8"))
QUIZBANK = {q["qid"]: q for q in json.loads((HERE / "data" / "quizbank.json").read_text(encoding="utf-8"))}
# COURSE_DATA_DIR lets tests (or a web host's disk) use another folder.
DATA_SETTING = ENV.get("COURSE_DATA_DIR")
DATA_DIR = (ROOT / DATA_SETTING) if DATA_SETTING else HERE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RECORDS_DIR = (DATA_DIR / "learning-records") if DATA_SETTING else ROOT / "learning-records"
STORE = Store(DATA_DIR / "course.db")

# Progress saved before accounts existed lives in progress.json. Without sign-in it becomes
# the "local" person's progress; with sign-in, OWNER_EMAIL's account gets it.
LEGACY = load_file(DATA_DIR / "progress.json")
if LEGACY and not STORE.has_progress(LOCAL_USER):
    STORE.replace_progress(LOCAL_USER, LEGACY)


def make_ai():
    if ENV.get("TUTOR_FAKE_AI") == "1":
        return FakeGemini()
    key = ENV.get("GEMINI_API_KEY", "")
    if not key or key.startswith("paste"):
        return None
    return Gemini(key, ENV.get("GEMINI_MODEL") or "gemini-3.8-flash")


AI = make_ai()


def lesson_by_id(lesson_id):
    return next((l for l in CURRICULUM if l["id"] == lesson_id), None)


def learning_record(lesson_id, progress):
    """A learning record (the teach skill's format) for a lesson someone just finished."""
    lesson = lesson_by_id(lesson_id)
    s = progress.lesson_summary(lesson_id)
    exercises = [e for e in s["exercises"].items() if not e[1].get("practice")]
    practice = [e for e in s["exercises"].items() if e[1].get("practice")]
    solved = sum(1 for _, e in exercises if e.get("solved"))
    lines = [
        f"# Lesson {int(lesson_id)} finished: {lesson['nav_title']}",
        "",
        f"Completed {date.today().isoformat()} through the course app. Concepts covered: {', '.join(lesson['concepts'])}.",
        "",
        "**Evidence**:",
        f"- Exercises solved: {solved} of {len(exercises)}" + (f" (attempts: {', '.join(f'{k} {v['attempts']}' for k, v in exercises)})" if exercises else ""),
        f"- Quiz questions right on the first try: {s['quizzes_first_try']} of {s['quizzes_answered']}",
    ]
    if practice:
        lines.append(f"- Tutor practice exercises solved: {sum(1 for _, e in practice if e.get('solved'))} of {len(practice)}")
    if s["mistakes"]:
        lines += ["", "**Mistakes during the lesson** (for future warm-ups and practice):"]
        lines += [f"- {m['detail']}" for m in s["mistakes"][-10:]]
    lines += ["", "*Written automatically by app/server.py. A teacher session may revise or supersede it.*", ""]
    return "\n".join(lines)


def save_learning_record(user_id, lesson_id, progress):
    text = learning_record(lesson_id, progress)
    STORE.add_record(user_id, lesson_id, text)
    # On your own computer, also write it where a Claude teaching session will find it.
    if user_id == LOCAL_USER or (OWNER_EMAIL and (STORE.user(user_id) or {}).get("email") == OWNER_EMAIL):
        RECORDS_DIR.mkdir(exist_ok=True)
        numbers = [int(p.name[:4]) for p in RECORDS_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")]
        number = (max(numbers) if numbers else 0) + 1
        slug = lesson_by_id(lesson_id)["url"].split("-", 1)[1]
        (RECORDS_DIR / f"{number:04d}-lesson-{lesson_id}-{slug}.md").write_text(text, encoding="utf-8")


def give_owner_old_progress(user_id, email):
    """The first time OWNER_EMAIL signs in, copy over the progress saved before sign-in existed."""
    if OWNER_EMAIL and email == OWNER_EMAIL and not STORE.has_progress(user_id) and STORE.has_progress(LOCAL_USER):
        STORE.replace_progress(user_id, STORE.read_progress(LOCAL_USER).data)


def is_owner(user_id):
    """The person running the course: everyone on a computer without sign-in, else OWNER_EMAIL."""
    if not AUTH:
        return user_id == LOCAL_USER
    return bool(OWNER_EMAIL and user_id and (STORE.user(user_id) or {}).get("email") == OWNER_EMAIL)


def page(title, message):
    """A small page for sign-in problems, in the course style."""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>
<link rel="stylesheet" href="/assets/style.css"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><script src="/assets/theme.js"></script></head>
<body><main><div class="hero"><h1>{title}</h1><p class="intro">{message}</p>
<div class="badges" style="margin-top: 32px"><a class="btn btn-primary" href="/">Back to the course</a></div></div></main></body></html>"""


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Handler(BaseHTTPRequestHandler):
    server_version = "PythonFromZero/2.0"

    def log_message(self, fmt, *args):
        if args and ("/api/" in str(args[0]) or "/auth/" in str(args[0])):
            sys.stderr.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {fmt % args}\n")

    def end_headers(self):
        for name, value in SECURITY_HEADERS:
            self.send_header(name, value)
        if SECURE:
            self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        super().end_headers()

    def client_ip(self):
        if TRUST_PROXY and self.headers.get("X-Forwarded-For"):
            return self.headers["X-Forwarded-For"].split(",")[0].strip()
        return self.client_address[0]

    def safely(self, handler):
        """Run a request handler; log anything unexpected instead of dropping the connection."""
        try:
            handler()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception:
            sys.stderr.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ERROR {self.command} {self.path}\n{traceback.format_exc()}")
            try:
                self.send_json({"error": "Something went wrong on the server. It has been logged."}, 500)
            except Exception:
                pass

    # ---------- helpers ----------
    def send_json(self, data, status=200, cookies=()):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for c in cookies:
            self.send_header("Set-Cookie", c)
        if self.path.startswith("/api/health"):
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, location, status=302, cookies=()):
        self.send_response(status)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        if status == 302:
            self.send_header("Cache-Control", "no-store")
        for c in cookies:
            self.send_header("Set-Cookie", c)
        self.end_headers()

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > 2_000_000:
            raise ValueError("Request too large")
        return json.loads(self.rfile.read(length) or b"{}")

    def cookie(self, name):
        jar = SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie") or "")
        except Exception:
            return None
        return jar[name].value if name in jar else None

    @staticmethod
    def make_cookie(name, value, max_age):
        parts = [f"{name}={value}", "Path=/", "HttpOnly", "SameSite=Lax", f"Max-Age={max_age}"]
        if SECURE:
            parts.append("Secure")
        return "; ".join(parts)

    def user_id(self):
        """Who is asking: the signed-in account, "local" when sign-in is off, or None."""
        if not AUTH:
            return LOCAL_USER
        return STORE.session_user(self.cookie(SESSION_COOKIE))

    def same_site(self):
        """Refuse changes sent from other websites."""
        origin = self.headers.get("Origin")
        return origin is None or origin in (PUBLIC_URL, f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}")

    def send_stream(self, pieces, on_done=None):
        """Send a tutor reply as Gemini writes it: one JSON line per piece of text.

        The first piece is fetched before replying, so a bad key or a network
        problem still comes back as a normal JSON error.
        """
        first = next(pieces, "")
        if not first:
            return self.send_json({"error": "Gemini sent back an empty reply. Try again."}, 502)
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        parts = []

        def write(obj):
            self.wfile.write((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
            self.wfile.flush()

        try:
            for piece in itertools.chain([first], pieces):
                parts.append(piece)
                write({"text": piece})
        except GeminiError as e:
            write({"error": str(e)})
            return
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return  # the page was closed mid-reply
        if on_done:
            on_done("".join(parts))

    def ai_for(self, user_id):
        """The AI tutor, or None after sending the reason it can't be used."""
        if AI is None:
            self.send_json({"error": "The AI tutor is off: add your GEMINI_API_KEY to the .env file, then restart the app."}, 503)
            return None
        if not AI_LIMIT.allow(user_id):
            self.send_json({"error": "That's a lot of questions in one minute. Wait a moment, then ask again."}, 429)
            return None
        over = STORE.use_ai(user_id, DAILY_LIMIT, TOTAL_LIMIT)
        if over == "person":
            self.send_json({"error": f"You've used today's {DAILY_LIMIT} tutor requests. They reset tomorrow."}, 429)
            return None
        if over == "everyone":
            self.send_json({"error": "The tutor is resting: the course has reached today's limit for everyone. It's back tomorrow."}, 429)
            return None
        return AI

    # ---------- GET ----------
    def do_GET(self):
        self.safely(self.handle_get)

    def do_POST(self):
        self.safely(self.handle_post)

    def handle_get(self):
        url = urlparse(self.path)
        if url.path == "/admin":
            return self.send_admin()
        if url.path == "/api/health":
            return self.send_json({"ok": True, "ai": AI is not None, "model": getattr(AI, "model", None), "auth": AUTH})
        if url.path == "/api/state":
            return self.send_state(parse_qs(url.query))
        if url.path == "/api/progress/export":
            return self.export_progress()
        if url.path == "/auth/google":
            return self.start_sign_in(parse_qs(url.query))
        if url.path == "/auth/callback":
            return self.finish_sign_in(parse_qs(url.query))
        if url.path.startswith("/api/") or url.path.startswith("/auth/"):
            return self.send_json({"error": "Not found"}, 404)
        return self.serve_static(url)

    def do_HEAD(self):
        url = urlparse(self.path)
        if url.path.startswith(("/api/", "/auth/")):
            self.send_response(200)
            self.end_headers()
            return
        self.serve_static(url, head=True)

    def send_state(self, q):
        lesson_id = (q.get("lesson") or [""])[0]
        user_id = self.user_id()
        user = STORE.user(user_id) if AUTH and user_id else None
        data = {
            "ai": AI is not None,
            "auth": AUTH,
            "signedIn": user_id is not None,
            "user": user and {k: user[k] for k in ("name", "email", "picture", "avatar")},
            "lessons": [{"id": l["id"], "url": l["url"], "nav_title": l["nav_title"]} for l in CURRICULUM],
            "completed": [],
            "review": [],
            "dueCount": 0,
        }
        if user_id:
            if AUTH:
                STORE.touch(user_id)
            data["owner"] = is_owner(user_id)
            progress = STORE.read_progress(user_id)
            data["completed"] = progress.completed()
            data["review"] = [QUIZBANK[qid] for qid in progress.due_cards(lesson_id) if qid in QUIZBANK]
            data["dueCount"] = len(progress.due_cards("", limit=999))
            if lesson_id:
                data["lesson"] = progress.lesson_summary(lesson_id)
                data["chat"] = progress.chat(lesson_id)[-20:]
        return self.send_json(data)

    def send_admin(self):
        """A private overview for the course owner: numbers and the feedback people sent."""
        if not is_owner(self.user_id()):
            return self.send_error(404)
        st = STORE.stats()
        rows = "".join(
            f"<tr><td>{datetime.fromtimestamp(f['created']):%Y-%m-%d %H:%M}</td><td>{esc(f['lesson'] or '')}</td>"
            f"<td>{esc(f['message'])}</td><td>{esc(f['from'])}</td></tr>" for f in STORE.feedback())
        body = f"""<p class="intro">Accounts: {st['accounts']} · Active in the last day: {st['active_today']} ·
AI requests today: {st['ai_requests_today']} of {TOTAL_LIMIT or 'no limit'} · Feedback messages: {st['feedback']}</p></div>
<div class="col" style="margin-top: 48px"><h2>Feedback</h2>
<div class="table-wrap"><table><thead><tr><th>When</th><th>Lesson</th><th>Message</th><th>From</th></tr></thead>
<tbody>{rows or '<tr><td colspan="4">Nothing yet.</td></tr>'}</tbody></table></div>"""
        return self.send_html(page("Course overview", "").replace('<p class="intro"></p>', body).replace(
            '<div class="badges" style="margin-top: 32px"><a class="btn btn-primary" href="/">Back to the course</a></div></div>',
            '<p style="margin-top: 32px"><a href="/">Back to the course</a></p></div>'))

    def export_progress(self):
        user_id = self.user_id()
        if not user_id:
            return self.send_json({"error": "Sign in first."}, 401)
        body = json.dumps(STORE.read_progress(user_id).data, indent=1, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="python-from-zero-progress-{date.today().isoformat()}.json"')
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, url, head=False):
        """Pages have clean addresses: /lessons/0003-variables serves lessons/0003-variables.html.
        Old addresses ending in .html redirect to the clean ones."""
        rel = unquote(url.path).lstrip("/")
        if ".." in rel or "\\" in rel:
            return self.send_error(404)
        if rel.endswith(".html"):
            clean = rel[:-len(".html")]
            clean = "" if clean == "index" else clean[:-len("index")] if clean.endswith("/index") else clean
            if (ROOT / rel).is_file() and rel.startswith(PUBLIC):
                return self.redirect("/" + quote(clean) + (f"?{url.query}" if url.query else ""), 301)
            return self.send_error(404)
        if rel == "" or rel.endswith("/"):
            rel += "index.html"
        elif (ROOT / rel).is_dir():
            return self.redirect("/" + quote(rel) + "/", 301)
        elif "." not in rel.rsplit("/", 1)[-1]:
            rel += ".html"
        if not rel.startswith(PUBLIC):
            return self.send_error(404)
        file = (ROOT / rel).resolve()
        if ROOT not in file.parents or not file.is_file():
            return self.send_error(404)
        body = file.read_bytes()
        ctype = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if not head:
            self.wfile.write(body)

    # ---------- Sign in with Google ----------
    def start_sign_in(self, q):
        if not AUTH:
            return self.redirect("/")
        if not SIGN_IN_LIMIT.allow(self.client_ip()):
            return self.send_html(page("Too many sign-in attempts", "Wait a few minutes, then try again."), 429)
        state, verifier, nonce = auth.new_request()
        STORE.add_pending(state, verifier, nonce, auth.safe_next((q.get("next") or ["/"])[0]))
        target = auth.authorize_url(CLIENT_ID, PUBLIC_URL + "/auth/callback", state, verifier, nonce, AUTH_URL)
        self.redirect(target, cookies=[self.make_cookie(STATE_COOKIE, state, 600)])

    def finish_sign_in(self, q):
        if not AUTH:
            return self.redirect("/")
        clear_state = self.make_cookie(STATE_COOKIE, "", 0)
        if q.get("error"):
            return self.redirect("/", cookies=[clear_state])  # they pressed Cancel at Google
        state = (q.get("state") or [""])[0]
        browser_state = self.cookie(STATE_COOKIE) or ""
        pending = STORE.take_pending(state) if state else None
        if not pending or not hmac.compare_digest(state, browser_state):
            return self.send_html(page("Sign-in didn't finish", "That sign-in link has expired or was opened in a different browser. Start again from the course."), 400)
        verifier, nonce, next_path = pending
        try:
            tokens = auth.exchange_code(CLIENT_ID, CLIENT_SECRET, PUBLIC_URL + "/auth/callback",
                                        (q.get("code") or [""])[0], verifier, TOKEN_URL)
            claims = auth.read_id_token(tokens.get("id_token", ""), CLIENT_ID, nonce)
        except auth.SignInError as e:
            return self.send_html(page("Sign-in didn't work", esc(e)), 400)
        email = claims.get("email", "").lower()
        if ALLOWED and email not in ALLOWED:
            return self.send_html(page("Not on the list yet", f"This course is invite-only. Ask the owner to add {esc(email)}."), 403)
        user_id = "google:" + claims["sub"]
        # Google's profile picture address; only kept if it really is one of Google's https images.
        picture = claims.get("picture", "")
        picture = picture if PICTURE_HOSTS.match(picture) else ""
        STORE.save_user(user_id, email, claims.get("name") or email, picture)
        give_owner_old_progress(user_id, email)
        token = secrets.token_urlsafe(32)
        STORE.new_session(user_id, token)
        self.redirect(next_path, cookies=[self.make_cookie(SESSION_COOKIE, token, SESSION_DAYS * 86400), clear_state])

    # ---------- POST ----------
    def handle_post(self):
        url = urlparse(self.path)
        if not self.same_site():
            return self.send_json({"error": "Requests from other websites aren't allowed."}, 403)
        if url.path == "/auth/logout":
            STORE.end_session(self.cookie(SESSION_COOKIE))
            return self.send_json({"ok": True}, cookies=[self.make_cookie(SESSION_COOKIE, "", 0)])
        try:
            body = self.read_json()
        except (ValueError, json.JSONDecodeError):
            return self.send_json({"error": "Bad request"}, 400)
        user_id = self.user_id()
        if not user_id:
            return self.send_json({"error": "Sign in to save progress and use the tutor.", "signin": True}, 401)
        if not SAVE_LIMIT.allow(user_id):
            return self.send_json({"error": "Too many requests at once. Wait a moment and try again."}, 429)
        try:
            return self.handle_api(url.path, body, user_id)
        except GeminiError as e:
            return self.send_json({"error": str(e)}, 502)
        except ValueError as e:
            return self.send_json({"error": str(e)}, 400)

    def handle_api(self, path, body, user_id):
        if path == "/api/event":
            kind = body.get("type")
            with STORE.progress(user_id) as p:
                if kind == "exercise":
                    p.record_exercise(body)
                elif kind == "quiz":
                    p.record_quiz(body)
                elif kind == "paste":
                    p.record_paste(body)
            return self.send_json({"ok": True})
        if path == "/api/complete":
            lesson_id = body.get("lesson", "")
            if not lesson_by_id(lesson_id):
                return self.send_json({"error": "Unknown lesson"}, 400)
            with STORE.progress(user_id) as p:
                if p.complete(lesson_id):
                    save_learning_record(user_id, lesson_id, p)
                done = p.completed()
            nxt = next((l for l in CURRICULUM if l["id"] > lesson_id and l["id"] not in done), None)
            return self.send_json({"ok": True, "next": nxt and {"url": nxt["url"], "nav_title": nxt["nav_title"], "id": nxt["id"]}})
        if path == "/api/feedback":
            message = str(body.get("message") or "").strip()
            if not message:
                return self.send_json({"error": "Write a message first."}, 400)
            STORE.add_feedback(user_id, str(body.get("lesson") or "")[:8], str(body.get("page") or "")[:200], message[:2000])
            return self.send_json({"ok": True})
        if path == "/api/account/delete":
            if user_id == LOCAL_USER or body.get("confirm") != "delete":
                return self.send_json({"error": "Nothing was deleted."}, 400)
            STORE.delete_user(user_id)
            return self.send_json({"ok": True}, cookies=[self.make_cookie(SESSION_COOKIE, "", 0)])
        if path == "/api/avatar":
            # "" means automatic (Google photo, else initial), "google", "letter", or a drawn avatar's name.
            avatar = str(body.get("avatar", ""))
            if user_id == LOCAL_USER or not (avatar in ("", "google", "letter") or AVATAR_NAME.fullmatch(avatar)):
                return self.send_json({"error": "That avatar can't be used."}, 400)
            STORE.set_avatar(user_id, avatar)
            return self.send_json({"ok": True, "avatar": avatar})
        if path == "/api/progress/import":
            data = normalise(body)
            STORE.replace_progress(user_id, data)
            return self.send_json({"ok": True, "completed": STORE.read_progress(user_id).completed()})
        if path == "/api/explain":
            ai = self.ai_for(user_id)
            if ai:
                return self.send_stream(tutor.explain(ai, CURRICULUM, STORE.read_progress(user_id), body))
            return
        if path == "/api/practice":
            ai = self.ai_for(user_id)
            if ai:
                return self.send_json({"exercises": tutor.practice(ai, CURRICULUM, STORE.read_progress(user_id), body.get("lesson", ""))})
            return
        if path == "/api/chat":
            lesson_id = body.get("lesson", "")
            message = (body.get("message") or "").strip()
            if not message:
                return self.send_json({"error": "Empty message"}, 400)
            ai = self.ai_for(user_id)
            if ai:
                def save(reply):
                    with STORE.progress(user_id) as p:
                        p.add_chat(lesson_id, "user", message)
                        p.add_chat(lesson_id, "tutor", reply)

                return self.send_stream(tutor.chat(ai, CURRICULUM, STORE.read_progress(user_id), lesson_id, message), save)
            return
        return self.send_json({"error": "Not found"}, 404)


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    open_browser = "--no-browser" not in sys.argv and HOST in ("127.0.0.1", "localhost")
    if port_in_use(PORT):
        print(f"The course app is already running. Opening {PUBLIC_URL}")
        if open_browser:
            webbrowser.open(PUBLIC_URL + "/")
        return
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    status = f"on ({AI.model})" if AI else "off (add GEMINI_API_KEY to .env to turn it on)"
    print(f"Python from zero is running at {PUBLIC_URL}/")
    print(f"AI tutor: {status}")
    print("Sign in with Google: " + ("on" + (f", limited to {len(ALLOWED)} email(s)" if ALLOWED else "") if AUTH else "off (progress is saved on this computer)"))
    print("Keep this window open while you study. Close it to stop the app.")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(PUBLIC_URL + "/")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
