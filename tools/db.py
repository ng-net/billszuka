#!/usr/bin/env python3
"""SQLite store (stdlib) for FAQ entries, chat log, knowledge metadata,
rejects blocklist and the single-flight session row.

WAL + busy_timeout make the rare concurrent write safe; the session row
is claimed with an atomic UPDATE so only one generation session runs.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "billszuka.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS faq_entries (
  id TEXT PRIMARY KEY,
  q TEXT NOT NULL,
  a TEXT NOT NULL,
  category TEXT,
  sources TEXT NOT NULL DEFAULT '[]',
  ground_key TEXT,
  verified_kind TEXT NOT NULL,
  judge_model TEXT,
  verified_at TEXT,
  created_at TEXT NOT NULL,
  hits INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS faq_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS faq_session (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  state TEXT NOT NULL DEFAULT 'idle',
  mode TEXT,
  progress TEXT,
  report TEXT,
  checkpoint TEXT,
  updated_at TEXT
);
CREATE TABLE IF NOT EXISTS chat_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  user TEXT,
  query TEXT NOT NULL,
  response TEXT,
  provider TEXT,
  dataset TEXT,
  knowledge_ids TEXT,
  faq_hit INTEGER,
  sources TEXT
);
CREATE TABLE IF NOT EXISTS knowledge_inbox (
  file TEXT PRIMARY KEY,
  saved_by TEXT,
  question TEXT,
  content_hash TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending',
  saved_at TEXT
);
CREATE TABLE IF NOT EXISTS faq_rejects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  q TEXT NOT NULL,
  q_norm TEXT NOT NULL UNIQUE,
  reason TEXT,
  rejected_at TEXT
);
CREATE TABLE IF NOT EXISTS catalog_files (
  filename TEXT PRIMARY KEY,
  uploaded_by TEXT NOT NULL,
  uploaded_at TEXT NOT NULL,
  size_bytes INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS user_logins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user TEXT NOT NULL,
  company TEXT,
  login_at TEXT NOT NULL,
  user_agent TEXT,
  ip TEXT
);
CREATE INDEX IF NOT EXISTS idx_chat_log_user_ts ON chat_log (user, ts DESC);
CREATE INDEX IF NOT EXISTS idx_user_logins_user ON user_logins (user, login_at DESC);
CREATE INDEX IF NOT EXISTS idx_catalog_files_user ON catalog_files (uploaded_by);
-- Per-user identity + activity (added 2026-08-30, restored 2026-08-31).
-- Layered on top of Basic Auth: anyone with the team password can hit
-- /api/*, but per-user features (bookmarks, soft-delete, knowledge
-- attribution, activity) require a logged-in session.
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  display_name TEXT,
  invite_code_hash TEXT,
  role TEXT NOT NULL DEFAULT 'member',
  created_at TEXT NOT NULL,
  last_seen_at TEXT,
  disabled_at TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  user_agent TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE TABLE IF NOT EXISTS user_activity (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  session_id TEXT,
  kind TEXT NOT NULL,
  lead_id TEXT,
  target_kind TEXT,
  target_id TEXT,
  payload TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_activity_user_ts ON user_activity(user_id, ts DESC);
CREATE TABLE IF NOT EXISTS bookmarks (
  user_id INTEGER NOT NULL,
  lead_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  note TEXT,
  PRIMARY KEY (user_id, lead_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS lead_deletions (
  user_id INTEGER NOT NULL,
  lead_id TEXT NOT NULL,
  deleted_at TEXT NOT NULL,
  reason TEXT,
  PRIMARY KEY (user_id, lead_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS keyword_scan (
  id TEXT NOT NULL,
  kraj TEXT NOT NULL,
  url TEXT NOT NULL,
  keywords_found TEXT NOT NULL DEFAULT '[]',   -- JSON array of hit strings
  keywords_total INTEGER NOT NULL DEFAULT 0,   -- ile słów w słowniku (denominator)
  score_pct INTEGER NOT NULL DEFAULT 0,        -- 0-100
  http_code INTEGER,
  html_size INTEGER,
  error TEXT,
  scanned_at TEXT NOT NULL,
  PRIMARY KEY (id, url)
);
CREATE INDEX IF NOT EXISTS idx_keyword_scan_kraj ON keyword_scan (kraj);
CREATE INDEX IF NOT EXISTS idx_keyword_scan_score ON keyword_scan (score_pct);
CREATE TABLE IF NOT EXISTS url_status (
  id TEXT NOT NULL,
  kraj TEXT NOT NULL,
  url TEXT NOT NULL,
  status TEXT NOT NULL,           -- 'green' | 'red' | 'unknown' (high-level)
  state TEXT NOT NULL,            -- 'ok' | 'redirect' | '4xx' | '5xx' | 'timeout' | 'ssl' | 'dns' | 'empty' | 'unknown'
  http_code INTEGER,
  redirect_url TEXT,              -- URL po follow-redirects (jeśli był redirect)
  response_ms INTEGER,            -- czas odpowiedzi w ms
  error TEXT,
  checked_at TEXT NOT NULL,
  PRIMARY KEY (id, url)
);
CREATE INDEX IF NOT EXISTS idx_url_status_kraj ON url_status (kraj);
CREATE INDEX IF NOT EXISTS idx_url_status_status ON url_status (status);
-- Note: idx_url_status_state is created in init() AFTER ALTER TABLE,
-- because sqlite CREATE INDEX fails if the column doesn't exist yet
-- (and IF NOT EXISTS doesn't help here).
"""


@contextmanager
def connect(db_path: Path | str | None = None):
    # NOTE: default resolved at call time (not a bound default arg) so
    # tests can monkeypatch db.DB_PATH.
    # The plan returned the raw Connection — its `with` protocol commits
    # but never CLOSES, so every statement emitted "unclosed database"
    # ResourceWarnings via GC (fatal under pytest filterwarnings=error).
    # Wrapping in a context manager preserves commit-on-success semantics
    # and closes the handle deterministically.
    path = Path(db_path) if db_path is not None else DB_PATH
    conn = sqlite3.connect(str(path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    except BaseException:
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        conn.close()


def init(db_path: Path | str | None = None) -> None:
    with connect(db_path) as conn:
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT OR IGNORE INTO faq_session (id, state, updated_at) "
            "VALUES (1, 'idle', '')"
        )
        # Idempotent migrations for existing tables (sqlite doesn't have IF NOT EXISTS for ADD COLUMN)
        for stmt in [
            "ALTER TABLE url_status ADD COLUMN state TEXT NOT NULL DEFAULT 'unknown'",
            "ALTER TABLE url_status ADD COLUMN redirect_url TEXT",
            "ALTER TABLE url_status ADD COLUMN response_ms INTEGER",
        ]:
            try:
                conn.execute(stmt)
            except Exception:
                pass  # column already exists
        # Index na state — po ALTER, bo sqlite wywala CREATE INDEX na nieistniejącej kolumnie
        conn.execute("CREATE INDEX IF NOT EXISTS idx_url_status_state ON url_status (state)")


def claim_session(db_path: Path | str | None = None, force: bool = False) -> bool:
    """Atomically claim the single-flight session row. True = we own it.
    Claimable from any state except 'running'; force recovers a stuck row
    (a SIGKILLed runner left state='running')."""
    where = "id=1" if force else "id=1 AND state != 'running'"
    with connect(db_path) as conn:
        cur = conn.execute(
            f"UPDATE faq_session SET state='running', updated_at=datetime('now') "
            f"WHERE {where}"
        )
        return cur.rowcount == 1
