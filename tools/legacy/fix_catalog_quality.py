#!/usr/bin/env python3
"""
fix_catalog_quality.py — One-shot comprehensive cleanup for ALL per-country catalogs.

Actions per catalog file:
  1. Remove retail/noise rows (uses RETAIL_BLACKLIST, respects DIST_WHITELIST)
  2. Remove rows that duplicate an entry already in catalog-A (by normalized name or Place ID)
  3. Deduplicate within the file by rejestr_id (Place ID) and normalized name
  4. Renumber id_unikalne sequentially (SI-B-001, SI-B-002, … preserving catalog type A/B)
  5. Write clean file atomically

Run: python3 tools/fix_catalog_quality.py [--dry-run]
"""
import csv
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR, make_id

DRY_RUN = "--dry-run" in sys.argv

# ── Retail / noise keywords ──────────────────────────────────────────────────
RETAIL_BLACKLIST = [
    "iqos", "relay ", "drugstore", "lounge bar", "vape shop", "vapista",
    "smoke shop", "bat.com", "jti.com", "imperialbrandsplc.com",
    "facebook.com", "instagram.com", "trafika", "civette",
    "fdj", " pmu", "nickel", "elfbar", "spirits & wine", "davidoff of geneva",
    "tabac des catacombes", "tabac de la bourse", "tabac saint-germain",
    "tabac le terminus", "tabac le voltaire", "tabac de la reynie",
    "art tabac", "beau drugstore", "7j/7j tabac", "tabac circle",
    "tabac du trocadero", "tabac des sports", "la tabatiere",
    "tabakas studija", "tabakas nams",  # individual retail chain shops (not HQ)
    "cigari ", "amstergrams",
    "ozzo smoke", "puffkalica", "nicobros", "happy cigars",
    "british american tobacco finland",
    "souvenirs, tobacco", "telemax", "tisak", "dragor lux",
    "tabakeria art", "tabakeria ",
    "hookah.si", "hookahshop", "hookah shop",
    "pyur smoke", "belidim", "q store:", "fuga store", "the clouds space",
    "vaporizer, prodajalna", "hadouta shisha", "trojashisha",
    "cigar lounge bar", "havana cigar point", "cigar house",
    "smoke shop 420", "rolling paper & tobacco", "tobacco city",
    "happy cigars", "vaperbg", "esmoker.bg", "vape bulgaria",
    "nargile.bg", "best cigars lounge", "corojoclubcigarshop",
    "aficionado cigar shops", "la casa del habano",
    "bongai.lt", "skonis ir kvapas", "cigarų namai",
    "iqos parduotuvė", "iqos store", "relay paris",
    "tabac saint", "tabac le ", "tabac des ", "tabac du ",
    "civette ", "la civette", "civette rennes",
    "trafika - dýmka", "tobacco shop",  # generic name with no B2B signal
    "moje trafika", "tobacc dc trafika",
    "kryptonit kratom", "ejuice.cz", "vapestyle",
    "vape shop n1", "vape in czech", "hookahs aladin",
    "doutníky praha", "doutníky-rb", "stanislav cigar",
    "albertapipes", "alberta pīpes", "albert pipes",
    "tabacalera", "shadow tobacco", "get • store",
    "tutun vrac firicel", "trabucuri de lux", "davidoff of geneva baneasa",
    "magazin fadi", "tabacco house", "newsmoke vape", "casa del tabaco",
    "mister tabaco", "tabaks.md",
    "prodejna", "prodajalna", "prodaja časopisov",
    "spela radic", "špela radić",
]

# Whitelist overrides blacklist — these signal real B2B even if blacklist matches
DIST_WHITELIST = [
    "distribution", "distribut", "wholesale", "trading", "logistics",
    "export", "import", "veleprodaj", "vairumtird", "hulgimyyk",
    "didmenin", "grossiste", "edro ", "srl", " ltd", " as ",
    " sia ", "sp. z", "s.r.o", "d.o.o.", " oü", "tabak invest",
    "ggt", "makro", "peal inc", "tobacco dc", "tobacco moravia",
    "tobacco valmont", "geco", "traficon", "phenix trade",
    "mp tobacco", "mostex", "interbrands", "tobacco logistic",
    "tobacco distribution", "tobacco trading", "ltt as", "prike as",
    "nicorex", "fib trade", "m tobacco", "tutun-ctc", "tutun ieftin",
    "tabakum export", "scandinavian tobacco group",
    "jt international", "philip morris", "imperial tobacco",
    "sanitex", "rasta 1", "tabakas nams grupa",
    "grosist", "grossist",
]

# Entries to always remove regardless of whitelist
HARD_BLACKLIST_NAMES = {
    "hookah.si ljubljana - specializirana tobačna trgovina. shisha shop. head shop. tobacco shop.",
    "pyur smoke", "belidim ljubljana center - premium vape & cbd shop",
    "belidim - premium vape & cbd shop", "trojashisha- adalya shop",
    "q store: trgovina z brezdimnimi izdelki", "fuga store",
    "the clouds space", "vaporizer, prodajalna elektronskih uparjalnikov za zelišča",
    "hadouta shisha lounge", "cigar lounge bar", "havana cigar point",
    "smoke shop 420", "happy cigars", "tobacco city", "rolling paper & tobacco",
    "cigar house", "nicobros",
}


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())


def is_noise(row: dict) -> bool:
    name = row.get("nazwa_firmy", "").lower().strip()
    www = row.get("www", "").lower()
    combined = name + " " + www

    if normalize(name) in HARD_BLACKLIST_NAMES:
        return True
    if any(w in combined for w in DIST_WHITELIST):
        return False
    return any(b in combined for b in RETAIL_BLACKLIST)


def load_place_ids_and_names(path: Path) -> tuple[set, set]:
    """Return (set of place_ids, set of normalized names) from a catalog file."""
    place_ids, names = set(), set()
    if not path.exists():
        return place_ids, names
    for row in csv.DictReader(open(path, encoding="utf-8")):
        rid = row.get("rejestr_id", "").strip()
        if rid and rid != "brak" and rid.startswith("ChIJ"):
            place_ids.add(rid)
        n = normalize(row.get("nazwa_firmy", ""))
        if n:
            names.add(n)
    return place_ids, names


def fix_catalog(cat_path: Path, iso: str, cat_type: str,
                a_place_ids: set, a_names: set) -> dict:
    """Clean one catalog file. Returns stats dict."""
    rows = list(csv.DictReader(open(cat_path, encoding="utf-8")))
    original = len(rows)
    stats = {"original": original, "noise": 0, "dup_a": 0, "dup_self": 0, "kept": 0}

    # 1. Remove retail noise
    clean1 = []
    for r in rows:
        if is_noise(r):
            stats["noise"] += 1
        else:
            clean1.append(r)

    # 2. Remove if already in catalog-A (only applies to catalog-B)
    clean2 = []
    if cat_type == "B":
        for r in clean1:
            rid = r.get("rejestr_id", "").strip()
            n = normalize(r.get("nazwa_firmy", ""))
            if (rid and rid in a_place_ids) or (n and n in a_names):
                stats["dup_a"] += 1
            else:
                clean2.append(r)
    else:
        clean2 = clean1

    # 3. Deduplicate within this file (by rejestr_id, then by name)
    seen_ids, seen_names = set(), set()
    clean3 = []
    for r in clean2:
        rid = r.get("rejestr_id", "").strip()
        n = normalize(r.get("nazwa_firmy", ""))
        if rid and rid != "brak" and rid in seen_ids:
            stats["dup_self"] += 1
            continue
        if n and n in seen_names:
            stats["dup_self"] += 1
            continue
        if rid and rid != "brak":
            seen_ids.add(rid)
        if n:
            seen_names.add(n)
        clean3.append(r)

    stats["kept"] = len(clean3)

    # 4. Renumber id_unikalne sequentially (preserving rows that already have good IDs first)
    # Sort: rows with real enrichment (non-B9, or has nip_vat/www/phone) go first
    def sort_key(r):
        has_data = bool(r.get("nip_vat") or r.get("www") or r.get("telefon") or r.get("email"))
        cat_code = r.get("kategoria", "B9")
        is_b9 = cat_code.endswith("9")
        return (is_b9, not has_data)  # enriched rows first

    clean3.sort(key=sort_key)

    for i, r in enumerate(clean3, start=1):
        r["id_unikalne"] = make_id(iso, cat_type, i)

    if not DRY_RUN and clean3 != rows:
        fieldnames = list(clean3[0].keys()) if clean3 else CANONICAL_SCHEMA
        # Ensure canonical schema columns
        tmp = cat_path.with_suffix(".csv.tmp")
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
            w.writeheader()
            for r in clean3:
                row_out = {k: r.get(k, "") for k in CANONICAL_SCHEMA}
                w.writerow(row_out)
        tmp.replace(cat_path)

    return stats


def main():
    print("=" * 70)
    print("BILLSzuka — Comprehensive catalog quality fix")
    mode = "[DRY-RUN]" if DRY_RUN else "[LIVE]"
    print(f"  {mode} Targets: all A+B catalogs for 11 non-PL countries")
    print("  Actions: noise removal · dedup vs A · self-dedup · renumber IDs")
    print("=" * 70)

    total_orig = total_noise = total_dup_a = total_dup_self = total_kept = 0

    for iso, dirname in sorted(COUNTRY_MAP.items()):
        if iso == "PL":
            continue

        a_path = DATA_DIR / dirname / f"catalog-A-{iso}.csv"
        b_path = DATA_DIR / dirname / f"catalog-B-{iso}.csv"
        a_place_ids, a_names = load_place_ids_and_names(a_path)

        for cat_type, cat_path in [("A", a_path), ("B", b_path)]:
            if not cat_path.exists():
                continue
            s = fix_catalog(cat_path, iso, cat_type, a_place_ids, a_names)
            total_orig += s["original"]
            total_noise += s["noise"]
            total_dup_a += s["dup_a"]
            total_dup_self += s["dup_self"]
            total_kept += s["kept"]

            removed = s["noise"] + s["dup_a"] + s["dup_self"]
            tag = "✓ clean" if removed == 0 else f"→ removed {removed} ({s['noise']} noise, {s['dup_a']} dup-A, {s['dup_self']} dup-self)"
            print(f"  {iso} [{cat_type}]: {s['original']} rows → {s['kept']} kept  {tag}")

    print()
    print("=" * 70)
    print(f"  TOTAL: {total_orig} rows → {total_kept} kept")
    print(f"  Removed: {total_noise} noise | {total_dup_a} dup-A | {total_dup_self} dup-self")
    if DRY_RUN:
        print("  [DRY-RUN] No files modified.")
    else:
        print("  All files written. Run billszuka.py compile next.")
    print("=" * 70)


if __name__ == "__main__":
    main()
