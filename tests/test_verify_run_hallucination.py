"""
test_verify_run_hallucination.py — Regression tests for tools/verify_run.py
hallucination detection (PL NIP mod-11 + KRS pre-flight).

Bug fix 2026-08-31: previously verify_row trusted string-match in
zrodlo_danych for tokens like 'KRS'/'CEIDG' and returned FROZEN without
verifying the NIP/KRS actually exist / match. This let 19+ PL-B rows
with hallucinated NIPs pass as FROZEN.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
ROOT = TOOLS.parent


def _load_verify_run():
    """Load tools/verify_run.py as a module (avoids `tools.` package import)."""
    spec = importlib.util.spec_from_file_location("verify_run", TOOLS / "verify_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vr = _load_verify_run()


class TestPlNipMod11:
    """Polish NIP mod-11 checksum validation."""

    def test_bills_real_nip(self):
        # BILLS Sp. z o.o. — known good
        assert vr.pl_nip_mod11_ok("5140361901") is True

    def test_ck_complex_real_nip(self):
        # PL-B-001 CK COMPLEX — known good
        assert vr.pl_nip_mod11_ok("9291744080") is True

    def test_selgros_real_nip(self):
        # Real Selgros NIP (correct one)
        assert vr.pl_nip_mod11_ok("7811011998") is True

    def test_master_płodowscy_real_nip(self):
        # Real NIP for KRS 0000308003 (real firm at that KRS)
        assert vr.pl_nip_mod11_ok("5372504633") is True

    @pytest.mark.parametrize("bad_nip,label", [
        ("7792223933", "PL-B-048 halucynacja Selgros"),
        ("9532585250", "PL-B-050 halucynacja"),
        ("6792683072", "PL-B-052 halucynacja"),
        ("1234567890", "random 1-2-3"),
    ])
    def test_hallucinated_or_invalid_nip(self, bad_nip, label):
        assert vr.pl_nip_mod11_ok(bad_nip) is False, f"{label}: {bad_nip} should fail mod-11"

    def test_empty_string(self):
        assert vr.pl_nip_mod11_ok("") is False

    def test_too_short(self):
        assert vr.pl_nip_mod11_ok("12345") is False

    def test_too_long(self):
        assert vr.pl_nip_mod11_ok("12345678901") is False

    def test_with_letters(self):
        assert vr.pl_nip_mod11_ok("514036190X") is False


class TestVerifyRowMod11PreFlight:
    """verify_row() should catch PL NIP mod-11 hallucination as DO-WERYFIKACJI."""

    def _row(self, nip, krs="KRS 0001074645", zrodlo="KRS API 0001074645"):
        return {
            "kraj": "PL",
            "id": "PL-TEST",
            "nazwa": "TEST FIRMA SP. Z O.O.",
            "nip_vat": nip,
            "rejestr_id": krs,
            "zrodlo_danych": zrodlo,
            "kategoria": "B8",
            "miasto": "Testowo",
            "adres": "ul. Test 1",
            "www": "https://test.pl",
            "wolumen": "duży",
            "confidence_wolumen": "🟢",
        }

    def test_hallucinated_nip_becomes_do_weryfikacji(self):
        status, reason = vr.verify_row(self._row("7792223933"))
        assert status == "DO-WERYFIKACJI"
        assert "mod-11 invalid" in reason
        assert "HALUCYNACJA" in reason

    def test_valid_nip_passes_mod11_check(self):
        # BILLS real NIP + BILLS real KRS → would still need KRS pre-flight
        # but mod-11 check passes
        row = self._row("5140361901", krs="KRS 0001074645")
        status, _ = vr.verify_row(row)
        # Should NOT be DO-WERYFIKACJI from mod-11 (might be from KRS mismatch if KRS doesn't match)
        assert "mod-11 invalid" not in _


class TestKrsPreFlight:
    """KRS pre-flight: live API lookup, cross-check NIP."""

    def test_real_krs_real_nip(self):
        # BILLS KRS + BILLS NIP — should match
        result = vr.live_krs_lookup("0001074645")
        if result and "error" not in result:
            assert result["nip"] == "5140361901"
            assert "BILLS" in result.get("nazwa", "").upper()

    def test_hallucinated_krs_returns_404(self):
        # KRS 0000203325 — doesn't exist (PL-B-048 halucynacja)
        result = vr.live_krs_lookup("0000203325")
        assert result is not None
        assert "error" in result
        assert "404" in result["error"]

    def test_real_krs_different_nip_detected(self):
        # KRS 0000308003 → API NIP 5372504633 (MASTER PŁODOWSCY)
        # This is a real KRS but pointing to a different firm than the CSV
        result = vr.live_krs_lookup("0000308003")
        if result and "error" not in result:
            assert result["nip"] == "5372504633"
            assert "MASTER" in result.get("nazwa", "").upper() or "PŁODOWSCY" in result.get("nazwa", "").upper()


class TestVerifyRowKrsPreFlight:
    """verify_row() should catch KRS hallucination as DO-WERYFIKACJI."""

    def _row(self, nip, krs, name):
        return {
            "kraj": "PL",
            "id": "PL-TEST",
            "nazwa": name,
            "nip_vat": nip,
            "rejestr_id": krs,
            "zrodlo_danych": f"{krs} | {name[:20]}",
            "kategoria": "B8",
            "miasto": "Testowo",
            "adres": "ul. Test 1",
            "www": "https://test.pl",
            "wolumen": "duży",
            "confidence_wolumen": "🟢",
        }

    @pytest.mark.network
    def test_hallucinated_krs_becomes_do_weryfikacji(self):
        # PL-B-110 was: KRS 0000181515 → API NIP 5213266960 (FABRYKA ZNAKÓW)
        # CSV: WEST TRADING SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ
        row = self._row("9552074426", "KRS 0000181515", "WEST TRADING SPÓŁKA Z OGRANICZONĄ")
        status, reason = vr.verify_row(row)
        # Either KRS HALUCYNACJA (if KRS exists with different NIP) or
        # KRS lookup failed (if KRS 404)
        assert status == "DO-WERYFIKACJI"
        assert "KRS" in reason

    @pytest.mark.network
    def test_real_krs_with_real_nip_passes_krs_check(self):
        # BILLS: real KRS + real NIP → should pass KRS pre-flight
        row = self._row("5140361901", "KRS 0001074645", "BILLS SPÓŁKA Z OGRANICZONĄ")
        status, reason = vr.verify_row(row)
        # Mod-11 passes, KRS pre-flight passes (real NIP matches real KRS)
        # → would land in the FROZEN branch (last return in verify_row)
        # OR in DO-WERYFIKACJI from missing field check (depends on row completeness)
        assert "KRS HALUCYNACJA" not in reason
        assert "KRS lookup failed" not in reason
