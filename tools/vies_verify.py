#!/usr/bin/env python3
"""
vies_verify.py — EU VIES VAT validation module for BILLSzuka.

Uses the official EU VIES REST API:
  https://ec.europa.eu/taxation_customs/vies/rest-api/ms/{country_code}/vat/{vat_number}

No authentication required.
Returns structured dict:
  {
      "valid": bool,
      "country_code": str,
      "vat_number": str,
      "name": str,
      "address": str,
      "request_date": str,
      "error": str or None
  }
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

VIES_REST_URL = "https://ec.europa.eu/taxation_customs/vies/rest-api/ms/{country}/vat/{vat}"


def vies_lookup(vat_id: str, timeout: int = 10) -> dict:
    """Lookup VAT number in EU VIES.
    
    vat_id can be in formats: 'PL9590822602', 'CZ25221981', 'SK2020298285', '9590822602' (with country passed or inferred).
    """
    clean = re.sub(r"[^A-Za-z0-9]", "", vat_id).upper()
    if len(clean) < 4:
        return {"valid": False, "error": f"VAT ID za krótki: '{vat_id}'"}
    
    country = clean[:2]
    vat_num = clean[2:]
    
    # If first 2 chars are numbers, country is not in clean string
    if country.isdigit():
        return {"valid": False, "error": f"Brak kodu kraju w VAT ID: '{vat_id}'"}
        
    url = VIES_REST_URL.format(country=country, vat=vat_num)
    headers = {"User-Agent": "BILLSzuka-Verifier/2.0", "Accept": "application/json"}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            
        valid = bool(data.get("isValid", False))
        name = (data.get("name") or "").strip()
        address = (data.get("address") or "").strip()
        user_error = data.get("userError")
        
        if user_error and user_error != "VALID":
            return {"valid": False, "error": f"VIES Error: {user_error}"}
            
        return {
            "valid": valid,
            "country_code": country,
            "vat_number": vat_num,
            "name": name if name != "---" else "",
            "address": address if address != "---" else "",
            "request_date": data.get("requestDate", time.strftime("%Y-%m-%d")),
            "error": None if valid else "VAT ID nieaktywny w VIES",
        }
    except urllib.error.HTTPError as e:
        if e.code == 400:
            return {"valid": False, "error": f"VIES: Niepoprawny format VAT ({country}{vat_num})"}
        elif e.code == 404:
            return {"valid": False, "error": f"VIES: Nie znaleziono VAT {country}{vat_num}"}
        return {"valid": False, "error": f"VIES HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"valid": False, "error": f"VIES connection error: {e}"}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_vats = ["PL9590822602", "CZ25221981", "PL0000000000"]
        print("--- Testing VIES Lookup ---")
        for vat in test_vats:
            res = vies_lookup(vat)
            print(f"VAT: {vat} -> Valid: {res['valid']} | Name: {res.get('name')} | Err: {res.get('error')}")
        return 0
    elif len(sys.argv) > 1:
        res = vies_lookup(sys.argv[1])
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0
    else:
        print("Usage: python3 vies_verify.py <VAT_ID> or --test")
        return 1


if __name__ == "__main__":
    sys.exit(main())
