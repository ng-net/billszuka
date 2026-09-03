#!/usr/bin/env python3
"""
registry_lookup.py — Unified free public-registry lookup across 9 countries.

Wraps the most-used free corporate registries so a single CLI call returns
official company data (name, address, status, NACE/CAEN code, board members,
foundation date). Designed for "registry-first" workflow in lead research.

Currently supports (free, no auth):
  - CZ: ARES REST API (https://ares.gov.cz)
  - SK: ORSR web search fallback (no public API)
  - EE: ARIREGISTER (https://ariregister.rik.ee)
  - LT: get.data.gov.lt open data (JAR registruoti)
  - LV: Lursoft (paid) → fallback to info.ur.gov.lv (no public API)
  - RO: termene.ro / listafirme.ro (no public API, but web_search usable)
  - HR: sudreg.pravosudje.hr (no public API)
  - BG: companybook.bg (no public API)
  - SI: AJPES (no public API, maticna.posta.si)
  - RS: companywall.rs (no public API)
  - MD: cis.gov.md / infobiz.md (no public API)

For countries without public APIs (most of them), this tool returns
"NO_API" status with the URL to query manually. This is a deliberate
fallback so the agent can still do registry-first work via web_fetch.

Usage:
  python3 tools/registry_lookup.py --country CZ --ico 63489821
  python3 tools/registry_lookup.py --country EE --name "Stimbar" --autocomplete
  python3 tools/registry_lookup.py --country LT --ja_kodas 303182002
  python3 tools/registry_lookup.py --country SK --ico 53070992    # → NO_API + URL
  python3 tools/registry_lookup.py --batch lookups.json
  python3 tools/registry_lookup.py --supported   # list countries

Output (one country):
  {
    "country": "CZ",
    "ico": "63489821",
    "name": "Tabák Plus, spol. s r.o.",
    "address": "Nové sady 606/40, 602 00 Brno",
    "status": "AKTIVNI",
    "legal_form": "Společnost s ručením omezeným",
    "nace": ["46350"],
    "founded": "1996-01-31",
    "source": "ARES",
    "url": "https://ares.gov.cz/...",
    "raw": {...}
  }
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "BILLSzuka-Research/1.0 (Marceli; bills@op.pl)"

# Registry URLs (for countries with no API, we provide a manual URL)
REGISTRY_URLS = {
    "SK": "https://www.orsr.sk/search_subjekt.asp?lan=en",
    "LV": "https://info.ur.gov.lv/",
    "RO": "https://termene.ro/",
    "HR": "https://sudreg.pravosudje.hr/ords/f?p=148:1",
    "BG": "https://companybook.bg/",
    "SI": "https://www.ajpes.si/prs/",
    "RS": "https://www.companywall.rs/",
    "MD": "https://infobiz.md/",
}


def http_get_json(url: str, timeout: int = 15) -> dict:
    """GET request returning JSON or {} on error."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        return {"_error": str(e)}


def http_get_text(url: str, timeout: int = 15) -> str:
    """GET request returning raw text or '' on error."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as e:
        return ""


# === Country-specific lookups ===

def lookup_cz(ico: str) -> dict:
    """Czech ARES REST API: by IČO (8 digits)."""
    ico = re.sub(r"\D", "", ico)[:8]
    if not ico:
        return {"_error": "invalid ICO"}
    url = f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}"
    data = http_get_json(url)
    if not data or data.get("_error"):
        return {"country": "CZ", "ico": ico, "status": "NOT_FOUND",
                "url": f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}",
                "raw": data}
    sidlo = data.get("sidlo", {})
    address = ", ".join(filter(None, [
        sidlo.get("nazevUlice"), str(sidlo.get("cisloDomovni", "")),
        sidlo.get("nazevMestskeCastiObvodu"), str(sidlo.get("psc", "")),
        sidlo.get("nazevObce")
    ])).strip(", ")
    return {
        "country": "CZ", "ico": ico,
        "name": data.get("obchodniJmeno"),
        "ico_verified": data.get("ico"),
        "address": address,
        "legal_form": data.get("pravniForma"),
        "founded": data.get("datumVzniku"),
        "nace": data.get("czNace2008", []),
        "dic": data.get("dic"),
        "status": "AKTIVNI" if data.get("dttFrom") is None else "HISTORICAL",
        "source": "ARES",
        "url": f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}",
        "raw": data,
    }


def lookup_cz_autocomplete(name: str) -> list:
    """ARES autocomplete by name (returns multiple matches)."""
    url = f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat?obchodniJmeno={urllib.parse.quote(name)}&start=0&pocet=10"
    data = http_get_json(url)
    if not data or data.get("_error") or "ekonomickeSubjekty" not in data:
        return []
    return [{"ico": s.get("ico"), "name": s.get("obchodniJmeno"),
             "address": s.get("sidlo", {}).get("textovaAdresa")}
            for s in data["ekonomickeSubjekty"]]


def lookup_ee(registry_code: str = "", name: str = "") -> dict:
    """Estonian ARIREGISTER: by registry code (KMKR 8 digits) or name autocomplete."""
    base = "https://ariregister.rik.ee/est"
    if registry_code:
        # KMKR = 8 digits
        rc = re.sub(r"\D", "", registry_code)[:8]
        if not rc:
            return {"_error": "invalid registry code"}
        # Detail URL
        html = http_get_text(f"{base}/autoregister?reg_code={rc}")
        if "Ei leitud" in html or "not found" in html.lower():
            return {"country": "EE", "registry_code": rc, "status": "NOT_FOUND",
                    "url": f"{base}/autoregister?reg_code={rc}"}
        return {"country": "EE", "registry_code": rc, "status": "OK",
                "url": f"{base}/autoregister?reg_code={rc}",
                "note": "parse the HTML for name/address/NACE/EMTAK"}
    if name:
        url = f"{base}/api/autocomplete?q={urllib.parse.quote(name)}"
        data = http_get_json(url)
        if not data or data.get("_error"):
            return []
        return data  # list of {name, registry_code, ...}
    return {"_error": "specify --registry-code or --name"}


def lookup_lt(ja_kodas: str) -> dict:
    """Lithuanian get.data.gov.lt: JAR registruoti by įmonės kodas (9 digits)."""
    jk = re.sub(r"\D", "", ja_kodas)[:9]
    if not jk or len(jk) != 9:
        return {"_error": "invalid JA kodas (need 9 digits)"}
    url = (f"https://get.data.gov.lt/datasets/gov/rc/jar/iregistruoti/JuridinisAsmuo"
           f"?ja_kodas={jk}")
    data = http_get_json(url)
    if not data or data.get("_error"):
        return {"country": "LT", "ja_kodas": jk, "status": "NOT_FOUND",
                "url": url}
    # Response shape: {"_data": [{ja_kodas, ja_pavadinimas, ...}], "_page": {...}}
    rows = data.get("_data", data) if isinstance(data, dict) else data
    if isinstance(rows, list) and rows:
        feat = rows[0]
        # NACE codes live in a separate dataset (VeiklosRusys) — would need join.
        # For now, return what we have.
        return {
            "country": "LT", "ja_kodas": jk,
            "name": feat.get("ja_pavadinimas"),
            "address": feat.get("pilnas_adresas") or feat.get("adresas"),
            "legal_form_id": feat.get("forma", {}).get("_id"),
            "status_id": feat.get("statusas", {}).get("_id"),
            "founded": feat.get("reg_data"),
            "closed": feat.get("isreg_data"),
            "source": "get.data.gov.lt (JAR)",
            "url": url,
            "raw": feat,
        }
    return {"country": "LT", "ja_kodas": jk, "status": "NOT_FOUND", "url": url}


def lookup_no_api(country: str, query: str) -> dict:
    """Fallback for countries with no public API: return manual URL + advice."""
    if country not in REGISTRY_URLS:
        return {"_error": f"unsupported country: {country}"}
    return {
        "country": country, "status": "NO_API",
        "query": query,
        "url": REGISTRY_URLS[country],
        "note": (f"No public API for {country}. Use web_search with operator "
                 f"'site:{REGISTRY_URLS[country].split('/')[2]} {query}' "
                 f"or web_fetch to scrape the registry page directly.")
    }


# === Dispatcher ===

def lookup(country: str, **kwargs) -> dict:
    country = country.upper()
    if country == "CZ":
        if "name" in kwargs:
            res = lookup_cz_autocomplete(kwargs["name"])
            return {"country": "CZ", "results": res, "source": "ARES"}
        return lookup_cz(kwargs.get("ico", kwargs.get("id", "")))
    if country == "EE":
        return lookup_ee(registry_code=kwargs.get("registry_code", ""),
                          name=kwargs.get("name", ""))
    if country == "LT":
        return lookup_lt(kwargs.get("ja_kodas", kwargs.get("id", "")))
    if country in REGISTRY_URLS:
        q = kwargs.get("name") or kwargs.get("ico") or kwargs.get("id", "")
        return lookup_no_api(country, q)
    return {"_error": f"unsupported country: {country}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", help="ISO country code (CZ, EE, LT, SK, ...)")
    ap.add_argument("--ico", help="ICO / IČO / NIP / CUI / IČ DPH / etc.")
    ap.add_argument("--id", help="Generic ID field (alias for ico)")
    ap.add_argument("--ja-kodas", help="LT: įmonės kodas (9 digits)")
    ap.add_argument("--registry-code", help="EE: KMKR (8 digits)")
    ap.add_argument("--name", help="Name (autocomplete for some countries)")
    ap.add_argument("--autocomplete", action="store_true",
                    help="Name search (returns multiple matches)")
    ap.add_argument("--batch", help="JSON file with [{country, ...}, ...]")
    ap.add_argument("--supported", action="store_true",
                    help="List supported countries")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    if args.supported:
        print("Countries with free public API:")
        print("  CZ — ARES (https://ares.gov.cz)")
        print("  EE — ARIREGISTER (https://ariregister.rik.ee)")
        print("  LT — get.data.gov.lt (JAR)")
        print()
        print("Countries without API (manual lookup via web_search):")
        for c, u in REGISTRY_URLS.items():
            print(f"  {c} — {u}")
        return

    if args.batch:
        with open(args.batch) as f:
            batch = json.load(f)
        results = [lookup(item.get("country", ""), **{k: v for k, v in item.items()
                                                          if k != "country"})
                    for item in batch]
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for r in results:
                print(f"{r.get('country','?')}\t{r.get('status','?')}\t"
                      f"{r.get('name', r.get('query',''))[:60]}")
        return

    if not args.country:
        print("Usage: --country CZ --ico 63489821  OR  --supported", file=sys.stderr)
        sys.exit(2)

    kwargs = {}
    if args.ico: kwargs["ico"] = args.ico
    if args.id: kwargs["id"] = args.id
    if args.ja_kodas: kwargs["ja_kodas"] = args.ja_kodas
    if args.registry_code: kwargs["registry_code"] = args.registry_code
    if args.name: kwargs["name"] = args.name
    r = lookup(args.country, **kwargs)
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
