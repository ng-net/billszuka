"""
test_l0_preflight.py — Tests for tools/l0_preflight.py.

Covers:
  • name_match() — Jaccard-based fuzzy matching (FABRYKAT detection)
"""
from __future__ import annotations

import pytest

import l0_preflight


class TestNameMatch:
    """name_match() uses Jaccard 0.8 threshold + LEGAL_TOKENS strip.

    Same logic as tools/verify_api.py:name_similarity — kept as a separate
    copy because l0_preflight.py is a standalone tool that can be run
    without importing verify_api.
    """

    def test_exact_match(self):
        assert l0_preflight.name_match("ACME", "ACME") == (True, "jaccard 1.00 (≥0.8)")

    def test_peal_vs_peal_real_estate_mismatch(self):
        # Old substring check passed this — Jaccard correctly rejects.
        m, reason = l0_preflight.name_match("PEAL a.s.", "PEAL Real Estate s.r.o.")
        assert m is False
        assert "jaccard" in reason.lower()

    def test_geco_vs_geco_klempizo_mismatch(self):
        m, reason = l0_preflight.name_match("GECO, a.s.", "GECO KLEMPIZO s.r.o.")
        assert m is False
        assert "jaccard" in reason.lower()

    def test_fortis_db_matches_self(self):
        m, reason = l0_preflight.name_match(
            "FORTIS-DB, spol. s r.o.", "FORTIS-DB, spol. s r.o."
        )
        assert m is True
        assert "1.00" in reason

    def test_legal_form_tokens_stripped(self):
        # "ACME SP. Z O.O." vs "ACME" — SP/ZO/O should be stripped,
        # leaving "ACME" vs "ACME" → jaccard 1.0
        m, _ = l0_preflight.name_match("ACME SP. Z O.O.", "ACME")
        assert m is True

    def test_empty_input(self):
        assert l0_preflight.name_match("", "ACME") == (False, "empty name")
        assert l0_preflight.name_match("ACME", "") == (False, "empty name")
        assert l0_preflight.name_match("", "") == (False, "empty name")

    def test_threshold_boundary(self):
        # 4 tokens overlap out of 5 total → 0.8 = exact threshold (match)
        m, _ = l0_preflight.name_match(
            "ALPHA BETA GAMMA DELTA", "ALPHA BETA GAMMA DELTA X"
        )
        assert m is True
