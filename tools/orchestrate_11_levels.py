#!/usr/bin/env python3
"""
orchestrate_11_levels.py — Per-country 11-level search & lead discovery playbook for BILLSzuka.

Levels (L0-L11 per methodology.md):
  L0: Pre-flight validation (NIP checksum + Registry name match)
  L1: Web Search (B2B phrases + operators)
  L2: Marketplaces & Aggregators (Allegro, Ceneo, OLX, Heureka, Bazos, etc.)
  L3: State Registries (CEIDG/KRS, ARES, ORSR, ListaFirme, Rekvizitai, e-Äriregister, Pappers, etc.)
  L4: Customs & Regulatory (CN 8479 89 97 90, Excise, White List VAT, BDO)
  L5: DNS WHOIS & Certificate Transparency (crt.sh)
  L6: Trade Fairs (InterTabac, World Vape Show, Eurocis, Vapexpo)
  L7: Social OSINT (FB groups, YouTube review comments, Reddit, TikTok)
  L8: B2B Catalogs (Aleo, PKT, Panorama Firm, Firmy.cz, Kompass, Europages, ENTIA)
  L9: LLM Scouting (OpenRouter multi-model extraction guarded by L0)
  L10: EUIPO Trademark Search (euipo.europa.eu/eSearch)
  L11: Public Procurement (BZP PL / TED EU)

Usage:
  python3 tools/orchestrate_11_levels.py --list
  python3 tools/orchestrate_11_levels.py --country PL [--level L1]
"""

import argparse
import csv
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, make_id, rynek_skala_for

COUNTRY_PLANS = {
    "PL": {
        "name": "Polska",
        "csv": "data/Polska/catalog-B-PL.csv",
        "L0_preflight": "NIP Mod 11 Checksum + KRS API name match (api-krs.ms.gov.pl) + CEIDG v3",
        "L1_web_search": [
            'site:linkedin.com/in "hurtownia tytoniowa"',
            '"hurtownia akcesoriów tytoniowych" cennik',
            '"dystrybutor tytoniu" oferta',
            '"nabijarki hurtownia" Warszawa OR Kraków OR Poznań OR Wrocław',
        ],
        "L2_marketplace": ["allegro.pl (Allegro REST API seller search)", "ceneo.pl", "olx.pl", "erli.pl", "inpostbuy.pl"],
        "L3_registries": {
            "CEIDG": "https://dane.biznes.gov.pl/api/ceidg/v3/firmy",
            "KRS": "https://api-krs.ms.gov.pl",
            "REGON": "https://wyszukiwarkaregon.stat.gov.pl",
            "PKD": ["46.35.Z", "46.69.Z", "46.43.Z", "47.26.Z", "47.11.Z"],
        },
        "L4_customs_regulatory": [
            "CN 8479 89 97 90 (maszyny specjalne)",
            "Biała Lista VAT (podatki.gov.pl)",
            "KAS Rejestr Pośredniczących Podmiotów Tytoniowych",
            "BDO Rejestr (rejestr-bdo.mos.gov.pl)",
        ],
        "L5_dns_whois": {"tld": ".pl", "whois": "whois.dns.pl", "crt_sh": "crt.sh/?q=%.powermatic.pl"},
        "L6_trade_fairs": ["InterTabac Dortmund", "Vapexpo PL", "Tobacco Plus Expo"],
        "L7_social_osint": [
            "facebook.com/groups/nabijarki-do-tytoniu",
            "facebook.com/groups/powermatic-polska",
            "youtube.com ('PowerMatic recenzja' comment buyers)",
        ],
        "L8_B2B_catalogs": ["aleo.com", "pkt.pl", "panoramafirm.pl", "bizraport.pl", "nipgo.pl", "europages.pl"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "EUIPO eSearch (PowerMatic / Hawk trademark owners)",
        "L11_procurement": "BZP PL (ezamowienia.gov.pl) CPV 15800000-6",
    },
    "CZ": {
        "name": "Czechy",
        "csv_B": "data/Czechy/catalog-B-CZ.csv",
        "csv_A": "data/Czechy/catalog-A-CZ.csv",
        "L0_preflight": "IČO 8-digit modulo 11 check + ARES API name match (ares.gov.cz)",
        "L1_web_search": [
            '"velkoobchod tabák" ceník',
            '"kuřácké potřeby velkoobchod"',
            '"doutníky velkoobchod" Praha OR Brno OR Ostrava',
            '"nabiječka cigaret" velkoobchod OR distributor',  # nabijarka-specific
            '"plnička tabáku" OR "plnička cigaret" velkoobchod',  # nabijarka-specific
        ],
        "L2_marketplace": ["heureka.cz", "zbozi.cz", "aukro.cz", "alza.cz", "bazos.cz"],
        "L3_registries": {
            "ARES": "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ICO}",
            "VIES": "http://ec.europa.eu/taxation_customs/vies/",
            "NACE": ["46.35", "46.69", "47.26"],
        },
        "L4_customs_regulatory": ["Celní správa ČR (Czech Customs excise tax list)"],
        "L5_dns_whois": {"tld": ".cz", "whois": "whois.nic.cz", "crt_sh": "crt.sh/?q=%.tabak.cz"},
        "L6_trade_fairs": ["InterTabac (CZ exhibitors)", "Tabak Expo Praha"],
        "L7_social_osint": ["facebook.com/groups (CZ tobacco)", "bazos.cz seller profiles"],
        "L8_B2B_catalogs": ["firmy.cz", "kompass.com", "europages.cz"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "EUIPO eSearch CZ applicants",
        "L11_procurement": "NEN CZ (nen.nipez.cz)",
    },
    "SK": {
        "name": "Słowacja",
        "csv_B": "data/Słowacja/catalog-B-SK.csv",
        "csv_A": "data/Słowacja/catalog-A-SK.csv",
        "L0_preflight": "IČO 8-digit check + FinStat / ORSR html match",
        "L1_web_search": [
            '"veľkoobchod tabak" cenník',
            '"fajčiarske potreby veľkoobchod"',
            '"tabak predaj" Bratislava OR Košice',
            '"plničky cigariet" veľkoobchod OR distribútor',  # nabijarka-specific
            '"tabakové príslušenstvo" veľkoobchod',  # nabijarka-specific
        ],
        "L2_marketplace": ["heureka.sk", "bazos.sk", "mall.sk", "alza.sk"],
        "L3_registries": {"ORSR": "https://www.orsr.sk", "FinStat": "https://finstat.sk/{ICO}", "VIES": True},
        "L4_customs_regulatory": ["Finančná správa SR (SK Customs)"],
        "L5_dns_whois": {"tld": ".sk", "whois": "whois.sk-nic.sk"},
        "L6_trade_fairs": ["InterTabac (SK exhibitors)"],
        "L7_social_osint": ["facebook.com/groups (SK tobacco)", "bazos.sk"],
        "L8_B2B_catalogs": ["firmy.sk", "kompass.com", "europages.sk"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "EUIPO eSearch SK applicants",
        "L11_procurement": "UVO SK (uvo.gov.sk)",
    },
    "RO": {
        "name": "Rumunia",
        "csv_B": "data/Rumunia/catalog-B-RO.csv",
        "csv_A": "data/Rumunia/catalog-A-RO.csv",
        "L0_preflight": "CUI format check + ListaFirme / ONRC match",
        "L1_web_search": [
            '"angrosist tutun" pret',
            '"distribuitor tutun"',
            '"articole fumat en-gros" București',
            '"injectoare tigari" angrosist OR distribuitor',  # nabijarka-specific
            '"masina umplut tigari" gros',  # nabijarka-specific
        ],
        "L2_marketplace": ["emag.ro", "olx.ro", "cel.ro"],
        "L3_registries": {"ListaFirme": "https://www.listafirme.ro", "ONRC": "https://myreconc.onrc.ro", "VIES": True},
        "L4_customs_regulatory": ["Autoritatea Vamală Română"],
        "L5_dns_whois": {"tld": ".ro", "whois": "whois.rotld.ro"},
        "L6_trade_fairs": ["Indagra / Romexpo FMCG"],
        "L7_social_osint": ["facebook.com/groups (RO tobacco)", "olx.ro sellers"],
        "L8_B2B_catalogs": ["listafirme.ro", "firmegala.ro", "europages.ro"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "OSIM / EUIPO",
        "L11_procurement": "SEAP RO (e-licitatie.ro)",
    },
    "LT": {
        "name": "Litwa",
        "csv_B": "data/Litwa/catalog-B-LT.csv",
        "csv_A": "data/Litwa/catalog-A-LT.csv",
        "L0_preflight": "Įmonės kodas 9-digit check + Rekvizitai VZ match",
        "L1_web_search": [
            '"didmeninė prekyba tabaku"',
            '"rūkymo reikmenys didmena" Vilnius OR Kaunas',
            '"cigarečių pildymo mašina" didmena OR distributorius',  # nabijarka-specific
            '"tabako priedai" didmeninė prekyba',  # nabijarka-specific
        ],
        "L2_marketplace": ["pigu.lt", "skelbiu.lt"],
        "L3_registries": {"Rekvizitai": "https://rekvizitai.vz.lt", "JAR": "https://www.registrucentras.lt", "VIES": True},
        "L4_customs_regulatory": ["Muitinės departamentas prie LR FM"],
        "L5_dns_whois": {"tld": ".lt", "whois": "whois.domreg.lt"},
        "L6_trade_fairs": ["RIGA FOOD / Baltic Expo"],
        "L7_social_osint": ["skelbiu.lt sellers", "FB groups LT"],
        "L8_B2B_catalogs": ["rekvizitai.vz.lt", "visalietuva.lt", "europages.lt"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "VPB / EUIPO",
        "L11_procurement": "CVP IS LT (cvpis.eviesiejipirkimai.lt)",
    },
    "LV": {
        "name": "Łotwa",
        "csv_B": "data/Łotwa/catalog-B-LV.csv",
        "csv_A": "data/Łotwa/catalog-A-LV.csv",
        "L0_preflight": "Reģistrācijas numurs 11-digit check + LURSOFT match",
        "L1_web_search": [
            '"tabakas vairumtirdzniecība"',
            '"smēķēšanas piederumi vairumā" Rīga',
            '"cigarešu uzpildes mašīna" vairumtirdzniecība',  # nabijarka-specific
            '"tabakas piederumi" vairumtirdzniecība distribūtors',  # nabijarka-specific
        ],
        "L2_marketplace": ["ss.com", "220.lv"],
        "L3_registries": {"Lursoft": "https://www.lursoft.lv", "UR": "https://www.ur.gov.lv", "VIES": True},
        "L4_customs_regulatory": ["VID Muitas pārvalde"],
        "L5_dns_whois": {"tld": ".lv", "whois": "whois.nic.lv"},
        "L6_trade_fairs": ["Riga Food Expo"],
        "L7_social_osint": ["ss.com sellers", "FB groups LV"],
        "L8_B2B_catalogs": ["firmas.lv", "zl.lv", "europages.lv"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "LRPV / EUIPO",
        "L11_procurement": "EIS LV (eis.gov.lv)",
    },
    "EE": {
        "name": "Estonia",
        "csv_B": "data/Estonia/catalog-B-EE.csv",
        "csv_A": "data/Estonia/catalog-A-EE.csv",
        "L0_preflight": "Registrikood 8-digit check + e-Äriregister match",
        "L1_web_search": [
            '"tubakatoodete hulgimüük"',
            '"suitsetamistarvikud hulgimüük" Tallinn',
            '"sigarettide täitemasin" hulgimüük OR distributoor',  # nabijarka-specific
            '"tubakatarvikud" hulgimüük distributorid',  # nabijarka-specific
        ],
        "L2_marketplace": ["kuldnebors.ee", "okidoki.ee", "kaup24.ee"],
        "L3_registries": {"e-Ariregister": "https://ariregister.rik.ee", "VIES": True},
        "L4_customs_regulatory": ["Maksu- ja Tolliamet"],
        "L5_dns_whois": {"tld": ".ee", "whois": "whois.tld.ee"},
        "L6_trade_fairs": ["Tallinn FoodFest"],
        "L7_social_osint": ["okidoki.ee sellers", "FB groups EE"],
        "L8_B2B_catalogs": ["inforegister.ee", "eesti.ee", "europages.ee"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "EPA / EUIPO",
        "L11_procurement": "RHR EE (riigihanked.eesti.ee)",
    },
    "FR": {
        "name": "Francja",
        "csv_B": "data/Francja/catalog-B-FR.csv",
        "csv_A": "data/Francja/catalog-A-FR.csv",
        "L0_preflight": "SIREN 9-digit / SIRET 14-digit Luhn check + Pappers API match",
        "L1_web_search": [
            '"grossiste tabac" prix',
            '"grossiste articles fumeurs" Paris OR Lyon OR Marseille',
            '"machine injecteur cigarettes" grossiste distributeur',  # nabijarka-specific
            '"grossiste accessoires tabac" distributeur France',  # nabijarka-specific
        ],
        "L2_marketplace": ["leboncoin.fr", "cdiscount.com", "amazon.fr"],
        "L3_registries": {"Pappers": "https://www.pappers.fr", "Societe": "https://www.societe.com", "VIES": True},
        "L4_customs_regulatory": ["Douanes françaises (douane.gouv.fr)"],
        "L5_dns_whois": {"tld": ".fr", "whois": "whois.afnic.fr"},
        "L6_trade_fairs": ["Losangexpo Paris", "Vapexpo Paris"],
        "L7_social_osint": ["leboncoin.fr pro sellers", "FB groups FR"],
        "L8_B2B_catalogs": ["pappers.fr", "societe.com", "kompass.fr", "europages.fr"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "INPI / EUIPO",
        "L11_procurement": "BOAMP FR (boamp.fr)",
    },
    "MD": {
        "name": "Mołdawia",
        "csv_B": "data/Mołdawia/catalog-B-MD.csv",
        "csv_A": "data/Mołdawia/catalog-A-MD.csv",
        "L0_preflight": "IDNO 13-digit check + CIS registry match",
        "L1_web_search": [
            '"gros tutun" Chisinau',
            '"accesorii fumat gros"',
            '"masini injectat tigari" angrosist Moldova',  # nabijarka-specific
        ],
        "L2_marketplace": ["999.md"],
        "L3_registries": {"CIS": "https://cis.gov.md", "Apollo": "Apollo.io fallback"},
        "L4_customs_regulatory": ["Serviciul Vamal al Republicii Moldova"],
        "L5_dns_whois": {"tld": ".md", "whois": "whois.nic.md"},
        "L6_trade_fairs": ["Moldagrotech / Expo Moldova"],
        "L7_social_osint": ["999.md sellers", "FB groups MD"],
        "L8_B2B_catalogs": ["yellowpages.md", "kompass.md"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "AGEPI MD",
        "L11_procurement": "MTender MD (mtender.gov.md)",
    },
    "BG": {
        "name": "Bułgaria",
        "csv_B": "data/Bułgaria/catalog-B-BG.csv",
        "csv_A": "data/Bułgaria/catalog-A-BG.csv",
        "L0_preflight": "EIK/UIC 9-digit check + Trade Register match",
        "L1_web_search": [
            '"търговия na едро тютюн"',
            '"аксесоари за пушене едро" София',
            '"машина за пълнене цигари" едро дистрибутор',  # nabijarka-specific
            '"тютюневи принадлежности" едро дистрибутор',  # nabijarka-specific
        ],
        "L2_marketplace": ["olx.bg", "bazar.bg"],
        "L3_registries": {"ASP": "https://portal.registryagency.bg", "VIES": True},
        "L4_customs_regulatory": ["Агенция Митници (customs.bg)"],
        "L5_dns_whois": {"tld": ".bg", "whois": "whois.register.bg"},
        "L6_trade_fairs": ["Plovdiv Fair"],
        "L7_social_osint": ["olx.bg sellers", "bazar.bg"],
        "L8_B2B_catalogs": ["firmite.bg", "goldenpages.bg", "europages.bg"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "BPO / EUIPO",
        "L11_procurement": "AOP BG (aop.bg)",
    },
    "SI": {
        "name": "Słowenia",
        "csv_B": "data/Słowenia/catalog-B-SI.csv",
        "csv_A": "data/Słowenia/catalog-A-SI.csv",
        "L0_preflight": "Davčna številka 8-digit check + AJPES match",
        "L1_web_search": [
            '"trgovina na debelo tobak"',
            '"tobačni izdelki debelo" Ljubljana',
            '"stroji za polnjenje cigaret" veleprodaja',  # nabijarka-specific
            '"tobačni pribor" veleprodaja distributer',  # nabijarka-specific
        ],
        "L2_marketplace": ["bolha.com"],
        "L3_registries": {"AJPES": "https://www.ajpes.si", "VIES": True},
        "L4_customs_regulatory": ["FURS (Finančna uprava RS)"],
        "L5_dns_whois": {"tld": ".si", "whois": "whois.register.si"},
        "L6_trade_fairs": ["MOS Celje"],
        "L7_social_osint": ["bolha.com sellers"],
        "L8_B2B_catalogs": ["bizi.si", "piran.si", "europages.si"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "UIL / EUIPO",
        "L11_procurement": "E-Naročanje SI (enarocanje.si)",
    },
    "HR": {
        "name": "Chorwacja",
        "csv_B": "data/Chorwacja/catalog-B-HR.csv",
        "csv_A": "data/Chorwacja/catalog-A-HR.csv",
        "L0_preflight": "OIB 11-digit ISO 7064 Mod 11,10 check + Sudreg match",
        "L1_web_search": [
            '"veleprodaja duhana"',
            '"pribor za pušenje veleprodaja" Zagreb',
            '"stroj za punjenje cigareta" veleprodaja',  # nabijarka-specific
            '"duhanski pribor" veleprodaja distributer Hrvatska',  # nabijarka-specific
        ],
        "L2_marketplace": ["njuskalo.hr"],
        "L3_registries": {"Sudreg": "https://sudreg.pravosudje.hr", "VIES": True},
        "L4_customs_regulatory": ["Carinska uprava HR"],
        "L5_dns_whois": {"tld": ".hr", "whois": "whois.dns.hr"},
        "L6_trade_fairs": ["Zagrebački Velesajam"],
        "L7_social_osint": ["njuskalo.hr sellers"],
        "L8_B2B_catalogs": ["poslovna.hr", "fininfo.hr", "europages.hr"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "DZIV / EUIPO",
        "L11_procurement": "EOJN HR (eojn.nn.hr)",
    },
    "RS": {
        "name": "Serbia (out-of-scope)",
        "csv_A": "data/Serbia/catalog-A-RS.csv",
        "csv_B": "data/Serbia/catalog-B-RS.csv",
        "L0_preflight": "PIB 9-digit check + APR name match (apr.gov.rs)",
        "L1_web_search": [
            '"velikoprodaja duvana"',
            '"pribor za pušenje" veleprodaja Beograd OR "Novi Sad"',
            '"mašina za punjenje cigareta" veleprodaja OR distributer',  # nabijarka-specific
            '"električna punilica za duvan" prodaja',  # nabijarka-specific
        ],
        "L2_marketplace": ["kupujemprodajem.com", "limundo.com"],
        "L3_registries": {"APR": "https://www.apr.gov.rs", "Carina": "https://www.carina.rs"},
        "L4_customs_regulatory": ["Uprava Carina RS (carina.rs)", "Poreska uprava RS"],
        "L5_dns_whois": {"tld": ".rs", "whois": "whois.rnids.rs"},
        "L6_trade_fairs": ["InterTabac (RS exhibitors)", "Sajam privrede Beograd"],
        "L7_social_osint": ["kupujemprodajem.com sellers", "FB groups RS"],
        "L8_B2B_catalogs": ["ekapija.com", "companywall.rs", "yubuild.com"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek/deepseek-chat", "env_key": "OPENROUTER_API_KEY"},
        "L10_trademark": "ZIS RS (zis.gov.rs) / EUIPO",
        "L11_procurement": "Portal javnih nabavki RS (jnportal.ujn.gov.rs)",
    },
}


def _csv_label(plan: dict) -> str:
    """First available CSV path for a country plan (old 'csv' or new 'csv_A'/'csv_B')."""
    return plan.get("csv") or plan.get("csv_B") or plan.get("csv_A") or "—"


def add_lead(country: str, name: str, category: str, nip_clean: str, rejestr_id: str, source: str, catalog: str = "B") -> bool:
    """Manually append a verified lead to data/{Kraj}/catalog-{A|B}-{ISO}.csv."""
    country = country.upper()
    catalog = catalog.upper()
    plan = COUNTRY_PLANS.get(country)
    if not plan:
        print(f"❌ Unknown country: {country}")
        return False

    # Support both old 'csv' key (catalog-B) and new 'csv_A'/'csv_B' keys
    if f"csv_{catalog}" in plan:
        csv_rel = plan[f"csv_{catalog}"]
    elif "csv" in plan:
        csv_rel = plan["csv"]  # backward compat
    else:
        print(f"❌ No CSV path for catalog-{catalog} in country plan: {country}")
        return False

    csv_path = ROOT / csv_rel
    if not csv_path.exists():
        print(f"❌ CSV path not found: {csv_path}")
        return False

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not fieldnames or fieldnames != CANONICAL_SCHEMA:
        fieldnames = CANONICAL_SCHEMA

    existing_nips = {r.get("nip_vat", "").replace(" ", "").upper() for r in rows if r.get("nip_vat")}
    nip_norm = nip_clean.replace(" ", "").upper()
    if nip_norm in existing_nips:
        print(f"   ℹ️  Skip duplicate NIP {nip_norm} ({name})")
        return False

    counter = len(rows) + 1
    row = {k: "" for k in fieldnames}
    row["id_unikalne"] = make_id(country, catalog, counter)
    row["kategoria"] = category
    row["nazwa_firmy"] = name
    row["kraj"] = country
    row["nip_vat"] = nip_norm
    row["rejestr_id"] = rejestr_id if rejestr_id else "brak"
    row["tier"] = "hurtownik"
    row["zrodlo_danych"] = source
    row["data_weryfikacji"] = time.strftime("%Y-%m-%d")
    row["flagi"] = f"{time.strftime('%Y-%m-%d')} ⚠️ DO-WERYFIKACJI"
    row["rynek_skala"] = rynek_skala_for(country)

    rows.append(row)
    tmp_path = csv_path.with_suffix(".csv.tmp")
    with open(tmp_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    tmp_path.replace(csv_path)
    print(f"   ➕ Added lead: {name} ({country}, NIP: {nip_norm}, {rejestr_id})")
    return True


def list_countries():
    print("=" * 80)
    print("  BILLSzuka 11-level Search Options — 13 tracked countries (12 EU + RS)")
    print("=" * 80)
    for code, plan in COUNTRY_PLANS.items():
        n_levels = sum(1 for k in plan if k.startswith("L") and "_" in k)
        n_mkt = len(plan.get("L2_marketplace", []))
        print(f"  {code:2s} | {plan['name']:14s} | {n_levels:2d} Search Levels | {n_mkt} Marketplaces | CSV: {_csv_label(plan)}")


def show_country(country: str, target_level: str = None):
    plan = COUNTRY_PLANS.get(country.upper())
    if not plan:
        print(f"❌ Unknown country: {country}")
        return

    print("=" * 80)
    print(f"  Search Options: {country.upper()} — {plan['name']}  (CSV: {_csv_label(plan)})")
    print("=" * 80)

    for key, val in plan.items():
        if key in ("name", "csv", "csv_A", "csv_B"):
            continue
        if target_level and not key.lower().startswith(target_level.lower()):
            continue

        print(f"\n📌 [{key}]:")
        if isinstance(val, list):
            for item in val:
                print(f"   • {item}")
        elif isinstance(val, dict):
            for k, v in val.items():
                print(f"   • {k}: {v}")
        else:
            print(f"   • {val}")


def main():
    ap = argparse.ArgumentParser(description="BILLSzuka 11-level search strategy runner")
    ap.add_argument("--list", action="store_true", help="List search summary for all 12 countries")
    ap.add_argument("--country", help="Show search options for a country (e.g. PL, CZ, SK)")
    ap.add_argument("--level", help="Filter specific search level (e.g. L1, L2, L3)")
    args = ap.parse_args()

    if args.list:
        list_countries()
    elif args.country:
        show_country(args.country, target_level=args.level)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
