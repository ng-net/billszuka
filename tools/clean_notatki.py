#!/usr/bin/env python3
"""
tools/clean_notatki.py — Clean `notatki` column across BILLSzuka catalogs.

Goals (per Marceli 2026-08-18):
  1. Strip structured source/audit metadata that belongs in zrodlo_danych / flagi, not notatki:
       orig_uzasadnienie, orig_uwagi, orig_next, Status źródłowy,
       user_orig_priorytet, user_orig_score, user_orig_segment,
       renamed, l1, tier-fix
  2. Strip emoji-only flags (✅🐋, 🐋🔍, etc.) — already in `flagi` column.
  3. Remove duplicates and noise from free-form text (extra whitespace, "| . |" artifacts).
  4. Migrate useful data from notatki → other columns WHEN the target cell is empty:
       - decydent ← "Dział X: [Name]"
       - marki_nabijarki ← "dystrybutor [BRAND1, BRAND2]" if brand ∈ canonical list
       - miasto ← "siedziba/magazyn w [City]" if not in current miasto
       - wolumen ← "Sieć X+ sklepów" / "X+ sklepów" (X≥20→średni, X≥100→duży)
       - kanal_sprzedaży ← "sklep stacjonarny"/"e-commerce"/"hurtownia" hints
       - rok_zalozenia ← "Rejestracja YYYY" / "aktywna od YYYY"
  5. Keep only NEW information in notatki (anything not already in any other column).

Usage:
    python3 tools/clean_notatki.py --dry-run          # report only, no writes
    python3 tools/clean_notatki.py --apply            # write changes to all files
    python3 tools/clean_notatki.py --apply --file F   # only one file (testing)
"""

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# ---------- Source/audit metadata keys to strip from notatki ----------
STRUCTURED_KEYS = {
    'orig_uzasadnienie', 'orig_uwagi', 'orig_next',
    'user_orig_priorytet', 'user_orig_score', 'user_orig_segment',
    'renamed', 'l1', 'tier-fix'
}
# "Status źródłowy" is multi-word, handled separately

# Canonical brand list (from methodology)
CANONICAL_BRANDS = {
    'powermatic', 'hawk', 'topomat', 'gm', 'turbomatic', 'dark horse',
    'fern', 'ocb', 'mascotte', 'champ', 'gerui', 'matteo', 'angel',
    'atomic', 'premier', 'c77', 'cartel', 'rollo', 'imperator',
    'raw', 'bonggo', 'dopalenia', 'dym', 'don pealo', 'ggtabak',
    'smok', 'voopoo', 'aspire', 'vaporesso', 'doctorvape',
    'powersmoke', 'easysmoke', 'belet', 'bletki'
}

# ---------- Regex patterns for migration ----------
RE_DZIAL_NAME = re.compile(
    r'Dział\s+eksportu:\s*'
    r'([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+'
    r'(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)+)'
)
RE_SIEDZIBA = re.compile(
    r'siedziba\s+([A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻ\-]+(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻ\-]+)*)'
    r'\s*\(([A-ZĄĆĘŁŃÓŚŹŻ][A-ZĄĆĘŁŃÓŚŹŻ]+)\)'  # optional (REGION_UPPER)
)
RE_MAGAZYN = re.compile(r'magazyn(?:em)?\s+w\s+([A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻ\-]+)')
RE_SIEC = re.compile(r'(?:Sieć|sieć)\s+(\d+)\s*\+?\s*sklep')
RE_SKLEPOW = re.compile(r'(\d+)\s*\+?\s*sklep[ówow]?\b')
RE_REJESTRACJA = re.compile(r'(?:Rejestracja|aktywna od|Zarejestrowana)\s+(\d{4})(?:[-/]\d{2}(?:[-/]\d{2})?)?')
RE_BRAND_LIST = re.compile(
    r'(?:Dystrybutor|dystrybutor|oferuje|sprzedaje|asortyment(?:em)?)\s+'
    r'((?:[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+'
    r'(?:\s+(?:[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+|i|oraz|/|&))?'
    r'){1,6})'
)
RE_KANAL_HINT = re.compile(
    r'\b(sklep(?:y)?\s+stacjonarn(?:y|ych)|hurtownia|e-?commerce|marketplace|sklep\s+online)\b',
    re.IGNORECASE
)

# Word-boundary check for canonical brand (avoid partial matches)
def find_canonical_brands(text):
    """Find canonical brand names in text, return list of properly-cased ones."""
    found = []
    text_lower = text.lower()
    for brand in CANONICAL_BRANDS:
        # Word boundary: must not be part of larger word
        pattern = r'(?<![a-ząćęłńóśźż])' + re.escape(brand) + r'(?![a-ząćęłńóśźż])'
        if re.search(pattern, text_lower):
            # Preserve original casing from text (or canonical if not present)
            m = re.search(r'(?i)(?<![a-ząćęłńóśźż])' + re.escape(brand) + r'(?![a-ząćęłńóśźż])', text)
            if m:
                found.append(m.group(0))
            else:
                found.append(brand.title() if len(brand) > 3 else brand.upper())
    return list(dict.fromkeys(found))  # dedupe, preserve order


# ---------- Notatki cleanup ----------

def is_emoji_only(s):
    """True if string contains only emojis / whitespace / pipe-separators."""
    stripped = re.sub(
        r'[\s\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF'
        r'\u2600-\u27BF\u2700-\u27BF'
        r'⚠️✅❌🐋💎🔍🔴🟡🟢📦⛔]|',
        '', s
    )
    return len(stripped) == 0


def parse_pipe_parts(n):
    """Split by | but respect single/double quotes."""
    parts = []
    current = ''
    in_quote = False
    quote_char = None
    for c in n:
        if c in ("'", '"') and not in_quote:
            in_quote = True
            quote_char = c
            current += c
        elif c == quote_char and in_quote:
            in_quote = False
            quote_char = None
            current += c
        elif c == '|' and not in_quote:
            if current.strip():
                parts.append(current.strip())
            current = ''
        else:
            current += c
    if current.strip():
        parts.append(current.strip())
    return parts


def is_structured_part(part):
    """True if part is one of the source/audit key:value pairs to strip."""
    # Multi-word keys
    if part.startswith('Status źródłowy:'):
        return True
    if part.startswith('orig_'):
        return True
    if part.startswith('user_orig_'):
        return True
    if part.startswith('renamed:'):
        return True
    if part.startswith('l1:'):
        return True
    if part.startswith('tier-fix:'):
        return True
    return False


def strip_structured(notatki):
    """Remove all structured source/audit parts. Return free-form text only."""
    if not notatki:
        return ''
    parts = parse_pipe_parts(notatki)
    freeform = [p for p in parts if not is_structured_part(p)]
    return ' | '.join(freeform).strip()


def clean_whitespace(s):
    """Normalize whitespace and remove pipe artifacts."""
    if not s:
        return ''
    # Remove multiple spaces
    s = re.sub(r'  +', ' ', s)
    # Remove empty segments around pipes: " | foo | " → "foo"
    s = re.sub(r'(?:\|\s*){2,}', '| ', s)
    s = re.sub(r'^\s*\|\s*', '', s)
    s = re.sub(r'\s*\|\s*$', '', s)
    # Remove leftover leading " | " in compound sentences
    s = re.sub(r'\s*\|\s+', ' | ', s)
    return s.strip()


# ---------- Column-aware deduplication ----------

# Common tokens to look for in notatki and strip if duplicate
PATTERN_NIP = re.compile(r'\b(?:NIP|NIP[::]?)\s*(?:PL)?\s*(\d{10})\b', re.IGNORECASE)
PATTERN_KRS = re.compile(r'\b(?:KRS|KRS[::]?)\s*(\d{6,10})\b', re.IGNORECASE)
PATTERN_KRS_API = re.compile(r'\bKRS\s+API[::]?\s*\d{6,10}\b', re.IGNORECASE)
PATTERN_REGON = re.compile(r'\bREGON\s+(\d{14})\b', re.IGNORECASE)
PATTERN_SIEDZIBA = re.compile(r'siedziba\s+([A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻ\-]+(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻ\-]+)*)\s*(\([^)]+\))?', re.IGNORECASE)
PATTERN_MAGAZYN = re.compile(r'magazyn(?:em)?\s+w\s+([A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻ\-]+)')

REGION_CODES = {
    # PL województwa
    'DOLNOŚLĄSKIE', 'KUJAWSKO-POMORSKIE', 'LUBELSKIE', 'LUBUSKIE',
    'ŁÓDZKIE', 'MAŁOPOLSKIE', 'MAZOWIECKIE', 'OPOLSKIE',
    'PODKARPACKIE', 'PODLASKIE', 'POMORSKIE', 'ŚLĄSKIE',
    'ŚWIĘTOKRZYSKIE', 'WARMIŃSKO-MAZURSKIE', 'WIELKOPOLSKIE', 'ZACHODNIOPOMORSKIE',
    # EE maakond (county) — these are regions, not cities
    'HARJU MAAKOND', 'TARTU MAAKOND', 'VÕRU MAAKOND', 'PÄRNU MAAKOND',
    'IDA-VIRU MAAKOND', 'LÄÄNE-VIRU MAAKOND', 'JÄRVA MAAKOND', 'JÕGEVA MAAKOND',
    'PÕLVA MAAKOND', 'RAPLA MAAKOND', 'SAARE MAAKOND', 'HIIU MAAKOND',
    'LÄÄNE MAAKOND', 'VALGA MAAKOND', 'VILJANDI MAAKOND'
}


def dedupe_against_columns(notatki, row):
    """Remove information from notatki that already exists in other columns.
    Only removes obvious duplicate tokens (NIPs, KRS, REGON, cities) — not free text.
    Country-aware: only applies PL-specific dedup to PL rows.
    """
    if not notatki:
        return notatki

    n = notatki
    kraj = row.get('kraj', '').strip().upper()
    is_pl = kraj == 'PL'
    is_ee = kraj == 'EE'

    # 1. NIP — match "NIP 1234567890" with word boundaries
    # PL-only: 10-digit NIP, format "NIP 1234567890"
    if is_pl:
        nip = re.sub(r'[^0-9]', '', row.get('nip_vat', ''))
        if nip and len(nip) >= 10:
            nip10 = nip[-10:]
            # Strip optional "(?:NIP ... )" label
            n = re.sub(
                r',?\s*'
                r'(?:NIP[::]?\s*)?'
                r'(?:PL\s*)?'
                + re.escape(nip10)
                + r'(?!\d)',
                '',
                n,
                flags=re.IGNORECASE
            )
    # EE-specific: strip "KMKR EE100722880" (VAT number with EE prefix)
    if is_ee:
        nip = re.sub(r'[^0-9]', '', row.get('nip_vat', ''))
        if nip and len(nip) >= 8:
            # Strip "KMKR EE12345678" or "VAT EE12345678"
            n = re.sub(
                r',?\s*'
                r'(?:KMKR|VAT)\s*\(?VAT\)?\s*EE\s*' + re.escape(nip)
                + r'(?!\d)',
                '',
                n,
                flags=re.IGNORECASE
            )

    # 2. KRS — match "KRS 123456" or "KRS: 123456"
    # ONLY for Polish companies (KRS is PL-specific)
    is_pl = row.get('kraj', '').strip().upper() == 'PL'
    krs = re.sub(r'[^0-9]', '', row.get('rejestr_id', '')) if is_pl else ''
    if krs and len(krs) >= 6:
        # Match any number with at least the suffix digits
        n = re.sub(
            r',?\s*'
            r'(?:KRS[::]?\s*)?'
            r'0*' + re.escape(krs[-7:])  # 7 digits to be safe
            + r'(?!\d)',
            '',
            n,
            flags=re.IGNORECASE
        )

    # 3. KRS API — match "KRS API: 123456" with full label and value
    if krs and len(krs) >= 6:
        n = re.sub(
            r',?\s*'
            r'KRS\s+API[::]?\s*'
            r'0*' + re.escape(krs[-7:])
            + r'(?!\d)',
            '',
            n,
            flags=re.IGNORECASE
        )

    # 4. REGON — match "REGON 12345678901234"
    n = re.sub(r',?\s*REGON\s+\d{14}(?!\d)', '', n, flags=re.IGNORECASE)

    # 5. Region codes in parentheses — strip " (LUBELSKIE)"
    for rc in REGION_CODES:
        n = re.sub(r'\s*\(\s*' + rc + r'\s*\)', '', n, flags=re.IGNORECASE)

    # 6. Miasto — strip "siedziba [CITY]" if matches
    miasto = row.get('miasto', '').strip()
    if miasto and len(miasto) > 2:
        # Extract first word of miasto (handles "Smolec (k. Wrocławia)" → "Smolec")
        miasto_first = re.split(r'\s*\(', miasto)[0].strip()
        miasto_first_esc = re.escape(miasto_first)
        # Strip "siedziba [CITY]" (case-insensitive, word boundary)
        n = re.sub(
            r'[,.]?\s*'
            r'siedziba\s+' + miasto_first_esc + r'\b',
            '',
            n,
            flags=re.IGNORECASE
        )
        # Strip "w [CITY]" for "magazyn w [city]"
        n = re.sub(
            r'magazyn(?:em)?\s+w\s+' + miasto_first_esc + r'\b',
            'magazyn',
            n,
            flags=re.IGNORECASE
        )

    # 7. Phone numbers — strip "608 023 300" or "608023300"
    telefon = re.sub(r'[^0-9+]', '', row.get('telefon', ''))
    if telefon and len(telefon) >= 9:
        last9 = telefon[-9:]
        # Find all 9+ digit runs
        for m in re.finditer(r'\b\d{9,}\b', n):
            digits = re.sub(r'\D', '', m.group(0))
            if len(digits) >= 9 and digits[-9:] == last9:
                # Remove this whole occurrence, including surrounding spaces
                n = (n[:m.start()] + n[m.end():]).strip()
                break
        # Also try formatted (with spaces)
        formatted = ' '.join(last9[i:i+3] for i in range(0, 9, 3))
        if formatted in n:
            n = n.replace(formatted, '')

    # Cleanup
    # Strip orphan labels (e.g., "KRS API:" with no value after it)
    n = re.sub(r'^KRS\s+API[::]?\s*', '', n, flags=re.IGNORECASE)
    n = re.sub(r'\s*,\s*,\s*', ', ', n)
    n = re.sub(r'\s*\(\s*\)', '', n)
    n = re.sub(r'^\s*[,;]\s*', '', n)
    n = re.sub(r'\s*[,;]\s*$', '', n)
    n = re.sub(r'\s*\|\s*$', '', n)
    n = re.sub(r'^\s*\|\s*', '', n)
    n = re.sub(r'\s*\|\s*\|\s*', ' | ', n)
    n = re.sub(r'\s{2,}', ' ', n)
    # Strip leading punctuation/whitespace (but not trailing period — it's sentence punctuation)
    n = re.sub(r'^[\s,;.\-]+', '', n)
    n = n.rstrip()  # only strip trailing whitespace
    return n.strip()

def migrate_from_notatki(row, notatki):
    """Try to fill empty cells in other columns from notatki content.
    Returns (migrations_list, remaining_notatki).
    """
    migrations = []
    n = notatki

    # 1. decydent ← "Dział eksportu: [Name]"
    if not row.get('decydent', '').strip():
        m = RE_DZIAL_NAME.search(n)
        if m:
            name = m.group(1).strip()
            # Remove the matched portion from notatki
            n = (n[:m.start()] + n[m.end():]).strip()
            n = re.sub(r'\s*\|\s*\|\s*', ' | ', n)
            migrations.append(('decydent', name))

    # 2. miasto ← "siedziba [City]" or "magazyn w [City]"
    if not row.get('miasto', '').strip():
        m = RE_SIEDZIBA.search(n)
        if m:
            city = m.group(1).strip()
            n = (n[:m.start()] + n[m.end():]).strip()
            n = re.sub(r'\s*\|\s*\|\s*', ' | ', n)
            migrations.append(('miasto', city))
        else:
            m = RE_MAGAZYN.search(n)
            if m:
                city = m.group(1).strip()
                n = (n[:m.start()] + n[m.end():]).strip()
                n = re.sub(r'\s*\|\s*\|\s*', ' | ', n)
                migrations.append(('miasto', city))

    # 3. rok_zalozenia ← "Rejestracja YYYY" / "aktywna od YYYY"
    if not row.get('rok_zalozenia', '').strip():
        m = RE_REJESTRACJA.search(n)
        if m:
            year = m.group(1)
            n = (n[:m.start()] + n[m.end():]).strip()
            n = re.sub(r'\s*\|\s*\|\s*', ' | ', n)
            migrations.append(('rok_zalozenia', year))

    # 4. marki_nabijarki ← canonical brands found in notatki
    if not row.get('marki_nabijarki', '').strip():
        brands = find_canonical_brands(n)
        if brands:
            # Filter out brands that look like noise (e.g., "BongGo", "Dopalenia" are trade names, not nabijarki brands)
            # For marki_nabijarki we only want nabijarka brands, not vape/lifestyle brands
            nabijarka_brands = [b for b in brands if b.lower() in {
                'powermatic', 'hawk', 'topomat', 'gm', 'turbomatic', 'dark horse',
                'c77', 'cartel', 'rollo', 'imperator', 'ocb'
            }]
            if nabijarka_brands:
                migrations.append(('marki_nabijarki', ', '.join(nabijarka_brands)))

    # 5. wolumen ← "Sieć X+ sklepów"
    if not row.get('wolumen', '').strip():
        m = RE_SIEC.search(n) or RE_SKLEPOW.search(n)
        if m:
            x = int(m.group(1))
            if x >= 100:
                migrations.append(('wolumen', 'duży'))
            elif x >= 20:
                migrations.append(('wolumen', 'średni'))
            elif x >= 5:
                migrations.append(('wolumen', 'mały'))

    return migrations, n


# ---------- Per-row cleanup ----------

def clean_row(row):
    """Clean notatki + migrate data. Returns (cleaned_row, migrations_applied)."""
    original_notatki = row.get('notatki', '')
    if not original_notatki:
        return row.copy(), []

    # Step 1: strip structured metadata
    after_strip = strip_structured(original_notatki)
    after_strip = clean_whitespace(after_strip)

    # Step 2: try to migrate useful info to other columns
    # Note: we work on the stripped text so we don't migrate from a key:value field
    migrations, after_migrate = migrate_from_notatki(row, after_strip)
    after_migrate = clean_whitespace(after_migrate)

    # Step 3: column-aware dedup (only after migrations, to avoid stripping values we just migrated)
    # We use a fresh copy of row with migrations applied
    temp_row = row.copy()
    for field, value in migrations:
        if not temp_row.get(field, '').strip():
            temp_row[field] = value
    after_dedup = dedupe_against_columns(after_migrate, temp_row)
    after_dedup = clean_whitespace(after_dedup)

    # Step 4: if only emoji flag remains, drop it (it's already in `flagi`)
    if is_emoji_only(after_dedup):
        after_dedup = ''

    # Apply migrations to row copy
    new_row = row.copy()
    for field, value in migrations:
        if not new_row.get(field, '').strip():
            new_row[field] = value
    new_row['notatki'] = after_dedup
    return new_row, migrations


# ---------- File processing ----------

def process_file(path, apply=False, dry_run=False):
    """Process one CSV file. Returns list of (id, original_notatki, new_notatki, migrations)."""
    changes = []
    with path.open('r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    new_rows = []
    for r in rows:
        new_r, migrations = clean_row(r)
        new_rows.append(new_r)
        if r.get('notatki', '') != new_r.get('notatki', '') or migrations:
            changes.append({
                'id': r.get('id', ''),
                'field': r.get('nazwa_firmy', '')[:40],
                'orig_notatki': r.get('notatki', ''),
                'new_notatki': new_r.get('notatki', ''),
                'migrations': migrations,
            })

    if apply and not dry_run and changes:
        with path.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(new_rows)

    return changes


def all_catalog_files():
    """Yield (path, country_dir) for every catalog CSV in per-country folders.
    Skips .snapshots/ (auto-generated backups)."""
    for sub in sorted(DATA_DIR.iterdir()):
        if not sub.is_dir():
            continue
        if sub.name.startswith('.'):
            continue  # skip .snapshots, .verify-state, etc.
        for f in sorted(sub.glob('catalog-*.csv')):
            yield f


def main():
    p = argparse.ArgumentParser(description='Clean BILLSzuka notatki column')
    p.add_argument('--apply', action='store_true', help='Write changes (default: dry-run)')
    p.add_argument('--dry-run', action='store_true', help='Force dry-run (default if --apply not set)')
    p.add_argument('--file', help='Process only this one file (relative to project root or absolute)')
    p.add_argument('--limit', type=int, default=0, help='Show only first N changes per file')
    p.add_argument('--quiet', action='store_true', help='Less output')
    args = p.parse_args()

    apply = args.apply and not args.dry_run
    target_files = []
    if args.file:
        fp = Path(args.file)
        if not fp.is_absolute():
            fp = ROOT / fp
        target_files.append(fp)
    else:
        target_files = list(all_catalog_files())

    if not args.quiet:
        print(f"🔍 {'Apply' if apply else 'Dry-run'} — {len(target_files)} file(s)")
        print()

    total_changes = 0
    total_migrations = 0
    summary_by_file = []

    for path in target_files:
        if not path.exists():
            print(f"  ❌ Not found: {path}")
            continue
        changes = process_file(path, apply=apply, dry_run=args.dry_run)
        if not changes:
            if not args.quiet:
                print(f"  ✓ {path.relative_to(ROOT)}: no changes")
            continue

        n_migrations = sum(len(c['migrations']) for c in changes)
        total_changes += len(changes)
        total_migrations += n_migrations
        summary_by_file.append((path, len(changes), n_migrations))

        if not args.quiet:
            print(f"  ✏️  {path.relative_to(ROOT)}: {len(changes)} row(s) changed, {n_migrations} migration(s)")

        if not args.quiet and not args.quiet:
            show_n = args.limit if args.limit else min(3, len(changes))
            for c in changes[:show_n]:
                if c['migrations']:
                    mig_str = ' | '.join(f"{f}={v!r}" for f, v in c['migrations'])
                else:
                    mig_str = '-'
                o = c['orig_notatki'][:80].replace('\n', ' ')
                n = c['new_notatki'][:80].replace('\n', ' ') if c['new_notatki'] else '(empty)'
                print(f"     [{c['id']}] {c['field']}")
                print(f"       was: {o}")
                print(f"       now: {n}")
                print(f"       → migrated: {mig_str}")

    print()
    print(f"=== Summary ===")
    print(f"Files processed:      {len(target_files)}")
    print(f"Rows changed:         {total_changes}")
    print(f"Migrations applied:   {total_migrations}")
    if summary_by_file:
        for p, n, m in summary_by_file:
            print(f"  {p.relative_to(ROOT)}: {n} changed, {m} migrated")

    if not apply and total_changes > 0:
        print()
        print(f"💡 Run with --apply to write changes. Use --file X for testing first.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
