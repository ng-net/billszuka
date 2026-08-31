"""tools/pdf_append_leads.py — Append leads appendix pages to PDF-{ISO}.pdf.

Locked rules (PDF-LEADS-SPEC):
- 13 visible columns: Firma, Miasto/Adres, WWW, Email/Telefon, Kontakt, Email decydent,
  Social media, Marki/Sourcing, Wolumen+confidence, Tier, Kanał, Flagi, Notatki
- Social media: 1 column with 4 sub-rows (LinkedIn/Facebook/Instagram/TikTok) + icons
- Wolumen: bold value + colored dot icon (green/yellow/orange/gray/red)
- Decydent/Stanowisko/Email decydent: check/cross icon
- Flagi: parsed emoji → icons (✓ ⚠ 🐋 🔴 🟢 💎)
- Multi-line wrap, font 7.5pt, name 8.5pt bold
- Uses pypdf.PdfWriter to merge (doesn't overwrite existing PDF)

Usage: python3 tools/pdf_append_leads.py --iso CZ
"""
import argparse
import csv
import re
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Fonts
pdfmetrics.registerFont(TTFont("V", "/System/Library/Fonts/Supplemental/Verdana.ttf"))
pdfmetrics.registerFont(TTFont("VB", "/System/Library/Fonts/Supplemental/Verdana Bold.ttf"))
pdfmetrics.registerFont(TTFont("VI", "/System/Library/Fonts/Supplemental/Verdana Italic.ttf"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICON_DIR = PROJECT_ROOT / "data" / "_icons"

PAGE_W, PAGE_H = A4  # 21 × 29.7 cm — portrait, 18cm usable
MUTED = HexColor("#707070")
TEXT = HexColor("#1A1A1A")
ACCENT = HexColor("#1F1F1F")
LINE = HexColor("#D0D0D0")

NAME = ParagraphStyle("NAME", fontName="VB", fontSize=11, leading=13, textColor=TEXT, alignment=TA_LEFT)
ID = ParagraphStyle("ID", fontName="VI", fontSize=7.5, leading=9.5, textColor=MUTED)
BODY = ParagraphStyle("BODY", fontName="V", fontSize=8, leading=10, textColor=TEXT, alignment=TA_LEFT)
BODY_S = ParagraphStyle("BODY_S", fontName="V", fontSize=7.5, leading=9, textColor=TEXT, alignment=TA_LEFT)
BOLD = ParagraphStyle("BOLD", fontName="VB", fontSize=8, leading=10, textColor=TEXT, alignment=TA_LEFT)
HEADER = ParagraphStyle("HEADER", fontName="VB", fontSize=7.5, leading=9, textColor=white, alignment=TA_LEFT)
META = ParagraphStyle("META", fontName="V", fontSize=7.5, leading=9.5, textColor=MUTED)


# --- Icon helpers ---
ICON_SIZE = "9"  # pt in <img> width/height

def icon(name: str) -> str:
    """Return <img> tag for icon (assumes /data/_icons/{name}.png)."""
    abs_path = ICON_DIR / f"{name}.png"
    if not abs_path.exists():
        return "?"
    return f'<img src="{abs_path}" width="{ICON_SIZE}" height="{ICON_SIZE}"></img>'


def bool_icon(val: str) -> str:
    """Return check or cross icon based on cell value (any non-empty = yes)."""
    if val and val.strip() and val.strip().lower() not in ("—", "-", "n/a", "brak", ""):
        return icon("check")
    return icon("cross")


def dot_icon(confidence: str) -> str:
    """Return dot icon based on confidence_wolumen (1-5)."""
    try:
        n = int(str(confidence).strip())
    except (ValueError, TypeError):
        return icon("dot-2")
    return icon(f"dot-{max(1, min(5, n))}")


# --- Flagi parser (✅ ✓ → flag-check, ⚠ → flag-warn, 🐋 → flag-whale, 🔴 → flag-red, 🟢 → flag-green, 💎 → flag-diamond) ---
FLAG_MAP = {
    "✅": "flag-check",
    "✓": "flag-check",
    "✔": "flag-check",
    "⚠": "flag-warn",
    "⚠️": "flag-warn",
    "🐋": "flag-whale",
    "🔴": "flag-red",
    "🟢": "flag-green",
    "💎": "flag-diamond",
    "💠": "flag-diamond",
}


def parse_flagi(text: str) -> str:
    """Convert flagi text into icon-rich paragraph HTML."""
    if not text:
        return "—"
    # Truncate raw text BEFORE injecting <img> tags (avoids splitting tags)
    if len(text) > 60:
        text = text[:57] + "…"
    # Replace known flags with icons
    out = []
    for ch in text:
        if ch in FLAG_MAP:
            out.append(icon(FLAG_MAP[ch]))
        else:
            out.append(ch)
    s = "".join(out)
    return s or "—"


# --- Column renderers ---
def col_firma(row: dict) -> str:
    """Company name (bolder) + ID + kategoria code (A1, A2, B3 etc.) below."""
    name = row.get("nazwa_firmy", "").strip()
    fid = row.get("id", "").strip()
    kat = row.get("kategoria", "").strip()  # e.g. "A1", "A4", "B8"
    parts = []
    if name:
        parts.append(f'<font size="9"><b>{name}</b></font>')
    if fid:
        parts.append(f'<font color="#4466aa" size="7.5">{fid}</font>')
    if kat:
        # Kategoria badge — kolorowe tło nie jest dozwolone, więc bold + kolor
        parts.append(f'<font color="#1F1F1F" size="8"><b>{kat}</b></font>')
    return "<br/>".join(parts) or "—"


def col_miasto(row: dict) -> str:
    """City + address (short) + WWW on a new line — 3-in-1 column."""
    miasto = row.get("miasto", "").strip()
    adres = row.get("adres", "").strip()
    www = row.get("www", "").strip()
    parts = []
    if miasto:
        parts.append(f'<b>{miasto}</b>')
    if adres:
        # Skrócony adres (tylko pierwszy człon przed przecinkiem)
        adres_short = adres.split(",")[0].strip() if "," in adres else adres
        parts.append(f'<font color="#888" size="7.5">{adres_short}</font>')
    if www:
        www_clean = www.replace("https://", "").replace("http://", "").rstrip("/")
        parts.append(f'<font color="#4466aa" size="7.5">{www_clean}</font>')
    if not parts:
        return "—"
    # Single space between lines (already <br/>)
    return "<br/>".join(parts)


def col_www(row: dict) -> str:
    www = row.get("www", "").strip()
    if not www:
        return ""
    www_clean = www.replace("https://", "").replace("http://", "").rstrip("/")
    return www_clean or ""


def col_email_tel(row: dict) -> str:
    """DEPRECATED — merged into col_kontakt."""
    email = row.get("email", "").strip()
    tel = row.get("telefon", "").strip()
    parts = []
    if email:
        parts.append(email)
    if tel:
        parts.append(f'<font color="#888" size="7">{tel}</font>')
    return "<br/>".join(parts) or "—"


def col_kontakt(row: dict) -> str:
    """Decydent + stanowisko + email_decydent + email firmy + telefon — 5 sub-rows."""
    dec = row.get("decydent", "").strip()
    stn = row.get("stanowisko", "").strip()
    email_dec = row.get("email_decydent", "").strip()
    email = row.get("email", "").strip()
    tel = row.get("telefon", "").strip()
    parts = []
    if dec:
        parts.append(f'<b>{dec}</b>')
    if stn:
        parts.append(f'<font color="#888" size="7">{stn}</font>')
    if email_dec:
        ico = bool_icon(email_dec)
        parts.append(f'{ico} <font size="7">{email_dec}</font>')
    elif dec:
        ico = icon("cross")
        parts.append(f'{ico} <font color="#aaa" size="7">brak emailu decydenta</font>')
    if email:
        parts.append(f'<font size="7">{email}</font>')
    if tel:
        parts.append(f'<font color="#666" size="7">{tel}</font>')
    return "<br/>".join(parts) or "—"


def col_email_decydent(row: dict) -> str:
    """DEPRECATED — merged into col_kontakt. Kept as fallback."""
    email = row.get("email_decydent", "").strip()
    ico = bool_icon(email)
    if email:
        return f'{ico} {email}'
    return f"{ico} <font color='#aaa'>brak</font>"


def col_social(row: dict) -> str:
    """One column with 4 sub-rows (LinkedIn/FB/IG/TikTok)."""
    platforms = [
        ("LinkedIn", row.get("linkedin", "")),
        ("Facebook", row.get("facebook", "")),
        ("Instagram", row.get("instagram", "")),
        ("TikTok", row.get("tiktok", "")),
    ]
    lines = []
    for name, val in platforms:
        ico = bool_icon(val)
        lines.append(f'{ico} <font size="6.5">{name}</font>')
    return "<br/>".join(lines)


def col_marki(row: dict) -> str:
    marki = row.get("marki_nabijarki", "").strip()
    sourcing = row.get("sourcing", "").strip()
    parts = []
    if marki:
        parts.append(marki)
    if sourcing:
        parts.append(f'<font color="#888" size="6.5">{sourcing}</font>')
    return "<br/>".join(parts) or "—"


def col_wolumen(row: dict) -> str:
    wol = row.get("wolumen", "").strip() or "—"
    conf = row.get("confidence_wolumen", "")
    ico = dot_icon(conf)
    return f"{ico} <b>{wol}</b>"


def col_tier(row: dict) -> str:
    """Tier (top) + empty line + Wolumen z dot (bottom) — visually separated."""
    tier = row.get("tier", "").strip()
    wol = row.get("wolumen", "").strip()
    conf = row.get("confidence_wolumen", "")
    parts = []
    if tier:
        parts.append(tier)
    if wol:
        # Empty line separator (visually separates tier from wolumen)
        ico = dot_icon(conf)
        parts.append('&nbsp;')  # empty line
        parts.append(f'{ico} <b>{wol}</b>')
    if not parts:
        return "—"
    return "<br/>".join(parts)


def col_kanal(row: dict) -> str:
    k = row.get("kanal_sprzedaży", "").strip() or "—"
    return k


def col_flagi(row: dict) -> str:
    """DEPRECATED — flags column removed in v11 portrait mode."""
    return parse_flagi(row.get("flagi", ""))


def col_rozmiar(row: dict) -> str:
    """Company size (rynek_skala): 'bardzo duży' / 'duży' / 'średni' / 'mały'."""
    r = row.get("rynek_skala", "").strip()
    if not r:
        return "—"
    # Map to bold + small caption
    return f'<b>{r}</b>'


def col_notatki(row: dict) -> str:
    n = row.get("notatki", "").strip()
    if not n:
        return "—"
    # Truncate very long notes
    if len(n) > 140:
        n = n[:137] + "…"
    return f'<font size="6.8">{n}</font>'


def _sanitize_unicode(text: str) -> str:
    """Replace unicode chars not in Verdana (arrows, emoji) with ASCII equivalents.
    Prevents empty squares (□) in PDF.
    """
    if not text:
        return text
    replacements = {
        '→': '->',  # right arrow
        '←': '<-',  # left arrow
        '↑': '^',   # up arrow
        '↓': 'v',   # down arrow
        '⚠': '!',   # warning
        '✅': 'OK', # green check
        '✓': 'OK',  # check
        '✗': 'X',   # cross
        '🐋': 'WHALE',  # whale (high confidence)
        '🔍': 'Q',  # magnifying glass
        '🔴': 'R',  # red circle
        '🟡': 'Y',  # yellow circle
        '🟢': 'G',  # green circle
    }
    for u, a in replacements.items():
        text = text.replace(u, a)
    return text


# --- v11.5: 3-row mini-block per lead, bolder name (11pt VB), 6 leads/page ---
# Each lead = 4 cols × 3 rows structure (with horizontal+vertical merges):
#
# Row 1 (4 cells): [Firma+ID+Kat] | [Lokalizacja+WWW] | [Kontakt]        | [Kanał + Wolumen ●]
# Row 2 (3 cells): [Marki+Sourcing — SPANS 2 rows] | [Email firmy + Tel] | [Email decydent ✓/✗]
# Row 3 (2 cells): [Notatka — SPANS 3 cells (cols 0+1+2)]              | [Tier]
#
# Row 1 = 4 cols. Row 2 = 3 cols (one spans 2 cells). Row 3 = 2 cells (Notatka spans 3 horizontally).
LEAD_COL_WIDTHS = [4.5, 4.0, 3.5, 7.0]  # cm — sum 19.0cm, 0.5cm margins × 2 = 20.0cm usable
assert abs(sum(LEAD_COL_WIDTHS) - 19.0) < 0.5, f"sum: {sum(LEAD_COL_WIDTHS)}"


def build_lead_block(r: dict, tight: bool = False) -> Table:
    """3-row × 4-col mini-table per lead (v11.5).
    v11.5: bolder name (11pt Verdana Bold), visible box (1.0pt border), 6 leads/page.
    Notatka in row 3 spans 3 cells (cols 0+1+2). Wider, less wasted space.
    - Row 1: 4 cells (Firma | Lokalizacja+WWW | Kontakt | Kanał+Wolumen)
    - Row 2: 3 cells (Marki-spans-2 | Email firmy+Tel | Email decydent)
    - Row 3: 2 cells (Notatka-spans-3 | Tier)
    tight: True = padding 2/2 (compacter, for PL with many leads, no PageBreak needed)
    """
    # === Col 0 (row 1: Firma; rows 2-3: Marki+Sourcing spans 2 cells) ===
    firma_html = (
        f'<font size="11"><b>{_sanitize_unicode(r.get("nazwa_firmy", "").strip() or "—")}</b></font>'
        f'<br/><font color="#4466aa" size="7.5">{_sanitize_unicode(r.get("id", "").strip())}</font>'
        f'<br/><font color="#1F1F1F" size="8"><b>{_sanitize_unicode(r.get("kategoria", "").strip())}</b></font>'
    )
    marki = _sanitize_unicode(r.get("marki_nabijarki", "").strip()) or "—"
    sourcing = _sanitize_unicode(r.get("sourcing", "").strip())
    marki_html = (
        f'{marki}'
        + (f'<br/><font color="#888" size="7.5">{sourcing}</font>' if sourcing else "")
    )

    # === Col 1 (row 1: Lokalizacja; row 2: Email firmy + Tel; row 3: Notatka spans) ===
    miasto = _sanitize_unicode(r.get("miasto", "").strip())
    adres = _sanitize_unicode(r.get("adres", "").strip())
    www = r.get("www", "").strip()
    adres_short = adres.split(",")[0].strip() if "," in adres else adres
    www_clean = www.replace("https://", "").replace("http://", "").rstrip("/") if www else ""
    lok_html = (
        f'<b>{miasto or "—"}</b>'
        + (f'<br/><font color="#888" size="7.5">{adres_short}</font>' if adres_short else "")
        + (f'<br/><font color="#4466aa" size="7.5">{www_clean}</font>' if www_clean else "")
    )
    email = _sanitize_unicode(r.get("email", "").strip()) or "—"
    tel = _sanitize_unicode(r.get("telefon", "").strip()) or "—"
    email_tel_html = f'{email}<br/><br/><font color="#666" size="7.5">{tel}</font>'

    # === Col 2 (row 1: Kontakt; row 2: Email decydent; row 3: Notatka spans) ===
    dec = _sanitize_unicode(r.get("decydent", "").strip())
    stn = _sanitize_unicode(r.get("stanowisko", "").strip())
    kontakt_html = (
        f'<b>{dec or "—"}</b>'
        + (f'<br/><font color="#888" size="7.5">{stn}</font>' if stn else "")
    )
    email_dec = _sanitize_unicode(r.get("email_decydent", "").strip())
    if email_dec:
        ico_dec = bool_icon(email_dec)
        email_dec_html = f'{ico_dec} {email_dec}'
    else:
        ico_dec = icon("cross")
        email_dec_html = f'{ico_dec} <font color="#aaa" size="7.5">brak emailu decydenta</font>'

    # === Col 3 (row 1: Kanał + Wolumen; row 3: Tier) ===
    kanal = _sanitize_unicode(r.get("kanal_sprzedaży", "").strip()) or "—"
    wol = _sanitize_unicode(r.get("wolumen", "").strip()) or "—"
    conf = r.get("confidence_wolumen", "")
    ico = dot_icon(conf)
    kanal_wol_html = f'{kanal}<br/><br/>{ico} <b>{wol}</b>'
    tier = _sanitize_unicode(r.get("tier", "").strip()) or "—"

    # === Notatka — teraz w row 3 spanning 3 cells (cols 0+1+2) ===
    notatki_raw = r.get("notatki", "").strip() or "—"
    # Sanitize unicode chars not in Verdana (→, emoji, etc.) — render as ASCII
    notatki = _sanitize_unicode(notatki_raw)

    # === 3×4 data structure ===
    data = [
        # Row 0 (4 cells)
        [
            Paragraph(firma_html, BODY),
            Paragraph(lok_html, BODY),
            Paragraph(kontakt_html, BODY),
            Paragraph(kanal_wol_html, BODY),
        ],
        # Row 1 (3 cells: Marki-spans-2 | Email firmy+Tel | Email decydent)
        [
            Paragraph(marki_html, BODY),
            Paragraph(email_tel_html, BODY),
            Paragraph(email_dec_html, BODY),
            "",  # empty
        ],
        # Row 2 (2 cells: Notatka-spans-3 | Tier)
        [
            Paragraph(f'<font size="7.5" color="#888"><b>Notatka:</b></font> {notatki}', BODY),
            "",  # spanned — Notatka
            "",  # spanned — Notatka
            Paragraph(f'<font color="#888" size="7.5">Tier:</font><br/>{tier}', BODY),
        ],
    ]

    tbl = Table(data, colWidths=[w * cm for w in LEAD_COL_WIDTHS])
    pad = 2 if tight else 3
    tbl.setStyle(TableStyle([
        # SPANs
        ('SPAN', (0, 1), (0, 2)),  # Marki spans rows 1+2
        ('SPAN', (0, 2), (2, 2)),  # Notatka spans cols 0+1+2 in row 2
        # Vertical alignment
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        # Padding (ciasne dla 6 leadów/stronę, jeszcze ciaśniej dla tight)
        ('LEFTPADDING', (0, 0), (-1, -1), pad),
        ('RIGHTPADDING', (0, 0), (-1, -1), pad),
        ('TOPPADDING', (0, 0), (-1, -1), pad),
        ('BOTTOMPADDING', (0, 0), (-1, -1), pad),
        # Borders — visible box around each lead
        ('BOX', (0, 0), (-1, -1), 1.0, ACCENT),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, LINE),
        # Light grey bg for Notatka row
        ('BACKGROUND', (0, 2), (2, 2), HexColor("#F4F4F4")),
    ]))
    return tbl


# --- Legacy (kept for backward compat) ---
HEADERS = [
    "Firma", "Lokalizacja", "Kontakt", "Marki",
    "Tier / Wolumen", "Kanał", "Notatki"
]

RENDERERS = {
    "Firma": col_firma,
    "Lokalizacja": col_miasto,
    "Kontakt": col_kontakt,
    "Marki": col_marki,
    "Tier / Wolumen": col_tier,
    "Kanał": col_kanal,
    "Notatki": col_notatki,
}

COL_WIDTHS = [3.2, 2.9, 3.0, 2.2, 1.9, 1.2, 2.6]


def load_catalog(iso: str, kraj_dir: str, b_max_cat: str = "B9") -> dict:
    """Load catalog-A and catalog-B separately. Returns {"A": [rows], "B": [rows]}.
    b_max_cat: max B-category to keep in B (e.g. "B4" = keep B1-B4 only, move B5-B9 to extra list).
    """
    sections = {"A": [], "B": []}
    for cat in ("A", "B"):
        path = PROJECT_ROOT / "data" / kraj_dir / f"catalog-{cat}-{iso}.csv"
        if not path.exists():
            print(f"⚠️  Missing: {path}")
            continue
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                # Skip empty rows
                if not r.get("id"):
                    continue
                # For B catalog: filter by category if b_max_cat set
                if cat == "B" and b_max_cat != "B9":
                    kategoria = r.get("kategoria", "").strip()
                    if kategoria > b_max_cat:
                        # Skip — this row goes to extra list
                        continue
                sections[cat].append(r)
    return sections


def load_b_outside_range(iso: str, b_max_cat: str = "B4") -> list[dict]:
    """Load B-catalog rows with kategoria > b_max_cat (e.g. B5-B9 when max is B4).
    These are 'verified but outside the displayed B range' — for PL list-extended mode.
    """
    from pathlib import Path as _P
    kraj_dir = COUNTRY_DIRS.get(iso)
    if not kraj_dir:
        return []
    path = PROJECT_ROOT / "data" / kraj_dir / f"catalog-B-{iso}.csv"
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r.get("id"):
                continue
            kategoria = r.get("kategoria", "").strip()
            if kategoria > b_max_cat:
                out.append(r)
    return out


def load_extra_leads(iso: str) -> list[dict]:
    """Load web-researched extra leads (50 new PL records from web search 2026-08-19).
    Returns list of dicts, normalized to fields used by build_extra_simple_block.
    Skips if no extra-leads file exists for the country.
    """
    from pathlib import Path as _P
    kraj_dir = COUNTRY_DIRS.get(iso)
    if not kraj_dir:
        return []
    extra_path = PROJECT_ROOT / "data" / kraj_dir / f"extra-leads-{iso}.csv"
    if not extra_path.exists():
        return []
    out = []
    with open(extra_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize: ensure all expected fields exist
            norm = {
                "id": row.get("id", "").strip(),
                "kategoria": row.get("kategoria", "").strip(),
                "nazwa_firmy": row.get("nazwa_firmy", "").strip(),
                "kraj": iso,
                "miasto": row.get("miasto", "").strip(),
                "adres": row.get("adres", "").strip(),
                "www": row.get("www", "").strip(),
                "email": row.get("email", "").strip(),
                "telefon": row.get("telefon", "").strip(),
                "tier": row.get("tier", "").strip(),
                "wolumen": row.get("wolumen", "").strip(),
                "kanal_sprzedaży": row.get("kanal_sprzedaży", "").strip(),
                "powinowactwo_nabijarki": row.get("powinowactwo_nabijarki", "").strip(),
                "notatki": row.get("notatki", "").strip(),
                "zrodlo_danych": row.get("zrodlo_danych", "").strip(),
                "data_weryfikacji": row.get("data_weryfikacji", "").strip(),
                "flagi": row.get("flagi", "").strip(),
                "nip_vat": row.get("nip_vat", "").strip(),
                "rejestr_id": row.get("rejestr_id", "").strip(),
            }
            out.append(norm)
    return out


def load_unverified(iso: str, limit: int = 20) -> list[dict]:
    """Load unverified leads from gmaps raw data, dedup by name, exclude master.csv, max `limit`.
    Returns list of dicts: [{nazwa_firmy, miasto, www, telefon, adres, source_file}, ...]
    """
    import glob as _glob
    from collections import OrderedDict

    # Master.csv for dedup
    m_path = PROJECT_ROOT / "data" / "master.csv"
    master_names: set[str] = set()
    if m_path.exists():
        with open(m_path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                n = r.get("nazwa_firmy", "").strip().lower()
                if n:
                    master_names.add(n)

    # Find gmaps files for this ISO
    intake_dir = PROJECT_ROOT / "data" / "_intake" / "gmaps" / "processed"
    pattern = str(intake_dir / f"gmaps_search_*{iso}*.csv")
    files = sorted(_glob.glob(pattern))

    seen: "OrderedDict[str, dict]" = OrderedDict()
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    if r.get("kraj", "").strip() != iso:
                        continue
                    name = r.get("nazwa_firmy", "").strip()
                    if not name or len(name) < 3:
                        continue
                    name_l = name.lower()
                    if name_l in master_names:
                        continue
                    www = r.get("www", "").strip()
                    tel = r.get("telefon", "").strip()
                    if not www and not tel:
                        continue
                    if name_l in seen:
                        continue
                    seen[name_l] = {
                        "nazwa_firmy": name,
                        "miasto": r.get("miasto", "").strip(),
                        "adres": r.get("adres", "").strip(),
                        "www": www,
                        "telefon": tel,
                        "source_file": f.split("/")[-1],
                    }
                    if len(seen) >= limit:
                        break
        except Exception as e:
            print(f"⚠️  {f}: {e}")
        if len(seen) >= limit:
            break

    return list(seen.values())


# Section titles (Polish)
SECTION_TITLES = {
    "A": ("Katalog A", "Dystrybutorzy maszynek do nabijania"),
    "B": ("Katalog B", "Branża tytoniowa — cross-sell"),
    "C": ("Katalog C", "Sygnały z gmaps — DO-WERYFIKACJI"),
}


def build_leads_table(rows: list[dict]) -> Table:
    data = [[Paragraph(h, HEADER) for h in HEADERS]]
    for r in rows:
        row_cells = []
        for h in HEADERS:
            cell_html = RENDERERS[h](r)
            row_cells.append(Paragraph(cell_html, BODY))
        data.append(row_cells)

    tbl = Table(data, colWidths=[w * cm for w in COL_WIDTHS], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, 0), 4),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#FAFAFA")]),
    ]))
    return tbl


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(1.0*cm, PAGE_H - 1.0*cm, PAGE_W - 1.0*cm, PAGE_H - 1.0*cm)
    canvas.setFont("V", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(1.0*cm, PAGE_H - 0.85*cm, "BILLS Sp. z o.o.  ·  Dystrybucja PowerMatic & Hawk")
    canvas.drawRightString(PAGE_W - 1.0*cm, PAGE_H - 0.85*cm, "Katalog leadów B2B/B2C")
    canvas.line(1.0*cm, 1.0*cm, PAGE_W - 1.0*cm, 1.0*cm)
    canvas.setFont("V", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(1.0*cm, 0.85*cm, "BILLS Sp. z o.o.  ·  Ostrzeszów  ·  serwis@bills.pl")
    canvas.drawRightString(PAGE_W - 1.0*cm, 0.85*cm, f"v11.5 · 18.08.2026 · Strona {doc.page}")
    canvas.restoreState()


def build_section_title(iso: str, cat: str, rows: list[dict]) -> list:
    """Returns a list of Paragraphs/Spacers forming a section title block."""
    title, subtitle = SECTION_TITLES[cat]
    out = []
    out.append(Paragraph(
        f'<font size="16"><b>{title}</b></font>'
        f'<font color="#666" size="10">  ·  {subtitle}</font>',
        ParagraphStyle("H_SECTION", fontName="VB", fontSize=16, leading=20, textColor=TEXT, spaceBefore=2, spaceAfter=2)
    ))
    # Stats line — different for Katalog C (unverified)
    if cat == "C":
        a_count = len(rows)
        # Collect unique source files
        sources = sorted({r.get("source_file", "") for r in rows if r.get("source_file")})
        src_str = ", ".join(sources[:2]) + ("…" if len(sources) > 2 else "")
        out.append(Paragraph(
            f'<font color="#cc6600" size="8"><i>{a_count} sygnałów · źródło: gmaps 2026-08-13/14 · DO-WERYFIKACJI</i></font>',
            ParagraphStyle("H_SUB", fontName="VI", fontSize=8, leading=11, textColor=MUTED, spaceAfter=4)
        ))
    else:
        a_count = len(rows)
        a_frozen = sum(1 for r in rows if "FROZEN" in r.get("flagi", ""))
        a_dower = a_count - a_frozen
        out.append(Paragraph(
            f'<font color="#888" size="8"><i>{a_count} firm · {a_frozen} FROZEN · {a_dower} DO-WER</i></font>',
            ParagraphStyle("H_SUB", fontName="VI", fontSize=8, leading=11, textColor=MUTED, spaceAfter=4)
        ))
    out.append(Spacer(1, 4))
    return out


def build_unverified_block(r: dict, idx: int) -> Table:
    """1-row compact table for unverified lead (gmaps signal).
    Columns: [#] [⚠️] [Nazwa | Miasto] [WWW] [Tel]
    No border (just thin line below), compact font, warning icon.
    """
    name = r.get("nazwa_firmy", "").strip() or "—"
    miasto = r.get("miasto", "").strip() or r.get("adres", "").split(",")[0].strip() or "—"
    www = r.get("www", "").strip()
    www_clean = www.replace("https://", "").replace("http://", "").rstrip("/") if www else "—"
    tel = r.get("telefon", "").strip() or "—"

    UNVERIFIED_BODY = ParagraphStyle(
        "UNV", fontName="V", fontSize=8, leading=10, textColor=TEXT
    )
    UNVERIFIED_BODY_GREY = ParagraphStyle(
        "UNV_GREY", fontName="V", fontSize=7.5, leading=9, textColor=MUTED
    )
    UNVERIFIED_BODY_LINK = ParagraphStyle(
        "UNV_LINK", fontName="V", fontSize=7.5, leading=9, textColor=HexColor("#4466aa")
    )

    data = [[
        Paragraph(f'<font color="#888"><b>{idx:02d}</b></font>', UNVERIFIED_BODY),
        Paragraph(f'<font size="13" color="#cc6600"><b>●</b></font>', UNVERIFIED_BODY),
        Paragraph(
            f'<b>{name}</b><br/><font color="#888" size="7">{miasto[:60]}</font>',
            UNVERIFIED_BODY
        ),
        Paragraph(
            f'<font color="#4466aa">{www_clean[:50]}</font>' if www != "—" else f'<font color="#aaa">—</font>',
            UNVERIFIED_BODY_LINK
        ),
        Paragraph(f'<font color="#666">{tel}</font>', UNVERIFIED_BODY_GREY),
    ]]
    # Column widths: 0.6 + 0.5 + 8.5 + 6.0 + 3.4 = 19.0cm
    col_widths = [0.6, 0.5, 8.5, 6.0, 3.4]
    tbl = Table(data, colWidths=[w * cm for w in col_widths])
    tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Thin line below each row (not a full box — differentiate from Katalog A/B)
        ('LINEBELOW', (0, 0), (-1, -1), 0.3, HexColor("#CCCCCC")),
    ]))
    return tbl


def build_extra_simple_block(r: dict, idx: int) -> Table:
    """6-col block: [#] [Nazwa] [Contact (email/tel)] [URL] [Typ/Skala] [Notatka]
    Used for PL list-extended mode (B5-B9 + gmaps, no warning box).
    Column 5: tier + wolumen for master firms; miasto for gmaps signals.
    Column 6: short notatka (master) or types (gmaps) or NIP/REGON if available.
    """
    name = _sanitize_unicode(r.get("nazwa_firmy", "").strip()) or "—"
    email = _sanitize_unicode(r.get("email", "").strip()) or _sanitize_unicode(r.get("email_decydent", "").strip())
    tel = _sanitize_unicode(r.get("telefon", "").strip())
    contact_parts = []
    if email:
        contact_parts.append(email)
    if tel:
        contact_parts.append(tel)
    contact = "\n".join(contact_parts) if contact_parts else "—"

    www = r.get("www", "").strip()
    www_clean = www.replace("https://", "").replace("http://", "").rstrip("/") if www else "—"

    # Col 5: typ sprzedawcy + skala (or miasto for gmaps)
    kategoria = r.get("kategoria", "").strip()
    tier = r.get("tier", "").strip()
    wolumen = r.get("wolumen", "").strip()
    if kategoria and tier:
        typ_html = f'<font color="#4466aa"><b>{kategoria}</b></font><br/><font color="#888" size="7">{tier} · {wolumen or "—"}</font>'
    elif r.get("miasto"):
        typ_html = f'<font color="#888">{_sanitize_unicode(r.get("miasto", "").strip())}</font>'
    else:
        typ_html = f'<font color="#aaa">—</font>'

    # Col 6: short notatka (master) or types (gmaps) — first 80 chars max
    notatka_raw = r.get("notatki", "").strip()
    gmaps_types = r.get("types", "").strip()
    nip = r.get("nip_vat", "").strip()
    rejestr = r.get("rejestr_id", "").strip()

    if notatka_raw:
        # Truncate to first sentence or 80 chars
        notatka_clean = _sanitize_unicode(notatka_raw)
        # Cut at first sentence if possible
        for sep in ['. ', ' | ', ' — ']:
            if sep in notatka_clean:
                notatka_clean = notatka_clean.split(sep)[0] + '.'
                break
        if len(notatka_clean) > 80:
            notatka_clean = notatka_clean[:77] + "…"
        notatka_html = f'<font color="#555" size="7">{notatka_clean}</font>'
    elif gmaps_types:
        # Gmaps: show types (e.g. "tobacco_shop, wholesaler")
        types_clean = _sanitize_unicode(gmaps_types)[:60]
        notatka_html = f'<font color="#888" size="7" fontstyle="italic">{types_clean}</font>'
    elif nip or rejestr:
        # Fallback: show NIP/REGON as short id
        ids = []
        if nip:
            ids.append(_sanitize_unicode(nip))
        if rejestr:
            ids.append(_sanitize_unicode(rejestr))
        notatka_html = f'<font color="#888" size="7">{" / ".join(ids)[:30]}</font>'
    else:
        notatka_html = f'<font color="#aaa" size="7">—</font>'

    SIMPLE_BODY = ParagraphStyle(
        "SIMP", fontName="V", fontSize=8, leading=10, textColor=TEXT
    )
    SIMPLE_BODY_GREY = ParagraphStyle(
        "SIMP_GREY", fontName="V", fontSize=7.5, leading=9, textColor=MUTED
    )
    SIMPLE_BODY_LINK = ParagraphStyle(
        "SIMP_LINK", fontName="V", fontSize=7.5, leading=9, textColor=HexColor("#4466aa")
    )

    data = [[
        Paragraph(f'<font color="#888"><b>{idx}</b></font>', SIMPLE_BODY),
        Paragraph(f'<b>{name}</b>', SIMPLE_BODY),
        Paragraph(contact.replace("\n", "<br/>"), SIMPLE_BODY_GREY),
        Paragraph(
            f'<font color="#4466aa">{www_clean[:35]}</font>' if www_clean != "—" else f'<font color="#aaa">—</font>',
            SIMPLE_BODY_LINK
        ),
        Paragraph(typ_html, SIMPLE_BODY_GREY),
        Paragraph(notatka_html, SIMPLE_BODY_GREY),
    ]]
    # Column widths: 0.9 + 4.8 + 3.6 + 3.5 + 2.6 + 3.6 = 19.0cm
    # 6-col layout: [# | Nazwa | Kontakt | URL | Typ/Skala | Notatka]
    # # column widened to 0.9cm so 3-digit numbers (e.g. 116) don't break
    col_widths = [0.9, 4.8, 3.6, 3.5, 2.6, 3.6]
    tbl = Table(data, colWidths=[w * cm for w in col_widths])
    tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        # Thin line below each row
        ('LINEBELOW', (0, 0), (-1, -1), 0.3, HexColor("#CCCCCC")),
    ]))
    return tbl


def build_leads_pdf(iso: str, country: str, sections: dict, unverified: list[dict], out_tmp: str,
                    extra_mode: str = "unverified", extra_label: str | None = None,
                    tight_layout: bool = False) -> int:
    """Build leads PDF to a temp file. v11.5: max 6 leads/page + extra list.

    extra_mode:
      - "unverified" (default): gmaps signals with warning box, 20/stronę, 5-col block
      - "simple": simple 3-col block (name + contact + URL), more per page, no warning
    extra_label: override section title (e.g. "Lista dodatkowa")
    tight_layout: True = padding 2/2 + no PageBreak (KeepTogether, natural flow, fewer empty pages).
                  Recommended for countries with many leads (e.g. PL with 162).
    """
    doc = SimpleDocTemplate(
        out_tmp, pagesize=A4,
        leftMargin=0.5*cm, rightMargin=0.5*cm,
        topMargin=1.0*cm, bottomMargin=1.0*cm,
        title=f"Leads — {country}",
        author="BILLS Sp. z o.o.",
    )
    story = []
    # NO top "Leads — {country}" title — section titles (Katalog A, Katalog B, ...) provide context

    # Each section — force max 6 leads per page (v11.5)
    LEADS_PER_PAGE = 6
    spacer = Spacer(1, 2) if tight_layout else Spacer(1, 4)
    for cat in ("A", "B"):
        rows = sections[cat]
        if not rows:
            continue
        # Section title
        for el in build_section_title(iso, cat, rows):
            story.append(el)
        # Each lead — visible separator between results
        for i, r in enumerate(rows):
            lead_block = build_lead_block(r, tight=tight_layout)
            if tight_layout:
                # KeepTogether ensures lead block is not split across pages
                story.append(KeepTogether(lead_block))
            else:
                story.append(lead_block)
            # Page break after every 6 leads (force 6/page) — only in non-tight mode
            if not tight_layout:
                if (i + 1) % LEADS_PER_PAGE == 0 and (i + 1) < len(rows):
                    story.append(PageBreak())
                elif i < len(rows) - 1:
                    story.append(spacer)
            elif i < len(rows) - 1:
                story.append(spacer)
        # Spacer between sections
        story.append(Spacer(1, 8))

    # === Extra list (gmaps unverified + optionally B-out-of-range) ===
    if unverified:
        # Force new page
        story.append(PageBreak())
        # Section title (with optional override label)
        if extra_label:
            # Use a custom title block
            story.append(Paragraph(
                f'<font size="16"><b>{extra_label}</b></font>'
                f'<font color="#666" size="10">  ·  Rozszerzona lista kontaktów</font>',
                ParagraphStyle("H_EXTRA", fontName="VB", fontSize=16, leading=20, textColor=TEXT, spaceBefore=2, spaceAfter=2)
            ))
            story.append(Paragraph(
                f'<font color="#888" size="8"><i>{len(unverified)} firm · firmy z rozszerzonej bazy (B5-B9 + sygnały gmaps + web search 2026-08-19)</i></font>',
                ParagraphStyle("H_EXTRA_SUB", fontName="VI", fontSize=8, leading=11, textColor=MUTED, spaceAfter=4)
            ))
            story.append(Spacer(1, 4))
        else:
            for el in build_section_title(iso, "C", unverified):
                story.append(el)
            # Warning box (only in unverified mode)
            if extra_mode == "unverified":
                story.append(Paragraph(
                    '<font color="#cc6600" size="8"><b>⚠ DO-WERYFIKACJI</b></font> '
                    '<font color="#888" size="7.5">— sygnały z Google Maps, brak weryfikacji KRS/CEIDG/VIES. '
                    'Wymagają pełnej weryfikacji przed kontaktem.</font>',
                    ParagraphStyle("UNV_WARN", fontName="VI", fontSize=8, leading=10, textColor=MUTED, spaceAfter=4)
                ))
        # Render each entry
        if extra_mode == "simple":
            for i, r in enumerate(unverified):
                story.append(build_extra_simple_block(r, i + 1))
        else:
            for i, r in enumerate(unverified):
                story.append(build_unverified_block(r, i + 1))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)

    # Count pages
    from pypdf import PdfReader
    return len(PdfReader(out_tmp).pages)


def append_to_pdf(main_pdf: Path, leads_pdf: Path, out_pdf: Path) -> int:
    """Append leads_pdf pages to main_pdf, write to out_pdf (atomic via temp)."""
    import shutil
    reader_main = PdfReader(str(main_pdf))
    reader_leads = PdfReader(str(leads_pdf))
    writer = PdfWriter()
    for page in reader_main.pages:
        writer.add_page(page)
    for page in reader_leads.pages:
        writer.add_page(page)
    # Write to temp then move (avoids in-place corruption)
    tmp_out = out_pdf.with_suffix(".pdf.tmp")
    with open(tmp_out, "wb") as f:
        writer.write(f)
    shutil.move(str(tmp_out), str(out_pdf))
    return len(reader_leads.pages)


# --- Country configs (must mirror pdf_gen_country.py) ---
COUNTRY_DIRS = {
    "PL": "Polska", "CZ": "Czechy", "SK": "Słowacja", "SI": "Słowenia",
    "HR": "Chorwacja", "BG": "Bułgaria", "RO": "Rumunia", "MD": "Mołdawia",
    "LT": "Litwa", "LV": "Łotwa", "EE": "Estonia", "FR": "Francja",
}

COUNTRY_NAMES = {
    "PL": "Polska", "CZ": "Czechy", "SK": "Słowacja", "SI": "Słowenia",
    "HR": "Chorwacja", "BG": "Bułgaria", "RO": "Rumunia", "MD": "Mołdawia",
    "LT": "Litwa", "LV": "Łotwa", "EE": "Estonia", "FR": "Francja",
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--iso", required=True, choices=list(COUNTRY_DIRS.keys()))
    p.add_argument("--unverified-limit", type=int, default=20, help="Max unverified leads to append (default: 20)")
    p.add_argument("--b-max-cat", default=None, help="Max B-category to keep in Katalog B (e.g. B4). PL uses B4 by default.")
    args = p.parse_args()

    iso = args.iso
    kraj_dir = COUNTRY_DIRS[iso]
    country = COUNTRY_NAMES[iso]
    pdf_path = PROJECT_ROOT / "data" / kraj_dir / f"PDF-{iso}.pdf"

    if not pdf_path.exists():
        print(f"❌ {pdf_path} not found. Run first: python3 tools/pdf_gen_country.py --iso {iso}")
        sys.exit(1)

    # PL uses extended mode: Katalog B = B1-B4 only, B5-B9 go to extra list
    pl_extended = (iso == "PL")
    b_max_cat = args.b_max_cat or ("B4" if pl_extended else "B9")

    sections = load_catalog(iso, kraj_dir, b_max_cat=b_max_cat)
    total = sum(len(sections[k]) for k in ("A", "B"))
    if total == 0:
        print(f"❌ No leads found for {iso}")
        sys.exit(1)

    # Extra list:
    #  - PL: B5-B9 from master (verified but out of B range) + gmaps unverified
    #  - Other: gmaps unverified (with warning)
    if pl_extended:
        b_outside = load_b_outside_range(iso, b_max_cat="B4")
        gmaps = load_unverified(iso, limit=args.unverified_limit)
        extra_web = load_extra_leads(iso)  # Web-researched 50 new leads
        # Dedupe: B5-B9 may overlap with gmaps names (e.g. company in master and gmaps)
        master_names = {r.get("nazwa_firmy", "").strip().lower() for r in b_outside}
        gmaps_filtered = [r for r in gmaps if r.get("nazwa_firmy", "").strip().lower() not in master_names]
        # Dedupe web extra against B5-B9 and gmaps
        existing = master_names | {r.get("nazwa_firmy", "").strip().lower() for r in gmaps_filtered}
        extra_web_filtered = [r for r in extra_web if r.get("nazwa_firmy", "").strip().lower() not in existing]
        extra_list = b_outside + gmaps_filtered + extra_web_filtered
        extra_mode = "simple"
        extra_label = "Lista dodatkowa"
    else:
        extra_list = load_unverified(iso, limit=args.unverified_limit)
        extra_mode = "unverified"
        extra_label = None

    print(f"📋 {iso} ({country}): A={len(sections['A'])}, B={len(sections['B'])}, extra={len(extra_list)} (mode={extra_mode})")

    # Build leads PDF to temp
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        leads_tmp = tmp.name
    try:
        # PL uses tight_layout (smaller padding, no forced PageBreak) to minimize empty pages
        tight = pl_extended
        n_pages = build_leads_pdf(iso, country, sections, extra_list, leads_tmp,
                                   extra_mode=extra_mode, extra_label=extra_label,
                                   tight_layout=tight)
        print(f"📄 Leads PDF: {n_pages} page(s) → {leads_tmp} (tight={tight})")

        # Merge: main + leads
        n_appended = append_to_pdf(pdf_path, Path(leads_tmp), pdf_path)
        print(f"✅ Appended {n_appended} page(s) to {pdf_path}")
        print(f"📦 Final: {pdf_path} ({pdf_path.stat().st_size//1024} KB)")
    finally:
        Path(leads_tmp).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
