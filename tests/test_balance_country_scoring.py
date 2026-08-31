"""Tests for tools/balance_country_scoring.py — verifier-aware field inference.

These tests pin down the iron rules the script must honor. They run as
unit tests on the inference functions (not on the full file walker) so
they don't touch data/ and are fast + CI-stable.

Iron rules encoded here (mirrors AGENTS.md "Never hallucinate" and the
INTEL entry on the verify gate):
  - Never overwrite a verifier-set 🟢/🟡/🔴.
  - Never overwrite a verified wolumen (duży/średni/mały).
  - HALUCYNACJA in flagi → 🔴 (structural fields cannot be trusted).
  - DO-WERYFIKACJI / sourcing='do weryfikacji' → 🟡 if any structural
    field present, else 🔴.
  - 'nie' in Catalog B marki_nabijarki is a meaningful sentinel —
    preserve it.
  - cross_sell_potential without a real signal in notes/sourcing/marki
    stays empty (honest unknown), not synthetic 'wysoki'.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "tools")

import balance_country_scoring as bcs


# ---------------------------------------------------------------------------
# Verifier-aware signal helpers
# ---------------------------------------------------------------------------

class TestHasHallucination:
    def test_exact(self):
        assert bcs.has_hallucination("⚠️ HALUCYNACJA KRS — KRS wskazuje na inną firmę")

    def test_lowercase(self):
        # Upper-cased internally, so lowercase still matches
        assert bcs.has_hallucination("halucynacja nip mod-11 invalid")

    def test_absent(self):
        assert not bcs.has_hallucination("2026-08-31 ✅ FROZEN (API)")

    def test_empty(self):
        assert not bcs.has_hallucination("")

    def test_none_safe(self):
        assert not bcs.has_hallucination(None)


class TestHasPendingVerification:
    def test_flag_pending(self):
        assert bcs.has_pending_verification("⏳ PENDING_API", "", "")

    def test_flag_do_weryfikacji(self):
        assert bcs.has_pending_verification("⚠️ DO-WERYFIKACJI (API)", "", "")

    def test_sourcing(self):
        assert bcs.has_pending_verification("", "do weryfikacji", "")

    def test_notes(self):
        assert bcs.has_pending_verification("", "", "weryfikacja czy importuje ⚠️ DO-WERYFIKACJI")

    def test_frozen_clean(self):
        assert not bcs.has_pending_verification("2026-08-31 ✅ FROZEN (API)", "Polska (dystrybucja)", "")

    def test_empty(self):
        assert not bcs.has_pending_verification("", "", "")


# ---------------------------------------------------------------------------
# Confidence inference — the heart of the verifier gate
# ---------------------------------------------------------------------------

class TestInferConfidence:
    def test_protected_green_preserved(self):
        """Already-🟢 must NEVER be downgraded, even if data looks weak."""
        row = {
            "confidence_wolumen": "🟢",
            "flagi": "", "sourcing": "", "notatki": "",
            "nip_vat": "", "www": "", "rejestr_id": "",
            "telefon": "", "email": "",
            "wolumen": "mały",
        }
        assert bcs.infer_confidence(row, "PL") == "🟢"

    def test_protected_yellow_preserved(self):
        row = dict.fromkeys(
            ["confidence_wolumen", "flagi", "sourcing", "notatki",
             "nip_vat", "www", "rejestr_id", "telefon", "email", "wolumen"],
            "",
        )
        row["confidence_wolumen"] = "🟡"
        row["nip_vat"] = "PL123"
        row["www"] = "x"
        row["rejestr_id"] = "KRS 1"
        # All conditions say 🟢, but 🟡 is preserved.
        assert bcs.infer_confidence(row, "PL") == "🟡"

    def test_hallucination_forces_red_even_with_structural_data(self):
        """The regression that bit PL-B-061 / PL-B-075 in the v1 script."""
        row = {
            "confidence_wolumen": "",
            "flagi": "⚠️ HALUCYNACJA NIP — mod-11 invalid 2026-08-31 ⚠️ DO-WERYFIKACJI (API)",
            "sourcing": "",
            "notatki": "hurtownia tytoniowa",
            "nip_vat": "PL1234567890",
            "www": "https://example.com",
            "rejestr_id": "KRS 0000123456",
            "telefon": "+48 600 000 000",
            "email": "x@x.pl",
            "wolumen": "duży",
        }
        assert bcs.infer_confidence(row, "PL") == "🔴"

    def test_pending_with_structural_is_yellow(self):
        row = {
            "confidence_wolumen": "",
            "flagi": "⏳ PENDING_API",
            "sourcing": "",
            "notatki": "",
            "nip_vat": "PL123", "www": "https://x.pl",
            "rejestr_id": "KRS 1", "telefon": "", "email": "",
            "wolumen": "średni",
        }
        assert bcs.infer_confidence(row, "PL") == "🟡"

    def test_pending_without_structural_is_red(self):
        row = {
            "confidence_wolumen": "",
            "flagi": "⚠️ DO-WERYFIKACJI (API)",
            "sourcing": "do weryfikacji", "notatki": "",
            "nip_vat": "", "www": "", "rejestr_id": "",
            "telefon": "", "email": "",
            "wolumen": "średni",
        }
        assert bcs.infer_confidence(row, "PL") == "🔴"

    def test_pending_in_sourcing_with_structural_is_yellow(self):
        row = {
            "confidence_wolumen": "",
            "flagi": "",
            "sourcing": "do weryfikacji", "notatki": "",
            "nip_vat": "PL123", "www": "https://x.pl",
            "rejestr_id": "KRS 1", "telefon": "", "email": "",
            "wolumen": "średni",
        }
        assert bcs.infer_confidence(row, "PL") == "🟡"

    def test_frozen_is_green(self):
        row = {
            "confidence_wolumen": "",
            "flagi": "2026-08-31 ✅ FROZEN (API)",
            "sourcing": "", "notatki": "",
            "nip_vat": "PL123", "www": "https://x.pl",
            "rejestr_id": "KRS 1", "telefon": "", "email": "",
            "wolumen": "duży",
        }
        assert bcs.infer_confidence(row, "PL") == "🟢"

    def test_structural_complete_is_green(self):
        row = {
            "confidence_wolumen": "",
            "flagi": "", "sourcing": "", "notatki": "",
            "nip_vat": "PL123", "www": "https://x.pl",
            "rejestr_id": "KRS 1", "telefon": "", "email": "",
            "wolumen": "duży",
        }
        assert bcs.infer_confidence(row, "PL") == "🟢"

    def test_structural_complete_no_registry_is_yellow(self):
        row = {
            "confidence_wolumen": "",
            "flagi": "", "sourcing": "", "notatki": "",
            "nip_vat": "PL123", "www": "https://x.pl",
            "rejestr_id": "", "telefon": "", "email": "",
            "wolumen": "duży",
        }
        # nip+www but no registry → 🟡 per the rule
        assert bcs.infer_confidence(row, "PL") == "🟡"

    def test_empty_inputs_default_yellow(self):
        row = dict.fromkeys(
            ["confidence_wolumen", "flagi", "sourcing", "notatki",
             "nip_vat", "www", "rejestr_id", "telefon", "email", "wolumen"],
            "",
        )
        assert bcs.infer_confidence(row, "PL") == "🟡"


# ---------------------------------------------------------------------------
# Wolumen — never overwrite verified values
# ---------------------------------------------------------------------------

class TestInferVolume:
    def test_existing_duzy_preserved(self):
        row = {"wolumen": "duży", "tier": "detalista", "kategoria": "B4",
               "notatki": "", "nazwa_firmy": ""}
        assert bcs.infer_volume(row, "PL") == "duży"

    def test_existing_sredni_preserved(self):
        row = {"wolumen": "średni", "tier": "producent", "kategoria": "B8",
               "notatki": "", "nazwa_firmy": ""}
        assert bcs.infer_volume(row, "PL") == "średni"

    def test_empty_with_hurtownik_in_pl_is_duzy(self):
        row = {"wolumen": "", "tier": "hurtownik", "kategoria": "B8",
               "notatki": "", "nazwa_firmy": ""}
        assert bcs.infer_volume(row, "PL") == "duży"

    def test_empty_with_hurtownik_in_lt_is_sredni(self):
        row = {"wolumen": "", "tier": "hurtownik", "kategoria": "B8",
               "notatki": "", "nazwa_firmy": ""}
        # LT is "mały" market but B8 hurtownik → średni
        assert bcs.infer_volume(row, "LT") == "średni"

    def test_empty_with_lider_signal_is_duzy(self):
        row = {"wolumen": "", "tier": "", "kategoria": "",
               "notatki": "lider rynku, 1000+ sklepów", "nazwa_firmy": ""}
        assert bcs.infer_volume(row, "PL") == "duży"

    def test_empty_with_kiosk_signal_is_maly(self):
        row = {"wolumen": "", "tier": "", "kategoria": "",
               "notatki": "lokalny kiosk", "nazwa_firmy": ""}
        assert bcs.infer_volume(row, "PL") == "mały"

    def test_brak_treated_as_empty(self):
        row = {"wolumen": "brak", "tier": "hurtownik", "kategoria": "B8",
               "notatki": "", "nazwa_firmy": ""}
        assert bcs.infer_volume(row, "PL") == "duży"


# ---------------------------------------------------------------------------
# Tier — never overwrite verified values
# ---------------------------------------------------------------------------

class TestInferTier:
    def test_existing_preserved(self):
        row = {"tier": "detalista", "notatki": "producent papierosów", "kategoria": "B8"}
        assert bcs.infer_tier(row) == "detalista"

    def test_empty_with_producent_notes(self):
        row = {"tier": "", "notatki": "zakład produkcyjny", "kategoria": ""}
        assert bcs.infer_tier(row) == "producent"

    def test_empty_with_b8_kategoria_is_hurtownik(self):
        row = {"tier": "", "notatki": "", "kategoria": "B8"}
        assert bcs.infer_tier(row) == "hurtownik"

    def test_empty_fallback_reseller(self):
        row = {"tier": "", "notatki": "", "kategoria": ""}
        assert bcs.infer_tier(row) == "reseller"


# ---------------------------------------------------------------------------
# Powinowactwo (Catalog B) — never overwrite valid 1-5
# ---------------------------------------------------------------------------

class TestInferPowinowactwo:
    def test_existing_4_preserved(self):
        row = {"powinowactwo_nabijarki": "4", "kategoria": "B8", "notatki": ""}
        assert bcs.infer_powinowactwo(row) == "4"

    def test_existing_2_preserved_even_if_b8(self):
        """Human-set value beats category default — never override."""
        row = {"powinowactwo_nabijarki": "2", "kategoria": "B8", "notatki": ""}
        assert bcs.infer_powinowactwo(row) == "2"

    def test_empty_b8_gets_5(self):
        row = {"powinowactwo_nabijarki": "", "kategoria": "B8", "notatki": ""}
        assert bcs.infer_powinowactwo(row) == "5"

    def test_empty_b1_gets_2(self):
        row = {"powinowactwo_nabijarki": "", "kategoria": "B1", "notatki": ""}
        assert bcs.infer_powinowactwo(row) == "2"

    def test_invalid_string_falls_through(self):
        row = {"powinowactwo_nabijarki": "abc", "kategoria": "B8", "notatki": ""}
        assert bcs.infer_powinowactwo(row) == "5"

    def test_tyton_signal_raises_floor(self):
        row = {"powinowactwo_nabijarki": "", "kategoria": "B1", "notatki": "tytoń sypki"}
        # B1 default is 2, but "tytoń" signal raises to max(2, 4) = 4
        assert bcs.infer_powinowactwo(row) == "4"

    def test_out_of_range_replaced(self):
        row = {"powinowactwo_nabijarki": "9", "kategoria": "B8", "notatki": ""}
        # 9 is out of 1-5 range → not valid, fall through
        assert bcs.infer_powinowactwo(row) == "5"


# ---------------------------------------------------------------------------
# cross_sell_potential — never hallucinate
# ---------------------------------------------------------------------------

class TestInferCrossSellSignal:
    def test_tyton_signal(self):
        row = {"notatki": "hurtownia tytoniowa", "sourcing": "", "marki_nabijarki": ""}
        assert bcs.infer_cross_sell_signal(row) is True

    def test_gilzy_signal(self):
        row = {"notatki": "sprzedaż gilz", "sourcing": "", "marki_nabijarki": ""}
        assert bcs.infer_cross_sell_signal(row) is True

    def test_papieros_signal(self):
        row = {"notatki": "papierosy + FMCG", "sourcing": "", "marki_nabijarki": ""}
        assert bcs.infer_cross_sell_signal(row) is True

    def test_nabijarka_signal(self):
        row = {"notatki": "nabijarki do tytoniu", "sourcing": "", "marki_nabijarki": ""}
        assert bcs.infer_cross_sell_signal(row) is True

    def test_no_signal(self):
        row = {"notatki": "sklep wielobranżowy", "sourcing": "", "marki_nabijarki": ""}
        assert bcs.infer_cross_sell_signal(row) is False

    def test_sourcing_alone_is_signal(self):
        row = {"notatki": "", "sourcing": "Chiny (import)", "marki_nabijarki": ""}
        assert bcs.infer_cross_sell_signal(row) is True

    def test_marki_nie_is_not_signal(self):
        """'nie' = "no, doesn't carry these brands" — NOT a positive cross-sell signal."""
        row = {"notatki": "", "sourcing": "", "marki_nabijarki": "nie"}
        assert bcs.infer_cross_sell_signal(row) is False

    def test_empty_all(self):
        row = {"notatki": "", "sourcing": "", "marki_nabijarki": ""}
        assert bcs.infer_cross_sell_signal(row) is False


# ---------------------------------------------------------------------------
# marki_nabijarki — Catalog B "nie" preservation
# ---------------------------------------------------------------------------

class TestCatalogBMarkiPreservation:
    """The regression: v1 cleared 'nie' to ''. 'nie' is a fact, not a default."""

    def test_nie_is_not_in_placeholder_set(self):
        """Pin: 'nie' must NOT be in CATB_MARKI_PLACEHOLDERS — the
        balance_catalog_file driver only clears values in that set."""
        assert "nie" not in bcs.CATB_MARKI_PLACEHOLDERS
        assert "brak" in bcs.CATB_MARKI_PLACEHOLDERS
        assert "do ustalenia" in bcs.CATB_MARKI_PLACEHOLDERS

    def test_nie_preserved_by_infer_marki_for_cat_a(self):
        """infer_marki_for_cat_a is for Catalog A only — but it's safe
        to verify it doesn't accidentally emit 'nie' from a clean state."""
        row = {"marki_nabijarki": "nie", "notatki": "", "nazwa_firmy": ""}
        # Existing 'nie' is preserved by the function (not a sentinel)
        assert bcs.infer_marki_for_cat_a(row) == "nie"


# ---------------------------------------------------------------------------
# Driver — atomic file write
# ---------------------------------------------------------------------------

class TestBalanceCatalogFile:
    def test_hallucination_row_stays_red_after_run(self, tmp_path):
        """End-to-end: a Catalog B row with HALUCYNACJA + structural data
        must come out 🔴, not 🟢."""
        csv_path = tmp_path / "catalog-B-XX.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "kraj", "id_unikalne", "nazwa_firmy", "tier", "kategoria",
                "rynek_skala", "wolumen", "confidence_wolumen",
                "cross_sell_potential", "powinowactwo_nabijarki",
                "marki_nabijarki", "marka_wlasna_oem", "notatki",
                "flagi", "sourcing", "nip_vat", "www", "rejestr_id",
                "telefon", "email",
            ])
            writer.writeheader()
            writer.writerow({
                "kraj": "XX", "id_unikalne": "XX-B-001",
                "nazwa_firmy": "Test Co",
                "tier": "hurtownik", "kategoria": "B8",
                "rynek_skala": "",
                "wolumen": "",
                "confidence_wolumen": "",
                "cross_sell_potential": "brak",
                "powinowactwo_nabijarki": "",
                "marki_nabijarki": "nie",
                "marka_wlasna_oem": "",
                "notatki": "hurtownia tytoniowa",
                "flagi": "⚠️ HALUCYNACJA NIP 2026-08-31 ⚠️ DO-WERYFIKACJI (API)",
                "sourcing": "do weryfikacji",
                "nip_vat": "PL1234567890",
                "www": "https://example.com",
                "rejestr_id": "KRS 0000123456",
                "telefon": "+48 600 000 000",
                "email": "x@x.pl",
            })

        # Patch ROOT/DATA path resolution for tmp run
        original_data = bcs.DATA
        bcs.DATA = tmp_path
        try:
            result = bcs.balance_catalog_file(csv_path)
        finally:
            bcs.DATA = original_data

        with open(csv_path, "r", encoding="utf-8") as f:
            row = next(csv.DictReader(f))

        # Critical assertions:
        assert row["confidence_wolumen"] == "🔴", \
            f"Hallucination flag must force 🔴, got {row['confidence_wolumen']!r}"
        # 'nie' is preserved (Catalog B, explicit "no")
        assert row["marki_nabijarki"] == "nie", \
            f"'nie' must be preserved, got {row['marki_nabijarki']!r}"
        # cross_sell_potential was 'brak' (sentinel) and there IS a tyton signal,
        # so it gets filled to category default.
        assert row["cross_sell_potential"] == "wysoki", \
            f"With tyton signal, B8 should be 'wysoki', got {row['cross_sell_potential']!r}"
        # rynek_skala filled with country default (XX is unknown → średni)
        assert row["rynek_skala"] == "średni"
        # powinowactwo_nabijarki 1-5 for B
        assert row["powinowactwo_nabijarki"] in {"1", "2", "3", "4", "5"}

    def test_protected_confidence_not_overwritten(self, tmp_path):
        """A row that's already 🟢 must stay 🟢 even if flagi says PENDING."""
        csv_path = tmp_path / "catalog-B-YY.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "kraj", "id_unikalne", "nazwa_firmy", "tier", "kategoria",
                "rynek_skala", "wolumen", "confidence_wolumen",
                "cross_sell_potential", "powinowactwo_nabijarki",
                "marki_nabijarki", "marka_wlasna_oem", "notatki",
                "flagi", "sourcing", "nip_vat", "www", "rejestr_id",
                "telefon", "email",
            ])
            writer.writeheader()
            writer.writerow({
                "kraj": "YY", "id_unikalne": "YY-B-001",
                "nazwa_firmy": "Verified Co",
                "tier": "hurtownik", "kategoria": "B8",
                "rynek_skala": "",
                "wolumen": "duży",
                "confidence_wolumen": "🟢",  # already verified
                "cross_sell_potential": "wysoki",
                "powinowactwo_nabijarki": "5",
                "marki_nabijarki": "nie",
                "marka_wlasna_oem": "",
                "notatki": "hurtownia tytoniowa",
                "flagi": "⏳ PENDING_API",  # would normally cap at 🟡
                "sourcing": "",
                "nip_vat": "PL123", "www": "https://x.pl",
                "rejestr_id": "KRS 1",
                "telefon": "", "email": "",
            })

        original_data = bcs.DATA
        bcs.DATA = tmp_path
        try:
            bcs.balance_catalog_file(csv_path)
        finally:
            bcs.DATA = original_data

        with open(csv_path, "r", encoding="utf-8") as f:
            row = next(csv.DictReader(f))

        # 🟢 must be preserved (verifier already judged this)
        assert row["confidence_wolumen"] == "🟢", \
            f"Protected 🟢 was overwritten to {row['confidence_wolumen']!r}"
        # Verified wolumen preserved
        assert row["wolumen"] == "duży"
        # powinowactwo 5 preserved
        assert row["powinowactwo_nabijarki"] == "5"
        # 'nie' preserved
        assert row["marki_nabijarki"] == "nie"

    def test_no_signal_no_cross_sell(self, tmp_path):
        """cross_sell_potential stays empty when there are no signals."""
        csv_path = tmp_path / "catalog-B-ZZ.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "kraj", "id_unikalne", "nazwa_firmy", "tier", "kategoria",
                "rynek_skala", "wolumen", "confidence_wolumen",
                "cross_sell_potential", "powinowactwo_nabijarki",
                "marki_nabijarki", "marka_wlasna_oem", "notatki",
                "flagi", "sourcing", "nip_vat", "www", "rejestr_id",
                "telefon", "email",
            ])
            writer.writeheader()
            writer.writerow({
                "kraj": "ZZ", "id_unikalne": "ZZ-B-001",
                "nazwa_firmy": "Generic Co",
                "tier": "reseller", "kategoria": "B1",
                "rynek_skala": "",
                "wolumen": "",
                "confidence_wolumen": "",
                "cross_sell_potential": "do ustalenia",  # sentinel + no signal
                "powinowactwo_nabijarki": "",
                "marki_nabijarki": "",
                "marka_wlasna_oem": "",
                "notatki": "sklep wielobranżowy",  # NO tytoń/gilzy/papieros
                "flagi": "",
                "sourcing": "do weryfikacji",
                "nip_vat": "PL123", "www": "https://x.pl",
                "rejestr_id": "KRS 1",
                "telefon": "", "email": "",
            })

        original_data = bcs.DATA
        bcs.DATA = tmp_path
        try:
            bcs.balance_catalog_file(csv_path)
        finally:
            bcs.DATA = original_data

        with open(csv_path, "r", encoding="utf-8") as f:
            row = next(csv.DictReader(f))

        # cross_sell_potential should stay empty (no signal) — NOT be filled
        # to a synthetic 'wysoki' default.
        assert row["cross_sell_potential"] in {"", "do ustalenia"}, \
            f"Without signal, cross_sell should stay empty, got {row['cross_sell_potential']!r}"


# Import here so the test file fails clearly if csv isn't available
import csv
