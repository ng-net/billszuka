#!/usr/bin/env python3
# Source: Google Maps Platform Code Assist
"""
gmaps_search.py — Lead discovery using Google Maps Places API (New) Text Search.

Finds wholesalers/distributors and outputs to CSV or appends to B-catalog.
Uses the modern POST v1/places:searchText endpoint with explicit field masks.

Usage:
  python3 tools/gmaps_search.py --query "hurtownia tytoniowa Warszawa" --country PL
  python3 tools/gmaps_search.py --query "velkoobchod tabák Praha" --country CZ --write
  python3 tools/gmaps_search.py --query "tabak predaj Bratislava" --country SK --dry-run
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR, make_id
from orchestrate_11_levels import add_lead

ENV_FILE = ROOT / ".env"
PLACES_API_URL = "https://places.googleapis.com/v1/places:searchText"

# ---------------------------------------------------------------------------
# Mock Data for Dry-run and No-Key fallback
# ---------------------------------------------------------------------------
MOCK_PLACES = [
    {
        "id": "ChIJu3c2M8NDFkcR_x4aZ_U2nBg",
        "displayName": {"text": "Hurtownia Akcesoriów Tytoniowych MOCK-1"},
        "formattedAddress": "Aleje Jerozolimskie 100, 00-001 Warszawa, Polska",
        "websiteUri": "http://mock-tobacco-wholesale-warsaw.pl",
        "nationalPhoneNumber": "22 123 45 67",
        "addressComponents": [
            {"longText": "Warszawa", "types": ["locality"]}
        ],
        "types": ["tobacco_shop", "wholesaler", "establishment"]
    },
    {
        "id": "ChIJc-2Z8NDFkcR_x4aZ_U2nBg1",
        "displayName": {"text": "Tabak-Hurt Sp. z o.o. (MOCK)"},
        "formattedAddress": "Piotrkowska 50, 90-004 Łódź, Polska",
        "websiteUri": "http://tabakhurt-mock.pl",
        "nationalPhoneNumber": "42 987 65 43",
        "addressComponents": [
            {"longText": "Łódź", "types": ["locality"]}
        ],
        "types": ["wholesaler", "store", "establishment"]
    }
]


def load_env_api_key() -> str:
    """Read GOOGLE_MAPS_API_KEY from .env file."""
    if not ENV_FILE.exists():
        return ""
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == "GOOGLE_MAPS_API_KEY":
            return v.strip().strip('"').strip("'")
    return ""


def extract_city(address_components: list) -> str:
    """Extract locality (city) name from address components."""
    if not address_components:
        return ""
    for comp in address_components:
        types = comp.get("types", [])
        if "locality" in types:
            return comp.get("longText", "")
    return ""


def search_gmaps_places(query: str, api_key: str, timeout: int = 15) -> list[dict]:
    """Execute modern Places API Text Search POST request."""
    # Field mask determines pricing SKU and fields returned.
    # We choose basic details and contact fields to remain cost-efficient.
    field_mask = (
        "places.id,"
        "places.displayName,"
        "places.formattedAddress,"
        "places.websiteUri,"
        "places.nationalPhoneNumber,"
        "places.addressComponents,"
        "places.types"
    )

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask,
    }

    payload = {
        "textQuery": query
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(PLACES_API_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            return resp_data.get("places", [])
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:1000]
        print(f"❌ Places API HTTP Error {e.code}: {body}")
        return []
    except Exception as e:
        print(f"❌ Places API Connection Error: {e}")
        return []


def print_cost_notice():
    """Print standard Google Maps cost warning."""
    print("=" * 80)
    print("⚠️  COST NOTICE & ATTRIBUTION:")
    print("   Usage of Google Maps Platform products and services may incur costs")
    print("   against your Google Cloud project billing account.")
    print("   API used: Places API (New) - Text Search SKU.")
    print("   Source: Google Maps Platform Code Assist")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Google Maps Places API Lead Search")
    parser.add_argument("--query", required=True, help="Search query (e.g. 'hurtownia tytoniowa')")
    parser.add_argument("--country", default="PL", help="2-letter country code (default: PL)")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run with mock data")
    parser.add_argument("--write", action="store_true", help="Append results to target country catalog (A or B)")
    parser.add_argument("--catalog", default="B", choices=["A", "B"],
                        help="Target catalog: A (high-quality distributor) or B (general lead). Default: B")
    args = parser.parse_args()

    country = args.country.upper()
    if country not in COUNTRY_MAP:
        print(f"❌ Unknown country code: {country}")
        sys.exit(1)

    print_cost_notice()

    api_key = load_env_api_key()
    is_dry = args.dry_run

    if not api_key:
        print("\n⚠️  WARNING: GOOGLE_MAPS_API_KEY not found in .env")
        print("   To obtain a free Maps Demo Key for prototyping, visit:")
        print("   https://mapsplatform.google.com/maps-demo-key?utm_campaign=gmp_git_agentskills_v1")
        print("   For this execution, we will fall back to DRY-RUN mode using mock data.\n")
        is_dry = True

    if is_dry:
        print(f"🚀 [DRY-RUN] Running mock search for query: '{args.query}'")
        places = MOCK_PLACES
    else:
        print(f"🚀 [LIVE] Querying Places API (New) for: '{args.query}'")
        places = search_gmaps_places(args.query, api_key)

    if not places:
        print("ℹ️  No places returned.")
        return

    print(f"🔎 Found {len(places)} potential leads:")
    
    catalog = args.catalog.upper()

    # Save results to intake folder first as a backup
    intake_dir = DATA_DIR / "_intake" / "gmaps"
    intake_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_file = intake_dir / f"gmaps_search_{country}_cat{catalog}_{timestamp}.csv"

    # Define simple raw columns for review
    raw_schema = ["id", "nazwa", "adres", "miasto", "www", "telefon", "kraj", "types"]
    
    written_count = 0
    with open(out_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=raw_schema)
        writer.writeheader()

        for place in places:
            name = place.get("displayName", {}).get("text", "")
            address = place.get("formattedAddress", "")
            city = extract_city(place.get("addressComponents", []))
            www = place.get("websiteUri", "")
            phone = place.get("nationalPhoneNumber", "")
            place_id = place.get("id", "")
            types = ", ".join(place.get("types", []))

            # print summary
            print(f"  • {name} | {city} | Tel: {phone or 'N/A'} | Web: {www or 'N/A'}")

            writer.writerow({
                "id": place_id,
                "nazwa": name,
                "adres": address,
                "miasto": city,
                "www": www,
                "telefon": phone,
                "kraj": country,
                "types": types
            })

            # If write requested, append to target catalog (A or B)
            if args.write:
                if is_dry:
                    # For dry-run write, we don't save to file, just skip
                    pass
                else:
                    cat_label = catalog  # "A" or "B"
                    category_code = f"{cat_label}1" if cat_label == "A" else "B9"
                    added = add_lead(
                        country=country,
                        name=name,
                        category=category_code,
                        nip_clean="",
                        rejestr_id=place_id,
                        source=f"Google Maps Search [{cat_label}]: {args.query} (ID: {place_id})",
                        catalog=cat_label,
                    )
                    if added:
                        written_count += 1

    print(f"\n📂 Saved raw results to: {out_file.relative_to(ROOT)}")
    if args.write:
        if is_dry:
            print("ℹ️  [DRY-RUN] Skipped adding to catalog CSV.")
        else:
            print(f"➕ Appended {written_count} new leads to {country} catalog-{catalog} CSV.")


if __name__ == "__main__":
    main()
