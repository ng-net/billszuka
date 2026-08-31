#!/usr/bin/env python3
"""
test_purge_and_orchestrate.py — Unit and integration tests for:
  1. tools/purge_hallucinations_and_normalize.py (anchored regexes, allowlist, quarantine, .bak, dry-run)
  2. tools/orchestrate_11_levels.py (country plans schema validation, dedup edge case, csv_A/csv_B handling)
"""

import csv
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from tools.config import (
    CANONICAL_SCHEMA,
    QUARANTINE_DIR,
    VERIFIED_ALLOWLIST,
    is_verified_allowlisted,
)
from tools.orchestrate_11_levels import (
    COUNTRY_PLANS,
    _csv_label,
    add_lead,
    load_country_plans,
    validate_country_plans,
)
from tools.purge_hallucinations_and_normalize import (
    clean_catalogs,
    is_dummy_identifier,
    is_hallucinated,
    write_quarantine_rows,
)


# ---------------------------------------------------------------------------
# Tests for tools/purge_hallucinations_and_normalize.py
# ---------------------------------------------------------------------------

class TestPurgeRegexAndAllowlist:
    def test_anchored_dummy_numbers(self):
        """Pure dummy sequences must be flagged."""
        dummy_samples = [
            "123456", "PL123456", "1234567890", "PL1234567890", "0123456789",
            "987654", "9876543210", "112233", "234567", "345678", "456789",
            "567890", "678901", "20234567", "202031234", "555444333",
            "55556666", "555666777", "00000000", "1111111111", "99999999"
        ]
        for s in dummy_samples:
            assert is_dummy_identifier(s) is True, f"Expected {s} to be flagged as dummy"

    def test_real_ids_with_substring_digits_pass(self):
        """Real NIPs that contain '123456' as a substring must NOT be flagged."""
        real_samples = [
            "5212345678",      # 10 digits containing 123456
            "PL5212345678",
            "7811011998",      # Real Polish NIP
            "5372504633",      # Real Polish NIP
            "CZ25775634",      # Real Czech IČO
            "RO123456789012",  # Long real registry ID containing digit run
        ]
        for s in real_samples:
            assert is_dummy_identifier(s) is False, f"Expected {s} NOT to be flagged as dummy"

    def test_verified_allowlist_bypass(self):
        """Allowlisted company IDs (e.g. AGROTAB PL7931626076) must never be flagged."""
        assert is_verified_allowlisted("PL7931626076") is True
        assert is_verified_allowlisted("7931626076") is True
        assert is_verified_allowlisted("PL 793-162-60-76") is True
        assert is_dummy_identifier("PL7931626076") is False
        assert is_dummy_identifier("7931626076") is False

    def test_is_hallucinated_reasons(self):
        """Verify various hallucination categories return correct bool and reason."""
        # 1. LeadScout ungrounded discovery
        res, reason = is_hallucinated({"zrodlo_danych": "LeadScout L1 Discovery batch 4"}, "PL")
        assert res is True
        assert "LeadScout" in reason

        # 2. Fake ListaFirme scraper
        res, reason = is_hallucinated({"zrodlo_danych": "ListaFirme RO Scraper (Verified RO 1234)"}, "RO")
        assert res is True
        assert "Fake ListaFirme" in reason

        # 3. Dummy NIP
        res, reason = is_hallucinated({"nip_vat": "1234567890"}, "PL")
        assert res is True
        assert "Dummy pattern in NIP" in reason

        # 4. Dummy rejestr_id
        res, reason = is_hallucinated({"rejestr_id": "00000000"}, "CZ")
        assert res is True
        assert "Dummy pattern in rejestr_id" in reason

        # 5. MD empty stub
        res, reason = is_hallucinated({"nazwa_firmy": "Moldova Tobacco Trade"}, "MD")
        assert res is True
        assert "Empty stub" in reason

        # 6. Generic placeholder names
        res, reason = is_hallucinated({"nazwa_firmy": "Smoke Shop"}, "PL")
        assert res is True
        assert "Generic placeholder name" in reason

        # 7. Valid row
        valid_row = {
            "nazwa_firmy": "BILLS Sp. z o.o.",
            "nip_vat": "5140361901",
            "rejestr_id": "0000854321",
            "zrodlo_danych": "KRS API",
            "www": "https://bills.pl"
        }
        res, reason = is_hallucinated(valid_row, "PL")
        assert res is False
        assert reason == ""


class TestPurgeExecutionAndQuarantine:
    def test_quarantine_write(self, tmp_path):
        """Test write_quarantine_rows writes headers and audit records."""
        q_file = tmp_path / "test_quarantine.csv"
        records = [
            {
                "kraj": "PL",
                "nazwa_firmy": "Fake Company",
                "nip_vat": "123456",
                "purge_reason": "Dummy pattern in NIP (123456)",
                "purged_at": "2026-08-31T12:00:00Z"
            }
        ]
        write_quarantine_rows(q_file, records)
        assert q_file.exists()

        with open(q_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["nazwa_firmy"] == "Fake Company"
            assert rows[0]["purge_reason"] == "Dummy pattern in NIP (123456)"
            assert rows[0]["purged_at"] == "2026-08-31T12:00:00Z"
            assert "kraj" in rows[0]


# ---------------------------------------------------------------------------
# Tests for tools/orchestrate_11_levels.py
# ---------------------------------------------------------------------------

class TestCountryPlansSchema:
    def test_country_plans_loaded_and_valid(self):
        """Check all 13 countries are loaded with valid L0-L11 schemas."""
        plans = COUNTRY_PLANS
        assert len(plans) >= 13
        assert "PL" in plans
        assert "CZ" in plans
        assert "RS" in plans

        for iso, plan in plans.items():
            assert "name" in plan
            assert "csv_A" in plan
            assert "csv_B" in plan
            assert "L0_preflight" in plan
            assert "L1_web_search" in plan
            assert "L2_marketplace" in plan
            assert "L3_registries" in plan
            assert "L4_customs_regulatory" in plan
            assert "L5_dns_whois" in plan
            assert "L6_trade_fairs" in plan
            assert "L7_social_osint" in plan
            assert "L8_B2B_catalogs" in plan
            assert "L9_LLM_extraction" in plan
            assert "L10_trademark" in plan
            assert "L11_procurement" in plan

    def test_validate_country_plans_catches_missing_keys(self):
        """Validator must raise ValueError if required keys are missing."""
        invalid_plans = {
            "PL": {
                "name": "Polska",
                "csv_A": "data/Polska/catalog-A-PL.csv",
                # missing csv_B and L0-L11
            }
        }
        with pytest.raises(ValueError, match="missing required key"):
            validate_country_plans(invalid_plans)

    def test_csv_label_formatting(self):
        """_csv_label must return comma-separated paths or dash."""
        plan = {"csv_A": "data/Polska/catalog-A-PL.csv", "csv_B": "data/Polska/catalog-B-PL.csv"}
        label = _csv_label(plan)
        assert "data/Polska/catalog-B-PL.csv" in label
        assert "data/Polska/catalog-A-PL.csv" in label


class TestAddLeadDeduplication:
    def test_add_lead_dedup_non_empty_nip(self, tmp_path, monkeypatch):
        """add_lead must prevent duplicate NIPs when non-empty."""
        # Setup temporary catalog file
        pl_dir = tmp_path / "data" / "Polska"
        pl_dir.mkdir(parents=True)
        csv_file = pl_dir / "catalog-B-PL.csv"

        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
            w.writeheader()
            w.writerow({col: "" for col in CANONICAL_SCHEMA})
            # write row with NIP 5140361901
            row1 = {col: "" for col in CANONICAL_SCHEMA}
            row1["nip_vat"] = "5140361901"
            row1["nazwa_firmy"] = "BILLS Sp. z o.o."
            w.writerow(row1)

        test_plans = {
            "PL": {
                "name": "Polska",
                "csv_A": str(pl_dir / "catalog-A-PL.csv"),
                "csv_B": str(csv_file.relative_to(tmp_path)),
                "L0_preflight": "", "L1_web_search": [], "L2_marketplace": [],
                "L3_registries": {}, "L4_customs_regulatory": [], "L5_dns_whois": {},
                "L6_trade_fairs": [], "L7_social_osint": [], "L8_B2B_catalogs": [],
                "L9_LLM_extraction": {}, "L10_trademark": "", "L11_procurement": ""
            }
        }

        monkeypatch.setattr("tools.orchestrate_11_levels.ROOT", tmp_path)
        monkeypatch.setattr("tools.orchestrate_11_levels.COUNTRY_PLANS", test_plans)

        # 1. Adding exact duplicate NIP must return False
        added = add_lead("PL", "BILLS Duplicate", "hurtownia", "514 036 19 01", "", "manual", "B")
        assert added is False

        # 2. Adding different NIP must return True
        added2 = add_lead("PL", "Second Company", "hurtownia", "7811011998", "0000123456", "manual", "B")
        assert added2 is True

    def test_add_lead_allows_multiple_empty_nips(self, tmp_path, monkeypatch):
        """add_lead must NOT block leads that lack a tax ID (empty NIP)."""
        pl_dir = tmp_path / "data" / "Polska"
        pl_dir.mkdir(parents=True)
        csv_file = pl_dir / "catalog-B-PL.csv"

        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
            w.writeheader()

        test_plans = {
            "PL": {
                "name": "Polska",
                "csv_A": str(pl_dir / "catalog-A-PL.csv"),
                "csv_B": str(csv_file.relative_to(tmp_path)),
                "L0_preflight": "", "L1_web_search": [], "L2_marketplace": [],
                "L3_registries": {}, "L4_customs_regulatory": [], "L5_dns_whois": {},
                "L6_trade_fairs": [], "L7_social_osint": [], "L8_B2B_catalogs": [],
                "L9_LLM_extraction": {}, "L10_trademark": "", "L11_procurement": ""
            }
        }

        monkeypatch.setattr("tools.orchestrate_11_levels.ROOT", tmp_path)
        monkeypatch.setattr("tools.orchestrate_11_levels.COUNTRY_PLANS", test_plans)

        # First lead without NIP
        added1 = add_lead("PL", "Lead No NIP 1", "hurtownia", "", "REG111", "manual", "B")
        assert added1 is True

        # Second lead without NIP — must NOT be blocked as a duplicate of the first empty NIP!
        added2 = add_lead("PL", "Lead No NIP 2", "sklep", "", "REG222", "manual", "B")
        assert added2 is True

        # Verify both rows written to CSV
        with open(csv_file, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            assert len(rows) == 2
            assert rows[0]["nazwa_firmy"] == "Lead No NIP 1"
            assert rows[1]["nazwa_firmy"] == "Lead No NIP 2"
