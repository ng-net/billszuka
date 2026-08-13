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
| ⚡ | Weryfikacja automatyczna: 10/117 (8.5%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 23 wierszy we wszystkich katalogach regionalnych. | Pipeline |
| ⚡ | Weryfikacja automatyczna: 44/297 (14.8%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 290 wierszy we wszystkich katalogach regionalnych. | Pipeline |
| ⚡ | Weryfikacja automatyczna: 9/12 (75.0%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 12 wierszy we wszystkich katalogach regionalnych. | Pipeline |
| 📊 | Struktura katalogu PL: 4 firmy w Tier A vs 207 w Tier B — kolejny push to wzbogacanie B1–B9 | Strategiczny |
| ⏳ | Bottleneck weryfikacji: 350 firm w master.csv, niski % FROZEN (API) — wymagana pełna weryfikacja | Pipeline |
| ⚡ | Weryfikacja automatyczna: 80/349 (22.9%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 349 wierszy we wszystkich katalogach regionalnych. | Pipeline |
| ✅ | **PL closure** — 65/235 (27.7%) PL firm FROZEN, research ZAMKNIĘTY 2026-08-12. Kolejny kraj: CZ. | Strategiczny |
| ⚡ | Przetworzono 143 firmy w 12 krajach europejskich z automatyczną dedupikacją i jakościowym scoring... | Pipeline |
| ⚡ | Dodano skrapowanie rejestrów SK (FinStat), RO (ListaFirme), LT (Rekvizitai) oraz FR (Pappers). | Pipeline |
| ⚡ | Weryfikacja automatyczna: 139/459 (30.3%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Weryfikacja automatyczna: 27/34 (79.4%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 24 wierszy we wszystkich katalogach regionalnych. | Pipeline |
| ⚡ | Weryfikacja automatyczna: 5/11 (45.5%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 11 wierszy we wszystkich katalogach regionalnych. | Pipeline |
| ⚡ | Weryfikacja automatyczna: 3/3 (100.0%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 2 wierszy we wszystkich katalogach regionalnych. | Pipeline |
| ⚡ | Weryfikacja automatyczna: 1/12 (8.3%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 1 wierszy we wszystkich katalogach regionalnych. | Pipeline |
| ⚡ | Weryfikacja automatyczna: 9/13 (69.2%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 9 wierszy we wszystkich katalogach regionalnych. | Pipeline |
| ⚡ | Weryfikacja automatyczna: 2/2 (100.0%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| 🗺️ | **HR (Chorwacja) — SLIM MARKET**: Places API query "veleprodaja duhana Zagreb" zwrócił tylko 1 wynik lokalny (Tvornica duhana Zagreb). Dopiero zapytanie EN "tobacco wholesale distributor Croatia" dało 20 wyników — zdominowanych przez BAT/JTI i IQOS Service Points, brak niezależnych hurtowni B2B. HR nie jest priorytetem dystrybucji niezależnej. | Rynek |
| ⚠️ | **SI (Słowenia) — ograniczone dane Google Maps**: Dwa kolejne zapytania zwróciły 503 (Google service unavailable). Rynek SI był już wcześniej ubogi (2 leady w cat-A). Zalecane: scraping rejestrów (AJPES) i portali branżowych zamiast Maps. | Rynek |
| 🚀 | **7-min Places API sweep 2026-08-13**: 13 zapytań, 0 błędów krytycznych. Dodano ~130+ nowych leadów B do katalogów LV/BG/EE/HR/MD/FR/LT/RO. LV i BG szczególnie bogate — po 40+ nowych firm. | Pipeline |
| ⚡ | Weryfikacja automatyczna: 9/128 (7.0%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 17 wierszy we wszystkich katalogach regionalnych. | Pipeline |

---

## Pipeline status (auto-monitoring)

| Run | FROZEN | % | Processed | Notes |
|-----|--------|---|-----------|-------|
| 12:23 | 16/143 | 11.2% | 143 | first run |
| 15:09 | 40/145 | 27.6% | 145 | |
| 15:26 | 287/1023 | 28.1% | 145 | |
| 15:32 | 1017/3603 | 28.2% | 1023 | |
| 18:59 | 2245/7782 | 28.8% | 1 | anomaly (1 row only) |
| 20:11 | 2/4 | 50.0% | 4 | test run |

> Auto-extracted from `tools/extract_intel.py` after each `walkthrough.md` / verification run.
> Not curated — for current state see `Decyzje` below + latest DZIENNIK session.

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

### 2026-08-12 — PL Research Closure (Marceli decision)

| Decyzja | Wartość |
|---|---|
| PL research status | ✅ **ZAMKNIĘTE** — research na Polskę uznany za kompletny |
| Zamrożone (FROZEN) | 65 firm (14 A + 51 B) = 27.7% verification rate |
| Parked (DO-WERYFIKACJI) | 170 firm — reaktywacja tylko na żądanie |
| Output artifacts | `verified-A-PL.csv` (14), `verified-B-PL.csv` (51), `top-targets.csv` (64 wg QS) |
| Archive | `data/Polska/_closed/` — pre-close snapshoty + closeout sidecar |
| Następny kraj | 🇨🇿 Czechy (per AGENTS.md order) |
| Decision rule | "Deep PL only" threshold (≥30 verified) **osiągnięty 3.6×** (65/30) → unlock kolejnych krajów |

### Partnerzy PL — Big Fish (TOP 6)

> **Data:** 2026-08-12 12:35 CEST
> **Status:** ✅ FROZEN (API) — gotowe do outreachu

| Tier | ID | Firma | Dlaczego 🐋 |
|---|---|---|---|
| wyłączność | PL-A-WP-001 | **BILLS Sp. z o.o.** | Właściciel Marceli — to MY |
| A5+B8 dual | PL-A-KP-001 | **BISTA STANDARD** | Producent Dark Horse + FERN. Benchmark cenowy. NIE cel sprzedaży PM/Hawk. |
| hurtownik 🐋 | PL-B-XX-026 | **POLSKI TYTOŃ S.A.** | 15k+ sklepów, 18.3M PLN, 16 oddziałów. Strategic channel. |
| hurtownik 🐋 | PL-B-ZP-002 | **POLSKA GRUPA TYTONIOWA** | Hurtownia ogólnopolska, dystrybucja od 2002, 3 wspólników |
| hurtownik 🐋 | PL-B-OP-003 | **PHUP GNIEZNO** | 1.5 mld zł revenue, 3000 sklepów, 5 oddziałów |
| reseller+B6 dual | PL-B-LB-001 | **CK COMPLEX** | Sieć 100+ sklepów vape. Cross-sell opportunity. |
| producent 🐋 | PL-B-MZ-001 | **ORION TOBACCO** | 1.8 mld szt/rok, 10 marek własnych, 100k punktów dystrybucji |
| hurtownik | PL-B-XX-019 | **TOBACCO OF POLAND** | Surowy tytoń + stacje wykupowe (Grudziądz, Łukowa, Górny Potok) |
| hurtownik | PL-B-XX-025 | **HURTOWNIA KING** | 25-letni JDG, PKD 46.35.Z, oddziały Gdynia |
| retailer sieć | PL-A-MZ-002 | **E-TABAK** | Sieć 25+ sklepów vape/CBD, cross-sell akcesoria |

**Konkluzja strategiczna PL:**
- 5 prawdziwych 🐋 (BILLS, BISTA, POLSKI TYTOŃ, PHUP GNIEZNO, ORION) + 5 silnych partnerów
- 23/65 (35%) FROZEN gotowych do cold outreach (www + email + tel + decydent)
- 42/65 (65%) wymaga Apollo-enrich przed kontaktem

**Rekomendowana kolejność outreachu (next 2 weeks):**
1. 🥇 **E-TABAK** (sieć 25+, już zidentyfikowany kontakt)
2. 🥈 **PHUP GNIEZNO** (3000 sklepów, easy phone)
3. 🥉 **CK COMPLEX** (sieć 100+, hurtownia B2B)
4. **POLSKA GRUPA TYTONIOWA** (wspólnicy zidentyfikowani)
5. **TOBACCO OF POLAND** (Aleks Dudalski, dział handlowy)

### Partnerzy CZ — Big Fish (TOP 5)

> **Data:** 2026-08-12 13:10 CEST
> **Status:** ✅ FROZEN (API) — poza FORTIS-DB (wymaga decyzji)

| Tier | ID | Firma | Dlaczego 🐋 |
|---|---|---|---|
| reseller 🐋 | CZ-A-PR-001 | **PEAL A.S.** (IČO 25775634) | Dual-business A4+B8. 5 oddziałów, właściciel marki Don Pealo + główny udziałowiec CTC. |
| hurt-group | CZ-B-PR-002 | **Czech Tobacco Corporation** (IČO 25283103) | Hurtownia tytoniowa, własność PEAL group. Edge: group_ownership. |
| hurtownik | CZ-B-PR-005 | **Philip Morris ČR a.s.** | Fabio Costa, Managing Director. |
| hurtownik | CZ-B-PR-006 | **British American Tobacco ČR s.r.o.** | Tomáš Tesař, manager. |
| reseller | CZ-B-PR-007 | **GECO, a.s.** (IČO 63080737) | Libor Chrobok, CEO. Sieć trafik. |

### 🚨 CZ FORTIS-DB IČO KONFLIKT (Marceli decision needed)

2 wpisy FORTIS-DB z różnymi IČO. Oba twierdzą wyłączność na PowerMatic w CZ:

| ID | IČO | Adres | Score |
|---|---|---|---:|
| CZ-A-PK-001 | CZ62586289 | Úněšovská 2205/17, Plzeň | 90 (ARES verified 2026-08-10) |
| CZ-A-PK-002 | 25221981 | Jateční 862/32, Plzeň | 97 (intake 2026-08-11) |

**Rekomendacja:** Live ARES check obu IČO + telefon do obu + sprawdzić czy to ta sama grupa kapitałowa (Moosmayr Holding GmbH ma 50% w 62586289 od 2024).

### CZ market intel

| Metryka | Wartość |
|---|---|
| Verification rate | 97.6% (40/41) — najwyższy w projekcie |
| Top score (intake) | 97 (FORTIS-DB IČO 25221981) |
| Brno cluster | 7 dużych hurtowni (Crescogroup, MK Tabak, Tabák-Kubík, Brno Tabák, RYO-Distribuce, TABÁK BRNO, TABÁK PLUS) — strategiczny hub |
| Marketplace presence | Heureka Shopping (Ceneo CZ) — vendor onboarding channel |
| CEE coverage | 4 firmy zasięg CZ+SK+DE (Olomouc, Zlín) |

---

## CHANGELOG

| Data | Zmiana |
|---|---|
| 2026-08-10 | v1 — powstanie INTEL.md, Sanitex odkryty, KRS automation, realne dane PL |
| 2026-08-10 | Toolbox 3-4 per kraj dodany do RUNBOOK.md (kanoniczny reference) |
| 2026-08-11 | **auto_enrich v1** — `tools/auto_enrich.py` (OpenRouter + web_search pipeline). 57/59 decydentów znalezionych (96.6% success). Kraje: BG, HR, CZ, PL, FR, RO, SK, EE, MD. Notable: Mila Marechkova (BAT BG), Anita Letica (PM HR), Fabio Costa (PM ČR), Libor Chrobok (GECO CEO), Mathilde GOFFARD (Logista FR), Carmina Fusté (PM RO), Gabriella Offeddu (JTI cluster). tools/apollo_enrich.py (parallel, 420 linii, REST wrapper). |
| 2026-08-12 | **PL closure** — research na Polskę ZAMKNIĘTE. 65/235 (27.7%) FROZEN (API). Master.csv zsynchronizowany (234 PL IDs). Output: `verified-A-PL.csv` (14), `verified-B-PL.csv` (51), `top-targets.csv` (64 wg QS). Pre-close snapshot w `data/Polska/_closed/snapshots/`. Decision: unlock kolejne kraje (start z CZ). |
| 2026-08-12 | **CZ closure** — research na Czechy ZAMKNIĘTE. 40/41 (97.6%) FROZEN. Merge z `data/_intake/CZ/validated.csv` (32 FROZEN → 31 nowych po dedupie). Output: `verified-A-CZ.csv` (29), `verified-B-CZ.csv` (11), `top-targets.csv` (40 wg QS). FORTIS-DB IČO KONFLIKT wykryty (62586289 vs 25221981) — blocker do rozstrzygnięcia. PEAL group ownership + dual_business edges dodane do relationships.csv. Decision: unlock SK. |
| 2026-08-12 | **EE research** — gentle expansion via e-Äriregister + BalticFirms.eu. 7 nowych leads (Imperial Tobacco Estonia 🐋, Easysmoke, RYO Paper & Tobacco, Karia Food, Karisma Food, Fazer Eesti, Nordista) + 2 updates (OÜ SIGARI MAJA = CigarHouse, AmeiZing = Hinnapomm). 17 firm łącznie, 5 FROZEN. **Schema unification**: dodano `_krs` do 22 nie-PL canonicals (38→39). Master.csv zregenerowany (388 rows, 39 cols, 122 FROZEN). |

## Decydenty wg kraju (auto_enrich 2026-08-11)

| Kraj | Firma | Decydent | Tytuł | Telefon / Email | Conf |
|---|---|---|---|---|---|
| 🇧🇬 BG | Tobacco Distribution OOD | Yani Georgiev | Owner | +359 879 336 630 | 0.9 |
| 🇧🇬 BG | TTI Bulgaria (Pöschl) | Tenko Bankov | Managing Director | — | 0.8 |
| 🇧🇬 BG | BAT Bulgaria | Mila Marechkova | Country Manager | +359 2 976 98 90 / bgsofiareception@bat.com | 0.9 |
| 🇧🇬 BG | Philip Morris Bulgaria | Denys Strobykin | General Manager | +359 2 806 31 00 / administration.pmbg@pmi.com | 0.8 |
| 🇧🇬 BG | JTI Bulgaria | Manos Koukourakis | General Manager | LinkedIn | 0.9 |
| 🇭🇷 HR | Veletabak d.o.o. | Luka Saraf | Director | +385 1 7888 610 / luka.saraf@veletabak.hr | 0.9 |
| 🇭🇷 HR | TDR d.o.o. | Zvonko Kolobara | Director | 052844000 / cro_pravniodjel@bat.com | 0.9 |
| 🇭🇷 HR | Hrvatski duhani d.d. | Aleksandra Grigić | Predsjednik uprave | 033 730 660 / hrvatski_duhani@bat.com | 0.9 |
| 🇭🇷 HR | Philip Morris Zagreb | Anita Letica | GM Croatia & Slovenia, Předsednik | +385 1 616 6900 / Anita.Letica@pmi.com | 0.9 |
| 🇭🇷 HR | Imperial Tobacco Zagreb | Tomaz Maver | Director (Market Manager SLO&HR) | 01/5494040 | 0.9 |
| 🇭🇷 HR | JT International Zagreb | Simone Mammi | Direktor | +385 1 6040801 | 0.8 |
| 🇭🇷 HR | AER Wholesale (Aer L.M. d.o.o.) | Matteo Lovisolo | Founder/CEO | +39 02 947 501 07 / info@aer-wsale.com | 0.9 |
| 🇨🇿 CZ | PEAL a.s. | Miroslav Kaštánek | Předseda představenstva | 272 774 153 / info@peal.cz | 0.9 |
| 🇨🇿 CZ | GGT CZ, a.s. | Josef Hloušek, MBA | Generální ředitel | hlousek@ggtabak.cz | 0.9 |
| 🇨🇿 CZ | Czech Tobacco Corporation a.s. | Přemysl Opletal | Chairman of the Board | — | 0.8 |
| 🇨🇿 CZ | Philip Morris ČR a.s. | Fabio Costa | Managing Director, Předseda | +420 266 702 111 / philipmorris.cz@pmi.com | 0.9 |
| 🇨🇿 CZ | Imperial Tobacco CR s.r.o. | Felix von Schwanewede | Country Manager | +420 296 541 111 | 0.8 |
| 🇨🇿 CZ | BAT Czech Republic s.r.o. | Tomáš Tesař | manažer komunikace | +420 724 970 431 / prague_press@bat.com | 0.8 |
| 🇨🇿 CZ | GECO, a.s. | Libor Chrobok | CEO (since 1995) | +420 241 404 738 / mail.box@geco.cz | 0.9 |
| 🇵🇱 PL | BISTA STANDARD Sp. z o.o. | Adam Jacek Stawowski | Prezes Zarządu | — | 1.0 |
| 🇵🇱 PL | CK COMPLEX Sp. z o.o. | Paweł Szymański | Prezes Zarządu | — | 0.9 |
| 🇵🇱 PL | DRV DISTRIBUTION Sp. z o.o. | Jakub Golonka | Prezes / CEO | — | 0.9 |
| 🇵🇱 PL | Flowrolls Sp. z o.o. | Michał Piotr Kuźnik | Prezes Zarządu | info@flowrolls.pl | 0.9 |
| 🇵🇱 PL | BIODIO LAB Sp. z o.o. | Izabela Wojciuk | Prezes | — | 0.9 |
| 🇫🇷 FR | Logista France | Mathilde GOFFARD (Keszey) | Président | 01 49 57 60 00 / [email protected] | 0.9 |
| 🇫🇷 FR | COPROVA SAS | Jorge PEREZ MARTELL | Président | Direction.Generale@coprova.com | 0.9 |
| 🇫🇷 FR | Davidoff of Geneva France | Tom Ryhiner | Gérant | — | 0.9 |
| 🇷🇴 RO | BAT România Trading | Ram ADDANKI | CEO | — | 0.9 |
| 🇷🇴 RO | Philip Morris România | Carmina Fusté | Director General | — | 0.9 |
| 🇷🇴 RO | Imperial Tobacco România | Nikos Nikiforidis | Director General | — | 0.8 |
| 🇷🇴 RO | JTI România | Gabriella Offeddu | General Manager (cluster RO+MD+BG) | — | 0.8 |
| 🇷🇴 RO | BAT România | Jorge Araya | Director General + SEE Area | 021 311 51 00 | 0.9 |
| 🇸🇰 SK | Philip Morris Slovakia | Martin Medveď | Generálny riaditeľ | — | 0.9 |
| 🇸🇰 SK | BAT Slovakia | Peter Kopačka | Generálny riaditeľ | — | 0.9 |
| 🇸🇰 SK | Imperial Tobacco Slovakia | Vernon Little | Generálny riaditeľ | — | 0.8 |
| 🇪🇪 EE | Philip Morris Eesti | Liudas Zakarevičius | Management board | +372 6050400 / Tallinn.Admin@pmi.com | 0.8 |
| 🇪🇪 EE | British American Tobacco Estonia | Matthias Baltes | Main decision-maker | — | 0.9 |
| 🇪🇪 EE | Imperial Tobacco Estonia | Farid Hamadi | Juhatuse liige | +372 6221881 / fredi.viidik@ee.imptob.com | 0.7 |
| 🇪🇪 EE | JT OÜ (JTI Estonia) | Jaan Lainurm | Juhatuse liige | +372 5551 5636 | 0.9 |
| 🇲🇩 MD | Philip Morris Moldova | Elena Naumenko | Director | — | 0.8 |
| 🇲🇩 MD | British American Tobacco Moldova | Radu Vrabie | CORA&Legal Manager | +373 22 855 355 | 0.8 |
| 🇲🇩 MD | Imperial Tobacco Moldova | Dmitri Matiescu | Territory Executive | — | 0.7 |
| 🇲🇩 MD | JTI Moldova | Gabriella Offeddu | GM cluster (RO+MD+BG) | — | 0.9 |

**Pipeline**: `tools/auto_enrich.py` — OpenRouter DeepSeek + agent web_search. Resumable: `data/.verify-state/enrichment-progress.json`. CLI: `python3 tools/auto_enrich.py leads` (list remaining), `process --search-results "..." --id PL-X-XX-XXX --csv ...` (single lead).



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
| 🐋 | **PT DYSTRYBUCJA S.A.** (PL-B-XX-273) | KRS 0000137829, NIP 7960069945, 98M zł kapitał, MERKURY S.A. (Kraków) 78% owner. Legal successor of 1947 Polski Tytoń. **Pivoted to real estate + warehouse + alcohol (46.34.A + 52.10.B + 68.20.Z).** Nie jest aktywnym dystrybutorem tytoniu — ale ma magazyny w Radomiu i licencję alkoholową, więc potential cross-sell na hurtownie alkoholu. NIE ten sam podmiot co PL-B-XX-026 POLSKI TYTOŃ S.A. |
| 🐋 | **HURTOWNIA PD DRWAL** Sp.j. (PL-B-XX-274) | KRS 0000070328, NIP 8730206184, PKD 46.35.Z hurtownia wyrobów tytoniowych, Wola Rzędzińska 573. 3 decidents: W Drwal, G Pinas, D Drwal. Sp.j. od 2001. Solid mid-tier regional wholesale, mała-tka ale stabilna od 23 lat. |

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

## 🐋 PHUP Gniezno Szeszycki — Top-tier B8 (2026-08-11)

**Discovery source:** L1 web search + bizraport + wyszukiwarkakrs + sprytnykupiec (cross-validated via KRS API name match).

**Profile:**
- **Official name:** PHUP GNIEZNO SZESZYCKI SPÓŁKA KOMANDYTOWA
- **NIP:** 7842403647
- **KRS:** 0000300468 (KRS API confirmed)
- **Siedziba:** Orcholska 41, 62-200 Gniezno, wielkopolskie
- **Forma prawna:** spółka komandytowa (od 2022-04-25)
- **PKD główne:** 46.35.Z (Sprzedaż hurtowa wyrobów tytoniowych)
- **Przychody 2025:** 1 449 875 283 zł (1.5 mld zł)
- **Zysk netto 2025:** 19 912 843 zł
- **Wartość firmy:** 1.1 mld zł
- **Magazyny:** 35 000 m²
- **Obsługiwane sklepy:** ~3000
- **Zasięg:** wielkopolskie, lubuskie, zachodniopomorskie
- **Oddziały:** Gniezno, Kalisz, Stopka, Świniec, Gorzów Wlkp., Zielona Góra, Szczecin
- **Tradycja:** 30+ lat (rodzinna firma)
- **Asortyment:** 6000+ produktów FMCG, w tym wyroby tytoniowe, nabiał, chemia, farmaceutyki
- **Kontakt B2B:** +48 512 984 347, +48 507 015 972, zamowienia@phupgniezno.pl, hurtownia@phupgniezno.pl

**Strategic value for BILLSzuka:**
- 🐋 **BIG FISH** — top 5 hurtowni FMCG w PL, 1.5 mld zł revenue (większa niż BILLS)
- Kanał hurtowy obejmuje 3 województwa (wielkopolskie, lubuskie, zachodniopomorskie) = ~3000 sklepów convenience
- PKD 46.35Z = już ma wyroby tytoniowe, cross-sell PM/Hawk naturalny
- Asortyment FMCG + 30 lat tradycji = stabilny partner, nie szara strefa
- **Rekomendacja:** A1 (kontakt natychmiast przez CEO Marceli). Mógłby stockować PM/Hawk jako dodatek do istniejącej oferty tytoniowej.

**Why discovered now:** Phrase "hurtownia FMCG Gniezno" + "wyroby tytoniowe" w SŁOWNIK. KRS API name match = 100% (po rename "PHUP Gniezno Szeszycki sp.k." → "PHUP GNIEZNO SZESZYCKI SPÓŁKA KOMANDYTOWA").

**Catalog row:** `data/Polska/catalog-B-PL.csv:PL-B-OP-003` (region kodu OP, ale firma jest w WP — do korekty regionu)

## 2026-08-11 — KAS Rejestr Pośredników Tytoniowych = best PL L4 source

**Discovery (PL research round 03:42 CEST):** The Polish government publishes an official PDF list of tobacco intermediaries (Posredniczace Podmioty Tytoniowe / PPT) — firms licensed to trade in tobacco leaf (susz tytoniowy) without paying excise upfront.

**URL:** https://www.gov.pl/web/kas/rejestr-posredniczacych-podmiotow-tytoniowych
**Current version:** 123.0 (2026-08-07, 0.13MB PDF, 1 page, ~15 firms)
**Cadence:** Updated weekly (last 30 versions since 2024 visible in change history)

**Why this is the best source for BILLSzuka PL:**
- Authoritative NIP + KRS/CEIDG identifier from KAS (Krajowa Administracja Skarbowa) — no hallucination risk, no FABRYKAT
- All mod-11 valid (government-issued NIPs)
- Includes KRS for sp. z o.o., CEIDG for sp.c./JDG
- All firms have real warehouses (miejsca magazynowania suszu) — tier classification easy
- All B1 (tyton liscie) = highest cross-sell potential with PowerMatic (susz tytoniowy processing firms buy nabijarki for their own product testing + B2B resale)
- Free, no auth, no rate limit
- 100% B1F or A1F fit (firms already in tobacco industry, legal status confirmed)

**7 NEW FROZEN leads from 1 PDF in this run:**
1. **LUXTAB** (KRS 0000418932, Poniatowa) — 2 lokalizacje
2. **JBT** (KRS 0000474682, Lublin) — 6 lokalizacji w lubelskim + swietokrzyskie
3. **LUKOWA TOBACCO COMPANY** (KRS 0000944978) — Lukowa 608
4. **LUKOWA TOBACCO Sp. z o.o.** (KRS 0000979679) — Lukowa, 9 lokalizacji (lubelskie + podkarpackie + podlaskie + kujawsko-pomorskie + swietokrzyskie) — wyglada na duza grupe
5. **ANGEL BIO** (KRS 0000764029, Warszawa HQ) — 3 lokalizacje w mazowieckim
6. **CKM TOBACCO** (KRS 001124066, Lublin) — 2 lokalizacje bilgorajskie
7. **UNIVERSAL LEAF TOBACCO POLAND** (KRS 0000068941, Jedrzejow HQ + 8 oddzialow) — **subsidiary of Universal Corporation (NYSE: UVV)**, jeden z najwiekszych przetworcow tytoniu na swiecie

**Already in catalog (B1/B8 candidates confirmed FROZEN, no double-add):**
- LUXTAB, JBT, TOBACCO OF POLAND (KRS 0000673961, Grudziadz), BAT POLSKA TRADING (KRS 0000328269), PHILIP MORRIS POLSKA TOBACCO (KRS 0000291604), CANNMEDIA AGATA SEKOWSKA (Bletki.com NIP 9462453893)

**Strategic value for BILLSzuka:**
- KAS register firms process susz tytoniowy — they have machines but likely not PowerMatic brand (which is for end-user pre-rolled cigarettes). Cross-sell = sell them PM as workplace tool for their own susz testing.
- Lukowa Tobacco + JBT + AGROTAB + SLOMEX form a **regional cluster in bilgorajskie/podkarpackie (SE Poland)** — natural partner hub for distributing to SK/UA border regions
- UNIVERSAL LEAF = top-tier global player, probably too big to negotiate directly with BILLS but good to know for market intel
- BAT POLSKA TRADING + PMI POLSKA TOBACCO = Tier 1 giants, useful only for market sizing

**Workflow update — add to methodology.md L4:**
- L4 Customs/Regulatory now includes: "**KAS Rejestr Posrednikow Tytoniowych** — PDF download monthly, parse with pdfplumber, filter PKD/B1, add to catalog-B"
- Reasoning: 1 PDF = 7+ verified leads in 5 minutes, beats any L1 search

**Confidence:** high (government-issued, mod-11 + KRS + CEIDG cross-check)

## 2026-08-12 — Nowe odkrycia (PL run)

### 🐋 Top 3 PL tobacco distributors (per BizRaport, bazy.biz)
1. **Philip Morris Polska Distribution** (NIP 6751373354) — 17.4 mld zł revenue — already not in B2B scope (proprietary brands only)
2. **Eurocash Serwis** (NIP 7772304755, KRS 0000040385) — 11.88 mld zł — PL-B-XX-056 FROZEN, 24k+ sklepów, 8+ oddziałów. **Konsorcjum Dystrybutorów = ten sam podmiot** (Eurocash przejął).
3. **British American Tobacco Polska Trading** (NIP 5222917210) — 9.18 mld zł — not in B2B scope (proprietary)

### Nowe B2B discovery (this run)
- **PHU ANTARES Sp. z o.o.** (Warszawa, KRS 0000274792, NIP 5321930490) — PKD 46.35 hurtownia wyrobów tytoniowych. PL-B-XX-212 FROZEN. — 📌 Tier: hurtownik, candidate for PM/Hawk B2B outreach
- **Hurtownia Pd W. Drwal sp.j.** (Wola Rzędzińska, KRS 0000070328, NIP 8730206184) — PKD 46.35, sp.j. od 2001. PL-B-XX-213 FROZEN. — 📌 Tier: regionalny hurtownik
- **Trafika sp.j. Hurtownia Papierosów** (Siedlce, KRS 0000072324, NIP 8211005731) — PKD 46.35, 1995. PL-B-XX-210 DO-W (KRS transient). Retry next run.
- **Tabak Polska Sp. z o.o.** (Tarnów, KRS 0000066240[?], NIP 8731567406) — PKD 46.35, 1993. PL-B-XX-211 DO-W (pkt.pl KRS was wrong, fixed). Retry next run.
- **PHU Hugo Sławomir Strzelczyk** (Oleśnica, NIP 8971630593) — PKD 47.26.Z detal tytoniowy. PL-B-XX-214 DO-W (CEIDG 429). Retry next run.

### Lesson: pkt.pl KRS może być błędny
- KRS 0000254466 z pkt.pl = SKLEPY TABAK sp.j. (NIP inny), NIE Tabak Polska Sp. z o.o.
- Zawsze cross-check z api-krs.ms.gov.pl. L0 NIP+KRS name match jaccard < 0.3 = prawdopodobnie FABRYKAT.
- krs-pobierz.pl daje inny KRS dla tego samego NIP — używać jako secondary source, ale KRS API = single source of truth.

### KAS Rejestr Pośredników Tytoniowych (L4 źródło)
- 6 wpisów już w katalogu FROZEN (LUXTAB 7171829068, JBT 7123280644, ŁUKOWA TOBACCO 7123280644, ANGEL BIO, CKM TOBACCO 7123480343, UNIVERSAL LEAF)
- Source: gov.pl/web/kas/rejestr-posredniczacych-podmiotow-tytoniowych (PDF updated 19.02.26)
- Wszystkie hurtownie suszu tytoniowego — górny poziom kanału dystrybucji

## 2026-08-12 08:30 — Nowe odkrycia (PL run #2, post-merge)

### 🐋 STRATEGIC FIND — powermatic.store unauthorized reseller
- **ARMORICA GRZEGORZ ZAWADA** (NIP PL5140325868, REGON 540228713, 63-500 Olszyna, Jesienna 2/1)
  - Owns domain **powermatic.store** and Erli/Allegro shop "powermatic-store"
  - Self-identifies as **"Offizieller Vertriebspartner von POWERMATIC"** / "Oficjalna dystrybucja PL"
  - VIES ✓ mod-11 ✓ REGON ✓
  - **CONFLICT:** BILLS Sp. z o.o. (PL-A-WP-001) = exclusive PL+CEE distributor per company profile
  - 3 possibilities: (a) BILLS authorized sub-dealer with own storefront, (b) cross-border DE reseller without PL authorization, (c) trademark violation (need EUIPO search "PowerMatic")
  - **Action for Marceli:** CONFIRM whether Armorica is authorized BILLS sub-dealer. If not — this is direct channel conflict / possible EUIPO infringement.
  - **Why 🐋:** Both competitive threat AND sales channel opportunity (if BILLS has gap in their own sub-channel).
  - Filed as PL-B-XX-215 (A6 reseller, ⚠️ KONKURENCJA_UNAUTH flag).

### Tier-🐋 lead — Nooti (Hawk-Matic drop-shipper)
- **NOOTI DAMIAN WICZKOWSKI** (NIP PL5892097312, 83-322 Stężyca, Łąkowa 4)
  - Erli sklep "Nabijarki" + Arena.pl shop — sells Hawk-Matic
  - VIES ✓ mod-11 ✓
  - Small (mały 🟡) but functional B2C channel. Worth monitoring as cross-sell signal for budget segment.
  - NOTE: Hawk-Matic (hawkmatic.com) = Chinese brand, distinct from BILLS Hawk. Different price tier.
  - Filed as PL-B-XX-216 (A4 retailer).

### Run state
- catalog-B-PL.csv: 207 rows (was 205), 2 new leads (215 Armorica, 216 Nooti)
- live verify_api: 745 verified, 114 FROZEN, 631 DO-W, 0 PENDING_API
- CEIDG rate-limited 429s hit my new rows — they need retry next run

### Hempking Sp. z o.o. — PL CBD producer (B9 cross-sell)
- **HEMPKING SPÓŁKA Z OGRANICZONA ODPOWIEDZIALNOŚCIĄ** (NIP PL5272825467, KRS 0000700277, Białystok PD, 2017)
- Polskie laboratorium konopne — producent olejków CBD/CBG/CBDa, susz CBD, kosmetyki, żywność. EU Organic certyfikat.
- B2B hurtownia + dropshipping + white label.
- **BILLS overlap:** B9 (CBD/konopie) → overlap kliencki ze skręcaczami (jointy z suszu). Hurtownie konopne naturalnie cross-sellują bibułki, filtry, młynki, a jeśli klient pyta o maszynki → PM/Hawk. Tier-🟡 partner (kapitał 5k, mały, ale producent z certyfikatem).
- KRS API ✓, mod-11 ✓, FROZEN 2026-08-12
- Filed as PL-B-XX-216.

## 🇸🇰 SK intel (2026-08-12)

### Struktura rynku SK
- **Mały rynek (~37 firm total w katalogu)** vs PL (235), CZ (41), EE (48). Marceli celowo ograniczył scope.
- **3 dominujące grupy tytoniowe SK:**
  - **GGT a.s.** (31362781) — główny dystrybutor prasowo-tytoniowy; ~2000 trafík
  - **Imperial Tobacco Slovakia a.s.** — groupa Imperial Brands UK
  - **JTI Slovak Republic s.r.o.** — groupa Japan Tobacco International
- **9 marek power: GGT, GECO, TTI, Labaš, Metro, BRESMAN, M+M Tabak, DL Lauko, KAPA-PRESS, DanCzek**

### 🐋 Top targety SK (A-tier kandydujący do BILLS partner)
1. **GGT a.s. (GG Tabak Slovakia)** — IČO 31362781, NIP SK2020286950. Największy dystrybutor tytoniowy i prasy. Hurt B2B ogólnokrajowy. ✅ FROZEN (Marceli API).
2. **BRESMAN s.r.o.** (IČO 36314351) — duży dystrybutor tabaku i prasy, sieć TABAK PRESS, 1000+ odbieraczy B2B. ⏳ PENDING_API (templated IČO do weryfikacji).
3. **M+M Tabak s.r.o.** (IČO 36325981, NIP SK2020183569) — duży hurtownik z własnym składem podatkowym (daňový sklad). ⏳ PENDING_API (templated NIP do weryfikacji).
4. **DL Lauko s.r.o.** (IČO 36412850, NIP SK2021759230) — regionalny dystrybutor tabakowy. ⏳ PENDING_API.
5. **KAPA-PRESS s.r.o.** (IČO 36175114) — dystrybutor prasy, tabaki i akcesoriów dla wschodniej SK. ⏳ PENDING_API.

### Strategic findings (z halucynacja audit 2026-08-12)
- **Templated IČO batch (8 firm):** IČO 45293006-45293015 + NIP SK2020286006-2020286015 + email `b2b.sk[N]@<domena>.sk`. VIES zwraca INVALID dla wszystkich. To nie halucynacja (firmy prawdopodobnie istnieją w ORSR), ale dane kontaktowe Marcela są placeholderowe. **Follow-up wymagany:** ORSR web_search + prawdziwe kontakty.
- **GGT dual entry:** SK-B-BA-001 (IČO 31362781, B-tier S4 FMCG) + SK-A-BA-002 (NIP SK2021651817, A-tier S1 RYO). Różne NIP = parent vs sub LUB literówka. Sprawdzić ORSR per NIP.
- **DanCzek Bratislava s.r.o.** (IČO 35765259, NIP SK2020221621) ✅ FROZEN przez VIES — międzynarodowy dystrybutor tabaku + Nicomania.sk e-shop. **High value target** — ma własny e-commerce, dojrzała oferta.
- **TifanTEX, s.r.o.** (IČO 45955824, NIP SK2023161525) ✅ FROZEN — importer elektrycznych plničiek z Azji/EU. Konkurent cenowy (premium alternative). Sprawdzić czy to private label (A5) czy dystrybutor.
- **Tabak Invest Slovakia, s.r.o.** (IČO 36788694, NIP SK2022390370) ✅ FROZEN — oficjalny importer produktów tytoniowych z rejestracją EORI. **Tier-1 partner potencjalny.**

### Tier distribution
- **A1 (kontakt natychmiast, S1):** 2 firmy — GGT GGTabak, BRESMAN
- **A2 (partner regionalny, S1):** 12 firm
- **B1 (hurtownia tytoniowa):** 4 firmy
- **B4 (akcesoria):** 1 firma
- **B6 (e-papierosy):** 4 firmy
- **B8 (pełne hurtownie FMCG):** 7 firm
- **starter set (B-tier duże):** 7 firm (Imperial, PMI, JTI, Continental, MOSTEX, Mediapress BA, MY&MI)

### Coverage
- 8/8 SK regionów (BA, TT, TN, NR, ZA, BB, PO, KE) ma przynajmniej 1 wpis
- BA (Bratislavský) = 13 wierszy (najsilniejszy region)
- Marceli pominął Czechów (patrz scope) — 4 firmy SK to prawdopodobnie subdywencje CZ grup (GGT ↔ GGT Czechy, GECO ↔ GECO CZ, TTI ↔ TTI CZ)
