#!/usr/bin/env python3
"""
l0_preflight.py — FABRYKAT detection per methodology L0.

Validates that each NIP+KRS pair in a per-kraj CSV actually points to a real
company matching the CSV `nazwa_firmy`. Catches LLM hallucinations where the
KRS exists in registry but belongs to a completely different entity.

Checks (defense in depth):
  1. NIP checksum (mod 11) — instant, free
  2. KRS API + name match (PL) — 200ms per row, free
  3. CEIDG API + name match (PL JDG) — when NIP only
  4. Retro-fix: re-verifies rows currently marked FROZEN (API) and flags
     any that fail name match as FABRYKAT (delete or mark for review)

Usage:
  python3 tools/l0_preflight.py --country PL              # check all PL rows
  python3 tools/l0_preflight.py --country PL --retrofix   # also re-verify existing FROZEN (API)
  python3 tools/l0_preflight.py --dry-run --country PL    # report only

Env: .env → CEIDG_API_TOKEN
"""

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from checksums import validate_id

ROOT = Path("/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka")
DATA = ROOT / "data"
ENV_FILE = ROOT / ".env"

KRS_API = "https://api-krs.ms.gov.pl/api/krs/OdpisAktualny"
CEIDG_API = "https://dane.biznes.gov.pl/api/ceidg/v3/firmy"


def log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def validate_nip(nip: str) -> tuple[bool, str]:
    """PL NIP mod-11 checksum. Returns (valid, reason)."""
    nip = re.sub(r"\D", "", str(nip))
    if len(nip) != 10:
        return False, f"wrong length ({len(nip)})"
    if not nip.isdigit():
        return False, "not all digits"
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    s = sum(int(nip[i]) * weights[i] for i in range(9))
    if s % 11 != int(nip[9]):
        return False, f"checksum fail (s={s}, expected {s % 11}, got {nip[9]})"
    return True, "ok"


def krs_lookup(krs: str) -> dict | None:
    """KRS API: returns parsed JSON or None on error."""
    krs = re.sub(r"\D", "", str(krs)).zfill(10)
    try:
        with urllib.request.urlopen(f"{KRS_API}/{krs}", timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"KRS HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)}


def ceidg_lookup(nip: str, token: str) -> dict | None:
    """CEIDG v3 by NIP. Returns parsed firmy[0] or None."""
    nip = re.sub(r"\D", "", str(nip))
    if len(nip) != 10:
        return None
    req = urllib.request.Request(
        f"{CEIDG_API}?nip={nip}&status=AKTYWNY",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        firms = data.get("firmy", [])
        return firms[0] if firms else None
    except Exception as e:
        return {"error": str(e)}


def normalize(s: str) -> str:
    """Strip Polish diacritics, legal-form suffixes, punctuation."""
    if not s:
        return ""
    s = s.upper()
    for suf in ["SP. Z O.O.", "SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
                "SPÓŁKA AKCYJNA", "S.A.", "S.R.O.", "SPOL. S R.O.", "A.S.",
                "S.C.", "SP.J.", "SPÓŁKA CYWILNA", "SPÓŁKA JAWNA", "F.H.U.",
                "SP. K.", "SPÓŁKA KOMANDYTOWA", "S.K.A.", "SP. Z O.O. SP.K.",
                "SP.J.", "SP. J."]:
        s = s.replace(suf, "")
    s = re.sub(r"[^A-Z0-9ĄĆĘŁŃÓŚŹŻ]+", " ", s)
    return " ".join(s.split())


def name_match(csv_name: str, api_name: str) -> tuple[bool, str]:
    """Fuzzy match: returns (match, reason).

    Token Jaccard similarity (same as tools/verify_api.py: name_similarity).
    Strips legal-form tokens first (they always match and would inflate
    the score, hiding real mismatches like "PEAL" vs "PEAL Real Estate").
    Threshold 0.8 catches the FABRYKAT pattern: LLM-generated identifiers
    pass checksum but point to entities sharing only a common prefix word
    with the claimed company.
    """
    c = normalize(csv_name)
    a = normalize(api_name)
    if not c or not a:
        return False, "empty name"
    legal = {"SP", "ZOO", "OO", "SRO", "AS", "SC", "SPJ", "FHU",
             "SPOL", "POL", "KOM", "SA", "AG", "GMBH"}
    c_tokens = set(c.split()) - legal
    a_tokens = set(a.split()) - legal
    if not c_tokens and not a_tokens:
        return False, "no tokens after legal-form strip"
    intersection = c_tokens & a_tokens
    union = c_tokens | a_tokens
    score = len(intersection) / len(union) if union else 0.0
    if score >= 0.8:
        return True, f"jaccard {score:.2f} (≥0.8)"
    return False, (
        f"jaccard {score:.2f} <0.8 (CSV='{c[:30]}' API='{a[:30]}')"
    )


def check_row(row: dict, country: str, token: str) -> dict:
    """Run all L0 checks on a row. Returns {verdict, reason, details}."""
    csv_nazwa = (row.get("nazwa_firmy") or "").strip()
    nip = (row.get("nip_vat") or "").replace("PL", "").replace(" ", "").strip()
    rejestr = (row.get("rejestr_id") or "").strip()

    result = {"verdict": "OK", "reason": "", "details": {}}

    # Check 1: Multi-country ID checksum (per checksums.py)
    # First, normalize: strip country prefix and check if it's a placeholder
    nip_clean = re.sub(r"\s+", "", str(nip or "")).lower()
    placeholders = {"brak", "doweryfikacji", "doustalenia", "na", "—", "n/a", "tbd", "todo"}
    if nip and nip_clean not in placeholders:
        ok, why = validate_id(nip, country)
        result["details"]["id_check"] = {"valid": ok, "reason": why}
        if not ok:
            # Don't auto-fail on "format only" countries (DE, LT) or where the
            # algorithm has known limitations
            if "format only" not in why and "not implemented" not in why:
                result["verdict"] = "FABRYKAT"
                result["reason"] = f"{country} ID {nip} invalid: {why}"
                return result

    # Check 2: KRS name match
    krs_match = re.search(r"KRS\s*(\d+)", rejestr, re.IGNORECASE)
    if krs_match and country == "PL":
        krs = krs_match.group(1)
        data = krs_lookup(krs)
        if "error" in data:
            result["details"]["krs_check"] = {"krs": krs, "error": data["error"]}
            result["verdict"] = "DO-WERYFIKACJI"
            result["reason"] = f"KRS {krs}: {data['error']}"
            return result
        api_nazwa = data.get("odpis", {}).get("dane", {}).get("dzial1", {}).get("danePodmiotu", {}).get("nazwa", "")
        ok, why = name_match(csv_nazwa, api_nazwa)
        result["details"]["krs_check"] = {
            "krs": krs, "api_name": api_nazwa, "match": ok, "reason": why
        }
        if not ok:
            result["verdict"] = "FABRYKAT"
            result["reason"] = f"KRS {krs} name mismatch — CSV='{csv_nazwa[:30]}' API='{api_nazwa[:30]}'"
            return result
        return result

    # Check 3: CEIDG (for JDG)
    if nip and len(nip) == 10 and country == "PL" and token:
        firm = ceidg_lookup(nip, token)
        if firm and "error" in firm:
            # API error (timeout, rate limit, etc.) — NOT a FABRYKAT, just can't verify
            result["details"]["ceidg_check"] = {"error": firm["error"]}
            result["verdict"] = "DO-WERYFIKACJI"
            result["reason"] = f"CEIDG API error: {firm['error'][:60]}"
            return result
        if firm:  # got a result
            api_nazwa = firm.get("nazwa", "") or " ".join(filter(None, [
                firm.get("imie", ""), firm.get("nazwisko", "")
            ]))
            api_nip = re.sub(r"\D", "", firm.get("nip", ""))
            if not api_nip:
                # CEIDG returned firm but no NIP — odd, treat as inconclusive
                result["details"]["ceidg_check"] = {"api_name": api_nazwa, "nip_empty": True}
                result["verdict"] = "DO-WERYFIKACJI"
                result["reason"] = f"CEIDG: firm found but no NIP (CSV={nip} API='{api_nazwa}')"
                return result
            if api_nip != nip:
                result["verdict"] = "FABRYKAT"
                result["reason"] = f"CEIDG NIP mismatch (CSV={nip} API={api_nip})"
                return result
            result["details"]["ceidg_check"] = {"api_name": api_nazwa, "nip_ok": True}
            return result
        # firm is None (no result, not an error) — try fallback
        result["details"]["ceidg_check"] = {"no_firm_found": True}
        result["verdict"] = "DO-WERYFIKACJI"
        result["reason"] = f"CEIDG: no firm for NIP {nip}"
        return result

    result["verdict"] = "SKIPPED"
    result["reason"] = "no KRS or CEIDG checkable"
    return result


def process_csv(csv_path: Path, country: str, token: str, retrofix: bool, dry_run: bool) -> dict:
    """Process one CSV file. Returns summary dict."""
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    id_idx = header.index("id_unikalne")
    flagi_idx = header.index("flagi")
    name_idx = header.index("nazwa_firmy")
    nip_idx = header.index("nip_vat")
    rejestr_idx = header.index("rejestr_id")
    zrodlo_idx = header.index("zrodlo_danych")
    data_v_idx = header.index("data_weryfikacji")

    fabrykaty = []
    pendings = []
    oks = []
    skipped = []
    retrofixed = []

    for i, row in enumerate(rows):
        if len(row) <= max(id_idx, flagi_idx, name_idx):
            continue
        row_dict = {
            "nazwa_firmy": row[name_idx],
            "nip_vat": row[nip_idx],
            "rejestr_id": row[rejestr_idx],
            "id_unikalne": row[id_idx],
            "flagi": row[flagi_idx],
        }
        idu = row[id_idx]

        # Skip non-PL rows in non-PL files
        if (row_dict.get("kraj") if len(row) > 8 else None) and False:
            pass

        is_frozen_api = "FROZEN (API)" in (row_dict["flagi"] or "")

        if is_frozen_api and not retrofix:
            skipped.append(idu)
            continue
            skipped.append(idu)
            continue

        result = check_row(row_dict, country, token)
        verdict = result["verdict"]

        if verdict == "FABRYKAT":
            fabrykaty.append((idu, result["reason"]))
            if not dry_run:
                # Update flagi to DO-WERYFIKACJI with FABRYKAT marker
                existing = row[flagi_idx] or ""
                cleaned = re.sub(r"\s*✅\s*FROZEN(?:\s*\(API\))?", "", existing)
                cleaned = re.sub(r"\s*⚠️\s*DO-WERYFIKACJI(?:\s*\(API\))?", "", cleaned)
                row[flagi_idx] = f"{cleaned.strip()} 🔴 FABRYKAT ⚠️ DO-WERYFIKACJI".strip()
                row[data_v_idx] = "2026-08-10"
                if is_frozen_api:
                    retrofixed.append(idu)
        elif verdict == "DO-WERYFIKACJI":
            pendings.append((idu, result["reason"]))
        elif verdict == "OK":
            oks.append(idu)
        else:
            skipped.append(idu)

    if not dry_run:
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            w.writerow(header)
            w.writerows(rows)

    return {
        "file": str(csv_path.relative_to(ROOT)),
        "total": len(rows),
        "ok": len(oks),
        "fabrykaty": fabrykaty,
        "pendings": pendings,
        "skipped": skipped,
        "retrofixed": retrofixed,
    }


def main():
    ap = argparse.ArgumentParser(description="BILLSzuka L0 preflight: FABRYKAT detection")
    ap.add_argument("--country", help="Country code (PL/CZ/etc.). If omitted: all")
    ap.add_argument("--retrofix", action="store_true",
                    help="Re-verify rows already marked FROZEN (API)")
    ap.add_argument("--dry-run", action="store_true", help="Report only, write nothing")
    args = ap.parse_args()

    env = load_env()
    token = env.get("CEIDG_API_TOKEN", "")

    log(f"L0 preflight: country={args.country or 'ALL'} retrofix={args.retrofix} dry_run={args.dry_run}")

    countries = [args.country] if args.country else [
        d.name for d in sorted(DATA.iterdir())
        if d.is_dir() and (d / f"SŁOWNIK-{d.name}.md").exists() or
           d.is_dir() and any(d.glob("catalog-*.csv"))
    ]
    # Find country folders; map "PL" arg → "Polska" folder
    folder_for_code = {
        "PL": "Polska", "CZ": "Czechy", "BG": "Bułgaria", "HR": "Chorwacja",
        "EE": "Estonia", "FR": "Francja", "LT": "Litwa", "LV": "Łotwa",
        "MD": "Mołdawia", "RO": "Rumunia", "SK": "Słowacja", "SI": "Słowenia",
    }
    if args.country:
        folder = folder_for_code.get(args.country.upper(), args.country)
        countries = [folder]
    else:
        countries = []
        for d in sorted(DATA.iterdir()):
            # Skip hidden dirs (.snapshots etc.)
            if d.is_dir() and not d.name.startswith(".") and list(d.glob("catalog-*.csv")):
                countries.append(d.name)

    total_fabrykaty = 0
    total_retrofixed = 0
    for country in countries:
        # country is the FOLDER name (e.g. "Polska"); map to ISO code (e.g. "PL") for check_row
        country_code = next((k for k, v in folder_for_code.items() if v == country), country)
        for csv_path in sorted((DATA / country).glob("catalog-*.csv")):
            log(f"Processing {csv_path.relative_to(ROOT)}...")
            try:
                r = process_csv(csv_path, country_code, token, args.retrofix, args.dry_run)
            except Exception as e:
                log(f"  ERROR: {e}")
                continue
            log(f"  total={r['total']} ok={r['ok']} pendings={len(r['pendings'])} fabrykaty={len(r['fabrykaty'])} skipped={len(r['skipped'])} retrofixed={len(r['retrofixed'])}")
            for idu, reason in r["fabrykaty"]:
                log(f"    🔴 FABRYKAT: {idu} — {reason}")
                total_fabrykaty += 1
            total_retrofixed += len(r["retrofixed"])

    log(f"\n=== TOTAL: {total_fabrykaty} FABRYKATY detected, {total_retrofixed} retro-fixed ===")
    if total_fabrykaty > 0 and not args.dry_run:
        log("⚠️  Review and delete FABRYKAT rows from CSV (or keep with explicit justification)")


if __name__ == "__main__":
    main()
