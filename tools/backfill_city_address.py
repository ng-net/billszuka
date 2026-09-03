"""tools/backfill_city_address.py — One-shot backfill of miasto + adres.

Strategy per missing row:
  1. Country-specific public registry API by company name (CZ/EE/PL)
  2. WebFetch the company's www URL and try imprint subpages
  3. Crawl homepage to find contact links (kontakt, imprint, kontakta, ...)
  4. Regex-extract city + street from the imprint block

Aggregator pages (europages, kompass, rekvizitai, vatrenishop, etc.) are
skipped — those are search-result pages, not company pages, and have no
single canonical address per row.

Stdlib only — deterministic, no LLM, no Gemini calls (anti-hallucination).
Atomic CSV write (csv_path.tmp + os.replace).
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.registry_lookup import (  # type: ignore
    lookup_cz_autocomplete,
    lookup_ee,
)

USER_AGENT = "BILLSzuka-Research/1.0 (Marceli; bills@op.pl)"

SENTINELS = {'', 'brak', 'n/a', 'do weryfikacji', 'do ustalenia', '—'}

COUNTRY_ISO = {
    'Polska': 'PL', 'Czechy': 'CZ', 'Słowacja': 'SK', 'Chorwacja': 'HR',
    'Bułgaria': 'BG', 'Estonia': 'EE', 'Francja': 'FR', 'Litwa': 'LT',
    'Łotwa': 'LV', 'Mołdawia': 'MD', 'Rumunia': 'RO', 'Serbia': 'RS',
    'Słowenia': 'SI',
}

AGGREGATOR_DOMAINS = (
    'europages.', 'kompass.', 'rekvizitai.', 'vatrenishop.',
    'business1.', 'panoram.', 'panoramafirm', 'pkt.pl', 'raptorsupplies',
    'moodiedavittreport', 'csd.eu/fileadmin', 'volza.com',
    'health.ec.europa.eu/document', 'vatrenishop',
)

# Comprehensive imprint/contact subpages to probe
IMPRINT_PATHS = (
    '/impressum', '/imprint', '/impressum-legal', '/legal-notice',
    '/kontakt', '/kontakty', '/kontakta', '/kontakte',
    '/contact', '/contacts', '/contact-us',
    '/o-firmie', '/o-nama', '/about', '/about-us', '/o-nas',
    '/footer', '/podmienky', '/pravne-informacije', '/pravni-informacije',
    '/legal', '/company', '/company-info', '/kontaktinformation',
    '/pobocky', '/predajne', '/kamenne-prodejny',
    '/obchodni-rejstrik', '/firemni-informace',
    '/impresszum', '/cegunkorunk',
    # English/PL/CZ/etc homepage anchors that often ARE the contact
)

# Specific patterns for imprint blocks. Ordered from most specific to loosest.
ADDRESS_PATTERNS = [
    # CZ: "Nové sady 606/40, 602 00 Brno" or "Sídlo: Brno, Šumavská 15"
    (re.compile(
        r'(?P<street>[A-ZÁČĎÉĚÍŇÓŘŠŤÚÝŽ][A-Za-zÁáČčĎďÉéĚěÍíŇňÓóŘřŠšŤťÚúÝýŽž0-9\.\-\s]+?\s+\d+[A-Za-z0-9/\-]*)'
        r',?\s*(?P<psc>\d{3}\s?\d{2})\s+(?P<city>[A-ZÁČĎÉĚÍŇÓŘŠŤÚÝŽ][A-Za-záčďéěíňóřšťúúýž\.\-\s]{1,40})',
        re.UNICODE), 'CZ_PSC'),
    # PL: "ul. Słoneczna 12, 00-001 Warszawa" or "ulica Słoneczna 12 00-001 Warszawa"
    (re.compile(
        r'(?:ul\.|ulica|ulicu|ulicy|Ulica|ulice|ulicí)?\s*'
        r'(?P<street>[A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż0-9\.\-\s]+?\s+\d+[A-Za-z0-9/\-]*)'
        r',?\s*(?P<psc>\d{2}-\d{3})\s+(?P<city>[A-ZĄĆĘŁŃÓŚŹŻ][A-Za-ząćęłńóśźż\.\-\s]{1,40})',
        re.UNICODE), 'PL_PSC'),
    # Generic EU "Street H, PSC City" (DE/AT: PLZ Stadt)
    (re.compile(
        r'(?P<street>[A-ZÀ-Ž][A-Za-zÀ-ž0-9\.\-\s]+?\s+\d+[A-Za-z0-9/\-]*)'
        r',?\s*(?P<psc>\d{4,5})\s+(?P<city>[A-ZÀ-Ž][A-Za-zÀ-ž\.\-\s]{1,40})',
        re.UNICODE), 'EU_PSC'),
    # "Sídlo: Brno" / "Address: Brno" / "Centrála: Praha"
    (re.compile(
        r'(?:Sídlo|Sidlo|Adresa|Address|Siedziba|Headquarters|Centrála|Centrala|Kontakt|Adres|Betriebsanschrift)'
        r'\s*[:\-–]\s*(?:'
        r'(?P<street>[A-ZÀ-Ž][A-Za-zÀ-ž0-9\.\-\s]{2,50}?\s+\d+[A-Za-z0-9/\-]*)\s*[,\n]?\s*'
        r'(?P<psc>\d{2}-\d{3}|\d{3}\s?\d{2}|\d{4,5})?\s*'
        r'(?P<city>[A-ZÀ-Ž][A-Za-zÀ-ž\.\-\s]{2,40})'
        r')',
        re.UNICODE), 'LABEL'),
]


def http_get_text(url: str, timeout: int = 15) -> str:
    try:
        req = urllib.request.Request(url, headers={
            # Mozilla UA — many small business sites reject non-browser UAs.
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en,pl,cs,sk,hr,si,bg,ro,rs,lt,lv,ee,fr,de;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(500_000)
            ct = r.headers.get('Content-Type', '')
            charset = 'utf-8'
            if 'charset=' in ct:
                charset = ct.split('charset=', 1)[1].split(';')[0].strip()
            return data.decode(charset, errors='replace')
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return ''


def strip_html(html: str) -> str:
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def is_aggregator(url: str) -> bool:
    if not url:
        return True
    u = url.lower()
    return any(a in u for a in AGGREGATOR_DOMAINS)


def find_contact_links(html: str, base: str) -> list[str]:
    """Return absolute URLs of likely contact pages found in homepage <a href>."""
    if not html:
        return []
    seen = set()
    out = []
    # match href values
    keywords = ('kontakt', 'imprint', 'impressum', 'o-firmie', 'o-nama',
                'about', 'o-nas', 'contact', 'footer', 'pobocky', 'pravne',
                'company', 'kontakta', 'legal')
    for m in re.finditer(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE):
        href = m.group(1)
        if not href or href.startswith('#') or href.startswith('mailto:'):
            continue
        full = urllib.parse.urljoin(base, href)
        if full in seen:
            continue
        if any(kw in full.lower() for kw in keywords):
            seen.add(full)
            out.append(full)
    return out[:5]


def parse_imprint(html: str) -> dict:
    out = {'miasto': '', 'adres': '', 'confidence': 0, 'kind': ''}
    if not html:
        return out
    text = strip_html(html)

    for pat, kind in ADDRESS_PATTERNS:
        m = pat.search(text)
        if m:
            street = (m.groupdict().get('street') or '').strip().rstrip(',').strip()
            city = (m.groupdict().get('city') or '').strip()
            psc = (m.groupdict().get('psc') or '').strip()
            # Trim city: stop at common suffixes
            city = re.split(r'\s+(?:Ltd|LLC|S\.r\.o\.|s\.r\.o\.|Sp\.|GmbH|a\.s\.|d\.o\.o\.|S\.A\.|SIA|S\.r\.l\.|Inc\.?|Corp\.?|—|-{2,})\b',
                            city, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            if 2 <= len(city) <= 40:
                out['miasto'] = city
                if street:
                    out['adres'] = (f'{street}, {psc} ' if psc else street).strip()
                else:
                    out['adres'] = psc
                out['confidence'] = 2 if kind == 'CZ_PSC' or kind == 'PL_PSC' else 1
                out['kind'] = kind
                return out
    return out


def try_imprint_fetch(www: str) -> dict:
    if not www or is_aggregator(www):
        return {'miasto': '', 'adres': '', 'skipped': True}

    base = www.rstrip('/')
    best = {'miasto': '', 'adres': '', 'confidence': 0, 'kind': ''}

    # 1) Fetch homepage, find contact links from anchor tags
    home_html = http_get_text(base)
    contact_links = find_contact_links(home_html, base)

    # 2) Probe direct paths + found links
    urls_to_try = [u for u in contact_links]
    urls_to_try += [base + p for p in IMPRINT_PATHS]
    urls_to_try = list(dict.fromkeys(urls_to_try))  # dedup preserve order

    for url in urls_to_try[:10]:  # cap
        html = http_get_text(url)
        if not html:
            continue
        parsed = parse_imprint(html)
        if parsed['confidence'] > best['confidence']:
            best = parsed
        if best['confidence'] >= 2:
            break
    return best


def lookup_pl_by_name(name: str) -> dict:
    """REGON BIR1 search by name. Returns dict with miasto/adres/regon."""
    key = os.environ.get('REGON_API_KEY', 'abcde12345abcde12345')
    try:
        sid = ''
        # Login: try a SID request via raw HTTP. The response usually sets cookie.
        login_url = 'https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzworek.svc'
        login_xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
            '<soap:Body><Zaloguj xmlns="http://tempuri.org/">'
            f'<pKluczUzytkownika>{key}</pKluczUzytkownika>'
            '</Zaloguj></soap:Body></soap:Envelope>'
        ).encode('utf-8')
        req = urllib.request.Request(login_url, data=login_xml,
                                     headers={'Content-Type': 'application/soap+xml; charset=utf-8'})
        with urllib.request.urlopen(req, timeout=20) as r:
            r.read()
            for k, v in r.getheaders():
                if k.lower() == 'set-cookie' and 'sid=' in v.lower():
                    sid = v.split('=', 1)[1].split(';', 1)[0]
        if not sid:
            return {}
        # Search
        search_url = 'https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzworek.svc/ajax'
        search_xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
            '<soap:Body><DaneSzukajPodmioty xmlns="http://tempuri.org/">'
            f'<pParametryWyszukiwania><Nazwa>{name[:100]}</Nazwa></pParametryWyszukiwania>'
            '</DaneSzukajPodmioty></soap:Body></soap:Envelope>'
        ).encode('utf-8')
        req2 = urllib.request.Request(search_url, data=search_xml,
                                      headers={'Content-Type': 'application/soap+xml; charset=utf-8',
                                               'Cookie': f'sid={sid}'})
        with urllib.request.urlopen(req2, timeout=20) as r:
            resp = r.read().decode('utf-8', errors='replace')
        m_miej = re.search(r'<Miejscowosc>([^<]+)</Miejscowosc>', resp)
        m_adr = re.search(r'<Adres[^>]*>([^<]+)</Adres>', resp)
        m_regon = re.search(r'<Regon>([^<]+)</Regon>', resp)
        if not m_miej:
            return {}
        return {
            'miasto': m_miej.group(1).strip(),
            'adres': (m_adr.group(1).strip() if m_adr else ''),
            'regon': (m_regon.group(1).strip() if m_regon else ''),
        }
    except Exception:
        return {}


def registry_lookup(country_iso: str, name: str) -> dict:
    if not name or len(name) < 3:
        return {}
    try:
        if country_iso == 'CZ':
            # ARES requires IČO. Autocomplete is the placeholder; just skip.
            return {}
        if country_iso == 'EE':
            hits = lookup_ee(name=name)
            if isinstance(hits, list) and hits:
                return {'reg_code': hits[0].get('registry_code', '')}
            return {}
        if country_iso == 'PL':
            return lookup_pl_by_name(name)
        return {}
    except Exception:
        return {}


def backfill(country_dir: str, country_iso: str, csv_path: Path, dry_run: bool = False,
             verbose: bool = False) -> dict:
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        header = reader.fieldnames or []
    if 'miasto' not in header or 'adres' not in header:
        return {'file': str(csv_path), 'skipped': 'no miasto/adres columns'}

    stats = {'file': str(csv_path), 'filled': 0, 'miasto_filled': 0, 'adres_filled': 0,
             'registry_hits': 0, 'webfetch_hits': 0, 'aggregator_skipped': 0,
             'still_missing': 0}

    updates = []
    for idx, row in enumerate(rows):
        cur_m = (row.get('miasto') or '').strip()
        cur_a = (row.get('adres') or '').strip()
        need_m = cur_m.lower() in SENTINELS
        need_a = cur_a.lower() in SENTINELS
        if not need_m and not need_a:
            continue
        name = (row.get('nazwa') or '').strip()
        www = (row.get('www') or '').strip()

        miasto = ''
        adres = ''
        src_parts = []

        # 1) Registry
        if country_iso in ('EE', 'PL') and name:
            reg = registry_lookup(country_iso, name)
            if need_m and reg.get('miasto'):
                miasto = reg['miasto']
            if need_a and reg.get('adres'):
                adres = reg['adres']
            if reg.get('miasto') or reg.get('adres') or reg.get('reg_code') or reg.get('regon'):
                stats['registry_hits'] += 1
                src_parts.append(f'REG:{country_iso}')

        # 2) WebFetch
        fetched = try_imprint_fetch(www)
        if fetched.get('skipped'):
            stats['aggregator_skipped'] += 1
        else:
            if need_m and not miasto and fetched.get('miasto'):
                miasto = fetched['miasto']
            if need_a and not adres and fetched.get('adres'):
                adres = fetched['adres']
            if fetched.get('miasto') or fetched.get('adres'):
                stats['webfetch_hits'] += 1
                if verbose:
                    print(f'  [fetch] {row.get("id")} → {fetched.get("kind")} {fetched.get("miasto")!r}')
                src_parts.append('WEB:imprint')

        if (miasto and miasto.lower() not in SENTINELS) or (adres and adres.lower() not in SENTINELS):
            updates.append((idx, miasto, adres, ', '.join(src_parts)))
            if need_m and miasto and miasto.lower() not in SENTINELS:
                stats['miasto_filled'] += 1
            if need_a and adres and adres.lower() not in SENTINELS:
                stats['adres_filled'] += 1
            stats['filled'] += 1
        else:
            stats['still_missing'] += 1

    if not updates or dry_run:
        return stats

    for idx, miasto, adres, src in updates:
        if (rows[idx].get('miasto') or '').strip().lower() in SENTINELS and miasto:
            rows[idx]['miasto'] = miasto
        if (rows[idx].get('adres') or '').strip().lower() in SENTINELS and adres:
            rows[idx]['adres'] = adres
        existing = (rows[idx].get('zrodlo_danych') or '').strip()
        rows[idx]['zrodlo_danych'] = (f'{existing}; {src}' if existing else src)

    tmp = csv_path.with_suffix(csv_path.suffix + '.tmp')
    with open(tmp, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, csv_path)

    return stats


def main():
    data_dir = ROOT / 'data'
    all_stats = []
    for country_dir in sorted(p for p in data_dir.iterdir() if p.is_dir()):
        if country_dir.name in ('verification', '.snapshots'):
            continue
        country_iso = COUNTRY_ISO.get(country_dir.name)
        if not country_iso:
            continue
        for csv_path in sorted(country_dir.glob('catalog-B-*.csv')):
            try:
                stats = backfill(country_dir.name, country_iso, csv_path, verbose=False)
                all_stats.append(stats)
            except Exception as e:
                all_stats.append({'file': str(csv_path), 'error': str(e)})

    print(json.dumps(all_stats, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()