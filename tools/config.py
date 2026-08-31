#!/usr/bin/env python3
"""
config.py — Central configuration for BILLSzuka data, schemas, country mappings,
and automatic macOS AppleDouble (._*) metadata file cleanup.
"""

import os
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
TOOLS_DIR = ROOT_DIR / "tools"
QUARANTINE_DIR = DATA_DIR / "_quarantine"


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
    "kraj",
    "id",
    "nazwa_firmy",
    "miasto",
    "adres",
    "www",
    "wolumen",
    "confidence_wolumen",
    "rejestr_id",
    "nip_vat",
    "rok_zalozenia",
    "tier",
    "marki_nabijarki",
    "marka_wlasna_oem",
    "powinowactwo_nabijarki",
    "kategoria",
    "rynek_skala",
    "cross_sell_potential",
    "kanal_sprzedaży",
    "kanal_zamiennik",
    "decydent",
    "stanowisko",
    "email_decydent",
    "email",
    "telefon",
    "notatki",
    "linkedin",
    "facebook",
    "instagram",
    "tiktok",
    "data_weryfikacji",
    "sourcing",
    "zrodlo_danych",
    "flagi",
    "related_to",
]

# Columns hidden by default in the frontend viewer because they are sparsely
# populated (<10% fill rate in master.csv as of 2026-08-23). Data is kept on
# disk; only the column visibility is suppressed so the UI defaults to a
# clean 28-column view. Users can re-enable any column via the Column toggle.
# Audit 2026-08-23 fill rates: tiktok 0.2%, kanal_zamiennik 1.9%, linkedin 2.2%,
# related_to 3.4%, instagram 3.8%, marka_wlasna_oem 5.8%, facebook 9.4%.
HIDDEN_COLUMNS = ["related_to", "kanal_zamiennik"]

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
    "RS": "Serbia",   # OUT-OF-SCOPE — tracked for competitive intelligence only
}

# Reverse mapping: Directory Name -> Country Code
DIR_TO_ISO = {v: k for k, v in COUNTRY_MAP.items()}

# Canonical country order for compilation/reporting.
COUNTRY_ORDER = ["PL", "CZ", "SK", "RO", "LT", "LV", "EE", "FR", "MD", "BG", "SI", "HR", "RS"]

# Market-scale formula (methodology.md §5): auto-filled from country code.
# duży = PL/CZ/FR, średni = RO/BG/HR/SI/SK (+RS out-of-scope intel), mały = LT/LV/EE/MD.
RYNEK_SKALA_MAP = {
    "PL": "duży", "CZ": "duży", "FR": "duży",
    "RO": "średni", "BG": "średni", "HR": "średni", "SI": "średni", "SK": "średni", "RS": "średni",
    "LT": "mały", "LV": "mały", "EE": "mały", "MD": "mały",
}


def rynek_skala_for(iso: str) -> str:
    """Market size band (duży/średni/mały) for a country code."""
    return RYNEK_SKALA_MAP.get(iso.upper(), "średni")


# FAQ fuzzy-matching threshold (tools/faq.py:FAQ_FUZZY_THRESHOLD — keep in
# sync). Measured by tests/test_faq.py::test_eval_gate: with the inflected-
# form entity guard, 0.6 yields 0 false accepts and <50% misses. Near-misses
# like "ile hurtownikow jest w pl" are caught by the guard (hurtownikow →
# hurtownik), never by the raw Jaccard score alone.


def make_id(iso: str, catalog_type: str, seq_num: int) -> str:
    """Generate region-free unique ID: e.g. PL-A-001, CZ-B-015."""
    cat = catalog_type.upper().strip()
    return f"{iso.upper()}-{cat}-{seq_num:03d}"


# Verified company identifiers allowlist (e.g. AGROTAB PL7931626076)
# Stored normalized (without spaces, dashes, or punctuation)
VERIFIED_ALLOWLIST = {
    "PL7931626076",
    "7931626076",
}


def is_verified_allowlisted(identifier: str) -> bool:
    """
    Check if a tax/registry identifier is in the verified allowlist.
    Normalizes whitespace, hyphens, and dots before checking.
    """
    if not identifier:
        return False
    norm = re.sub(r"[\s\-\.]+", "", str(identifier)).upper()
    return norm in VERIFIED_ALLOWLIST


# === Kimi K3 ===
KIMI_API_KEY  = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = "https://api.moonshot.ai/v1"
KIMI_MODEL    = "kimi-k3"
KIMI_MAX_TOKENS = 8192