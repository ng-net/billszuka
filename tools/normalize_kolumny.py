#!/usr/bin/env python3
"""
normalize_kolumny.py — Targeted column-value fixes for known data quality issues.

Handles four specific issues flagged by tools/validate_columns.py:

FixA — **PL-A kanal_sprzedaży junk**: col 25 has `bills.pl` (URL, not a channel),
   `Intertabac wystawca` (event, not a channel), or `brak` (placeholder). Clear col 25.

FixB — **PL-B misplaced powinowactwo (1-5)**: col 25 (kanal_sprzedaży) has 1, 2, 3, 4, 5
   as string, col 26 (powinowactwo_nabijarki) is empty. Move value from col 25 to col 26,
   clear col 25.

FixC — **A row has B-only fields filled** (cross-contamination): catalog-A rows with
   filled `powinowactwo_nabijarki` or `cross_sell_potential` (B-only per methodology
   §10). Clear those fields.

FixD — **B row has A-only fields filled**: catalog-B rows with non-neutral
   `marki_nabijarki` or `marka_wlasna_oem` (A-only per methodology §10). Clear
   those fields. "n/a" / "nie" / "no" treated as placeholders, not contamination.

All four ops are idempotent — re-running on already-fixed rows is a no-op.
Currently only operates on PL catalogs; other countries' data is already valid
per loose alias matching in validate_columns.py.

Backup: every modified file is copied to
``data/.pre-normalize-{YYYYMMDD-HHMMSS}/`` before any write. Backup is per-run
(overwritten if you re-run within the same second); use ``--backup-dir`` to
override.

Usage::

    python3 tools/normalize_kolumny.py --dry-run    # show what would change
    python3 tools/normalize_kolumny.py --apply     # make changes + backup
    python3 tools/normalize_kolumny.py --apply --backup-dir data/.manual-fix
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

CANONICAL_COLUMNS: list[str] = [
    "related_to", "rok_zalozenia", "id", "kategoria", "nazwa_firmy",
    "kraj", "miasto", "adres", "nip_vat", "rejestr_id",
    "www", "kanal_zamiennik", "email", "telefon", "linkedin",
    "facebook", "instagram", "tiktok", "tier", "marki_nabijarki",
    "marka_wlasna_oem", "sourcing", "wolumen", "confidence_wolumen", "kanal_sprzedaży",
    "powinowactwo_nabijarki", "cross_sell_potential", "decydent", "stanowisko", "email_decydent",
    "zrodlo_danych", "data_weryfikacji", "flagi", "notatki", "rynek_skala",
]

# Junk values in col 25 (kanal_sprzedaży) that indicate data-entry errors,
# not real sales channels. Exact match (case-sensitive after strip).
JUNK_KANAL_VALUES: set[str] = {
    "bills.pl",        # URL mis-placed in channel field
    "Intertabac wystawca",  # event name mis-placed in channel field
    "brak",            # placeholder, not a real channel
}

# Values 1-5 are valid in col 26 (powinowactwo_nabijarki) but invalid in
# col 25 (kanal_sprzedaży). If col 26 is empty, the value in col 25
# was clearly meant for col 26.
POWINOWACTWO_DIGITS: set[str] = {"1", "2", "3", "4", "5"}

# Neutral/empty values for B-only columns (cross-contamination cleanup).
# When a B row has "nie"/"n/a"/"no" in marki_nabijarki (which is
# normally A-only), treat it as a "no brands" placeholder rather than
# real cross-contamination — leave the row alone.
NEUTRAL_VALUES: set[str] = {"", "n/a", "nie", "no"}


def detect_catalog_type(path: Path) -> str | None:
    """Return 'A' / 'B' / None based on the catalog filename pattern."""
    name = path.stem.lower()
    m = re.search(r"catalog-([ab])-", name)
    return m.group(1).upper() if m else None


def is_eligible_fix_a(row: dict[str, str]) -> bool:
    """PL-A row: kanal_sprzedaży (col 25) has a junk value that should be cleared."""
    val = (row.get("kanal_sprzedaży") or "").strip()
    return val in JUNK_KANAL_VALUES


def is_eligible_fix_b(row: dict[str, str]) -> bool:
    """PL-B row: kanal_sprzedaży (col 25) has 1-5 and powinowactwo (col 26) is empty.

    Shifts the value from col 25 to col 26 and clears col 25.
    """
    val = (row.get("kanal_sprzedaży") or "").strip()
    if val not in POWINOWACTWO_DIGITS:
        return False
    pow_val = (row.get("powinowactwo_nabijarki") or "").strip()
    return pow_val == ""


def is_eligible_fix_c(row: dict[str, str], catalog_type: str | None) -> list[str]:
    """A row: cols 26-27 (powinowactwo, cross_sell) are filled.
    They should be empty for A rows (B-only per methodology §10).

    Returns list of columns to clear (empty list = no fix needed).
    """
    if catalog_type != "A":
        return []
    cols: list[str] = []
    for col in ("powinowactwo_nabijarki", "cross_sell_potential"):
        v = (row.get(col) or "").strip()
        if v and v.lower() not in NEUTRAL_VALUES:
            cols.append(col)
    return cols


def is_eligible_fix_d(row: dict[str, str], catalog_type: str | None) -> list[str]:
    """B row: cols 20-21 (marki_nabijarki, marka_wlasna_oem) are filled.
    They should be empty for B rows (A-only per methodology §10).

    Returns list of columns to clear. 'nie'/'n/a'/'no' are treated as
    intentional placeholders, not contamination.
    """
    if catalog_type != "B":
        return []
    cols: list[str] = []
    for col in ("marki_nabijarki", "marka_wlasna_oem"):
        v = (row.get(col) or "").strip()
        if v and v.lower() not in NEUTRAL_VALUES:
            cols.append(col)
    return cols


def find_target_files() -> list[Path]:
    """All per-kraj catalog files where fixes may apply."""
    targets: list[Path] = []
    for sub in sorted(DATA.iterdir()):
        if not sub.is_dir() or sub.name.startswith(".") or sub.name in {
            ".snapshots", ".verify-state", "backups", "verification", "_intake"
        }:
            continue
        for f in sorted(sub.glob("catalog-[AB]-*.csv")):
            if f.name.startswith("._"):
                continue
            targets.append(f)
    return targets


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read CSV with BOM handling. Return (header, rows_as_dicts)."""
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], []
        rows: list[dict[str, str]] = []
        for raw in reader:
            if not raw or all(not c for c in raw):
                continue
            # Pad to header length
            if len(raw) < len(header):
                raw = raw + [""] * (len(header) - len(raw))
            rows.append(dict(zip(header, raw)))
    return header, rows


def write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    """Atomic write (tmp + os.replace) preserving original column order."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\r\n")
            writer.writerow(header)
            for row in rows:
                writer.writerow([row.get(col, "") for col in header])
        os.replace(tmp, path)
    except OSError:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def make_backup(files: list[Path], backup_dir: Path) -> None:
    """Copy every to-be-modified file into backup_dir preserving relative paths."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    for src in files:
        rel = src.relative_to(DATA)
        dst = backup_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def apply_fixes(path: Path, write: bool = True) -> list[str]:
    """Apply eligible fixes to a single CSV. Return list of human-readable actions.

    Returns empty list if no changes were made (idempotent).
    Set ``write=False`` for dry-run previews.
    """
    header, rows = load_csv(path)
    if not header or not rows:
        return []

    # Only operate on PL files; other countries' data is already valid
    # (the loose alias match in validate_columns handles them).
    is_pl = "/Polska/" in str(path)
    if not is_pl:
        return []

    catalog_type = detect_catalog_type(path)

    actions: list[str] = []
    fixed_rows: list[dict[str, str]] = []
    for row in rows:
        new_row = dict(row)
        if is_eligible_fix_b(new_row):
            # Move 1-5 from col 25 to col 26; clear col 25.
            val = new_row["kanal_sprzedaży"].strip()
            new_row["powinowactwo_nabijarki"] = val
            new_row["kanal_sprzedaży"] = ""
            actions.append(f"{new_row.get('id', '?')}: "
                           f"shifted '{val}' col 25 -> col 26")
        elif is_eligible_fix_a(new_row):
            # Clear junk value in col 25.
            old = new_row["kanal_sprzedaży"].strip()
            new_row["kanal_sprzedaży"] = ""
            actions.append(f"{new_row.get('id', '?')}: "
                           f"cleared kanal_sprzedaży='{old}'")
        # FixC/D: A↔B cross-contamination cleanup. These are independent
        # of FixA/B above — a single row can have multiple fixes applied.
        for col in is_eligible_fix_c(new_row, catalog_type):
            old = new_row[col].strip()
            new_row[col] = ""
            actions.append(f"{new_row.get('id', '?')}: "
                           f"cleared {col}='{old}' (A row, B-only field)")
        for col in is_eligible_fix_d(new_row, catalog_type):
            old = new_row[col].strip()
            new_row[col] = ""
            actions.append(f"{new_row.get('id', '?')}: "
                           f"cleared {col}='{old}' (B row, A-only field)")
        fixed_rows.append(new_row)

    if actions and write:
        write_csv(path, header, fixed_rows)
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing")
    parser.add_argument("--apply", action="store_true",
                        help="Apply changes + write backup")
    parser.add_argument("--backup-dir", type=Path, default=None,
                        help="Override backup dir (default: data/.pre-normalize-{stamp})")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("ERROR: must specify --dry-run or --apply", file=sys.stderr)
        return 2

    targets = find_target_files()
    if not args.dry_run:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = args.backup_dir or (DATA / f".pre-normalize-{stamp}")
        # Pre-create backup dir so the user sees it before any writes
        backup_dir.mkdir(parents=True, exist_ok=True)

    files_to_modify: dict[Path, list[str]] = {}
    for path in targets:
        actions = apply_fixes(path, write=False)  # dry-run preview, no writes
        if actions:
            files_to_modify[path] = actions

    if not files_to_modify:
        print("No fixes needed. Already clean.")
        return 0

    # Show summary
    total_actions = sum(len(a) for a in files_to_modify.values())
    print(f"Planned changes: {total_actions} in {len(files_to_modify)} file(s)")
    for path, actions in files_to_modify.items():
        rel = path.relative_to(ROOT)
        print(f"\n  {rel}  ({len(actions)} fix(es))")
        for action in actions:
            print(f"    - {action}")

    if args.dry_run:
        print("\n(dry-run: no files written)")
        return 0

    # Apply: backup first, then re-apply with write=True
    print(f"\nBacking up to: {backup_dir}")
    make_backup(list(files_to_modify.keys()), backup_dir)
    for path in files_to_modify:
        apply_fixes(path, write=True)  # idempotent — same fixes re-applied
    print(f"Applied: {total_actions} change(s) across {len(files_to_modify)} file(s)")

    # Re-run validate_columns to confirm fixes
    print("\nRun `python3 tools/validate_columns.py` to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
