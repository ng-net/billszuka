#!/usr/bin/env python3
"""
migrate_strip_regions.py — Migration script to strip all region fields and re-index clean sequential IDs.

Actions:
1. Strips region_nazwa, region_kod, region_typ, _reg_code, _krs from all catalog-[AB]-*.csv files.
2. Assigns clean, strictly unique sequential IDs per country & catalog: e.g. PL-A-001, PL-A-002..., PL-B-001, PL-B-002...
3. Ensures all 24 catalogs have exactly 35 canonical columns in the exact order specified by config.py.
4. Rebuilds data/master.csv atomically.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR, make_id


def migrate_catalogs() -> dict[str, str]:
    """Migrate catalog CSVs and assign unique sequential IDs."""
    id_remap: dict[str, str] = {}
    total_files = 0
    total_rows = 0

    for iso, country_dir_name in COUNTRY_MAP.items():
        cdir = DATA_DIR / country_dir_name
        if not cdir.is_dir():
            continue

        for cat_type in ["A", "B"]:
            cfile = cdir / f"catalog-{cat_type}-{iso}.csv"
            if not cfile.exists():
                continue

            total_files += 1
            rows_out = []

            with cfile.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                seq = 1
                for row in reader:
                    old_id = row.get("id", "").strip()
                    new_id = make_id(iso, cat_type, seq)

                    if old_id and old_id != new_id:
                        id_remap[old_id] = new_id

                    # Construct clean row according to CANONICAL_SCHEMA
                    clean_row = {}
                    for col in CANONICAL_SCHEMA:
                        clean_row[col] = row.get(col, "").strip()

                    clean_row["id"] = new_id
                    clean_row["kraj"] = iso
                    rows_out.append(clean_row)
                    seq += 1
                    total_rows += 1

            # Atomic write back to catalog file
            tmp_file = cfile.with_suffix(".csv.tmp")
            with tmp_file.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
                writer.writeheader()
                writer.writerows(rows_out)
            tmp_file.replace(cfile)
            print(f"Migrated {cfile.relative_to(DATA_DIR)}: {len(rows_out)} rows")

    print(f"\nCompleted catalog migration: {total_files} files, {total_rows} rows, {len(id_remap)} ID remappings.")
    return id_remap


def migrate_relationships(id_remap: dict[str, str]):
    """Update relationships.csv with new region-free IDs."""
    rel_file = DATA_DIR / "relationships.csv"
    if not rel_file.exists():
        return

    with rel_file.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not fieldnames:
        return

    updated = 0
    for row in rows:
        from_id = row.get("from_id", "").strip()
        to_id = row.get("to_id", "").strip()
        if from_id in id_remap:
            row["from_id"] = id_remap[from_id]
            updated += 1
        if to_id in id_remap:
            row["to_id"] = id_remap[to_id]
            updated += 1

    tmp_file = rel_file.with_suffix(".csv.tmp")
    with tmp_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    tmp_file.replace(rel_file)
    print(f"Migrated relationships.csv ({updated} ID updates).")


def rebuild_master():
    """Rebuild data/master.csv from all migrated catalogs."""
    master_file = DATA_DIR / "master.csv"
    all_rows = []

    for iso, country_dir_name in COUNTRY_MAP.items():
        cdir = DATA_DIR / country_dir_name
        if not cdir.is_dir():
            continue

        for cat_type in ["A", "B"]:
            cfile = cdir / f"catalog-{cat_type}-{iso}.csv"
            if not cfile.exists():
                continue

            with cfile.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if any(v.strip() for v in row.values()):
                        all_rows.append(row)

    tmp_master = master_file.with_suffix(".csv.tmp")
    with tmp_master.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
        writer.writeheader()
        writer.writerows(all_rows)
    tmp_master.replace(master_file)
    print(f"Rebuilt data/master.csv: {len(all_rows)} total rows, 35 canonical columns.")


if __name__ == "__main__":
    remap = migrate_catalogs()
    migrate_relationships(remap)
    rebuild_master()
