#!/usr/bin/env python3
"""
_enrich_with_verify.py — Perplexity Sonar via OpenRouter with URL verification.

Workflow:
1. For each placeholder row, query Perplexity Sonar (search-augmented LLM)
   which has real-time web access and returns citations
2. Parse Name / Title / Sources from response
3. For each cited source URL, fetch and check if the name appears in the page
4. ONLY accept if at least one cited source verifies the name

Anti-hallucination: Perplexity Sonar is a search-augmented LLM with real-time
access to current web data, much more accurate than base DeepSeek. Combined with
URL cross-verification, the false positive rate is minimal.
"""
import csv
import json
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR
from enrich_decydenci_nonpl import is_placeholder_decydent
from _verify_url import verify_name_in_url

ISO_TO_FOLDER = {
    "PL": "Polska", "CZ": "Czechy", "SK": "Słowacja", "RO": "Rumunia",
    "LT": "Litwa", "LV": "Łotwa", "EE": "Estonia", "FR": "Francja",
    "MD": "Mołdawia", "BG": "Bułgaria", "SI": "Słowenia", "HR": "Chorwacja",
}
NON_PL = ["CZ", "SK", "RO", "LT", "LV", "EE", "FR", "MD", "BG", "SI", "HR"]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Perplexity Sonar is search-augmented — has real-time web data
DEFAULT_MODEL = "perplexity/sonar"


def get_env() -> dict:
    env = {}
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def query_perplexity(company: str, country: str, city: str, rejestr: str, api_key: str) -> dict:
    """Call Perplexity Sonar via OpenRouter. Returns parsed {name, title, sources} or {}."""
    system = (
        "Find the current CEO, owner, managing director, or general manager of a company. "
        "ALWAYS cite 1-3 source URLs (LinkedIn, official site, registry, news article, Kompass, etc.). "
        "Reply EXACTLY in this format:\n\n"
        "Name: <full name>\n"
        "Title: <position>\n"
        "Sources: <url1>, <url2>, <url3>\n\n"
        "If you cannot find a verifiable person, reply: Name: NOT_FOUND"
    )
    user = (
        f"Company: {company}\n"
        f"Country: {country}\n"
        f"City: {city or 'unknown'}\n"
        f"Registry: {rejestr or 'unknown'}\n\n"
        "Find the current decision-maker (CEO, owner, managing director, general manager). "
        "Provide name, title, and 1-3 source URLs."
    )
    body = json.dumps({
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 400,
        "temperature": 0.0,
    }).encode()
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ng-net/billszuka",
            "X-Title": "BILLSzuka",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
            content = resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return {}
    # Parse
    name_m = re.search(r"Name:\s*([^\n]+)", content)
    title_m = re.search(r"Title:\s*([^\n]+)", content)
    sources_m = re.search(r"Sources:\s*([^\n]+)", content)
    if not name_m:
        return {}
    name = name_m.group(1).strip()
    if name.upper() in ("NOT_FOUND", "UNKNOWN", "N/A", ""):
        return {}
    # Extract URLs
    sources_raw = sources_m.group(1) if sources_m else ""
    urls = re.findall(r"https?://[^\s,;\]]+", sources_raw)
    return {"name": name, "title": title_m.group(1).strip() if title_m else "", "urls": urls}


def find_catalog_for_id(id_unique: str) -> Path | None:
    iso = id_unique.split("-")[0]
    folder = ROOT / "data" / ISO_TO_FOLDER[iso]
    if not folder.exists():
        return None
    for cat in ("A", "B"):
        f = folder / f"catalog-{cat}-{iso}.csv"
        if not f.exists():
            continue
        with f.open("r", encoding="utf-8", newline="") as fp:
            for row in csv.DictReader(fp):
                if row.get("id_unikalne") == id_unique:
                    return f
    return None


def write_update(cfile: Path, id_unique: str, decydent: str, stanowisko: str,
                 zrodlo_danych: str) -> bool:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with cfile.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    modified = False
    for row in rows:
        if row.get("id_unikalne") != id_unique:
            continue
        row["decydent"] = decydent
        row["stanowisko"] = stanowisko
        row["zrodlo_danych"] = zrodlo_danych
        if not row.get("data_weryfikacji"):
            row["data_weryfikacji"] = today
        modified = True
        break
    if not modified:
        return False
    tmp = cfile.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(cfile)
    return True


def main():
    env = get_env()
    api_key = env.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not in .env")
        sys.exit(1)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20, help="Max rows to process")
    parser.add_argument("--country", type=str, default=None, help="ISO code")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written")
    args = parser.parse_args()

    countries = [args.country.upper()] if args.country else NON_PL
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    rows = list(csv.DictReader(open(ROOT / "data/master.csv", encoding="utf-8")))
    targets = [
        r for r in rows
        if r["kraj"] in countries
        and is_placeholder_decydent(r.get("decydent", ""))
    ]
    print(f"Targets: {len(targets)} | limit={args.limit}")
    processed = 0
    verified_count = 0
    rejected_count = 0
    no_source_count = 0
    for row in targets:
        if processed >= args.limit:
            break
        company = (row.get("nazwa_firmy") or "").strip()
        country = row["kraj"]
        city = (row.get("miasto") or "").strip()
        rejestr = (row.get("rejestr_id") or "").strip()
        www = (row.get("www") or "").strip()
        country_name = COUNTRY_MAP.get(country, country)
        id_ = row["id_unikalne"]
        # Step 1: Perplexity Sonar
        result = query_perplexity(company, country_name, city, rejestr, api_key)
        processed += 1
        if not result or not result.get("urls"):
            no_source_count += 1
            print(f"  [NO_SRC]  {id_}: {company[:40]}")
            continue
        # Step 2: Verify against at least one URL
        verified_url = None
        for url in result["urls"][:3]:
            v = verify_name_in_url(result["name"], url)
            if v["verified"]:
                verified_url = (url, v)
                break
        if verified_url:
            verified_count += 1
            url, v = verified_url
            new_zrodlo = f"Perplexity Sonar (OpenRouter) VERIFIED via {url} | match_count={v['match_count']} | conf={v['confidence']} | 2026-08-18"
            print(f"  [✓ OK]    {id_}: {result['name']} ({result.get('title','')[:25]}) | conf={v['confidence']}")
            if not args.dry_run:
                cfile = find_catalog_for_id(id_)
                if cfile:
                    write_update(cfile, id_, result["name"], result.get("title", "N/A"), new_zrodlo)
        else:
            rejected_count += 1
            print(f"  [✗ REJ]   {id_}: {result['name']} ({result.get('title','')[:25]}) | all URLs rejected (LLM hallucination)")
        time.sleep(1.5)
        sys.stdout.flush()
    print(f"\n✅ Processed: {processed} | Verified: {verified_count} | Rejected: {rejected_count} | No source: {no_source_count}")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
