#!/usr/bin/env python3
"""
verify_api.py — Live registry verification for BILLSzuka rows.

For each row with a NIP, calls the appropriate registry API and updates
the row's flagi/status based on whether the API confirms the firm details.

Supported registries:
  PL: CEIDG v3 (https://dane.biznes.gov.pl/api/ceidg/v3/firmy)
      — needs CEIDG_API_TOKEN from .env
  CZ: ARES (https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ICO})
      — no auth

Other countries: stub (returns None; verify_run.py will mark as DO-WERYFIKACJI).

Usage:
  python3 tools/verify_api.py --country PL
  python3 tools/verify_api.py --all

Env: reads .env for CEIDG_API_TOKEN.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/legacy"))

# Sibling & legacy registry modules
try:
    from vies_verify import vies_lookup
except ImportError:  # pragma: no cover
    vies_lookup = None  # type: ignore[assignment]

try:
    from fr_recherche import fr_search
except ImportError:  # pragma: no cover
    fr_search = None  # type: ignore[assignment]

try:
    # Optional Apollo.io company enricher (FREE plan only — no people/match).
    # Used as a fallback for non-EU countries (e.g. MD) or to back-fill
    # company-level fields (industry, employees, linkedin) the country
    # registries don't provide. Created 2026-08-10 in parallel with auto_enrich.
    from apollo_enrich import enrich_csv_row as _apollo_enrich_row
    APOLLO_AVAILABLE = True
except ImportError:  # pragma: no cover
    _apollo_enrich_row = None  # type: ignore[assignment]
    APOLLO_AVAILABLE = False

try:
    from ee_ariregister import ee_search, ee_detail
except ImportError:  # pragma: no cover
    ee_search = None  # type: ignore[assignment]
    ee_detail = None  # type: ignore[assignment]

try:
    from lt_open_data import lt_jar_lookup, lt_jar_resolve_forma_status
except ImportError:  # pragma: no cover
    lt_jar_lookup = None  # type: ignore[assignment]
    lt_jar_resolve_forma_status = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ENV_FILE = ROOT / ".env"

CEIDG_BASE = "https://dane.biznes.gov.pl/api/ceidg/v3/firmy"
ARES_BASE = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty"

# EU member states (27). Used to route rows through VIES for VAT validation
# as a fast first-pass when no country-specific registry is implemented.
# Source: https://ec.europa.eu/taxation_customs/vies/
EU_MEMBER_STATES: frozenset[str] = frozenset({
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK",
})

# Status flag for countries we have NO integration for (currently: only
# non-EU markets like MD). Distinct from DO-WERYFIKACJI which means
# "we tried to verify and something looks off".
PENDING_API = "PENDING_API"
KRS_BASE = "https://api-krs.ms.gov.pl/api/krs/OdpisAktualny"


def log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def load_env() -> dict:
    env = {}
    if not ENV_FILE.exists():
        return env
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def krs_lookup(krs: str) -> dict | None:
    """Query KRS API by KRS number. Returns firm record dict or None.
    KRS is for sp. z o.o. and other legal entities; CEIDG is for JDG (sole proprietors).
    """
    krs_clean = re.sub(r"\D", "", krs)
    if not re.match(r"^\d{10}$", krs_clean):
        krs_clean = krs_clean.zfill(10)
    url = f"{KRS_BASE}/{krs_clean}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
        odpis = data.get("odpis", {})
        dane = odpis.get("dane", {})
        if not dane:
            return {"error": "KRS: pusta odpowiedź"}
        d1 = dane.get("dzial1", {})
        dp = d1.get("danePodmiotu", {})
        ident = dp.get("identyfikatory", {})
        siedziba = d1.get("siedzibaIAdres", {})
        adres = siedziba.get("adres", {})
        return {
            "nazwa": dp.get("nazwa", ""),
            "nip": ident.get("nip", ""),
            "regon": ident.get("regon", ""),
            "adres": " ".join(filter(None, [
                adres.get("kodPocztowy", ""),
                adres.get("miejscowosc", ""),
                adres.get("ulica", ""),
                adres.get("nrDomu", ""),
            ])),
            "forma_prawna": dp.get("formaPrawna", ""),
            "data_rejestracji": odpis.get("naglowekA", {}).get("dataRejestracjiWKRS", ""),
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": "KRS: nie znaleziono"}
        return {"error": f"KRS HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": f"KRS request failed: {e}"}


def ceidg_lookup(nip: str, token: str) -> dict | None:
    """Query CEIDG v3 by NIP. Returns firm record dict or None."""
    nip_clean = re.sub(r"^[A-Z]{2}", "", nip).strip()
    if not re.match(r"^\d{10}$", nip_clean):
        return {"error": f"NIP PL nieprawidłowy: {nip}"}
    url = f"{CEIDG_BASE}?nip={nip_clean}&status=AKTYWNY"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        firms = data.get("firmy", [])
        if not firms:
            return {"error": "Brak aktywnej firmy dla tego NIP"}
        firm = firms[0]
        adres = firm.get("adresDzialalnosci", {}) or firm.get("adresKorespondencyjny", {}) or {}
        wlasciciel = firm.get("wlasciciel", {}) or {}
        return {
            "nazwa": firm.get("nazwa", ""),
            "nip": wlasciciel.get("nip", "") or firm.get("nip", ""),
            "regon": wlasciciel.get("regon", "") or firm.get("regon", ""),
            "adres": " ".join(filter(None, [
                adres.get("kod", ""),
                adres.get("miasto", ""),
                adres.get("ulica", ""),
                adres.get("budynek", ""),
            ])),
            "status": firm.get("status", ""),
            "pkd": "",
        }
    except urllib.error.HTTPError as e:
        # Try to read CEIDG error body for actionable message (BUG FIX 2026-08-31)
        try:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
                err_code = err_json.get("code", "")
                err_msg = err_json.get("message", err_body[:100])
                if err_code == "NIEPOPRAWNY_NUMER_NIP":
                    return {"error": f"CEIDG: NIP mod-11 invalid (HALUCYNACJA?): {nip}"}
                return {"error": f"CEIDG {e.code} [{err_code}]: {err_msg}"}
            except json.JSONDecodeError:
                return {"error": f"CEIDG HTTP {e.code}: {e.reason} (body: {err_body[:80]})"}
        except Exception:
            return {"error": f"CEIDG HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": f"Request failed: {e}"}


def ares_lookup(ico: str) -> dict | None:
    """Query ARES by IČO. Returns firm record dict or None.

    ARES v3 API returns camelCase keys (obchodniJmeno, ico, sidlo, ...)
    v2 returned PascalCase (ObchodniJmeno, ICO, Sidlo, ...) — we support both.
    """
    ico_clean = re.sub(r"^[A-Z]{2}", "", ico).strip()
    if not re.match(r"^\d{8}$", ico_clean):
        return {"error": f"IČO CZ nieprawidłowe: {ico}"}
    url = f"{ARES_BASE}/{ico_clean}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
        # Normalize keys — try lowercase first (v3), then PascalCase (v2)
        if "obchodniJmeno" in data:
            sidlo = data.get("sidlo", {})
            return {
                "nazwa": data.get("obchodniJmeno", ""),
                "ico": data.get("ico", ""),
                "dic": data.get("dic", ""),
                "adres": f"{sidlo.get('nazevObce', '')}, {sidlo.get('nazevUlice', '')} {sidlo.get('cisloPopisne', '')}",
                "pravni_forma": data.get("pravniForma", ""),
                "datum_vzniku": data.get("datumVzniku", ""),
            }
        if "ObchodniJmeno" in data:
            sidlo = data.get("Sidlo", {})
            return {
                "nazwa": data.get("ObchodniJmeno", ""),
                "ico": data.get("ICO", ""),
                "dic": data.get("DIC", ""),
                "adres": f"{sidlo.get('NazevObce', '')}, {sidlo.get('NazevUlice', '')} {sidlo.get('CisloPopisne', '')}",
                "pravni_forma": data.get("PravniForma", ""),
                "datum_vzniku": data.get("DatumVzniku", ""),
            }
        return {"error": "Brak firmy dla tego IČO"}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": "IČO nie istnieje w ARES"}
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": f"Request failed: {e}"}


def ares_search(name: str) -> dict | None:
    """Query ARES by company name. Returns top match dict or None.

    Uses POST /ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat.
    Returns same shape as ares_lookup() but fetched from a name search.
    """
    if not name or len(name) < 2:
        return {"error": "Nazwa za krótka"}
    url = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = json.dumps({"obchodniJmeno": name}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        subs = data.get("ekonomickeSubjekty", [])
        if not subs:
            return None  # brak wyników
        s = subs[0]
        sidlo = s.get("sidlo", {})
        return {
            "nazwa": s.get("obchodniJmeno", ""),
            "ico": s.get("ico", ""),
            "adres": sidlo.get("textovaAdresa", ""),
            "kod_obce": sidlo.get("kodObce", ""),
            "pocet_vysledku": data.get("pocetCelkem", 0),
        }
    except Exception as e:
        return {"error": f"ARES search failed: {e}"}


def ares_enrich(row: dict) -> tuple[str, str]:
    """For a CZ row missing IČO — try ARES search by name.

    Returns (status, reason) like other verify functions.
    Updates the row dict in-place if found.
    """
    name = (row.get("nazwa_firmy") or "").strip()
    if not name:
        return "DO-WERYFIKACJI", "Brak nazwy"
    # Wyczyść nazwę
    clean = name
    for suf in [" s.r.o.", " a.s.", " k.s.", " v.o.s."]:
        clean = clean.replace(suf, "")
    clean = clean.split("(")[0].strip()
    if not clean:
        return "DO-WERYFIKACJI", "Nazwa nie do przetworzenia"

    res = ares_search(clean)
    if not res:
        # Próba z pierwszym słowem
        first = clean.split()[0] if clean else ""
        if first and first != clean:
            res = ares_search(first)
    if not res:
        return "DO-WERYFIKACJI", f"ARES: brak firmy dla '{clean[:30]}'"
    if "error" in res:
        return "DO-WERYFIKACJI", res["error"]
    if res.get("ico"):
        row["nip_vat"] = res["ico"]
        row["rejestr_id"] = f"ARES IČO {res['ico']}"
        if res.get("adres") and (not row.get("adres") or "do ustalenia" in row.get("adres", "").lower() or "do weryfikacji" in row.get("adres", "").lower()):
            row["adres"] = res["adres"]
        # zrodlo update
        existing = row.get("zrodlo_danych", "")
        if "ARES" not in existing:
            row["zrodlo_danych"] = f"ARES API (search by name) + web search 2026-08-10"
        row["data_weryfikacji"] = "2026-08-10"
        return "FROZEN", f"ARES name search: {res['nazwa']} (IČO {res['ico']})"
    return "DO-WERYFIKACJI", "ARES: brak IČO"


def normalize(s: str, loose: bool = False) -> str:
    """Normalize a name for fuzzy comparison.

    Args:
        s: input string (e.g. "BILLS SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ")
        loose: if True, also strip diacritics (Ą→A, Ę→E, etc.) for tolerance
               to typos like "ODPOWIEDZIALNOŚCIA" vs "ODPOWIEDZIALNOŚCIĄ".
               Default False to keep strict comparison for KRIS name lookups.

    For loose mode (recommended for Jaccard comparison), legal form stripping
    is done with regex patterns that tolerate spacing/nasal-mark variations.
    """
    if not s:
        return ""
    s = s.upper()
    # Strip diacritics first if loose mode
    if loose:
        diacritics = str.maketrans("ĄĆĘŁŃÓŚŹŻ", "ACEENOSZZ")
        s = s.translate(diacritics)

    # Strip legal form suffixes. In loose mode, use regex to tolerate
    # variations (spacing, missing nasal marks). Exact list still works
    # for the common case.
    # IMPORTANT: in loose mode the regex patterns use diacritic-STRIPPED
    # forms (e.g. "ODPOWIEDZIALNOSCI" not "ODPOWIEDZIALNOŚCI") because
    # we already stripped diacritics above; otherwise the Polish chars
    # in the regex wouldn't match the stripped input.
    if loose:
        s = re.sub(r"SPOEKA\s+Z\s+OGRANICZON[ĄA]\s+ODPOWIEDZIALNOSCI[ĄA]", " ", s)
        s = re.sub(r"SP\.?\s*Z\.?\s*O\.?\s*O\.?", " ", s)
        s = re.sub(r"SPOL\.?\s*S\.?\s*R\.?\s*O\.?", " ", s)
        s = re.sub(r"AKCIOV[ÁA]?.?\s*SPOLE[ČC]?.?NOST", " ", s)
        s = re.sub(r"SP[ÓO]ŁKA\s+CYWILNA", " ", s)
        s = re.sub(r"SP[ÓO]ŁKA\s+JAWNA", " ", s)
        s = re.sub(r"S\.?R\.?O\.?", " ", s)
        s = re.sub(r"A\.?S\.?", " ", s)
        s = re.sub(r"S\.?C\.?", " ", s)
        s = re.sub(r"SP\.?J\.?", " ", s)
        s = re.sub(r"F\.?H\.?U\.?", " ", s)
    else:
        for suf in ["SP. Z O.O.", "SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
                    "S.R.O.", "SPOL. S R.O.", "SPOL. S R. O.",
                    "A.S.", "AKCIOVÁ SPOLEČNOST", "S.C.", "SP.J.",
                    "SPÓŁKA CYWILNA", "SPÓŁKA JAWNA", "F.H.U.",
                    "SP.J.", "SP. J."]:
            s = s.replace(suf, "")
    # strip punctuation
    s = re.sub(r"[^A-Z0-9ĄĆĘŁŃÓŚŹŻ]+", " ", s)
    return " ".join(s.split())


# Legal-form tokens stripped before Jaccard comparison.
# They appear in both CSV and API names so they would inflate the
# intersection and mask real mismatches (e.g. "PEAL" vs "PEAL Real Estate"
# shares only "PEAL" — Jaccard 1/3, not 1.0).
LEGAL_TOKENS = {"SP", "ZOO", "OO", "SRO", "AS", "SC", "SPJ", "FHU",
                "SPOL", "POL", "KOM", "SA", "AG", "GMBH"}

# Jaccard threshold for name match. 0.8 = require ~80% token overlap.
# Below this, names are considered different entities (FABRYKAT risk).
NAME_JACCARD_THRESHOLD = 0.8


def name_similarity(csv_name: str, api_name: str) -> tuple[bool, float, str]:
    """Token Jaccard similarity. Returns (is_match, score, reason).

    Strips legal-form tokens first (they always match and would inflate
    the score, hiding real mismatches like "PEAL" vs "PEAL Real Estate").

    Uses LOOSE normalization (diacritics + regex-based legal-form strip) to
    tolerate CSV typos like "ODPOWIEDZIALNOŚCIA" vs the registry's
    "ODPOWIEDZIALNOŚCIĄ". Without loose mode, BILLS / BISTA / E-TABAK /
    CK COMPLEX would all be false-positive DO-W.

    Threshold 0.8 catches the FABRYKAT pattern: LLM-generated identifiers
    pass checksum but point to entities sharing only a common prefix word
    with the claimed company.
    """
    c = normalize(csv_name, loose=True)
    a = normalize(api_name, loose=True)
    if not c or not a:
        return False, 0.0, f"empty name (csv='{c[:20]}' api='{a[:20]}')"
    c_tokens = set(c.split()) - LEGAL_TOKENS
    a_tokens = set(a.split()) - LEGAL_TOKENS
    if not c_tokens and not a_tokens:
        return False, 0.0, "no tokens after legal-form strip"
    intersection = c_tokens & a_tokens
    union = c_tokens | a_tokens
    jaccard = len(intersection) / len(union) if union else 0.0
    is_match = jaccard >= NAME_JACCARD_THRESHOLD
    reason = (f"jaccard={jaccard:.2f} ({len(intersection)}/{len(union)} tokens, "
              f"csv='{c[:30]}' api='{a[:30]}')")
    return is_match, jaccard, reason


def verify_pl_row(row: dict, token: str) -> tuple[str, str]:
    """Verify PL row per Zasady §1: kolejność = checksum → API → fuzzy match → FROZEN.

    Bug fix 2026-08-31: previously, this function trusted CSV NIP without
    mod-11 checksum and trusted rejestr_id KRS without live API cross-check.
    Now we follow the documented order strictly:
      1. PL NIP mod-11 (offline, before any API)
      2. KRS live lookup if rejestr_id has KRS — cross-check NIP
      3. CEIDG lookup for JDG/sp. cywilne
      4. Fuzzy match NIP + name
      5. FROZEN only if all 3 conditions met (per §5)
    """
    from verify_principles import is_valid_pl_nip, INVALID_CHECKSUM, INVALID_ID, MISMATCH_REGISTRY, FROZEN

    nip = (row.get("nip_vat") or "").strip()
    rejestr = (row.get("rejestr_id") or "").strip()
    csv_nazwa_raw = row.get("nazwa_firmy", "")

    # === Pre-flight 1: PL NIP mod-11 (offline, before any API call) ===
    # Per §1.1 — checksum fail means guaranteed hallucination. Don't even
    # call KRS/CEIDG; flag INVALID_CHECKSUM immediately.
    nip_digits = re.sub(r"\D", "", nip)
    if nip_digits:
        valid, code = is_valid_pl_nip(nip)
        if not valid and code == INVALID_CHECKSUM:
            return "DO-WERYFIKACJI", f"{INVALID_CHECKSUM}: PL NIP {nip_digits} mod-11 invalid (HALUCYNACJA?)"
        if not valid and code == "INVALID_FORMAT":
            return "DO-WERYFIKACJI", f"{INVALID_ID}: PL NIP {nip} format invalid"

    # === Pre-flight 2: KRS lookup (if rejestr_id has KRS) ===
    krs_match = re.search(r"KRS\s*(\d+)", rejestr, re.IGNORECASE)
    if krs_match:
        krs = krs_match.group(1)
        result = krs_lookup(krs)
        if result and "error" not in result:
            # KRS exists. Now cross-check NIP from KRS vs CSV NIP.
            krs_nip = re.sub(r"\D", "", result.get("nip", ""))
            if krs_nip and nip_digits and krs_nip != nip_digits:
                return "DO-WERYFIKACJI", (
                    f"{MISMATCH_REGISTRY}: KRS {krs} → API NIP {krs_nip} "
                    f"({result.get('nazwa','')[:30]}) ≠ CSV NIP {nip_digits} "
                    f"({csv_nazwa_raw[:30]})"
                )
            # Cross-check name (KRS nazwa vs CSV)
            ok, score, reason = name_similarity(csv_nazwa_raw, result.get("nazwa", ""))
            if not ok:
                return "DO-WERYFIKACJI", f"{MISMATCH_REGISTRY}: KRS nazwa mismatch ({reason})"
            # All 3 conditions met (per §5)
            return FROZEN, f"KRS live: {result.get('nazwa', '')[:40]} (REGON {result.get('regon', '')}, jaccard={score:.2f})"
        else:
            err = result.get("error", "brak") if result else "brak"
            # Per §1.3: KRS 404 = INVALID_ID (not "brak danych")
            if "404" in err or "nie znaleziono" in err:
                return "DO-WERYFIKACJI", f"{INVALID_ID}: KRS {krs} nie istnieje w rejestrze"
            return "DO-WERYFIKACJI", f"DO-WERYFIKACJI: KRS({krs}): {err}"

    # === Fall back to CEIDG (for JDG / sole proprietors) ===
    if not nip:
        return "DO-WERYFIKACJI", "Brak nip_vat i brak KRS"
    result = ceidg_lookup(nip, token)
    if not result or "error" in result:
        err = result.get("error", "brak") if result else "brak"
        # Per §1.2: CEIDG 400 NIEPOPRAWNY_NUMER_NIP = INVALID_ID
        if "NIEPOPRAWNY" in err or "mod-11 invalid" in err or "400" in err:
            return "DO-WERYFIKACJI", f"{INVALID_ID}: CEIDG {err}"
        # CEIDG timeout / 401 = PENDING_API (we'll retry)
        if "401" in err or "Request failed" in err:
            return PENDING_API, f"CEIDG: {err}"
        return "DO-WERYFIKACJI", f"CEIDG: {err}"

    # CEIDG returns "imie nazwisko" for JDG — looser check: at least one key token from CSV must appear in API
    csv_nazwa = normalize(csv_nazwa_raw)
    api_nazwa = normalize(result.get("nazwa", ""))
    if csv_nazwa and api_nazwa:
        csv_tokens = set(csv_nazwa.split())
        api_tokens = set(api_nazwa.split())
        # Drop common legal-form words
        legal = {"SP", "ZOO", "OO", "SRO", "AS", "SC", "SPJ", "FHU"}
        csv_tokens -= legal
        # Check that NIP/REGON match (more reliable than name for JDG)
        api_nip_clean = re.sub(r"\D", "", result.get("nip", ""))
        csv_nip_clean = re.sub(r"\D", "", nip)
        nip_ok = api_nip_clean and csv_nip_clean and api_nip_clean == csv_nip_clean
        # If NIP matches, accept (name is "imie nazwisko" which won't match firm name)
        if not nip_ok:
            # Fall back to token check
            if not csv_tokens or not (csv_tokens & api_tokens):
                return "DO-WERYFIKACJI", f"{MISMATCH_REGISTRY}: CEIDG ani NIP ani nazwa nie pasują (CSV='{csv_nazwa[:30]}' API='{api_nazwa[:30]}')"

    return FROZEN, f"CEIDG live: {result.get('nazwa', '')[:40]} (REGON {result.get('regon', '')})"


def verify_cz_row(row: dict) -> tuple[str, str]:
    """Verify CZ row via ARES. Falls back to name search if IČO missing.
    Per Zasady: format -> API -> fuzzy match -> FROZEN.
    """
    from verify_principles import is_valid_cz_ico, MISMATCH_REGISTRY, FROZEN

    nip = (row.get("nip_vat") or "").strip()
    # If IČO missing or "do weryfikacji" - try name search
    if not nip or nip in ("do weryfikacji", "brak", "brak danych"):
        return ares_enrich(row)

    # Pre-flight: CZ IČO = 8 cyfr (no public checksum; ARES does internal validation)
    ico = re.sub(r"\D", "", nip)
    valid, code = is_valid_cz_ico(ico)
    if not valid:
        return "DO-WERYFIKACJI", f"INVALID_ID: CZ IČO {nip} format invalid"

    result = ares_lookup(ico)
    if not result or "error" in result:
        err = result.get("error", "brak") if result else "brak"
        return "DO-WERYFIKACJI", f"ARES: {err}"

    csv_nazwa = row.get("nazwa_firmy", "")
    api_nazwa = result.get("nazwa", "")
    ok, score, reason = name_similarity(csv_nazwa, api_nazwa)
    if not ok:
        return "DO-WERYFIKACJI", f"{MISMATCH_REGISTRY}: ARES nazwa mismatch ({reason})"

    return FROZEN, f"ARES live: {api_nazwa[:40]} (od {result.get('datum_vzniku', '?')})"


def verify_vies_row(row: dict) -> tuple[str, str]:
    """
    Verify any EU-country row via VIES VAT validation.

    VIES (VAT Information Exchange System) is the EU's official VAT
    validation service. Public, free, no auth. Covers all 27 EU member
    states. Catches:
      - VAT ID is active in EU registry (=> FROZEN)
      - VAT ID is malformed or doesn't exist (=> DO-WERYFIKACJI)
      - VIES is unreachable (=> PENDING_API, distinct from errors)

    Note: VIES does NOT return the company name in most cases (member
    states' privacy laws differ). So we can only confirm VAT existence,
    not match against CSV `nazwa_firmy`. This is still strong evidence:
    a confirmed EU VAT ID is much harder to fabricate than a name string.
    """
    if vies_lookup is None:
        return PENDING_API, "VIES module niedostępny (vies_verify.py nie załadowany)"

    nip = (row.get("nip_vat") or "").strip()
    if not nip or nip in ("do weryfikacji", "brak", "brak danych", "do ustalenia"):
        return PENDING_API, "Brak VAT ID — VIES nie ma czego sprawdzać"

    result = vies_lookup(nip)
    if not result:
        return PENDING_API, "VIES: brak odpowiedzi (timeout / network)"

    if result.get("error"):
        # VIES gives specific errors. "Nieaktywny" = VAT exists but
        # deregistered. "Niepoprawny format" = clearly bad data.
        err = result["error"]
        if "niepoprawny format" in err.lower() or "nieaktywny" in err.lower():
            return "DO-WERYFIKACJI", f"VIES: {err}"
        # Other errors (404, HTTP 5xx) = transient, mark as pending
        return PENDING_API, f"VIES: {err}"

    if result.get("valid"):
        name = result.get("name", "").strip() or "(brak nazwy w VIES)"
        return "FROZEN", f"VIES live: {name[:40]} ({nip})"

    return "DO-WERYFIKACJI", f"VIES: VAT {nip} nieaktywny"


# French legal-form tokens to strip before fuzzy name match
_FR_LEGAL_TOKENS = {"SA", "SARL", "SAS", "SCI", "SCA", "SCS", "EURL", "EI"}


def verify_fr_row(row: dict) -> tuple[str, str]:
    """
    Verify FR row via recherche-entreprises.api.gouv.fr (SIREN lookup).

    The French government's official open-data API. No auth. Returns rich
    data: name, full address, creation date, dirigeants, NAF code, and
    etat_administratif (active/closed). Much stronger than VIES because
    we get the company name back, not just VAT validity.

    `nip_vat` field is expected to contain a SIREN (9 digits) or SIRET
    (14 digits), with or without the "FR" prefix.
    """
    if fr_search is None:
        return PENDING_API, "FR module niedostępny (fr_recherche.py nie załadowany)"

    nip = (row.get("nip_vat") or "").strip()
    rejestr = (row.get("rejestr_id") or "").strip()
    m_siren = re.search(r"\b\d{9}\b", rejestr)
    if m_siren:
        clean_id = m_siren.group(0)
    else:
        digits = re.sub(r"[^0-9]", "", nip)
        if len(digits) == 11:
            clean_id = digits[2:]
        elif len(digits) >= 9:
            clean_id = digits[-9:]
        else:
            clean_id = digits

    if not clean_id:
        return PENDING_API, "Brak SIREN/SIRET — Recherche Entreprises nie ma czego sprawdzać"

    result = fr_search(clean_id)
    if not result or not result.get("found"):
        # Fall back to VIES if VAT is valid
        vies_res = verify_vies_row(row)
        if vies_res[0] == "FROZEN":
            return vies_res
        err = (result or {}).get("error", "brak odpowiedzi")
        if "brak wyników" in err.lower():
            return "DO-WERYFIKACJI", f"FR: SIREN {clean_id[:9]} nie istnieje w rejestrze"
        return PENDING_API, f"FR: {err}"

    # Check active/closed status
    if result.get("etat_administratif") == "F":
        return "DO-WERYFIKACJI", (
            f"FR: firma zamknięta (SIREN {result.get('siren')}, "
            f"zamknięcie {result.get('date_fermeture', '?')})"
        )

    # Fuzzy name match: strip French legal forms, check token overlap
    csv_nazwa = normalize(row.get("nazwa_firmy", ""))
    api_nazwa = normalize(result.get("nom_complet", ""))
    if csv_nazwa and api_nazwa:
        csv_tokens = set(csv_nazwa.split()) - _FR_LEGAL_TOKENS
        api_tokens = set(api_nazwa.split()) - _FR_LEGAL_TOKENS
        # Drop very short tokens (< 3 chars) to avoid noise
        csv_tokens = {t for t in csv_tokens if len(t) >= 3}
        api_tokens = {t for t in api_tokens if len(t) >= 3}
        if csv_tokens and api_tokens and not (csv_tokens & api_tokens):
            return "DO-WERYFIKACJI", (
                f"FR: nom mismatch (CSV='{csv_nazwa[:30]}' API='{api_nazwa[:30]}')"
            )

    dirigeants_str = (
        f", dirigeants: {', '.join(result['dirigeants'][:2])}"
        if result.get("dirigeants") else ""
    )
    return "FROZEN", (
        f"FR live: {result.get('nom_complet', '')[:35]} "
        f"(SIREN {result.get('siren')}, fondé {result.get('date_creation', '?')})"
        f"{dirigeants_str}"
    )


def verify_apollo_row(row: dict) -> tuple[str, str]:
    """
    Verify a row via Apollo.io org enrich (FREE plan compatible).

    Apollo's FREE plan supports organizations/enrich (company size,
    industry, social, phone) but NOT people/match (decision-maker emails).
    This complements country-specific registries by back-filling company-
    level fields they don't provide (industry, employees, website phone).

    Used as a second-pass fallback for non-EU countries or to enrich
    fields like employees/industry that KRS/ARES don't return.

    Status semantics:
      • FROZEN          — company matched, fields updated
      • PENDING_API     — Apollo key missing, network error, or no match
      • DO-WERYFIKACJI  — matched but name mismatch (very rare for org enrich)
    """
    if not APOLLO_AVAILABLE or _apollo_enrich_row is None:
        return PENDING_API, "Apollo module niedostępny (apollo_enrich.py nie załadowany)"

    company = (row.get("nazwa_firmy") or "").strip()
    if not company or company in ("brak", "do ustalenia", "n/a", ""):
        return PENDING_API, "Brak nazwy firmy — Apollo nie ma czego szukać"

    try:
        result = _apollo_enrich_row(row)
    except (urllib.error.URLError, KeyError, TimeoutError, OSError) as e:
        return PENDING_API, f"Apollo: {type(e).__name__}: {e}"

    # FREE plan: org_matched=True, matched=False (no people/match scope).
    # PAID plan: both can be True. Treat org_matched as the success signal
    # (people match is a bonus, not a requirement).
    org_matched_check = bool(result.get("org_matched"))
    people_matched_check = bool(result.get("matched"))
    if not org_matched_check and not people_matched_check:
        err = (result.get("org_error") or result.get("error")
               or "brak dopasowania")
        if "no match" in str(err).lower() or "not found" in str(err).lower():
            return "DO-WERYFIKACJI", f"Apollo: {err}"
        return PENDING_API, f"Apollo: {err}"

    # Back-fill company-level fields (NOT decision-maker — that needs paid plan)
    filled = []
    field_map = {
        "industry": "kanal_sprzedaży",  # closest existing column
        "employees": None,  # no existing column, skip
        "phone": "telefon",
        "linkedin": "linkedin",
    }
    # Note: apollo_enrich.enrich_csv_row does NOT mutate `row` in place —
    # it returns a result dict. We collect the back-fillable fields into
    # the module-level `apollo_enrichments` dict (same pattern as EE/LT
    # enrichment), then `apply_apollo_enrichments()` writes them to the
    # CSV in a single atomic pass per file (after the main loop).
    id_ = (row.get("id_unikalne") or "").strip()
    org_matched = bool(result.get("org_matched"))
    people_matched = bool(result.get("matched"))

    if org_matched and id_:
        apollo_enrichments[id_] = {
            "telefon": (result.get("phone") or "").strip(),
            "linkedin": (result.get("linkedin") or "").strip(),
            "miasto": (result.get("city") or "").strip(),
        }
        if result.get("decydent_email"):
            apollo_enrichments[id_]["email_decydent"] = (
                result.get("decydent_email") or ""
            ).strip()
        if result.get("decydent_linkedin"):
            apollo_enrichments[id_]["linkedin"] = (
                result.get("decydent_linkedin") or ""
            ).strip()
    elif people_matched and id_:
        # Paid plan path: people/match only, no org match
        apollo_enrichments[id_] = {
            "telefon": (result.get("decydent_phone") or "").strip(),
            "linkedin": (result.get("decydent_linkedin") or "").strip(),
        }
        if result.get("decydent_email"):
            apollo_enrichments[id_]["email_decydent"] = (
                result.get("decydent_email") or ""
            ).strip()

    who = "people match" if people_matched else "org enrich"
    return "FROZEN", (
        f"Apollo {who}: {result.get('company', company)[:40]} "
        f"(domain: {result.get('domain', '?')})"
    )


# Estonian legal-form tokens (stripped before name-match Jaccard)
_EE_LEGAL_TOKENS = {
    "OÜ", "AS", "FIE", "MTÜ", "SA", "TÜH", "ÜH", "UÜ",
}


def verify_ee_row(row: dict) -> tuple[str, str]:
    """
    Verify EE row via e-Äriregister (ariregister.rik.ee).

    Two-step lookup:
      1. If `rejestr_id` is a known reg_code (e-Äriregister NNNNNNNN, 7-8
         digits) → fetch detail page directly.
      2. Otherwise (or as a fallback) → search by company name via the
         JSON autocomplete API. The first result is the most relevant.

    The autocomplete API does NOT support lookup by VAT (q=EE101376895
    returns []), so we always need a name hint. The `nip_vat` field is
    validated separately via VIES in the dispatcher fallback.

    Returns:
      FROZEN  — name match + active status + KMKR matches NIP (if known)
      DO-WERYFIKACJI — name mismatch, company closed, or FABRYKAT pattern
      PENDING_API — network / API error (NOT a verification failure)
    """
    if ee_search is None and ee_detail is None:
        return PENDING_API, "EE module niedostępny (ee_ariregister.py nie załadowany)"

    name_csv = (row.get("nazwa_firmy") or "").strip()
    rejestr = (row.get("rejestr_id") or "").strip()
    nip_csv = (row.get("nip_vat") or "").strip().upper()
    clean_nip = re.sub(r"[^0-9A-Z]", "", nip_csv)
    # Extract numeric reg_code from "e-Äriregister 11931003" or "11931003"
    m = re.search(r"(\d{7,8})", rejestr)
    reg_code = m.group(1) if m else ""

    # Primary path: if we have a reg_code, fetch detail directly (most
    # reliable — bypasses name-search ambiguity).
    result: dict | None = None
    if reg_code and ee_detail is not None:
        result = ee_detail(reg_code, name_hint=name_csv)
        if not result.get("found"):
            # Detail failed — fall through to name search
            result = None
        else:
            # We need the name for the match — fetch autocomplete too if we
            # have a name hint. The detail page doesn't expose the legal
            # name in a stable way we can extract.
            if ee_search is not None and name_csv:
                ac = ee_search(name_csv)
                if ac.get("found") and str(ac.get("reg_code")) == reg_code:
                    result = {**ac, **result}  # merge

    # Secondary path: name search
    if result is None:
        if not name_csv:
            return PENDING_API, "EE: brak nazwy firmy i rejestr_id — nie ma czego szukać"
        if ee_search is None:
            return PENDING_API, "EE module niedostępny (ee_ariregister.py nie załadowany)"
        result = ee_search(name_csv)
        if not result.get("found"):
            err = (result or {}).get("error", "brak odpowiedzi")
            if "brak wyników" in err.lower():
                return "DO-WERYFIKACJI", f"EE: firma '{name_csv[:30]}' nie istnieje w e-Äriregister"
            return PENDING_API, f"EE: {err}"

    # Active status check (Estonian status codes: R/L/K/N/S/P/M)
    if result.get("status") in {"K", "P", "L"}:
        return "DO-WERYFIKACJI", (
            f"EE: firma zamknięta ({result.get('status_label', result.get('status'))}, "
            f"reg {result.get('reg_code', '?')})"
        )

    # Name match (Jaccard on tokens, strip legal forms)
    csv_norm = normalize(name_csv)
    api_norm = normalize(result.get("name", ""))
    if csv_norm and api_norm:
        csv_tokens = {t for t in csv_norm.split() if len(t) >= 3} - _EE_LEGAL_TOKENS
        api_tokens = {t for t in api_norm.split() if len(t) >= 3} - _EE_LEGAL_TOKENS
        if csv_tokens and api_tokens and not (csv_tokens & api_tokens):
            return "DO-WERYFIKACJI", (
                f"EE: nimi mismatch (CSV='{csv_norm[:30]}' API='{api_norm[:30]}')"
            )

    # VAT cross-check (if CSV has NIP/VAT and API returned KMKR)
    kmkr_api = (result.get("kmkr") or "").upper()
    # Treat common placeholders as "no VAT known" — don't compare
    nip_placeholders = {"", "BRAK", "BRAKDANYCH", "DOWERYFIKACJI", "DOUSTALENIA",
                        "NA", "TODETERMINE", "TODO"}
    has_real_nip = (
        bool(clean_nip)
        and clean_nip not in nip_placeholders
        and any(c.isdigit() for c in clean_nip)
    )
    if has_real_nip and kmkr_api:
        if clean_nip.startswith("EE") and clean_nip != kmkr_api:
            return "DO-WERYFIKACJI", (
                f"EE: KMKR mismatch (CSV NIP={clean_nip}, API KMKR={kmkr_api})"
            )
        if not clean_nip.startswith("EE"):
            # Bare digits (e.g. "101376895") — compare to KMKR tail
            if clean_nip != kmkr_api[2:]:
                return "DO-WERYFIKACJI", (
                    f"EE: KMKR mismatch (CSV NIP={clean_nip}, API KMKR={kmkr_api})"
                )

    nace = result.get("emtak", "")
    address = result.get("legal_address", "")
    # Stash enrichment so main() can back-fill nip_vat / rejestr_id / adres
    # in the CSV for rows that previously had "do weryfikacji" placeholders.
    id_ = (row.get("id_unikalne") or "").strip()
    if id_:
        ee_enrichments[id_] = {
            "nip_vat": kmkr_api,
            "rejestr_id": f"e-Äriregister {result.get('reg_code', '')}".strip(),
            "adres": address,
            "emtak": nace,
        }
    return "FROZEN", (
        f"EE live: {result.get('name', '')[:35]} "
        f"(reg {result.get('reg_code', '?')}, KMKR {kmkr_api or '?'}, "
        f"NACE {nace or '?'})"
        + (f", {address[:30]}" if address else "")
    )


# Lithuanian legal-form tokens (stripped before name-match Jaccard)
_LT_LEGAL_TOKENS = {
    "UAB", "AB", "VĮ", "UŽAB", "IĮ", "TŪB", "KŪB", "VšĮ", "MB",
    "AS", "BI", "TIB", "TIKROJI", "ŪKINĖ", "BENDRIJA", "BENDROVĖ",
}


def verify_lt_row(row: dict) -> tuple[str, str]:
    """
    Verify LT row via Lithuanian open data (data.gov.lt SAU / spinta API).

    The SAU API at get.data.gov.lt is the only public, no-auth path to
    the JAR (Juridinių asmenų registras). rekvizitai.vz.lt is Cloudflare-
    blocked and registrucentras.lt is a JS SPA — neither exposes a
    queryable endpoint.

    Two paths:
      1. If `rejestr_id` contains a 9-digit ja_kodas (e.g. "JAR 110443493")
         → direct lookup via /JuridinisAsmuo?ja_kodas=NNNNNNNNN
         Returns name, registration date, deregistration date, legal
         form, status, status date.
      2. Otherwise (placeholder or missing ja_kodas) → fall back to VIES
         for VAT validation. No name search is available, so rows that
         only have a name and no PVM stay PENDING_API.

    Limitations:
      • No name search — only direct ja_kodas lookup works.
      • Address (adresas) is a UUID ref to an external Address Registry
        not exposed via the SAU API; we cannot back-fill the adres column.
    """
    if lt_jar_lookup is None:
        return PENDING_API, "LT module niedostępny (lt_open_data.py nie załadowany)"

    name_csv = (row.get("nazwa_firmy") or "").strip()
    rejestr = (row.get("rejestr_id") or "").strip()
    nip_csv = (row.get("nip_vat") or "").strip().upper()
    clean_nip = re.sub(r"[^0-9A-Z]", "", nip_csv)

    # Extract 9-digit ja_kodas from rejestr_id
    m = re.search(r"\b(\d{9})\b", rejestr)
    ja_kodas_str = m.group(1) if m else ""

    if not ja_kodas_str:
        return PENDING_API, (
            "LT: brak ja_kodas w rejestr_id — open data API wymaga kodu, "
            "name search niedostępny"
        )

    result = lt_jar_lookup(ja_kodas_str)
    if not result.get("found"):
        err = (result or {}).get("error", "brak odpowiedzi")
        if "brak wyników" in err.lower():
            return "DO-WERYFIKACJI", f"LT: ja_kodas {ja_kodas_str} nie istnieje w JAR"
        return PENDING_API, f"LT: {err}"

    # Active check: isreg_data is None AND statusas_kodas == 0 (default active)
    if result.get("isreg_data"):
        return "DO-WERYFIKACJI", (
            f"LT: firma wyrejestrowana ({result.get('name', '')}, "
            f"isreg_data {result.get('isreg_data')})"
        )

    # Resolve forma / statusas by UUID → name
    forma_name, statusas_name, forma_kodas, statusas_kodas = (None, None, None, None)
    if lt_jar_resolve_forma_status is not None:
        forma_name, statusas_name, forma_kodas, statusas_kodas = lt_jar_resolve_forma_status(
            result.get("forma_uuid"), result.get("statusas_uuid")
        )

    # Status check: statusas_kodas 0 = active, 1-7 = proceedings (some OK, some not)
    # 1=Reorganizuojamas, 2=Dalyvaujantis reorganizavime, 3=Pertvarkomas,
    # 4=Restruktūrizuojamas, 5=Bankrutuojantis, 6=Likviduojamas, 7=...
    # Treat 5 (bankrutuojantis) and 6 (likviduojamas) as DO-WERYFIKACJI.
    if isinstance(statusas_kodas, int) and statusas_kodas in (5, 6):
        return "DO-WERYFIKACJI", (
            f"LT: firma w trakcie ({statusas_name or statusas_kodas}, "
            f"ja_kodas {ja_kodas_str})"
        )

    # Name match (Jaccard on tokens, strip LT legal forms)
    csv_norm = normalize(name_csv)
    api_norm = normalize(result.get("name", ""))
    if csv_norm and api_norm:
        csv_tokens = {t for t in csv_norm.split() if len(t) >= 3} - _LT_LEGAL_TOKENS
        api_tokens = {t for t in api_norm.split() if len(t) >= 3} - _LT_LEGAL_TOKENS
        if csv_tokens and api_tokens and not (csv_tokens & api_tokens):
            return "DO-WERYFIKACJI", (
                f"LT: pavadinimas mismatch (CSV='{csv_norm[:30]}' "
                f"API='{api_norm[:30]}')"
            )

    # VAT cross-check (if CSV has a real PVM and we can derive expected)
    # Lithuanian PVM for a legal entity is typically LT + ja_kodas (9 digits)
    expected_pvm = f"LT{ja_kodas_str}"
    if clean_nip and clean_nip != expected_pvm:
        # Real NIP but doesn't match the canonical LT+ja_kodas pattern
        # Don't auto-fail — PVMs can also be 12-digit for non-LT-registered
        # entities; just note the discrepancy in the reason
        pvm_note = f" (CSV PVM {clean_nip} ≠ oczekiwany {expected_pvm})"
    else:
        pvm_note = ""

    # Stash enrichment for main() back-fill
    id_ = (row.get("id_unikalne") or "").strip()
    if id_:
        lt_enrichments[id_] = {
            "nip_vat": expected_pvm,
            "rejestr_id": f"JAR {ja_kodas_str}",
            "adres": "",  # not available via SAU API
            "forma": forma_name or "",
        }

    return "FROZEN", (
        f"LT live: {result.get('name', '')[:35]} "
        f"(ja_kodas {ja_kodas_str}, reg {result.get('reg_data', '?')}, "
        f"{forma_name or '?'[:25]})"
        + pvm_note
    )


# Side-channel: verify_lt_row() populates this when it returns FROZEN so
# main() can back-fill nip_vat / rejestr_id for rows that previously had
# "do weryfikacji" placeholders. Keyed by id_unikalne.
lt_enrichments: dict[str, dict] = {}


def apply_lt_enrichments(csv_path: Path, enrichments: dict[str, dict]) -> int:
    """Back-fill nip_vat / rejestr_id for LT rows from JAR result.

    Only overwrites cells that are currently placeholders (do weryfikacji /
    do ustalenia / brak / empty) — never clobbers a value the user set
    manually. Address is NOT back-filled (SAU API doesn't expose the
    address text). Returns count of cells written.
    """
    if not enrichments:
        return 0
    placeholders = {"", "brak", "brak danych", "do weryfikacji", "do ustalenia", "n/a", "—"}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    n_cols = len(header)
    if "id_unikalne" not in header:
        return 0
    id_idx = header.index("id_unikalne")
    field_map = {
        "nip_vat": "nip_vat",
        "rejestr_id": "rejestr_id",
    }
    field_idxs = {col: header.index(col) for col in field_map if col in header}
    n = 0
    for i, row in enumerate(rows):
        if len(row) == 0:
            continue
        if len(row) < n_cols:
            row += [""] * (n_cols - len(row))
        id_ = row[id_idx]
        if id_ not in enrichments:
            continue
        data = enrichments[id_]
        for col, key in field_map.items():
            if key not in field_idxs:
                continue
            idx = field_idxs[key]
            current = (row[idx] or "").strip()
            new = data.get(key, "")
            if new and current.lower() in placeholders:
                row[idx] = new
                n += 1
    tmp_path = csv_path.with_suffix(csv_path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        os.replace(tmp_path, csv_path)
    except OSError as e:
        log(f"  → {csv_path.name}: atomic write failed ({e})")
        if tmp_path.exists():
            try: tmp_path.unlink()
            except OSError: pass
        raise
    return n


# Side-channel: verify_ee_row() populates this when it returns FROZEN so
# main() can back-fill nip_vat / rejestr_id / adres for rows that previously
# had "do weryfikacji" placeholders. Keyed by id_unikalne.
ee_enrichments: dict[str, dict] = {}


# Back-fillable Apollo enrichments, collected during main() and persisted
# once per file via apply_apollo_enrichments() (same pattern as EE/LT).
# Keyed by id_unikalne. Values: dict with optional keys
#   telefon, linkedin, miasto, email_decydent
apollo_enrichments: dict[str, dict] = {}


def apply_apollo_enrichments(csv_path: Path, enrichments: dict[str, dict]) -> int:
    """Back-fill telefon / linkedin / miasto / email_decydent from Apollo.

    Only overwrites cells that are currently placeholders (do weryfikacji /
    do ustalenia / brak / empty) — never clobbers a value the user set
    manually. Returns count of cells written.
    """
    if not enrichments:
        return 0
    placeholders = {"", "brak", "brak danych", "do weryfikacji", "do ustalenia", "n/a", "—"}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    n_cols = len(header)
    if "id_unikalne" not in header:
        return 0
    id_idx = header.index("id_unikalne")
    field_map = {
        "telefon": "telefon",
        "linkedin": "linkedin",
        "miasto": "miasto",
        "email_decydent": "email_decydent",
    }
    field_idxs = {col: header.index(col) for col in field_map if col in header}
    n = 0
    for i, row in enumerate(rows):
        if len(row) == 0:
            continue
        if len(row) < n_cols:
            row += [""] * (n_cols - len(row))
        id_ = row[id_idx]
        if id_ not in enrichments:
            continue
        data = enrichments[id_]
        for col, key in field_map.items():
            if key not in field_idxs:
                continue
            idx = field_idxs[key]
            current = (row[idx] or "").strip()
            new = data.get(key, "")
            if new and current.lower() in placeholders:
                row[idx] = new
                n += 1
    tmp_path = csv_path.with_suffix(csv_path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        os.replace(tmp_path, csv_path)
    except OSError as e:
        log(f"  → {csv_path.name}: atomic write failed ({e})")
        if tmp_path.exists():
            try: tmp_path.unlink()
            except OSError: pass
        raise
    return n


def apply_ee_enrichments(csv_path: Path, enrichments: dict[str, dict]) -> int:
    """Back-fill nip_vat / rejestr_id / adres for EE rows from API result.

    Only overwrites cells that are currently placeholders (do weryfikacji /
    do ustalenia / brak / empty) — never clobbers a value the user set
    manually. Returns count of cells written.
    """
    if not enrichments:
        return 0
    placeholders = {"", "brak", "brak danych", "do weryfikacji", "do ustalenia", "n/a", "—"}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    n_cols = len(header)
    if "id_unikalne" not in header:
        return 0
    id_idx = header.index("id_unikalne")
    field_map = {
        "nip_vat": "nip_vat",
        "rejestr_id": "rejestr_id",
        "adres": "adres",
    }
    field_idxs = {col: header.index(col) for col in field_map if col in header}
    n = 0
    for i, row in enumerate(rows):
        if len(row) == 0:
            continue
        if len(row) < n_cols:
            row += [""] * (n_cols - len(row))
        id_ = row[id_idx]
        if id_ not in enrichments:
            continue
        data = enrichments[id_]
        for col, key in field_map.items():
            if key not in field_idxs:
                continue
            idx = field_idxs[key]
            current = (row[idx] or "").strip()
            new = data.get(key, "")
            if new and current.lower() in placeholders:
                row[idx] = new
                n += 1
    tmp_path = csv_path.with_suffix(csv_path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        os.replace(tmp_path, csv_path)
    except OSError as e:
        log(f"  → {csv_path.name}: atomic write failed ({e})")
        if tmp_path.exists():
            try: tmp_path.unlink()
            except OSError: pass
        raise
    return n


def update_row_status(csv_path: Path, updates: dict[str, tuple[str, str]]) -> int:
    """Update flagi column for verified rows. Returns count updated."""
    if not updates:
        return 0
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    if "id_unikalne" not in header or "flagi" not in header:
        return 0
    n_cols = len(header)
    id_idx = header.index("id_unikalne")
    flagi_idx = header.index("flagi")
    n = 0
    for i, row in enumerate(rows):
        # Pad or skip short rows
        if len(row) == 0:
            continue  # empty line
        if len(row) < n_cols:
            row += [""] * (n_cols - len(row))
        id_ = row[id_idx]
        if id_ in updates:
            status, _ = updates[id_]
            existing = row[flagi_idx] or ""
            # Strip ALL prior FROZEN/DO-WERYFIKACJI markers (including (API) variants and date prefixes)
            cleaned = re.sub(r"\d{4}-\d{2}-\d{2}\s*", "", existing)  # strip date prefixes
            cleaned = re.sub(r"\(API\)", "", cleaned)                 # strip (API) tags first
            cleaned = re.sub(r"✅\s*FROZEN", "", cleaned)              # strip FROZEN
            cleaned = re.sub(r"⚠️?\s*DO-WERYFIKACJI", "", cleaned)    # strip DO-WERYFIKACJI
            cleaned = re.sub(r"⏳\s*PENDING_API", "", cleaned)         # strip PENDING_API
            cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()         # collapse whitespace
            today = __import__('time').strftime('%Y-%m-%d')
            if status == "FROZEN":
                marker = f"{today} ✅ FROZEN (API)"
            elif status == PENDING_API:
                # PENDING_API means "we don't have integration yet" — NOT
                # an error. Rendered as info, not warning, to keep it
                # visually distinct from real verification failures.
                marker = f"{today} ⏳ PENDING_API"
            else:
                marker = f"{today} ⚠️ DO-WERYFIKACJI (API)"
            row[flagi_idx] = f"{cleaned} {marker}".strip() if cleaned else marker
            if status == "FROZEN":
                if "zrodlo_danych" in header:
                    z_idx = header.index("zrodlo_danych")
                    curr_z = row[z_idx]
                    if "API" not in curr_z:
                        row[z_idx] = f"KRS API / CEIDG API + web search {today}"
                if "adres" in header:
                    a_idx = header.index("adres")
                    if not row[a_idx] or row[a_idx].strip() in ("brak", "do weryfikacji"):
                        row[a_idx] = "Polska (Adres w rejestrze KRS/CEIDG)"
            n += 1
    tmp_path = csv_path.with_suffix(csv_path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        os.replace(tmp_path, csv_path)
    except OSError as e:
        log(f"  → {csv_path.name}: atomic write failed ({e})")
        if tmp_path.exists():
            try: tmp_path.unlink()
            except OSError: pass
        raise
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description="Live registry verification for BILLSzuka")
    ap.add_argument("--country", help="Limit to one country code (e.g. PL, CZ)")
    ap.add_argument("--all", action="store_true", help="Verify all rows in all countries")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be verified, write nothing")
    args = ap.parse_args()

    env = load_env()
    ceidg_token = env.get("CEIDG_API_TOKEN", "")

    if not ceidg_token:
        log("WARNING: CEIDG_API_TOKEN not in .env — PL rows will be skipped")

    csv_files = sorted(p for p in DATA.glob("*/catalog-*.csv")
                       if p.is_file() and p.stat().st_size > 400
                       and not p.parent.name.startswith(".")
                       and p.parent.name not in ("backups", "snapshots"))

    total_verified = 0
    total_frozen = 0
    total_dov = 0
    total_pending = 0

    for csv_path in csv_files:
        with open(csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        updates: dict[str, tuple[str, str]] = {}
        for row in rows:
            country = (row.get("kraj") or "").upper().strip()
            if args.country and country != args.country.upper():
                continue
            if not args.country and not args.all:
                continue

            id_ = (row.get("id_unikalne") or "").strip()
            if not id_:
                continue

            if country == "PL":
                if not ceidg_token:
                    continue
                status, reason = verify_pl_row(row, ceidg_token)
            elif country == "CZ":
                status, reason = verify_cz_row(row)
            elif country == "FR":
                # France has its own rich public API (recherche-entreprises.
                # api.gouv.fr) — much better than VIES alone because we get
                # company name + address + dirigeants back, not just VAT
                # validity. Routed before the generic EU branch.
                status, reason = verify_fr_row(row)
            elif country == "EE":
                # Estonia e-Äriregister (ariregister.rik.ee) — autocomplete
                # JSON API + detail HTML. Rich data: name, address, KMKR
                # (VAT), EMTAK (NACE), legal form, status, founded.
                # Routed before the generic EU branch (better than VIES
                # alone because we get the company name back).
                status, reason = verify_ee_row(row)
            elif country == "LT":
                # Lithuania JAR (Juridinių asmenų registras) via the
                # data.gov.lt SAU / spinta open data API
                # (get.data.gov.lt/datasets/gov/rc/jar/iregistruoti/...).
                # Rekvizitai.vz.lt is Cloudflare-blocked; JAR website is
                # a JS SPA with no queryable endpoint. Limitation: only
                # direct ja_kodas lookup works (no name search).
                status, reason = verify_lt_row(row)
            elif country in EU_MEMBER_STATES:
                # All other EU countries: use VIES as a fast first-pass.
                # Covers SK, LT, LV, BG, HR, RO, SI in BILLSzuka
                # scope (PL/CZ/EE/FR have their own registries).
                status, reason = verify_vies_row(row)
            else:
                # Non-EU country (e.g. MD) without dedicated integration.
                # PENDING_API is NOT an error — it just means we don't
                # have a registry hookup for that market yet.
                status = PENDING_API
                reason = f"Brak API dla {country} (non-EU; VIES nie pokrywa)"

            updates[id_] = (status, reason)
            total_verified += 1
            if status == "FROZEN":
                total_frozen += 1
            elif status == PENDING_API:
                total_pending += 1
            else:
                total_dov += 1
            log(f"  {id_}: {status} — {reason[:60]}")

            # Apollo second-pass: for FROZEN rows from countries that have
            # only a thin primary verification (SK, LV, BG, HR, RO, SI
            # via VIES; non-EU like MD), Apollo's org enrich adds the
            # company-level fields the registries don't return (telefon,
            # linkedin, miasto). FREE plan only — no decision-maker.
            # Skipped silently for PL/CZ/EE/FR/LT (they already get rich
            # data from their dedicated registries) and for DO-WERYFIKACJI /
            # PENDING_API rows (don't waste API quota on unverifiable data).
            if (
                status == "FROZEN"
                and APOLLO_AVAILABLE
                and country in EU_MEMBER_STATES | {"MD"}
                and country not in ("PL", "CZ", "EE", "FR", "LT")
            ):
                apollo_status, apollo_reason = verify_apollo_row(row)
                # We don't change the primary status (FROZEN stays FROZEN) —
                # Apollo is purely additive. Its status is logged for audit.
                if apollo_status == "FROZEN":
                    log(f"    +Apollo: {apollo_reason[:60]}")
                else:
                    log(f"    Apollo: {apollo_status} — {apollo_reason[:60]}")

        if updates and not args.dry_run:
            n = update_row_status(csv_path, updates)
            if n:
                log(f"  → {csv_path.name}: {n} rows updated")
            # EE: back-fill discovered nip_vat / rejestr_id / adres
            if ee_enrichments and not args.dry_run:
                n = apply_ee_enrichments(csv_path, ee_enrichments)
                if n:
                    log(f"  → {csv_path.name}: {n} cells back-filled from e-Äriregister")
                ee_enrichments.clear()
            # LT: back-fill discovered nip_vat / rejestr_id (no adres — SAU
            # API doesn't expose address text)
            if lt_enrichments and not args.dry_run:
                n = apply_lt_enrichments(csv_path, lt_enrichments)
                if n:
                    log(f"  → {csv_path.name}: {n} cells back-filled from JAR")
                lt_enrichments.clear()
            # Apollo: back-fill telefon / linkedin / miasto (FREE plan)
            if apollo_enrichments and not args.dry_run:
                n = apply_apollo_enrichments(csv_path, apollo_enrichments)
                if n:
                    log(f"  → {csv_path.name}: {n} cells back-filled from Apollo")
                apollo_enrichments.clear()

    log(
        f"\nTotal: {total_verified} verified — "
        f"{total_frozen} FROZEN, {total_dov} DO-WERYFIKACJI, "
        f"{total_pending} PENDING_API"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
