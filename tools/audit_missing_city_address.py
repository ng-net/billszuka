"""Audit: list ids missing miasto or adres (active catalog files only)."""
import csv, os

ROOT = '/Users/ciepolml/Documents/Bills-Drive/BILLSzuka-28-Aug/data'
SENTINELS = {'', 'brak', 'n/a', 'do weryfikacji', 'do ustalenia', '—'}

missing = []  # (country, id, name, www, miasto, adres)
for root, _, files in os.walk(ROOT):
    if '.snapshots' in root:
        continue
    for f in files:
        if not f.startswith('catalog-B-') or not f.endswith('.csv'):
            continue
        path = os.path.join(root, f)
        country = os.path.basename(root)
        with open(path, encoding='utf-8') as fh:
            r = csv.DictReader(fh)
            rows = list(r)
        for row in rows:
            miasto = (row.get('miasto') or '').strip()
            adres = (row.get('adres') or '').strip()
            if miasto.lower() in SENTINELS or adres.lower() in SENTINELS:
                missing.append((country, row.get('id',''), row.get('nazwa',''),
                                row.get('www',''), miasto, adres))

print(f'TOTAL rows needing fill: {len(missing)}')
print()
# Group by country
from collections import defaultdict
by_country = defaultdict(list)
for m in missing:
    by_country[m[0]].append(m)
for country in sorted(by_country):
    print(f'=== {country} ({len(by_country[country])} rows) ===')
    for c, id_, name, www, miasto, adres in by_country[country]:
        m_flag = '[M]' if miasto.lower() in SENTINELS else '   '
        a_flag = '[A]' if adres.lower() in SENTINELS else '   '
        print(f'  {m_flag}{a_flag} {id_:14s} {www:40s}  {name[:50]}')
    print()