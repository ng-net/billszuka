"""
fill_wolumen.py — wypełnia puste kolumny `wolumen` i `confidence_wolumen`
w katalogach data/<Kraj>/catalog-{A,B}-<CC>.csv na podstawie heurystyki
z istniejących wypełnionych rekordów PL (referencja).

Schemat wartości (zgodny z PL reference):
- wolumen ∈ {mały, średni, duży}
- confidence_wolumen ∈ {🟢, 🟡, 🔴}

Heurystyka:
1) wolumen
   - tier='producent'              -> duży
   - tier='autoryzowany'           -> duży
   - tier='hurtownik'              -> duży
   - tier='reseller'               -> średni
   - tier='detalista'              -> mały
   - tier='marketplace'            -> mały
   - tier='' (puste)               -> średni (zachowawczo)
2) confidence_wolumen
   - ma nip_vat LUB rejestr_id    -> 🟢
   - ma adres LUB www             -> 🟡
   - brak powyższych              -> 🔴
3) Jeśli wiersz już ma wartość — NIE nadpisuj.
4) Atomic write (tmp + os.replace) dla bezpieczeństwa danych.

Użycie:
    python3 tools/fill_wolumen.py          # wszystkie kraje, dry-run=False
    python3 tools/fill_wolumen.py --dry    # tylko pokaż co zmieni
"""
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Kraje do przetworzenia
DIRS = ['Bułgaria', 'Chorwacja', 'Czechy', 'Estonia', 'Francja', 'Litwa',
        'Łotwa', 'Mołdawia', 'Polska', 'Rumunia', 'Serbia', 'Słowacja', 'Słowenia']


def heurystyka_wolumen(tier: str) -> str:
    t = (tier or "").strip().lower()
    if t in ("producent", "autoryzowany", "hurtownik"):
        return "duży"
    if t == "reseller":
        return "średni"
    if t in ("detalista", "marketplace"):
        return "mały"
    return "średni"  # fallback dla pustych


def heurystyka_confidence(row: dict) -> str:
    # "Jest NIP" jeśli zweryfikowany rejestr
    if (row.get("nip_vat") or "").strip() or (row.get("rejestr_id") or "").strip():
        return "Jest NIP"
    # "www bez NIP" jeśli ma adres LUB www
    if (row.get("adres") or "").strip() or (row.get("www") or "").strip():
        return "www bez NIP"
    return "brak kontaktu"


def process_file(path: Path, dry: bool = False) -> tuple[int, int]:
    """Zwraca (filled_wolumen, filled_confidence)."""
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    changed_v = changed_c = 0
    for row in rows:
        # wolumen
        if not (row.get("wolumen") or "").strip():
            new_v = heurystyka_wolumen(row.get("tier", ""))
            row["wolumen"] = new_v
            changed_v += 1
        # confidence_wolumen
        if not (row.get("confidence_wolumen") or "").strip():
            new_c = heurystyka_confidence(row)
            row["confidence_wolumen"] = new_c
            changed_c += 1

    if changed_v or changed_c:
        if not dry:
            tmp = path.with_suffix(".csv.tmp")
            with open(tmp, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                w.writerows(rows)
            os.replace(tmp, path)

    return changed_v, changed_c


def main():
    dry = "--dry" in sys.argv
    only = [a for a in sys.argv[1:] if a.startswith("--only=")]
    only_kraj = only[0].split("=")[1] if only else None

    total_v = total_c = 0
    for d in DIRS:
        if only_kraj and d != only_kraj:
            continue
        dpath = DATA / d
        if not dpath.is_dir():
            continue
        for fname in sorted(os.listdir(dpath)):
            if not (fname.startswith("catalog-") and fname.endswith(".csv")):
                continue
            path = dpath / fname
            v, c = process_file(path, dry=dry)
            total_v += v
            total_c += c
            if v or c:
                tag = "[DRY] " if dry else ""
                print(f"{tag}{d}/{fname}: wolumen +{v}, conf +{c}")

    print(f"\n{'[DRY] ' if dry else ''}TOTAL: wolumen +{total_v}, conf +{total_c}")


if __name__ == "__main__":
    main()