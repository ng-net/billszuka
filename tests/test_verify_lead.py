"""
test_verify_lead.py — Tests for tools/verify_lead.py.

Covers the pure `normalize_url()` function. The verification orchestrator
(`verify_lead`) is integration-heavy and depends on real registry APIs,
so it's exercised in the runbook rather than the test suite.
"""
from __future__ import annotations

import verify_lead


class TestNormalizeUrl:
    """normalize_url() cleans firm URLs for WHOIS / domain lookups."""

    def test_empty_returns_none(self):
        assert verify_lead.normalize_url("") is None
        assert verify_lead.normalize_url(None) is None

    def test_already_clean(self):
        assert verify_lead.normalize_url("bills.pl") == "bills.pl"
        assert verify_lead.normalize_url("ckcomplex.pl") == "ckcomplex.pl"

    def test_strip_protocol(self):
        assert verify_lead.normalize_url("https://bills.pl") == "bills.pl"
        assert verify_lead.normalize_url("http://bills.pl") == "bills.pl"

    def test_strip_www(self):
        assert verify_lead.normalize_url("www.bills.pl") == "bills.pl"
        assert verify_lead.normalize_url("https://www.bills.pl") == "bills.pl"

    def test_strip_path(self):
        assert verify_lead.normalize_url("https://bills.pl/o-nas") == "bills.pl"
        assert verify_lead.normalize_url("bills.pl/about") == "bills.pl"

    def test_strip_query_string(self):
        assert verify_lead.normalize_url("bills.pl?utm_source=x") == "bills.pl"

    def test_strip_trailing_slash(self):
        assert verify_lead.normalize_url("bills.pl/") == "bills.pl"

    def test_combined(self):
        # Scheme is matched case-sensitively (lowercase only), then
        # urlparse lowercases the netloc per RFC and `www.` is stripped.
        assert (
            verify_lead.normalize_url("https://www.bills.pl/o-nas/?utm=x")
            == "bills.pl"
        )
