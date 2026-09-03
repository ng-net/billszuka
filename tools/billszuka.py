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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from config import DATA_DIR


def cmd_compile(args: argparse.Namespace) -> int:
    """Validate all catalog schemas and atomically rebuild data/master.csv.

    Uses pipeline.regenerate_master_csv() with strict_schema=True. This
    matches the original billszuka behavior (warn on schema drift, return
    false). Schema validation happens inside the helper.
    """
    print("🚀 [BILLSzuka] Compiling data/master.csv from per-kraj catalog CSVs...")

    from tools.pipeline import regenerate_master_csv
    ok, total = regenerate_master_csv(DATA_DIR, atomic=True, strict_schema=True)

    # Sync static copies into frontend-2/public/ for instant UI access
    master_file = DATA_DIR / "master.csv"
    if master_file.exists():
        public_dir = ROOT / "frontend-2" / "public"
        if public_dir.is_dir():
            import shutil
            shutil.copy2(master_file, public_dir / "master.csv")
            shutil.copy2(master_file, public_dir / "sample.csv")

    print(f"✅ Compilation complete!")
    print(f"   Total master rows:  {total}")
    if not ok:
        print(f"   ⚠️ Schema warnings: 1+ file(s) had schema drift (compile failed)")
        return 1
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


def cmd_sync(args: argparse.Namespace) -> int:
    """Verify 1:1 sync between regional catalogs and master.csv."""
    import sync_verifier
    if getattr(args, "watch", False):
        sync_verifier.run_gentle_watcher(
            interval_seconds=getattr(args, "interval", 60),
            auto_recompile=True,
        )
        return 0
    results = sync_verifier.verify_master_sync(
        auto_fix=getattr(args, "recompile", False),
        verbose=True,
    )
    return 0 if results["status"] == "PERFECT_SYNC" else 1


def main():
    parser = argparse.ArgumentParser(description="BILLSzuka Unified Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command")

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

    # Sync
    p_sync = subparsers.add_parser("sync", help="Verify 1:1 consistency between regional catalogs and master.csv")
    p_sync.add_argument("--recompile", "--fix", action="store_true", help="Auto-recompile master.csv if drift is detected")
    p_sync.add_argument("--watch", action="store_true", help="Run continuously in the background")
    p_sync.add_argument("--interval", type=int, default=60, help="Watch interval in seconds (default: 60)")
    p_sync.set_defaults(func=cmd_sync)

    if len(sys.argv) == 1:
        parser.print_help(sys.stdout)
        return 0

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help(sys.stdout)
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
