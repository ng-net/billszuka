#!/usr/bin/env python3
"""
tools/deep_clean_v3.py — Target-enrich and upgrade all verified records across CZ, LT, LV, RO, PL.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR

UPDATES = {
    # ===== CZECHY (CZ) =====
    "CZ-A-004": {
        "nazwa": "Ing. Jan Ševic (Plnicky-Powermatic.cz)",
        "nip_vat": "CZ7005132222",
        "rejestr_id": "IČO 45410003",
        "flagi": "✅ FROZEN (ARES / VIES)",
        "zrodlo_danych": "ARES 45410003 | VIES CZ7005132222 | plnicky-powermatic.cz",
    },
    "CZ-A-005": {
        "nazwa": "G8 point s.r.o. (Vseprokoureni.cz)",
        "nip_vat": "CZ06941281",
        "rejestr_id": "IČO 06941281",
        "flagi": "✅ FROZEN (ARES / VIES)",
        "zrodlo_danych": "ARES 06941281 | VIES CZ06941281 | vseprokoureni.cz",
    },
    "CZ-A-006": {
        "nazwa": "VIVACE spol. s r.o. (Dobra-trafika.com)",
        "nip_vat": "CZ29154529",
        "rejestr_id": "IČO 29154529",
        "flagi": "✅ FROZEN (ARES / VIES)",
        "zrodlo_danych": "ARES 29154529 | VIES CZ29154529 | dobra-trafika.com",
    },
    "CZ-B-001": {
        "nazwa": "GGT CZ, a.s. (GG Tabák)",
        "nip_vat": "CZ26293609",
        "rejestr_id": "IČO 26293609",
        "flagi": "✅ FROZEN (ARES / VIES)",
        "zrodlo_danych": "ARES 26293609 | VIES CZ26293609 | ggtabak.cz",
    },

    # ===== LITWA (LT) =====
    "LT-A-013": {
        "nazwa": "Uždaroji akcinė bendrovė \"SKONIS IR KVAPAS\"",
        "nip_vat": "LT235477515",
        "rejestr_id": "JAR 123547759",
        "flagi": "✅ FROZEN (RC Litwa / VIES)",
        "zrodlo_danych": "Registrų Centras 123547759 | VIES LT235477515 | skonis-kvapas.lt",
    },
    "LT-A-014": {
        "nazwa": "UAB \"Tirnoda\" (xprekes.lt)",
        "nip_vat": "LT100013400211",
        "rejestr_id": "JAR 306340639",
        "flagi": "✅ FROZEN (RC Litwa / VIES)",
        "zrodlo_danych": "Registrų Centras 306340639 | VIES LT100013400211 | xprekes.lt",
    },
    "LT-A-015": {
        "nazwa": "UAB \"Visterus\" (mandarinai.lt)",
        "nip_vat": "LT100012411817",
        "rejestr_id": "JAR 304158075",
        "flagi": "✅ FROZEN (RC Litwa / VIES)",
        "zrodlo_danych": "Registrų Centras 304158075 | VIES LT100012411817 | mandarinai.lt",
    },
    "LT-A-016": {
        "nazwa": "D. Marcinkevičiaus gamybinė- komercinė įmonė \"Medėja\"",
        "nip_vat": "LT697179515",
        "rejestr_id": "JAR 169717959",
        "flagi": "✅ FROZEN (RC Litwa / VIES)",
        "zrodlo_danych": "Registrų Centras 169717959 | VIES LT697179515 | medeja.lt",
    },
    "LT-B-010": {
        "nazwa": "UAB \"Lavisos LEZ terminalas\"",
        "nip_vat": "LT100002254218",
        "rejestr_id": "JAR 135940713",
        "flagi": "✅ FROZEN (RC Litwa / VIES)",
        "zrodlo_danych": "Registrų Centras 135940713 | VIES LT100002254218 | lez-terminalas.lt",
    },

    # ===== ŁOTWA (LV) =====
    "LV-A-003": {
        "nazwa": "SIA \"Nord Snus\" (Salt Point network)",
        "nip_vat": "LV40203076185",
        "rejestr_id": "Lursoft 40203076185",
        "flagi": "✅ FROZEN (Lursoft / VIES)",
        "zrodlo_danych": "Lursoft 40203076185 | VIES LV40203076185 | saltpoint.eu",
    },
    "LV-A-004": {
        "nazwa": "SIA \"Pro Vape\"",
        "nip_vat": "LV40203029617",
        "rejestr_id": "Lursoft 40203029617",
        "flagi": "✅ FROZEN (Lursoft / VIES)",
        "zrodlo_danych": "Lursoft 40203029617 | VIES LV40203029617 | pro-vape.lv",
    },
    "LV-A-008": {
        "nazwa": "SIA \"Tabakas Nams Grupa\" (TNG)",
        "nip_vat": "LV50003223511",
        "rejestr_id": "Lursoft 50003223511",
        "flagi": "✅ FROZEN (Lursoft / VIES)",
        "zrodlo_danych": "Lursoft 50003223511 | VIES LV50003223511 | tng.lv",
    },

    # ===== RUMUNIA (RO) =====
    "RO-A-003": {
        "nazwa": "GOLD STEAM GARDEN SRL (mtabac.ro)",
        "nip_vat": "RO36988731",
        "rejestr_id": "J19/120/2017",
        "flagi": "✅ FROZEN (ONRC)",
        "zrodlo_danych": "ONRC J19/120/2017 | CUI 36988731 | mtabac.ro",
    },
    "RO-B-002": {
        "nazwa": "BRANDS INTERNATIONAL SRL",
        "nip_vat": "RO15291684",
        "rejestr_id": "J23/464/2003",
        "flagi": "✅ FROZEN (ONRC)",
        "zrodlo_danych": "ONRC J23/464/2003 | CUI 15291684 | brandsinternational.ro",
    },
    "RO-B-003": {
        "nazwa": "COLISEUM SA",
        "nip_vat": "RO5057024",
        "rejestr_id": "J16/786/2007",
        "flagi": "✅ FROZEN (ONRC)",
        "zrodlo_danych": "ONRC J16/786/2007 | CUI 5057024 | Craiova",
    },
    "RO-B-004": {
        "nazwa": "ANGROSISTUL SRL",
        "nip_vat": "RO1156904",
        "rejestr_id": "J10/2495/1991",
        "flagi": "✅ FROZEN (ONRC)",
        "zrodlo_danych": "ONRC J10/2495/1991 | CUI 1156904 | Buzău",
    },
    "RO-B-005": {
        "nazwa": "VINCOM DISTRIBUTION SRL",
        "nip_vat": "RO14853032",
        "rejestr_id": "J08/1133/2002",
        "flagi": "✅ FROZEN (ONRC)",
        "zrodlo_danych": "ONRC J08/1133/2002 | CUI 14853032 | Brașov",
    },
    "RO-B-007": {
        "nazwa": "TOBACCO INTERNATIONAL IMPORT EXPORT S.R.L.",
        "nip_vat": "RO16173644",
        "rejestr_id": "J40/2867/2004",
        "flagi": "✅ FROZEN (ONRC)",
        "zrodlo_danych": "ONRC J40/2867/2004 | CUI 16173644 | București",
    },
    "RO-B-009": {
        "nazwa": "PRIMONET RO SRL (primonet.ro)",
        "nip_vat": "RO29972252",
        "rejestr_id": "J30/188/2012",
        "flagi": "✅ FROZEN (ONRC)",
        "zrodlo_danych": "ONRC J30/188/2012 | CUI 29972252 | primonet.ro",
    },

    # ===== POLSKA (PL) =====
    "PL-B-158": {
        "nazwa": "ARLGROUP SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ SPÓŁKA KOMANDYTOWA",
        "nip_vat": "PL5272712651",
        "rejestr_id": "KRS 0000502538",
        "adres": "ul. Księcia Janusza 19/31 lok. 75, 01-452 Warszawa",
        "miasto": "Warszawa",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000502538 | REGON 147178920 | arlgroup.pl",
    },
}


def apply_v3():
    print("🚀 [BILLSzuka] Executing Deep Clean V3...")
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
                    cid = r.get("id", "").strip()
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

    print(f"✅ V3 Complete! Enriched/Updated: {updated}")


if __name__ == "__main__":
    apply_v3()
