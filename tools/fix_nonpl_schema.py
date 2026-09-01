#!/usr/bin/env python3
"""Fix schema issues in non-PL catalog-B CSVs.

Fixes:
1. tier: 'duży/średni/mały' → 'hurtownik/detalista/reseller'
2. rynek_skala: 'ogólnokrajowy' → 'duży'
3. kraj: fill missing ISO codes from directory name
4. marki_nabijarki: move to notatki (B rows shouldn't have this)
5. Add missing canonical columns with defaults
6. CZ: full schema migration to 35-column canonical
"""

import csv
import os
import re
from pathlib import Path

# ISO code from directory name
ISO_MAP = {
    "Bułgaria": "BG",
    "Chorwacja": "HR",
    "Czechy": "CZ",
    "Estonia": "EE",
    "Francja": "FR",
    "Litwa": "LT",
    "Mołdawia": "MD",
    "Rumunia": "RO",
    "Serbia": "RS",
    "Słowacja": "SK",
    "Słowenia": "SI",
    "Łotwa": "LV",
}

TIER_MAP = {
    "duży": "hurtownik",
    "średni": "hurtownik",
    "mały": "reseller",
}

RYNEK_MAP = {
    "ogólnokrajowy": "duży",
}

CANONICAL_COLUMNS = [
    "kraj", "id", "nazwa", "miasto", "adres", "www", "wolumen",
    "confidence_wolumen", "rejestr_id", "nip_vat", "rok_zalozenia",
    "tier", "marki_nabijarki", "marka_wlasna_oem", "powinowactwo_nabijarki",
    "kategoria", "rynek_skala", "cross_sell_potential", "kanal_sprzedaży",
    "kanal_zamiennik", "decydent", "stanowisko", "email_decydent", "email",
    "telefon", "notatki", "linkedin", "facebook", "instagram", "tiktok",
    "data_weryfikacji", "sourcing", "zrodlo_danych", "flagi", "related_to",
]

# CZ old schema → canonical mapping
CZ_OLD_TO_CANONICAL = {
    "id": "id",
    "nazwa_firmy": "nazwa",
    "miasto": "miasto",
    "www": "www",
    "kategoria": "kategoria",
    "tier": "tier",
    "email": "email",
    "telefon": "telefon",
    "kanal_sprzedaży": "kanal_sprzedaży",
    "decydent": "decydent",
    "powinowactwo_nabijarki": "powinowactwo_nabijarki",
    "marki_nabijarki": "marki_nabijarki",
    "notatki": "notatki",
    "sourcing": "sourcing",
    "flagi": "flagi",
    "wolumen": "wolumen",
    "confidence_wolumen": "confidence_wolumen",
    "rejestr_id": "rejestr_id",
    "vat_id": "nip_vat",
    "address": "adres",
}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fix_row(row, iso):
    changed = False

    # 1. Fill missing kraj
    if not row.get("kraj", "").strip():
        row["kraj"] = iso
        changed = True

    # 2. Fix tier
    tier = row.get("tier", "").strip()
    if tier in TIER_MAP:
        row["tier"] = TIER_MAP[tier]
        changed = True

    # 3. Fix rynek_skala
    rynek = row.get("rynek_skala", "").strip()
    if rynek in RYNEK_MAP:
        row["rynek_skala"] = RYNEK_MAP[rynek]
        changed = True

    # 4. Move marki_nabijarki to notatki if present and not empty
    marki = row.get("marki_nabijarki", "").strip()
    if marki and marki not in ["PowerMatic", "do weryfikacji", "brak", "n/a"]:
        existing_notatki = row.get("notatki", "").strip()
        combined = f"{existing_notatki} | marki_nabijarki: {marki}".strip(" |")
        row["notatki"] = combined
        row["marki_nabijarki"] = ""
        changed = True

    # 5. Ensure all canonical columns exist
    for col in CANONICAL_COLUMNS:
        if col not in row or row[col] is None:
            row[col] = ""

    return changed, row


def migrate_cz_row(row):
    """Convert CZ old-schema row to canonical 35-column."""
    new_row = {col: "" for col in CANONICAL_COLUMNS}
    for old_col, value in row.items():
        canon = CZ_OLD_TO_CANONICAL.get(old_col, old_col)
        if canon in new_row:
            new_row[canon] = value
    return new_row


def process_catalog(path, iso, is_cz=False):
    rows, fieldnames = read_csv(path)
    if not rows:
        print(f"  {path.name}: empty, skipping")
        return 0

    changes = 0
    new_rows = []

    if is_cz:
        # CZ: full schema migration
        for row in rows:
            new_row = migrate_cz_row(row)
            new_row["kraj"] = iso
            changed, _ = fix_row(new_row, iso)
            if changed:
                changes += 1
            new_rows.append(new_row)
        write_csv(path, new_rows, CANONICAL_COLUMNS)
        print(f"  {path.name}: migrated {len(new_rows)} rows, {changes} changes")
    else:
        for row in rows:
            changed, fixed = fix_row(row, iso)
            if changed:
                changes += 1
            new_rows.append(fixed)
        # Keep original fieldnames + fill missing ones
        all_fields = list(dict.fromkeys(fieldnames + CANONICAL_COLUMNS))
        write_csv(path, new_rows, all_fields)
        print(f"  {path.name}: {len(new_rows)} rows, {changes} changes")

    return changes


def main():
    base = Path("/Users/ciepolml/Documents/Bills-Drive/BILLSzuka-28-Aug/data")
    total_changes = 0

    for dirname, iso in ISO_MAP.items():
        catalog_path = base / dirname / f"catalog-B-{iso}.csv"
        if not catalog_path.exists():
            print(f"  {catalog_path.name}: not found, skipping")
            continue

        changes = process_catalog(catalog_path, iso, is_cz=(iso == "CZ"))
        total_changes += changes

    print(f"\nTotal changes: {total_changes}")


if __name__ == "__main__":
    main()
