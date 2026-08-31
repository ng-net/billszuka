#!/usr/bin/env python3
"""
tools/deep_clean_v5.py — Clean defunct/unverified map stubs and enrich verified Polish entities.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR

REMOVE_IDS = {
    # Defunct / Closed / Radiată
    "RO-A-010": "Defunct / radiată Romanian entity (Vaper's Paradise SRL)",

    # Unresolvable Google Map generic keyword stubs (no entity, no NIP, no company name)
    "PL-B-076": "Defunct / Non-tobacco stub (ASW Trafika)",
    "PL-B-079": "Generic map pin stub (Hurtownia papierosów — Szczytno)",
    "PL-B-080": "Generic map pin stub (Hurtownia papierosów — Mostki)",
    "PL-B-081": "Generic map pin stub (Hurtownia papierosów — Koluszki)",
    "PL-B-082": "Generic map pin stub (Hurtownia papierosów — Czerwionka-Leszczyny)",
    "PL-B-125": "Empty stub without NIP or address (Tanie Palenie POINT)",
    "PL-B-126": "Empty stub without NIP or address (Pol-Ta)",
    "PL-B-127": "Duplicate of PL-B-114 (Milo Sp. z o.o. / MILO S.A.)",
    "PL-B-128": "Empty stub without NIP or address (Hurtownia Papierosów Grażyna Baltadzi)",
    "PL-B-129": "Empty stub without NIP or address (Efekt Łódź)",
    "PL-B-131": "Empty stub without NIP or address (Tabak Kraków)",
    "PL-B-136": "Alcohol retailer, non-tobacco (AlkoNaWesele.pl)",
    "PL-B-137": "Empty stub without NIP or address (Królestwo Tytoniu)",
}

UPDATES = {
    "PL-B-074": {
        "nazwa": "BIURO HANDLOWE \"ELROY\" KRYSTYNA ROJEK, LESZEK ROJEK - SPÓŁKA JAWNA",
        "nip_vat": "PL8880000685",
        "rejestr_id": "KRS 0000009117",
        "adres": "ul. Wojska Polskiego 18A, 87-800 Włocławek",
        "miasto": "Włocławek",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000009117 | REGON 910503811",
    },
    "PL-B-100": {
        "nazwa": "HURTOWNIA \"KIM\" KAZIMIERZ KRZEMIŃSKI, MAREK KRZEMIŃSKI, ANDRZEJ CHRZĄSZCZ SPÓŁKA JAWNA",
        "nip_vat": "PL6550003840",
        "rejestr_id": "KRS 0000026856",
        "adres": "ul. Bohaterów Warszawy 106, 28-100 Busko-Zdrój",
        "miasto": "Busko-Zdrój",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000026856 | REGON 290012018",
    },
    "PL-B-161": {
        "nazwa": "PASO POLSKA SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ SPÓŁKA KOMANDYTOWA",
        "nip_vat": "PL7820007588",
        "rejestr_id": "KRS 0000444926",
        "adres": "ul. Skrajna 1, Sierosław, 62-080 Tarnowo Podgórne",
        "miasto": "Tarnowo Podgórne",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000444926 | REGON 630519510 | hurtownia.paso.pl",
    },
}


def apply_v5():
    print("🚀 [BILLSzuka] Executing Deep Clean V5...")
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

    print(f"✅ V5 Complete! Removed: {removed}, Enriched: {updated}, Total leads: {total}")


if __name__ == "__main__":
    apply_v5()
