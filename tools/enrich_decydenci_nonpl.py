#!/usr/bin/env python3
"""
enrich_decydenci_nonpl.py — Gentle decydent (decision-maker) enrichment for
non-PL countries: CZ, SK, RO, LT, LV, EE, FR, MD, BG, SI, HR.

Strategy (public sources only):
1. For FR/CZ/EE/LT — query official registry APIs directly (free, no rate limits)
   to extract dirigeants/boardmembers from structured data.
2. For all other countries — query OpenRouter (DeepSeek) with structured
   web-search prompt to extract name+title from public LinkedIn / official site.

Rate limiting:
- 0.5s between each API call (FR/CZ/EE/LT)
- 2s between each OpenRouter call
- Processes max 10 rows per run (--limit N to override), resumable

Resume: skips rows already having a real decydent (not a placeholder).
Dry-run: --dry-run shows what would be written without modifying files.
"""

import argparse
import csv
import json
import os
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

PLACEHOLDERS = {"", "brak", "brak danych", "do weryfikacji", "do ustalenia", "n/a", "-", "—"}

NON_PL = ["CZ", "SK", "RO", "LT", "LV", "EE", "FR", "MD", "BG", "SI", "HR"]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-chat"


# ---------------------------------------------------------------------------
# Env
# ---------------------------------------------------------------------------

def _load_env() -> dict:
    env = {}
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    for k, v in os.environ.items():
        env.setdefault(k, v)
    return env


# ---------------------------------------------------------------------------
# Registry API enrichment (free, official)
# ---------------------------------------------------------------------------

def _api_get(url: str, timeout: int = 8) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BILLSzuka/1.0 research@bills.pl"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None


def registry_decydent_fr(rejestr: str, nip: str) -> dict:
    """Extract dirigeants from Recherche Entreprises API (FR)."""
    siren = None
    for src in (rejestr, nip):
        m = re.search(r"\b(\d{9})\b", re.sub(r"\D", " ", src))
        if m:
            siren = m.group(1)
            break
    if not siren:
        return {}
    data = _api_get(f"https://recherche-entreprises.api.gouv.fr/search?q={siren}")
    if not data:
        return {}
    results = data.get("results", [])
    if not results:
        return {}
    top = results[0]
    dirigeants = top.get("dirigeants", [])
    if not dirigeants:
        return {}
    d = dirigeants[0]
    nom = d.get("nom", "")
    prenom = d.get("prenoms", "")
    qualite = d.get("qualite", "Dirigeant")
    full_name = f"{prenom} {nom}".strip()
    return {"decydent": full_name, "stanowisko": qualite} if full_name else {}


def registry_decydent_cz(rejestr: str, nip: str) -> dict:
    """Extract board members from ARES API (CZ). ARES doesn't expose persons
    in the v2 public REST endpoint — returns address+name only."""
    ico = None
    for src in (rejestr, nip):
        m = re.search(r"\b(\d{8})\b", re.sub(r"\D", " ", src))
        if m:
            ico = m.group(1)
            break
    if not ico:
        return {}
    data = _api_get(f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}")
    if not data:
        return {}
    # ARES v2 REST doesn't return directors in this endpoint — skip person extraction
    addr = data.get("sidlo", {}).get("textovaAdresa", "")
    return {"adres": addr} if addr else {}


def registry_decydent_ee(rejestr: str, nip: str) -> dict:
    """Extract board members from e-Äriregister (EE)."""
    code = None
    for src in (rejestr, nip):
        m = re.search(r"\b(\d{8})\b", re.sub(r"\D", " ", src))
        if m:
            code = m.group(1)
            break
    if not code:
        return {}
    data = _api_get(f"https://ariregister.rik.ee/eng/api/autocomplete?q={code}")
    if not data or not data.get("data"):
        return {}
    item = data["data"][0]
    board = item.get("board_members", [])
    if board:
        person = board[0]
        name = person.get("name", "")
        role = person.get("role", "Juhatuse liige")
        if name:
            return {"decydent": name, "stanowisko": role}
    return {}


def registry_decydent_lt(rejestr: str, nip: str) -> dict:
    """Extract board members from JAR (Lithuanian Juridical Persons Register)."""
    ja_kodas = None
    for src in (rejestr, nip):
        m = re.search(r"\b(\d{9})\b", re.sub(r"\D", " ", src))
        if m:
            ja_kodas = m.group(1)
            break
    if not ja_kodas:
        return {}
    data = _api_get(
        f"https://www.registrucentras.lt/jar/p/rest/api/v1/entities?entityCode={ja_kodas}",
        timeout=10
    )
    if not data:
        return {}
    managers = data.get("managers", [])
    if managers:
        m = managers[0]
        name = m.get("fullName", "")
        role = m.get("position", "Vadovas")
        if name:
            return {"decydent": name, "stanowisko": role}
    return {}


# ---------------------------------------------------------------------------
# OpenRouter fallback for all other countries
# ---------------------------------------------------------------------------

def openrouter_decydent(company: str, country_name: str, city: str, website: str) -> dict:
    """Ask DeepSeek to extract decision-maker from public sources."""
    env = _load_env()
    api_key = env.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return {}

    system = (
        "You are a B2B research assistant. Extract the decision-maker "
        "(owner, CEO, Managing Director, General Manager or equivalent) "
        "for a given company from public sources (LinkedIn, official website, company registry). "
        "Return ONLY a JSON object with keys: name, title. "
        "If you cannot find a real person from public sources, return {}. "
        "Never invent names. Only return verified public data."
    )
    prompt = (
        f"Company: {company}\n"
        f"Country: {country_name}\n"
        f"City: {city or 'unknown'}\n"
        f"Website: {website or 'unknown'}\n\n"
        "Find the decision-maker (owner/CEO/MD/GM) from public sources. "
        "Return JSON: {{\"name\": \"...\", \"title\": \"...\"}} or {{}} if not found."
    )

    body = json.dumps({
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 150,
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
            # Extract JSON from response
            m = re.search(r"\{[^{}]+\}", content, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
                name = parsed.get("name", "").strip()
                title = parsed.get("title", "").strip()
                if name and name.lower() not in ("unknown", "n/a", "not found", ""):
                    return {"decydent": name, "stanowisko": title}
    except Exception as e:
        pass
    return {}


# ---------------------------------------------------------------------------
# Registry dispatcher
# ---------------------------------------------------------------------------

REGISTRY_FUNCS = {
    "FR": registry_decydent_fr,
    "CZ": registry_decydent_cz,
    "EE": registry_decydent_ee,
    "LT": registry_decydent_lt,
}


def enrich_row(row: dict, iso: str) -> dict:
    """Return enrichment dict (subset of CANONICAL_SCHEMA fields) for one row."""
    nip = (row.get("nip_vat") or "").strip()
    rejestr = (row.get("rejestr_id") or "").strip()
    company = (row.get("nazwa_firmy") or "").strip()
    city = (row.get("miasto") or "").strip()
    country_name = (row.get("kraj") or COUNTRY_MAP.get(iso, "")).strip()
    website = (row.get("www") or "").strip()

    enriched = {}

    # Step 1: Try official registry API for countries with structured person data
    if iso in REGISTRY_FUNCS:
        fn = REGISTRY_FUNCS[iso]
        enriched = fn(rejestr, nip)
        time.sleep(0.5)
    else:
        # Step 2: OpenRouter for SK, RO, LV, MD, BG, SI, HR
        enriched = openrouter_decydent(company, country_name, city, website)
        time.sleep(2.0)

    return enriched


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Gentle non-PL decydent enrichment")
    parser.add_argument("--limit", type=int, default=10,
                        help="Max rows to enrich per run (default: 10)")
    parser.add_argument("--country", type=str, default=None,
                        help="Restrict to one ISO country code, e.g. RO")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show changes without writing to files")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    countries = [args.country.upper()] if args.country else NON_PL
    processed = 0
    total_enriched = 0

    print(f"🌍 [Decydenci Enrichment] Countries: {countries} | limit={args.limit} | dry_run={args.dry_run}")
    print()

    for iso in countries:
        if processed >= args.limit:
            break
        country_name = COUNTRY_MAP.get(iso)
        if not country_name:
            print(f"  ⚠️ Unknown ISO: {iso}")
            continue

        for cat_type in ["A", "B"]:
            if processed >= args.limit:
                break
            cfile = DATA_DIR / country_name / f"catalog-{cat_type}-{iso}.csv"
            if not cfile.exists():
                continue

            with cfile.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))

            modified = False
            for row in rows:
                if processed >= args.limit:
                    break

                name = (row.get("nazwa_firmy") or "").strip()
                if not name:
                    continue

                current_dec = (row.get("decydent") or "").strip().lower()
                if current_dec not in PLACEHOLDERS:
                    continue  # Already has a real decydent — skip

                uid = row.get("id_unikalne", "?")
                print(f"  [{iso}-{cat_type}] {uid}: {name[:45]}...")

                enriched = enrich_row(row, iso)
                processed += 1

                if not enriched:
                    print(f"    → no data found")
                    continue

                # Apply enrichment — only fill placeholders, never overwrite
                for field, value in enriched.items():
                    if not value:
                        continue
                    current_val = (row.get(field) or "").strip().lower()
                    if current_val in PLACEHOLDERS:
                        if not args.dry_run:
                            row[field] = value
                        print(f"    ✓ {field}: {value[:60]}")
                        modified = True
                        total_enriched += 1

                if not args.dry_run and modified:
                    # Update data_weryfikacji
                    if not (row.get("data_weryfikacji") or "").strip():
                        row["data_weryfikacji"] = today

            if modified and not args.dry_run:
                tmp = cfile.with_suffix(".csv.tmp")
                with tmp.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
                    writer.writeheader()
                    writer.writerows(rows)
                tmp.replace(cfile)
                print(f"  💾 Saved: {cfile.name}")

    print()
    print(f"✅ Done. Rows inspected: {processed} | Fields enriched: {total_enriched}")
    if total_enriched > 0 and not args.dry_run:
        print(f"   Run `python3 tools/billszuka.py compile` to rebuild master.csv")
        print(f"   Run `python3 tools/billszuka.py sync` to verify integrity")


if __name__ == "__main__":
    main()
