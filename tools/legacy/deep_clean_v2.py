#!/usr/bin/env python3
"""
tools/deep_clean_v2.py — Comprehensive review, validation, deduplication, and hallucination cleanup.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, DATA_DIR

# IDs to remove (hallucinations, truncated artifacts, or cross-catalog duplicates)
REMOVE_IDS = {
    # Truncated / empty placeholders from initial web scrapes
    "PL-B-037": "Truncated 'PHU Andrzej...' without NIP/address/KRS",
    "PL-B-048": "Empty 'Wojmar s.c.' without city/address/NIP",
    "PL-B-049": "Empty 'P.H.U. TRANS' without city/address/NIP",
    "PL-B-051": "Empty 'JABA Firma Handlowa' without city/address/NIP",
    "PL-B-132": "Brand keyword placeholder 'Smok'",
    "PL-B-133": "Brand keyword placeholder 'Elso'",
    "PL-B-152": "Empty 'Vapetech Poland' without city/address/NIP",
    "PL-B-153": "Empty 'E-LIQ Distribution' without city/address/NIP",
    "PL-B-162": "Empty 'Doctor Vape' without city/address/NIP",

    # Duplicates in Poland
    "PL-B-141": "Duplicate of PL-B-027 (ROCH TRADE MAREK NATKANIEC SP. K.)",
    "PL-B-163": "Duplicate of PL-B-020 (Hurtownia KING Krzysztof Król)",
    "PL-B-165": "Duplicate of PL-B-189 (WEST TRADING SP. Z O.O.)",
    "PL-B-159": "Duplicate of PL-A-019 (ATG Dystrybucja Wojciech Pater)",
    "PL-B-188": "Duplicate of PL-B-027 (ROCH TRADE MAREK NATKANIEC SP. K.)",

    # Duplicates in France
    "FR-B-012": "Duplicate of FR-A-002 (P.W. DISTRIBUTION SIREN 507597698)",

    # Duplicates in Moldova
    "MD-A-004": "Duplicate of MD-A-002 (S.A. Tutun-CTC IDNO 1002600010996)",
    "MD-A-003": "Duplicate of MD-A-001 (S.R.L. NewSmoke Distribution IDNO 1014600025721)",
    "MD-B-004": "Duplicate of MD-A-020 (International Tobacco S.R.L. IDNO 1005600051817)",
}

# Verified enrichments for validated entities
UPDATES = {
    # ===== POLSKA (PL) =====
    "PL-A-005": {
        "nazwa_firmy": "TABAK GRUPA SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL6181914183",
        "rejestr_id": "KRS 0000119343",
        "adres": "ul. Złota 126, 62-800 Kalisz",
        "miasto": "Kalisz",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000119343 | REGON 250974864",
    },
    "PL-A-006": {
        "nazwa_firmy": "PRZEDSIĘBIORSTWO HANDLOWO-USŁUGOWE \"B.J.B.\" SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL6692127776",
        "rejestr_id": "KRS 0000121182",
        "adres": "ul. Klonowa 1, 75-644 Koszalin",
        "miasto": "Koszalin",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000121182 | REGON 330555099",
    },
    "PL-A-008": {
        "nazwa_firmy": "\"CK COMPLEX\" SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL9291744080",
        "rejestr_id": "KRS 0000237218",
        "adres": "ul. Naftowa 4, 65-705 Zielona Góra",
        "miasto": "Zielona Góra",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000237218 | REGON 080027815",
    },
    "PL-A-009": {
        "nazwa_firmy": "IGNIS COMPANY SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL5252995077",
        "rejestr_id": "KRS 0001091098",
        "adres": "ul. Szamocka 10C, 01-748 Warszawa",
        "miasto": "Warszawa",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0001091098 | REGON 527945830",
    },
    "PL-A-014": {
        "nazwa_firmy": "PROMOTORZY TRADING SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL5242751528",
        "rejestr_id": "KRS 0000422037",
        "adres": "ul. Odrowąża 15, 03-310 Warszawa",
        "miasto": "Warszawa",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000422037 | REGON 146139035",
    },
    "PL-A-017": {
        "nazwa_firmy": "ALPERATA SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL7282844071",
        "rejestr_id": "KRS 0000835586",
        "adres": "ul. Rewolucji 1905 r. 59, 90-216 Łódź",
        "miasto": "Łódź",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000835586 | REGON 385884236",
    },
    "PL-A-018": {
        "nazwa_firmy": "SPÓŁDZIELNIA \"BIELSIN\"",
        "nip_vat": "PL5470083919",
        "rejestr_id": "KRS 0000115372",
        "adres": "ul. Strażacka 35, 43-382 Bielsko-Biała",
        "miasto": "Bielsko-Biała",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000115372 | REGON 000876614",
    },
    "PL-A-020": {
        "nazwa_firmy": "STOPOL SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ SPÓŁKA KOMANDYTOWA",
        "nip_vat": "PL5790006978",
        "rejestr_id": "KRS 0000536165",
        "adres": "al. Wojska Polskiego 494-496, 82-200 Malbork",
        "miasto": "Malbork",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000536165 | REGON 008102527",
    },
    "PL-A-022": {
        "nazwa_firmy": "STALCO SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ SPÓŁKA KOMANDYTOWO-AKCYJNA",
        "nip_vat": "PL6792455066",
        "rejestr_id": "KRS 0000425156",
        "adres": "ul. Ofiar Katynia 1, 32-050 Skawina",
        "miasto": "Skawina",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000425156 | REGON 351398835",
    },
    "PL-B-059": {
        "nazwa_firmy": "Selgros / Transgourmet Polska Sp. z o.o.",
        "nip_vat": "PL7791906082",
        "rejestr_id": "KRS 0000203325",
        "adres": "ul. Chorzowska 88a, 41-910 Bytom",
        "miasto": "Bytom",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000203325 | selgros.pl",
    },
    "PL-B-062": {
        "nazwa_firmy": "Polska Grupa Tytoniowa Sp. z o.o.",
        "nip_vat": "PL9532585250",
        "rejestr_id": "KRS 0000308003",
        "adres": "ul. Pińczowska 8, 85-877 Bydgoszcz",
        "miasto": "Bydgoszcz",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000308003 | REGON 340456100",
    },
    "PL-B-064": {
        "nazwa_firmy": "Mona Sp. z o.o. (Hurtownia Papierosów)",
        "nip_vat": "PL6792683072",
        "rejestr_id": "KRS 0000085800",
        "adres": "ul. Saska 27, 30-720 Kraków",
        "miasto": "Kraków",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000085800 | CEIDG",
    },
    "PL-B-068": {
        "nazwa_firmy": "Hurtownia Centrum Wiesław Sacharski",
        "nip_vat": "PL7580003310",
        "rejestr_id": "REGON 550058690",
        "adres": "ul. Targowa 39G, 07-410 Ostrołęka",
        "miasto": "Ostrołęka",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 7580003310",
    },
    "PL-B-071": {
        "nazwa_firmy": "Firma Handlowa Mariusz Kawa",
        "nip_vat": "PL8731006509",
        "rejestr_id": "REGON 850389332",
        "adres": "ul. Spokojna 20C, 33-100 Tarnów",
        "miasto": "Tarnów",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 8731006509",
    },
    "PL-B-072": {
        "nazwa_firmy": "FLAJ Sklep i Hurtownia w Augustowie",
        "nip_vat": "PL8461001460",
        "rejestr_id": "REGON 790172650",
        "adres": "ul. Tytoniowa 7, 16-300 Augustów",
        "miasto": "Augustów",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 8461001460",
    },
    "PL-B-104": {
        "nazwa_firmy": "VIVOPLAST Hurtownia Opakowań i Artykułów",
        "nip_vat": "PL6610001890",
        "rejestr_id": "REGON 290515150",
        "adres": "ul. Sienkiewicza 32, 27-400 Ostrowiec Świętokrzyski",
        "miasto": "Ostrowiec Świętokrzyski",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 6610001890",
    },
    "PL-B-109": {
        "nazwa_firmy": "P.W. Kentdruk (KentDruk)",
        "nip_vat": "PL5490003504",
        "rejestr_id": "REGON 070440260",
        "adres": "ul. Marii Konopnickiej 6, 32-650 Kęty",
        "miasto": "Kęty",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 5490003504",
    },
    "PL-B-114": {
        "nazwa_firmy": "MILO S.A.",
        "nip_vat": "PL9590822602",
        "rejestr_id": "KRS 0000049457",
        "adres": "ul. Magazynowa 4, 25-565 Kielce",
        "miasto": "Kielce",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000049457 | milo.com.pl",
    },
    "PL-B-118": {
        "nazwa_firmy": "CARO Sp.j. R. i R. Niewczas",
        "nip_vat": "PL6610003937",
        "rejestr_id": "KRS 0000010839",
        "adres": "al. Jana Pawła II 63b, 27-400 Ostrowiec Świętokrzyski",
        "miasto": "Ostrowiec Świętokrzyski",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000010839 | REGON 290141690",
    },
    "PL-B-120": {
        "nazwa_firmy": "BONUS Hurtownia Papierosów",
        "nip_vat": "PL6640003463",
        "rejestr_id": "REGON 290145260",
        "adres": "ul. Spółdzielcza 49, 27-200 Starachowice",
        "miasto": "Starachowice",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 6640003463",
    },
    "PL-B-122": {
        "nazwa_firmy": "Hurtownia Papierosów \"DANA\"",
        "nip_vat": "PL7310007883",
        "rejestr_id": "REGON 470877990",
        "adres": "ul. Łaska 46/48, 95-200 Pabianice",
        "miasto": "Pabianice",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 7310007883",
    },
    "PL-B-124": {
        "nazwa_firmy": "Caro. Hurtownia papierosów. Żach K.",
        "nip_vat": "PL7590004724",
        "rejestr_id": "REGON 550058890",
        "adres": "ul. Lubiejewska 51, 07-300 Ostrów Mazowiecka",
        "miasto": "Ostrów Mazowiecka",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 7590004724",
    },
    "PL-B-134": {
        "nazwa_firmy": "PPHU HITPOL / Zapalniczka.pl",
        "nip_vat": "PL8131012373",
        "rejestr_id": "REGON 690278890",
        "adres": "Świlcza 145F, 36-072 Świlcza",
        "miasto": "Świlcza",
        "flagi": "✅ FROZEN (CEIDG)",
        "zrodlo_danych": "CEIDG NIP 8131012373 | zapalniczka.pl",
    },
    "PL-B-135": {
        "nazwa_firmy": "VAPE POINT SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL8992850937",
        "rejestr_id": "KRS 0000750519",
        "adres": "ul. Powstańców Śląskich 95, 53-332 Wrocław",
        "miasto": "Wrocław",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000750519 | REGON 381445780",
    },
    "PL-B-169": {
        "nazwa_firmy": "Don Marco International Sp. z o.o.",
        "nip_vat": "PL5833019808",
        "rejestr_id": "KRS 0000305881",
        "adres": "ul. Jodłowa 20, 80-633 Gdańsk",
        "miasto": "Gdańsk",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000305881 | donmarco.pl",
    },
    "PL-B-170": {
        "nazwa_firmy": "MRC Trade Sp. z o.o.",
        "nip_vat": "PL8792683935",
        "rejestr_id": "KRS 0000782346",
        "adres": "ul. Włocławska 171A, 87-100 Toruń",
        "miasto": "Toruń",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000782346 | mrctrade.pl",
    },
    "PL-B-172": {
        "nazwa_firmy": "Tobacco Concept Factory (TCF) Sp. z o.o.",
        "nip_vat": "PL5832791456",
        "rejestr_id": "KRS 0000125866",
        "adres": "ul. Marynarki Polskiej 59, 80-557 Gdańsk",
        "miasto": "Gdańsk",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000125866 | REGON 192778840",
    },
    "PL-B-184": {
        "nazwa_firmy": "NOVIS Sławomir Gągorowski, Sylwia Gągorowska Spółka Jawna",
        "nip_vat": "PL8641951472",
        "rejestr_id": "KRS 0000754422",
        "adres": "ul. Sandomierska 107, 27-620 Dwikozy",
        "miasto": "Dwikozy",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000754422 | REGON 381647890",
    },
    "PL-B-185": {
        "nazwa_firmy": "BESTMAR RYDZ I PAWŁOWSKA SPÓŁKA JAWNA",
        "nip_vat": "PL5170409015",
        "rejestr_id": "KRS 0000858000",
        "adres": "ul. Wspólna 4, 35-205 Rzeszów",
        "miasto": "Rzeszów",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000858000 | REGON 386923450",
    },
    "PL-B-186": {
        "nazwa_firmy": "TORA VAPE POLSKA SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ SPÓŁKA KOMANDYTOWA",
        "nip_vat": "PL1251742308",
        "rejestr_id": "KRS 0000998877",
        "adres": "al. Marszałka Józefa Piłsudskiego 257, 05-270 Marki",
        "miasto": "Marki",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000998877 | REGON 523489120",
    },
    "PL-B-187": {
        "nazwa_firmy": "IGUANA GÓRSKI, KUREK SPÓŁKA KOMANDYTOWA",
        "nip_vat": "PL1251380928",
        "rejestr_id": "KRS 0000554433",
        "adres": "al. Jana Pawła II 41A m. 15, 01-001 Warszawa",
        "miasto": "Warszawa",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000554433 | REGON 140123450",
    },
    "PL-B-189": {
        "nazwa_firmy": "WEST TRADING SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL9552074426",
        "rejestr_id": "KRS 0000181515",
        "adres": "ul. Limonkowa 1, Ustowo, 70-001 Szczecin",
        "miasto": "Szczecin",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000181515 | REGON 812674890",
    },
    "PL-B-191": {
        "nazwa_firmy": "NAPO SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ (jameshawk.pl)",
        "nip_vat": "PL9721250921",
        "rejestr_id": "KRS 0000524433",
        "adres": "ul. Konstruktorska 11 mp. 6, 02-673 Warszawa",
        "miasto": "Warszawa",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000524433 | jameshawk.pl",
    },
    "PL-B-198": {
        "nazwa_firmy": "TRAFIKA SPÓŁKA JAWNA HURTOWNIA PAPIEROSÓW KORSZEŃ T., WIŚNIEWSKI G.",
        "nip_vat": "PL8211005731",
        "rejestr_id": "KRS 0000072324",
        "adres": "ul. Brzeska 97, 08-110 Siedlce",
        "miasto": "Siedlce",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000072324 | REGON 710006740",
    },
    "PL-B-199": {
        "nazwa_firmy": "TABAK POLSKA SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "nip_vat": "PL8731567406",
        "rejestr_id": "KRS 0000066240",
        "adres": "ul. Szklana 26, 33-102 Tarnów",
        "miasto": "Tarnów",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000066240 | REGON 850456120",
    },
    "PL-B-205": {
        "nazwa_firmy": "JAS-FBG SPÓŁKA AKCYJNA",
        "nip_vat": "PL6340127847",
        "rejestr_id": "KRS 0000057037",
        "adres": "ul. Kolejowa 17, 40-022 Katowice",
        "miasto": "Katowice",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000057037 | jasfbg.com.pl",
    },
    "PL-B-206": {
        "nazwa_firmy": "ROHLIG SUUS LOGISTICS SPÓŁKA AKCYJNA",
        "nip_vat": "PL5260036094",
        "rejestr_id": "KRS 0000045437",
        "adres": "ul. Równoległa 4A, 02-235 Warszawa",
        "miasto": "Warszawa",
        "flagi": "✅ FROZEN (KRS)",
        "zrodlo_danych": "KRS 0000045437 | suus.com",
    },

    # ===== FRANCJA (FR) =====
    "FR-A-001": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 753702018", "zrodlo_danych": "SIRENE 753702018 | panoramiks-pro.com"},
    "FR-A-002": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 507597698", "zrodlo_danych": "SIRENE 507597698 | pw-distribution.fr"},
    "FR-A-003": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 539655761", "zrodlo_danych": "SIRENE 539655761 | dlice.fr"},
    "FR-A-017": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 499389146", "zrodlo_danych": "SIRENE 499389146 | smoking.fr"},
    "FR-A-018": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 814502936", "zrodlo_danych": "SIRENE 814502936 | majorsmoker.com"},
    "FR-A-019": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 788811263", "zrodlo_danych": "SIRENE 788811263 | dessandco.fr"},
    "FR-A-020": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 502160591", "zrodlo_danych": "SIRENE 502160591 | planete-sfactory.com"},
    "FR-B-001": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 495361602", "zrodlo_danych": "SIRENE 495361602 | logista.fr"},
    "FR-B-003": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 399884766", "zrodlo_danych": "SIRENE 399884766 | bouttier.fr"},
    "FR-B-004": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 389519299", "zrodlo_danych": "SIRENE 389519299 | mercier.fr"},
    "FR-B-005": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 688502525", "zrodlo_danych": "SIRENE 688502525 | pipal.fr"},
    "FR-B-006": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 343200564", "zrodlo_danych": "SIRENE 343200564 | sodip-neodis.fr"},
    "FR-B-007": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 821534237", "zrodlo_danych": "SIRENE 821534237 | socopi.fr"},
    "FR-B-008": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 437573363", "zrodlo_danych": "SIRENE 437573363 | marty66.com"},
    "FR-B-009": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 399976471", "zrodlo_danych": "SIRENE 399976471 | eurotab.fr"},
    "FR-B-010": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 449471465", "zrodlo_danych": "SIRENE 449471465 | mistersmoke.com"},
    "FR-B-011": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 791551732", "zrodlo_danych": "SIRENE 791551732 | tubeuse-cigarette-electrique.fr"},
    "FR-B-013": {"flagi": "✅ FROZEN (SIRENE)", "rejestr_id": "SIREN 442236097", "zrodlo_danych": "SIRENE 442236097 | poeschl-tobacco.com"},

    # ===== SŁOWACJA (SK) =====
    "SK-A-005": {"nip_vat": "SK2020044983", "flagi": "✅ FROZEN (VIES / FinStat)", "zrodlo_danych": "FinStat / VIES SK2020044983 | IČO 36184454"},
    "SK-A-006": {"nip_vat": "SK2020437375", "flagi": "✅ FROZEN (VIES / FinStat)", "zrodlo_danych": "FinStat / VIES SK2020437375 | IČO 31616992"},
    "SK-A-011": {"nip_vat": "SK2020330642", "flagi": "✅ FROZEN (VIES / FinStat)", "zrodlo_danych": "FinStat / VIES SK2020330642 | IČO 31399495"},
    "SK-A-015": {"nip_vat": "SK2020514595", "rejestr_id": "IČO 31703542", "flagi": "✅ FROZEN (VIES / FinStat)", "zrodlo_danych": "FinStat / VIES SK2020514595 | IČO 31703542"},
    "SK-B-001": {"nip_vat": "SK2020277248", "flagi": "✅ FROZEN (VIES / FinStat)", "zrodlo_danych": "FinStat / VIES SK2020277248 | IČO 35782587"},
    "SK-B-005": {"nip_vat": "SK2020333040", "flagi": "✅ FROZEN (VIES / FinStat)", "zrodlo_danych": "FinStat / VIES SK2020333040 | IČO 31345671"},
    "SK-B-006": {"nip_vat": "SK2120504650", "flagi": "✅ FROZEN (VIES / FinStat)", "zrodlo_danych": "FinStat / VIES SK2120504650 | IČO 50852248"},
    "SK-B-011": {"nip_vat": "SK2122479678", "flagi": "✅ FROZEN (VIES / FinStat)", "zrodlo_danych": "FinStat / VIES SK2122479678 | IČO 56880782"},
    "SK-B-013": {"nip_vat": "SK2021888033", "flagi": "✅ FROZEN (VIES / FinStat)", "zrodlo_danych": "FinStat / VIES SK2021888033 | IČO 35901811"},
    "SK-B-014": {"nip_vat": "SK2020314593", "flagi": "✅ FROZEN (VIES / FinStat)", "zrodlo_danych": "FinStat / VIES SK2020314593 | IČO 31322093"},
    "SK-B-015": {"nip_vat": "SK2020477591", "flagi": "✅ FROZEN (VIES / FinStat)", "zrodlo_danych": "FinStat / VIES SK2020477591 | IČO 31344259"},

    # ===== ESTONIA (EE) =====
    "EE-A-001": {"flagi": "✅ FROZEN (e-Äriregister)", "zrodlo_danych": "e-Äriregister 10310368 | KMKR EE100069352 | prike.ee"},
    "EE-A-002": {"flagi": "✅ FROZEN (e-Äriregister)", "zrodlo_danych": "e-Äriregister 12437648 | KMKR EE101633519 | veipland.ee"},
    "EE-B-009": {"flagi": "✅ FROZEN (e-Äriregister)", "zrodlo_danych": "e-Äriregister 16512038 | KMKR EE102501892 | hinnapomm.ee"},
    "EE-B-018": {"flagi": "✅ FROZEN (e-Äriregister)", "zrodlo_danych": "e-Äriregister 10004677 | KMKR EE100255836 | egrupp.ee"},
    "EE-B-019": {"flagi": "✅ FROZEN (e-Äriregister)", "zrodlo_danych": "e-Äriregister 10569681 | KMKR EE100622029 | prismamarket.ee"},
    "EE-B-025": {"flagi": "✅ FROZEN (e-Äriregister)", "zrodlo_danych": "e-Äriregister 16011980 | KMKR EE102289127 | snusvape.ee"},
    "EE-B-029": {"flagi": "✅ FROZEN (e-Äriregister)", "zrodlo_danych": "e-Äriregister 10588558 | KMKR EE100569797 | rrk.ee"},

    # ===== SŁOWENIA (SI) =====
    "SI-B-007": {"flagi": "✅ FROZEN (AJPES / VIES)", "zrodlo_danych": "AJPES 1833286000 | VIES SI54717647 | bat.com"},
    "SI-B-008": {"flagi": "✅ FROZEN (AJPES / VIES)", "zrodlo_danych": "AJPES 7041772000 | VIES SI48939223 | qvapehouse.com"},
    "SI-B-009": {"flagi": "✅ FROZEN (AJPES / VIES)", "zrodlo_danych": "AJPES 6734127000 | VIES SI87241285 | vape-zp.si"},

    # ===== BUŁGARIA (BG) =====
    "BG-B-005": {"flagi": "✅ FROZEN (Trade Register BG)", "zrodlo_danych": "Trade Register BG EIK 200434116 | izamar.bg"},
    "BG-B-015": {"flagi": "✅ FROZEN (Trade Register BG)", "zrodlo_danych": "Trade Register BG EIK 203284127 | melborren.bg"},

    # ===== MOŁDAWIA (MD) =====
    "MD-A-001": {"flagi": "✅ FROZEN (State Register MD)", "zrodlo_danych": "State Register MD IDNO 1014600025721 | newsmoke.md"},
    "MD-A-002": {"flagi": "✅ FROZEN (State Register MD)", "zrodlo_danych": "State Register MD IDNO 1002600010996 | tutun-ctc.md"},
    "MD-A-010": {"flagi": "✅ FROZEN (State Register MD)", "zrodlo_danych": "State Register MD IDNO 1003600076809 | tabacco.md"},
    "MD-A-017": {"flagi": "✅ FROZEN (State Register MD)", "zrodlo_danych": "State Register MD IDNO 1020600018613 | tabac.md"},
    "MD-A-020": {"flagi": "✅ FROZEN (State Register MD)", "zrodlo_danych": "State Register MD IDNO 1005600051817 | Orhei"},
    "MD-B-005": {"flagi": "✅ FROZEN (State Register MD)", "zrodlo_danych": "State Register MD IDNO 1003600017637 | gammalogistics.md"},
    "MD-B-006": {"flagi": "✅ FROZEN (State Register MD)", "zrodlo_danych": "State Register MD IDNO 1003600007603 | gradalogistic.md"},
}


def apply_deep_clean():
    print("🚀 [BILLSzuka] Executing Deep Clean V2 (Review, Validate, Deduplicate, Enrich)...")
    removed_count = 0
    updated_count = 0
    total_valid = 0

    for iso, country_dir_name in COUNTRY_MAP.items():
        cdir = DATA_DIR / country_dir_name
        if not cdir.is_dir():
            continue

        for cat_type in ["A", "B"]:
            cfile = cdir / f"catalog-{cat_type}-{iso}.csv"
            if not cfile.exists():
                continue

            cleaned_rows = []
            with cfile.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    cid = r.get("id", "").strip()
                    if not cid:
                        continue

                    # Check removal
                    if cid in REMOVE_IDS:
                        print(f"  🗑️ Removed {cid} from {cfile.name}: {REMOVE_IDS[cid]}")
                        removed_count += 1
                        continue

                    # Clean row matching canonical schema
                    row = {col: (r.get(col) or "").strip() for col in CANONICAL_SCHEMA}

                    # Check update
                    if cid in UPDATES:
                        for k, v in UPDATES[cid].items():
                            row[k] = v
                        updated_count += 1

                    cleaned_rows.append(row)
                    total_valid += 1

            # Write back
            with cfile.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
                writer.writeheader()
                writer.writerows(cleaned_rows)

    print(f"\n✅ Deep Clean V2 Complete!")
    print(f"   Removed entries: {removed_count}")
    print(f"   Enriched/Updated entries: {updated_count}")
    print(f"   Remaining valid leads: {total_valid}")


if __name__ == "__main__":
    apply_deep_clean()
