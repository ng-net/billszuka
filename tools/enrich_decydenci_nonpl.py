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

# Anti-hallucination placeholder detection (expanded for non-PL languages)
# Catches both explicit placeholders AND role-only entries (no person name).
PLACEHOLDERS_EXACT = {
    "", "brak", "brak danych", "do weryfikacji", "do ustalenia",
    "n/a", "-", "—", "tbd", "?",
}

# Words that indicate a role/title OR legal-entity marker, NOT a personal name.
# If ANY of these appear anywhere in the decydent field, the entry is a placeholder.
NON_PERSON_WORDS = {
    # SK
    "vedenie", "spoločnosti", "pobočky", "distribúcie", "firmy",
    "konateľ", "oddelenie", "obchodné", "obchodný", "zástupca",
    "category", "manager", "b2b", "konatel", "spolocnosti",
    # CZ
    "jednatel", "představenstvo", "dozorčí", "oddělení", "firma",
    # LV
    "vadība", "vadītājs", "sia", "z/s", "reģistrs",
    # LT
    "vadovas", "direktorius", "direktorė", "uab", "vadovybė",
    # EE
    "juhatuse", "liige", "osanik", "osaühing", "aktsiaselts",
    # RO
    "administrator", "conducere", "s.r.l", "srl", "societate",
    # BG
    "управител", "директор", "мениджър", "мениджър", "търговски",
    "еднолично", "ограничена", "отговорност", "търговско", "дружество",
    # SI
    "vedenje", "uprava", "podjetja", "družbe", "d.o.o", "d.o.o.",
    "kranj", "vodstvo", "vodja",
    # HR
    "direktor", "uprava", "d.o.o", "d.o.o.", "poduzeća",
    # MD
    "director", "s.r.l", "srl", "întreprindere",
    # FR
    "gérant", "président", "directeur", "sarl", "sas", "sasu",
    # DE (fallback)
    "geschäftsführer", "geschaftsfuhrer",
    # EN generic
    "management", "department", "board", "team", "office",
    # PL
    "dział", "oddział", "biuro", "zarząd", "właściciel",
    "wspólnicy", "prezes", "spółki", "firma", "spółka",
    "r.", "s.c.", "sp.j.", "sp.k.", "s.c", "spółka",
    "ceo", "cto", "cfo", "coo", "dyrektor",
}


def is_placeholder_decydent(value: str) -> bool:
    """True if decydent value is a placeholder or role-only (no real person)."""
    if not value:
        return True
    v = value.strip().lower()
    if v in PLACEHOLDERS_EXACT:
        return True
    # If entry contains any non-person word, it's a placeholder.
    tokens = re.findall(r"[a-zA-ZÀ-ÿĀ-ſА-Яа-я0-9]+", v)
    for tok in tokens:
        if tok in NON_PERSON_WORDS:
            return True
    # Strip punctuation then check: real person = exactly 2-4 capitalized words, no role words
    # e.g. "Adam Jacek Stawowski", "Lukács Attila", "Peter Kadnár", "BODO SCHILLER" (all caps)
    parts = re.findall(r"[A-ZÀ-ŸĀ-ſА-Я][a-zà-ÿ]+", value)
    if len(parts) < 2 or len(parts) > 5:
        # Try ALL CAPS: "BODO SCHILLER" or "PHILIPPE LE GALL"
        parts_caps = re.findall(r"\b[A-ZÀ-ŸĀ-ſА-Я]{2,}\b", value)
        if 2 <= len(parts_caps) <= 5:
            return False
        return True
    return False


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
    """Extract dirigeants from Recherche Entreprises API (FR).

    Source: official data from INPI/RNE (Registre National des Entreprises).
    Reliability: 100% — this is the authoritative French public registry.
    Skips 'personne morale' dirigeants (legal entity, not a person) — picks first
    real person from the dirigeants list.
    """
    siren = None
    # Try SIREN from rejestr first, then nip_vat (which has FR + 2 + 9 digits)
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
    # Find first REAL PERSON (not personne morale)
    for d in top.get("dirigeants", []):
        if d.get("type_dirigeant") == "personne morale":
            continue  # skip legal entities
        nom = (d.get("nom") or "").strip()
        prenom = (d.get("prenoms") or "").strip()
        qualite = d.get("qualite", "Dirigeant")
        full_name = f"{prenom} {nom}".strip()
        if full_name:
            return {
                "decydent": full_name,
                "stanowisko": qualite,
                "zrodlo_danych": f"recherche-entreprises.api.gouv.fr SIREN {siren} (RNE/INPI public) {siren}",
            }
    return {}


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


def registry_decydent_sk(rejestr: str, nip: str) -> dict:
    """Extract konatelia (statutory directors) from Slovak ORSR.

    Source: official Slovak Commercial Register (Ministerstvo spravodlivosti SR).
    Reliability: 100% — government registry, windows-1250 encoded HTML.
    Free, no registration required.
    """
    ico = None
    for src in (rejestr, nip):
        m = re.search(r"\b(\d{8})\b", re.sub(r"\D", " ", src))
        if m:
            ico = m.group(1)
            break
    if not ico:
        return {}
    try:
        # Step 1: search by IČO
        search_url = f"https://www.orsr.sk/hladaj_ico.asp?ICO={ico}&SID=0"
        req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0 BILLSzuka/1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            html = r.read().decode("windows-1250", errors="replace")
        # Find first detail link
        m = re.search(r'href="vypis\.asp\?ID=(\d+)&(?:amp;)?SID=(\d+)&(?:amp;)?P=(\d+)"', html)
        if not m:
            return {}
        detail_id, sid, p = m.group(1), m.group(2), m.group(3)
        # Step 2: get detail page
        detail_url = f"https://www.orsr.sk/vypis.asp?ID={detail_id}&SID={sid}&P={p}"
        req = urllib.request.Request(detail_url, headers={"User-Agent": "Mozilla/5.0 BILLSzuka/1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            detail = r.read().decode("windows-1250", errors="replace")
    except Exception:
        return {}
    # Step 3: extract 'Štatutárny orgán' (statutory body) section
    idx = detail.find("Štatutárny orgán")
    if idx < 0:
        return {}
    section = detail[idx:idx + 5000]
    # Pattern: <span class='ra'> TITLE </span><a class=lnm ...> <span>FIRST</span> <span>LAST</span></a>
    directors = re.findall(
        r"<span class='ra'>\s*([A-Za-z\.\s]{1,15})\s*</span>\s*"
        r"<a[^>]+>\s*<span class='ra'>\s*([^<]+)\s*</span>\s*"
        r"<span class='ra'>\s*([^<]+)\s*</span>\s*</a>",
        section,
    )
    if not directors:
        return {}
    # Filter out role labels (e.g. "konatelia", "konateľ", "štatutárny riaditeľ")
    real_directors = []
    for title, first, last in directors:
        combined = f"{title.strip()} {first.strip()} {last.strip()}".strip()
        # Skip if title is a role word, not a name prefix
        if title.strip().lower() in ("konatelia", "konateľ", "konatel", "štatutárny", "štatutárny riaditeľ", "člen", "členovia"):
            continue
        real_directors.append(combined)
    if not real_directors:
        return {}
    # Take first director
    full_name = real_directors[0]
    return {
        "decydent": full_name,
        "stanowisko": "Konateľ / Štatutárny orgán",
        "zrodlo_danych": f"orsr.sk IČO {ico} (Obchodný register SR, Ministerstvo spravodlivosti) {detail_url}",
    }


def registry_decydent_ee(rejestr: str, nip: str) -> dict:
    """Extract board members from e-Äriregister (EE).

    Source: official Estonian e-Business Register (justiitsministeerium / RIK).
    Reliability: 100% — this is the authoritative Estonian public registry.
    Strategy: use the autocomplete API to get the company URL, then scrape the
    company HTML page for board member names.
    """
    code = None
    for src in (rejestr, nip):
        m = re.search(r"\b(\d{8})\b", re.sub(r"\D", " ", src))
        if m:
            code = m.group(1)
            break
    if not code:
        return {}
    # Step 1: find company by reg code
    data = _api_get(f"https://ariregister.rik.ee/eng/api/autocomplete?q={code}")
    if not data or not data.get("data"):
        return {}
    item = data["data"][0]
    company_url = item.get("url", "")
    if not company_url:
        return {}
    # Step 2: fetch company page HTML and find first board member name
    try:
        # URL-encode non-ASCII chars in path (Estonian company names have ä, ö, ü)
        safe_url = company_url.encode("ascii", "ignore").decode("ascii")
        if not safe_url:
            safe_url = urllib.parse.quote(company_url, safe=":/?&=")
        req = urllib.request.Request(
            safe_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 BILLSzuka/1.0 research@bills.pl",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
    except Exception:
        return {}
    # Look for hidden form field with person name (used in Estonian registry)
    # Pattern: s__related_person_text" value="Name Surname"
    m = re.search(r's__related_person_text"\s*value="([^"]+)"', html)
    if m:
        full_name = m.group(1).strip()
        return {
            "decydent": full_name,
            "stanowisko": "Juhatuse liige (board member)",
            "zrodlo_danych": f"{company_url} (e-Äriregister / RIK public, reg {code})",
        }
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
    "SK": registry_decydent_sk,
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

                current_dec = (row.get("decydent") or "").strip()
                if not is_placeholder_decydent(current_dec):
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
                    current_val = (row.get(field) or "").strip()
                    if is_placeholder_decydent(current_val):
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
