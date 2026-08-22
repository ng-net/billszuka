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
    """Redirect DATA to a temp dir; pre-populate with test CSVs."""
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
    return TestClient(api_server.app)


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
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        assert data["filename"] == "new_upload.csv"
        # File should actually be on disk
        assert (tmp_data / "new_upload.csv").exists()
        assert (tmp_data / "new_upload.csv").read_text() == body

    def test_duplicate_rejected(self, client, tmp_data):
        # sales_data.csv already exists from fixture
        body = "month,revenue\n2026-03,3000\n"
        r = client.post(
            "/api/upload",
            files={"file": ("sales_data.csv", io.BytesIO(body.encode()), "text/csv")},
        )
        assert r.status_code == 409
        # Original content must not be overwritten
        assert (tmp_data / "sales_data.csv").read_text().startswith("month,revenue\n2026-01")

    def test_non_csv_rejected(self, client):
        r = client.post(
            "/api/upload",
            files={"file": ("evil.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert r.status_code == 400

    def test_path_traversal_rejected(self, client):
        r = client.post(
            "/api/upload",
            files={"file": ("../escape.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")},
        )
        assert r.status_code == 400

    def test_hidden_filename_rejected(self, client):
        r = client.post(
            "/api/upload",
            files={"file": (".hidden.csv", io.BytesIO(b"a,b\n"), "text/csv")},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/sync
# ---------------------------------------------------------------------------

class TestSync:
    def test_sync_regenerates_master(self, client, tmp_data):
        # master.csv shouldn't exist yet
        assert not (tmp_data / "master.csv").exists()
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
            "active_dataset": "catalog-A-PL.csv",
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
            "active_dataset": "catalog-A-PL.csv",
        })
        assert r.status_code == 200
        data = r.json()
        # 1 FROZEN, 1 DO-WERYFIKACJI in fixture
        assert "FROZEN=1" in data["response"]
        assert "DO-WERYFIKACJI=1" in data["response"]

    def test_missing_dataset(self, client):
        r = client.post("/api/chat", json={
            "query": "ile firm?",
            "active_dataset": "ghost.csv",
        })
        assert r.status_code == 200  # mock handles gracefully
        data = r.json()
        assert "ghost" in data["response"].lower() or "nie widzę" in data["response"].lower()

    def test_generic_query_returns_nudge(self, client):
        r = client.post("/api/chat", json={
            "query": "co sądzisz o życiu?",
            "active_dataset": "catalog-A-PL.csv",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["provider"] == "mock"
        assert "Mock AI" in data["response"] or "Spróbuj pytań" in data["response"]

    def test_country_grouping(self, client):
        r = client.post("/api/chat", json={
            "query": "rozkład wg kraj",
            "active_dataset": "catalog-A-PL.csv",
        })
        assert r.status_code == 200
        data = r.json()
        # All rows are PL
        assert "PL" in data["response"]


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
