#!/usr/bin/env python3
"""
One-shot schema migration: drop region_kod, region_typ, _reg_code from all
active BILLSzuka catalog/master CSVs.

Rationale (2026-08-12, Marceli decision):
- region_kod: 61% of master rows are "XX" (placeholder) or empty — column
  carries no signal. Region is already encoded in id_unikalne (e.g. PL-A-WP-001).
- region_typ: orphan type field with no useful typology below PL "województwo".
- _reg_code: registry number (KRS/ARES/e-Äriregister) that was previously
  overlapping with rejestr_id. Rejestr_id is the canonical source.

Kept:
- region_nazwa: human-readable region name (still useful where known).

Scope: master.csv + 11 country folders' catalog-A/B-*.csv. Skips backups/,
_closed/, .snapshots/ (historical state, must remain frozen).

Usage:
    python tools/drop_region_columns.py           # dry-run
    python tools/drop_region_columns.py --apply   # write changes
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

DATA_ROOT = Path("/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/data")
DROPS = {"region_kod", "region_typ", "_reg_code"}

# Files to skip (frozen historical state).
SKIP_DIRS = {"backups", "_closed", ".snapshots"}


def discover_files() -> list[Path]:
    files: list[Path] = []
    files.append(DATA_ROOT / "master.csv")
    files.append(DATA_ROOT / "relationships.csv")
    for path in sorted(DATA_ROOT.glob("*/catalog-*.csv")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def migrate(path: Path, apply: bool) -> tuple[int, int, int]:
    """Return (rows_in, rows_out, cols_removed)."""
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return 0, 0, 0

    header = rows[0]
    drop_idx = [i for i, h in enumerate(header) if h in DROPS]
    if not drop_idx:
        # Schema already migrated (idempotent).
        return len(rows) - 1, len(rows) - 1, 0

    keep_idx = [i for i, _ in enumerate(header) if i not in drop_idx]
    new_header = [header[i] for i in keep_idx]
    new_rows = [[r[i] for i in keep_idx] for r in rows[1:]]

    if apply:
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
            w.writerow(new_header)
            w.writerows(new_rows)

    return len(rows) - 1, len(new_rows), len(drop_idx)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    args = parser.parse_args()

    files = discover_files()
    if not files:
        print("No files matched.", file=sys.stderr)
        return 1

    total_in = total_out = total_cols = 0
    print(f"{'MODE':<10} {'ROWS':>6} {'COLS-':>6}  PATH")
    print("-" * 80)
    for path in files:
        rows_in, rows_out, cols = migrate(path, args.apply)
        total_in += rows_in
        total_out += rows_out
        total_cols = max(total_cols, cols)
        mode = "APPLIED" if args.apply else "DRY-RUN"
        flag = "✓" if rows_in == rows_out else "✗ ROW MISMATCH"
        print(f"{mode:<10} {rows_in:>6} {cols:>6}  {path.relative_to(DATA_ROOT)} {flag}")

    print("-" * 80)
    print(f"{'TOTAL':<10} {total_in:>6} {total_cols:>6}  ({len(files)} files)")
    if not args.apply:
        print("\nDry-run only. Re-run with --apply to write changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
