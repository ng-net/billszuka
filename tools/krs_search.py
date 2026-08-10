#!/usr/bin/env python3
"""
krs_search.py — Automatyczne wyszukiwanie firm PL + pobieranie pełnego odpisu KRS.

Chain:
  NIP/REGON → REGON API (BIR1.1) → KRS number → KRS API → full extract

Wymaga klucza REGON (USER_KEY). Zamów bezpłatnie: regon_bir@stat.gov.pl
Tymczasowo można użyć klucza testowego: abcde12345abcde12345 (production rate-limited)

Usage:
  python3 tools/krs_search.py --nip 5140361901
  python3 tools/krs_search.py --regon 020089511
  python3 tools/krs_search.py --krs 0001074645
  python3 tools/krs_search.py --nip 5140361901 --financials   # pobiera też sprawozdanie finansowe

Env: .env → REGON_API_KEY=...
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ───────────────────────── config ─────────────────────────

REGON_LOGIN_URL = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzworek.svc"
REGON_SEARCH_URL = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzworek.svc/ajax"

KRS_BASE = "https://api-krs.ms.gov.pl/api/krs"
KRS_FULL_EXTRACT = f"{KRS_BASE}/OdpisAktualny"
KRS_BASIC_EXTRACT = f"{KRS_BASE}/OdpisPelny"

KRS_FINANCIALS_SEARCH = "https://ekrs.ms.gov.pl/rdf/pd/search_df"


def load_env():
    env = {}
    env_path = ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env[k] = v
    return env


ENV = load_env()
REGON_KEY = ENV.get("REGON_API_KEY", "")


# ───────────────────────── SOAP client (stdlib only) ─────────────────────────

def soap_call(url, soap_body, soap_action=""):
    envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">
  <soap:Header>
    <wsa:Action>{soap_action}</wsa:Action>
    <wsa:To>{url}</wsa:To>
  </soap:Header>
  <soap:Body>
    {soap_body}
  </soap:Body>
</soap:Envelope>"""

    req = urllib.request.Request(
        url,
        data=envelope.encode("utf-8"),
        headers={
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"{soap_action}"',
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8")


# ───────────────────────── REGON API ─────────────────────────

class RegonSession:
    """Lightweight REGON BIR1.1 client using SOAP. No external deps."""

    def __init__(self, api_key=REGON_KEY):
        if not api_key:
            raise RuntimeError(
                "REGON_API_KEY not set. Zamów klucz bezpłatnie: regon_bir@stat.gov.pl"
            )
        self.key = api_key
        self.sid = None

    def login(self):
        body = f'<Zaloguj xmlns="http://tempuri.org/"><pKluczUzytkownika>{self.key}</pKluczUzytkownika></Zaloguj>'
        xml = soap_call(REGON_LOGIN_URL, body, "http://tempuri.org/IZworekUslugaBIR/Zaloguj")
        root = ET.fromstring(xml)
        # parse <ZalogujResult>...</ZalogujResult>
        result = root.find(".//{http://tempuri.org/}ZalogujResult")
        if result is None:
            raise RuntimeError(f"REGON login failed: {xml[:300]}")
        self.sid = result.text
        return self.sid

    def _search(self, method, value):
        if not self.sid:
            self.login()
        body = (
            f'<{method} xmlns="http://tempuri.org/">'
            f'<pParametryWyszukiwania><Nip>{value}</Nip></pParametryWyszukiwania>'
            f'</{method}>'
        )
        xml = soap_call(REGON_SEARCH_URL, body, f"http://tempuri.org/IZworekUslugaBIR/{method}")
        return xml

    def get_by_nip(self, nip):
        # NIP must be 10 digits, no PL prefix, no spaces
        nip = re.sub(r"\D", "", nip)
        if len(nip) != 10:
            raise ValueError(f"NIP must be 10 digits, got: {nip}")
        return self._search("DaneSzukajPodmiotyPoNip", nip)

    def get_by_regon(self, regon):
        regon = re.sub(r"\D", "", regon)
        if len(regon) not in (9, 14):
            raise ValueError(f"REGON must be 9 or 14 digits, got: {regon}")
        return self._search("DaneSzukajPodmiotyPoRegon", regon)

    def get_by_krs(self, krs):
        krs = re.sub(r"\D", "", krs).zfill(10)
        return self._search("DaneSzukajPodmiotyPoKrs", krs)

    def logout(self):
        if not self.sid:
            return
        body = f'<Wyloguj xmlns="http://tempuri.org/"><pIdentyfikatorSesji>{self.sid}</pIdentyfikatorSesji></Wyloguj>'
        try:
            soap_call(REGON_LOGIN_URL, body, "http://tempuri.org/IZworekUslugaBIR/Wyloguj")
        except Exception:
            pass
        self.sid = None


def parse_regon_response(xml_string):
    """Parse the SOAP XML and return list of {Regon, Nip, Krs, Nazwa, Wojewodztwo, ...}"""
    root = ET.fromstring(xml_string)
    ns = {"d": "http://tempuri.org/"}
    dane = root.find(".//d:Dane", ns)
    if dane is None:
        # Try without namespace
        dane = root.find(".//Dane")
    if dane is None:
        return []

    out = []
    # Real structure: each child of <root> is a company, with Krs/Nip/Regon/Nazwa...
    # The BIR1.1 endpoint returns XML where each direct child of root is a record
    for child in dane:
        record = {child.tag.split("}")[-1]: (child.text or "").strip() for child in child}
        out.append(record)
    return out


# ───────────────────────── KRS API (REST) ─────────────────────────

def krs_lookup(krs_number, full=True):
    """KRS REST API: https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{krs}"""
    krs = re.sub(r"\D", "", str(krs_number)).zfill(10)
    url = KRS_FULL_EXTRACT if full else KRS_BASIC_EXTRACT
    url = f"{url}/{krs}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"KRS API {e.code}: {e.reason}", "krs": krs}
    except Exception as e:
        return {"error": str(e), "krs": krs}


# ───────────────────────── financial documents ─────────────────────────

def krs_financials_url(krs_number):
    """Returns the search URL for KRS financial documents (.xml files)."""
    krs = re.sub(r"\D", "", str(krs_number)).zfill(10)
    return f"{KRS_FINANCIALS_SEARCH}?Krs={krs}"


# ───────────────────────── CLI ─────────────────────────

def main():
    parser = argparse.ArgumentParser(description="KRS lookup via REGON + KRS API")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--nip", help="10-cyfrowy NIP")
    group.add_argument("--regon", help="9- lub 14-cyfrowy REGON")
    group.add_argument("--krs", help="KRS (z lub bez zer wiodących)")
    parser.add_argument("--financials", action="store_true",
                        help="Pokaż URL do Przeglądarki Dokumentów Finansowych KRS")
    parser.add_argument("--json", action="store_true", help="Wyjście w formacie JSON")
    args = parser.parse_args()

    result = {"queried_at": datetime.now(timezone.utc).isoformat()}

    # 1. REGON search
    if args.nip or args.regon:
        try:
            session = RegonSession()
        except RuntimeError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

        try:
            if args.nip:
                xml = session.get_by_nip(args.nip)
                result["queried_via"] = "REGON.nip"
                result["query_value"] = args.nip
            else:
                xml = session.get_by_regon(args.regon)
                result["queried_via"] = "REGON.regon"
                result["query_value"] = args.regon

            records = parse_regon_response(xml)
            result["regon_records"] = records

            # Pick KRS from first record
            krs = None
            if records:
                krs_raw = records[0].get("Krs", "")
                krs = re.sub(r"\D", "", krs_raw).zfill(10) if krs_raw else None
            result["krs"] = krs
        finally:
            session.logout()
    else:
        krs = re.sub(r"\D", "", args.krs).zfill(10)
        result["krs"] = krs
        result["queried_via"] = "direct"

    # 2. KRS API full extract
    if result.get("krs"):
        krs_data = krs_lookup(result["krs"], full=True)
        result["krs_full_extract"] = krs_data

        if args.financials:
            result["financials_url"] = krs_financials_url(result["krs"])

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Pretty print
    print(f"🔍 Queried: {result.get('queried_via')} = {result.get('query_value')}")
    if result.get("regon_records"):
        print("\n📋 REGON records:")
        for r in result["regon_records"]:
            print(f"  • {r.get('Nazwa', '?')}")
            print(f"    NIP: {r.get('Nip', '?')}  REGON: {r.get('Regon', '?')}  KRS: {r.get('Krs', '?')}")
            print(f"    Adres: {r.get('Ulica', '')} {r.get('NrNieruchomosci', '')} {r.get('NrLokalu', '')}, "
                  f"{r.get('KodPocztowy', '')} {r.get('Miejscowosc', '')}")
            print(f"    Typ: {r.get('Typ', '?')}")
    if result.get("krs_full_extract"):
        ext = result["krs_full_extract"]
        if "error" in ext:
            print(f"\n❌ KRS API error: {ext['error']}")
        else:
            print(f"\n✅ KRS {result['krs']} — pełny odpis pobrany")
            print(f"   Pola: {len(ext)} kluczy")
    if result.get("financials_url"):
        print(f"\n💰 Sprawozdania finansowe (.xml): {result['financials_url']}")


if __name__ == "__main__":
    main()
