#!/usr/bin/env python3
"""Fix remaining validation criticals after schema normalization.

1. rynek_skala: regionalny→średni, lokalny/krajowy→mały, krajowy→duży
2. nip_vat: clear 'HR' placeholder from Veletabak (no OIB confirmed)
3. telefon: take first phone from multi-value entries
4. email: take first email from multi-value entries
"""

import csv
from pathlib import Path

RYNEK_MAP = {
    "regionalny": "średni",
    "lokalny/krajowy": "mały",
    "krajowy": "duży",
}

BASE = Path("/Users/ciepolml/Documents/Bills-Drive/BILLSzuka-28-Aug/data")


def fix_file(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    changes = 0
    for row in rows:
        # 1. rynek_skala
        v = row.get("rynek_skala", "").strip()
        if v in RYNEK_MAP:
            row["rynek_skala"] = RYNEK_MAP[v]
            changes += 1

        # 2. nip_vat: clear 'HR' placeholder
        if row.get("nip_vat", "").strip() == "HR":
            row["nip_vat"] = ""
            changes += 1

        # 3. telefon: first value only
        tel = row.get("telefon", "").strip()
        if ";" in tel or "," in tel:
            first = tel.split(";")[0].split(",")[0].strip()
            if first and first != tel:
                row["telefon"] = first
                changes += 1

        # 4. email: first value only
        em = row.get("email", "").strip()
        if ";" in em or "," in em:
            first = em.split(";")[0].split(",")[0].strip()
            if first and first != em:
                row["email"] = first
                changes += 1

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  {path.name}: {len(rows)} rows, {changes} changes")
    return changes


def main():
    total = 0
    for cat_dir in BASE.iterdir():
        if not cat_dir.is_dir():
            continue
        for csv_file in cat_dir.glob("catalog-B-*.csv"):
            total += fix_file(csv_file)
    print(f"Total: {total} changes")


if __name__ == "__main__":
    main()
