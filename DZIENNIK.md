# BILLSzuka — Dziennik Projektu

> **Work log.** Chronological, condense. Stare iteracje → `DZIENNIK-archive.md`.
> Strategia, partnerzy, rynki → `INTEL.md`. Konwencje / setup → `RUNBOOK.md`, `methodology.md`.

---

## Status snapshot (2026-08-31)

| Metryka | Wartość |
|---|---|
| Git | `main` @ ng-net/billszuka, clean |
| Tests | 401/401 PASS (Python pytest + node:test) |
| master.csv | 376 wierszy × 35 kolumn, 12 krajów |
| FROZEN | 323 (86.1%) |
| DO-WERYFIKACJI | 52 (13.9%) — głównie halucynowane NIP/KRS z poprzednich enrichment passes |
| Frontend | `frontend-2/` (React 19 + Vite) — canonical. `frontend/` DEPRECATED. |
| Backend | `tools/api_server.py` na `127.0.0.1:8000`, proxy vite na `:3001` |
| Deploy | Cloudflare (frontend green 2026-08-30) |
| Remote | `github.com/ng-net/billszuka` (private) — flipped 3x, sprawdź DZIENNIK-archive przed zmianą |
| LLM chain | `gemini → mock → openrouter` (openrouter jako final fallback; deepseek hallucinuje) |

**Otwarte (non-blocking):**
- 19 PL-B NIP + 7 PL-B KRS + 3 KRS-lookup-failed → DO-WERYFIKACJI do manual lookup przez `tools/krs_search.py --nip <real>`
- 8 outlierów `wolumen` w EE (notatki finansowe w złej kolumnie) → przenieść do `notatki`
- 2 PL-B z `miasto="Polska"` (PL-B-086, PL-B-104) → manual fix
- Vape-frazy do SŁOWNIK-XX.md (słowniki tytoniowe → 0% dla firm vape)
- UI: filtr po "red URL" + "high keyword score"

---

## 2026-08-31 — Zasady weryfikacji: implementacja gate + verify_principles

**Incydent:** 19/129 PL-B wpisów miało halucynowany NIP (mod-11 invalid) a mimo to
`verify_run.py` ustawiał FROZEN. Root cause: status FROZEN nadawany na podstawie
string-match w `zrodlo_danych` (czy zawiera "KRS"/"CEIDG") **bez walidacji NIP/KRS**.

**Fix warstwa 1 — `tools/verify_run.py:verify_row()`:**
- Pre-flight PL NIP mod-11 → `DO-WERYFIKACJI: NIP PL mod-11 invalid (HALUCYNACJA?)`
- Pre-flight KRS lookup → jeśli KRS istnieje a NIP z KRS ≠ CSV NIP → `DO-WERYFIKACJI: KRS HALUCYNACJA`
- Wynik: 29/375 firm (7.7%) przeniesionych FROZEN → DO-WERYFIKACJI z explicytną przyczyną

**Fix warstwa 2 — `tools/verify_principles.py` (nowy) + `verify_api.py` update:**

Master dispatch `is_valid_vat_format(country_iso, vat_id)` — 11 algorytmów checksum:

| Kraj | Walidator | Status | Accuracy na real danych |
|---|---|---|---|
| PL | mod-11 (wagi 6,5,7,2,3,4,5,6,7) | ✅ | 8/8 |
| CZ | mod-11 (wagi 8-2) | ✅ | 8/9 (1 znany edge: G8 point) |
| HR | ISO 7064 MOD 11,10 | ✅ | 11/11 |
| FR | Luhn + La Poste exception | ✅ | 3/3 |
| RO | mod-11 (tylko 9+ cyfr) | ✅ z ograniczeniem | N/A (katalog: 2-8 cyfr) |
| SK IČ DPH | — | ❌ no checksum | 3/26 (odrzucone) |
| SI davčna | — | ❌ no checksum | 13/16 (odrzucone) |
| BG/EE/LV/LT/MD/RS | — | format-check only | brak wzorów |

**Zasada:** wdrożenie niepewnego checksumu jest gorsze niż jego brak (per VERIFICATION-RULES.md §SK/§SI).

**Kody powodów gate (per §1.4 + §5):** `INVALID_CHECKSUM` / `INVALID_ID` / `MISMATCH_REGISTRY` / `ADDRESS_MISMATCH` / `FROZEN`. FROZEN wolno ustawić tylko gdy **3 warunki**: checksum OK + rejestr HTTP 200 + nazwa fuzzy-match (Jaccard ≥ 0.5).

**Skala pracy per grupa krajów:** high (PL/CZ/FR, 5% sample min 10), medium (RO/BG/HR/SI/SK/RS, 10% min 5), low (LT/LV/EE/MD, 20% min 3).

**Testy:** 401 PASSED. Nowe: `test_verify_principles.py` (65), `test_verify_run_hallucination.py` (19), `TestVerifyPlRowKRS::test_hallucinated_nip_blocks_krs_lookup` (regression).

**Edge case G8 point s.r.o. (CZ IČO 06941281):** nie przechodzi mod-11 mimo że ARES potwierdza. 1/9 false-positive akceptowalny koszt za blokadę 100% halucynacji. Test dokumentuje.

---

## 2026-08-31 — URL status + keyword scan (12 krajów)

**Nowe narzędzia:** `tools/check_urls.py` (HEAD, 4s delay, UA rotacja), `tools/scan_keywords.py` (GET 50KB, 7s delay, score = % trafionych słów z SŁOWNIK-XX.md). SQLite: 2 nowe tabele + ALTER TABLE migrations. API: 3 endpointy (`/api/url-status`, `/api/url-status/check`, `/api/keyword-scan`). Frontend: `UrlBadge.jsx` (7 stanów pill) + `useUrlStatus` / `useKeywordScan` hooks wpięte w `ModernLeadsTableV2`.

**Wyniki URL status (297 URL-i):**

| Kraj | n | green | % | Uwagi |
|---|---|---|---|---|
| CZ | 9 | 9 | 100% | benchmark |
| EE | 28 | 24 | 85.7% | |
| HR | 19 | 16 | 84.2% | |
| SK | 30 | 25 | 83.3% | |
| BG | 27 | 22 | 81.5% | |
| LV | 10 | 8 | 80.0% | |
| PL | 75 | 59 | 78.7% | 9× unknown (DNS) |
| FR | 22 | 16 | 72.7% | |
| RO | 17 | 12 | 70.6% | |
| MD | 6 | 4 | 66.7% | |
| LT | 20 | 13 | 65.0% | 4× unknown |
| RS | 18 | 10 | 55.6% | najsłabszy |
| **Total** | **297** | **231** | **77.8%** | |

**Wyniki keyword scan (275 URL-i):** firmy vape mają 0% (słowniki tytoniowe — poprawne). Top trafień: CZ-A-007 atcdistribution.cz 4%, SI-A-001 tobaccostuff.net 3%, LV-A-004 rasta1.eu 2%, PL-B-013 skleptytoniowy.pl 2%.

**Pitfalls napotkane (zachować na przyszłość):**
1. SQLite `CREATE INDEX` na nieistniejącej kolumnie wywala nawet z `IF NOT EXISTS` — index **po** ALTER TABLE.
2. `db.connect()` to **context manager** (`with db.connect() as conn:`), nie zwykły connection.
3. WAL + dwa procesy piszące równolegle → `database is locked` → retry z backoff 15-30× × 2s.
4. `python3 -u` dla `nohup` w tle — bez tego stdout buforowany, log pusty do końca.
5. Cron reporting „done" musi sprawdzać `pgrep=0` **AND** 12/12 krajów **AND** "ALL DONE" w logu — nie tylko pgrep.

---

## 2026-08-30 — Merge 4 branchy do main + Cloudflare deploy

Merged: `fix-tooltip-and-login` (17 commits, 122 files), `feat/proposal-queue-master-csv-only`, `chore/oxlint-actions-brand-sync`, `feat/per-user-sessions` (częściowo zrevertowany — wrócono do Basic Auth).

**Cloudflare deploy:** secrets dodane, deploy green. Backup remote `marlink/BILLSzuka` usunięty po merge (commit `af3f2b51`).

---

## 2026-08-30 — Revert per-user auth (zostajemy przy Basic Auth)

Per-user sessions / bookmarks / soft-delete / activity log — wycofane. Powód: zbyt dużo surface'a dla MVP, Basic Auth wystarcza. Commit: `c9d8354a`.

---

## 2026-08-29 — czat-table search/filter consistency fix (kompletny cykl)

5-commit fix:
1. Hydrate search index z `useCsv` (nie lazy)
2. Dedup `defer` zamiast `delete` (race condition)
3. Split enum filter (text vs badge)
4. Atomic clear filters
5. `useDebouncedEmit` — debounce faktycznie fires (bug: handler nigdy nie odpalał)
6. `filterFn` undefined dla text columns — fix w `TableHeader.jsx`

Commit: `f6897172`.

---

## 2026-08-27 — AGENTS.md & Storage documentation update

Aktualizacja AGENTS.md: workspace path, remote rules, file-scoped storage, data hygiene.

---

## 2026-08-26 — Full Project Review + Validation Fixes

| Obszar | Status |
|---|---|
| Test suite | 349 passed |
| Master regen | 375 rows × 35 cols |
| Sync (sync_verifier) | PERFECT_SYNC |
| 11-level search | PASS (4/12 working; 8 SKIP bez BRAVE_API_KEY) |
| CI workflow | Green (ci-python.yml, 7 steps) |
| API server | OK |

**validate_columns.py — 1076 criticals → 148 (2026-08-26):**
- Root cause: sentinele `brak`/`n/a`/`do weryfikacji`/`do ustalenia`/`nie`/`no`/`unknown`/`—`/`–`/`-` nie były w known-list → każde wystąpienie w LinkedIn/email/sourcing/cross_sell_potential flagowane jako CRITICAL
- Fix: `KNOWN_NON_VALUE` set (16 sentineli) + `normalize_non_value()` na wejściu `validate_value()`
- Fixed `cross_check()` B-row marki check

**Logout Tooltip 2s delay + dissolve:** `AccessGate.jsx` z Radix Tooltip `delayDuration={2000}`, dissolve-on-click (`opacity-0 scale-95 blur-[3px]`).

**Dataset persistence (F5 reset fix):** nowy `datasetStorage.js` (IndexedDB `billszuka_db` dla CSV > 5MB), `prefs.js` rozszerzony o `activeTab`, `RawTable.jsx` boot loader.

**master.csv data-integrity (2026-08-26):**
1. `rynek_skala` niezgodne z formułą w 181/377 (48%) — backfill do 24 plików źródłowych
2. `PL-B-086` oznaczony FROZEN bez `adres` — zdegradowany do DO-WERYFIKACJI
3. Kolizja ID `PL-X-051/052/053` + `FR-X-001` (litera "X" niekanoniczna) → przejście do prawidłowego schematu `{A|B}`

---

## 2026-08-25 — Login gate (AccessGate) + prep Netlify/Render + fix CI

6 produkcyjnych blockerów naprawionych: zepsuty CI krok (test_9_levels.py → test_11_levels.py), brak engines/Node, brak auth backendu, brak netlify.toml/render.yaml/requirements.txt, efemeryczny FS Rendera, public/sample.csv.

**AccessGate (frontend-only MVP):**
- `design/LOGIN-RULES.md` — 6 imion (marceli/karol/jarek/jaroslaw/jaro/jaroslaw-wariant) + firmy bills/smoks, case-insensitive, trim
- `tools/hash_name.py` + `frontend-2/src/lib/access.js` (WebCrypto SHA-256, `localStorage["billszuka.access.v1"]`)
- `frontend-2/public/access.json` — TYLKO hashe, brak plaintext w bundlu
- `AccessGate.jsx` — 2 ekrany (imię → firma), chip Wyloguj

**Deploy prep:** netlify.toml (NODE_VERSION 22), render.yaml (billszuka-api, free, regeneracja master.csv w startCommand).

**Tests:** pytest 215/215 PASS, node --test 5/5, oxlint 0 błędów, vite build exit 0.

Commit: `7105610` (13 files, 417 insertions). Uwaga: `fe at:` zamiast `feat:` w message — kosmetyka, zostawione (amend = force push).

---

## 2026-08-25 — Snapshot LLM setup (operator working)

`api_secrets.json` + UI Settings drawer. Chain: `gemini → mock → openrouter` (openrouter = final fallback only). `maxOutputTokens` 2048 (gemini) / `max_tokens` 1500 (openrouter). OpenRouter `sk-o…eeb9` OK.

---

## 2026-08-23 — Plan: Trade-show Intelligence Pipeline (4 layers)

Źródła: `01-Kalendarz-Targow-2024-27.html` (671 linii, 121 encji), `Print-1-Dogłębna...pdf` (5-str. strategia platformy e-commerce).

**Decyzje:** scope = plan only, zero kodu. Ingestion depth = tylko HTML + PDF przez istniejący `extract_intel.py`. Storage = `data/events/` w BILLSzuka.

**Warstwy (all additive, zero duplikacji):**
1. `tools/ingest_calendar.py` → `data/events/calendar-2024-27.csv` + `exhibitors.csv`
2. `tools/crosslink_events_to_leads.py` → `data/events/event-attendance.csv` (delta exhibitors not in master)
3. `frontend-2/src/views/EventsView.jsx` + 3 endpointy (`/api/events`, `/api/events/{id}/exhibitors`, `/api/strategy`)
4. `tools/run_event_intel.sh` + cron (mtime-aware, idempotent)

Status: 🟡 plan only — czeka na zielone światło.

---

## 2026-08-23 — Cleanup pass: dead-weight columns + 2 PL miasto rows

Rekomendacje z audytu master.csv (393 wierszy × 35 kolumn):

| Kolumna | Puste | Komentarz |
|---|---|---|
| `tiktok` | 100% | dead weight, ale klient chce widzieć |
| `linkedin` | 98.7% | dead weight |
| `instagram` | 98.2% | dead weight |
| `kanal_zamiennik` | 98.0% | do usunięcia |
| `facebook` | 96.4% | dead weight |
| `marka_wlasna_oem` | 93.9% | mało wartościowy |
| `related_to` | 83.0% | nieużywane |
| `rok_zalozenia` | 81.7% | 44/72 = "brak" (extra-leads) |
| `email_decydent` | 73.9% | **krytyczne** dla outreachu |
| `sourcing` | 58.6% | utrudnia ocenę wiarygodności |

**Naprawione w tej sesji:**
- `powinowactwo_nabijarki` — 28 non-numeric (wysoki/średni/Maribor/Ljubljana) → 100% numeric (1-5). Fix: `inferColumnType()` próg `numLike/n === 1.0`. Dodane badge colors (wysoki=emerald, średni=amber).
- `wolumen` — 8 outlierów EE (Müügitulu, EMTAK, liczby pracowników) → DO-WERYFIKACJI + notatka.

**Do zrobienia:** 2 PL-B z `miasto="Polska"` (bug data entry), 8 EE `wolumen` outliers (przenieść do notatki), rozważyć usunięcie dead-weight kolumn.

**Lekcja dla mnie:** przy audycie CSV z cytowanymi polami (przecinki w środku) **zawsze** PapaParse, nigdy `split(',')` — mój skrypt node-owy raportował 0 unikalnych wartości `rynek_skala` przez quoted fields.

---

## 2026-08-22 — Bug review pass 1 + 2 (10 bugs found, 10 fixed)

**Pass 1 (8 bugs):**
- #1 [HIGH] Brak `POST /api/settings/rotate-all` endpoint
- #2 [MED] GeminiDrawer autoscroll broken
- #3 [MED] GeminiDrawer hardcodes `master.csv`
- #4 [HIGH] Vite proxy missing
- #5 [LOW] Dead `api_secrets.lock` w .gitignore
- #6 [MED] RS/Serbia missing z COUNTRY_MAP + COUNTRY_ORDER
- #7 [MED] Zero test coverage for /api/settings/*
- #8 [MED] `_csv_path` recursive search could return wrong file
- Sub-bug: test fixture monkeypatching wrong module (podczas fix #7)

**Pass 2 (1 CRITICAL + 1 known minor):**
- #9 [CRITICAL] App.jsx zrevertowany do stub; 6 orphan components dead — przywrócone.

**Migracja ng-net/billszuka → marlink/BILLSzuka → ng-net/billszuka** (commit `b305fd04...`):
- 2x flip w 3 tygodnie. Check DZIENNIK-archive przed zmianą remote.
- `marlink/BILLSzuka` backup remote usunięty 2026-08-30 po merge.

---

## 2026-08-22 — Frontend consolidation (Phases 1-9)

Konsolidacja frontend/ i frontend-2/. 1 frontend, 1 viewer, 1 design system. Phases 1-9 wykonane, migration notes dla Marcelego w DZIENNIK-archive.

---

## 2026-08-22 — .env auto-bootstrap do secrets vault

Pierwszy setup jest automatyczny — klucze z `.env` (OpenRouter/Gemini) są skanowane i wgrywane do `tools/api_secrets.json` przy starcie api_server. Chain order (`openrouter → gemini → mock` poprzednio = halucynacje) → `gemini → mock → openrouter` (openrouter jako final fallback).

---

## 2026-08-20/21 — czat-table subproject: built, perf, review, code review, framer-motion remove

Sub-projekt: dashboard CSV w `frontend-2/`. Pełny cykl: build → pagination → virtualization removed (no-flicker fix) → hide-column × on hover → 4-PR cleanup → data quality fix + validator → pre-computed filter/sort indexes (perf) → code review → usunięcie framer-motion z row path → viewer perf pass.

---

## 2026-08-21 — master.csv Pass 1-8 (konsolidacja 8 sesji integrity)

8 sesji jednego dnia, łączny wynik:
- **40 duplikatów NIP** usuniętych
- **5 SI/EE confidence** out-of-scope items wyczyszczonych
- **14 kolumn** schema alignment audit
- **RS catalog** tier-cardinality cleanup
- **notatki dedupe** + tool idempotency fix
- **8 PL-B telefonów** (wielo-numer) wyczyszczonych
- **65 A-row cross_sell_potential** → n/a
- **Inferencja typów** — kolumny z błędnym typem poprawione (np. `powinowactwo_nabijarki` z number → enum)

---

## 2026-08-21 — Enrichment Pass: decydenci z publicznych źródeł (anti-halucynacja)

**Metodologia:** WSZYSTKIE decydenty dodane 2026-08-18 mają publiczne, weryfikowalne źródła (rejestry rządowe, agregatory firmowe, media branżowe, LinkedIn, strony korporacyjne). **OpenRouter/DeepSeek NIE został użyty** do decydentów.

Przykłady: FR-A-004 ADNS SARL DAMIEN CLAUDE ROUSSEAU (api.gouv.fr SIREN 508404167), EE-B-014 Karisma Food OÜ Ando Laine (ariregister.rik.ee/eng/company/10048083), SK 9 firm (orsr.sk windows-1250 HTML scrape).

**Strategia następnej sesji:**
1. OpenCorporates free API key (1 min, brak karty, 200 req/mies)
2. Unified scraper dla 12 krajów (PL już ma)
3. Per kraj: register URL, anti-bot status, rate limit, hit rate
4. Commit per kraj osobno (łatwiej revertować)

---

## 2026-08-18 — PDF generation: 12 krajów, propagacja v11.5 (konsolidacja 13 iteracji)

13 sesji iteracji v9 → v11.5 jednego dnia, final state:

**Wynik:** 12 PDF-ów per kraj wygenerowanych (Σ 107 stron, 393 leadów = 105 A + 288 B). Plus `data/INSTRUKCJA.md` (37 KB) + `data/INSTRUKCJA.pdf` (20 stron) per Marceli request.

**Layout final (v11.5):** 2 sekcje (Katalog A + B), 3-wierszowe bloki per lead, 6 leadów/stronę, Notatka w row 3 span 3 cells, bolder nazwa (11pt), 7 kol, kategoria badge, scalony kontakt+email, marginesy zmniejszone, font 8.5pt.

**Tool: `tools/pdf_gen_instrukcja.py`** (54 KB, 940 linii, ReportLab Verdana) + per-country PDF gen.

---

## 2026-08-18 — multi-country full verification

393/393 FROZEN across 24 catalogs (12 countries). Apollo enrichments, atomic write fixes, VIES multi-country. Nowe `tools/sync_verifier.py` + cron (every 30 min) gwarantujące 1:1 sync katalogi ↔ master.csv.

---

## 2026-08-18 — Google Places API sweep (9 krajów)

Sweep 9 krajów, dedupikacja, translacja notatek, integration do `data/{Kraj}/catalog-B-{ISO}.csv`.

---

## 2026-08-18 — Per-country insight files (Marceli request)

12 insight files per kraj. Pipeline per kraj: rejestr → web → LLM summary (gemini).

---

## 2026-08-18 — Katalog C: niezweryfikowane sygnały z gmaps (20/kraj)

C-katalog (sygnały z Google Maps, nieoficjalne źródła) — 20 leads per kraj z 4 (PL/HR/BG/FR). Strategia: osobna warstwa "sygnał vs lead", verify-data skill z flagą C-tier.

---

## 2026-08-17 — Project Cleanup & Modernization

Konsolidacja narzędzi, usunięcie redundancji, czysty 35-kolumnowy schemat (usunięto `region_nazwa`/`region_kod`/`region_typ`/`_reg_code` na rzecz ujednoliconego `{ISO}-{A|B}-{NNN}`).

---

## 2026-08-15 — Precyzyjny gentle search nabijarek & infrastruktury celno-akcyzowej

Kraje CEE/UE: PL, RO, MD, BG, HR, EE, FR, LT, LV. KAS Rejestr Pośredników Tytoniowych (L4) — 100% sprawdzonych podmiotów B1/B8 z realnymi magazynami akcyzowymi. Gracze: LUXTAB, JBT, Łukowa Tobacco, Angel Bio, CKM Tobacco, Universal Leaf Tobacco Poland.

---

## 2026-08-14 — Audyt integralności danych i deduplikacja

Pierwszy audyt master.csv po closure PL+CZ.

---

## 2026-08-13 — Places API Sweep & Pipeline Oczyszczania

Google Places API sweep (9 krajów start), pipeline oczyszczania i dedupikacji.

---

## 2026-08-12 — Architektura 11 Poziomów Wyszukiwania & Schemat 35-kolumnowy

L0-L11 wyszukiwania (KRS/CEIDG → ARES/VIES → e-Äriregister → ...). Schemat 35-kolumnowy kanoniczny.

**PL closure:** 65/235 (27.7%) firm FROZEN, research zakończony formalnie. Następny kraj CZ.
**CZ closure:** 40/41 (97.6%) firm FROZEN, wysoki wskaźnik konwersji.

---

## 2026-08-10 — Powstanie Projektu i Wzorzec 2-Tool Verification

Projekt startuje. Sanitex group odkryty (1 partner = 3 kraje bałtyckie). KRS automation: NIP/REGON → REGON API → KRS API. Realne dane PL (Allegro/Ceneo/TikTok). 2-tool pattern: web_search + whois + rejestry API → FROZEN/DO-WERYFIKACJI.
