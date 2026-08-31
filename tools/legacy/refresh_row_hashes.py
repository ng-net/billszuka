#!/usr/bin/env python3
"""
One-shot: regenerate row-hashes.json to match the new (post-migration) CSV
schema. Use after structural changes that don't alter row data (column add/drop).

Why: verify_run.py diffs each row against stored hashes. If a column is
removed, every row's hash changes → next run re-verifies everything.
Recomputing once keeps the schema migration transparent.

Usage:
    python3 tools/refresh_row_hashes.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STATE = DATA / ".verify-state" / "row-hashes.json"

# Match the key set the original verify_run uses (id).
HASH_KEY = "id"


def row_hash(row: dict[str, str]) -> str:
    blob = json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha1(blob).hexdigest()[:16]


def main() -> int:
    if not STATE.exists():
        print(f"State file not found: {STATE}", file=sys.stderr)
        return 1

    with STATE.open() as f:
        state = json.load(f)

    files = state.get("files", {})
    updated = 0
    missing = 0
    for rel_path, by_id in files.items():
        path = ROOT / rel_path
        if not path.exists():
            missing += 1
            continue
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            new_by_id = {}
            for row in reader:
                key = row.get(HASH_KEY)
                if key:
                    new_by_id[key] = row_hash(row)
        # Only update if hashes actually changed (avoid pointless churn).
        if new_by_id != by_id:
            files[rel_path] = new_by_id
            updated += 1
            print(f"  refreshed: {rel_path} ({len(new_by_id)} rows)")

    with STATE.open("w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print(f"\nUpdated {updated}/{len(files)} files (missing on disk: {missing})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
