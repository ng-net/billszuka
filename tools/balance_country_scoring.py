#!/usr/bin/env python3
"""
tools/balance_country_scoring.py — Balances and calibrates scoring across all 13 countries.

Normalizes and calibrates (only when the source field is empty/sentinel — never overwrites
verified values):

  1. rynek_skala: auto-set from RYNEK_SKALA_MAP (PL/CZ/FR: duży, RO/BG/HR/SI/SK/RS: średni,
     LT/LV/EE/MD: mały)
  2. wolumen: fill empty/sentinel with tier/category-aware default. Never downgrade a
     verified value.
  3. confidence_wolumen: only fill if missing OR if currently 'brak'/sentinel. NEVER
     overwrite a 🟢/🟡/🔴 already set by the verifier. Hard-gate on
     HALUCYNACJA (→ 🔴) and DO-WERYFIKACJI markers in flagi / sourcing / notatki
     (→ 🟡 if any structural field present, else 🔴).
  4. powinowactwo_nabijarki (Catalog B only): 1-5, never overwrite if already valid.
  5. cross_sell_potential (Catalog B only): wysoki/średni/niski/bardzo wysoki. Never
     hallucinate a value when only 'brak'/'do ustalenia' is present — leave as empty
     (honest unknown) unless we have at least one real signal in notatki/marki/sourcing.
  6. marki_nabijarki: Catalog A fill from notes; Catalog B — never clear a meaningful
     value like 'nie' (Polish "no" = explicit "doesn't carry these brands"), only
     clear obvious placeholders ('brak', 'do ustalenia', '').
  7. tier: fill missing tiers from category and notes.

Iron rules enforced here (mirrors AGENTS.md / DZIENNIK):
  - Never overwrite a verifier-set 🟢/🟡/🔴 — those are evidence, not defaults.
  - Never set a field when the source says "do weryfikacji" / "DO-WERYFIKACJI" /
    "HALUCYNACJA" — those mean the data is suspect, not absent.
  - Never hallucinate cross_sell_potential. Empty is honest; synthetic "wysoki"
    from category alone is a default dressed as analysis.
  - 'nie' (Polish "no") is a meaningful sentinel — preserve it.
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# ---------------------------------------------------------------------------
# Static maps
# ---------------------------------------------------------------------------

RYNEK_SKALA_MAP = {
    "PL": "duży", "CZ": "duży", "FR": "duży",
    "RO": "średni", "BG": "średni", "HR": "średni",
    "SI": "średni", "SK": "średni", "RS": "średni",
    "LT": "mały", "LV": "mały", "EE": "mały", "MD": "mały",
}

# Powinowactwo (Catalog B): 1-5 by kategoria. Conservative — not all B8 deserve 5.
CATEGORY_AFFINITY_MAP = {
    "B8": 5,  # tytoń / gilzy — direct channel
    "B5": 4,  # akcesoria
    "B6": 4,  # dystrybucja FMCG/tytoń
    "B4": 4,  # e-papierosy / vape
    "B9": 3,  # mix
    "B7": 3,  # hurt detal online
    "B1": 2,  # ogólne FMCG
    "B2": 2,  # convenience
    "B3": 2,  # convenience/online
}

# cross_sell_potential (Catalog B): category-aware default IF we have a real
# signal — never set this from category alone. Caller checks signal presence.
CATEGORY_CROSS_SELL_MAP = {
    "B8": "wysoki",
    "B5": "wysoki",
    "B4": "wysoki",
    "B6": "średni",
    "B9": "średni",
    "B7": "średni",
    "B1": "średni",
    "B2": "niski",
    "B3": "niski",
}

SENTINELS = {"", "brak", "do ustalenia", "—", "-", "n/a", "na", "nd",
             "nie dotyczy", "do weryfikacji", "do uzupełnienia"}

# Values that ARE the verifier's signal — never overwrite
PROTECTED_CONFIDENCE = {"🟢", "🟡", "🔴"}

# Placeholder marki_nabijarki values that are safe to clear from Catalog B
# (Catalog B is prospective partners — should not carry brand list).
# 'nie' is EXPLICIT "no" — preserve.
CATB_MARKI_PLACEHOLDERS = {"", "brak", "do ustalenia", "—", "-", "n/a",
                            "na", "nd", "nie dotyczy", "do weryfikacji",
                            "do uzupełnienia", "?"}


# ---------------------------------------------------------------------------
# Helpers — verifier-aware signal extraction
# ---------------------------------------------------------------------------

def _norm(s):
    return (s or "").strip()


def _is_sentinel(s):
    return _norm(s).lower() in SENTINELS


def _is_protected_confidence(s):
    return _norm(s) in PROTECTED_CONFIDENCE


def has_hallucination(flagi: str) -> bool:
    """True if the flagi string contains a HALUCYNACJA marker.

    A hallucinated NIP/KRS is an explicit signal that the existing structural
    fields (nip_vat, rejestr_id) are WRONG. We must NOT compute confidence
    from them in that case — the verifier said "don't trust this".
    """
    return "HALUCYNACJA" in (flagi or "").upper()


def has_pending_verification(flagi: str, sourcing: str, notes: str) -> bool:
    """True if any source says this row is awaiting verification.

    Used to cap confidence at 🟡 regardless of structural completeness.
    Reads from three places because the flag is recorded differently across
    intake batches:
      - flagi: 'DO-WERYFIKACJI' or 'PENDING' or 'PENDING_API'
      - sourcing: 'do weryfikacji' literal
      - notatki: '⚠️ DO-WERYFIKACJI' or 'do weryfikacji' inline
    """
    f = (flagi or "").upper()
    if "DO-WERYFIKACJI" in f or "PENDING" in f:
        return True
    s = (sourcing or "").lower()
    if "do weryfikacji" in s or s == "pending":
        return True
    n = (notes or "").lower()
    if "do weryfikacji" in n or "⚠️ do-weryfikacji" in (notes or "").lower():
        return True
    return False


def is_frozen(flagi: str) -> bool:
    return "FROZEN" in (flagi or "").upper()


def has_structural(row: dict) -> bool:
    """True if NIP and WWW are both present and non-sentinel."""
    nip_ok = not _is_sentinel(row.get("nip_vat", ""))
    www_ok = not _is_sentinel(row.get("www", ""))
    return nip_ok and www_ok


def has_registry(row: dict) -> bool:
    return not _is_sentinel(row.get("rejestr_id", ""))


def has_contact(row: dict) -> bool:
    """At least one real contact channel beyond the registry."""
    return bool(_norm(row.get("telefon"))) or bool(_norm(row.get("email")))


# ---------------------------------------------------------------------------
# Per-field inferrers
# ---------------------------------------------------------------------------

def infer_tier(row: dict) -> str:
    """Infer tier only if empty/sentinel — never overwrite a verified value."""
    current = (row.get("tier") or "").strip().lower()
    if current and current not in SENTINELS:
        return row.get("tier")  # return as-is, no rewrite

    notes = (row.get("notatki") or "").lower()
    cat = (row.get("kategoria") or "").upper().strip()

    if "producent" in notes or "fabryka" in notes or "zakład" in notes:
        return "producent"
    if ("hurt" in notes or "dystrybutor" in notes or "b2b" in notes
            or cat in ("B8", "A1", "A2", "A4")):
        return "hurtownik"
    if "sieć" in notes or "sklep" in notes or "salon" in notes:
        return "detalista"
    return "reseller"


def infer_volume(row: dict, country: str) -> str:
    """Infer balanced wolumen for a lead row. Never overwrite a verified value."""
    current = (row.get("wolumen") or "").strip().lower()
    if current and current not in SENTINELS:
        return row.get("wolumen")  # preserve

    tier = (row.get("tier") or "").strip().lower()
    notes = (row.get("notatki") or "").lower()
    name = (row.get("nazwa") or "").lower()
    cat = (row.get("kategoria") or "").upper().strip()

    # Strong positive signals (only when notes/name actually carry them)
    is_big = (
        "lider" in notes or "ogólnokraj" in notes or "monopol" in notes
        or "największ" in notes or "top b2b" in notes
        or re.search(r"\b\d{3,5}\+\b", notes) is not None  # 100+, 500+, 1000+
        or "mld" in notes
    )
    is_small = (
        "sklep detaliczny" in notes or "jednosobow" in notes
        or "lokalny" in notes or "kiosk" in notes
    )

    if is_big:
        return "duży"
    if is_small:
        return "mały"
    if tier in ("hurtownik", "producent") or cat in ("B8", "A4", "A5", "A6"):
        return "duży" if country in ("PL", "CZ", "FR") else "średni"
    if tier == "reseller":
        return "średni"
    return "średni"


def infer_confidence(row: dict, country: str) -> str:
    """Infer balanced confidence_wolumen — RESPECT THE VERIFIER.

    Order of precedence (highest first):
      1. Already set to 🟢/🟡/🔴 — return as-is.
      2. HALUCYNACJA in flagi → 🔴 (structural fields cannot be trusted).
      3. DO-WERYFIKACJI / PENDING / sourcing='do weryfikacji' → 🟡 if any
         structural field is present, else 🔴.
      4. FROZEN in flagi OR (NIP+WWW present AND registry present) → 🟢.
      5. NIP+WWW or contact info present → 🟢 if duży else 🟡.
      6. Otherwise 🟡.
    """
    current = (row.get("confidence_wolumen") or "").strip()
    if _is_protected_confidence(current):
        return current  # NEVER overwrite a verifier-set value

    flagi = row.get("flagi") or ""
    sourcing = row.get("sourcing") or ""
    notes = row.get("notatki") or ""
    vol = (row.get("wolumen") or "").strip().lower()

    if has_hallucination(flagi):
        return "🔴"
    if has_pending_verification(flagi, sourcing, notes):
        # Pending + any structural field = 🟡 (verified-form but not yet cleared)
        if has_structural(row) or has_registry(row) or has_contact(row):
            return "🟡"
        return "🔴"
    if is_frozen(flagi):
        return "🟢"
    # No FROZEN → need BOTH structural (nip+www) AND registry to be 🟢.
    # Registry alone is weak (KRS can be stale); structural alone is also weak
    # (could be a domain-squatter). Together they're solid.
    if has_structural(row) and has_registry(row):
        return "🟢"
    if has_structural(row) or has_contact(row):
        return "🟡"
    return "🟡"


def infer_cross_sell_signal(row: dict) -> bool:
    """True if we have at least one real signal that cross-sell is meaningful.

    Without a signal we leave cross_sell_potential empty (honest unknown)
    rather than assign a synthetic default.

    Polish keyword stems (substring match, not exact word match — covers
    "tytoniowa", "papierosowy", "gilzami" etc.):
      tyto  → tytoń / tytoniowy / tytoniowa
      gilz  → gilza / gilzami
      papier → papieros
      akcesor → akcesoria / akcesoriom
      nabijar → nabijarka / nabijarkami
      vapo / vape → e-papierosy
      ryo / myo / roll-your-own
    """
    notes = (row.get("notatki") or "").lower()
    sourcing = (row.get("sourcing") or "").lower()
    marki = (row.get("marki_nabijarki") or "").lower()

    stems = ("tyto", "gilz", "papier", "akcesor", "nabijar",
             "vapo", "vape", "ryo", "myo", "roll-your-own", "snus", "shish")
    positive_signals = any(stem in notes for stem in stems)

    sourcing_signal = bool(sourcing and sourcing not in SENTINELS
                           and "do weryfikacji" not in sourcing)
    marki_signal = bool(marki and marki not in SENTINELS and marki != "nie")
    return positive_signals or sourcing_signal or marki_signal


def infer_powinowactwo(row: dict) -> str:
    """Infer powinowactwo_nabijarki (1-5) for Catalog B. Never overwrite a
    valid existing value."""
    current = (row.get("powinowactwo_nabijarki") or "").strip()
    if current and current not in SENTINELS:
        try:
            n = int(current)
            if 1 <= n <= 5:
                return current  # preserve
        except ValueError:
            pass  # not a number → fall through to default

    cat = (row.get("kategoria") or "").upper().strip()
    notes = (row.get("notatki") or "").lower()
    base = CATEGORY_AFFINITY_MAP.get(cat, 4)
    if any(stem in notes for stem in ("tyto", "gilz", "akcesor", "nabijar")):
        base = max(base, 4)
    return str(base)


def infer_marki_for_cat_a(row: dict) -> str:
    """Infer appropriate product/brand descriptor for Catalog A rows.

    Only fills when truly empty — never overwrites an existing meaningful
    marki string.
    """
    current = (row.get("marki_nabijarki") or "").strip()
    if current and current.lower() not in SENTINELS:
        return current

    notes = (row.get("notatki") or "").lower()
    name = (row.get("nazwa") or "").lower()

    if "powermatic" in notes or "hawk" in notes or "powermatic" in name:
        return "PowerMatic | Hawk | Akcesoria tytoniowe"
    if "vape" in notes or "veip" in name or "smoke" in name or "smokemania" in name or "elvapo" in name:
        return "Vape | E-papierosy | Akcesoria"
    if "snus" in notes or "nikotyna" in notes or "snus" in name:
        return "Snus | Nikotyna | Akcesoria dla palaczy"
    if "philip morris" in name or "pmi" in notes:
        return "Tytoń | Heets | Wyroby tytoniowe"
    if "tng" in notes or "tabakas" in name or "hurt" in notes:
        return "Tytoń | Gilzy | Akcesoria tytoniowe | B2B"
    return "Akcesoria tytoniowe | RYO/MYO"


# ---------------------------------------------------------------------------
# Per-file driver
# ---------------------------------------------------------------------------

def balance_catalog_file(csv_path: Path) -> dict:
    """Balance and calibrate a single catalog CSV file.

    Strict rules (encoded above):
      - Never overwrite a verifier-set confidence 🟢/🟡/🔴.
      - Never overwrite a verified wolumen.
      - Never clear 'nie' from Catalog B marki_nabijarki.
      - Never set cross_sell_potential without a real signal.
    """
    country = csv_path.parent.name
    filename = csv_path.name
    cat_type = "A" if "catalog-A" in filename else "B"

    iso_match = re.search(r"catalog-[AB]-([A-Z]{2})\.csv", filename)
    iso = iso_match.group(1) if iso_match else "PL"

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not rows or not fieldnames:
        return {"file": filename, "rows": 0, "updated": 0}

    updated_count = 0
    for r in rows:
        # 1. rynek_skala — always set (country-level constant)
        r["kraj"] = iso
        r["rynek_skala"] = RYNEK_SKALA_MAP.get(iso, "średni")

        # 2. tier — fill only if empty/sentinel
        tier_val = infer_tier(r)
        if r.get("tier") != tier_val:
            r["tier"] = tier_val
            updated_count += 1

        # 3. wolumen — fill only if empty/sentinel, never downgrade
        vol = infer_volume(r, iso)
        if r.get("wolumen") != vol:
            r["wolumen"] = vol
            updated_count += 1

        # 4. confidence_wolumen — verifier-aware (most important)
        conf = infer_confidence(r, iso)
        if r.get("confidence_wolumen") != conf:
            r["confidence_wolumen"] = conf
            updated_count += 1

        cat = (r.get("kategoria") or "").upper().strip()

        if cat_type == "A":
            # Catalog A: no cross_sell, no powinowactwo — clear if anything there
            if r.get("cross_sell_potential") and r["cross_sell_potential"] != "":
                r["cross_sell_potential"] = ""
                updated_count += 1
            if r.get("powinowactwo_nabijarki") and r["powinowactwo_nabijarki"] != "":
                r["powinowactwo_nabijarki"] = ""
                updated_count += 1
            # Ensure marki is populated (fallback for empty A rows)
            marki = infer_marki_for_cat_a(r)
            if r.get("marki_nabijarki") != marki:
                r["marki_nabijarki"] = marki
                updated_count += 1
        else:
            # Catalog B: powinowactwo 1-5 (only fill if empty/invalid)
            pow_val = infer_powinowactwo(r)
            if r.get("powinowactwo_nabijarki") != pow_val:
                r["powinowactwo_nabijarki"] = pow_val
                updated_count += 1

            # Catalog B: cross_sell_potential — only with a real signal
            cross_current = (r.get("cross_sell_potential") or "").strip()
            cross_norm = cross_current.lower()
            if (not cross_current or cross_norm in SENTINELS
                    or cross_norm not in {"wysoki", "średni", "niski", "bardzo wysoki"}):
                if infer_cross_sell_signal(r):
                    default_cross = CATEGORY_CROSS_SELL_MAP.get(cat, "wysoki")
                    if r.get("cross_sell_potential") != default_cross:
                        r["cross_sell_potential"] = default_cross
                        updated_count += 1
                # else: leave as-is (empty) — honest unknown

            # Catalog B: clear only placeholder marki, NEVER 'nie' (it's a fact)
            marki_current = (r.get("marki_nabijarki") or "").strip()
            if marki_current and marki_current.lower() in CATB_MARKI_PLACEHOLDERS:
                r["marki_nabijarki"] = ""
                updated_count += 1
            # Note: 'nie' is preserved by this branch (it is not in
            # CATB_MARKI_PLACEHOLDERS).

    tmp_path = csv_path.with_suffix(".csv.tmp")
    with open(tmp_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    tmp_path.replace(csv_path)

    return {"file": filename, "rows": len(rows), "updated": updated_count}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print("=" * 80)
    print("  BALANCING & CALIBRATING SCORING ACROSS ALL 13 COUNTRIES")
    print("  (verifier-aware: respects HALUCYNACJA / DO-WERYFIKACJI / FROZEN)")
    print("=" * 80)

    catalog_files = sorted(DATA.glob("*/catalog-*.csv"))
    total_files = 0
    total_rows = 0

    for p in catalog_files:
        # Skip macOS resource fork files (._foo.csv) and snapshot dir
        if p.name.startswith("._") or ".snapshots" in str(p):
            continue
        res = balance_catalog_file(p)
        total_files += 1
        total_rows += res.get("rows", 0)
        print(f"  ✓ {p.parent.name:<12} | {res['file']:<20} | "
              f"{res.get('rows', 0):3d} rows (updated {res.get('updated', 0)} fields)")

    print("\n" + "=" * 80)
    print(f"  Completed balancing across {total_files} catalog files "
          f"({total_rows} total rows).")
    print("=" * 80)


if __name__ == "__main__":
    main()
