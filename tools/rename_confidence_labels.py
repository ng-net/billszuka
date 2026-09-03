"""
rename_confidence_labels.py — zamienia emoji confidence_wolumen
🟢 → "Jest NIP"
🟡 → "www bez NIP"
🔴 → "brak kontaktu"

W plikach:
- data/<Kraj>/catalog-{A,B}-<CC>.csv
- frontend-2/public/{master,sample}.csv
- data/verification/.../proposed-catalog-B*.csv
- data/gems*.csv, data/gems.csv (jeśli istnieją)

Atomic write (tmp + os.replace).

Użycie:
    python3 tools/rename_confidence_labels.py --dry   # tylko pokaż co zmieni
    python3 tools/rename_confidence_labels.py         # wykonaj
"""
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Emoji → tekst
EMOJI_MAP = {
    "🟢": "Jest NIP",
    "🟡": "www bez NIP",
    "🔴": "brak kontaktu",
}

# Pliki do przetworzenia
TARGETS = []

# Kraje: catalog-A i catalog-B
DIRS = ['Bułgaria', 'Chorwacja', 'Czechy', 'Estonia', 'Francja', 'Litwa',
        'Łotwa', 'Mołdawia', 'Polska', 'Rumunia', 'Serbia', 'Słowacja', 'Słowenia']

for d in DIRS:
    dpath = ROOT / "data" / d
    if dpath.is_dir():
        for f in sorted(os.listdir(dpath)):
            if f.startswith("catalog-") and f.endswith(".csv"):
                TARGETS.append(dpath / f)

# Frontend public
for fname in ["master.csv", "sample.csv"]:
    p = ROOT / "frontend-2" / "public" / fname
    if p.exists():
        TARGETS.append(p)

# Verification (proposed-catalog-B*)
verif = ROOT / "data" / "verification"
if verif.is_dir():
    for p in verif.rglob("proposed-catalog-B*.csv"):
        TARGETS.append(p)

# gems* w data root (na wszelki wypadek)
for p in (ROOT / "data").glob("gems*.csv"):
    TARGETS.append(p)


def transform_row(row: dict) -> bool:
    """Zwraca True jeśli dokonano zmiany."""
    val = row.get("confidence_wolumen", "")
    if val in EMOJI_MAP:
        row["confidence_wolumen"] = EMOJI_MAP[val]
        return True
    return False


def process_file(path: Path, dry: bool) -> int:
    """Zwraca liczbę zmienionych wierszy."""
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    changed = 0
    for row in rows:
        if transform_row(row):
            changed += 1
    if changed and not dry:
        tmp = path.with_suffix(".csv.tmp")
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
    return changed


def main():
    dry = "--dry" in sys.argv
    total = 0
    for p in TARGETS:
        n = process_file(p, dry)
        if n:
            tag = "[DRY] " if dry else ""
            try:
                rel = p.relative_to(ROOT)
            except ValueError:
                rel = p
            print(f"{tag}{rel}: {n} wierszy")
            total += n
    print(f"\n{'[DRY] ' if dry else ''}TOTAL: {total} wierszy zmienionych")


if __name__ == "__main__":
    main()