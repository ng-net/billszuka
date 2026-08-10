#!/usr/bin/env python3
"""
apollo_enrich.py — Apollo.io enrichment client for BILLSzuka.

Uses the public Apollo API at api.apollo.io/v1 — no SDK, plain HTTP.
API key read from .env (APOLLO_API).

Main endpoints used:
  POST /v1/people/match            — 1 person by name+company/domain
                                      → email, phone, title, linkedin
  POST /v1/people/bulk_match       — up to 10 people per call
  POST /v1/organizations/enrich    — 1 company by domain
                                      → industry, size, revenue, social
  POST /v1/mixed_people/search     — search by title+seniority+company
                                      size+location (lead generation)

Output dict shapes are documented in each function. All functions return
{"error": "..."} on failure (network, auth, no-match) — never raise.

CLI:
  apollo_enrich.py match "Jan Kowalski" "BISTA STANDARD" --domain bistastandard.pl
  apollo_enrich.py org --domain bistastandard.pl
  apollo_enrich.py search "CEO" --company-size "50,200" --country PL --limit 5
  apollo_enrich.py bulk --csv data/Polska/catalog-B-PL.csv --country PL

Usage as library:
  from apollo_enrich import apollo_match
  result = apollo_match("Jan Kowalski", "BISTA STANDARD", domain="bistastandard.pl")
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_BASE = "https://api.apollo.io/v1"
ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"


def _load_api_key() -> str:
    """Read APOLLO_API from .env. Empty string if missing."""
    if not ENV_FILE.exists():
        return ""
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == "APOLLO_API":
                return v.strip().strip('"').strip("'")
    return ""


def _post(endpoint: str, payload: dict[str, Any], timeout: int = 15) -> dict[str, Any]:
    """POST JSON to Apollo, return parsed response or {"error": "..."}.

    Per Apollo docs (https://docs.apollo.io/reference/authentication):
    - API path: /api/v1/... (not /v1/...)
    - Auth: x-api-key header (not api_key in body)
    - Apollo users: static x-api-key
    - Apollo partners: OAuth 2.0
    """
    api_key = _load_api_key()
    if not api_key:
        return {"error": "APOLLO_API not set in .env"}
    # Note: do NOT include api_key in body — Apollo expects x-api-key header
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/{endpoint.lstrip('/')}",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "x-api-key": api_key,
            "User-Agent": "BILLSzuka-Apollo/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        return {"error": f"HTTP {e.code}: {body}"}
    except (urllib.error.URLError, TimeoutError) as e:
        return {"error": f"connection: {e}"}
    except json.JSONDecodeError as e:
        return {"error": f"json: {e}"}

# Note: Apollo API base path is /api/v1 per docs, but the popular
# /v1/ shorthand also works for some endpoints. We use the documented
# /v1/ for backward compat; health check uses the explicit /v1/auth/health.
API_BASE = "https://api.apollo.io/api/v1"


def apollo_health() -> dict[str, Any]:
    """Check Apollo API health (no auth needed)."""
    req = urllib.request.Request(
        f"{API_BASE}/auth/health",
        headers={"User-Agent": "BILLSzuka-Apollo/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def apollo_match(
    name: str,
    company: str,
    domain: str = "",
    timeout: int = 15,
) -> dict[str, Any]:
    """Find a specific person by name + company.

    Args:
      name:     "Jan Kowalski"
      company:  "BISTA STANDARD" (organization name)
      domain:   optional "bistastandard.pl" — disambiguates when
                company name is generic

    Returns: dict with keys like
      person = {
        "first_name", "last_name", "title", "email", "email_status",
        "linkedin_url", "phone_numbers": [{"number", "type"}],
        "organization": {"name", "domain", "industry", "size", ...}
      }
    On no-match: {"error": "no match", "person": None}
    """
    parts = (name or "").strip().split()
    first = parts[0] if parts else ""
    last = " ".join(parts[1:]) if len(parts) > 1 else ""
    payload: dict[str, Any] = {
        "first_name": first,
        "last_name": last,
        "organization_name": (company or "").strip(),
    }
    if domain:
        payload["domain"] = domain.strip()
    return _post("people/match", payload, timeout=timeout)


def apollo_org(domain: str, timeout: int = 15) -> dict[str, Any]:
    """Enrich a company by domain.

    Returns: dict with keys like
      organization = {
        "name", "domain", "industry", "estimated_num_employees",
        "retail_location_count", "raw_address", "city", "state",
        "country", "linkedin_url", "twitter_url", "facebook_url",
        "phone_number", "founded_year", "publicly_traded_symbol", ...
      }
    """
    if not domain:
        return {"error": "domain is required"}
    return _post("organizations/enrich", {"domain": domain.strip()}, timeout=timeout)


def apollo_search_people(
    title_keywords: list[str] | None = None,
    company_size_min: int = 0,
    company_size_max: int = 0,
    country: str = "",
    domain: str = "",
    limit: int = 10,
    timeout: int = 30,
) -> dict[str, Any]:
    """Search for people matching filters (Apollo /v1/mixed_people/search).

    Args:
      title_keywords: ["CEO", "owner", "managing director"]
      company_size_min/max: 0 means no filter; otherwise use Apollo's
        employee_ranges buckets ("1,10", "11,50", "51,200", "201,500",
        "501,1000", "1001,2000", "2001,5000", "5001,10000", "10001+")
      country: ISO code "PL", "CZ", ...
      domain: limit to a specific company
      limit: 1-100 (Apollo default is 25; 0 = use default)
    """
    payload: dict[str, Any] = {"per_page": limit or 10}
    if title_keywords:
        payload["person_titles"] = title_keywords
    if domain:
        payload["q_organization_domains"] = domain
    if country:
        payload["person_locations"] = [country]
    if company_size_min or company_size_max:
        # Apollo uses inclusive ranges; pass a single bucket if min==max
        if company_size_min == company_size_max:
            payload["person_seniorities"] = []  # not strictly size, but helper
            payload["organization_num_employees_ranges"] = [f"{company_size_min},{company_size_max}"]
        else:
            payload["organization_num_employees_ranges"] = [f"{company_size_min},{company_size_max}"]
    return _post("mixed_people/search", payload, timeout=timeout)


# ---------------------------------------------------------------------------
# BILLSzuka-specific helpers
# ---------------------------------------------------------------------------

# Polish decision-maker titles
PL_DECISION_TITLES = [
    "CEO", "Prezes", "Prezes Zarządu", "Właściciel", "Dyrektor",
    "Managing Director", "General Manager", "Head of Sales",
    "Kierownik Sprzedaży", "Sales Director", "Commercial Director",
]


def derive_domain(company: str, www: str = "") -> str:
    """Extract domain from company name (heuristic) or www field."""
    if www:
        m = re.search(r"https?://(?:www\.)?([^/]+)", www)
        if m:
            return m.group(1).lower()
    # Polish company suffix cleanup
    s = (company or "").lower()
    for suf in (" sp. z o.o.", " sp. z o. o.", " s.a.", " sa", " sp.j.",
                " sp.k.", " s.c.", " sc", " spółka z ograniczoną odpowiedzialnością",
                " spółka akcyjna", " spółka jawna", " spółka komandytowa"):
        s = s.replace(suf, "")
    s = re.sub(r"[\"\'\(\)\.,]", "", s)
    s = re.sub(r"\s+", "", s)
    s = s.replace("ł", "l").replace("ą", "a").replace("ć", "c")
    s = s.replace("ę", "e").replace("ń", "n").replace("ó", "o")
    s = s.replace("ś", "s").replace("ź", "z").replace("ż", "z")
    return f"{s}.pl" if s else ""


def enrich_csv_row(row: dict[str, str], timeout: int = 15) -> dict[str, Any]:
    """Enrich a single CSV row from data/{Kraj}/catalog-*.csv.

    Uses:
      - nip_vat → domain discovery (via company name heuristic)
      - nazwa_firmy → apollo_match against decydent + stanowisko
      - www → apollo_org (if not already a domain)
    """
    company = (row.get("nazwa_firmy") or "").strip()
    www = (row.get("www") or "").strip()
    decydent = (row.get("decydent") or "").strip()
    stanowisko = (row.get("stanowisko") or "").strip()

    domain = derive_domain(company, www)

    out: dict[str, Any] = {"company": company, "domain": domain, "matched": False}

    # 1. Enrich company
    if domain:
        org = apollo_org(domain, timeout=timeout)
        if not org.get("error") and org.get("organization"):
            o = org["organization"]
            out["industry"] = o.get("industry")
            out["employees"] = o.get("estimated_num_employees")
            out["phone"] = o.get("phone_number")
            out["linkedin"] = o.get("linkedin_url")
            out["city"] = o.get("city")
            out["country"] = o.get("country")
            out["org_matched"] = True
        else:
            out["org_error"] = org.get("error")

    # 2. Enrich decision-maker
    if decydent and company:
        match = apollo_match(decydent, company, domain=domain, timeout=timeout)
        if not match.get("error") and match.get("person"):
            p = match["person"]
            out["decydent_email"] = p.get("email")
            out["decydent_email_status"] = p.get("email_status")
            out["decydent_phone"] = (
                p.get("phone_numbers", [{}])[0].get("number")
                if p.get("phone_numbers")
                else None
            )
            out["decydent_linkedin"] = p.get("linkedin_url")
            out["decydent_title_actual"] = p.get("title")
            out["matched"] = True
        else:
            out["match_error"] = match.get("error")

    return out


def bulk_enrich_csv(csv_path: Path, country: str = "", limit: int = 0, timeout: int = 15) -> list[dict[str, Any]]:
    """Enrich every row in a BILLSzuka catalog CSV. Returns list of results."""
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if country:
        rows = [r for r in rows if (r.get("kraj") or "").upper() == country.upper()]
    if limit:
        rows = rows[:limit]
    results: list[dict[str, Any]] = []
    for i, row in enumerate(rows, 1):
        id_ = (row.get("id_unikalne") or "").strip()
        name = (row.get("nazwa_firmy") or "").strip()
        print(f"  [{i}/{len(rows)}] {id_} {name[:30]:30s}", file=sys.stderr)
        r = enrich_csv_row(row, timeout=timeout)
        r["id_unikalne"] = id_
        r["nazwa_firmy"] = name
        results.append(r)
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage:")
        print("  apollo_enrich.py health")
        print("  apollo_enrich.py match 'Jan Kowalski' 'BISTA STANDARD' [--domain ...]")
        print("  apollo_enrich.py org --domain bistastandard.pl")
        print("  apollo_enrich.py search 'CEO;Owner' [--domain ...] [--country PL] [--limit 5]")
        print("  apollo_enrich.py bulk --csv data/Polska/catalog-B-PL.csv [--country PL] [--limit 3]")
        return 1
    cmd = sys.argv[1]
    if cmd == "health":
        print(json.dumps(apollo_health(), indent=2))
        return 0
    if cmd == "match":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        company = sys.argv[3] if len(sys.argv) > 3 else ""
        domain = ""
        if "--domain" in sys.argv:
            i = sys.argv.index("--domain")
            if i + 1 < len(sys.argv):
                domain = sys.argv[i + 1]
        print(json.dumps(apollo_match(name, company, domain=domain), indent=2))
        return 0
    if cmd == "org":
        domain = ""
        if "--domain" in sys.argv:
            i = sys.argv.index("--domain")
            domain = sys.argv[i + 1]
        print(json.dumps(apollo_org(domain), indent=2))
        return 0
    if cmd == "search":
        titles = []
        if len(sys.argv) > 2:
            titles = sys.argv[2].split(";")
        domain = ""
        country = ""
        limit = 10
        if "--domain" in sys.argv:
            i = sys.argv.index("--domain")
            domain = sys.argv[i + 1]
        if "--country" in sys.argv:
            i = sys.argv.index("--country")
            country = sys.argv[i + 1]
        if "--limit" in sys.argv:
            i = sys.argv.index("--limit")
            limit = int(sys.argv[i + 1])
        print(json.dumps(
            apollo_search_people(titles, country=country, domain=domain, limit=limit),
            indent=2,
        ))
        return 0
    if cmd == "bulk":
        csv_path = None
        country = ""
        limit = 0
        if "--csv" in sys.argv:
            i = sys.argv.index("--csv")
            csv_path = Path(sys.argv[i + 1])
        if "--country" in sys.argv:
            i = sys.argv.index("--country")
            country = sys.argv[i + 1]
        if "--limit" in sys.argv:
            i = sys.argv.index("--limit")
            limit = int(sys.argv[i + 1])
        if not csv_path or not csv_path.exists():
            print(f"CSV not found: {csv_path}")
            return 1
        results = bulk_enrich_csv(csv_path, country=country, limit=limit)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0
    print(f"Unknown command: {cmd}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
