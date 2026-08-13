#!/usr/bin/env python3
"""
gmaps_retry_si_lt_ro.py - Targeted retry for missed/failed queries from sweep.
  SI: both attempts got 503 -> retry with multiple query variants
  LT/RO/FR: queries 8,9,14 not reached in 7min sweep
"""
import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "gmaps_search.py"
DELAY = 30

QUERIES = [
    ("SI", "veleprodaja tobacnih izdelkov Ljubljana"),
    ("SI", "tobacco wholesale Slovenia Ljubljana"),
    ("SI", "distributer cigaret Slovenija"),
    ("LT", "tabako didmenine prekyba Vilnius"),
    ("LT", "tobacco wholesale distributor Lithuania Kaunas"),
    ("RO", "comert cu ridicata tutun Bucuresti"),
    ("RO", "tobacco wholesale distributor Romania"),
    ("FR", "distributeur tabac cigarettes Paris"),
]

def run(country, query):
    cmd = [sys.executable, str(SCRIPT), "--query", query, "--country", country, "--write"]
    print(f"  >> [{country}] {query}")
    try:
        r = subprocess.run(cmd, timeout=60, cwd=str(ROOT))
        return r.returncode == 0
    except Exception as e:
        print(f"  ERROR: {e}"); return False

def main():
    ok = fail = 0
    print("=" * 60)
    print("BILLSzuka -- retry SI + missed LT/RO/FR queries")
    print(f"  {len(QUERIES)} queries @ {DELAY}s gap")
    print("=" * 60)
    for i, (cc, q) in enumerate(QUERIES):
        print(f"\n[Query {i+1}/{len(QUERIES)}]")
        if run(cc, q): ok += 1
        else: fail += 1
        if i < len(QUERIES) - 1:
            print(f"  Sleeping {DELAY}s...")
            time.sleep(DELAY)
    print(f"\nDONE  OK:{ok}  Fail:{fail}")

if __name__ == "__main__":
    main()
