# BILLSzuka — INTEL

> **Strategiczne odkrycia, partnerzy, ryzyka, narzędzia.**
> Tu ląduje wszystko co zmienia decyzje lub jest kluczową wiedzą na przyszłość.
> Materiały referencyjne (definicje, schematy) → `methodology.md`.
> Postęp prac, pytania, feedback → `DZIENNIK.md`.

---

## 📋 Spis treści

1. [TOP odkrycia](#top-odkrycia) — kluczowe wnioski strategiczne i rynkowe
2. [Partnerzy — Big Fish 🐋](#partnerzy) — kto może być partnerem dystrybucyjnym
3. [Dane rynkowe PL](#dane-rynkowe-pl) — realne dane (Allegro, Ceneo, TikTok)
4. [Narzędzia i automatyzacja](#narzędzia) — integracje, API i weryfikacja
5. [Limity i znane ograniczenia](#limity) — co nie działa, fallbacki i ewolucja schematu
6. [Decyzje projektowe](#decyzje) — kluczowe ustalenia, partnerzy i zamknięte kraje
7. [CHANGELOG](#changelog) — historia zmian
8. [Decydenci wg kraju](#decydenci-wg-kraju-auto_enrich-2026-08-11) — kontakty decydentów
9. [Infrastruktura weryfikacyjna](#infrastruktura-weryfikacji-dla-billszuka) — wzorzec 2-tool
10. [Wykrywanie FABRYKATÓW & Checksums](#fabrykat-detection-kluczowe-odkrycie) — mechanizmy obronne
11. [Profile rynkowe i strategiczne](#phup-gniezno-szeszycki--top-tier-b8-2026-08-11) — szczegółowe analizy (PL, SK, CZ)

---

## TOP odkrycia

| # | Odkrycie | Wpływ |
|---|---|---|
| 🐋 | **Sanitex group (LT/LV/EE)** = 1 partner otwiera cały rynek bałtycki (~7M konsumentów, 3 kraje) | Strategiczny |
| 💡 | **Rynek PL jest płytki**: 30 produktów "Nabijarki" na Ceneo, średnia 121 zł — miejsce na nowe marki | Szanse na nowe marki |
| ⚠️ | **PowerMatic** ma tylko 2 opinie 2.5/5 na Ceneo = otwarta pozycja do budowy zaufania | Otwarta pozycja |
| 💡 | **#tiktokpolska**: 18.6k wyświetleń/post (najwyższy engagement w polskim TikToku) | Kanał sprzedaży |
| 🔧 | **KRS API** nie ma search-by-name → chain NIP/REGON → REGON API → KRS | Workflow |
| 🆔 | **Dostępne integracje rejestrowe**: Veritor, ENTIA, nipgo.pl, klucznicy/krs-fetcher, pawel-id/bir1 | Nowe możliwości |
| 📊 | **Struktura katalogu PL**: Naturalny skos w stronę hurtowników ogólnych (B) vs dedykowanych maszynkom (A) | Strategiczny |
| ✅ | **PL closure** — 65/235 (27.7%) PL firm FROZEN, research zakończony formalnie 2026-08-12 | Strategiczny |
| 🇨🇿 | **CZ closure** — 40/41 (97.6%) firm FROZEN, wysoki wskaźnik konwersji i zintegrowany rynek z ARES/VIES | Strategiczny |
| 🗺️ | **HR (Chorwacja) — SLIM MARKET**: Zapytania lokalne zwracają pojedyncze wyniki; rynek zdominowany przez BAT/JTI i kioski Tisak/iNovine | Rynek |
| ⚠️ | **SI (Słowenia) — specyfika źródeł**: Rynek z małą liczbą leadów Google Maps; kluczem są rejestry państwowe (AJPES) | Rynek |
| 🚀 | **Places API sweep**: Masowe pozyskanie leadów B z precyzyjną dedupikacją i translacją notatek | Pipeline |
| 🇧🇬 | **BG (Bułgaria) — HUB PRODUKCYJNY RYO/NABIJAREK**: Płowdiw to centrum maszynek i gilz (M Tobacco/Cartel/Rollo), duzi gracze: Giga Trade BG, Bull Drias | Rynek / Strategia |
| 🇭🇷 | **HR (Chorwacja) — DYSTRYBUTORZY**: Veletabak (PowerMatic/OCB), Nostri Maris, Telemax, NLK Trgovina | Rynek / Strategia |
| 🇨🇿 | **CZ (Czechy) — STRUKTURA RYNKU**: Fortis-DB, Jan Ševic, PEAL (Don Pealo), GECO, TRAFICON, GGT Tabák | Rynek / Strategia |
| 🇪🇪 | **EE (Estonia) — RYNEK & LOGISTYKA CELNA**: Montrade NetStores (tubakas.ee), Nordic Digital; składy celne ALPI EESTI, Estonia Logistics | Rynek / Strategia |
| 🇫🇷 | **FR (Francja) — SYSTEM BURALISTE & DOUANES**: 23k buralistów, akredytowani dostawcy: Logista SAF, Royal Distribution, Project Web (smoking.fr) | Rynek / Strategia |
| 🇱🇹 | **LT (Litwa) — SALONY RYO & SKŁADY**: UAB Skonis ir kvapas (tabakas.eu), Xdalys LT, składy: Vingės Terminalas, Liteksportas | Rynek / Strategia |
| 🇱🇻 | **LV (Łotwa) — DYSTRYBUCJA RIGA & VID**: SIA Avalons (tabakeria.lv), SIA RASTA 1, Tabakas Nams Grupa SIA, Wellman Logistics | Rynek / Strategia |
| 🇲🇩 | **MD (Mołdawia) — RYNEK RYO & BROKERZY VAMAL**: NewSmoke Distribution, S.A. Tutun-CTC, Gamma Logistics VR, GRADALOGISTIC | Rynek / Strategia |
| 🇵🇱 | **PL (Polska) — E-COMMERCE NABIJAREK**: ZOLTA Trade, PRIMA-TECH, P&P Cigarro, składy celne/podatkowe: JAS-FBG S.A., ROHLIG SUUS | Rynek / Strategia |
| 🇷🇴 | **RO (Rumunia) — POPYT MYO & BROKERZY**: SC Golden Tip (tuburipentrutigari.ro), Sensimark Consult, Sibis Concept, Interbrands Orbico | Rynek / Strategia |
| ⚡ | Weryfikacja automatyczna: 44/92 (47.8%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 61 wierszy we wszystkich katalogach regionalnych. | Pipeline |
| ⚡ | Wzbogacono decydentów B2B oraz zweryfikowano NIP/rejestry dla kluczowych podmiotów tytoniowych w ... | Pipeline |
| ⚡ | Weryfikacja automatyczna: 283/359 (78.8%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 357 wierszy we wszystkich katalogach regionalnych. | Pipeline |
| ⚡ | Weryfikacja automatyczna: 60/60 (100.0%) firm zweryfikowanych i oznaczonych jako FROZEN (API). | Pipeline |
| ⚡ | Auto-cleaning & Quality Scoring przetworzył 60 wierszy we wszystkich katalogach regionalnych. | Pipeline |

---

## Pipeline status

> Weryfikacja oparta o 11 Poziomów Wyszukiwania (L0-L11) i kanoniczny schemat 35-kolumnowy (`tools/config.py`).
> Weryfikacja rejestrowa na żywo: KRS, CEIDG, ARES, VIES, e-Äriregister, ONRC, ASP, Sudski registar.
> Aktualna baza skompilowana (`data/master.csv`): 594 podmioty w 12 krajach europejskich.

---

## Partnerzy

### 🐋 Sanitex group — Baltic wholesale (TOP 1)

> **Data:** 2026-08-10 08:21 CEST
> **Status:** 🟡 DO-WERYFIKACJI (Baltiki po zakończeniu rynków priorytetowych)

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
- [ ] LinkedIn Ramūnasa Kairysa — ocena otwartości na nowe marki
- [ ] www.sanitex.lt — analiza portfolio marek
- [ ] Integracja w catalog-A-LT/LV/EE

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

**Wniosek:** polskie hashtagi tytoń/nabijarka to nisza — realistyczny zasięg 50k-1M wyświetleń/post. #tiktokpolska ma **najwyższy engagement** w polskim TikToku.

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
2. tiktokhashtags.com → całkowite wyświetlenia (niszowe < 1M, średnie 1-100M, duże > 100M)
3. Apify scraper → avg likes/comments/views
4. Google Trends → trend rosnący/malejący, porównanie 3-5 fraz

### 🔧 Automatyzacja KRS — chain REGON → KRS API

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

### 🆔 Integracje i narzędzia do weryfikacji firm

**Cross-country APIs:**

| Narzędzie | URL | Co daje | Cena |
|---|---|---|---|
| **Veritor** ⭐ | https://veritor.org/api | 10 europejskich rejestrów, KYB pełny raport, UBO, sankcje, monitoring | Free 50/m, Starter 5k/m |
| **ENTIA** | https://entia.fr / MCP | 5.5M firm 34 kraje, głębokie ES coverage, trust score 0-100, VIES | paid MCP |
| **eu-verify** (MCP) | github.com/contentfactory/eu-verify | FR/EU verification: registry, VAT, sanctions, IBAN, SIRET, tenders, LEI | pay-per-call |
| **OpenCorporates** | opencorporates.com | Globalny agregator, mirror 100+ rejestrów | free z limitem |

**PL-specific:**

| Narzędzie | URL | Co daje | Cena |
|---|---|---|---|
| **nipgo.pl** ⭐ | https://nipgo.pl | 3M polskich firm, KRS + CEIDG + VAT + BZP + SUDOP, search by name/NIP/REGON | Freemium, Basic CSV |
| **Apify CEIDG Scraper** | apify.com/trev0n/ceidg-scraper | Bulk CEIDG search by NIP/REGON/KRS/name/location | paid per result |
| **rolzwy7/RegonAPI** | github.com/rolzwy7/RegonAPI | Klient REGON BIR1.1, search by NIP/REGON/KRS | open source |
| **pawel-id/bir1** | github.com/pawel-id/bir1 | Klient BIR1 z wbudowanym kluczem demo | open source |
| **klucznicy/krs-fetcher** | github.com/klucznicy/krs-fetcher | KRS data via rejestr.io API | open source |

---

## Limity

### KRS API (Polska)
- KRS API (`https://api-krs.ms.gov.pl`) wymaga numeru KRS w formacie **10 cyfr**
- Zwraca **HTTP 204** dla starych/słabo zindeksowanych wpisów
- **Nie obsługuje wyszukiwania po NIP** — chain REGON API → KRS rozwiązuje ten problem (`tools/krs_search.py`)

### Verify_run vs verify_api precedence
- `verify_api.py` oznacza wiersze markerem `(API)`: `✅ FROZEN (API)`
- `verify_run.py` pomija wiersze z markerem `(API)`, chyba że podano flagę `--force`

### Ewolucja schematu
- **35 kolumn (Standard Kanoniczny)**: Usunięto kolumny regionów (`region_nazwa`, `region_kod`, `region_typ`, `_reg_code`) na rzecz ujednoliconego identyfikatora `{ISO}-{A|B}-{NNN}`.

---

## Decyzje

### 2026-08-10 — Ustalenia ogólne z Marcelim

| Decyzja | Wartość |
|---|---|
| Output format | Excel/Google Sheets + CSV (dual) |
| Scope | Deep PL first → CZ → SK → kraje CEE/UE |
| Decydent | Publiczne źródła (KRS, LinkedIn), Marceli nie dostarcza listy firm |
| Weryfikacja | Każdy CSV entry → verify-data skill → FROZEN/DO-WERYFIKACJI |
| Frontend | Vite (prosty, lekki) |
| Tokeny | `.env` (gitignored), `.env.example` z placeholderami |

### 2026-08-12 — PL Research Closure

| Decyzja | Wartość |
|---|---|
| PL research status | ✅ **ZAMKNIĘTE** — research na Polskę uznany za kompletny |
| Zamrożone (FROZEN) | 65 firm (14 A + 51 B) |
| Parked (DO-WERYFIKACJI) | 170 firm — reaktywacja tylko na żądanie |
| Następny kraj | 🇨🇿 Czechy |

### Partnerzy PL — Big Fish (TOP 6)

| Tier | ID | Firma | Dlaczego 🐋 |
|---|---|---|---|
| wyłączność | PL-A-001 | **BILLS Sp. z o.o.** | Właściciel Marceli — to MY |
| A5+B8 dual | PL-A-002 | **BISTA STANDARD** | Producent Dark Horse + FERN. Benchmark cenowy. |
| hurtownik 🐋 | PL-B-026 | **POLSKI TYTOŃ S.A.** | 15k+ sklepów, 18.3M PLN, 16 oddziałów. Strategic channel. |
| hurtownik 🐋 | PL-B-002 | **POLSKA GRUPA TYTONIOWA** | Hurtownia ogólnopolska, dystrybucja od 2002 |
| hurtownik 🐋 | PL-B-003 | **PHUP GNIEZNO** | 1.5 mld zł revenue, 3000 sklepów, 5 oddziałów |
| reseller+B6 | PL-B-001 | **CK COMPLEX** | Sieć 100+ sklepów vape. Cross-sell opportunity. |
| producent 🐋 | PL-B-001 | **ORION TOBACCO** | 1.8 mld szt/rok, 10 marek własnych, 100k punktów dystrybucji |

### Partnerzy CZ — Big Fish (TOP 5)

| Tier | ID | Firma | Dlaczego 🐋 |
|---|---|---|---|
| reseller 🐋 | CZ-A-001 | **PEAL A.S.** (IČO 25775634) | Dual-business A4+B8. 5 oddziałów, właściciel marki Don Pealo. |
| hurt-group | CZ-B-002 | **Czech Tobacco Corporation** (IČO 25283103) | Hurtownia tytoniowa, własność PEAL group. |
| hurtownik | CZ-B-005 | **Philip Morris ČR a.s.** | Fabio Costa, Managing Director. |
| hurtownik | CZ-B-006 | **British American Tobacco ČR s.r.o.** | Tomáš Tesař, manager. |
| reseller | CZ-B-007 | **GECO, a.s.** (IČO 63080737) | Libor Chrobok, CEO. Sieć trafik. |

### 🚨 CZ FORTIS-DB IČO KONFLIKT
Wykryto 2 wpisy FORTIS-DB z różnymi IČO (CZ62586289 vs 25221981). Obaj deklarują wyłączność na PowerMatic w CZ:
- `CZ-A-001` (IČO CZ62586289): Úněšovská 2205/17, Plzeň (Moosmayr Holding GmbH ma 50% udziałów)
- `CZ-A-002` (IČO 25221981): Jateční 862/32, Plzeň
**Rekomendacja:** Live ARES check obu IČO + kontakt bezpośredni.

---

## CHANGELOG

| Data | Zmiana |
|---|---|
| 2026-08-10 | v1 — Powstanie INTEL.md, Sanitex odkryty, KRS automation, realne dane PL |
| 2026-08-11 | **auto_enrich v1** — pipeline OpenRouter + web_search. 57/59 decydentów zidentyfikowanych. |
| 2026-08-12 | **PL closure** — research na Polskę ZAMKNIĘTE (65 firm FROZEN). |
| 2026-08-12 | **CZ closure** — research na Czechy ZAMKNIĘTE (40 firm FROZEN, 97.6%). |
| 2026-08-12 | **EE research** — integracja z e-Äriregister. |
| 2026-08-13 | **Google Places API Sweep** — sweep 9 krajów, oczyszczenie i dedupikacja. |
| 2026-08-15 | **Deep MYO & Customs Sweep** — precyzyjny research nabijarek i brokerów celnych (PL, RO, MD, BG, HR, EE, FR, LT, LV). |
| 2026-08-17 | **Project Cleanup & Modernization** — konsolidacja narzędzi, usunięcie redundancji, czysty 35-kolumnowy schemat. |

---

## Decydenci wg kraju (auto_enrich 2026-08-11)

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
| 🇭🇷 HR | Philip Morris Zagreb | Anita Letica | GM Croatia & Slovenia | +385 1 616 6900 / Anita.Letica@pmi.com | 0.9 |
| 🇭🇷 HR | Imperial Tobacco Zagreb | Tomaz Maver | Director | 01/5494040 | 0.9 |
| 🇨🇿 CZ | PEAL a.s. | Miroslav Kaštánek | Předseda představenstva | 272 774 153 / info@peal.cz | 0.9 |
| 🇨🇿 CZ | GGT CZ, a.s. | Josef Hloušek, MBA | Generální ředitel | hlousek@ggtabak.cz | 0.9 |
| 🇨🇿 CZ | Philip Morris ČR a.s. | Fabio Costa | Managing Director | +420 266 702 111 / philipmorris.cz@pmi.com | 0.9 |
| 🇨🇿 CZ | GECO, a.s. | Libor Chrobok | CEO | +420 241 404 738 / mail.box@geco.cz | 0.9 |
| 🇵🇱 PL | BISTA STANDARD Sp. z o.o. | Adam Jacek Stawowski | Prezes Zarządu | — | 1.0 |
| 🇵🇱 PL | CK COMPLEX Sp. z o.o. | Paweł Szymański | Prezes Zarządu | — | 0.9 |
| 🇵🇱 PL | Flowrolls Sp. z o.o. | Michał Piotr Kuźnik | Prezes Zarządu | info@flowrolls.pl | 0.9 |
| 🇫🇷 FR | Logista France | Mathilde GOFFARD (Keszey) | Président | 01 49 57 60 00 | 0.9 |
| 🇷🇴 RO | BAT România Trading | Ram Addanki | CEO | — | 0.9 |
| 🇷🇴 RO | Philip Morris România | Carmina Fusté | Director General | — | 0.9 |
| 🇸🇰 SK | Philip Morris Slovakia | Martin Medveď | Generálny riaditeľ | — | 0.9 |
| 🇸🇰 SK | BAT Slovakia | Peter Kopačka | Generálny riaditeľ | — | 0.9 |
| 🇪🇪 EE | Philip Morris Eesti | Liudas Zakarevičius | Management board | +372 6050400 / Tallinn.Admin@pmi.com | 0.8 |
| 🇪🇪 EE | JT OÜ (JTI Estonia) | Jaan Lainurm | Juhatuse liige | +372 5551 5636 | 0.9 |
| 🇲🇩 MD | Philip Morris Moldova | Elena Naumenko | Director | — | 0.8 |

---

## Infrastruktura weryfikacji dla BILLSzuka

### 2-tool pattern:
1. **Tool 1**: `web_search` (potwierdza aktywność firmy + wydobywa NIP/IČO/CUI z oficjalnych źródeł)
2. **Tool 2**: `whois` / domain check (walidacja domeny)
3. **Tool 3**: Rejestry API (`verify_api.py` / KRS / CEIDG / ARES / VIES / ONRC / e-Äriregister)
- **Werdykt**: `✅ FROZEN` (pełna zgodność rejestrowa) / `⚠️ DO-WERYFIKACJI` (niepotwierdzone)

---

## FABRYKAT detection (Kluczowe odkrycie)

> **Zasada**: Weryfikacja musi obejmować **NAME MATCH (Jaccard / Token Similarity)**, nie tylko sumę kontrolną NIP/IČO.

Wykryto przypadki, gdzie modele LLM dobierały istniejący formalnie NIP/KRS, który należał do zupełnie innej spółki (np. z branży optycznej lub rolniczej).

✅ **Rozwiązanie**: Wdrożono rygorystyczny name-matching w `tools/verify_api.py` oraz `tools/l0_preflight.py`. Jeśli nazwa z rejestru różni się znacząco od nazwy firmy w CSV, wiersz jest natychmiast blokowany jako `FABRYKAT` i odrzucany.

---

## Walidacja wielokrajowa (`tools/checksums.py`)

Moduł `tools/checksums.py` zawiera dispatcher `validate_id(id, country)`:
- 11 algorytmów sum kontrolnych (PL/CZ/SK/FR/HR/SI/EE/LV/RO/BG/MD)
- Automatyczne usuwanie prefiksów ISO
- Pre-flight L0 odrzuca 99% syntetycznych numerów podatkowych przed odpytaniem rejestrów

---

## PHUP Gniezno Szeszycki — Top-tier B8 (2026-08-11)

- **Nazwa oficjalna:** PHUP GNIEZNO SZESZYCKI SPÓŁKA KOMANDYTOWA
- **NIP:** 7842403647 | **KRS:** 0000300468
- **Siedziba:** Orcholska 41, 62-200 Gniezno
- **PKD główne:** 46.35.Z (Sprzedaż hurtowa wyrobów tytoniowych)
- **Przychody:** ~1.5 mld zł | **Magazyny:** 35 000 m² | **Obsługiwane sklepy:** ~3000
- **Zasięg:** wielkopolskie, lubuskie, zachodniopomorskie
- **Oddziały:** Gniezno, Kalisz, Stopka, Świniec, Gorzów Wlkp., Zielona Góra, Szczecin
- **Kontakt B2B:** +48 512 984 347, zamowienia@phupgniezno.pl

---

## KAS Rejestr Pośredników Tytoniowych (L4)

- Oficjalny rejestr Ministerstwa Finansów / KAS podmiotów pośredniczących w obrocie suszem tytoniowym (PPT).
- Źródło 100% sprawdzonych podmiotów B1/B8 z realnymi magazynami akcyzowymi.
- Zidentyfikowani gracze: LUXTAB, JBT, Łukowa Tobacco, Angel Bio, CKM Tobacco, Universal Leaf Tobacco Poland.

---

## 🇸🇰 SK Intel (Rynek Słowacki)

### Struktura rynku SK
- 3 dominujące grupy tytoniowe: **GGT a.s.** (GG Tabak), **Imperial Tobacco Slovakia a.s.**, **JTI Slovak Republic s.r.o.**
- Kluczowe sieci i dystrybutorzy: GGT, GECO, TTI, Labaš, Metro, BRESMAN, M+M Tabak, DL Lauko, KAPA-PRESS, DanCzek.

### Top targety SK:
1. **GGT a.s. (GG Tabak Slovakia)** (IČO 31362781, SK2020286950) — największy dystrybutor tytoniowy i prasy (~2000 punktów). ✅ FROZEN.
2. **BRESMAN s.r.o.** (IČO 36314351) — sieć TABAK PRESS, 1000+ odbiorców B2B.
3. **M+M Tabak s.r.o.** (IČO 36325981) — hurtownik z własnym składem podatkowym (daňový sklad).
4. **DanCzek Bratislava s.r.o.** (IČO 35765259) — dystrybutor tytoniu i e-commerce Nicomania.sk. ✅ FROZEN.
5. **Tabak Invest Slovakia, s.r.o.** (IČO 36788694) — importer produktów tytoniowych z rejestracją EORI. ✅ FROZEN.
