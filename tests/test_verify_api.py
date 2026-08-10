"""
test_verify_api.py — Tests for tools/verify_api.py.

Covers:
  • normalize() — pure string function, no I/O
  • verify_pl_row() — KRS path (mocked) + CEIDG path (mocked) + edge cases
  • verify_cz_row() — ARES path (mocked) + missing-token path

Mocking strategy: monkeypatch the `krs_lookup`, `ceidg_lookup`, `ares_lookup`
module-level functions in verify_api. No real HTTP calls are made.
"""
from __future__ import annotations

import pytest

import verify_api


# ---------------------------------------------------------------------------
# normalize() — pure function, no mocking needed
# ---------------------------------------------------------------------------

class TestNormalize:
    """normalize() strips legal-form suffixes, collapses whitespace, uppercases."""

    def test_empty(self):
        assert verify_api.normalize("") == ""
        assert verify_api.normalize(None) == ""

    def test_already_normalized(self):
        assert verify_api.normalize("ACME CORP") == "ACME CORP"

    def test_lowercase_to_upper(self):
        assert verify_api.normalize("acme corp") == "ACME CORP"

    def test_strip_pl_sp_zoo(self):
        # "SP. Z O.O." should be stripped
        assert verify_api.normalize("ACME SP. Z O.O.") == "ACME"

    def test_strip_pl_full_form(self):
        s = "ACME SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ"
        assert verify_api.normalize(s) == "ACME"

    def test_strip_cz_sro(self):
        # normalize() strips ALL punctuation, not just legal-form suffixes
        # (regex `[^A-Z0-9ĄĆĘŁŃÓŚŹŻ]+` → space). Dash and comma disappear.
        assert verify_api.normalize("FORTIS-DB, SPOL. S R.O.") == "FORTIS DB"

    def test_strip_cz_as(self):
        assert verify_api.normalize("PEAL A.S.") == "PEAL"

    def test_strip_sp_jaw(self):
        assert verify_api.normalize("CASISS SP.J.") == "CASISS"

    def test_strip_fhu(self):
        assert verify_api.normalize("F.H.U. ALPIK") == "ALPIK"

    def test_collapses_whitespace(self):
        # Multiple internal spaces collapse to single
        assert verify_api.normalize("ACME    CORP") == "ACME CORP"

    def test_dash_and_comma_become_spaces(self):
        # Punctuation in firm name is replaced with a single space.
        # This is a side-effect of the regex used to strip legal forms —
        # acceptable for fuzzy matching (the "ACME" in "ACME-CORP" and
        # "ACME CORP" will still match) but worth documenting as a test.
        assert verify_api.normalize("FORTIS-DB, SPOL. S R.O.") == "FORTIS DB"
        assert verify_api.normalize("ALPIK / TRZCIŃSKI") == "ALPIK TRZCIŃSKI"


# ---------------------------------------------------------------------------
# verify_pl_row() — KRS branch (mocked)
# ---------------------------------------------------------------------------

class TestVerifyPlRowKRS:
    """Tests for the KRS code path in verify_pl_row."""

    @pytest.fixture
    def row_with_krs(self):
        return {
            "nazwa_firmy": "ACME SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
            "nip_vat": "PL1234567890",
            "rejestr_id": "KRS 0000123456",
        }

    def test_krs_match_returns_frozen(self, row_with_krs, monkeypatch):
        monkeypatch.setattr(
            verify_api, "krs_lookup",
            lambda krs: {"nazwa": "ACME SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
                         "regon": "123456789", "krs": krs},
        )
        status, reason = verify_api.verify_pl_row(row_with_krs, token="dummy")
        assert status == "FROZEN", f"expected FROZEN, got {status!r}: {reason}"
        assert "KRS live" in reason
        assert "123456789" in reason  # REGON surfaces

    def test_krs_name_mismatch_returns_doweryfikacji(self, row_with_krs, monkeypatch):
        # API returns a totally different company name
        monkeypatch.setattr(
            verify_api, "krs_lookup",
            lambda krs: {"nazwa": "RODENTOPEST POLSKA SP. Z O.O.",
                         "regon": "999999999", "krs": krs},
        )
        status, reason = verify_api.verify_pl_row(row_with_krs, token="dummy")
        assert status == "DO-WERYFIKACJI"
        assert "mismatch" in reason.lower()

    def test_krs_api_error_returns_doweryfikacji(self, row_with_krs, monkeypatch):
        monkeypatch.setattr(
            verify_api, "krs_lookup",
            lambda krs: {"error": "HTTP 503"},
        )
        status, reason = verify_api.verify_pl_row(row_with_krs, token="dummy")
        assert status == "DO-WERYFIKACJI"
        assert "503" in reason

    def test_krs_api_returns_none(self, row_with_krs, monkeypatch):
        # krs_lookup returns None on network failure
        monkeypatch.setattr(verify_api, "krs_lookup", lambda krs: None)
        status, reason = verify_api.verify_pl_row(row_with_krs, token="dummy")
        assert status == "DO-WERYFIKACJI"
        assert "brak" in reason.lower()


# ---------------------------------------------------------------------------
# verify_pl_row() — CEIDG branch (JDG, no KRS)
# ---------------------------------------------------------------------------

class TestVerifyPlRowCEIDG:
    """Tests for the CEIDG fallback path in verify_pl_row (sole proprietors)."""

    def test_ceidg_nip_match(self, monkeypatch):
        row = {
            "nazwa_firmy": "ALPIK RYSZARD TRZCIŃSKI",
            "nip_vat": "PL9551541914",
            "rejestr_id": "JDG (CEIDG)",
        }
        # CEIDG returns "imie nazwisko" not the firm name; NIP must match
        monkeypatch.setattr(
            verify_api, "ceidg_lookup",
            lambda nip, token: {"nazwa": "RYSZARD TRZCIŃSKI",
                                "nip": "9551541914", "regon": "810172286"},
        )
        status, reason = verify_api.verify_pl_row(row, token="dummy")
        assert status == "FROZEN"
        assert "CEIDG live" in reason

    def test_ceidg_nip_mismatch(self, monkeypatch):
        row = {
            "nazwa_firmy": "WRONG NAME",
            "nip_vat": "PL9551541914",
            "rejestr_id": "JDG (CEIDG)",
        }
        monkeypatch.setattr(
            verify_api, "ceidg_lookup",
            lambda nip, token: {"nazwa": "JAN KOWALSKI",
                                "nip": "9999999999", "regon": "111111111"},
        )
        status, reason = verify_api.verify_pl_row(row, token="dummy")
        assert status == "DO-WERYFIKACJI"
        assert "NIP" in reason or "nazwa" in reason.lower()

    def test_no_nip_no_krs(self):
        row = {
            "nazwa_firmy": "ORPHAN",
            "nip_vat": "",
            "rejestr_id": "",
        }
        status, reason = verify_api.verify_pl_row(row, token="dummy")
        assert status == "DO-WERYFIKACJI"
        assert "Brak" in reason


# ---------------------------------------------------------------------------
# verify_cz_row() — ARES branch
# ---------------------------------------------------------------------------

class TestVerifyCzRow:
    """Tests for verify_cz_row (Czech ARES registry)."""

    def test_ares_match(self, monkeypatch):
        row = {
            "nazwa_firmy": "FORTIS-DB, SPOL. S R.O.",
            "nip_vat": "CZ62586289",
            "rejestr_id": "ARES IČO 62586289",
        }
        monkeypatch.setattr(
            verify_api, "ares_lookup",
            lambda ico: {"nazwa": "FORTIS-DB, spol. s r.o.",
                         "ico": "62586289", "dic": "CZ62586289"},
        )
        status, reason = verify_api.verify_cz_row(row)
        assert status == "FROZEN"
        assert "ARES" in reason

    def test_ares_404(self, monkeypatch):
        row = {
            "nazwa_firmy": "GHOST LTD.",
            "nip_vat": "CZ00000000",
            "rejestr_id": "ARES IČO 00000000",
        }
        monkeypatch.setattr(
            verify_api, "ares_lookup",
            lambda ico: None,  # ARES returns nothing for unknown IČO
        )
        status, reason = verify_api.verify_cz_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "ARES" in reason or "brak" in reason.lower()

    def test_ares_name_mismatch(self, monkeypatch):
        row = {
            "nazwa_firmy": "FORTIS-DB",
            "nip_vat": "CZ62586289",
            "rejestr_id": "ARES IČO 62586289",
        }
        monkeypatch.setattr(
            verify_api, "ares_lookup",
            lambda ico: {"nazwa": "TOTALLY DIFFERENT COMPANY A.S.",
                         "ico": "62586289"},
        )
        status, reason = verify_api.verify_cz_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "mismatch" in reason.lower()

    def test_ares_geco_klempizo_returns_doweryfikacji(self, monkeypatch):
        """FABRYKAT case: IČO 60471484 is real 'GECO KLEMPIZO s.r.o.' — different
        from 'GECO, a.s.' that the CSV claims. Token Jaccard must catch this
        (substring 'in' check would NOT — see git history for the bug)."""
        row = {
            "nazwa_firmy": "GECO, A.S.",
            "nip_vat": "CZ60471484",
            "rejestr_id": "ARES IČO 60471484",
        }
        monkeypatch.setattr(
            verify_api, "ares_lookup",
            lambda ico: {"nazwa": "GECO KLEMPIZO s.r.o.", "ico": "60471484"},
        )
        status, reason = verify_api.verify_cz_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "mismatch" in reason.lower()
        assert "jaccard" in reason.lower()

    def test_ares_peal_real_estate_returns_doweryfikacji(self, monkeypatch):
        """FABRYKAT case: IČO 07752211 is real 'PEAL Real Estate s.r.o.' —
        different from 'PEAL a.s.' that the CSV claims. Real PEAL a.s. is
        IČO 25775634. Substring 'in' would let 'PEAL' match 'PEAL Real Estate'."""
        row = {
            "nazwa_firmy": "PEAL A.S.",
            "nip_vat": "CZ07752211",
            "rejestr_id": "ARES IČO 07752211",
        }
        monkeypatch.setattr(
            verify_api, "ares_lookup",
            lambda ico: {"nazwa": "PEAL Real Estate s.r.o.", "ico": "07752211"},
        )
        status, reason = verify_api.verify_cz_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "mismatch" in reason.lower()
        assert "jaccard" in reason.lower()

    def test_ares_legal_form_only_token_does_not_inflate(self, monkeypatch):
        """Sanity: legal-form tokens (SP, AS, SRO...) must not inflate the
        Jaccard score. Otherwise 'PEAL' vs 'PEAL Real Estate' could pass
        if 'PEAL' shares token with another entity also having 'A.S.'."""
        row = {
            "nazwa_firmy": "ACME A.S.",
            "nip_vat": "CZ12345678",
            "rejestr_id": "ARES IČO 12345678",
        }
        monkeypatch.setattr(
            verify_api, "ares_lookup",
            lambda ico: {"nazwa": "TOTALLY DIFFERENT COMPANY A.S.", "ico": "12345678"},
        )
        status, _ = verify_api.verify_cz_row(row)
        assert status == "DO-WERYFIKACJI"


# ---------------------------------------------------------------------------
# name_similarity() — token Jaccard unit tests
# ---------------------------------------------------------------------------

class TestNameSimilarity:
    """Token Jaccard ≥ 0.8 — catches FABRYKAT pattern (shared prefix only)."""

    def test_exact_match(self):
        ok, score, _ = verify_api.name_similarity("ACME A.S.", "ACME a.s.")
        assert ok is True
        assert score == 1.0

    def test_substring_match_fails_peal(self):
        """PEAL vs PEAL Real Estate — substring check would pass (PEAL in PEAL Real Estate).
        Jaccard should fail: only 1 of 3 tokens shared (1/3 = 0.33)."""
        ok, score, _ = verify_api.name_similarity("PEAL a.s.", "PEAL Real Estate s.r.o.")
        assert ok is False
        assert score < 0.5

    def test_substring_match_fails_geco(self):
        """GECO vs GECO KLEMPIZO — Jaccard 1/2 = 0.5, fails 0.8 threshold."""
        ok, score, _ = verify_api.name_similarity("GECO, a.s.", "GECO KLEMPIZO s.r.o.")
        assert ok is False
        assert score == 0.5

    def test_legal_forms_stripped(self):
        """Legal forms (SP ZOO, AS, SRO) should be stripped before comparison."""
        ok, score, _ = verify_api.name_similarity(
            "FORTIS-DB, SPOL. S R.O.", "FORTIS-DB, spol. s r.o."
        )
        assert ok is True
        assert score == 1.0

    def test_empty_name(self):
        ok, score, _ = verify_api.name_similarity("", "ANYTHING")
        assert ok is False
        assert score == 0.0

    def test_no_overlap(self):
        ok, score, _ = verify_api.name_similarity("ACME", "FOO BAR BAZ")
        assert ok is False
        assert score == 0.0

    def test_threshold_boundary_above(self):
        """Jaccard = 5/6 = 0.83 → above 0.8 → match."""
        ok, score, _ = verify_api.name_similarity(
            "A B C D E", "A B C D E F"  # 5 of 6 shared
        )
        assert ok is True
        assert score > 0.8

    def test_threshold_boundary_below(self):
        """Jaccard = 2/3 = 0.67 → below 0.8 → no match."""
        ok, score, _ = verify_api.name_similarity(
            "ACME POLSKA", "ACME OTHER STUFF"  # 1 of 3 shared
        )
        assert ok is False
        assert score < 0.8


# ---------------------------------------------------------------------------
# EU_MEMBER_STATES constant
# ---------------------------------------------------------------------------

class TestEUMemberStates:
    """The 27 EU member states should be in the set; non-EU like MD should not."""

    def test_count_is_27(self):
        # EU has had 27 members since Croatia joined in 2013.
        assert len(verify_api.EU_MEMBER_STATES) == 27

    def test_billszuka_eu_countries_in_set(self):
        # All BILLSzuka countries except MD (Moldova) are EU members
        for c in ("PL", "CZ", "SK", "LT", "LV", "EE", "BG", "FR", "HR", "RO", "SI"):
            assert c in verify_api.EU_MEMBER_STATES, f"{c} should be EU member"

    def test_non_eu_countries_not_in_set(self):
        for c in ("MD", "UA", "BY", "RS", "NO", "CH", "UK"):
            assert c not in verify_api.EU_MEMBER_STATES, f"{c} should NOT be EU member"

    def test_brexit_uk_excluded(self):
        # Common mistake: including UK after Brexit (left 2020-01-31)
        assert "UK" not in verify_api.EU_MEMBER_STATES

    def test_pending_api_constant_value(self):
        # The PENDING_API status must be a string distinct from
        # FROZEN / DO-WERYFIKACJI so update_row_status() can branch on it.
        assert verify_api.PENDING_API == "PENDING_API"
        assert verify_api.PENDING_API != "FROZEN"
        assert verify_api.PENDING_API != "DO-WERYFIKACJI"


# ---------------------------------------------------------------------------
# verify_vies_row() — VIES branch (mocked)
# ---------------------------------------------------------------------------

class TestVerifyViesRow:
    """Tests for verify_vies_row covering the new PENDING_API status path."""

    def test_valid_vat_returns_frozen(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "vies_lookup",
            lambda vat: {"valid": True, "name": "ACME SRO", "vat_number": "12345678",
                         "country_code": "SK"},
        )
        row = {"nazwa_firmy": "ACME", "nip_vat": "SK12345678", "rejestr_id": ""}
        status, reason = verify_api.verify_vies_row(row)
        assert status == "FROZEN"
        assert "VIES live" in reason
        assert "SK12345678" in reason

    def test_invalid_vat_returns_doweryfikacji(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "vies_lookup",
            lambda vat: {"valid": False, "error": "VAT ID nieaktywny w VIES",
                         "vat_number": "00000000", "country_code": "SK"},
        )
        row = {"nazwa_firmy": "GHOST", "nip_vat": "SK00000000", "rejestr_id": ""}
        status, reason = verify_api.verify_vies_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "nieaktywny" in reason.lower() or "vies" in reason.lower()

    def test_malformed_vat_returns_doweryfikacji(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "vies_lookup",
            lambda vat: {"valid": False, "error": "VIES: Niepoprawny format VAT"},
        )
        row = {"nazwa_firmy": "BROKEN", "nip_vat": "XX999", "rejestr_id": ""}
        status, reason = verify_api.verify_vies_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "Niepoprawny format" in reason or "format" in reason.lower()

    def test_network_error_returns_pending_api(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "vies_lookup",
            lambda vat: {"valid": False, "error": "VIES connection error: timeout"},
        )
        row = {"nazwa_firmy": "ACME", "nip_vat": "SK12345678", "rejestr_id": ""}
        status, reason = verify_api.verify_vies_row(row)
        # Network errors are NOT verification failures — they should
        # surface as PENDING_API so they're not confused with real misses.
        assert status == verify_api.PENDING_API
        assert "VIES" in reason

    def test_no_vat_returns_pending_api(self, monkeypatch):
        # Don't even call VIES if there's nothing to look up
        def fail(vat):
            raise AssertionError("vies_lookup should not be called")
        monkeypatch.setattr(verify_api, "vies_lookup", fail)
        row = {"nazwa_firmy": "EMPTY", "nip_vat": "", "rejestr_id": ""}
        status, reason = verify_api.verify_vies_row(row)
        assert status == verify_api.PENDING_API

    def test_placeholder_vat_returns_pending_api(self, monkeypatch):
        def fail(vat):
            raise AssertionError("vies_lookup should not be called")
        monkeypatch.setattr(verify_api, "vies_lookup", fail)
        for placeholder in ("do weryfikacji", "brak", "brak danych", "do ustalenia"):
            row = {"nazwa_firmy": "X", "nip_vat": placeholder, "rejestr_id": ""}
            status, _ = verify_api.verify_vies_row(row)
            assert status == verify_api.PENDING_API, f"placeholder {placeholder!r} should yield PENDING_API"

    def test_module_unavailable_returns_pending_api(self, monkeypatch):
        # Simulate ImportError fallback path: vies_lookup is None
        monkeypatch.setattr(verify_api, "vies_lookup", None)
        row = {"nazwa_firmy": "X", "nip_vat": "SK12345", "rejestr_id": ""}
        status, reason = verify_api.verify_vies_row(row)
        assert status == verify_api.PENDING_API
        assert "niedostępny" in reason.lower() or "niedost" in reason.lower()

    def test_vies_returns_none(self, monkeypatch):
        monkeypatch.setattr(verify_api, "vies_lookup", lambda vat: None)
        row = {"nazwa_firmy": "X", "nip_vat": "SK12345", "rejestr_id": ""}
        status, reason = verify_api.verify_vies_row(row)
        assert status == verify_api.PENDING_API


# ---------------------------------------------------------------------------
# verify_fr_row() — French government registry branch (mocked)
# ---------------------------------------------------------------------------

class TestVerifyFrRow:
    """Tests for verify_fr_row covering the FR-specific dispatcher branch."""

    def test_siren_match_returns_frozen(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "fr_search",
            lambda q: {
                "found": True, "siren": "931159206",
                "nom_complet": "PAPETERIE", "date_creation": "2024-07-18",
                "etat_administratif": "A", "adresse": "12 RUE DU PARC",
                "dirigeants": ["SCP CSG"], "activite_principale": "68.20B",
                "error": None,
            },
        )
        row = {"nazwa_firmy": "PAPETERIE", "nip_vat": "931159206", "rejestr_id": ""}
        status, reason = verify_api.verify_fr_row(row)
        assert status == "FROZEN"
        assert "FR live" in reason
        assert "931159206" in reason
        assert "2024-07-18" in reason

    def test_siren_with_fr_prefix(self, monkeypatch):
        # nip_vat may have "FR" prefix — should be stripped
        called_with: list[str] = []
        def fake_search(q):
            called_with.append(q)
            return {
                "found": True, "siren": "931159206",
                "nom_complet": "PAPETERIE", "date_creation": "2024-07-18",
                "etat_administratif": "A", "adresse": "", "dirigeants": [],
                "activite_principale": "", "error": None,
            }
        monkeypatch.setattr(verify_api, "fr_search", fake_search)
        row = {"nazwa_firmy": "PAPETERIE", "nip_vat": "FR931159206", "rejestr_id": ""}
        status, _ = verify_api.verify_fr_row(row)
        assert status == "FROZEN"
        # Should have been called with digits only, not "FR..."
        assert called_with[0] == "931159206"

    def test_siren_not_found_returns_doweryfikacji(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "fr_search",
            lambda q: {"found": False, "error": "brak wyników dla '999999999'"},
        )
        row = {"nazwa_firmy": "GHOST", "nip_vat": "999999999", "rejestr_id": ""}
        status, reason = verify_api.verify_fr_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "nie istnieje" in reason.lower() or "brak" in reason.lower()

    def test_network_error_returns_pending_api(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "fr_search",
            lambda q: {"found": False, "error": "HTTP 503: Service Unavailable"},
        )
        row = {"nazwa_firmy": "X", "nip_vat": "123456789", "rejestr_id": ""}
        status, reason = verify_api.verify_fr_row(row)
        # Network errors are NOT verification failures
        assert status == verify_api.PENDING_API
        assert "503" in reason or "HTTP" in reason

    def test_closed_company_returns_doweryfikacji(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "fr_search",
            lambda q: {
                "found": True, "siren": "123456789",
                "nom_complet": "OLD CORP", "date_creation": "1990-01-01",
                "date_fermeture": "2020-06-15",
                "etat_administratif": "F",  # F = fermée
                "adresse": "", "dirigeants": [], "activite_principale": "",
                "error": None,
            },
        )
        row = {"nazwa_firmy": "OLD CORP", "nip_vat": "123456789", "rejestr_id": ""}
        status, reason = verify_api.verify_fr_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "zamknięta" in reason.lower() or "fermé" in reason.lower()

    def test_name_mismatch_returns_doweryfikacji(self, monkeypatch):
        # SIREN exists but the CSV name doesn't match the API name at all
        monkeypatch.setattr(
            verify_api, "fr_search",
            lambda q: {
                "found": True, "siren": "123456789",
                "nom_complet": "ACME TOTALLY DIFFERENT",
                "date_creation": "2020-01-01",
                "etat_administratif": "A",
                "adresse": "", "dirigeants": [], "activite_principale": "",
                "error": None,
            },
        )
        row = {"nazwa_firmy": "BILLS POLSKA SP ZOO", "nip_vat": "123456789", "rejestr_id": ""}
        status, reason = verify_api.verify_fr_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "mismatch" in reason.lower()

    def test_legal_form_tokens_stripped_for_match(self, monkeypatch):
        # CSV: "SNC PAPETERIE", API: "PAPETERIE" — should match because
        # legal-form tokens are stripped before the overlap check
        monkeypatch.setattr(
            verify_api, "fr_search",
            lambda q: {
                "found": True, "siren": "931159206",
                "nom_complet": "PAPETERIE", "date_creation": "2024-07-18",
                "etat_administratif": "A", "adresse": "", "dirigeants": [],
                "activite_principale": "", "error": None,
            },
        )
        row = {"nazwa_firmy": "PAPETERIE SAS", "nip_vat": "931159206", "rejestr_id": ""}
        status, _ = verify_api.verify_fr_row(row)
        assert status == "FROZEN"  # not DO-WERYFIKACJI from the mismatch path

    def test_no_siren_returns_pending_api(self, monkeypatch):
        def fail(q):
            raise AssertionError("fr_search should not be called")
        monkeypatch.setattr(verify_api, "fr_search", fail)
        for placeholder in ("", "brak", "do weryfikacji", "do ustalenia"):
            row = {"nazwa_firmy": "X", "nip_vat": placeholder, "rejestr_id": ""}
            status, _ = verify_api.verify_fr_row(row)
            assert status == verify_api.PENDING_API

    def test_module_unavailable(self, monkeypatch):
        monkeypatch.setattr(verify_api, "fr_search", None)
        row = {"nazwa_firmy": "X", "nip_vat": "123456789", "rejestr_id": ""}
        status, reason = verify_api.verify_fr_row(row)
        assert status == verify_api.PENDING_API
        assert "niedostępny" in reason.lower()

    def test_dirigeants_in_reason(self, monkeypatch):
        # When dirigeants exist, they should appear in the FROZEN reason
        monkeypatch.setattr(
            verify_api, "fr_search",
            lambda q: {
                "found": True, "siren": "931159206",
                "nom_complet": "PAPETERIE", "date_creation": "2024-07-18",
                "etat_administratif": "A", "adresse": "",
                "dirigeants": ["JEAN DUPONT", "MARIE CURIE"],
                "activite_principale": "", "error": None,
            },
        )
        row = {"nazwa_firmy": "PAPETERIE", "nip_vat": "931159206", "rejestr_id": ""}
        status, reason = verify_api.verify_fr_row(row)
        assert status == "FROZEN"
        assert "dirigeants" in reason
        assert "JEAN DUPONT" in reason


# ---------------------------------------------------------------------------
# verify_ee_row() — Estonian e-Äriregister (mocked)
# ---------------------------------------------------------------------------

class TestVerifyEeRow:
    """Tests for the e-Äriregister code path in verify_ee_row."""

    def _good_result(self, **overrides):
        """Build a successful e-Äriregister result dict."""
        base = {
            "found": True,
            "reg_code": "11931003",
            "name": "Sanitex OÜ",
            "historical_names": [],
            "status": "R",
            "legal_form": "5",
            "legal_address": "Harju maakond, Rae vald, Rae küla, Graniidi tee 1",
            "zip_code": "75310",
            "kmkr": "EE101376895",
            "emtak": "46.17",
            "founded": "01.01.1991",
            "capital_eur": 30000.0,
            "url": "https://ariregister.rik.ee/est/company/11931003",
            "error": None,
        }
        base.update(overrides)
        return base

    def test_reg_code_match_returns_frozen(self, monkeypatch):
        monkeypatch.setattr(verify_api, "ee_search", lambda q: self._good_result())
        monkeypatch.setattr(verify_api, "ee_detail", lambda c, **kw: self._good_result())
        row = {
            "nazwa_firmy": "Sanitex OÜ",
            "nip_vat": "EE101376895",
            "rejestr_id": "e-Äriregister 11931003",
        }
        status, reason = verify_api.verify_ee_row(row)
        assert status == "FROZEN"
        assert "11931003" in reason
        assert "EE101376895" in reason

    def test_name_search_match_returns_frozen(self, monkeypatch):
        # No reg_code in rejestr_id → use name search
        monkeypatch.setattr(verify_api, "ee_search", lambda q: self._good_result(name="Nicorex Baltic OÜ"))
        monkeypatch.setattr(verify_api, "ee_detail", lambda c, **kw: {"found": False, "error": "skip"})
        row = {
            "nazwa_firmy": "Nicorex Baltic OÜ",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "do weryfikacji",
        }
        status, reason = verify_api.verify_ee_row(row)
        assert status == "FROZEN"
        assert "Nicorex" in reason

    def test_name_mismatch_returns_doweryfikacji(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "ee_search",
            lambda q: self._good_result(name="COMPLETELY DIFFERENT OÜ"),
        )
        row = {
            "nazwa_firmy": "Sanitex OÜ",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "do weryfikacji",
        }
        status, reason = verify_api.verify_ee_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "mismatch" in reason.lower() or "nimi" in reason.lower()

    def test_kpmr_mismatch_returns_doweryfikacji(self, monkeypatch):
        # CSV claims VAT EE999999999, but registry says EE101376895
        monkeypatch.setattr(verify_api, "ee_search", lambda q: self._good_result())
        monkeypatch.setattr(verify_api, "ee_detail", lambda c, **kw: self._good_result())
        row = {
            "nazwa_firmy": "Sanitex OÜ",
            "nip_vat": "EE999999999",
            "rejestr_id": "e-Äriregister 11931003",
        }
        status, reason = verify_api.verify_ee_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "kmkr" in reason.lower() or "mismatch" in reason.lower()

    def test_closed_company_returns_doweryfikacji(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "ee_search",
            lambda q: self._good_result(status="K"),
        )
        row = {
            "nazwa_firmy": "Sanitex OÜ",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "do weryfikacji",
        }
        status, reason = verify_api.verify_ee_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "zamknięta" in reason.lower() or "kustutatud" in reason.lower()

    def test_company_not_found_returns_doweryfikacji(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "ee_search",
            lambda q: {"found": False, "error": "brak wyników dla 'FAKE'"},
        )
        row = {
            "nazwa_firmy": "FAKE BALTIC OÜ",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "do weryfikacji",
        }
        status, reason = verify_api.verify_ee_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "nie istnieje" in reason.lower()

    def test_api_error_returns_pending_api(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "ee_search",
            lambda q: {"found": False, "error": "connection: timeout"},
        )
        row = {
            "nazwa_firmy": "Sanitex OÜ",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "do weryfikacji",
        }
        status, reason = verify_api.verify_ee_row(row)
        assert status == verify_api.PENDING_API
        assert "connection" in reason.lower()

    def test_module_unavailable(self, monkeypatch):
        monkeypatch.setattr(verify_api, "ee_search", None)
        monkeypatch.setattr(verify_api, "ee_detail", None)
        row = {
            "nazwa_firmy": "Sanitex OÜ",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "do weryfikacji",
        }
        status, reason = verify_api.verify_ee_row(row)
        assert status == verify_api.PENDING_API
        assert "niedostępny" in reason.lower()

    def test_no_name_no_rejestr_returns_pending_api(self, monkeypatch):
        # Cannot search without a name hint and no reg_code
        def fail(q, **kw):
            raise AssertionError("ee_search should not be called")
        monkeypatch.setattr(verify_api, "ee_search", fail)
        monkeypatch.setattr(verify_api, "ee_detail", fail)
        row = {
            "nazwa_firmy": "",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "do weryfikacji",
        }
        status, reason = verify_api.verify_ee_row(row)
        assert status == verify_api.PENDING_API
        assert "brak" in reason.lower()

    def test_legal_form_tokens_stripped_for_match(self, monkeypatch):
        # CSV: "Sanitex", API: "Sanitex OÜ" — should match (OÜ stripped)
        monkeypatch.setattr(verify_api, "ee_search", lambda q: self._good_result(name="Sanitex OÜ"))
        monkeypatch.setattr(verify_api, "ee_detail", lambda c, **kw: {"found": False, "error": "skip"})
        row = {
            "nazwa_firmy": "Sanitex",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "do weryfikacji",
        }
        status, _ = verify_api.verify_ee_row(row)
        assert status == "FROZEN"

