#!/usr/bin/env python3
"""
map_intake.py — Map Marcel's 35-col intake CSVs → BILLSzuka 37-col master.

Input:  data/_intake/{ISO}/07-MASTER-Katalog-Wszystkich-Leadow-B2B-{ISO}.csv
Output: data/_intake/{ISO}/normalized.csv (37 cols, BILLSzuka master schema)

Mapping (35 → 37):
  Marcel col             BILLSzuka col           Transform
  ─────────────────────  ──────────────────────  ─────────────────────────
  Firma                  nazwa_firmy             1:1
  Region                 region_kod+region_nazwa split on first word
  Miasto                 miasto                  1:1
  Adres                  adres                   1:1
  Numer Rejestrowy       rejestr_id              extract clean ID + prefix label
  NIP / VAT              nip_vat                 extract bare digits (DIČ/KMKR/PVM)
  WWW                    www                     1:1
  Email                  email                   first valid recipient
  Telefon                telefon                 first valid phone
  Decydent               decydent                1:1
  Stanowisko             stanowisko              1:1
  Relacja                tier                    map to BILLSzuka tier enum
  Segment                kategoria               map to A1-A6 / B1-B9
  Produkty i Marki       marki_nabijarki         1:1 (B catalog: → notatki)
  Oferta Powermatic      notatki                 always to notatki
  Kanał Sprzedaży        kanal_sprzedaży         1:1
  Kanał Importu          sourcing                1:1 (B catalog: → notatki)
  Skala                  rynek_skala             1:1
  Zasięg                 kanal_zamiennik         mapped to existing channel enum
  Status                 flagi                   → "status: {value}"
  Priorytet              flagi                   → "priorytet: {value}"
  Uzasadnienie Potencjału  notatki               truncate to 500 chars
  Uwagi                  notatki                 consolidate
  Następny Krok          notatki                 consolidate
  Źródła                 zrodlo_danych           1:1
  (rest)                 notatki                 consolidate as "extras"

Generated columns:
  id_unikalne  — from {ISO}-B-{REGION}-{NNN}
  kraj         — ISO code
  region_typ   — "kraj" (always for country level)
  related_to   — blank
  rok_zalozenia — blank
  linkedin / facebook / instagram / tiktok — blank
  marka_wlasna_oem — blank (A only)
  powinowactwo_nabijarki / cross_sell_potential — blank (B only)
  wolumen / confidence_wolumen — "do ustalenia"
  email_decydent — blank
  data_weryfikacji — today
  flagi — from Priorytet + Status + verdict

Usage:
  python3 tools/map_intake.py --iso CZ
  python3 tools/map_intake.py --all
  python3 tools/map_intake.py --iso EE --skip-hallucinations
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
INTAKE = ROOT / "data" / "_intake"

from config import CANONICAL_SCHEMA as MASTER_COLS, COUNTRY_MAP as CONF_COUNTRY_MAP, make_id

# Country → (intake subdir, catalog dir, ISO code)
COUNTRY_MAP = {
    iso: (iso, country_name, iso)
    for iso, country_name in CONF_COUNTRY_MAP.items()
}

# BILLSzuka tier enum (from methodology)
TIER_ENUM = {
    "Importer": "wyłączność",
    "Wyłączny Importer": "wyłączność",
    "Importer Ogólnokrajowy & Sieć B2B": "wyłączność",
    "Hurtownia": "hurtownik",
    "Hurtownia Tytoniowa": "hurtownik",
    "Hurtownia FMCG & Trafika": "hurtownik",
    "Hurtownia FMCG": "hurtownik",
    "Hurtownia Regionalna": "hurtownik",
    "Hurtownia Tytoniowa & Akcesoriów RYO": "hurtownik",
    "Hurtownia Tytoniowa Regionalna": "hurtownik",
    "Hurtownia Tytoniowa & RYO": "hurtownik",
    "Hurtownik Trafik Regionalny": "hurtownik",
    "Dystrybutor": "hurtownik",
    "Dystrybutor FMCG": "hurtownik",
    "Dystrybutor E-cigaret / Vape": "hurtownik",
    "Dystrybutor Tytoniowy & FMCG": "hurtownik",
    "Dystrybutor Powermatic & E-Commerce": "hurtownik",
    "Sieć Supermarketów": "marketplace",
    "Sieć Hipermarketów": "marketplace",
    "Sieć Čerpací Stanice (Stacje)": "marketplace",
    "Sieć Trafika": "marketplace",
    "Platforma Marketplace E-Commerce": "marketplace",
    "Sklep": "detalista",
    "Sklep E-Commerce RYO & Vape": "detalista",
    "Sklep E-Commerce Maszynek": "detalista",
    "Specjalistyczna Hurtownia Tytoniowa": "hurtownik",
    "Specjalistyczny Sklep RYO Online": "detalista",
    "Specjalistyczny Sklep Tytoniowy Premium": "detalista",
    "Specjalista na elektrické plničky": "detalista",
    "Importer maszyn RYO": "wyłączność",
    "Velkoobchod s tabákem": "hurtownik",
    "Velkoobchod s tabákem a příslušenstvím": "hurtownik",
    "Velkoobchod s tabákem a plničkami": "hurtownik",
    "Lider E-Commerce B2B ČR": "marketplace",
    "Główny Dystrybutor Tytoniu & Akcesoriów": "hurtownik",
    "Distributor tabákových strojů": "hurtownik",
    "Dodavatel strojů pro RYO": "hurtownik",
    "E-commerce & Distribuce RYO": "detalista",
    "E-Commerce & Wholesale B2B": "marketplace",
}

# BILLSzuka kategoria (A1-A6 / B1-B9) — derived from Segment
KATEGORIA_MAP = {
    # B catalog (B1-B9 = industry without machines)
    "S2 — Hurtownia Tytoniowa / FMCG": "B8",  # Wholesale FMCG
    "S1 — Nabijarki RYO/MYO & Gilze": "B1",  # RYO machines & papers
    "S3 — Dystrybuacja E-papierosów / Vape": "B3",  # E-cig distribution
    "S3 — E-papierosy & Liquidy / Vape": "B3",
    "S4 — Ogólny Hurt FMCG & Convenience": "B9",  # General wholesale
}

# Load the validated.csv (has _verdict column) — fall back to raw intake CSV
def load_validated(intake_dir: Path, iso: str) -> tuple[list[dict], bool]:
    """Returns (rows, has_verdict) — has_verdict=True if _verdict column present."""
    val_csv = intake_dir / "validated.csv"
    if val_csv.exists():
        rows = list(csv.DictReader(val_csv.open(encoding="utf-8")))
        return rows, "_verdict" in (rows[0] if rows else {})
    raw_csv = intake_dir / f"07-MASTER-Katalog-Wszystkich-Leadow-B2B-{iso}.csv"
    if not raw_csv.exists():
        return [], False
    return list(csv.DictReader(raw_csv.open(encoding="utf-8"))), False


def normalize_email(email: str) -> str:
    """Take first valid recipient from multi-recipient string."""
    e = (email or "").strip()
    for r in re.split(r"[;,]", e):
        r = r.strip()
        if r and re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", r):
            return r
    return ""


def normalize_phone(phone: str) -> str:
    """Take first phone from multi-phone string. Just split on ; | and take first non-empty."""
    p = (phone or "").strip()
    if not p:
        return ""
    # If has separator, take first chunk (assume caller joined multiple phones)
    for sep in (";", "|"):
        if sep in p:
            first = p.split(sep, 1)[0].strip()
            if first:
                return first
    return p


def normalize_rejestr(rejestr: str, iso: str) -> str:
    """Clean rejestr_id to BILLSzuka format: 'ARES IČO NNNNNNNN' / 'e-Äriregister NNNNNNNN' / 'JAR NNNNNNNNN'."""
    from validate_intake import (
        extract_ico, extract_registrikood, extract_kodas,
    )
    r = (rejestr or "").strip()
    if iso == "CZ":
        ico = extract_ico(r)
        if ico:
            return f"ARES IČO {ico}"
    elif iso == "EE":
        reg = extract_registrikood(r)
        if reg:
            return f"e-Äriregister {reg}"
    elif iso == "LT":
        kod = extract_kodas(r)
        if kod:
            return f"JAR {kod}"
    return ""


def normalize_nip(nip: str) -> str:
    """Extract bare digits from VAT/DIČ/KMKR/PVM."""
    from validate_intake import extract_vat
    return extract_vat(nip) or ""


def consolidate_notatki(parts: list[str], max_len: int = 500) -> str:
    """Join non-empty parts with ' | ' separator, truncate."""
    text = " | ".join(p for p in parts if p and p.strip())
    if len(text) > max_len:
        text = text[:max_len - 3] + "..."
    return text


def map_row(marcel_row: dict, iso: str, seq_num: int = 1, skip_hallucinations: bool = False) -> dict | None:
    """Map one Marcel row to 35-col BILLSzuka row. Returns None if skipped."""
    # Skip hallucinations / dup if requested
    if skip_hallucinations:
        verdict = (marcel_row.get("_verdict") or "").strip()
        if "HALUCYNACJA" in verdict or "DUPLIKAT" in verdict:
            return None

    out = {col: "" for col in MASTER_COLS}

    # Direct 1:1 mappings
    out["nazwa_firmy"] = (marcel_row.get("Firma") or "").strip()
    out["miasto"] = (marcel_row.get("Miasto") or "").strip()
    out["adres"] = (marcel_row.get("Adres") or "").strip()
    out["email"] = normalize_email(marcel_row.get("Email") or "")
    out["telefon"] = normalize_phone(marcel_row.get("Telefon") or "")
    out["decydent"] = (marcel_row.get("Decydent") or "").strip()
    out["stanowisko"] = (marcel_row.get("Stanowisko") or "").strip()
    out["www"] = (marcel_row.get("WWW") or "").strip()
    out["kanal_sprzedaży"] = (marcel_row.get("Kanał Sprzedaży") or "").strip()
    out["marki_nabijarki"] = (marcel_row.get("Produkty i Marki") or "").strip()
    out["zrodlo_danych"] = (marcel_row.get("Źródła") or "").strip()
    out["kraj"] = iso
    out["sourcing"] = (marcel_row.get("Kanał Importu") or "").strip()
    out["rynek_skala"] = (marcel_row.get("Skala") or "").strip()

    # Rejestr + NIP normalization
    out["rejestr_id"] = normalize_rejestr(marcel_row.get("Numer Rejestrowy") or "", iso)
    out["nip_vat"] = normalize_nip(marcel_row.get("NIP / VAT") or "")

    # ID
    out["id_unikalne"] = make_id(iso, "B", seq_num)

    # Tier from Relacja (exact match, then substring match for compound labels)
    relacja = (marcel_row.get("Relacja") or "").strip()
    tier = TIER_ENUM.get(relacja, "")
    if not tier:
        # Substring fallback — match the most specific key in TIER_ENUM
        # against the relacja string
        relacja_lower = relacja.lower()
        for key, val in sorted(TIER_ENUM.items(), key=lambda x: -len(x[0])):
            if key.lower() in relacja_lower:
                tier = val
                break
    out["tier"] = tier or "do ustalenia"

    # Kategoria from Segment
    segment = (marcel_row.get("Segment") or "").strip()
    out["kategoria"] = KATEGORIA_MAP.get(segment, "B9")  # B9 fallback = industry generic

    # Flagi from Priorytet + Status + verdict
    priorytet = (marcel_row.get("Priorytet") or "").strip()
    status = (marcel_row.get("Status") or "").strip()
    verdict = (marcel_row.get("_verdict") or "").strip()
    flagi_parts = []
    if priorytet:
        flagi_parts.append(f"priorytet: {priorytet}")
    if status:
        flagi_parts.append(f"status: {status}")
    if verdict:
        flagi_parts.append(f"intake: {verdict}")
    out["flagi"] = " | ".join(flagi_parts)

    # Notatki — consolidate extras
    notatki_parts = []
    if marcel_row.get("Uzasadnienie Potencjału"):
        uzas = marcel_row["Uzasadnienie Potencjału"]
        if len(uzas) > 400:
            uzas = uzas[:397] + "..."
        notatki_parts.append(f"Uzasadnienie: {uzas}")
    if marcel_row.get("Uwagi"):
        notatki_parts.append(f"Uwagi: {marcel_row['Uwagi']}")
    if marcel_row.get("Następny Krok"):
        notatki_parts.append(f"Następny krok: {marcel_row['Następny Krok']}")
    if marcel_row.get("Oferta Powermatic"):
        notatki_parts.append(f"Oferta Powermatic: {marcel_row['Oferta Powermatic']}")
    if marcel_row.get("Ruch WWW"):
        notatki_parts.append(f"Ruch WWW: {marcel_row['Ruch WWW']}")
    if marcel_row.get("Targi / Expo"):
        notatki_parts.append(f"Targi: {marcel_row['Targi / Expo']}")
    if marcel_row.get("Sprzedawca Marketplace"):
        notatki_parts.append(f"Marketplace: {marcel_row['Sprzedawca Marketplace']}")
    if marcel_row.get("Status EORI"):
        notatki_parts.append(f"EORI: {marcel_row['Status EORI']}")
    if marcel_row.get("Technologia WWW"):
        notatki_parts.append(f"Tech: {marcel_row['Technologia WWW']}")
    if marcel_row.get("Weryfikacja Domeny"):
        notatki_parts.append(f"Domena: {marcel_row['Weryfikacja Domeny']}")
    if marcel_row.get("Platforma E-Commerce"):
        notatki_parts.append(f"Platforma: {marcel_row['Platforma E-Commerce']}")
    if marcel_row.get("Strefa Sprzedaży"):
        notatki_parts.append(f"Strefa: {marcel_row['Strefa Sprzedaży']}")
    if marcel_row.get("Zasięg"):
        notatki_parts.append(f"Zasięg: {marcel_row['Zasięg']}")
    if marcel_row.get("Ocena Sklepu"):
        notatki_parts.append(f"Ocena: {marcel_row['Ocena Sklepu']}")
    if marcel_row.get("Score"):
        notatki_parts.append(f"Score Marcela: {marcel_row['Score']}")
    out["notatki"] = consolidate_notatki(notatki_parts, max_len=600)

    # Date
    out["data_weryfikacji"] = date.today().isoformat()

    # Wolumen placeholder
    out["wolumen"] = "do ustalenia"
    out["confidence_wolumen"] = "0.0"

    return out


def map_country(iso: str, skip_hallucinations: bool = False) -> dict:
    """Map all intake rows for one country. Returns stats."""
    sub, dirname, code, _ = COUNTRY_MAP[iso]
    intake_dir = INTAKE / sub
    if not intake_dir.exists():
        return {"error": f"intake dir not found: {intake_dir}"}

    rows, has_verdict = load_validated(intake_dir, iso)
    if not rows:
        return {"error": "no rows"}

    mapped = []
    skipped = []
    for r in rows:
        out = map_row(r, iso, skip_hallucinations=skip_hallucinations)
        if out is None:
            skipped.append(r.get("Firma", "?"))
        else:
            mapped.append(out)

    out_path = intake_dir / "normalized.csv"
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MASTER_COLS)
        w.writeheader()
        w.writerows(mapped)

    return {
        "iso": iso,
        "input": len(rows),
        "mapped": len(mapped),
        "skipped": len(skipped),
        "out": str(out_path),
        "skipped_firms": skipped,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", help="Country code (e.g. CZ)")
    ap.add_argument("--all", action="store_true", help="All countries in intake")
    ap.add_argument("--skip-hallucinations", action="store_true",
                    help="Skip HALUCYNACJA + DUPLIKAT verdicts")
    args = ap.parse_args()

    if not args.iso and not args.all:
        print("Specify --iso CZ or --all")
        return 1

    targets = []
    if args.all:
        for sub in INTAKE.iterdir():
            if not sub.is_dir():
                continue
            for f in sub.glob("07-MASTER-Katalog-Wszystkich-Leadow-B2B-*.csv"):
                m = re.search(r"-([A-Z]{2})\.csv$", f.name)
                if m:
                    targets.append(m.group(1))
    else:
        targets = [args.iso]

    total_in = 0
    total_out = 0
    for iso in targets:
        if iso not in COUNTRY_MAP:
            print(f"⚠️ Unknown ISO: {iso} — skipping")
            continue
        result = map_country(iso, skip_hallucinations=args.skip_hallucinations)
        if "error" in result:
            print(f"❌ {iso}: {result['error']}")
            continue
        total_in += result["input"]
        total_out += result["mapped"]
        skip_info = f" (skipped {result['skipped']} halucynacje/dup)" if result["skipped"] else ""
        print(
            f"✅ {iso}: {result['input']} → {result['mapped']} mapped{skip_info} → {result['out']}"
        )
        if result["skipped"]:
            for f in result["skipped_firms"]:
                print(f"    ⏭️  {f}")

    print()
    print(f"=== RAZEM: {total_in} input → {total_out} mapped ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
