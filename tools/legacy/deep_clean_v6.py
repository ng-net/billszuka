#!/usr/bin/env python3
"""
tools/deep_clean_v6.py — Clean retail/non-wholesale stubs and enrich verified Polish entities.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR

REMOVE_IDS = {
    "PL-B-061": "Wykreślona / defunct entity (Redo Sp. z o.o. w likwidacji/przejęta przez Sobieski Trade)",
    "PL-B-067": "Non-tobacco stationery retailer (Hurtownia Papiernicza GRAFIT)",
    "PL-B-069": "Non-tobacco dairy wholesaler (Hero Sp. z o.o. PW. Hurtownia nabiałowo-spożywcza)",
    "PL-B-052": "Retail liquor store (Świat Alkoholi Mikołów)",
    "PL-B-057": "Corner retail kiosk (Sklep po schodkach - tanie papierosy)",
    "PL-B-058": "Hotel Marriott basement retail kiosk (Sherlock Trafika)",
}

UPDATES = {
    "PL-B-029": {
        "nazwa_firmy": "\"CARMEN\" SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL9372338579",
        "rejestr_id": "KRS 0000014510",
        "adres": "ul. Strumieńska 63, 43-385 Jasienica",
        "miasto": "Jasienica",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000014510 | REGON 072713706",
    },
    "PL-B-043": {
        "nazwa_firmy": "UNIKAT SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ (d. Rela Sp. z o.o.)",
        "nip_vat": "PL8921342248",
        "rejestr_id": "KRS 0000109132",
        "adres": "ul. Lipnowska 21A, 87-500 Rypin",
        "miasto": "Rypin",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000109132 | REGON 910945070",
    },
    "PL-B-053": {
        "nazwa_firmy": "\"TABAK POLSKA\" SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL6312331460",
        "rejestr_id": "KRS 0000059254",
        "adres": "ul. Fabryczna 14, 53-609 Wrocław",
        "miasto": "Wrocław",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000059254 | REGON 277658779",
    },
    "PL-B-056": {
        "nazwa_firmy": "\"FIRMA HANDLOWA SUPRA. J.MOZDYNIEWICZ. A.RUDOLPHI. SPÓŁKA JAWNA\"",
        "nip_vat": "PL7351001483",
        "rejestr_id": "KRS 0000083756",
        "adres": "ul. Ludźmierska 29, 34-400 Nowy Targ",
        "miasto": "Nowy Targ",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000083756 | REGON 490489040",
    },
    "PL-B-073": {
        "nazwa_firmy": "EUROCASH S.A. (Cash & Carry Wągrowiec)",
        "nip_vat": "PL7791906082",
        "rejestr_id": "KRS 0000213765",
        "adres": "ul. Wiśniowa 11, 62-052 Komorniki (Oddział: ul. Gnieźnieńska 72, Wągrowiec)",
        "miasto": "Wągrowiec",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000213765 | eurocash.pl",
    },
}


def apply_v6():
    print("🚀 [BILLSzuka] Executing Deep Clean V6...")
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

    print(f"✅ V6 Complete! Removed: {removed}, Enriched: {updated}, Total leads: {total}")


if __name__ == "__main__":
    apply_v6()
