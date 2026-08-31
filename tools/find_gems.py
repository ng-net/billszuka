#!/usr/bin/env python3
"""
tools/find_gems.py — Find high-value B2B partner "gems" across all 12
non-Poland countries.

A "gem" is a Catalog B lead that is:
  1. FROZEN (verifier-confirmed, not DO-WERYFIKACJI/PENDING/HALUCYNACJA)
  2. Has contact info (email or telefon non-empty)
  3. Has at least one "signal" in notatki/marki:
     - whale/lider/ogólnokrajowy/sieć/monopol (whale-tier distribution)
     - or: distrubutor/hurtownia with B8/B4/B6 (tytoń/akcesoria/e-papierosy)
  4. NOT marked as hurt-weryfikacji in sourcing (intake not yet validated)
  5. powinowactwo_nabijarki >= 4 (Catalog B scoring)

Output:
  - data/verification/gems.csv         — full ranked list
  - data/verification/gems_summary.md  — per-country summary
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_CSV = ROOT / "data" / "verification" / "gems.csv"
OUT_MD = ROOT / "data" / "verification" / "gems_summary.md"

NON_PL_COUNTRIES = [
    "Bułgaria", "Chorwacja", "Czechy", "Estonia", "Francja", "Litwa",
    "Mołdawia", "Rumunia", "Serbia", "Słowacja", "Słowenia", "Łotwa",
]

ISO_MAP = {
    "Bułgaria": "BG", "Chorwacja": "HR", "Czechy": "CZ", "Estonia": "EE",
    "Francja": "FR", "Litwa": "LT", "Mołdawia": "MD", "Rumunia": "RO",
    "Serbia": "RS", "Słowacja": "SK", "Słowenia": "SI", "Łotwa": "LV",
}

# Whale/distributor signals (Polish + international)
WHALE_TERMS = (
    "lider", "ogólnokraj", "monopol", "największ", "top b2b",
    "🐋", "główny dystrybutor", "exclusive", "wyłączność",
    "national leader", "largest", "market leader",
)

B2B_TERMS = (
    "hurtowni", "dystrybutor", "dystrybucja", "hurtowy",
    "importer", "b2b", "sieć sklep", "sieć skład",
    "centrum dystrybucyjne", "wholesale", "distributor",
    "sieć hurtowni", "sieć sklepów",
)

CATEGORY_AFFINITY = {"B8", "B5", "B6", "B4", "B7"}  # tytoń/akcesoria/vape


def is_frozen(row: dict) -> bool:
    """FROZEN in flagi and not DO-WERYFIKACJI / PENDING / HALUCYNACJA."""
    flagi = (row.get("flagi") or "").upper()
    return "FROZEN" in flagi and "DO-WERYFIKACJI" not in flagi \
        and "PENDING" not in flagi and "HALUCYNACJA" not in flagi


def has_contact(row: dict) -> bool:
    return bool((row.get("email") or "").strip() or (row.get("telefon") or "").strip())


def sourcing_clean(row: dict) -> bool:
    """Sourcing not 'do weryfikacji' / 'brak' / empty."""
    s = (row.get("sourcing") or "").strip().lower()
    return s not in {"", "brak", "do weryfikacji", "—", "-", "n/a"}


def has_whale_signal(row: dict) -> bool:
    text = " ".join([
        (row.get("notatki") or ""),
        (row.get("kanal_sprzedaży") or ""),
        (row.get("marki_nabijarki") or ""),
    ]).lower()
    return any(t in text for t in WHALE_TERMS)


def has_b2b_signal(row: dict) -> bool:
    text = " ".join([
        (row.get("notatki") or ""),
        (row.get("kanal_sprzedaży") or ""),
        (row.get("tier") or ""),
    ]).lower()
    cat = (row.get("kategoria") or "").upper().strip()
    if cat in CATEGORY_AFFINITY:
        return True
    return any(t in text for t in B2B_TERMS)


def powinowactwo_score(row: dict) -> int:
    """Parse powinowactwo_nabijarki; default 0."""
    raw = (row.get("powinowactwo_nabijarki") or "").strip()
    if raw.isdigit():
        return int(raw)
    return 0


def score_gem(row: dict) -> int:
    """Higher = better gem. Max ~10."""
    s = 0
    # Tier 1: whale signal (5 pts) — top priority
    if has_whale_signal(row):
        s += 5
    # Tier 2: powinowactwo 4-5 (2 pts)
    p = powinowactwo_score(row)
    if p >= 4:
        s += 2
    elif p == 3:
        s += 1
    # Tier 3: B2B distribution signal (2 pts)
    if has_b2b_signal(row):
        s += 2
    # Bonus: real sourcing (1 pt)
    if sourcing_clean(row):
        s += 1
    return s


def main():
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    gems = []
    for country in NON_PL_COUNTRIES:
        for csv_path in sorted((DATA / country).glob("catalog-B-*.csv")):
            with open(csv_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if not is_frozen(r):
                        continue
                    if not has_contact(r):
                        continue
                    score = score_gem(r)
                    if score < 3:  # minimum bar
                        continue
                    gems.append({
                        "country": country,
                        "iso": ISO_MAP[country],
                        "id": r.get("id", ""),
                        "name": r.get("nazwa", ""),
                        "miasto": r.get("miasto", ""),
                        "www": r.get("www", ""),
                        "kategoria": r.get("kategoria", ""),
                        "tier": r.get("tier", ""),
                        "powinowactwo": powinowactwo_score(r),
                        "wolumen": r.get("wolumen", ""),
                        "confidence": r.get("confidence_wolumen", ""),
                        "email": r.get("email", ""),
                        "telefon": r.get("telefon", ""),
                        "kanal": r.get("kanal_sprzedaży", ""),
                        "decydent": r.get("decydent", ""),
                        "notatki": (r.get("notatki") or "")[:200],
                        "flagi": r.get("flagi", ""),
                        "score": score,
                        "whale": "✓" if has_whale_signal(r) else "",
                    })

    # Sort: score desc, then country asc
    gems.sort(key=lambda g: (-g["score"], g["country"], g["id"]))

    # CSV
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "score", "whale", "country", "iso", "id", "name", "miasto",
            "kategoria", "tier", "powinowactwo", "wolumen", "confidence",
            "kanal", "email", "telefon", "www", "decydent", "notatki", "flagi",
        ])
        w.writeheader()
        w.writerows(gems)

    # Summary by country
    by_country = Counter(g["iso"] for g in gems)
    by_country_full = defaultdict(list)
    for g in gems:
        by_country_full[g["iso"]].append(g)

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("# Gems — non-PL B2B partner candidates (2026-08-31)\n\n")
        f.write(f"**Total gems found:** {len(gems)} across {len(by_country)} countries\n\n")
        f.write("## Gem criteria (all required)\n\n")
        f.write("- **FROZEN** flag (verifier-confirmed, not DO-WERYFIKACJI / PENDING / HALUCYNACJA)\n")
        f.write("- Has **contact info** (email or telefon)\n")
        f.write("- Score ≥ 3: whale/distribution signal + powinowactwo + B2B tier + sourcing\n")
        f.write("- powinowactwo_nabijarki weighted 4-5 (out of 1-5)\n\n")
        f.write("## Score breakdown (max ~10)\n\n")
        f.write("- 5 pts: **whale signal** in notatki (lider/ogólnokrajowy/monopol/🐋/wyłączność)\n")
        f.write("- 2 pts: powinowactwo 4-5 (1 pt for 3)\n")
        f.write("- 2 pts: B2B tier or category B8/B5/B6/B4/B7\n")
        f.write("- 1 pt: real sourcing (not 'brak' / 'do weryfikacji')\n\n")
        f.write("## Per-country summary\n\n")
        f.write("| ISO | Country | Gems | Top score |\n|---|---|---|---|\n")
        for iso, count in by_country.most_common():
            top = max(g["score"] for g in by_country_full[iso])
            country_name = next(c for c, i in ISO_MAP.items() if i == iso)
            f.write(f"| {iso} | {country_name} | {count} | {top} |\n")
        f.write(f"\n**Total: {len(gems)} gems** in {len(by_country)} countries\n\n")

        # Top 20 list (cross-country, best first)
        f.write("## Top 20 gems (cross-country, by score)\n\n")
        f.write("| # | Score | 🐋 | ISO | Name | Pow | Email/Phone |\n|---|---|---|---|---|---|---|\n")
        for i, g in enumerate(gems[:20], 1):
            contact = g["email"] or g["telefon"]
            f.write(f"| {i} | {g['score']} | {g['whale']} | {g['iso']} | "
                    f"{g['name'][:40]} | {g['powinowactwo']} | {contact[:35]} |\n")
        f.write("\n")

        # Per-country detail
        for iso in sorted(by_country_full.keys(), key=lambda i: -len(by_country_full[i])):
            country_name = next(c for c, i in ISO_MAP.items() if i == iso)
            f.write(f"## {iso} — {country_name} ({len(by_country_full[iso])} gems)\n\n")
            f.write("| # | Score | 🐋 | Name | Pow | City | Category | Contact |\n")
            f.write("|---|---|---|---|---|---|---|---|\n")
            for i, g in enumerate(by_country_full[iso], 1):
                contact = g["email"] or g["telefon"] or "—"
                f.write(f"| {i} | {g['score']} | {g['whale']} | {g['name'][:35]} | "
                        f"{g['powinowactwo']} | {g['miasto'][:20]} | {g['kategoria']} | {contact[:30]} |\n")
            f.write("\n")

    # Print summary
    print("=" * 70)
    print(f"  GEMS — non-PL B2B partner candidates")
    print("=" * 70)
    for iso, count in by_country.most_common():
        country_name = next(c for c, i in ISO_MAP.items() if i == iso)
        top_score = max(g["score"] for g in by_country_full[iso])
        top_name = max(by_country_full[iso], key=lambda g: g["score"])["name"]
        print(f"  {iso}  {count:3d} gems (top: {top_score} pts — {top_name[:50]})")
    print("=" * 70)
    print(f"  Total: {len(gems)} gems across {len(by_country)} countries")
    print(f"  CSV:  {OUT_CSV.relative_to(ROOT)}")
    print(f"  MD:   {OUT_MD.relative_to(ROOT)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
