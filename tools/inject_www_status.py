#!/usr/bin/env python3
"""
inject_www_status.py — wstrzykuje kolumnę www_status do wszystkich katalogów BILLSzuka.

Czyta dane z billszuka.db (url_status table, schema z tools/db.py) i wstawia
status obok www w każdym catalog-*.csv, extra-leads-*.csv, gems-*.csv, master.csv.

Kolumna www_status trafia na pozycję 6 (bezpośrednio po www), zgodnie z
CANONICAL_SCHEMA w tools/config.py.

Format www_status (compact, czytelny w CSV):
  "green|200|12ms"  - 2xx/3xx z czasem odpowiedzi
  "red|404"          - 4xx/5xx z kodem HTTP
  "red|timeout"      - timeout/DNS/SSL
  ""                 - brak www LUB brak wpisu w url_status (do przeskanowania)
  "unknown"          - status='unknown' z url_status

Idempotentny: nadpisuje istniejącą www_status, nie duplikuje kolumny.

Użycie:
  python3 tools/inject_www_status.py --dry-run    # podgląd zmian
  python3 tools/inject_www_status.py               # zapis
  python3 tools/inject_www_status.py --country SK  # tylko SK
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from config import CANONICAL_SCHEMA, COUNTRY_MAP  # noqa: E402

DB_PATH = ROOT / "data" / "billszuka.db"
DATA = ROOT / "data"

# Country ISO code → directory name (FROM config.py COUNTRY_MAP, but includes
# all country directories in data/, not just in-scope ones)
ISO_TO_FOLDER = {iso: folder for iso, folder in COUNTRY_MAP.items()}


def load_url_status() -> dict[tuple[str, str], str]:
    """
    Return {(id, url): www_status_string} from url_status table.
    Pick the most recent entry per (id, url).
    """
    if not DB_PATH.exists():
        print(f"⚠️ Brak {DB_PATH} — wracam z pustym słownikiem")
        return {}

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        # Get the most recent check per (id, url) — url_status can have multiple
        # entries if scan was re-run. ORDER BY checked_at DESC + window trick.
        cur.execute("""
            SELECT id_unikalne, url, status, state, http_code, response_ms, error, checked_at
            FROM url_status
            WHERE (id_unikalne, url, checked_at) IN (
                SELECT id_unikalne, url, MAX(checked_at)
                FROM url_status
                GROUP BY id_unikalne, url
            )
        """)
        out = {}
        for row in cur.fetchall():
            id_, url, status, state, code, ms, err, _ = row
            out[(id_, url)] = _format_status(status, state, code, ms, err)
        return out
    finally:
        conn.close()


def _format_status(status: str, state: str, code: int | None, ms: int | None, err: str | None) -> str:
    """Compact string format for CSV column."""
    if status == "green":
        if code and ms is not None:
            return f"green|{code}|{ms}ms"
        if code:
            return f"green|{code}"
        return "green"
    if status == "red":
        # Prefer http_code; fall back to state
        if code:
            return f"red|{code}"
        if state and state != "red":
            return f"red|{state}"
        if err:
            return f"red|{err[:30]}"
        return "red"
    if status == "unknown":
        return "unknown"
    return status or ""


def find_catalog_csvs(country: str | None = None) -> list[Path]:
    """Find all catalog/extra-leads/gems/master CSV files (skip .snapshots/)."""
    files = []
    if country:
        iso = country.upper()
        folder = ISO_TO_FOLDER.get(iso)
        if not folder:
            print(f"⚠️ Nieznany kod kraju: {iso}")
            return files
        d = DATA / folder
        if d.exists():
            files.extend(_csvs_in(d))
    else:
        for d in DATA.iterdir():
            if d.is_dir() and d.name not in {".snapshots", "_intake", "users", "knowledge", "verification", "validation-reports"}:
                files.extend(_csvs_in(d))
        # master.csv at root
        master = DATA / "master.csv"
        if master.exists():
            files.append(master)
    return [f for f in files if f.is_file()]


def _csvs_in(d: Path) -> list[Path]:
    return sorted([
        f for f in d.iterdir()
        if f.is_file()
        and f.suffix == ".csv"
        and (f.name.startswith("catalog-") or f.name.startswith("extra-leads-") or f.name.startswith("gems-"))
    ])


def inject_into_csv(path: Path, status_map: dict[tuple[str, str], str], dry_run: bool) -> dict:
    """
    Add www_status column to CSV. Returns stats dict.
    Idempotent: if www_status column already exists, replace its values.
    """
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        old_fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if not old_fieldnames:
        return {"path": str(path), "rows": 0, "updated": 0, "skipped_no_www": 0, "no_data": 0}

    # Determine if www_status column already exists
    has_col = "www_status" in old_fieldnames
    if has_col:
        new_fieldnames = old_fieldnames
    else:
        # Insert www_status right after www (per CANONICAL_SCHEMA position 6)
        try:
            www_idx = old_fieldnames.index("www")
        except ValueError:
            return {"path": str(path), "rows": len(rows), "updated": 0, "skipped_no_www": 0, "no_data": 0,
                    "error": "no www column"}
        new_fieldnames = old_fieldnames[:www_idx + 1] + ["www_status"] + old_fieldnames[www_idx + 1:]

    updated = 0
    skipped_no_www = 0
    no_data = 0
    for row in rows:
        id_ = row.get("id", "").strip()
        www = row.get("www", "").strip()
        if not www:
            skipped_no_www += 1
            if has_col:
                row["www_status"] = ""
            continue
        val = status_map.get((id_, www), "")
        if val:
            updated += 1
        else:
            no_data += 1
        row["www_status"] = val

    if dry_run:
        return {"path": str(path), "rows": len(rows), "updated": updated,
                "skipped_no_www": skipped_no_www, "no_data": no_data, "would_write": True}

    # Write back
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return {"path": str(path), "rows": len(rows), "updated": updated,
            "skipped_no_www": skipped_no_www, "no_data": no_data, "would_write": False}


def main():
    ap = argparse.ArgumentParser(description="Inject www_status column into BILLSzuka CSVs")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change, don't write")
    ap.add_argument("--country", help="ISO code (e.g. SK, PL) — only process that country")
    args = ap.parse_args()

    print("=" * 70)
    print(f"INJECT www_status  |  schema: {len(CANONICAL_SCHEMA)} columns  |  "
          f"{'DRY RUN' if args.dry_run else 'WRITE'}")
    print("=" * 70)

    status_map = load_url_status()
    print(f"url_status table: {len(status_map)} (id,url) pairs loaded")

    files = find_catalog_csvs(args.country)
    print(f"CSV files to process: {len(files)}")
    print()

    total_rows = 0
    total_updated = 0
    total_no_www = 0
    total_no_data = 0
    errors = []

    for f in files:
        result = inject_into_csv(f, status_map, dry_run=args.dry_run)
        if "error" in result:
            errors.append(result)
            continue
        rel = result["path"].replace(str(ROOT) + "/", "")
        total_rows += result["rows"]
        total_updated += result["updated"]
        total_no_www += result["skipped_no_www"]
        total_no_data += result["no_data"]
        marker = "📝" if result.get("would_write") else "✅"
        print(f"  {marker} {rel}: {result['rows']} rows, "
              f"{result['updated']} updated, {result['skipped_no_www']} no-www, "
              f"{result['no_data']} no-data-in-url_status")

    print()
    print("=" * 70)
    print(f"TOTAL: {total_rows} rows across {len(files)} files")
    print(f"  with www_status filled: {total_updated} ({100*total_updated/max(total_rows,1):.1f}%)")
    print(f"  no www (left empty):    {total_no_www}")
    print(f"  www exists but no scan: {total_no_data}  ← run check_urls.py for these")
    if errors:
        print(f"  errors: {len(errors)}")
        for e in errors:
            print(f"    - {e['path']}: {e['error']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
