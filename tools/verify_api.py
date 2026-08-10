#!/usr/bin/env python3
"""
verify_api.py — Live registry verification for BILLSzuka rows.

For each row with a NIP, calls the appropriate registry API and updates
the row's flagi/status based on whether the API confirms the firm details.

Supported registries:
  PL: CEIDG v3 (https://dane.biznes.gov.pl/api/ceidg/v3/firmy)
      — needs CEIDG_API_TOKEN from .env
  CZ: ARES (https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ICO})
      — no auth

Other countries: stub (returns None; verify_run.py will mark as DO-WERYFIKACJI).

Usage:
  python3 tools/verify_api.py --country PL
  python3 tools/verify_api.py --all

Env: reads .env for CEIDG_API_TOKEN.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ENV_FILE = ROOT / ".env"

CEIDG_BASE = "https://dane.biznes.gov.pl/api/ceidg/v3/firmy"
ARES_BASE = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty"
KRS_BASE = "https://api-krs.ms.gov.pl/api/krs/OdpisAktualny"


def log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def load_env() -> dict:
    env = {}
    if not ENV_FILE.exists():
        return env
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def krs_lookup(krs: str) -> dict | None:
    """Query KRS API by KRS number. Returns firm record dict or None.
    KRS is for sp. z o.o. and other legal entities; CEIDG is for JDG (sole proprietors).
    """
    krs_clean = re.sub(r"\D", "", krs)
    if not re.match(r"^\d{10}$", krs_clean):
        krs_clean = krs_clean.zfill(10)
    url = f"{KRS_BASE}/{krs_clean}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
        odpis = data.get("odpis", {})
        dane = odpis.get("dane", {})
        if not dane:
            return {"error": "KRS: pusta odpowiedź"}
        d1 = dane.get("dzial1", {})
        dp = d1.get("danePodmiotu", {})
        ident = dp.get("identyfikatory", {})
        siedziba = d1.get("siedzibaIAdres", {})
        adres = siedziba.get("adres", {})
        return {
            "nazwa": dp.get("nazwa", ""),
            "nip": ident.get("nip", ""),
            "regon": ident.get("regon", ""),
            "adres": " ".join(filter(None, [
                adres.get("kodPocztowy", ""),
                adres.get("miejscowosc", ""),
                adres.get("ulica", ""),
                adres.get("nrDomu", ""),
            ])),
            "forma_prawna": dp.get("formaPrawna", ""),
            "data_rejestracji": odpis.get("naglowekA", {}).get("dataRejestracjiWKRS", ""),
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": "KRS: nie znaleziono"}
        return {"error": f"KRS HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": f"KRS request failed: {e}"}


def ceidg_lookup(nip: str, token: str) -> dict | None:
    """Query CEIDG v3 by NIP. Returns firm record dict or None."""
    nip_clean = re.sub(r"^[A-Z]{2}", "", nip).strip()
    if not re.match(r"^\d{10}$", nip_clean):
        return {"error": f"NIP PL nieprawidłowy: {nip}"}
    url = f"{CEIDG_BASE}?nip={nip_clean}&status=AKTYWNY"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        firms = data.get("firmy", [])
        if not firms:
            return {"error": "Brak aktywnej firmy dla tego NIP"}
        firm = firms[0]
        adres = firm.get("adresDzialalnosci", {}) or firm.get("adresKorespondencyjny", {}) or {}
        wlasciciel = firm.get("wlasciciel", {}) or {}
        return {
            "nazwa": firm.get("nazwa", ""),
            "nip": wlasciciel.get("nip", "") or firm.get("nip", ""),
            "regon": wlasciciel.get("regon", "") or firm.get("regon", ""),
            "adres": " ".join(filter(None, [
                adres.get("kod", ""),
                adres.get("miasto", ""),
                adres.get("ulica", ""),
                adres.get("budynek", ""),
            ])),
            "status": firm.get("status", ""),
            "pkd": "",
        }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": f"Request failed: {e}"}


def ares_lookup(ico: str) -> dict | None:
    """Query ARES by IČO. Returns firm record dict or None.

    ARES v3 API returns camelCase keys (obchodniJmeno, ico, sidlo, ...)
    v2 returned PascalCase (ObchodniJmeno, ICO, Sidlo, ...) — we support both.
    """
    ico_clean = re.sub(r"^[A-Z]{2}", "", ico).strip()
    if not re.match(r"^\d{8}$", ico_clean):
        return {"error": f"IČO CZ nieprawidłowe: {ico}"}
    url = f"{ARES_BASE}/{ico_clean}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
        # Normalize keys — try lowercase first (v3), then PascalCase (v2)
        if "obchodniJmeno" in data:
            sidlo = data.get("sidlo", {})
            return {
                "nazwa": data.get("obchodniJmeno", ""),
                "ico": data.get("ico", ""),
                "dic": data.get("dic", ""),
                "adres": f"{sidlo.get('nazevObce', '')}, {sidlo.get('nazevUlice', '')} {sidlo.get('cisloPopisne', '')}",
                "pravni_forma": data.get("pravniForma", ""),
                "datum_vzniku": data.get("datumVzniku", ""),
            }
        if "ObchodniJmeno" in data:
            sidlo = data.get("Sidlo", {})
            return {
                "nazwa": data.get("ObchodniJmeno", ""),
                "ico": data.get("ICO", ""),
                "dic": data.get("DIC", ""),
                "adres": f"{sidlo.get('NazevObce', '')}, {sidlo.get('NazevUlice', '')} {sidlo.get('CisloPopisne', '')}",
                "pravni_forma": data.get("PravniForma", ""),
                "datum_vzniku": data.get("DatumVzniku", ""),
            }
        return {"error": "Brak firmy dla tego IČO"}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": "IČO nie istnieje w ARES"}
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": f"Request failed: {e}"}


def ares_search(name: str) -> dict | None:
    """Query ARES by company name. Returns top match dict or None.

    Uses POST /ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat.
    Returns same shape as ares_lookup() but fetched from a name search.
    """
    if not name or len(name) < 2:
        return {"error": "Nazwa za krótka"}
    url = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = json.dumps({"obchodniJmeno": name}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        subs = data.get("ekonomickeSubjekty", [])
        if not subs:
            return None  # brak wyników
        s = subs[0]
        sidlo = s.get("sidlo", {})
        return {
            "nazwa": s.get("obchodniJmeno", ""),
            "ico": s.get("ico", ""),
            "adres": sidlo.get("textovaAdresa", ""),
            "kod_obce": sidlo.get("kodObce", ""),
            "pocet_vysledku": data.get("pocetCelkem", 0),
        }
    except Exception as e:
        return {"error": f"ARES search failed: {e}"}


def ares_enrich(row: dict) -> tuple[str, str]:
    """For a CZ row missing IČO — try ARES search by name.

    Returns (status, reason) like other verify functions.
    Updates the row dict in-place if found.
    """
    name = (row.get("nazwa_firmy") or "").strip()
    if not name:
        return "DO-WERYFIKACJI", "Brak nazwy"
    # Wyczyść nazwę
    clean = name
    for suf in [" s.r.o.", " a.s.", " k.s.", " v.o.s."]:
        clean = clean.replace(suf, "")
    clean = clean.split("(")[0].strip()
    if not clean:
        return "DO-WERYFIKACJI", "Nazwa nie do przetworzenia"

    res = ares_search(clean)
    if not res:
        # Próba z pierwszym słowem
        first = clean.split()[0] if clean else ""
        if first and first != clean:
            res = ares_search(first)
    if not res:
        return "DO-WERYFIKACJI", f"ARES: brak firmy dla '{clean[:30]}'"
    if "error" in res:
        return "DO-WERYFIKACJI", res["error"]
    if res.get("ico"):
        row["nip_vat"] = res["ico"]
        row["rejestr_id"] = f"ARES IČO {res['ico']}"
        if res.get("adres") and (not row.get("adres") or "do ustalenia" in row.get("adres", "").lower() or "do weryfikacji" in row.get("adres", "").lower()):
            row["adres"] = res["adres"]
        # zrodlo update
        existing = row.get("zrodlo_danych", "")
        if "ARES" not in existing:
            row["zrodlo_danych"] = f"ARES API (search by name) + web search 2026-08-10"
        row["data_weryfikacji"] = "2026-08-10"
        return "FROZEN", f"ARES name search: {res['nazwa']} (IČO {res['ico']})"
    return "DO-WERYFIKACJI", "ARES: brak IČO"


def normalize(s: str) -> str:
    """Normalize a name for fuzzy comparison."""
    if not s:
        return ""
    s = s.upper()
    # strip legal form suffixes
    for suf in ["SP. Z O.O.", "SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
                "S.R.O.", "SPOL. S R.O.", "SPOL. S R. O.",
                "A.S.", "AKCIOVÁ SPOLEČNOST", "S.C.", "SP.J.",
                "SPÓŁKA CYWILNA", "SPÓŁKA JAWNA", "F.H.U.",
                "SP.J.", "SP. J."]:
        s = s.replace(suf, "")
    # strip punctuation
    s = re.sub(r"[^A-Z0-9ĄĆĘŁŃÓŚŹŻ]+", " ", s)
    return " ".join(s.split())


def verify_pl_row(row: dict, token: str) -> tuple[str, str]:
    """Verify PL row via KRS (for sp. z o.o.) or CEIDG (for JDG)."""
    nip = (row.get("nip_vat") or "").strip()
    rejestr = (row.get("rejestr_id") or "").strip()

    # Try KRS first if rejestr_id contains KRS number
    krs_match = re.search(r"KRS\s*(\d+)", rejestr, re.IGNORECASE)
    if krs_match:
        krs = krs_match.group(1)
        result = krs_lookup(krs)
        if result and "error" not in result:
            csv_nazwa = normalize(row.get("nazwa_firmy", ""))
            api_nazwa = normalize(result.get("nazwa", ""))
            if csv_nazwa and api_nazwa and csv_nazwa not in api_nazwa and api_nazwa not in csv_nazwa:
                return "DO-WERYFIKACJI", f"KRS: nazwa mismatch (CSV='{csv_nazwa[:30]}' API='{api_nazwa[:30]}')"
            return "FROZEN", f"KRS live: {result.get('nazwa', '')[:40]} (REGON {result.get('regon', '')})"
        else:
            err = result.get("error", "brak") if result else "brak"
            return "DO-WERYFIKACJI", f"KRS({krs}): {err}"

    # Fall back to CEIDG (for JDG / sole proprietors)
    if not nip:
        return "DO-WERYFIKACJI", "Brak nip_vat i brak KRS"
    result = ceidg_lookup(nip, token)
    if not result or "error" in result:
        return "DO-WERYFIKACJI", f"CEIDG: {result.get('error', 'brak') if result else 'brak'}"

    # CEIDG returns "imie nazwisko" for JDG — looser check: at least one key token from CSV must appear in API
    csv_nazwa = normalize(row.get("nazwa_firmy", ""))
    api_nazwa = normalize(result.get("nazwa", ""))
    if csv_nazwa and api_nazwa:
        csv_tokens = set(csv_nazwa.split())
        api_tokens = set(api_nazwa.split())
        # Drop common legal-form words
        legal = {"SP", "ZOO", "OO", "SRO", "AS", "SC", "SPJ", "FHU"}
        csv_tokens -= legal
        # Check that NIP/REGON match (more reliable than name for JDG)
        api_nip_clean = re.sub(r"\D", "", result.get("nip", ""))
        csv_nip_clean = re.sub(r"\D", "", nip)
        nip_ok = api_nip_clean and csv_nip_clean and api_nip_clean == csv_nip_clean
        # If NIP matches, accept (name is "imie nazwisko" which won't match firm name)
        if not nip_ok:
            # Fall back to token check
            if not csv_tokens or not (csv_tokens & api_tokens):
                return "DO-WERYFIKACJI", f"CEIDG: ani NIP ani nazwa nie pasują (CSV='{csv_nazwa[:30]}' API='{api_nazwa[:30]}')"

    return "FROZEN", f"CEIDG live: {result.get('nazwa', '')[:40]} (REGON {result.get('regon', '')})"


def verify_cz_row(row: dict) -> tuple[str, str]:
    """Verify CZ row via ARES. Falls back to name search if IČO missing."""
    nip = (row.get("nip_vat") or "").strip()
    # If IČO missing or "do weryfikacji" — try name search
    if not nip or nip in ("do weryfikacji", "brak", "brak danych"):
        return ares_enrich(row)
    result = ares_lookup(nip)
    if not result or "error" in result:
        return "DO-WERYFIKACJI", f"ARES: {result.get('error', 'brak') if result else 'brak'}"

    csv_nazwa = normalize(row.get("nazwa_firmy", ""))
    api_nazwa = normalize(result.get("nazwa", ""))
    if csv_nazwa and api_nazwa and csv_nazwa not in api_nazwa and api_nazwa not in csv_nazwa:
        return "DO-WERYFIKACJI", f"ARES: nazwa mismatch (CSV='{csv_nazwa[:30]}' API='{api_nazwa[:30]}')"

    return "FROZEN", f"ARES live: {result.get('nazwa', '')[:40]} (od {result.get('datum_vzniku', '?')})"


def update_row_status(csv_path: Path, updates: dict[str, tuple[str, str]]) -> int:
    """Update flagi column for verified rows. Returns count updated."""
    if not updates:
        return 0
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    if "id_unikalne" not in header or "flagi" not in header:
        return 0
    id_idx = header.index("id_unikalne")
    flagi_idx = header.index("flagi")
    n = 0
    for row in rows:
        id_ = row[id_idx]
        if id_ in updates:
            status, _ = updates[id_]
            existing = row[flagi_idx] or ""
            # Strip ALL prior FROZEN/DO-WERYFIKACJI markers (including (API) variants and date prefixes)
            cleaned = re.sub(r"\d{4}-\d{2}-\d{2}\s*", "", existing)  # strip date prefixes
            cleaned = re.sub(r"\(API\)", "", cleaned)                 # strip (API) tags first
            cleaned = re.sub(r"✅\s*FROZEN", "", cleaned)              # strip FROZEN
            cleaned = re.sub(r"⚠️?\s*DO-WERYFIKACJI", "", cleaned)    # strip DO-WERYFIKACJI
            cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()         # collapse whitespace
            today = __import__('time').strftime('%Y-%m-%d')
            marker = f"{today} ✅ FROZEN (API)" if status == "FROZEN" else f"{today} ⚠️ DO-WERYFIKACJI (API)"
            row[flagi_idx] = f"{cleaned} {marker}".strip() if cleaned else marker
            n += 1
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description="Live registry verification for BILLSzuka")
    ap.add_argument("--country", help="Limit to one country code (e.g. PL, CZ)")
    ap.add_argument("--all", action="store_true", help="Verify all rows in all countries")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be verified, write nothing")
    args = ap.parse_args()

    env = load_env()
    ceidg_token = env.get("CEIDG_API_TOKEN", "")

    if not ceidg_token:
        log("WARNING: CEIDG_API_TOKEN not in .env — PL rows will be skipped")

    csv_files = sorted(p for p in DATA.glob("*/catalog-*.csv")
                       if p.is_file() and p.stat().st_size > 400
                       and not p.parent.name.startswith("."))

    total_verified = 0
    total_frozen = 0
    total_dov = 0

    for csv_path in csv_files:
        with open(csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        updates: dict[str, tuple[str, str]] = {}
        for row in rows:
            country = (row.get("kraj") or "").upper().strip()
            if args.country and country != args.country.upper():
                continue
            if not args.country and not args.all:
                continue

            id_ = (row.get("id_unikalne") or "").strip()
            if not id_:
                continue

            if country == "PL":
                if not ceidg_token:
                    continue
                status, reason = verify_pl_row(row, ceidg_token)
            elif country == "CZ":
                status, reason = verify_cz_row(row)
            else:
                continue  # no API yet for this country

            updates[id_] = (status, reason)
            total_verified += 1
            if status == "FROZEN":
                total_frozen += 1
            else:
                total_dov += 1
            log(f"  {id_}: {status} — {reason[:60]}")

        if updates and not args.dry_run:
            n = update_row_status(csv_path, updates)
            if n:
                log(f"  → {csv_path.name}: {n} rows updated")

    log(f"\nTotal: {total_verified} verified — {total_frozen} FROZEN, {total_dov} DO-WERYFIKACJI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
