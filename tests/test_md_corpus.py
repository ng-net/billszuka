"""Tests for tools/md_corpus.py — load, inject, inbox save, sanitization."""
from __future__ import annotations

import db
import md_corpus


def _setup(tmp_path, monkeypatch):
    corpus = tmp_path / "md"
    inbox = corpus / "inbox"
    corpus.mkdir(parents=True)
    (corpus / "01-a.md").write_text("treść pierwszego pliku", encoding="utf-8")
    (corpus / "02-b.md").write_text("treść drugiego", encoding="utf-8")
    monkeypatch.setattr(md_corpus, "CORPUS_DIR", corpus)
    monkeypatch.setattr(md_corpus, "INBOX_DIR", inbox)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    db.init()
    return corpus


def test_load_corpus_lists_md_files(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    names = [n for n, _ in md_corpus.load_corpus()]
    assert names == ["01-a.md", "02-b.md"]


def test_inject_corpus_labeled_blocks_and_budget(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    blocks = md_corpus.inject_corpus([])
    assert len(blocks) == 2
    assert blocks[0].startswith("[DOKUMENT: 01-a.md]")
    assert blocks[0].endswith("[/DOKUMENT]")
    # tiny budget → first file gets truncated with a note, second skipped
    blocks = md_corpus.inject_corpus([], budget_tokens=10)
    assert len(blocks) == 1
    assert "[obcięto" in blocks[0]


def test_inject_corpus_respects_reserved_chars(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    blocks = md_corpus.inject_corpus([], budget_tokens=100, reserved_chars=90_000)
    assert blocks == []


def test_sanitize_component_blocks_path_traversal():
    assert md_corpus.sanitize_component("../../etc/passwd") == "etc_passwd"
    assert md_corpus.sanitize_component("jaro!@#") == "jaro"
    assert md_corpus.sanitize_component("") == "doc"


def test_save_fact_to_inbox_with_dedupe(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    ok, msg = md_corpus.save_fact_to_inbox("fakt A", "pytanie?", ["master.csv"], "marceli")
    assert ok and "marceli" in msg
    ok2, msg2 = md_corpus.save_fact_to_inbox("fakt A", "pytanie?", ["master.csv"], "jaro")
    assert not ok2 and "już" in msg2
    # header carries provenance
    files = list(md_corpus.INBOX_DIR.glob("fact-*.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "saved_by: marceli" in text and "pytanie?" in text
