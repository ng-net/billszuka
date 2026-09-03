"""Tests for tools/normalize_kolumny.py — targeted column fixes."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, "tools")

import normalize_kolumny as nk


# ---------------------------------------------------------------------------
# Eligibility heuristics
# ---------------------------------------------------------------------------

class TestIsEligibleFixA:
    def test_bills_pl_junk(self):
        row = {"kanal_sprzedaży": "bills.pl"}
        assert nk.is_eligible_fix_a(row)

    def test_intertabac_junk(self):
        row = {"kanal_sprzedaży": "Intertabac wystawca"}
        assert nk.is_eligible_fix_a(row)

    def test_brak_junk(self):
        row = {"kanal_sprzedaży": "brak"}
        assert nk.is_eligible_fix_a(row)

    def test_empty_not_eligible(self):
        row = {"kanal_sprzedaży": ""}
        assert not nk.is_eligible_fix_a(row)

    def test_legitimate_channel_not_eligible(self):
        row = {"kanal_sprzedaży": "B2B hurtownia + sieć kiosków"}
        assert not nk.is_eligible_fix_a(row)

    def test_legitimate_strict_not_eligible(self):
        row = {"kanal_sprzedaży": "B2B only"}
        assert not nk.is_eligible_fix_a(row)


class TestIsEligibleFixB:
    def test_digit_3_with_empty_powinowactwo(self):
        row = {"kanal_sprzedaży": "3", "powinowactwo_nabijarki": ""}
        assert nk.is_eligible_fix_b(row)

    def test_digit_5_with_empty_powinowactwo(self):
        row = {"kanal_sprzedaży": "5", "powinowactwo_nabijarki": ""}
        assert nk.is_eligible_fix_b(row)

    def test_digit_with_filled_powinowactwo_not_eligible(self):
        # If col 26 already has a value, the digit in col 25 might be intentional
        # (e.g. code "5" meaning something). Don't shift.
        row = {"kanal_sprzedaży": "3", "powinowactwo_nabijarki": "4"}
        assert not nk.is_eligible_fix_b(row)

    def test_non_digit_not_eligible(self):
        row = {"kanal_sprzedaży": "B2B only", "powinowactwo_nabijarki": ""}
        assert not nk.is_eligible_fix_b(row)

    def test_digit_6_not_eligible(self):
        # 6 is outside the 1-5 powinowactwo range
        row = {"kanal_sprzedaży": "6", "powinowactwo_nabijarki": ""}
        assert not nk.is_eligible_fix_b(row)

    def test_empty_not_eligible(self):
        row = {"kanal_sprzedaży": "", "powinowactwo_nabijarki": ""}
        assert not nk.is_eligible_fix_b(row)


# ---------------------------------------------------------------------------
# End-to-end apply_fixes on PL files
# ---------------------------------------------------------------------------

class TestApplyFixesOnPL:
    def test_pl_a_clears_bills_pl(self, tmp_path):
        # Build a minimal PL catalog-A with the bills.pl junk
        f = tmp_path / "catalog-A-PL.csv"
        f.write_text(
            "related_to,rok_zalozenia,id,kategoria,nazwa,kraj,miasto,"
            "adres,nip_vat,rejestr_id,www,kanal_zamiennik,email,telefon,linkedin,"
            "facebook,instagram,tiktok,tier,marki_nabijarki,marka_wlasna_oem,"
            "sourcing,wolumen,confidence_wolumen,kanal_sprzedaży,"
            "powinowactwo_nabijarki,cross_sell_potential,decydent,stanowisko,"
            "email_decydent,zrodlo_danych,data_weryfikacji,flagi,notatki,rynek_skala\n"
            ",2023,PL-A-999,A1,Test Firma,PL,Warsaw,ul. X 1,PL1234567890,KRS 0000123456,"
            "https://example.com,brak,test@example.com,+48 22 000 00 00,,,,,wyłączność,"
            "PowerMatic,nie,Polska,duży,Jest NIP,bills.pl,,,właściciel/CEO,,KRS API,2026-08-25,"
            "✅ FROZEN,Test,duży\n",
            encoding="utf-8"
        )
        # Re-construct absolute path under DATA structure
        # apply_fixes only acts on /Polska/ paths, so use a real-path-like string
        real_path = tmp_path / "Polska" / "catalog-A-PL.csv"
        real_path.parent.mkdir(parents=True, exist_ok=True)
        f.rename(real_path)

        # The path-string check is "/Polska/" in str(path) — that matches
        actions = nk.apply_fixes(real_path)
        assert len(actions) == 1
        assert "cleared kanal_sprzedaży='bills.pl'" in actions[0]
        # Verify file was modified
        content = real_path.read_text(encoding="utf-8")
        # Row should have empty kanal_sprzedaży in the position where 'bills.pl' was
        # (35 columns; kanal_sprzedaży is column index 24)
        # Easier: check that 'bills.pl' is no longer present
        assert "bills.pl" not in content

    def test_pl_b_shifts_powinowactwo_digit(self, tmp_path):
        real_path = tmp_path / "Polska" / "catalog-B-PL.csv"
        real_path.parent.mkdir(parents=True, exist_ok=True)
        real_path.write_text(
            "related_to,rok_zalozenia,id,kategoria,nazwa,kraj,miasto,"
            "adres,nip_vat,rejestr_id,www,kanal_zamiennik,email,telefon,linkedin,"
            "facebook,instagram,tiktok,tier,marki_nabijarki,marka_wlasna_oem,"
            "sourcing,wolumen,confidence_wolumen,kanal_sprzedaży,"
            "powinowactwo_nabijarki,cross_sell_potential,decydent,stanowisko,"
            "email_decydent,zrodlo_danych,data_weryfikacji,flagi,notatki,rynek_skala\n"
            ",2005,PL-B-999,B8,Test Firma,PL,Warsaw,ul. X 1,PL1234567890,KRS 0000123456,"
            "https://example.com,brak,test@example.com,+48 22 000 00 00,,,,,hurtownik,"
            ",,Europa,duży,Jest NIP,3,,,właściciel,owner,,KRS API,2026-08-25,✅ FROZEN,Test,duży\n",
            encoding="utf-8"
        )
        actions = nk.apply_fixes(real_path)
        assert len(actions) == 1
        assert "shifted '3' col 25 -> col 26" in actions[0]

        header, rows = nk.load_csv(real_path)
        row = rows[0]
        assert row["kanal_sprzedaży"] == ""
        assert row["powinowactwo_nabijarki"] == "3"

    def test_idempotent(self, tmp_path):
        """Running apply_fixes twice yields no further changes."""
        real_path = tmp_path / "Polska" / "catalog-B-PL.csv"
        real_path.parent.mkdir(parents=True, exist_ok=True)
        # Exactly 35 fields per row. Field-position comments are 1-indexed.
        #   col 1 = related_to (empty)
        #   col 2 = rok_zalozenia (2005)
        #   cols 3-10 = id/kategoria/nazwa/kraj/miasto/adres/nip/rejestr
        #   col 11 = www (empty)
        #   col 12 = kanal_zamiennik (brak)
        #   col 13 = email
        #   col 14 = telefon (empty)
        #   cols 15-18 = linkedin/facebook/instagram/tiktok (4 empty)
        #   col 19 = tier (hurtownik)
        #   cols 20-21 = marki/oem (2 empty)
        #   col 22 = sourcing (Europa)
        #   col 23 = wolumen (duży)
        #   col 24 = confidence (Jest NIP)
        #   col 25 = kanal (`3` — target for fix B)
        #   cols 26-27 = pow/cross_sell (2 empty)
        #   col 28 = decydent (Owner)
        #   col 29 = stanowisko (owner)
        #   col 30 = email_decydent (empty)
        #   col 31 = zrodlo_danych (KRS API)
        #   col 32 = data_weryfikacji (2026-08-25)
        #   col 33 = flagi (empty)
        #   col 34 = notatki (Test)
        #   col 35 = rynke_skala (duży)
        real_path.write_text(
            "related_to,rok_zalozenia,id,kategoria,nazwa,kraj,miasto,"
            "adres,nip_vat,rejestr_id,www,kanal_zamiennik,email,telefon,linkedin,"
            "facebook,instagram,tiktok,tier,marki_nabijarki,marka_wlasna_oem,"
            "sourcing,wolumen,confidence_wolumen,kanal_sprzedaży,"
            "powinowactwo_nabijarki,cross_sell_potential,decydent,stanowisko,"
            "email_decydent,zrodlo_danych,data_weryfikacji,flagi,notatki,rynek_skala\n"
            # 1 empty, 2-13 values, 14-18 empty (5 commas), 19=hurtownik,
            # 20-21 empty (2 commas), 22=Europa, 23=duży, 24=Jest NIP, 25=3,
            # 26-27 empty (2 commas), 28=Owner, 29=owner, 30 empty (1 comma),
            # 31=KRS API, 32=2026-08-25, 33 empty (1 comma), 34=Test, 35=duży
            ",2005,PL-B-001,B8,Test,PL,City,addr,PL1234567890,KRS,,brak,test@x.com,,,,,"
            "hurtownik,,,Europa,duży,Jest NIP,3,,,Owner,owner,,KRS API,2026-08-25,,Test,duży\n",
            encoding="utf-8"
        )
        actions1 = nk.apply_fixes(real_path)
        assert len(actions1) == 1
        # Second pass: the value 3 has moved to col 26 and col 25 is empty.
        # is_eligible_fix_b now returns False (col 25 is empty, not a digit),
        # so no further changes.
        actions2 = nk.apply_fixes(real_path)
        assert actions2 == []

    def test_non_pl_files_untouched(self, tmp_path):
        """CZs / ROs etc. are never modified, even if they have similar values."""
        real_path = tmp_path / "Czechy" / "catalog-B-CZ.csv"
        real_path.parent.mkdir(parents=True, exist_ok=True)
        real_path.write_text(
            "related_to,rok_zalozenia,id,kategoria,nazwa,kraj,miasto,"
            "adres,nip_vat,rejestr_id,www,kanal_zamiennik,email,telefon,linkedin,"
            "facebook,instagram,tiktok,tier,marki_nabijarki,marka_wlasna_oem,"
            "sourcing,wolumen,confidence_wolumen,kanal_sprzedaży,"
            "powinowactwo_nabijarki,cross_sell_potential,decydent,stanowisko,"
            "email_decydent,zrodlo_danych,data_weryfikacji,flagi,notatki,rynek_skala\n"
            ",2001,CZ-B-001,B8,Test,CZ,Praha,addr,CZ12345678,IČO,,info@x.cz,,,"
            ",,,hurtownik,,wyroby,,duży,Jest NIP,3,,,Director,CEO,,ARES,2026-08-25,,Test,duży\n",
            encoding="utf-8"
        )
        # Even though CZ-B-001 has "3" in kanal_sprzedaży, the fix is PL-only.
        actions = nk.apply_fixes(real_path)
        assert actions == []


# ---------------------------------------------------------------------------
# FixC: A row has B-only fields filled (powinowactwo, cross_sell)
# ---------------------------------------------------------------------------

class TestIsEligibleFixC:
    def test_a_row_powinowactwo_filled(self):
        row = {"powinowactwo_nabijarki": "3", "cross_sell_potential": ""}
        assert nk.is_eligible_fix_c(row, "A") == ["powinowactwo_nabijarki"]

    def test_a_row_cross_sell_filled(self):
        row = {"powinowactwo_nabijarki": "", "cross_sell_potential": "wysoki"}
        assert nk.is_eligible_fix_c(row, "A") == ["cross_sell_potential"]

    def test_a_row_both_filled(self):
        row = {"powinowactwo_nabijarki": "3", "cross_sell_potential": "wysoki"}
        cols = nk.is_eligible_fix_c(row, "A")
        assert "powinowactwo_nabijarki" in cols
        assert "cross_sell_potential" in cols

    def test_a_row_neutral_value_not_eligible(self):
        # "n/a" / "nie" / "" treated as no contamination
        row = {"powinowactwo_nabijarki": "n/a", "cross_sell_potential": "nie"}
        assert nk.is_eligible_fix_c(row, "A") == []

    def test_b_row_never_eligible(self):
        # FixC is A-only. B row with filled values should NOT trigger.
        row = {"powinowactwo_nabijarki": "3", "cross_sell_potential": "wysoki"}
        assert nk.is_eligible_fix_c(row, "B") == []
        assert nk.is_eligible_fix_c(row, None) == []


# ---------------------------------------------------------------------------
# FixD: B row has A-only fields filled (marki_nabijarki, marka_wlasna_oem)
# ---------------------------------------------------------------------------

class TestIsEligibleFixD:
    def test_b_row_marki_filled(self):
        row = {"marki_nabijarki": "PowerMatic | Rollo", "marka_wlasna_oem": ""}
        assert nk.is_eligible_fix_d(row, "B") == ["marki_nabijarki"]

    def test_b_row_oem_filled(self):
        row = {"marki_nabijarki": "", "marka_wlasna_oem": "Cartel / Rollo"}
        assert nk.is_eligible_fix_d(row, "B") == ["marka_wlasna_oem"]

    def test_b_row_neutral_value_not_eligible(self):
        row = {"marki_nabijarki": "nie", "marka_wlasna_oem": "n/a"}
        assert nk.is_eligible_fix_d(row, "B") == []

    def test_a_row_never_eligible(self):
        row = {"marki_nabijarki": "PowerMatic", "marka_wlasna_oem": "OEM Brand"}
        assert nk.is_eligible_fix_d(row, "A") == []
        assert nk.is_eligible_fix_d(row, None) == []


class TestDetectCatalogType:
    def test_a_from_filename(self):
        from pathlib import Path
        assert nk.detect_catalog_type(Path("data/Polska/catalog-A-PL.csv")) == "A"

    def test_b_from_filename(self):
        from pathlib import Path
        assert nk.detect_catalog_type(Path("data/Polska/catalog-B-PL.csv")) == "B"

    def test_unknown(self):
        from pathlib import Path
        assert nk.detect_catalog_type(Path("data/Polska/extra-leads-PL.csv")) is None


class TestApplyFixesOnPLABCrossContamination:
    def test_a_row_clears_b_only_fields(self, tmp_path):
        real_path = tmp_path / "Polska" / "catalog-A-PL.csv"
        real_path.parent.mkdir(parents=True, exist_ok=True)
        real_path.write_text(
            "related_to,rok_zalozenia,id,kategoria,nazwa,kraj,miasto,"
            "adres,nip_vat,rejestr_id,www,kanal_zamiennik,email,telefon,linkedin,"
            "facebook,instagram,tiktok,tier,marki_nabijarki,marka_wlasna_oem,"
            "sourcing,wolumen,confidence_wolumen,kanal_sprzedaży,"
            "powinowactwo_nabijarki,cross_sell_potential,decydent,stanowisko,"
            "email_decydent,zrodlo_danych,data_weryfikacji,flagi,notatki,rynek_skala\n"
            # 1 empty, 2-13 values, 14-18 empty (5 commas), 19=hurtownik,
            # 20-21 empty (2 commas), 22=Europa, 23=duży, 24=Jest NIP, 25=B2B only,
            # 26-27 empty (2 commas, B-only fields to be cleared by FixC),
            # 28=wysoki (decydent), 29=Owner (stanowisko), 30=owner (email_decydent),
            # 31 empty (1 comma), 32=KRS API (zrodlo_danych), 33=2026-08-25 (data_weryfikacji),
            # 34=✅ FROZEN (flagi), 35=Test (rynek_skala)  — 35 fields, no trailing `,duży`
            ",2023,PL-A-999,A1,Test,PL,City,addr,PL1234567890,KRS,,brak,test@x.com,,,,,"
            "hurtownik,,Europa,duży,Jest NIP,B2B only,,wysoki,Owner,owner,,KRS API,"
            "2026-08-25,✅ FROZEN,Test\n",
            encoding="utf-8"
        )
        actions = nk.apply_fixes(real_path)
        assert any("cleared powinowactwo_nabijarki" in a for a in actions)
        assert any("cleared cross_sell_potential" in a for a in actions)

    def test_b_row_clears_a_only_fields(self, tmp_path):
        real_path = tmp_path / "Polska" / "catalog-B-PL.csv"
        real_path.parent.mkdir(parents=True, exist_ok=True)
        real_path.write_text(
            "related_to,rok_zalozenia,id,kategoria,nazwa,kraj,miasto,"
            "adres,nip_vat,rejestr_id,www,kanal_zamiennik,email,telefon,linkedin,"
            "facebook,instagram,tiktok,tier,marki_nabijarki,marka_wlasna_oem,"
            "sourcing,wolumen,confidence_wolumen,kanal_sprzedaży,"
            "powinowactwo_nabijarki,cross_sell_potential,decydent,stanowisko,"
            "email_decydent,zrodlo_danych,data_weryfikacji,flagi,notatki,rynek_skala\n"
            # Same field layout as the A test (above). marki_nabijarki and
            # marka_wlasna_oem (cols 20, 21) are A-only fields that FixD
            # will clear on B rows.
            ",2005,PL-B-999,B8,Test,PL,City,addr,PL1234567890,KRS,,brak,test@x.com,,,,,"
            "hurtownik,,Europa,duży,Jest NIP,B2B only,,wysoki,Owner,owner,,KRS API,"
            "2026-08-25,✅ FROZEN,Test\n",
            encoding="utf-8"
        )
        actions = nk.apply_fixes(real_path)
        assert any("cleared marki_nabijarki" in a for a in actions)
        assert any("cleared marka_wlasna_oem" in a for a in actions)


# ---------------------------------------------------------------------------
# Backup behaviour
# ---------------------------------------------------------------------------

class TestMakeBackup:
    def test_copies_modified_files_only(self, tmp_path, monkeypatch):
        # build files under a temporary DATA tree isolated in tmp_path,
        # avoiding any risk of mutating or unlinking live catalog files.
        test_data = tmp_path / "data"
        test_data.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(nk, "DATA", test_data)

        poland = test_data / "Polska"
        poland.mkdir(parents=True, exist_ok=True)
        f1 = poland / "catalog-A-PL.csv"
        f1.write_text("header\na,b,c\n", encoding="utf-8")
        czech = test_data / "Czechy"
        czech.mkdir(parents=True, exist_ok=True)
        f2 = czech / "catalog-B-CZ.csv"
        f2.write_text("header\nx,y,z\n", encoding="utf-8")

        backup_dir = test_data / ".test-backup-tmp"
        nk.make_backup([f1, f2], backup_dir)

        assert (backup_dir / "Polska" / "catalog-A-PL.csv").exists()
        assert (backup_dir / "Czechy" / "catalog-B-CZ.csv").exists()
        # Original dirs not affected
        assert f1.read_text(encoding="utf-8") == "header\na,b,c\n"
        assert f2.read_text(encoding="utf-8") == "header\nx,y,z\n"

