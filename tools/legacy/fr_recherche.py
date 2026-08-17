#!/usr/bin/env python3
"""
fr_recherche.py — French government open-company search (SIREN/SIRET).

Uses the official recherche-entreprises.api.gouv.fr API:
  https://recherche-entreprises.api.gouv.fr/search?q=<query>

No authentication required. Returns rich JSON with company name, address,
creation date, dirigeants, NAF code, etat_administratif (active/closed).

Output dict shape:
  {
      "found": bool,
      "siren": str,
      "nom_complet": str,
      "date_creation": str,          # ISO date
      "etat_administratif": str,     # "A" = active, "F" = closed
      "adresse": str,                # formatted siège address
      "dirigeants": list[str],       # names of dirigeants
      "activite_principale": str,    # NAF code
      "error": str | None,
  }

Search modes:
  - By name:    fr_search("IMPORT")           -> may match many, take first
  - By SIREN:   fr_search("491041646")        -> exact match (9 digits)
  - By SIRET:   fr_search("49104164600012")   -> exact match (14 digits)
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_URL = "https://recherche-entreprises.api.gouv.fr/search"


def fr_search(query: str, timeout: int = 10) -> dict[str, Any]:
    """
    Search French government open-data API for a company.

    `query` may be a SIREN (9 digits), SIRET (14 digits), or a name fragment.
    Returns the first (most relevant) result, or an error dict.
    """
    clean = (query or "").strip()
    if not clean:
        return {"found": False, "error": "puste zapytanie"}

    url = f"{API_URL}?q={urllib.parse.quote(clean)}&page=1&per_page=5"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "BILLSzuka-Verifier/2.0", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"found": False, "error": f"HTTP {e.code}: {e.reason}"}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        return {"found": False, "error": f"connection: {e}"}
    except Exception as e:  # pragma: no cover
        return {"found": False, "error": f"{type(e).__name__}: {e}"}

    results = data.get("results") or []
    if not results:
        return {"found": False, "error": f"brak wyników dla {clean!r}"}

    # If query looks like a SIREN/SIRET, find exact match; else first result
    if re.fullmatch(r"\d{9,14}", re.sub(r"\s", "", clean)):
        target = re.sub(r"\s", "", clean)[:9]  # SIREN is 9 digits
        for r in results:
            if r.get("siren") == target:
                return _extract(r)
        # Exact SIREN not in top-5 — fall through to first result anyway
    return _extract(results[0])


def _extract(r: dict) -> dict[str, Any]:
    """Pull the fields we care about from the rich API response."""
    siege = r.get("siege") or {}
    adresse = siege.get("adresse") or r.get("adresse") or ""
    dirigeants = [
        d.get("nom") or d.get("prenom") or d.get("denomination", "")
        for d in (r.get("dirigeants") or [])
    ]
    dirigeants = [d for d in dirigeants if d]  # drop None / empty

    return {
        "found": True,
        "siren": r.get("siren", ""),
        "nom_complet": r.get("nom_complet", ""),
        "date_creation": r.get("date_creation", ""),
        "etat_administratif": r.get("etat_administratif", ""),
        "adresse": adresse,
        "dirigeants": dirigeants,
        "activite_principale": r.get("activite_principale", ""),
        "error": None,
    }


def main() -> int:
    """CLI: pass a SIREN, SIRET, or name as argv[1]."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: fr_recherche.py <SIREN_or_name>")
        return 1
    result = fr_search(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("found") else 1


if __name__ == "__main__":
    sys.exit(main())
