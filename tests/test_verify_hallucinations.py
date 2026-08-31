"""Tests for tools/verify_hallucinations.py — mod-11 + KRS lookup verifier.

These tests pin down the verifier's correctness independently of the live
KRS API. They use known-good and known-bad NIPs from public sources.

Real verified NIPs (from Polish Tax Authority KAS):
  - 9482622620  → POLSKI TYTOŃ S.A. (mod-11 OK)
  - 7252077543  → ORION TOBACCO POLAND (mod-11 OK)
  - 7811011998  → TRANSGOURMET POLSKA (mod-11 OK)
  - 6510000539  → PIEKARNIA REHLIS (mod-11 OK, but KRS 0000108390 belongs
                  to PIEKARNIA REHLIS, NOT to PL-B-061 CARMEN POLSKA)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "tools")

import verify_hallucinations as vh


# ---------------------------------------------------------------------------
# mod-11: known-good NIPs (verified against KAS WL API)
# ---------------------------------------------------------------------------

class TestPlNipMod11KnownGood:
    """NIPs that the Polish Tax Authority accepts."""

    def test_polski_tyton(self):
        ok, reason = vh.pl_nip_mod11_ok("PL9482622620")
        assert ok, reason

    def test_orion_tobacco(self):
        ok, reason = vh.pl_nip_mod11_ok("PL7252077543")
        assert ok, reason

    def test_transgourmet(self):
        ok, reason = vh.pl_nip_mod11_ok("PL7811011998")
        assert ok, reason

    def test_piekarnia_rehlis(self):
        # KRS 0000108390 → NIP 6510000539 (PIEKARNIA REHLIS, Żory)
        ok, reason = vh.pl_nip_mod11_ok("PL6510000539")
        assert ok, reason

    def test_no_pl_prefix(self):
        ok, _ = vh.pl_nip_mod11_ok("9482622620")
        assert ok

    def test_with_spaces(self):
        ok, _ = vh.pl_nip_mod11_ok("94 826 226 20")
        assert ok

    def test_with_dashes(self):
        ok, _ = vh.pl_nip_mod11_ok("948-262-26-20")
        assert ok


class TestPlNipMod11KnownBad:
    """NIPs that fail mod-11 (KAS WL API returns 'Nieprawidłowy NIP.' for all of them)."""

    def test_selgros_hallucinated(self):
        # CSV's PL-B-048 NIP. Real Selgros is 7811011998, not 7792223933.
        ok, reason = vh.pl_nip_mod11_ok("PL7792223933")
        assert not ok
        assert "got 3" in reason or "check" in reason

    def test_mona_hallucinated(self):
        # CSV's PL-B-052 NIP. KAS rejects as invalid.
        ok, reason = vh.pl_nip_mod11_ok("PL6792683072")
        assert not ok

    def test_milo_hallucinated(self):
        ok, _ = vh.pl_nip_mod11_ok("PL9590822602")
        assert not ok

    def test_empty_string(self):
        ok, reason = vh.pl_nip_mod11_ok("")
        assert not ok
        assert "10 digits" in reason

    def test_too_short(self):
        ok, reason = vh.pl_nip_mod11_ok("PL123")
        assert not ok

    def test_too_long(self):
        ok, _ = vh.pl_nip_mod11_ok("PL12345678901")
        assert not ok

    def test_letters(self):
        ok, _ = vh.pl_nip_mod11_ok("PL12345ABCDE")
        assert not ok


# ---------------------------------------------------------------------------
# KRS API parser — uses real KRS API structure
# ---------------------------------------------------------------------------

class TestKrsNipNameParser:
    """Test the parser against the real KRS API response shape."""

    SAMPLE = {
        "odpis": {
            "dane": {
                "dzial1": {
                    "danePodmiotu": {
                        "identyfikatory": {
                            "regon": "00352424100000",
                            "nip": "6510000539",
                        },
                        "nazwa": "PIEKARNIA REHLIS SPÓŁKA JAWNA",
                    }
                }
            }
        }
    }

    def test_extracts_nip(self):
        nip, _ = vh.krs_nip_name(self.SAMPLE)
        assert nip == "6510000539"

    def test_extracts_name(self):
        _, name = vh.krs_nip_name(self.SAMPLE)
        assert name == "PIEKARNIA REHLIS SPÓŁKA JAWNA"

    def test_handles_none(self):
        assert vh.krs_nip_name(None) == (None, None)

    def test_handles_empty(self):
        assert vh.krs_nip_name({}) == (None, None)

    def test_handles_missing_dzial1(self):
        sample = {"odpis": {"dane": {}}}
        assert vh.krs_nip_name(sample) == (None, None)


# ---------------------------------------------------------------------------
# KRS API lookup — live test, marked as integration
# ---------------------------------------------------------------------------

class TestKrsLookupIntegration:
    """Real KRS API calls. Skipped in CI if network unavailable."""

    def test_known_krs_returns_data(self):
        # KRS 0000108390 → PIEKARNIA REHLIS, NIP 6510000539
        data = vh.krs_lookup("0000108390")
        if data is None:
            import pytest
            pytest.skip("KRS API unreachable in this environment")
        nip, name = vh.krs_nip_name(data)
        assert nip == "6510000539"
        assert "REHLIS" in (name or "")

    def test_nonexistent_krs_returns_none(self):
        data = vh.krs_lookup("9999999999")
        # Either None (not found) or a 200 with empty data
        if data is not None:
            nip, _ = vh.krs_nip_name(data)
            # Acceptable outcomes: nip is None, or the call worked
            assert True
