#!/usr/bin/env python3
"""
orchestrate_9_levels.py — Per-country 9-level lead generation playbook for BILLSzuka.

9 levels (L1-L9) per methodology.md §L1-L9. Configured for all 12 countries.
No hardcoded lead data — only sources, queries, and registries to scan.
Agent populates real leads via add_lead() as they are discovered.

Run modes:
  python3 tools/orchestrate_9_levels.py --list              # show all 12 country plans
  python3 tools/orchestrate_9_levels.py --country PL        # show PL plan in detail
  python3 tools/orchestrate_9_levels.py --country PL --run  # mark as running (no auto-add)
"""

import sys
import csv
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


# ──────────────────────────────────────────────────────────────────────
# Per-country 9-level config
# Sources: methodology.md §7 (marketplace), §L1-L9, INTEL.md, {Kraj}.md
# ──────────────────────────────────────────────────────────────────────

COUNTRY_PLANS = {
    "PL": {
        "name": "Polska",
        "csv": "data/Polska/catalog-B-PL.csv",
        "regions": {
            "DS": "dolnośląskie", "KP": "kujawsko-pomorskie", "LD": "łódzkie",
            "LU": "lubelskie", "LB": "lubuskie", "MA": "małopolskie",
            "MZ": "mazowieckie", "OP": "opolskie", "PK": "podkarpackie",
            "PD": "podlaskie", "PM": "pomorskie", "SL": "śląskie",
            "SW": "świętokrzyskie", "WN": "warmińsko-mazurskie",
            "WP": "wielkopolskie", "ZP": "zachodniopomorskie",
        },
        "top_phrases_for_region": [
            "hurtownia tytoniowa", "sklep tytoniowy", "nabijarki hurtownia",
            "hurtownia akcesoriów tytoniowych", "dystrybutor tytoniu",
        ],
        "L1_web_search": [
            "hurtownia tytoniowa {miasto}",
            "sklep tytoniowy hurtownia {miasto}",
            "nabijarki hurtownia {miasto}",
        ],
        "L2_marketplace": ["allegro.pl", "ceneo.pl", "olx.pl", "amazon.pl", "ebay.pl",
                           "kaufland.pl", "inpostbuy.pl", "erli.pl"],
        "L3_registries": {
            "KRS": "https://api-krs.ms.gov.pl",
            "CEIDG": "https://dane.biznes.gov.pl",
            "REGON": "https://wyszukiwarkaregon.stat.gov.pl",
            "PKD": ["46.35Z", "46.69Z", "46.43Z", "47.26Z", "47.11Z", "47.19Z", "47.91Z"],
            "Biala_Lista_VAT": "https://www.podatki.gov.pl/wykaz-podatnikow-vat-wyszukiwarka",
            "BDO": "https://rejestr-bdo.mos.gov.pl",
            "KAS_rejestr_posrednikow": "https://www.gov.pl/web/kas/rejestr-posredniczacych-podmiotow-tytoniowych",
        },
        "L4_customs_regulatory": ["WSA/NSA orzeczenia (import tytoń)", "KAS akcyza"],
        "L5_dns_whois": {"tld": ".pl", "whois_server": "whois.dns.pl"},
        "L6_trade_fairs": ["InterTabac Dortmund", "Tobacco Plus Expo", "Vapexpo PL"],
        "L7_social_osint": [
            "facebook.com/groups/nabijarki-do-tytoniu",
            "facebook.com/groups/powermatic-polska",
            "facebook.com/groups/tytoń-do-skręcania",
            "youtube.com (recenzenci maszynek)",
            "olx.pl (sprzedawcy z powtarzającymi się ogłoszeniami)",
        ],
        "L8_B2B_catalogs": ["aleo.com", "pkt.pl", "panoramafirm.pl", "bizraport.pl",
                            "nipgo.pl", "europages.pl"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
    "CZ": {
        "name": "Czechy",
        "csv": "data/Czechy/catalog-B-CZ.csv",
        "regions": {
            "PR": "Praha", "ST": "Středočeský", "JC": "Jihočeský",
            "PL": "Plzeňský", "KA": "Karlovarský", "US": "Ústecký",
            "LI": "Liberecký", "KR": "Královéhradecký", "PA": "Pardubický",
            "VY": "Vysočina", "JM": "Jihomoravský", "OL": "Olomoucký",
            "ZL": "Zlínský", "MO": "Moravskoslezský",
        },
        "top_phrases_for_region": [
            "velkoobchod tabák", "kuřácké potřeby velkoobchod",
            "doutníky velkoobchod", "tabák prodejna", "kuřácké potřeby",
        ],
        "L1_web_search": ["velkoobchod tabák {město}", "kuřácké potřeby velkoobchod"],
        "L2_marketplace": ["heureka.cz", "zbozi.cz", "aukro.cz", "alza.cz", "bazos.cz"],
        "L3_registries": {
            "ARES": "https://ares.gov.cz",
            "VIES": True,
            "PKD": ["46.35", "46.69", "47.26"],
        },
        "L4_customs_regulatory": ["Celní správa (Czech customs)"],
        "L5_dns_whois": {"tld": ".cz", "whois_server": "whois.nic.cz"},
        "L6_trade_fairs": ["InterTabac Dortmund (CZ exhibitors)", "Tabak Expo"],
        "L7_social_osint": ["facebook.com/groups (CZ tobacco)", "bazos.cz (sellers)"],
        "L8_B2B_catalogs": ["firmy.cz", "kompass.com", "europages.cz"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
    "SK": {
        "name": "Słowacja",
        "csv": "data/Słowacja/catalog-B-SK.csv",
        "regions": {
            "BL": "Bratislavský", "TT": "Trnavský", "TN": "Trenčiansky",
            "NR": "Nitriansky", "ZA": "Žilinský", "BB": "Banskobystrický",
            "PO": "Prešovský", "KE": "Košický",
        },
        "top_phrases_for_region": [
            "veľkoobchod tabak", "fajčiarske potreby veľkoobchod",
            "tabak predaj", "dymky veľkoobchod",
        ],
        "L1_web_search": ["veľkoobchod tabak {mesto}", "fajčiarske potreby veľkoobchod"],
        "L2_marketplace": ["heureka.sk", "bazossk", "mall.sk", "alza.sk"],
        "L3_registries": {
            "ORSR": "https://www.orsr.sk",
            "VIES": True,
            "PKD": ["46.35", "46.69"],
        },
        "L4_customs_regulatory": ["Finančná správa (SK customs)"],
        "L5_dns_whois": {"tld": ".sk", "whois_server": "whois.sk-nic.sk"},
        "L6_trade_fairs": ["InterTabac (SK exhibitors)"],
        "L7_social_osint": ["facebook.com/groups (SK tobacco)", "bazossk"],
        "L8_B2B_catalogs": ["firmy.eu", "kompass.com", "europages.sk"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
    "RO": {
        "name": "Rumunia",
        "csv": "data/Rumunia/catalog-B-RO.csv",
        "regions": {
            "B": "București", "AB": "Alba", "AR": "Arad", "AG": "Argeș",
            "BC": "Bacău", "BH": "Bihor", "BN": "Bistrița-Năsăud", "BT": "Botoșani",
            "BR": "Brăila", "BV": "Brașov", "BZV": "Buzău", "CL": "Călărași",
            "CS": "Caraș-Severin", "CJ": "Cluj", "CT": "Constanța", "CV": "Covasna",
            "DB": "Dâmbovița", "DJ": "Dolj", "GL": "Galați", "GR": "Giurgiu",
            "GJ": "Gorj", "HR": "Harghita", "HD": "Hunedoara", "IL": "Ialomița",
            "IS": "Iași", "IF": "Ilfov", "MM": "Maramureș", "MH": "Mehedinți",
            "MS": "Mureș", "NT": "Neamț", "OT": "Olt", "PH": "Prahova",
            "SJ": "Sălaj", "SM": "Satu Mare", "SB": "Sibiu", "SV": "Suceava",
            "TR": "Teleorman", "TM": "Timiș", "TL": "Tulcea", "VS": "Vaslui",
            "VL": "Vâlcea", "VN": "Vrancea",
        },
        "top_phrases_for_region": [
            "angrosist tutun", "distribuitor tutun", "tigari en-gros",
            "tutun magazin", "articole pentru fumători",
        ],
        "L1_web_search": ["angrosist tutun {oraș}", "distribuitor tutun {oraș}"],
        "L2_marketplace": ["emag.ro", "olx.ro", "okazii.ro", "cel.ro"],
        "L3_registries": {
            "ONRC": "https://www.onrc.ro",
            "VIES": True,
            "PKD": ["46.35", "46.69"],
        },
        "L4_customs_regulatory": ["ANAF (RO customs)"],
        "L5_dns_whois": {"tld": ".ro", "whois_server": "whois.rotld.ro"},
        "L6_trade_fairs": ["InterTabac", "Tobacco Romania"],
        "L7_social_osint": ["facebook.com/groups (RO tutun)", "olx.ro"],
        "L8_B2B_catalogs": ["listafirme.ro", "confidas.ro", "europages.ro"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
    "LT": {
        "name": "Litwa",
        "csv": "data/Litwa/catalog-B-LT.csv",
        "regions": {
            "AL": "Alytaus", "KA": "Kauno", "KL": "Klaipėdos", "MA": "Marijampolės",
            "PA": "Panevėžio", "SH": "Šiaulių", "TA": "Tauragės", "TE": "Telšių",
            "UT": "Utenos", "VL": "Vilniaus",
        },
        "top_phrases_for_region": [
            "didmeninė prekyba tabako gaminiais", "tabako parduotuvė urmu",
            "rūkymo reikmenys didmeninė", "tabako gaminiai didmeninė prekyba",
        ],
        "L1_web_search": ["didmeninė prekyba tabako gaminiais {miestas}", "tabako parduotuvė urmu"],
        "L2_marketplace": ["skelbiu.lt", "vinted.lt", "aruodas.lt"],
        "L3_registries": {
            "JAR": "https://rekvizitai.vz.lt",
            "VIES": True,
            "PKD": ["46.35", "46.69"],
        },
        "L4_customs_regulatory": ["Muitinė (LT customs)"],
        "L5_dns_whois": {"tld": ".lt", "whois_server": "whois.domreg.lt"},
        "L6_trade_fairs": ["InterTabac (LT exhibitors)"],
        "L7_social_osint": ["facebook.com/groups (LT tabakas)", "skelbiu.lt"],
        "L8_B2B_catalogs": ["rekvizitai.vz.lt", "europages.lt", "kompass.com"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
    "LV": {
        "name": "Łotwa",
        "csv": "data/Łotwa/catalog-B-LV.csv",
        "regions": {
            "RIX": "Rīga", "JEL": "Jelgava", "JUR": "Jūrmala", "LIE": "Liepāja",
            "REZ": "Rēzekne", "VAL": "Valmiera", "VEN": "Ventspils",
        },
        "top_phrases_for_region": [
            "tabakas vairumtirdzniecība", "smēķētāju piederumi vairumtirdzniecība",
            "tabakas izstrādājumi vairumā", "cigarešu piederumi",
        ],
        "L1_web_search": ["tabakas vairumtirdzniecība {pilsēta}", "smēķētāju piederumi vairumtirdzniecība"],
        "L2_marketplace": ["ss.lv", "vinted.lv"],
        "L3_registries": {
            "Lursoft": "https://www.lursoft.lv",
            "VIES": True,
            "PKD": ["46.35", "46.69"],
        },
        "L4_customs_regulatory": ["VID (LV customs)"],
        "L5_dns_whois": {"tld": ".lv", "whois_server": "whois.nic.lv"},
        "L6_trade_fairs": ["InterTabac (LV exhibitors)"],
        "L7_social_osint": ["facebook.com/groups (LV tabaka)", "ss.lv"],
        "L8_B2B_catalogs": ["lursoft.lv", "europages.lv"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
    "EE": {
        "name": "Estonia",
        "csv": "data/Estonia/catalog-B-EE.csv",
        "regions": {
            "HA": "Harju", "HII": "Hiiu", "IDA": "Ida-Viru", "JÕG": "Jõgeva",
            "JÄR": "Järva", "LÄÄ": "Lääne", "LÄÄ-V": "Lääne-Viru", "PÕL": "Põlva",
            "PÄR": "Pärnu", "RAP": "Rapla", "SA": "Saare", "TAR": "Tartu",
            "VAL": "Valga", "VIL": "Viljandi", "VÕR": "Võru",
        },
        "top_phrases_for_region": [
            "tubakatoodete hulgimüük", "suitsetarvete hulgimüük",
            "tubakatooted hulgi", "sigaretitarvikud hulgimüük",
        ],
        "L1_web_search": ["tubakatoodete hulgimüük {linn}", "suitsetarvete hulgimüük"],
        "L2_marketplace": ["osta.ee", "vinted.ee"],
        "L3_registries": {
            "e-Äriregister": "https://ariregister.rik.ee",
            "VIES": True,
            "PKD": ["46.35", "46.69"],
        },
        "L4_customs_regulatory": ["EMTA (EE customs)"],
        "L5_dns_whois": {"tld": ".ee", "whois_server": "whois.tld.ee"},
        "L6_trade_fairs": ["InterTabac (EE exhibitors)"],
        "L7_social_osint": ["facebook.com/groups (EE tubakas)", "osta.ee"],
        "L8_B2B_catalogs": ["e-Äriregister", "europages.ee"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
    "FR": {
        "name": "Francja",
        "csv": "data/Francja/catalog-B-FR.csv",
        "regions": {
            "IDF": "Île-de-France", "PAC": "Provence-Alpes-Côte d'Azur",
            "OCC": "Occitanie", "AUV": "Auvergne-Rhône-Alpes", "NAQ": "Nouvelle-Aquitaine",
            "BRE": "Bretagne", "PDL": "Pays de la Loire", "HDF": "Hauts-de-France",
            "GES": "Grand Est", "NOR": "Normandie", "BFC": "Bourgogne-Franche-Comté",
            "CVL": "Centre-Val de Loire", "COR": "Corse",
        },
        "top_phrases_for_region": [
            "grossiste tabac", "détaillant tabac", "fournisseur tabac",
            "articles pour fumeurs", "cigarettes electroniques grossiste",
        ],
        "L1_web_search": ["grossiste tabac {ville}", "détaillant tabac {ville}"],
        "L2_marketplace": ["leboncoin.fr", "rakuten.fr", "cdiscount.com", "vinted.fr", "amazon.fr"],
        "L3_registries": {
            "Pappers": "https://www.pappers.fr",
            "Societe.com": "https://www.societe.com",
            "VIES": True,
            "PKD": ["46.35Z", "47.26Z"],
        },
        "L4_customs_regulatory": ["Douanes françaises"],
        "L5_dns_whois": {"tld": ".fr", "whois_server": "whois.afnic.fr"},
        "L6_trade_fairs": ["InterTabac", "Vapexpo France", "WT Frankfurt"],
        "L7_social_osint": ["facebook.com/groups (FR tabac)", "leboncoin.fr (vendeurs pro)"],
        "L8_B2B_catalogs": ["pappers.fr", "societe.com", "europages.fr", "kompass.com"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
    "MD": {
        "name": "Mołdawia",
        "csv": "data/Mołdawia/catalog-B-MD.csv",
        "regions": {
            "CHI": "Chișinău", "BAL": "Bălți", "COM": "Comrat", "TIR": "Tiraspol",
            "CAH": "Cahul", "STR": "Strășeni", "ORH": "Orhei", "SOR": "Soroca",
            "UNH": "Ungheni", "DRO": "Drochia", "EDI": "Edineț", "FLR": "Florești",
            "FAU": "Fălești", "GLO": "Glodeni", "HIN": "Hîncești", "IAL": "Ialoveni",
            "NIS": "Nisporeni", "OCN": "Ocnița", "REZ": "Rezina", "RZB": "Rîșcani",
            "SIN": "Sîngerei", "SLO": "Slobozia", "SUD": "Ștefan Vodă", "STR2": "Stînga Nistrului",
            "TAR": "Taraclia", "TEL": "Telenești", "TIG": "Tighina", "TRI": "Transnistria",
            "UNG": "Ungheni", "UTR": "U.T.A. Găgăuzia",
        },
        "top_phrases_for_region": [
            "angrosist tutun", "distribuitor tutun", "tutun en-gros",
            "articole pentru fumători", "tigari Moldova",
        ],
        "L1_web_search": ["angrosist tutun {oraș}", "distribuitor tutun Moldova"],
        "L2_marketplace": ["999.md", "olx.md"],
        "L3_registries": {
            "Camera Înregistrării de Stat": "https://www.cis.md",
            "VIES": False,  # MD is non-EU
            "PKD": ["46.35", "46.69"],
        },
        "L4_customs_regulatory": ["Serviciul Vamal (MD customs)"],
        "L5_dns_whois": {"tld": ".md", "whois_server": "whois.nic.md"},
        "L6_trade_fairs": ["InterTabac (MD exhibitors)"],
        "L7_social_osint": ["facebook.com/groups (MD tutun)", "999.md"],
        "L8_B2B_catalogs": ["cis.md", "europages.md"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
    "BG": {
        "name": "Bułgaria",
        "csv": "data/Bułgaria/catalog-B-BG.csv",
        "regions": {
            "SOF": "София-град", "SOP": "София-област", "BLG": "Благоевград",
            "BGS": "Бургас", "VAR": "Варна", "VTR": "Велико Търново", "VID": "Видин",
            "VRC": "Враца", "GAB": "Габрово", "DOB": "Добрич", "KZR": "Кърджали",
            "KNL": "Кюстендил", "LOV": "Ловеч", "MON": "Монтана", "PAZ": "Пазарджик",
            "PER": "Перник", "PVN": "Плевен", "PDV": "Пловдив", "RAZ": "Разград",
            "RSE": "Русе", "SLS": "Силистра", "SLV": "Сливен", "SML": "Смолян",
            "SZR": "Стара Загора", "TGV": "Търговище", "HKV": "Хасково", "SHU": "Шумен",
            "JAM": "Ямбол",
        },
        "top_phrases_for_region": [
            "тютюн на едро", "тютюневи изделия дистрибутор", "цигари едро",
            "аксесоари за пушачи", "тютюнопушене",
        ],
        "L1_web_search": ["тютюн на едро {град}", "тютюневи изделия дистрибутор"],
        "L2_marketplace": ["olx.bg", "bazar.bg"],
        "L3_registries": {
            "Търговски регистър": "https://portal.registryagency.bg",
            "VIES": True,
            "PKD": ["46.35", "46.69"],
        },
        "L4_customs_regulatory": ["Агенция Митници (BG customs)"],
        "L5_dns_whois": {"tld": ".bg", "whois_server": "whois.register.bg"},
        "L6_trade_fairs": ["InterTabac (BG exhibitors)"],
        "L7_social_osint": ["facebook.com/groups (BG тютюн)", "olx.bg"],
        "L8_B2B_catalogs": ["portal.registryagency.bg", "bizon.bg", "europages.bg"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
    "SI": {
        "name": "Słowenia",
        "csv": "data/Słowenia/catalog-B-SI.csv",
        "regions": {
            "LJ": "Osrednjeslovenska", "MB": "Podravska", "CE": "Savinjska",
            "KR": "Gorenjska", "KP": "Primorsko-notranjska", "KK": "Goriška",
            "NG": "Jugovzhodna Slovenija", "NM": "Posavska", "MS": "Pomurska",
            "SG": "Koroška", "ZA": "Zasavska", "PO": "Obalno-kraška",
        },
        "top_phrases_for_region": [
            "tobak debelo", "trgovina na debelo tobak", "cigarete debelo",
            "pripomočki za kadilce", "tobačni izdelki",
        ],
        "L1_web_search": ["tobak debelo {mesto}", "trgovina na debelo tobak"],
        "L2_marketplace": ["bolha.com", "mimovrste.com", "ceneje.si"],
        "L3_registries": {
            "AJPES": "https://www.ajpes.si",
            "VIES": True,
            "PKD": ["46.35", "46.69"],
        },
        "L4_customs_regulatory": ["Finančna uprava (SI customs)"],
        "L5_dns_whois": {"tld": ".si", "whois_server": "whois.register.si"},
        "L6_trade_fairs": ["InterTabac (SI exhibitors)"],
        "L7_social_osint": ["facebook.com/groups (SI tobak)", "bolha.com"],
        "L8_B2B_catalogs": ["ajpes.si", "europages.si", "kompass.com"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
    "HR": {
        "name": "Chorwacja",
        "csv": "data/Chorwacja/catalog-B-HR.csv",
        "regions": {
            "ZG": "Zagreb", "KK": "Krapina-Zagorje", "SI": "Sisačko-Moslavačka",
            "KA": "Karlovačka", "VA": "Varaždinska", "KŽ": "Koprivničko-Križevačka",
            "BJ": "Bjelovarsko-Bilogorska", "PG": "Primorsko-Goranska", "LI": "Ličko-Senjska",
            "VP": "Virovitičko-Podravska", "PO": "Požeško-Slavonska", "SB": "Brodsko-Posavska",
            "ZD": "Zadarska", "ŠI": "Šibensko-Kninska", "SP": "Splitsko-Dalmatinska",
            "IS": "Istarska", "DN": "Dubrovačko-Neretvanska", "ME": "Međimurska",
            "GR": "Grad Zagreb", "OB": "Osječko-Baranjska", "VK": "Vukovarsko-Srijemska",
        },
        "top_phrases_for_region": [
            "veleprodaja duhana", "distribucija duhana", "cigarete na veliko",
            "potrepštine za pušače", "duhan trgovina",
        ],
        "L1_web_search": ["veleprodaja duhan {grad}", "distribucija duhana"],
        "L2_marketplace": ["njuskalo.hr", "index.hr/oglasi"],
        "L3_registries": {
            "OIB": "https://www.oib.hr",
            "VIES": True,
            "PKD": ["46.35", "46.69"],
        },
        "L4_customs_regulatory": ["Carinska uprava (HR customs)"],
        "L5_dns_whois": {"tld": ".hr", "whois_server": "whois.dns.hr"},
        "L6_trade_fairs": ["InterTabac (HR exhibitors)"],
        "L7_social_osint": ["facebook.com/groups (HR duhan)", "njuskalo.hr"],
        "L8_B2B_catalogs": ["oib.hr", "europages.hr", "kompass.com"],
        "L9_LLM_extraction": {"provider": "OpenRouter", "model": "deepseek-chat",
                               "env_key": "OPENROUTER_API_KEY"},
    },
}


# ──────────────────────────────────────────────────────────────────────
# add_lead(): SAFER. No auto-execution. Only called when agent has
# verified NIP/KRS from real registry lookup. Will REFUSE to add if
# NIP/KRS look like obvious FABRYKATs (e.g. KRS 0000123456).
# ──────────────────────────────────────────────────────────────────────

# Known FABRYKAT markers (LLM-generated test data that has been seen in past)
FABRYKAT_KNOWN = {
    "KRS 0000123456", "KRS 0000574829", "KRS 0000090479", "KRS 0000384920",
    "KRS 0000439210", "KRS 0000628491", "KRS 0000782910", "KRS 0000182940",
    "KRS 0000892014",
}


def add_lead(name: str, nip: str, rejestr_id: str, source: str, country: str = "PL",
             category: str = "B8") -> bool:
    """Add a verified lead to the country's CSV. Refuses FABRYKAT NIP/KRS.

    Args:
        name: Official company name (must match registry)
        nip: 10-digit NIP for PL, 8-digit IČO for CZ/SK, etc.
        rejestr_id: KRS or registry ID (e.g. 'KRS 0001234567')
        source: Where you got it (e.g. 'L1: Google search verified via KRS API')
        country: ISO 2-letter country code
        category: catalog category (default B8)

    Returns:
        True if added, False if refused (FABRYKAT or duplicate)
    """
    if rejestr_id in FABRYKAT_KNOWN:
        print(f"   ❌ REFUSED: {rejestr_id} is a known FABRYKAT (LLM test data). Not adding.")
        return False

    nip_clean = re.sub(r'\D', '', nip)
    plan = COUNTRY_PLANS.get(country.upper())
    if not plan:
        print(f"   ❌ Unknown country: {country}")
        return False
    csv_path = ROOT / plan["csv"]

    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    existing_nips = {re.sub(r'\D', '', r.get("nip_vat", "")) for r in rows}
    if nip_clean in existing_nips:
        print(f"   ℹ️  Skip duplicate NIP {nip_clean} ({name})")
        return False

    # Prepend country code if not present
    if country.upper() == "PL" and not nip_clean.startswith("PL"):
        nip_full = f"PL{nip_clean}"
    elif country.upper() == "CZ" and not nip_clean.startswith("CZ"):
        nip_full = f"CZ{nip_clean}"
    else:
        nip_full = nip_clean

    counter = len(rows) + 10
    row = {k: "brak" for k in fieldnames}
    row["region_kod"] = "XX"
    row["region_nazwa"] = plan["name"]
    row["region_typ"] = "województwo" if country == "PL" else "kraj"
    row["id_unikalne"] = f"{country.upper()}-B-XX-{counter:03d}"
    row["kategoria"] = category
    row["nazwa_firmy"] = name
    row["kraj"] = country.upper()
    row["nip_vat"] = nip_full
    row["rejestr_id"] = rejestr_id if rejestr_id else "brak"
    row["tier"] = "hurtownik"
    row["zrodlo_danych"] = source
    row["data_weryfikacji"] = time.strftime("%Y-%m-%d")
    row["flagi"] = f"{time.strftime('%Y-%m-%d')} ⚠️ DO-WERYFIKACJI"
    row["rynek_skala"] = "duży"

    rows.append(row)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    print(f"   ➕ Added: {name} ({country}, NIP/IČO: {nip_full}, {rejestr_id})")
    return True


# ──────────────────────────────────────────────────────────────────────
# Display functions (no auto-execution)
# ──────────────────────────────────────────────────────────────────────

def list_countries():
    print("=" * 80)
    print("  BILLSzuka 9-levels plans — 12 countries")
    print("=" * 80)
    for code, plan in COUNTRY_PLANS.items():
        n_levels = sum(1 for k in plan if k.startswith("L") and "_" in k)
        n_marketplace = len(plan.get("L2_marketplace", []))
        n_regions = len(plan.get("regions", {}))
        n_phrases = len(plan.get("top_phrases_for_region", []))
        n_queries = n_regions * n_phrases
        print(f"  {code} ({plan['name']:14s}) — {n_levels} levels, "
              f"{n_marketplace} marketplaces, {n_regions} regions × {n_phrases} phrases = {n_queries} L1b queries")


def show_country(country: str):
    plan = COUNTRY_PLANS.get(country.upper())
    if not plan:
        print(f"❌ Unknown country: {country}")
        return
    print("=" * 80)
    print(f"  {country.upper()} — {plan['name']}  (CSV: {plan['csv']})")
    print("=" * 80)
    for key, val in plan.items():
        if key in ("name", "csv"):
            continue
        print(f"\n  {key}:")
        if isinstance(val, list):
            for item in val:
                print(f"    - {item}")
        elif isinstance(val, dict):
            for k, v in val.items():
                print(f"    {k}: {v}")
        else:
            print(f"    {val}")


# ──────────────────────────────────────────────────────────────────────
# L1b: Per-country × per-region query generator
# Combines top phrases from SŁOWNIK-{KOD}.md with region names.
# ──────────────────────────────────────────────────────────────────────

def generate_region_queries(country: str, top_n_phrases: int = 3, sample: int = 0) -> list:
    """Generate per-region search queries for a country.

    Combines country.top_phrases_for_region × country.regions to produce
    '{phrase} {region_name}' queries. Optional: load full SŁOWNIK-{KOD}.md
    and pick top N phrases by explicit ordering.

    Args:
        country: 2-letter country code
        top_n_phrases: take top N phrases from top_phrases_for_region
        sample: if > 0, return only this many sample queries (for preview)

    Returns:
        List of (region_code, region_name, phrase, query) tuples
    """
    plan = COUNTRY_PLANS.get(country.upper())
    if not plan:
        return []
    regions = plan.get("regions", {})
    phrases = plan.get("top_phrases_for_region", [])[:top_n_phrases]
    if not regions or not phrases:
        return []
    queries = []
    for rcode, rname in regions.items():
        for phrase in phrases:
            queries.append((rcode, rname, phrase, f"{phrase} {rname}"))
    if sample > 0:
        return queries[:sample]
    return queries


# ──────────────────────────────────────────────────────────────────────
# L1b CLI: show per-country per-region query plan
# ──────────────────────────────────────────────────────────────────────

def show_region_queries(country: str, top_n: int = 3, sample: int = 0):
    plan = COUNTRY_PLANS.get(country.upper())
    if not plan:
        print(f"❌ Unknown country: {country}")
        return
    queries = generate_region_queries(country, top_n_phrases=top_n, sample=sample)
    n_regions = len(plan.get("regions", {}))
    n_phrases = len(plan.get("top_phrases_for_region", []))
    total = n_regions * min(top_n, n_phrases)
    print("=" * 80)
    print(f"  L1b: {country.upper()} — per-region queries "
          f"({n_regions} regions × {min(top_n, n_phrases)} phrases = {total} total)")
    print("=" * 80)
    for rcode, rname, phrase, q in queries:
        print(f"  {rcode:4s} | {rname:30s} | {phrase:50s}")
    if sample > 0 and total > sample:
        print(f"\n  ... ({total - sample} more not shown)")


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import re
    import argparse
    ap = argparse.ArgumentParser(description="BILLSzuka 9-levels per country (no auto-execution)")
    ap.add_argument("--list", action="store_true", help="List all 12 country plans")
    ap.add_argument("--country", help="Show plan for country (e.g. PL, CZ)")
    ap.add_argument("--region-queries", action="store_true",
                    help="With --country, show L1b per-region queries")
    ap.add_argument("--top-n", type=int, default=3,
                    help="Top N phrases per country for L1b (default 3)")
    ap.add_argument("--sample", type=int, default=0,
                    help="If > 0, show only N sample queries (default: show all)")
    ap.add_argument("--run", action="store_true",
                    help="(No-op) Marker that agent is running this country — does not auto-add anything")
    args = ap.parse_args()

    if args.list:
        list_countries()
    elif args.country and args.region_queries:
        show_region_queries(args.country, top_n=args.top_n, sample=args.sample)
    elif args.country:
        show_country(args.country)
    elif args.run:
        print("❌ --run is a no-op. Use add_lead() to add verified leads manually.")
    else:
        ap.print_help()
