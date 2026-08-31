#!/usr/bin/env python3
"""
tools/fix_master_data_integrity.py — One-shot fix of data-integrity issues
in data/master.csv (and same-pattern bugs in the source per-country catalogs
that would re-introduce them on next `billszuka.py compile`).

Issues addressed (per user audit 2026-08-21):
  A. duplicate NIPs (4)         → INTENTIONAL dual-business (A+B pairs);
                                  documented, no data change.
  B. data_weryfikacji (4)        → strip leaked flag text; keep YYYY-MM-DD.
  C. email with ';' (4)          → first email = primary, alt email in notatki.
  D. PL-A-003 swapped cols       → wolumen='duży', confidence='🟢',
                                  tier='reseller' (was brand list in tier).
  D2. wolumen canonicalization  → split 'duży 🟢 (...)' into wolumen+conf,
                                  fix casing ('Średni'→'średni'), map
                                  'Bardzo duży'→'duży', '5'→'🟢', '0.0'→'🔴'.
  J.  SI multi-col corruption   → SI-A-006, SI-B-008: reconstruct kanal_sprzedaży
                                  from city-name fragments; clear decydent/
                                  stanowisko/powinowactwo/email_decydent.
  K.  EE wolumen descriptive    → 8 EE rows with employee counts / NACE
                                  codes / revenue trends → canonical enum
                                  (heuristic) + detail → notatki.
  L.  descriptive confidence    → 13 rows where confidence_wolumen has prose
                                  (e.g. 'hurtownia + logistyka') → emoji
                                  based on evidence in notatki/wolumen.
  M.  powinowactwo_nabijarki    → A-rows with values (71) → clear; B-rows
                                  with non-1-5 values ('brak'/'wysoki'/
                                  'średni' = 56) → 'brak' (placeholder).
  N.  rynek_skala 'bardzo duży' → 51 rows; canonical max is 'duży' → fix.
  O.  email_decydent junk       → 12 rows with non-email (positions,
                                  source data, em-dash, HTML entities,
                                  URL like 'sanitex.eu') → clear or move
                                  to correct column.
  P.  social handles → URLs     → 18 rows where facebook/instagram/linkedin
                                  has a bare handle instead of full URL;
                                  prepend platform base URL.
  Q.  rok_zalozenia placeholder  → 44 rows with 'brak' → clear (empty).
  R.  nip_vat whitespace         → RO-A-009 'RO 48715727' → 'RO48715727'.
  S.  related_to↔rok_zalozenia swap  → enrichment pipeline (KRS/CEIDG/VIES
                                  import) or spreadsheet paste put a founding
                                  year in related_to while rok_zalozenia was
                                  empty.  Pattern: related_to='YYYY', rok_zalozenia=''.
                                  Fix: move year → rok_zalozenia, related_to='brak'.
  E. tier cardinality (58→7)     → map to canonical 7-value enum.
  F. flagi freeform (2)          → canonicalize, move freeform text to notatki.
  G. cross_sell_potential (8)    → move person-name data to decydent/notatki;
                                  city names → csp='brak' (manual fix needed
                                  for SI rows with multi-column city corruption).

Scope: master.csv + source catalogs that have the SAME specific issues
(Polska A+B, Litwa B for LT-B-001).  Out of scope: full tier-cardinality
cleanup across all 26 catalogs (74 unique values) — needs separate session.

Usage:
    python3 tools/fix_master_data_integrity.py --dry-run
    python3 tools/fix_master_data_integrity.py --apply
"""

import argparse
import csv
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MASTER = DATA / "master.csv"

# ---------------------------------------------------------------------------
#  Tier normalization: 58 unique values → 7 canonical (per methodology §10)
# ---------------------------------------------------------------------------
TIER_CANONICAL = {
    "wyłączność", "autoryzowany", "reseller", "detalista",
    "marketplace", "producent", "hurtownik",
}

# Hand-curated mapping (long-tail → canonical). Order: longest match first
# so e.g. "hurtownik regionalny (Istria & Kvarner)" is checked before
# "hurtownik regionalny" (which itself maps to hurtownik).
TIER_MAP_RAW = [
    # compound / multi-role
    ("ogólnokrajowy oddział koncernu", "hurtownik"),
    ("importer + producent (full chain)", "producent"),
    ("ogólnokrajowy producent + dystrybutor", "producent"),
    ("ogólnokrajowy importer + hurtownik", "hurtownik"),
    ("importer + hurtownik akcesoriów", "hurtownik"),
    ("importer + hurtownik", "hurtownik"),
    ("importer + hurtownik B2B", "hurtownik"),
    ("importer + dystrybutor premium", "hurtownik"),
    ("importer + producent maszyn tytoniowych", "producent"),
    ("autoryzowany importer / hurtownik", "autoryzowany"),
    ("producent + dystrybutor", "producent"),
    ("producent/hurtownik", "producent"),
    ("producent papierosów + dystrybutor hurt", "producent"),
    ("koncern/hurtownik", "hurtownik"),
    # e-commerce / kanał mix
    ("e-commerce/hurt", "hurtownik"),
    ("hurtownik/e-shop", "hurtownik"),
    ("hurt-detal specjalistyczny", "hurtownik"),
    ("detalista/hurt", "detalista"),
    ("e-commerce detal", "detalista"),
    # ogólnokrajowy * dystrybutor
    ("ogólnokrajowy dystrybutor FMCG i akcesoriów", "hurtownik"),
    ("ogólnokrajowy dystrybutor FMCG i artykułów użytkowych", "hurtownik"),
    ("ogólnokrajowy dystrybutor FMCG i artykuły użytkowe", "hurtownik"),
    ("ogólnokrajowy dystrybutor akcesoriów", "hurtownik"),
    ("ogólnokrajowy dystrybutor hurtowy", "hurtownik"),
    ("ogólnokrajowy dystrybutor tytoniowy", "hurtownik"),
    ("ogólnokrajowy dystrybutor / hurtownik", "hurtownik"),
    ("ogólnokrajowy dystrybutor + sieć Don Pealo", "hurtownik"),
    ("największa sieć handlowa + hurtownik", "hurtownik"),
    ("ogólnokrajowa sieć salonów + hurtownik", "hurtownik"),
    ("ogólnokrajowa sieć salonów tytoniowych", "hurtownik"),
    ("hurtownik + sieć specjalistyczna", "hurtownik"),
    ("hurtownik + operator sieci kiosków", "hurtownik"),
    ("hurtownik regionalny + sieć specjalistyczna", "hurtownik"),
    ("ogólnokrajowy operator dystrybucji i kiosków", "hurtownik"),
    ("ogólnokrajowy operator sieci kiosków", "hurtownik"),
    ("ogólnokrajowy operator logistyczny / hurtownik", "hurtownik"),
    ("ogólnokrajowy gigant logistyczno-dystrybucyjny", "hurtownik"),
    ("hurtownik tytoniowy (grupa Imperial Brands)", "hurtownik"),
    ("hurtownik FMCG", "hurtownik"),
    ("hurtownik FMCG (fresh produce)", "hurtownik"),
    ("hurtownik FMCG (sweets)", "hurtownik"),
    ("hurtownik regionalny", "hurtownik"),
    ("hurtownik regionalny (Istria & Kvarner)", "hurtownik"),
    ("hurtownik / dystrybutor maszynek", "hurtownik"),
    ("wyspecjalizowany hurtownik akcesoriów", "hurtownik"),
    ("wyspecjalizowany dystrybutor osprzętu", "hurtownik"),
    ("wyspecjalizowany dealer maszynek", "reseller"),
    ("logistyka / agencja celna", "hurtownik"),
    ("detalista RYO specjalistyczny", "detalista"),
    ("ogólnokrajowy producent tytoniu", "producent"),
    ("importer RYO (wholesale + retail)", "hurtownik"),
    # PL-A-003 specific (was brand list in tier col)
    ("marki własne + SMOK/VooPoo/Aspire/Vaporesso", "reseller"),
    # RS catalog (English descriptive; canonical mapping by dominant role)
    ("chain retailer + importer", "reseller"),       # retail dominant
    ("chain retailer + distributor", "hurtownik"),   # 1700+ pts = wholesale
    ("chain retailer", "reseller"),
    ("chain retailer (tobacco shop)", "reseller"),
    ("chain retailer (trafiki)", "reseller"),
    ("chain retailer (3 lokale)", "reseller"),
    ("importer + retail + cafe (B2B + B2C)", "reseller"),
    ("importer + e-commerce (e-papierosy)", "hurtownik"),
    ("importer / distributor (hookah)", "hurtownik"),
    ("distributor (RELX brand)", "hurtownik"),
    ("manufacturer + distributor (Big Tobacco)", "producent"),
    ("specialty retail (cigars + pipes + spirits)", "detalista"),
    ("specialty (shisha bar + lounge)", "detalista"),
    ("wholesale + retail", "hurtownik"),
    ("wholesale distributor", "hurtownik"),
    ("e-commerce retail + wholesale (Cartel distributer)", "hurtownik"),
]
# Final fallback: bare canonicals
TIER_MAP = dict(TIER_MAP_RAW)
for c in TIER_CANONICAL:
    TIER_MAP.setdefault(c, c)


def normalize_tier(val: str) -> str:
    """Map any of 58 tier values to canonical 7-value enum."""
    v = val.strip()
    if not v:
        return v
    if v in TIER_CANONICAL:
        return v
    return TIER_MAP.get(v, v)  # fall through if unmapped (kept for audit)


def append_notatki_unique(row: dict, addition: str) -> bool:
    """Append ` | <addition>` to row['notatki'] if not already present.

    Splits existing notatki by ' | ' separator, then checks if the new
    addition is already among the parts. Idempotent: re-running is a no-op.

    Returns True if the row was actually changed, False if no-op.
    """
    if not addition or not addition.strip():
        return False
    current = row.get("notatki", "").strip()
    parts = [p.strip() for p in current.split(" | ")] if current else []
    addition_clean = addition.strip()
    if addition_clean in parts:
        return False
    parts.append(addition_clean)
    new_val = " | ".join(p for p in parts if p)
    row["notatki"] = new_val
    return True


# S. Swap guard: related_to ↔ rok_zalozenia.
# Bug origin: KRS/CEIDG/VIES enrichment pipeline or spreadsheet paste placed a
# founding year (YYYY) in related_to while rok_zalozenia stayed empty.
# Pattern: related_to matches ^\d{4}$ AND rok_zalozenia is empty.
RE_BARE_YEAR = re.compile(r"^\d{4}$")


def _detect_rok_swap(row: dict) -> bool:
    """True when related_to holds a bare YYYY and rok_zalozenia is empty."""
    related = row.get("related_to", "").strip().strip("'")
    rok = row.get("rok_zalozenia", "").strip()
    return bool(RE_BARE_YEAR.match(related)) and not rok


# ---------------------------------------------------------------------------
#  Per-row fix tables (id → dict of column → new value).
#  Each change is evidence-backed; see docstring for the audit that produced
#  these targets.  Keys not present in the dict are unchanged.
# ---------------------------------------------------------------------------

# B. data_weryfikacji: extract first YYYY-MM-DD anywhere in the string.
DATE_LEAK = re.compile(r"(\d{4}-\d{2}-\d{2})")

# C. multi-email: primary + alt.
EMAIL_MULTI = {
    "PL-A-004": ("biuro@trober-polska.pl", "anna.skarbek@troeber.com"),
    "PL-A-008": ("monika.wachel@ckcomplex.pl", "b2b@ckcomplex.pl"),
    "PL-A-009": ("sekretariat@eignis.pl", "zamowienia@eignis.pl"),
    "PL-B-092": ("biuro@mrctrade.pl", "export@mrctrade.pl"),
}

# D. PL-A-003 col swap. Evidence: notatki explicitly says "Sieć 25+ sklepów"
#    + confidence is "e-commerce + 25+ sklepów stacjonarnych" (high).
PL_A_003 = {
    "tier": "reseller",                  # was brand list "marki własne + ..."
    "wolumen": "duży",                   # was '✅' (the confidence emoji)
    "confidence_wolumen": "🟢",          # was descriptive text
}

# J. SI multi-column corruption (2 rows). The data has a sentence
#   "Sieć salonów (City1, City2, ...) & E-commerce" split across multiple
#   columns: kanal_sprzedaży (start), powinowactwo_nabijarki, decydent,
#   stanowisko (end). Reconstruct kanal_sprzedaży, clear the rest,
#   move the city list to notatki.
SI_FIX = {
    "SI-A-006": {
        "kanal_sprzedaży": "Sieć salonów (Ljubljana, Maribor, Kranj, Krško) & E-commerce",
        "miasto": "Celje",  # HQ per adres (Stanetova 20, 3000 Celje)
        "decydent": "",
        "stanowisko": "",
        "powinowactwo_nabijarki": "",  # A-row, should be empty
        "email_decydent": "",          # was '4' (corrupted)
        "notatki_add": "Sieć 4+ lokali: Ljubljana, Maribor, Kranj, Krško.",
    },
    "SI-B-008": {
        "kanal_sprzedaży": "Sieć salonów (Maribor, Ljubljana, Murska Sobota) & E-commerce",
        "miasto": "Maribor",  # HQ per adres
        "decydent": "",
        "stanowisko": "",            # was '3' (corrupted; means 3 lokale)
        "powinowactwo_nabijarki": "",  # was 'Ljubljana'
        "email_decydent": "",        # was 'srednji' (Slovenian for medium)
        "notatki_add": "Sieć 3 lokali: Maribor, Ljubljana, Murska Sobota.",
    },
}

# K. EE wolumen (8 rows with employee counts / NACE / revenue). Heuristic
#   per evidence in notatki. Detail text → notatki.
#   Rules: 100+ employees → duży; 30-100 employees + wholesale → średni;
#          specialty retail / declining / e-commerce-only → mały.
EE_WOLUMEN_FIX = {
    "EE-B-008": {"wolumen": "średni", "notatki_add": "32 pracowników (BalticFirms.eu 2025)"},
    "EE-B-009": {"wolumen": "mały", "notatki_add": "EMTAK 47.11 (e-commerce detaliczny niewyspecjalizowany)"},
    "EE-B-011": {"wolumen": "mały", "notatki_add": "Müügitulu: €2.77M (2020) → €0 (2024-2025, declining)"},
    "EE-B-012": {"wolumen": "mały", "notatki_add": "Największy wybór RYO w Tallinnie i Nordics (per własne claim)"},
    "EE-B-013": {"wolumen": "średni", "notatki_add": "88 pracowników (BalticFirms.eu 2025)"},
    "EE-B-014": {"wolumen": "duży", "notatki_add": "108 pracowników (BalticFirms.eu 2025)"},
    "EE-B-015": {"wolumen": "średni", "notatki_add": "88 pracowników, founded 1993"},
    "EE-B-016": {"wolumen": "średni", "notatki_add": "45 pracowników (BalticFirms.eu 2025)"},
}

# L. Descriptive-text confidence_wolumen (13 rows). Each mapping based
#   on evidence in notatki + other columns.
DESCRIPTIVE_CONFIDENCE_FIX = {
    "PL-A-001": "🟢",   # BILLS — verified exclusive distributor, top evidence
    "PL-A-002": "🟢",   # BISTA — 70-country exporter, Intertabac exhibitor
    "PL-B-001": "🟢",   # CK COMPLEX — 100+ sklepów, KRS verified, distributor
    "PL-B-002": "🟡",   # F.H.U. ALPIK — single shop + B2B, mały scale
    "PL-B-003": "🟡",   # GABIMIX — single shop + hurtownia, CEIDG active
    "PL-B-004": "🟢",   # CASISS — 6+ locations, KRS 0000061705 verified
    "PL-B-005": "🟢",   # POLSKA GRUPA TYTONIOWA — ogólnopolska, KRS verified
    "PL-B-022": "🟡",   # AMPEX — 2 lokalizacje + serwis, mały scale
    "PL-B-023": "🟡",   # ELENPIPE — declining revenue, 2 emp 2014
    "PL-B-024": "🟢",   # ORION — 1.8 mld szt/rok, 10M kapitał, producent+export
    "LT-B-001": "🟢",   # UAB SANITEX — major Baltic FMCG (per INTEL)
    "LV-B-001": "🟢",   # SIA SANITEX — sister of LT-B-001
    "EE-B-001": "🟢",   # OÜ SANITEX — sister of LT-B-001
}

# M. powinowactwo_nabijarki (B-only, 1-5). A-rows must be empty; B-rows
#   with placeholder ('brak'/'wysoki'/'średni') → 'brak' (the canonical
#   placeholder per the existing data pattern).
POWINOWACTWO_PLACEHOLDER = {"brak", "wysoki", "średni", "niski", "do ustalenia", ""}

# N. rynek_skala 'bardzo duży' → 'duży' (max canonical).
RYNEK_SKALA_BARDZO_DUZY = "bardzo duży"

# O. email_decydent junk values → cleared or moved to zrodlo_danych.
#   Keyed by id → (new_email_decydent, optional stanowisko, optional notatki_add)
#   'clear' = empty string; 'move_to_zrodlo' = append to zrodlo_danych
EMAIL_DECYDENT_FIX = {
    "PL-A-001": {"email_decydent": "", "stanowisko": "właściciel/CEO"},
    "PL-B-002": {"email_decydent": "", "zrodlo_add": "ceidg api + web search"},
    "PL-B-003": {"email_decydent": "", "zrodlo_add": "ceidg + web search"},
    "PL-B-004": {"email_decydent": "", "zrodlo_add": "panoramafirm + pkt.pl (2 niezależne źródła)"},
    "PL-B-022": {"email_decydent": "", "zrodlo_add": "bizraport.pl + panoramafirm + web search"},
    "PL-B-023": {"email_decydent": "", "zrodlo_add": "krs api + elenpipe.com + emis.com"},
    "PL-B-026": {"email_decydent": ""},   # was '—'
    "PL-B-062": {"email_decydent": ""},   # was '—'
    "LT-B-001": {"email_decydent": "", "zrodlo_add": "rekvizitai.vz.lt + web search"},
    "LT-B-006": {"email_decydent": ""},   # was '[email&#160;protected]' (HTML entity)
    "LV-B-001": {"email_decydent": ""},   # was 'sanitex.eu' (URL, not email)
    "EE-B-001": {"email_decydent": ""},   # was 'sanitex.eu'
}

# P. Social handles → URLs. Per-id fixes where the value is clearly a
#   handle (no protocol). We prepend the platform base URL.
SOCIAL_HANDLE_FIX = {
    "facebook": {
        "PL-A-002": "https://facebook.com/bistastandard",
        "PL-A-008": "https://facebook.com/CKComplex",
        "PL-B-001": "https://facebook.com/CKComplex",
        "PL-B-002": "https://facebook.com/BongoGoPL",
        "PL-B-003": "https://facebook.com/dopalenia",
        "PL-B-005": "https://facebook.com/polskagtpl",
        "PL-B-023": "https://facebook.com/elenpipepl",
        "PL-B-024": "https://facebook.com/oriontobaccopoland",
        "LT-B-001": "https://facebook.com/sanitex",
        "LV-B-001": "https://facebook.com/sanitex",
        "EE-B-001": "https://facebook.com/sanitex",
        "CZ-A-001": "https://facebook.com/fortisdbcz",
    },
    "instagram": {
        "PL-A-002": "https://instagram.com/bistastandard",
        "PL-A-008": "https://instagram.com/ckcomplexspzoo",
        "PL-B-001": "https://instagram.com/ckcomplexspzoo",
        "PL-B-002": "https://instagram.com/bongogo",
        "PL-B-005": "https://instagram.com/polskagt_pl",
        "PL-B-023": "https://instagram.com/elenpipe_pl",
        "PL-B-024": "https://instagram.com/orion_tobacco_pl",
    },
    "linkedin": {
        "PL-A-008": "https://www.linkedin.com/company/ck-complex-sp.-z-o.o.",
        "PL-B-001": "https://www.linkedin.com/company/ck-complex-sp.-z-o.o.",
    },
}

# D2. wolumen+confidence_wolumen canonicalization. Per methodology §10
#     wolumen ∈ {mały, średni, duży}, confidence_wolumen ∈ {🟢, 🟡, 🔴}.
#     The data has 4 patterns that violate this:
#       a) 'Średni' / 'Duży' / 'Mały'  → case fix
#       b) 'Bardzo duży'                → 'duży' (methodology max)
#       c) 'duży 🟢 (1.8 mld szt...)'   → split: wolumen='duży', conf='🟢',
#                                          extra detail in notatki
#       d) confidence_wolumen='5'/'0.0'  → '🟢'/'🔴' (5/5 or 0/5 rating)
#     Descriptive text in confidence_wolumen (e.g. 'hurtownia + logistyka')
#     is LEFT AS-IS — would require domain knowledge to convert; flagged
#     for manual review in audit log.
WOLUMEN_RE = re.compile(
    r"^(mały|średni|duży|bardzo duży)\s*(🟢|🟡|🔴)?\s*(\([^)]*\))?\s*$",
    re.IGNORECASE,
)
CONFIDENCE_NUMERIC = {"5": "🟢", "0.0": "🔴", "0": "🔴", "1": "🔴"}


def normalize_wolumen_confidence(row: dict, changes: list) -> None:
    """Clean wolumen+confidence to match canonical schema.

    Conservative — only fixes patterns that are EVIDENTLY data entry errors
    (case, combined format, numeric rating).  Descriptive text in
    confidence_wolumen is LEFT AS-IS — would require domain knowledge to
    convert; flagged for manual review.
    """
    w = row.get("wolumen", "").strip()
    c = row.get("confidence_wolumen", "").strip()
    if not w and not c:
        return

    new_w = w
    new_c = c
    extra = None
    confidence_placeholder = {"", "brak", "do ustalenia"}

    # (pre) Handle combined confidence like 'mały 🟡' / 'średni 🟢' / 'duży 🔴'
    if c and c not in ("🟢", "🟡", "🔴"):
        m_c = re.match(r"^(mały|średni|duży)\s*([🟢🟡🔴]).*$", c)
        if m_c:
            new_c = m_c.group(2)
            changes.append(f"confidence_wolumen (split combined): {c!r} → {new_c!r}")

    if w and w != "✅":
        m = WOLUMEN_RE.match(w)
        if m:
            base = m.group(1).lower()
            if base == "bardzo duży":
                base = "duży"
            emoji = m.group(2)
            tail = m.group(3)
            new_w = base
            # Only set confidence from embedded emoji if current confidence
            # is empty/placeholder — never overwrite descriptive text
            # (would lose domain knowledge).
            if emoji and c in confidence_placeholder:
                new_c = emoji
            if tail:
                extra = tail.strip("()")
        else:
            # Casing fix only (clearly data entry error)
            wl = w.lower()
            if wl.startswith("bardzo"):
                new_w = "duży"
            elif wl in ("mały", "średni", "duży"):
                new_w = wl
            else:
                # Handle non-canonical trailing emojis (e.g. 'mały ⚪')
                m2 = re.match(r"^(mały|średni|duży)\s*[^🟢🟡🔴].*$", w, re.IGNORECASE)
                if m2:
                    new_w = m2.group(1).lower()

    # Numeric score → emoji (5/5 = 🟢, 0/5 = 🔴) — same pattern as D
    if new_c in CONFIDENCE_NUMERIC:
        new_c = CONFIDENCE_NUMERIC[new_c]

    if new_w != w:
        changes.append(f"wolumen: {w!r} → {new_w!r}")
        row["wolumen"] = new_w
    if new_c != c:
        changes.append(f"confidence_wolumen: {c!r} → {new_c!r}")
        row["confidence_wolumen"] = new_c
    if extra:
        addition = f"wolumen detail: {extra}"
        if append_notatki_unique(row, addition):
            changes.append(f"notatki += wolumen detail: {extra!r}")

# F. flagi: 2 rows where flagi is a freeform notatka. Move prose to notatki,
#    set flagi to canonical. Use the row's data_weryfikacji as the date.
FLAG_FREEFORM = {
    # id → (new_flagi, notatki_addition)
    "RO-A-009": (None,  # date filled in dynamically
                 "🔍 MUST-CHECK: czy kupił PowerMatic od BILLS PL czy od innego dystrybutora"),
    "LT-B-010": (None,
                 "🔍 HOOKAH/SHISHA — NIE powerMatic, przekategoryzowano z A1→B5"),
}

# G. cross_sell_potential: person-name leaks.
#  Each entry: csp_new, plus optional decydent_new / stanowisko_new / notatki_add.
#  Where decydent/stanowisko currently hold POSITION data, we keep them as
#  stanowisko and put the name (or fuller info) in decydent.  Where they are
#  empty, the csp text becomes decydent directly.
CSP_PERSON_FIX = {
    "PL-A-003": {"csp": "do ustalenia"},  # normalize placeholder (decydent/stanowisko OK)
    "PL-B-002": {
        "csp": "brak",
        "decydent": "Ryszard Trzciński",
        "stanowisko": "właściciel",  # was in decydent
    },
    "PL-B-003": {
        "csp": "brak",
        "decydent": "Krzysztof Jaszczak",
        "stanowisko": "właściciel",  # was in decydent
    },
    "PL-B-005": {
        "csp": "brak",
        "notatki_add": "Wspólnicy: Robert Biela (33% udziałów) + Barbara Urcus-Wargocka (33%) + Robert Rutkowski (33%).",
        # Also fix stanowisko='biuro@polskagt.pl' which is an email
        "email_decydent": "biuro@polskagt.pl",
        "stanowisko": "",  # clear
    },
    "PL-B-006": {"csp": "do ustalenia"},  # placeholder
    "PL-B-014": {
        "csp": "brak",
        "decydent": "Aleks Dudalski (dział handlowy) + Artur Dudalski",
    },
    "PL-B-015": {"csp": "do ustalenia"},  # placeholder
    "PL-B-020": {
        "csp": "brak",
        "decydent": "Krzysztof Król",
        "stanowisko": "właściciel JDG",
    },
    "PL-B-022": {
        "csp": "brak",
        "decydent": "Adam Minicki + Paweł Potoniec",
        "stanowisko": "wspólnicy sp.j.",  # was in decydent
    },
    "PL-B-023": {"csp": "do ustalenia"},  # placeholder
    "PL-B-024": {
        "csp": "brak",
        "notatki_add": "Wspólnicy: Jerzy Czernek (88 tys. udziałów, 4.4M PLN) + Łukasz M***** (102 tys. udziałów, 5.1M PLN).",
        "email_decydent": "karolina@orion.mail.pl",
        "stanowisko": "sprzedaż krajowa",
    },
    "LT-B-001": {"csp": "brak"},  # 'Ramūnas Kairys' already in decydent
}

# G. cross_sell_potential: city-name leaks (SI rows have multi-col city
#    corruption; only fix the csp value here, leave other cols for manual
#    review — out of scope for this batch).
CSP_CITY_FIX = {
    "SI-A-006": {"csp": "brak"},
    "SI-B-008": {"csp": "brak"},
}

# G. cross_sell_potential: non-PL translations (canonical is wysoki/średni/niski)
CSP_TRANSLATE = {
    "visok": "wysoki",
    "zelo visok": "bardzo wysoki",
    "srednji": "średni",
    "nizek": "niski",
}


# ---------------------------------------------------------------------------
#  Engine
# ---------------------------------------------------------------------------

def fix_row(row: dict, src_label: str, log: list) -> dict:
    """Apply all per-row fixes. Returns the row (modified in place) and
    appends human-readable change notes to `log`."""
    cid = row.get("id", "")
    changes = []

    # ---- B. data_weryfikacji: strip leaked flag text ----
    dv = row.get("data_weryfikacji", "").strip()
    if dv:
        m = DATE_LEAK.search(dv)
        if m and m.group(1) != dv:
            new_dv = m.group(1)
            changes.append(f"data_weryfikacji: {dv!r} → {new_dv!r}")
            row["data_weryfikacji"] = new_dv
            dv = new_dv

    # ---- C. multi-email ----
    if cid in EMAIL_MULTI:
        primary, alt = EMAIL_MULTI[cid]
        old = row.get("email", "")
        if ";" in old:
            row["email"] = primary
            if append_notatki_unique(row, f"alt email: {alt}"):
                changes.append(f"email: {old!r} → {primary!r} (alt→notatki)")

    # ---- D. PL-A-003 swapped cols ----
    if cid in ("PL-A-003",) and any(k in PL_A_003 for k in row):
        for k, v in PL_A_003.items():
            if row.get(k) != v:
                changes.append(f"{k}: {row.get(k)!r} → {v!r}")
                row[k] = v

    # ---- D2. wolumen+confidence canonicalization (all rows) ----
    normalize_wolumen_confidence(row, changes)

    # ---- J. SI multi-column corruption (2 rows) ----
    if cid in SI_FIX:
        spec = SI_FIX[cid]
        for k in ("kanal_sprzedaży", "miasto", "decydent", "stanowisko",
                  "powinowactwo_nabijarki", "email_decydent"):
            if k in spec:
                old = row.get(k, "")
                if spec[k] != old:
                    changes.append(f"{k}: {old!r} → {spec[k]!r}")
                    row[k] = spec[k]
        if "notatki_add" in spec:
            if append_notatki_unique(row, spec["notatki_add"]):
                changes.append("notatki += lokale list")

    # ---- K. EE wolumen descriptive (8 rows) ----
    if cid in EE_WOLUMEN_FIX:
        spec = EE_WOLUMEN_FIX[cid]
        old = row.get("wolumen", "")
        if spec["wolumen"] != old:
            changes.append(f"wolumen: {old!r} → {spec['wolumen']!r}")
            row["wolumen"] = spec["wolumen"]
        if "notatki_add" in spec:
            if append_notatki_unique(row, spec["notatki_add"]):
                changes.append("notatki += wolumen detail")

    # ---- L. Descriptive confidence_wolumen (13 rows) ----
    if cid in DESCRIPTIVE_CONFIDENCE_FIX:
        new_c = DESCRIPTIVE_CONFIDENCE_FIX[cid]
        old = row.get("confidence_wolumen", "")
        if old != new_c:
            changes.append(f"confidence_wolumen: {old!r} → {new_c!r}")
            row["confidence_wolumen"] = new_c
            # Move old descriptive text to notatki so it's not lost
            append_notatki_unique(row, f"cf detail: {old}")

    # ---- M. powinowactwo_nabijarki (B-only, 1-5) ----
    p = row.get("powinowactwo_nabijarki", "").strip()
    if p:
        is_a = row.get("kategoria", "").strip().startswith("A")
        if is_a:
            # A-rows must be empty (B-only field)
            changes.append(f"powinowactwo_nabijarki: A-row cleared (was {p!r})")
            row["powinowactwo_nabijarki"] = ""
        elif p in POWINOWACTWO_PLACEHOLDER or p not in ("1", "2", "3", "4", "5"):
            # B-row with non-canonical value (placeholder or text)
            # 'brak'/'wysoki'/'średni' are placeholders meaning "no data"
            # → clear to empty (canonical = "no value" for B-only enum).
            changes.append(f"powinowactwo_nabijarki: {p!r} → '' (placeholder)")
            row["powinowactwo_nabijarki"] = ""

    # ---- N. rynek_skala 'bardzo duży' → 'duży' ----
    rs = row.get("rynek_skala", "").strip()
    if rs == RYNEK_SKALA_BARDZO_DUZY:
        changes.append("rynek_skala: 'bardzo duży' → 'duży' (canonical max)")
        row["rynek_skala"] = "duży"

    # ---- O. email_decydent junk values ----
    if cid in EMAIL_DECYDENT_FIX:
        spec = EMAIL_DECYDENT_FIX[cid]
        if "email_decydent" in spec:
            old = row.get("email_decydent", "")
            new = spec["email_decydent"]
            if old != new:
                changes.append(f"email_decydent: {old!r} → {new!r}")
                row["email_decydent"] = new
        if "stanowisko" in spec:
            old = row.get("stanowisko", "")
            new = spec["stanowisko"]
            if old != new:
                changes.append(f"stanowisko: {old!r} → {new!r}")
                row["stanowisko"] = new
        if "zrodlo_add" in spec:
            zd = row.get("zrodlo_danych", "")
            if spec["zrodlo_add"] not in zd:
                row["zrodlo_danych"] = (zd + f" | {spec['zrodlo_add']}").strip(" |")
                changes.append("zrodlo_danych += email_decydent content")

    # ---- P. Social handles → URLs (per-id mapping) ----
    for col, fixes in SOCIAL_HANDLE_FIX.items():
        if cid in fixes:
            old = row.get(col, "")
            new = fixes[cid]
            if old and old != new and not old.startswith("http"):
                changes.append(f"{col}: {old!r} → {new!r}")
                row[col] = new

    # ---- Q. rok_zalozenia 'brak' → empty ----
    rok = row.get("rok_zalozenia", "").strip()
    if rok == "brak":
        changes.append("rok_zalozenia: 'brak' → '' (placeholder)")
        row["rok_zalozenia"] = ""

    # ---- S. related_to↔rok_zalozenia swap guard ----
    # Pattern: related_to='YYYY' (bare year) AND rok_zalozenia is empty.
    # Fix: move year → rok_zalozenia, set related_to = 'brak'.
    # This repair is idempotent: if already fixed it will no longer match _detect_rok_swap.
    if _detect_rok_swap(row):
        year_val = row["related_to"].strip().strip("'")
        changes.append(
            f"SWAP FIX S: related_to={year_val!r}→'brak', "
            f"rok_zalozenia=''→{year_val!r}"
        )
        row["related_to"] = "brak"
        row["rok_zalozenia"] = year_val

    # ---- R. nip_vat whitespace (RO-A-009) ----
    nip = row.get("nip_vat", "")
    if nip and " " in nip:
        new_nip = nip.replace(" ", "")
        if cid == "RO-A-009":
            changes.append(f"nip_vat: {nip!r} → {new_nip!r}")
            row["nip_vat"] = new_nip

    # ---- E. tier normalize (apply to all rows) ----
    t = row.get("tier", "").strip()
    if t:
        new_t = normalize_tier(t)
        if new_t != t:
            changes.append(f"tier: {t!r} → {new_t!r}")
            row["tier"] = new_t

    # ---- F. flagi freeform ----
    if cid in FLAG_FREEFORM:
        new_flagi_template, notatki_add = FLAG_FREEFORM[cid]
        if new_flagi_template is None:
            # Build canonical: "<date> ✅ FROZEN (API)"
            row["flagi"] = f"{dv} ✅ FROZEN (API)" if dv else "2026-08-18 ✅ FROZEN (API)"
        else:
            row["flagi"] = new_flagi_template
        if append_notatki_unique(row, notatki_add):
            changes.append(f"flagi → canonical; notatki += {notatki_add[:40]!r}…")

    # ---- G. cross_sell_potential: person / city / translation ----
    for fixdict in (CSP_PERSON_FIX, CSP_CITY_FIX):
        if cid in fixdict:
            spec = fixdict[cid]
            old_csp = row.get("cross_sell_potential", "")
            new_csp = spec.get("csp", old_csp)
            if new_csp != old_csp:
                changes.append(f"cross_sell_potential: {old_csp!r} → {new_csp!r}")
                row["cross_sell_potential"] = new_csp
            for k in ("decydent", "stanowisko", "email_decydent"):
                if k in spec:
                    old = row.get(k, "")
                    if spec[k] != old:
                        changes.append(f"{k}: {old!r} → {spec[k]!r}")
                        row[k] = spec[k]
            if "notatki_add" in spec:
                if append_notatki_unique(row, spec["notatki_add"]):
                    changes.append("notatki += shareholder data")

    # cross_sell_potential: language translation
    csp = row.get("cross_sell_potential", "").strip()
    if csp in CSP_TRANSLATE:
        new_csp = CSP_TRANSLATE[csp]
        changes.append(f"cross_sell_potential (i18n): {csp!r} → {new_csp!r}")
        row["cross_sell_potential"] = new_csp

    if changes:
        log.append(f"  [{src_label}] {cid}: " + "; ".join(changes))
    return row


def fix_file(path: Path, log: list, src_label: str) -> int:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    n_changed_rows = 0
    for r in rows:
        before = dict(r)
        fix_row(r, src_label, log)
        if any(before.get(k) != r.get(k) for k in before):
            n_changed_rows += 1

    return n_changed_rows, rows, fieldnames


def write_file(path: Path, rows: list, fieldnames: list) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would change, don't write")
    ap.add_argument("--apply", action="store_true",
                    help="Apply fixes to master.csv + same-pattern source catalogs")
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        ap.error("specify --dry-run or --apply")

    # Build list of files to fix — every per-kraj catalog (so compile won't
    # revert our changes by pulling stale values back into master.csv) plus
    # master.csv itself.  Skip hidden/snapshot dirs (per tools/auto_enrich.py
    # SKIP_DIRS convention) and intake/extras.
    SKIP_DIR_NAMES = {".snapshots", ".verify-state", "backups", "verification", "_intake", "_icons"}
    catalog_files = []
    for p in DATA.glob("*/catalog-*-*.csv"):
        if p.parent.name in SKIP_DIR_NAMES:
            continue
        if any(skip in p.parts for skip in SKIP_DIR_NAMES):
            continue
        if "extra-leads" in p.name:
            continue
        catalog_files.append(p)
    catalog_files.sort()
    targets = [(MASTER, "master")]
    for p in catalog_files:
        # short label like "PL-A" or "RO-B"
        parts = p.stem.split("-")
        label = f"{parts[1]}-{parts[2]}" if len(parts) == 3 else p.stem
        targets.append((p, label))

    log = []
    log.append(f"# Master data-integrity fix — {datetime.now().isoformat(timespec='seconds')}")
    log.append(f"# Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    log.append("")

    summary = []
    for path, label in targets:
        if not path.exists():
            summary.append(f"  {label}: NOT FOUND ({path})")
            continue
        n_changed, rows, fieldnames = fix_file(path, log, label)
        if args.apply and n_changed > 0:
            # Backup once
            bak = path.with_suffix(path.suffix + f".pre-fix-{datetime.now().strftime('%Y%m%d')}.bak")
            if not bak.exists():
                shutil.copy2(path, bak)
            write_file(path, rows, fieldnames)
        summary.append(f"  {label} ({path.name}): {n_changed} rows changed")

    log.append("")
    log.append("# Summary")
    log.extend(summary)

    print("\n".join(log))

    if args.dry_run:
        print("\n(dry-run; no files modified)")


if __name__ == "__main__":
    main()
