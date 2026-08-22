#!/usr/bin/env python3
"""
test_11_levels.py — Strict-assertion test for all Lead Generation Levels (Poland),
L0-L11 per methodology.md.

Each level is a function `test_l<n>_<slug>()` that returns a tuple
(passed: bool, msg: str, count: int). The script:
  • Aggregates pass/fail/skip counts
  • Prints a final summary table
  • Exits 0 only if every level is PASS or SKIP (no FAIL)
  • Exits 1 if any level FAILED — broken scrapes now fail the test suite
  • Detects DDG anti-bot landing page and reports SKIP (not fake PASS)
  • Honors BRAVE_API_KEY env var as a real search provider (preferred)

Run:
  python3 tools/test_11_levels.py           # strict, default
  python3 tools/test_11_levels.py --warn    # warn-only mode (exits 0 always)
  pytest tools/test_11_levels.py            # standard pytest, asserts work natively
"""

from __future__ import annotations

import json
import os
import re
import socket
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Per-level minimum-result thresholds. Tighten in production, loosen in dev.
LEVEL_CONFIG: dict[str, dict] = {
    "L0":  {"min_results": 1, "category": "offline", "label": "Pre-flight NIP Checksum (mod 11)"},
    "L1": {"min_results": 1, "category": "search", "label": "General Web Search"},
    "L2": {"min_results": 1, "category": "search", "label": "Marketplace & Aggregators"},
    "L3": {"min_results": 1, "category": "api",    "label": "Official Register Scans (KRS)"},
    "L4": {"min_results": 1, "category": "search", "label": "Customs & Regulatory (WSA/NSA)"},
    "L5": {"min_results": 1, "category": "dns",    "label": "Domain DNS Keyword Sweeps"},
    "L6": {"min_results": 1, "category": "search", "label": "Trade Fairs & Expos"},
    "L7": {"min_results": 1, "category": "search", "label": "Social Media OSINT"},
    "L8": {"min_results": 1, "category": "search", "label": "Business Directories"},
    "L9": {"min_results": 1, "category": "config", "label": "LLM Scouting (OpenRouter)"},
    "L10": {"min_results": 1, "category": "search", "label": "EUIPO Trademark Search"},
    "L11": {"min_results": 1, "category": "search", "label": "Public Procurement (TED/BZP)"},
}

# Markers in DDG HTML that indicate the anti-bot landing page (not real results).
# If these dominate and no `class="result__` is present, we are being blocked.
DDG_BLOCK_TITLE_RE = re.compile(r"<title>\s*DuckDuckGo\s*</title>", re.IGNORECASE)
DDG_RESULT_CLASS_RE = re.compile(r'class="result__|class="web-result|class="result ')


# ---------------------------------------------------------------------------
# Search provider abstraction
# ---------------------------------------------------------------------------

def _read_env() -> dict[str, str]:
    env: dict[str, str] = dict(os.environ)
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip())
    return env


def search_ddg(query: str, timeout: int = 10) -> tuple[str, bool]:
    """
    Raw DDG HTML search. Returns (html, blocked).
    `blocked=True` means the response is the anti-bot landing page, not search results.
    """
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", errors="replace")
    blocked = bool(DDG_BLOCK_TITLE_RE.search(html)) and not DDG_RESULT_CLASS_RE.search(html)
    return html, blocked


def search_brave(query: str, api_key: str, timeout: int = 10) -> tuple[str, bool]:
    """
    Brave Search API — real, reliable, requires API key.
    Returns (html_text, blocked) where html_text is the raw JSON response as a string.
    """
    url = (
        f"https://api.search.brave.com/res/v1/web/search"
        f"?q={urllib.parse.quote(query)}&count=10"
    )
    req = urllib.request.Request(
        url,
        headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
    )
    body = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", errors="replace")
    return body, False


def search_serpapi(query: str, api_key: str, timeout: int = 10) -> tuple[str, bool]:
    """
    SerpAPI Google Search. Returns (json_text, blocked).
    """
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key
    }
    encoded_params = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{encoded_params}", headers={"User-Agent": "Mozilla/5.0"})
    body = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", errors="replace")
    return body, False


def get_search_provider() -> tuple[str, Callable[[str], tuple[str, bool]]]:
    """
    Pick a search provider. SerpAPI if key is set, else Brave if key is set, else DDG (best-effort).
    Returns (name, fn). The fn takes a query and returns (raw_response, blocked).
    """
    env = _read_env()
    serpapi_key = env.get("SERPAPI_KEY", "").strip()
    if serpapi_key:
        def serpapi_call(q: str) -> tuple[str, bool]:
            return search_serpapi(q, serpapi_key)
        return "serpapi", serpapi_call

    brave_key = env.get("BRAVE_API_KEY", "").strip()
    if brave_key:
        def brave_call(q: str) -> tuple[str, bool]:
            return search_brave(q, brave_key)
        return "brave", brave_call

    def ddg_call(q: str) -> tuple[str, bool]:
        return search_ddg(q)
    return "ddg", ddg_call


# ---------------------------------------------------------------------------
# Level implementations
# ---------------------------------------------------------------------------

def run_l0() -> tuple[bool, str, int]:
    """L0 pre-flight: NIP (mod 11) checksum formula — offline, deterministic."""
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]

    def nip_checksum_ok(nip: str) -> bool:
        nip = str(nip).replace("PL", "").replace(" ", "")
        if len(nip) != 10 or not nip.isdigit():
            return False
        s = sum(int(nip[i]) * weights[i] for i in range(9))
        return s % 11 == int(nip[9])

    # Construct a valid NIP: 9 fixed digits + computed control digit
    base = "526104082"
    ctrl = sum(int(base[i]) * weights[i] for i in range(9)) % 11
    valid = base + str(ctrl)
    assert nip_checksum_ok(valid), f"L0: constructed NIP {valid} must pass checksum"
    assert not nip_checksum_ok(base + str((ctrl + 1) % 10)), "L0: corrupted control digit must fail"
    assert not nip_checksum_ok("12345"), "L0: wrong length must fail"
    return True, f"PASS — NIP mod-11 checksum formula verified ({valid})", 1


def run_l1(provider_fn) -> tuple[bool, str, int]:
    """General Web Search."""
    name, fn = provider_fn
    raw, blocked = fn("dystrybutor powermatic polska")
    if name == "ddg":
        if blocked:
            return True, f"SKIP — DDG anti-bot landing page (no `result__` class). Set BRAVE_API_KEY in .env for real search.", 0
        titles = re.findall(r'<a class="result__url"[^>]*>\s*([^<]+)\s*</a>', raw)
        assert len(titles) >= LEVEL_CONFIG["L1"]["min_results"], (
            f"L1: expected ≥ {LEVEL_CONFIG['L1']['min_results']} result, got {len(titles)}. "
            "DDG may have changed markup or rate-limited us."
        )
        return True, f"PASS — {len(titles)} results", len(titles)
    elif name == "serpapi":
        data = json.loads(raw)
        n = len(data.get("organic_results", []))
        assert n >= LEVEL_CONFIG["L1"]["min_results"], f"L1 SerpAPI: expected ≥ {LEVEL_CONFIG['L1']['min_results']} result, got {n}"
        return True, f"PASS — {n} results (SerpAPI)", n
    else:
        # brave: parse JSON
        data = json.loads(raw)
        n = len(data.get("web", {}).get("results", []))
        assert n >= LEVEL_CONFIG["L1"]["min_results"], f"L1 Brave: expected ≥ {LEVEL_CONFIG['L1']['min_results']} result, got {n}"
        return True, f"PASS — {n} results (Brave)", n


def run_l2(provider_fn) -> tuple[bool, str, int]:
    """Marketplace & Aggregators (Allegro / Ceneo / OLX)."""
    name, fn = provider_fn
    raw, blocked = fn("powermatic 3 plus allegro")
    if name == "ddg":
        if blocked:
            return True, "SKIP — DDG blocked. Set BRAVE_API_KEY for real scrape.", 0
        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', raw, re.DOTALL)
        assert len(snippets) >= LEVEL_CONFIG["L2"]["min_results"], (
            f"L2: expected ≥ {LEVEL_CONFIG['L2']['min_results']} snippet, got {len(snippets)}"
        )
        return True, f"PASS — {len(snippets)} snippets", len(snippets)
    elif name == "serpapi":
        data = json.loads(raw)
        n = len(data.get("organic_results", []))
        assert n >= LEVEL_CONFIG["L2"]["min_results"], f"L2 SerpAPI: expected ≥ {LEVEL_CONFIG['L2']['min_results']} result, got {n}"
        return True, f"PASS — {n} results (SerpAPI)", n
    else:
        data = json.loads(raw)
        n = len(data.get("web", {}).get("results", []))
        assert n >= LEVEL_CONFIG["L2"]["min_results"], f"L2 Brave: expected ≥ {LEVEL_CONFIG['L2']['min_results']} result, got {n}"
        return True, f"PASS — {n} results (Brave)", n


def run_l3() -> tuple[bool, str, int]:
    """KRS API live response — independent of search provider."""
    url = "https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/0000847239"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    nazwa = data["odpis"]["dane"]["dzial1"]["danePodmiotu"]["nazwa"]
    assert nazwa, "L3: KRS API returned empty `nazwa`"
    return True, f"PASS — {nazwa}", 1


def run_l4(provider_fn) -> tuple[bool, str, int]:
    """NSA / WSA court rulings."""
    name, fn = provider_fn
    raw, blocked = fn("site:orzeczenia.nsa.gov.pl nabijarka tytoniowa urząd celny")
    if name == "ddg":
        if blocked:
            return True, "SKIP — DDG blocked. Use BRAVE_API_KEY or scrape orzeczenia.nsa.gov.pl directly.", 0
        matches = re.findall(r'href="([^"]*orzeczenia\.nsa\.gov\.pl[^"]*)"', raw)
        assert len(matches) >= LEVEL_CONFIG["L4"]["min_results"], (
            f"L4: expected ≥ {LEVEL_CONFIG['L4']['min_results']} NSA ruling, got {len(matches)}. "
            "Query may have zero hits — adjust SŁOWNIK-PL or use a real search API."
        )
        return True, f"PASS — {len(matches)} NSA rulings", len(matches)
    elif name == "serpapi":
        data = json.loads(raw)
        n = sum(1 for r in data.get("organic_results", []) if "orzeczenia.nsa.gov.pl" in r.get("link", ""))
        assert n >= LEVEL_CONFIG["L4"]["min_results"], f"L4 SerpAPI: expected ≥ {LEVEL_CONFIG['L4']['min_results']} NSA ruling, got {n}"
        return True, f"PASS — {n} NSA rulings (SerpAPI)", n
    else:
        data = json.loads(raw)
        n = sum(1 for r in data.get("web", {}).get("results", []) if "orzeczenia.nsa.gov.pl" in r.get("url", ""))
        assert n >= LEVEL_CONFIG["L4"]["min_results"], f"L4 Brave: expected ≥ {LEVEL_CONFIG['L4']['min_results']} NSA ruling, got {n}"
        return True, f"PASS — {n} NSA rulings (Brave)", n


def run_l5() -> tuple[bool, str, int]:
    """DNS resolution sweep — independent of search provider."""
    test_domains = ["powermatic.pl", "ismoking.pl", "tabak.pl", "bonga.pl"]
    resolved = []
    for dom in test_domains:
        try:
            ip = socket.gethostbyname(dom)
            resolved.append(f"{dom}->{ip}")
        except Exception:
            pass
    assert len(resolved) >= LEVEL_CONFIG["L5"]["min_results"], (
        f"L5: expected ≥ {LEVEL_CONFIG['L5']['min_results']} resolved domain, got {len(resolved)}. "
        "Test domains may have lapsed."
    )
    return True, f"PASS — {len(resolved)}/{len(test_domains)} domains resolved", len(resolved)


def run_l6(provider_fn) -> tuple[bool, str, int]:
    """Trade fairs & expos."""
    name, fn = provider_fn
    raw, blocked = fn('"InterTabac" "polska" "wystawca" OR "exhibitor" 2024 OR 2025')
    if name == "ddg":
        if blocked:
            return True, "SKIP — DDG blocked. Set BRAVE_API_KEY for real scrape.", 0
        matches = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', raw, re.DOTALL)
        assert len(matches) >= LEVEL_CONFIG["L6"]["min_results"], (
            f"L6: expected ≥ {LEVEL_CONFIG['L6']['min_results']} InterTabac result, got {len(matches)}"
        )
        return True, f"PASS — {len(matches)} InterTabac snippets", len(matches)
    elif name == "serpapi":
        data = json.loads(raw)
        n = len(data.get("organic_results", []))
        assert n >= LEVEL_CONFIG["L6"]["min_results"], f"L6 SerpAPI: expected ≥ {LEVEL_CONFIG['L6']['min_results']} result, got {n}"
        return True, f"PASS — {n} results (SerpAPI)", n
    else:
        data = json.loads(raw)
        n = len(data.get("web", {}).get("results", []))
        assert n >= LEVEL_CONFIG["L6"]["min_results"], f"L6 Brave: expected ≥ {LEVEL_CONFIG['L6']['min_results']} result, got {n}"
        return True, f"PASS — {n} results (Brave)", n


def run_l7(provider_fn) -> tuple[bool, str, int]:
    """Social Media OSINT (FB groups)."""
    name, fn = provider_fn
    raw, blocked = fn('site:facebook.com/groups "nabijarka" OR "tytoń hurt"')
    if name == "ddg":
        if blocked:
            return True, "SKIP — DDG blocked. Set BRAVE_API_KEY for real scrape.", 0
        matches = re.findall(r'href="([^"]*facebook\.com/groups[^"]*)"', raw)
        assert len(matches) >= LEVEL_CONFIG["L7"]["min_results"], (
            f"L7: expected ≥ {LEVEL_CONFIG['L7']['min_results']} FB group, got {len(matches)}"
        )
        return True, f"PASS — {len(matches)} FB trade groups", len(matches)
    elif name == "serpapi":
        data = json.loads(raw)
        n = sum(1 for r in data.get("organic_results", []) if "facebook.com/groups" in r.get("link", ""))
        assert n >= LEVEL_CONFIG["L7"]["min_results"], f"L7 SerpAPI: expected ≥ {LEVEL_CONFIG['L7']['min_results']} FB group, got {n}"
        return True, f"PASS — {n} FB groups (SerpAPI)", n
    else:
        data = json.loads(raw)
        n = sum(1 for r in data.get("web", {}).get("results", []) if "facebook.com/groups" in r.get("url", ""))
        assert n >= LEVEL_CONFIG["L7"]["min_results"], f"L7 Brave: expected ≥ {LEVEL_CONFIG['L7']['min_results']} FB group, got {n}"
        return True, f"PASS — {n} FB groups (Brave)", n


def run_l8(provider_fn) -> tuple[bool, str, int]:
    """Business Directories (Aleo / PKT)."""
    name, fn = provider_fn
    raw, blocked = fn('site:aleo.com "hurtownia tytoniowa"')
    if name == "ddg":
        if blocked:
            return True, "SKIP — DDG blocked. Set BRAVE_API_KEY for real scrape.", 0
        matches = re.findall(r'href="([^"]*aleo\.com[^"]*)"', raw)
        assert len(matches) >= LEVEL_CONFIG["L8"]["min_results"], (
            f"L8: expected ≥ {LEVEL_CONFIG['L8']['min_results']} Aleo profile, got {len(matches)}"
        )
        return True, f"PASS — {len(matches)} Aleo profiles", len(matches)
    elif name == "serpapi":
        data = json.loads(raw)
        n = sum(1 for r in data.get("organic_results", []) if "aleo.com" in r.get("link", ""))
        assert n >= LEVEL_CONFIG["L8"]["min_results"], f"L8 SerpAPI: expected ≥ {LEVEL_CONFIG['L8']['min_results']} Aleo profile, got {n}"
        return True, f"PASS — {n} Aleo profiles (SerpAPI)", n
    else:
        data = json.loads(raw)
        n = sum(1 for r in data.get("web", {}).get("results", []) if "aleo.com" in r.get("url", ""))
        assert n >= LEVEL_CONFIG["L8"]["min_results"], f"L8 Brave: expected ≥ {LEVEL_CONFIG['L8']['min_results']} Aleo profile, got {n}"
        return True, f"PASS — {n} Aleo profiles (Brave)", n


def run_l9() -> tuple[bool, str, int]:
    """LLM Scouting — OpenRouter key in .env."""
    env = _read_env()
    api_key = env.get("OPENROUTER_API_KEY", "").strip()
    assert api_key, (
        "L9: OPENROUTER_API_KEY not set in .env. "
        "Add it or skip L9 by removing it from LEVEL_CONFIG."
    )
    # Smoke-check: format only. Live call avoided to keep test fast and key-quota-safe.
    assert api_key.startswith("sk-or-"), f"L9: OPENROUTER_API_KEY malformed (got prefix '{api_key[:6]}...')"
    return True, "PASS — key present and well-formed", 1


def _provider_link_check(provider_fn, query: str, domain: str, level: str, label: str) -> tuple[bool, str, int]:
    """Shared L10/L11-style check: search via provider, count links matching `domain`."""
    name, fn = provider_fn
    raw, blocked = fn(query)
    if name == "ddg":
        if blocked:
            return True, f"SKIP — DDG anti-bot landing page. Set BRAVE_API_KEY for real scrape.", 0
        matches = re.findall(r'href="([^"]*' + re.escape(domain) + r'[^"]*)"', raw)
        assert len(matches) >= LEVEL_CONFIG[level]["min_results"], (
            f"{level}: expected ≥ {LEVEL_CONFIG[level]['min_results']} {label} result, got {len(matches)}. "
            "Query may have zero hits — adjust the query or use a real search API."
        )
        return True, f"PASS — {len(matches)} {label} links", len(matches)
    elif name == "serpapi":
        data = json.loads(raw)
        n = sum(1 for r in data.get("organic_results", []) if domain in r.get("link", ""))
        assert n >= LEVEL_CONFIG[level]["min_results"], f"{level} SerpAPI: expected ≥ {LEVEL_CONFIG[level]['min_results']} {label} result, got {n}"
        return True, f"PASS — {n} {label} links (SerpAPI)", n
    else:
        data = json.loads(raw)
        n = sum(1 for r in data.get("web", {}).get("results", []) if domain in r.get("url", ""))
        assert n >= LEVEL_CONFIG[level]["min_results"], f"{level} Brave: expected ≥ {LEVEL_CONFIG[level]['min_results']} {label} result, got {n}"
        return True, f"PASS — {n} {label} links (Brave)", n


def run_l10(provider_fn) -> tuple[bool, str, int]:
    """EUIPO Trademark Search (L10)."""
    return _provider_link_check(
        provider_fn,
        'site:euipo.europa.eu "powermatic" OR "hawk" trademark',
        "euipo.europa.eu", "L10", "EUIPO",
    )


def run_l11(provider_fn) -> tuple[bool, str, int]:
    """Public Procurement — TED EU / BZP (L11)."""
    return _provider_link_check(
        provider_fn,
        'site:ted.europa.eu CPV 15800000-6 tobacco OR tytoń',
        "ted.europa.eu", "L11", "TED",
    )


# ---------------------------------------------------------------------------
# Pytest-discoverable wrappers (each level becomes a real `assert`-using test)
# ---------------------------------------------------------------------------

import pytest

_SEARCH_PROVIDER = get_search_provider()  # resolved once at import

def test_l0_nip_checksum():
    passed, msg, n = run_l0()
    if not passed:
        pytest.fail(msg)
    print(f"   L0: {msg}")

def test_l1_general_search():
    passed, msg, n = run_l1(_SEARCH_PROVIDER)
    if not passed:
        pytest.fail(msg)
    print(f"   L1: {msg}")

def test_l2_marketplace():
    passed, msg, n = run_l2(_SEARCH_PROVIDER)
    if not passed:
        pytest.fail(msg)
    print(f"   L2: {msg}")

def test_l3_krs_api():
    passed, msg, n = run_l3()
    if not passed:
        pytest.fail(msg)
    print(f"   L3: {msg}")

def test_l4_nsa_rulings():
    passed, msg, n = run_l4(_SEARCH_PROVIDER)
    if not passed:
        pytest.fail(msg)
    print(f"   L4: {msg}")

def test_l5_dns_sweep():
    passed, msg, n = run_l5()
    if not passed:
        pytest.fail(msg)
    print(f"   L5: {msg}")

def test_l6_trade_fairs():
    passed, msg, n = run_l6(_SEARCH_PROVIDER)
    if not passed:
        pytest.fail(msg)
    print(f"   L6: {msg}")

def test_l7_social_osint():
    passed, msg, n = run_l7(_SEARCH_PROVIDER)
    if not passed:
        pytest.fail(msg)
    print(f"   L7: {msg}")

def test_l8_directories():
    passed, msg, n = run_l8(_SEARCH_PROVIDER)
    if not passed:
        pytest.fail(msg)
    print(f"   L8: {msg}")

def test_l9_llm_key():
    passed, msg, n = run_l9()
    if not passed:
        pytest.fail(msg)
    print(f"   L9: {msg}")

def test_l10_euipo_trademark():
    passed, msg, n = run_l10(_SEARCH_PROVIDER)
    if not passed:
        pytest.fail(msg)
    print(f"   L10: {msg}")

def test_l11_procurement():
    passed, msg, n = run_l11(_SEARCH_PROVIDER)
    if not passed:
        pytest.fail(msg)
    print(f"   L11: {msg}")


# ---------------------------------------------------------------------------
# Standalone runner (preserves original `python3 tools/test_11_levels.py` UX)
# ---------------------------------------------------------------------------

LEVEL_RUNNERS: list[tuple[str, Callable]] = [
    ("L0", lambda: run_l0()),
    ("L1", lambda: run_l1(_SEARCH_PROVIDER)),
    ("L2", lambda: run_l2(_SEARCH_PROVIDER)),
    ("L3", lambda: run_l3()),
    ("L4", lambda: run_l4(_SEARCH_PROVIDER)),
    ("L5", lambda: run_l5()),
    ("L6", lambda: run_l6(_SEARCH_PROVIDER)),
    ("L7", lambda: run_l7(_SEARCH_PROVIDER)),
    ("L8", lambda: run_l8(_SEARCH_PROVIDER)),
    ("L9", lambda: run_l9()),
    ("L10", lambda: run_l10(_SEARCH_PROVIDER)),
    ("L11", lambda: run_l11(_SEARCH_PROVIDER)),
]


def _standalone(warn_only: bool = False) -> int:
    provider_name = _SEARCH_PROVIDER[0]
    print("=" * 80)
    print(f"  TESTING L0-L11 LEAD GENERATION LEVELS (POLAND) — provider={provider_name}")
    print("=" * 80)

    # outcome: one of PASS, FAIL, SKIP
    results: list[tuple[str, str, str, int]] = []  # (level, outcome, msg, count)

    for level_id, runner in LEVEL_RUNNERS:
        label = LEVEL_CONFIG[level_id]["label"]
        try:
            passed, msg, count = runner()
            if passed and "SKIP" in msg:
                outcome = "SKIP"
            elif passed:
                outcome = "PASS"
            else:
                outcome = "FAIL"
        except AssertionError as e:
            outcome = "FAIL"
            msg = f"ASSERTION FAILED: {e}"
            count = 0
        except Exception as e:
            outcome = "FAIL"
            msg = f"EXCEPTION: {type(e).__name__}: {e}"
            count = 0

        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⚠️ "}[outcome]
        print(f"\n[{level_id}] {icon} {outcome} — {label}")
        print(f"      {msg}")
        if count and outcome == "PASS":
            print(f"      count: {count}")
        results.append((level_id, outcome, msg, count))

    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print(f"  {'Level':<6} {'Status':<6} {'Count':<6} Label")
    print(f"  {'-'*6} {'-'*6} {'-'*6} {'-'*40}")
    for level_id, outcome, _, count in results:
        label = LEVEL_CONFIG[level_id]["label"]
        print(f"  {level_id:<6} {outcome:<6} {count:<6} {label}")

    passed_n = sum(1 for _, o, _, _ in results if o == "PASS")
    skipped_n = sum(1 for _, o, _, _ in results if o == "SKIP")
    failed_n = sum(1 for _, o, _, _ in results if o == "FAIL")
    total = len(results)
    print()
    print(f"  TOTAL: {total} | PASS: {passed_n} | SKIP: {skipped_n} | FAIL: {failed_n}")

    if failed_n == 0:
        if skipped_n > 0:
            print(f"\n  RESULT: PASS (with {skipped_n} SKIP — set BRAVE_API_KEY in .env to convert SKIP → PASS)")
        else:
            print("\n  RESULT: ALL L0-L11 LEVELS PASS")
        return 0

    print(f"\n  RESULT: {failed_n} LEVEL(S) FAILED — test suite is now honest about broken scrapes")
    if warn_only:
        print("  (--warn mode: exit 0 despite failures)")
        return 0
    return 1


if __name__ == "__main__":
    warn = "--warn" in sys.argv
    sys.exit(_standalone(warn_only=warn))
