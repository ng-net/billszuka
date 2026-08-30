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
