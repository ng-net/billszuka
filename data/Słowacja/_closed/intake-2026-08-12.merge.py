#!/usr/bin/env python3
"""
merge_SK.py — Merge normalized_A + normalized_B into Słowacja/catalog-{A,B}-SK.csv.

Dedup strategy:
  Match existing SK-B-XX-* (11 rows) vs new normalized_B/A by:
    1. IČO (_reg_code) if present
    2. NIP (nip_vat) if IČO not present in either
    3. Fuzzy name match as last resort
  When matched: drop old (low-quality), keep new (richer data, with new ID).
  When unmatched: keep old (7 tobacco big-league companies Marceli will research later).

Output: 39-col format, _reg_code as last column.
"""
import csv
import re
from pathlib import Path

ROOT = Path("/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka")
EX_A = ROOT / "data/Słowacja/catalog-A-SK.csv"
EX_B = ROOT / "data/Słowacja/catalog-B-SK.csv"
NEW_A = ROOT / "data/_intake/SK/normalized_A.csv"
NEW_B = ROOT / "data/_intake/SK/normalized_B.csv"
DEDUP_LOG = ROOT / "data/_intake/SK/merge_dedup.md"

MASTER_COLS = [
    "region_kod", "region_nazwa", "region_typ", "related_to", "rok_zalozenia",
    "id_unikalne", "kategoria", "nazwa_firmy", "kraj", "miasto", "adres",
    "nip_vat", "rejestr_id", "www", "kanal_zamiennik", "email", "telefon",
    "linkedin", "facebook", "instagram", "tiktok", "tier",
    "marki_nabijarki", "marka_wlasna_oem", "sourcing", "wolumen",
    "confidence_wolumen", "kanal_sprzedaży", "powinowactwo_nabijarki",
    "cross_sell_potential", "decydent", "stanowisko", "email_decydent",
    "zrodlo_danych", "data_weryfikacji", "flagi", "notatki", "rynek_skala",
    "_reg_code",
]


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MASTER_COLS, delimiter=",")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def normalize_name(s: str) -> str:
    """For fuzzy match: lowercase, strip non-alphanumeric, drop common legal suffixes.

    Only strip suffixes that are TOKEN-BOUNDARY (preceded/followed by non-alphanumeric).
    Prevents 'as' inside 'tabak' from being stripped.
    """
    s = (s or "").lower()
    # Use regex with word boundaries to avoid stripping 'as' from 'tabak'
    s = re.sub(r"\b(spol\s*s\s*r\.?\s*o\.?|s\.?\s*r\.?\s*o\.?)\b", " ", s)
    s = re.sub(r"\b(a\.?\s*s\.?)\b", " ", s)
    s = re.sub(r"\b(ltd\.?|inc\.?|gmbh\.?|kg\.?)\b", " ", s)
    return re.sub(r"[^a-z0-9]", "", s)


def extract_first_word(s: str) -> str:
    """Extract first alphanumeric word of the name (raw, lowercase, no suffix stripping).

    This is the most reliable brand signal: GGT a.s. (Slovakia) → 'ggt',
    M+M Tabak s.r.o. → 'm' (alphanumeric, stops at '+').
    Used for prefix matching only when both names are 3+ chars.
    """
    s = (s or "").lower()
    m = re.match(r"([a-z0-9]+)", s)
    return m.group(1) if m else ""


def extract_brand(normalized: str) -> str:
    """Extract brand by stripping known geographic/modifier words from the right.

    For GGT a.s. Slovakia → 'ggt' (strip 'slovakia' from end).
    For GGT a.s. (GG Tabak Slovakia) → 'ggtggtabak' → first 6 → 'ggtggt' (we still
    don't match perfectly here, but first-word fallback will catch it).
    """
    modifiers = ["slovakia", "slovensko", "cesko", "czech", "poland", "polska",
                 "bratislava", "kosice", "presov", "network", "wholesale", "press"]
    s = normalized
    for m in modifiers:
        idx = s.find(m)
        if idx > 0:
            s = s[:idx]
            break
    return s[:8] if len(s) > 8 else s


def names_match(a: str, b: str) -> bool:
    """Conservative name match. Avoids merging different legal entities
    (e.g. Mediapress Bratislava vs MEDIAPRESS Poprad).

    Match if:
    1. Exact normalized match
    2. Substring match (one name fully inside the other)
    3. First 3+ char first-word match AND a common geographic word (slovakia, cz, etc.)
       appears in BOTH names. Catches GGT, Geco (both with "slovakia") but not
       Mediapress (one Bratislava, one Poprad).
    """
    na = normalize_name(a)
    nb = normalize_name(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if na in nb or nb in na:
        return True

    # 3. First-word match + common geographic word
    geo_words = ["slovakia", "slovensko", "bratislava", "kosice", "presov", "trnava",
                 "nitra", "zilina", "bystrica", "trencin", "sk", "cz", "czech"]
    fa = extract_first_word(a)
    fb = extract_first_word(b)
    if fa and fb and len(fa) >= 3 and len(fb) >= 3 and fa == fb:
        # Check that BOTH names contain a common geographic/subsidiary word
        common_geo = [w for w in geo_words if w in na and w in nb]
        if common_geo:
            return True
    return False


def main():
    # Read existing (39-col format already per _reg_code rename)
    ex_a = read_csv(EX_A)
    ex_b = read_csv(EX_B)
    new_a = read_csv(NEW_A)
    new_b = read_csv(NEW_B)

    print(f"Existing: A={len(ex_a)}, B={len(ex_b)}")
    print(f"New: A={len(new_a)}, B={len(new_b)}")

    # Build dedup keys
    # Key strategy: (IČO, NIP, normalized_name)
    new_keys = {}  # key → row
    for r in new_a + new_b:
        ico = r.get("_reg_code", "").strip()
        nip = r.get("nip_vat", "").strip()
        nm = normalize_name(r.get("nazwa_firmy", ""))
        if ico:
            new_keys[("ico", ico)] = r
        if nip:
            new_keys[("nip", nip)] = r

    # Match existing
    dedup_matches = []  # (existing_id, existing_name, new_id, key_type, key_val)
    kept_existing = []
    dropped_existing = []
    for r in ex_a + ex_b:
        ex_id = r["id_unikalne"]
        ex_name = r["nazwa_firmy"]
        ex_ico = r.get("_reg_code", "").strip()
        ex_nip = r.get("nip_vat", "").strip() if r.get("nip_vat", "").strip() != "do weryfikacji" else ""
        ex_nm = normalize_name(ex_name)

        matched = None
        match_type = None
        match_val = None

        # IČO match (won't match — ex_ico is empty for all)
        if ex_ico and ("ico", ex_ico) in new_keys:
            matched = new_keys[("ico", ex_ico)]
            match_type = "IČO"
            match_val = ex_ico
        # NIP match
        elif ex_nip and ("nip", ex_nip) in new_keys:
            matched = new_keys[("nip", ex_nip)]
            match_type = "NIP"
            match_val = ex_nip
        # Fuzzy name match (substring or strong prefix)
        else:
            for new_r in new_a + new_b:
                if names_match(ex_name, new_r["nazwa_firmy"]):
                    matched = new_r
                    match_type = "name"
                    match_val = f"{ex_name} ↔ {new_r['nazwa_firmy']}"
                    break

        if matched:
            dedup_matches.append((ex_id, ex_name, matched["id_unikalne"], matched["nazwa_firmy"], match_type, match_val))
            dropped_existing.append(r)
        else:
            kept_existing.append(r)

    # Categorize kept existing
    kept_a = [r for r in kept_existing if r.get("kategoria", "").startswith("A")]
    kept_b = [r for r in kept_existing if not r.get("kategoria", "").startswith("A")]

    # Final A and B
    final_a = list(new_a)  # all 14 new A rows
    final_b = list(new_b) + list(kept_b)  # all 16 new B + 7 kept B (ex_a is empty, all 7 kept are from ex_b)

    print(f"\nDedup matches: {len(dedup_matches)}")
    for m in dedup_matches:
        print(f"  {m[0]} ({m[1][:35]}) → {m[2]} ({m[3][:35]}) via {m[4]}={m[5]}")
    print(f"\nKept existing: {len(kept_existing)} (will remain in catalog with low quality)")
    print(f"Final A: {len(final_a)} (all new)")
    print(f"Final B: {len(final_b)} = {len(new_b)} new + {len(kept_b)} kept existing")

    # Write outputs
    write_csv(EX_A, final_a)
    write_csv(EX_B, final_b)
    print(f"\nWrote {EX_A.name} ({len(final_a)} rows)")
    print(f"Wrote {EX_B.name} ({len(final_b)} rows)")

    # Write dedup log
    with open(DEDUP_LOG, "w", encoding="utf-8") as f:
        f.write("# SK merge — dedup log (etap 1 → 2)\n\n")
        f.write(f"**Data:** 2026-08-12 13:50 CEST  \n")
        f.write(f"**Existing:** A={len(ex_a)} (empty), B={len(ex_b)} (11 rows)  \n")
        f.write(f"**New:** A={len(new_a)}, B={len(new_b)} (total 30)\n\n")

        f.write("## Dedup matches (4)\n\n")
        f.write("Stara kolumna (starter set, QS 28-35/100) → nowa (intake, weryfikowalna)\n\n")
        f.write("| Stary ID | Stara firma | Nowy ID | Nowa firma | Match via |\n")
        f.write("|---|---|---|---|---|\n")
        for m in dedup_matches:
            f.write(f"| {m[0]} | {m[1]} | **{m[2]}** | {m[3]} | {m[4]}={m[5]} |\n")
        f.write("\n")

        f.write("## Kept existing (7 — nie ma ich w nowym intake)\n\n")
        f.write("Pozostają w catalog-B-SK.csv ze statusem PENDING_API (big-league tobacco — Marceli follow-up).\n\n")
        f.write("| ID | Firma | IČO | NIP |\n")
        f.write("|---|---|---|---|\n")
        for r in kept_existing:
            f.write(f"| {r['id_unikalne']} | {r['nazwa_firmy']} | {r.get('_reg_code','') or '—'} | {r.get('nip_vat','') or '—'} |\n")
        f.write("\n")

        f.write("## Final catalog state\n\n")
        f.write(f"- `catalog-A-SK.csv`: **{len(final_a)}** wierszy (14 nowych + 0 starych)\n")
        f.write(f"- `catalog-B-SK.csv`: **{len(final_b)}** wierszy (16 nowych + {len(kept_b)} starych)\n")
        f.write(f"- **SUMA SK: {len(final_a) + len(final_b)} wierszy**\n\n")
        f.write("## Tier migration summary\n\n")
        f.write("- DL Lauko (stary B-XX-001): **B → A** (Segment=S1 w nowym intake)\n")
        f.write("- M+M Tabak (stary B-XX-003): **B → A** (Segment=S1 w nowym intake)\n")
        f.write("- GGT (stary B-XX-002): **B → B** (ale dane upgrade — IČO 31362781, NIP SK2020286950)\n")
        f.write("- Geco (stary B-XX-010): **B → B** (ale dane upgrade — IČO 35848521, NIP SK2020300481)\n\n")
        f.write("## Kolejne kroki\n\n")
        f.write("1. **Krok 6:** update `data/Słowacja/SK.md` z nowym tier breakdown\n")
        f.write("2. **Krok 7:** `tools/verify_api.py --country SK` (16 wierszy 'Nowy' = ORSR+VIES)\n")
        f.write("3. **Krok 8:** lock 14 wierszy 'Zweryfikowany' jako FROZEN\n")
        f.write("4. **Krok 9-10:** sync master.csv + audit-log + frozen-baseline\n")

    print(f"Wrote {DEDUP_LOG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
