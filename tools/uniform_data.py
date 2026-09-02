#!/usr/bin/env python3
"""
tools/uniform_data.py — Unified data cleaner & standardizer for all BILLSzuka catalogs.

Ensures:
1. Canonical 35-column schema alignment.
2. Canonical enum standardisation for rynek_skala, tier, kategoria.
3. Phone number formatting with international dial codes.
4. Clean https:// website URLs and lowercase email addresses.
5. Fixes known shifted fields in PL-A-003, PL-B-014/015/020, EE-B-018..022.
6. Cleans and aligns NIP/VAT and registry numbers.
"""

import csv
import glob
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR

DIAL_CODES = {
    "PL": "+48",
    "CZ": "+420",
    "SK": "+421",
    "RO": "+40",
    "LT": "+370",
    "LV": "+371",
    "EE": "+372",
    "FR": "+33",
    "MD": "+373",
    "BG": "+359",
    "SI": "+386",
    "HR": "+385",
}

SKALA_MAP = {
    "bardzo duży": "duży",
    "bardzo duzy": "duży",
    "duży": "duży",
    "duzy": "duży",
    "średni": "średni",
    "sredni": "średni",
    "mały": "mały",
    "maly": "mały",
    "mali": "mały",
}


def clean_url(url: str) -> str:
    url = url.strip()
    if not url or url.lower() in ["brak", "n/a", "-", "none", "null"]:
        return ""
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    # remove trailing slashes
    url = re.sub(r"/+$", "", url)
    return url


def clean_email(email: str) -> str:
    email = email.strip().lower()
    if not email or email in ["brak", "n/a", "-", "none", "null"]:
        return ""
    # remove trailing semicolons/commas/spaces
    email = email.strip(";,").strip()
    return email


def clean_phone(phone: str, iso: str) -> str:
    phone = phone.strip()
    if not phone or phone.lower() in ["brak", "n/a", "-", "none", "null"]:
        return ""
    # standardize multiple spaces or weird separators
    phone = re.sub(r"\s+", " ", phone).strip()
    dial = DIAL_CODES.get(iso, "")
    
    # If phone doesn't start with +, but has digits
    if dial and not phone.startswith("+"):
        # Check if starts with country code without +
        raw_dial = dial.replace("+", "")
        if phone.startswith(raw_dial) and len(phone) > len(raw_dial) + 5:
            phone = "+" + phone
        elif not phone.startswith("00") and len(re.sub(r"\D", "", phone)) in [9, 8, 7]:
            phone = f"{dial} {phone}"
    return phone


def clean_nip(nip: str, iso: str) -> str:
    nip = nip.strip()
    if not nip or nip.lower() in ["brak", "n/a", "-", "none", "null"]:
        return ""
    # Remove weird placeholders
    if "ChIJ" in nip:  # Google place ID accidentally in NIP
        return ""
    # Clean whitespace
    clean_digits = re.sub(r"[^0-9A-Za-z]", "", nip)
    if iso in ["PL", "CZ", "SK", "RO", "LT", "LV", "EE", "FR", "BG", "SI", "HR"]:
        if clean_digits.startswith(iso):
            return clean_digits
        elif clean_digits.isdigit() and len(clean_digits) >= 8:
            return f"{iso}{clean_digits}"
    return nip


def normalize_all_catalogs():
    print("🚀 [BILLSzuka] Normalizing and uniformizing all 24 catalogs...")
    total_processed = 0
    shifted_fixed = 0

    for iso, country_dir_name in COUNTRY_MAP.items():
        cdir = DATA_DIR / country_dir_name
        if not cdir.is_dir():
            continue

        for cat_type in ["A", "B"]:
            cfile = cdir / f"catalog-{cat_type}-{iso}.csv"
            if not cfile.exists():
                continue

            rows = []
            with cfile.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if not any(v.strip() for v in r.values()):
                        continue
                    row = {col: (r.get(col) or "").strip() for col in CANONICAL_SCHEMA}
                    cid = row.get("id", "")

                    # 1. Fix shifted rynek_skala
                    skala = row.get("rynek_skala", "")
                    if cid == "PL-A-003" and "Sieć 25+" in skala:
                        row["notatki"] = f"{skala} | {row['notatki']}".strip(" |")
                        row["rynek_skala"] = "duży"
                        shifted_fixed += 1
                    elif cid in ["PL-B-014", "PL-B-015", "PL-B-020"] and "FROZEN" in skala:
                        row["rynek_skala"] = "duży"
                        shifted_fixed += 1
                    elif cid.startswith("EE-B-018") or cid in ["EE-B-019", "EE-B-020", "EE-B-021", "EE-B-022"]:
                        if skala == "Estonia":
                            row["rynek_skala"] = "duży" if cid in ["EE-B-018", "EE-B-019"] else "średni"
                            shifted_fixed += 1

                    # 2. Canonical rynek_skala enum
                    curr_skala = row.get("rynek_skala", "").lower().strip()
                    if curr_skala in SKALA_MAP:
                        row["rynek_skala"] = SKALA_MAP[curr_skala]
                    elif not row.get("rynek_skala"):
                        tier_lower = row.get("tier", "").lower()
                        if "importer" in tier_lower or "koncern" in tier_lower or "producent" in tier_lower:
                            row["rynek_skala"] = "duży"
                        else:
                            row["rynek_skala"] = "średni"

                    # 3. Clean URLs & Emails
                    row["www"] = clean_url(row.get("www", ""))
                    row["email"] = clean_email(row.get("email", ""))
                    row["email_decydent"] = clean_email(row.get("email_decydent", ""))

                    # 4. Clean Phones
                    row["telefon"] = clean_phone(row.get("telefon", ""), iso)

                    # 5. Clean NIP/VAT
                    row["nip_vat"] = clean_nip(row.get("nip_vat", ""), iso)

                    # 6. Clean Country
                    if not row.get("kraj"):
                        row["kraj"] = iso

                    # 7. Clean Category
                    cat_val = row.get("kategoria", "").strip()
                    if not cat_val:
                        row["kategoria"] = "A4" if cat_type == "A" else "B8"

                    # 8. Clean Tier Enum
                    tier_val = (row.get("tier") or "").strip().lower()
                    VALID_TIERS = {"wyłączność", "autoryzowany", "reseller", "detalista", "marketplace", "producent", "hurtownik"}
                    if tier_val not in VALID_TIERS:
                        if any(w in tier_val for w in ["hurt", "dystryb", "wholesal", "import", "distrib"]):
                            row["tier"] = "hurtownik"
                        elif any(w in tier_val for w in ["sklep", "retail", "detal"]):
                            row["tier"] = "detalista"
                        elif "market" in tier_val or "allegro" in tier_val:
                            row["tier"] = "marketplace"
                        elif "prod" in tier_val:
                            row["tier"] = "producent"
                        else:
                            row["tier"] = "hurtownik"

                    # 9. Clean Foreign NIP (if NIP prefix doesn't match country, move to rejestr_id)
                    nip_val = row.get("nip_vat", "").strip()
                    if nip_val and len(nip_val) > 2 and nip_val[:2].isalpha():
                        nip_prefix = nip_val[:2].upper()
                        if nip_prefix != iso and nip_prefix in ["PL", "CZ", "SK", "RO", "LT", "LV", "EE", "FR", "BG", "SI", "HR", "ES", "DE", "IT", "UK", "GB"]:
                            if not row.get("rejestr_id"):
                                row["rejestr_id"] = nip_val
                            row["nip_vat"] = ""

                    # 10. Cross-sell potential for B
                    if cat_type == "B" and not row.get("cross_sell_potential"):
                        p = row.get("powinowactwo_nabijarki", "")
                        row["cross_sell_potential"] = "wysoki" if p in ["4", "5"] else "średni"

                    rows.append(row)
                    total_processed += 1

            # Write back
            with cfile.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
                writer.writeheader()
                writer.writerows(rows)
            print(f"  ✓ {cfile.relative_to(DATA_DIR)}: {len(rows)} uniform rows")

    print(f"\n✅ Total rows normalized: {total_processed}")
    print(f"   Shifted rows repaired: {shifted_fixed}")


if __name__ == "__main__":
    normalize_all_catalogs()
