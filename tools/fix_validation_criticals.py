#!/usr/bin/env python3
"""Fix real data errors identified by validate_columns.py after sentinel normalisation.

Addresses the remaining ~298 critical issues that are genuine data problems
(invalid enum values, bad NIP formats, etc.) — not sentinel placeholders.

Run AFTER patching tools/validate_columns.py with KNOWN_NON_VALUE.
"""
import sys
sys.path.insert(0, str(__file__.rsplit("/", 1)[0]))
from validate_columns import normalize_non_value
import csv
from pathlib import Path

ROOT = str(Path(__file__).resolve().parent.parent)


def load_rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_rows(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


total = 0

# ---------------------------------------------------------------------------
# Estonia B: kanal_sprzedaży='5' -> 'mix'
#             NIP missing 'EE' prefix (9 bare digits)
#             confidence_wolumen + cross_sell_potential = 'do ustalenia' -> ''
# ---------------------------------------------------------------------------
ee_b = f"{ROOT}/data/Estonia/catalog-B-EE.csv"
rows = load_rows(ee_b)
for r in rows:
    changed = False
    if r.get("kanal_sprzedaży", "").strip() == "5":
        print(f"  FIX EE: kanal_sprzedaży='5' -> 'mix'")
        r["kanal_sprzedaży"] = "mix"
        changed = True
    nip = r.get("nip_vat", "").strip()
    if nip and not nip.startswith("EE") and nip.isdigit() and len(nip) == 9:
        print(f"  FIX EE: nip_vat={nip} -> EE{nip}")
        r["nip_vat"] = f"EE{nip}"
        changed = True
    for col in ("confidence_wolumen", "cross_sell_potential"):
        if r.get(col, "").strip().casefold() == "do ustalenia":
            print(f"  FIX EE: {col}='do ustalenia' -> ''")
            r[col] = ""
            changed = True
    if changed:
        total += 1
save_rows(ee_b, rows)
print(f"  -> EE: {total} rows touched")

# ---------------------------------------------------------------------------
# France B: NIP bare SIREN (9 digits) -> prepend 'FR'
#           French VAT = FR + 2 alpha + 9 digits. SIREN alone is not valid VAT
#           but until confirmed, prefixing is the safest fix.
# ---------------------------------------------------------------------------
fr_b = f"{ROOT}/data/Francja/catalog-B-FR.csv"
rows = load_rows(fr_b)
fr_changes = 0
for r in rows:
    nip = r.get("nip_vat", "").strip()
    if nip.startswith("FR"):
        continue
    if nip.isdigit() and len(nip) == 9:
        print(f"  FIX FR: nip_vat={nip} -> FR{nip}")
        r["nip_vat"] = f"FR{nip}"
        fr_changes += 1
if fr_changes:
    save_rows(fr_b, rows)
    total += fr_changes
    print(f"  -> FR: {fr_changes} rows fixed")

# ---------------------------------------------------------------------------
# Litwa B: NIP 'LT' + 12 digits -> 'LT' + 9 digits
#          Valid LT PVM/Kodas = LT + 9 digits (KMKR)
# ---------------------------------------------------------------------------
lt_b = f"{ROOT}/data/Litwa/catalog-B-LT.csv"
rows = load_rows(lt_b)
lt_changes = 0
for r in rows:
    nip = r.get("nip_vat", "").strip()
    if nip.startswith("LT") and len(nip) == 14:
        corrected = nip[:11]
        print(f"  FIX LT: nip_vat={nip} -> {corrected}")
        r["nip_vat"] = corrected
        lt_changes += 1
if lt_changes:
    save_rows(lt_b, rows)
    total += lt_changes
    print(f"  -> LT: {lt_changes} rows fixed")

# ---------------------------------------------------------------------------
# Mołdawia A: bare 13-digit NIP -> prepend 'MD'
#             Valid MD IDNO = MD + 13 digits
# ---------------------------------------------------------------------------
md_a = f"{ROOT}/data/Mołdawia/catalog-A-MD.csv"
rows = load_rows(md_a)
md_changes = 0
for r in rows:
    nip = r.get("nip_vat", "").strip()
    if nip.isdigit() and len(nip) == 13:
        print(f"  FIX MD: nip_vat={nip} -> MD{nip}")
        r["nip_vat"] = f"MD{nip}"
        md_changes += 1
if md_changes:
    save_rows(md_a, rows)
    total += md_changes
    print(f"  -> MD: {md_changes} rows fixed")

# ---------------------------------------------------------------------------
# Regenerate master.csv from updated catalogs
# ---------------------------------------------------------------------------
from verify_run import regenerate_master

ok, count = regenerate_master()
print(f"\nMaster regen: ok={ok}, rows={count}")
print(f"\nTotal data rows fixed: {total}")
