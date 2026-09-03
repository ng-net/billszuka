#!/usr/bin/env python3
"""
orchestrate_11_levels.py — Interactive reference playbook & lead intake CLI for BILLSzuka.

NOTE: This script serves as the living research playbook, query library, registry guide,
and manual lead intake CLI. It does not automatically execute web searches or crawler requests.
For executing verification gates or automated checks, see tools/test_11_levels.py and tools/verify_run.py.

Levels (L0-L11 per methodology.md):
  L0: Pre-flight validation (NIP checksum + Registry name match)
  L1: Web Search (B2B phrases + operators)
  L2: Marketplaces & Aggregators (Allegro, Ceneo, OLX, Heureka, Bazos, etc.)
  L3: State Registries (CEIDG/KRS, ARES, ORSR, ListaFirme, Rekvizitai, e-Äriregister, Pappers, etc.)
  L4: Customs & Regulatory (CN 8479 89 97 90, Excise, White List VAT, BDO)
  L5: DNS WHOIS & Certificate Transparency (crt.sh)
  L6: Trade Fairs (InterTabac, World Vape Show, Eurocis, Vapexpo)
  L7: Social OSINT (FB groups, YouTube review comments, Reddit, TikTok)
  L8: B2B Catalogs (Aleo, PKT, Panorama Firm, Firmy.cz, Kompass, Europages, ENTIA)
  L9: LLM Scouting (OpenRouter multi-model extraction guarded by L0)
  L10: EUIPO Trademark Search (euipo.europa.eu/eSearch)
  L11: Public Procurement (BZP PL / TED EU)

Usage:
  python3 tools/orchestrate_11_levels.py --list
  python3 tools/orchestrate_11_levels.py --country PL [--level L1]
"""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, make_id, rynek_skala_for

PLANS_PATH = ROOT / "tools" / "country_plans.json"
REQUIRED_PLAN_KEYS = [
    "name", "csv_A", "csv_B", "L0_preflight", "L1_web_search", "L2_marketplace",
    "L3_registries", "L4_customs_regulatory", "L5_dns_whois", "L6_trade_fairs",
    "L7_social_osint", "L8_B2B_catalogs", "L9_LLM_extraction", "L10_trademark", "L11_procurement"
]


def validate_country_plans(plans: dict) -> bool:
    """Validate that all country plans contain required metadata and level keys."""
    for iso, plan in plans.items():
        for key in REQUIRED_PLAN_KEYS:
            if key not in plan:
                raise ValueError(f"Country plan for {iso} is missing required key '{key}'")
    return True


def load_country_plans(path: Path = PLANS_PATH) -> dict:
    """Load and validate 11-level country search plans from JSON configuration."""
    if not path.exists():
        raise FileNotFoundError(f"Country plans configuration not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        plans = json.load(f)
    validate_country_plans(plans)
    return plans


# Export for direct imports / backward compatibility
COUNTRY_PLANS = load_country_plans()


def _csv_label(plan: dict) -> str:
    """Formatted label of available CSV catalog paths for a country plan."""
    csv_b = plan.get("csv_B")
    csv_a = plan.get("csv_A")
    paths = [p for p in [csv_b, csv_a] if p]
    return ", ".join(paths) if paths else "—"


def add_lead(country: str, name: str, category: str, nip_clean: str, rejestr_id: str, source: str, catalog: str = "B") -> bool:
    """Manually append a verified lead to data/{Kraj}/catalog-{A|B}-{ISO}.csv."""
    country = country.upper()
    catalog = catalog.upper()
    plan = COUNTRY_PLANS.get(country)
    if not plan:
        print(f"❌ Unknown country: {country}")
        return False

    csv_key = f"csv_{catalog}"
    csv_rel = plan.get(csv_key)
    if not csv_rel:
        print(f"❌ No CSV path for catalog-{catalog} in country plan: {country}")
        return False

    csv_path = ROOT / csv_rel
    if not csv_path.exists():
        print(f"❌ CSV path not found: {csv_path}")
        return False

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not fieldnames or fieldnames != CANONICAL_SCHEMA:
        fieldnames = CANONICAL_SCHEMA

    # Deduplicate only on non-empty tax numbers to prevent blocking leads without NIP
    nip_norm = nip_clean.replace(" ", "").upper() if nip_clean else ""
    existing_nips = {
        r.get("nip_vat", "").replace(" ", "").upper()
        for r in rows
        if r.get("nip_vat", "").strip()
    }
    if nip_norm and nip_norm in existing_nips:
        print(f"   ℹ️  Skip duplicate NIP {nip_norm} ({name})")
        return False

    counter = len(rows) + 1
    row = {k: "" for k in fieldnames}
    row["id"] = make_id(country, catalog, counter)
    row["kategoria"] = category
    row["nazwa"] = name
    row["kraj"] = country
    row["nip_vat"] = nip_norm
    row["rejestr_id"] = rejestr_id if rejestr_id else "brak"
    row["tier"] = "hurtownik"
    row["zrodlo_danych"] = source
    row["data_weryfikacji"] = time.strftime("%Y-%m-%d")
    row["flagi"] = f"{time.strftime('%Y-%m-%d')} ⚠️ DO-WERYFIKACJI"
    row["rynek_skala"] = rynek_skala_for(country)

    rows.append(row)
    tmp_path = csv_path.with_suffix(".csv.tmp")
    with open(tmp_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    tmp_path.replace(csv_path)
    print(f"   ➕ Added lead: {name} ({country}, NIP: {nip_norm}, {rejestr_id})")
    return True


def list_countries():
    """List 11-level search summary for all configured countries."""
    print("=" * 80)
    print("  BILLSzuka 11-level Search Playbook — 13 tracked countries (12 EU + RS)")
    print("  (Reference query bank and intake tool — not an automated scraper)")
    print("=" * 80)
    for code, plan in COUNTRY_PLANS.items():
        n_levels = sum(1 for k in plan if k.startswith("L") and "_" in k)
        n_mkt = len(plan.get("L2_marketplace", []))
        print(f"  {code:2s} | {plan['name']:14s} | {n_levels:2d} Search Levels | {n_mkt} Marketplaces | CSV: {_csv_label(plan)}")


def show_country(country: str, target_level: str = None):
    """Show detailed search queries, registries, and configuration for a country."""
    plan = COUNTRY_PLANS.get(country.upper())
    if not plan:
        print(f"❌ Unknown country: {country}")
        return

    print("=" * 80)
    print(f"  Search Playbook: {country.upper()} — {plan['name']}  (CSV: {_csv_label(plan)})")
    print("=" * 80)

    for key, val in plan.items():
        if key in ("name", "csv_A", "csv_B"):
            continue
        if target_level:
            lvl_clean = target_level.strip().lower()
            key_clean = key.lower()
            # Match exact key, level prefix (e.g. "l1" -> "l1_..."), or startswith
            matches_level = (
                key_clean == lvl_clean
                or key_clean.startswith(f"{lvl_clean}_")
                or key_clean.split("_")[0] == lvl_clean
                or (not lvl_clean.startswith("l") and key_clean.startswith(lvl_clean))
            )
            if not matches_level:
                continue

        print(f"\n📌 [{key}]:")
        if isinstance(val, list):
            for item in val:
                print(f"   • {item}")
        elif isinstance(val, dict):
            for k, v in val.items():
                print(f"   • {k}: {v}")
        else:
            print(f"   • {val}")


def main():
    ap = argparse.ArgumentParser(
        description="BILLSzuka 11-level search strategy reference playbook and lead intake tool"
    )
    ap.add_argument("--list", action="store_true", help="List search summary for all 13 countries")
    ap.add_argument("--country", help="Show search options for a country (e.g. PL, CZ, SK)")
    ap.add_argument("--level", help="Filter specific search level (e.g. L1, L2, L3)")
    args = ap.parse_args()

    if args.list:
        list_countries()
    elif args.country:
        show_country(args.country, target_level=args.level)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
