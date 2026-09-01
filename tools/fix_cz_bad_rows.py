#!/usr/bin/env python3
"""Fix the 6 bad CZ rows (CZ-B-017 to CZ-B-022) with column-shift issues."""

import csv

path = "/Users/ciepolml/Documents/Bills-Drive/BILLSzuka-28-Aug/data/Czechy/catalog-B-CZ.csv"

with open(path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# Fix rows where kategoria = 'B2B hurtownik' (descriptive, not a tier code)
BAD_KAT = "B2B hurtownik"
changes = 0
for row in rows:
    if row.get("kategoria", "").strip() == BAD_KAT:
        # Clear kategoria (these are manual entries without proper tier codes)
        row["kategoria"] = ""
        # If telefon is just '+420' (incomplete), clear it
        tel = row.get("telefon", "").strip()
        if tel == "+420":
            row["telefon"] = ""
        changes += 1
        print(f"Fixed {row.get('id')}: kategoria cleared, tel='{tel}'")

with open(path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Done: {changes} rows fixed")
