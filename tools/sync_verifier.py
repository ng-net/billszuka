#!/usr/bin/env python3
"""
sync_verifier.py — Deep verification and comparison between data/master.csv
and all regional catalogs (/data/[Kraj]/catalog-[A|B]-[ISO].csv).

Performs:
1. 100% ID coverage check (ensures every single lead in regional catalogs is in master.csv)
2. Orphan check (ensures no ghost leads exist in master.csv without source catalog)
3. Column-by-column equality check (ensures field values have zero drift)
4. Schema & uniqueness validation (ensures 35 canonical columns and unique IDs)
5. Atomic reconciliation/auto-sync (--recompile)
6. Continuous gentle background watcher mode (--watch / --loop)
"""

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR


def verify_master_sync(auto_fix: bool = False, verbose: bool = True) -> dict:
    """Run full verification between per-country catalogs and data/master.csv."""
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_catalogs": 0,
        "total_catalog_leads": 0,
        "total_master_leads": 0,
        "catalogs_checked": [],
        "missing_in_master": [],
        "orphans_in_master": [],
        "field_mismatches": [],
        "duplicate_ids": [],
        "schema_warnings": [],
        "status": "PASS",
    }

    catalog_leads_by_id = {}
    master_file = DATA_DIR / "master.csv"

    # 1. Read all regional catalogs
    for iso, country_name in COUNTRY_MAP.items():
        cdir = DATA_DIR / country_name
        if not cdir.is_dir():
            results["schema_warnings"].append(f"Directory not found: {country_name}")
            continue

        for cat_type in ["A", "B"]:
            cfile = cdir / f"catalog-{cat_type}-{iso}.csv"
            if not cfile.exists():
                results["schema_warnings"].append(f"Catalog file missing: {cfile.name}")
                continue

            results["total_catalogs"] += 1
            rel_name = f"{country_name}/{cfile.name}"
            cat_info = {
                "file": rel_name,
                "iso": iso,
                "type": cat_type,
                "rows_count": 0,
            }

            with cfile.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != CANONICAL_SCHEMA:
                    diff = set(CANONICAL_SCHEMA) ^ set(reader.fieldnames or [])
                    results["schema_warnings"].append(
                        f"Schema header mismatch in {rel_name}: diff={diff}"
                    )

                for row_idx, row in enumerate(reader, start=2):
                    uid = (row.get("id") or "").strip()
                    name = (row.get("nazwa_firmy") or "").strip()
                    if not uid and not name:
                        continue  # Skip completely blank rows

                    cat_info["rows_count"] += 1
                    results["total_catalog_leads"] += 1

                    if not uid:
                        results["schema_warnings"].append(
                            f"Empty id at {rel_name}:{row_idx} ({name})"
                        )
                        continue

                    if uid in catalog_leads_by_id:
                        prev_file = catalog_leads_by_id[uid]["_source_file"]
                        results["duplicate_ids"].append(
                            {"id": uid, "source_1": prev_file, "source_2": rel_name}
                        )

                    clean_row = {col: (row.get(col) or "").strip() for col in CANONICAL_SCHEMA}
                    clean_row["_source_file"] = rel_name
                    catalog_leads_by_id[uid] = clean_row

            results["catalogs_checked"].append(cat_info)

    # 2. Read master.csv
    if not master_file.exists():
        results["status"] = "FAIL"
        results["schema_warnings"].append("data/master.csv does not exist!")
        if auto_fix:
            from billszuka import cmd_compile
            cmd_compile(argparse.Namespace())
            return verify_master_sync(auto_fix=False, verbose=verbose)
        return results

    master_leads_by_id = {}
    with master_file.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != CANONICAL_SCHEMA:
            diff = set(CANONICAL_SCHEMA) ^ set(reader.fieldnames or [])
            results["schema_warnings"].append(
                f"Schema header mismatch in master.csv: diff={diff}"
            )

        for row_idx, row in enumerate(reader, start=2):
            uid = (row.get("id") or "").strip()
            name = (row.get("nazwa_firmy") or "").strip()
            if not uid and not name:
                continue

            results["total_master_leads"] += 1
            if not uid:
                results["schema_warnings"].append(
                    f"Empty id at master.csv:{row_idx} ({name})"
                )
                continue

            if uid in master_leads_by_id:
                results["duplicate_ids"].append(
                    {"id": uid, "source_1": "master.csv", "source_2": "master.csv"}
                )

            master_leads_by_id[uid] = {col: (row.get(col) or "").strip() for col in CANONICAL_SCHEMA}

    # 3. Cross-compare catalog rows with master rows
    for uid, cat_row in catalog_leads_by_id.items():
        if uid not in master_leads_by_id:
            results["missing_in_master"].append(
                {
                    "id": uid,
                    "nazwa_firmy": cat_row.get("nazwa_firmy", ""),
                    "source": cat_row.get("_source_file", ""),
                }
            )
        else:
            m_row = master_leads_by_id[uid]
            diffs = {}
            for col in CANONICAL_SCHEMA:
                val_cat = cat_row.get(col, "")
                val_mst = m_row.get(col, "")
                if val_cat != val_mst:
                    diffs[col] = {"catalog": val_cat, "master": val_mst}
            if diffs:
                results["field_mismatches"].append(
                    {
                        "id": uid,
                        "nazwa_firmy": cat_row.get("nazwa_firmy", ""),
                        "source": cat_row.get("_source_file", ""),
                        "differences": diffs,
                    }
                )

    # 4. Check for orphans in master (leads in master that aren't in any catalog)
    for uid, m_row in master_leads_by_id.items():
        if uid not in catalog_leads_by_id:
            results["orphans_in_master"].append(
                {
                    "id": uid,
                    "nazwa_firmy": m_row.get("nazwa_firmy", ""),
                    "kraj": m_row.get("kraj", ""),
                }
            )

    # Status evaluation
    if (
        results["missing_in_master"]
        or results["orphans_in_master"]
        or results["field_mismatches"]
        or results["duplicate_ids"]
    ):
        results["status"] = "DRIFT_DETECTED"
    else:
        results["status"] = "PERFECT_SYNC"

    if auto_fix and results["status"] == "DRIFT_DETECTED":
        if verbose:
            print("🔄 [Sync Verifier] Drift detected, auto-compiling master.csv...")
        from billszuka import cmd_compile
        cmd_compile(argparse.Namespace())
        return verify_master_sync(auto_fix=False, verbose=verbose)

    if verbose:
        print("\n" + "=" * 65)
        print("🔍 BILLSzuka Master Sync & Catalog Integrity Verification")
        print("=" * 65)
        print(f"Catalogs scanned:    {results['total_catalogs']} files")
        print(f"Total catalog leads: {results['total_catalog_leads']} rows")
        print(f"Total master leads:  {results['total_master_leads']} rows")
        print("-" * 65)
        print(f"Missing in master:   {len(results['missing_in_master'])}")
        print(f"Orphans in master:   {len(results['orphans_in_master'])}")
        print(f"Field mismatches:    {len(results['field_mismatches'])}")
        print(f"Duplicate IDs:       {len(results['duplicate_ids'])}")
        print(f"Schema warnings:     {len(results['schema_warnings'])}")
        print("-" * 65)
        print(f"Sync Status:         ✅ {results['status']}" if results["status"] == "PERFECT_SYNC" else f"Sync Status:         ⚠️ {results['status']}")
        print("=" * 65 + "\n")

    return results


def run_gentle_watcher(interval_seconds: int = 60, auto_recompile: bool = True):
    """Gently monitor catalogs in background and keep master.csv synchronized."""
    print(f"🛡️ [Sync Verifier] Starting gentle watcher loop (interval: {interval_seconds}s, auto_recompile={auto_recompile})...")
    try:
        while True:
            res = verify_master_sync(auto_fix=auto_recompile, verbose=False)
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            if res["status"] == "PERFECT_SYNC":
                print(f"[{now_str}] ✓ Sync OK: {res['total_catalog_leads']} leads across {res['total_catalogs']} catalogs match master.csv 1:1.")
            else:
                print(f"[{now_str}] ⚠️ Discrepancy detected: {res['status']}. Auto-fix applied: {auto_recompile}")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n🛑 Watcher stopped by user.")


def main():
    parser = argparse.ArgumentParser(
        description="Verify 1:1 consistency between regional catalogs and data/master.csv"
    )
    parser.add_argument(
        "--recompile",
        "--fix",
        action="store_true",
        help="Automatically recompile master.csv if drift or missing leads are found",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run continuously in background with gentle sleep intervals",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in seconds for continuous watch mode (default: 60)",
    )
    args = parser.parse_args()

    if args.watch:
        run_gentle_watcher(interval_seconds=args.interval, auto_recompile=args.recompile or True)
    else:
        results = verify_master_sync(auto_fix=args.recompile, verbose=True)
        sys.exit(0 if results["status"] == "PERFECT_SYNC" else 1)


if __name__ == "__main__":
    main()
