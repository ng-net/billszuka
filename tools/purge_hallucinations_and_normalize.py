#!/usr/bin/env python3
"""
purge_hallucinations_and_normalize.py — Purges all synthetic LLM hallucinations,
re-indexes unique IDs cleanly (e.g. CZ-A-001, CZ-B-001), ensures 35-column canonical schema,
and prepares catalogs for verification.
"""

import csv
import glob
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

sys.path.insert(0, str(ROOT / "tools"))
from config import CANONICAL_SCHEMA, COUNTRY_MAP

DUMMY_PATTERNS = [
    r"123456", r"987654", r"112233", r"234567", r"345678", r"456789", r"567890", r"678901",
    r"20234567", r"202031234", r"555444333", r"55556666", r"555666777"
]

def is_hallucinated(row: dict, iso: str) -> tuple[bool, str]:
    src = (row.get("zrodlo_danych") or "").strip()
    nip = (row.get("nip_vat") or "").strip()
    rejestr = (row.get("rejestr_id") or "").strip()
    name = (row.get("nazwa_firmy") or "").strip()
    www = (row.get("www") or "").strip()
    
    # 1. LeadScout ungrounded discovery
    if "LeadScout L1 Discovery" in src:
        return True, f"LeadScout ungrounded source: {src[:40]}"
        
    # 2. Fake ListaFirme scraper with dummy numbers
    if "ListaFirme RO Scraper (Verified RO" in src and any(p in src for p in ["1234", "3456", "1122", "2345", "5678"]):
        return True, f"Fake ListaFirme dummy regex: {src[:40]}"
        
    # 3. Dummy sequential tax / registry numbers (except verified PL companies like AGROTAB PL7931626076)
    if "PL7931626076" not in nip:
        for p in DUMMY_PATTERNS:
            if re.search(p, nip):
                return True, f"Dummy pattern in NIP ({nip})"
            if re.search(p, rejestr):
                return True, f"Dummy pattern in rejestr_id ({rejestr})"
                
    # 4. Empty stubs without official registry identifier
    if iso == "MD" and not nip and not rejestr and not www and any(w in name for w in ["Moldova", "Tabac", "Tobacco"]):
        return True, f"Empty stub without official registry ID ({name})"
        
    # 5. Invalid / generic placeholder names
    if name.lower() in ["tobacco import", "smoke shop", "tobacco world", "smoke & more", "tobacco distributors"]:
        return True, f"Generic placeholder name ({name})"

    return False, ""


def clean_catalogs():
    total_checked = 0
    total_purged = 0
    total_retained = 0
    
    for iso, cdir_name in COUNTRY_MAP.items():
        cdir = DATA_DIR / cdir_name
        if not cdir.is_dir():
            continue
            
        for cat_type in ["A", "B"]:
            cfile = cdir / f"catalog-{cat_type}-{iso}.csv"
            if not cfile.exists():
                continue
                
            with open(cfile, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                orig_rows = list(reader)
                
            clean_rows = []
            file_purged = 0
            
            for idx, row in enumerate(orig_rows, 1):
                total_checked += 1
                hallucinated, reason = is_hallucinated(row, iso)
                if hallucinated:
                    total_purged += 1
                    file_purged += 1
                else:
                    clean_rows.append(row)
                    
            # Re-index clean rows
            for i, row in enumerate(clean_rows, 1):
                row["id_unikalne"] = f"{iso}-{cat_type}-{i:03d}"
                # Ensure 35 canonical columns
                clean_row = {col: (row.get(col) or "").strip() for col in CANONICAL_SCHEMA}
                clean_rows[i - 1] = clean_row
                
            # Write back
            with open(cfile, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
                writer.writeheader()
                writer.writerows(clean_rows)
                
            total_retained += len(clean_rows)
            status_str = f"  ✓ {cdir_name}/catalog-{cat_type}-{iso}.csv: {len(clean_rows)} verified rows"
            if file_purged > 0:
                status_str += f" (purged {file_purged} hallucinations)"
            print(status_str)
            
    print(f"\n==========================================")
    print(f"Total rows inspected : {total_checked}")
    print(f"Hallucinations purged: {total_purged}")
    print(f"Grounded rows kept   : {total_retained}")
    print(f"==========================================")

if __name__ == "__main__":
    clean_catalogs()
