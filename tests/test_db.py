"""Tests for tools/db.py — schema, atomic counters, single-flight claim."""
from __future__ import annotations

import sqlite3

import db


def _tmp_db(tmp_path):
    db.init(tmp_path / "t.db")
    return tmp_path / "t.db"


def test_init_creates_all_tables(tmp_path):
    db.init(tmp_path / "t.db")
    with db.connect(tmp_path / "t.db") as conn:
        names = {r["name"] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"faq_entries", "faq_meta", "faq_session", "chat_log",
            "knowledge_inbox", "faq_rejects"} <= names


def test_hits_increment_is_atomic(tmp_path):
    path = _tmp_db(tmp_path)
    with db.connect(path) as conn:
        conn.execute(
            "INSERT INTO faq_entries (id, q, a, category, sources, verified_kind, created_at, hits) "
            "VALUES ('e1', 'q', 'a', 'c', '[]', 'numeric', 'now', 0)")
    # two separate connections, interleaved increments — nothing lost
    with db.connect(path) as a, db.connect(path) as b:
        a.execute("UPDATE faq_entries SET hits = hits + 1 WHERE id='e1'")
        a.commit()
        b.execute("UPDATE faq_entries SET hits = hits + 1 WHERE id='e1'")
        b.commit()
    with db.connect(path) as conn:
        hits = conn.execute("SELECT hits FROM faq_entries WHERE id='e1'").fetchone()["hits"]
    assert hits == 2


def test_upsert_preserves_hits(tmp_path):
    path = _tmp_db(tmp_path)
    with db.connect(path) as conn:
        conn.execute(
            "INSERT INTO faq_entries (id, q, a, category, sources, verified_kind, created_at, hits) "
            "VALUES ('e1', 'q', 'a', 'c', '[]', 'numeric', 'now', 7)")
    with db.connect(path) as conn:
        conn.execute(
            "INSERT INTO faq_entries (id, q, a, category, sources, verified_kind, created_at, hits) "
            "VALUES ('e1', 'q2', 'a2', 'c', '[]', 'numeric', 'now2', 0) "
            "ON CONFLICT(id) DO UPDATE SET q=excluded.q, a=excluded.a")
    with db.connect(path) as conn:
        row = conn.execute("SELECT hits, q FROM faq_entries WHERE id='e1'").fetchone()
    assert row["hits"] == 7   # rebuild never clobbers hits
    assert row["q"] == "q2"


def test_rejects_are_unique(tmp_path):
    path = _tmp_db(tmp_path)
    with db.connect(path) as conn:
        conn.execute("INSERT INTO faq_rejects (q, q_norm, reason) VALUES ('a', 'a', 'judge')")
        with __import__("pytest").raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO faq_rejects (q, q_norm, reason) VALUES ('b', 'a', 'judge')")


def test_claim_session_single_flight(tmp_path):
    path = _tmp_db(tmp_path)
    assert db.claim_session(path) is True      # idle → running
    assert db.claim_session(path) is False     # running → nobody else
    assert db.claim_session(path, force=True) is True   # force recovers stuck
    with db.connect(path) as conn:
        conn.execute("UPDATE faq_session SET state='done' WHERE id=1")
    assert db.claim_session(path) is True      # done → running (re-run allowed)


def test_claim_session_resumes_interrupted(tmp_path):
    path = _tmp_db(tmp_path)
    with db.connect(path) as conn:
        conn.execute("UPDATE faq_session SET state='interrupted' WHERE id=1")
    assert db.claim_session(path) is True
