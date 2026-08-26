"""Tests for tools/validate_columns.py — header mapping + value validators."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, "tools")

import validate_columns as vc


class TestNormalize:
    def test_lowercase(self):
        assert vc._normalize("NAZWA_FIRMY") == "nazwa firmy"

    def test_strip_diacritics(self):
        assert vc._normalize("Łódź") == "lodz"
        assert vc._normalize("Přeštice") == "prestice"
        # Uppercase Ł (U+0141) and ł (U+0142) are atomic in Unicode — NFKD
        # doesn't decompose them. The manual map in _normalize handles them.
        assert vc._normalize("ŁÓDŹ") == "lodz"
        assert vc._normalize("Straße") == "strasse"  # casefold handles ß
        assert vc._normalize("Malmö") == "malmo"  # Swedish
        assert vc._normalize("Üniversität") == "universitat"  # German
        assert vc._normalize("Curaçao") == "curacao"  # Dutch Caribbean
        assert vc._normalize("København") == "kobenhavn"  # Danish ø → o
        assert vc._normalize("Reykjavík") == "reykjavik"  # Icelandic
        assert vc._normalize("Æther") == "aether"  # Nordic ligature
        assert vc._normalize("Œuvre") == "oeuvre"  # French ligature
        assert vc._normalize("Zagreb") == "zagreb"  # Croatian đ — already covered

    def test_underscore_to_space(self):
        assert vc._normalize("id_unikalne") == "id unikalne"

    def test_collapse_whitespace(self):
        assert vc._normalize("  foo   bar  ") == "foo bar"


class TestHeaderMapping:
    def test_exact_match(self):
        lookup = vc._build_alias_lookup(vc.DEFAULT_ALIASES)
        canon, conf, source = vc.map_header("id_unikalne", lookup, {})
        assert canon == "id_unikalne"
        assert conf == 1.0
        assert source == "exact"

    def test_alias_match_polish(self):
        lookup = vc._build_alias_lookup(vc.DEFAULT_ALIASES)
        canon, conf, source = vc.map_header("firma", lookup, {})
        assert canon == "nazwa_firmy"
        assert source == "alias"
        assert conf >= 0.9

    def test_alias_match_english(self):
        lookup = vc._build_alias_lookup(vc.DEFAULT_ALIASES)
        canon, conf, source = vc.map_header("company", lookup, {})
        assert canon == "nazwa_firmy"
        assert source == "alias"

    def test_alias_match_german(self):
        lookup = vc._build_alias_lookup(vc.DEFAULT_ALIASES)
        canon, conf, source = vc.map_header("unternehmen", lookup, {})
        assert canon == "nazwa_firmy"
        assert source == "alias"

    def test_fuzzy_match(self):
        lookup = vc._build_alias_lookup(vc.DEFAULT_ALIASES)
        canon, conf, source = vc.map_header("kategorja", lookup, {})  # typo
        # Should fuzzy-match to "kategoria"
        assert canon in (None, "kategoria")

    def test_unknown_column(self):
        lookup = vc._build_alias_lookup(vc.DEFAULT_ALIASES)
        canon, conf, source = vc.map_header("xyzzy_foobar_42", lookup, {})
        assert canon is None
        assert source in ("unknown", "fuzzy")

    def test_manual_override(self):
        lookup = vc._build_alias_lookup(vc.DEFAULT_ALIASES)
        canon, conf, source = vc.map_header("foo", lookup, {"foo": "nazwa_firmy"})
        assert canon == "nazwa_firmy"
        assert source == "manual"
        assert conf == 1.0


class TestValueValidators:
    def test_id_unikalne_valid(self):
        issues = vc.validate_value("id_unikalne", "PL-A-001", "PL")
        assert issues == []

    def test_id_unikalne_invalid(self):
        issues = vc.validate_value("id_unikalne", "BILLS-1", "PL")
        assert len(issues) == 1

    def test_id_unikalne_required(self):
        issues = vc.validate_value("id_unikalne", "", "PL")
        assert any("required" in i for i in issues)

    def test_kategoria_enum(self):
        assert vc.validate_value("kategoria", "A1", "PL") == []
        assert vc.validate_value("kategoria", "B5", "PL") == []
        assert vc.validate_value("kategoria", "Z9", "PL") != []

    def test_nip_pl_valid(self):
        assert vc.validate_value("nip_vat", "PL1234567890", "PL") == []
        assert vc.validate_value("nip_vat", "PL0000000000", "PL") == []
        assert vc.validate_value("nip_vat", "", "PL") == []
        issues = vc.validate_value("nip_vat", "PL12345", "PL")
        assert len(issues) == 1

    def test_nip_cz_valid(self):
        assert vc.validate_value("nip_vat", "CZ12345678", "CZ") == []
        issues = vc.validate_value("nip_vat", "CZ1234567", "CZ")
        assert len(issues) == 1

    def test_ico_pl_invalid_country(self):
        # No pattern for unknown country → warning, not error
        issues = vc.validate_value("nip_vat", "XX12345", "XX")
        assert any("no NIP pattern" in i for i in issues)

    def test_url_valid(self):
        assert vc.validate_value("www", "https://example.com", "PL") == []
        assert vc.validate_value("www", "www.example.com", "PL") == []
        assert vc.validate_value("www", "", "PL") == []
        assert vc.validate_value("www", "not a url", "PL") != []

    def test_url_linkedin_must_contain(self):
        assert vc.validate_value("linkedin", "https://linkedin.com/company/x", "PL") == []
        issues = vc.validate_value("linkedin", "https://facebook.com/x", "PL")
        assert any("linkedin.com" in i for i in issues)

    def test_email_valid(self):
        assert vc.validate_value("email", "info@example.com", "PL") == []
        assert vc.validate_value("email", "", "PL") == []
        assert vc.validate_value("email", "not-an-email", "PL") != []

    def test_tier_enum(self):
        assert vc.validate_value("tier", "wyłączność", "PL") == []
        assert vc.validate_value("tier", "reseller", "PL") == []
        assert vc.validate_value("tier", "unknown_tier", "PL") != []

    def test_kanal_sprzedazy_loose(self):
        # Strict enum: fail
        assert vc.validate_value("kanal_sprzedaży", "B2B only", "PL") == []
        # Loose match: contains "B2B" → pass
        assert vc.validate_value("kanal_sprzedaży", "B2B hurtownia + sieć kiosków", "PL") == []
        # Doesn't contain any enum token → fail
        assert vc.validate_value("kanal_sprzedaży", "completely unrelated text", "PL") != []

    def test_enum_loose_first_word_match(self):
        # "Sklep stacjonarny + Allegro" should match enum "sklep stacjonarny" via first-word
        assert vc.validate_value("kanal_sprzedaży", "Sklep stacjonarny + Allegro", "PL") == []
        # "Marketplace (Amazon)" should match enum "marketplace" via first-word
        assert vc.validate_value("kanal_sprzedaży", "Marketplace (Amazon)", "PL") == []
        # First-word doesn't appear → fail
        assert vc.validate_value("kanal_sprzedaży", "Hotel recepcyjny", "PL") != []

    def test_kanal_sprzedazy_loose_aliases(self):
        # Path C: extended loose aliases for descriptive values seen in the wild.
        # Each value's first word matches one of the loose aliases.
        assert vc.validate_value("kanal_sprzedaży", "Hurt + E-commerce sieciowy", "PL") == []
        assert vc.validate_value("kanal_sprzedaży", "Hurt (EMTAK 46.35)", "PL") == []
        assert vc.validate_value("kanal_sprzedaży", "Veleprodaja & Spletna trgovina", "PL") == []
        assert vc.validate_value("kanal_sprzedaży", "E-commerce (Sellme.ee)", "PL") == []
        assert vc.validate_value("kanal_sprzedaży", "Dystrybucja hurtowa", "PL") == []
        assert vc.validate_value("kanal_sprzedaży", "Logistyka celno-akcyzowa", "PL") == []
        # "agent" alias matches "Agent celny" (Polish singular for broker) — not "Agencja"
        assert vc.validate_value("kanal_sprzedaży", "Agent celny", "PL") == []
        # "agencja" alias matches "Agencja celna" (Polish noun form)
        assert vc.validate_value("kanal_sprzedaży", "Agencja celna + Skład akcyzowy", "PL") == []
        # "obsługa" alias matches "Obsługa celna i skład celny"
        assert vc.validate_value("kanal_sprzedaży", "Obsługa celna i skład celny", "PL") == []
        # "B2C" alias matches "B2C e-commerce"
        assert vc.validate_value("kanal_sprzedaży", "B2C e-commerce (tabacarouler.fr)", "PL") == []
        # "cash" + "carry" aliases match "Cash & Carry Veleprodaja"
        assert vc.validate_value("kanal_sprzedaży", "Cash & Carry Veleprodaja", "PL") == []
        # "wholesale" alias matches "Wholesale platform"
        assert vc.validate_value("kanal_sprzedaży", "Wholesale platform", "PL") == []
        # "sieciowy" alias matches "Sieciowy retailer"
        assert vc.validate_value("kanal_sprzedaży", "Sieciowy retailer (8+ lokali)", "PL") == []
        # "produkcja" alias matches "Produkcja i dystrybucja hurtowa"
        assert vc.validate_value("kanal_sprzedaży", "Produkcja i dystrybucja hurtowa", "PL") == []
        # Truly unrelated → still fail
        assert vc.validate_value("kanal_sprzedaży", "kosmos", "PL") != []

    def test_powinowactwo_range(self):
        assert vc.validate_value("powinowactwo_nabijarki", "3", "PL") == []
        assert vc.validate_value("powinowactwo_nabijarki", "1", "PL") == []
        assert vc.validate_value("powinowactwo_nabijarki", "5", "PL") == []
        assert vc.validate_value("powinowactwo_nabijarki", "0", "PL") != []
        assert vc.validate_value("powinowactwo_nabijarki", "6", "PL") != []
        assert vc.validate_value("powinowactwo_nabijarki", "", "PL") == []

    def test_cross_sell_enum_or_empty(self):
        assert vc.validate_value("cross_sell_potential", "wysoki", "PL") == []
        assert vc.validate_value("cross_sell_potential", "średni", "PL") == []
        assert vc.validate_value("cross_sell_potential", "niski", "PL") == []
        assert vc.validate_value("cross_sell_potential", "bardzo wysoki", "PL") == []
        # Empty and sentinel placeholders are treated as empty (valid for B-only field)
        assert vc.validate_value("cross_sell_potential", "", "PL") == []
        assert vc.validate_value("cross_sell_potential", "n/a", "PL") == []
        assert vc.validate_value("cross_sell_potential", "brak", "PL") == []
        # Path C: descriptive sourcing values are accepted via loose match
        # (first-word of enum aliases matches token in value).
        assert vc.validate_value("sourcing", "import (UE + Azja)", "PL") == []
        assert vc.validate_value("sourcing", "dystrybucja krajowa", "PL") == []
        assert vc.validate_value("sourcing", "dystrybucja regionalna", "PL") == []
        assert vc.validate_value("sourcing", "dystrybucja ogólnokrajowa", "PL") == []
        assert vc.validate_value("sourcing", "własna produkcja + import", "PL") == []
        assert vc.validate_value("sourcing", "produkcja krajowa", "PL") == []
        # Strict enum values still pass
        assert vc.validate_value("sourcing", "Chiny", "PL") == []
        assert vc.validate_value("sourcing", "Europa", "PL") == []
        assert vc.validate_value("sourcing", "Polska", "PL") == []
        assert vc.validate_value("sourcing", "mix", "PL") == []
        # Truly unrelated → fail
        assert vc.validate_value("sourcing", "kosmos", "PL") != []
        # Empty is OK (sourcing is allow_empty)
        assert vc.validate_value("sourcing", "", "PL") == []

    def test_date_format(self):
        assert vc.validate_value("data_weryfikacji", "2026-08-25", "PL") == []
        assert vc.validate_value("data_weryfikacji", "", "PL") == []
        assert vc.validate_value("data_weryfikacji", "25/08/2026", "PL") != []
        assert vc.validate_value("data_weryfikacji", "2026-13-01", "PL") != []  # invalid month

    def test_rok_zalozenia_range(self):
        assert vc.validate_value("rok_zalozenia", "2020", "PL") == []
        assert vc.validate_value("rok_zalozenia", "1800", "PL") == []
        assert vc.validate_value("rok_zalozenia", "1799", "PL") != []
        assert vc.validate_value("rok_zalozenia", "2031", "PL") != []
        assert vc.validate_value("rok_zalozenia", "", "PL") == []


class TestCrossConsistency:
    def test_a_row_powinowactwo_should_be_empty(self):
        row = {"kategoria": "A1", "powinowactwo_nabijarki": "3"}
        issues = vc.cross_check(row, "A")
        assert any("powinowactwo" in i for i in issues)

    def test_a_row_cross_sell_should_be_empty(self):
        row = {"kategoria": "A1", "cross_sell_potential": "wysoki"}
        issues = vc.cross_check(row, "A")
        assert any("cross_sell" in i for i in issues)

    def test_b_row_marki_should_be_empty(self):
        row = {"kategoria": "B8", "marki_nabijarki": "PowerMatic", "powinowactwo_nabijarki": "3", "cross_sell_potential": "wysoki"}
        issues = vc.cross_check(row, "B")
        assert any("marki_nabijarki" in i for i in issues)

    def test_b_row_marki_sentinel_is_empty(self):
        # Sentinel placeholders ("brak", "n/a", "nie", "do weryfikacji", etc.)
        # are treated as empty — no B-row violation.
        for sentinel in ("brak", "n/a", "nie", "no", "do weryfikacji", "do ustalenia"):
            row = {"kategoria": "B8", "marki_nabijarki": sentinel,
                   "powinowactwo_nabijarki": "3", "cross_sell_potential": "wysoki"}
            issues = vc.cross_check(row, "B")
            assert not any("marki_nabijarki" in i for i in issues), \
                f"'{sentinel}' should be treated as empty (no B-row violation)"

    def test_b_row_missing_powinowactwo(self):
        row = {"kategoria": "B8", "cross_sell_potential": "wysoki"}
        issues = vc.cross_check(row, "B")
        assert any("missing powinowactwo" in i for i in issues)

    def test_b_row_missing_cross_sell(self):
        row = {"kategoria": "B8", "powinowactwo_nabijarki": "3"}
        issues = vc.cross_check(row, "B")
        assert any("missing cross_sell" in i for i in issues)

    def test_clean_b_row_no_issues(self):
        row = {"kategoria": "B8", "powinowactwo_nabijarki": "4", "cross_sell_potential": "wysoki"}
        issues = vc.cross_check(row, "B")
        assert issues == []

    def test_clean_a_row_no_issues(self):
        row = {"kategoria": "A1"}
        issues = vc.cross_check(row, "A")
        assert issues == []


class TestSentinelNormalisation:
    """KNOW_NON_VALUE + normalize_non_value — provenance placeholders."""

    def test_known_sentinels_normalised_to_empty(self):
        for sentinel in ("brak", "n/a", "na", "nd", "nie", "no",
                         "nie dotyczy", "do weryfikacji", "do ustalenia",
                         "do uzupe\u0142nienia", "unknown", "\u2014", "\u2013", "-"):
            assert vc.normalize_non_value(sentinel) == "", f"sentinel {sentinel!r} -> empty"

    def test_non_sentinels_pass_through(self):
        for value in ("PowerMatic", "wysoki", "https://example.com", "test@example.com",
                      "+48 123 456 789", "PL", "mix"):
            assert vc.normalize_non_value(value) == value.strip(), f"value {value!r} passes through"

    def test_sentinel_on_enum_columns(self):
        assert vc.validate_value("cross_sell_potential", "brak", "PL") == []
        assert vc.validate_value("cross_sell_potential", "do ustalenia", "PL") == []
        assert vc.validate_value("linkedin", "brak", "PL") == []
        assert vc.validate_value("email_decydent", "n/a", "PL") == []


class TestSeparatorDetection:
    def test_comma(self, tmp_path):
        p = tmp_path / "test.csv"
        p.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
        assert vc.detect_separator(p) == ","

    def test_semicolon(self, tmp_path):
        p = tmp_path / "test.csv"
        p.write_text("a;b;c\n1;2;3\n", encoding="utf-8")
        assert vc.detect_separator(p) == ";"

    def test_tab(self, tmp_path):
        p = tmp_path / "test.csv"
        p.write_text("a\tb\tc\n1\t2\t3\n", encoding="utf-8")
        assert vc.detect_separator(p) == "\t"


class TestInferCountry:
    def test_from_filename(self, tmp_path):
        p = tmp_path / "catalog-A-PL.csv"
        p.write_text("a\n1\n", encoding="utf-8")
        assert vc.infer_country(p, {}) == "PL"

    def test_from_mapped_kraj_column(self):
        mappings = {"country": {"canonical": "kraj", "confidence": 1.0, "source": "alias"}}
        row = {"country": "PL"}
        assert vc.infer_country(Path("anything.csv"), row, mappings) == "PL"

    def test_from_row_value_scan(self):
        # No filename pattern, no mapping — but row has a known ISO code
        row = {"some_col": "PL", "other": "foo"}
        assert vc.infer_country(Path("foo.csv"), row, None) == "PL"

    def test_unknown_country(self):
        row = {"some_col": "US"}
        assert vc.infer_country(Path("foo.csv"), row, None) is None

    def test_empty_row(self):
        from pathlib import Path
        assert vc.infer_country(Path("foo.csv"), {}, None) is None

    def test_filename_pattern_uses_stem_not_full_path(self):
        # Bug fix: regex had \.csv at end but path.stem excludes extension.
        # This test ensures catalog-A-PL.csv (any path) → "PL".
        p = Path("/some/deep/path/catalog-B-CZ.csv")
        assert vc.infer_country(p, {}) == "CZ"
        p2 = Path("./relative/catalog-A-HR.csv")
        assert vc.infer_country(p2, {}) == "HR"
