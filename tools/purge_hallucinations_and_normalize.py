#!/usr/bin/env python3
"""
purge_hallucinations_and_normalize.py — Purges all synthetic LLM hallucinations,
re-indexes unique IDs cleanly (e.g. CZ-A-001, CZ-B-001), ensures 35-column canonical schema,
quarantines purged rows with audit reasons, creates .bak backups, and prepares catalogs for verification.
"""

import argparse
import csv
import datetime
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

sys.path.insert(0, str(ROOT / "tools"))
from config import CANONICAL_SCHEMA, COUNTRY_MAP, QUARANTINE_DIR, is_verified_allowlisted

# Anchored exact dummy values & dummy regexes
# Only matches when the whole normalized number is a dummy sequence or placeholder pattern
DUMMY_ID_PATTERNS = [
    # Sequential / ascending / descending runs as the full ID
    r"^(?:[A-Z]{2})?(?:123456|987654|112233|234567|345678|456789|567890|678901)$",
    r"^(?:[A-Z]{2})?(?:1234567|12345678|123456789|1234567890|0123456789)$",
    r"^(?:[A-Z]{2})?(?:9876543|98765432|987654321|9876543210)$",
    r"^(?:[A-Z]{2})?(?:20234567|202031234|555444333|55556666|555666777|11223344)$",
    # Single digit repeated 5+ times (e.g. 000000, 111111111, 9999999999)
    r"^(?:[A-Z]{2})?([0-9])\1{4,}$",
]
COMPILED_DUMMY_PATTERNS = [re.compile(p, re.IGNORECASE) for p in DUMMY_ID_PATTERNS]


def is_dummy_identifier(val: str) -> bool:
    """Check if tax/registry ID matches anchored dummy patterns and is not allowlisted."""
    if not val:
        return False
    if is_verified_allowlisted(val):
        return False
    clean = re.sub(r"[\s\-\.]+", "", val).strip()
    if not clean:
        return False
    return any(p.match(clean) for p in COMPILED_DUMMY_PATTERNS)


def is_hallucinated(row: dict, iso: str) -> tuple[bool, str]:
    """Inspect a catalog row and return (is_hallucinated, reason)."""
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
        
    # 3. Dummy sequential tax / registry numbers (checked against anchored patterns & allowlist)
    if is_dummy_identifier(nip):
        return True, f"Dummy pattern in NIP ({nip})"
    if is_dummy_identifier(rejestr):
        return True, f"Dummy pattern in rejestr_id ({rejestr})"
                
    # 4. Empty stubs without official registry identifier
    if iso == "MD" and not nip and not rejestr and not www and any(w in name for w in ["Moldova", "Tabac", "Tobacco"]):
        return True, f"Empty stub without official registry ID ({name})"
        
    # 5. Invalid / generic placeholder names
    if name.lower() in ["tobacco import", "smoke shop", "tobacco world", "smoke & more", "tobacco distributors"]:
        return True, f"Generic placeholder name ({name})"

    return False, ""


def write_quarantine_rows(quarantine_path: Path, purged_records: list[dict]):
    """Write or append purged records with reason and timestamp to quarantine file."""
    if not purged_records:
        return
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = CANONICAL_SCHEMA + ["purge_reason", "purged_at"]
    
    file_exists = quarantine_path.exists()
    with open(quarantine_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        for rec in purged_records:
            row_dict = {col: rec.get(col, "") for col in fieldnames}
            writer.writerow(row_dict)


def clean_catalogs(dry_run: bool = False):
    """
    Scan all catalogs, purge hallucinations, write quarantine records,
    backup originals to .bak, and write back canonical 35-column rows via atomic tempfile swap.
    """
    total_checked = 0
    total_purged = 0
    total_retained = 0
    now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
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
            purged_records = []
            file_purged = 0
            
            for row in orig_rows:
                total_checked += 1
                hallucinated, reason = is_hallucinated(row, iso)
                if hallucinated:
                    total_purged += 1
                    file_purged += 1
                    p_rec = dict(row)
                    p_rec["purge_reason"] = reason
                    p_rec["purged_at"] = now_ts
                    purged_records.append(p_rec)
                else:
                    clean_rows.append(row)
                    
            # Re-index clean rows
            for i, row in enumerate(clean_rows, 1):
                row["id"] = f"{iso}-{cat_type}-{i:03d}"
                # Ensure 35 canonical columns
                clean_row = {col: (row.get(col) or "").strip() for col in CANONICAL_SCHEMA}
                clean_rows[i - 1] = clean_row
                
            if not dry_run:
                # 1. Write quarantine if there are purged rows
                if purged_records:
                    quarantine_file = QUARANTINE_DIR / f"purged-{cat_type}-{iso}.csv"
                    write_quarantine_rows(quarantine_file, purged_records)
                
                # 2. Backup original file to .bak before overwriting
                bak_file = cfile.with_suffix(".csv.bak")
                shutil.copy2(cfile, bak_file)
                
                # 3. Write clean rows to temporary file and swap atomically
                tmp_file = cfile.with_suffix(".csv.tmp")
                with open(tmp_file, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
                    writer.writeheader()
                    writer.writerows(clean_rows)
                tmp_file.replace(cfile)
                
            total_retained += len(clean_rows)
            prefix = "[DRY RUN] " if dry_run else "  ✓ "
            status_str = f"{prefix}{cdir_name}/catalog-{cat_type}-{iso}.csv: {len(clean_rows)} verified rows"
            if file_purged > 0:
                action_word = "would purge" if dry_run else "purged"
                status_str += f" ({action_word} {file_purged} hallucinations)"
            print(status_str)
            if dry_run and purged_records:
                for p in purged_records:
                    print(f"      - Purge candidate: '{p.get('nazwa_firmy', '')}' (NIP: '{p.get('nip_vat', '')}') -> {p.get('purge_reason', '')}")
            
    mode_label = " (DRY RUN - No files modified)" if dry_run else ""
    print(f"\n==========================================")
    print(f"Catalog Hallucination Scan Summary{mode_label}")
    print(f"Total rows inspected : {total_checked}")
    print(f"Hallucinations purged: {total_purged}")
    print(f"Grounded rows kept   : {total_retained}")
    print(f"==========================================")


def main():
    parser = argparse.ArgumentParser(
        description="Purge synthetic LLM hallucinations, normalize IDs, backup original CSVs, and quarantine purged records."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate purge without modifying catalogs, creating .bak backups, or writing quarantine files.",
    )
    args = parser.parse_args()
    clean_catalogs(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
