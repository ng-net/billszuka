#!/usr/bin/env python3
"""
config.py — Central configuration for BILLSzuka data, schemas, country mappings,
and automatic macOS AppleDouble (._*) metadata file cleanup.
"""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
TOOLS_DIR = ROOT_DIR / "tools"


def clean_apple_double(target_dir: Path = ROOT_DIR) -> int:
    """
    Remove macOS AppleDouble metadata files (._*) and .DS_Store generated on ex-FAT volumes.
    Returns the number of deleted files.
    """
    deleted_count = 0
    for root, dirs, files in os.walk(target_dir):
        # Skip git internal directory
        if ".git" in dirs:
            dirs.remove(".git")
        for f in files:
            if f.startswith("._") or f == ".DS_Store":
                fpath = Path(root) / f
                try:
                    fpath.unlink(missing_ok=True)
                    deleted_count += 1
                except Exception:
                    pass
    return deleted_count


# Auto-clean AppleDouble files on module import whenever any tool runs
_cleaned = clean_apple_double(ROOT_DIR)


# Canonical 35-column schema (Region fields completely removed)
CANONICAL_SCHEMA = [
    "related_to",
    "rok_zalozenia",
    "id_unikalne",
    "kategoria",
    "nazwa_firmy",
    "kraj",
    "miasto",
    "adres",
    "nip_vat",
    "rejestr_id",
    "www",
    "kanal_zamiennik",
    "email",
    "telefon",
    "linkedin",
    "facebook",
    "instagram",
    "tiktok",
    "tier",
    "marki_nabijarki",
    "marka_wlasna_oem",
    "sourcing",
    "wolumen",
    "confidence_wolumen",
    "kanal_sprzedaży",
    "powinowactwo_nabijarki",
    "cross_sell_potential",
    "decydent",
    "stanowisko",
    "email_decydent",
    "zrodlo_danych",
    "data_weryfikacji",
    "flagi",
    "notatki",
    "rynek_skala",
]

# Country Code -> Directory Name mapping
COUNTRY_MAP = {
    "PL": "Polska",
    "CZ": "Czechy",
    "SK": "Słowacja",
    "RO": "Rumunia",
    "LT": "Litwa",
    "LV": "Łotwa",
    "EE": "Estonia",
    "FR": "Francja",
    "MD": "Mołdawia",
    "BG": "Bułgaria",
    "SI": "Słowenia",
    "HR": "Chorwacja",
}

# Reverse mapping: Directory Name -> Country Code
DIR_TO_ISO = {v: k for k, v in COUNTRY_MAP.items()}

# Canonical country order for compilation/reporting
COUNTRY_ORDER = ["PL", "CZ", "SK", "RO", "LT", "LV", "EE", "FR", "MD", "BG", "SI", "HR"]


def make_id(iso: str, catalog_type: str, seq_num: int) -> str:
    """Generate region-free unique ID: e.g. PL-A-001, CZ-B-015."""
    cat = catalog_type.upper().strip()
    return f"{iso.upper()}-{cat}-{seq_num:03d}"
