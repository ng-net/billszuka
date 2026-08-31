#!/usr/bin/env python3
"""
tools/deep_clean_v9.py — Clean residual directory stubs and enrich confirmed Polish distributors.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR

REMOVE_IDS = {
    "PL-B-038": "Unresolvable stub without NIP/KRS (Noban Sp. z o.o. Wrocław)",
    "PL-B-040": "Unresolvable stub without NIP/KRS (Beata Hurtownia Katowice)",
    "PL-B-111": "Unresolvable directory stub without NIP/KRS (W.O.Z. S.C. Ostrowiec)",
    "PL-B-112": "Unresolvable directory stub without NIP/KRS (Trafika Nord Białystok)",
    "PL-B-113": "Unresolvable directory stub without NIP/KRS (Ogrodniczak Skarżysko)",
    "PL-B-115": "Unresolvable directory stub without NIP/KRS (Kirex Bis Starachowice)",
    "PL-B-116": "Unresolvable directory stub without NIP/KRS (Jolbex Skarżysko)",
    "PL-B-117": "Unresolvable directory stub without NIP/KRS (CORA Kielce)",
    "PL-B-119": "Unresolvable directory stub without NIP/KRS (Carmen S.C. Starachowice)",
    "PL-B-123": "Unresolvable directory stub without NIP/KRS (E-nilsen.pl Pruszków)",
    "PL-B-138": "Duplicate/unresolvable stub (Viva S.j. Ostrowiec)",
    "PL-B-139": "Unresolvable directory stub without NIP/KRS (Smok Zielonka)",
    "PL-B-155": "Unresolvable directory stub without NIP/KRS (PHU Mars Lubin)",
}

UPDATES = {
    "PL-B-190": {
        "nazwa": "\"DAMIMAR\" DANUTA KUŚ, MAREK KUŚ, MICHAŁ KUŚ SPÓŁKA JAWNA",
        "nip_vat": "PL8271833992",
        "rejestr_id": "KRS 0000098449",
        "adres": "al. Jana Pawła II 45, 98-200 Sieradz",
        "miasto": "Sieradz",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000098449 | REGON 730936305",
    },
    "PL-B-182": {
        "nazwa": "SŁOMEX TOBACCO S.C. BOŻENA SŁOMA, ANDRZEJ SŁOMA",
        "nip_vat": "PL9182163585",
        "rejestr_id": "REGON 360620689",
        "adres": "Polska",
        "miasto": "Polska",
        "flagi": "✅ FROZEN (MF PPT)",
        "zrodlo_danych": "Rejestr PPT Ministerstwa Finansów | NIP 9182163585 | REGON 360620689",
    },
    "PL-B-045": {
        "nazwa": "P.P.H.U. Export-Import \"Alfa\" s.c. Aneta Starosta, Cezar Starosta",
        "nip_vat": "PL5992541456",
        "rejestr_id": "REGON 211001648",
        "adres": "ul. Dąbrowskiej 3A / Piłsudskiego 2, 66-530 Drezdenko",
        "miasto": "Drezdenko",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 5992541456 | REGON 211001648",
    },
    "PL-B-181": {
        "nazwa": "AGROTAB S.C. MONIKA PIECZONKA, FABIAN STACHÓW",
        "nip_vat": "PL7931626076",
        "rejestr_id": "REGON 380234567",
        "adres": "ul. Zielona 4C, 37-630 Oleszyce",
        "miasto": "Oleszyce",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 7931626076 | Rejestr Tytoniowy",
    },
}


def apply_v9():
    print("🚀 [BILLSzuka] Executing Deep Clean V9...")
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

    print(f"✅ V9 Complete! Removed: {removed}, Enriched: {updated}, Total leads: {total}")


if __name__ == "__main__":
    apply_v9()
