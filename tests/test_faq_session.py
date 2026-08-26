"""Tests for tools/faq_build_session.py — bank, verdicts, artifacts, lock
(pure parts only; LLM callers are never invoked in tests)."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import db
import faq
import md_corpus
from faq_build_session import (
    build_numeric_bank,
    build_qual_bank,
    parse_judge,
    reject_question,
    render_numeric,
    rotate_backups,
    run_session,
    upsert_entry,
    write_artifacts,
)

FIXTURE = Path(__file__).parent / "fixtures" / "master_fixture.csv"


def _facts():
    return faq.compute_facts(FIXTURE)


def test_numeric_bank_expands_countries():
    bank = build_numeric_bank(_facts())
    keys = {b["ground_key"] for b in bank}
    assert {"rows", "columns.tier", "columns.kraj.PL", "columns.kraj.CZ",
            "flags_x_kraj.frozen|PL"} <= keys


def test_render_numeric_scalar_dict_missing():
    facts = _facts()
    assert render_numeric("rows", facts) == "6"
    assert render_numeric("columns.kraj.PL", facts) == "3"
    assert "hurtownik" in render_numeric("columns.tier", facts)
    assert render_numeric("nie.ma.takiej", facts) == "brak danych"


def test_parse_judge_verdicts():
    assert parse_judge("TAK, odpowiedź jest zgodna z danymi.") is True
    assert parse_judge("Nie.") is False
    assert parse_judge("Nie wiem, trudno ocenić.") is None
    assert parse_judge("Może być.") is None


def test_qual_bank_seeds_and_headings(tmp_path, monkeypatch):
    corpus = tmp_path / "md"
    corpus.mkdir()
    (corpus / "01-a.md").write_text(
        "## Rynek hurtowy w Polsce\ntekst\n### Duzi hurtownicy\n", encoding="utf-8")
    monkeypatch.setattr(md_corpus, "CORPUS_DIR", corpus)
    monkeypatch.setattr(md_corpus, "INBOX_DIR", corpus / "inbox")
    monkeypatch.setattr(md_corpus, "_cache", {})
    questions = build_qual_bank(None)
    assert "Rynek hurtowy w Polsce" in questions
    assert "Duzi hurtownicy" in questions
    assert any("weryfikacji" in q for q in questions)      # seeds present
    assert build_qual_bank("01-a.md") == ["Rynek hurtowy w Polsce", "Duzi hurtownicy"]


def test_rejects_and_upsert(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    db.init()
    reject_question("Ile firm w PL?", "judge rejected twice")
    reject_question("Ile firm w PL?", "again")             # UNIQUE — no crash
    upsert_entry({"id": "e1", "q": "Q?", "a": "A", "category": "c",
                  "sources": "[]", "ground_key": None, "verified_kind": "judge",
                  "judge_model": "x", "verified_at": "t", "created_at": "t"})
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM faq_rejects").fetchone()["n"] == 1
        assert conn.execute("SELECT hits FROM faq_entries WHERE id='e1'").fetchone()["hits"] == 0


def test_artifacts_and_backup_rotation(tmp_path, monkeypatch):
    import faq_build_session as fbs

    monkeypatch.setattr(fbs, "ARTIFACT_JSON", tmp_path / "faq.json")
    monkeypatch.setattr(fbs, "ARTIFACT_CSV", tmp_path / "faq.csv")
    entries = [{"id": "e1", "q": "Q?", "a": "A", "category": "c", "sources": "[]",
                "ground_key": None, "verified_kind": "numeric", "judge_model": None,
                "verified_at": "t"}]
    write_artifacts(entries)
    assert (tmp_path / "faq.json").exists() and (tmp_path / "faq.csv").exists()
    for _ in range(7):                            # 7 rebuilds → 5 backups kept
        write_artifacts(entries)
    assert len(list(tmp_path.glob("faq-*.json"))) == 5


def test_run_session_conflict_when_running(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    db.init()
    with db.connect() as conn:
        conn.execute("UPDATE faq_session SET state='running' WHERE id=1")
    assert asyncio.run(run_session("full", None, force=False)) == 3
