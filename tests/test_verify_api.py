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
    """Tests for the KRS code path in verify_pl_row.

    Bug fix 2026-08-31: tests use real PL NIP (BILLS Sp. z o.o. 5140361901)
    that passes mod-11, so the verify_pl_row() flow reaches the KRS
    lookup branch. Previously tests used NIP 1234567890 which is mod-11
    invalid and now correctly hits the INVALID_CHECKSUM gate before
    reaching KRS (which is exactly the bug fix we wanted).
    """

    @pytest.fixture
    def row_with_krs(self):
        # BILLS Sp. z o.o. — real NIP that passes mod-11
        return {
            "nazwa_firmy": "ACME SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
            "nip_vat": "PL5140361901",  # BILLS Sp. z o.o. — real, mod-11 OK
            "rejestr_id": "KRS 0000123456",
        }

    def test_krs_match_returns_frozen(self, row_with_krs, monkeypatch):
        monkeypatch.setattr(
            verify_api, "krs_lookup",
            lambda krs: {"nazwa": "ACME SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
                         "nip": "5140361901",  # match CSV NIP (otherwise MISMATCH_REGISTRY)
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
                         "nip": "5140361901",
                         "regon": "999999999", "krs": krs},
        )
        status, reason = verify_api.verify_pl_row(row_with_krs, token="dummy")
        assert status == "DO-WERYFIKACJI"
        assert "mismatch" in reason.lower() or "MISMATCH_REGISTRY" in reason

    def test_krs_api_error_returns_doweryfikacji(self, row_with_krs, monkeypatch):
        monkeypatch.setattr(
            verify_api, "krs_lookup",
            lambda krs: {"error": "KRS HTTP 503"},
        )
        status, reason = verify_api.verify_pl_row(row_with_krs, token="dummy")
        assert status == "DO-WERYFIKACJI"
        assert "503" in reason

    def test_krs_api_returns_none(self, row_with_krs, monkeypatch):
        # krs_lookup returns None on network failure
        monkeypatch.setattr(verify_api, "krs_lookup", lambda krs: None)
        status, reason = verify_api.verify_pl_row(row_with_krs, token="dummy")
        assert status == "DO-WERYFIKACJI"
        assert "brak" in reason.lower() or "KRS" in reason

    def test_hallucinated_nip_blocks_krs_lookup(self, row_with_krs, monkeypatch):
        # NEW: NIP 1234567890 is mod-11 invalid → should hit INVALID_CHECKSUM
        # gate before KRS lookup is ever called.
        called = []
        def fake_krs(krs):
            called.append(krs)
            return {"nazwa": "ACME", "nip": "1234567890", "regon": "999"}
        monkeypatch.setattr(verify_api, "krs_lookup", fake_krs)

        row = {
            "nazwa_firmy": "ACME",
            "nip_vat": "PL1234567890",  # mod-11 invalid (halucynacja)
            "rejestr_id": "KRS 0000123456",
        }
        status, reason = verify_api.verify_pl_row(row, token="dummy")
        assert status == "DO-WERYFIKACJI"
        assert "INVALID_CHECKSUM" in reason
        assert called == [], f"KRS lookup should NOT be called for invalid NIP, but was: {called}"


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
        # Real but unknown IČO — ARES returns 404 / not found.
        # Bug fix 2026-08-31: now verify_cz_row has a pre-flight mod-11 check
        # that catches bad IČO BEFORE calling ARES. Use a real IČO that
        # passes mod-11 but is unknown in ARES, so we reach the API path.
        # CZ00000000 has s=0, expected=1 → INVALID_CHECKSUM before ARES.
        # We test that pre-flight catches it.
        row = {
            "nazwa_firmy": "GHOST LTD.",
            "nip_vat": "CZ00000000",  # 00000000 → INVALID_CHECKSUM (s=0, exp=1)
            "rejestr_id": "ARES IČO 00000000",
        }
        status, reason = verify_api.verify_cz_row(row)
        assert status == "DO-WERYFIKACJI"
        # Per Zasady: INVALID_CHECKSUM is caught BEFORE ARES API call
        assert "INVALID_CHECKSUM" in reason or "INVALID_ID" in reason

    def test_ares_404_real_unknown_ico(self, monkeypatch):
        # Real IČO that passes mod-11 but ARES returns 404 (unknown IČO).
        # FORTIS-DB real IČO is 25775634 (passes mod-11), so we use that
        # but mock ARES to return None (simulating 404).
        called = []
        def fake_ares(ico):
            called.append(ico)
            return None  # ARES returns nothing for unknown IČO
        monkeypatch.setattr(verify_api, "ares_lookup", fake_ares)
        row = {
            "nazwa_firmy": "GHOST LTD.",
            "nip_vat": "CZ25775634",  # real IČO, passes mod-11
            "rejestr_id": "ARES IČO 25775634",
        }
        status, reason = verify_api.verify_cz_row(row)
        assert status == "DO-WERYFIKACJI"
        # Pre-flight passed (real IČO), ARES returned None → DO-WERYFIKACJI
        assert "ARES" in reason
        assert called == ["25775634"]  # pre-flight should NOT short-circuit ARES lookup

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

    def test_loose_diacritics_typo_match(self):
        """CSV typo 'ODPOWIEDZIALNOSCIA' (no Ą) vs API 'ODPOWIEDZIALNOŚCIĄ'
        must still match (loose mode strips diacritics). Real BILLS regression
        case — false positive DO-W if strict."""
        ok, score, _ = verify_api.name_similarity(
            "BILLS SPÓŁKA Z OGRANICZONA ODPOWIEDZIALNOŚCIĄ",
            "BILLS SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        )
        assert ok is True
        assert score == 1.0

    def test_loose_legal_form_variants_match(self):
        """Loose mode regex tolerates 'SP. Z.O.O.' vs 'SP. Z O.O.' and
        'SPOL. S R.O.' vs 'SPOL. S R. O.'"""
        ok, score, _ = verify_api.name_similarity(
            "ACME SP. Z.O.O.", "ACME sp. z o.o."
        )
        assert ok is True
        assert score == 1.0

    def test_strict_mode_catches_diacritic_difference(self):
        """Strict normalize (loose=False) does NOT strip diacritics —
        reserved for non-Jaccard uses (e.g. KRS exact lookup)."""
        # This documents the difference but we use loose in name_similarity
        strict = verify_api.normalize("BILLS SPÓŁKA", loose=False)
        loose = verify_api.normalize("BILLS SPÓŁKA", loose=True)
        assert strict != loose  # they differ (loose strips diacritics)


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


# ---------------------------------------------------------------------------
# verify_lt_row() — Lithuanian JAR (data.gov.lt SAU API) (mocked)
# ---------------------------------------------------------------------------

class TestVerifyLtRow:
    """Tests for the Lithuanian JAR code path in verify_lt_row."""

    def _good_result(self, **overrides):
        base = {
            "found": True,
            "ja_kodas": 110443493,
            "name": 'UAB "SANITEX"',
            "reg_data": "1992-11-12",
            "isreg_data": None,  # active
            "forma_uuid": "5c444113-5081-4d88-b94d-782c0779bb89",
            "statusas_uuid": "5ef6b364-a5ff-47fb-8600-ff859214ef85",
            "stat_data": "2025-05-30",
            "source_url": "https://get.data.gov.lt/...?ja_kodas=110443493",
            "error": None,
        }
        base.update(overrides)
        return base

    def test_ja_kodas_match_returns_frozen(self, monkeypatch):
        monkeypatch.setattr(verify_api, "lt_jar_lookup", lambda c: self._good_result())
        monkeypatch.setattr(
            verify_api, "lt_jar_resolve_forma_status",
            lambda f, s: ("Uždaroji akcinė bendrovė", "Teisinis statusas neįregistruotas", 310, 0),
        )
        row = {
            "nazwa_firmy": 'UAB "SANITEX"',
            "nip_vat": "LT110443493",
            "rejestr_id": "JAR 110443493",
        }
        status, reason = verify_api.verify_lt_row(row)
        assert status == "FROZEN"
        assert "110443493" in reason
        assert "1992-11-12" in reason

    def test_no_ja_kodas_returns_pending_api(self, monkeypatch):
        # No JAR code in rejestr_id → name search not available
        def fail(c):
            raise AssertionError("lt_jar_lookup should not be called")
        monkeypatch.setattr(verify_api, "lt_jar_lookup", fail)
        row = {
            "nazwa_firmy": "UAB Tabakininkas",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "do weryfikacji",
        }
        status, reason = verify_api.verify_lt_row(row)
        assert status == verify_api.PENDING_API
        assert "name search" in reason.lower() or "brak" in reason.lower()

    def test_invalid_ja_kodas_returns_doweryfikacji(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "lt_jar_lookup",
            lambda c: {"found": False, "error": "brak wyników dla ja_kodas=999999999"},
        )
        row = {
            "nazwa_firmy": "UAB FAKE",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "JAR 999999999",
        }
        status, reason = verify_api.verify_lt_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "999999999" in reason

    def test_deregistered_company_returns_doweryfikacji(self, monkeypatch):
        monkeypatch.setattr(
            verify_api, "lt_jar_lookup",
            lambda c: self._good_result(isreg_data="2020-01-15"),
        )
        row = {
            "nazwa_firmy": 'UAB "SANITEX"',
            "nip_vat": "do weryfikacji",
            "rejestr_id": "JAR 110443493",
        }
        status, reason = verify_api.verify_lt_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "wyrejestrowana" in reason.lower() or "isreg" in reason.lower()

    def test_bankrupt_company_returns_doweryfikacji(self, monkeypatch):
        # statusas_kodas=5 = Bankrutuojantis (going bankrupt)
        monkeypatch.setattr(verify_api, "lt_jar_lookup", lambda c: self._good_result())
        monkeypatch.setattr(
            verify_api, "lt_jar_resolve_forma_status",
            lambda f, s: ("Uždaroji akcinė bendrovė", "Bankrutuojantis", 310, 5),
        )
        row = {
            "nazwa_firmy": 'UAB "SANITEX"',
            "nip_vat": "do weryfikacji",
            "rejestr_id": "JAR 110443493",
        }
        status, reason = verify_api.verify_lt_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "bankrut" in reason.lower() or "likwid" in reason.lower()

    def test_name_mismatch_returns_doweryfikacji(self, monkeypatch):
        # CSV "UAB ACME" vs API "UAB \"SANITEX\"" — no token overlap
        monkeypatch.setattr(verify_api, "lt_jar_lookup", lambda c: self._good_result())
        monkeypatch.setattr(
            verify_api, "lt_jar_resolve_forma_status",
            lambda f, s: ("Uždaroji akcinė bendrovė", "Teisinis statusas neįregistruotas", 310, 0),
        )
        row = {
            "nazwa_firmy": "UAB ACME WHOLESALE",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "JAR 110443493",
        }
        status, reason = verify_api.verify_lt_row(row)
        assert status == "DO-WERYFIKACJI"
        assert "mismatch" in reason.lower() or "pavadinimas" in reason.lower()

    def test_legal_form_tokens_stripped_for_match(self, monkeypatch):
        # CSV: 'UAB "SANITEX"', API: 'UAB "SANITEX"' — exact match
        # CSV: "SANITEX" (just name) vs API: 'UAB "SANITEX"' — match after UAB stripped
        monkeypatch.setattr(verify_api, "lt_jar_lookup", lambda c: self._good_result())
        monkeypatch.setattr(
            verify_api, "lt_jar_resolve_forma_status",
            lambda f, s: ("Uždaroji akcinė bendrovė", "Teisinis statusas neįregistruotas", 310, 0),
        )
        row = {
            "nazwa_firmy": "SANITEX",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "JAR 110443493",
        }
        status, _ = verify_api.verify_lt_row(row)
        assert status == "FROZEN"

    def test_module_unavailable(self, monkeypatch):
        monkeypatch.setattr(verify_api, "lt_jar_lookup", None)
        row = {
            "nazwa_firmy": "UAB",
            "nip_vat": "do weryfikacji",
            "rejestr_id": "JAR 110443493",
        }
        status, reason = verify_api.verify_lt_row(row)
        assert status == verify_api.PENDING_API
        assert "niedostępny" in reason.lower()

    def test_pvm_mismatch_does_not_fail(self, monkeypatch):
        # CSV PVM LT999999999 ≠ expected LT110443493 — not a verification
        # failure (PVMs can differ for non-LT branches); reason should note it
        monkeypatch.setattr(verify_api, "lt_jar_lookup", lambda c: self._good_result())
        monkeypatch.setattr(
            verify_api, "lt_jar_resolve_forma_status",
            lambda f, s: ("Uždaroji akcinė bendrovė", "Teisinis statusas neįregistruotas", 310, 0),
        )
        row = {
            "nazwa_firmy": 'UAB "SANITEX"',
            "nip_vat": "LT999999999",
            "rejestr_id": "JAR 110443493",
        }
        status, reason = verify_api.verify_lt_row(row)
        # PVM mismatch is informational, not a verification failure
        assert status == "FROZEN"
        assert "999999999" in reason



# ---------------------------------------------------------------------------
# apply_apollo_enrichments() — back-fill from Apollo org enrich
# ---------------------------------------------------------------------------

class TestApplyApolloEnrichments:
    """apply_apollo_enrichments() writes only into placeholder cells."""

    def test_no_enrichments_no_op(self, tmp_path):
        csv_path = tmp_path / "catalog-B-SK.csv"
        csv_path.write_text(
            "id,nazwa_firmy,telefon,linkedin,miasto,email_decydent\n"
            "SK-1,Foo,,,Bratislava,\n"
        )
        assert verify_api.apply_apollo_enrichments(csv_path, {}) == 0
        # File unchanged
        assert "SK-1,Foo" in csv_path.read_text()

    def test_backfills_placeholders(self, tmp_path):
        csv_path = tmp_path / "catalog-B-SK.csv"
        csv_path.write_text(
            "id,nazwa_firmy,telefon,linkedin,miasto,email_decydent\n"
            "SK-1,Foo,do weryfikacji,brak,do ustalenia,n/a\n"
        )
        enrichments = {
            "SK-1": {
                "telefon": "+421 2 1234 5678",
                "linkedin": "linkedin.com/company/foo",
                "miasto": "Bratislava",
                "email_decydent": "ceo@foo.sk",
            }
        }
        n = verify_api.apply_apollo_enrichments(csv_path, enrichments)
        assert n == 4
        text = csv_path.read_text()
        assert "+421 2 1234 5678" in text
        assert "linkedin.com/company/foo" in text
        assert "Bratislava" in text
        assert "ceo@foo.sk" in text

    def test_does_not_clobber_existing(self, tmp_path):
        """If a cell already has real data, Apollo must NOT overwrite it."""
        csv_path = tmp_path / "catalog-B-SK.csv"
        csv_path.write_text(
            "id,nazwa_firmy,telefon,linkedin,miasto,email_decydent\n"
            "SK-1,Foo,+421 911 000 000,linkedin.com/existing,Kosice,ceo@existing.sk\n"
        )
        enrichments = {
            "SK-1": {
                "telefon": "+421 2 1234 5678",
                "linkedin": "linkedin.com/company/foo",
                "miasto": "Bratislava",
                "email_decydent": "ceo@foo.sk",
            }
        }
        n = verify_api.apply_apollo_enrichments(csv_path, enrichments)
        assert n == 0  # nothing written
        text = csv_path.read_text()
        # Originals preserved
        assert "+421 911 000 000" in text
        assert "linkedin.com/existing" in text
        assert "Kosice" in text
        assert "ceo@existing.sk" in text

    def test_unknown_id_ignored(self, tmp_path):
        csv_path = tmp_path / "catalog-B-SK.csv"
        csv_path.write_text(
            "id,nazwa_firmy,telefon,linkedin,miasto,email_decydent\n"
            "SK-1,Foo,brak,brak,brak,brak\n"
        )
        enrichments = {
            "SK-NOT-EXIST": {"telefon": "+421 9", "linkedin": "x", "miasto": "y"},
        }
        n = verify_api.apply_apollo_enrichments(csv_path, enrichments)
        assert n == 0
        text = csv_path.read_text()
        # All cells still placeholder
        assert "Foo,brak,brak,brak,brak" in text


# ---------------------------------------------------------------------------
# verify_apollo_row() — second-pass back-fill via Apollo
# ---------------------------------------------------------------------------

class TestVerifyApolloRow:
    """verify_apollo_row() routes Apollo org/people enrich into apollo_enrichments."""

    def setup_method(self):
        # Reset module-level enrichments dict before each test
        verify_api.apollo_enrichments.clear()

    def test_apollo_module_unavailable_returns_pending(self, monkeypatch):
        monkeypatch.setattr(verify_api, "APOLLO_AVAILABLE", False)
        monkeypatch.setattr(verify_api, "_apollo_enrich_row", None)
        row = {"id": "SK-1", "nazwa_firmy": "Foo s.r.o."}
        status, reason = verify_api.verify_apollo_row(row)
        assert status == verify_api.PENDING_API
        assert "niedostępny" in reason.lower()

    def test_org_match_populates_enrichments(self, monkeypatch):
        def fake_enrich(row):
            return {
                "company": "Foo s.r.o.",
                "domain": "foo.sk",
                "matched": False,  # FREE plan: no people match
                "org_matched": True,
                "phone": "+421 2 123 4567",
                "linkedin": "linkedin.com/company/foo",
                "city": "Bratislava",
            }
        monkeypatch.setattr(verify_api, "_apollo_enrich_row", fake_enrich)
        row = {"id": "SK-1", "nazwa_firmy": "Foo s.r.o."}
        status, reason = verify_api.verify_apollo_row(row)
        assert status == "FROZEN"
        assert "org enrich" in reason
        assert verify_api.apollo_enrichments.get("SK-1") == {
            "telefon": "+421 2 123 4567",
            "linkedin": "linkedin.com/company/foo",
            "miasto": "Bratislava",
        }

    def test_no_match_returns_pending(self, monkeypatch):
        def fake_enrich(row):
            return {"company": "X", "domain": "x", "matched": False, "org_matched": False, "org_error": "not in Apollo DB"}
        monkeypatch.setattr(verify_api, "_apollo_enrich_row", fake_enrich)
        row = {"id": "PL-X", "nazwa_firmy": "X"}
        status, reason = verify_api.verify_apollo_row(row)
        assert status == verify_api.PENDING_API
        assert "PL-X" not in verify_api.apollo_enrichments

    def test_empty_company_returns_pending(self, monkeypatch):
        monkeypatch.setattr(verify_api, "_apollo_enrich_row", lambda r: {"org_matched": True, "phone": "x"})
        row = {"id": "PL-X", "nazwa_firmy": ""}
        status, reason = verify_api.verify_apollo_row(row)
        assert status == verify_api.PENDING_API
        assert "nazwy" in reason.lower() or "nazwa" in reason.lower()
