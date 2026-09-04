#!/usr/bin/env python3
"""
dedup_check.py — Pre-flight dedup check against master.csv + gems-NON-PL.csv
plus all per-country catalog-A/B files.

Usage:
  python3 tools/dedup_check.py --name "Tabák Plus" --nip "63489821"
  python3 tools/dedup_check.py --name "POGON KOOLTURA" --nip "83711572958" --country HR
  python3 tools/dedup_check.py --name "KON-RAD" --country SK
  echo '["name", "nip", "country"]' | python3 tools/dedup_check.py --json
  python3 tools/dedup_check.py --batch candidates.json

Output (human):
  NEW                                          # not in any catalog
  EXACT_PL-B-079                               # exact NIP+name match
  PARTIAL_PL-A-010|name=tabak plus|nip=N/A     # name match only
  DUPLICATE_BONUS Hurtownia...                # full name match

Exit codes:
  0 = NEW (or PARTIAL — needs review)
  1 = exact or duplicate match
  2 = invalid input
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
COUNTRIES = {
    "PL": "Polska", "CZ": "Czechy", "SK": "Słowacja", "RO": "Rumunia",
    "HR": "Chorwacja", "BG": "Bułgaria", "EE": "Estonia", "LT": "Litwa",
    "LV": "Łotwa", "MD": "Mołdawia", "RS": "Serbia", "SI": "Słowenia",
    "FR": "Francja",  # legacy
}


def strip_country_prefix(norm_nip: str) -> str:
    """Strip ISO country prefix from normalized NIP. e.g. cz63489821 → 63489821."""
    if norm_nip and len(norm_nip) >= 8:
        for prefix in ("md", "cz", "sk", "ro", "hr", "bg", "ee", "lt",
                      "lv", "rs", "si", "pl", "fr"):
            if norm_nip.startswith(prefix) and norm_nip[len(prefix):].isdigit():
                return norm_nip[len(prefix):]
    return norm_nip


def norm(s: str) -> str:
    """Normalize: strip diacritics, lowercase, collapse non-alnum."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in nfkd if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    return s


def load_all():
    """Return list of (kraj, id, name, nip, source_file)."""
    rows = []
    # master.csv (canonical)
    p = DATA / "master.csv"
    if p.exists():
        with p.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append((r.get("kraj", ""), r.get("id", ""),
                             r.get("nazwa", ""), r.get("nip_vat", ""),
                             "master.csv"))
    # gems-NON-PL.csv
    p = DATA / "verification" / "gems-NON-PL.csv"
    if not p.exists():
        p = DATA / "gems-NON-PL.csv"
    if p.exists():
        with p.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                # schema: score,whale,country,iso,id,name,miasto,kategoria,tier,powinowactwo,wolumen,confidence,kanal,email,telefon,www,decydent,notatki,flagi
                if not r.get("id"):
                    continue
                # gems has no NIP column → try to extract from notatki/email via regex
                nip = ""
                for field in ("notatki", "email", "www"):
                    v = r.get(field, "") or ""
                    m = re.search(r"\b(\d{6,13})\b", v)
                    if m:
                        nip = m.group(1)
                        break
                rows.append((r.get("country", ""), r.get("id", ""),
                             r.get("name", ""), nip,
                             "gems-NON-PL.csv"))
    # per-country catalog-A + catalog-B + extra-leads
    for cc, dir_name in COUNTRIES.items():
        dd = DATA / dir_name
        if not dd.exists():
            continue
        for fn in (f"catalog-A-{cc}.csv", f"catalog-B-{cc}.csv",
                   f"extra-leads-{cc}.csv"):
            p = dd / fn
            if not p.exists():
                continue
            try:
                with p.open(encoding="utf-8") as f:
                    for r in csv.DictReader(f):
                        if not r:
                            continue
                        # The ID column name varies: "id" (catalog-A/B) or empty (extra-leads)
                        rid = r.get("id") or r.get("ID") or ""
                        # Find name column: prefer "nazwa"/"Název"/"Názov"
                        name = (r.get("nazwa") or r.get("Název") or r.get("Názov")
                                or r.get("name") or r.get("Name") or "")
                        if not name and not rid:
                            continue
                        if not name:
                            continue
                        # NIP: look in known columns
                        nip = (r.get("nip_vat") or r.get("NIP") or r.get("nip")
                               or r.get("IČO") or r.get("ico") or r.get("IDNO")
                               or r.get("idno") or r.get("CUI") or r.get("cui")
                               or r.get("OIB") or r.get("oib")
                               or r.get("PIB") or r.get("pib")
                               or r.get("EIK") or r.get("eik")
                               or r.get("MŠ") or r.get("mš")
                               or r.get("IČ DPH") or "")
                        rows.append((cc, rid, name, str(nip).strip(),
                                     str(p.relative_to(ROOT))))
            except (UnicodeDecodeError, csv.Error, KeyError):
                continue
    return rows


def check(name: str, nip: str = "", country: str = "", all_rows=None) -> dict:
    """Return dedup result dict."""
    if all_rows is None:
        all_rows = load_all()
    norm_name = norm(name)
    norm_nip = norm(nip).replace(" ", "")
    # Strip ISO country prefix (case-insensitive). E.g. CZ63489821 → 63489821,
    # MD1002606001330 → 1002606001330, PL8511005882 → 8511005882.
    norm_nip = strip_country_prefix(norm_nip)
    result = {"input": {"name": name, "nip": nip, "country": country},
              "normalized": {"name": norm_name, "nip": norm_nip},
              "matches": [], "verdict": "NEW"}
    for kraj, id_, row_name, row_nip, source in all_rows:
        if country and kraj != country:
            continue
        row_n_norm = norm(row_name)
        row_nip_n = strip_country_prefix(norm(row_nip).replace(" ", ""))
        if row_nip_n and norm_nip and row_nip_n == norm_nip:
            # Exact NIP match
            result["matches"].append({"kraj": kraj, "id": id_, "name": row_name,
                                       "nip": row_nip, "source": source,
                                       "match_type": "EXACT_NIP"})
            result["verdict"] = "EXACT_" + id_
            return result
    result = {"input": {"name": name, "nip": nip, "country": country},
              "normalized": {"name": norm_name, "nip": norm_nip},
              "matches": [], "verdict": "NEW"}
    for kraj, id_, row_name, row_nip, source in all_rows:
        if country and kraj != country:
            continue
        row_n_norm = norm(row_name)
        row_nip_n = norm(row_nip).replace(" ", "")
        if row_nip and norm_nip and row_nip_n == norm_nip:
            # Exact NIP match
            result["matches"].append({"kraj": kraj, "id": id_, "name": row_name,
                                       "nip": row_nip, "source": source,
                                       "match_type": "EXACT_NIP"})
            result["verdict"] = "EXACT_" + id_
            return result
        if norm_name and row_n_norm == norm_name:
            result["matches"].append({"kraj": kraj, "id": id_, "name": row_name,
                                       "nip": row_nip, "source": source,
                                       "match_type": "EXACT_NAME"})
            result["verdict"] = "EXACT_" + id_
            return result
        # Fuzzy: token overlap ≥ 70% AND len >= 5 chars
        if norm_name and row_n_norm and len(norm_name) >= 5:
            t1 = set(norm_name.split())
            t2 = set(row_n_norm.split())
            if t1 and t2:
                overlap = len(t1 & t2) / max(len(t1), len(t2))
                if overlap >= 0.7:
                    result["matches"].append({
                        "kraj": kraj, "id": id_, "name": row_name,
                        "nip": row_nip, "source": source,
                        "match_type": f"FUZZY_{overlap:.0%}",
                    })
    if result["matches"]:
        # If fuzzy only, mark as PARTIAL (needs review)
        if all(m["match_type"].startswith("FUZZY") for m in result["matches"]):
            result["verdict"] = "PARTIAL"
    return result


def main():
    ap = argparse.ArgumentParser(description="BILLSzuka dedup check")
    ap.add_argument("--name", help="Company name to check")
    ap.add_argument("--nip", default="", help="NIP / IČO / IDNO / CUI etc.")
    ap.add_argument("--country", default="", help="ISO country code (PL, CZ, ...)")
    ap.add_argument("--batch", help="JSON file with [{name, nip, country}, ...] array")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    all_rows = load_all()
    if args.batch:
        with open(args.batch) as f:
            batch = json.load(f)
        results = [check(item.get("name", ""), item.get("nip", ""),
                          item.get("country", ""), all_rows)
                    for item in batch]
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for r in results:
                print(f"{r['verdict']}\t{r['input']['name']}\t{r['input']['nip']}")
        sys.exit(0)

    if not args.name:
        print("Usage: --name 'X' [--nip 'Y'] [--country 'CC']", file=sys.stderr)
        sys.exit(2)

    r = check(args.name, args.nip, args.country, all_rows)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(r["verdict"])
        for m in r["matches"]:
            print(f"  match={m['match_type']} id={m['id']} kraj={m['kraj']} "
                  f"name={m['name'][:50]} nip={m.get('nip','')} source={m['source']}")
    sys.exit(0 if r["verdict"] in ("NEW", "PARTIAL") else 1)


if __name__ == "__main__":
    main()
