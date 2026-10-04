"""Everyone's saved data, in one SQLite file: course.db in the data folder.

Tables:
  users     one row per person: a Google account, or "local" when sign-in is off
  progress  each person's progress document (see progress.py)
  sessions  which browsers are signed in (only a hash of each cookie is kept)
  pending   sign-ins that have gone to Google and not come back yet
  records   learning records, written when someone finishes a lesson
  usage     how many AI tutor requests each person made each day ("*" is everyone together)
  feedback  problems and suggestions people send from a lesson
"""

import hashlib
import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import date

from progress import Progress, normalise

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, email TEXT, name TEXT, created REAL, last_seen REAL);
CREATE TABLE IF NOT EXISTS progress (
    user_id TEXT PRIMARY KEY, data TEXT NOT NULL, updated REAL);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, created REAL, expires REAL);
CREATE TABLE IF NOT EXISTS pending (
    state TEXT PRIMARY KEY, verifier TEXT, nonce TEXT, next TEXT, created REAL);
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, lesson_id TEXT, created REAL, text TEXT);
CREATE TABLE IF NOT EXISTS usage (
    user_id TEXT, day TEXT, count INTEGER, PRIMARY KEY (user_id, day));
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, lesson_id TEXT, page TEXT, message TEXT, created REAL);
"""

SESSION_DAYS = 30
PENDING_SECONDS = 600


def token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class Store:
    def __init__(self, path):
        self.lock = threading.RLock()
        self.user_locks = {}
        self.db = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)
        # Databases made before profile pictures and avatars were added need the new columns.
        columns = [row[1] for row in self.db.execute("PRAGMA table_info(users)")]
        for column in ("picture", "avatar"):
            if column not in columns:
                self.db.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")

    def _query(self, sql, args=()):
        with self.lock:
            return self.db.execute(sql, args).fetchall()

    def _one(self, sql, args=()):
        rows = self._query(sql, args)
        return rows[0] if rows else None

    # ---------- People ----------
    def save_user(self, user_id, email="", name="", picture=""):
        t = time.time()
        self._query(
            "INSERT INTO users (id, email, name, picture, created, last_seen) VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET email = excluded.email, name = excluded.name, "
            "picture = excluded.picture, last_seen = excluded.last_seen",
            (user_id, email, name, picture, t, t))

    def user(self, user_id):
        row = self._one("SELECT id, email, name, picture, avatar FROM users WHERE id = ?", (user_id,))
        return row and {"id": row[0], "email": row[1], "name": row[2], "picture": row[3] or "", "avatar": row[4] or ""}

    def set_avatar(self, user_id, avatar):
        self._query("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id))

    # ---------- Progress ----------
    def _user_lock(self, user_id):
        with self.lock:
            return self.user_locks.setdefault(user_id, threading.Lock())

    def read_progress(self, user_id):
        """A snapshot to read from. Changes to it are not saved."""
        row = self._one("SELECT data FROM progress WHERE user_id = ?", (user_id,))
        return Progress(json.loads(row[0]) if row else {})

    @contextmanager
    def progress(self, user_id):
        """Load someone's progress to change it. Every change is saved straight away, and
        nobody else can change the same person's progress until the block ends."""
        with self._user_lock(user_id):
            yield Progress(self.read_progress(user_id).data, lambda data: self.replace_progress(user_id, data))

    def replace_progress(self, user_id, data):
        self._query(
            "INSERT INTO progress (user_id, data, updated) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET data = excluded.data, updated = excluded.updated",
            (user_id, json.dumps(normalise(data), ensure_ascii=False), time.time()))

    def has_progress(self, user_id):
        p = self.read_progress(user_id).data
        return bool(p["lessons"] or p["cards"] or p["chats"])

    # ---------- Sessions ----------
    def new_session(self, user_id, token):
        t = time.time()
        self._query("DELETE FROM sessions WHERE expires < ?", (t,))
        self._query("INSERT INTO sessions VALUES (?, ?, ?, ?)", (token_hash(token), user_id, t, t + SESSION_DAYS * 86400))

    def session_user(self, token):
        if not token:
            return None
        row = self._one("SELECT user_id FROM sessions WHERE token_hash = ? AND expires > ?", (token_hash(token), time.time()))
        return row[0] if row else None

    def end_session(self, token):
        if token:
            self._query("DELETE FROM sessions WHERE token_hash = ?", (token_hash(token),))

    # ---------- Sign-ins in progress ----------
    def add_pending(self, state, verifier, nonce, next_path):
        t = time.time()
        self._query("DELETE FROM pending WHERE created < ?", (t - PENDING_SECONDS,))
        self._query("INSERT INTO pending VALUES (?, ?, ?, ?, ?)", (state, verifier, nonce, next_path, t))

    def take_pending(self, state):
        """Return (verifier, nonce, next) for a sign-in, once only, or None if unknown or too old."""
        with self.lock:
            row = self._one("SELECT verifier, nonce, next, created FROM pending WHERE state = ?", (state,))
            self._query("DELETE FROM pending WHERE state = ?", (state,))
        if not row or row[3] < time.time() - PENDING_SECONDS:
            return None
        return row[:3]

    # ---------- Learning records ----------
    def add_record(self, user_id, lesson_id, text):
        self._query("INSERT INTO records (user_id, lesson_id, created, text) VALUES (?, ?, ?, ?)",
                    (user_id, lesson_id, time.time(), text))

    # ---------- AI usage ----------
    def use_ai(self, user_id, daily_limit, total_limit=0):
        """Count one AI request. Returns None if allowed, or "person" / "everyone" if that
        daily limit has been reached (a limit of 0 means no limit)."""
        day = date.today().isoformat()
        with self.lock:
            count = lambda who: (self._one("SELECT count FROM usage WHERE user_id = ? AND day = ?", (who, day)) or (0,))[0]
            if daily_limit and count(user_id) >= daily_limit:
                return "person"
            if total_limit and count("*") >= total_limit:
                return "everyone"
            for who in (user_id, "*"):
                self._query("INSERT INTO usage VALUES (?, ?, 1) ON CONFLICT(user_id, day) DO UPDATE SET count = count + 1",
                            (who, day))
            return None

    # ---------- Feedback ----------
    def add_feedback(self, user_id, lesson_id, page, message):
        self._query("INSERT INTO feedback (user_id, lesson_id, page, message, created) VALUES (?, ?, ?, ?, ?)",
                    (user_id, lesson_id, page, message, time.time()))

    def feedback(self, limit=200):
        rows = self._query(
            "SELECT f.created, f.lesson_id, f.page, f.message, COALESCE(u.email, f.user_id) FROM feedback f "
            "LEFT JOIN users u ON u.id = f.user_id ORDER BY f.id DESC LIMIT ?", (limit,))
        return [{"created": r[0], "lesson": r[1], "page": r[2], "message": r[3], "from": r[4]} for r in rows]

    # ---------- Overview for the owner ----------
    def stats(self):
        day = date.today().isoformat()
        one = lambda sql, args=(): (self._one(sql, args) or (0,))[0]
        return {
            "accounts": one("SELECT COUNT(*) FROM users WHERE id != 'local'"),
            "active_today": one("SELECT COUNT(*) FROM users WHERE last_seen > ?", (time.time() - 86400,)),
            "ai_requests_today": one("SELECT count FROM usage WHERE user_id = '*' AND day = ?", (day,)),
            "feedback": one("SELECT COUNT(*) FROM feedback"),
        }

    # ---------- Deleting an account ----------
    def delete_user(self, user_id):
        """Remove everything stored about one person. Feedback they sent is kept, without their name."""
        with self.lock:
            for table, column in (("sessions", "user_id"), ("progress", "user_id"), ("records", "user_id"),
                                  ("usage", "user_id"), ("users", "id")):
                self._query(f"DELETE FROM {table} WHERE {column} = ?", (user_id,))
            self._query("UPDATE feedback SET user_id = 'deleted' WHERE user_id = ?", (user_id,))

    def touch(self, user_id):
        self._query("UPDATE users SET last_seen = ? WHERE id = ?", (time.time(), user_id))
