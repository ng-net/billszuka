"""Tests for tools/map_intake.py — 35 column mapping + tier/kategoria logic."""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import map_intake as mi


class TestNormalizeEmail(unittest.TestCase):
    def test_single(self):
        self.assertEqual(mi.normalize_email("info@example.com"), "info@example.com")

    def test_multi_recipient_takes_first(self):
        self.assertEqual(mi.normalize_email("a@x.com; b@y.com"), "a@x.com")
        self.assertEqual(mi.normalize_email("ceo@firm.cz, biuro@firm.cz"), "ceo@firm.cz")

    def test_empty(self):
        self.assertEqual(mi.normalize_email(""), "")
        self.assertEqual(mi.normalize_email(None), "")

    def test_invalid(self):
        self.assertEqual(mi.normalize_email("not-an-email"), "")


class TestNormalizePhone(unittest.TestCase):
    def test_single(self):
        self.assertEqual(mi.normalize_phone("+420 272 774 153"), "+420 272 774 153")

    def test_multi_takes_first(self):
        self.assertEqual(mi.normalize_phone("+370 620 40051; +370 600 36608"), "+370 620 40051")

    def test_pipe_separator(self):
        self.assertEqual(mi.normalize_phone("+48 22 123 | +48 22 456"), "+48 22 123")

    def test_empty(self):
        self.assertEqual(mi.normalize_phone(""), "")


class TestNormalizeRejestr(unittest.TestCase):
    def test_cz_plain(self):
        self.assertEqual(mi.normalize_rejestr("25775634", "CZ"), "ARES IČO 25775634")

    def test_cz_with_label(self):
        self.assertEqual(mi.normalize_rejestr("ARES IČO 25221981", "CZ"), "ARES IČO 25221981")

    def test_cz_invalid(self):
        self.assertEqual(mi.normalize_rejestr("5678950", "CZ"), "")  # 7 digits, not 8

    def test_ee_plain(self):
        self.assertEqual(mi.normalize_rejestr("11370720", "EE"), "e-Äriregister 11370720")

    def test_lt_plain(self):
        self.assertEqual(mi.normalize_rejestr("110443493", "LT"), "JAR 110443493")


class TestNormalizeNip(unittest.TestCase):
    def test_cz_dic(self):
        self.assertEqual(mi.normalize_nip("CZ25775634"), "25775634")

    def test_ee_kmkr(self):
        self.assertEqual(mi.normalize_nip("EE101376895"), "101376895")

    def test_lt_pvm(self):
        self.assertEqual(mi.normalize_nip("LT100002442812"), "100002442812")


class TestMakeId(unittest.TestCase):
    def test_format(self):
        self.assertEqual(mi.make_id("CZ", "B", 5), "CZ-B-005")
        self.assertEqual(mi.make_id("CZ", "B", 12), "CZ-B-012")
        self.assertEqual(mi.make_id("CZ", "B", 100), "CZ-B-100")


class TestMapRow(unittest.TestCase):
    def test_basic_mapping(self):
        row = {
            "Firma": "Test Co s.r.o.",
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
        out = mi.map_row(row, "CZ", seq_num=5)
        self.assertEqual(out["nazwa"], "Test Co s.r.o.")
        self.assertEqual(out["kraj"], "CZ")
        self.assertEqual(out["id"], "CZ-B-005")
        self.assertEqual(out["rejestr_id"], "ARES IČO 25775634")
        self.assertEqual(out["nip_vat"], "25775634")
        self.assertEqual(out["email"], "info@test.cz")
        self.assertEqual(out["tier"], "wyłączność")
        self.assertEqual(out["kategoria"], "B1")

    def test_substring_tier_match(self):
        row = {
            "Firma": "X",
            "Relacja": "Importer Ogólnokrajowy & Sieć B2B",
            "Segment": "S2 — Hurtownia Tytoniowa / FMCG",
            "Rank": "1",
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
        out = mi.map_row(row, "CZ", seq_num=1)
        self.assertEqual(out["tier"], "wyłączność")

    def test_unknown_tier_fallback(self):
        row = {
            "Firma": "X",
            "Relacja": "Something completely new",
            "Segment": "S1 — Nabijarki RYO/MYO & Gilze",
            "Rank": "1",
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
        out = mi.map_row(row, "CZ", seq_num=1)
        self.assertEqual(out["tier"], "do ustalenia")

    def test_notatki_consolidates_extras(self):
        row = {
            "Firma": "X",
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
        out = mi.map_row(row, "CZ", seq_num=1)
        self.assertIn("Uzasadnienie: Test rationale", out["notatki"])
        self.assertIn("Uwagi: Some note", out["notatki"])
        self.assertIn("Następny krok: Send email", out["notatki"])

    def test_skip_hallucination(self):
        row = {
            "Firma": "Fake s.r.o.",
            "Miasto": "Praha",
            "Adres": "Průmyslová 12",
            "Numer Rejestrowy": "5678950",
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
        self.assertIsNone(mi.map_row(row, "CZ", seq_num=1, skip_hallucinations=True))
        out = mi.map_row(row, "CZ", seq_num=1, skip_hallucinations=False)
        self.assertIsNotNone(out)


if __name__ == "__main__":
    unittest.main()
