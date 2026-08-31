#!/usr/bin/env python3
"""
Normalize PL: 25 cols (Marceli) → 37 cols (master).
Per mapping.md (data/_intake/PL/mapping.md).

Decisions (from Marceli 2026-08-10):
  - Region: LB=lubuskie, LU=lubelskie (NUTS-2)
  - Priorytet D: drop UNLESS has NIP or WWW
  - Status column: DROP, rekonstruuj z L0
  - A1-A6 dla unclear S1: A4 default + 🔍

Output:
  data/_intake/PL/normalized_A.csv  (katalog A — firmy z maszynami)
  data/_intake/PL/normalized_B.csv  (katalog B — cross-sell)
  data/_intake/PL/normalized_dropped.csv (Dlaczego wyrzucone)
  data/_intake/PL/hallucination_audit.md (raport)
"""

import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
INTAKE = ROOT / "data/_intake/PL"
SOURCE = INTAKE / "source.csv"

from config import CANONICAL_SCHEMA as SCHEMA, make_id

# Województwo → region_kod (NUTS-2 zgodnie z decyzją: LB=lubuskie, LU=lubelskie)
WOJ_TO_KOD = {
    "dolnośląskie": "DS", "kujawsko-pomorskie": "KP", "lubelskie": "LU",
    "lubuskie": "LB", "łódzkie": "LD", "małopolskie": "MA", "mazowieckie": "MZ",
    "opolskie": "OP", "podkarpackie": "PK", "podlaskie": "PD", "pomorskie": "PM",
    "śląskie": "SL", "świętokrzyskie": "SK", "warmińsko-mazurskie": "WM",
    "wielkopolskie": "WP", "zachodniopomorskie": "ZP",
}

WOJ_TO_NAZWA = {k: k for k in WOJ_TO_KOD}

# Relacja → tier
RELACJA_TO_TIER = {
    "potencjalny reseller / odbiorca hurtowy": "reseller",
    "partner dystrybucyjny/importer": "autoryzowany",
    "partner strategiczny / producent": "producent",
    "partner strategiczny / możliwy konflikt produktowy": "marketplace",  # flaga 🔴
    "partner cross-sell / kanał sąsiedni": "hurtownik",
    "sprzedawca detaliczny/e-commerce": "detalista",
    "do weryfikacji": "marketplace",
    "wykluczyć — podmiot własny bills": "EXCLUDE",
}

# Kanał → kanal_sprzedaży
KANAL_TO_KANAL = {
    "hurt ogólnopolski": "B2B only",
    "hurt b2b + detal": "mix",
    "hurt b2b regionalny": "B2B only",
    "importer/dystrybutor krajowy": "B2B only",
    "detal/e-commerce": "własny e-commerce",
    "sieć detaliczna/omnichannel": "mix",
    "producent": "B2B only",
    "producent/importer/dystrybutor": "mix",
}

# Skala → (wolumen, confidence)
SKALA_TO_WOL = {
    "duży": ("duży", "🟢"),
    "duża": ("duży", "🟢"),
    "średni": ("średni", "🟢"),
    "średnia": ("średni", "🟢"),
    "mały–średni": ("średni", "🟡"),
    "mały-średni": ("średni", "🟡"),
    "mały": ("mały", "🟢"),
}

NABIJARKI_KW = ['nabijark', 'powermatic', 'inject', 'filling machine', 'maszynk',
                'zwijark', 'rolling machin', 'injector', 'półautomatyczn',
                'rdzeń systemu nabijarek']


def normalize_text(s):
    if not s:
        return ""
    s = unicodedata.normalize('NFC', s).strip()
    return s


def nip_clean(s):
    if not s:
        return ""
    s = s.strip().replace(' ', '').replace('-', '').replace('.0', '')
    if s.endswith('.0'):
        s = s[:-2]
    return s if (s.isdigit() and len(s) == 10) else ""


def krs_clean(s):
    if not s:
        return ""
    s = s.strip().replace(' ', '').replace('.0', '')
    if s.endswith('.0'):
        s = s[:-2]
    if not s.isdigit():
        return ""
    if len(s) in (8, 9, 10):
        return s
    if len(s) < 8:
        return s + "(?)"  # zły format
    return s


def classify_ab(segment, produkty):
    """Re-classify per mapping.md."""
    seg = (segment or "").lower()
    prod = (produkty or "").lower()
    has_nab = any(kw in prod for kw in NABIJARKI_KW)
    is_s1 = "s1" in seg and "ryo/myo" in seg
    is_s2 = "s2" in seg and "hurtownie" in seg
    is_s3 = "s3" in seg and "akcesoria" in seg
    is_s4 = "s4" in seg and "vape" in seg
    is_s5 = "s5" in seg
    is_s6 = "s6" in seg
    is_s7 = "s7" in seg

    if is_s1:
        # KATALOG A — RYO/MYO segment
        # Wewnątrz A — klasyfikuj wg Produkty/marki
        prod_l = prod
        has_pm = "powermatic" in prod_l
        has_hawk = "hawk" in prod_l
        has_own_brand = any(m in prod_l for m in
                            ["dark horse", "mascotte", "gerui", "matteo",
                             "angel", "zen", "champ", "premier", "korona", "zorr"])
        if has_pm and has_hawk:
            return "A", "A3"
        if has_pm:
            return "A", "A1"
        if has_hawk:
            return "A", "A2"
        if has_nab:
            return "A", "A4"
        # S1 ale brak słowa "nabijarka" w produkty → A4 default per decyzja
        return "A", "A4"

    if is_s2:
        return "B", "B8"
    if is_s3:
        return "B", "B4"
    if is_s4:
        return "B", "B6"
    if is_s5:
        return "B", "B4"  # trafiki premium = akcesoria
    if is_s6:
        return "B", "B4"  # retail = akcesoria
    if is_s7:
        return "B", "B9"  # niezweryfikowane = CBD/susz analog
    return "B", "B9"  # unknown = DO-WERYFIKACJI


def get_brand_list(produkty):
    """Extract list of nabijarka brands from Produkty/marki."""
    if not produkty:
        return ""
    # Szukamy marek
    BRANDS = ["PowerMatic", "Hawk", "Topomat", "Turbomatic", "GM", "Dark Horse",
              "Mascotte", "Gerui", "Matteo", "Angel", "Zen", "Champ", "Premier",
              "Korona", "Zorr", "OCB", "RAW", "MOODS", "Al Capone", "Smoking",
              "Retro", "Clipper", "BIC"]
    found = []
    pl = produkty.lower()
    for b in BRANDS:
        if b.lower() in pl:
            found.append(b)
    return ", ".join(found[:8]) if found else ""


def get_own_brand(produkty):
    """Detect own brand indicator (A5)."""
    if not produkty:
        return ""
    ind = ["dark horse", "mascotte", "gerui", "matteo", "angel", "zen",
           "champ", "premier", "korona", "zorr", "własna marka", "oem"]
    pl = produkty.lower()
    for i in ind:
        if i in pl:
            return i.title()
    return ""


def build_notatki(row, orig_idx, kategoria):
    """Build notatki from Uzasadnienie + Uwagi + fragmenty Status."""
    parts = []
    u = normalize_text(row.get("Uzasadnienie potencjału", ""))
    if u:
        parts.append(f"orig_uzasadnienie: {u[:200]}")
    w = normalize_text(row.get("Uwagi", ""))
    if w:
        parts.append(f"orig_uwagi: {w[:300]}")
    nk = normalize_text(row.get("Następny krok", ""))
    if nk:
        parts.append(f"orig_next: {nk[:200]}")
    # Dodaj info o user_orig_*
    parts.append(f"user_orig_priorytet={row.get('Priorytet','')[:50]!r}")
    parts.append(f"user_orig_score={row.get('Score','')}")
    parts.append(f"user_orig_segment={row.get('Segment','')[:50]!r}")
    return " | ".join(parts)


def normalize_row(r, idx):
    """Map one row to 37-col dict."""
    firma = normalize_text(r.get("Firma", ""))
    relacja = normalize_text(r.get("Relacja", ""))
    segment = normalize_text(r.get("Segment", ""))
    kanal_t = normalize_text(r.get("Kanał", ""))
    woj = normalize_text(r.get("Województwo", ""))
    miasto = normalize_text(r.get("Miasto", ""))
    skala = normalize_text(r.get("Skala", ""))
    email = normalize_text(r.get("Email", ""))
    telefon = normalize_text(r.get("Telefon", ""))
    osoba = normalize_text(r.get("Osoba/Dział decyzyjny", ""))
    stanowisko = normalize_text(r.get("Stanowisko", ""))
    www = normalize_text(r.get("WWW", ""))
    adres = normalize_text(r.get("Adres", ""))
    nip = nip_clean(r.get("NIP", ""))
    krs = krs_clean(r.get("KRS", ""))
    produkty = normalize_text(r.get("Produkty/marki", ""))
    zrodla = normalize_text(r.get("Źródła", ""))

    # Exclusion
    if "wykluczyć" in relacja.lower() and "bills" in relacja.lower():
        return None, "EXCLUDE_BILLS"

    # Priorytet D — zachowaj te z NIP+WWW (per decyzja)
    priorytet = normalize_text(r.get("Priorytet", ""))
    if priorytet.startswith("D"):
        if not (nip and www):
            return None, "DROP_D_no_NIP_WWW"

    # Region
    woj_l = woj.lower().strip()
    region_kod = WOJ_TO_KOD.get(woj_l, "")
    region_nazwa = WOJ_TO_NAZWA.get(woj_l, woj)
    region_typ = "województwo" if region_kod else ""

    # Tier
    rel_l = relacja.lower().strip()
    tier = RELACJA_TO_TIER.get(rel_l, "")
    flagi_extra = ""
    if "konflikt produktowy" in rel_l:
        flagi_extra += "🔴"

    # Kanał
    kan_l = kanal_t.lower().strip()
    kanal = KANAL_TO_KANAL.get(kan_l, "")

    # Wolumen
    sk_l = skala.lower().strip()
    if sk_l in SKALA_TO_WOL:
        wolumen, conf = SKALA_TO_WOL[sk_l]
    elif sk_l in ("", "nieustalona"):
        wolumen, conf = ("", "🔴")
    else:
        # dziwne wartości
        wolumen, conf = ("", "🔴")

    # Classify A/B
    catalog, kategoria = classify_ab(segment, produkty)
    if not kategoria:
        kategoria = "B9"  # fallback

    # Powinowactwo + cross_sell (tylko B)
    if catalog == "B":
        pow_map = {"B1": 5, "B2": 5, "B3": 5, "B4": 3, "B5": 2, "B6": 2,
                   "B7": 2, "B8": 5, "B9": 4}
        cross_map = {"B8": "wysoki", "B1": "wysoki", "B2": "wysoki", "B3": "wysoki",
                     "B4": "średni", "B5": "niski", "B6": "średni", "B7": "średni",
                     "B9": "średni"}
        powinowactwo = pow_map.get(kategoria, 3)
        cross_sell = cross_map.get(kategoria, "średni")
    else:
        powinowactwo = ""
        cross_sell = ""

    # Marki / own brand
    marki = get_brand_list(produkty) if catalog == "A" else ""
    own_brand = get_own_brand(produkty) if catalog == "A" else ""

    # Sourcing — heurystyka per "wyłączność" tier lub PM/Hawk
    sourcing = ""
    if catalog == "A":
        if "Chiny" in produkty or "import" in (kanal_t or "").lower():
            sourcing = "Chiny"
        elif tier in ("producent", "autoryzowany"):
            sourcing = "Polska"
        else:
            sourcing = "mix"

    # zrodlo_danych
    zrodlo = zrodla
    if not zrodlo:
        zrodlo = f"intake_PL_2026-08-10 (user_score={r.get('Score','')})"
    else:
        zrodlo = f"intake_PL_2026-08-10 | {zrodlo[:200]}"

    # data_weryfikacji = None (do uzupełnienia po L0)
    data_weryfikacji = ""

    # Flagi — start
    flagi = "🔍"  # default = relacja z marką niezweryfikowana
    if flagi_extra:
        flagi = flagi_extra + flagi
    if catalog == "A" and "A5" == kategoria:
        flagi = "🔴" + flagi  # konkurent
    elif catalog == "A" and own_brand:
        flagi = "🟡" + flagi

    # Notatki
    notatki = build_notatki(r, idx, kategoria)

    # rynek_skala
    rynek_skala = "duży"  # PL

    out = {
        "region_kod": region_kod, "region_nazwa": region_nazwa,
        "region_typ": region_typ, "related_to": "", "rok_zalozenia": "",
        "id": "",  # assigned later
        "kategoria": kategoria, "nazwa": firma, "kraj": "PL",
        "miasto": miasto, "adres": adres, "nip_vat": nip, "rejestr_id": krs,
        "www": www, "kanal_zamiennik": "", "email": email, "telefon": telefon,
        "linkedin": "", "facebook": "", "instagram": "", "tiktok": "",
        "tier": tier, "marki_nabijarki": marki, "marka_wlasna_oem": own_brand,
        "sourcing": sourcing, "wolumen": wolumen, "confidence_wolumen": conf,
        "kanal_sprzedaży": kanal, "powinowactwo_nabijarki": powinowactwo,
        "cross_sell_potential": cross_sell, "decydent": osoba,
        "stanowisko": stanowisko, "email_decydent": "",
        "zrodlo_danych": zrodlo, "data_weryfikacji": data_weryfikacji,
        "flagi": flagi, "notatki": notatki, "rynek_skala": rynek_skala,
    }
    return out, kategoria


def assign_ids(rows_a, rows_b, existing_ids):
    """Assign id in format PL-A-{NNN} or PL-B-{NNN}."""
    for i, r in enumerate(rows_a, 1):
        r["id"] = f"PL-A-{i:03d}"
    for i, r in enumerate(rows_b, 1):
        r["id"] = f"PL-B-{i:03d}"


def dedupe(rows):
    """Dedupe by NIP (exact) or name+miasto (fuzzy)."""
    seen_nip = {}
    seen_name_miasto = {}
    out = []
    for r in rows:
        nip = r.get("nip_vat", "")
        firma = r.get("nazwa", "").lower().strip()
        miasto = r.get("miasto", "").lower().strip()
        if nip and nip in seen_nip:
            # merge: keep first, add note to second
            r["notatki"] += f" | DUPLIKAT_NIP:{seen_nip[nip]}"
            continue
        if nip:
            seen_nip[nip] = r["id"]
        # name+miasto dedupe (lenient)
        key = (firma[:15], miasto[:10])
        if key[0] and key in seen_name_miasto:
            r["notatki"] += f" | DUPLIKAT_NAME:{seen_name_miasto[key]}"
            continue
        if key[0]:
            seen_name_miasto[key] = r["id"]
        out.append(r)
    return out


def main():
    if not SOURCE.exists():
        print(f"❌ Brak {SOURCE}")
        sys.exit(1)

    with open(SOURCE, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    print(f"Input: {len(rows)} wierszy")

    normalized = []
    dropped = []
    stats = Counter()
    for i, r in enumerate(rows):
        out, reason = normalize_row(r, i)
        if out is None:
            dropped.append((i+2, reason, r.get("Firma", "")[:50]))
            stats[f"drop_{reason}"] += 1
        else:
            normalized.append(out)
            stats[f"cat_{out['kategoria']}"] += 1

    # Split A/B
    rows_a = [r for r in normalized if r["kategoria"].startswith("A")]
    rows_b = [r for r in normalized if r["kategoria"].startswith("B")]

    # Assign IDs
    assign_ids(rows_a, rows_b, existing_ids=set())

    # Dedupe within each catalog
    rows_a = dedupe(rows_a)
    rows_b = dedupe(rows_b)

    # Write outputs
    def write_csv(path, rows):
        with open(path, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=SCHEMA)
            w.writeheader()
            w.writerows(rows)

    write_csv(INTAKE / "normalized_A.csv", rows_a)
    write_csv(INTAKE / "normalized_B.csv", rows_b)
    print(f"\n✓ normalized_A.csv: {len(rows_a)} wierszy")
    print(f"✓ normalized_B.csv: {len(rows_b)} wierszy")
    print(f"✓ Dropped: {len(dropped)}")

    # Dropped details
    if dropped:
        with open(INTAKE / "normalized_dropped.csv", 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(["row_index", "reason", "firma"])
            for idx, reason, firma in dropped:
                w.writerow([idx, reason, firma])
        print(f"✓ normalized_dropped.csv: {len(dropped)} wpisów")

    # Stats
    print(f"\n=== Statystyki klasyfikacji ===")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")

    # Per-catalog breakdown
    print(f"\n=== Katalog A breakdown ===")
    a_cats = Counter(r["kategoria"] for r in rows_a)
    for k, v in a_cats.most_common():
        print(f"  {k}: {v}")
    print(f"\n=== Katalog B breakdown ===")
    b_cats = Counter(r["kategoria"] for r in rows_b)
    for k, v in b_cats.most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
