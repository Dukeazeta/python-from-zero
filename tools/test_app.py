"""End-to-end test of the course app: clean addresses, Google sign-in, accounts and progress.

Runs the real app/server.py against a small stand-in for Google's sign-in servers, with a
throwaway data folder and the fake AI tutor, so no real account or API key is used.
    python tools/test_app.py
"""

import base64
import hashlib
import http.cookiejar
import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
import auth as app_auth  # noqa: E402
GOOGLE_PORT, APP_PORT = 8771, 8772
APP = f"http://localhost:{APP_PORT}"
DATA = ".test-auth"
PHOTO = "https://lh3.googleusercontent.com/a/test-photo=s96-c"
CLIENT_ID, CLIENT_SECRET = "test-client.apps.googleusercontent.com", "test-secret"
failures = []


def check(label, got, expected):
    ok = got == expected
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else f"\n     expected {expected!r}\n     got      {got!r}"))
    if not ok:
        failures.append(label)


# ---------- A stand-in for Google ----------
class FakeGoogle(BaseHTTPRequestHandler):
    next_user = {}
    codes = {}

    def log_message(self, *args):
        pass

    def do_GET(self):
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
        assert q["client_id"] == CLIENT_ID and q["code_challenge_method"] == "S256" and "openid" in q["scope"]
        code = secrets.token_urlsafe(16)
        FakeGoogle.codes[code] = (q["nonce"], q["code_challenge"], q["redirect_uri"], dict(FakeGoogle.next_user))
        self.send_response(302)
        self.send_header("Location", q["redirect_uri"] + "?" + urllib.parse.urlencode({"code": code, "state": q["state"]}))
        self.end_headers()

    def do_POST(self):
        form = dict(urllib.parse.parse_qsl(self.rfile.read(int(self.headers["Content-Length"])).decode()))
        nonce, challenge, redirect_uri, user = FakeGoogle.codes.pop(form.get("code"), (None,) * 4)
        pkce = base64.urlsafe_b64encode(hashlib.sha256(form.get("code_verifier", "").encode()).digest()).rstrip(b"=").decode()
        if not nonce or pkce != challenge or form.get("client_secret") != CLIENT_SECRET or form.get("redirect_uri") != redirect_uri:
            self.send_response(400)
            self.end_headers()
            return
        claims = {"iss": "https://accounts.google.com", "aud": CLIENT_ID, "exp": time.time() + 3600,
                  "nonce": nonce, "email_verified": True, **user}
        part = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
        body = json.dumps({"id_token": f"{part({'alg': 'RS256'})}.{part(claims)}.sig"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


# ---------- A browser with its own cookies ----------
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Browser:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.follow = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.single = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), NoRedirect)

    def get(self, path, follow=True):
        try:
            r = (self.follow if follow else self.single).open(APP + path if path.startswith("/") else path, timeout=20)
            return r.status, r.headers, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read().decode("utf-8", "replace")

    def post(self, path, data, origin=None):
        headers = {"Content-Type": "application/json"}
        if origin:
            headers["Origin"] = origin
        req = urllib.request.Request(APP + path, data=json.dumps(data).encode(), headers=headers, method="POST")
        try:
            r = self.follow.open(req, timeout=20)
            return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")

    def state(self, lesson=""):
        return json.loads(self.get("/api/state" + (f"?lesson={lesson}" if lesson else ""))[2])

    def sign_in(self, sub, email, name, next_path="/lessons/0003-variables", picture=""):
        FakeGoogle.next_user = {"sub": sub, "email": email, "name": name, "picture": picture}
        return self.get("/auth/google?next=" + urllib.parse.quote(next_path))


def start_app(extra_env):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GOOGLE_", "GEMINI_", "TUTOR_", "OWNER_", "ALLOWED_", "PUBLIC_"))}
    # Set every setting here, so values in the course's .env file can't leak into the test.
    env.update({"COURSE_PORT": str(APP_PORT), "COURSE_DATA_DIR": DATA, "TUTOR_FAKE_AI": "1", "GEMINI_API_KEY": "",
                "PUBLIC_URL": APP, "GOOGLE_CLIENT_ID": "", "GOOGLE_CLIENT_SECRET": "", "OWNER_EMAIL": "",
                "ALLOWED_EMAILS": "", "TUTOR_DAILY_LIMIT": "", "TUTOR_TOTAL_DAILY_LIMIT": "", "TRUST_PROXY": "",
                "HOST": "127.0.0.1", "PYTHONUNBUFFERED": "1"}, **extra_env)
    proc = subprocess.Popen([sys.executable, str(ROOT / "app" / "server.py"), "--no-browser"], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(50):
        try:
            urllib.request.urlopen(APP + "/api/health", timeout=1)
            return proc
        except Exception:
            time.sleep(0.1)
    proc.kill()
    raise SystemExit("The app didn't start:\n" + proc.stdout.read())


def fresh_data(seed_progress=None):
    shutil.rmtree(ROOT / DATA, ignore_errors=True)
    (ROOT / DATA).mkdir()
    if seed_progress:
        (ROOT / DATA / "progress.json").write_text(json.dumps(seed_progress), encoding="utf-8")


def main():
    google = ThreadingHTTPServer(("127.0.0.1", GOOGLE_PORT), FakeGoogle)
    threading.Thread(target=google.serve_forever, daemon=True).start()
    auth_env = {"GOOGLE_CLIENT_ID": CLIENT_ID, "GOOGLE_CLIENT_SECRET": CLIENT_SECRET,
                "GOOGLE_AUTH_URL": f"http://127.0.0.1:{GOOGLE_PORT}/auth", "GOOGLE_TOKEN_URL": f"http://127.0.0.1:{GOOGLE_PORT}/token",
                "OWNER_EMAIL": "ada@example.com", "ALLOWED_EMAILS": "ada@example.com,bo@example.com", "TUTOR_DAILY_LIMIT": "2",
                "TUTOR_TOTAL_DAILY_LIMIT": "3"}
    old = {"lessons": {"0001": {"started": "2026-10-03T10:00:00", "completed": "2026-10-03T11:00:00", "exercises": {}, "quizzes": {}}}}
    fresh_data(old)
    app = start_app(auth_env)
    try:
        b = Browser()
        print("-- Clean addresses")
        check("lesson without .html", b.get("/lessons/0003-variables")[0], 200)
        s, h, _ = b.get("/lessons/0003-variables.html", follow=False)
        check("old .html address redirects", (s, h["Location"]), (301, "/lessons/0003-variables"))
        check("index.html redirects home", b.get("/index.html", follow=False)[1]["Location"], "/")
        check("/reference adds its slash", b.get("/reference", follow=False)[1]["Location"], "/reference/")
        check("reference/index.html redirects", b.get("/reference/index.html", follow=False)[1]["Location"], "/reference/")
        check("reference sheet without .html", b.get("/reference/algorithms")[0], 200)
        check("unknown page is 404", b.get("/lessons/nope")[0], 404)
        check(".env is never served", b.get("/.env")[0], 404)
        check("database is never served", b.get(f"/{DATA}/course.db")[0], 404)
        check("lesson links have no .html", ".html\"" in b.get("/lessons/0003-variables")[2].split("<main")[1], False)
        s, h, _ = b.get("/lessons/0003-variables")
        check("security headers sent", all(h.get(k) for k in ("Content-Security-Policy", "X-Content-Type-Options", "Referrer-Policy", "X-Frame-Options")), True)
        check("privacy and terms pages", (b.get("/privacy")[0], b.get("/terms")[0]), (200, 200))
        check("overview hidden when signed out", b.get("/admin")[0], 404)

        print("-- Signed out")
        st = b.state()
        check("signed out state", (st["auth"], st["signedIn"], st["completed"]), (True, False, []))
        check("saving needs sign-in", b.post("/api/event", {"type": "quiz", "lesson": "0003", "qid": "0003-q1", "firstTry": True})[0], 401)

        print("-- Sign in (owner)")
        s, h, _ = b.sign_in("111", "ada@example.com", "Ada Lovelace", picture=PHOTO)
        check("lands back on the lesson", s, 200)
        session = next((c for c in b.jar if c.name == "pfz_session"), None)
        check("session cookie set", session is not None, True)
        check("session cookie is HttpOnly", bool(session and session.has_nonstandard_attr("HttpOnly")), True)
        st = b.state("0003")
        check("signed in as Ada", (st["signedIn"], st["user"]["email"]), (True, "ada@example.com"))
        check("owner received the old progress", st["completed"], ["0001"])
        check("Google profile picture saved", st["user"]["picture"], PHOTO)
        check("choose a drawn avatar", (b.post("/api/avatar", {"avatar": "coral-cat"})[0], b.state()["user"]["avatar"]), (200, "coral-cat"))
        check("odd avatar values refused", b.post("/api/avatar", {"avatar": "<script>"})[0], 400)
        check("back to the Google photo", (b.post("/api/avatar", {"avatar": "google"})[0], b.state()["user"]["avatar"]), (200, "google"))
        check("record a quiz", b.post("/api/event", {"type": "quiz", "lesson": "0003", "qid": "0003-q1", "firstTry": False, "wrongPicks": ["7"], "question": "Q"})[0], 200)
        s, body = b.post("/api/complete", {"lesson": "0003"})
        check("finish Lesson 3", (s, json.loads(body)["next"]["url"]), (200, "0004-input-and-types"))
        check("Lesson 3 saved", b.state()["completed"], ["0001", "0003"])
        check("owner sees the overview", b.get("/admin")[0], 200)
        check("feedback is saved", b.post("/api/feedback", {"lesson": "0003", "page": "/lessons/0003-variables", "message": "Step 2 is unclear"})[0], 200)
        check("feedback shows in the overview", "Step 2 is unclear" in b.get("/admin")[2], True)
        check("empty feedback refused", b.post("/api/feedback", {"lesson": "0003", "message": "  "})[0], 400)
        check("other websites can't post", b.post("/api/event", {"type": "quiz"}, origin="https://evil.example")[0], 403)

        print("-- Tutor")
        s, body = b.post("/api/chat", {"lesson": "0003", "message": "hi"})
        reply = "".join(json.loads(line).get("text", "") for line in body.splitlines() if line.strip())
        check("chat streams in pieces", (s, len(body.splitlines()) > 3, "fake tutor" in reply), (200, True, True))
        check("chat saved", len(b.state("0003")["chat"]), 2)
        check("second tutor request allowed", b.post("/api/chat", {"lesson": "0003", "message": "again"})[0], 200)
        check("daily limit reached", b.post("/api/chat", {"lesson": "0003", "message": "third"})[0], 429)

        print("-- Moving progress")
        s, h, exported = b.get("/api/progress/export")
        check("export downloads", ("attachment" in h["Content-Disposition"], "0003" in json.loads(exported)["lessons"]), (True, True))
        check("import rejects junk", b.post("/api/progress/import", {"lessons": []})[0], 400)

        print("-- A second person")
        b2 = Browser()
        b2.sign_in("222", "bo@example.com", "Bo", picture="https://evil.example/x.png")
        st2 = b2.state()
        check("picture from anywhere but Google is dropped", st2["user"]["picture"], "")
        check("Bo has separate, empty progress", (st2["user"]["name"], st2["completed"]), ("Bo", []))
        check("import into Bo", json.loads(b2.post("/api/progress/import", json.loads(exported))[1])["completed"], ["0001", "0003"])
        check("Bo can't see the overview", b2.get("/admin")[0], 404)
        check("Bo's first tutor request fits the shared limit", b2.post("/api/chat", {"lesson": "0003", "message": "hi"})[0], 200)
        s, body = b2.post("/api/chat", {"lesson": "0003", "message": "again"})
        check("shared daily limit reached", (s, "everyone" in body), (429, True))
        check("deleting needs the word delete", b2.post("/api/account/delete", {})[0], 400)
        check("Bo deletes his account", b2.post("/api/account/delete", {"confirm": "delete"})[0], 200)
        check("Bo is signed out and gone", b2.state()["signedIn"], False)
        b2.sign_in("222", "bo@example.com", "Bo")
        check("signing in again starts fresh", b2.state()["completed"], [])
        check("Ada unaffected by Bo", b.state()["user"]["email"], "ada@example.com")

        print("-- Refusals")
        b3 = Browser()
        s, _, body = b3.sign_in("333", "eve@example.com", "Eve")
        check("not on the allow list", (s, "invite-only" in body), (403, True))
        b4 = Browser()
        FakeGoogle.next_user = {"sub": "444", "email": "bo@example.com", "name": "Bo"}
        s, h, _ = b4.get("/auth/google?next=/", follow=False)
        google_url = h["Location"]
        b5 = Browser()  # a different browser opens the callback: no matching state cookie
        s, h, _ = b5.get(google_url, follow=False)
        s, _, body = b5.get(h["Location"])
        check("sign-in finished in another browser is refused", (s, "expired" in body), (400, True))
        check("off-site next is ignored", [app_auth.safe_next(x) for x in ("//evil.example", "https://evil.example", "/lessons/x")], ["/", "/", "/lessons/x"])

        print("-- Sign out")
        b.post("/auth/logout", {})
        check("signed out", b.state()["signedIn"], False)
    finally:
        app.terminate()
        app.wait()

    print("-- Without sign-in (on your own computer)")
    fresh_data(old)
    app = start_app({})
    try:
        b = Browser()
        st = b.state()
        check("local mode is signed in, no account", (st["auth"], st["signedIn"], st["user"]), (False, True, None))
        check("old progress kept", st["completed"], ["0001"])
        check("saving works", b.post("/api/complete", {"lesson": "0002"})[0], 200)
        check("no avatars without an account", b.post("/api/avatar", {"avatar": "coral-cat"})[0], 400)
        check("sign-in page goes home", b.get("/auth/google", follow=False)[1]["Location"], "/")
    finally:
        app.terminate()
        app.wait()
        google.shutdown()
        shutil.rmtree(ROOT / DATA, ignore_errors=True)

    print(f"\n{'All checks passed.' if not failures else f'{len(failures)} failed: ' + ', '.join(failures)}")
    sys.exit(1 if failures else 0)


def serve():
    """For looking at sign-in in a browser: the stand-in Google signs everyone in as Ada."""
    google = ThreadingHTTPServer(("127.0.0.1", GOOGLE_PORT), FakeGoogle)
    FakeGoogle.next_user = {"sub": "111", "email": "ada@example.com", "name": "Ada Lovelace", "picture": PHOTO}
    threading.Thread(target=google.serve_forever, daemon=True).start()
    fresh_data()
    app = start_app({"GOOGLE_CLIENT_ID": CLIENT_ID, "GOOGLE_CLIENT_SECRET": CLIENT_SECRET,
                     "GOOGLE_AUTH_URL": f"http://127.0.0.1:{GOOGLE_PORT}/auth",
                     "GOOGLE_TOKEN_URL": f"http://127.0.0.1:{GOOGLE_PORT}/token", "OWNER_EMAIL": "ada@example.com"})
    print(f"Test app with sign-in at {APP}", flush=True)
    try:
        app.wait()
    finally:
        app.terminate()


if __name__ == "__main__":
    serve() if "--serve" in sys.argv else main()
