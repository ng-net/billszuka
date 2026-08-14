#!/usr/bin/env python3
"""
gmaps_20min_underrepresented_sweep.py — Gentle 20-minute targeted Catalog-A sweep for underrepresented countries.

Target Countries (least Catalog-A rows):
  - MD (Moldova): 3 leads
  - RO (Romania): 4 leads
  - LT (Lithuania): 5 leads
  - LV (Latvia): 8 leads
  - SI (Slovenia): 8 leads
  - HR (Croatia): 13 leads

Pacing: ~75s delay between queries to ensure gentle API usage within a 20-minute budget (1200s).
Post-sweep: Automatically cleans false positives and recompiles master.csv.
"""

import csv
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from config import DATA_DIR, COUNTRY_MAP

SCRIPT = ROOT / "tools" / "gmaps_search.py"
CLEANER = ROOT / "tools" / "clean_and_rebuild_verified_catalogs.py"
INTEL_EXTRACTOR = ROOT / "tools" / "extract_intel.py"

DELAY = 75           # seconds between requests
DURATION = 20 * 60   # 20 minutes total

QUERIES = [
    # ── MD (Moldova) ────────────────────────────────────────────────────────
    ("MD", "aparate injectat tutun angro Moldova Chisinau", "A"),
    ("MD", "accesorii fumat distribuitor angro Chisinau", "A"),
    ("MD", "distribuitor produse din tutun Moldova", "A"),

    # ── RO (Romania) ────────────────────────────────────────────────────────
    ("RO", "masini electrice de rulat tutun angrosist Romania", "A"),
    ("RO", "aparate de injectat tutun distribuitor Bucuresti", "A"),
    ("RO", "tuburi tigari accesorii fumat en-gros Cluj Timisoara", "A"),
    ("RO", "distribuitor articole fumat buralist Romania", "A"),

    # ── LT (Lithuania) ──────────────────────────────────────────────────────
    ("LT", "elektrinės cigarečių pildymo mašinos didmena Lietuva", "A"),
    ("LT", "tabako sukimo mašinėlės didmeninė prekyba Vilnius", "A"),
    ("LT", "rūkymo reikmenys didmena Kaunas Klaipeda", "A"),

    # ── LV (Latvia) ─────────────────────────────────────────────────────────
    ("LV", "cigarešu tīšanas mašīnas vairumtirdzniecība Rīga", "A"),
    ("LV", "tabakas izstrādājumi un piederumi vairumā Latvija", "A"),
    ("LV", "elektriskās cigarešu uzpildes mašīnas vairumtirdzniecība", "A"),

    # ── SI (Slovenia) ───────────────────────────────────────────────────────
    ("SI", "električni strojčki za polnjenje cigaret veleprodaja Slovenija", "A"),
    ("SI", "tobačni pribor in aparati za cigarete Ljubljana Maribor", "A"),

    # ── HR (Croatia) ────────────────────────────────────────────────────────
    ("HR", "električne punilice za cigarete veleprodaja Hrvatska", "A"),
    ("HR", "pribor za motanje duhana veleprodaja Zagreb", "A"),
]


def normalize(name: str) -> str:
    return re.sub(r"\s+", " ", name.lower().strip())


def build_blocklist() -> set[str]:
    """Load all existing names and Place IDs across all catalogs."""
    blocklist: set[str] = set()
    for cat_path in DATA_DIR.glob("*/catalog-[AB]-*.csv"):
        if ".snapshots" in str(cat_path):
            continue
        try:
            for row in csv.DictReader(open(cat_path, encoding="utf-8")):
                name = row.get("nazwa_firmy", "").strip()
                if name:
                    blocklist.add(normalize(name))
                rid = row.get("rejestr_id", "").strip()
                if rid and rid.startswith("ChIJ"):
                    blocklist.add(rid)
        except Exception:
            pass
    return blocklist


def run_query(country: str, query: str, catalog: str, dry_run: bool = False) -> bool:
    cmd = [
        sys.executable, str(SCRIPT),
        "--query", query,
        "--country", country,
        "--catalog", catalog,
        "--write"
    ]
    if dry_run:
        cmd.append("--dry-run")
    try:
        r = subprocess.run(cmd, timeout=70, cwd=str(ROOT))
        return r.returncode == 0
    except Exception as e:
        print(f"  ❌ Error executing query: {e}")
        return False


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 70)
    print("BILLSzuka — 20-Min Targeted Catalog-A Sweep (Underrepresented Countries)")
    print(f"  Target: MD, RO, LT, LV, SI, HR | Total queries: {len(QUERIES)}")
    print(f"  Delay: {DELAY}s | Duration budget: 20 minutes")
    print(f"  Start: {time.strftime('%H:%M:%S')} | Target finish: {time.strftime('%H:%M:%S', time.localtime(time.time() + DURATION))}")
    print("=" * 70)

    blocklist = build_blocklist()
    print(f"📋 Loaded dedup blocklist with {len(blocklist)} existing entries.")

    start_time = time.time()
    deadline = start_time + DURATION
    ok_count = 0
    fail_count = 0

    for i, (country, query, catalog) in enumerate(QUERIES, start=1):
        now = time.time()
        if now >= deadline:
            print("\n⏰ 20-minute deadline reached. Stopping sweep.")
            break

        elapsed_min = (now - start_time) / 60
        remaining_min = (deadline - now) / 60
        print(f"\n[{elapsed_min:.1f}m / {remaining_min:.1f}m left] [{i}/{len(QUERIES)}] [{country}] [Cat-{catalog}] — \"{query}\"")

        success = run_query(country, query, catalog, dry_run)
        if success:
            ok_count += 1
        else:
            fail_count += 1

        if i < len(QUERIES):
            remaining_time = deadline - time.time()
            if remaining_time < DELAY + 15:
                print("  ⏱ Not enough time for next query + sleep. Wrapping up.")
                break
            print(f"  💤 Gentle delay ({DELAY}s)...")
            time.sleep(DELAY)

    total_min = (time.time() - start_time) / 60
    print("\n" + "=" * 70)
    print(f"SWEEP COMPLETED in {total_min:.1f} min | ✅ {ok_count} Successful | ❌ {fail_count} Failed")
    print("=" * 70)

    if not dry_run and ok_count > 0:
        print("\n🧹 Running post-sweep clean & rebuild...")
        subprocess.run([sys.executable, str(CLEANER)], cwd=str(ROOT))
        
        print("\n📊 Extracting strategic intel...")
        subprocess.run([sys.executable, str(INTEL_EXTRACTOR), "--target", "both"], cwd=str(ROOT))

    print("\n✅ Targeted sweep run complete.")


if __name__ == "__main__":
    main()
