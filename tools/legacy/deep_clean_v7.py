#!/usr/bin/env python3
"""
tools/deep_clean_v7.py — Final verification sweep & directory artifact cleanup.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR

REMOVE_IDS = {
    "PL-B-140": "Unresolvable directory scrape artifact without KRS/CEIDG (PAKO FW Koło)",
    "PL-B-142": "Unresolvable directory scrape artifact without KRS/CEIDG (Hurtownia Starogard)",
    "PL-B-143": "Unresolvable directory scrape artifact without KRS/CEIDG (Golden FHU Głubczyce)",
    "PL-B-144": "Unresolvable directory scrape artifact without KRS/CEIDG (EDMAR PH Koło)",
    "PL-B-145": "Unresolvable directory scrape artifact without KRS/CEIDG (Dymek Lublin)",
    "PL-B-146": "Unresolvable directory scrape artifact without KRS/CEIDG (Aleksander Ostrowski Olsztyn)",
    "PL-B-147": "Unresolvable directory scrape artifact without KRS/CEIDG (Aga Rzeszów)",
    "PL-B-148": "Unresolvable directory scrape artifact without KRS/CEIDG (ALFA Białystok)",
    "PL-B-149": "Unresolvable directory scrape artifact without KRS/CEIDG (Lorbad Sp. z o.o.)",
}

UPDATES = {
    "PL-B-150": {
        "nazwa_firmy": "\"KAMEL A.K. DEPIŃSKA-FOŁDA\" SPÓŁKA JAWNA",
        "nip_vat": "PL6652367882",
        "rejestr_id": "KRS 0000009417",
        "adres": "ul. Wioślarska 16, 62-510 Konin",
        "miasto": "Konin",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000009417 | REGON 311080171",
    },
    "PL-B-151": {
        "nazwa_firmy": "MINOS SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL7962427567",
        "rejestr_id": "KRS 0000189777",
        "adres": "ul. Lubelska 9, 26-600 Radom",
        "miasto": "Radom",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000189777 | REGON 672718205",
    },
    "PL-B-166": {
        "nazwa_firmy": "PAVOLT Paweł Dziurkowski (Pavolt.pl)",
        "nip_vat": "PL9492206509",
        "rejestr_id": "REGON 364031263",
        "adres": "ul. Główna 8, 42-256 Zrębice Pierwsze",
        "miasto": "Zrębice",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 9492206509 | pavolt.pl",
    },
}


def apply_v7():
    print("🚀 [BILLSzuka] Executing Deep Clean V7...")
    removed = 0
    updated = 0
    total = 0

    for iso, country_dir_name in COUNTRY_MAP.items():
        cdir = DATA_DIR / country_dir_name
        if not cdir.is_dir():
            continue

        for cat_type in ["A", "B"]:
            cfile = cdir / f"catalog-{cat_type}-{iso}.csv"
            if not cfile.exists():
                continue

            cleaned_rows = []
            with cfile.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    cid = r.get("id", "").strip()
                    if not cid:
                        continue

                    if cid in REMOVE_IDS:
                        print(f"  🗑️ Removed {cid} from {cfile.name}: {REMOVE_IDS[cid]}")
                        removed += 1
                        continue

                    row = {col: (r.get(col) or "").strip() for col in CANONICAL_SCHEMA}
                    if cid in UPDATES:
                        for k, v in UPDATES[cid].items():
                            row[k] = v
                        updated += 1

                    cleaned_rows.append(row)
                    total += 1

            with cfile.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
                writer.writeheader()
                writer.writerows(cleaned_rows)

    print(f"✅ V7 Complete! Removed: {removed}, Enriched: {updated}, Total leads: {total}")


if __name__ == "__main__":
    apply_v7()
