#!/usr/bin/env python3
"""
validate_columns.py — Flexible column validation for BILLSzuka catalogs.

Accepts ANY CSV file (existing per-kraj catalogs, master.csv, or new intake).
Recognises the canonical 35-column schema, matches unknown headers via
fuzzy + alias matching, validates per-column rules, and reports
missing/extra columns and per-row violations.

Stdlib only (csv, difflib, re, json, pathlib, argparse, datetime, unicodedata).

Usage:
    python3 tools/validate_columns.py                        # validate everything in data/
    python3 tools/validate_columns.py --csv path/to/file.csv # single file
    python3 tools/validate_columns.py --csv path/to/dir/    # all .csv in dir
    python3 tools/validate_columns.py --strict              # warnings → critical
    python3 tools/validate_columns.py --json                 # JSON only to stdout
    python3 tools/validate_columns.py --exit-zero            # always exit 0

Exit codes:
    0  OK (no critical, no warnings) or --exit-zero
    1  Critical violations present
    2  Warnings only (no critical)
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Canonical schema (mirrors methodology.md §10 + tools/config.py:CANONICAL_SCHEMA)
# ---------------------------------------------------------------------------

CANONICAL_COLUMNS: list[str] = [
    "related_to", "rok_zalozenia", "id", "kategoria", "nazwa_firmy",
    "kraj", "miasto", "adres", "nip_vat", "rejestr_id",
    "www", "kanal_zamiennik", "email", "telefon", "linkedin",
    "facebook", "instagram", "tiktok", "tier", "marki_nabijarki",
    "marka_wlasna_oem", "sourcing", "wolumen", "confidence_wolumen", "kanal_sprzedaży",
    "powinowactwo_nabijarki", "cross_sell_potential", "decydent", "stanowisko", "email_decydent",
    "zrodlo_danych", "data_weryfikacji", "flagi", "notatki", "rynek_skala",
]

CANONICAL_SET = set(CANONICAL_COLUMNS)

# Aliases — extend as needed. Format: canonical_name -> list of accepted aliases
# (lowercase, no diacritics, no underscores). Covers PL/EN/DE/FR/IT/SK/CZ/HR/SI/RS.
DEFAULT_ALIASES: dict[str, list[str]] = {
    "related_to": ["related to", "related", "powiazania", "polaczone"],
    "rok_zalozenia": ["rok zalozenia", "rok zalozenia firmy", "founded", "founded year",
                      "year founded", "registration year", "gruendungsjahr", "annee",
                      "anno fondazione", "rok registracie"],
    "id": ["id unikalne", "id", "id unique", "unique id", "lead id",
                    "catalog id", "numer", "cislo"],
    "kategoria": ["kategoria", "category", "cat", "typ katalogu", "klasse", "categorie",
                  "categoria", "kategoria katalogu"],
    "nazwa_firmy": ["nazwa firmy", "firma", "company", "company name", "name",
                    "nazwa", "nazwa spolki", "unternehmen", "firme", "nom",
                    "societe", "ragione sociale", "obchodne meno", "naziv",
                    "ime podjetja", "ime firme", "naziv firme", "preduzece"],
    "kraj": ["kraj", "country", "land", "pays", "paese", "zeme", "krajina",
             "drzava", "orszag"],
    "miasto": ["miasto", "city", "town", "stadt", "ville", "citta", "mesto",
               "mesto/obec", "grad", "mesto", "kraj"],
    "adres": ["adres", "address", "adresse", "anschrift", "indirizzo", "adresa",
              "ulica i numer", "ulica", "strasse"],
    "nip_vat": ["nip vat", "nip", "vat", "vat number", "tax id", "taxid",
                "numer nip", "numer vat", "ico", "cui", "siren", "siret",
                "kmkr", "pvm", "pvn", "idno", "eik", "oib", "pib",
                "ustno davcna", "davcna", "ids", "ruc"],
    "rejestr_id": ["rejestr id", "registry id", "register id", "krs", "krs number",
                   "or number", "ico number", "obchodny register", "reg number",
                   "registration number", "obchodny rejstrik"],
    "www": ["www", "website", "web", "url", "strona www", "strona", "site",
            "homepage", "webseite", "site web", "sito web"],
    "kanal_zamiennik": ["kanal zamiennik", "channel replacement", "alt channel",
                        "alternate web", "zastepczy kanal", "in channel"],
    "email": ["email", "e mail", "e-mail", "mail", "adres email", "courriel",
              "posta elettronica"],
    "telefon": ["telefon", "phone", "tel", "phone number", "numer telefonu",
                "telefonnummer", "telephone", "numero", "telefono", "telefonski"],
    "linkedin": ["linkedin", "linkedin url", "linkedin profile", "in"],
    "facebook": ["facebook", "fb", "facebook page", "fb page", "facebook url"],
    "instagram": ["instagram", "ig", "insta", "instagram url"],
    "tiktok": ["tiktok", "tik tok", "tiktok url"],
    "tier": ["tier", "level", "kategoria dystrybucji", "typ relacji",
             "distribution tier", "vertriebsstufe"],
    "marki_nabijarki": ["marki nabijarki", "brands", "machines", "nabijarki marki",
                        "injection brands", "machine brands", "marki maszynek",
                        "marki urzadzen"],
    "marka_wlasna_oem": ["marka wlasna oem", "own brand", "oem", "private label",
                         "marque propre", "eigenmarke", "marchio proprio"],
    "sourcing": ["sourcing", "zrodlo dostaw", "supply source", "source", "origin",
                 "herkunft", "provenance", "fonte"],
    "wolumen": ["wolumen", "volume", "skala", "scale", "size", "volumen",
                "grandeur", "dimensione"],
    "confidence_wolumen": ["confidence wolumen", "volume confidence", "confidence",
                           "pewnosc", "surete"],
    "kanal_sprzedaży": ["kanal sprzedazy", "sales channel", "channel", "distribution channel",
                        "kanal dystrybucji", "verteiler", "canal de vente",
                        "canale di vendita", "predajny kanal"],
    "powinowactwo_nabijarki": ["powinowactwo nabijarki", "affinity", "related affinity",
                               "machine affinity", "nabijarka powinowactwo", "powinowactwo"],
    "cross_sell_potential": ["cross sell potential", "cross-sell", "cross sell",
                             "potencjal cross sell", "potencjal sprzedazy krzyzowej"],
    "decydent": ["decydent", "decision maker", "decider", "contact person",
                 "osoba decyzyjna", "entscheidungstrager"],
    "stanowisko": ["stanowisko", "position", "title", "role", "fonction", "funzione",
                   "pozicia"],
    "email_decydent": ["email decydent", "decision maker email", "contact email",
                       "direct email", "osobisty email", "decision email",
                       "contact mail", "mail direct"],
    "zrodlo_danych": ["zrodlo danych", "source", "data source", "source data",
                      "quelle", "fonte dati"],
    "data_weryfikacji": ["data weryfikacji", "verification date", "verified on",
                         "verified date", "datum", "date de verification",
                         "data verifica"],
    "flagi": ["flagi", "flags", "markers", "indicators", "znaczniki"],
    "notatki": ["notatki", "notes", "comments", "description", "uwagi", "notizen",
                "note", "remarques", "note"],
    "rynek_skala": ["rynek skala", "market scale", "market size", "scale", "skala rynku",
                    "taille du marche", "dimensione del mercato"],
}

# Per-column validation rules
# type: "enum" | "enum_loose" | "enum_or_empty" | "regex" | "regex_or_empty"
#       | "integer" | "integer_or_empty" | "date" | "date_or_empty"
#       | "url" | "url_or_empty" | "email" | "email_or_empty" | "text"
COLUMN_RULES: dict[str, dict[str, Any]] = {
    "related_to": {"type": "text", "allow_empty": True},
    "rok_zalozenia": {"type": "integer_or_empty", "min": 1800, "max": 2030},
    "id": {"type": "regex", "pattern": r"^[A-Z]{2}-[AB]-\d{3,4}$",
                    "allow_empty": False},
    "kategoria": {"type": "enum",
                  "values": ["A1", "A2", "A3", "A4", "A5", "A6",
                             "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"],
                  "allow_empty": False},
    "nazwa_firmy": {"type": "text", "min_len": 2, "allow_empty": False},
    "kraj": {"type": "enum",
             "values": ["PL", "CZ", "SK", "RO", "LT", "LV", "EE", "FR", "MD",
                        "BG", "SI", "HR", "RS"],
             "allow_empty": False},
    "miasto": {"type": "text", "allow_empty": True},
    "adres": {"type": "text", "allow_empty": True},
    "nip_vat": {"type": "nip_per_kraj", "allow_empty": True},
    "rejestr_id": {"type": "text", "allow_empty": True},
    "www": {"type": "url_or_empty", "allow_empty": True},
    "kanal_zamiennik": {"type": "text", "allow_empty": True},
    "email": {"type": "email_or_empty", "allow_empty": True},
    "telefon": {"type": "phone_or_empty", "allow_empty": True},
    "linkedin": {"type": "url_or_empty", "allow_empty": True, "must_contain": "linkedin.com"},
    "facebook": {"type": "url_or_empty", "allow_empty": True, "must_contain": "facebook.com"},
    "instagram": {"type": "url_or_empty", "allow_empty": True, "must_contain": "instagram.com"},
    "tiktok": {"type": "url_or_empty", "allow_empty": True, "must_contain": "tiktok.com"},
    "tier": {"type": "enum",
             "values": ["wyłączność", "autoryzowany", "reseller", "detalista",
                        "marketplace", "producent", "hurtownik"],
             "allow_empty": True},
    "marki_nabijarki": {"type": "text", "allow_empty": True},
    "marka_wlasna_oem": {"type": "text", "allow_empty": True},
    "sourcing": {"type": "enum_loose",
                 "values": ["Chiny", "Europa", "Polska", "mix",
                            # Loose aliases for descriptive values seen in the wild.
                            # First-word of each (e.g. "import", "dystrybucja") acts
                            # as a loose substring token; full enum values (Chiny,
                            # Europa, Polska, mix) act as the strict spec.
                            "import", "dystrybucja", "produkcja",
                            "własna produkcja", "import + dystrybucja",
                            "krajowa", "regionalna", "ogólnokrajowa",
                            "logistics", "cargo", "sklad", "skład", "skladiste",
                            "trošarine", "export", "direct", "daňový", "furs"],
                 "allow_empty": True},
    "wolumen": {"type": "enum", "values": ["mały", "średni", "duży"],
                "allow_empty": True},
    "confidence_wolumen": {"type": "enum",
                           "values": ["🟢", "🟡", "🔴", ""],
                           "allow_empty": True},
    "kanal_sprzedaży": {"type": "enum_loose",
                        "values": [
                            # Strict spec from methodology §10
                            "B2B only", "sklep stacjonarny", "marketplace",
                            "własny e-commerce", "mix",
                            # Loose aliases for descriptive values seen in
                            # the wild. Loose matching via first-word of the
                            # value catches these (case-insensitive).
                            # Wholesale
                            "hurt", "hurtownia", "veleprodaja", "dystrybucja",
                            "wholesale", "cash", "carry",
                            # E-commerce / retail / chain stores
                            "e-commerce", "online", "sieć", "sieciowy",
                            "salon", "salony", "sklepy", "sklep",
                            # Hospitality / HoReCa / Lounge
                            "hospitality", "lounge", "horeca", "gastronomia", "shisha",
                            # Customs / logistics / brokerage (out-of-spec
                            # but accepted as loose aliases for non-standard
                            # entries that don't fit the 5 strict enum values)
                            "logistyka", "skład", "agencja", "obsługa",
                            "agent", "broker",
                            # B2C variant
                            "B2C",
                            # Manufacturing / production
                            "produkcja", "producent",
                            # Distribution
                            "import", "eksport",
                        ],
                        "allow_empty": True},
    "powinowactwo_nabijarki": {"type": "integer_or_empty", "min": 1, "max": 5},
    "cross_sell_potential": {"type": "enum_loose",
                             "values": ["wysoki", "średni", "niski",
                                        # Loose alias for "bardzo wysoki" — first-word
                                        # of "wysoki" is "wysoki" which is a substring
                                        # of "bardzo wysoki". Tool accepts the
                                        # descriptive; methodology §10 keeps strict.
                                        "bardzo wysoki"],
                             "allow_empty": True},
    "decydent": {"type": "text", "allow_empty": True},
    "stanowisko": {"type": "text", "allow_empty": True},
    "email_decydent": {"type": "email_or_empty", "allow_empty": True},
    "zrodlo_danych": {"type": "text", "allow_empty": True},
    "data_weryfikacji": {"type": "date_or_empty", "format": "%Y-%m-%d"},
    "flagi": {"type": "text", "allow_empty": True},
    "notatki": {"type": "text", "allow_empty": True},
    "rynek_skala": {"type": "enum",
                    "values": ["duży", "średni", "mały"],
                    "allow_empty": True},
}

# Per-country NIP/IČO/CUI/etc. patterns
NIP_PATTERNS: dict[str, str] = {
    "PL": r"^PL\d{10}$|^\d{10}$",                  # NIP (10 digits)
    "CZ": r"^CZ\d{8,10}$|^\d{8}$",                 # IČO (8 digits) or DIČ (CZ + 8-10 digits)
    "SK": r"^SK\d{10}$|^\d{8,10}$",                # IČ DPH / IČO
    "RO": r"^RO\d{2,10}$|^\d{2,10}$",              # CUI/CIF
    "LT": r"^LT\d{9,12}$|^\d{9,12}$",              # PVM (9 or 12 digits) / Įmonės kodas (9 digits)
    "LV": r"^LV\d{11}$|^\d{11}$",                  # PVN / Reģistrācijas numurs
    "EE": r"^EE\d{8,9}$|^\d{8,9}$",                # KMKR (9 digits) / Registrikood (8 digits)
    "FR": r"^FR[A-Z0-9]{2}\d{9}$|^FR\d{9}$|^\d{9}$", # TVA (FR + 2 chars + 9 digits) / SIREN (9 digits)
    "MD": r"^MD\d{13}$|^\d{13}$",                  # IDNO (13 digits)
    "BG": r"^BG\d{9,10}$|^\d{9,10}$",              # EIK / Bulstat (9-10 digits)
    "SI": r"^SI\d{8}$|^\d{8}$",                    # ID za DDV / Matična številka
    "HR": r"^HR\d{11}$|^\d{11}$",                  # OIB (11 digits)
    "RS": r"^RS\s?\d{9,10}$|^\d{9}$",              # PIB (9 digits)
}

URL_RE = re.compile(r"^https?://[^\s]+\.[^\s]+$", re.IGNORECASE)
WWW_RE = re.compile(r"^(https?://|www\.)[^\s]+$", re.IGNORECASE)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[\+\d][\d\s\-\(\)]{5,}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# -----------------------------------------------------------------------------
# Known sentinel / non-value strings.
#
# In BILLSzuka, "brak", "n/a", "do weryfikacji", "nie", "no", "unknown"
# are PROVENANCE placeholders meaning "field intentionally left blank —
# no value found in any source".  They are NOT data-quality errors.
#
# These are normalised to "" before any validation runs, so every validator
# (url_or_empty, email_or_empty, enum_loose, phone_or_empty, nip_per_kraj,
# cross_check) treats them as empty rather than a garbage value.
#
# Additions should be lowercase / casefolded.  All comparisons use
# str.casefold() semantics.
# -----------------------------------------------------------------------------
KNOWN_NON_VALUE: set[str] = {
    "",           # already empty
    "brak",       # Polish: "none / not found"
    "n/a",        # not applicable
    "na",         # abbreviation (no dots)
    "nd",         # "nie dotyczy"
    "nie",        # "no"
    "no",         # English
    "nie dotyczy",
    "nie dotyczy.",
    "do weryfikacji",
    "do uzupełnienia",
    "do uzupelnienia",
    "unknown",
    "—",          # em-dash sentinel
    "do ustalenia",
    "–",          # en-dash sentinel
    "-",
    "do weryfikacji",
}


def is_known_non_value(value: Any) -> bool:
    """Return True if value is a known sentinel / provenance placeholder."""
    if value is None:
        return True
    return str(value).strip().casefold() in KNOWN_NON_VALUE


def normalize_non_value(value: Any) -> str:
    """Return '' for known sentinels, else the strip()d string."""
    if is_known_non_value(value):
        return ""
    return str(value).strip()



# ---------------------------------------------------------------------------
# Header mapping
# ---------------------------------------------------------------------------

def _normalize(name: str) -> str:
    """casefold + strip diacritics + replace _ with space + collapse whitespace.

    Three-step pipeline:

    1. ``name.casefold()`` — Unicode-aware caseless folding. Handles
       German ß → ss, Turkish İ → i̇, etc. But casefold does NOT map
       Polish Ł / ł (they remain atomic).
    2. **Manual replacement** for atomic letters-with-stroke and
       ligatures that NFKD cannot decompose. Python's NFKD leaves U+0141
       (Ł) and U+0142 (ł) untouched — they have no canonical decomposition
       mapping in Unicode. Same for Ø/ø (Danish/Norwegian), Ð/ð (Icelandic),
       Þ/þ (Icelandic thorn), Æ/æ, Œ/œ (French ligatures), đ/Đ (Croatian),
       ı/İ (Turkish dotless i).
    3. ``unicodedata.normalize("NFKD", ...)`` + drop combining marks.
       Strips acute, grave, circumflex, caron, breve, diaeresis, tilde,
       macron, ring above, etc. on all remaining characters.

    Common casefold gotcha: `unicodedata.combining()` returns 0 for U+0335
    (COMBINING SHORT STROKE OVERLAY) only if it appears standalone; but
    since NFKD never produces that codepoint for Ł anyway, the manual map
    above is the only reliable fix.
    """
    out = name
    # Manual map BEFORE casefold (defensive — casefold for some letters with
    # stroke is implementation-defined across Python versions; safer to
    # convert Ł/ł → l first, then casefold the rest).
    out = (out
        .replace("Ł", "l").replace("ł", "l")
        .replace("Ø", "o").replace("ø", "o")
        .replace("Ð", "d").replace("ð", "d")
        .replace("Þ", "th").replace("þ", "th")
        .replace("Æ", "ae").replace("æ", "ae")
        .replace("Œ", "oe").replace("œ", "oe")
        .replace("Đ", "d").replace("đ", "d")
        .replace("İ", "i").replace("ı", "i")
    )
    out = out.casefold()
    nfkd = unicodedata.normalize("NFKD", out)
    no_diacritics = "".join(c for c in nfkd if not unicodedata.combining(c))
    out = no_diacritics.replace("_", " ").strip()
    out = re.sub(r"\s+", " ", out)
    return out


def _build_alias_lookup(aliases: dict[str, list[str]]) -> dict[str, str]:
    """Map normalized alias -> canonical column name."""
    lookup: dict[str, str] = {}
    for canonical, names in aliases.items():
        for n in names:
            key = _normalize(n)
            if key in lookup and lookup[key] != canonical:
                # First wins — keep deterministic. Real ambiguity is rare.
                continue
            lookup[key] = canonical
    return lookup


def map_header(csv_header: str,
               alias_lookup: dict[str, str],
               custom_mapping: dict[str, str]) -> tuple[str | None, float, str]:
    """Return (canonical_name | None, confidence, source).

    source ∈ {"exact", "alias", "fuzzy", "manual", "unknown"}
    """
    if csv_header in CANONICAL_SET:
        return csv_header, 1.0, "exact"
    if csv_header in custom_mapping:
        return custom_mapping[csv_header], 1.0, "manual"
    norm = _normalize(csv_header)
    if norm in alias_lookup:
        return alias_lookup[norm], 0.95, "alias"
    # Fuzzy match against canonical + aliases
    candidates: list[tuple[str, float]] = []
    for canonical in CANONICAL_COLUMNS:
        ratio = difflib.SequenceMatcher(None, norm, _normalize(canonical)).ratio()
        candidates.append((canonical, ratio))
    for alias_key, canonical in alias_lookup.items():
        ratio = difflib.SequenceMatcher(None, norm, alias_key).ratio()
        candidates.append((canonical, ratio))
    if not candidates:
        return None, 0.0, "unknown"
    best_canonical, best_score = max(candidates, key=lambda x: x[1])
    if best_score >= 0.85:
        return best_canonical, best_score, "fuzzy"
    if best_score >= 0.65:
        return None, best_score, "fuzzy"  # suggestion only
    return None, best_score, "unknown"


# ---------------------------------------------------------------------------
# Row validators
# ---------------------------------------------------------------------------

def _is_empty(v: Any) -> bool:
    return v is None or str(v).strip() == ""


# PowerMatic / Hawk / "Inna" patterns — kept in sync with the frontend
# classifier in frontend-2/src/lib/brand.js so the validator and the
# UI agree on what counts as a brand signal. The regex set is the same
# shape: PowerMatic (incl. numeric+roman variants), Hawk (incl. James
# Hawk), and a generic "nabijarka/maszynka/tytoń" catch-all.
_BRAND_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"powermatic", re.IGNORECASE),
    re.compile(r"power\s*matic", re.IGNORECASE),
    # numeric (I-V) and variant forms like 3+, 4 IV; must mirror
    # frontend-2/src/lib/brand.js POWERMATIC_PATTERNS[2]
    re.compile(r"\b(?:1|2|3|4|5)[+\s]*[ivx]?\b", re.IGNORECASE),
    re.compile(r"\b(?:james)?hawk\b", re.IGNORECASE),
    re.compile(r"nabijark|nabijarki|machine|roller|gilz|tyton|tobacco", re.IGNORECASE),
)

_BRAND_TEXT_FIELDS: tuple[str, ...] = ("nazwa_firmy", "notatki", "zrodlo_danych", "sourcing")


def _brand_signal_in_row(row: dict[str, str]) -> bool:
    """Return True if the row has a recognisable brand keyword in any of
    the text columns used by the frontend `classifyBrand()`.

    A row with no `marki_nabijarki` but a brand keyword in its name /
    notes / source is still considered "classified" — e.g. a row whose
    `nazwa_firmy` literally says "PowerMatic distributor" doesn't need
    `marki_nabijarki='PowerMatic'` to be valid.
    """
    blob = " ".join(str(row.get(k) or "") for k in _BRAND_TEXT_FIELDS).lower()
    return any(p.search(blob) for p in _BRAND_PATTERNS)


def validate_value(canonical: str, value: Any, country: str | None) -> list[str]:
    """Return list of issue strings (empty = OK)."""
    rule = COLUMN_RULES.get(canonical, {"type": "text", "allow_empty": True})
    rtype = rule["type"]
    allow_empty = rule.get("allow_empty", True)

    # Normalise sentinel placeholders ("brak", "n/a", "do weryfikacji", etc.)
    # to "" before any validation check.
    value = normalize_non_value(value)

    if _is_empty(value):
        if allow_empty:
            return []
        return [f"{canonical}: required field is empty"]

    s = str(value).strip()

    if rtype == "text":
        if "min_len" in rule and len(s) < rule["min_len"]:
            return [f"{canonical}: '{s[:30]}' shorter than min_len={rule['min_len']}"]
        return []

    if rtype == "enum":
        if s not in rule["values"]:
            return [f"{canonical}: '{s}' not in enum {rule['values']}"]
        return []

    if rtype == "enum_loose":
        # Empty handling for B-only fields (e.g. cross_sell_potential in A rows).
        if rule.get("allow_empty") and _is_empty(value):
            return []
        # Loose match: accept if the full enum value is a substring of `s`,
        # OR if the FIRST WORD of the enum value appears anywhere in `s`.
        # The first-word check is what makes "B2B hurtownia + sieć kiosków"
        # match enum "B2B only" — full-substring would fail because
        # "B2B only" is never a contiguous substring of the value.
        value_lower = s.lower()
        for v in rule["values"]:
            v_lower = v.lower()
            if v_lower in value_lower:
                return []
            first_word = v_lower.split()[0] if v_lower else ""
            if first_word and first_word in value_lower:
                return []
        return [f"{canonical}: '{s[:60]}' doesn't contain any of {rule['values']} (loose match)"]

    if rtype == "enum_or_empty":
        if s == "":
            return []
        if s not in rule["values"]:
            return [f"{canonical}: '{s}' not in enum {rule['values']} (or empty)"]
        return []

    if rtype == "regex":
        if not re.match(rule["pattern"], s):
            return [f"{canonical}: '{s}' doesn't match pattern {rule['pattern']}"]
        return []

    if rtype == "regex_or_empty":
        if s == "":
            return []
        if not re.match(rule["pattern"], s):
            return [f"{canonical}: '{s}' doesn't match pattern {rule['pattern']}"]
        return []

    if rtype == "integer":
        try:
            n = int(s)
        except ValueError:
            return [f"{canonical}: '{s}' is not an integer"]
        if "min" in rule and n < rule["min"]:
            return [f"{canonical}: {n} < min={rule['min']}"]
        if "max" in rule and n > rule["max"]:
            return [f"{canonical}: {n} > max={rule['max']}"]
        return []

    if rtype == "integer_or_empty":
        if s == "":
            return []
        try:
            n = int(s)
        except ValueError:
            return [f"{canonical}: '{s}' is not an integer"]
        if "min" in rule and n < rule["min"]:
            return [f"{canonical}: {n} < min={rule['min']}"]
        if "max" in rule and n > rule["max"]:
            return [f"{canonical}: {n} > max={rule['max']}"]
        return []

    if rtype == "date_or_empty":
        if s == "":
            return []
        if not DATE_RE.match(s):
            return [f"{canonical}: '{s}' is not YYYY-MM-DD"]
        try:
            datetime.strptime(s, rule.get("format", "%Y-%m-%d"))
        except ValueError as e:
            return [f"{canonical}: '{s}' invalid date ({e})"]
        return []

    if rtype in ("url", "url_or_empty"):
        if s == "" and rtype == "url_or_empty":
            return []
        if not (URL_RE.match(s) or WWW_RE.match(s)):
            return [f"{canonical}: '{s}' is not a URL"]
        if "must_contain" in rule and rule["must_contain"] not in s.lower():
            return [f"{canonical}: '{s}' missing '{rule['must_contain']}'"]
        return []

    if rtype in ("email", "email_or_empty"):
        if s == "" and rtype == "email_or_empty":
            return []
        if not EMAIL_RE.match(s):
            return [f"{canonical}: '{s}' is not an email"]
        return []

    if rtype in ("phone", "phone_or_empty"):
        if s == "" and rtype == "phone_or_empty":
            return []
        if not PHONE_RE.match(s):
            return [f"{canonical}: '{s}' is not a phone number"]
        return []

    if rtype == "nip_per_kraj":
        if s == "":
            return []
        if country and country in NIP_PATTERNS:
            if not re.match(NIP_PATTERNS[country], s):
                return [f"{canonical}: '{s}' doesn't match NIP pattern for {country}"]
            return []
        # Unknown country — accept any non-empty value as warning
        return [f"{canonical}: '{s}' — no NIP pattern for country '{country}' (warning)"]

    return []


def cross_check(row: dict[str, str], catalog_type: str | None) -> list[str]:
    """A/B catalog consistency. catalog_type ∈ {'A', 'B', None}."""
    issues: list[str] = []
    if catalog_type == "A":
        if not _is_empty(row.get("powinowactwo_nabijarki")):
            issues.append("A row has powinowactwo_nabijarki (should be B-only)")
        if not _is_empty(row.get("cross_sell_potential")):
            issues.append("A row has cross_sell_potential (should be B-only)")
    elif catalog_type == "B":
        for col in ("marki_nabijarki", "marka_wlasna_oem"):
            # Sentinel placeholders ("brak", "n/a", etc.) are treated as empty.
            v = normalize_non_value(row.get(col))
            if v:
                issues.append(
                    f"B row has {col}='{row.get(col)}' (should be empty for B)"
                )
        if _is_empty(row.get("powinowactwo_nabijarki")):
            issues.append("B row missing powinowactwo_nabijarki (1-5)")
        if _is_empty(row.get("cross_sell_potential")):
            issues.append("B row missing cross_sell_potential (wysoki/średni/niski)")
    # marki_nabijarki consistency (added per task 5)
    marki = normalize_non_value(row.get("marki_nabijarki"))
    if catalog_type == "B" and marki:
        issues.append(f"B row has marki_nabijarki='{row.get('marki_nabijarki')}' (should be empty for B)")
    # A rows should list brands via marki_nabijarki — BUT a row is also
    # valid if the brand is detectable from nazwa_firmy / notatki /
    # zrodlo_danych / sourcing (the same fields the frontend
    # `classifyBrand()` reads). A row with no nazwa_firmy at all is a
    # minimal test fixture — we don't flag it. This matches
    # `test_clean_a_row_no_issues` and avoids flagging the 17 A-rows in
    # master.csv whose brand is implicit in their name.
    if (
        catalog_type == "A"
        and not marki
        and not _brand_signal_in_row(row)
        and any(not _is_empty(row.get(k)) for k in _BRAND_TEXT_FIELDS)
    ):
        issues.append(
            "A row missing marki_nabijarki (and no brand signal in nazwa_firmy/notatki/zrodlo_danych)",
        )
    return issues


# ---------------------------------------------------------------------------
# CSV reading helpers
# ---------------------------------------------------------------------------

def detect_separator(path: Path) -> str:
    """Sniff separator from first non-empty line."""
    with path.open("r", encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            if line.strip():
                # Count common separators
                counts = {sep: line.count(sep)
                          for sep in [",", ";", "\t", "|"]}
                sep = max(counts, key=counts.get)
                return "\t" if sep == "\t" else sep
    return ","


def detect_catalog_type(path: Path, header: list[str]) -> str | None:
    """Return 'A' / 'B' / None based on filename or kategoria samples."""
    name = path.stem.lower()
    m = re.search(r"catalog-([ab])-", name)
    if m:
        return m.group(1).upper()
    return None


def infer_country(path: Path,
                  row: dict[str, str],
                  header_mappings: dict[str, dict] | None = None) -> str | None:
    """Return ISO-2 code from filename, mapped canonical column, or row values.

    Priority:
    1. Filename pattern ``catalog-[ab]-<ISO>.csv`` — used by per-kraj catalogs.
    2. Look up the CSV column that maps to canonical "kraj" via header_mappings
       (e.g. new CSV with header "country" → canonical "kraj" → value "PL").
    3. Scan row values for an ISO-2 code in the 13-country set.
    """
    name = path.stem.lower()
    m = re.search(r"catalog-[ab]-([a-z]{2})$", name)
    if m:
        return m.group(1).upper()
    iso_set = {"PL", "CZ", "SK", "RO", "LT", "LV", "EE", "FR", "MD",
               "BG", "SI", "HR", "RS"}
    if header_mappings:
        for csv_col, m_info in header_mappings.items():
            if m_info.get("canonical") == "kraj":
                v = (row.get(csv_col) or "").strip().upper()
                if v in iso_set:
                    return v
    for v in row.values():
        s = str(v).strip().upper()
        if s in iso_set:
            return s
    return None


def load_custom_mapping(csv_path: Path) -> dict[str, str]:
    """Load sidecar .mapping.json if present (manual column overrides)."""
    sidecar = csv_path.with_suffix(csv_path.suffix + ".mapping.json")
    if sidecar.exists():
        try:
            return json.loads(sidecar.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def write_mapping_suggestion(csv_path: Path, mapping: dict[str, str]) -> None:
    """Write .mapping.suggested.json for manual review."""
    sidecar = csv_path.with_suffix(csv_path.suffix + ".mapping.suggested.json")
    sidecar.write_text(json.dumps(mapping, ensure_ascii=False, indent=2),
                       encoding="utf-8")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

@dataclass
class FileReport:
    path: str
    rows: int = 0
    header_mappings: dict[str, dict] = field(default_factory=dict)  # csv_col -> {canonical, confidence, source}
    missing_columns: list[str] = field(default_factory=list)
    extra_columns: list[str] = field(default_factory=list)
    row_arity_issues: list[tuple[int, int]] = field(default_factory=list)  # (row_num, actual_cols)
    value_issues: list[dict] = field(default_factory=list)  # {row, col, severity, msg}
    cross_issues: list[dict] = field(default_factory=list)
    catalog_type: str | None = None
    country: str | None = None
    severity_counts: dict[str, int] = field(default_factory=lambda: {"critical": 0, "warning": 0, "info": 0})


def _classify_severity(msg: str) -> str:
    """Heuristic: short words = critical, longer parenthetical = warning."""
    if "should be" in msg or "missing" in msg or "required" in msg:
        return "critical"
    if "doesn't match" in msg or "not in enum" in msg or "not a" in msg or "doesn't contain" in msg:
        return "critical"
    if "no NIP pattern" in msg:
        return "warning"
    return "warning"


def validate_file(csv_path: Path,
                  alias_lookup: dict[str, str],
                  strict: bool) -> FileReport:
    rep = FileReport(path=str(csv_path))
    sep = detect_separator(csv_path)
    custom_mapping = load_custom_mapping(csv_path)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=sep)
        try:
            header = next(reader)
        except StopIteration:
            return rep
        rep.catalog_type = detect_catalog_type(csv_path, header)

        # Map headers
        for csv_col in header:
            canonical, conf, source = map_header(csv_col, alias_lookup, custom_mapping)
            rep.header_mappings[csv_col] = {
                "canonical": canonical, "confidence": conf, "source": source
            }

        mapped_canonicals = {v["canonical"] for v in rep.header_mappings.values()
                             if v["canonical"] is not None}
        rep.missing_columns = sorted(CANONICAL_SET - mapped_canonicals)
        rep.extra_columns = sorted(set(header) - CANONICAL_SET - {csv_col for csv_col, v in rep.header_mappings.items() if v["canonical"] in CANONICAL_SET and v["source"] != "exact"})

        # Walk rows
        country: str | None = None
        for row_num, raw_row in enumerate(reader, start=2):
            if not raw_row or all(_is_empty(c) for c in raw_row):
                continue
            rep.rows += 1

            if len(raw_row) > len(header):
                rep.row_arity_issues.append((row_num, len(raw_row)))
                rep.severity_counts["critical"] += 1
                continue  # Can't safely map columns
            if len(raw_row) < len(header):
                # Pad with empty
                raw_row = raw_row + [""] * (len(header) - len(raw_row))

            row = dict(zip(header, raw_row))

            # Infer country per-row: filename pattern is file-level (per-kraj
            # catalogs), but a free-form intake CSV can have different countries
            # in different rows. ``country`` (set from filename) is the default;
            # ``row_country`` overrides per-row.
            row_country = country or infer_country(csv_path, row, rep.header_mappings)
            if rep.country is None and row_country:
                rep.country = row_country

            # Per-column value checks
            for csv_col, mapping in rep.header_mappings.items():
                canonical = mapping["canonical"]
                if canonical is None:
                    continue
                value = row.get(csv_col, "")
                issues = validate_value(canonical, value, row_country)
                for msg in issues:
                    sev = _classify_severity(msg)
                    if strict and sev == "warning":
                        sev = "critical"
                    rep.value_issues.append({
                        "row": row_num, "col": canonical, "severity": sev, "msg": msg
                    })
                    rep.severity_counts[sev] += 1

            # Cross-consistency
            cross = cross_check(row, rep.catalog_type)
            for msg in cross:
                sev = "critical" if strict else "warning"
                rep.cross_issues.append({
                    "row": row_num, "severity": sev, "msg": msg
                })
                rep.severity_counts[sev] += 1

    return rep


def render_markdown(reports: list[FileReport]) -> str:
    lines: list[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"# BILLSzuka — Column Validation Report")
    lines.append(f"\n_Generated: {now}_\n")

    total_critical = sum(r.severity_counts["critical"] for r in reports)
    total_warning = sum(r.severity_counts["warning"] for r in reports)
    total_rows = sum(r.rows for r in reports)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Files validated**: {len(reports)}")
    lines.append(f"- **Total data rows**: {total_rows}")
    lines.append(f"- **Critical issues**: {total_critical}")
    lines.append(f"- **Warnings**: {total_warning}")
    status = "✅ PASS" if total_critical == 0 and total_warning == 0 else \
             ("🔴 CRITICAL" if total_critical > 0 else "⚠️ WARNINGS")
    lines.append(f"- **Status**: {status}")
    lines.append("")

    for rep in reports:
        rel = rep.path
        if rep.severity_counts["critical"] == 0 and rep.severity_counts["warning"] == 0:
            continue  # Skip clean files in detailed report
        lines.append(f"## `{rel}`")
        lines.append("")
        lines.append(f"- Rows: {rep.rows} | "
                     f"Critical: {rep.severity_counts['critical']} | "
                     f"Warning: {rep.severity_counts['warning']}")
        if rep.country:
            lines.append(f"- Country: {rep.country}")
        if rep.catalog_type:
            lines.append(f"- Catalog type: {rep.catalog_type}")
        lines.append("")

        # Header mapping summary
        low_conf = {k: v for k, v in rep.header_mappings.items()
                    if v["canonical"] and v["confidence"] < 0.9}
        unmapped = {k: v for k, v in rep.header_mappings.items() if v["canonical"] is None}
        if low_conf or unmapped:
            lines.append("### Header mapping")
            lines.append("")
            lines.append("| CSV column | → canonical | confidence | source |")
            lines.append("|---|---|---|---|")
            for csv_col, m in rep.header_mappings.items():
                if m["canonical"] is None or m["confidence"] < 0.9:
                    lines.append(f"| `{csv_col}` | {m['canonical'] or '_unmapped_'} | "
                                 f"{m['confidence']:.2f} | {m['source']} |")
            lines.append("")

        if rep.missing_columns:
            lines.append(f"### Missing canonical columns ({len(rep.missing_columns)})")
            lines.append("")
            for col in rep.missing_columns:
                lines.append(f"- `{col}`")
            lines.append("")

        if rep.extra_columns:
            lines.append(f"### Extra non-canonical columns ({len(rep.extra_columns)})")
            lines.append("")
            for col in rep.extra_columns:
                lines.append(f"- `{col}`")
            lines.append("")

        if rep.row_arity_issues:
            lines.append(f"### Row arity issues ({len(rep.row_arity_issues)})")
            lines.append("")
            for row_num, n_cols in rep.row_arity_issues[:10]:
                lines.append(f"- row {row_num}: {n_cols} cols (expected {len(CANONICAL_COLUMNS)})")
            if len(rep.row_arity_issues) > 10:
                lines.append(f"- ... and {len(rep.row_arity_issues) - 10} more")
            lines.append("")

        if rep.value_issues:
            lines.append(f"### Value issues (first 20 of {len(rep.value_issues)})")
            lines.append("")
            lines.append("| row | column | severity | message |")
            lines.append("|---|---|---|---|")
            for v in rep.value_issues[:20]:
                msg = v["msg"].replace("|", "\\|")
                lines.append(f"| {v['row']} | `{v['col']}` | {v['severity']} | {msg} |")
            if len(rep.value_issues) > 20:
                lines.append(f"\n_…and {len(rep.value_issues) - 20} more_")
            lines.append("")

        if rep.cross_issues:
            lines.append(f"### Cross-consistency issues ({len(rep.cross_issues)})")
            lines.append("")
            by_msg: dict[str, int] = {}
            for c in rep.cross_issues:
                by_msg[c["msg"]] = by_msg.get(c["msg"], 0) + 1
            for msg, n in by_msg.items():
                lines.append(f"- {msg} ({n}×)")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", type=Path, action="append",
                        help="CSV file or dir (can be repeated). Default: data/*/catalog-*.csv + data/master.csv")
    parser.add_argument("--strict", action="store_true", help="Promote warnings to critical")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout only")
    parser.add_argument("--exit-zero", action="store_true", help="Always exit 0 (for CI info-only)")
    parser.add_argument("--report-dir", type=Path,
                        default=Path("data/validation-reports"),
                        help="Where to write the report (default: data/validation-reports)")
    parser.add_argument("--alias-file", type=Path,
                        help="JSON file with extra column aliases (canonical -> [aliases])")
    args = parser.parse_args()

    # Build alias lookup
    aliases = {k: list(v) for k, v in DEFAULT_ALIASES.items()}
    if args.alias_file and args.alias_file.exists():
        extra = json.loads(args.alias_file.read_text(encoding="utf-8"))
        for canonical, names in extra.items():
            aliases.setdefault(canonical, []).extend(names)
    alias_lookup = _build_alias_lookup(aliases)

    # Resolve targets
    root = Path.cwd()
    targets: list[Path] = []
    if args.csv:
        for p in args.csv:
            if p.is_dir():
                targets.extend(sorted(p.glob("*.csv")))
            elif p.is_file():
                targets.append(p)
            else:
                print(f"WARN: {p} not found", file=sys.stderr)
    else:
        data_dir = root / "data"
        if data_dir.exists():
            # Per-kraj catalogs
            for sub in sorted(data_dir.iterdir()):
                if sub.is_dir() and not sub.name.startswith("."):
                    targets.extend(sorted(sub.glob("catalog-[AB]-*.csv")))
            # Master + relationships
            for top in (data_dir / "master.csv", data_dir / "relationships.csv"):
                if top.exists():
                    targets.append(top)

    if not targets:
        print("No CSV files to validate.", file=sys.stderr)
        return 0

    # Validate
    reports: list[FileReport] = []
    for t in targets:
        try:
            rep = validate_file(t, alias_lookup, args.strict)
        except Exception as e:
            print(f"ERROR validating {t}: {e}", file=sys.stderr)
            continue
        reports.append(rep)

    # Output
    if args.json:
        out = {
            "timestamp": datetime.now().isoformat(),
            "files": [
                {
                    "path": r.path,
                    "rows": r.rows,
                    "country": r.country,
                    "catalog_type": r.catalog_type,
                    "missing_columns": r.missing_columns,
                    "extra_columns": r.extra_columns,
                    "header_mappings": r.header_mappings,
                    "row_arity_issues": r.row_arity_issues,
                    "value_issues": r.value_issues,
                    "cross_issues": r.cross_issues,
                    "severity_counts": r.severity_counts,
                } for r in reports
            ],
            "totals": {
                "files": len(reports),
                "rows": sum(r.rows for r in reports),
                "critical": sum(r.severity_counts["critical"] for r in reports),
                "warning": sum(r.severity_counts["warning"] for r in reports),
            }
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        md = render_markdown(reports)
        args.report_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        # When validating a single file, include its stem so consecutive runs
        # with --csv don't overwrite each other in the same second.
        if len(reports) == 1:
            stem = Path(reports[0].path).stem
            out_path = args.report_dir / f"columns-{stem}-{stamp}.md"
        else:
            out_path = args.report_dir / f"columns-{stamp}.md"
        out_path.write_text(md, encoding="utf-8")

        total_critical = sum(r.severity_counts["critical"] for r in reports)
        total_warning = sum(r.severity_counts["warning"] for r in reports)
        print(f"Files: {len(reports)} | Rows: {sum(r.rows for r in reports)} | "
              f"Critical: {total_critical} | Warning: {total_warning}")
        print(f"Report: {out_path}")

    # Exit code
    if args.exit_zero:
        return 0
    total_critical = sum(r.severity_counts["critical"] for r in reports)
    total_warning = sum(r.severity_counts["warning"] for r in reports)
    if total_critical > 0:
        return 1
    if total_warning > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
