"""Tests for tools/map_intake.py — 35→37 column mapping + tier/kategoria logic."""
from __future__ import annotations

import sys
sys.path.insert(0, "tools")

import map_intake as mi


class TestNormalizeEmail:
    def test_single(self):
        assert mi.normalize_email("info@example.com") == "info@example.com"

    def test_multi_recipient_takes_first(self):
        assert mi.normalize_email("a@x.com; b@y.com") == "a@x.com"
        assert mi.normalize_email("ceo@firm.cz, biuro@firm.cz") == "ceo@firm.cz"

    def test_empty(self):
        assert mi.normalize_email("") == ""
        assert mi.normalize_email(None) == ""

    def test_invalid(self):
        assert mi.normalize_email("not-an-email") == ""


class TestNormalizePhone:
    def test_single(self):
        assert mi.normalize_phone("+420 272 774 153") == "+420 272 774 153"

    def test_multi_takes_first(self):
        assert mi.normalize_phone("+370 620 40051; +370 600 36608") == "+370 620 40051"

    def test_pipe_separator(self):
        assert mi.normalize_phone("+48 22 123 | +48 22 456") == "+48 22 123"

    def test_empty(self):
        assert mi.normalize_phone("") == ""


class TestNormalizeRejestr:
    def test_cz_plain(self):
        assert mi.normalize_rejestr("25775634", "CZ") == "ARES IČO 25775634"

    def test_cz_with_label(self):
        assert mi.normalize_rejestr("ARES IČO 25221981", "CZ") == "ARES IČO 25221981"

    def test_cz_invalid(self):
        assert mi.normalize_rejestr("5678950", "CZ") == ""  # 7 digits, not 8

    def test_ee_plain(self):
        assert mi.normalize_rejestr("11370720", "EE") == "e-Äriregister 11370720"

    def test_lt_plain(self):
        assert mi.normalize_rejestr("110443493", "LT") == "JAR 110443493"


class TestNormalizeNip:
    def test_cz_dic(self):
        assert mi.normalize_nip("CZ25775634") == "25775634"

    def test_ee_kmkr(self):
        assert mi.normalize_nip("EE101376895") == "101376895"

    def test_lt_pvm(self):
        assert mi.normalize_nip("LT100002442812") == "100002442812"


class TestDeriveRegion:
    def test_known_cz(self):
        assert mi.derive_region("CZ", "Hlavní město Praha") == ("PR", "Hlavní město Praha", "kraj")

    def test_unknown_cz_fallback(self):
        kod, nazwa, typ = mi.derive_region("CZ", "Nowy region")
        assert kod == "NO"
        assert nazwa == "Nowy region"
        assert typ == "nieznany"

    def test_empty(self):
        assert mi.derive_region("CZ", "") == ("XX", "nieznany", "nieznany")

    def test_ee_no_regions(self):
        # EE doesn't have a region map — falls back to first 2 chars
        kod, nazwa, typ = mi.derive_region("EE", "Harju maakond")
        assert kod == "HA"


class TestMakeId:
    def test_format(self):
        assert mi.make_id("CZ", "PR", "5") == "CZ-B-PR-005"
        assert mi.make_id("CZ", "PR", "12") == "CZ-B-PR-012"
        assert mi.make_id("CZ", "PR", "100") == "CZ-B-PR-100"

    def test_invalid_rank(self):
        assert mi.make_id("CZ", "PR", "abc") == "CZ-B-PR-000"
        assert mi.make_id("CZ", "PR", "") == "CZ-B-PR-000"


class TestMapRow:
    def test_basic_mapping(self):
        row = {
            "Firma": "Test Co s.r.o.",
            "Region": "Hlavní město Praha",
            "Miasto": "Praha",
            "Adres": "Test 1, Praha",
            "Numer Rejestrowy": "ARES IČO 25775634",
            "NIP / VAT": "CZ25775634",
            "WWW": "https://test.cz",
            "Email": "info@test.cz; biuro@test.cz",
            "Telefon": "+420 272 774 153",
            "Decydent": "Jan Kowalski",
            "Stanowisko": "CEO",
            "Relacja": "Wyłączny Importer Powermatic ČR",
            "Segment": "S1 — Nabijarki RYO/MYO & Gilze",
            "Produkty i Marki": "Powermatic II+ | Gilze",
            "Skala": "Bardzo duży",
            "Rank": "5",
        }
        out = mi.map_row(row, "CZ")
        assert out["nazwa_firmy"] == "Test Co s.r.o."
        assert out["region_kod"] == "PR"
        assert out["kraj"] == "CZ"
        assert out["id_unikalne"] == "CZ-B-PR-005"
        assert out["rejestr_id"] == "ARES IČO 25775634"
        assert out["nip_vat"] == "25775634"
        assert out["email"] == "info@test.cz"  # first of multi
        assert out["tier"] == "wyłączność"  # substring match
        assert out["kategoria"] == "B1"

    def test_substring_tier_match(self):
        """Relacja with 'Importer' anywhere should match 'wyłączność'."""
        row = {
            "Firma": "X",
            "Relacja": "Importer Ogólnokrajowy & Sieć B2B",
            "Segment": "S2 — Hurtownia Tytoniowa / FMCG",
            "Rank": "1",
            "Region": "",
            "Miasto": "Praha",
            "Adres": "",
            "Numer Rejestrowy": "",
            "NIP / VAT": "",
            "WWW": "",
            "Email": "",
            "Telefon": "",
            "Decydent": "",
            "Stanowisko": "",
            "Produkty i Marki": "",
            "Skala": "",
        }
        out = mi.map_row(row, "CZ")
        assert out["tier"] == "wyłączność"

    def test_unknown_tier_fallback(self):
        row = {
            "Firma": "X",
            "Relacja": "Something completely new",
            "Segment": "S1 — Nabijarki RYO/MYO & Gilze",
            "Rank": "1",
            "Region": "",
            "Miasto": "X",
            "Adres": "",
            "Numer Rejestrowy": "",
            "NIP / VAT": "",
            "WWW": "",
            "Email": "",
            "Telefon": "",
            "Decydent": "",
            "Stanowisko": "",
            "Produkty i Marki": "",
            "Skala": "",
        }
        out = mi.map_row(row, "CZ")
        assert out["tier"] == "do ustalenia"

    def test_notatki_consolidates_extras(self):
        row = {
            "Firma": "X",
            "Region": "",
            "Miasto": "X",
            "Adres": "",
            "Numer Rejestrowy": "",
            "NIP / VAT": "",
            "WWW": "",
            "Email": "",
            "Telefon": "",
            "Decydent": "",
            "Stanowisko": "",
            "Relacja": "",
            "Segment": "",
            "Produkty i Marki": "",
            "Skala": "",
            "Uzasadnienie Potencjału": "Test rationale",
            "Uwagi": "Some note",
            "Następny Krok": "Send email",
            "Oferta Powermatic": "Powermatic II+",
            "Ruch WWW": "10k/mc",
            "Score": "95",
            "Rank": "1",
        }
        out = mi.map_row(row, "CZ")
        assert "Uzasadnienie: Test rationale" in out["notatki"]
        assert "Uwagi: Some note" in out["notatki"]
        assert "Następny krok: Send email" in out["notatki"]
        assert "Oferta Powermatic: Powermatic II+" in out["notatki"]
        assert "Ruch WWW: 10k/mc" in out["notatki"]
        assert "Score Marcela: 95" in out["notatki"]

    def test_skip_hallucination(self):
        row = {
            "Firma": "Fake s.r.o.",
            "Region": "",
            "Miasto": "Praha",
            "Adres": "Průmyslová 12",
            "Numer Rejestrowy": "5678950",  # 7 digits
            "NIP / VAT": "CZ5678950",
            "WWW": "",
            "Email": "",
            "Telefon": "",
            "Decydent": "",
            "Stanowisko": "",
            "Relacja": "Hurtownia",
            "Segment": "S2 — Hurtownia Tytoniowa / FMCG",
            "Produkty i Marki": "",
            "Skala": "",
            "Rank": "1",
            "_verdict": "❌ HALUCYNACJA",
        }
        assert mi.map_row(row, "CZ", skip_hallucinations=True) is None
        # Without skip, it's still mapped
        out = mi.map_row(row, "CZ", skip_hallucinations=False)
        assert out is not None
