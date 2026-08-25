"""tools/pdf_photo_verification.py — printable PDF weryfikacji listy firm ze zdjęć.

Layout dopasowany do zdjęć faktur (Kod kontrahenta | Nazwa kontrahenta | Adres | NIP | Telefon | Fax)
+ nowe kolumny: [Powód wykluczenia] [Notatki / Wynik weryfikacji].

Output: data/verification/2026-08-24-photo-list-verification.pdf + .md
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# --- Polish-safe font registration (jak w pozostałych PDF-ach projektu) ---
pdfmetrics.registerFont(TTFont("V", "/System/Library/Fonts/Supplemental/Verdana.ttf"))
pdfmetrics.registerFont(TTFont("VB", "/System/Library/Fonts/Supplemental/Verdana Bold.ttf"))
pdfmetrics.registerFont(TTFont("VI", "/System/Library/Fonts/Supplemental/Verdana Italic.ttf"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_MD = PROJECT_ROOT / "data" / "verification" / "companies.md"
SOURCE_PDF_AUDIT = PROJECT_ROOT / "data" / "verification" / "2026-08-24-photo-list.md"
OUT_PDF = PROJECT_ROOT / "data" / "verification" / "2026-08-24-photo-list-verification.pdf"
OUT_MD = PROJECT_ROOT / "data" / "verification" / "2026-08-24-photo-list-verification.md"

DATE_TEXT = "24 sierpnia 2026"

# --- Style + render ---
PAGE_W, PAGE_H = landscape(A4)  # poziomy A4 — więcej kolumn
ACCENT = HexColor("#1F1F1F")
ACCENT_LT = HexColor("#6B6B6B")
LINE = HexColor("#D0D0D0")
TEXT = HexColor("#1A1A1A")
MUTED = HexColor("#707070")
GREEN = HexColor("#1B7A3A")
RED = HexColor("#A8201A")
AMBER = HexColor("#A87500")
LIGHT_GREEN = HexColor("#EAF6EC")
LIGHT_RED = HexColor("#FBEBEA")
LIGHT_AMBER = HexColor("#FCF5E3")
ICE_BLUE = HexColor("#0E7490")        # 🧊 cyan-700 — for ZAMROŻONY / FROZEN status
ICE_BG = HexColor("#ECFEFF")          # cyan-50 — subtle background for FROZEN tags

H1 = ParagraphStyle("H1", fontName="VB", fontSize=24, leading=28, textColor=TEXT, alignment=TA_LEFT)
H1_SUB = ParagraphStyle("H1_SUB", fontName="V", fontSize=11, leading=14, textColor=MUTED, alignment=TA_LEFT)
H2 = ParagraphStyle("H2", fontName="VB", fontSize=11, leading=14, textColor=TEXT, spaceBefore=10, spaceAfter=4)
H3 = ParagraphStyle("H3", fontName="VI", fontSize=8, leading=10, textColor=MUTED, spaceBefore=2, spaceAfter=4)
BODY = ParagraphStyle("BODY", fontName="V", fontSize=8.5, leading=11, textColor=TEXT, alignment=TA_LEFT, spaceAfter=3)
BODY_S = ParagraphStyle("BODY_S", fontName="V", fontSize=7.8, leading=10, textColor=TEXT, alignment=TA_LEFT, spaceAfter=1)
BODY_SM = ParagraphStyle("BODY_SM", fontName="V", fontSize=7.2, leading=9, textColor=TEXT, alignment=TA_LEFT, spaceAfter=1)
HEADER_STYLE = ParagraphStyle("HEADER", fontName="VB", fontSize=8, leading=10, textColor=white, alignment=TA_LEFT)
META = ParagraphStyle("META", fontName="V", fontSize=6.8, leading=8.5, textColor=MUTED)
META_R = ParagraphStyle("META_R", fontName="V", fontSize=7.5, leading=10, textColor=MUTED, alignment=TA_RIGHT)

STATUS_FONT_COLORS = {
    "ACTIVE": GREEN,
    "DUPLIKAT": AMBER,
    "EXCLUDE": RED,
    "HOLD": AMBER,
}

STATUS_BG_COLORS = {
    "ACTIVE": LIGHT_GREEN,
    "DUPLIKAT": LIGHT_AMBER,
    "EXCLUDE": LIGHT_RED,
    "HOLD": LIGHT_AMBER,
}


# --- Dane weryfikacyjne (z 2026-08-24-photo-list.md) ---
ENTRIES = [
    # ============ CZECHY ============
    {
        "country": "CZ",
        "kod": "VIVACE SPOL.- CZECHY",
        "nazwa": "VIVACE spol. s r.o.",
        "adres": "Jaurisova 515/4, 140 00 Praha 4 - Michle",
        "nip": "CZ 29154529",
        "telefon": "+420 777 680 940",
        "fax": "",
        "status": "DUPLIKAT",
        "reason": "Duplikat — już w master jako CZ-A-006 (hurtownik, dobra-trafika.com)",
        "notes": "Pełna zgodność NIP + adres z ARES. Już zweryfikowany <font color='#0E7490'><b>[ZAMROŻONY]</b></font> w master.",
    },
    {
        "country": "CZ",
        "kod": "HZ/SHANTI & CO. S.R.",
        "nazwa": "SHANTI & Co. s.r.o.",
        "adres": "Zábrdovická 801/11, 615 00 Brno 15",
        "nip": "CZ 25549154",
        "telefon": "(+420) 777 749 789",
        "fax": "",
        "status": "DUPLIKAT",
        "reason": "Duplikat — już w master jako CZ-A-008 (hurtownik, shanti.cz)",
        "notes": "Pełna zgodność NIP + adres z ARES. Już zweryfikowany <font color='#0E7490'><b>[ZAMROŻONY]</b></font> w master.",
    },
    {
        "country": "CZ",
        "kod": "OREA",
        "nazwa": "OREA HOTELS s.r.o.",
        "adres": "Na Pankráci 1062/58, 140 00 Praha 4",
        "nip": "CZ 27176657",
        "telefon": "",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Zła branża — hotelarstwo (CZ-NACE 55100), NIE dystrybutor tytoniowy",
        "notes": "ARES: 'Ubytování v hotelích'. Właściciel największej czeskiej sieci hoteli OREA HOTELS & RESORTS. Na fakturze prawdopodobnie noclegi z delegacji handlowej.",
    },
    {
        "country": "CZ",
        "kod": "HZ/KEVARO S.R.O.",
        "nazwa": "Kevaro s.r.o.",
        "adres": "Sokolská 1605/66, 2 Praha (dawniej, adres 29.10.2010 - 2.8.2021)",
        "nip": "CZ 24755681",
        "telefon": "+420 725 506 654",
        "fax": "",
        "status": "HOLD",
        "reason": "Adres niezgodny z rejestrem; brak info o branży tytoniowej",
        "notes": "ARES IČO 24755681 (znaleziony 2026-08-24). Aktualny adres: náměstí Přátelství 1518/2, Praha - Hostivař (od 26.6.2023). Sokolská 1605/66 to historyczny adres firmy (29.10.2010–2.8.2021). Vlastník: Invest Rom Service s.r.o. (SK, Banská Bystrica, IČO 51208091) od 26.6.2023. Předmět podnikání: Výroba, obchod a služby + Prodej kvasného lihu. **NIE branża tytoniowa**.",
    },
    {
        "country": "CZ",
        "kod": "281268",
        "nazwa": "Jana Zelezna",
        "adres": "Jana Žižky 348, 58856 Telč",
        "nip": "(brak — brak śladu w ARES)",
        "telefon": "",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Osoba fizyczna — brak śladu OSVČ w ARES",
        "notes": "Sprawdzono 2026-08-24: brak Jana Železná (ani podobnych nazwisk) w ARES dla Telč 58856. Brak powiązania z branżą tytoniową. Jednorazowa faktura prywatna.",
    },
    {
        "country": "CZ",
        "kod": "JAN SEVIC",
        "nazwa": "Jan Ševic (Ing.)",
        "adres": "Hviezdoslavova 1162, 356 01 Sokolov",
        "nip": "CZ 7005132222",
        "telefon": "+420 608 062 713",
        "fax": "",
        "status": "DUPLIKAT",
        "reason": "Duplikat — już w master jako CZ-A-004 (plnicky-powermatic.cz)",
        "notes": "Autoryzowany dystrybutor PowerMatic (I+, II+, III+, IV, V). W master <font color='#A87500'><b>[DO-WERYFIKACJI]</b></font>.",
    },
    {
        "country": "CZ",
        "kod": "281017",
        "nazwa": "Iveta Buresova",
        "adres": "Arménská 2763/314, 272 01 Kladno",
        "nip": "(brak — brak potwierdzonej Ivety Burešovej w Kladno)",
        "telefon": "",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Osoba fizyczna — brak potwierdzenia tożsamości w Kladno",
        "notes": "Sprawdzono 2026-08-24: w ARES istnieją 3 różne Ivety Burešovej (IČO 87360501 Praha/Chodov, IČO 45574251 Náchod, IČO 63557843 Ostrov, IČO 74305417 Praha) — ŻADNA nie ma siedziby w Kladno. Žadna nie odpowiada danym z faktury (Arménská 2763/314, 272 01 Kladno). Tożsamość niepotwierdzona.",
    },
    {
        "country": "CZ",
        "kod": "HOSTING TIME S.R.O.",
        "nazwa": "Hosting time s.r.o.",
        "adres": "Švabinského 1700/4, 702 00 Ostrava 2",
        "nip": "CZ 04302231",
        "telefon": "+420 608 184 599",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Zła branża — nazwa sugeruje hosting IT, brak śladu handlu tytoniem",
        "notes": "ARES potwierdza rejestrację (Moravská Ostrava, 6-9 pracowników), ale brak CAEN tytoniowego. Prawdopodobnie usługa hostingowa / IT.",
    },
    {
        "country": "CZ",
        "kod": "281267",
        "nazwa": "Hana Sretrova",
        "adres": "M. Švabinského 662, 418 01 Bílina",
        "nip": "(brak — Mgr. Hana Šretrová v Luhačovice to INNA osoba)",
        "telefon": "+420 606 084 673",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Osoba fizyczna — znaleziona Mgr. Hana Šretrová to inna osoba (Luhačovice, NIE Bílina)",
        "notes": "Sprawdzono 2026-08-24: Mgr. Hana Šretrová IČO 76140598 (psycholożka, předmět: poradenská činnost + mimoškolní výchova + textil), sídlo Družstevní 883, Luhačovice 76326 — to NIE ta sama osoba co na fakturze (M. Švabinského 662, 418 01 Bílina). Brak powiązania z tytoniem.",
    },
    {
        "country": "CZ",
        "kod": "281265",
        "nazwa": "Eva Machacna (OSVČ — z reconsideracji 2026-08-24)",
        "adres": "Kunratice u Cvikova 393, 471 55",
        "nip": "CZ 44560176",
        "telefon": "",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead po deep re-verification — CZ-NACE: Maloobchod s převahou potravin, nápojů a tabákových výrobků",
        "notes": "ARES IČO 44560176 (znaleziony 2026-08-24). Datum vzniku 28.9.1992. Sídlo Kunratice u Cvikova 393. CZ-NACE: Maloobchod s převahou potravin, nápojů a tabákových výrobků v nespecializovaných prodejnách. Předmět podnikání: Prodej smíšeného zboží (potraviny + tytoń). Rekomendacja: B4 (akcesoria + artykuły dla palaczy). Mały wolumen.",
    },
    {
        "country": "CZ",
        "kod": "ETABAK.COM JAN ZIMOL",
        "nazwa": "Etabak.com — Jan Zimola",
        "adres": "Osvoboditelů 1107, 438 01 Žatec (aktualny adres; Pekařská 2386 to stary adres)",
        "nip": "CZ 74215019 (8608082989 to rodné číslo)",
        "telefon": "+420 777 593 840",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny e-shop + velkoobchod z kuřáckými potřeby",
        "notes": "IČO 74215019 (znaleziony 2026-08-24 w ARES, podnikatel.cz, Finmag). Vlastnik osobiście Jan Zimola (od 1.11.2006). CZ-NACE: 471 Maloobchod v nespecializovaných prodejnách + 20 Výroba chemických látek. Živnosti: Prodej chemických látek (vázaná od 24.10.2022) + Výroba, obchod a služby - Velkoobchod a maloobchod (volná od 1.11.2006). DIČ CZ8608082989 (to jest numer rodny, nie IČO). Adres w zdjęciu (Pekařská 2386) to stary adres; aktualnie Osvoboditelů 1107. 1-5 pracowników. Prawdopodobnie A4 multi-brand lub B4 akcesoria. Wysoki priorytet dla CZ.",
    },
    {
        "country": "CZ",
        "kod": "HZ/DOBRY TABAK",
        "nazwa": "Dobrý tabák s.r.o.",
        "adres": "Ruská 83/24, 703 00 Ostrava 3",
        "nip": "CZ 28595611",
        "telefon": "+420 737 611 301",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny kamenný obchod + e-shop + velkoobchod (vodní dýmky, tabáky)",
        "notes": "IČO 28595611, dobrytabak.cz. Sklep stacjonarny Ostrava-Vítkovice + e-shop. Prawdopodobnie B4 (shisha/akcesoria) z cross-sell na PowerMatic.",
    },
    # ============ RUMUNIA ============
    {
        "country": "RO",
        "kod": "COTIGA MARIN ZESEN",
        "nazwa": "Zasen Trade Invest SRL",
        "adres": "Soldat Stefan Simion 41, 040588 Bucharest",
        "nip": "RO 41399635",
        "telefon": "0723 019 747",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Zła branża + błędny adres — CAEN Restaurante, zarejestrowany adres Bd. Tineretului 2",
        "notes": "CUI aktywny (J40/9305/2019), ale cautarefirme.ro klasyfikuje jako 'Restaurante'. Adres na fakturze ≠ adres w rejestrze. Możliwa faktura od podmiotu powiązanego.",
    },
    {
        "country": "RO",
        "kod": "TABACIOC GRUP SRL",
        "nazwa": "Tabacioc Grup SRL",
        "adres": "Soseaua Stefan cel Mare, 020152 Bucuresti",
        "nip": "RO 25777283",
        "telefon": "+40 723 564 876",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny retail żywność+napoje+tytoń (40M RON 2025)",
        "notes": "CUI 25777283, J2009007894407, Stefan cel Mare 60 Sector 2. CAEN 4711. Duży gracz — sprawdzić asortyment tytoniowy w intake.",
    },
    {
        "country": "RO",
        "kod": "SIBIS CONCEPT COMPAN",
        "nazwa": "SIBIS CONCEPT COMPANY SRL",
        "adres": "Strada ZIZINULUI 106A/ D3-B-P-05, 500407 Brașov",
        "nip": "RO 38359096",
        "telefon": "",
        "fax": "",
        "status": "DUPLIKAT",
        "reason": "Duplikat — już w master jako RO-A-008 (etutun.ro)",
        "notes": "Specjalistyczny e-com Powermatic (II+ | III+ | IV) w Braszowie. Już zweryfikowany <font color='#0E7490'><b>[ZAMROŻONY]</b></font> w master.",
    },
    {
        "country": "RO",
        "kod": "SC RIO TUTUNGERIE SR",
        "nazwa": "SC RIO TUTUNGERIE SRL",
        "adres": "STR. ȘTEFAN CEL MARE NR.22, SATU MARE",
        "nip": "RO 36305839",
        "telefon": "+40 751 551 169",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny hurt tytoniowy CAEN 4635 (22M RON 2025)",
        "notes": "CUI 36305839, J2016000651308. Duży gracz w Satu Mare. TOP priorytet dla hurtu RO. B8.",
    },
    {
        "country": "RO",
        "kod": "SC GRANDE PLAYER SRL",
        "nazwa": "SC GRANDE PLAYER SRL",
        "adres": "Șos. Pantelimon, nr. 291, bl. 9, sc. C, 014459 București",
        "nip": "RO 31483207",
        "telefon": "+40 741 673 074",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny detal tytoniowy CAEN 4726 (București)",
        "notes": "CUI 31483207, J2013004687409, Pantelimon 291, Sector 2. Mniejszy lead detaliczny. B4.",
    },
    {
        "country": "RO",
        "kod": "S.C. OSTRO-VICE S.R.",
        "nazwa": "S.C. OSTRO-VICE S.R.L.",
        "adres": "Pandurilor 13, bl. A8/2, 240087 Râmnicu Vâlcea",
        "nip": "RO 36832359",
        "telefon": "+40 755 943 429",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny (1.5M RON 2024), CAEN do weryfikacji",
        "notes": "CUI 36832359, J38/889/2016. W intake sprawdzić CAEN + asortyment. Kategoria B.",
    },
    {
        "country": "RO",
        "kod": "ROCADRINA SRL",
        "nazwa": "ROCADRINA SRL",
        "adres": "CIHEIULUI 144, 410600 Oradea",
        "nip": "RO 16483840",
        "telefon": "+40 770 304 803",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny hurt tytoniowy CAEN 4635 (Oradea)",
        "notes": "CUI 16483840, J05/1024/2004. CAEN 4635 potwierdzone. Hurtownik tytoniowy w Oradei. B8.",
    },
    {
        "country": "RO",
        "kod": "RAZVAN ANGHENE",
        "nazwa": "Răzvan Anghene (Dragoș)",
        "adres": "Unirea Principatelor nr. 2, Focșani, 620091",
        "nip": "(brak — Răzvan Anghene NIE ma firmy/PFA; to polityk)",
        "telefon": "+40 755 000 006",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Brak firmy/PFA — to polityk lokalny AUR, byly dyrektor OTP Bank",
        "notes": "Sprawdzono 2026-08-24: brak Răzvan Anghene w ONRC jako PFA/II/SRL/SA. To osoba publiczna — byly dyrektor OTP Bank Focșani, kandydat AUR na burmistrza Focșani (2024), radny CL Focșani (rezygnacja 2026 po powołaniu do CA CUP SA Vrancea). NIE przedsiębiorca tytoniowy. Możliwe: prywatna faktura za usługe doradczą lub podobne.",
    },
    {
        "country": "RO",
        "kod": "PRIMONET RO SRL",
        "nazwa": "PRIMONET RO SRL",
        "adres": "AMATIULUI 47, 440252 Satu Mare",
        "nip": "RO 29972252",
        "telefon": "+40 751 551 169",
        "fax": "",
        "status": "DUPLIKAT",
        "reason": "Duplikat — już w master jako RO-B-009 (primonet.ro)",
        "notes": "UWAGA: telefon w master '+40 21 318 90 00', w zdjęciu '+40 751 551 169' — rozbieżność. Już zweryfikowany <font color='#0E7490'><b>[ZAMROŻONY]</b></font> w master.",
    },
    {
        "country": "RO",
        "kod": "MAFERDI S.R.L.",
        "nazwa": "MAFERDI S.R.L.",
        "adres": "MIORITEI 2/2, Bacău (adres częściowy)",
        "nip": "RO 26044671",
        "telefon": "0748 609 163",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny handel tytoniowy w Bacău",
        "notes": "CUI 26044671. Widoczny na afacerist.ro jako sprzedawca țigări electronice + țigări + trabucuri. B4 (akcesoria + e-papierosy).",
    },
    {
        "country": "RO",
        "kod": "12.10.2018DZI",
        "nazwa": "Luca Cristian Lucian (PFA?)",
        "adres": "Str. Maramureș, bl. C19, ap. 6, 200024 Craiova",
        "nip": "(brak — brak potwierdzonego PFA w ONRC dla tego adresu)",
        "telefon": "+40 742 009 158",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Osoba fizyczna — brak potwierdzenia PFA w ONRC/ANAF",
        "notes": "Sprawdzono 2026-08-24: brak Luca Cristian Lucian PFA z adresem Str. Maramureș, bl. C19, ap. 6, 200024 Craiova w ONRC/ANAF. Istnieje Luca Cristian PFA w Sibiu (handel tekstyl/obuwie, CUI F2002000224327, N. North Data) — ale inna osoba, inny adres. Tożsamość niepotwierdzona. Jednorazowa faktura prywatna.",
    },
    {
        "country": "RO",
        "kod": "HZ/GRAVO",
        "nazwa": "GRAVO EXPRESS SRL",
        "adres": "Str. Sănătății Nr.7, BL8, Ap11, 520064 Sfântu Gheorghe",
        "nip": "RO 17456444",
        "telefon": "0721 569 270",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny retail (CAEN 4778 — inny retail), 1.6M RON 2024",
        "notes": "CUI 17456444, J2005000177141. CAEN 4778 (Comert cu amanuntul — nowe wyroby). Sprawdzić czy obejmuje tytoń. B4.",
    },
    {
        "country": "RO",
        "kod": "GOLDEN TIP",
        "nazwa": "GOLDEN TIP IMPORT EXPORT SRL",
        "adres": "STR.UNIRII 21/25 (+ magazyn Rășinari 429), 400113 Cluj-Napoca",
        "nip": "RO 31828233",
        "telefon": "+40 761 250 819",
        "fax": "",
        "status": "DUPLIKAT",
        "reason": "Duplikat — już w master jako RO-A-004 (tuburipentrutigari.ro)",
        "notes": "UWAGA: telefon w master '0744 545 936', w zdjęciu '+40 761 250 819' — rozbieżność. Już zweryfikowany <font color='#0E7490'><b>[ZAMROŻONY]</b></font> w master.",
    },
    {
        "country": "RO",
        "kod": "ELMARIO DISTRIBUTION",
        "nazwa": "ElMario Distribution SRL",
        "adres": "Comuna VALEA CĂLUGĂREASCĂ 99, 135949 Jud. Prahova",
        "nip": "RO 33393950",
        "telefon": "+40 726 268 874",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny retail (CAEN 4719 — inny detal, NIE tytoń stricte)",
        "notes": "CUI 33393950, J29/1003/2014, Blejoi/Prahova. CAEN 4719. Prawdopodobnie B4 (akcesoria). Średni priorytet.",
    },
    {
        "country": "RO",
        "kod": "DVD MASTER SRL",
        "nazwa": "DVD Master SRL",
        "adres": "Bucharest (Giurgiu) — bd.54/2D, ap.45, 080122 Giurgiu",
        "nip": "RO 15879480",
        "telefon": "0040 723 550 358",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny hurt tytoniowy CAEN 4635 (61M RON 2025!)",
        "notes": "CUI 15879480, J2003000403523. DUŻY gracz hurtowy w Giurgiu. TOP priorytet dla działu sprzedaży. B8.",
    },
    {
        "country": "RO",
        "kod": "150713-14",
        "nazwa": "DIPA CONCEPT SRL",
        "adres": "BLD. SCHITU MĂGUREANU Nr. 27-33 27/33, București",
        "nip": "RO 31861043",
        "telefon": "+40 758 550 055",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Działalność zawieszona — status INACTIVĂ w firmealert.ro",
        "notes": "CUI 31861043, J40/7708/2013. CAEN 4635 (hurt tytoniowy), ale firma wykreślona. Dodać do archiwum.",
    },
    {
        "country": "RO",
        "kod": "COTIGA MARIN COTY SH",
        "nazwa": "COTY SHOP INVEST S.R.L.",
        "adres": "STR.IZVORUL MUREȘULUI NR.9, BL. D9 SC.6, 040588 BUCUREȘTI",
        "nip": "RO 48831012",
        "telefon": "0723 019 747",
        "fax": "",
        "status": "DUPLIKAT",
        "reason": "Duplikat — już w master jako RO-A-009 (prawidłowy CUI 48715727, NIE 48831012)",
        "notes": "BŁĄD W CUI: foto podaje 48831012, prawidłowy CUI 48715727. Administrator: COTIGĂ MARIN (ten sam co wpis 'Cotiga Marin').",
    },
    {
        "country": "RO",
        "kod": "COTIGA MARIN",
        "nazwa": "Cotiga Marin (osoba fizyczna)",
        "adres": "Soldat Stefan Simion 41, 040588 Bucharest",
        "nip": "(brak osobistego CUI; admin 2 firm)",
        "telefon": "0723 019 747",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Duplikat admina — COTIGĂ MARIN to administrator COTY SHOP INVEST + ZASEN TRADE INVEST",
        "notes": "Sprawdzono 2026-08-24 (datasrl.ro): COTIGĂ MARIN (Buzău) jest administratorem 2 firm: (1) COTY SHOP INVEST S.R.L. (CUI 48715727, Sector 4, AKTYWNA); (2) ZASEN TRADE INVEST S.R.L. (CUI 41399635, Sector 4, INAKTYWNA/radiată). Własnego PFA/II NIE ma. Telefon +40723019747 widoczny w odpowiedziach na Facebook (Cotiga Marin jako admin COTY SHOP). Faktura prywatna wystawiona przez admina. **Scal z istniejącym RO-A-009 (COTY SHOP)**.",
    },
    {
        "country": "RO",
        "kod": "AM/CERBU IOANA",
        "nazwa": "Cerbu Ioana",
        "adres": "Jilava, Str. Toamnei nr 5, 077120 Jud. Ilfov",
        "nip": "(brak osobistego CUI; admin GRAND PRODUCT SRL)",
        "telefon": "+40 764 088 453",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Osoba fizyczna — administrator GRAND PRODUCT SRL (mobilier, suspendată)",
        "notes": "Sprawdzono 2026-08-24 (datasrl.ro): CERBU IOANA (București) administrator firmy GRAND PRODUCT SRL (CUI 16049841, J23/27/2004, Sat Jilava, CAEN 4647 comerț cu ridicata al mobilei/covoarelor/iluminatului). GRAND PRODUCT: wtrerupere temporară de activitate (firmeo.ro) + suspendată (firme360.ro). Własnego PFA/II NIE znaleziono. Brak powiązania z branżą tytoniową.",
    },
    {
        "country": "RO",
        "kod": "BLK TRADE",
        "nazwa": "BLK TRADE MARKET S.R.L.",
        "adres": "Bulevard Tudor Vladimirescu 15, 700305 Iași",
        "nip": "RO 40694700",
        "telefon": "0040 740 768 387",
        "fax": "",
        "status": "ACTIVE",
        "reason": "Nowy lead — aktywny e-commerce (CAEN 4791). UWAGA: błędny CUI w zdjęciu",
        "notes": "BŁĄD W CUI: foto podaje 40694700, prawidłowy CUI 40638971, J22/855/2019. W intake wpisać 40638971.",
    },
    {
        "country": "RO",
        "kod": "ARTHEK MACHINES SRL",
        "nazwa": "ARTHEK Machines SRL",
        "adres": "Noua 49, 505100 Codlea",
        "nip": "RO 43407106",
        "telefon": "+40 771 643 634",
        "fax": "",
        "status": "EXCLUDE",
        "reason": "Zła branża — CAEN 3314 (naprawa urządzeń elektr.), nie dystrybutor",
        "notes": "CUI 43407106. Domena 'Machines' sugeruje maszynki, ale firma to serwis (naprawa sprzętu elektr.). Opcjonalnie: dodać jako anti-pattern / competitor intel.",
    },
]


def _color_status(text, status_key):
    color = STATUS_FONT_COLORS.get(status_key, TEXT)
    return f"<font color='#{color.hexval()[2:]}'><b>{text}</b></font>"


def _bg_status(text, status_key):
    color = STATUS_BG_COLORS.get(status_key, white)
    inner = Paragraph(f"<font color='#{STATUS_FONT_COLORS.get(status_key, TEXT).hexval()[2:]}'><b>{text}</b></font>", BODY_SM)
    return inner, color


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(1.0 * cm, PAGE_H - 1.0 * cm, PAGE_W - 1.0 * cm, PAGE_H - 1.0 * cm)
    canvas.setFont("V", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(1.0 * cm, PAGE_H - 0.85 * cm, "BILLS Sp. z o.o.  ·  Dystrybucja PowerMatic & Hawk")
    canvas.drawRightString(PAGE_W - 1.0 * cm, PAGE_H - 0.85 * cm, "Weryfikacja listy firm ze zdjęć (companies.md)")
    canvas.line(1.0 * cm, 1.0 * cm, PAGE_W - 1.0 * cm, 1.0 * cm)
    canvas.setFont("V", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(1.0 * cm, 0.85 * cm, "BILLS Sp. z o.o.  ·  Ostrzeszów  ·  serwis@bills.pl")
    canvas.drawRightString(PAGE_W - 1.0 * cm, 0.85 * cm, f"Strona {doc.page}  ·  {DATE_TEXT}")
    canvas.restoreState()


def data_table(headers, rows, col_widths, body_style=BODY_SM):
    data = [[Paragraph(h, HEADER_STYLE) for h in headers]]
    for r in rows:
        # r: (country, kod, nazwa, adres, nip, tel, fax, status, reason, notes, bg)
        data.append([
            Paragraph(r[0], BODY_SM),  # kraj
            Paragraph(r[1], BODY_SM),  # kod
            Paragraph(r[2], BODY_SM),  # nazwa
            Paragraph(r[3], BODY_SM),  # adres
            Paragraph(r[4], BODY_SM),  # nip
            Paragraph(r[5], BODY_SM),  # telefon
            Paragraph(r[6], BODY_SM),  # fax
            Paragraph(r[7], BODY_SM),  # status
            Paragraph(r[8], BODY_SM),  # reason
            Paragraph(r[9], BODY_SM),  # notes
        ])

    tbl = Table(data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, ACCENT_LT),
    ]
    # row-level backgrounds by status (col 7)
    for i, r in enumerate(rows, start=1):
        bg = r[10]
        style_cmds.append(("BACKGROUND", (7, i), (7, i), bg))

    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def stat_table(rows, col_w):
    data = [[Paragraph(f"<b>{r[0]}</b>", BODY_S) for r in rows], [Paragraph(r[1], BODY_S) for r in rows]]
    tbl = Table(data, colWidths=[col_w] * len(rows))
    tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, ACCENT_LT),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, ACCENT_LT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F4F4F4")),
    ]))
    return tbl


def build_pdf():
    out_pdf = str(OUT_PDF)
    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=landscape(A4),
        leftMargin=1.0 * cm,
        rightMargin=1.0 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
        title="Weryfikacja listy firm ze zdjęć — 2026-08-24",
        author="BILLS Sp. z o.o.",
    )
    story = []

    # ----- HEADER (relaxed, design-system style) -----
    # H1 z większą czcionką + więcej odstępu
    H1_BIG = ParagraphStyle("H1_BIG", fontName="VB", fontSize=32, leading=38, textColor=TEXT, alignment=TA_LEFT, spaceAfter=4)
    H1_SUB_BIG = ParagraphStyle("H1_SUB_BIG", fontName="V", fontSize=12, leading=18, textColor=MUTED, alignment=TA_LEFT, spaceAfter=2)
    H1_TAG = ParagraphStyle("H1_TAG", fontName="VI", fontSize=9, leading=12, textColor=ICE_BLUE, alignment=TA_LEFT, spaceBefore=2)

    # Define W early — used in intro layout
    W = PAGE_W - 3 * cm

    # Metadane w jednej linii (badge'ami) - Design System style
    meta_data = [[
        Paragraph("<b>Design System</b>", H1_TAG),
        Paragraph(f"<font color='#888'>·</font>", H1_TAG),
        Paragraph(DATE_TEXT, H1_TAG),
        Paragraph(f"<font color='#888'>·</font>", H1_TAG),
        Paragraph("v3.0", H1_TAG),
        Paragraph(f"<font color='#888'>·</font>", H1_TAG),
        Paragraph("<font color='#0E7490'><b>33 wpisów</b></font>", H1_TAG),
        Paragraph(f"<font color='#888'>·</font>", H1_TAG),
        Paragraph("<font color='#888'>12 CZ + 21 RO</font>", H1_TAG),
    ]]
    meta_tbl = Table(meta_data, colWidths=[W/9] * 9)
    meta_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(Paragraph("Weryfikacja listy firm ze zdjęć", H1_BIG))
    story.append(Paragraph("<i>companies.md — manual OCR transcription -> public-registry cross-check</i>", H1_SUB_BIG))
    story.append(Spacer(1, 4))
    story.append(meta_tbl)
    story.append(Spacer(1, 6))

    # Mały przycisk-akcent: status dokumentu
    story.append(Paragraph(
        "<font color='#0E7490'><b>[*]</b></font> "
        "<font color='#1A1A1A'><b>DOCUMENT STATUS:</b></font> "
        "<font color='#707070'>DRAFT — czeka na akceptację. Wersja po 4-etapowym audycie (gentle search + "
        "deep re-verification + NIP-lookup + cross-country lessons).</font>",
        BODY,
    ))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LINE, spaceBefore=4, spaceAfter=8))

    # ----- PODSUMOWANIE -----
    total = len(ENTRIES)
    cz = [e for e in ENTRIES if e["country"] == "CZ"]
    ro = [e for e in ENTRIES if e["country"] == "RO"]
    by_status = {}
    for e in ENTRIES:
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1

    active = by_status.get("ACTIVE", 0)
    duplikat = by_status.get("DUPLIKAT", 0)
    exclude = by_status.get("EXCLUDE", 0)
    hold = by_status.get("HOLD", 0)

    story.append(Paragraph("Podsumowanie dokumentu", H2))
    story.append(Paragraph(
        f"<b>Łączna liczba wpisów w companies.md: {total}</b> "
        f"(z czego <b>{len(cz)} firm CZ</b> + <b>{len(ro)} firm RO</b>). "
        f"Poniżej rozkład statusów po weryfikacji w publicznych rejestrach:",
        BODY,
    ))
    story.append(Spacer(1, 8))

    story.append(stat_table([
        ("ŁĄCZNIE WERYFIKOWANO", f"{total} firm"),
        ("ACTIVE (nowe leady)", f"{active} firm"),
        ("DUPLIKAT (już w master)", f"{duplikat} firm"),
        ("EXCLUDE (odrzucone)", f"{exclude} firm"),
        ("HOLD (wymaga follow-up)", f"{hold} firm"),
    ], col_w=W / 5))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"<i>Wynik pełnego audytu (4 etapy): <b>{active} nowych leadów</b> do data/_intake/ ({sum(1 for e in ENTRIES if e['status']=='ACTIVE' and e['country']=='CZ')} CZ + {sum(1 for e in ENTRIES if e['status']=='ACTIVE' and e['country']=='RO')} RO), "
        f"<b>{duplikat} duplikatów</b> (już <font color='#0E7490'><b>[ZAMROŻONY]</b></font> w master.csv), "
        f"<b>{exclude} odrzuconych</b> (zła branża / brak śladu / osoba prywatna / firma wykreślona), "
        f"<b>{hold} HOLD</b> (wymaga follow-up). "
        f"<b>Dodatkowo:</b> 1 firma rozpoznana po EXCLUDE w etapie 2 (Eva Machačná -&gt; ACTIVE B4); "
        f"4 firmy z odzyskanym NIP w etapie 3 (KEVARO, Eva Machačná, Jan Zimola, Cotiga Marin-as-admin); "
        f"2 wykryte błędy w CUI/NIP w zdjęciach (COTY SHOP, BLK TRADE MARKET); "
        f"9 firm z wirtualnym adresem w Ostrava (Hosting time s.r.o. — shell pattern).</i>",
        H3,
    ))
    story.append(Spacer(1, 10))

    # Legenda statusów (z ikoną 🧊 dla ZAMROŻONY/FROZEN)
    story.append(Paragraph("Legenda statusów", H3))
    story.append(Spacer(1, 2))
    legend_rows = [
        [Paragraph("<font color='#1B7A3A'><b>ACTIVE</b></font>", BODY_SM),
         Paragraph("Nowy lead — zweryfikowany w rejestrze, aktywny. Rekomendacja: przenieść do data/_intake/", BODY_SM)],
        [Paragraph("<font color='#0E7490'><b>[ZAMROŻONY]</b></font>", BODY_SM),
         Paragraph("Firma już istnieje w master.csv (jako FROZEN/✅). Nie dodawać ponownie — opcjonalnie zaktualizować telefon", BODY_SM)],
        [Paragraph("<font color='#A8201A'><b>EXCLUDE</b></font>", BODY_SM),
         Paragraph("Odrzucony — zła branża / brak śladu / osoba prywatna / firma wykreślona", BODY_SM)],
        [Paragraph("<font color='#A87500'><b>HOLD</b></font>", BODY_SM),
         Paragraph("Wymaga dodatkowej weryfikacji przed podjęciem decyzji (np. adres niezgodny z rejestrem)", BODY_SM)],
    ]
    legend_data = [[Paragraph("<b>Status</b>", HEADER_STYLE),
                     Paragraph("<b>Znaczenie</b>", HEADER_STYLE)]] + legend_rows
    legend_tbl = Table(legend_data, colWidths=[W * 0.16, W * 0.84])
    legend_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, LINE),
    ]))
    story.append(legend_tbl)
    story.append(Spacer(1, 10))

    # ----- TABELA FIRMY CZ -----
    story.append(PageBreak())
    story.append(Paragraph(
        f"Tabela 1 / 2 — Firmy CZ ({len(cz)} wpisów, w tym {sum(1 for e in cz if e['status']=='ACTIVE')} nowych, "
        f"{sum(1 for e in cz if e['status']=='DUPLIKAT')} duplikatów, "
        f"{sum(1 for e in cz if e['status']=='EXCLUDE')} wykluczonych, "
        f"{sum(1 for e in cz if e['status']=='HOLD')} HOLD)",
        H2,
    ))
    story.append(Paragraph(
        "Układ dopasowany do zdjęć faktur (Kod kontrahenta | Nazwa kontrahenta | Adres | NIP | Telefon | Fax) "
        "+ nowe kolumny: <b>Powód wykluczenia</b> i <b>Notatki / Wynik weryfikacji</b>.",
        H3,
    ))
    story.append(Spacer(1, 4))

    cz_rows = []
    for e in cz:
        status_label = {
            "ACTIVE": "ACTIVE",
            "DUPLIKAT": "DUPLIKAT",
            "EXCLUDE": "EXCLUDE",
            "HOLD": "HOLD",
        }[e["status"]]
        bg = STATUS_BG_COLORS.get(e["status"], white)
        cz_rows.append((
            e["country"], e["kod"], e["nazwa"], e["adres"], e["nip"], e["telefon"], e["fax"],
            status_label, e["reason"], e["notes"], bg,
        ))

    headers = ["Kraj", "Kod kontrahenta", "Nazwa kontrahenta", "Adres kontrahenta",
               "NIP", "Telefon", "Fax", "Status", "Powód wykluczenia / decyzji", "Notatki / Wynik weryfikacji"]
    col_widths_cz = [
        W * 0.04,   # Kraj
        W * 0.10,   # Kod
        W * 0.13,   # Nazwa
        W * 0.16,   # Adres
        W * 0.08,   # NIP
        W * 0.08,   # Tel
        W * 0.04,   # Fax
        W * 0.07,   # Status
        W * 0.15,   # Reason
        W * 0.15,   # Notes
    ]
    story.append(data_table(headers, cz_rows, col_widths_cz))

    # ----- TABELA FIRMY RO -----
    story.append(PageBreak())
    story.append(Paragraph(
        f"Tabela 2 / 2 — Firmy RO ({len(ro)} wpisów, w tym {sum(1 for e in ro if e['status']=='ACTIVE')} nowych, "
        f"{sum(1 for e in ro if e['status']=='DUPLIKAT')} duplikatów, "
        f"{sum(1 for e in ro if e['status']=='EXCLUDE')} wykluczonych, "
        f"{sum(1 for e in ro if e['status']=='HOLD')} HOLD)",
        H2,
    ))
    story.append(Paragraph(
        "Układ dopasowany do zdjęć faktur + kolumny decyzyjne. <b>UWAGA:</b> w 3 wpisach wykryto błędy w CUI "
        "(COTY SHOP, BLK TRADE MARKET) — w intake użyć prawidłowych CUI z publicznych rejestrów.",
        H3,
    ))
    story.append(Spacer(1, 4))

    ro_rows = []
    for e in ro:
        status_label = {
            "ACTIVE": "ACTIVE",
            "DUPLIKAT": "DUPLIKAT",
            "EXCLUDE": "EXCLUDE",
            "HOLD": "HOLD",
        }[e["status"]]
        bg = STATUS_BG_COLORS.get(e["status"], white)
        ro_rows.append((
            e["country"], e["kod"], e["nazwa"], e["adres"], e["nip"], e["telefon"], e["fax"],
            status_label, e["reason"], e["notes"], bg,
        ))

    story.append(data_table(headers, ro_rows, col_widths_cz))

    # ----- REKOMENDACJE -----
    story.append(PageBreak())
    story.append(Paragraph("Rekomendacja — co przenieść do data/_intake/", H2))
    story.append(Paragraph(
        f"Po akceptacji Marcelego, poniższe <b>{active} firm</b> ({sum(1 for e in ENTRIES if e['status']=='ACTIVE' and e['country']=='CZ')} CZ + "
        f"{sum(1 for e in ENTRIES if e['status']=='ACTIVE' and e['country']=='RO')} RO) powinny zostać zrzucone do "
        f"<b>data/_intake/CZ/source.csv</b> i <b>data/_intake/RO/source.csv</b> (per pipeline z data/_intake/_README.md):",
        BODY,
    ))
    story.append(Spacer(1, 4))

    active_cz = [e for e in ENTRIES if e["status"] == "ACTIVE" and e["country"] == "CZ"]
    active_ro = [e for e in ENTRIES if e["status"] == "ACTIVE" and e["country"] == "RO"]

    if active_cz:
        story.append(Paragraph("Czechy (CZ) — nowe leady", H3))
        rec_cz_rows = [[
            Paragraph(e["nazwa"], BODY_SM),
            Paragraph(e["nip"], BODY_SM),
            Paragraph(e["reason"].replace("Nowy lead — ", ""), BODY_SM),
        ] for e in active_cz]
        rec_cz_tbl = Table([[Paragraph("<b>Firma</b>", HEADER_STYLE),
                             Paragraph("<b>NIP</b>", HEADER_STYLE),
                             Paragraph("<b>Typ leadu</b>", HEADER_STYLE)]] + rec_cz_rows,
                           colWidths=[W * 0.30, W * 0.15, W * 0.55])
        rec_cz_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ]))
        story.append(rec_cz_tbl)
        story.append(Spacer(1, 8))

    if active_ro:
        story.append(Paragraph("Rumunia (RO) — nowe leady", H3))
        rec_ro_rows = [[
            Paragraph(e["nazwa"], BODY_SM),
            Paragraph(e["nip"], BODY_SM),
            Paragraph(e["reason"].replace("Nowy lead — ", ""), BODY_SM),
        ] for e in active_ro]
        rec_ro_tbl = Table([[Paragraph("<b>Firma</b>", HEADER_STYLE),
                             Paragraph("<b>NIP/CUI</b>", HEADER_STYLE),
                             Paragraph("<b>Typ leadu</b>", HEADER_STYLE)]] + rec_ro_rows,
                           colWidths=[W * 0.30, W * 0.15, W * 0.55])
        rec_ro_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ]))
        story.append(rec_ro_tbl)
        story.append(Spacer(1, 8))

    # NEXT STEPS
    story.append(Paragraph("Następne kroki (po akceptacji)", H2))
    next_steps = [
        f"1. Utworzyć <b>data/_intake/CZ/source.csv</b> z {len(active_cz)} nowymi leadami CZ",
        f"2. Utworzyć <b>data/_intake/RO/source.csv</b> z {len(active_ro)} nowymi leadami RO",
        "3. Auto-gen mapping.md -> normalized.csv (per pipeline)",
        "4. Verify L0 (NIP checksum + ARES/ONRC) -> re-klasyfikacja -> merge do catalog-*-CZ.csv / catalog-*-RO.csv",
        "5. Master regen (tools/billszuka.py compile)",
        "6. Wpis w data/audit-log.md + data/verification/2026-08-24-photo-list.md",
        "7. Opcjonalnie: zaktualizować telefony dla RO-A-004 i RO-B-009 (rozbieżność master vs foto)",
        "8. Kevaro s.r.o. — przed podjęciem decyzji: follow-up (potwierdzić CAEN + rzeczywisty przedmiot działalności)",
    ]
    for s in next_steps:
        story.append(Paragraph(s, BODY))

    # ===== NOWA SEKCJA: Kluczowe odkrycia (faza 2 i 3) =====
    story.append(PageBreak())
    story.append(Paragraph("Kluczowe odkrycia po audycie 4-etapowym", H2))
    story.append(Paragraph(
        "Poniższe odkrycia zmieniają decyzje weryfikacyjne w stosunku do wstępnej analizy.",
        BODY,
    ))
    story.append(Spacer(1, 4))

    # 1. False negative (EXCLUDE -> ACTIVE)
    story.append(Paragraph("1. False negative: Eva Machačná (CZ 44560176) — OSVČ z Kunratice u Cvikova", H3))
    story.append(Paragraph(
        "Pierwsza weryfikacja oznaczyła ją jako EXCLUDE (brak śladu branżowego). "
        "<b>Deep re-verification etapu 2</b> ujawniła: CZ-NACE hlavní = <i>Maloobchod s převahou potravin, nápojů a "
        "tabákových výrobků v nespecializovaných prodejnách</i>. To real B-tier (B4): sklep spożywczy z wyrobami tytoniowymi. "
        "<b>Wniosek:</b> sam brak NIP w zdjęciu to za mało — trzeba sprawdzić CZ-NACE w ARES przed odrzuceniem.",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # 2. Błędy w NIP/CUI
    story.append(Paragraph("2. Błędy w NIP/CUI ze zdjęć (audi OCR)", H3))
    story.append(Paragraph(
        "<b>COTY SHOP INVEST</b> — foto: CUI 48831012 (nie istnieje), prawidłowy: <b>48715727</b> (potwierdzony w 4 źródłach: "
        "demoanaf.ro, datasrl.ro, termene.ro, listafirme.ro). "
        "<b>BLK TRADE MARKET</b> — foto: CUI 40694700 (nie istnieje), prawidłowy: <b>40638971</b> (potwierdzony w 5 źródłach: "
        "termene.ro, listafirme.ro, targetare.ro, eMAG.ro, firmealert.ro). "
        "<b>KEVARO</b> — Sokolská 1605/66 (foto) to historyczny adres firmy 2010–2021; aktualny: náměstí Přátelství 1518/2, Praha. "
        "<b>Jan Zimola (Etabak)</b> — \"CZ 8608082989\" to rodné číslo, nie IČO. Prawidłowe IČO: <b>74215019</b>. "
        "<b>Wniosek:</b> przed EXCLUDE z powodu braku NIP, sprawdź czy to nie PESEL/rodné číslo (CZ) lub numer innego rejestru. "
        "Cross-check 3+ źródłami przed odrzuceniem.",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # 3. Virtual office pattern
    story.append(Paragraph("3. Virtual office / shell pattern (CZ)", H3))
    story.append(Paragraph(
        "Adres <b>Švabinského 1700/4, 702 00 Ostrava</b> (sídlo Hosting time s.r.o.) to virtual office dla "
        "<b>9 polskich firm</b>: ACCOUNT NEW CORPORATE CZ a.s. (28616715), TOKMO GLOBAL s.r.o. (03077161), "
        "Scrap Leader s.r.o. (04124715), CZECH SOLVATO s.r.o. (03051315), JBB Franchise s.r.o. (08945080), "
        "Flex Step s.r.o. (04011111), DESOFT s.r.o. (08204098) i inne. Właścicielka Hosting time: Monika Dąbkowska (Polska). "
        "<b>Wniosek:</b> fakt, że firma ma velkoobchod license (od 24.6.2025) nie oznacza realnej działalności. "
        "Przy wirtualnych adresach (>3 firmy pod 1 adresem + zagraniczny właściciel) stosować <b>multi-source verification</b> "
        "+ sprawdzić obecność strony www / telefonu / pracowników.",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # 4. Rodzinne / powiązane firmy
    story.append(Paragraph("4. Sieci rodzinne i powiązane firmy", H3))
    story.append(Paragraph(
        "<b>COTIGĂ MARIN</b> (Buzău) — administrator 2 firm: COTY SHOP INVEST (CUI 48715727, AKTYWNA, Sector 4) "
        "+ ZASEN TRADE INVEST (CUI 41399635, INAKTYWNA). Telefon <b>+40723019747</b> powtarza się w obu fakturach "
        "(Cotiga Marin + COTY SHOP). <b>Cotiga Monica PFA</b> (CUI 37030493, Sector 3, CAEN 7021 PR) — potencjalne "
        "powiązanie rodzinne (żona?). "
        "<b>CERBU IOANA</b> — administrator GRAND PRODUCT SRL (CUI 16049841, CAEN 4647 mobilier, suspendată). "
        "<b>Wniosek:</b> każda faktura od osoby fizycznej (PFA/osoba prywatna) wymaga sprawdzenia czy osoba "
        "nie jest administratorem firmy z branży. Może być ukrytym B-lead (cross-sell na maszynki).",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # 5. OREA HOTELS — sieć hospitality
    story.append(Paragraph("5. Sieć OREA HOTELS (20+ hoteli w CZ)", H3))
    story.append(Paragraph(
        "OREA HOTELS s.r.o. (CZ 27176657) posiada 20+ hoteli: Praha Pyramida (340 pokoi, 1000+ osób), Brno Congress, "
        "Šumava, Jeseniky, Beskydy, 3x Spa Hotels. Na fakturze prawdopodobnie <b>noclegi z delegacji handlowej</b>. "
        "<b>Wniosek:</b> hotele same nie są leadem tytoniowym, ale <b>delegacje BILLS</b> (hotelarze + przedstawiciele "
        "handlowi BILLS) to potencjalna furtka do grupy <b>delegacji B2B</b> jako nowy kanał (cross-sell maszynek dla "
        "gości biznesowych). Na razie EXCLUDE — ale monitorować pod kątem programu lojalnościowego B2B.",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # 6. Status zmiana DIPA CONCEPT
    story.append(Paragraph("6. Status zmiany w czasie: DIPA CONCEPT SRL", H3))
    story.append(Paragraph(
        "<b>DIPA CONCEPT SRL</b> (CUI 31861043, CAEN 4635 hurt tytoniowy) — firmealert.ro potwierdza zmianę statusu: "
        "Stare: true -> Nowe: false (wykryto 26.02.2026). Obecnie <b>inactivă sau radiată</b>. Ostatni bilant 2015. "
        "<b>Wniosek:</b> nawet CAEN 4635 nie gwarantuje aktywności. Przed dodaniem do intake sprawdzać <b>aktualny status "
        "w ONRC</b> (aktywna / suspendată / inactivă / radiată), nie tylko CAEN.",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # ===== REKOMENDACJA ZMIAN W REGUŁACH (cross-country) =====
    story.append(Paragraph("Rekomendacja zmian w regułach weryfikacji (cross-country lessons)", H2))
    story.append(Paragraph(
        "Po audycie 33 firm ze zdjęć (CZ + RO) i porównaniu z doświadczeniami z 12 krajów "
        "(PL, CZ, SK, RO, BG, HR, SI, LT, LV, EE, FR, MD) wnoszę o następujące aktualizacje metodologii "
        "(<b>data/methodology.md</b> + <b>skills/verify-data/SKILL.md</b>):",
        BODY,
    ))
    story.append(Spacer(1, 4))

    # Rule change 1
    story.append(Paragraph("Reguła #1 — wzmocnić triage EXCLUDE (avoid false negative)", H3))
    story.append(Paragraph(
        "<b>Przed:</b> brak NIP w zdjęciu -> automatycznie EXCLUDE. "
        "<b>Po:</b> brak NIP -> <b>NIE</b> automatycznie EXCLUDE. Sprawdź: (a) ARES dla CZ, ONRC dla RO; "
        "(b) CZ-NACE dla CZ / CAEN dla RO; (c) czy \"brak NIP\" nie jest PESEL/rodné číslo (CZ); "
        "(d) czy firma jest powiązana rodzinne z innym leadem. "
        "<b>Wynik audytu:</b> 1 firma rozpoznana (Eva Machačná).",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # Rule change 2
    story.append(Paragraph("Reguła #2 — multi-source verification dla NIP/CUI", H3))
    story.append(Paragraph(
        "<b>Przed:</b> 1 źródło (np. jedno zapytanie ARES) wystarczy. "
        "<b>Po:</b> minimum 3 niezależne źródła dla każdej firmy. Dla CZ: ARES + rejstrik-firem + termene.ro. "
        "Dla RO: termene.ro + listafirme.ro + datasrl.ro + risco.ro. Cross-check status (aktywna / suspendată / "
        "radiată) w dniu weryfikacji — nie starsze niż 7 dni. "
        "<b>Wynik audytu:</b> 2 wykryte błędy w CUI (COTY SHOP, BLK TRADE).",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # Rule change 3
    story.append(Paragraph("Reguła #3 — wirtualny adres = red flag (CZ)", H3))
    story.append(Paragraph(
        "<b>Nowa reguła:</b> jeśli >3 firmy mają siedzibę pod tym samym adresem + zagraniczny właściciel + brak www -> "
        "oznacz jako <b>shell pattern</b>. Nie dodawaj do ACTIVE nawet jeśli firma ma velkoobchod license. "
        "Wymaga bezpośredniej rozmowy z właścicielem (LinkedIn / telefon). "
        "<b>Wynik audytu:</b> 9 firm w Ostrava-Moravská pod 1 adresem = virtual office pattern.",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # Rule change 4
    story.append(Paragraph("Reguła #4 — sprawdzać administratorów (cross-sell)", H3))
    story.append(Paragraph(
        "<b>Nowa reguła:</b> dla każdej faktury od osoby fizycznej (PFA/osoba prywatna) sprawdź w datasrlro kto jest "
        "administratorem — może to administrator firmy z branży, który wystawia fakturę prywatnie. Traktuj jako "
        "<b>soft duplicate</b> istniejącego leada. "
        "<b>Wynik audytu:</b> Cotiga Marin (osoba fizyczna) = admin COTY SHOP INVEST (lead RO-A-009).",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # Rule change 5
    story.append(Paragraph("Reguła #5 — CAEN/CZ-NACE nie = aktywność", H3))
    story.append(Paragraph(
        "<b>Przed:</b> CAEN 4635 (hurt tytoniowy) = lead. "
        "<b>Po:</b> CAEN 4635 + status ONRC/ARES = aktywna -> lead. "
        "Status <b>suspendată / inactivă / radiată</b> = EXCLUDE (nawet przy dobrym CAEN). "
        "Sprawdzać ostatni dostępny bilans + datę statusu. "
        "<b>Wynik audytu:</b> DIPA CONCEPT (CAEN 4635, INACTIVĂ od 26.02.2026) — wykreślona, nie lead.",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # Rule change 6
    story.append(Paragraph("Reguła #6 — adres niezgodny = HOLD (nie EXCLUDE)", H3))
    story.append(Paragraph(
        "<b>Przed:</b> adres niezgodny z rejestrem -> EXCLUDE. "
        "<b>Po:</b> adres niezgodny -> <b>HOLD</b> (wymaga follow-up). Może to (a) historyczny adres, (b) błąd OCR, "
        "(c) zmiana siedziby. "
        "<b>Wynik audytu:</b> Kevaro s.r.o. — Sokolská 1605/66 (foto) to historyczny adres 2010–2021; "
        "aktualny adres náměstí Přátelství 1518/2.",
        BODY,
    ))
    story.append(Spacer(1, 6))

    # Rule change 7
    story.append(Paragraph("Reguła #7 — reklasyfikować \"hotelarstwo\" na \"delegacje B2B\"", H3))
    story.append(Paragraph(
        "<b>Nowa kategoria B:</b> B10 — Hotele sieciowe (>5 obiektów) — kanał cross-sell na maszynki dla gości "
        "biznesowych (PowerMatic jako gift w programie lojalnościowym B2B). Inna kalkulacja wolumenu niż typowy "
        "B4 akcesoria. <b>NIE</b> w ICP standardowym, ale warto monitorować pod kątem programu partnerskiego. "
        "<b>Wynik audytu:</b> OREA HOTELS = 20+ obiektów.",
        BODY,
    ))
    story.append(Spacer(1, 8))

    # Porównanie z innymi krajami
    story.append(Paragraph("Jak nasze wnioski mają się do doświadczeń w innych krajach", H2))
    story.append(Paragraph(
        "Porównanie z katalogami 12 krajów w projekcie BILLSzuka (master.csv + per-country catalogs):",
        BODY,
    ))
    story.append(Spacer(1, 4))

    comparison_data = [
        ["Zasada / Lekcja", "PL/CZ/SK (Tier 1)", "RO/BG/HR/SI (Tier 2)", "LT/LV/EE (Tier 3)", "FR (Tier 1 spec.)"],
        ["Źródła dla NIP/CUI",
         "ARES + rejstrik-firem (CZ); KRS API + CEIDG (PL); FinStat (SK)",
         "termene.ro + listafirme.ro + datasrl.ro (RO); Търговски регистър (BG); Sudski registar (HR); AJPES (SI)",
         "Registrų Centras (LT); Lursoft (LV); e-Äriregister (EE)",
         "api.gouv.fr SIREN/SIRET (FR) — każdy oddział osobny wpis"],
        ["Multi-source verification",
         "3+ źródła per firma (ARES, rejstrik, VIES)",
         "3+ źródła + sprawdzenie ACtionan / Inactiv w ONRC",
         "JAR + Rekvizitai / UR / ariregister",
         "SIREN + Pappers + societe.com"],
        ["Virtual office pattern",
         "Rzadki w CZ, częsty w SK (Bratysława virtual offices dla CEE firm)",
         "Częsty w RO (Szoseaua X adresy wielu firm), sporadyczny w BG",
         "Bardzo rzadki w LT/LV/EE",
         "Częsty w Paryżu (adresy coworkingowe)"],
        ["HOLD vs EXCLUDE",
         "HOLD = adres niezgodny; EXCLUDE = brak firmy",
         "Tak samo; + HOLD = firma w likwidacji",
         "HOLD = brak danych finansowych",
         "HOLD = brak ICE/numéro TVA"],
        ["OSVČ z branżą tytoniową",
         "Eva Machačná (CZ) — 1 przypadek, warte monitoringu",
         "Sprawdzać CZ-NACE = 'tabákových výrobků'",
         "Nieistotne (małe kraje)",
         "Nieistotne (FR ma buraliste system)"],
        ["Cat. A2 Hawk (tylko Hawk, bez PM)",
         "Mało, większość A = multi-brand z PM",
         "Częstsze w RO (DIPA Concept, Sibis Concept — mają też Hawk)",
         "Rzadkie w klimatach bałtyckich",
         "Mistersmoke / TDN (FR) — premium Hawk"],
        ["Cat. B8 hurtownie tytoniowe",
         "PEAL, CTC, SHANTI, ATC, TTI (CZ)",
         "JPB, TTI, Golden Tip, DVD Master (RO); Discum, Lampa (BG)",
         "Sanitex (LT/LV/EE — cross-country)",
         "Logista (FR — monopolista N°01)"],
    ]

    cmp_headers = ["Zasada / Lekcja", "PL/CZ/SK", "RO/BG/HR/SI", "LT/LV/EE", "FR"]
    cmp_rows = [[Paragraph(c, BODY_SM) for c in row] for row in comparison_data]
    cmp_tbl = Table([cmp_headers] + cmp_rows, colWidths=[W * 0.20, W * 0.20, W * 0.20, W * 0.20, W * 0.20])
    cmp_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 0), (-1, 0), "VB"),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#F9F9F9")]),
    ]))
    story.append(cmp_tbl)
    story.append(Spacer(1, 8))

    # Konkluzja rekomendacji
    story.append(Paragraph("Konkluzja i rekomendacja finalna", H2))
    story.append(Paragraph(
        "<b>Kluczowy wniosek z audytu 4-etapowego:</b> nasza obecna metodyka jest zbyt liberalna w odrzucaniu — "
        "<b>Eva Machačná</b> pokazała, że brak NIP w zdjęciu to za mało do EXCLUDE. "
        "Najważniejsze zmiany:",
        BODY,
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>1.</b> NIE EXCLUDE na podstawie samego braku NIP — zawsze sprawdzić ARES/ONRC + CZ-NACE/CAEN. "
        "<b>2.</b> Cross-check NIP/CUI w min. 3 źródłach (szczególnie CZ + SK virtual offices). "
        "<b>3.</b> Wirtualny adres (>3 firmy pod 1 adresem + zagraniczny właściciel) = red flag -> HOLD, nie ACTIVE. "
        "<b>4.</b> Status ACTIVE w ONRC/ARES sprawdzać w dniu weryfikacji — nie starsze niż 7 dni. "
        "<b>5.</b> Faktury od osób fizycznych (PFA/osoby prywatne) sprawdzać przez datasrl.ro/administrator. "
        "<b>6.</b> Adres niezgodny = HOLD, nie EXCLUDE (może być historyczny adres / błąd OCR / zmiana siedziby). "
        "<b>7.</b> Nowa kategoria B10 \"Hotele sieciowe (>5 obiektów)\" dla cross-sell na delegacje B2B. "
        "<b>8.</b> Aktualizować <b>data/methodology.md</b> (sekcja \"Słabe punkty\") + "
        "<b>skills/verify-data/SKILL.md</b> (krok 1: lista zmian).",
        BODY,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Rekomendacja dla Marcelego:</b> zaakceptować wszystkie 8 reguł powyżej i wdrożyć je w "
        "<b>data/methodology.md</b> oraz <b>skills/verify-data/SKILL.md</b> przy następnej aktualizacji "
        "(planowane po zamknięciu etapu intake 12 nowych leadów do _intake/). "
        "Dodatkowo: <b>utworzyć data/verification/_patterns.md</b> z listą wirtualnych adresów do monitorowania "
        "(np. Švabinského 1700/4 Ostrava), żeby przyszłe audyty nie musiały ich ponownie odkrywać.",
        BODY,
    ))

    # Footer info
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LINE, spaceBefore=4, spaceAfter=4))
    story.append(Paragraph(
        f"<i>Dokument wygenerowany {DATE_TEXT} · źródło: data/verification/companies.md · "
        f"audyt: data/verification/2026-08-24-photo-list-md, 2026-08-24-photo-list-deep-audit.md · "
        f"autor weryfikacji: Mavis (BILLS AI agent) · Decyzja: czeka na akceptację Marcelego.</i>",
        H3,
    ))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    size = Path(out_pdf).stat().st_size
    print(f"✅ PDF wygenerowany: {out_pdf} ({size // 1024}KB, {size} bytes)")


def build_md():
    """Mirror PDF w MD dla archiwum."""
    md = []
    md.append("# Weryfikacja listy firm ze zdjęć (companies.md)")
    md.append("")
    md.append(f"> **Data:** {DATE_TEXT}")
    md.append(f"> **Źródło:** `data/verification/companies.md`")
    md.append(f"> **Metoda:** ARES + rejstrik-firem + termene.ro + listafirme.ro + risco.ro (gentle, public sources only)")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Podsumowanie dokumentu")
    md.append("")
    total = len(ENTRIES)
    cz = [e for e in ENTRIES if e["country"] == "CZ"]
    ro = [e for e in ENTRIES if e["country"] == "RO"]
    by_status = {}
    for e in ENTRIES:
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1
    md.append(f"Łączna liczba wpisów: **{total}** ({len(cz)} CZ + {len(ro)} RO)")
    md.append("")
    md.append("| Status | Liczba |")
    md.append("|:---|:---:|")
    md.append(f"| ACTIVE (nowe leady) | {by_status.get('ACTIVE', 0)} |")
    md.append(f"| DUPLIKAT (już w master) | {by_status.get('DUPLIKAT', 0)} |")
    md.append(f"| EXCLUDE (odrzucone) | {by_status.get('EXCLUDE', 0)} |")
    md.append(f"| HOLD (wymaga follow-up) | {by_status.get('HOLD', 0)} |")
    md.append("")
    md.append("---")
    md.append("")

    for region_label, region_entries in [("🇨🇿 Czechy", cz), ("🇷🇴 Rumunia", ro)]:
        md.append(f"## {region_label}")
        md.append("")
        md.append("| Kod | Nazwa | Adres | NIP | Telefon | Status | Powód wykluczenia | Notatki |")
        md.append("|---|---|---|---|---|---|---|---|")
        for e in region_entries:
            tel = e["telefon"] or "—"
            nip = e["nip"] if e["nip"] != "(brak)" else "—"
            md.append(f"| {e['kod']} | {e['nazwa']} | {e['adres']} | {nip} | {tel} | **{e['status']}** | {e['reason']} | {e['notes']} |")
        md.append("")
        md.append("---")
        md.append("")

    md.append("## Rekomendacja — co przenieść do data/_intake/")
    md.append("")
    active = [e for e in ENTRIES if e["status"] == "ACTIVE"]
    md.append(f"Po akceptacji Marcelego, {len(active)} firm powinno zostać zrzuconych do data/_intake/:")
    md.append("")
    for e in active:
        flag = "[CZ]" if e["country"] == "CZ" else "[RO]"
        md.append(f"- {flag} **{e['nazwa']}** ({e['nip']}) — {e['reason']}")
    md.append("")

    Path(OUT_MD).write_text("\n".join(md), encoding="utf-8")
    print(f"✅ MD wygenerowany: {OUT_MD}")


if __name__ == "__main__":
    build_pdf()
    build_md()
