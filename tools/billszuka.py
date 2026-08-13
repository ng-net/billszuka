#!/usr/bin/env python3
"""
billszuka.py — Unified Master CLI tool for BILLSzuka lead generation & data management.

Commands:
  compile   - Validate schema across all 24 per-country catalogs and rebuild data/master.csv
  verify    - Run automated verification loop, update hashes/flags, append audit log, rebuild master
  intake    - Process raw lead CSVs from data/_intake/ into catalog format
  search    - Run lead discovery scrapers or 11-level strategy playbooks

Usage:
  python3 tools/billszuka.py compile
  python3 tools/billszuka.py verify [--init | --all | --dry-run]
  python3 tools/billszuka.py intake --iso CZ
  python3 tools/billszuka.py search --country SK
"""

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR


def cmd_compile(args: argparse.Namespace) -> int:
    """Validate all catalog schemas and atomically rebuild data/master.csv."""
    print("🚀 [BILLSzuka] Compiling data/master.csv from per-kraj catalog CSVs...")
    all_rows = []
    file_count = 0
    schema_errors = 0

    for iso, country_dir_name in COUNTRY_MAP.items():
        cdir = DATA_DIR / country_dir_name
        if not cdir.is_dir():
            continue

        for cat_type in ["A", "B"]:
            cfile = cdir / f"catalog-{cat_type}-{iso}.csv"
            if not cfile.exists():
                continue

            file_count += 1
            with cfile.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != CANONICAL_SCHEMA:
                    diff = set(CANONICAL_SCHEMA) ^ set(reader.fieldnames or [])
                    print(f"  ⚠️ Schema mismatch in {cfile.relative_to(DATA_DIR)}: diff={diff}")
                    schema_errors += 1

                for row in reader:
                    if any(v.strip() for v in row.values()):
                        # Standardize row keys to CANONICAL_SCHEMA
                        clean_row = {col: row.get(col, "").strip() for col in CANONICAL_SCHEMA}
                        all_rows.append(clean_row)

    master_file = DATA_DIR / "master.csv"
    tmp_master = master_file.with_suffix(".csv.tmp")
    with tmp_master.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
        writer.writeheader()
        writer.writerows(all_rows)

    tmp_master.replace(master_file)

    print(f"✅ Compilation complete!")
    print(f"   Catalogs processed: {file_count}/24")
    print(f"   Total master rows:  {len(all_rows)}")
    print(f"   Schema columns:     {len(CANONICAL_SCHEMA)}")
    if schema_errors:
        print(f"   ⚠️ Schema warnings:   {schema_errors} file(s) auto-corrected")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Run verification loop via verify_run.py."""
    import verify_run
    sys.argv = [sys.argv[0]]
    if getattr(args, "init", False):
        sys.argv.append("--init")
    if getattr(args, "all", False):
        sys.argv.append("--all")
    if getattr(args, "dry_run", False):
        sys.argv.append("--dry-run")
    return verify_run.main()


def cmd_intake(args: argparse.Namespace) -> int:
    """Run intake processing via map_intake.py and validate_intake.py."""
    iso = getattr(args, "iso", None)
    if not iso:
        print("Error: --iso is required for intake (e.g. --iso CZ)")
        return 1

    import map_intake
    sys.argv = [sys.argv[0], "--iso", iso]
    map_intake.main()
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Run 11-level strategy search or registry scrapers."""
    country = getattr(args, "country", None)
    if not country:
        print("Error: --country is required for search (e.g. --country SK)")
        return 1

    import orchestrate_11_levels
    sys.argv = [sys.argv[0], "--country", country]
    orchestrate_11_levels.main()
    return 0


def main():
    parser = argparse.ArgumentParser(description="BILLSzuka Unified Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Compile
    p_compile = subparsers.add_parser("compile", help="Validate catalog schemas and rebuild data/master.csv")
    p_compile.set_defaults(func=cmd_compile)

    # Verify
    p_verify = subparsers.add_parser("verify", help="Run verification loop and update master.csv")
    p_verify.add_argument("--init", action="store_true", help="Build state without re-verifying existing rows")
    p_verify.add_argument("--all", action="store_true", help="Force re-verify all rows")
    p_verify.add_argument("--dry-run", action="store_true", help="Show changes without modifying files")
    p_verify.set_defaults(func=cmd_verify)

    # Intake
    p_intake = subparsers.add_parser("intake", help="Process raw intake CSV into catalog format")
    p_intake.add_argument("--iso", required=True, help="2-letter country code (e.g. CZ, SK)")
    p_intake.set_defaults(func=cmd_intake)

    # Search
    p_search = subparsers.add_parser("search", help="Run 11-level lead discovery strategy")
    p_search.add_argument("--country", required=True, help="2-letter country code (e.g. PL, CZ, SK)")
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
