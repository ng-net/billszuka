"""Tests for tools/validate_intake.py — pattern extraction + verdict logic."""
from __future__ import annotations

import sys
sys.path.insert(0, "tools")

import validate_intake as vi


class TestExtractIco:
    """extract_ico() should pull 8-digit IČO from various formats."""

    def test_plain_8_digits(self):
        assert vi.extract_ico("25775634") == "25775634"

    def test_with_prefix(self):
        assert vi.extract_ico("IČO: 25775634") == "25775634"
        assert vi.extract_ico("ARES IČO 25775634") == "25775634"
        assert vi.extract_ico("IČO 25775634") == "25775634"

    def test_7_digits_returns_none(self):
        """7-digit value is not a valid IČO — should NOT match (return None)."""
        assert vi.extract_ico("5678950") is None

    def test_with_other_text(self):
        assert vi.extract_ico("  ARES IČO  25221981  ") == "25221981"

    def test_empty(self):
        assert vi.extract_ico("") is None
        assert vi.extract_ico(None) is None


class TestExtractRegistrikood:
    def test_plain_8_digits(self):
        assert vi.extract_registrikood("11370720") == "11370720"

    def test_with_prefix(self):
        assert vi.extract_registrikood("Registrikood 11370720") == "11370720"
        assert vi.extract_registrikood("e-Äriregister 11931003") == "11931003"


class TestExtractKodas:
    def test_9_digits(self):
        assert vi.extract_kodas("110443493") == "110443493"

    def test_7_digits(self):
        assert vi.extract_kodas("1234567") == "1234567"

    def test_with_label(self):
        assert vi.extract_kodas("Įmonės kodas: 110443493") == "110443493"


class TestExtractVat:
    def test_cz_dic(self):
        assert vi.extract_vat("CZ25775634") == "25775634"

    def test_ee_kmkr(self):
        assert vi.extract_vat("EE101376895") == "101376895"

    def test_lt_pvm(self):
        assert vi.extract_vat("LT100002442812") == "100002442812"

    def test_bare_digits(self):
        assert vi.extract_vat("25775634") == "25775634"


class TestIsGenericAddress:
    def test_prumyslova_is_generic(self):
        is_gen, reason = vi.is_generic_address("Průmyslová 10, Praha", "CZ")
        assert is_gen is True
        assert "generic" in reason.lower()

    def test_specific_address_not_generic(self):
        is_gen, _ = vi.is_generic_address("U Plynárny 412/101, Praha 10", "CZ")
        assert is_gen is False

    def test_empty_address(self):
        is_gen, _ = vi.is_generic_address("", "CZ")
        assert is_gen is False


class TestIsValidPhone:
    def test_cz_format_ok(self):
        assert vi.is_valid_phone("+420 272 774 153", "CZ") is True
        assert vi.is_valid_phone("+420 272774153", "CZ") is True

    def test_ee_format_ok(self):
        assert vi.is_valid_phone("+372 622 6399", "EE") is True
        assert vi.is_valid_phone("+372 60 70 800", "EE") is True  # 2 spaces
        assert vi.is_valid_phone("+372 6 226 399", "EE") is True

    def test_lt_format_ok(self):
        assert vi.is_valid_phone("+370 5 2109555", "LT") is True
        assert vi.is_valid_phone("+370 37 401111", "LT") is True  # 9 digits

    def test_wrong_prefix(self):
        assert vi.is_valid_phone("+48 123 456 789", "CZ") is False
        assert vi.is_valid_phone("+370 5 2109555", "EE") is False

    def test_too_short(self):
        assert vi.is_valid_phone("+420 12 34", "CZ") is False


class TestIsValidEmail:
    def test_simple_email(self):
        assert vi.is_valid_email("info@example.com") is True

    def test_multi_recipient(self):
        assert vi.is_valid_email("m.svoboda@peal.cz; b2b@peal.cz") is True
        assert vi.is_valid_email("a@x.com, b@y.com") is True

    def test_placeholder_only(self):
        """All recipients are just the local part — fabrication."""
        assert vi.is_valid_email("info@") is False
        assert vi.is_valid_email("kontakt@") is False

    def test_mixed_one_real_one_placeholder(self):
        """If at least one is real, the whole string is valid."""
        assert vi.is_valid_email("info@; real@company.com") is True

    def test_empty_or_broken(self):
        assert vi.is_valid_email("") is False
        assert vi.is_valid_email("not-an-email") is False
        assert vi.is_valid_email("@nodomain") is False
