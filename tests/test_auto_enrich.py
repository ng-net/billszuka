"""
test_auto_enrich.py — Tests for tools/auto_enrich.py.

Covers:
  • _load_env() — .env as source of truth
  • enrich_from_search_results() — LLM extraction
  • update_csv_row() — placeholder detection + field mapping
  • find_unenriched_leads() / next_batch() — discovery
  • mark_done() / load_state() / save_state() — state management
  • CLI subcommands: extract / apply / process / leads
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Path setup
TESTS = Path(__file__).resolve().parent
TOOLS = TESTS.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import auto_enrich  # noqa: E402


# ---------------------------------------------------------------------------
# _load_env() — .env wins over OS env
# ---------------------------------------------------------------------------

class TestLoadEnv:
    """The .env file should be the source of truth, overriding the OS env."""

    def test_env_file_overrides_os_env(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("MY_KEY=from_env_file\n")
        # Even if OS has it set to a different value, .env wins
        monkeypatch.setenv("MY_KEY", "from_os")
        monkeypatch.setattr(auto_enrich, "ENV_FILE", env_file)
        env = auto_enrich._load_env()
        assert env["MY_KEY"] == "from_env_file"

    def test_os_env_used_when_not_in_env_file(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("ONLY_IN_FILE=yes\n")
        monkeypatch.setenv("ONLY_IN_OS", "fallback")
        monkeypatch.setattr(auto_enrich, "ENV_FILE", env_file)
        env = auto_enrich._load_env()
        assert env["ONLY_IN_FILE"] == "yes"
        assert env["ONLY_IN_OS"] == "fallback"

    def test_missing_env_file_falls_back_to_os(self, tmp_path, monkeypatch):
        missing = tmp_path / ".env.does_not_exist"
        monkeypatch.setattr(auto_enrich, "ENV_FILE", missing)
        monkeypatch.setenv("FROM_OS", "yes")
        env = auto_enrich._load_env()
        assert env.get("FROM_OS") == "yes"

    def test_comments_and_blank_lines_skipped(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# comment\n"
            "\n"
            "REAL_KEY=value\n"
            "=novalue\n"  # No key — should be skipped
        )
        monkeypatch.setattr(auto_enrich, "ENV_FILE", env_file)
        env = auto_enrich._load_env()
        assert "REAL_KEY" in env
        assert env["REAL_KEY"] == "value"


# ---------------------------------------------------------------------------
# enrich_from_search_results() — parser robustness
# ---------------------------------------------------------------------------

class TestEnrichFromSearchResults:
    """The LLM extraction handles list/dict/garbage responses gracefully."""

    def _mock_openrouter(self, monkeypatch, raw_text):
        """Patch _call_openrouter to return canned text."""
        monkeypatch.setattr(
            auto_enrich, "_call_openrouter",
            lambda *a, **kw: raw_text,
        )

    def test_list_response_takes_highest_confidence(self, monkeypatch):
        # LLM returned a list of 2 candidates
        self._mock_openrouter(monkeypatch, json.dumps([
            {"name": "Alice", "title": "CEO", "confidence": 0.7},
            {"name": "Bob", "title": "CTO", "confidence": 0.9},
        ]))
        result = auto_enrich.enrich_from_search_results("Acme", "London", "UK",
                                                       "ignored text")
        assert result["name"] == "Bob"
        assert result["title"] == "CTO"
        # alternates should contain Alice (the lower-confidence one)
        alternates = result.get("_alternates", [])
        names = [a.get("name") for a in alternates]
        assert "Alice" in names

    def test_dict_response_passes_through(self, monkeypatch):
        self._mock_openrouter(monkeypatch, json.dumps({
            "name": "Carol", "title": "Founder", "phone": "+1 555 1234",
            "linkedin": "https://linkedin.com/in/carol",
            "confidence": 0.95,
        }))
        result = auto_enrich.enrich_from_search_results("Acme", "NYC", "US", "t")
        assert result["name"] == "Carol"
        assert result["phone"] == "+1 555 1234"
        # _alternates should NOT be set for single dict
        assert "_alternates" not in result

    def test_markdown_fences_stripped(self, monkeypatch):
        # LLM often wraps in ```json ... ```
        self._mock_openrouter(monkeypatch, '```json\n{"name": "Dan", "title": "PM"}\n```')
        result = auto_enrich.enrich_from_search_results("Acme", "Berlin", "DE", "t")
        assert result["name"] == "Dan"

    def test_garbage_response_returns_error(self, monkeypatch):
        self._mock_openrouter(monkeypatch, "Sorry, I don't know.")
        result = auto_enrich.enrich_from_search_results("Acme", "X", "PL", "t")
        assert "_error" in result

    def test_empty_text_returns_empty_dict(self, monkeypatch):
        # Even if _call_openrouter were called, empty input short-circuits
        result = auto_enrich.enrich_from_search_results("X", "Y", "PL", "")
        assert result == {}

    def test_openrouter_error_returns_error_dict(self, monkeypatch):
        def boom(*a, **kw):
            raise RuntimeError("network down")
        monkeypatch.setattr(auto_enrich, "_call_openrouter", boom)
        result = auto_enrich.enrich_from_search_results("X", "Y", "PL", "t")
        assert "_error" in result
        assert "network down" in result["_error"]

    def test_null_fields_are_dropped(self, monkeypatch):
        # LLM sometimes includes explicit nulls
        self._mock_openrouter(monkeypatch, json.dumps({
            "name": "Eve", "title": None, "phone": None, "email": "eve@x.com",
        }))
        result = auto_enrich.enrich_from_search_results("X", "Y", "PL", "t")
        assert result["name"] == "Eve"
        assert "title" not in result
        assert "phone" not in result
        assert result["email"] == "eve@x.com"


# ---------------------------------------------------------------------------
# update_csv_row() — placeholder detection + field mapping
# ---------------------------------------------------------------------------

class TestUpdateCsvRow:
    """The CSV write must overwrite placeholders but preserve real data."""

    @pytest.fixture
    def csv_file(self, tmp_path):
        path = tmp_path / "catalog.csv"
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "decydent", "stanowisko",
                        "telefon", "linkedin", "data_weryfikacji"])
            w.writerow(["PL-X-001", "do ustalenia", "brak", "brak", "brak", ""])
        return path

    def test_overwrites_do_ustalenia(self, csv_file):
        ok = auto_enrich.update_csv_row(
            str(csv_file), "PL-X-001",
            {"name": "Anna Nowak", "title": "Prezes"},
        )
        assert ok is True
        with csv_file.open() as f:
            row = next(csv.DictReader(f))
        assert row["decydent"] == "Anna Nowak"
        assert row["stanowisko"] == "Prezes"

    def test_overwrites_brak(self, csv_file):
        ok = auto_enrich.update_csv_row(
            str(csv_file), "PL-X-001",
            {"phone": "+48 22 123 45 67"},
        )
        assert ok is True
        with csv_file.open() as f:
            row = next(csv.DictReader(f))
        assert row["telefon"] == "+48 22 123 45 67"

    def test_preserves_existing_real_value(self, csv_file):
        # If the field already has a real value, do NOT overwrite
        with csv_file.open("r") as f:
            rows = list(csv.DictReader(f))
        rows[0]["decydent"] = "Jan Kowalski (real)"
        with csv_file.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        ok = auto_enrich.update_csv_row(
            str(csv_file), "PL-X-001",
            {"name": "Anna Nowak"},  # try to overwrite
        )
        assert ok is True
        with csv_file.open() as f:
            row = next(csv.DictReader(f))
        assert row["decydent"] == "Jan Kowalski (real)"  # preserved

    def test_unknown_id_returns_false(self, csv_file):
        ok = auto_enrich.update_csv_row(str(csv_file), "NONEXISTENT", {"name": "X"})
        assert ok is False

    def test_missing_id_column_returns_false(self, tmp_path):
        # CSV without id column
        path = tmp_path / "bad.csv"
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["foo", "bar"])
            w.writerow(["1", "2"])
        ok = auto_enrich.update_csv_row(str(path), "1", {"name": "X"})
        assert ok is False

    def test_field_mapping_to_polish_columns(self, csv_file):
        # Verify: name→decydent, title→stanowisko, email→email_decydent
        with csv_file.open("r") as f:
            r = csv.DictReader(f)
            header = list(r.fieldnames)
        # The fixture uses 'decydent' (not 'email_decydent') — verify by direct test
        # Add a row with email_decydent column
        with csv_file.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "decydent", "stanowisko", "email_decydent",
                        "telefon", "linkedin", "data_weryfikacji"])
            w.writerow(["PL-X-002", "do ustalenia", "brak", "brak", "brak", "brak", ""])
        ok = auto_enrich.update_csv_row(str(csv_file), "PL-X-002", {
            "name": "Anna Nowak",
            "title": "Prezes",
            "email": "anna@acme.pl",
            "phone": "+48 22 123 45 67",
        })
        assert ok is True
        with csv_file.open() as f:
            row = next(csv.DictReader(f))
        assert row["decydent"] == "Anna Nowak"
        assert row["stanowisko"] == "Prezes"
        assert row["email_decydent"] == "anna@acme.pl"
        assert row["telefon"] == "+48 22 123 45 67"

    def test_bumps_data_weryfikacji(self, csv_file):
        ok = auto_enrich.update_csv_row(str(csv_file), "PL-X-001", {"name": "X"})
        with csv_file.open() as f:
            row = next(csv.DictReader(f))
        # Should be today's date in YYYY-MM-DD
        import re
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", row["data_weryfikacji"])


# ---------------------------------------------------------------------------
# find_unenriched_leads() / next_batch()
# ---------------------------------------------------------------------------

class TestFindLeads:
    """The discovery should skip backups, snapshots, and processed entries."""

    @pytest.fixture
    def populated(self, tmp_path, monkeypatch):
        """Build a fake data/ tree with 3 country dirs + a backup dir."""
        monkeypatch.setattr(auto_enrich, "DATA", tmp_path)
        # Country A: 2 unenriched
        pa = tmp_path / "Polska"
        pa.mkdir()
        with (pa / "catalog-B-PL.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "kraj", "nazwa_firmy", "miasto",
                        "www", "decydent", "stanowisko"])
            w.writerow(["PL-1", "PL", "Alpha", "Warsaw", "x.pl",
                        "do ustalenia", "brak"])
            w.writerow(["PL-2", "PL", "Beta", "Krakow", "y.pl",
                        "Anna Nowak", "Prezes"])  # already filled
        # Country B: 1 unenriched
        cz = tmp_path / "Czechy"
        cz.mkdir()
        with (cz / "catalog-A-CZ.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "kraj", "nazwa_firmy", "decydent"])
            w.writerow(["CZ-1", "CZ", "Gamma", "do ustalenia"])
        # Backup dir: should be ignored
        bk = tmp_path / "backups"
        bk.mkdir()
        with (bk / "catalog-B-PL.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "kraj", "decydent"])
            w.writerow(["PL-99", "PL", "do ustalenia"])  # should be SKIPPED
        # Snapshots dir: should be ignored
        sn = tmp_path / ".snapshots"
        sn.mkdir()
        with (sn / "catalog-B-PL.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "kraj", "decydent"])
            w.writerow(["PL-100", "PL", "do ustalenia"])  # SKIPPED
        return tmp_path

    def test_finds_unenriched_only(self, populated):
        leads = auto_enrich.find_unenriched_leads()
        ids = [l["id"] for l in leads]
        assert "PL-1" in ids  # needs enrichment
        assert "PL-2" not in ids  # already has Anna Nowak
        assert "CZ-1" in ids
        assert "PL-99" not in ids  # in backups/
        assert "PL-100" not in ids  # in .snapshots/

    def test_next_batch_respects_done_state(self, populated, monkeypatch):
        # Pretend PL-1 was already done
        monkeypatch.setattr(auto_enrich, "STATE_FILE",
                            populated / ".verify-state" / "enrichment.json")
        (populated / ".verify-state").mkdir()
        from auto_enrich import mark_done
        mark_done(
            {"id": "PL-1", "csv_path": str(populated / "Polska" / "catalog-B-PL.csv"),
             "name": "Alpha", "country": "PL"},
            {"name": "Test", "confidence": 0.9},
        )
        leads = auto_enrich.next_batch(limit=10)
        ids = [l["id"] for l in leads]
        assert "PL-1" not in ids
        assert "CZ-1" in ids


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

class TestState:
    def test_load_state_empty_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(auto_enrich, "STATE_FILE", tmp_path / "x.json")
        assert auto_enrich.load_state() == {}

    def test_load_state_corrupt_json(self, tmp_path, monkeypatch):
        path = tmp_path / "x.json"
        path.write_text("not json{{{")
        monkeypatch.setattr(auto_enrich, "STATE_FILE", path)
        assert auto_enrich.load_state() == {}  # graceful

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        path = tmp_path / "x.json"
        monkeypatch.setattr(auto_enrich, "STATE_FILE", path)
        state = {"done": {"PL-1@x": {"ts": "2026-08-11", "name": "Test"}}}
        auto_enrich.save_state(state)
        loaded = auto_enrich.load_state()
        assert loaded == state

    def test_mark_done_appends(self, tmp_path, monkeypatch):
        path = tmp_path / ".verify-state" / "enrichment.json"
        monkeypatch.setattr(auto_enrich, "STATE_FILE", path)
        auto_enrich.mark_done(
            {"id": "PL-1", "csv_path": "x.csv", "name": "A", "country": "PL"},
            {"name": "Anna", "confidence": 0.8},
        )
        auto_enrich.mark_done(
            {"id": "PL-2", "csv_path": "x.csv", "name": "B", "country": "PL"},
            {"name": "Bob", "_error": "x"},
        )
        state = auto_enrich.load_state()
        assert "PL-1@x.csv" in state["done"]
        assert "PL-2@x.csv" in state["done"]
        assert state["done"]["PL-1@x.csv"]["had_error"] is False
        assert state["done"]["PL-2@x.csv"]["had_error"] is True


# ---------------------------------------------------------------------------
# CLI: process subcommand end-to-end (with mocked network)
# ---------------------------------------------------------------------------

class TestProcessCLI:
    """process should run extract+apply+mark_done in one call."""

    @pytest.fixture
    def csv_file(self, tmp_path):
        path = tmp_path / "test.csv"
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "decydent", "stanowisko",
                        "telefon", "linkedin", "data_weryfikacji"])
            w.writerow(["PL-99", "do ustalenia", "brak", "brak", "brak", ""])
        return path

    def test_process_happy_path(self, tmp_path, csv_file, monkeypatch, capsys):
        monkeypatch.setattr(auto_enrich, "STATE_FILE",
                            tmp_path / "state.json")
        monkeypatch.setattr(
            auto_enrich, "_call_openrouter",
            lambda *a, **kw: json.dumps({
                "name": "Anna Nowak", "title": "Prezes", "phone": "+48 22 1234",
                "confidence": 0.9,
            }),
        )
        argv = [
            "process",
            "--csv", str(csv_file),
            "--id", "PL-99",
            "--name", "Test Co", "--city", "Warsaw", "--country", "PL",
            "--search-results", "Anna Nowak is the CEO of Test Co",
        ]
        import sys as _sys
        original_argv = _sys.argv
        _sys.argv = ["auto_enrich"] + argv
        try:
            rc = auto_enrich.main_with_args(argv)
        finally:
            _sys.argv = original_argv
        assert rc == 0
        # Output JSON on stdout
        out = capsys.readouterr().out.strip()
        data = json.loads(out)
        assert data["ok"] is True
        assert data["primary"]["name"] == "Anna Nowak"
        # CSV was updated
        with csv_file.open() as f:
            row = next(csv.DictReader(f))
        assert row["decydent"] == "Anna Nowak"
        assert row["stanowisko"] == "Prezes"
        # State was saved
        state = auto_enrich.load_state()
        # Key is "{id}@{csv_path}" — csv_path is the full path the test passed
        assert any(k.startswith("PL-99@") and k.endswith("test.csv")
                   for k in state["done"]), f"unexpected state keys: {list(state['done'])}"

    def test_process_no_state_flag(self, tmp_path, csv_file, monkeypatch, capsys):
        monkeypatch.setattr(
            auto_enrich, "_call_openrouter",
            lambda *a, **kw: json.dumps({"name": "Anna", "confidence": 0.9}),
        )
        argv = [
            "process", "--no-state",
            "--csv", str(csv_file),
            "--id", "PL-99",
            "--name", "X", "--country", "PL",
            "--search-results", "irrelevant",
        ]
        import sys as _sys
        original_argv = _sys.argv
        _sys.argv = ["auto_enrich"] + argv
        try:
            rc = auto_enrich.main_with_args(argv)
        finally:
            _sys.argv = original_argv
        assert rc == 0
        # State file was NOT created
        assert not (tmp_path / ".verify-state" / "enrichment.json").exists()


# ---------------------------------------------------------------------------
# find_unenriched_leads() — glob must skip pre-clean snapshots
# ---------------------------------------------------------------------------

class TestFindUnenrichedLeads:
    """find_unenriched_leads() must only scan canonical catalog files."""

    def test_skips_pre_clean_snapshots(self, tmp_path, monkeypatch):
        import csv as _csv
        # Build a fake data tree
        country = tmp_path / "Polska"
        country.mkdir()
        # Canonical file (should be picked up)
        canonical = country / "catalog-B-PL.csv"
        with canonical.open("w", newline="", encoding="utf-8") as f:
            w = _csv.writer(f)
            w.writerow(["id", "kraj", "nazwa_firmy", "miasto", "www", "decydent"])
            w.writerow(["PL-A-1", "PL", "Foo sp. z o.o.", "Wawa", "", "do ustalenia"])
        # Pre-clean snapshot (should be ignored)
        pre = country / "catalog-B-PL-pre-clean-20260811_023054.csv"
        with pre.open("w", newline="", encoding="utf-8") as f:
            w = _csv.writer(f)
            w.writerow(["id", "kraj", "nazwa_firmy", "miasto", "www", "decydent"])
            w.writerow(["PL-B-1", "PL", "Old", "Wawa", "", "do ustalenia"])
        # AppleDouble file (should be ignored)
        doubled = country / "._catalog-B-PL.csv"
        doubled.write_text("")

        monkeypatch.setattr(auto_enrich, "DATA", tmp_path)
        leads = auto_enrich.find_unenriched_leads()
        ids = [l["id"] for l in leads]
        assert "PL-A-1" in ids, "canonical file not picked up"
        assert "PL-B-1" not in ids, "pre-clean snapshot was incorrectly picked up"
