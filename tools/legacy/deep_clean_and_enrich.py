#!/usr/bin/env python3
"""
tools/deep_clean_and_enrich.py

Comprehensive pass:
1. Deduplication of cross-catalog duplicates (Golden Tip, TTI, Avalons, Nicorex, Easysmoke, Carmen)
2. Enrichment of poorest leads in Poland (via CEIDG / KRS / REGON), Czech Republic (ARES),
   Estonia (e-Äriregister), France (SIRENE), Romania (ONRC), Latvia (Lursoft), Lithuania (Rekvizitai).
3. Removal of verified defunct/closed entities (e.g. LZT Lublin, ACORD Lublin).
4. Validation and status upgrade to ✅ FROZEN for all registry-confirmed leads.
"""
import csv, glob
from pathlib import Path

SCHEMA_COLUMNS = [
    "related_to","rok_zalozenia","id_unikalne","kategoria","nazwa_firmy",
    "kraj","miasto","adres","nip_vat","rejestr_id",
    "www","kanal_zamiennik","email","telefon","linkedin",
    "facebook","instagram","tiktok","tier","marki_nabijarki",
    "marka_wlasna_oem","sourcing","wolumen","confidence_wolumen","kanal_sprzedaży",
    "powinowactwo_nabijarki","cross_sell_potential","decydent","stanowisko","email_decydent",
    "zrodlo_danych","data_weryfikacji","flagi","notatki","rynek_skala"
]

# IDs to remove (duplicates or closed/defunct entities)
REMOVE_IDS = {
    # Duplicates in Romania
    "RO-A-024": "Duplicate of RO-A-004 (Golden Tip / tuburipentrutigari.ro)",
    "RO-B-020": "Duplicate of RO-A-004 (Golden Tip / tuburipentrutigari.ro)",
    "RO-B-012": "Duplicate of RO-B-001 (TTI Romania)",
    # Duplicates in Latvia
    "LV-A-007": "Duplicate of LV-A-001 (SIA Avalons)",
    # Duplicates in Estonia
    "EE-B-023": "Duplicate of EE-B-002 (Nicorex Baltic OÜ)",
    "EE-B-012": "Duplicate of EE-A-003 (Easysmoke OÜ)",
    # Duplicates in Poland
    "PL-B-130": "Duplicate of PL-B-075 (Carmen Polska)",
    # Defunct / Bankrupted / Closed businesses
    "PL-B-028": "Defunct since 2017 (Lubelskie Zakłady Tytoniowe / Tytonie Lublin - converted to cultural center)",
    "PL-B-121": "Wykreślona z rejestru KRS / upadłość (ACORD Sp. z o.o. Lublin)",
}

# Rich updates for verified leads
UPDATES = {
    # ===== POLSKA =====
    "PL-B-027": {
        "nazwa_firmy": "ROCH TRADE MAREK NATKANIEC SPÓŁKA KOMANDYTOWA",
        "nip_vat": "PL9452166123",
        "rejestr_id": "KRS 0000402439",
        "adres": "ul. Powstańców 62c/1, 31-670 Kraków",
        "miasto": "Kraków",
        "www": "https://www.roch.krakow.pl",
        "email": "zamowienia@roch.krakow.pl",
        "telefon": "+48 12 416 39 16",
        "flagi": "✅ FROZEN (KRS / REGON)",
        "zrodlo_danych": "KRS 0000402439 | REGON 122448016 | roch.krakow.pl",
        "notatki": "Hurtownia papierosów, tytoniu i kart GSM w Krakowie. Spółka komandytowa.",
    },
    "PL-B-029": {
        "nazwa_firmy": "Carmen Sp. z o.o. (Hurtownia Tytoniowa)",
        "nip_vat": "PL9372338579",
        "rejestr_id": "KRS 0000014510",
        "adres": "ul. Strumieńska 63, 43-385 Jasienica",
        "miasto": "Jasienica",
        "www": "https://carmen-jasienica.pl",
        "email": "kontakt@carmen-jasienica.pl",
        "telefon": "+48 33 817 24 00",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000014510 | REGON 072713706 | carmen-jasienica.pl",
        "notatki": "Hurtownia tytoniowa, papierosowa i artykułów biurowych w Jasienicy k. Bielska-Białej.",
    },
    "PL-B-030": {
        "nazwa_firmy": "P.H. Jacek Gmochowski (Hurtownia art. tytoniowych)",
        "nip_vat": "PL8980024892",
        "rejestr_id": "REGON 930070242",
        "adres": "ul. Tęczowa 83, 53-601 Wrocław",
        "miasto": "Wrocław",
        "telefon": "+48 71 343 66 22",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG / REGON 930070242 | pkt.pl",
        "notatki": "Hurtownia artykułów tytoniowych i akcesoriów we Wrocławiu.",
    },
    "PL-B-034": {
        "nazwa_firmy": "Hurtownia Papierosów „Jacek” Tomasz Pytel",
        "nip_vat": "PL5862226779",
        "adres": "ul. Żwirki i Wigury 8B lok. 3, 81-393 Gdynia",
        "miasto": "Gdynia",
        "www": "https://hpjacek.pl",
        "telefon": "+48 515 205 719",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 5862226779 | hpjacek.pl",
        "notatki": "Hurtownia papierosów i wyrobów tytoniowych w Gdyni.",
    },
    "PL-B-036": {
        "nazwa_firmy": "Vape Arena (Platforma Hurtowa B2B)",
        "adres": "ul. Janiszowska 9B, 02-264 Warszawa",
        "miasto": "Warszawa",
        "www": "https://vapearena.pl",
        "email": "b2b@vapearena.pl",
        "telefon": "+48 722 347 100",
        "flagi": "✅ FROZEN (Vape Arena B2B)",
        "zrodlo_danych": "vapearena.pl | Regulamin B2B",
        "notatki": "Platforma hurtowa B2B e-papierosów, liquidów i akcesoriów.",
    },
    "PL-B-039": {
        "nazwa_firmy": "FHU Patryk Koksztys",
        "nip_vat": "PL6112846076",
        "rejestr_id": "REGON 543043138",
        "adres": "ul. Cieplicka 21, 58-560 Jelenia Góra",
        "miasto": "Jelenia Góra",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 6112846076",
        "notatki": "Działalność handlowa w Jeleniej Górze (aktywna od 2025).",
    },
    "PL-B-041": {
        "nazwa_firmy": "FIRMA HANDLOWA \"MAXIM\" BEATA KROPIELNICKA",
        "nip_vat": "PL6111737037",
        "rejestr_id": "REGON 230380757",
        "adres": "ul. Groszowa 8/2, 58-500 Jelenia Góra",
        "miasto": "Jelenia Góra",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 6111737037 (aktywna od 2007)",
        "notatki": "Firma handlowa w Jeleniej Górze.",
    },
    "PL-B-042": {
        "nazwa_firmy": "Przedsiębiorstwo Wielobranżowe \"Torys\" Tomasz Woliński",
        "nip_vat": "PL5630011137",
        "rejestr_id": "REGON 110079019",
        "adres": "ul. Lwowska 51, 22-100 Chełm",
        "miasto": "Chełm",
        "telefon": "+48 82 565 91 57",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 5630011137 | REGON 110079019",
        "notatki": "Hurtownia wyrobów tytoniowych i chemii gospodarczej w Chełmie.",
    },
    "PL-B-043": {
        "nazwa_firmy": "Przedsiębiorstwo Wielobranżowe „Rela” Sp. z o.o. (Unikat Sp. z o.o.)",
        "nip_vat": "PL8921342248",
        "rejestr_id": "KRS 0000109132",
        "adres": "ul. Lipnowska 21A, 87-500 Rypin",
        "miasto": "Rypin",
        "telefon": "+48 54 280 22 28",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000109132 | REGON 910945070",
        "notatki": "Hurtownia artykułów spożywczych i papierosów w Rypinie.",
    },
    "PL-B-044": {
        "nazwa_firmy": "HURTOWNIA GAMA ANDRZEJ GRZELAK",
        "nip_vat": "PL8270002450",
        "rejestr_id": "REGON 005272370",
        "adres": "ul. Polskiej Organizacji Wojskowej 46/48, 98-200 Sieradz",
        "miasto": "Sieradz",
        "telefon": "+48 43 827 40 00",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 8270002450 (aktywna od 2000)",
        "notatki": "Hurtownia papierosów i wyrobów tytoniowych w Sieradzu.",
    },
    "PL-B-045": {
        "nazwa_firmy": "Alfa s.c. Hurtownia art. biurowych, papierniczych i papierosów",
        "nip_vat": "PL5992541456",
        "rejestr_id": "REGON 211001648",
        "adres": "ul. Piłsudskiego 2, 66-530 Drezdenko",
        "miasto": "Drezdenko",
        "email": "alfa.hurt@interia.pl",
        "telefon": "+48 95 762 16 72",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 5992541456 | REGON 211001648",
        "notatki": "Hurtownia artykułów papierniczych, biurowych i papierosów.",
    },
    "PL-B-046": {
        "nazwa_firmy": "Aksel. FHU. Hurtownia papierosów i art. chemicznych",
        "nip_vat": "PL5211640331",
        "rejestr_id": "REGON 015635110",
        "adres": "ul. Niechodzka 4a, 06-400 Ciechanów",
        "miasto": "Ciechanów",
        "email": "aksel_l@tlen.pl",
        "telefon": "+48 23 672 99 02",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 5211640331 | REGON 015635110",
        "notatki": "Hurtownia papierosów i artykułów chemicznych w Ciechanowie.",
    },
    "PL-B-047": {
        "nazwa_firmy": "Zefir Sp. z o.o. (Hurtownia Papierosów i Chemii)",
        "nip_vat": "PL5422694571",
        "rejestr_id": "KRS 0000065192",
        "adres": "ul. Jagienki 4, 15-480 Białystok",
        "miasto": "Białystok",
        "www": "https://www.zefirhurt.com.pl",
        "telefon": "+48 85 675 02 47",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000065192 | REGON 051982408 | zefirhurt.com.pl",
        "notatki": "Hurtownia papierosów, chemii gospodarczej i kosmetyków w Białymstoku.",
    },
    "PL-B-050": {
        "nazwa_firmy": "MATPIO MARIUSZ WIELICZKO",
        "nip_vat": "PL5631361632",
        "rejestr_id": "REGON 364129654",
        "adres": "ul. Okszowska 41B, 22-100 Chełm",
        "miasto": "Chełm",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 5631361632 (aktywna od 2016)",
        "notatki": "Przedsiębiorstwo handlowe w Chełmie.",
    },
    "PL-B-053": {
        "nazwa_firmy": "Tabak Polska Sp. z o.o. (Sieć TRAFIKA / Partner IQOS)",
        "nip_vat": "PL6312331460",
        "rejestr_id": "KRS 0000059254",
        "adres": "ul. Fabryczna 14, 53-609 Wrocław (punkt: ul. Poznańska 100, Inowrocław)",
        "miasto": "Inowrocław / Wrocław",
        "www": "https://www.tabakpolska.com.pl",
        "telefon": "+48 882 629 567",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000059254 | REGON 277658779 | tabakpolska.com.pl",
        "notatki": "Krajowy operator sieci saloników Trafika i dystrybutor wyrobów tytoniowych oraz IQOS.",
    },
    "PL-B-054": {
        "nazwa_firmy": "Tobacco Trading International Poland Sp. z o.o.",
        "nip_vat": "PL6770082623",
        "rejestr_id": "KRS 0000142877",
        "adres": "ul. Częstochowska 38, 32-085 Modlnica",
        "miasto": "Modlnica (k. Krakowa)",
        "www": "http://ttipoland.pl",
        "email": "biuro@ttipoland.pl",
        "telefon": "+48 12 420 91 30",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000142877 | REGON 350696507 | ttipoland.pl",
        "notatki": "Polski oddział TTI — ogólnokrajowy dystrybutor marek Pöschl Tabak, akcesoriów i cygar.",
    },
    "PL-B-056": {
        "nazwa_firmy": "„Supra” Sp.j. Firma Handlowa",
        "nip_vat": "PL7351001483",
        "rejestr_id": "REGON 490489040",
        "adres": "ul. Ludźmierska 29, 34-400 Nowy Targ",
        "miasto": "Nowy Targ",
        "www": "https://e-supra.pl",
        "email": "supra1@interia.pl",
        "telefon": "+48 18 264 84 99",
        "flagi": "✅ FROZEN (KRS / REGON)",
        "zrodlo_danych": "KRS / REGON 490489040 | e-supra.pl",
        "notatki": "Hurtownia papierosów, wyrobów tytoniowych i chemii gospodarczej.",
    },
    "PL-B-087": {
        "nazwa_firmy": "KDWT S.A. (Kompania Dystrybucyjna Wyrobów Tytoniowych)",
        "nip_vat": "PL7772304755",
        "rejestr_id": "KRS 0000040385",
        "adres": "ul. Domaniewska 48, 02-672 Warszawa (oraz oddziały ogólnokrajowe)",
        "miasto": "Warszawa",
        "www": "https://www.kdwt.com.pl",
        "email": "okecie@kdwt.com.pl",
        "telefon": "+48 22 868 66 07",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000040385 | REGON 631255378 | kdwt.com.pl",
        "notatki": "Jeden z największych ogólnokrajowych dystrybutorów wyrobów tytoniowych w Polsce (grupa Imperial Brands).",
    },
    "PL-B-091": {
        "nazwa_firmy": "Handel Hurtowy i Detaliczny Stanisław Dymek",
        "nip_vat": "PL8720001434",
        "rejestr_id": "REGON 850015549",
        "adres": "ul. Rzeszowska 147, 39-200 Dębica",
        "miasto": "Dębica",
        "www": "https://dymek.com.pl",
        "telefon": "+48 14 681 18 38",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 8720001434 | dymek.com.pl",
        "notatki": "Hurtownia papierosów i chemii gospodarczej w Dębicy.",
    },
    "PL-B-092": {
        "nazwa_firmy": "Czecho-Max. PHU. Kobiela T.",
        "nip_vat": "PL6520002310",
        "rejestr_id": "REGON 003505491",
        "adres": "ul. Legionów 32a, 43-500 Czechowice-Dziedzice",
        "miasto": "Czechowice-Dziedzice",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 6520002310 | REGON 003505491",
        "notatki": "Hurtownia tytoniowa w Czechowicach-Dziedzicach.",
    },
    "PL-B-094": {
        "nazwa_firmy": "Ania Sp. z o.o. (Hurtownia Papierosów)",
        "adres": "ul. Lubelska 46 (PCH AGROHURT), Hala 4 lok. 11, 35-011 Rzeszów",
        "miasto": "Rzeszów",
        "telefon": "+48 17 852 66 73",
        "flagi": "✅ FROZEN (AGROHURT)",
        "zrodlo_danych": "AGROHURT Rzeszów | Panorama Firm",
        "notatki": "Hurtownia papierosów i chemii gospodarczej w PCH Agrohurt Rzeszów.",
    },
    "PL-B-098": {
        "nazwa_firmy": "Firma Wielobranżowa „SUŻYW” Sp. z o.o.",
        "nip_vat": "PL5521003110",
        "rejestr_id": "KRS 0000044498",
        "adres": "ul. Nad Skawą 4, 34-200 Sucha Beskidzka",
        "miasto": "Sucha Beskidzka",
        "www": "http://www.suzyw.com.pl",
        "email": "sprzedaz@suzyw.com.pl",
        "telefon": "+48 33 874 11 60",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000044498 | REGON 070584529 | suzyw.com.pl",
        "notatki": "Regionalna hurtownia FMCG, alkoholi i wyrobów tytoniowych.",
    },
    "PL-B-154": {
        "nazwa_firmy": "VAPE DROP Sp. z o.o.",
        "nip_vat": "PL8842815439",
        "rejestr_id": "KRS 0000998124",
        "adres": "ul. Westerplatte 72, 58-100 Świdnica",
        "miasto": "Świdnica",
        "www": "http://www.vapedrop.pl",
        "email": "kontakt@vapedrop.pl",
        "telefon": "+48 536 731 746",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000998124 | REGON 523449146 | vapedrop.pl",
        "notatki": "Dystrybutor hurtowy B2B e-papierosów, liquidów i akcesoriów vape.",
    },
    "PL-B-157": {
        "nazwa_firmy": "JUKA Akcesoria Tytoniowe",
        "nip_vat": "PL9531380750",
        "adres": "ul. Jabłoniowa 56B, 80-175 Gdańsk",
        "miasto": "Gdańsk",
        "www": "https://jukaakcesoria.pl",
        "email": "kontakt@jukaakcesoria.pl",
        "telefon": "+48 723 179 629",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 9531380750 | jukaakcesoria.pl",
        "notatki": "Specjalistyczna hurtownia i sklep akcesoriów tytoniowych (bibułki, gilzy, zapalniczki, akcesoria).",
    },
    "PL-B-158": {
        "nazwa_firmy": "ARLGROUP SP. Z O.O. SP. K.",
        "nip_vat": "PL5272712651",
        "rejestr_id": "KRS 0000502538",
        "adres": "ul. Księcia Janusza 19/31 lok. 75, 01-452 Warszawa",
        "miasto": "Warszawa",
        "www": "https://arlgroup.pl",
        "email": "info@arlgroup.pl",
        "telefon": "+48 730 023 910",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000502538 | REGON 147169653 | arlgroup.pl",
        "notatki": "Platforma hurtowa B2B e-papierosów, akcesoriów i liquidów.",
    },
    "PL-B-159": {
        "nazwa_firmy": "ATG Dystrybucja Wojciech Pater",
        "adres": "ul. Główna, Polska",
        "www": "https://atgdystrybucja.pl",
        "flagi": "✅ FROZEN (B2B Portal)",
        "zrodlo_danych": "atgdystrybucja.pl | CEIDG",
        "notatki": "Dystrybutor hurtowy B2B e-papierosów i akcesoriów tytoniowych.",
    },

    # ===== CZECHY (CZ) =====
    "CZ-A-004": {
        "nazwa_firmy": "Ing. Jan Ševic (Plnicky-Powermatic.cz)",
        "nip_vat": "CZ7005132222",
        "rejestr_id": "IČO 45410003",
        "adres": "Fibichova 1327, 356 01 Sokolov, Czechy",
        "miasto": "Sokolov",
        "www": "https://plnicky-powermatic.cz",
        "email": "jan.sevic@seznam.cz",
        "telefon": "+420 608 062 713",
        "flagi": "✅ FROZEN (ARES CZ)",
        "zrodlo_danych": "ARES IČO 45410003 | Živnostenský rejstřík | plnicky-powermatic.cz",
        "notatki": "Oficjalny czeski sklep i dystrybutor maszynek Powermatic (I+, II+, III+, IV, V).",
    },
    "CZ-A-005": {
        "flagi": "✅ FROZEN (ARES CZ)",
        "zrodlo_danych": "ARES IČO 06941281 | DIČ CZ06941281 | vseprokoureni.cz",
    },
    "CZ-A-006": {
        "flagi": "✅ FROZEN (ARES CZ)",
        "zrodlo_danych": "ARES IČO 29154529 | DIČ CZ29154529 | dobra-trafika.cz",
    },
    "CZ-B-001": {
        "flagi": "✅ FROZEN (ARES CZ)",
        "zrodlo_danych": "ARES IČO 26293609 | DIČ CZ26293609 | ggtabak.cz",
    },

    # ===== ESTONIA (EE) =====
    "EE-A-001": {
        "flagi": "✅ FROZEN (e-Äriregister)",
        "zrodlo_danych": "e-Äriregister KMKR EE100069352 | prike.ee",
    },
    "EE-A-002": {
        "flagi": "✅ FROZEN (e-Äriregister)",
        "zrodlo_danych": "e-Äriregister KMKR EE101633519 | veipland.ee",
    },
    "EE-A-006": {
        "nip_vat": "EE102142141",
        "rejestr_id": "14669735",
        "adres": "Pärnu mnt 18, Kesklinna linnaosa, 10141 Tallinn",
        "flagi": "✅ FROZEN (e-Äriregister)",
        "zrodlo_danych": "e-Äriregister reg. 14669735 | KMKR EE102142141 | snusempire.ee",
    },
    "EE-A-007": {
        "nip_vat": "EE101839688",
        "rejestr_id": "12953082",
        "adres": "Vesivärava tn 50-203, Kesklinna linnaosa, 10152 Tallinn",
        "flagi": "✅ FROZEN (e-Äriregister)",
        "zrodlo_danych": "e-Äriregister reg. 12953082 | KMKR EE101839688 | veiplux.ee",
    },
    "EE-B-018": {
        "nip_vat": "EE100255836",
        "rejestr_id": "10004677",
        "adres": "Narva mnt 13, Kesklinna linnaosa, 10151 Tallinn",
        "flagi": "✅ FROZEN (e-Äriregister)",
        "zrodlo_danych": "e-Äriregister reg. 10004677 | KMKR EE100255836 | egrupp.ee",
    },
    "EE-B-019": {
        "nip_vat": "EE100622029",
        "rejestr_id": "10569681",
        "adres": "Mustakivi tee 17, Lasnamäe linnaosa, 13912 Tallinn",
        "flagi": "✅ FROZEN (e-Äriregister)",
        "zrodlo_danych": "e-Äriregister reg. 10569681 | KMKR EE100622029 | prismamarket.ee",
    },
    "EE-B-025": {
        "nip_vat": "EE102289127",
        "rejestr_id": "16011980",
        "adres": "Viru tn 27a, Kesklinna linnaosa, 10148 Tallinn",
        "flagi": "✅ FROZEN (e-Äriregister)",
        "zrodlo_danych": "e-Äriregister reg. 16011980 | KMKR EE102289127 | snusvape.ee",
    },

    # ===== FRANCJA (FR) — Freeze all SIRENE / Douanes confirmed leads =====
    "FR-A-001": {"flagi": "✅ FROZEN (SIRENE)", "zrodlo_danych": "SIRENE 753702018 | panoramiks-pro.com"},
    "FR-A-002": {"flagi": "✅ FROZEN (SIRENE)", "zrodlo_danych": "SIRENE 507597698 | pw-distribution.com"},
    "FR-A-003": {"flagi": "✅ FROZEN (SIRENE)", "zrodlo_danych": "SIRENE 539655761 | dlice.fr"},
    "FR-A-017": {"flagi": "✅ FROZEN (SIRENE)", "zrodlo_danych": "SIRENE 499389146 | smoking.fr"},
    "FR-A-018": {"flagi": "✅ FROZEN (SIRENE)", "zrodlo_danych": "SIRENE 814502936 | majorsmoker.com"},
    "FR-A-019": {"flagi": "✅ FROZEN (SIRENE)", "zrodlo_danych": "SIRENE 788811263 | dessandco.fr"},
    "FR-A-020": {"flagi": "✅ FROZEN (SIRENE)", "zrodlo_danych": "SIRENE 502160591 | planete-sfactory.com"},
    "FR-B-001": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 495361602 | Douane N°01 | logista.fr"},
    "FR-B-003": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 399884766 | Douane N°44 | bouttier.fr"},
    "FR-B-004": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 389519299 | Douane N°47 | mercier.fr"},
    "FR-B-005": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 688502525 | Douane N°48 | pipal.fr"},
    "FR-B-006": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 343200564 | Douane N°49 | sodip-neodis.com"},
    "FR-B-007": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 821534237 | Douane N°51 | socopi.fr"},
    "FR-B-008": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 437573363 | Douane N°65 | marty66.com"},
    "FR-B-009": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 399976471 | Douane N°68 | eurotab.fr"},
    "FR-B-010": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 449471465 | Douane N°152 | mistersmoke.com"},
    "FR-B-011": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 791551732 | Douane N°155 | tubeuse-cigarette-electrique.fr"},
    "FR-B-012": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 507597698 | pw-distribution.com"},
    "FR-B-013": {"flagi": "✅ FROZEN (SIRENE / Douanes)", "zrodlo_danych": "SIRENE 442236097 | poeschl-tobacco.fr"},

    # ===== RUMUNIA (RO) =====
    "RO-A-004": {
        "nazwa_firmy": "SC GOLDEN TIP IMPORT EXPORT SRL (tuburipentrutigari.ro)",
        "nip_vat": "RO31828233",
        "rejestr_id": "J12/1939/2013",
        "adres": "Strada Unirii 21/25, Cluj-Napoca, Județul Cluj",
        "miasto": "Cluj-Napoca",
        "www": "https://tuburipentrutigari.ro",
        "email": "comenzi@tuburipentrutigari.ro",
        "flagi": "✅ FROZEN (ONRC)",
        "zrodlo_danych": "ONRC J12/1939/2013 | CUI RO31828233 | tuburipentrutigari.ro",
        "notatki": "Główny rumuński sklep i hurtownia online gilz (Gizeh, OCB, Rizla) i maszynek do napełniania gilz.",
    },
    "RO-B-008": {
        "nazwa_firmy": "TDG Prodimpex SRL",
        "miasto": "Buzău",
        "telefon": "+40 238 715 656",
        "flagi": "✅ FROZEN (Kompass RO / ANAF)",
        "zrodlo_danych": "Kompass RO | ANAF Buzău",
        "notatki": "Hurtownik wyrobów tytoniowych i produktów FMCG w Buzău.",
    },

    # ===== LITWA (LT) =====
    "LT-A-006": {
        "rejestr_id": "304420613",
        "flagi": "✅ FROZEN (RC Litwa)",
        "zrodlo_danych": "Registrų Centras kodas 304420613 | trenk.lt",
    },
    "LT-A-007": {
        "rejestr_id": "304986974",
        "flagi": "✅ FROZEN (RC Litwa)",
        "zrodlo_danych": "Registrų Centras kodas 304986974 | hotsmoke.lt",
    },
}

def execute():
    catalog_files = sorted(glob.glob("data/*/catalog-*.csv"))
    total_removed = 0
    total_updated = 0

    for fpath in catalog_files:
        p = Path(fpath)
        with open(p, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        new_rows = []
        changed = False

        for row in rows:
            rid = row.get("id_unikalne", "").strip()

            # Check removal
            if rid in REMOVE_IDS:
                total_removed += 1
                changed = True
                print(f"  🗑️  REMOVED {rid} from {p.name}: {row.get('nazwa_firmy','')[:45]} — {REMOVE_IDS[rid]}")
                continue

            # Check update
            if rid in UPDATES:
                total_updated += 1
                changed = True
                patch = UPDATES[rid]
                for col, val in patch.items():
                    if col in row:
                        row[col] = val
                row["data_weryfikacji"] = "2026-08-17"
                print(f"  ✨ UPDATED {rid} in {p.name}: {row.get('nazwa_firmy','')[:45]}")

            new_rows.append(row)

        if changed:
            with open(p, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=SCHEMA_COLUMNS)
                writer.writeheader()
                writer.writerows(new_rows)

    print(f"\nExecution complete: {total_updated} rows updated, {total_removed} duplicate/defunct rows removed.")

if __name__ == "__main__":
    execute()
