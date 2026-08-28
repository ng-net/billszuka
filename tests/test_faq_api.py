"""API tests for the FAQ layer — chat integration, endpoints, auth."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api_server
import db
import faq
import md_corpus

FIXTURE = Path(__file__).parent / "fixtures" / "master_fixture.csv"


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(api_server, "ROOT", tmp_path)
    monkeypatch.setattr(api_server, "DATA", tmp_path)
    monkeypatch.setattr(api_server, "SECRETS_PATH", tmp_path / "api_secrets.json")
    monkeypatch.setattr(api_server, "KNOWLEDGE_DIR", tmp_path / "knowledge")
    monkeypatch.setattr(api_server, "KNOWLEDGE_FILES_DIR", tmp_path / "knowledge" / "files")
    monkeypatch.setattr(api_server, "KNOWLEDGE_INDEX_PATH", tmp_path / "knowledge" / "index.json")
    monkeypatch.setattr(faq, "MASTER_CSV", FIXTURE)
    monkeypatch.setattr(faq, "PHRASES_PATH", tmp_path / "save-phrases.json")
    monkeypatch.setattr(faq, "_facts_cache", (None, None))   # clear cache for isolation
    monkeypatch.setattr(md_corpus, "CORPUS_DIR", tmp_path / "knowledge" / "md")
    monkeypatch.setattr(md_corpus, "INBOX_DIR", tmp_path / "knowledge" / "md" / "inbox")
    monkeypatch.setattr(md_corpus, "_cache", {})
    monkeypatch.setattr(api_server, "_chat_mock",
                        lambda req: api_server.ChatResponse(response="MOCK-ODP", provider="mock"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY_1", "")
    (tmp_path / "frontend-2" / "public").mkdir(parents=True)
    (tmp_path / "frontend-2" / "public" / "access.json").write_text(
        json.dumps({"names": [hashlib.sha256(b"marceli").hexdigest()]}), encoding="utf-8")
    (tmp_path / "save-phrases.json").write_text(
        json.dumps({"pl": ["zapisz ten fakt"], "en": ["save this"]}), encoding="utf-8")
    db.init()   # conftest autouse fixture already pointed DB_PATH at a throwaway file
    return TestClient(api_server.app)


def _headers(name="marceli"):
    return {"X-Billszuka-User": name}


def _seed_entry(entry_id="e1", q="Ile firm jest w katalogu?", a="SZEŚĆ",
                sources="[]", kind="numeric"):
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO faq_entries (id, q, a, category, sources, verified_kind, "
            "created_at, hits) VALUES (?, ?, ?, 'dane', ?, ?, 't', 0)",
            (entry_id, q, a, sources, kind))


def test_chat_miss_uses_chain_and_logs(client):
    r = client.post("/api/chat", json={"query": "co to jest maszynka do tytoniu"})
    assert r.status_code == 200 and r.json()["provider"] == "mock"
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM chat_log").fetchone()["n"] == 1


def test_chat_faq_hit_zero_llm(client):
    _seed_entry()
    r = client.post("/api/chat", json={"query": "ile firm jest w katalogu"})
    body = r.json()
    assert body["provider"] == "faq" and body["response"] == "SZEŚĆ"
    with db.connect() as conn:
        assert conn.execute("SELECT hits FROM faq_entries WHERE id='e1'").fetchone()["hits"] == 1


# Captured BEFORE the fixture monkeypatches _chat_mock, so the nudge-text
# regression test can verify the real default (regression: the old text
# blamed OPENROUTER_API_KEY while the quota note blamed Gemini — two
# contradictory explanations in one answer).
REAL_CHAT_MOCK = api_server._chat_mock


def test_mock_default_text_is_provider_agnostic(client, monkeypatch):
    monkeypatch.setattr(api_server, "_chat_mock", REAL_CHAT_MOCK)
    r = api_server._chat_mock(api_server.ChatRequest(
        query="opowiedz coś o projekcie", active_dataset="master.csv", knowledge_ids=[]))
    assert "OPENROUTER_API_KEY not configured" not in r.response
    assert "100 pytań do…" in r.response


def test_gemini_quota_note_is_coherent(client, tmp_path, monkeypatch):
    (tmp_path / "api_secrets.json").write_text(json.dumps({
        "priority": ["gemini", "mock", "openrouter"],
        "gemini": [{"key": "AIza-TEST"}],
        "openrouter": [],
    }), encoding="utf-8")

    async def no_gemini(req, key):
        return None

    monkeypatch.setattr(api_server, "_call_gemini", no_gemini)
    monkeypatch.setattr(api_server, "_last_call_was_quota", lambda: True)
    r = client.post("/api/chat", json={"query": "opowiedz coś o projekcie"})
    body = r.json()
    assert body["provider"] == "mock-gemini-quota"
    assert "OPENROUTER_API_KEY not configured" not in body["response"]
    assert "FAQ" in body["response"]


def test_chat_faq_stale_numeric_falls_through(client):
    _seed_entry(q="Ile firm jest w katalogu?", sources='["master.csv"]')
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO faq_meta (key, value) VALUES ('source_digests', '{\"master.csv\": \"stary\"}')")
    r = client.post("/api/chat", json={"query": "ile firm jest w katalogu"})
    assert r.json()["provider"] == "mock"          # fell through — no stale number served


def test_save_command_writes_inbox(client):
    client.post("/api/chat", json={"query": "co to jest maszynka"}, headers=_headers())
    r = client.post("/api/chat", json={"query": "zapisz ten fakt"}, headers=_headers())
    body = r.json()
    assert body["provider"] == "save" and "Zapisano" in body["response"]
    files = list(md_corpus.INBOX_DIR.glob("fact-*.md"))
    assert len(files) == 1
    assert "saved_by: marceli" in files[0].read_text(encoding="utf-8")


def test_save_command_without_last_answer_falls_through(client):
    r = client.post("/api/chat", json={"query": "zapisz ten fakt"}, headers=_headers())
    assert r.json()["provider"] != "save"


def test_generate_requires_user_and_locks(client, monkeypatch):
    calls = []
    monkeypatch.setattr(api_server.subprocess, "Popen",
                        lambda *a, **k: calls.append(a) or type("P", (), {"pid": 1})())
    assert client.post("/api/faq/generate", json={"mode": "full"}).status_code == 403
    assert client.post("/api/faq/generate", json={"mode": "full"},
                       headers={"X-Billszuka-User": "hacker"}).status_code == 403
    ok = client.post("/api/faq/generate", json={"mode": "full"}, headers=_headers())
    assert ok.status_code == 200 and ok.json()["state"] == "running"
    assert len(calls) == 1
    conflict = client.post("/api/faq/generate", json={"mode": "full"}, headers=_headers())
    assert conflict.status_code == 409


def test_delete_faq_verified_and_blocks(client):
    _seed_entry()
    assert client.delete("/api/faq/e1").status_code == 403
    assert client.delete("/api/faq/e1", headers=_headers()).status_code == 200
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM faq_entries").fetchone()["n"] == 0
        row = conn.execute("SELECT q_norm FROM faq_rejects").fetchone()
        assert row and row["q_norm"] == "ile firm jest w katalogu"


def test_faq_list_and_session(client):
    _seed_entry()
    r = client.get("/api/faq")
    assert r.status_code == 200
    assert r.json()["items"][0]["q"] == "Ile firm jest w katalogu?"
    assert client.get("/api/faq/session").json()["state"] in {"idle", "running", "done"}


def test_knowledge_upload_marks_uploaded_by(client, monkeypatch):
    monkeypatch.setattr(api_server, "_get_first_gemini_key", lambda: "fake-key")
    monkeypatch.setattr(api_server, "_gemini_files_upload",
                        lambda *a, **k: {"name": "files/x", "uri": "u", "state": "ACTIVE"})
    files = {"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")}
    assert client.post("/api/knowledge/upload", files=files).status_code == 403
    r = client.post("/api/knowledge/upload", files=files, headers=_headers())
    assert r.status_code == 200
    assert r.json()["uploaded_by"] == "marceli"
