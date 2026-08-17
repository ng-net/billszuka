#!/usr/bin/env python3
"""
tools/deep_clean_v4.py — Verified registry upgrade for wholesale networks.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR

UPDATES = {
    # ===== LITWA (LT) =====
    "LT-B-001": {
        "nazwa_firmy": "UAB SANITEX",
        "nip_vat": "LT104434917",
        "rejestr_id": "JAR 110443493",
        "adres": "Raudondvario pl. 131C, LT-47501 Kaunas",
        "miasto": "Kaunas",
        "flagi": "✅ FROZEN (RC Litwa / VIES)",
        "zrodlo_danych": "Registrų Centras 110443493 | VIES LT104434917 | sanitex.eu",
    },

    # ===== MOŁDAWIA (MD) =====
    "MD-B-001": {
        "nazwa_firmy": "S.A. Tutun-CTC",
        "nip_vat": "1002600010996",
        "rejestr_id": "IDNO 1002600010996",
        "adres": "str. Ismail 10, MD-2001 Chișinău",
        "miasto": "Chișinău",
        "flagi": "✅ FROZEN (State Register MD)",
        "zrodlo_danych": "State Register MD IDNO 1002600010996 | tutun-ctc.md",
    },

    # ===== POLSKA (PL) =====
    "PL-B-070": {
        "nazwa_firmy": "\"FREGA\" FREJOWSKI, GARBOL SPÓŁKA JAWNA",
        "nip_vat": "PL6570386005",
        "rejestr_id": "KRS 0000084815",
        "adres": "ul. Batalionów Chłopskich 172, 25-670 Kielce (Oddział Tarnów: ul. Czerwona 54A)",
        "miasto": "Tarnów",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000084815 | REGON 290500060 | frega24.pl",
    },
    "PL-B-075": {
        "nazwa_firmy": "CARMEN POLSKA SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL8370001711",
        "rejestr_id": "KRS 0000245817",
        "adres": "ul. Warszawska 93, 96-500 Sochaczew",
        "miasto": "Sochaczew",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000245817 | REGON 750324012",
    },
    "PL-B-078": {
        "nazwa_firmy": "LIQUIDER POLAND SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ SPÓŁKA KOMANDYTOWA",
        "nip_vat": "PL7773264101",
        "rejestr_id": "KRS 0000621078",
        "adres": "ul. Poznańska 21, 62-020 Jasin",
        "miasto": "Jasin",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000621078 | REGON 364574621 | liquider.pl",
    },
    "PL-B-087": {
        "nazwa_firmy": "EUROCASH SERWIS SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ (d. KDWT)",
        "nip_vat": "PL7772304755",
        "rejestr_id": "KRS 0000519553",
        "adres": "ul. Wiśniowa 11, 62-052 Komorniki",
        "miasto": "Komorniki",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000519553 | REGON 631255378 | eurocash.pl",
    },
    "PL-B-168": {
        "nazwa_firmy": "TABAK GRUPA SP. Z O.O. (SklepTytoniowy.pl)",
        "nip_vat": "PL6181914183",
        "rejestr_id": "KRS 0000119343",
        "adres": "ul. Złota 126, 62-800 Kalisz",
        "miasto": "Kalisz",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000119343 | skleptytoniowy.pl",
    },
}


def apply_v4():
    print("🚀 [BILLSzuka] Executing Deep Clean V4...")
    updated = 0
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
                    cid = r.get("id_unikalne", "").strip()
                    row = {col: (r.get(col) or "").strip() for col in CANONICAL_SCHEMA}
                    if cid in UPDATES:
                        for k, v in UPDATES[cid].items():
                            row[k] = v
                        updated += 1
                    rows.append(row)

            with cfile.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
                writer.writeheader()
                writer.writerows(rows)

    print(f"✅ V4 Complete! Enriched/Updated: {updated}")


if __name__ == "__main__":
    apply_v4()
