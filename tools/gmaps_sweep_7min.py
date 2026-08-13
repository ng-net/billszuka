#!/usr/bin/env python3
"""
gmaps_sweep_7min.py - Gentle 7-minute Places API sweep.
Targets lowest catalog-A countries (excl. PL):
  LV(1), BG(2), EE(2), HR(2), MD(2), SI(2), FR(3), LT(3), RO(3)
~14 queries, 30s apart = stays well under API limits.
Results written directly to catalog-B CSVs via --write.
"""

import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "gmaps_search.py"
DELAY = 30          # seconds between requests
DURATION = 7 * 60   # 7 minutes

# 14 queries covering all 9 target countries
QUERIES = [
    ("LV", "tabaka vairumtirdznieciba Riga"),
    ("BG", "tobacco wholesale Sofia Bulgaria"),
    ("EE", "tobacco wholesale distributor Estonia"),
    ("HR", "veleprodaja duhana Zagreb"),
    ("MD", "distribuitor produse tutun Moldova"),
    ("SI", "veleprodaja tobacnih izdelkov Ljubljana"),
    ("FR", "grossiste tabac France"),
    ("LT", "tabako didmenine prekyba Vilnius"),
    ("RO", "comert cu ridicata tutun Bucuresti"),
    ("LV", "tobacco wholesale distributor Riga"),
    ("BG", "cigari edro distributor Bulgaria"),
    ("EE", "sigaretid hulgimyyja Eesti"),
    ("HR", "tobacco wholesale distributor Croatia"),
    ("FR", "distributeur tabac cigarettes Paris"),
]

def run(country, query):
    cmd = [sys.executable, str(SCRIPT), "--query", query, "--country", country, "--write"]
    print(f"  >> [{country}] {query}")
    try:
        r = subprocess.run(cmd, timeout=60, cwd=str(ROOT))
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        print("  TIMEOUT"); return False
    except Exception as e:
        print(f"  ERROR: {e}"); return False

def main():
    start = time.time()
    deadline = start + DURATION
    ok = fail = 0
    print("=" * 60)
    print("BILLSzuka -- 7-min Places sweep (LV,BG,EE,HR,MD,SI,FR,LT,RO)")
    print(f"  {len(QUERIES)} queries @ {DELAY}s gap")
    print("=" * 60)

    for i, (country, query) in enumerate(QUERIES):
        if time.time() >= deadline:
            print("Time limit reached."); break
        remaining = (deadline - time.time()) / 60
        elapsed = (time.time() - start) / 60
        print(f"\n[{elapsed:.1f}m elapsed | {remaining:.1f}m left] Query {i+1}/{len(QUERIES)}")
        if run(country, query): ok += 1
        else: fail += 1
        if i < len(QUERIES) - 1:
            if time.time() + DELAY >= deadline:
                print("Not enough time for next. Stopping."); break
            print(f"  Sleeping {DELAY}s...")
            time.sleep(DELAY)

    elapsed = (time.time() - start) / 60
    print("\n" + "=" * 60)
    print(f"DONE in {elapsed:.1f}min  OK:{ok}  Fail:{fail}  Total:{ok+fail}")
    print("=" * 60)
    print("Next: run python3 tools/verify_run.py")

if __name__ == "__main__":
    main()
