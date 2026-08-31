#!/usr/bin/env python3
"""
tools/normalize_catalogs.py

Comprehensive normalization, sanity cleaning, and schema compliance for all BILLSzuka CSV catalogs.
Ensures exact 35 columns, correct quoting, eliminates empty/corrupted lines, and audits duplicates & hallucinations.
"""

import csv
import glob
import os
import re
import sys
from pathlib import Path

SCHEMA_COLUMNS = [
    "related_to", "rok_zalozenia", "id_unikalne", "kategoria", "nazwa_firmy",
    "kraj", "miasto", "adres", "nip_vat", "rejestr_id",
    "www", "kanal_zamiennik", "email", "telefon", "linkedin",
    "facebook", "instagram", "tiktok", "tier", "marki_nabijarki",
    "marka_wlasna_oem", "sourcing", "wolumen", "confidence_wolumen", "kanal_sprzedaży",
    "powinowactwo_nabijarki", "cross_sell_potential", "decydent", "stanowisko", "email_decydent",
    "zrodlo_danych", "data_weryfikacji", "flagi", "notatki", "rynek_skala"
]

# Index positions for swap detection (col 0 = related_to, col 1 = rok_zalozenia)
IDX_RELATED_TO = 0
IDX_ROK_ZALOZENIA = 1
RE_YEAR = re.compile(r"^\d{4}$")

# Swap-guard: columns that are ALLOWED to contain a bare year (YYYY).
# related_to should be an entity ID/name, not a year.
# If related_to holds a YYYY and rok_zalozenia is empty, it is the swap pattern.
def _detect_swap(row: list) -> bool:
    """Return True if related_to (col 0) is a bare YYYY and rok_zalozenia (col 1) is empty."""
    related = row[IDX_RELATED_TO].strip().strip("'")
    rok = row[IDX_ROK_ZALOZENIA].strip()
    return bool(RE_YEAR.match(related)) and not rok


def _repair_swap(row: list, row_id: str) -> bool:
    """Swap year from col 0 (related_to) into col 1 (rok_zalozenia), put 'brak' in col 0.

    Returns True if a swap was performed.
    """
    related = row[IDX_RELATED_TO].strip().strip("'")
    row[IDX_ROK_ZALOZENIA] = related
    row[IDX_RELATED_TO] = "brak"
    return True
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

COUNTRY_DIR_MAP = {
    "PL": "Polska", "CZ": "Czechy", "SK": "Słowacja", "SI": "Słowenia",
    "LT": "Litwa", "LV": "Łotwa", "EE": "Estonia", "FR": "Francja",
    "RO": "Rumunia", "BG": "Bułgaria", "HR": "Chorwacja", "MD": "Mołdawia",
    "RS": "Serbia",
}

def clean_row_data(row, header, filename):
    """Normalize row fields to match 35 schema columns."""
    if not row or not any(field.strip() for field in row):
        return None  # empty row
    
    # If row has more columns than schema, inspect and repair common overflow patterns
    if len(row) > 35:
        # Check if extra columns are due to unquoted commas in notes, flags, or address
        # Common offset: extra fields appended or split in notes
        # Let's inspect where the overflow occurred
        id_val = row[2] if len(row) > 2 else ""
        cat_val = row[3] if len(row) > 3 else ""
        name_val = row[4] if len(row) > 4 else ""
        
        # Build a 35-item array by aligning from start and end
        # Columns 0..30 (related_to through zrodlo_danych) are usually standard
        # Columns 31..34 (data_weryfikacji, flagi, notatki, rynek_skala)
        # Often notatki contains unquoted commas that caused splitting
        new_row = row[:31]
        trailing = row[31:]
        
        # Look for date in trailing (YYYY-MM-DD)
        date_idx = None
        for i, val in enumerate(trailing):
            if re.match(r"^\d{4}-\d{2}-\d{2}$", val.strip()):
                date_idx = i
                break
        
        if date_idx is not None:
            data_wer = trailing[date_idx].strip()
            rest = trailing[date_idx+1:]
            # rynek_skala is usually the last item (mały, średni, duży, Bardzo duży, etc.)
            if rest and rest[-1].strip().lower() in ["mały", "maly", "średni", "sredni", "duży", "duzy", "bardzo duży", "bardzo duzy", "do ustalenia"]:
                rynek_skala = rest[-1].strip()
                middle = rest[:-1]
            else:
                rynek_skala = "średni"
                middle = rest
            
            # middle contains flagi and notatki
            # usually flagi has emojis / FROZEN / PENDING / etc.
            flagi = middle[0].strip() if middle else ""
            notatki = " | ".join(m.strip() for m in middle[1:] if m.strip()) if len(middle) > 1 else ""
            
            new_row = row[:31] + [data_wer, flagi, notatki, rynek_skala]
        else:
            # Fallback truncation / merge
            new_row = row[:34] + [row[-1]]
            
        row = new_row
    elif len(row) < 35:
        row = row + [""] * (35 - len(row))
        
    return [field.strip() for field in row]

def audit_and_normalize_all():
    catalog_files = sorted(DATA_DIR.glob("*/catalog-*.csv"))
    print(f"Auditing {len(catalog_files)} catalog files...")
    
    total_cleaned_rows = 0
    all_rows = []
    seen_ids = set()
    duplicates = []
    hallucination_flags = []
    
    swap_warnings = []
    for fpath in catalog_files:
        p = Path(fpath)
        with open(p, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                print(f"Empty file: {fpath}")
                continue

            raw_rows = list(reader)

        cleaned_rows = []
        for idx, r in enumerate(raw_rows, start=2):
            cleaned = clean_row_data(r, header, p.name)
            if cleaned is None:
                continue

            # ---- Swap guard: related_to ↔ rok_zalozenia ----
            # Bug origin: enrichment pipeline (KRS/CEIDG/VIES import) or spreadsheet
            # paste accidentally placed a founding year in related_to (col 0) while
            # rok_zalozenia (col 1) stayed empty.  Pattern:
            #   related_to = '2017'  (a bare year, possibly quoted)
            #   rok_zalozenia = ''
            # Fix: move the year to rok_zalozenia, put 'brak' in related_to.
            row_id = cleaned[2]
            if _detect_swap(cleaned):
                _repair_swap(cleaned, row_id)
                swap_warnings.append((row_id, p.name, idx, cleaned[IDX_ROK_ZALOZENIA]))

            # Verify ID format
            if not row_id:
                # generate or report
                print(f"⚠️ Missing id_unikalne in {p.name} line {idx}: {cleaned[4]}")
            else:
                if row_id in seen_ids:
                    duplicates.append((row_id, cleaned[4], p.name, idx))
                seen_ids.add(row_id)
                
            # Audit for placeholder / fake data
            nip = cleaned[8]
            email = cleaned[12]
            name = cleaned[4]
            notes = cleaned[33]
            
            # Check fake patterns
            if "45293" in nip and "SK" in row_id:
                hallucination_flags.append((row_id, name, "Templated IČO 45293XXX series"))
            if "Centralna ulica" in cleaned[7]:
                hallucination_flags.append((row_id, name, "Templated address 'Centralna ulica'"))
            if re.match(r"^b2b\.sk\d+@", email):
                hallucination_flags.append((row_id, name, f"Templated email '{email}'"))
            if "ChIJ" in nip:
                # Google place ID accidentally in nip
                # Move to notes or zrodlo_danych
                cleaned[30] = f"Google Places ID: {nip} | {cleaned[30]}"
                cleaned[8] = ""
                
            cleaned_rows.append(cleaned)
            total_cleaned_rows += 1
            all_rows.append(cleaned)
            
        # Write back normalized CSV
        with open(p, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(SCHEMA_COLUMNS)
            writer.writerows(cleaned_rows)
            
        print(f"  ✓ {p.name}: {len(cleaned_rows)} normalized rows (35 columns).")
        
    print(f"\nTotal rows processed: {total_cleaned_rows}")
    if duplicates:
        print(f"⚠️ Found {len(duplicates)} duplicates:")
        for dup in duplicates:
            print(f"   - {dup}")
    else:
        print("✅ Zero duplicate IDs detected.")
        
    if hallucination_flags:
        print(f"⚠️ Detected {len(hallucination_flags)} suspicious/templated entries:")
        for h in hallucination_flags:
            print(f"   - {h}")
    else:
        print("✅ Zero templated placeholders detected.")

    if swap_warnings:
        print(f"⚠️ Detected & repaired {len(swap_warnings)} related_to↔rok_zalozenia swaps:")
        for row_id, fname, line, year in swap_warnings:
            print(f"   - {row_id} ({fname}:{line}) → rok_zalozenia='{year}', related_to='brak'")
    else:
        print("✅ Zero related_to↔rok_zalozenia column swaps detected.")

    return total_cleaned_rows

if __name__ == "__main__":
    audit_and_normalize_all()
