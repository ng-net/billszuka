"""
test_api_server.py — Tests for tools/api_server.py.

Uses FastAPI's TestClient (synchronous wrapper over httpx).
The `tmp_data` fixture points the server at a temp dir so we don't pollute
the real `data/` directory during tests.
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_data(monkeypatch, tmp_path):
    """Redirect DATA to a temp dir; pre-populate with test CSVs.

    Seeds BOTH catalog-A-PL.csv (for /api/sync tests) AND master.csv
    (for /api/chat tests — chat is master.csv-only as of 2026-08-30).
    The chat tests no longer depend on test ordering vs sync tests."""
    import api_server
    monkeypatch.setattr(api_server, "DATA", tmp_path)
    # Build a fake country structure
    pl = tmp_path / "Polska"
    pl.mkdir()
    with (pl / "catalog-A-PL.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kraj", "nazwa_firmy", "nip_vat", "flagi"])
        w.writerow(["PL", "BILLS SP ZOO", "PL1234567890", "FROZEN"])
        w.writerow(["PL", "TEST SA", "PL9999999999", "DO-WERYFIKACJI"])
    (tmp_path / "sales_data.csv").write_text("month,revenue\n2026-01,1000\n2026-02,2000\n")
    # Seed master.csv directly so /api/chat tests can pass active_dataset=
    # "master.csv" without first hitting /api/sync to regenerate it.
    with (tmp_path / "master.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kraj", "nazwa_firmy", "nip_vat", "flagi"])
        w.writerow(["PL", "BILLS SP ZOO", "PL1234567890", "FROZEN"])
        w.writerow(["PL", "TEST SA", "PL9999999999", "DO-WERYFIKACJI"])
    return tmp_path


@pytest.fixture
def client(tmp_data, monkeypatch, tmp_path):
    """Build a TestClient with the temp DATA dir, force-mock chat.

    The api_server reads OPENROUTER_API_KEY from .env as a fallback (after
    os.environ). To force the mock path, we point api_server.ROOT at a
    temp dir that has no .env file. The secrets vault is also pointed
    at an isolated path so persisted keys from real runs don't leak in.
    """
    import api_server
    import tools.api_server as tools_api_server  # noqa: F401 — same module, but `api_server` is the bare-name binding
    import verify_run
    # Force the chat endpoint into mock mode for tests (no real LLM)
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    # No .env file in this tmp ROOT → fallback finds nothing
    isolated_root = tmp_path / "isolated_root"
    isolated_root.mkdir()
    monkeypatch.setattr(api_server, "ROOT", isolated_root)
    monkeypatch.setattr(api_server, "DATA", tmp_path)
    # Isolated secrets vault so persisted keys from real runs don't leak in.
    # IMPORTANT: api_server functions resolve SECRETS_PATH via their
    # __globals__ (== api_server.__dict__), so patching `api_server.SECRETS_PATH`
    # works. But avoid importing as a fresh `tools.api_server` alias in the
    # test bodies — that's a DIFFERENT module object in sys.modules.
    monkeypatch.setattr(api_server, "SECRETS_PATH", isolated_root / "api_secrets.json")
    # And ensure regenerate_master() writes to our tmp dir, not the real one
    monkeypatch.setattr(verify_run, "DATA", tmp_data)
    monkeypatch.setattr(verify_run, "MASTER_CSV", tmp_data / "master.csv")
    # Ensure access.json exists with marceli's hash for auth
    import hashlib
    import json
    import db
    db.init()
    (isolated_root / "frontend-2" / "public").mkdir(parents=True, exist_ok=True)
    (isolated_root / "frontend-2" / "public" / "access.json").write_text(
        json.dumps({"names": [hashlib.sha256(b"marceli").hexdigest()]}), encoding="utf-8"
    )
    return TestClient(api_server.app)


# ---------------------------------------------------------------------------
# Secrets bootstrap
# ---------------------------------------------------------------------------


def test_read_env_keys_prefers_runtime_env(monkeypatch, tmp_path):
    import api_server

    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENROUTER_API_KEY=sk-or-local\n"
        "GEMINI_API_KEY_1=AIza-local\n"
        "GEMINI_API_KEY_2=AIza-local-two\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(api_server, "ROOT", tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-prod")
    monkeypatch.setenv("GEMINI_API_KEY_1", "AIza-prod")

    keys = api_server._read_env_keys()

    assert keys["openrouter"][0] == {
        "alias": "primary",
        "key": "sk-or-prod",
        "source": "env",
    }
    assert {entry["alias"]: entry["source"] for entry in keys["gemini"]} == {
        "env-1": "env",
        "env-2": ".env",
    }
    assert {entry["alias"]: entry["key"] for entry in keys["gemini"]} == {
        "env-1": "AIza-prod",
        "env-2": "AIza-local-two",
    }


# ---------------------------------------------------------------------------
# /api/datasets
# ---------------------------------------------------------------------------

class TestDatasets:
    def test_lists_master_and_catalogs(self, client):
        r = client.get("/api/datasets")
        assert r.status_code == 200
        data = r.json()
        assert "datasets" in data
        names = [d["filename"] for d in data["datasets"]]
        # sales_data should be there
        assert "sales_data.csv" in names
        # catalog from Polska subdir
        assert "catalog-A-PL.csv" in names

    def test_count_field_present(self, client):
        r = client.get("/api/datasets")
        assert r.status_code == 200
        assert r.json()["count"] == len(r.json()["datasets"])


# ---------------------------------------------------------------------------
# /api/dataset/{filename}
# ---------------------------------------------------------------------------

class TestDatasetDetail:
    def test_reads_catalog(self, client):
        r = client.get("/api/dataset/catalog-A-PL.csv")
        assert r.status_code == 200
        data = r.json()
        assert data["filename"] == "catalog-A-PL.csv"
        assert data["columns"] == ["kraj", "nazwa_firmy", "nip_vat", "flagi"]
        assert data["total_rows"] == 2
        assert len(data["data"]) == 2
        assert data["data"][0][1] == "BILLS SP ZOO"

    def test_404_for_missing_file(self, client):
        r = client.get("/api/dataset/nonexistent.csv")
        assert r.status_code == 404

    def test_path_traversal_blocked(self, client):
        r = client.get("/api/dataset/..%2F..%2Fetc%2Fpasswd")
        # URL-decoded: "../../etc/passwd" — must be rejected
        assert r.status_code in (400, 404)  # validation or not-found

    def test_non_csv_rejected(self, client):
        r = client.get("/api/dataset/foo.txt")
        assert r.status_code == 400

    def test_limit_caps_rows(self, client):
        r = client.get("/api/dataset/catalog-A-PL.csv?limit=1")
        assert r.status_code == 200
        assert len(r.json()["data"]) == 1
        assert r.json()["total_rows"] == 2  # total still full count

    def test_limit_too_large(self, client):
        r = client.get("/api/dataset/catalog-A-PL.csv?limit=99999")
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/upload
# ---------------------------------------------------------------------------

class TestUpload:
    def test_upload_success(self, client, tmp_data):
        body = "kraj,nazwa\nPL,NEW CO\n"
        r = client.post(
            "/api/upload",
            files={"file": ("new_upload.csv", io.BytesIO(body.encode()), "text/csv")},
            headers={"X-Billszuka-User": "marceli"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        assert data["filename"] == "new_upload.csv"
        # File should actually be on disk in user catalogs directory
        user_catalog = tmp_data / "users" / "marceli" / "catalogs" / "new_upload.csv"
        assert user_catalog.exists()
        assert user_catalog.read_text() == body

    def test_duplicate_rejected(self, client, tmp_data):
        # Create existing catalog for marceli
        cat_dir = tmp_data / "users" / "marceli" / "catalogs"
        cat_dir.mkdir(parents=True, exist_ok=True)
        (cat_dir / "sales_data.csv").write_text("month,revenue\n2026-01,1000\n")
        body = "month,revenue\n2026-03,3000\n"
        r = client.post(
            "/api/upload",
            files={"file": ("sales_data.csv", io.BytesIO(body.encode()), "text/csv")},
            headers={"X-Billszuka-User": "marceli"},
        )
        assert r.status_code == 409
        # Original content must not be overwritten
        assert (cat_dir / "sales_data.csv").read_text().startswith("month,revenue\n2026-01")

    def test_non_csv_rejected(self, client):
        r = client.post(
            "/api/upload",
            files={"file": ("evil.txt", io.BytesIO(b"hello"), "text/plain")},
            headers={"X-Billszuka-User": "marceli"},
        )
        assert r.status_code == 400

    def test_path_traversal_rejected(self, client):
        r = client.post(
            "/api/upload",
            files={"file": ("../escape.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")},
            headers={"X-Billszuka-User": "marceli"},
        )
        assert r.status_code == 400

    def test_hidden_filename_rejected(self, client):
        r = client.post(
            "/api/upload",
            files={"file": (".hidden.csv", io.BytesIO(b"a,b\n"), "text/csv")},
            headers={"X-Billszuka-User": "marceli"},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/sync
# ---------------------------------------------------------------------------

class TestSync:
    def test_sync_regenerates_master(self, client, tmp_data):
        # master.csv must not exist yet — remove the seed from tmp_data
        # fixture so we exercise the regen path, not the seed path.
        (tmp_data / "master.csv").unlink()
        r = client.post("/api/sync", json={"source_type": "master"})
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["master_rows"] == 2  # catalog-A-PL.csv has 2 data rows
        assert (tmp_data / "master.csv").exists()

    def test_sync_invalid_source(self, client, monkeypatch):
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: type("Proc", (), {"stdout": "mock tail", "returncode": 0})(),
        )
        r = client.post("/api/sync", json={})  # default source_type="all"
        # Should still work — defaults are sensible
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# /api/chat
# ---------------------------------------------------------------------------

class TestChat:
    def test_empty_query_rejected(self, client):
        r = client.post("/api/chat", json={"query": ""})
        assert r.status_code == 400

    def test_count_query(self, client):
        r = client.post("/api/chat", json={
            "query": "ile firm jest w tym datasecie?",
            "active_dataset": "master.csv",
        })
        assert r.status_code == 200
        data = r.json()
        # 2 rows in the fixture
        assert "2" in data["response"]
        # No OPENROUTER_API_KEY in this test env → mock
        assert data["provider"] == "mock"

    def test_status_query(self, client):
        r = client.post("/api/chat", json={
            "query": "pokaż status frozen",
            "active_dataset": "master.csv",
        })
        assert r.status_code == 200
        data = r.json()
        # 1 FROZEN, 1 DO-WERYFIKACJI in fixture
        assert "FROZEN=1" in data["response"]
        assert "DO-WERYFIKACJI=1" in data["response"]

    def test_missing_dataset(self, client):
        # Per project policy /api/chat is master.csv-only — any other
        # dataset (real or ghost) gets a 400 with an actionable hint.
        r = client.post("/api/chat", json={
            "query": "ile firm?",
            "active_dataset": "ghost.csv",
        })
        assert r.status_code == 400
        assert "master.csv" in r.json()["detail"]

    def test_generic_query_returns_nudge(self, client):
        r = client.post("/api/chat", json={
            "query": "co sądzisz o życiu?",
            "active_dataset": "master.csv",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["provider"] == "mock"
        assert "Mock AI" in data["response"] or "Spróbuj pytań" in data["response"]

    def test_country_grouping(self, client):
        r = client.post("/api/chat", json={
            "query": "rozkład wg kraj",
            "active_dataset": "master.csv",
        })
        assert r.status_code == 200
        data = r.json()
        # All rows are PL
        assert "PL" in data["response"]



    def test_chat_allows_master_csv(self, client):
        # Sanity check: the master.csv guard is permissive for the
        # canonical dataset (default behavior preserved).
        r = client.post("/api/chat", json={
            "query": "ile firm jest w tym datasecie?",
            "active_dataset": "master.csv",
        })
        assert r.status_code == 200

    def test_chat_rejects_uploaded_csv_with_hint(self, client):
        # Uploaded/temporary datasets are session-only — questions about
        # them never grow into persistent knowledge, so the LLM chain
        # refuses. The error points the user at the proposal queue.
        r = client.post("/api/chat", json={
            "query": "ile firm?",
            "active_dataset": "uploaded.csv",
        })
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert "master.csv" in detail
        assert "proponuj" in detail.lower() or "wyszukiwark" in detail.lower()


# ---------------------------------------------------------------------------
# /api/chat/propose — admin proposal queue for new follow-up questions
# ---------------------------------------------------------------------------

class TestChatPropose:
    """Follow-up pills and user-typed questions can be added to the admin
    proposal queue (data/proposals/queue.jsonl). The admin of BILLSzuka
    reviews pending entries and folds approved ones into the FAQ / KB.

    Only master.csv-rooted questions can be proposed — uploaded CSVs are
    session-only and never become persistent knowledge."""

    PROPOSALS_PATH = None  # patched per-test via tmp_path

    @pytest.fixture
    def isolated_proposals(self, tmp_path, monkeypatch):
        """Each test gets a fresh proposals dir. monkeypatch auto-restores
        the module attribute on test teardown so later tests don't see
        state from earlier ones."""
        import api_server
        monkeypatch.setattr(api_server, "_PROPOSALS_DIR", tmp_path)
        monkeypatch.setattr(api_server, "_PROPOSALS_FILE", tmp_path / "queue.jsonl")
        return tmp_path

    def test_propose_new_question(self, client, isolated_proposals):
        r = client.post("/api/chat/propose", json={
            "question": "Ile firm PowerMatic jest w CZ?",
            "source_dataset": "master.csv",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["id"] and len(data["id"]) == 12
        assert "kolejki propozycji" in data["msg"].lower() or "admin" in data["msg"].lower()

    def test_propose_dedupes_within_24h(self, client, isolated_proposals):
        body = {"question": "Top 5 hurtowników w PL", "source_dataset": "master.csv"}
        first = client.post("/api/chat/propose", json=body).json()
        second = client.post("/api/chat/propose", json=body).json()
        assert first["ok"] is True
        assert second["ok"] is True
        assert first["id"] == second["id"]
        assert "już zaproponowane" in second["msg"].lower()

    def test_propose_rejects_uploaded_dataset(self, client, isolated_proposals):
        r = client.post("/api/chat/propose", json={
            "question": "Coś o moim CSV",
            "source_dataset": "uploaded.csv",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is False
        assert "master.csv" in data["msg"]

    def test_propose_rejects_empty(self, client):
        r = client.post("/api/chat/propose", json={"question": "  "})
        assert r.status_code == 400

    def test_propose_rejects_too_long(self, client):
        r = client.post("/api/chat/propose", json={"question": "x" * 501})
        assert r.status_code == 400

    def test_propose_list_returns_recent(self, client, isolated_proposals):
        for q in ("Pytanie A", "Pytanie B", "Pytanie C"):
            client.post("/api/chat/propose", json={
                "question": q, "source_dataset": "master.csv",
            })
        r = client.get("/api/chat/propose")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 3
        assert {it["question"] for it in data["items"]} == {"Pytanie A", "Pytanie B", "Pytanie C"}
        # All pending
        assert all(it["status"] == "pending" for it in data["items"])
# ---------------------------------------------------------------------------
# /api/settings — secrets vault (multi-provider LLM keys)
# ---------------------------------------------------------------------------

class TestSettingsVault:
    """The vault is auto-bootstrapped from .env on server start. These tests
    run with `SECRETS_PATH` monkeypatched to an isolated tmp file (see the
    `client` fixture), so persisted keys from real runs don't leak in.

    Tests are pure — no real network calls. We never exercise /test against
    a real provider; that path is integration-tested manually.
    """

    def test_get_settings_returns_redacted_fingerprints(self, client):
        r = client.get("/api/settings")
        assert r.status_code == 200
        data = r.json()
        # Shape: openrouter/gemini are lists, priority is list of strings
        assert isinstance(data["openrouter"], list)
        assert isinstance(data["gemini"], list)
        assert isinstance(data["priority"], list)
        # No raw 'key' field anywhere — must be fingerprint only
        for entry in data["openrouter"] + data["gemini"]:
            assert "key" not in entry
            assert "fingerprint" in entry

    def test_add_openrouter_key(self, client):
        r = client.post(
            "/api/settings/openrouter",
            json={"alias": "test-or-1", "key": "sk-or-v1-test1234567890abcd"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["alias"] == "test-or-1"
        assert body["fingerprint"].startswith("sk-o") and "…" in body["fingerprint"]

        # Now visible in /api/settings
        s = client.get("/api/settings").json()
        aliases = [e["alias"] for e in s["openrouter"]]
        assert "test-or-1" in aliases

    def test_add_gemini_key_with_project(self, client):
        r = client.post(
            "/api/settings/gemini",
            json={"alias": "test-gem-1", "key": "AIzaSyAbcdefghij1234567890", "project": "billszuka-test"},
        )
        assert r.status_code == 200
        s = client.get("/api/settings").json()
        entry = next(e for e in s["gemini"] if e["alias"] == "test-gem-1")
        assert entry["fingerprint"].startswith("AIza")
        assert entry.get("project") == "billszuka-test"

    def test_add_duplicate_alias_rejected(self, client):
        # First add succeeds
        client.post("/api/settings/openrouter",
                    json={"alias": "dup-alias", "key": "sk-or-v1-xxx"})
        # Second add with same alias must fail 409
        r = client.post("/api/settings/openrouter",
                        json={"alias": "dup-alias", "key": "sk-or-v1-yyy"})
        assert r.status_code == 409

    def test_delete_key(self, client):
        client.post("/api/settings/openrouter",
                    json={"alias": "to-delete", "key": "sk-or-v1-del"})
        r = client.delete("/api/settings/openrouter/to-delete")
        assert r.status_code == 200
        # Confirm gone
        s = client.get("/api/settings").json()
        assert "to-delete" not in [e["alias"] for e in s["openrouter"]]

    def test_delete_nonexistent_alias_404(self, client):
        r = client.delete("/api/settings/openrouter/never-existed")
        assert r.status_code == 404

    def test_set_priority(self, client):
        r = client.put("/api/settings/priority",
                       json={"priority": ["gemini", "openrouter", "mock"]})
        assert r.status_code == 200
        assert r.json()["priority"] == ["gemini", "openrouter", "mock"]
        # Verify persistence
        s = client.get("/api/settings").json()
        assert s["priority"] == ["gemini", "openrouter", "mock"]

    def test_set_priority_invalid_provider(self, client):
        r = client.put("/api/settings/priority",
                       json={"priority": ["gemini", "openrouter", "made-up"]})
        assert r.status_code == 400

    def test_rotate_all_endpoint_exists(self, client):
        """Bug #1: /api/settings/rotate-all was missing — clicking the
        'Rotuj wg last_ok' button in Settings drawer 404'd."""
        r = client.post("/api/settings/rotate-all")
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert "rotated_providers" in body
        assert isinstance(body["rotated_providers"], int)

    def test_rotate_all_reorders_keys(self, client):
        """Set last_ok timestamps on two gemini keys — newer one should
        come first after rotate-all."""
        import api_server as srv
        vault = srv._secrets_load()
        vault["gemini"] = [
            {"alias": "older", "key": "AIzaSyOLD0000000000000000",
             "source": "ui", "created": "2026-01-01T00:00:00Z",
             "last_ok": "2026-08-01T00:00:00Z"},
            {"alias": "newer", "key": "AIzaSyNEW0000000000000000",
             "source": "ui", "created": "2026-01-01T00:00:00Z",
             "last_ok": "2026-08-22T00:00:00Z"},
        ]
        srv._secrets_save(vault)

        client.post("/api/settings/rotate-all")

        vault = srv._secrets_load()
        assert vault["gemini"][0]["alias"] == "newer"
        assert vault["gemini"][1]["alias"] == "older"

    def test_unknown_provider_400(self, client):
        # DELETE /api/settings/{provider}/{alias} catches unknown provider
        # and returns 400 with a clear message.
        r = client.delete("/api/settings/unknown/alias")
        assert r.status_code == 400
        assert "unknown" in r.json()["detail"].lower()

        # POST /api/settings/{provider}/test — same 400 treatment
        r = client.post("/api/settings/unknown/alias/test")
        assert r.status_code == 400

    def test_add_key_empty_fields_400(self, client):
        r = client.post("/api/settings/openrouter", json={"alias": "", "key": ""})
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/chat with vault isolated — ensure no key leakage
# ---------------------------------------------------------------------------

class TestChatVaultIsolation:
    """The chat chain walks openrouter → gemini → mock. When the test fixture
    isolates SECRETS_PATH to a tmp file (empty vault), all chain steps miss
    and we fall through to mock. This proves the isolation actually works.
    """

    def test_no_real_keys_in_empty_vault(self, client):
        """With isolated empty vault, even real .env keys must not leak in."""
        import api_server as srv
        vault = srv._secrets_load()
        assert vault["openrouter"] == []
        assert vault["gemini"] == []

    def test_chat_falls_through_to_mock(self, client):
        r = client.post("/api/chat", json={"query": "ile firm jest?"})
        assert r.status_code == 200
        data = r.json()
        assert data["provider"] == "mock"
