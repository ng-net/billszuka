#!/usr/bin/env python3
"""
ee_ariregister.py — Estonian e-Äriregister client for BILLSzuka.

Two endpoints:
  1. Autocomplete (JSON): https://ariregister.rik.ee/est/api/autocomplete?q=<name>
     Returns company list with reg_code, name, address, status, legal_form.
  2. Detail (HTML):       https://ariregister.rik.ee/est/company/<reg_code>/<slug>
     Returns full page with KMKR (VAT), EMTAK (NACE), capital, revenue, founded.

No auth required. HTML scraping is brittle; primary path is autocomplete JSON.
Detail HTML is parsed for KMKR/EMTAK/capital/founded when reg_code is known.

Output dict shape:
  {
      "found": bool,
      "reg_code": str,           # 8 digits
      "name": str,               # e.g. "Sanitex OÜ"
      "historical_names": list[str],
      "status": str,             # "R" = registered, "L" = in liquidation, etc.
      "status_label": str,       # "Registrisse kantud" etc.
      "legal_form": str,         # "5" = OÜ, "6" = AS, etc.
      "legal_address": str,      # "Harju maakond, Rae vald, Rae küla, Graniidi tee 1"
      "zip_code": str,
      "kmkr": str,               # VAT like "EE101376895"
      "emtak": str,              # primary EMTAK/NACE code like "46.39"
      "founded": str,            # dd.mm.yyyy
      "capital_eur": float,      # share capital in EUR (0 if not found)
      "url": str,                # canonical company page
      "error": str | None,
  }
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

AUTOCOMPLETE_URL = "https://ariregister.rik.ee/est/api/autocomplete"
COMPANY_URL_TPL = "https://ariregister.rik.ee/est/company/{reg_code}/{slug}"

LEGAL_FORMS = {
    "1": "Täisühing",
    "2": "Usaldusühing",
    "3": "Osaühing (vanem vorm)",
    "4": "Aktsiaselts (vanem vorm)",
    "5": "OÜ (osaühing)",
    "6": "AS (aktsiaselts)",
    "7": "Tulundusühistu",
    "8": "Mittetulundusühing",
    "9": "Sihtasutus",
    "10": "FIE (Füüsilisest isikust ettevõtja)",
    "11": "Riigi-asutus",
    "12": "Kohaliku omavalitsuse asutus",
    "13": "Muu",
}

STATUS_LABELS = {
    "R": "Registrisse kantud",
    "L": "Likvideerimisel",
    "K": "Kustutatud",
    "N": "Nimetuse muutmine",
    "S": "Ümberkujundamine",
    "P": "Pankrotis",
    "M": "Mitteaktiivne",
}


def _slugify(name: str) -> str:
    """e-Äriregister URL slugs use ASCII-folded, dash-joined form."""
    s = (name or "").strip()
    # Replace Estonian and other diacritics
    repl = {
        "õ": "o", "ä": "a", "ö": "o", "ü": "u", "š": "s", "ž": "z",
        "Õ": "O", "Ä": "A", "Ö": "O", "Ü": "U", "Š": "S", "Ž": "Z",
        "č": "c", "Č": "C", "ņ": "n", "Ņ": "N", "ģ": "g", "Ģ": "G",
        "ē": "e", "Ē": "E", "ī": "i", "Ī": "I", "ķ": "k", "Ķ": "K",
        "ļ": "l", "Ļ": "L", "ŗ": "r", "Ŗ": "R", "ţ": "t", "Ţ": "T",
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    s = re.sub(r"[^A-Za-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def _http_get(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "BILLSzuka-Verifier/2.0",
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.5",
            "Accept-Language": "et,en;q=0.8,pl;q=0.6",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def ee_autocomplete(query: str, timeout: int = 10) -> list[dict[str, Any]]:
    """Search by company name fragment. Returns list of matches.

    Does not return VAT/NACE — those need detail() lookup.
    """
    clean = (query or "").strip()
    if not clean:
        return []
    url = f"{AUTOCOMPLETE_URL}?q={urllib.parse.quote(clean)}"
    try:
        body = _http_get(url, timeout=timeout)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.reason}")
    except (urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError(f"connection: {e}")

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"json: {e}")
    return data.get("data") or []


def ee_detail(reg_code: str, name_hint: str = "", timeout: int = 15) -> dict[str, Any]:
    """Fetch detail page and extract VAT, NACE, capital, founded.

    `name_hint` improves the URL slug (404 otherwise). Use autocomplete to find
    the canonical name first, then call detail().
    """
    clean_code = (reg_code or "").strip()
    if not re.fullmatch(r"\d{6,8}", clean_code):
        return {"found": False, "error": f"invalid reg_code: {reg_code!r}"}
    slug = _slugify(name_hint) if name_hint else "company"
    url = COMPANY_URL_TPL.format(reg_code=clean_code, slug=slug)
    try:
        html = _http_get(url, timeout=timeout)
    except urllib.error.HTTPError as e:
        return {"found": False, "error": f"HTTP {e.code}: {e.reason}"}
    except (urllib.error.URLError, TimeoutError) as e:
        return {"found": False, "error": f"connection: {e}"}

    kmkr_match = re.search(r"\b(EE\d{9,11})\b", html)
    kmkr = kmkr_match.group(1) if kmkr_match else ""

    # EMTAK (NACE) — the page has NACE codes in a <td> after a "NACE kood"
    # label cell. Take the first one (primary NACE).
    emtak = ""
    m = re.search(
        r'NACE\s*kood\s*</td>\s*<td[^>]*>\s*([0-9]{1,3}\.[0-9]{2}[A-Z]?)\s*</td>',
        html,
    )
    if m:
        emtak = m.group(1)
    if not emtak:
        # Fallback to Põhitegevusala 5-digit (truncate to NACE NN.NN)
        m = re.search(r'Põhitegevusala[^<]*?(\d{5})', html)
        if m:
            emtak = m.group(1)[:2] + "." + m.group(1)[2:4]

    founded = ""
    m = re.search(r'Asutatud\s*</div>\s*<div[^>]*>(\d{2}\.\d{2}\.\d{4})', html)
    if m:
        founded = m.group(1)
    if not founded:
        # Some companies: "Registreeritud" or "Asutatud" with different markup
        m = re.search(r'Registreeritud\s*</?\w*[^>]*>\s*(\d{2}\.\d{2}\.\d{4})', html)
        if m:
            founded = m.group(1)
    if not founded:
        # Older records sometimes use ISO date
        m = re.search(r'Asutatud\s*</?\w*[^>]*>\s*(\d{4}-\d{2}-\d{2})', html)
        if m:
            founded = m.group(1)

    capital = 0.0
    m = re.search(r'Osakapital\s*</div>\s*<div[^>]*>\s*([0-9][0-9 ,.]*)', html)
    if not m:
        m = re.search(r'Aktsiakapital\s*</div>\s*<div[^>]*>\s*([0-9][0-9 ,.]*)', html)
    if m:
        try:
            capital = float(m.group(1).replace(" ", "").replace(",", "."))
        except ValueError:
            capital = 0.0

    return {
        "found": True,
        "kmkr": kmkr,
        "emtak": emtak,
        "founded": founded,
        "capital_eur": capital,
        "source_url": url,
    }


def ee_search(query: str, timeout: int = 10) -> dict[str, Any]:
    """End-to-end: autocomplete + detail extraction for the first match.

    Returns the rich dict described in the module docstring.
    """
    try:
        matches = ee_autocomplete(query, timeout=timeout)
    except RuntimeError as e:
        return {"found": False, "error": f"autocomplete: {e}"}
    if not matches:
        return {"found": False, "error": f"brak wyników dla {query!r}"}

    first = matches[0]
    reg_code = str(first.get("reg_code", ""))
    name = first.get("name", "")
    slug = _slugify(name)
    detail_url = COMPANY_URL_TPL.format(reg_code=reg_code, slug=slug)

    result: dict[str, Any] = {
        "found": True,
        "reg_code": reg_code,
        "company_id": first.get("company_id"),
        "name": name,
        "historical_names": first.get("historical_names") or [],
        "status": first.get("status", ""),
        "status_label": STATUS_LABELS.get(first.get("status", ""), ""),
        "legal_form": first.get("legal_form", ""),
        "legal_form_label": LEGAL_FORMS.get(first.get("legal_form", ""), ""),
        "legal_address": first.get("legal_address", ""),
        "zip_code": first.get("zip_code", ""),
        "url": first.get("url") or detail_url,
        "kmkr": "",
        "emtak": "",
        "founded": "",
        "capital_eur": 0.0,
        "error": None,
    }

    detail = ee_detail(reg_code, name_hint=name, timeout=timeout)
    if detail.get("found"):
        result.update(detail)
    else:
        # Not fatal: autocomplete result is still useful for name/address
        result["error"] = f"detail: {detail.get('error')}"

    return result


def main() -> int:
    """CLI: pass a name (or reg_code) as argv[1]."""
    if len(sys.argv) < 2:
        print("Usage: ee_ariregister.py <name_or_reg_code>")
        return 1
    arg = sys.argv[1].strip()
    if re.fullmatch(r"\d{6,8}", arg):
        # Direct reg_code lookup: need a name hint for the slug
        # Try autocomplete with the reg_code as a guess — usually returns []
        # so just fetch detail with a generic slug
        result = ee_detail(arg, name_hint=arg, timeout=15)
    else:
        result = ee_search(arg)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("found") else 1


if __name__ == "__main__":
    sys.exit(main())
