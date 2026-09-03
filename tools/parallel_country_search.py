#!/usr/bin/env python3
"""
parallel_country_search.py — Registry-first parallel lookup across many leads.

Given a batch JSON of [{country, ico, ja_kodas, registry_code, name, ...}, ...]
runs registry lookups in PARALLEL threads (max 8 workers) using
tools/registry_lookup.py. Designed to replace the slow sequential
"web search then registry" loop.

Usage:
  python3 tools/parallel_country_search.py --batch candidates.json
  python3 tools/parallel_country_search.py --batch candidates.json --workers 16

JSON output is a list of {input, result, status, error} objects.

The candidates JSON should look like:
  [
    {"country": "CZ", "ico": "63489821", "name": "Tabák Plus"},
    {"country": "LT", "ja_kodas": "303182002", "name": "Hordus UAB"},
    {"country": "EE", "registry_code": "10060432", "name": "Stimbar"},
    {"country": "HR", "name": "POGON KOOLTURA d.o.o."},
    ...
  ]

For countries without public API, the result is a NO_API stub with the
manual registry URL — the agent is then expected to do web_search +
web_fetch to extract the data.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry_lookup as rl


def lookup_one(item: dict) -> dict:
    """Run one lookup with error capture."""
    try:
        country = item.get("country", "")
        # Build kwargs from item
        kwargs = {k: v for k, v in item.items() if k != "country"}
        result = rl.lookup(country, **kwargs)
        return {"input": item, "result": result, "status": "OK"}
    except Exception as e:
        return {"input": item, "result": None, "status": "ERROR", "error": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True, help="JSON file with candidates")
    ap.add_argument("--workers", type=int, default=8,
                    help="Max parallel workers (default 8)")
    ap.add_argument("--output", help="Output JSON file (default stdout)")
    ap.add_argument("--summary", action="store_true",
                    help="Print human-readable summary instead of JSON")
    args = ap.parse_args()

    with open(args.batch) as f:
        batch = json.load(f)
    print(f"Processing {len(batch)} candidates with {args.workers} workers...",
          file=sys.stderr)

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(lookup_one, item): i for i, item in enumerate(batch)}
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                r = fut.result()
            except Exception as e:
                r = {"input": batch[idx], "result": None, "status": "ERROR",
                     "error": str(e)}
            results.append(r)

    # Sort by input order
    results.sort(key=lambda r: batch.index(r["input"]) if r["input"] in batch
                                       else 999)

    if args.summary:
        for r in results:
            inp = r["input"]
            res = r.get("result", {}) or {}
            status = res.get("status", r.get("status", "?"))
            name = (res.get("name") or inp.get("name", ""))[:50]
            print(f"{inp.get('country','?')}\t{status}\t{name}")
    else:
        out = json.dumps(results, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(out)
            print(f"Wrote {len(results)} results to {args.output}", file=sys.stderr)
        else:
            print(out)


if __name__ == "__main__":
    main()
