#!/usr/bin/env python3
"""
scrapers_registry.py — Web registry scrapers for non-API countries (SK, RO, LT, FR, EE, SI, HR).

Provides fallback web scraping logic for:
  - SK (Slovakia): ORSR / FinStat HTML search
  - RO (Romania): ListaFirme / Confidas HTML search
  - LT (Lithuania): Rekvizitai VZ search
  - FR (France): Pappers / Societe search

Returns standardized firm dictionaries compatible with verify_api.py.
"""

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl,en-US;q=0.7,en;q=0.3",
}


def fetch_url(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return ""


def scrape_sk_orsr(ico_or_name: str) -> dict | None:
    """Scrape Slovakia ORSR / FinStat for firm info."""
    clean = re.sub(r"\D", "", ico_or_name)
    if len(clean) == 8:
        # Search by ICO on FinStat / ORSR aggregator
        url = f"https://finstat.sk/{clean}"
        html = fetch_url(url)
        if html:
            title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
            address_m = re.search(r"Adresa:?.*?<dd[^>]*>(.*?)</dd>", html, re.DOTALL | re.IGNORECASE)
            dic_m = re.search(r"DIČ:?.*?<dd[^>]*>(.*?)</dd>", html, re.DOTALL | re.IGNORECASE)
            
            if title_m:
                nazwa = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
                adres = re.sub(r"<[^>]+>", "", address_m.group(1)).strip() if address_m else ""
                dic = re.sub(r"<[^>]+>", "", dic_m.group(1)).strip() if dic_m else ""
                return {
                    "nazwa": nazwa,
                    "ico": clean,
                    "dic": dic,
                    "adres": adres,
                    "kraj": "SK",
                    "zrodlo": "FinStat SK Scraper",
                }
    return None


def scrape_ro_listafirme(cui_or_name: str) -> dict | None:
    """Scrape Romania ListaFirme for CUI/Name info."""
    clean = re.sub(r"\D", "", cui_or_name)
    if len(clean) >= 6 and len(clean) <= 10:
        url = f"https://www.listafirme.ro/search.asp?q={clean}"
        html = fetch_url(url)
        if html:
            title_m = re.search(r"<h1[^>]*>(.*?)</h1>|<h2><a[^>]*>(.*?)</a></h2>", html, re.DOTALL | re.IGNORECASE)
            if title_m:
                nazwa = re.sub(r"<[^>]+>", "", title_m.group(1) or title_m.group(2)).strip()
                return {
                    "nazwa": nazwa,
                    "cui": clean,
                    "kraj": "RO",
                    "zrodlo": "ListaFirme RO Scraper",
                }
    return None


def scrape_lt_rekvizitai(code_or_name: str) -> dict | None:
    """Scrape Lithuania Rekvizitai for company info."""
    clean = re.sub(r"\D", "", code_or_name)
    if len(clean) == 9:
        url = f"https://rekvizitai.vz.lt/en/company-search/1/?code={clean}"
        html = fetch_url(url)
        if html:
            title_m = re.search(r'<a class="company-title"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
            if title_m:
                nazwa = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
                return {
                    "nazwa": nazwa,
                    "imones_kodas": clean,
                    "kraj": "LT",
                    "zrodlo": "Rekvizitai LT Scraper",
                }
    return None


def scrape_fr_pappers(siren_or_name: str) -> dict | None:
    """Scrape France Pappers for SIREN/SIRET company info."""
    clean = re.sub(r"\D", "", siren_or_name)
    if len(clean) == 9 or len(clean) == 14:
        siren = clean[:9]
        url = f"https://www.pappers.fr/entreprise/{siren}"
        html = fetch_url(url)
        if html:
            title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
            if title_m:
                nazwa = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
                return {
                    "nazwa": nazwa,
                    "siren": siren,
                    "kraj": "FR",
                    "zrodlo": "Pappers FR Scraper",
                }
    return None


def scrape_ee_ariregister(code_or_name: str) -> dict | None:
    """Scrape Estonia e-Äriregister or Inforegister."""
    clean = re.sub(r"\D", "", code_or_name)
    if len(clean) == 8:
        url = f"https://ariregister.rik.ee/eng/company/{clean}"
        html = fetch_url(url)
        if html:
            title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
            if title_m:
                nazwa = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
                return {
                    "nazwa": nazwa,
                    "registrikood": clean,
                    "kraj": "EE",
                    "zrodlo": "e-Äriregister EE Scraper",
                }
    return None


def scrape_lv_lursoft(code_or_name: str) -> dict | None:
    """Scrape Latvia Firmas.lv / Lursoft."""
    clean = re.sub(r"\D", "", code_or_name)
    if len(clean) == 11:
        url = f"https://www.firmas.lv/lv/uznemumi/{clean}"
        html = fetch_url(url)
        if html:
            title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
            if title_m:
                nazwa = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
                return {
                    "nazwa": nazwa,
                    "reg_num": clean,
                    "kraj": "LV",
                    "zrodlo": "Firmas.lv Scraper",
                }
    return None


def scrape_bg_papagal(eik_or_name: str) -> dict | None:
    """Scrape Bulgaria Papagal / Registry."""
    clean = re.sub(r"\D", "", eik_or_name)
    if len(clean) == 9:
        url = f"https://papagal.bg/eik/{clean}"
        html = fetch_url(url)
        if html:
            title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
            if title_m:
                nazwa = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
                return {
                    "nazwa": nazwa,
                    "eik": clean,
                    "kraj": "BG",
                    "zrodlo": "Papagal BG Scraper",
                }
    return None


def scrape_si_bizi(tax_or_name: str) -> dict | None:
    """Scrape Slovenia Bizi.si."""
    clean = re.sub(r"\D", "", tax_or_name)
    if len(clean) == 8:
        url = f"https://www.bizi.si/iskanje?q={clean}"
        html = fetch_url(url)
        if html:
            title_m = re.search(r'<h3 class="title[^>]*>(.*?)</h3>|<a class="title[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
            if title_m:
                nazwa = re.sub(r"<[^>]+>", "", title_m.group(1) or title_m.group(2)).strip()
                return {
                    "nazwa": nazwa,
                    "davcna": clean,
                    "kraj": "SI",
                    "zrodlo": "Bizi.si SI Scraper",
                }
    return None


def scrape_hr_poslovna(oib_or_name: str) -> dict | None:
    """Scrape Croatia Poslovna / Sudreg."""
    clean = re.sub(r"\D", "", oib_or_name)
    if len(clean) == 11:
        url = f"https://www.poslovna.hr/search.aspx?q={clean}"
        html = fetch_url(url)
        if html:
            title_m = re.search(r'<a class="subject-title[^>]*>(.*?)</a>|<h1[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
            if title_m:
                nazwa = re.sub(r"<[^>]+>", "", title_m.group(1) or title_m.group(2)).strip()
                return {
                    "nazwa": nazwa,
                    "oib": clean,
                    "kraj": "HR",
                    "zrodlo": "Poslovna HR Scraper",
                }
    return None


def registry_web_lookup(country: str, identifier_or_name: str) -> dict | None:
    """Router for web scrapers by country across the 11 non-PL project markets."""
    c = country.upper().strip()
    if c == "SK":
        return scrape_sk_orsr(identifier_or_name)
    elif c == "RO":
        return scrape_ro_listafirme(identifier_or_name)
    elif c == "LT":
        return scrape_lt_rekvizitai(identifier_or_name)
    elif c == "FR":
        return scrape_fr_pappers(identifier_or_name)
    elif c == "EE":
        return scrape_ee_ariregister(identifier_or_name)
    elif c == "LV":
        return scrape_lv_lursoft(identifier_or_name)
    elif c == "BG":
        return scrape_bg_papagal(identifier_or_name)
    elif c == "SI":
        return scrape_si_bizi(identifier_or_name)
    elif c == "HR":
        return scrape_hr_poslovna(identifier_or_name)
    return None


if __name__ == "__main__":
    if len(sys.argv) > 2:
        country = sys.argv[1]
        ident = sys.argv[2]
        res = registry_web_lookup(country, ident)
        print(json.dumps(res, indent=2, ensure_ascii=False) if res else "Brak wyników")
    else:
        print("Usage: python3 scrapers_registry.py <COUNTRY> <IDENTIFIER_OR_NAME>")

