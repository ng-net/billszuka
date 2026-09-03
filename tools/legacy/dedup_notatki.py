"""Dedupe ' | '-separated parts in notatki column.

BILLSzuka fix tool (`tools/fix_master_data_integrity.py`) was non-idempotent for
notatki appends — each run added another copy of the same ' | X' part. After 5-6
runs, 14 master rows had x5-x6 duplicates of the same fragment.

This script:
  - Splits each notatki by ' | '
  - Deduplicates while preserving first-occurrence order
  - Re-joins with ' | '

Usage:
  python3 tools/dedup_notatki.py            # dry-run
  python3 tools/dedup_notatki.py --apply    # write changes

Scope: data/master.csv + all data/{Kraj}/catalog-*.csv (24 files).
Idempotent: re-running is a no-op once duplicates are removed.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def dedupe_notatki(text: str) -> str:
    """Dedupe ' | '-separated parts preserving first-seen order."""
    if not text:
        return text
    parts = [p.strip() for p in text.split(" | ")]
    seen = set()
    out = []
    for p in parts:
        if p and p not in seen:
            out.append(p)
            seen.add(p)
    return " | ".join(out)


def process_file(path: Path, dry: bool = True) -> int:
    """Returns number of rows changed."""
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    changed = 0
    for row in rows:
        old = row.get("notatki", "")
        new = dedupe_notatki(old)
        if new != old:
            changed += 1
            row["notatki"] = new
    if changed and not dry:
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
    return changed


def main():
    dry = "--apply" not in sys.argv
    files = [DATA / "master.csv"]
    for country in sorted(p for p in DATA.iterdir() if p.is_dir()):
        for f in country.iterdir():
            if f.name.startswith("catalog-") and f.name.endswith(".csv") and ".bak" not in f.name:
                files.append(f)
    total = 0
    for f in files:
        n = process_file(f, dry=dry)
        if n:
            rel = f.relative_to(ROOT)
            print(f"  {rel}: {n} rows {'would change' if dry else 'changed'}")
            total += n
    print(f"\nTotal: {total} rows {'would change' if dry else 'changed'}")
    if dry:
        print("(dry-run; use --apply to write)")


if __name__ == "__main__":
    main()
