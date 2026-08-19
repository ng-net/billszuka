"""tools/pdf_gen_instrukcja.py — A4 printable INSTRUKCJA.pdf for sales team v1.2.

Reads data/INSTRUKCJA.md, renders to PDF with:
  - minimal margins (1.0cm)
  - Verdana font (Polish-safe, full Latin Extended coverage verified)
  - 13-section layout
  - intro page with 12-country PDF inventory + stats
  - phrases section in 12 languages with Polish translations
  - compact layout (no gaps), KeepTogether where needed
  - tables, callouts, A4 portrait

Usage: python3 tools/pdf_gen_instrukcja.py
Output: data/INSTRUKCJA.pdf
"""
import re
import sys
import csv
import json
import os
from collections import Counter
from pathlib import Path

from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
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
    KeepTogether,
)

# --- Polish-safe font registration (Verdana) ---
pdfmetrics.registerFont(TTFont("V", "/System/Library/Fonts/Supplemental/Verdana.ttf"))
pdfmetrics.registerFont(TTFont("VB", "/System/Library/Fonts/Supplemental/Verdana Bold.ttf"))
pdfmetrics.registerFont(TTFont("VI", "/System/Library/Fonts/Supplemental/Verdana Italic.ttf"))
pdfmetrics.registerFont(TTFont("VBI", "/System/Library/Fonts/Supplemental/Verdana Bold Italic.ttf"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PHRASES_PATH = Path("/tmp/phrases_v3.json")

# --- Style palette ---
COLOR_PRIMARY = HexColor("#1a4d7a")
COLOR_ACCENT = HexColor("#c19a3e")
COLOR_LIGHT_BG = HexColor("#f0f4f8")
COLOR_HEADER_BG = HexColor("#1a4d7a")
COLOR_HEADER_TEXT = white
COLOR_ZEBRA = HexColor("#fafbfc")
COLOR_BORDER = HexColor("#d0d7de")
COLOR_GREY = HexColor("#6a737d")

# --- Minimal margins: 1.0cm all around ---
MARGIN = 0.8 * cm

# --- Styles ---
styles = {
    "title_main": ParagraphStyle(
        "title_main", fontName="VB", fontSize=24, leading=28,
        textColor=COLOR_PRIMARY, alignment=TA_CENTER, spaceAfter=4,
    ),
    "title_sub": ParagraphStyle(
        "title_sub", fontName="V", fontSize=13, leading=16,
        textColor=COLOR_GREY, alignment=TA_CENTER, spaceAfter=6,
    ),
    "h1": ParagraphStyle(
        "h1", fontName="VB", fontSize=14, leading=17,
        textColor=COLOR_PRIMARY, spaceBefore=6, spaceAfter=2,
    ),
    "h2": ParagraphStyle(
        "h2", fontName="VB", fontSize=10, leading=13,
        textColor=COLOR_PRIMARY, spaceBefore=3, spaceAfter=1,
    ),
    "h3": ParagraphStyle(
        "h3", fontName="VB", fontSize=9, leading=11,
        textColor=COLOR_ACCENT, spaceBefore=1, spaceAfter=1,
    ),
    "body": ParagraphStyle(
        "body", fontName="V", fontSize=8.5, leading=11,
        textColor=black, spaceAfter=2, alignment=TA_LEFT,
    ),
    "body_tight": ParagraphStyle(
        "body_tight", fontName="V", fontSize=8, leading=10,
        textColor=black, spaceAfter=1, alignment=TA_LEFT,
    ),
    "small": ParagraphStyle(
        "small", fontName="V", fontSize=7, leading=9,
        textColor=COLOR_GREY, alignment=TA_LEFT,
    ),
    "small_italic": ParagraphStyle(
        "small_italic", fontName="VI", fontSize=6.5, leading=8.5,
        textColor=COLOR_GREY, alignment=TA_LEFT,
    ),
    "phrase_main": ParagraphStyle(
        "phrase_main", fontName="V", fontSize=7.5, leading=9.5,
        textColor=black,
    ),
    "phrase_pl": ParagraphStyle(
        "phrase_pl", fontName="VI", fontSize=6.5, leading=8,
        textColor=COLOR_GREY, leftIndent=6,
    ),
    "code": ParagraphStyle(
        "code", fontName="VI", fontSize=7.5, leading=9.5,
        textColor=COLOR_PRIMARY, leftIndent=6,
    ),
    "callout": ParagraphStyle(
        "callout", fontName="VI", fontSize=8, leading=10.5,
        textColor=COLOR_PRIMARY, leftIndent=8, rightIndent=8,
        spaceBefore=1, spaceAfter=1,
    ),
    "bullet": ParagraphStyle(
        "bullet", fontName="V", fontSize=8, leading=10.5,
        leftIndent=12, bulletIndent=4, spaceAfter=1,
    ),
    "intro_big": ParagraphStyle(
        "intro_big", fontName="VB", fontSize=13, leading=17,
        textColor=COLOR_PRIMARY, alignment=TA_CENTER, spaceAfter=4,
    ),
}


def hr():
    return HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER,
                      spaceBefore=1, spaceAfter=2)


def callout_box(text, color=COLOR_LIGHT_BG, border=COLOR_PRIMARY):
    """Render text in a callout box."""
    tbl = Table([[Paragraph(text, styles["callout"])]], colWidths=[17.5 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("BOX", (0, 0), (-1, -1), 0.5, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tbl


def country_stats():
    """Get PDF page counts and lead counts per country."""
    try:
        from pypdf import PdfReader
    except ImportError:
        PdfReader = None

    countries = [
        ("Polska", "PL"), ("Czechy", "CZ"), ("Słowacja", "SK"),
        ("Rumunia", "RO"), ("Bułgaria", "BG"), ("Chorwacja", "HR"),
        ("Słowenia", "SI"), ("Litwa", "LT"), ("Łotwa", "LV"),
        ("Estonia", "EE"), ("Francja", "FR"), ("Mołdawia", "MD"),
    ]
    rows = []
    for cname, iso in countries:
        pdf_path = DATA_DIR / cname / f"PDF-{iso}.pdf"
        pages = "—"
        if pdf_path.exists() and PdfReader:
            try:
                pages = len(PdfReader(str(pdf_path)).pages)
            except Exception:
                pages = "?"
        a_total = b_total = 0
        a_break = Counter()
        b_break = Counter()
        for cat in ("A", "B"):
            p = DATA_DIR / cname / f"catalog-{cat}-{iso}.csv"
            if p.exists():
                with p.open("r", encoding="utf-8") as f:
                    for r in csv.DictReader(f):
                        k = r.get("kategoria", "?").strip() or "?"
                        (a_break if cat == "A" else b_break)[k] += 1
                        if cat == "A":
                            a_total += 1
                        else:
                            b_total += 1
        rows.append({
            "country": cname, "iso": iso, "pages": pages,
            "a_total": a_total, "b_total": b_total,
            "a_break": a_break, "b_break": b_break,
        })
    return rows


# Country labels with ISO codes (no flag emojis — Verdana doesn't render them)
COUNTRY_LABEL = {
    "PL": "[PL] Polska", "CZ": "[CZ] Czechy", "SK": "[SK] Słowacja",
    "RO": "[RO] Rumunia", "BG": "[BG] Bułgaria", "HR": "[HR] Chorwacja",
    "SI": "[SI] Słowenia", "LT": "[LT] Litwa", "LV": "[LV] Łotwa",
    "EE": "[EE] Estonia", "FR": "[FR] Francja", "MD": "[MD] Mołdawia",
}


# ============================================================
# Build PDF
# ============================================================

def build_intro_title(story):
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("BILLS Sp. z o.o.", styles["title_main"]))
    story.append(Paragraph("Ostrzeszów · Dystrybutor PowerMatic & Hawk", styles["title_sub"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(HRFlowable(width="60%", thickness=2, color=COLOR_ACCENT,
                             hAlign="CENTER", spaceBefore=2, spaceAfter=4))
    story.append(Paragraph("BILLSzuka", styles["intro_big"]))
    story.append(Paragraph("Instrukcja dla Działu Sprzedaży", styles["h1"]))
    story.append(Paragraph("<i>Wersja 1.4 · 19 sierpnia 2026</i>", styles["small"]))
    story.append(Paragraph("<i>Właściciel: Marceli · BILLS Sp. z o.o.</i>", styles["small"]))
    story.append(Spacer(1, 0.3 * cm))

    stats_data = [
        ["Parametr", "Wartość"],
        ["Kraje", "12 (PL, CZ, SK, RO, BG, HR, SI, LT, LV, EE, FR, MD)"],
        ["Łącznie firm", "393 (105 katalog A + 288 katalog B)"],
        ["Status FROZEN", "374 (95,2%)"],
        ["Status DO-WERYFIKACJI", "19 (4,8%)"],
        ["Pliki PDF per kraj", "12 x data/{Kraj}/PDF-{ISO}.pdf (107 stron łącznie)"],
        ["Pliki SŁOWNIK per kraj", "12 x data/{Kraj}/SŁOWNIK-{ISO}.md"],
        ["Źródła danych", "100% publiczne (KRS, ARES, VIES, marketplace, OSINT)"],
        ["Cel biznesowy", "3–5 podpisanych umów dystrybucyjnych / 12 mies."],
    ]
    tbl = Table(stats_data, colWidths=[5 * cm, 12.5 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_HEADER_TEXT),
        ("FONTNAME", (0, 0), (-1, 0), "VB"),
        ("FONTNAME", (0, 1), (0, -1), "VB"),
        ("FONTNAME", (1, 1), (1, -1), "V"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.25, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    for i in range(1, len(stats_data)):
        if i % 2 == 0:
            tbl.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), COLOR_ZEBRA)]))
    story.append(tbl)
    story.append(PageBreak())


def build_inventory_page(story, country_rows):
    story.append(Paragraph("0. Katalog 12 dokumentów PDF per kraj", styles["h1"]))
    story.append(Paragraph(
        "Dla każdego z 12 krajów wygenerowaliśmy osobny katalog PDF (A4, layout v9). "
        "Poniżej pełen wykaz ze statystykami: ile stron, ile leadów w każdej kategorii A1–A6 i B1–B9.",
        styles["body"]))
    story.append(Spacer(1, 0.1 * cm))

    total_pages = total_a = total_b = 0
    data = [["#", "Kraj", "PDF", "Str.", "Σ", "Katalog A", "Katalog B"]]
    for i, r in enumerate(country_rows, 1):
        a_str = ", ".join(f"{k}:{v}" for k, v in sorted(r["a_break"].items())) or "—"
        b_str = ", ".join(f"{k}:{v}" for k, v in sorted(r["b_break"].items())) or "—"
        total = r["a_total"] + r["b_total"]
        data.append([
            str(i), COUNTRY_LABEL[r["iso"]], f"PDF-{r['iso']}.pdf",
            str(r["pages"]), str(total), a_str, b_str,
        ])
        if isinstance(r["pages"], int):
            total_pages += r["pages"]
        total_a += r["a_total"]
        total_b += r["b_total"]
    data.append([
        "", "Σ 12 krajów", "", str(total_pages), str(total_a + total_b),
        f"{total_a}", f"{total_b}",
    ])

    tbl = Table(data, colWidths=[0.7 * cm, 2.6 * cm, 2.2 * cm, 0.7 * cm, 0.7 * cm, 4.5 * cm, 5.6 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_HEADER_TEXT),
        ("FONTNAME", (0, 0), (-1, 0), "VB"),
        ("FONTNAME", (0, 1), (-1, -2), "V"),
        ("FONTNAME", (0, -1), (-1, -1), "VB"),
        ("BACKGROUND", (0, -1), (-1, -1), COLOR_LIGHT_BG),
        ("FONTSIZE", (0, 0), (-1, -1), 6.5),
        ("FONTSIZE", (0, -1), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (4, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]))
    for i in range(1, len(data) - 1):
        if i % 2 == 0:
            tbl.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), COLOR_ZEBRA)]))
    story.append(tbl)
    story.append(Spacer(1, 0.15 * cm))

    story.append(callout_box(
        "<b>Layout PDF per kraj (locked v9):</b> strona 1 = tytuł + Potencjał rynkowy + Statystyki + "
        "5 insightów · strona 2+ = Podział firm + 3 legendy · ostatnia strona = stopka. "
        "Font: Verdana, 1.5 cm marginesy, A4 portrait."
    ))

    story.append(Paragraph("Który PDF czytać pierwszy — priorytet per typ klienta", styles["h2"]))
    data2 = [
        ["Jeśli Twój klient jest…", "Zacznij od", "Strony z potencjałem"],
        ["Polski hurtownik tytoniowy", "PDF-PL.pdf", "str. 1 (PL: 26 mld)"],
        ["Bałtycki dystrybutor FMCG", "LT+LV+EE PDF", "1 + §6 (Sanitex)"],
        ["Czeski gracz tytoniowy", "PDF-CZ.pdf", "str. 1 (CZ: 55 mld)"],
        ["Bułgarski producent OEM", "PDF-BG.pdf", "str. 1 (BG: Płowdiw)"],
        ["Francuski buralista", "PDF-FR.pdf", "str. 1 (FR: 23k)"],
    ]
    tbl2 = Table(data2, colWidths=[5.5 * cm, 4.5 * cm, 7.5 * cm])
    tbl2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_HEADER_TEXT),
        ("FONTNAME", (0, 0), (-1, 0), "VB"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.25, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(tbl2)
    story.append(Spacer(1, 0.4 * cm))


# --- Compact section helpers ---

def section_h1(story, text, num=None, keep_first_lines=0):
    if num is not None:
        title = f"{num}. {text}"
    else:
        title = text
    p = Paragraph(title, styles["h1"])
    if keep_first_lines > 0:
        return [p]
    story.append(p)


def para(story, text, style="body"):
    story.append(Paragraph(text, styles[style]))


def bullet(story, text):
    story.append(Paragraph(f"• {text}", styles["bullet"]))


def callout(story, text, color=None):
    story.append(callout_box(text, color or COLOR_LIGHT_BG))
    story.append(Spacer(1, 0.05 * cm))


def table(story, data, col_widths, header=True, zebra=True, fontsize=7,
          row_heights=None, header_bg=COLOR_HEADER_BG):
    tbl = Table(data, colWidths=col_widths, repeatRows=1 if header else 0,
                rowHeights=row_heights)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "V"),
        ("FONTSIZE", (0, 0), (-1, -1), fontsize),
        ("GRID", (0, 0), (-1, -1), 0.25, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_HEADER_TEXT),
            ("FONTNAME", (0, 0), (-1, 0), "VB"),
        ]
    tbl.setStyle(TableStyle(style))
    if zebra and header:
        for i in range(1, len(data)):
            if i % 2 == 0:
                tbl.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), COLOR_ZEBRA)]))
    story.append(tbl)
    story.append(Spacer(1, 0.05 * cm))


def build_main(story):
    # === TOC ===
    section_h1(story, "Spis treści", "")
    toc_data = [
        ["Sekcja", "Temat"],
        ["0", "Strona tytułowa + Katalog 12 dokumentów PDF per kraj + statystyki"],
        ["1", "Co to jest BILLSzuka"],
        ["2", "Skąd wzięły się te dane — 11 poziomów wyszukiwania"],
        ["3", "Podział firm na dwa katalogi (A1–A6, B1–B9)"],
        ["4", "Scoring — Tier, Wolumen, Flagi"],
        ["5", "Weryfikacja FROZEN + defense in depth"],
        ["6", "Potencjał rynkowy per kraj (12 krajów)"],
        ["7", "TOP firmy per kraj (20 Big Fish)"],
        ["8", "Słownik fraz — „nabijarka do tytoniu\" w 12 językach (z tłumaczeniem PL)"],
        ["9", "Co zadziałało / co nie zadziałało"],
        ["10", "Problemy ze źródłami danych"],
        ["11", "Rekomendowane API i płatne serwisy z cenami"],
        ["12", "Jak korzystać z bazy (3 kroki dla handlowca)"],
        ["13", "Status projektu i plan Q3–Q4 2026"],
    ]
    table(story, toc_data, [1.5 * cm, 16 * cm], fontsize=7)
    story.append(Spacer(1, 0.3 * cm))

    # === 1 ===
    section_h1(story, "Co to jest BILLSzuka", 1)
    para(story,
         "<b>BILLSzuka</b> to wewnętrzna baza leadów dystrybucyjnych dla BILLS Sp. z o.o. (Ostrzeszów) — "
         "autoryzowanego dystrybutora maszynek <b>PowerMatic</b> i <b>Hawk</b> w Polsce i Europie "
         "Środkowo-Wschodniej. Baza powstała w sierpniu 2026 r. w jeden cykl badawczy (8 sesji) "
         "z publicznie dostępnych danych — bez list od klienta.")
    table(story, [
        ["Parametr", "Wartość"],
        ["Kraje", "12 (PL, CZ, SK, RO, BG, HR, SI, LT, LV, EE, FR, MD)"],
        ["Łącznie firm", "393"],
        ["Katalog A (maszynki)", "105 firm"],
        ["Katalog B (branża)", "288 firm"],
        ["Status FROZEN", "374 (95,2%)"],
        ["Status DO-WERYFIKACJI", "19 (4,8%)"],
        ["Źródła danych", "100% publiczne (rejestry, KRS/CEIDG/ARES/VIES, marketplace, OSINT)"],
        ["Pliki PDF per kraj", "12 x data/{Kraj}/PDF-{ISO}.pdf (107 stron łącznie)"],
        ["Pliki SŁOWNIK per kraj", "12 x data/{Kraj}/SŁOWNIK-{ISO}.md"],
    ], [5 * cm, 12.5 * cm], fontsize=7)
    callout(story,
        "<b>Cel biznesowy:</b> 3–5 podpisanych umów dystrybucyjnych na PowerMatic / Hawk w ciągu 12 miesięcy. "
        "Każdy rekord w master.csv jest kandydatem, który przeszedł weryfikację minimum jednego oficjalnego rejestru.")
    story.append(Spacer(1, 0.3 * cm))

    # === 2 ===
    section_h1(story, "Skąd wzięły się te dane — 11 poziomów wyszukiwania", 2)
    para(story, "Każdy lead przeszedł przez kombinację poniższych metod. Nazwy i opisy są kanoniczne — pełne w methodology.md.")
    table(story, [
        ["Poziom", "Co to", "Typowy koszt", "Status"],
        ["L0", "Walidacja NIP/KRS (checksum mod 11 + name match)", "darmowy", "[OK] wdrożone"],
        ["L1", "Google / DuckDuckGo / Brave + site:, intitle:", "darmowy", "[OK] używane"],
        ["L2", "Allegro REST API, eBay Finding, Heureka (CZ)", "darmowy / limit", "[!] Allegro OK, OLX/Ceneo brak API"],
        ["L3", "Google Maps Places API + rejestry państwowe (PKD)", "$32/1000 req", "[OK] używane"],
        ["L4", "Biała Lista VAT, BDO, KAS Rejestr Pośredników Tytoniowych", "darmowy", "[OK] PL"],
        ["L5", "DNS / WHOIS / Certificate Transparency (crt.sh)", "darmowy", "[!] WHOIS ukryty po 2018"],
        ["L6", "InterTabac, World Vape Show, Eurocis, Tobacco Plus Expo", "darmowy", "[X] tylko manual"],
        ["L7", "Social media (FB, IG, TikTok, YouTube komentarze)", "darmowy / Apify $5", "[!] częściowo"],
        ["L8", "Katalogi firm (Aleo, Panorama, Kompass, nipgo.pl, Veritor)", "freemium / paid", "[OK] nipgo.pl, Veritor"],
        ["L9", "LLM (DeepSeek, Gemini, Claude) + multi-LLM consensus", "OpenRouter paid", "[OK] używane"],
        ["L10", "EUIPO trademark search", "darmowy", "[X] nie wdrożone"],
        ["L11", "BZP / TED zamówienia publiczne", "darmowy", "[X] nie wdrożone"],
    ], [1.2 * cm, 8.5 * cm, 3.5 * cm, 4.3 * cm], fontsize=7)
    callout(story,
        "<b>W skrócie:</b> działa to, co jest darmowe i oficjalne (KRS, ARES, VIES, e-Äriregister). "
        "Nie działa to, co wymaga SPA scraping (LT, LV, BG) lub płatnej subskrypcji (Veritor, ENTIA).")
    story.append(Spacer(1, 0.3 * cm))

    # === 3 ===
    section_h1(story, "Podział firm na dwa katalogi", 3)
    section_h2_marker = Paragraph("3.1 Katalog A — firmy, które mają lub mogą mieć maszynki (105 firm)", styles["h2"])
    story.append(section_h2_marker)
    table(story, [
        ["Kod", "Kategoria", "Znaczenie dla BILLS"],
        ["A1", "Tylko PowerMatic", "Sub-dystrybutorzy / autoryzowani resellerzy"],
        ["A2", "Tylko Hawk", "Potencjalny kanał dla Hawk"],
        ["A3", "PowerMatic + Hawk", "Najcenniejsi — znają oba produkty"],
        ["A4", "Multi-brand z PM/Hawk", "Resellerzy wielu marek"],
        ["A5", "Własna marka / OEM z Chin", "Konkurencja cenowa (zostaje w katalogu)"],
        ["A6", "Multi-brand bez PM/Hawk", "Kandydaci do pozyskania"],
    ], [1.2 * cm, 5.5 * cm, 10.8 * cm], fontsize=7)
    story.append(Paragraph("3.2 Katalog B — branża tytoniowa bez maszynek (288 firm)", styles["h2"]))
    para(story, "Numer to <b>powinowactwo z nabijarkami</b> w skali 1–5: 5 = kupi prawie na pewno, 1 = marginalny overlap.")
    table(story, [
        ["Kod", "Specjalizacja", "Pow.", "Uzasadnienie"],
        ["B1", "Tytoń liście / RYO", "5", "Klient kupuje surowiec -> maszynka = upsell"],
        ["B2", "Bibułki papierosowe", "5", "Top-of-mind palaczy skręcających"],
        ["B3", "Filtry / gilzy", "5", "Klient już w kategorii"],
        ["B4", "Akcesoria (zapalniczki, fajki)", "3", "Te same sklepy, inna demografia"],
        ["B5", "Shisha / hookah", "2", "Shared retail, różni klienci"],
        ["B6", "E-papierosy / vape", "2", "Shared channel, rozbieżne regulacje"],
        ["B7", "Snus / pouches", "2", "Rosnący segment, klient raczej nie skręca"],
        ["B8", "Hurtownie tytoniowe", "5", "Najwyższy priorytet — mają wszystko poza maszynkami"],
        ["B9", "CBD / susz", "4", "Wysoki overlap kliencki"],
    ], [1 * cm, 5 * cm, 0.8 * cm, 10.7 * cm], fontsize=7)
    callout(story,
        "<b>Najważniejsza reguła:</b> Kryterium to <b>overlap kliencki, nie kanałowy</b>. B8 (hurtownia) "
        "waży więcej niż B6 (sieć vape), bo hurtownia ma decydenta i 5 000 punktów dystrybucji.")
    story.append(Spacer(1, 0.3 * cm))

    # === 4 ===
    section_h1(story, "Scoring — jak czytać flagi", 4)
    para(story, "Każda firma ma zestaw flag. Dla działu sprzedaży najważniejsze są trzy:")
    story.append(Paragraph("4.1 TIER — typ relacji handlowej", styles["h2"]))
    table(story, [
        ["Tier", "Co to znaczy", "Jak rozpoznać", "Skala PL"],
        ["wyłączność", "Jedyny autoryz. dystrybutor", "„Jedyny autoryzowany\"", "1–2"],
        ["autoryzowany", "Partner z umową, nie wyłączny", "„Autoryzowany sprzedawca\"", "5–15"],
        ["reseller", "Hurtowy zakup lub import", "Brak „oficjalny\"", "30–100"],
        ["detalista", "Sklep detaliczny, wąska marża", "Brak logistyki hurtowej", "setki"],
        ["marketplace", "Allegro/Amazon, dropshipping", "Konto >5k opinii", "tysiące"],
        ["producent", "Własne maszynki lub gilzy", "Własna marka, fabryka", "5–10"],
        ["hurtownik", "Hurtownia FMCG/tytoniowa", "PKD 46.35Z, magazyn", "20–50"],
    ], [2.5 * cm, 5 * cm, 6.5 * cm, 3.5 * cm], fontsize=7)
    story.append(Paragraph("4.2 WOLUMEN — szacowany miesięczny obrót maszynkami", styles["h2"]))
    para(story, "Format: <code>duży [OK]</code> (skala + confidence). Progi skalibrowane na niszę, nie na FMCG ogólne.")
    table(story, [
        ["Skala rynku", "Kraje", "Mały/m-c", "Średni/m-c", "Duży/m-c"],
        ["duży", "PL, CZ, FR", "<50", "50–500", "500+"],
        ["średni", "RO, BG, HR, SI, SK", "<20", "20–200", "200+"],
        ["mały", "LT, LV, EE, MD", "<5", "5–50", "50+"],
    ], [3 * cm, 4.5 * cm, 3 * cm, 3.5 * cm, 3.5 * cm], fontsize=7)
    callout(story,
        "<b>Zastrzeżenie:</b> rynek nabijarek to nisza. Nawet „duży\" gracz w PL to realnie 200–500 szt./mies. "
        "Próg 500+ to największe hurtownie ogólnopolskie.")
    story.append(Paragraph("4.3 FLAGI — krótkie oznaczenia", styles["h2"]))
    table(story, [
        ["Flaga", "Znaczenie"],
        ["[BIG]", "Big Fish — najgrubsza ryba w danym kraju (sieć sklepów, hurtownia ogólnopolska)"],
        ["[GEM]", "Gem — off-internet (FB grupa, targi, OLX, opakowanie z numerem seryjnym)"],
        ["[OK] FROZEN", "Zweryfikowane 2 niezależnymi źródłami (rejestr + WWW)"],
        ["[!] DO-WERYFIKACJI", "Weryfikacja niepełna, brak 2. źródła"],
        ["[KONK-B]", "Sprzedaje klon 1:1 naszych marek (Topomat, Turbomatic)"],
        ["[KONK-P]", "Nabijarki, ale inna półka cenowa"],
        ["[PARTNER]", "Może być kanałem"],
    ], [4 * cm, 13.5 * cm], fontsize=7)
    callout(story,
        "<b>Dla handlowca:</b> [OK] FROZEN + [BIG] = kontakt priorytetowy. "
        "[!] DO-WERYFIKACJI = sprawdzić ręcznie przed wysłaniem oferty.",
        color=HexColor("#fff8e6"))
    story.append(Spacer(1, 0.3 * cm))

    # === 5 ===
    section_h1(story, "Weryfikacja — jak działa status FROZEN", 5)
    story.append(Paragraph("Procedura FROZEN (2-tool check)", styles["h2"]))
    para(story, "<b>1.</b> Web search -> potwierdzenie, że firma istnieje i działa.")
    para(story, "<b>2.</b> Rejestr państwowy -> KRS/CEIDG/ARES/VIES + name match "
                 "(nazwa z CSV musi się zgadzać z nazwą w rejestrze).")
    para(story, "<b>3.</b> PASS x 2 -> FROZEN. <b>Mismatch</b> -> DO-WERYFIKACJI lub FABRYKAT (usunięcie).")
    story.append(Paragraph("Defense in depth (3 warstwy anty-halucynacji)", styles["h2"]))
    para(story, "<b>1. NIP checksum (mod 11)</b> — instant, eliminuje 100% losowo generowanych NIP-ów.")
    para(story, "<b>2. KRS/CEIDG API + name-match</b> — eliminuje FABRYKATY (LLM może wygenerować poprawny NIP wskazujący na inną firmę).")
    para(story, "<b>3. Multi-LLM cross-check</b> — gdy to samo pytanie do 2+ LLM-ów daje 2 różne NIP-y -> odrzucenie.")
    callout(story,
        "<b>Dlaczego to ważne:</b> LLM (Gemini, DeepSeek, Claude) potrafi generować NIP-y z poprawnym "
        "checksumem i KRS-y istniejące w rejestrze — ale wskazujące na zupełnie inne firmy. "
        "Bez name-match mielibyśmy 30% halucynacji w bazie.",
        color=HexColor("#fdecea"))
    story.append(Spacer(1, 0.3 * cm))

    # === 6 ===
    section_h1(story, "Potencjał rynkowy per kraj — podział", 6)
    para(story, "Każdy z 12 krajów ma swoją własną notę <code>data/{Kraj}/insight-{ISO}.md</code> i PDF katalogu "
                 "<code>PDF-{ISO}.pdf</code>. Poniżej skrót — wszystkie kwoty są <b>szacunkami</b> (szac.), "
                 "nie twardymi danymi z badań rynkowych.")
    table(story, [
        ["Kraj", "Pop.", "Rynek tytoniowy/rok", "RYO/MYO", "Rynek maszynek/rok", "Bariera", "A/B", "FROZEN"],
        ["[PL] Polska", "38 M", "~26 mld PLN", "~15%", "~15–25 mln PLN", "wysoka", "31/126", "108/157"],
        ["[CZ] Czechy", "10,7 M", "~55 mld CZK", "~20%", "~5–10 mln EUR", "niska", "9/9", "14/18"],
        ["[SK] Słowacja", "5,5 M", "~12 mld EUR", "~18%", "~3–5 mln EUR", "niska", "15/15", "28/30"],
        ["[RO] Rumunia", "19 M", "~30 mld RON", "~25%", "~5–8 mln EUR", "średnia", "8/15", "22/23"],
        ["[BG] Bułgaria", "6,5 M", "~10 mld BGN", "~30%", "~3–5 mln EUR", "średnia", "7/27", "30/34"],
        ["[HR] Chorwacja", "3,9 M", "~8 mld HRK", "~25%", "~2–3 mln EUR", "średnia", "8/11", "17/19"],
        ["[SI] Słowenia", "2,1 M", "~3 mld EUR", "~20%", "~1–2 mln EUR", "niska", "7/9", "14/16"],
        ["[LT] Litwa", "2,8 M", "~5 mld EUR", "~22%", "~1–2 mln EUR", "niska", "12/9", "14/21"],
        ["[LV] Łotwa", "1,9 M", "~3 mld EUR", "~22%", "~0,5–1 mln EUR", "niska", "7/4", "10/11"],
        ["[EE] Estonia", "1,3 M", "~2 mld EUR", "~20%", "~0,5–1 mln EUR", "niska", "10/26", "32/36"],
        ["[FR] Francja", "67 M", "~120 mld EUR", "~10%", "~20–30 mln EUR", "wysoka", "9/12", "18/21"],
        ["[MD] Mołdawia", "2,6 M", "~2 mld MDL", "~35%", "~0,5–1 mln EUR", "niska", "5/2", "5/7"],
    ], [2.5 * cm, 1.5 * cm, 3.5 * cm, 1.5 * cm, 3.5 * cm, 1.5 * cm, 1.5 * cm, 1.5 * cm], fontsize=7)
    para(story, "<b>Tier 1 (priority):</b> PL, CZ, SK, RO, FR — 80% leadów, najlepszy stosunek nakładu do wyniku.")
    para(story, "<b>Tier 2 (hub):</b> BG (hub Płowdiw), EE/LT/LV (Sanitex = 1 partner = 3 kraje).")
    para(story, "<b>Tier 3 (opportunity):</b> SI, HR, MD — małe rynki, niska bariera, brak konkurencji marek premium.")
    story.append(Paragraph("Sanitex group — strategiczna dźwignia multi-country (TOP 1)", styles["h2"]))
    para(story, "<b>Sanitex group</b> = 1 partner otwiera cały rynek bałtycki (~7M konsumentów, 3 kraje).")
    table(story, [
        ["Kraj", "Firma", "Numer", "PKD", "CEO"],
        ["[LT] Litwa", "UAB SANITEX", "LT 110443493", "46.39.00", "Ramūnas Kairys"],
        ["[LV] Łotwa", "SIA SANITEX", "LV 40003166842", "46.39.00", "—"],
        ["[EE] Estonia", "OÜ SANITEX", "EE 11931003", "46.39.00", "—"],
    ], [2 * cm, 4 * cm, 4 * cm, 2 * cm, 5.5 * cm], fontsize=7)
    callout(story,
        "<b>Metryki:</b> 1 239 pracowników, 35 000 klientów, kapitał 4,4M EUR. "
        "<b>Wniosek:</b> Jedna umowa dystrybucyjna otwiera 3 kraje.",
        color=HexColor("#e6f4ea"))
    story.append(Spacer(1, 0.3 * cm))

    # === 7 ===
    section_h1(story, "TOP firmy per kraj — szybki przegląd", 7)
    para(story, "20 najgrubszych ryb z całej bazy. Pełna lista w <code>insight-{ISO}.md</code> + <code>PDF-{ISO}.pdf</code>.")
    table(story, [
        ["Kraj", "Top partner", "Tier", "Kat.", "Dlaczego"],
        ["[PL]", "PHUP GNIEZNO SZESZYCKI", "hurtownik [BIG]", "B8", "1,5 mld zł revenue, 3 000 sklepów, 5 oddziałów"],
        ["[PL]", "POLSKI TYTOŃ S.A.", "hurtownik [BIG]", "B8", "15k+ sklepów, 18,3M PLN, 16 oddziałów"],
        ["[PL]", "BISTA STANDARD", "A5+B8 dual", "A4", "Producent Dark Horse + FERN, eksport 70 krajów"],
        ["[CZ]", "PEAL a.s.", "reseller [BIG]", "A4", "Właściciel marki Don Pealo, dystrybutor ogólnokrajowy"],
        ["[CZ]", "GGT CZ (GG Tabák)", "hurt-group", "B8", "Największy dystrybutor tytoniowy, multi-country"],
        ["[SK]", "GGT a.s. (GGTabak)", "hurtownik [BIG]", "B8", "2 000+ trafik, 16 oddziałów"],
        ["[SK]", "M+M s.r.o.", "producent", "B8", "Własny skład podatkowy, 100+ salonów, hurtownia B2B"],
        ["[RO]", "SC Golden Tip", "reseller", "A4", "E-commerce + hurt, Powermatic, Cartel, Gerui"],
        ["[RO]", "Interbrands Orbico", "hurtownik", "B4", "Dystrybutor PMI, large-scale"],
        ["[BG]", "М ТАБАКО ООД (M Tobacco)", "producent [BIG]", "A5", "Płowdiw — Cartel, Rollo, Imperator; globalny eksporter"],
        ["[BG]", "ГИГА ТРЕЙД БГ ЕООД", "reseller", "A4", "PowerMatic I–IV, Atomic"],
        ["[HR]", "Veletabak d.o.o.", "dystrybutor", "A4", "PowerMatic/OCB; Director: Luka Saraf"],
        ["[SI]", "MERCATOR d.o.o.", "hurtownik", "B8", "Największa sieć handlowa Słowenii"],
        ["[LT]", "UAB Skonis ir kvapas", "e-commerce", "A4", "Specjalistyczny RYO e-com"],
        ["[LV]", "SIA Avalons (tabakeria.lv)", "dystrybutor", "A4", "Największy łotewski dystrybutor tytoniowy"],
        ["[EE]", "PRIKE AS", "hurtownik", "B8", "Czołowy estoński dystrybutor FMCG"],
        ["[EE]", "Montrade NetStores", "e-commerce", "A4", "Największy estoński e-com tytoniowy"],
        ["[FR]", "Logista France", "hurtownik [BIG]", "B4", "23k buralistów, główny kanał dla papierosów"],
        ["[FR]", "Royal Distribution", "hurtownik", "B4", "Akredytowany dostawca buralistów"],
        ["[MD]", "S.R.L. NewSmoke Distribution", "dystrybutor", "A4", "Kiszyniów, RYO + e-papierosy"],
    ], [1.5 * cm, 4.5 * cm, 2.5 * cm, 1 * cm, 8 * cm], fontsize=7)
    story.append(Spacer(1, 0.3 * cm))


# =================== Phrases section ===================

def render_phrase_row(phrase, pl, vol, iso, has_translation=True):
    """Build a 3-col cell with: phrase (bold) | szac. wolumen | PL translation (italic small)."""
    # If iso == PL, pl is same as phrase, so we just show it once
    if iso == "PL":
        return [
            Paragraph(phrase, styles["phrase_main"]),
            Paragraph(vol, styles["body_tight"]),
        ]
    return [
        Paragraph(f"{phrase}", styles["phrase_main"]),
        Paragraph(vol, styles["body_tight"]),
        Paragraph(f"<i>{pl}</i>" if pl else "", styles["phrase_pl"]),
    ]


def build_phrases_section(story):
    if not PHRASES_PATH.exists():
        para(story, "<i>Brak danych o frazach — uruchom najpierw ekstrakcję z SŁOWNIK-{ISO}.md</i>")
        return
    with PHRASES_PATH.open("r", encoding="utf-8") as f:
        all_phrases = json.load(f)

    section_h1(story, "Słownik fraz — „nabijarka do tytoniu\" w 12 językach (z tłumaczeniem PL)", 8)
    para(story,
        "<b>Dlaczego to ważne:</b> Research w każdym kraju zaczyna się od lokalnej nazwy produktu. "
        "Polskie „nabijarka do tytoniu\" nie zadziała w Czechach ani w Estonii. Poniżej rozszerzone listy fraz "
        "(<b>urządzenia + marki + hurtownie + sklepy</b>) per kraj z szac. wolumenem "
        "(<code>szac.</code> z SŁOWNIK-{ISO}.md, walidowane wobec realnych danych Allegro/Ceneo/Heureka/TikTok) "
        "i <b>tłumaczeniem na polski</b> pod każdą obcą frazą. Mniejsze litery = polski przekład.")

    # Validation note
    callout(story,
        "<b>Walidacja wolumenów:</b> Allegro PL: 576 ofert dla „maszyna do produkcji papierosów nabijania\" (sierpień 2026) -> "
        "potwierdza aktywność rynku PL. Ceneo PL: 30 produktów „Nabijarki do papierosów\", średnia 121,24 zł. "
        "FR: „machine à rouler les cigarettes\" — stabilne zainteresowanie z sezonowymi szczytami VI-VIII. "
        "TikTok: #tiktokpolska = 18 606 śr. wyświetleń/post.",
        color=HexColor("#e6f4ea"))

    # Build per-country blocks
    order = ['PL', 'CZ', 'SK', 'RO', 'BG', 'HR', 'SI', 'LT', 'LV', 'EE', 'FR', 'MD']
    for iso in order:
        if iso not in all_phrases:
            continue
        cats = all_phrases[iso]
        device = cats.get('device', [])
        brand = cats.get('brand', [])
        wholesale = cats.get('wholesale', [])
        retail = cats.get('retail', [])

        # Country header (keep with first table)
        country_block = []
        country_block.append(Paragraph(COUNTRY_LABEL[iso], styles["h2"]))

        # Helper to build 3-col table: fraza | szac. wolumen | tłumaczenie PL (smaller)
        def build_cat_table(items, cat_label):
            if not items:
                return None
            # PL: 2 cols (no translation); others: 3 cols
            if iso == "PL":
                data = [[
                    Paragraph(f"<b>{cat_label}</b>", styles["body_tight"]),
                    Paragraph("<b>Szac. wolumen</b>", styles["body_tight"]),
                ]]
                for it in items:
                    phrase = it['phrase']
                    vol = it['vol']
                    data.append([
                        Paragraph(phrase, styles["phrase_main"]),
                        Paragraph(vol, styles["body_tight"]),
                    ])
                col_widths = [12.0 * cm, 5.5 * cm]
            else:
                data = [[
                    Paragraph(f"<b>{cat_label}</b>", styles["body_tight"]),
                    Paragraph("<b>Szac. wolumen</b>", styles["body_tight"]),
                    Paragraph("<b>Tłumaczenie PL</b>", styles["body_tight"]),
                ]]
                for it in items:
                    phrase = it['phrase']
                    pl = it.get('pl', phrase)
                    vol = it['vol']
                    data.append([
                        Paragraph(phrase, styles["phrase_main"]),
                        Paragraph(vol, styles["body_tight"]),
                        Paragraph(f"<i>{pl}</i>" if pl else "", styles["phrase_pl"]),
                    ])
                col_widths = [6.5 * cm, 4.0 * cm, 7.0 * cm]

            tbl = Table(data, colWidths=col_widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_HEADER_TEXT),
                ("FONTNAME", (0, 0), (-1, 0), "VB"),
                ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.2, COLOR_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ]))
            for i in range(1, len(data)):
                if i % 2 == 0:
                    tbl.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), COLOR_ZEBRA)]))
            return tbl

        # Build categories — at most 3 most important (wholesale+device+brand) for compactness
        cat_order = [
            ('Urządzenia (nabijarki)', device[:10]),
            ('Marki (PowerMatic, Hawk, Topomat...)', brand[:6]),
            ('Hurtownie / dystrybutorzy', wholesale[:10]),
            ('Sklepy / e-commerce', retail[:6]),
        ]
        for cat_label, items in cat_order:
            t = build_cat_table(items, cat_label)
            if t:
                country_block.append(t)
                country_block.append(Spacer(1, 0.1 * cm))

        # Operators hint
        country_block.append(Paragraph(
            f"<i>Operatory: site:google.com \"{ {'PL':'nabijarka', 'CZ':'plnička', 'SK':'plnička', 'RO':'mașină', 'BG':'машина', 'HR':'stroj', 'SI':'stroj', 'LT':'pildymo', 'LV':'pildītājs', 'EE':'täitemasin', 'FR':'machine', 'MD':'mașină'}[iso]}\" | "
            f"intitle:\"{'hurtownia' if iso in ['PL','CZ'] else 'velkoobchod' if iso == 'CZ' else 'distribuitor' if iso in ['RO','MD'] else 'distributor' if iso == 'HR' else 'veleprodaja' if iso in ['HR','SI'] else 'hulgimüük' if iso == 'EE' else 'vairumtirdzniecība' if iso == 'LV' else 'didmeninė' if iso == 'LT' else 'grossiste' if iso == 'FR' else 'velkoobchod'}\" "
            f"\"{ {'PL':'tytoń', 'CZ':'tabák', 'SK':'tabak', 'RO':'tutun', 'BG':'тютюн', 'HR':'duhan', 'SI':'tobak', 'LT':'tabakas', 'LV':'tabaka', 'EE':'tubakas', 'FR':'tabac', 'MD':'tutun'}[iso]}\"</i>",
            styles["small_italic"]
        ))
        country_block.append(Spacer(1, 0.15 * cm))

        # Keep country header with first 2-3 elements to avoid orphan headers
        story.append(KeepTogether(country_block[:3]))
        for el in country_block[3:]:
            story.append(el)

    # Bonus
    story.append(Paragraph("Bonus — globalne marki (EN)", styles["h2"]))
    story.append(Paragraph(
        "<b>powerMatic rolling machine</b>, <b>hawk rolling machine</b>, <b>topomat</b>, "
        "<b>turbomatic</b>, <b>luxfux</b>, <b>cigarette injector machine</b>, <b>tobacco filling machine</b>, "
        "<b>electric cigarette maker</b>, <b>piston rolling machine</b> — działają globalnie "
        "(LinkedIn, YouTube, eBay, Amazon). Używaj jako fallback gdy brak lokalnej nazwy.",
        styles["body"]))
    callout(story,
        "<b>Pełne słowniki (20–80 fraz per kraj + operatory + szac. wolumeny):</b> "
        "<code>data/{Kraj}/SŁOWNIK-{ISO}.md</code> (12 plików).",
        color=HexColor("#e6f4ea"))
    story.append(Spacer(1, 0.3 * cm))


def build_tail(story):
    # === 9 — Metody researchu B2B + nauka per sesja (DZIENNIK + INTEL) ===
    section_h1(story, "Metody researchu B2B — 11 poziomów + nauka per sesja", 9)

    # 9.0 Filozofia
    para(story,
         "<b>Filozofia:</b> research to iteracyjny proces. Każda sesja to cykl: <b>search</b> wg "
         "<code>SŁOWNIK-{ISO}.md</code> -> <b>log do DZIENNIK.md</b> (5-10 min) -> <b>ekstrakcja do INTEL.md</b> "
         "(partnerzy, rynek, narzędzia) -> <b>następna sesja</b> zaczyna z lekcji poprzedniej. "
         "Bez tego cyklu każda sesja zaczyna od zera.")
    callout(story,
        "<b>DZIENNIK.md</b> = chronologiczny log sesji (data, metoda L0-L11, wynik, pytania, błędy). "
        "<b>INTEL.md</b> = skumulowana wiedza (partnerzy, dane rynkowe, limity API, decyzje architektoniczne). "
        "<b>methodology.md</b> = kanoniczny reference (definicje, schematy, kolejność). "
        "Po 8 sesjach (10-18 VIII 2026): DZIENNIK 1586 linii, INTEL 450 linii, methodology 875 linii.")

    # 9.1 Tabela 11 metod + efektywność
    story.append(Paragraph("9.1 Tabela: 11 metod + efektywność", styles["h2"]))
    para(story, "Każda z 11 metod (L0-L11) to osobna warstwa. L0-L3 + L7-L9 = core (używane). L4-L6 = PL-only lub manual. L10-L11 = planowane.")
    table(story, [
        ["L", "Metoda", "Co robiliśmy konkretnie", "Efekt", "Wniosek"],
        ["L0", "Pre-flight NIP/KRS", "NIP checksum mod 11 + KRS API name-match", "[OK] 100% odrz.", "Must-have"],
        ["L1", "Web search G/DDG/Brave", "Frazy z SŁOWNIK + operatory site:, intitle:, inurl:", "[OK] start 80%", "DDG captcha; Brave"],
        ["L2", "Marketplace Allegro/OLX", "Allegro REST API: sprzedawca -> NIP -> CEIDG", "[OK] PL, [!] reszta", "OLX = brak API"],
        ["L3", "Rejestry KRS/ARES/VIES", "PKD 46.35Z/47.26Z/47.11Z + name-search + chain", "[OK] PL/CZ/EE", "ARES CZ 97.6%"],
        ["L4", "Urząd Celny + KAS", "Status VAT, KAS Pośrednicy, BDO, CN 8479 89 97 90", "[OK] PL only", "Twarde dane PL"],
        ["L5", "DNS + WHOIS + crt.sh", "Certificate Transparency dla subdomen PM/Hawk", "[!] manual", "WHOIS po 2018 = pusty"],
        ["L6", "Targi 2024-2026", "InterTabac / World Vape / Eurocis / Vapexpo", "[!] manual", "Brak API; PDF scrape"],
        ["L7", "Social FB/IG/TikTok/YT", "Grupy FB, TikTok Creative Center, YT komentarze", "[OK] PL, [!] reszta", "#tiktokpolska złoto"],
        ["L8", "Katalogi nipgo/Veritor", "Bulk search NIP/nazwa. nipgo.pl 3M PL, Veritor 10 EU", "[OK]", "nipgo.pl PL; Veritor EU"],
        ["L9", "LLM DeepSeek/Gemini/Claude", "OpenRouter enrichment + multi-LLM consensus (2/3 zgoda)", "[OK] z L0", "Nigdy solo — z L0"],
        ["L10", "EUIPO trademark", "Właściciele znaków towarowych PM/Hawk w EU", "[X] nie wdrożone", "Planowane Q4 2026"],
        ["L11", "BZP / TED zamówienia publ.", "Kto dostarczał tytoń do instytucji (CPV 15800000-6)", "[X] nie wdrożone", "Planowane Q4 2026"],
    ], [0.7 * cm, 3.3 * cm, 7.3 * cm, 2.5 * cm, 3.7 * cm], fontsize=6.5)

    # 9.2 Co zadziałało
    story.append(Paragraph("9.2 Co zadziałało ([OK])", styles["h2"]))
    table(story, [
        ["Metoda", "Wynik", "Dowód / liczby"],
        ["KRS Open API (PL)", "100% match dla 65 PL firm", "Pełny odpis .json, bez autoryzacji"],
        ["VIES (EU)", "85% match dla PL NIP + L2 name-match", "52/61 PL NIP zwalidowanych"],
        ["ARES (CZ)", "97,6% FROZEN dla CZ (40/41)", "IČO lookup, bez limitu, JSON API"],
        ["e-Äriregister (EE)", "Pełne dane z KMKR, EMTAK, reg_code", "Najlepszy rejestr w regionie"],
        ["Allegro REST API (PL)", "Lista sprzedawców + opinie (proxy wolumen)", "9000 req/h, OAuth darmowy, 576 ofert dla „nabijarka\""],
        ["Heureka (CZ)", "30 produktów „Nabijarki do papierosów\"", "średnia 121,24 zł — benchmark cenowy"],
        ["Google Maps Places API", "Masowe pozyskanie leadów B z deduplikacją", "$32/1000 req — najskuteczniejsze dla B8/B6"],
        ["TikTok Creative Center", "Weryfikacja realnych zasięgów hashtagów", "18,6k śr. wyświetleń #tiktokpolska (TOP PL)"],
        ["Multi-LLM consensus", "Eliminuje halucynacje NIP/KRS", "2/3 modeli muszą się zgodzić"],
        ["Sanitex (LT/LV/EE hub)", "1 partner = 3 kraje (multi-country)", "1239 pracowników, 35k klientów, 4,4M EUR kapitał"],
    ], [4 * cm, 7.5 * cm, 6 * cm], fontsize=7)

    # 9.3 Co nie zadziałało
    story.append(Paragraph("9.3 Co nie zadziałało ([!]) + fallback", styles["h2"]))
    table(story, [
        ["Metoda", "Problem", "Fallback", "Wniosek"],
        ["WHOIS dla .pl", "Po 2018 (GDPR) ukryte dane", "crt.sh + scraping strony", "Nie ufaj WHOIS 2026+"],
        ["DuckDuckGo HTML", "Bot blocker + captcha, 0%", "Brave Search", "DDG tylko do weryfikacji"],
        ["CEIDG v3 API", "Pusty body dla typowych nazw", "ręczne / nipgo.pl", "API zawodne, frontend działa"],
        ["OpenRouter Perplexity", "LLM bez dostępu do rejestrów", "Perplexity + URL verifier", "NIE ufaj LLM bez L0"],
        ["LT/LV/BG/SI/HR rejestry", "SPA-only, reCAPTCHA", "Manual + Veritor (paid)", "Bałtyckie = Veritor must"],
        ["ONRC (RO)", "Paid 8 lei/odpis (~7 PLN)", "Limitowane, tylko krytyczne", "Najgorszy ROI w regionie"],
        ["OLX / Ceneo / InPost Buy", "Brak oficjalnego API", "Scraping (blokowany)", "NIE polegaj dla skali"],
        ["Photon / OSM", "Brak danych B2B (tylko adresy)", "Google Places", "OSM = adresy, nie firmy"],
        ["Facebook grup scrape", "reCAPTCHA + ToS", "Manual przez grupy FB", "FB grupy = ręcznie"],
    ], [4.5 * cm, 4.5 * cm, 4.5 * cm, 4 * cm], fontsize=7)

    # 9.4 Wnioski strategiczne
    story.append(Paragraph("9.4 Wnioski strategiczne (po 8 sesjach)", styles["h2"]))
    bullet(story, "<b>Baza darmowa + publiczna = ~70% leadów</b> weryfikowalnych. Reszta = paid API lub manual.")
    bullet(story, "<b>Najlepszy stosunek sygnału do ceny:</b> KRS + VIES + ARES + Google Places + Allegro (~$30/m) — pokrywa ~85% PL/CZ.")
    bullet(story, "<b>Dla LT/LV/BG/SI/HR:</b> jedyna realna opcja to Veritor ($199/5k) — bez tego manual.")
    bullet(story, "<b>L0 must-have</b> — bez niego 30% halucynacji. <b>L9 (LLM) bez L0 = katastrofa</b>.")
    bullet(story, "<b>Najgorszy ROI:</b> ONRC (8 lei/odpis) + WHOIS po 2018 (zero danych) + OLX scraping (ciągle blokowany).")
    callout(story,
        "<b>Dla handlowca:</b> Jak dostajesz nowy lead i nie możesz znaleźć NIP w Google — sprawdź czy to nie mała firma / JDG. "
        "Wtedy trzeba albo Veritor ($199/m), albo 5-10 min manual przez nipgo.pl. "
        "Nie trać czasu na ONRC, OLX scraping ani WHOIS.")

    # 9.5 Cykl DZIENNIK + INTEL
    story.append(Paragraph("9.5 Cykl DZIENNIK + INTEL — jak się uczymy", styles["h2"]))
    para(story,
         "<b>DZIENNIK.md</b> to chronologiczny log sesji. <b>INTEL.md</b> to skumulowana wiedza. Razem tworzą "
         "<b>compounding knowledge</b> — każda sesja zaczyna z lekcji poprzedniej, nie od zera.")
    callout(story,
        "<b>Cykl:</b> (1) Search -> (2) Log do DZIENNIK (5-10 min: co zadziałało, co nie, pytania) -> "
        "(3) Ekstrakcja do INTEL (partnerzy > hurt 1k klientów, realne dane Allegro/Ceneo/TikTok, nowe API, limity systemowe) -> "
        "(4) Następna sesja zaczyna z tej wiedzy.",
        color=HexColor("#e6f4ea"))
    para(story, "<b>Kiedy pisać do DZIENNIK.md:</b>", style="body")
    bullet(story, "Po każdej sesji search (5-10 min): data, metoda (L0-L11), co znaleziono, nowe pytania")
    bullet(story, "Przy napotkaniu halucynacji LLM (typ NIP/KRS wskazuje na inną firmę)")
    bullet(story, "Przy znalezieniu nowego narzędzia / API / źródła danych")
    bullet(story, "Przy zmianie kolumny schematu CSV lub decyzji architektonicznej")
    bullet(story, "Po każdej decyzji z Marcelim (kierunek, scope, priorytet)")
    para(story, "<b>Kiedy przenosić do INTEL.md:</b>", style="body")
    bullet(story, "Partner > hurtownik 1000+ klientów → wpis do sekcji <b>Partnerzy</b>")
    bullet(story, "Realne dane rynkowe (Allegro/Ceneo/TikTok) → sekcja <b>Dane rynkowe PL</b>")
    bullet(story, "Nowe API lub tool → sekcja <b>Narzędzia</b>")
    bullet(story, "Ograniczenie systemowe (np. CEIDG v3 pusty body) → sekcja <b>Limity</b>")
    callout(story,
        "<b>Korzyść po 8 sesjach (10-18 VIII 2026):</b> DZIENNIK 1586 linii logu + INTEL 450 linii wiedzy + "
        "methodology 875 linii reference. Bez tego cyklu każda sesja zaczynałaby od zera. "
        "<b>To jest compounding knowledge</b> — i dlatego BILLSzuka jest wartościowa, a nie jednorazowa.",
        color=HexColor("#fff8e6"))
    story.append(Spacer(1, 0.3 * cm))

    # === 10 ===
    section_h1(story, "Problemy ze źródłami danych — szczegóły", 10)
    para(story, "<b>Dla działu sprzedaży:</b> to jest lista rzeczy, które nie są widoczne w gotowej bazie master.csv ale wpływają na jej kompletność. "
                 "Przeczytaj zanim powiesz „ta firma powinna tu być, a jej nie ma\".")
    story.append(Paragraph("10.1 Rejestry państwowe bez publicznego API", styles["h2"]))
    table(story, [
        ["Kraj", "Rejestr", "Problem", "Konsekwencja"],
        ["[LT]", "JAR (Registrų Centras)", "SPA, brak JSON, rate limit", "14/21 (66%)"],
        ["[LV]", "UR (info.ur.gov.lv)", "SPA, captcha", "10/11 (91%)"],
        ["[SI]", "AJPES", "SPA, brak JSON", "14/16 (87%)"],
        ["[HR]", "Sudski registar", "SPA + reCAPTCHA", "17/19 (89%)"],
        ["[BG]", "Trade Register", "Brak API, web search per firma", "30/34 (88%)"],
        ["[MD]", "State Register (IDNO)", "Brak dobrego API", "5/7 (71%)"],
    ], [1.5 * cm, 4.5 * cm, 6 * cm, 5.5 * cm], fontsize=7)
    callout(story,
        "<b>Praktyczny efekt:</b> w tych krajach część leadów jest oznaczona [!] DO-WERYFIKACJI. "
        "<b>Przed wysłaniem oferty</b> sprawdź ręcznie w przeglądarce.")
    story.append(Paragraph("10.2 Brak NIP/REGON w danych źródłowych", styles["h2"]))
    para(story, "Dla ~50–80% nowych leadów (zwłaszcza małych firm, JDG, e-commerce) nie da się automatycznie znaleźć NIP/REGON.")
    table(story, [
        ["Metoda", "Skuteczność", "Uwagi"],
        ["Bezpośredni fetch firmy WWW", "5–10%", "PL firmy rzadko mają NIP na homepage"],
        ["DuckDuckGo HTML", "0%", "Bot blocker"],
        ["WHOIS dla .pl", "0% (po 2018)", "Tylko registrar, daty"],
        ["CEIDG v3 API", "~5%", "Pusty body dla typowych nazw"],
        ["OpenRouter Perplexity/sonar", "0–10%", "LLM nie ma dostępu do rejestrów"],
    ], [5 * cm, 3 * cm, 9.5 * cm], fontsize=7)
    callout(story, "<b>Wniosek:</b> dla małych firm potrzeba <b>paid API</b> (Veritor, ENTIA) albo <b>manual</b> (5–10 min/firma).")
    story.append(Paragraph("10.3 Marketplace'y bez API", styles["h2"]))
    table(story, [
        ["Marketplace", "API", "Dane", "Fallback"],
        ["Allegro (PL)", "OAuth2", "NIP, opinie, kategoria", "Używane"],
        ["OLX (PL)", "brak", "—", "Scraping (blokowany)"],
        ["Ceneo (PL)", "brak", "—", "Mirror rankingu"],
        ["Heureka (CZ)", "brak", "—", "ręczne"],
        ["eMAG (RO)", "dla sellerów", "Dane sprzedawcy", "nie wdrożone"],
        ["Alza (CZ)", "B2B partner", "Stany magazynowe", "nie wdrożone"],
        ["Kaufland (DE/PL)", "Marketplace", "NIP, opinie", "nie wdrożone"],
        ["InPost Buy (PL)", "brak", "—", "brak"],
    ], [4 * cm, 2.5 * cm, 5.5 * cm, 5.5 * cm], fontsize=7)
    story.append(Paragraph("10.4 Brak danych decydentów (główna luka)", styles["h2"]))
    para(story, "<b>Stan na 2026-08-19:</b> decydent wypełniony tylko dla 142/393 firm (36%).")
    table(story, [
        ["Kraj", "Decydent fill", "Trudność"],
        ["[PL]", "20% (32/157)", "Główna luka — Perplexity Sonar dawał 0/30 w auto-loop; zawieszony 2026-08-18"],
        ["[CZ]", "89% (16/18)", "ARES daje jednatele dla sp. z o.o."],
        ["[SK]", "87% (26/30)", "orsr.sk działa"],
        ["[RO]", "78% (18/23)", "ANAF offline, listafirme wymaga Apify"],
        ["[BG]", "32% (11/34)", "finansi.bg działa, ale web_search per firma"],
        ["[HR]", "53% (10/19)", "Sudreg SPA + reCAPTCHA"],
        ["[SI]", "50% (8/16)", "AJPES SPA"],
        ["[LT]", "57% (12/21)", "JAR SPA"],
        ["[LV]", "36% (4/11)", "ur.gov.lv SPA"],
        ["[EE]", "53% (19/36)", "e-Äriregister działa dobrze"],
        ["[FR]", "19% (4/21)", "Pappers.fr (paid) lub Societe.com (limit)"],
        ["[MD]", "14% (1/7)", "Brak publicznego źródła"],
    ], [1.5 * cm, 3 * cm, 13 * cm], fontsize=7)
    callout(story, "<b>Wniosek:</b> wypełnienie decydenta do >80% wymaga <b>Veritor / ENTIA / Pappers.fr</b> (subskrypcja).")
    story.append(Paragraph("10.5 Hallucynacje LLM — zagrożenie dla bazy", styles["h2"]))
    para(story, "LLM potrafi generować poprawne checksumowo NIP-y wskazujące na zupełnie inne firmy. Przykład z bazy: „HURTOWNIA PAPIEROSÓW CYGARO\" = KRS 0000123456 -> realnie to RODENSTOCK POLSKA (optyka).")
    callout(story, "<b>Zabezpieczenie:</b> 2-tool check + multi-LLM consensus + NIP checksum + KRS name-match. <b>Skutek:</b> złapano 9 halucynacji w pierwszym przejściu (2026-08-18), wszystkie odrzucone.", color=HexColor("#fdecea"))
    story.append(Spacer(1, 0.3 * cm))

    # === 11 ===
    section_h1(story, "Rekomendowane API i płatne serwisy", 11)
    para(story, "<b>Dla kierownictwa:</b> lista narzędzi, które pozwoliłyby podnieść kompletność bazy z obecnych 95,2% FROZEN do ~99% i wypełnić lukę decydentów (36% -> 80%+). Ceny 2026-08.")
    story.append(Paragraph("11.1 Cross-country KYB (Know Your Business)", styles["h2"]))
    table(story, [
        ["Narzędzie", "Co daje", "Cena (mies.)", "Rekomendacja"],
        ["Veritor *", "10 rejestrów EU, KYB, UBO, sankcje", "Free 50, $199/5k, $499/25k", "TOP 1: LT/LV/BG/SI/HR/MD"],
        ["ENTIA", "5,5M firm 34 kraje, trust score, sankcje", "MCP paid, od €290/m", "EU + UK + Szwajcaria"],
        ["eu-verify MCP", "FR/EU: rejestr, VAT, sankcje, IBAN, SIRET, LEI", "~$0.10/zapytanie", "Dobry do FR i ad-hoc"],
        ["OpenCorporates", "Globalny agregator, mirror 100+ rejestrów", "Free + API $99/10k", "Backup dla Veritor"],
        ["Pappers.fr * FR", "FR: rejestr, dyrektorzy, finanse", "49 € Essentiel, 199 € Premium", "Obowiązkowe dla FR"],
    ], [3 * cm, 5.5 * cm, 4.5 * cm, 4.5 * cm], fontsize=7)
    story.append(Paragraph("11.2 Rejestry per kraj (alternatywa dla Veritor)", styles["h2"]))
    table(story, [
        ["Kraj", "Rejestr", "Cena", "Status"],
        ["[PL]", "KRS API (ekrs.ms.gov.pl)", "Darmowy", "[OK] działa"],
        ["[PL]", "CEIDG v3 API", "Darmowy (Bearer token)", "[OK] wdrożone"],
        ["[PL]", "REGON (GUS BIR1)", "Darmowy (USER_KEY z BIR)", "[OK] wdrożone"],
        ["[CZ]", "ARES (ares.gov.cz)", "Darmowy", "[OK] działa"],
        ["[SK]", "FinStat", "€19/m (Basic, 1000/dzień)", "[X] nie wdrożone"],
        ["[RO]", "ONRC", "8 lei/odpis (~7 PLN)", "[X] zbyt drogo"],
        ["[RO]", "Termene.ro", "€30/m", "Alternatywa"],
        ["[BG]", "finansi.bg", "~30 BGN/m", "Alternatywa"],
        ["[HR]", "Poslovna Hrvatska", "€49/m Pro", "[X] nie wdrożone"],
        ["[LT]", "data.gov.lt (JAR spinta)", "Darmowy (dla sp. państwowych)", "[OK] działa dla części"],
        ["[LV]", "Lursoft", "€25/m (Lite)", "[X] nie wdrożone"],
        ["[EE]", "e-Äriregister (ariregister.rik.ee)", "Darmowy", "[OK] działa"],
        ["[FR]", "SIRENE / Recherche Entreprises", "Darmowy", "[OK] bez dyrektorów"],
    ], [1.5 * cm, 5 * cm, 5.5 * cm, 5.5 * cm], fontsize=7)
    story.append(Paragraph("11.3 Marketplace + social media", styles["h2"]))
    table(story, [
        ["Narzędzie", "Co daje", "Cena", "Status"],
        ["Allegro REST API", "NIP sprzedawcy, opinie, kategoria", "Darmowy (OAuth2)", "[OK] wdrożone"],
        ["Apify CEIDG Scraper", "Bulk CEIDG search", "~$0.01/result", "[OK] używane"],
        ["Apify Instagram Hashtag", "Avg likes/comments/views", "$5–15 / 1k wyników", "[X] nie wdrożone"],
        ["Apify YouTube Comments", "Komentarze pod recenzjami", "$5/10k wyników", "[X] nie wdrożone"],
        ["Google Maps Places API", "Nazwa, adres, telefon, rating, opinie", "$32/1000 req, $200/m free", "[OK] używane"],
        ["Ahrefs / Senuto", "Realne wolumeny wyszukiwania", "$99–$199/m", "[X] nie wdrożone"],
        ["Google Trends", "Trend rosnący/malejący", "Darmowy", "[OK] używane"],
        ["TikTok Creative Center", "Realne zasięgi hashtagów", "Darmowy", "[OK] używane"],
    ], [4 * cm, 6 * cm, 4 * cm, 3.5 * cm], fontsize=7)
    story.append(Paragraph("11.4 Rekomendowany stack (priorytet 1, 2, 3)", styles["h2"]))
    callout(story,
        "<b>Priorytet 1 — najszybszy efekt (~$250/m):</b><br/>"
        "• Veritor Starter $199/m (LT/LV/BG/SI/HR/MD/EE/FR/RO/CZ)<br/>"
        "• Allegro REST API free (PL marketplace)<br/>"
        "• Google Maps Places API $30/m (masowe B-leads)<br/>"
        "• Apify CEIDG $20/m (bulk PL)<br/>"
        "-> <b>100% FROZEN + 80% decydentów</b>",
        color=HexColor("#e6f4ea"))
    callout(story,
        "<b>Priorytet 2 — rozszerzenie (~$650/m):</b><br/>"
        "• Pappers.fr Essentiel €49/m (dyrektorzy FR 19% -> 80%)<br/>"
        "• Ahrefs Standard $99/m (realne wolumeny zamiast szacunków)<br/>"
        "• FinStat SK €19/m (dyrektorzy + finanse SK)<br/>"
        "-> <b>100% FROZEN + 90% decydentów + realne wolumeny</b>",
        color=HexColor("#fff8e6"))
    callout(story,
        "<b>Priorytet 3 — premium (~$1 200/m):</b><br/>"
        "• ENTIA MCP €290/m (trust score, sankcje, monitoring)<br/>"
        "• OpenCorporates API $99/m (backup dla Veritor, mirror globalny)<br/>"
        "• Lursoft LV €25/m (Łotwa)<br/>"
        "-> <b>pełna baza KYB + monitoring zmian statusu</b>",
        color=HexColor("#e8eaf6"))
    story.append(Spacer(1, 0.3 * cm))

    # === 12 ===
    section_h1(story, "Jak korzystać z bazy — 3 kroki dla handlowca", 12)
    story.append(Paragraph("Krok 1: Otwórz master.csv lub PDF per kraj", styles["h2"]))
    para(story, "<code>data/master.csv</code> (393 wiersze, 35 kolumn) lub <code>PDF katalogu dla swojego kraju</code> (PDF-{ISO}.pdf). Filtruj po:")
    bullet(story, "<b>tier</b> (wyłączność > autoryzowany > reseller)")
    bullet(story, "<b>kategoria</b> (A1–A6 dla maszynek, B1–B9 dla cross-sell)")
    bullet(story, "<b>flagi</b> ([OK] FROZEN + [BIG] = priorytet)")
    bullet(story, "<b>decydent</b> (puste = wymaga wzbogacenia ręcznego)")
    story.append(Paragraph("Krok 2: Sprawdź insight-{ISO}.md", styles["h2"]))
    para(story, "Dla kontekstu rynkowego (regulacje, marketplace'y, TOP firmy, cross-country ties).")
    story.append(Paragraph("Krok 3: Zanotuj feedback", styles["h2"]))
    para(story, "W <code>DZIENNIK.md</code> — co zadziałało, co nie, kto odpowiedział, kto odrzucił. Baza żyje dzięki Waszemu feedbackowi.")
    callout(story,
        "<b>Ważne:</b> Przed pierwszą rozmową z firmą DO-WERYFIKACJI ([!]) — sprawdź ręcznie w przeglądarce "
        "<code>https://www.{kraj}-registry.gov/</code> (KRS, ARES, e-Äriregister itd.), żeby potwierdzić nazwę i NIP. "
        "30 sekund pracy, a oszczędza wstyd przy „literówce w nazwie firmy\".",
        color=HexColor("#fdecea"))
    story.append(Spacer(1, 0.3 * cm))

    # === 13 ===
    section_h1(story, "Status projektu i plan na najbliższe miesiące", 13)
    table(story, [
        ["Kamień milowy", "Data", "Status"],
        ["[PL] PL research zamknięty", "2026-08-12", "[OK] 65/235 (27,7%) FROZEN"],
        ["[CZ] CZ research zamknięty", "2026-08-12", "[OK] 40/41 (97,6%) FROZEN"],
        ["Wszystkie 12 krajów zweryfikowane", "2026-08-18", "[OK] 393/393 (100%) -> 374/393 (95,2%) po enrichment"],
        ["Decydent enrichment", "2026-08-11 -> 18", "[!] 142/393 (36%) — główna luka"],
        ["Cross-country ties", "2026-08-18", "[OK] GGT (CZ+SK), GECO (CZ+SK), TTI (CZ+SK+BG+RO), Sanitex (LT+LV+EE)"],
        ["12 PDF katalogów per kraj", "2026-08-18", "[OK] 107 stron łącznie, locked v9"],
        ["3–5 podpisanych umów dystrybucyjnych", "target: 12 mies.", "[W TOKU] w toku"],
    ], [6.5 * cm, 3.5 * cm, 7.5 * cm], fontsize=7)
    story.append(Paragraph("Plan 2026 Q3-Q4", styles["h2"]))
    para(story, "<b>1. Veritor / Pappers.fr subskrypcja</b> -> decydent fill 36% -> 80%.")
    para(story, "<b>2. Outreach 28 FROZEN PL firm</b> (katalog A) + <b>6 Big Fish PL</b> (katalog B).")
    para(story, "<b>3. Outreach CZ TOP 5</b> (PEAL, GGT, GECO, CTC, FORTIS-DB).")
    para(story, "<b>4. Outreach Sanitex (LT/LV/EE)</b> — 1 umowa = 3 kraje.")
    story.append(Spacer(1, 0.3 * cm))
    para(story,
        "<i>Dokument wygenerowany 2026-08-19 na podstawie INTEL.md, DZIENNIK.md, methodology.md, "
        "data/{Kraj}/insight-{ISO}.md, data/{Kraj}/SŁOWNIK-{ISO}.md i data/master.csv.</i>", "small")
    para(story, "<i>Wersja 1.4 · Właściciel: Marceli (BILLS Sp. z o.o.) · Kolejna aktualizacja: po każdym nowym enrichment lub outreachu.</i>", "small")


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("V", 7)
    canvas.setFillColor(COLOR_GREY)
    canvas.drawString(MARGIN, 0.5 * cm,
                      f"BILLS Sp. z o.o. · Ostrzeszów · INSTRUKCJA · 2026-08-19")
    canvas.drawRightString(A4[0] - MARGIN, 0.5 * cm,
                           f"Strona {doc.page}")
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(0.3)
    canvas.line(MARGIN, A4[1] - 0.5 * cm, A4[0] - MARGIN, A4[1] - 0.5 * cm)
    canvas.restoreState()


def main():
    output_pdf = DATA_DIR / "INSTRUKCJA.pdf"
    print(f"[PDF] Generuję: {output_pdf}")

    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="BILLSzuka — Instrukcja dla Działu Sprzedaży",
        author="BILLS Sp. z o.o.",
        subject="B2B lead research methodology",
        creator="pdf_gen_instrukcja.py v1.4",
    )

    story = []
    country_rows = country_stats()
    print(f"  -> {len(country_rows)} krajów, "
          f"Σ {sum(r['a_total']+r['b_total'] for r in country_rows)} leadów")

    build_intro_title(story)
    build_inventory_page(story, country_rows)
    build_main(story)
    build_phrases_section(story)
    build_tail(story)

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"[OK] Gotowe: {output_pdf}")
    print(f"  Rozmiar: {output_pdf.stat().st_size / 1024:.1f} KB")
    try:
        from pypdf import PdfReader
        n = len(PdfReader(str(output_pdf)).pages)
        print(f"  Stron: {n}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
