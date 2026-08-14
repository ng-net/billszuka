#!/usr/bin/env python3
"""
gmaps_45min_sweep.py — Focused 45-minute Places API sweep for nabijarka/tobacco distributor leads.

Strategy:
  - All 11 non-PL countries: CZ, SK, RO, LT, LV, EE, FR, MD, BG, SI, HR
  - Nabijarka-specific queries (cigarette tube injector language) → catalog-A targeting
  - Generic tobacco wholesale queries → catalog-B fallback
  - Pre-sweep dedup: build blocklist from ALL existing catalog-A and catalog-B entries
  - 90s gap between requests to stay well under API rate limits
  - Time-budgeted: stops gracefully before 45-min deadline
  - Post-sweep: runs gmaps_clean_and_verify.py automatically

Usage:
  python3 tools/gmaps_45min_sweep.py
  python3 tools/gmaps_45min_sweep.py --dry-run
"""

import csv
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from config import COUNTRY_MAP, DATA_DIR

SCRIPT = ROOT / "tools" / "gmaps_search.py"
DELAY = 90          # seconds between requests (polite / rate-safe)
DURATION = 45 * 60  # 45 minutes total budget

# ---------------------------------------------------------------------------
# Query plan: (country, query, catalog_target, priority)
# catalog_target: "A" = nabijarka/accessory distributor → catalog-A
#                 "B" = generic tobacco wholesale → catalog-B
# priority: 1=highest (run first) … 3=nice-to-have (run if time allows)
# ---------------------------------------------------------------------------
QUERIES = [
    # ── CZ ──────────────────────────────────────────────────────────────────
    ("CZ", "nabiječka cigaret velkoobchod Praha", "A", 1),
    ("CZ", "plnička tabáku velkoobchod Brno", "A", 1),
    ("CZ", "tabák příslušenství velkoobchod Czech Republic", "B", 2),
    ("CZ", "velkoobchod tabák Ostrava distributor", "B", 2),

    # ── SK ──────────────────────────────────────────────────────────────────
    ("SK", "plničky cigariet veľkoobchod Bratislava", "A", 1),
    ("SK", "tabakové príslušenstvo distribútor Slovakia", "A", 1),
    ("SK", "veľkoobchod tabak Bratislava distributor", "B", 2),

    # ── RO ──────────────────────────────────────────────────────────────────
    ("RO", "injectoare tigari angrosist Romania", "A", 1),
    ("RO", "masina umplut tigari gros Bucuresti", "A", 1),
    ("RO", "accesorii tutun angrosist distribuitor Romania", "B", 2),

    # ── LT ──────────────────────────────────────────────────────────────────
    ("LT", "cigarečių pildymo mašina didmena Vilnius", "A", 1),
    ("LT", "tabako priedai didmeninė prekyba Lithuania", "A", 1),
    ("LT", "tabako didmenine prekyba Kaunas distributor", "B", 2),

    # ── LV ──────────────────────────────────────────────────────────────────
    ("LV", "cigarešu uzpildes mašīna vairumtirdzniecība Rīga", "A", 1),
    ("LV", "tabakas piederumi vairumtirdzniecība Latvia", "A", 1),
    ("LV", "tobacco accessories wholesale distributor Riga", "B", 2),

    # ── EE ──────────────────────────────────────────────────────────────────
    ("EE", "sigarettide täitemasin hulgimüük Tallinn", "A", 1),
    ("EE", "tubakatarvikud hulgimüük Estonia distributor", "A", 1),
    ("EE", "tobacco accessories wholesale Tallinn", "B", 2),

    # ── FR ──────────────────────────────────────────────────────────────────
    # FR note: generic Paris queries returned all retail — use B2B-specific terms
    ("FR", "machine injecteur cigarettes grossiste distributeur France", "A", 1),
    ("FR", "grossiste accessoires tabac distributeur France", "A", 1),
    ("FR", "distributeur tabac cigarettes Lyon Marseille grossiste", "B", 2),

    # ── MD ──────────────────────────────────────────────────────────────────
    ("MD", "masini injectat tigari angrosist Moldova", "A", 1),
    ("MD", "accesorii tutun gros Chisinau distribuitor", "B", 2),

    # ── BG ──────────────────────────────────────────────────────────────────
    ("BG", "машина за пълнене цигари едро дистрибутор България", "A", 1),
    ("BG", "тютюневи принадлежности едро дистрибутор София", "A", 1),
    ("BG", "tobacco accessories wholesale distributor Bulgaria Sofia", "B", 2),

    # ── SI ──────────────────────────────────────────────────────────────────
    ("SI", "stroji za polnjenje cigaret veleprodaja Ljubljana", "A", 1),
    ("SI", "tobačni pribor veleprodaja Slovenija distributer", "A", 1),
    ("SI", "tobacco accessories wholesale distributor Ljubljana", "B", 2),

    # ── HR ──────────────────────────────────────────────────────────────────
    ("HR", "stroj za punjenje cigareta veleprodaja Zagreb", "A", 1),
    ("HR", "duhanski pribor veleprodaja distributer Hrvatska", "A", 1),
    ("HR", "tobacco accessories wholesale Zagreb distributor", "B", 2),
]

# Sort: priority 1 first (nabijarka-specific), then priority 2 (generic)
QUERIES.sort(key=lambda x: x[3])


def normalize(name: str) -> str:
    return re.sub(r"\s+", " ", name.lower().strip())


def build_blocklist() -> set[str]:
    """Load all existing names from ALL catalog-A and catalog-B files for all non-PL countries."""
    blocklist: set[str] = set()
    for iso, dirname in COUNTRY_MAP.items():
        if iso == "PL":
            continue
        for cat in ["A", "B"]:
            fpath = DATA_DIR / dirname / f"catalog-{cat}-{iso}.csv"
            if not fpath.exists():
                continue
            try:
                for row in csv.DictReader(open(fpath, encoding="utf-8")):
                    name = row.get("nazwa_firmy", "").strip()
                    if name:
                        blocklist.add(normalize(name))
                    # Also block by rejestr_id (Place ID) if present
                    rid = row.get("rejestr_id", "").strip()
                    if rid and rid != "brak":
                        blocklist.add(rid)
            except Exception:
                pass
    return blocklist


def run_query(country: str, query: str, catalog: str, dry_run: bool = False) -> bool:
    """Execute one gmaps_search.py query. catalog-A targets are written to catalog-A."""
    cmd = [sys.executable, str(SCRIPT),
           "--query", query,
           "--country", country,
           "--catalog", catalog,
           "--write"]
    if dry_run:
        cmd.append("--dry-run")
    try:
        r = subprocess.run(cmd, timeout=75, cwd=str(ROOT))
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        print("  ⏱  TIMEOUT (75s)")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False


def print_banner(blocklist_size: int, total_queries: int):
    print("=" * 70)
    print("BILLSzuka — 45-min Multi-Country Nabijarka Sweep")
    print(f"  Target: 11 countries (excl. PL) | {total_queries} queries | {DELAY}s gap")
    print(f"  Dedup blocklist: {blocklist_size} existing entries loaded")
    print(f"  Strategy: nabijarka-specific → catalog-A | generic → catalog-B")
    print(f"  Start: {time.strftime('%H:%M:%S')} | Deadline: {time.strftime('%H:%M:%S', time.localtime(time.time() + DURATION))}")
    print("=" * 70)


def main():
    dry_run = "--dry-run" in sys.argv

    print("\n📋 Loading dedup blocklist from all non-PL catalogs...")
    blocklist = build_blocklist()

    p1 = sum(1 for q in QUERIES if q[3] == 1)
    p2 = sum(1 for q in QUERIES if q[3] == 2)
    print_banner(len(blocklist), len(QUERIES))
    print(f"  Priority 1 (nabijarka/A-catalog): {p1} queries")
    print(f"  Priority 2 (generic/B-catalog):   {p2} queries")

    if dry_run:
        print("\n⚠️  DRY-RUN MODE — no API calls, no writes\n")

    start = time.time()
    deadline = start + DURATION
    ok = fail = skipped = 0
    results_log = []

    for i, (country, query, catalog, priority) in enumerate(QUERIES):
        now = time.time()
        if now >= deadline:
            print("\n⏰ 45-minute deadline reached. Stopping.")
            break

        elapsed_m = (now - start) / 60
        remaining_m = (deadline - now) / 60
        label = "⭐A" if catalog == "A" else " B"
        print(f"\n[{elapsed_m:.1f}m | {remaining_m:.1f}m left] [{label}] [{country}] P{priority} — {query}")

        success = run_query(country, query, catalog, dry_run)
        if success:
            ok += 1
            results_log.append(f"✅ [{country}][{label}] {query}")
        else:
            fail += 1
            results_log.append(f"❌ [{country}][{label}] {query}")

        # Sleep between queries, but not after the last one
        if i < len(QUERIES) - 1:
            remaining_after = (deadline - time.time())
            if remaining_after < DELAY + 30:
                print("  Not enough time budget for next query + delay. Stopping.")
                break
            print(f"  💤 Sleeping {DELAY}s...")
            time.sleep(DELAY)

    elapsed_total = (time.time() - start) / 60
    print("\n" + "=" * 70)
    print(f"SWEEP COMPLETE in {elapsed_total:.1f}min | ✅ {ok} OK | ❌ {fail} Failed | ⏭ {skipped} Skipped")
    print("=" * 70)

    # Post-sweep: clean and verify
    if not dry_run and ok > 0:
        print("\n🧹 Running gmaps_clean_and_verify.py (noise removal + dedup + verify)...")
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "gmaps_clean_and_verify.py")],
            cwd=str(ROOT)
        )
        if result.returncode == 0:
            print("✅ Clean and verify complete.")
        else:
            print("⚠️  Clean/verify returned non-zero. Check output above.")

        # Mandatory: extract_intel
        print("\n📊 Running extract_intel.py --target both...")
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "extract_intel.py"), "--target", "both"],
            cwd=str(ROOT)
        )

    print("\n📋 Full results log:")
    for line in results_log:
        print(f"  {line}")
    print()


if __name__ == "__main__":
    main()
