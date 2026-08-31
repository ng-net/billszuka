#!/usr/bin/env python3
"""
rescue_intake_leads.py — One-shot rescue of quality leads found in intake review (2026-08-14).

19 companies rescued from 20 raw gmaps CSVs (see intake_quality_review.md).
Dedup: skip if normalized name already in target catalog (A or B).
"""
import csv, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR, make_id

TODAY = time.strftime("%Y-%m-%d")

# ---------------------------------------------------------------------------
# Leads to rescue. Fields: country, catalog (A|B), name, city, www, phone, rejestr_id, tier, notes
# Dedup check already done against current catalog state (2026-08-14 13:30):
#   - LV: all 4 leads already in catalog-B → SKIP (tabakas nams, g&p tobacco, rasta1, leversa)
#   - BG: tobacco distribution, tti bulgaria, m tobacco, kaliman karibe → already in B → SKIP
#   - EE: ltt as, prike as, nicorex baltic → already in B → SKIP
#   - RO: tutun ieftin, ttiro, interbrands orbico, tobacco logistic → already in B → SKIP
#   - SI: tobacna grosist → already in A; tabakum → already in B → SKIP both
#   - MD: tutun-ctc → in A and B; international tobacco srl → in B → SKIP
#   - HR: daily press tobacco (nlk-tid) → in B → SKIP
#
# After dedup: 0 of 19 are genuinely new — all were already rescued in a prior session.
# Script kept for audit trail. Will report status per company.
# ---------------------------------------------------------------------------

RESCUE_LEADS = [
    # LV
    {"country": "LV", "catalog": "B", "name": "Tabakas Nams Grupa SIA",
     "city": "Piņķi", "www": "http://www.tng.lv/", "phone": "27 043 337",
     "rejestr_id": "ChIJg1Lz_M7T7kYRUG0vGpxdnh0", "tier": "hurtownik",
     "notatki": "Wholesale group, Meistaru iela 5, Piņķi. Google Maps type: wholesaler."},
    {"country": "LV", "catalog": "B", "name": "G & P Tobacco, SIA",
     "city": "Rīga", "www": "https://www.firmas.lv/profile/g-p-tobacco-sia/40103239254", "phone": "67 813 516",
     "rejestr_id": "ChIJzyvBBcbP7kYR39UlTdLZ4aU", "tier": "hurtownik",
     "notatki": "Tobacco wholesaler SIA, Emiļa Melngaiļa iela 2A, Rīga. Typ: wholesaler."},
    {"country": "LV", "catalog": "B", "name": "Rasta 1, SIA",
     "city": "Rīga", "www": "https://rasta1.eu/", "phone": "67 724 216",
     "rejestr_id": "ChIJg1Lz_M7T7kYRUG0vGpxdnh0", "tier": "hurtownik",
     "notatki": "Rasta 1 SIA, Krustpils iela 121A, Rīga. Wholesaler/distributor."},
    {"country": "LV", "catalog": "B", "name": "Leversa, SIA",
     "city": "Rīga", "www": "http://www.leversa.lv/", "phone": "67 517 490",
     "rejestr_id": "ChIJbQeYLHTP7kYRWaMDsnNrNt8", "tier": "hurtownik",
     "notatki": "Leversa SIA, Uriekstes iela 12c, Rīga. Typ: wholesaler."},
    # BG
    {"country": "BG", "catalog": "B", "name": "Tobacco Distribution OOD",
     "city": "Sofia", "www": "http://www.tobacco.bg/", "phone": "087 933 6630",
     "rejestr_id": "ChIJy5hE696FqkARmp3bohVzvqQ", "tier": "hurtownik",
     "notatki": "Magazyn/dystrybucja, strefa przemysłowa Iliyanci, bul. Rozhen 41V. Typ: store (industrial zone)."},
    {"country": "BG", "catalog": "B", "name": "Tabacco Traiding International (TTI Bulgaria)",
     "city": "Sofia", "www": "http://ttibulgaria.com/", "phone": "02 955 7403",
     "rejestr_id": "ChIJ3R7dSDWbqkAR7yomcYotjeI", "tier": "hurtownik",
     "notatki": "TTI Bulgaria, ul. Angelov vrah 22, Ovcha Kupel. Importer/dystrybutor."},
    {"country": "BG", "catalog": "B", "name": "M Tobacco LTD.",
     "city": "Plovdiv", "www": "http://www.mtobacco.bg/", "phone": "032 642 441",
     "rejestr_id": "ChIJ533s0cTRrBQRgKVyUBAXc_k", "tier": "producent",
     "notatki": "M Tobacco LTD, ul. Mladezhka 26, Plovdiv. Typ: manufacturer, service."},
    {"country": "BG", "catalog": "B", "name": "Kaliman Karibe OOD",
     "city": "Sofia", "www": "https://kalimancaribe.com/bg/", "phone": "02 953 1180",
     "rejestr_id": "ChIJWYzqyh-FqkARdxscCvSvbrM", "tier": "hurtownik",
     "notatki": "Kaliman Karibe, blvd. Bulgaria 118, Sofia. Typ: wholesaler/manufacturer. Sieć premium cigar."},
    # EE
    {"country": "EE", "catalog": "B", "name": "LTT AS",
     "city": "Tallinn", "www": "http://www.ltt.ee/", "phone": "606 6500",
     "rejestr_id": "ChIJdfyijKTskkYRl8czuF0uAlA", "tier": "hurtownik",
     "notatki": "LTT AS, Lõõtsa tn 12, Tallinn. Typ: wholesaler, food. Kluczowy hurtownik EE."},
    {"country": "EE", "catalog": "A", "name": "Prike AS",
     "city": "Tallinn", "www": "https://www.prike.ee/", "phone": "622 4900",
     "rejestr_id": "ChIJgRGMzJPskkYRk4UT6bl3StU", "tier": "hurtownik",
     "notatki": "Prike AS, Peterburi tee 92g, Tallinn. Corporate office. Dystrybutor tytoniowy EE."},
    {"country": "EE", "catalog": "B", "name": "Nicorex Baltic OÜ",
     "city": "Peetri", "www": "http://www.nicorex.ee/", "phone": "",
     "rejestr_id": "ChIJq06LpUyTkkYRaq1Xn-1vzxU", "tier": "hurtownik",
     "notatki": "Nicorex Baltic OÜ, Allika tee 1, Peetri. Hurtownik bałtycki, zasięg LV/LT/EE."},
    # RO
    {"country": "RO", "catalog": "B", "name": "Tutun Ieftin",
     "city": "București", "www": "https://tutun-ieftin.com/", "phone": "",
     "rejestr_id": "ChIJhdX2BSsDskAR4PQoCHphSqw", "tier": "hurtownik",
     "notatki": "Tutun Ieftin, Bulevardul Bucureștii Noi 15. Typ: wholesaler, manufacturer, service. Własny sklep online."},
    {"country": "RO", "catalog": "B", "name": "Tobacco Trading International Ro S.R.L.",
     "city": "București", "www": "http://www.ttiro.ro/", "phone": "0733 050 624",
     "rejestr_id": "ChIJFXmmZm1IRkcRk-JFSYcJ9P4", "tier": "hurtownik",
     "notatki": "TTIRO, Bulevardul Ficusului 16. Importer/dystrybutor B2B."},
    {"country": "RO", "catalog": "B", "name": "Interbrands Orbico",
     "city": "București", "www": "", "phone": "021 336 1915",
     "rejestr_id": "ChIJ65T5K3X_sUARc4sv2cSSxu8", "tier": "hurtownik",
     "notatki": "Interbrands Orbico, Str. Sergent Nuțu Ion 44. Typ: wholesaler, manufacturer. Duży dystrybutor FMCG RO."},
    {"country": "RO", "catalog": "B", "name": "Tobacco Logistic & Marketing Srl",
     "city": "Târgu Jiu", "www": "https://www.listafirme.ro/tobacco-logistic-marketing-srl-37086257/", "phone": "",
     "rejestr_id": "ChIJ58ENxh6LTUcRooIC7sQFcAM", "tier": "hurtownik",
     "notatki": "Tobacco Logistic & Marketing Srl, Strada Jiului 1, Târgu Jiu. Typ: wholesaler, manufacturer."},
    # SI
    {"country": "SI", "catalog": "A", "name": "Tobačna grosist d.o.o.",
     "city": "Ljubljana", "www": "http://www.tobacna-grosist.si/", "phone": "(01) 477 71 00",
     "rejestr_id": "ChIJJ8CssV0tZUcRhdhU7wiWPTU", "tier": "hurtownik",
     "notatki": "Tobačna grosist = 'Hurtownia tytoniowa' po słoweńsku. C. 24. Junija 90, Ljubljana."},
    {"country": "SI", "catalog": "B", "name": "Tabakum Export-Import Novo mesto d.o.o.",
     "city": "Novo Mesto", "www": "http://www.tabakum.si/", "phone": "(07) 393 06 60",
     "rejestr_id": "ChIJd8ytdlJVZEcR2pa7Irbca4E", "tier": "hurtownik",
     "notatki": "Tabakum Export-Import, Podbevškova ulica 8b, Novo Mesto. Import/eksport tytoniu."},
    # MD
    {"country": "MD", "catalog": "B", "name": "International Tobacco SRL",
     "city": "Orhei", "www": "", "phone": "022 009 300",
     "rejestr_id": "ChIJFVHKrHfvy0ARguTcwdQCsT4", "tier": "producent",
     "notatki": "International Tobacco SRL, strada Constantin Negruzzi 99a, Orhei. Typ: manufacturer, service."},
    # HR
    {"country": "HR", "catalog": "B", "name": "NLK-TID d.o.o.",
     "city": "Zagreb", "www": "http://www.nlk-tid.hr/", "phone": "01 4093 561",
     "rejestr_id": "ChIJVQ8vm_nXZUcRBi12Upk-L0g", "tier": "hurtownik",
     "notatki": "NLK-TID, Koledovčina ul. 1, Zagreb. Daily Press Tobacco network — distribution/retail channel."},
]


def normalize(name: str) -> str:
    return re.sub(r"\s+", " ", name.lower().strip())


def load_catalog(path: Path) -> tuple[list[dict], list[str]]:
    if not path.exists():
        return [], []
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    names = [normalize(r.get("nazwa", "")) for r in rows]
    return rows, names


def save_catalog(path: Path, rows: list[dict]):
    tmp = path.with_suffix(".csv.tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def main():
    added = 0
    skipped_dup = 0
    skipped_missing = 0

    print("=" * 70)
    print("BILLSzuka — Rescue intake leads (2026-08-14)")
    print("=" * 70)

    for lead in RESCUE_LEADS:
        iso = lead["country"]
        cat = lead["catalog"]
        dirname = COUNTRY_MAP.get(iso, "")
        if not dirname:
            print(f"  ❌ Unknown country: {iso}")
            skipped_missing += 1
            continue

        cat_path = DATA_DIR / dirname / f"catalog-{cat}-{iso}.csv"
        rows, existing_names = load_catalog(cat_path)

        norm_name = normalize(lead["name"])
        if norm_name in existing_names:
            print(f"  ⏭  SKIP (already in catalog-{cat}-{iso}): {lead['name']}")
            skipped_dup += 1
            continue

        # Also check the other catalog for same country
        other_cat = "A" if cat == "B" else "B"
        other_path = DATA_DIR / dirname / f"catalog-{other_cat}-{iso}.csv"
        _, other_names = load_catalog(other_path)
        if norm_name in other_names:
            print(f"  ⏭  SKIP (already in catalog-{other_cat}-{iso}): {lead['name']}")
            skipped_dup += 1
            continue

        # Build new row
        counter = len(rows) + 1
        row = {k: "" for k in CANONICAL_SCHEMA}
        row["id"] = make_id(iso, cat, counter)
        row["kategoria"] = f"{cat}9" if cat == "B" else f"{cat}1"
        row["nazwa"] = lead["name"]
        row["kraj"] = iso
        row["miasto"] = lead.get("city", "")
        row["www"] = lead.get("www", "")
        row["telefon"] = lead.get("phone", "")
        row["rejestr_id"] = lead.get("rejestr_id", "brak")
        row["tier"] = lead.get("tier", "hurtownik")
        row["zrodlo_danych"] = f"Google Maps Intake Rescue 2026-08-14 (Place ID: {lead.get('rejestr_id','')})"
        row["data_weryfikacji"] = TODAY
        row["flagi"] = f"{TODAY} ⚠️ DO-WERYFIKACJI"
        row["notatki"] = lead.get("notatki", "")
        row["rynek_skala"] = "średni"

        rows.append(row)
        save_catalog(cat_path, rows)
        print(f"  ✅ ADDED → catalog-{cat}-{iso}: {lead['name']} ({lead.get('city','')})")
        added += 1

    print()
    print("=" * 70)
    print(f"  Done: {added} added | {skipped_dup} already present | {skipped_missing} errors")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
