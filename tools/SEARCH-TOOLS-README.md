# Search Tools (added 2026-09-03)

These four tools address the bottlenecks found during the 12-country gentle
search session. Run `python3 tools/<name>.py --help` for full options.

## 1. `dedup_check.py` — Pre-flight dedup

Stops you from re-researching companies already in master.csv, gems-NON-PL.csv,
or any per-country catalog. Always run before adding a new lead.

```bash
python3 tools/dedup_check.py --name "Tabák Plus" --nip "63489821" --country CZ
# → EXACT_CZ-A-010 (master.csv)
#   exit 1
python3 tools/dedup_check.py --name "Acme Tobacco" --country PL
# → NEW (exit 0)
```

What it checks:
- Exact NIP match (handles CZ/MD/PL/etc. prefix stripping)
- Exact name match (diacritic-insensitive)
- Fuzzy token overlap ≥ 70%

Searches:
- `data/master.csv`
- `data/gems-NON-PL.csv`
- `data/<Country>/catalog-A-{CC}.csv`
- `data/<Country>/catalog-B-{CC}.csv`
- `data/<Country>/extra-leads-{CC}.csv`

## 2. `score_powinowactwo.py` — Deterministic powinowactwo scoring

Replaces ad-hoc guesswork with a rule-based score (1-5) for the
`powinowactwo_nabijarki` field. Apply BEFORE adding a new lead to master.csv.

```bash
python3 tools/score_powinowactwo.py --name "POGON KOOLTURA" --text "MAŠINICE filter omotnice cigarete" --nace 46350
# → score=4 rule=ROLLER+ACCESSORY
```

Score rules (priority order):
- **5** = ROLLER: explicit rolling-machine token in name or marki
- **4** = ROLLER+ACCESSORY: above + gilzy/filtry/papierki
- **3** = NACE 4635: tobacco wholesale (in NACE/CAEN code or in text)
- **2** = NACE_GENERAL_TOBACCO: NACE 12 / 47.26 / 4639 / default
- **1** = ADJACENT: e-sig / snus / pouches / FMCG / cash&carry

Caveats:
- `marki_nabijarki` field is authoritative for ROLLER detection.
- `notatki` text is used for NACE detection (so "CAEN 4635" in notatki gives 3).
- Negative-context patterns filter out commentary like
  "raczej niski" / "nie oferuje" / "prawdopodobnie niezwiązane z" / "adjacent".

## 3. `registry_lookup.py` — Unified registry lookup

Free public-registry lookups for 9 countries. **Registry-first** workflow:
look up NIP/IČO first, then web_search for assortment.

```bash
python3 tools/registry_lookup.py --country CZ --ico 63489821
# → Tabák Plus, Brno, NACE 46350, founded 1996

python3 tools/registry_lookup.py --country LT --ja-kodas 303182002
# → Hordus, UAB, founded 2013-11-06

python3 tools/registry_lookup.py --country EE --name "Stimbar" --autocomplete

python3 tools/registry_lookup.py --country SK --ico 53070992
# → NO_API (returns manual URL fallback)
```

| Country | API source                              | Status   |
|---------|-----------------------------------------|----------|
| CZ      | ARES (ares.gov.cz)                       | ✅ live  |
| EE      | ARIREGISTER (ariregister.rik.ee)        | ✅ live  |
| LT      | get.data.gov.lt (JAR)                    | ✅ live  |
| SK      | orsr.sk (no API, web search)             | 🔁 manual |
| LV      | info.ur.gov.lv (no API)                  | 🔁 manual |
| RO      | termene.ro / listafirme.ro (no API)      | 🔁 manual |
| HR      | sudreg.pravosudje.hr (no API)            | 🔁 manual |
| BG      | companybook.bg (no API)                  | 🔁 manual |
| SI      | ajpes.si (no API)                        | 🔁 manual |
| RS      | companywall.rs (no API)                  | 🔁 manual |
| MD      | infobiz.md (no API)                      | 🔁 manual |

## 4. `parallel_country_search.py` — Batch parallel lookup

Runs multiple registry lookups in parallel threads. Use for batch dedup
or batch verification of 20+ leads.

```bash
python3 tools/parallel_country_search.py --batch candidates.json --workers 16
```

Input JSON:
```json
[
  {"country": "CZ", "ico": "63489821", "name": "Tabák Plus"},
  {"country": "LT", "ja_kodas": "303182002", "name": "Hordus"},
  {"country": "HR", "name": "POGON KOOLTURA d.o.o."}
]
```

Speed: 5 lookups in 0.6s (vs ~5s sequential).

## Recommended workflow

```bash
# Step 1: dedup
python3 tools/dedup_check.py --name "$FIRMA" --nip "$NIP" --country "$CC"
# (exits 0 = new, 1 = duplicate)

# Step 2: registry lookup (if API supported)
python3 tools/registry_lookup.py --country "$CC" --id "$NIP"
# (returns full name/address/NACE for CZ/EE/LT)

# Step 3: web_search for assortment
# (looking for "MAŠINICE" / "nabijarka" / "plnička" / "rolling machine")

# Step 4: score
python3 tools/score_powinowactwo.py --name "$FIRMA" --text "$TEXT" --nace "$NACE" --marki "$MARKI"

# Step 5: append to master.csv + frontend mirror
```

## Remaining gaps

- **SK, LV, RO, HR, BG, SI, RS, MD**: no free public API. For these, fall
  back to `registry_lookup.py` (which returns the manual URL) + a follow-up
  `web_search "site:<url> <query>"` to scrape the registry page.
- **ONRC (Romania)**: paywalled. Certificat Constatator 79 RON (paid).
- **Lursoft (Latvia)**: paywalled. Public data is sparse.
- **AJPES (Slovenia)**: public maticna.posta.si is paginated HTML.

For each country, the priority is to **discover the official tobacco-license
registry** (e.g. MZ dovoljenja in SI, duvan.gov.rs in RS, gov.pl in PL) before
general web search — these are authoritative and free.
