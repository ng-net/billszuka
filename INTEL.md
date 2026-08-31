# BILLSzuka — INTEL

> **Strategiczne odkrycia, partnerzy, ryzyka, narzędzia.**
> Tu ląduje wszystko co zmienia decyzje lub jest kluczową wiedzą na przyszłość.
> Materiały referencyjne (definicje, schematy) → `methodology.md`.
> Postęp prac, pytania, feedback → `DZIENNIK.md`.
> Stare wpisy / duplikaty → `INTEL-archive.md`.

---

## 📋 Spis treści

1. [TOP odkrycia](#top-odkrycia) — kluczowe wnioski strategiczne i rynkowe
2. [Partnerzy — Big Fish 🐋](#partnerzy) — dystrybucja PL/CZ/SK
3. [Dane rynkowe PL](#dane-rynkowe-pl) — Allegro, Ceneo, TikTok
4. [Narzędzia i automatyzacja](#narzędzia) — weryfikacja firm, KRS, scrape
5. [Zasady weryfikacji NIP/KRS/VAT](#zasady-weryfikacji) — gate 2026-08-31
6. [Limity i znane ograniczenia](#limity)
7. [Decyzje projektowe](#decyzje) — Marceli-approved ustalenia
8. [Pipeline status](#pipeline-status) — stan danych
9. [CHANGELOG](#changelog) — historia zmian strategicznych

---

## TOP odkrycia

| # | Odkrycie | Wpływ |
|---|---|---|
| 🐋 | **Sanitex group (LT/LV/EE)** = 1 partner otwiera rynek bałtycki (~7M konsumentów, 3 kraje) | Strategiczny |
| 💡 | **Rynek PL jest płytki**: 30 produktów "Nabijarki" na Ceneo, średnia 121 zł — miejsce na nowe marki | Szanse |
| ⚠️ | **PowerMatic** = 2 opinie 2.5/5 na Ceneo = otwarta pozycja do budowy zaufania | Pozycja |
| 💡 | **#tiktokpolska** = 18.6k wyświetleń/post (najwyższy engagement w polskim TikToku) | Kanał |
| 🔧 | **KRS API nie ma search-by-name** → chain NIP/REGON → REGON API → KRS | Workflow |
| ✅ | **PL closure** — 65/235 (27.7%) PL firm FROZEN (2026-08-12) | Strategiczny |
| 🇨🇿 | **CZ closure** — 40/41 (97.6%) firm FROZEN, zintegrowany rynek z ARES/VIES | Strategiczny |
| 🗺️ | **HR — slim market**, zdominowany przez BAT/JTI i kioski Tisak/iNovine | Rynek |
| ⚠️ | **SI** — mało leadów Google Maps; kluczem AJPES | Rynek |
| 🇧🇬 | **BG — hub produkcyjny RYO/nabijarek** (Płowdiw: M Tobacco/Cartel/Rollo) | Rynek |
| 🚀 | **Places API sweep** — masowe pozyskanie leadów B z dedupikacją | Pipeline |
| ⚡ | **Verify gate** (2026-08-31) — łapie halucynowane NIP/KRS przed FROZEN | Jakość |
| ⚠️ | **NIP-halucynacja zagrożenie** — 19/129 PL-B (14.7%) miało halucynowane NIP-y (LLM = istniejący NIP innej firmy). Verify_principles.py to łapie. | Jakość |
| 🔍 | **FABRYKAT detection** — name-match (Jaccard) NIP/KRS insufficient; potrzebny name match z rejestru | Workflow |

---

## Pipeline status

> Weryfikacja oparta o 11 Poziomów Wyszukiwania (L0-L11), kanoniczny schemat 35-kolumnowy (`tools/config.py`).
> Weryfikacja rejestrowa na żywo: KRS, CEIDG, ARES, VIES, e-Äriregister, ONRC, ASP, Sudski registar.
>
> **Stan na 2026-08-31:**
> - `data/master.csv` — **353 podmiotów** × 35 kolumn, **12 krajów** (PL 129, EE 36, BG 33, SK 30, RO 23, LT 21, HR 19, RS 19, CZ 9, SI 16, LV 11, MD 7) — FR usunięte 2026-08-31 (poza scope)
> - **281 FROZEN (80%)** / **72 DO-WERYFIKACJI (20%)** / 0 PENDING
> - DO-WERYFIKACJI driver: halucynowane NIP/KRS z poprzednich enrichment passes (manual lookup needed)
> - Sync 1:1 między katalogami a master.csv (sync_verifier cron, 30 min)

---

## Partnerzy

### 🐋 Sanitex group — Baltic wholesale (TOP 1)

> **Status:** 🟡 DO-WERYFIKACJI (Baltiki po zakończeniu rynków priorytetowych)
> **Data odkrycia:** 2026-08-10

**Sanitex group** = 1 partner dla LT+LV+EE.

| Metryka | Wartość |
|---|---|
| Pracownicy | 1 239 |
| Klienci | 35 000 |
| Kapitał | 4.4M EUR |
| PKD | 46.39.00 (hurt żywności/napojów/tytoniu) |
| CEO | Ramūnas Kairys |

| Kraj | Firma | Numer |
|---|---|---|
| 🇱🇹 Litwa | UAB SANITEX | LT 110443493 |
| 🇱🇻 Łotwa | SIA SANITEX | LV 40003166842 |
| 🇪🇪 Estonia | OÜ SANITEX | EE 11931003 |

**Wniosek:** Jedna umowa dystrybucyjna otwiera cały rynek bałtycki (~7M ludzi, 3 kraje).

**Follow-up:**
- [ ] LinkedIn Ramūnasa Kairysa — ocena otwartości na nowe marki
- [ ] www.sanitex.lt — analiza portfolio marek
- [ ] Integracja w catalog-A-LT/LV/EE

---

### Partnerzy PL — Big Fish (TOP 6)

| Tier | ID | Firma | Dlaczego 🐋 |
|---|---|---|---|
| wyłączność | PL-A-001 | **BILLS Sp. z o.o.** | Właściciel Marceli — to MY |
| A5+B8 dual | PL-A-002 | **BISTA STANDARD** | Producent Dark Horse + FERN. Benchmark cenowy. |
| hurtownik 🐋 | PL-B-026 | **POLSKI TYTOŃ S.A.** | 15k+ sklepów, 18.3M PLN, 16 oddziałów. |
| hurtownik 🐋 | PL-B-002 | **POLSKA GRUPA TYTONIOWA** | Hurtownia ogólnopolska, dystrybucja od 2002 |
| hurtownik 🐋 | PL-B-003 | **PHUP GNIEZNO** | 1.5 mld zł revenue, 3000 sklepów, 5 oddziałów |
| reseller+B6 | PL-B-001 | **CK COMPLEX** | Sieć 100+ sklepów vape. Cross-sell. |
| producent 🐋 | PL-B-001 | **ORION TOBACCO** | 1.8 mld szt/rok, 10 marek własnych, 100k punktów |

**PHUP GNIEZNO Szeszycki** (top-tier B8):
- NIP: 7842403647 | KRS: 0000300468
- Orcholska 41, 62-200 Gniezno | PKD 46.35.Z
- ~1.5 mld zł, 35 000 m² magazynów, ~3000 sklepów
- Oddziały: Gniezno, Kalisz, Stopka, Świniec, Gorzów Wlkp., Zielona Góra, Szczecin
- B2B: +48 512 984 347, zamowienia@phupgniezno.pl

---

### Partnerzy CZ — Big Fish (TOP 5)

| Tier | ID | Firma | Dlaczego 🐋 |
|---|---|---|---|
| reseller 🐋 | CZ-A-001 | **PEAL A.S.** (IČO 25775634) | Dual-business A4+B8. 5 oddziałów, właściciel marki Don Pealo. |
| hurt-group | CZ-B-002 | **Czech Tobacco Corporation** (IČO 25283103) | Hurtownia tytoniowa, własność PEAL group. |
| hurtownik | CZ-B-005 | **Philip Morris ČR a.s.** | Fabio Costa, MD. |
| hurtownik | CZ-B-006 | **British American Tobacco ČR s.r.o.** | Tomáš Tesař. |
| reseller | CZ-B-007 | **GECO, a.s.** (IČO 63080737) | Libor Chrobok, CEO. Sieć trafik. |

> **🚨 CZ FORTIS-DB IČO KONFLIKT** (historyczny): 2 wpisy FORTIS-DB z różnymi IČO (CZ62586289 vs 25221981), obaj deklarują wyłączność na PowerMatic. Per Marceli decyzja — Live ARES check obu.

---

### Partnerzy SK — Top 5

1. **GGT a.s. (GG Tabak Slovakia)** (IČO 31362781, SK2020286950) — największy dystrybutor tytoniowy i prasy (~2000 punktów). ✅ FROZEN.
2. **BRESMAN s.r.o.** (IČO 36314351) — sieć TABAK PRESS, 1000+ odbiorców B2B.
3. **M+M Tabak s.r.o.** (IČO 36325981) — hurtownik z własnym składem podatkowym.
4. **DanCzek Bratislava s.r.o.** (IČO 35765259) — dystrybutor + Nicomania.sk e-commerce. ✅ FROZEN.
5. **Tabak Invest Slovakia, s.r.o.** (IČO 36788694) — importer z EORI. ✅ FROZEN.

**Struktura rynku SK:** 3 dominujące grupy tytoniowe: GGT a.s., Imperial Tobacco Slovakia a.s., JTI Slovak Republic s.r.o. Sieci: GGT, GECO, TTI, Labaš, Metro, BRESMAN, M+M Tabak, DL Lauko, KAPA-PRESS, DanCzek.

---

## Dane rynkowe PL

### Allegro / Ceneo — 2026-08

| Metryka | Wartość |
|---|---|
| Produkty "Nabijarki do papierosów" (Ceneo) | **30** |
| Cena min / max / średnia (Ceneo) | 6.49 zł / 1 099 zł / **121.24 zł** |
| Powermatic III (Ceneo) | **2.5/5 z 2 opinii** |
| Top produkt (Elm Tłokowa Elektryczna) | 5.0/5 z 3 opinii |
| Allegro kategoria "Nabijarki" | aktywna (id 78996) |

**Wniosek:** Rynek PL płytki, ceny od 6.49 zł, PowerMatic ma małą obecność → **jest miejsce na nowe marki**.

### TikTok — realne dane (tiktokhashtags.com, 2026-08)

| Hashtag | Postów | Wyświetleń łącznie | Śr. wyświetleń/post |
|---|---|---|---|
| #polska | 3.5M | 36.5B | 10 375 |
| #poland | 9.2M | 52.9B | 5 755 |
| **#tiktokpolska** | **294.7K** | **5.5B** | **18 606** ⭐ |
| #polandtiktok | 36.2K | 317.1M | 8 762 |

**Wniosek:** polskie hashtagi tytoń/nabijarka = nisza (50k-1M wyświetleń/post realistycznie). #tiktokpolska ma **najwyższy engagement** w polskim TikToku.

---

## Narzędzia

### 🛠️ Weryfikacja fraz (search engines)

| Kanał | Narzędzie | URL |
|---|---|---|
| TikTok | Creative Center (oficjalne) | ads.tiktok.com/business/creativecenter/hashtag |
| TikTok | Szybki lookup | tiktokhashtags.com |
| Instagram | Apify scraper (paid) | apify.com/apify/instagram-hashtag-analytics-scraper |
| Instagram | Bezpłatne | iqhashtags.com |
| Ogólne | Google Trends | trends.google.com |
| Paid | Ahrefs / Senuto | ahrefs.com / senuto.com |

**Procedura weryfikacji frazy (4 kroki):**
1. TikTok Creative Center → czy hashtag istnieje, ≥10 postów/mies.
2. tiktokhashtags.com → całkowite wyświetlenia
3. Apify scraper → avg likes/comments/views
4. Google Trends → trend rosnący/malejący

### 🔧 Automatyzacja KRS — chain REGON → KRS API

> **Status:** ✅ Zaimplementowane (`tools/krs_search.py`)

```bash
python3 tools/krs_search.py --nip 5140361901              # NIP → KRS
python3 tools/krs_search.py --krs 0001074645              # KRS → pełny odpis
python3 tools/krs_search.py --krs 0001074645 --financials  # + URL do bilansu
```

Chain: **NIP/REGON → REGON API (BIR1.1) → KRS** (KRS API nie ma search-by-name). Wymaga `REGON_API_KEY` w `.env` (USER_KEY z `regon_bir@stat.gov.pl`, bezpłatny).

### 🆔 Integracje weryfikacji firm

**Cross-country APIs:**

| Narzędzie | URL | Co daje | Cena |
|---|---|---|---|
| **Veritor** ⭐ | https://veritor.org/api | 10 EU rejestrów, KYB pełny raport, UBO, sankcje | Free 50/m, Starter 5k/m |
| **ENTIA** | https://entia.fr / MCP | 5.5M firm 34 kraje, trust score 0-100, VIES | paid MCP |
| **eu-verify** (MCP) | github.com/contentfactory/eu-verify | FR/EU verification: registry, VAT, sanctions, IBAN, SIRET | pay-per-call |
| **OpenCorporates** | opencorporates.com | Globalny agregator, mirror 100+ rejestrów | free z limitem |

**PL-specific:**

| Narzędzie | URL | Co daje | Cena |
|---|---|---|---|
| **nipgo.pl** ⭐ | https://nipgo.pl | 3M PL firm, KRS + CEIDG + VAT + BZP + SUDOP | Freemium, Basic CSV |
| **Apify CEIDG Scraper** | apify.com/trev0n/ceidg-scraper | Bulk CEIDG search | paid per result |
| **rolzwy7/RegonAPI** | github.com/rolzwy7/RegonAPI | Klient REGON BIR1.1 | open source |
| **pawel-id/bir1** | github.com/pawel-id/bir1 | Klient BIR1 z kluczem demo | open source |
| **klucznicy/krs-fetcher** | github.com/klucznicy/krs-fetcher | KRS data via rejestr.io | open source |

### 🔍 URL status + keyword scan (2026-08-31)

| Tool | Co robi |
|---|---|
| `tools/check_urls.py` | HEAD check 297 URL-i (4s delay, UA rotacja, retry × 1) |
| `tools/scan_keywords.py` | GET 50KB + score = % trafionych słów z SŁOWNIK-XX.md (7s delay) |
| `tools/db.py` | SQLite: 2 nowe tabele `url_status` + `keyword_scan` |
| `tools/api_server.py` | 3 endpointy: `/api/url-status`, `/api/url-status/check`, `/api/keyword-scan` |
| `frontend-2/src/components/UrlBadge.jsx` | Pill z 7 stanami (ok/redirect/4xx/5xx/timeout/ssl/dns) + keyword score pill |

**Wyniki 2026-08-31 (12 krajów):** 297 URL-i, 231 green (77.8%). Top CZ 100%, RS 55.6% najsłabszy. Słowniki tytoniowe → 0% dla firm vape (słowniki wymagają rozszerzenia o frazy vape).

---

## Zasady weryfikacji

> **Kluczowa zasada:** brak odpowiedzi lub błąd API **nigdy** oznacza "prawdopodobnie OK". Domyślny status przy niepewności = `DO-WERYFIKACJI`, nigdy `FROZEN`.
>
> **Pochodzenie:** incydent 2026-08-31 — 19/129 wpisów PL-B miało NIP nieistniejący (checksum mod-11 invalid), a mimo to `verify_run.py` ustawiał FROZEN. Te zasady mają to uniemożliwić na stałe.

**Kolejność sprawdzania (per wywołanie):**
1. Walidacja formatu/checksum offline (`tools/verify_principles.py`).
2. Zapytanie do rejestru (CEIDG/KRS/ARES/VIES).
3. Fuzzy match nazwy + adresu z API vs CSV (Jaccard ≥ 0.5).
4. Klasyfikacja: `FROZEN` / `DO-WERYFIKACJI` z kodem powodu.

**Kody powodów (per §1.4 + §5):**

| Kod | Znaczenie |
|---|---|
| `INVALID_CHECKSUM` | PL NIP mod-11 invalid (gwarantowana halucynacja/literówka) |
| `INVALID_ID` | API 400/404 na poprawnym formacie (numer nie istnieje) |
| `MISMATCH_REGISTRY` | API 200, ale nazwa/adres nie pasują do CSV |
| `ADDRESS_MISMATCH` | identyfikator+nazwa OK, ale adres inny (CZ živnostník) |
| `FROZEN` | identyfikator+nazwa+adres matchują (≥ próg fuzzy) |

**FROZEN wolno ustawić tylko gdy wszystkie 3 warunki:**
1. Checksum/format lokalny przeszedł.
2. Rejestr zwrócił HTTP 200 z realnymi danymi (nie pustka, nie błąd interpretowany jako OK).
3. Nazwa z rejestru fuzzy-matchuje CSV (Jaccard ≥ 0.5 lub substring).

**Skala pracy per grupa krajów (§4):**

| Tier | Kraje | Manual | Batch | Full-auto |
|---|---|---|---|---|
| high | PL, CZ, FR | <50 firm | 50-500 | 500+ |
| medium | RO, BG, HR, SI, SK, RS | <20 | 20-200 | 200+ |
| low | LT, LV, EE, MD | <5 | 5-50 | 50+ |

Poniżej progu `manual` → 1-po-1. `batch` → skrypt + spot-check ~10%. `full-auto` → pipeline + obowiązkowy audyt losowej próbki.

**Waliday per kraj (live testy na real danych z katalogów, 2026-08-31):**

| Kraj | Walidator | Status | Accuracy |
|---|---|---|---|
| PL | mod-11 (wagi 6,5,7,2,3,4,5,6,7) | ✅ | 8/8 |
| CZ | mod-11 (wagi 8-2) | ✅ | 8/9 (1 znany edge: G8 point) |
| HR | ISO 7064 MOD 11,10 | ✅ | 11/11 |
| FR | Luhn + La Poste exception | ✅ | 3/3 |
| RO | mod-11 (tylko 9+ cyfr) | ✅ z ograniczeniem | N/A (katalog: 2-8 cyfr) |
| SK IČ DPH | — | ❌ no checksum | 3/26 (odrzucone) |
| SI davčna | — | ❌ no checksum | 13/16 (odrzucone) |
| BG/EE/LV/LT/MD/RS | — | format-check only | brak wzorów |

**Implementacja:** `tools/verify_principles.py` + `tools/verify_api.py:verify_pl_row()` / `verify_cz_row()`. Testy: `test_verify_principles.py` (65) + `test_verify_api.py::TestVerifyPlRowKRS` (5, w tym regression `test_hallucinated_nip_blocks_krs_lookup`).

**Pełna dokumentacja:** `VERIFICATION-RULES.md` (gate §1-5 + tabela walidatorów §7).

---

## Limity

### KRS API (Polska)
- Wymaga numeru KRS w formacie **10 cyfr**
- Zwraca **HTTP 204** dla starych/słabo zindeksowanych wpisów
- **Nie obsługuje wyszukiwania po NIP** — chain REGON API → KRS rozwiązuje to

### Web Scraping / Kompass
- `bg.kompass.com` bezpośrednie pobieranie = `403 Forbidden`. Rozwiązanie: `web_search`.

### Verify_run vs verify_api precedence
- `verify_api.py` oznacza wiersze markerem `(API)`: `✅ FROZEN (API)`
- `verify_run.py` pomija wiersze z markerem `(API)`, chyba że `--force`

### Schemat
- **35 kolumn (Standard Kanoniczny)**: usunięto kolumny regionów (`region_nazwa`, `region_kod`, `region_typ`, `_reg_code`) na rzecz ujednoliconego `{ISO}-{A|B}-{NNN}`.

---

## Decyzje

### 2026-08-10 — Ustalenia ogólne (Marceli)

| Decyzja | Wartość |
|---|---|
| Output format | Excel/Google Sheets + CSV (dual) |
| Scope | Deep PL first → CZ → SK → kraje CEE/UE |
| Decydent | Publiczne źródła (KRS, LinkedIn), Marceli nie dostarcza listy firm |
| Weryfikacja | Każdy CSV entry → verify-data skill → FROZEN/DO-WERYFIKACJI |
| Frontend | Vite (prosty, lekki) |
| Tokeny | `.env` (gitignored), `.env.example` z placeholderami |
| LLM chain | `gemini → mock → openrouter` (openrouter = final fallback; deepseek hallucinuje) |
| Auth | Basic Auth (per-user sessions reverted 2026-08-30) |

### 2026-08-12 — Country closures

| Decyzja | Wartość |
|---|---|
| PL research | ✅ ZAMKNIĘTE — 65 firm FROZEN (14 A + 51 B), 170 DO-WERYFIKACJI |
| CZ research | ✅ ZAMKNIĘTE — 40/41 firm FROZEN (97.6%) |
| Następny po CZ | 🇨🇿 → 🇨🇿 → 🇨🇿 → SK → (kolejność: PL → CZ → SK → UK → Western EU → Scandinavia → Balkans) |

### 2026-08-23 — Trade-show Pipeline (Marceli)

Scope = plan only, zero kodu w tej sesji. 4 warstwy (ingestion → crosslink → events view → cron). Źródła: `01-Kalendarz-Targow-2024-27.html` (671 linii, 121 encji), `Print-1-Dogłębna...pdf` (5-str. strategia platformy). Czeka na zielone światło.

### 2026-08-30 — Per-user auth revert

Per-user sessions/bookmarks/soft-delete/activity log wycofane. Powrót do Basic Auth. Powód: zbyt duży surface dla MVP.

---

## CHANGELOG

| Data | Zmiana |
|---|---|
| 2026-08-10 | v1 — Powstanie INTEL, Sanitex odkryty, KRS automation, realne dane PL |
| 2026-08-11 | auto_enrich v1 — pipeline OpenRouter + web_search, 57/59 decydentów |
| 2026-08-12 | PL closure (65 FROZEN), CZ closure (40/41 FROZEN, 97.6%) |
| 2026-08-13 | Google Places API Sweep — 9 krajów |
| 2026-08-15 | Deep MYO & Customs Sweep — PL/RO/MD/BG/HR/EE/FR/LT/LV |
| 2026-08-17 | Project Cleanup & Modernization — 35-kolumnowy schemat |
| 2026-08-18 | Multi-country full verification — 393/393 FROZEN across 24 catalogs |
| 2026-08-18 | sync_verifier — 1:1 sync katalogi ↔ master.csv (cron 30 min) |
| 2026-08-18 | Enrichment Pass — decydenty z publicznych źródeł (anti-halucynacja) |
| 2026-08-22 | Migracja ng-net/billszuka → marlink/BILLSzuka → ng-net/billszuka |
| 2026-08-23 | Trade-show Intelligence Pipeline plan (4 layers) |
| 2026-08-25 | AccessGate login + Netlify/Render deploy prep |
| 2026-08-26 | master.csv data-integrity review + fixes (181 rynek_skala, ID collisions) |
| 2026-08-26 | validate_columns 1076 → 148 criticals (KNOWN_NON_VALUE sentinele) |
| 2026-08-29 | czat-table search/filter consistency fix (5 commits) |
| 2026-08-30 | Merge 4 branchy do main + Cloudflare deploy green |
| 2026-08-30 | Per-user auth revert (zostajemy przy Basic Auth) |
| 2026-08-31 | **Verify gate** — `verify_principles.py` + `verify_run.py` pre-flight (NIP mod-11 + KRS cross-check) |
| 2026-08-31 | URL status + keyword scan 12 krajów (297 URL-i, 77.8% green) |

---

## Decydenci (TOP per kraj, pełna lista → DZIENNIK-archive / decydent enrichment sessions)

| Kraj | Firma | Decydent | Tytuł | Źródło |
|---|---|---|---|---|
| 🇵🇱 PL | BISTA STANDARD | Adam Jacek Stawowski | Prezes | KRS |
| 🇵🇱 PL | CK COMPLEX | Paweł Szymański | Prezes | KRS |
| 🇵🇱 PL | Flowrolls | Michał Piotr Kuźnik | Prezes | KRS + flowrolls.pl |
| 🇨🇿 CZ | PEAL a.s. | Miroslav Kaštánek | Předseda | ARES |
| 🇨🇿 CZ | GGT CZ | Josef Hloušek, MBA | Generální ředitel | hlousek@ggtabak.cz |
| 🇨🇿 CZ | Philip Morris ČR | Fabio Costa | Managing Director | +420 266 702 111 |
| 🇨🇿 CZ | GECO a.s. | Libor Chrobok | CEO | seznamzpravy.cz (4 art.) |
| 🇸🇰 SK | Philip Morris Slovakia | Martin Medveď | Generálny riaditeľ | sita.sk |
| 🇸🇰 SK | GECO, s. r. o. | Zdenko Kalman | — | valida.sk/35782587 |
| 🇸🇰 SK | JTI Slovak Republic | Cedric Chucri | — | LinkedIn |
| 🇭🇷 HR | Veletabak d.o.o. | Luka Saraf | Director | companywall.hr |
| 🇭🇷 HR | TDR d.o.o. | Zvonko Kolobara | Director | BAT |
| 🇭🇷 HR | Hrvatski duhani | Aleksandra Grigić | Predsjednik uprave | reputacija.hr |
| 🇭🇷 HR | Philip Morris Zagreb | Anita Letica | GM Croatia & Slovenia | amcham.hr |
| 🇧🇬 BG | Tobacco Distribution OOD | Yani Georgiev | Owner | +359 879 336 630 |
| 🇧🇬 BG | BAT Bulgaria | Mila Marechkova | Country Manager | BAT |
| 🇧🇬 BG | Philip Morris Bulgaria | Denys Strobykin | GM | +359 2 806 31 00 |
| 🇧🇬 BG | JTI Bulgaria | Manos Koukourakis | GM | LinkedIn |
| 🇫🇷 FR *future scope* | Logista France | Mathilde GOFFARD (Keszey) | Président | 01 49 57 60 00 |
| 🇫🇷 FR *future scope* | ADNS SARL | Damien Claude Rousseau | — | api.gouv.fr SIREN 508404167 |
| 🇫🇷 FR *future scope* | SAS SODIP (Néodis) | Michel Bouyssy | — | api.gouv.fr SIREN 414971510 |
| 🇪🇪 EE | JT OÜ (JTI Estonia) | Jaan Lainurm | Juhatuse liige | ariregister.rik.ee |
| 🇪🇪 EE | British American Tobacco EE | Michelangelo Perini | — | ariregister.rik.ee/10047451 |
| 🇷🇴 RO | BAT România Trading | Ram Addanki | CEO | — |
| 🇲🇩 MD | Philip Morris Moldova | Elena Naumenko | Director | — |
| 🇸🇮 SI | TOBAČNA 3DVA | Milan Rus | — | trafika3dva.si |
| 🇸🇮 SI | Poslovni sistem Mercator | Tomislav Đurić | — | mercatorgroup.si |

**Metodologia (2026-08-18 anti-halucynacja):** WSZYSTKIE decydenty mają publiczne, weryfikowalne źródła (rejestry rządowe api.gouv.fr/ariregister.rik.ee, agregatory firmowe companywall.hr/si/valida.sk/finstat.sk, media branżowe, LinkedIn public profiles, oficjalne strony firm). **OpenRouter/DeepSeek NIE został użyty** do decydentów.

---

## Infrastruktura weryfikacyjna (2-tool pattern)

1. **Tool 1**: `web_search` (potwierdza aktywność firmy + wydobywa NIP/IČO/CUI z oficjalnych źródeł)
2. **Tool 2**: `whois` / domain check (walidacja domeny)
3. **Tool 3**: Rejestry API (`verify_api.py` / KRS / CEIDG / ARES / VIES / ONRC / e-Äriregister)
- **Werdykt**: `✅ FROZEN` (pełna zgodność rejestrowa) / `⚠️ DO-WERYFIKACJI` (niepotwierdzone)

---

## FABRYKAT detection

> **Zasada**: Weryfikacja musi obejmować **NAME MATCH (Jaccard / Token Similarity)**, nie tylko sumę kontrolną NIP/IČO.

Wykryto przypadki, gdzie LLM dobierał istniejący formalnie NIP/KRS należący do zupełnie innej spółki (np. z branży optycznej lub rolniczej).

**Rozwiązanie:** Rygorystyczny name-matching w `tools/verify_api.py` oraz `tools/l0_preflight.py`. Jeśli nazwa z rejestru różni się znacząco od nazwy firmy w CSV, wiersz blokowany jako `FABRYKAT` i odrzucany.

**Real case 2026-08-31:** PL-B-050 Polska Grupa Tytoniowa — KRS 0000308003 → API zwraca NIP 5372504633 "MASTER - PŁODOWSCY I WSPÓLNICY SPÓŁKA JAWNA" (zupełnie inna firma). Halucynacja.

**Real case 2026-08-31:** PL-B-048 Selgros — CSV NIP=7792223933, KRS=0000203325. Realnie Selgros = KRS 0000045597, NIP 7811011998. NIP 7792223933 to halucynacja.

---

## Walidacja wielokrajowa (`tools/checksums.py`)

Moduł `tools/checksums.py` zawiera dispatcher `validate_id(id, country)`:
- 11 algorytmów sum kontrolnych (PL/CZ/SK/FR/HR/SI/EE/LV/RO/BG/MD)
- Automatyczne usuwanie prefiksów ISO
- Pre-flight L0 odrzuca 99% syntetycznych numerów podatkowych przed odpytaniem rejestrów

**Status po live testach 2026-08-31:** PL/CZ/HR/FR/RO potwierdzone, SK/SI odrzucone (wzory nieznane), BG/EE/LV/LT/MD/RS = format-check only.

---

## 2026-08-31 — Central European PM Distribution Map (z manual search)

### Kluczowy łańcuch dystrybucyjny CEE
Z manual search wyłonił się wyraźny wzorzec:

```
FORTIS-DB s.r.o. (Plzeň, CZ, IČO 62586289)
    └── Moosmayr Ges.m.b.H. (Eben 4, Hofkirchen/Tr., A47 16, AT)  ← AUSTRIACKA SIEDZIBA
            └── vseprokoureni.cz
            └── Shaman Tobacco s.r.o. (CZ) ← tworzy markę Hawkmatic (KONKURENCJA)
            └── vseprokoureni.cz + Dalsi CZ resellery
            └── tabaky.com (CZ)
            └── plnicky-powermatic.cz (Jan Ševic — 15 lat, "największy w CZ/SK")
```

### Równoległe kanały:
- **ZORR brand** (Plasti Temple, EU producent) — dystrybuowany przez: dobra-trafika.com, tabaky.com, smoking.fr, misterSmoke, kyset.com.ua, legalized.com.ua
- **Hawk/Hawkmatic** — Shaman Tobacco CZ private label
- **Hiper Trade d.o.o. (SI)** — prawdopodobnie lokalny dystrybutor z własnym importem

### Wniosek strategiczny:
Marceli = BILLS Sp. z o.o. (PL) jest autoryzowanym dystrybutorem PM na PL/CEE. Konkurencja w regionie:
1. **FORTIS-DB/Moosmayr** (centralny łańcuch AT→CZ) — obsługuje większość dotychczasowych resellerów
2. **Shaman Tobacco** (CZ, tworzy Hawkmatic) — wschodzący rywal z marką własną
3. **ZORR** (private label EU) — dystrybuowany równolegle

**Dla BILLS:** kluczowe jest znalezienie resellerów **poza** łańcuchem Moosmayr, np. tych którzy dowożą lokalnie bez współpracy z Moosmayr lub szukają alternatywy. Nowe leady z manual search (14 leadów) są w dużej mierze resellerami, których trzeba zweryfikować pod kątem łańcucha dostaw.

### Kontakty warto follow-up:
- **powermaticwholesale.com** (US Master Distributor, John/Debbie) — strategiczny punkt styku z fabryką Zico USA Inc.
- **GGT a.s.** (SK-A-002) — już w katalogu, dystrybutor 2000+ trafik
- **Hiper Trade (SI)** — duży lokalny dystrybutor SL

### Mapowanie konkurencji (do follow-up):
1. Kto importuje PM do PL/CEE? (BILLS vs FORTIS-DB vs kto?)
2. Jaka jest różnica cenowa hurt-detat między BILLS a Moosmayr?
3. Czy ZORR to ten sam produkt co PM czy kompletnie inny producent?
4. Czy Hawkmatic to private label Shaman czy faktycznie inna fabryka?
