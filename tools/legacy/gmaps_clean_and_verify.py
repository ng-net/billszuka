#!/usr/bin/env python3
"""
gmaps_clean_and_verify.py
1. Remove obvious retail/noise entries from catalog-B CSVs (new gmaps leads)
2. Deduplicate by Google Place ID (rejestr_id) and by normalized name+country
3. Translate any English notatki field content to Polish equivalents
4. Run verify_run.py to VIES-check and rebuild master.csv
"""

import csv, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR

# ── STEP 1: Retail / noise removal ──────────────────────────────────────────
# These appear in names/URLs and indicate retail shops, not B2B wholesalers
RETAIL_BLACKLIST = [
    "iqos", "relay ", "drugstore", "lounge bar", "vape shop", "vapista",
    "smoke shop", "bat.com", "jti.com", "imperialbrandsplc.com",
    "facebook.com", "instagram.com", "trafika", "civette",
    "fdj", " pmu", "nickel", "elfbar", "spirits & wine", "davidoff of geneva",
    "tabac des catacombes", "tabac de la bourse", "tabac saint-germain",
    "tabac le terminus", "tabac le voltaire", "tabac de la reynie",
    "art tabac", "beau drugstore", "7j/7j tabac", "tabac circle",
    "tabac du trocadero", "tabac des sports", "la tabatiere",
    "tabakas studija", "tabakas nams", "cigari ", "amstergrams",
    "ozzo smoke", "puffkalica", "nicobros", "happy cigars",
    "british american tobacco finland",  # wrong country (EE query returned FI)
    "souvenirs, tobacco", "telemax", "tisak", "dragor lux",
    "tabakas studija olimpia", "tabakas studija saharova",
    "tabakas studija dižozolu", "tabakas studija teika",
    "tabakas studija akropole", "tabakas studija interneta",
    "tabakeria art", "tabakeria ",
    "Tabak des Sports",
]

# These in name signal a real distributor / wholesale / B2B
DIST_WHITELIST_OVERRIDE = [
    "distribution", "distribut", "wholesale", "trading", "logistics",
    "export", "import", "veleprodaj", "vairumtird", "hulgimyyk",
    "didmenin", "grossiste", "edro ", "srl", " ltd", " as ",
    " sia ", "sp. z", "s.r.o", "d.o.o", " oü", "tabak invest",
    "noza distrib", "pw distribution", "nicorex", "prike as",
    "ltt as", "rasta 1", "imperial tobacco", "bat hrvatska",
    "jt international", "veletabak", "tobacco distribution",
    "fib trade", "m tobacco", "tobacco logistic", "tutun-ctc",
    "interbrands", "tabakum export",
]

# ── STEP 2: notatki Polish translations ─────────────────────────────────────
EN_TO_PL_NOTATKI = {
    "Google Maps result": "Wynik Google Maps",
    "tobacco shop": "sklep tytoniowy",
    "wholesale": "hurtownia",
    "distributor": "dystrybutor",
    "retail": "sprzedaż detaliczna",
    "vape shop": "sklep z e-papierosami",
    "cigar shop": "sklep z cygarami",
    "tobacco wholesale": "hurtownia tytoniowa",
    "tobacco distribution": "dystrybucja tytoniu",
}

def is_retail_noise(row: dict) -> bool:
    name = row.get("nazwa", "").lower()
    www  = row.get("www", "").lower()
    combined = name + " " + www

    # If any dist whitelist keyword present → keep regardless
    if any(k in combined for k in DIST_WHITELIST_OVERRIDE):
        return False

    # Check blacklist
    return any(k in combined for k in RETAIL_BLACKLIST)

def translate_notatki(text: str) -> str:
    if not text:
        return text
    for en, pl in EN_TO_PL_NOTATKI.items():
        text = text.replace(en, pl)
    return text

def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.lower().strip())

def clean_catalog(filepath: Path) -> tuple[int, int, int]:
    """Returns (original_count, removed_noise, removed_dups)."""
    with open(filepath, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    original = len(rows)

    # Remove retail noise
    cleaned = [r for r in rows if not is_retail_noise(r)]
    removed_noise = original - len(cleaned)

    # Translate notatki
    for r in cleaned:
        r["notatki"] = translate_notatki(r.get("notatki", ""))

    # Deduplicate: by rejestr_id (Place ID) first, then by normalized name+country
    seen_ids  = set()
    seen_keys = set()
    deduped   = []
    removed_dups = 0
    for r in cleaned:
        rid = r.get("rejestr_id", "").strip()
        key = (normalize_name(r.get("nazwa", "")), r.get("kraj", "").strip().upper())
        if rid and rid in seen_ids:
            removed_dups += 1
            continue
        if key[0] and key in seen_keys:
            removed_dups += 1
            continue
        if rid:
            seen_ids.add(rid)
        seen_keys.add(key)
        deduped.append(r)

    # Write back
    if not deduped:
        return original, removed_noise, removed_dups

    fieldnames = list(deduped[0].keys())
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped)

    return original, removed_noise, removed_dups


def main():
    targets = ["CZ", "SK", "LV", "BG", "EE", "HR", "MD", "SI", "FR", "LT", "RO"]  # all non-PL
    catalogs = ["A", "B"]

    print("=" * 60)
    print("Step 1: Cleaning catalog-A and catalog-B CSVs (all non-PL)")
    print("=" * 60)

    total_noise = 0
    total_dups  = 0
    total_orig  = 0

    for cc in targets:
        for cat in catalogs:
            files = [f for f in DATA_DIR.rglob(f"catalog-{cat}-{cc}.csv")
                     if ".snapshots" not in str(f)]
            if not files:
                continue
            fp = files[0]
            orig, noise, dups = clean_catalog(fp)
            total_orig  += orig
            total_noise += noise
            total_dups  += dups
            kept = orig - noise - dups
            if noise > 0 or dups > 0:
                print(f"  {cc} [{cat}]: {orig} → kept {kept}  (removed {noise} noise, {dups} dups)")
            else:
                print(f"  {cc} [{cat}]: {orig} rows — clean ✓")

    print(f"\n  TOTAL: {total_orig} → removed {total_noise} retail/noise + {total_dups} duplicates")

    print("\n" + "=" * 60)
    print("Step 2: Running verify_run.py (VIES + master rebuild)")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "verify_run.py")],
        cwd=str(ROOT)
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
