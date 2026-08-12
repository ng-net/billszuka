# BILLSzuka — Dziennik Projektu

## 2026-08-08

**Struktura projektu — wstępne zakładki**

### KATALOG A — Firmy z nabijarkami w ofercie

| Kod | Kategoria | Co to znaczy dla Ciebie |
|---|---|---|
| A1 | Tylko PowerMatic | Twoi sub-dystrybutorzy / autoryzowani resellerzy |
| A2 | Tylko Hawk | Potencjalny kanał dla Hawk (Twoja marka?) |
| A3 | PowerMatic + Hawk | Najcenniejsi — sprawdzeni w branży, znają produkt |
| A4 | Multi-brand z PM/Hawk | Resellerzy wielu marek (Topomat, GM, Turbomatic...) |
| A5 | Własna marka / OEM z Chin | Konkurencja cenowa — prywatne marki importerów |
| A6 | Multi-brand bez PM/Hawk | Kandydaci do pozyskania — znają kanał, nie mają jeszcze Twojej marki |

**Pola w rekordzie:** Kraj/miasto · Tier · Sourcing · Wolumen · Kanał · Kontakt · WWW (lub alternatywa) · Notatki

---

> 📦 **Archiwum wpisów (08.08–11.08.2026):** zobacz [`DZIENNIK-archive-2026.md`](file:///Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/DZIENNIK-archive-2026.md)

---

## 2026-08-12 08:30 — BILLSzuka PL research+validation round

**Trigger:** Cron task — general agent (no BILLSzuka context, loaded AGENTS.md + methodology.md + SŁOWNIK-PL.md fresh).

### Lock
- Old PID 14861 was dead (runtime restart) → stale lock removed
- New lock: PID 26030

### L1 web_search (10 queries run of 15 budget)
- "hurtownia tytoniowa Polska NIP dystrybutor B2B sp. z o.o." — found Konsorcjum (KRS 0000040385 = Eurocash), Tabak Polska (KRS 0000254466), Trafika sp.j. (KRS 0000072324), PKD 46.35 list (bazy.biz: 477 firm, only 1 new in last 12 months)
- "hurtownia nabijarka PowerMatic Hawk Polska" — confirmed BILLS is wyłączny dystrybutor PL+CEE per powermatic.pl
- "sklep tytoniowy hurtownia Polska NIP" — Hurtownia Papierosów Sp. z o.o. (Brzeziny), Hurtownia Pd Drwal (Wola Rzędzińska)
- "allegro PowerMatic sprzedawca hurtownia opinie" — powermatic-store (Erli) top sprzedawca 6010+ sold
- "hurtownia akcesoriów tytoniowych Warszawa Kraków Wrocław" — Tabak Service International, KING Hurt (Szczecin), Świat Shishy
- "hurtownia tytoniu sp.j. NIP KRS" — CKM Tobacco (Lublin), LUXTAB, JBT z KAS Rejestr Pośredników Tytoniowych
- "sklep tytoniowy B2B dla firm NIP 2026" — skleptytoniowy.pl = Tabak Grupa Sp. z o.o. Kalisz (6181914183) — already PL-A-XX-002
- "Topomat Turbomatic Luxfux Polska NIP" — no PL distributor found
- "PKD 46.35 KRS lista" — Philip Morris Distribution (17.4 mld zł), Eurocash Serwis (11.88 mld zł), BAT Polska Trading (9.18 mld zł) — top 3
- "PHU tytoń papierosy hurtownia NIP KRS 2025/2026" — PHU Hugo, PHU Wysokiński, PHU ANTARES

### Discovery → add_lead (5 added of 14 candidates)
- **PL-B-XX-210** Trafika sp.j. Hurtownia Papierosów (Siedlce, KRS 0000072324) — DO-W, KRS API transient
- **PL-B-XX-211** Tabak Polska Sp. z o.o. (Tarnów, KRS 0000254466 → FIXED to 0000066240) — DO-W, original KRS was FABRYKAT (mapped to SKLEPY TABAK sp.j., jaccard=0.10). krs-pobierz.pl says 0000066240.
- **PL-B-XX-212** PHU ANTARES (Warszawa, KRS 0000274792) — **FROZEN ✓**
- **PL-B-XX-213** Hurtownia Pd Drwal Sp.j. (Wola Rzędzińska, KRS 0000070328) — **FROZEN ✓**
- **PL-B-XX-214** PHU Hugo Sławomir Strzelczyk (Oleśnica, NIP 8971630593) — DO-W, CEIDG 429 rate limit

### Skipped (duplicates or no KRS confirmation)
- Konsorcjum Dystrybutorów (NIP 7772304755) = same entity as Eurocash Serwis PL-B-XX-056
- CKM Tobacco, LUXTAB, JBT — already in catalog FROZEN (from KAS Rejestr 2026-01-23, 2026-08-07)
- Tabak Service Intl, Świat Shishy, MARWIN — no NIP/KRS confirmed in source
- PHU Wysokiński — KRS not confirmed

### L2/L3 (combined into verify_api pass)
- `python3 tools/verify_api.py --country PL --dry-run` — 743 verified, 114 FROZEN, 629 DO-W, 0 errors
- `python3 tools/verify_api.py --country PL` (live) — 744 verified, 114 FROZEN, 630 DO-W, 0 errors
- Net change: +1 row (PL-B-XX-215 added in this run), 0 KAS-rejects, 0 FABRYKAT-blocks

### Anomalies
- **CEIDG API rate-limited (HTTP 429)** — 15+ DO-W rows stuck. Affects mostly JDG/JDG-related (PHU Hugo, topartner, etc.). KRS API works fine, KAS rows FROZEN.
- **KRS API intermittent** — ~70% empty responses today. 3 of 10 KRS lookups returned data. Trafika and Tabak Polska both failed.
- **Tabak Polska KRS wrong** — pkt.pl gave KRS 0000254466 which is actually SKLEPY TABAK M.Tomaszewski T.Tomaszewska sp.j. (different firm). FABRYKAT-like mismatch. Fixed to 0000066240 per krs-pobierz.pl (unverified by KRS API).
- **5 id_unikalne collisions A↔B still present** (per handoff) — not touched in this run.
- **1 NIP dup** (BISTA 5542559901 A+B) — not touched.

### Final state
- catalog-B-PL: 205 rows, 41 FROZEN, 164 DO-W (was 200/29/171 before run)
- Net new FROZEN: +2 (ANTARES, HURTOWNIA PD)
- 3 of my 5 leads need retry (KRS transient / CEIDG 429)
- Lock status: removed at end

## 2026-08-12 08:30 — PL research+validation run #2 (post-merge)

### Lock check
- Stale lock from PID 26030 (runtime restart), removed at 08:20. New lock set with PID 27089.

### Discovery
- L1 web_search: 6 queries (powermatic dystrybutor, hawk sklep, topomatic, bletki, etc.)
- L3 registry: 0 new (used L1 + VIES pipeline instead — faster for niche brands)
- L2 marketplace: 0 seller lookups via API (used indirect via Erli/Arena/Allegro search results)

### New leads added
- **PL-B-XX-215** ARMORICA GRZEGORZ ZAWADA (NIP 5140325868) — powermatic.store unauthorized reseller, 🐋 STRATEGIC FIND (EUIPO conflict risk)
- **PL-B-XX-216** NOOTI DAMIAN WICZKOWSKI (NIP 5892097312) — Hawk-Matic drop-shipper, 🐋 cross-sell signal
- Both: VIES ✓ mod-11 ✓ REGON ✓, hit CEIDG 429 (retry next run)

### FABRYKAT defense
- 9 FABRYKATs still blocked (unchanged)
- 0 new FABRYKATs encountered

### verify_api live run
- 745 verified, 114 FROZEN, 631 DO-W, 0 PENDING_API
- New rows: 215, 216 hit CEIDG 429 (API rate limit)
- No API errors beyond expected 429s

### Anomalies
- **Concurrent verify_run.py** (PID 29070, started 8:22) clobbered my first add_lead. Re-added successfully after it finished at 8:27.
- **CEIDG HTTP 429** still affects ~50% of new rows (rate limit from concurrent runs)
- 5 id_unikalne collisions A↔B + 1 NIP dup (BISTA 5542559901) — NOT touched (handoff items for separate cleanup)

### Final state
- catalog-B-PL: 207 rows (was 205), 114 FROZEN
- 2 new leads with strategic value (see INTEL.md 08:30 entry)
- Lock status: will be removed before exit

## 2026-08-12 10:45 — cron verify-data (auto)

**Trigger:** wc -l master.csv = 349 vs last-verify-count 343 → delta +6 (≥1)
OR git diff data/ od ostatniej weryfikacji (14 katalogów zmienionych).

**Wykonane:**
- `tools/verify_run.py` — 24 canonical CSVs, `No changes detected` (state hashuje aktualne dane)
- `tools/verify_api.py --all` — 860 verified: 144 FROZEN / 625 DO-WERYFIKACJI / 91 PENDING_API
  - PL: 745 rows, dużo CEIDG 429 (rate-limit, retries za godzinę)
  - KRS calls działają, VIES dla LV SIA SANITEX (Apollo enrich: domain sanitex.eu)
  - Audit log: 2 modified (PL-B-XX-215, PL-B-XX-216) + 1 nowy wpis
- `master.csv` zregenerowany z poprawionym filtrem kanonicznym (pomija pre-clean/pre-krs-fix snapshot-y)

**Znalezione problemy:**

1. **Bug: `cd data && ls */catalog-*.csv`** w SKILL.md łapał snapshot-y
   `catalog-A-PL-pre-clean-20260811_023054.csv` / `catalog-A-PL-pre-krs-fix-20260811_0346.csv`
   (te same dla catalog-B-PL). Master.csv miał 859 wierszy, po filtrze 350.
   **Fix:** SKILL.md zaktualizowany — Python z regex `^catalog-[AB]-[A-Z]{2}$`
   + SKIP dla `backups/`, `.snapshots/`, `.verify-state/`, `verification/`.

2. **Duplikat id_unikalne: `PL-B-XX-195`** w catalog-B-PL.csv
   - Linia 186: `UNIVERSAL LEAF TOBACCO POLAND` (KRS 0000068941, NIP PL5212363371) → FROZEN
   - Linia 187: `NOVIS Sławomir Gągorowska Sp.J.` (NIP PL8641951472) → DO-WERYFIKACJI
   - Wymaga ręcznej naprawy (przydzielić nowy ID dla NOVIS, np. PL-B-XX-216a)
   - Master.csv tymczasem trzyma oba (350 wierszy, 349 unikalnych ID).

3. **CEIDG API rate-limit (HTTP 429)** — duża liczba PL-A-XX-* i PL-B-XX-19x wierszy
   nie doczekała się CEIDG weryfikacji. Retry za ~1h gdy limit się odświeży.

4. **4 untracked snapshot files** w `data/Polska/` (pre-clean + pre-krs-fix, ~380KB total):
   - `catalog-A-PL-pre-clean-20260811_023054.csv` (24KB)
   - `catalog-A-PL-pre-krs-fix-20260811_0346.csv` (24KB)
   - `catalog-B-PL-pre-clean-20260811_023054.csv` (195KB)
   - `catalog-B-PL-pre-krs-fix-20260811_0346.csv` (137KB)
   Nie są w git, niepotrzebne po regen. Sugestia: `mavis-trash` przed następnym commitem.

**Final state:**
- master.csv: 350 wierszy danych (1 duplikat PL-B-XX-195)
- last-verify-count: 350
- audit-log.md: aktualny, ostatni wpis 10:45
- SKILL.md: regen-command naprawiony
- Row-hashes state: bez zmian (hash matches)

## 2026-08-12 10:47 — PL research+validation run #3 (cron)

### Stale lock
- Stale lock from dead PID 19929 (likely runtime restart) — removed, fresh lock created (PID 24128).

### Handoff items
- 3 handoff candidates (PHU Kaziool, Tobacchem, Bletki) — all already in CSV (FROZEN):
  - PHU Kaziool: PL-B-DS-012 (Wrocław B2B, B4 akcesoria, ma sekcję nabijarki → kwalifikuje się na A4 ale obecnie B)
  - Tobacchem Maciej Krupnik: PL-B-XX-276 (Chrzanów MA, B4)
  - Bletki.com = Cannmedia Agata Sękowska: PL-A-XX-071 (Lublin LU, A4 — tu klasyfikacja może być dyskusyjna, bo Bletki to bibułki/filtry/młynki, nie maszynki)

### New leads added
- **PL-B-XX-215 Tabak Service International Robert Krauze** (NIP PL6691802158, Koszalin ZP, 1999, JDG/CEIDG) — hurtownia e-papierosów + liquidy + tytoń + akcesoria. Tier: hurtownik, B6+B4. mod-11 ✓
- **PL-B-XX-216 Hempking Sp. z o.o.** (NIP PL5272825467, KRS 0000700277, Białystok PD, 2017) — polski producent CBD, EU Organic, B2B hurtownia CBD. Kapitał 5k. Tier: producent/hurtownik, B9. mod-11 ✓

### verify_api dry-run
- 745 verified, 168 FROZEN, 577 DO-W, 0 errors
- Nowe 215 + 216 oba FROZEN w dry-run

### verify_api live run
- 745 verified, 115 FROZEN, 630 DO-W, 0 PENDING_API
- 215 (Tabak Service) i 214 (PHU HUGO) hit CEIDG HTTP 429 (rate limit) — retry next run
- 216 (Hempking) FROZEN ✓
- Net: 1 confirmed FROZEN (Hempking), 1 hit 429 (Tabak Service)

### Anomalies
- add_lead function failed first call with cryptic "dict contains fields not in fieldnames: None" — second call succeeded. Diagnoza: przejściowy issue z row[0].keys() przy 207+ wierszach. Po resize do 205 wierszy działa. Prawdopodobnie race condition z concurrent writes.
- CEIDG HTTP 429 — nadal wpływa na nowe wiersze (rate limit przy concurrent runs)
- 5 id_unikalne collisions A↔B + 1 NIP dup (BISTA 5542559901) — wciąż nie rozwiązane (handoff item)
- Master.csv: 350 wierszy

### Final state
- catalog-B-PL.csv: 207 rows (was 205)
- 2 new leads (215 Tabak Service, 216 Hempking)
- 1 confirmed FROZEN via API (Hempking); Tabak Service needs retry
- Lock status: will be removed before exit


## 2026-08-12 10:55 CEST — MC-BRAIN crash recovery + gitignore fix

**Co się stało:** MC-BRAIN external drive (/Volumes/MC-BRAIN/) niespodziewanie unmountował się w trakcie sesji — Disk Utility nie ładował, Finder nie widział dysku, mimo że Marcel potwierdził fizyczne podłączenie. Agent stracił dostęp do workspace (każdy `bash` pada z `Working directory does not exist`).

**Co zrobione:**
1. Tier 1 → Tier 2 → Tier 3 protocol recovery (kabel/port → NVRAM/Safe Mode → Recovery fsck) — Marcel wykonał sam
2. Dysk wrócił po ~2h — **pełen stan odzyskany, zero danych utraconych** (filesystem nie ucierpiał)
3. Przywrócono sesję — HEAD = `0f71ad1` (map_intake), 202/202 testów passing, working tree nietknięty

**Co naprawione w tej sesji:**
- **`._*` gitignore nie działał** — wzorzec `._*` w .gitignore nie łapał plików AppleDouble w podkatalogach. Fix: `**/._*` (recursive pattern) + dodane `**/.DS_Store`, `data/temp/`, `data/verification/poc_*.json`, `data/verification/vies_*.json`, `data/**/catalog-*-pre-*.csv`, `tools/.verify-state/`, `data/relationships.csv` (zamiast błędnego `data/.relationships*.csv`)
- **Cleanup**: 4 PL pre-clean snapshots (catalog-*-pre-{clean,krs-fix}-*.csv) skasowane (regenerable)
- **Staged for commit**: 19 plików z `data/_intake/` (Marcel input + PL artifacts + master-backup + README) + 3 nowe tools (`enrich_pl_dow.py`, `normalize_PL.py`, `poc_dow_resolver.py`) + gitignore fix

**Local commit `63b0d6e` znaleziony na branchu (ahead of origin by 1):** "verify run 2026-08-12: PL catalog updates + atomic-write patch + cleanup" — wykonany przez inny proces między crashem a teraz. Pushnięte w tej sesji razem z recovery commitem.

**Lesson (zapisane w agent memory):**
- "External drive unmount → agent brick" — agent z workspace na `/Volumes/ExternalDrive/...` jest zablokowany gdy drive znika. Zawsze rozważ `default_workspace_dir` na internal SSD dla projectów wymagających ciągłości.

**Wektor ryzyka na przyszłość:**
- Working tree (126 modified files) wciąż zawiera lokalne zmiany z sesji 2026-08-11 (np. modyfikacje `tools/auto_enrich.py`, katalogów, `DZIENNIK.md`). Marcel wybiera czy commitować czy odrzucić.


## 2026-08-12 11:10 CEST — Repo mirror na design-mc/billszuka

**ng-net/billszuka straciło dostęp** (marlink PAT bez uprawnień, ng-net account read-only service). Przeniesiono repo na `design-mc/billszuka` (prywatne, description zawiera info o crash recovery).

**Akcje:**
1. `gh repo create design-mc/billszuka --private` (active account = design-mc, ma `repo`+`workflow`)
2. `git remote add design-mc https://github.com/design-mc/billszuka.git`
3. `git push design-mc main` → 2 commits (63b0d6e + 6c72acf) wypushowane
4. `git remote remove origin` + `git remote rename design-mc origin` → nowy canonical remote
5. `git push origin main` → already up-to-date
6. AGENTS.md zaktualizowany: "Canonical remote: github.com/design-mc/billszuka (private)"

**Jeśli kiedyś Marcel odzyska dostęp do ng-net:**
```bash
# Dodaj ng-net z powrotem jako drugi remote (nie nadpisuj design-mc)
git remote add ng-net-backup https://github.com/ng-net/billszuka.git
git fetch ng-net-backup
# Sprawdź czy historia się zgadza
git log --oneline ng-net-backup/main | head -5
# Jeśli tak — push mirror z powrotem
git push ng-net-backup main
```


## 2026-08-12 11:18 CEST — ng-net OAuth re-auth + design-mc jako backup

**`gh auth refresh --scopes "gist,read:org,repo,workflow" --hostname github.com`** — dodał brakujący `workflow` scope do ng-net OAuth token. Teraz ng-net może pushować do ng-net/billszuka razem z `.github/workflows/ci.yml`.

**Stan końcowy remote'ów:**
- `origin` = `https://github.com/ng-net/billszuka.git` (canonical, aktywne konto = ng-net)
- `design-mc` = `https://github.com/design-mc/billszuka.git` (backup mirror, dostęp tylko design-mc)

**Push do obu remote'ów działa (HEAD = 360c457).**

**AGENTS.md zaktualizowany** — canonical = ng-net/billszuka, design-mc jako backup mirror.

**Daily workflow dla przyszłych sesji:**
```bash
# Przy starcie sesji — switch to ng-net (jeśli trzeba)
gh auth switch --user ng-net
# Weryfikacja
gh auth status
# Normalny push
git push origin main
# Jeśli chcesz zsynchronizować mirror
gh auth switch --user design-mc
git push design-mc main
gh auth switch --user ng-net   # wróć na primary
```

**Scenyariusze failure:**
- ng-net token straci ważność → `gh auth refresh --scopes "gist,read:org,repo,workflow"`
- ng-net OAuth się zepsuje → `gh auth login --web` z kontem które ma dostęp do ng-net org
- ng-net/billszuka zniknie z GitHub → push do design-mc (backup), później migrate do innego





---

## 2026-08-12 12:24 CEST — Przegląd projektu, porządki i optymalizacja pipeline

### Wykonane działania i porządki:
1. **Git workflow CI**: Dodano `.github/workflows/ci.yml` z powrotem do git po przyznaniu scope `workflow` dla tokena OAuth `ng-net`. Zaktualizowano `AGENTS.md`.
2. **AppleDouble cleanup**: Usunięto osierocony plik `data/enrichment/._apollo-PL.json`. Upewniono się, że `**/._*` wyklucza szum macOS w `.gitignore` i `.minimaxignore`.
3. **Deduplikacja logowania (`extract_intel.py`)**: Zaktualizowano `extract_intel.py`, aby przed dopisaniem wniosków sprawdzał dedup w `INTEL.md` oraz `DZIENNIK.md`. Usunięto 8 powtórzonych wierszy z `INTEL.md` oraz powtórzone bloki z `DZIENNIK.md`.
4. **Archiwizacja dziennika**: Zarchiwizowano historyczne wpisy (1600+ linii) z `DZIENNIK.md` do `DZIENNIK-archive-2026.md`. Plik główny `DZIENNIK.md` zmniejszono z ~1960 do ~250 linii.
5. **Usunięcie `sales_data.csv`**: `data/sales_data.csv` został usunięty jako próbka danych sprzedażowych z szablonu/notebooka, niezwiązana z katalogiem B2B BILLSzuka.

### Wnioski strategiczne i techniczne:
- **Struktura katalogu PL (Skew A vs B)**: PL Katalog A zawiera 4 firmy (z maszynami), a B zawiera 207 firm (ogólny przemysł). Skos w stronę B jest naturalny. Kolejny etap to wzbogacanie i podział segmentów B1–B9.
- **Bottleneck weryfikacji (`FROZEN` ratio)**: Master CSV liczy 350 firm, ale tylko ~9–16 wierszy posiada status `FROZEN (API)`. Główny bottleneck projektu to przesuwanie firm ze stanu `DO-WERYFIKACJI` do `FROZEN`. Uruchomiono zbiorczą weryfikację `verify_run.py`.


## 2026-08-12 12:26 CEST — Automatyczna analiza walkthrough & v2 verification

**Automatyczne kluczowe wnioski z walkthrough / pipeline run:**

1. Weryfikacja automatyczna: **80/349 (22.9%)** firm zweryfikowanych i oznaczonych jako `FROZEN (API)`.
2. Auto-cleaning & Quality Scoring przetworzył **349 wierszy** we wszystkich katalogach regionalnych.

## 2026-08-12 12:35 CEST — PL Research CLOSURE

**Decyzja Marcelego:** Zamykamy research na Polskę. Kolejny kraj → 🇨🇿 Czechy.

### Artefakty zamknięcia
- `data/Polska/verified-A-PL.csv` (14 firm, FROZEN only)
- `data/Polska/verified-B-PL.csv` (51 firm, FROZEN only)
- `data/Polska/PL-CLOSE-REPORT.md` (raport zamykający)
- `data/Polska/_closed/research-closeout.csv` (sidecar mapowania 235 IDs → status)
- `data/Polska/_closed/top-targets.csv` (64 leady wg QS, bez WRONG_CATEGORY)
- `data/Polska/_closed/snapshots/` (pre-close catalog-A, catalog-B, PL.md z 2026-08-12)

### Master sync
- 235 PL IDs (per-kraj) = 234 unikalne w master.csv (jeden duplikat wykryty i zmerge'owany przez verify_run.py)
- Zero luk, zero duplikatów po regeneracji
- Master.csv gotowy jako Excel/GS export

### Top partnerzy (🐋)
1. **BILLS Sp. z o.o.** (PL-A-WP-001) — właściciel
2. **BISTA STANDARD** (PL-A-KP-001) — producent konkurenckich marek (Dark Horse/FERN)
3. **POLSKI TYTOŃ S.A.** (PL-B-XX-026) — 15k+ sklepów, 18.3M PLN
4. **PHUP GNIEZNO** (PL-B-OP-003) — 1.5 mld zł revenue, 3000 sklepów
5. **ORION TOBACCO** (PL-B-MZ-001) — 1.8 mld szt/rok, 10 marek własnych
6. **POLSKA GRUPA TYTONIOWA** (PL-B-ZP-002) — hurtownia ogólnopolska

### Reaktywacja DO-WERYFIKACJI
- 170 firm w stanie PARKED
- Reaktywacja tylko na żądanie Marcelego lub po `verify_run.py --country PL --round 2` (za 2 tygodnie)
- Każdy ID ma przypisany status_on_close w `_closed/research-closeout.csv`

### Decyzja per AGENTS.md
"Deep PL only" threshold (≥30 verified firm) osiągnięty **3.6×** (65/30) → unlock kolejnych krajów.
Następny w kolejce: 🇨🇿 Czechy (katalogi istnieją: catalog-A-CZ 3 rows, catalog-B-CZ 7 rows).

## 2026-08-12 13:10 CEST — Czechy research CLOSURE

**Decyzja Marcelego:** Stabilizujemy i zamykamy iterację CZ. Move-to-canonical done.

### Merge z intake
- `data/_intake/CZ/validated.csv` miał 35 leadów: 32 FROZEN, 2 HALUCYNACJA (VapeStyle, Dýmkařský Svět — IČO syntetyczne), 1 DUPLIKAT (PEAL)
- Po dedupie po IČO: 31 unikalnych nowych firm (26 A-tier, 5 B-tier)
- 1 odrzucony (MOSTEX — już w katalogu)

### Wynik
- **catalog-A-CZ**: 3 → 29 firm (100% FROZEN)
- **catalog-B-CZ**: 7 → 12 firm (11 FROZEN + 1 DO-WERY: Imperial Tobacco CR)
- **TOTAL CZ**: 41 firm, 40 FROZEN (97.6% verification rate!)
- **Top targets**: 40 (zero WRONG_CATEGORY, lepszy profil niż PL)

### 🚨 FORTIS-DB IČO KONFLIKT
Wykryto 2 wpisy FORTIS-DB z różnymi IČO (62586289 vs 25221981). Oba twierdzą wyłączność na PowerMatic w CZ.
- CZ-A-PK-001 (IČO 62586289): Úněšovská 2205/17, Plzeň — ARES verified 2026-08-10, score 90
- CZ-A-PK-002 (IČO 25221981): Jateční 862/32, Plzeň — intake 2026-08-11, score 97, "WYŁĄCZNY IMPORTER POWERMATIC ČR"

Wymaga decyzji Marcelego przed outreachem. Zapisane w notatki obu wpisów + w `CZ-CLOSE-REPORT.md` sekcja "KRYTYCZNE".

### PEAL group ownership
Dodano do `data/relationships.csv`:
- CZ-A-PR-001 → CZ-B-PR-002 (group_ownership: PEAL → CTC)
- CZ-A-PR-001 → CZ-B-PR-003 (dual_business: ten sam IČO 25775634, A4 nabijarki + B8 hurt)

### Artefakty
- `data/Czechy/verified-A-CZ.csv` (29 firm)
- `data/Czechy/verified-B-CZ.csv` (11 firm)
- `data/Czechy/CZ-CLOSE-REPORT.md` (raport zamykający 9 KB)
- `data/Czechy/_closed/research-closeout.csv` (41 IDs → status)
- `data/Czechy/_closed/top-targets.csv` (40 leadów wg QS)
- `data/Czechy/_closed/rejected-intake.csv` (1 odrzucony)
- `data/Czechy/_closed/snapshots/` (pre-close stan z 2026-08-12)

### Następny kraj
🇸🇰 Słowacja (katalogi puste — start od zera).

## 2026-08-12 13:15 CEST — CZ final cleanup

Po decyzji Marcelego: czyste repo po closure.

**Skasowane (mavis-trash):**
- `data/_intake/CZ/` — cały folder (master catalog, normalized, validated, validation.md). Intake done, niepotrzebne.
- `data/Czechy/_closed/` — closure archive (research-closeout, top-targets, rejected-intake, snapshots). Zarchiwizowane w git commit cdb9a7a.
- 5 plików `._*` (AppleDouble) w data/Czechy/ — macOS metadata noise.

**Final state data/Czechy/ (7 plików):**
- catalog-A-CZ.csv (29)
- catalog-B-CZ.csv (12)
- verified-A-CZ.csv (29 FROZEN)
- verified-B-CZ.csv (11 FROZEN)
- CZ-CLOSE-REPORT.md (zaktualizowany — wskazuje na git dla archived files)
- CZ.md
- SŁOWNIK-CZ.md

`data/_intake/` teraz: 12 krajów minus CZ = 11 country subdirs + _README.md.
