"""Targeted fixes for remaining 12 criticals across PL/CZ/SK/BG/RO/EE/FR/RS."""
import csv
from pathlib import Path

ROOT = Path("/Users/ciepolml/Documents/Bills-Drive/BILLSzuka-28-Aug")

fixes = [
    # PL — PL-B-138 row 25 needs kanal fix; PL-B-138 row 136 needs rok_zalozenia int
    ("data/Polska/catalog-B-PL.csv", 25, "kanal_sprzedaży", "hurt + dystrybucja"),
    ("data/Polska/catalog-B-PL.csv", 136, "rok_zalozenia", "2001"),
    # CZ — CZ-B-029 nip_vat should be just CZ61775339 (strip DIČ: prefix)
    ("data/Czechy/catalog-B-CZ.csv", 28, "nip_vat", "CZ61775339"),
    # SK — SK-B-021 nip_vat + SK-B-023 kanal
    ("data/Słowacja/catalog-B-SK.csv", 21, "nip_vat", "SK2021803157"),
    ("data/Słowacja/catalog-B-SK.csv", 23, "kanal_sprzedaży", "sklep stacjonarny: maloobchod s tabak.výr. (NACE 47260)"),
    # BG — BG-B-032 nip_vat placeholder
    ("data/Bułgaria/catalog-B-BG.csv", 33, "nip_vat", "BG206942648"),
    # RO — row 7 kanal
    ("data/Rumunia/catalog-B-RO.csv", 7, "kanal_sprzedaży", "hurt + dystrybucja"),
    # EE — row 22 kanal
    ("data/Estonia/catalog-B-EE.csv", 22, "kanal_sprzedaży", "hurt + dystrybucja"),
    # FR — FR-B-013 kanal
    ("data/Francja/catalog-B-FR.csv", 16, "kanal_sprzedaży", "hurt + dystrybucja (raporty badawcze)"),
    # RS — RS-B-026/027/028 nip_vat need prefix only (RS PIB format)
    ("data/Serbia/catalog-B-RS.csv", 26, "nip_vat", "07319665"),
    ("data/Serbia/catalog-B-RS.csv", 27, "nip_vat", "07178972"),
    ("data/Serbia/catalog-B-RS.csv", 28, "nip_vat", "06921493"),
]

for path, row_num, col, new_val in fixes:
    p = ROOT / path
    with p.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if row_num - 1 >= len(rows):
        print(f"ERROR: {path} row {row_num} out of range (only {len(rows)} rows)")
        continue
    if rows[row_num - 1].get(col) == new_val:
        continue
    rows[row_num - 1][col] = new_val
    fieldnames = list(rows[0].keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
    print(f"{path}: row {row_num} {col} -> {new_val}")
print("Done.")
