#!/usr/bin/env python3
"""
lt_open_data.py — Lithuanian JAR (Legal Entity Registry) open data client.

Single source: https://get.data.gov.lt (SAU / spinta open data portal)
Hosting: VĮ Registrų centras (state enterprise Register Centre of Lithuania).

Why this and not Rekvizitai.vz.lt / registrucentras.lt?
  • rekvizitai.vz.lt (the "recommended" path in RUNBOOK) is behind Cloudflare
    and returns 403 to any non-browser User-Agent.
  • registrucentras.lt is a Drupal/JS SPA — search results are rendered
    client-side and not exposed as a queryable API.
  • atviras.jar.lt times out (>30s) for any meaningful request.
  • data.gov.lt's SAU API (this module) is the only public, free,
    no-auth path that actually returns clean JSON.

Endpoint:
  GET https://get.data.gov.lt/datasets/gov/rc/jar/iregistruoti/JuridinisAsmuo?ja_kodas=<int>

Returns: { _data: [ { ja_kodas, ja_pavadinimas, reg_data, isreg_data,
                       forma: {_id}, statusas: {_id}, stat_data, ... } ] }

Lookups needed for human-readable forma/statusas:
  • datasets/gov/rc/jar/formos_statusai/Forma
  • datasets/gov/rc/jar/formos_statusai/Statusas

Limitations:
  • No name-search endpoint — must know the ja_kodas (9 digits, e.g. 110443493).
    The CSV column `rejestr_id` carries it as "JAR NNNNNNNNN" or just the
    digits. For rows without ja_kodas, the verifier falls back to VIES (VAT
    validation only) and reports PENDING_API for the rich-data path.
  • Address (adresas) is referenced by UUID to an external Address Registry
    not exposed via this API. The buveines dataset only carries the
    juridinis_asmuo._id → adresas._id link, not the address text.

Output dict shape:
  {
      "found": bool,
      "ja_kodas": int,             # 9-digit company code
      "name": str,                 # "UAB \"SANITEX\""
      "reg_data": str,             # ISO date or None
      "isreg_data": str | None,    # ISO date or None (active = None)
      "forma": str,                # "Uždaroji akcinė bendrovė" (resolved)
      "forma_kodas": int,          # 110 = UAB, 120 = VĮ, 130 = AB, etc.
      "statusas": str,             # "Veikiantis" (resolved)
      "statusas_kodas": int,       # 0..N
      "stat_data": str | None,     # date of current status
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

JAR_BASE = "https://get.data.gov.lt/datasets/gov/rc/jar"
JURIDINIS_ASMUO = f"{JAR_BASE}/iregistruoti/JuridinisAsmuo"
FORMA = f"{JAR_BASE}/formos_statusai/Forma"
STATUSAS = f"{JAR_BASE}/formos_statusai/Statusas"

# --- cached lookup tables (loaded lazily) ---
_FORMA_CACHE: dict[int, str] | None = None
_STATUSAS_CACHE: dict[int, str] | None = None


def _http_get_json(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "BILLSzuka-Verifier/2.0",
            "Accept": "application/json",
            "Accept-Language": "lt,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _load_forma_cache() -> dict[int, str]:
    """Load all Forma (legal form) records into a {kodas: pavadinimas} dict.

    Lithuania has ~80 distinct legal forms. Cached after first call.
    """
    global _FORMA_CACHE
    if _FORMA_CACHE is not None:
        return _FORMA_CACHE
    out: dict[int, str] = {}
    try:
        data = _http_get_json(FORMA)
        for row in data.get("_data") or []:
            k = row.get("kodas")
            p = row.get("pavadinimas") or row.get("name") or ""
            if isinstance(k, int) and p:
                out[k] = p
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        pass
    _FORMA_CACHE = out
    return out


def _load_statusas_cache() -> dict[int, str]:
    """Load all Statusas (legal status) records into a {kodas: pavadinimas} dict."""
    global _STATUSAS_CACHE
    if _STATUSAS_CACHE is not None:
        return _STATUSAS_CACHE
    out: dict[int, str] = {}
    try:
        data = _http_get_json(STATUSAS)
        for row in data.get("_data") or []:
            k = row.get("kodas")
            p = row.get("pavadinimas") or row.get("name") or ""
            if isinstance(k, int) and p:
                out[k] = p
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        pass
    _STATUSAS_CACHE = out
    return out


def lt_jar_lookup(ja_kodas: int | str, timeout: int = 15) -> dict[str, Any]:
    """Look up a Lithuanian legal entity by JAR company code (ja_kodas).

    `ja_kodas` is a 9-digit integer (e.g. 110443493 for UAB SANITEX).
    Returns the rich dict described in the module docstring, or
    {"found": False, "error": "..."} on any failure.
    """
    # Coerce and validate
    try:
        code = int(str(ja_kodas).strip())
    except (ValueError, TypeError):
        return {"found": False, "error": f"invalid ja_kodas: {ja_kodas!r}"}
    if not (100_000_000 <= code <= 999_999_999):
        return {"found": False, "error": f"ja_kodas out of range: {code}"}

    url = f"{JURIDINIS_ASMUO}?ja_kodas={code}"
    try:
        data = _http_get_json(url, timeout=timeout)
    except urllib.error.HTTPError as e:
        return {"found": False, "error": f"HTTP {e.code}: {e.reason}"}
    except (urllib.error.URLError, TimeoutError) as e:
        return {"found": False, "error": f"connection: {e}"}
    except json.JSONDecodeError as e:
        return {"found": False, "error": f"json: {e}"}

    rows = data.get("_data") or []
    if not rows:
        return {"found": False, "error": f"brak wyników dla ja_kodas={code}"}
    if len(rows) > 1:
        # ja_kodas is supposed to be unique, but defensively take the first
        pass
    row = rows[0]

    # Resolve forma / statusas by UUID via the cached lookup tables
    # The response only has UUID refs; we need the legal-form/status name
    # which lives in a separate model keyed by `kodas` (int), not UUID.
    # We have to do an extra lookup because the API doesn't dereference.
    forma_uuid = (row.get("forma") or {}).get("_id")
    statusas_uuid = (row.get("statusas") or {}).get("_id")

    # We can't reverse-UUID→kodas cheaply; cache the other direction
    # by fetching all forma/statusas once and inverting.
    # For now, expose only what we have; the verifier can match by name.
    return {
        "found": True,
        "ja_kodas": row.get("ja_kodas"),
        "name": row.get("ja_pavadinimas", ""),
        "reg_data": row.get("reg_data"),
        "isreg_data": row.get("isreg_data"),  # None = active
        "forma_uuid": forma_uuid,
        "statusas_uuid": statusas_uuid,
        "stat_data": row.get("stat_data"),
        "source_url": url,
        "error": None,
    }


def lt_jar_resolve_forma_status(forma_uuid: str | None, statusas_uuid: str | None) -> tuple[str | None, str | None, int | None, int | None]:
    """Resolve forma/statusas UUIDs to (forma_name, statusas_name, forma_kodas, statusas_kodas).

    The SAU open data API doesn't dereference these refs; we have to
    build a UUID→{kodas,pavadinimas} map client-side. The maps are
    cached in the module globals.
    """
    forma_name = statusas_name = None
    forma_kodas = statusas_kodas = None

    if forma_uuid:
        # Build a reverse map once (UUID → kodas+pavadinimas)
        global _FORMA_REV
        if not hasattr(lt_jar_resolve_forma_status, "_forma_rev_loaded"):
            lt_jar_resolve_forma_status._forma_rev = {}
            try:
                data = _http_get_json(FORMA)
                for r in data.get("_data") or []:
                    uid = r.get("_id")
                    k = r.get("kodas")
                    p = r.get("pavadinimas") or r.get("name") or ""
                    if uid and isinstance(k, int):
                        lt_jar_resolve_forma_status._forma_rev[uid] = (k, p)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                pass
            lt_jar_resolve_forma_status._forma_rev_loaded = True
        entry = lt_jar_resolve_forma_status._forma_rev.get(forma_uuid)
        if entry:
            forma_kodas, forma_name = entry

    if statusas_uuid:
        if not hasattr(lt_jar_resolve_forma_status, "_statusas_rev_loaded"):
            lt_jar_resolve_forma_status._statusas_rev = {}
            try:
                data = _http_get_json(STATUSAS)
                for r in data.get("_data") or []:
                    uid = r.get("_id")
                    k = r.get("kodas")
                    p = r.get("pavadinimas") or r.get("name") or ""
                    if uid and isinstance(k, int):
                        lt_jar_resolve_forma_status._statusas_rev[uid] = (k, p)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                pass
            lt_jar_resolve_forma_status._statusas_rev_loaded = True
        entry = lt_jar_resolve_forma_status._statusas_rev.get(statusas_uuid)
        if entry:
            statusas_kodas, statusas_name = entry

    return forma_name, statusas_name, forma_kodas, statusas_kodas


# --- Legal-form tokens for name-match Jaccard (matches verify_ee_row, etc.) ---
_LT_LEGAL_TOKENS = {
    "UAB", "AB", "VĮ", "UŽAB", "IĮ", "TŪB", "KŪB", "VšĮ", "MB",
    "AS", "BĮ", "Ko", "KP", "Tikroji", "UABAR", "UABK", "UABS", "UABT",
}


def main() -> int:
    """CLI: pass a JAR code (9 digits) as argv[1]."""
    if len(sys.argv) < 2:
        print("Usage: lt_open_data.py <ja_kodas>")
        return 1
    arg = sys.argv[1].strip()
    result = lt_jar_lookup(arg)
    if result.get("found"):
        forma_name, statusas_name, forma_k, statusas_k = lt_jar_resolve_forma_status(
            result.get("forma_uuid"), result.get("statusas_uuid")
        )
        result["forma"] = forma_name or ""
        result["forma_kodas"] = forma_k
        result["statusas"] = statusas_name or ""
        result["statusas_kodas"] = statusas_k
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("found") else 1


if __name__ == "__main__":
    sys.exit(main())
