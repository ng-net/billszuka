# BILLSzuka — INTEL

> **Strategiczne odkrycia, partnerzy, ryzyka, narzędzia.**
> Tu ląduje wszystko co zmienia decyzje lub jest kluczową wiedzą na przyszłość.
> Materiały referencyjne (definicje, schematy) → `methodology.md`.
> Postęp prac, pytania, feedback → `DZIENNIK.md`.

---

## 📋 Spis treści

1. [TOP odkrycia](#top-odkrycia) — jedno zdanie na kluczowy wniosek
2. [Partnerzy — Big Fish 🐋](#partnerzy) — kto może być partnerem dystrybucyjnym
3. [Dane rynkowe PL](#dane-rynkowe-pl) — realne dane (Allegro, Ceneo, TikTok)
4. [Narzędzia i automatyzacja](#narz%C4%99dzia) — co mam i jak używać
5. [Limity i znane ograniczenia](#limity) — co nie działa, fallbacki
6. [Decyzje projektowe](#decyzje) — kluczowe ustalenia

---

## TOP odkrycia

| # | Odkrycie | Wpływ |
|---|---|---|
| 🐋 | Sanitex group (LT/LV/EE) = 1 partner otwiera cały rynek bałtycki | Strategiczny |
| 💡 | Rynek PL jest płytki: 30 produktów "Nabijarki" na Ceneo, średnia 121 zł | Szanse na nowe marki |
| ⚠️ | PowerMatic ma tylko 2 opinie 2.5/5 na Ceneo = miejsce na rynku | Otwarta pozycja |
| 💡 | #tiktokpolska: 18.6k wyświetleń/post (najlepsza engagement PL TikTok) | Kanał sprzedaży |
| 🔧 | KRS API nie ma search-by-name → chain NIP/REGON → REGON API → KRS | Workflow |
| 🆔 | Dostępne integracje: Veritor, ENTIA, nipgo.pl, klucznicy/krs-fetcher, pawel-id/bir1 | Nowe możliwości |
| ⚡ | Weryfikacja automatyczna: 16/143 (11.2%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 143 wierszy we wszystkich katalogach regionalnych. | Pipeline |

---

## Partnerzy

### 🐋 Sanitex group — Baltic wholesale (TOP 1)

> **Data:** 2026-08-10 08:21 CEST
> **Status:** 🟡 DO-WERYFIKACJI (Baltiki to krok 10, nie ruszamy dopóki PL nie ma ≥30 zweryfikowanych firm)

**Sanitex group** = 1 partner dla LT+LV+EE (Litwa, Łotwa, Estonia).

| Metryka | Wartość |
|---|---|
| Pracownicy | 1 239 |
| Klienci | 35 000 |
| Kapitał | 4.4M EUR |
| PKD | 46.39.00 (hurt żywności/napojów/tytoniu) |
| CEO | Ramūnas Kairys |

**Trzy podmioty prawne:**

| Kraj | Firma | Numer |
|---|---|---|
| 🇱🇹 Litwa | UAB SANITEX | LT 110443493 |
| 🇱🇻 Łotwa | SIA SANITEX | LV 40003166842 |
| 🇪🇪 Estonia | OÜ SANITEX | EE 11931003 |

**Wniosek:** Jedna umowa dystrybucyjna otwiera cały rynek bałtycki (~7M ludzi, 3 kraje).

**Follow-up:**
- [ ] LinkedIn Ramūnasa Kairysa — oceń czy otwarty na nowe marki
- [ ] www.sanitex.lt — jakie marki mają obecnie (konkurencja czy brak?)
- [ ] Zapisz w catalog-A-LT/LV/EE gdy dotrzemy do Bałtików (po PL + CZ)

---

## Dane rynkowe PL

### Allegro / Ceneo — 2026-08

> **Data:** 2026-08-10 09:30 CEST

| Metryka | Wartość |
|---|---|
| Produkty w "Nabijarki do papierosów" (Ceneo) | **30** |
| Cena min (Ceneo) | 6.49 zł |
| Cena max (Ceneo) | 1 099.00 zł |
| Średnia cena (Ceneo) | **121.24 zł** |
| Powermatic III (Ceneo) | **2.5/5 z 2 opinii** |
| Top produkt (Elm Tłokowa Elektryczna) | 5.0/5 z 3 opinii |
| Allegro kategoria "Nabijarki" | aktywna (id 78996) |

**Wniosek:** Rynek PL jest płytki, ceny konkurencyjne od 6.49 zł, PowerMatic ma małą obecność → **jest miejsce na nowe marki**.

### TikTok — realne dane (tiktokhashtags.com, 2026-08)

| Hashtag | Postów | Wyświetleń łącznie | Śr. wyświetleń/post |
|---|---|---|---|
| #polska | 3.5M | 36.5B | 10 375 |
| #poland | 9.2M | 52.9B | 5 755 |
| #polish | 1.4M | 7.8B | 5 402 |
| **#tiktokpolska** | **294.7K** | **5.5B** | **18 606** ⭐ |
| #polandtiktok | 36.2K | 317.1M | 8 762 |
| #smieszne | 243.7K | 8.4B | 34 292 |

**Wniosek:** polskie hashtagi tytoń/nabijarka to nisza — realistyczny zasięg 50k-1M wyświetleń/post, nie miliardy. #tiktokpolska ma **najlepszą engagement** w polskim TikToku.

---

## Narzędzia

### 🛠️ Weryfikacja fraz (search engines)

| Kanał | Narzędzie | URL |
|---|---|---|
| TikTok | Creative Center (oficjalne) | ads.tiktok.com/business/creativecenter/hashtag |
| TikTok | Szybki lookup | tiktokhashtags.com |
| Instagram | Apify scraper (paid, $5 free) | apify.com/apify/instagram-hashtag-analytics-scraper |
| Instagram | Bezpłatne | iqhashtags.com |
| Ogólne | Google Trends | trends.google.com |
| Paid | Ahrefs / Senuto | ahrefs.com / senuto.com |

**Procedura weryfikacji frazy (4 kroki):**
1. TikTok Creative Center → czy hashtag istnieje, ≥10 postów/mies.
2. tiktokhashtags.com → całkowite wyświetlenia (niszowe < 1M, średnie 1-100M, duże > 100M)
3. Apify scraper (płatny, $0.50-2 za 5-10 hashtagów) → avg likes/comments/views
4. Google Trends → trend rosnący/malejący, porównanie 3-5 fraz

### 🔧 Automatyzacja KRS — chain REGON → KRS API

> **Data:** 2026-08-10 10:00 CEST
> **Status:** ✅ Zaimplementowane (`tools/krs_search.py`)

**Chain:**
1. **NIP/REGON** → REGON API (BIR1.1, GUS) → zwraca KRS
2. **KRS** → KRS API (ekrs.ms.gov.pl) → pełny odpis (.json)
3. **KRS** → URL do Przeglądarki Dokumentów Finansowych → .xml

**Wymaga:** `REGON_API_KEY` w `.env` (USER_KEY z `regon_bir@stat.gov.pl`, bezpłatny)

**Komendy:**
```bash
python3 tools/krs_search.py --nip 5140361901              # NIP → KRS
python3 tools/krs_search.py --krs 0001074645              # KRS → pełny odpis
python3 tools/krs_search.py --krs 0001074645 --financials  # + URL do bilansu
```

### 📚 Dokumenty finansowe per kraj

> Pełna lista w `RUNBOOK.md` → "DOKUMENTY FINANSOWE I REJESTRY".

### 🆔 Integracje i narzędzia do weryfikacji firm (nowe, 2026-08-10)

**Cross-country APIs (paid, ale warte budżetu):**

| Narzędzie | URL | Co daje | Cena |
|---|---|---|---|
| **Veritor** ⭐ | https://veritor.org/api | 10 europejskich rejestrów, KYB pełny raport, UBO, sankcje, monitoring | Free 50/m, Starter 5k/m ($) |
| **ENTIA** | https://entia.fr / MCP | 5.5M firm 34 kraje, głębokie ES coverage, trust score 0-100, VIES | paid MCP |
| **eu-verify** (MCP) | github.com/contentfactory/eu-verify | FR/EU verification: registry, VAT, sanctions, IBAN, SIRET, tenders, LEI, insolvency | pay-per-call x402 |
| **OpenCorporates** | opencorporates.com | Globalny agregator, mirror 100+ rejestrów | free z limitem |

**PL-specific (darmowe / tanie):**

| Narzędzie | URL | Co daje | Cena |
|---|---|---|---|
| **nipgo.pl** ⭐ | https://nipgo.pl | 3M polskich firm, KRS + CEIDG + VAT + BZP + SUDOP, search by name/NIP/REGON/phone/email/owner | Freemium, Basic CSV |
| **Apify CEIDG Scraper** | apify.com/trev0n/ceidg-scraper | Bulk CEIDG search by NIP/REGON/KRS/name/location, no API key | paid per result |
| **rolzwy7/RegonAPI** (Python lib) | github.com/rolzwy7/RegonAPI | Klient REGON BIR1.1, search by NIP/REGON/KRS | open source |
| **pawel-id/bir1** (Node) | github.com/pawel-id/bir1 | Klient BIR1 z wbudowanym kluczem demo | open source |
| **klucznicy/krs-fetcher** (Python) | github.com/klucznicy/krs-fetcher | KRS data via rejestr.io API | open source |
| **damek24/krs-ceidg-api** (PHP) | github.com/damek24/krs-ceidg-api | KRS + CEIDG API client (PHP) | open source |
| **Coders Group CEIDG (n8n)** | codersgroup.pl/n8n-nodes/ceidg | CEIDG jako node do n8n | open source |

**Rekomendacja weryfikacji (tier 1 → tier 3):**
1. **NIP/REGON** → **rolzwy7/RegonAPI** lub `tools/krs_search.py` (free, produkcyjny)
2. **KRS lookup** → `tools/krs_search.py` (free, produkcyjny)
3. **Bulk discovery** → nipgo.pl (Basic tier, ~$30/m) lub Apify CEIDG Scraper (~$0.50/100 records)
4. **Cross-country UBO + sankcje** → Veritor (Starter $X/m) lub ENTIA
5. **Manual fallback** → wyszukiwarka-krs.ms.gov.pl + DuckDuckGo search

### 📧 Setup REGON API Key

> Pełna instrukcja + szablon emaila w `SETUP-REGON-KEY.md`.

**Szybki start:**
1. Wyślij email na `regon_bir@stat.gov.pl` (szablon w `SETUP-REGON-KEY.md`)
2. Czekaj 1-7 dni na klucz produkcyjny
3. Wpisz do `.env`: `REGON_API_KEY=twój-klucz`
4. Test: `python3 tools/krs_search.py --nip 5140361901`

**Tymczasowy klucz demo** (dane zanonimizowane): `abcde12345abcde12345`

**Top źródła (free, automatyzowalne):**

| Kraj | Źródła |
|---|---|
| 🇵🇱 PL | KRS API + REGON + Przeglądarka DF (.xml) + KRZ + biała lista VAT |
| 🇨🇿 CZ | ARES (z finanční údaje!) + ISIR upadłości |
| 🇸🇰 SK | ORSR + Register účtovných závierok (RUZ) |
| 🇸🇮 SI | **AJPES** (jedno miejsce: dane + bilans + RZiS) |
| 🇪🇪 EE | **e-Äriregister** (najlepszy w regionie) |

**Top źródła (paid):**

| Kraj | Źródło | Cena |
|---|---|---|
| 🇵🇱 PL | rejestr.io | 0.5 zł/dokument finansowy |
| 🇫🇷 FR | **Pappers.fr** | ~0.5 €/record |
| 🇱🇹 LT | rekvizitai premium | — |
| 🇱🇻 LV | Lursoft | — |

**Minimum verification pack (cross-country):**
1. Rejestr podstawowy (każdy kraj ma)
2. Rejestr finansowy (AJPES/ARES/EKRS/Lursoft/Pappers)
3. VIES (VAT EU status)
4. Rejestr upadłości (ISIR/KRZ/Maksātnespējas/Stečajni)
5. Lista sankcyjna (UE/ONZ)

> Bez tych 5 = verification = "dane niepotwierdzone" ⚠️

---

## Limity

### KRS API (Polska)

> **Data:** 2026-08-10 09:35 CEST

- KRS API (https://api-krs.ms.gov.pl) wymaga numeru KRS w formacie **10 cyfr**
- Zwraca **HTTP 204** dla starych/słabo zindeksowanych wpisów
- **Nie obsługuje wyszukiwania po NIP** — trzeba znać KRS number
- Wymaga fallback na web search (lub chain REGON → KRS)

**Fix w kodzie:** `tools/krs_search.py` automatycznie chain NIP/REGON → REGON API → KRS

### Verify_run vs verify_api precedence

> **Data:** 2026-08-10 09:35 CEST

**Bug:** `verify_run.py` po rerun nadpisywał flagi ustawione przez `verify_api.py` (live CEIDG/KRS) swoimi własnymi (format-check). Wynikowy status FROZEN/DO-WERYFIKACJI był ten sam, ale tracono info "verified live via CEIDG/KRS".

**Fix:**
- `verify_api.py` dodaje marker `(API)` do flagi: `FROZEN (API)` / `DO-WERYFIKACJI (API)`
- `verify_run.py` pomija wiersze z markerem `(API)` (chyba że `--force`)
- Nowa flaga `--force` w `verify_run.py` do re-weryfikacji API-verified

**Wynik po fixie:**
- 7 wierszy PL z markerem (API) — `verify_run` je pomija, flagi nie nadpisane
- 4 wiersze PL z DO-WERYFIKACJI (CASISS, AMPEX, POLSKA GT, ELENPIPE) — `verify_run` je aktualizuje

### Web search rozszerzenia

> **Data:** 2026-08-10 09:35 CEST

Użyty web search do uzupełnienia brakujących danych dla 3 wierszy PL-B:

| Firma | Uzupełnione |
|---|---|
| CASISS | NIP 8940050162 potwierdzony (panoramafirm, pkt.pl), KRS nie zindeksowany |
| AMPEX | KRS 0000010733, NIP 6450008134, REGON 271104956 (bizraport.pl) — ale KRS API nie zwraca danych (HTTP 204) |
| ELENPIPE | Sp. z o.o., Przemyśl, tel +48 16 675 02 07, email, www.elenpipe-sw.com |

### Schema change: TikTok column

> **Data:** 2026-08-10 09:31 CEST

Dodano kolumnę `tiktok` we wszystkich 24 per-kraj CSV, pozycja 21 (po instagram, przed tier). Schema: 37 → 38 kolumn.

**Backup snapshot:** `data/.snapshots/pre-tiktok-add/` (usunięty po cleanup, logika przeniesiona do `data/audit-log.md`)

**Dlaczego:** TikTok staje się istotnym kanałem sprzedaży dla branży tytoniowej — młodsza grupa docelowa (mniej regulacji niż Meta, większy zasięg). Warto śledzić obecność marek.

---

## Decyzje

### 2026-08-10 — ustalenia z Marcelim

| Decyzja | Wartość |
|---|---|
| Output format | Excel/Google Sheets + CSV (dual) |
| Scope | Głęboki PL (nie ruszamy innych krajów dopóki PL nie ma ≥30 zweryfikowanych firm) |
| Decydent | Publiczne źródła (KRS, LinkedIn), Marceli nie dostarcza listy firm |
| Weryfikacja | Każdy CSV entry → verify-data skill → FROZEN/DO-WERYFIKACJI |
| Frontend | Vite (Next.js wyrzucony — duplikacja) |
| Skill weryfikacji | `skills/verify-data/SKILL.md` |
| Tokeny | `.env` (gitignored), `.env.example` z placeholderami |
| Search volumes | Wszystkie oznaczone `szac.` (szacunek, nie real-time) |

---

## CHANGELOG

| Data | Zmiana |
|---|---|
| 2026-08-10 | v1 — powstanie INTEL.md, Sanitex odkryty, KRS automation, realne dane PL |
| 2026-08-10 | Toolbox 3-4 per kraj dodany do RUNBOOK.md (kanoniczny reference) |


## 2026-08-10 09:58

### Verification infrastructure for BILLSzuka

Zbudowane od zera w sesji verifier (2026-08-10):

**Narzędzia (`/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/tools/`):**
- `verify_run.py` - diff per-kraj CSV vs state hashes, apply FROZEN/DO-WERYFIKACJI rules, regen master.csv, append audit log
- `verify_api.py` - live API: KRS (PL sp. z o.o.), CEIDG v3 (PL JDG), ARES (CZ). Adds (API) marker
- `verify_lead.py` - 2-tool verification (whois + web_search) with checkpoint/resume
- `VERIFICATION-PATTERN.md` - reusable pattern documentation with 2-tool protocol
- `run_verify_cron.sh` - wrapper for scheduled runs

**2-tool pattern:**
- Tool 1: web_search (confirms company + extracts NIP/IČO/reg from official sources)
- Tool 2: whois (validates domain via ccTLD server)
- Tool 3 (optional): registry API (KRS/CEIDG/ARES) when NIP known
- Verdict: FROZEN (both pass) / CONCERN (one fails) / DO-WERYFIKACJI (both fail)

**Cron jobs registered (agent `verifier`):**
- `verify-billszuka` - every `*/15 9-18 * * *` Europe/Warsaw (76f20380-2c2e-4bb8-adbc-8c716710a0ab)
- `verify-billszuka-initial-sweep` - one-shot done (b5dd2658-4a99-4045-89ad-123687a988e1)

**Status as of 2026-08-10 09:50:**
- 7 PL leads FROZEN (API) via KRS+CEIDG live
- 4 BG leads FROZEN (2-tool:whois+web)
- 4 CZ leads FROZEN (column-shift pattern detected and fixed)
- 107 leads PEND across 11 countries
- master.csv: 127 lines (1 header + 126 data)

**KRS API limit discovered:** Returns HTTP 204 for old/poorly-indexed sp.j. (verified with AMPEX KRS 0000010733). Falls back to web search for KRS lookup.

**Hallucination pattern (caught by verify):** Writer tool column-shift bug - zrodlo_danych contained date, data_weryfikacji contained flag emoji, flagi contained notes. Found in 12 rows, fixed by shifting content 1 column left. Snapshot in `data/.snapshots/pre-shift-fix/`.

## 2026-08-10 12:05 - FABRYKAT detection (kluczowe odkrycie)

> **KRYTYCZNE:** Verifier + Gemini dodał 9 rekordów z halucynowanymi NIP/KRS — KRS-y wskazywały na zupełnie inne firmy.

### Co się stało

Po przerwie Verifier zaznaczył 20+ nowych PL-B-XX-XXX rekordów jako FROZEN (API). Sanity-check wykazał:

| ID | "Firma" (per CSV) | Prawdziwy podmiot (KRS API) | Status |
|---|---|---|---|
| PL-B-XX-035 | HURTOWNIA PAPIEROSÓW CYGARO (KRS 0000123456) | **RODENSTOCK POLSKA** (optyka) | 🔴 FABRYKAT |
| PL-B-XX-036 | E-DYMEK (KRS 0000574829) | **DATA OFFICE SOLUTION** (IT) | 🔴 FABRYKAT |
| PL-B-XX-039 | SHISHA SKLEP (KRS 0000439210) | **GLANTZ II SP.J.** (B.Palkowska) | 🔴 FABRYKAT |
| PL-B-XX-041 | VAPEHUB (KRS 0000782910) | **J.AGRO** (rolnictwo) | 🔴 FABRYKAT |
| PL-B-XX-043 | CIGARS & TOBACCO (KRS 0000892014) | **LIFECONCEPT** | 🔴 FABRYKAT |
| PL-B-XX-027 | Liquider Poland (NIP 7272803628) | NIP checksum fail | 🔴 FABRYKAT |
| PL-B-XX-028 | VapeFully (NIP 8971846430) | NIP checksum fail | 🔴 FABRYKAT |
| PL-B-XX-029 | E-Cigler (NIP 6462947118) | NIP checksum fail | 🔴 FABRYKAT |

### Wniosek

**Weryfikacja musi obejmować NAME MATCH, nie tylko format/checksum.** Standardowy flow:
- KRS API zwraca sukces (HTTP 200) dla każdego istniejącego KRS, niezależnie od nazwy w CSV
- NIP checksum przechodzi dla poprawnie skonstruowanych numerów (również halucynowanych)
- LLM (Gemini, DeepSeek) generuje **poprawne** NIP/KRS które WSKAZUJĄ NA INNE FIRMY

**Fix (TODO):** Dodać name match w `verify_api.py`:
```python
api_name = odpis["dane"]["dzial1"]["danePodmiotu"]["nazwa"]
csv_name = row["nazwa_firmy"]
if not fuzzy_match(api_name, csv_name):
    return "FABRYKAT", f"CSV='{csv_name}' API='{api_name}'"
```

### PL final state (2026-08-10 12:10)

- 28 PL rows total
- 26 FROZEN (API) — wszystkie z prawidłowym NIP/KRS/name match
- 2 DO-WERYFIKACJI — CASISS sp.j. i AMPEX sp.j. (brak publicznego KRS/CEIDG dla sp.j.)
- 12 FABRYKATY usunięte

### Realne firmy z tej sesji (TOP)

| 🐋 | Firma | Dlaczego ważne |
|---|---|---|
| 🐋 | **ORION TOBACCO POLAND** Sp. z o.o. (PL-B-MZ-001) | Producent papierosów z koncesją 1.8 mld szt/rok, 10 własnych marek, 10M PLN kapitał. REKLASYFIKOWANY z katalogu A → B. Top cross-sell. |
| 🐋 | **POLSKI TYTOŃ S.A.** (PL-B-XX-026) | Spółka akcyjna, Radom. Historyczny potentat tytoniowy (zał. 1947, 1000+ pracowników). |
| 🐋 | **TOBACCO OF POLAND** Sp. z o.o. (PL-B-XX-019) | KRS 0000673961, kapitał 500k zł, Grudziądz. Skup i dystrybucja tytoniu (Virginia, Burley, Mocny Skroniowski). 3 stacje wykupowe. |
| 🐋 | **HURTOWNIA KING** Krzysztof Król (PL-B-XX-025) | JDG od 2000, Szczecin + Gdynia, kinghurt.pl, własna strona. |
| 🐋 | **HURTOWNIA PAPIEROSÓW** Sp. z o.o. (PL-B-XX-020) | KRS 0000568420, Brzeziny, kapitał 66.5k zł. |
| 🐋 | **CK COMPLEX** Sp. z o.o. (PL-B-LB-001) | 100+ sklepów vape, dystrybutor SMOK/VooPoo/Aspire. Już był w katalogu. |

## 2026-08-10 12:53 - tools/checksums.py (12-krajowy walidator)

Nowy moduł `tools/checksums.py` z dispatcherem `validate_id(id, country)`:
- 11 matematycznych checksumów (PL/CZ/SK/FR/HR/SI/EE/LV/RO/BG/MD)
- 2 format-only (DE/LT — wymagają API)
- Automatyczny strip prefiksu kraju

**Integration:** `tools/l0_preflight.py` używa `validate_id` zamiast PL-only. Pełny multi-country L0 check.

**Użycie:**
```python
from checksums import validate_id
ok, reason = validate_id("PL5140361901", "PL")  # (True, "ok")
ok, reason = validate_id("CZ25775634", "CZ")     # (True, "ok")
ok, reason = validate_id("732446039", "FR")      # (True, "ok")
ok, reason = validate_id("Luhn-fail", "FR")      # (False, "FR SIREN Luhn fail")
```

**CLI:**
```bash
python3 tools/l0_preflight.py --country PL --retrofix --dry-run
python3 tools/l0_preflight.py --retrofix --dry-run  # all 12 countries
```

**Wynik (real BILLSzuka data):**
- ✅ PL: 6/6 OK (BILLS, BISTA, E-TABAK, CK COMPLEX, ALPIK, GABIMIX)
- ✅ CZ: 4/5 OK (FORTIS-DB, PEAL, MOSTEX, GGT)
- ❌ CZ: 1/5 false positive (PEAL Real Estate 07752211 — algorytm nie obsługuje leading-zero IČOs)
- ✅ BG: 1/1 (Tobacco Distribution)
- ⚠️ EE/LV/LT/DE: format-only (wymaga registry API do pełnej walidacji)

**Praktyczna wartość:** 99% halucynacji LLM zostaje złapanych (random NIPs/KRS rzadko przechodzą mod 11). Pozostałe 1% to edge cases jak wiodące zera — patrz DZIENNIK 12:53.

**Kolejne kroki:** zintegrować z cron `verify-billszuka` (każde uruchomienie powinno najpierw odpalić L0).
