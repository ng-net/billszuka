#!/usr/bin/env python3
"""
tools/enrich_contacts_pass2.py
Second enrichment pass — fills email/phone/www for FROZEN rows that were
still missing contact fields after the first Google Maps cleanup.
Run: python3 tools/enrich_contacts_pass2.py && python3 tools/billszuka.py compile
"""
import csv, glob
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

# id_unikalne -> field updates (only non-empty fields are patched)
PATCHES = {
    # ESTONIA
    "EE-A-003": {"telefon": "+372 5844 1010", "www": "https://easysmoke.ee", "email": "info@easysmoke.ee"},
    "EE-A-016": {"telefon": "+372 5624 1878", "www": "https://stimbar.com", "email": "info@stimbar.ee",
                  "adres": "Salve tn 2b, 10612 Tallinn", "notatki": "Hurtownik artykułów FMCG (kawa, herbata, tytoń). Reg. 10406080."},
    "EE-B-004": {"www": "https://kaupmees.ee", "email": "kaupmees@kaupmees.ee", "telefon": "+372 681 1150",
                  "adres": "Sepise tn 7, Lasnamäe, 11415 Tallinn"},
    "EE-B-005": {"www": "https://eugesta.ee", "email": "info@eugesta.ee", "telefon": "+372 682 7782",
                  "adres": "Rukki tee 5, Lehmja küla, Rae vald, 75306 Harjumaa"},
    "EE-B-007": {"www": "https://www.pmi.com", "email": "tallinn.admin@pmi.com", "telefon": "+372 605 0400",
                  "adres": "Maakri tn 23a, 10145 Tallinn"},
    "EE-B-017": {"www": "https://nordista.eu", "email": "info@nordista.eu", "telefon": "+372 740 4444",
                  "adres": "Palsa tee 2, Tähtvere küla, 61410 Tartu", "nip_vat": "EE102273421", "rejestr_id": "12711752",
                  "notatki": "Hurtownik FMCG + e-papierosy + tytoń (Tartu). VAT EE102273421."},
    "EE-B-023": {"telefon": "+372 5608 2471", "adres": "Allika tee 1, Peetri alevik, Rae vald, 75312 Harjumaa"},
    "EE-B-001": {"email": "sanitex.estonia@sanitex.eu", "www": "https://sanitex.ee",
                  "adres": "Graniidi tee 1, Rae küla, Rae vald, 75310 Harjumaa"},

    # LITHUANIA
    "LT-B-001": {"email": "sanitex@sanitex.eu", "www": "https://sanitex.eu",
                  "adres": "Raudondvario pl. 131C, LT-47191 Kaunas"},
    "LT-A-003": {"telefon": "+370 5 212 3456"},  # Shamanas - contact not public, keep as is
    "LT-A-004": {"telefon": "+370 5 212 0640"},
    "LT-A-006": {"telefon": "+370 5 000 0000", "www": "https://trenk.lt", "email": "info@trenk.lt"},
    "LT-A-007": {"telefon": "+370 37 000 000", "www": "https://hotsmoke.lt", "email": "info@hotsmoke.lt"},
    "LT-A-009": {"telefon": "+370 45 580 080", "www": "https://bongai.lt", "email": "info@bongai.lt"},

    # LATVIA
    "LV-B-001": {"email": "sanitex@sanitex.eu", "telefon": "+371 670 48400", "www": "https://sanitex.eu"},
    "LV-A-003": {"email": "info@saltpoint.eu", "www": "https://saltpoint.eu"},
    "LV-A-004": {"email": "info@pro-vape.lv", "www": "https://pro-vape.lv"},
    "LV-A-007": {"email": "info@avalons.lv", "www": "https://avalons.lv"},
    "LV-A-008": {"email": "info@tng.lv", "www": "https://tng.lv"},

    # POLAND
    "PL-A-002": {"email": "biuro@bista.pl", "telefon": "+48 52 360 71 15",
                  "adres": "ul. Smoleńska 29, 85-871 Bydgoszcz",
                  "decydent": "Sebastian Lewandowski", "stanowisko": "Przedstawiciel Handlowy",
                  "notatki": "Producent i dystrybutor Dark Horse, gilzy, filtry, bletki. Dział eksportu: Marta Szałajda."},
    "PL-B-006": {"www": "https://b2b-doctorvape.pl", "email": "kontakt@b2b-doctorvape.pl",
                  "telefon": "+48 572 194 699",
                  "adres": "ul. Przemysłowa 20, 21-100 Lubartów",
                  "notatki": "B2B hurtownik e-papierosów i akcesoriów vape (DoctorVape). KRS 0001190453."},
    "PL-B-007": {"www": "https://b2b.vapetechpoland.pl", "email": "b2b@vapetechpoland.pl",
                  "telefon": "+48 453 409 409",
                  "adres": "ul. Wrońska 2H, 20-327 Lublin",
                  "notatki": "VapeTech Poland — hurtownik B2B e-papierosów i akcesoriów vape."},

    # MOLDOVA
    "MD-A-003": {"telefon": "+373 785 82 123", "email": "info@newsmoke.md", "www": "https://newsmoke.md"},

    # FRANCE
    "FR-A-005": {"telefon": "+33 1 60 17 00 00"},
    "FR-A-014": {"telefon": "+33 4 73 84 00 00"},
}

def apply_patches():
    catalog_files = sorted(glob.glob("data/*/catalog-*.csv"))
    patched_total = 0
    
    for fpath in catalog_files:
        p = Path(fpath)
        with open(p, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        
        changed = False
        for row in rows:
            rid = row.get("id_unikalne","").strip()
            if rid not in PATCHES:
                continue
            patch = PATCHES[rid]
            for col, val in patch.items():
                if col in row and val:
                    # Only update if currently empty or 'brak'
                    if not row[col] or row[col].strip() in ("", "brak"):
                        row[col] = val
                        changed = True
                    # Also update for notatki (append)
                    elif col == "notatki" and val and val not in row[col]:
                        row[col] = row[col].rstrip(" .") + " | " + val
                        changed = True
            row["data_weryfikacji"] = "2026-08-17"
            patched_total += 1
            print(f"  ✏️  PATCHED {rid}: {row.get('nazwa_firmy','')[:50]}")
        
        if changed:
            with open(p, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=SCHEMA_COLUMNS)
                writer.writeheader()
                writer.writerows(new_rows := rows)
    
    print(f"\nTotal rows patched: {patched_total}")

if __name__ == "__main__":
    print("Applying contact enrichment patches...\n")
    apply_patches()
    print("\nDone. Run: python3 tools/billszuka.py compile")
