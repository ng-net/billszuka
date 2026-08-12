#!/usr/bin/env python3
"""
fix_data_quality.py — Data Auto-Cleaning, Fuzzy Deduplication & Lead Quality Scoring for BILLSzuka.

Capabilities:
  1. Creates automatic CSV backups in data/backups/ before modification.
  2. Standardizes text encoding, address formatting, and region codes.
  3. Performs fuzzy deduplication on company names and NIP/VAT IDs.
  4. Calculates a 0–100 Quality Score (QS) for every lead based on data completeness and API verification.
  5. Updates the `flagi` field with the calculated QS and standardized status markers.

Usage:
  python3 tools/fix_data_quality.py [--dry-run] [--country CODE]
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BACKUP_DIR = DATA / "backups"


def log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


SKIP_DIRS = {".snapshots", ".verify-state", "backups", "verification", "_intake", "temp"}


def prune_old_backups(max_age_days: int = 7) -> int:
    """Delete backup CSVs older than max_age_days. Keeps data/backups/ from
    growing unboundedly across many fix_data_quality.py runs.

    Returns count of files deleted.
    """
    if not BACKUP_DIR.exists():
        return 0
    cutoff = time.time() - (max_age_days * 86400)
    deleted = 0
    for f in BACKUP_DIR.glob("*.csv"):
        try:
            if f.name.startswith("._"):
                f.unlink()
                deleted += 1
            elif f.stat().st_mtime < cutoff:
                f.unlink()
                deleted += 1
        except OSError:
            pass
    return deleted


def create_backups() -> None:
    """Create timestamped backup copies of all canonical CSV catalogs."""
    # Housekeeping first: prune stale backups so we don't accumulate forever.
    pruned = prune_old_backups(max_age_days=7)
    if pruned:
        log(f"🧹 Pruned {pruned} stale backup(s) older than 7 days")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")

    # Discover canonical catalog CSVs only (excluding backups, intake, temp, snapshots)
    candidates = list(DATA.glob("*/catalog-[AB]-*.csv")) + list(DATA.glob("catalog-[AB]-*.csv"))
    csv_files = [
        p for p in candidates
        if p.is_file()
        and p.stat().st_size > 10
        and p.parent.name not in SKIP_DIRS
        and not p.name.startswith("._")
    ]

    created = 0
    for p in csv_files:
        # Strip existing timestamps or pre-clean suffixes to prevent timestamp chaining
        canonical_stem = re.sub(r"(_\d{8}_\d{6}.*|_-pre-clean.*)", "", p.stem)

        # Check if identical content already exists in backups for this catalog
        content = p.read_bytes()
        content_hash = hashlib.md5(content).hexdigest()

        # Look for matching backup
        already_backed_up = False
        for b in BACKUP_DIR.glob(f"{canonical_stem}_*.csv"):
            if not b.name.startswith("._"):
                try:
                    if hashlib.md5(b.read_bytes()).hexdigest() == content_hash:
                        already_backed_up = True
                        break
                except OSError:
                    pass

        if not already_backed_up:
            dest = BACKUP_DIR / f"{canonical_stem}_{ts}{p.suffix}"
            dest.write_bytes(content)
            created += 1

    log(f"✅ Created {created} backup(s) of {len(csv_files)} catalog CSVs in {BACKUP_DIR.name}/")


def string_similarity(a: str, b: str) -> float:
    """Return similarity ratio (0.0 to 1.0) between two strings."""
    if not a or not b:
        return 0.0
    a_norm = re.sub(r"[^A-Z0-9]+", "", a.upper())
    b_norm = re.sub(r"[^A-Z0-9]+", "", b.upper())
    if not a_norm or not b_norm:
        return 0.0
    if a_norm == b_norm:
        return 1.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def calculate_quality_score(row: dict) -> tuple[int, list[str]]:
    """Calculate 0-100 Quality Score and breakdown reasons for a lead row."""
    score = 0
    reasons = []

    # 1. Registration / NIP/VAT format (+25 max)
    nip = (row.get("nip_vat") or "").strip()
    rejestr = (row.get("rejestr_id") or "").strip()
    if nip and nip not in ("brak", "do weryfikacji", "brak danych"):
        score += 25
        reasons.append("NIP/VAT obecny")
    elif rejestr and rejestr != "brak":
        score += 15
        reasons.append("Rejestr ID obecny")

    # 2. Verification status (+35 max)
    flagi = (row.get("flagi") or "").upper()
    if "FROZEN" in flagi:
        score += 35
        reasons.append("Weryfikacja API/FROZEN")
    elif "DO-WERYFIKACJI" in flagi:
        score += 15
        reasons.append("Do weryfikacji")

    # 3. Address completeness (+20 max)
    adres = (row.get("adres") or "").strip()
    region = (row.get("region_nazwa") or "").strip()
    if adres and len(adres) > 8 and "do ustalenia" not in adres.lower():
        score += 15
        reasons.append("Adres pełny")
    elif adres:
        score += 8
    if region and region not in ("brak", "Polska", "Czechy"):
        score += 5

    # 4. Web presence / Contact info (+20 max)
    strona = (row.get("strona_www") or "").strip()
    email = (row.get("email") or "").strip()
    telefon = (row.get("telefon") or "").strip()
    contact_pts = 0
    if strona and strona not in ("brak", "nie dotyczy"):
        contact_pts += 10
    if email and email != "brak":
        contact_pts += 5
    if telefon and telefon != "brak":
        contact_pts += 5
    score += contact_pts
    if contact_pts > 0:
        reasons.append(f"Kontakt (+{contact_pts})")

    return min(100, score), reasons


def clean_and_score_catalog(csv_path: Path, dry_run: bool = False) -> tuple[int, int]:
    """Clean catalog, remove fuzzy duplicates, update Quality Scores."""
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not fieldnames or not rows:
        return 0, 0

    seen_nips = set()
    seen_names = []
    cleaned_rows = []
    duplicates_count = 0
    updated_count = 0

    for row in rows:
        nip = (row.get("nip_vat") or "").strip().upper()
        name = (row.get("nazwa_firmy") or "").strip()

        # Deduplication check
        if nip and nip not in ("BRAK", "DO WERYFIKACJI") and nip in seen_nips:
            duplicates_count += 1
            log(f"  ⚠️ Duplikaty po NIP pominięty: {name} ({nip})")
            continue
        
        # Fuzzy name deduplication for non-empty names
        is_dup = False
        if name and len(name) > 6:
            for s_name in seen_names:
                if string_similarity(name, s_name) > 0.92:
                    duplicates_count += 1
                    log(f"  ⚠️ Duplikat podobieństwa nazwy ({string_similarity(name, s_name):.2f}): '{name}' ~ '{s_name}'")
                    is_dup = True
                    break
        if is_dup:
            continue

        if nip and nip not in ("BRAK", "DO WERYFIKACJI"):
            seen_nips.add(nip)
        if name:
            seen_names.append(name)

        # Standardize address
        adres = (row.get("adres") or "").strip()
        adres = re.sub(r"\s+", " ", adres)
        row["adres"] = adres

        # Calculate Quality Score
        qs, _ = calculate_quality_score(row)

        # Update flagi field with Quality Score tag
        existing_flagi = (row.get("flagi") or "").strip()
        # Strip old QS tags
        cleaned_flagi = re.sub(r"QS:\s*\d+/100\s*\|?\s*", "", existing_flagi).strip()
        new_flagi = f"QS: {qs}/100 | {cleaned_flagi}".strip(" |")
        row["flagi"] = new_flagi
        updated_count += 1

        cleaned_rows.append(row)

    if not dry_run:
        tmp_path = csv_path.with_suffix(csv_path.suffix + ".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\r\n")
                writer.writeheader()
                writer.writerows(cleaned_rows)
            os.replace(tmp_path, csv_path)
        except OSError as e:
            log(f"  → {csv_path.name}: atomic write failed ({e})")
            if tmp_path.exists():
                try: tmp_path.unlink()
                except OSError: pass
            raise

    return updated_count, duplicates_count


def main():
    ap = argparse.ArgumentParser(description="BILLSzuka Data Auto-Cleaning & Quality Scoring")
    ap.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    ap.add_argument("--country", help="Process only target country (e.g. PL, CZ)")
    args = ap.parse_args()

    if not args.dry_run:
        create_backups()

    csv_files = sorted(p for p in DATA.glob("*/catalog-[AB]-*.csv")
                       if p.is_file() and p.stat().st_size > 100
                       and p.parent.name not in SKIP_DIRS
                       and not p.name.startswith("._"))

    total_cleaned = 0
    total_dups = 0

    log("🧹 Starting Data Auto-Cleaning & Quality Scoring...")
    for csv_path in csv_files:
        if args.country and args.country.upper() not in csv_path.name.upper() and args.country.upper() not in csv_path.parent.name.upper():
            continue
        cleaned, dups = clean_and_score_catalog(csv_path, dry_run=args.dry_run)
        total_cleaned += cleaned
        total_dups += dups
        log(f"  → {csv_path.name}: {cleaned} row(s) scored, {dups} duplicate(s) cleaned")

    log(f"\n🎉 Done! Total {total_cleaned} leads scored, {total_dups} duplicates removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
