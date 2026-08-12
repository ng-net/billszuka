#!/usr/bin/env python3
"""
normalize_SK.py — Normalize 30-row SK source CSV to 39-col master schema.

Splits by Segment:
  S1 (Nabijarki RYO/MYO) → normalized_A.csv
  S2/S3/S4 (Hurt / E-pap / FMCG) + non-S segments → normalized_B.csv

Writes hallucination audit to normalize_audit.md.
"""
import csv
import re
import json
from pathlib import Path
from datetime import datetime

ROOT = Path("/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka")
SRC = ROOT / "data/_intake/SK/source.csv"
OUT_A = ROOT / "data/_intake/SK/normalized_A.csv"
OUT_B = ROOT / "data/_intake/SK/normalized_B.csv"
AUDIT = ROOT / "data/_intake/SK/normalize_audit.md"

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

REGION_MAP = {
    "Bratislavský kraj": "BA", "Bratislavsky kraj": "BA",
    "Trnavský kraj": "TT", "Trnavsky kraj": "TT",
    "Trenčiansky kraj": "TN", "Trenciansky kraj": "TN",
    "Nitriansky kraj": "NR", "Nitriansky kraj": "NR",
    "Žilinský kraj": "ZA", "Žilina Region": "ZA", "Zilinsky kraj": "ZA",
    "Banskobystrický kraj": "BB", "Banskobystricky kraj": "BB",
    "Prešovský kraj": "PO", "Presovsky kraj": "PO",
    "Košický kraj": "KE", "Kosicky kraj": "KE",
}

SCALE_MAP = {
    "Bardzo duży": "Bardzo duży",  # keep PL label
    "Duży": "Duży",
    "Duża": "Duży",
    "Średnia": "Średni",
    "Średni": "Średni",
    "Mała": "Mały",
    "Kluczowy Dystrybutor Krajowy": "Bardzo duży",  # collapse
    "Duży Hurtownik": "Duży",
    "Lider Sieci Vape": "Duży",
    "Średni Hurtownik Specializowany": "Średni",
    "Duży Hurtownik Regionalny": "Duży",
    "Lider Regionalny Wschód": "Duży",
    "Duży Distribútor (1,000+ odbieraczy B2B)": "Duży",
    "Średni Specialistyczny B2B/B2C": "Średni",
    "Duży Distribútor Międzynarodowy": "Bardzo duży",
    "Średni Hurtownik Regionalny": "Średni",
    "Duży Importer i Hurtownik B2B": "Duży",
    "Międzynarodowy Importer & Hurtownik B2B": "Bardzo duży",
    "Oficjalny Importer Narodowy": "Duży",
    "Średni Importer Specializovaný": "Średni",
    "Średni Importer Regionalny": "Średni",
    "Duży Importer i Hurtownik Regionalny": "Duży",
}


def reclassify(segment: str, priorytet: str) -> tuple[str, str]:
    """Return (kategoria, kanal_sprzedaży) based on Segment + Priorytet."""
    seg = (segment or "").strip()
    prio = (priorytet or "").strip()

    if seg.startswith("S1"):
        # A-tier: A1 if "kontakt natychmiast", A2 if "partner regionalny" / "wysoki potencjał"
        if "kontakt natychmiast" in prio:
            return ("A1", "B2B only")
        return ("A2", "B2B only")

    if seg.startswith("S2"):
        # B1 (hurt tytoniowy)
        return ("B1", "Hurt B2B regionalny")
    if seg.startswith("S3"):
        # B6 (e-papierosy)
        return ("B6", "Hurt B2B regionalny")
    if seg.startswith("S4"):
        # B8 (pełne hurtownie tytoniowe)
        return ("B8", "Hurt B2B ogólnokrajowy")

    # non-S fallbacks
    seg_low = seg.lower()
    if "smoking accessories" in seg_low and "ryo" in seg_low:
        return ("B4", "Hurt B2B regionalny")
    if "vape" in seg_low:
        return ("B6", "Hurt B2B regionalny")
    if "vaping" == seg_low.strip():
        return ("B6", "Hurt B2B regionalny")

    return ("B1", "Hurt B2B regionalny")  # default B-tier


def parse_ico(reg: str) -> tuple[str, str]:
    """Extract IČO (8 digits) from 'Numer Rejestrowy'. Return (rejestr_id, _reg_code)."""
    if not reg:
        return ("", "")
    # Try to find 8-digit IČO
    m = re.search(r"\b(\d{8})\b", reg)
    if m:
        ico = m.group(1)
        # rejestr_id = the original full string (cleaned)
        cleaned = reg.strip()
        return (cleaned, ico)
    return (reg.strip(), "")


def parse_email(email_field: str) -> str:
    """Take first email if multiple separated by ;"""
    if not email_field:
        return ""
    parts = [e.strip() for e in email_field.split(";") if e.strip()]
    return parts[0] if parts else ""


def region_kod(region_str: str) -> str:
    """Map 'Bratislavský kraj' → 'BA'."""
    if not region_str:
        return "XX"
    s = region_str.strip()
    return REGION_MAP.get(s, "XX")


def scale_value(skala: str) -> str:
    return SCALE_MAP.get((skala or "").strip(), "nieznany")


def cross_sell(kat: str) -> str:
    if kat in ("B1", "B8"):
        return "wysoki"
    if kat == "B4":
        return "średni"
    if kat == "B6":
        return "niski"
    return "średni"


def powinowactwo(kat: str) -> str:
    if kat in ("B1", "B8"):
        return "5 — najwyższy"
    if kat == "B4":
        return "3"
    if kat == "B6":
        return "2"
    return "3"


def build_tier(kat: str, relacja: str) -> str:
    if kat.startswith("A"):
        rl = (relacja or "").lower()
        if "wyłącz" in rl or "exclus" in rl:
            return "wyłączność"
        if "autoryz" in rl:
            return "autoryzowany"
        if "importer" in rl or "dystrybutor" in rl:
            return "hurtownik"
        if "marketplace" in rl or "e-commerce" in rl:
            return "marketplace"
        if "sklep" in rl or "retail" in rl or "trafik" in rl:
            return "detalista"
        return "reseller"
    if kat == "B1":
        return "hurtownik"
    if kat == "B8":
        return "hurtownik"
    if kat == "B4":
        return "hurtownik"
    if kat == "B6":
        return "hurtownik"
    return "do ustalenia"


def build_flagi(prio: str, score: str, status: str, intake_state: str) -> str:
    parts = []
    if prio:
        parts.append(f"priorytet: {prio}")
    if score:
        parts.append(f"score: {score}")
    if status:
        parts.append(f"status: {status}")
    parts.append(f"intake: {intake_state}")
    return " | ".join(parts)


def build_notatki(row: dict) -> str:
    parts = []
    if row.get("Uzasadnienie Potencjału"):
        parts.append(f"Uzasadnienie: {row['Uzasadnienie Potencjału'].strip()}")
    if row.get("Uwagi"):
        parts.append(f"Uwagi: {row['Uwagi'].strip()}")
    if row.get("Relacja"):
        parts.append(f"Relacja: {row['Relacja'].strip()}")
    if row.get("Status EORI"):
        parts.append(f"EORI: {row['Status EORI'].strip()}")
    if row.get("Zasięg"):
        parts.append(f"Zasięg: {row['Zasięg'].strip()}")
    if row.get("Oferta Powermatic") and not row.get("Segment", "").startswith("S1"):
        parts.append(f"Oferta Powermatic: {row['Oferta Powermatic'].strip()}")
    if row.get("Produkty i Marki") and not row.get("Segment", "").startswith("S1"):
        parts.append(f"Produkty: {row['Produkty i Marki'].strip()}")
    if row.get("Platforma E-Commerce"):
        parts.append(f"Platforma: {row['Platforma E-Commerce'].strip()}")
    return " | ".join(p for p in parts if p)


def main():
    with open(SRC, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")
        rows = list(reader)

    print(f"Read {len(rows)} rows from {SRC.name}")

    # ID counters per region for A-tier and B-tier (skip if not needed)
    a_counters = {}
    b_counters = {}

    a_rows = []
    b_rows = []
    audit_issues = []

    for row in rows:
        rank = row.get("Rank", "").strip()
        segment = row.get("Segment", "").strip()
        prio = row.get("Priorytet", "").strip()
        score = row.get("Score", "").strip()
        status = row.get("Status", "").strip()
        region_str = row.get("Region", "").strip()
        miasto = row.get("Miasto", "").strip()
        firma = row.get("Firma", "").strip()
        nip = row.get("NIP / VAT", "").strip()
        numer = row.get("Numer Rejestrowy", "").strip()

        rk = region_kod(region_str)
        kategoria, kanal = reclassify(segment, prio)
        rejestr_id, ico = parse_ico(numer)
        email = parse_email(row.get("Email", ""))
        skala = scale_value(row.get("Skala", ""))
        flagi = build_flagi(prio, score, status, "⏳ PENDING_API" if status == "Nowy" else "✅ FROZEN (Marceli)")
        notatki = build_notatki(row)
        tier = build_tier(kategoria, row.get("Relacja", ""))
        marki = row.get("Produkty i Marki", "").strip() or row.get("Oferta Powermatic", "").strip()

        if kategoria.startswith("A"):
            a_counters[rk] = a_counters.get(rk, 0) + 1
            idu = f"SK-A-{rk}-{a_counters[rk]:03d}"
        else:
            b_counters[rk] = b_counters.get(rk, 0) + 1
            idu = f"SK-B-{rk}-{b_counters[rk]:03d}"

        out = {
            "region_kod": rk,
            "region_nazwa": "nieznany",  # Marceli nie podaje
            "region_typ": "nieznany",
            "related_to": "",
            "rok_zalozenia": "",
            "id_unikalne": idu,
            "kategoria": kategoria,
            "nazwa_firmy": firma,
            "kraj": "SK",
            "miasto": miasto,
            "adres": row.get("Adres", "").strip(),
            "nip_vat": nip,
            "rejestr_id": rejestr_id,
            "www": row.get("WWW", "").strip(),
            "kanal_zamiennik": "",
            "email": email,
            "telefon": row.get("Telefon", "").strip(),
            "linkedin": "",
            "facebook": "",
            "instagram": "",
            "tiktok": "",
            "tier": tier,
            "marki_nabijarki": marki,
            "marka_wlasna_oem": "",  # unknown — patrz audit
            "sourcing": row.get("Kanał Importu", "").strip() if not kategoria.startswith("A") else "",
            "wolumen": "do ustalenia",
            "confidence_wolumen": "0.0",
            "kanal_sprzedaży": kanal,
            "powinowactwo_nabijarki": powinowactwo(kategoria) if not kategoria.startswith("A") else "",
            "cross_sell_potential": cross_sell(kategoria) if not kategoria.startswith("A") else "",
            "decydent": row.get("Decydent", "").strip() if row.get("Decydent", "").strip() != "Unknown" else "",
            "stanowisko": row.get("Stanowisko", "").strip(),
            "email_decydent": "",
            "zrodlo_danych": row.get("Źródła", "").strip() or "intake 2026-08-12",
            "data_weryfikacji": "2026-08-12",
            "flagi": flagi,
            "notatki": notatki,
            "rynek_skala": skala,
            "_reg_code": ico,
        }

        if kategoria.startswith("A"):
            a_rows.append(out)
        else:
            b_rows.append(out)

        # Audit checks
        if ico and len(ico) != 8:
            audit_issues.append(f"**{idu}** ({firma}): IČO `{ico}` ma {len(ico)} cyfr (oczekiwane 8)")
        if ico.startswith("45293"):
            audit_issues.append(f"**{idu}** ({firma}): IČO `{ico}` jest w serii `45293XXX` — wygląda na templated (Marceli batch r4-r11); wymaga ORSR potwierdzenia")
        if not row.get("Adres", "").strip():
            audit_issues.append(f"**{idu}** ({firma}): brak adresu w 'Adres'")
        if not row.get("Numer Rejestrowy", "").strip():
            audit_issues.append(f"**{idu}** ({firma}): brak 'Numer Rejestrowy' (IČO nie do ustalenia)")
        if not row.get("NIP / VAT", "").strip():
            audit_issues.append(f"**{idu}** ({firma}): brak 'NIP / VAT'")
        if "Unknown" in row.get("Decydent", ""):
            audit_issues.append(f"**{idu}** ({firma}): Decydent='Unknown' — Marceli nie znalazł; OSINT follow-up")
        if "b2b.sk" in row.get("Email", "").lower() or "labas" in row.get("Email", "").lower() or "metro" in row.get("Email", "").lower():
            audit_issues.append(f"**{idu}** ({firma}): Email `{row.get('Email','')}` wygląda na templated wzorzec Marcela (b2b.sk[N]@<domena>) — do weryfikacji VIES")

    # Write A and B
    def write_csv(path: Path, data: list):
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=MASTER_COLS, delimiter=",")
            w.writeheader()
            for r in data:
                w.writerow(r)
        print(f"Wrote {len(data)} rows to {path.relative_to(ROOT)}")

    write_csv(OUT_A, a_rows)
    write_csv(OUT_B, b_rows)

    # Add duplicate-name audit (run on both sets)
    a_names = {r["nazwa_firmy"] for r in a_rows}
    b_names = {r["nazwa_firmy"] for r in b_rows}
    cross_dupes = a_names & b_names
    if cross_dupes:
        for n in cross_dupes:
            audit_issues.append(f"**A↔B dups**: `{n}` pojawia się w A i B (prawdopodobnie parent + subsidiary LUB dwie rejestracje — patrz NIP/IČO)")

    # Same-NIP check
    nip_seen = {}
    for r in a_rows + b_rows:
        nip = r["nip_vat"]
        if nip and nip in nip_seen:
            audit_issues.append(f"**NIP dups**: `{nip}` w {nip_seen[nip]} i {r['id_unikalne']} ({r['nazwa_firmy']}) — patrz dedup")
        elif nip:
            nip_seen[nip] = r["id_unikalne"]

    # Same IČO check
    ico_seen = {}
    for r in a_rows + b_rows:
        ic = r["_reg_code"]
        if ic and ic in ico_seen:
            audit_issues.append(f"**IČO dups**: `{ic}` w {ico_seen[ic]} i {r['id_unikalne']} ({r['nazwa_firmy']}) — patrz dedup")
        elif ic:
            ico_seen[ic] = r["id_unikalne"]

    # Write audit
    with open(AUDIT, "w", encoding="utf-8") as f:
        f.write(f"# SK intake — normalizacja + audyt\n\n")
        f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M CEST')}\n")
        f.write(f"**Źródło:** `data/_intake/SK/source.csv` (30 wierszy)\n\n")
        f.write(f"## Wynik\n\n")
        f.write(f"- A-tier (S1 — Nabijarki RYO/MYO): **{len(a_rows)} wierszy** → `normalized_A.csv`\n")
        f.write(f"- B-tier (S2/S3/S4 + non-S): **{len(b_rows)} wierszy** → `normalized_B.csv`\n")
        f.write(f"- Łącznie: **{len(a_rows) + len(b_rows)} / 30**\n\n")
        f.write(f"## Re-kategoryzacja Segment → Kategoria\n\n")
        f.write(f"Per `mapping.md`:\n\n")
        f.write(f"| Segment Marcela | Kategoria projektu | # | Lista ID |\n")
        f.write(f"|---|---|---|---|\n")
        by_kat = {}
        for r in a_rows + b_rows:
            by_kat.setdefault(r["kategoria"], []).append(r["id_unikalne"])
        for k in sorted(by_kat.keys()):
            ids = ", ".join(by_kat[k])
            f.write(f"| — | **{k}** | {len(by_kat[k])} | {ids} |\n")
        f.write(f"\n")
        f.write(f"## ID assignment per region (A-tier)\n\n")
        f.write(f"| region_kod | region_nazwa (Marceli) | # | IDs |\n")
        f.write(f"|---|---|---|---|\n")
        a_by_reg = {}
        for r in a_rows:
            a_by_reg.setdefault(r["region_kod"], []).append(r["id_unikalne"])
        for r in sorted(a_by_reg.keys()):
            ids = ", ".join(a_by_reg[r])
            f.write(f"| **{r}** | — | {len(a_by_reg[r])} | {ids} |\n")
        f.write(f"\n")
        f.write(f"## ID assignment per region (B-tier)\n\n")
        f.write(f"| region_kod | # | IDs |\n")
        f.write(f"|---|---|---|\n")
        b_by_reg = {}
        for r in b_rows:
            b_by_reg.setdefault(r["region_kod"], []).append(r["id_unikalne"])
        for r in sorted(b_by_reg.keys()):
            ids = ", ".join(b_by_reg[r])
            f.write(f"| **{r}** | {len(b_by_reg[r])} | {ids} |\n")
        f.write(f"\n")
        f.write(f"## Halucynacja / audyt ({len(audit_issues)} flag)\n\n")
        if audit_issues:
            for i in audit_issues:
                f.write(f"- {i}\n")
        else:
            f.write(f"✅ Brak flag\n")
        f.write(f"\n")
        f.write(f"## Status flagów per wiersz (etap 1)\n\n")
        f.write(f"Stan przed weryfikacją (kroki 7-8):\n")
        f.write(f"- ✅ **FROZEN (Marceli)**: 14 wierszy (Status=Zweryfikowany) — patrz krok 8\n")
        f.write(f"- ⏳ **PENDING_API**: 16 wierszy (Status=Nowy) — patrz krok 7 (ORSR+VIES)\n")
        f.write(f"\n")
        f.write(f"## Per-wiersz snapshot\n\n")
        f.write(f"| ID | Firma | Kategoria | Status | IČO | NIP | Region |\n")
        f.write(f"|---|---|---|---|---|---|---|\n")
        for r in a_rows + b_rows:
            stat = "✅" if "FROZEN" in r["flagi"] else "⏳"
            f.write(f"| {r['id_unikalne']} | {r['nazwa_firmy'][:40]} | {r['kategoria']} | {stat} | {r['_reg_code'] or '—'} | {r['nip_vat'] or '—'} | {r['region_kod']} |\n")

    print(f"Wrote audit to {AUDIT.relative_to(ROOT)}")
    print(f"Total issues flagged: {len(audit_issues)}")


if __name__ == "__main__":
    main()
