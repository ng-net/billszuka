#!/usr/bin/env python3
"""
freeze_baseline.py — Update frozen-baseline.json + row-hashes.json with new SK FROZEN rows.

17 new FROZEN rows from SK intake:
  - 14 from Marceli Zweryfikowany (now FROZEN with audit flag for 8 templated)
  - 3 from VIES live (DanCzek, TifanTEX, Tabak Invest Slovakia)

Updates:
  - data/.verify-state/row-hashes.json (add 37 SK rows)
  - tools/.verify-state/frozen-baseline.json (add 17 FROZEN SK rows to by_country_file + master)
"""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka")
CATALOG_A = ROOT / "data/Słowacja/catalog-A-SK.csv"
CATALOG_B = ROOT / "data/Słowacja/catalog-B-SK.csv"
ROW_HASHES = ROOT / "data/.verify-state/row-hashes.json"
FROZEN_BASELINE = ROOT / "tools/.verify-state/frozen-baseline.json"


def hash_row(row: dict) -> str:
    """sha256 of row, excluding flagi and data_weryfikacji (same as verify_run.py)."""
    h = hashlib.sha256()
    skip = {"flagi", "data_weryfikacji", None, ""}
    for k in sorted((k_ for k_ in row.keys() if k_ not in skip), key=lambda x: x or ""):
        h.update((k or "").encode())
        h.update(b"=")
        h.update((row.get(k) or "").strip().encode())
        h.update(b"|")
    return h.hexdigest()[:16]


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    # ── 1. Update row-hashes.json ──
    rh_state = {"files": {}, "last_run": None}
    if ROW_HASHES.exists():
        rh_state = json.loads(ROW_HASHES.read_text())

    a_rows = read_csv(CATALOG_A)
    b_rows = read_csv(CATALOG_B)

    new_a_hashes = {r["id_unikalne"]: hash_row(r) for r in a_rows}
    new_b_hashes = {r["id_unikalne"]: hash_row(r) for r in b_rows}

    rh_state["files"]["data/Słowacja/catalog-A-SK.csv"] = new_a_hashes
    rh_state["files"]["data/Słowacja/catalog-B-SK.csv"] = new_b_hashes
    rh_state["last_run"] = datetime.now(timezone.utc).astimezone().isoformat()
    ROW_HASHES.write_text(json.dumps(rh_state, indent=2, ensure_ascii=False))
    print(f"Updated {ROW_HASHES.relative_to(ROOT)}: catalog-A-SK ({len(new_a_hashes)} rows), catalog-B-SK ({len(new_b_hashes)} rows)")

    # ── 2. Update frozen-baseline.json ──
    fb = json.loads(FROZEN_BASELINE.read_text())

    # Identify FROZEN rows (have FROZEN in flagi, not PENDING_API / DO-WERYFIKACJI / templated warning)
    # We treat:
    #   ✅ FROZEN → count
    #   ⚠️ FROZEN (templated) → also count (Marceli's verification)
    #   ⏳ PENDING_API → skip
    #   ⚠️ DO-WERYFIKACJI → skip
    frozen_a = [r for r in a_rows if "FROZEN" in r.get("flagi", "")]
    frozen_b = [r for r in b_rows if "FROZEN" in r.get("flagi", "")]
    print(f"FROZEN rows: A={len(frozen_a)}, B={len(frozen_b)}, total={len(frozen_a) + len(frozen_b)}")

    # Update by_country_file
    a_ids = [r["id_unikalne"] for r in frozen_a]
    b_ids = [r["id_unikalne"] for r in frozen_b]
    fb["by_country_file"]["data/Słowacja/catalog-A-SK.csv"] = a_ids
    fb["by_country_file"]["data/Słowacja/catalog-B-SK.csv"] = b_ids

    # Add to master list (remove existing SK entries first to avoid dupes)
    fb["master"] = [m for m in fb["master"] if m.get("kraj") != "SK"]
    for r in frozen_a + frozen_b:
        fb["master"].append({
            "id": r["id_unikalne"],
            "kraj": r["kraj"],
            "hash": hash_row(r),
        })

    # Update stats
    fb["stats"]["frozen_count"] = len(fb["master"])
    files_with_frozen = sum(1 for v in fb["by_country_file"].values() if v)
    fb["stats"]["files"] = files_with_frozen
    fb["captured_at"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    FROZEN_BASELINE.write_text(json.dumps(fb, indent=2, ensure_ascii=False))
    print(f"Updated {FROZEN_BASELINE.relative_to(ROOT)}: frozen_count={fb['stats']['frozen_count']}, files={files_with_frozen}")

    # ── 3. Summary ──
    from collections import Counter
    counter = Counter(m["kraj"] for m in fb["master"])
    print("\nFrozen by country:")
    for k, v in sorted(counter.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print(f"  Total: {sum(counter.values())}")


if __name__ == "__main__":
    main()
