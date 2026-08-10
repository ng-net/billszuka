#!/usr/bin/env python3
"""BILLSzuka — migracja ID do formatu z regionem + wydzielenie SIA/OÜ do LV/EE."""
import csv
import os
import re
from pathlib import Path

DATA = Path("/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/data")

NEW_COLS = ["region_kod", "region_nazwa", "region_typ"]

PL_CITY_TO_REGION = {
    "Ostrzeszów": ("wielkopolskie", "województwo", "WP"),
    "Bydgoszcz": ("kujawsko-pomorskie", "województwo", "KP"),
    "Goszczyn": ("mazowieckie", "województwo", "MZ"),
    "Zielona Góra": ("lubuskie", "województwo", "LB"),
    "Szczecin": ("zachodniopomorskie", "województwo", "ZP"),
    "Konstantynów Łódzki": ("łódzkie", "województwo", "LD"),
    "Wrocław": ("dolnośląskie", "województwo", "DS"),
    "Ząbkowice Śląskie": ("dolnośląskie", "województwo", "DS"),
    "Przemyśl": ("podkarpackie", "województwo", "PK"),
}

CZ_CITY_TO_REGION = {
    "Plzeň": ("Plzeňský kraj", "kraj", "PK"),  # koliduje z PL-PK, ale ID ma prefix kraju
    "Praha 10": ("Hlavní město Praha", "kraj", "PR"),
    "Modřice (Brno-venkov)": ("Jihomoravský kraj", "kraj", "JM"),
}

LT_CITY_TO_REGION = {
    "Kaunas": ("Kauno apskritis", "apskritis", "KA"),
}

UNKNOWN = ("nieznany", "nieznany", "XX")


def region_for(country, city):
    if not city or city.strip() in ("", "brak danych", "brak"):
        return UNKNOWN
    if country == "PL":
        return PL_CITY_TO_REGION.get(city, UNKNOWN)
    if country == "CZ":
        return CZ_CITY_TO_REGION.get(city, UNKNOWN)
    if country == "LT":
        return LT_CITY_TO_REGION.get(city, UNKNOWN)
    return UNKNOWN


def upgrade_header(path):
    """Upewnij się, że CSV ma nowe kolumny region_* na początku."""
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        old_header = reader.fieldnames
        rows = list(reader)

    if old_header is None:
        return

    # Wypełnij None → "" (gdy wiersz ma mniej pól niż nagłówek)
    for r in rows:
        for k in old_header:
            if r.get(k) is None:
                r[k] = ""

    has_region = "region_kod" in old_header
    if has_region:
        return

    new_header = NEW_COLS + list(old_header)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=new_header, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in rows:
            r.setdefault("region_kod", "")
            r.setdefault("region_nazwa", "")
            r.setdefault("region_typ", "")
            writer.writerow(r)


def rewrite_rows_with_region(path, country):
    """Migruj ID + dodaj region_* do wierszy."""
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames)
        rows = list(reader)

    # Wypełnij None → ""
    for r in rows:
        for k in header:
            if r.get(k) is None:
                r[k] = ""

    if not rows:
        return []

    # Kolejność: region_*, id_unikalne, reszta
    ordered_header = NEW_COLS + [h for h in header if h not in NEW_COLS]

    seq_counter = {}  # (typ, region_kod) → sequence
    id_map = {}  # old_id → new_id (do aktualizacji notatek w drugim przebiegu)

    for r in rows:
        old_id = r["id_unikalne"]
        m = re.match(r"^([A-Z]{2})-([AB])-(\d{3})$", old_id)
        if not m:
            continue
        typ = m.group(2)
        city = r.get("miasto", "")
        region_nazwa, region_typ, region_kod = region_for(country, city)
        if not city or city in ("brak danych", "brak"):
            region_nazwa, region_typ, region_kod = UNKNOWN
        key = (typ, region_kod)
        seq_counter.setdefault(key, 0)
        seq_counter[key] += 1
        new_id = f"{country}-{typ}-{region_kod}-{seq_counter[key]:03d}"
        r["id_unikalne"] = new_id
        r["region_kod"] = region_kod
        r["region_nazwa"] = region_nazwa
        r["region_typ"] = region_typ
        id_map[old_id] = new_id

    # Drugi przebieg: zaktualizuj notatki (np. odwołania do innych ID)
    for r in rows:
        for k, v in r.items():
            if isinstance(v, str):
                for old, new in id_map.items():
                    if old in v:
                        r[k] = v.replace(old, new)

    # Zapisz
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_header, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in ordered_header})

    return rows


def main():
    print("=== Krok 1: upgrade nagłówków (dodaj region_*) ===")
    for country_dir in DATA.iterdir():
        if not country_dir.is_dir():
            continue
        for f in country_dir.glob("catalog-*.csv"):
            upgrade_header(f)

    print("=== Krok 2: migracja ID dla PL ===")
    pl_files = [
        (DATA / "Polska" / "catalog-A-PL.csv", "PL"),
        (DATA / "Polska" / "catalog-B-PL.csv", "PL"),
    ]
    for path, country in pl_files:
        rows = rewrite_rows_with_region(path, country)
        for r in rows:
            print(f"  {r['id_unikalne']:18} {r['miasto']:25} → {r['region_nazwa']}")

    print("=== Krok 3: migracja ID dla CZ ===")
    cz_files = [
        (DATA / "Czechy" / "catalog-A-CZ.csv", "CZ"),
        (DATA / "Czechy" / "catalog-B-CZ.csv", "CZ"),
    ]
    for path, country in cz_files:
        rows = rewrite_rows_with_region(path, country)
        for r in rows:
            print(f"  {r['id_unikalne']:18} {r['miasto']:25} → {r['region_nazwa']}")

    print("=== Krok 4: LT — wydzielenie SIA/OÜ do LV/EE, migracja LT ===")
    path = DATA / "Litwa" / "catalog-B-LT.csv"
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames)
        rows = list(reader)

    lt_rows = [r for r in rows if r["kraj"] == "LT"]
    lv_rows = [r for r in rows if r["kraj"] == "LV"]
    ee_rows = [r for r in rows if r["kraj"] == "EE"]

    # Przepisz LT (tylko LT)
    ordered_header = NEW_COLS + [h for h in header if h not in NEW_COLS]
    seq = {}
    for r in lt_rows:
        city = r.get("miasto", "")
        region_nazwa, region_typ, region_kod = region_for("LT", city)
        if not city or city in ("brak danych", "brak"):
            region_nazwa, region_typ, region_kod = UNKNOWN
        key = ("A" if r["kategoria"].startswith("A") else "B", region_kod)
        seq.setdefault(key, 0)
        seq[key] += 1
        r["id_unikalne"] = f"LT-{key[0]}-{region_kod}-{seq[key]:03d}"
        r["region_kod"] = region_kod
        r["region_nazwa"] = region_nazwa
        r["region_typ"] = region_typ
        print(f"  {r['id_unikalne']:18} {r['miasto']:25} → {region_nazwa}")

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_header, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in lt_rows:
            writer.writerow({k: r.get(k, "") for k in ordered_header})

    # Zapisz LV
    if lv_rows:
        lv_path = DATA / "Łotwa" / "catalog-B-LV.csv"
        ordered = NEW_COLS + [h for h in header if h not in NEW_COLS]
        seq_lv = 1
        for r in lv_rows:
            city = r.get("miasto", "")
            region_nazwa, region_typ, region_kod = ("Ķekavas novads", "novads", "XX")
            r["id_unikalne"] = f"LV-B-{region_kod}-{seq_lv:03d}"
            seq_lv += 1
            r["region_kod"] = region_kod
            r["region_nazwa"] = region_nazwa
            r["region_typ"] = region_typ
            print(f"  → {r['id_unikalne']:18} {r['miasto']:25} → {region_nazwa}")
        with open(lv_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=ordered, quoting=csv.QUOTE_MINIMAL)
            for r in lv_rows:
                writer.writerow({k: r.get(k, "") for k in ordered})

    # Zapisz EE
    if ee_rows:
        ee_path = DATA / "Estonia" / "catalog-B-EE.csv"
        ordered = NEW_COLS + [h for h in header if h not in NEW_COLS]
        seq_ee = 1
        for r in ee_rows:
            city = r.get("miasto", "")
            region_nazwa, region_typ, region_kod = ("Harju maakond", "maakond", "XX")
            r["id_unikalne"] = f"EE-B-{region_kod}-{seq_ee:03d}"
            seq_ee += 1
            r["region_kod"] = region_kod
            r["region_nazwa"] = region_nazwa
            r["region_typ"] = region_typ
            print(f"  → {r['id_unikalne']:18} {r['miasto']:25} → {region_nazwa}")
        with open(ee_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=ordered, quoting=csv.QUOTE_MINIMAL)
            for r in ee_rows:
                writer.writerow({k: r.get(k, "") for k in ordered})

    print("\n✓ Gotowe")


if __name__ == "__main__":
    main()
