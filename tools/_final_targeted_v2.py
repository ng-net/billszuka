"""Targeted fixes v2 — fix by ID, not by row index."""
import csv
from pathlib import Path

ROOT = Path("/Users/ciepolml/Documents/Bills-Drive/BILLSzuka-28-Aug")

# (path, id_match, column, new_value) — find row by id containing substring, set column
fixes = [
    # CZ — CZ-B-029 nip_vat
    ("data/Czechy/catalog-B-CZ.csv", "CZ-B-029", "nip_vat", "CZ61775339"),
    # SK — SK-B-023 kanal
    ("data/Słowacja/catalog-B-SK.csv", "SK-B-023", "kanal_sprzedaży", "sklep stacjonarny: maloobchod s tabak.výr. (NACE 47260)"),
    # BG — BG-B-032 nip_vat
    ("data/Bułgaria/catalog-B-BG.csv", "BG-B-032", "nip_vat", "BG206942648"),
    # FR — FR-B-013 kanal (last row)
    ("data/Francja/catalog-B-FR.csv", "FR-B-013", "kanal_sprzedaży", "hurt + dystrybucja (raporty badawcze)"),
    # RS — RS-B-028 nip_vat (last row, 28 in csv including header)
    ("data/Serbia/catalog-B-RS.csv", "RS-B-028", "nip_vat", "06921493"),
]

for path, id_substr, col, new_val in fixes:
    p = ROOT / path
    with p.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    n = 0
    for r in rows:
        if id_substr in r.get("id", ""):
            r[col] = new_val
            n += 1
    if n:
        fieldnames = list(rows[0].keys())
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            w.writeheader()
            w.writerows(rows)
        print(f"{path}: {n} fixes ({id_substr})")
    else:
        print(f"WARN: {path} no match for {id_substr}")

print("Done.")
