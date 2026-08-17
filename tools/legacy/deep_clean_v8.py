#!/usr/bin/env python3
"""
tools/deep_clean_v8.py — Verified registry upgrade wave 8.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR

REMOVE_IDS = {
    "PL-B-083": "Unresolvable generic scrape artifact without NIP/KRS (EM Łęczyca)",
    "PL-B-084": "Unresolvable generic scrape artifact without NIP/KRS (Dzidek Gdańsk)",
    "PL-B-085": "Unresolvable generic scrape artifact without NIP/KRS (ABC Kościerzyna)",
    "PL-B-086": "Unresolvable generic scrape artifact without NIP/KRS (Mewa Mińsk Mazowiecki)",
    "PL-B-088": "Unresolvable generic scrape artifact without NIP/KRS (JAR Lublin)",
    "PL-B-089": "Unresolvable generic scrape artifact without NIP/KRS (Irba Jelenia Góra)",
    "PL-B-090": "Unresolvable generic scrape artifact without NIP/KRS (Mars Lublin)",
    "PL-B-093": "Unresolvable generic scrape artifact without NIP/KRS (Artus Kujawsko-Pomorskie)",
    "PL-B-095": "Unresolvable generic scrape artifact without NIP/KRS (ADGAR Olsztyn)",
    "PL-B-096": "Unresolvable generic scrape artifact without NIP/KRS (7&7 Rypin)",
    "PL-B-097": "Unresolvable generic scrape artifact without NIP/KRS (Wir Strzelce Opolskie)",
    "PL-B-101": "Unresolvable generic scrape artifact without NIP/KRS (Hurtownia Śląsk i Zagłębie)",
    "PL-B-102": "Unresolvable generic scrape artifact without NIP/KRS (F.H. Alans Ruda Śląska)",
    "PL-B-077": "Unresolvable generic scrape artifact without NIP/KRS (ABC Władysławowo)",
}

UPDATES = {
    "PL-B-004": {
        "nazwa_firmy": "CASISS KRZYSZTOF RZESZOWSKI SPÓŁKA JAWNA",
        "nip_vat": "PL8940050162",
        "rejestr_id": "KRS 0000061705",
        "adres": "ul. Bolesława Krzywoustego 300, 51-312 Wrocław",
        "miasto": "Wrocław",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000061705 | REGON 931501520",
    },
    "PL-B-033": {
        "nazwa_firmy": "TOP-KART SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL5422737004",
        "rejestr_id": "KRS 0001107489",
        "adres": "ul. Adama Mickiewicza 82/1, 15-232 Białystok",
        "miasto": "Białystok",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0001107489 | REGON 052018703",
    },
    "PL-B-047": {
        "nazwa_firmy": "ZEFIR SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL5422694571",
        "rejestr_id": "KRS 0000065192",
        "adres": "ul. Handlowa 1, 15-399 Białystok",
        "miasto": "Białystok",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000065192 | REGON 051982408",
    },
    "PL-B-103": {
        "nazwa_firmy": "Drek Hurtownia Gilz Papierosowych i Akcesoriów",
        "nip_vat": "PL9481180350",
        "rejestr_id": "REGON 670937720",
        "adres": "ul. Kalińska 6 lok. 6a, 26-600 Radom",
        "miasto": "Radom",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 9481180350 | drek.pl",
    },
    "PL-B-105": {
        "nazwa_firmy": "Tabak. Hurtownia papierosów i chemii gospodarczej. Łożyniak D.",
        "nip_vat": "PL9251013660",
        "rejestr_id": "REGON 970471547",
        "adres": "ul. Szprotawska 18A, 67-120 Kożuchów",
        "miasto": "Kożuchów",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 9251013660",
    },
    "PL-B-106": {
        "nazwa_firmy": "PHU TABAK PIOTR FORNALA",
        "nip_vat": "PL8950017491",
        "rejestr_id": "REGON 930182225",
        "adres": "ul. Wierzchowicka 7, 51-127 Wrocław",
        "miasto": "Wrocław",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 8950017491",
    },
    "PL-B-107": {
        "nazwa_firmy": "LOKIVAPE - DOMINIK NOWIKOWSKI",
        "nip_vat": "PL8481886316",
        "rejestr_id": "REGON 526205545",
        "adres": "ul. Armii Krajowej 9 lok. U11, 19-300 Ełk",
        "miasto": "Ełk",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 8481886316 | lokivape.com",
    },
    "PL-B-110": {
        "nazwa_firmy": "PHPU \"TEKS\" SA (Markowe Cygara)",
        "nip_vat": "PL7960073210",
        "rejestr_id": "KRS 0000045612",
        "adres": "ul. Biznesowa 8, 26-612 Radom",
        "miasto": "Radom",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000045612 | markowecygara.pl",
    },
}


def apply_v8():
    print("🚀 [BILLSzuka] Executing Deep Clean V8...")
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
                    cid = r.get("id_unikalne", "").strip()
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

    print(f"✅ V8 Complete! Removed: {removed}, Enriched: {updated}, Total leads: {total}")


if __name__ == "__main__":
    apply_v8()
