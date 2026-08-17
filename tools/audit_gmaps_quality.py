#!/usr/bin/env python3
"""
tools/audit_gmaps_quality.py

Audits all Google Maps-sourced rows across all BILLSzuka catalog CSVs.
Produces a quality report and flags thin rows for re-verification or removal.
Applies tiered quality decisions:
  - signals >= 3: KEEP (enough data to be real)
  - signals == 2: REVIEW (partial but salvageable)
  - signals <= 1: FLAG as DO-WERYFIKACJI (thin shell, needs enrichment or deletion)

Usage: python3 tools/audit_gmaps_quality.py
"""
import csv
import glob
from pathlib import Path

SCHEMA_COLUMNS = [
    "related_to","rok_zalozenia","id_unikalne","kategoria","nazwa_firmy",
    "kraj","miasto","adres","nip_vat","rejestr_id",
    "www","kanal_zamiennik","email","telefon","linkedin",
    "facebook","instagram","tiktok","tier","marki_nabijarki",
    "marka_wlasna_oem","sourcing","wolumen","confidence_wolumen","kanal_sprzedaży",
    "powinowactwo_nabijarki","cross_sell_potential","decydent","stanowisko","email_decydent",
    "zrodlo_danych","data_weryfikacji","flagi","notatki","rynek_skala"
]

def score_row(row):
    """Score a row 0-5 based on enrichment signals (non-empty, non-ChIJ)."""
    nip = row.get("nip_vat","").strip()
    email = row.get("email","").strip()
    www = row.get("www","").strip()
    tel = row.get("telefon","").strip()
    adres = row.get("adres","").strip()
    return sum([
        bool(nip and nip not in ("brak","") and "ChIJ" not in nip and len(nip) > 4),
        bool(email and email not in ("brak","") and "@" in email),
        bool(www and www not in ("brak","","https://brak") and "http" in www),
        bool(tel and tel not in ("brak","") and len(tel) > 5),
        bool(adres and adres not in ("brak","") and len(adres) > 8),
    ])

def audit_gmaps(flag_thin=True, min_signals=2):
    catalog_files = sorted(glob.glob("data/*/catalog-*.csv"))
    report = []
    total_gmaps = 0
    total_kept = 0
    total_flagged = 0
    
    modified_files = set()
    
    for fpath in catalog_files:
        p = Path(fpath)
        with open(p, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        modified = False
        new_rows = []
        for row in rows:
            rid = row.get("id_unikalne","")
            if "ChIJ" in row.get("rejestr_id",""):
                total_gmaps += 1
                signals = score_row(row)
                
                if signals < min_signals:
                    # Flag as thin
                    total_flagged += 1
                    existing_flags = row.get("flagi","")
                    if "DO-WERYFIKACJI" not in existing_flags and "FROZEN" not in existing_flags:
                        row["flagi"] = f"⚠️ DO-WERYFIKACJI (GPlaces thin, signals={signals}) | {existing_flags}".strip(" |")
                        modified = True
                    report.append({
                        "action": "FLAGGED" if flag_thin else "REPORTED",
                        "id": rid,
                        "name": row.get("nazwa_firmy","")[:50],
                        "file": p.name,
                        "signals": signals,
                        "nip": row.get("nip_vat","")[:30],
                        "email": row.get("email","")[:40],
                        "www": row.get("www","")[:60],
                    })
                else:
                    total_kept += 1
                    
            new_rows.append(row)
            
        if modified and flag_thin:
            with open(p, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=SCHEMA_COLUMNS)
                writer.writeheader()
                writer.writerows(new_rows)
            modified_files.add(p.name)
    
    print(f"\n=== GOOGLE MAPS QUALITY AUDIT REPORT ===")
    print(f"Total Google Maps-sourced rows (ChIJ in rejestr_id): {total_gmaps}")
    print(f"  Kept (signals >= {min_signals}): {total_kept}")
    print(f"  Flagged as thin (signals < {min_signals}): {total_flagged}\n")
    
    country_summary = {}
    for r in report:
        c = r["id"].split("-")[0]
        country_summary[c] = country_summary.get(c, 0) + 1
    
    print("Flagged rows by country:")
    for c, n in sorted(country_summary.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n} flagged")
    
    print(f"\nDetailed flagged rows (signals 0-1):")
    for r in sorted(report, key=lambda x: x["id"]):
        sig_icon = "🔴" if r["signals"] == 0 else "🟡"
        print(f"  {sig_icon} {r['id']:15s} | {r['file']:30s} | signals={r['signals']} | www={r['www'][:40]} | email={r['email'][:30]}")
    
    if modified_files:
        print(f"\nModified catalog files (flags applied):")
        for f in sorted(modified_files):
            print(f"  - {f}")
    
    print(f"\nRecommendation: Enrich or remove the {total_flagged} thin rows.")
    print("  Run 'python3 tools/billszuka.py compile' after enrichment.")
    
    return report

if __name__ == "__main__":
    audit_gmaps(flag_thin=True, min_signals=2)
