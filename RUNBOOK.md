# BILLSzuka Runbook — odtwarzalne metody weryfikacji

> **Cel:** w 10-15 minut zweryfikować firmę (NIP/KRS/nazwa) w dowolnym kraju europejskim
> i uniknąć powtórzenia błędów z iteracji 1.
> **Zasada nadrzędna:** nie ufaj danym z listy — weryfikuj przez oficjalne API + web search.
>
> **Jak czytać ten plik:** sekcje są niezależne — wczytaj tylko tę, której potrzebujesz
> (np. `## PL` albo `## Pułapki`). Nie trzeba czytać całości.

---

## Komendy

```bash
python3 tools/billszuka.py compile              # przebuduj master.csv (24 katalogi, 35 kolumn)
python3 tools/billszuka.py verify               # weryfikacja API + aktualizacja flag/hashy
python3 tools/billszuka.py intake --iso CZ      # normalizacja nowego intake
python3 tools/billszuka.py search --country SK [--level L1]   # strategie L0-L11
python3 tools/orchestrate_11_levels.py --list
tools/clean_macos_metadata.sh [frontend]        # czyści AppleDouble ._* pliki (patrz Pułapka #10)
```

## Quick start (5 min, nowa sesja)

```bash
cd /Volumes/MC-BRAIN/Dev-Ext/BILLSzuka
ls .env && echo OK || echo "Brak .env"
git status && git remote -v

TOKEN=$(grep CEIDG_API_TOKEN .env | cut -d= -f2-)
KEY=$(grep OPENROUTER_API_KEY .env | cut -d= -f2-)

curl -s -H "Authorization: Bearer $TOKEN" \
  "https://dane.biznes.gov.pl/api/ceidg/v3/firmy?nazwa=BILLS&status=AKTYWNY" | head -c 200
curl -s "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/62586289" | head -c 200
curl -s -H "Authorization: Bearer $KEY" "https://openrouter.ai/api/v1/auth/key" | python3 -m json.tool
```

## Sekrety (`.env`, gitignored)

```bash
CEIDG_API_TOKEN=...      # CEIDG v3 (PL, JWT)
OPENROUTER_API_KEY=...   # LLM batch, $ budget
APOLLO_MCP_KEY=...       # Apollo.io (nieaktywny — Free plan 403, patrz §AUTO_ENRICH)
GOOGLE_MAPS_API_KEY=...  # Places (New) API — patrz SETUP-GOOGLE-MAPS.md
SERPAPI_KEY=...          # search fallback
BRAVE_API_KEY=...        # search — PREFEROWANY nad DDG (patrz Pułapka #9), 2000/mies free
```
Odczyt: `KEY=$(grep NAZWA .env | cut -d= -f2-)`

## Skille zainstalowane

| Skill | Do czego |
|---|---|
| `useosint` | Router OSINT, start głębokiej analizy |
| `x-ray-a-company` | Deep dive: owners, structure, financials |
| `enrich-lead` | Masowy enrichment (wymaga API) |
| `crawl4ai` | Crawling stron z JS/anti-bot |
| `apify-public-registries` | Scrapery rejestrów, wolumen >100/skan |
| `vies-api` | Szybki sanity check NIP/VAT |

## Web search — wzorce i uwaga krytyczna

```
"<FIRMA>" KRS sp. z o.o. <miasto> NIP rejestracja   # PL
"<FIRMA>" IČO <miasto> ARES                          # CZ
"<FIRMA>" company code <miasto> register             # ogólny EU
site:rejestr.io "<FIRMA>"                            # PL aggregator
```
**⚠️ NIE UŻYWAJ `html.duckduckgo.com` scraping.** Blokuje boty → 14KB "you are a bot"
landing page, wygląda jak 0 wyników (silent fail, patrz Pułapka #9).
**Kolejność preferencji:** 1) Brave Search API (`BRAVE_API_KEY`) 2) SerpAPI/Google CSE
3) Playwright headless (`crawl4ai` skill) 4) bezpośredni scrape docelowej domeny.

## OpenRouter — koszt per model

```
meta-llama/llama-3.1-8b-instruct   # ~$0.0001/1k tok — DEFAULT dla batch/cross-validation
anthropic/claude-3.5-sonnet        # ~$3/1M tok — tylko do finalnej syntezy
```
100 batch calls na 8B ≈ $0.01. Zawsze zaczynaj mały, eskaluj tylko gdy trzeba.

---

## Kraje — rejestry, automatyzacja, pułapki

Format per kraj: **Podstawowy** (nazwa/adres/status) · **Finansowy** (bilans) ·
**Upadłości** · **VAT** · **Automatyzacja** (co już mamy) · **Pułapki**.

### 🇵🇱 PL — priorytet, 2 ścieżki (JDG vs spółka)

- Podstawowy (JDG): `dane.biznes.gov.pl/api/ceidg/v3/firmy?nip=X` — Bearer token
- Podstawowy (spółka): KRS lookup-only (**brak search po nazwie**) —
  `api-krs.ms.gov.pl/api/krs/OdpisAktualny/{KRS}` — brak auth, 20/min.
  Znajdź KRS przez `wyszukiwarka-krs.ms.gov.pl` lub web_search.
- REGON (BIR1.1): `api.stat.gov.pl/Home/RegonApi` — wymaga USER_KEY (email)
- Finansowy: `ekrs.ms.gov.pl/rdf/pd/search_df?Krs={KRS}` (.xml bilans+RZiS);
  paid alt: rejestr.io (0.5 zł/dok), krs-online.com.pl
- Upadłości: KRZ — `prs.ms.gov.pl/krz`
- VAT: biała lista — `podatki.gov.pl/wykaz-podatnikow-vat-wyszukiwarka`
- Inne: sankcje MSWiA, rejestr pośredników tytoniowych KAS (kontakt weryfikacyjny),
  aleo.com, panoramafirm.pl
- **Automatyzacja:** `tools/krs_search.py --nip X` / `--krs X` / `--krs X --financials`
- **Pułapki:** CEIDG = tylko JDG i s.c. (spółka cywilna); sp. z o.o./S.A./sp.k./sp.j. →
  KRS. KRS API nie ma search po nazwie/NIP. 3/6 KRS z listy użytkownika w iteracji 1
  wskazywały na obce firmy — **zawsze weryfikuj**. PKD 46.35Z to trop, nie dowód (25
  firm z tym kodem, 0 realnych hurtowni tytoniu).

### 🇨🇿 CZ — najłatwiejszy kraj, 1 request

- Podstawowy + finansowy w jednym: `ares.gov.cz/ekonomicke-subjekty-v-be/rest/
  ekonomicke-subjekty/{ICO}` (+`/financni-udaje`), search by name też dostępny — brak auth
- Upadłości: ISIR — `isir.justice.cz`
- Spółki (odpis/likwidacja): `or.justice.cz`; Živnosti (JDG): `rzp.cz`
- **Pułapki:** nazwa w `obchodniJmeno` (bez pełnej formy prawnej); NACE 46350 =
  wholesale tobacco vs 471 = retail — nie mylić; 1 IČO z listy iteracji 1
  (25221981) wskazywał na zupełnie inną firmę.

### 🇸🇰 SK — brak JSON API, web search → ORSR

- Podstawowy: ORSR, formularz HTML — `orsr.sk/hladaj_subjekt.asp`. Znajdź IČO (8 cyfr)
  przez `web_search: "<FIRMA>" IČO Slovensko` lub `site:orsr.sk "<FIRMA>"`
- Finansowy: RUZ — `registeruz.sk` (.xml)
- Živnosti (JDG): `zrsr.sk`
- VAT/DIČ: `financnasprava.sk`

### 🇷🇴 RO — ONRC płatny, użyj agregatorów

- Podstawowy: ONRC paid (~8 lei/odpis) lub darmowo przez agregatory:
  `web_search: site:termene.ro <FIRMA>` (+ bilans), `site:listafirme.ro <FIRMA>`,
  `"CUI <numer> <FIRMA>"`
- VAT/bilanț: `anaf.ro` · Upadłości: `bpi.just.ro`
- **Format:** CUI ≠ SIREN/SIRET. Nr rejestrowy: `J40/1234/2005` (sąd/numer/rok).
- **Pułapka:** plain packaging regulacje mogą wykluczać niektóre marki tytoniowe.

### 🇱🇹 LT — SAU open data (NIE rekvizitai — Cloudflare 403)

- Podstawowy: `get.data.gov.lt/datasets/gov/rc/jar/iregistruoti/JuridinisAsmuo?ja_kodas=X`
  — no-auth, jedyny działający publiczny path. Filtr **tylko po `ja_kodas`** (9 cyfr),
  brak name-search. Adres = UUID ref do zewn. Address Registry (niedostępny) → kolumna
  adres nie jest back-fillowana. Legal form/status też UUID refs → lookup przez
  `formos_statusai/Forma` i `/Statusas`.
- **Automatyzacja:** `tools/lt_open_data.py`, routed przez `verify_lt_row()` w
  `verify_api.py` (`COUNTRY_API["LT"] = "jar"`)
- Finansowy/przeglądowy (manualnie, za Cloudflare): `rekvizitai.vz.lt`
- Registrų centras (pełne dane): `registrucentras.lt` · Upadłości: tamże
  `/nemokumoregistras` · VAT: `vmi.lt`
- **PVM format:** LT+9 cyfr (krajowe) lub LT+12 (wewn.). Canonical dla UAB =
  LT + ja_kodas.
- **Specjalny przypadek:** grupa Sanitex ma sister firms LT/LV/EE pod jednym brandem.
- **Live check 2026-08-10:** 10 firm → 1 FROZEN (SANITEX), 9 PENDING_API (placeholder
  "do weryfikacji", brak ja_kodas).

### 🇱🇻 LV

- Podstawowy: UR — `info.ur.gov.lv` (web search: `"<FIRMA>" reģistrs Latvija PVN`)
- Finansowy/ryzyko: Lursoft (`lursoft.lv`, free preview) · DataMe.lv (.pdf)
- VAT: `vid.gov.lv` · Upadłości: `ur.gov.lv/lv/maksatnespejas-registrs`

### 🇪🇪 EE — najlepszy cyfrowy rejestr w regionie ⭐

- Podstawowy + finansowy: `ariregister.rik.ee` — autocomplete JSON
  `/est/api/autocomplete?q=<nazwa>` (**tylko po nazwie, NIE po KMKR/VAT**) + detail
  page scrape dla KMKR/VAT, EMTAK/NACE, kapitał, status
- VAT: KM = EE + 9 cyfr, status w EMTA (`emta.ee`) · Licencje fin.: `fi.ee`
- **Automatyzacja:** `tools/ee_ariregister.py`, `verify_ee_row()` w `verify_api.py`
  (`COUNTRY_API["EE"] = "ariregister"`)
- **Live check:** 10/10 zweryfikowane — 8 FROZEN, 2 DO-WERYFIKACJI (detal B2C, brak
  wpisu jako hurtownia).

### 🇫🇷 FR — *future scope (poza scope 12 krajów, 2026-08-31)*

> **Status 2026-08-31:** FR ma 0 wierszy w `data/master.csv` (usunęliśmy 22 rekordy).
> Ta sekcja jest zachowana jako playbook na wypadek powrotu FR do scope.

- Podstawowy (oficjalny, darmowy): `annuaire-entreprises.data.gouv.fr` — SIREN/SIRET,
  dirigeants, bilans
- Paid ale najlepsze: `pappers.fr/api` · free z limitem: `societe.com`
- Legal announcements/upadłości: `bodacc.fr` · IP: `inpi.fr` · paid odpis: `infogreffe.fr`
- **Format:** SIREN = 9 cyfr (firma), SIRET = 14 cyfr (z adresem).
- **Kontekst branżowy:** rolling tobacco to duży segment we Francji.
- **Dlaczego poza scope:** Marceli 2026-08-31 — projekt pozostaje przy 12 krajach V4+Balkans+Baltics.

### 🇲🇩 MD (poza UE)

- Podstawowy: `cis.gov.md` (IDNO = 13 cyfr) · VAT: `sfs.md`
- Procedura jak RO, ale poza UE = szara strefa prawna.

### 🇧🇬 BG

- Podstawowy + bilans: `portal.justice.bg` (EIK) — też przez
  `web_search: "ЕИК <numer> <FIRMA>"`
- Upadłości: `public.registryagency.bg` · VAT (DDS): `nap.bg`

### 🇸🇮 SI — drugi najlepszy po EE ⭐

- Wszystko w jednym: `ajpes.si` — matična + bilans + RZiS (.pdf/.xml)
- Insolvenčni register: `ajpes.si/Register` · VAT (DDV): `furs.si`
- **Nieautomatyzowane, ale API jest darmowe** — warto zrobić `tools/si_ajpes.py`.

### 🇭🇷 HR

- Podstawowy: `sudreg.pravosudje.hr` (OIB = 11 cyfr, MBS, zarząd) — też upadłości
  (Stečajni registar) na tej samej domenie
- Finansowy: FINA — `fina.hr` (.xml) · VAT (PDV): `porezna-uprava.hr`

### 🌍 Cross-country universals (działają wszędzie)

| Narzędzie | URL | Co daje |
|---|---|---|
| VIES | ec.europa.eu/taxation_customs/vies | Walidacja VAT-EU (27 krajów) |
| OpenCorporates | opencorporates.com | ~200/mies free, mirror 100+ rejestrów |
| OpenSanctions | opensanctions.org | Listy sankcyjne EU/ONZ/US/UK |
| GLEIF | gleif.org | LEI lookup globalny |
| EU Open Data Portal | data.europa.eu | Dane oficjalne EU |

**Minimalny pakiet weryfikacji (każdy kraj):** 1) rejestr podstawowy 2) VIES
3) rejestr upadłości 4) (opcjonalnie) rejestr finansowy 5) lista sankcyjna.
Bez tych 5 → dane = "niepotwierdzone ⚠️".

**Priorytet kolejności (po PL):** 1. SI (AJPES, pakiet kompletny) 2. EE
(e-Äriregister, najlepszy UX) 3. CZ (ARES + VIES, blisko + duży rynek).

**Brakujące integracje (budżet 100-200 PLN/mies. odblokowałby PL pełną
automatyzację; FR jest poza scope od 2026-08-31):** rejestr.io API (PL, 0.5 zł/dok), Pappers.fr API (FR, paid — future scope),
AJPES API (SI, free — warto zrobić), Lursoft API (LV, paid).

---

## Language reference — terminy branżowe per kraj

| Kraj | dystrybutor tytoniu | hurtownia | nabijarka/maszynka | akcesoria dla palaczy |
|---|---|---|---|---|
| PL | dystrybutor wyrobów tytoniowych | hurtownia papierosów | nabijarka do tytoniu | akcesoria dla palaczy |
| CZ | velkoobchodník tabákových výrobků | velkoobchod s tabákem | plnička cigaret | kuřácké potřeby |
| SK | distribútor tabakových výrobkov | veľkoobchod s tabakom | strojček na cigarety | fajčiarske potreby |
| RO | distribuitor de produse din tutun | depozit en-gros de țigări | mașină de umplut țigări | accesorii pentru fumători |
| LT | tabako gaminių platintojas | didmeninė prekyba tabako gaminiais | cigarečių pildymo mašina | rūkymo reikmenys |
| LV | tabakas izstrādājumu izplatītājs | vairumtirdzniecība tabaka | cigarešu pildīšanas mašīna | smēķētāju piederumi |
| EE | tubakatoodete edasimüüja | tubaka hulgimüük | sigarettide täitmise masin | suitsetamistarbed |
| FR | distributeur de produits du tabac | grossiste en tabac | machine à rouler les cigarettes | accessoires pour fumeurs |
| MD | distribuitor de produse din tutun | depozit en-gros țigări | mașină de umplut țigări | accesorii pentru fumători |
| BG | дистрибутор на тютюневи изделия | търговия на едро тютюн | машина за пълнене на цигари | аксесоари за пушачи |
| SI | distributer tobačnih izdelkov | trgovina na debelo tobak | strojček za cigarete | kadilski pripomočki |
| HR | distributer duhanskih proizvoda | veleprodaja duhana | stroj za punjenje cigareta | pribor za pušače |

**Tip:** dodaj lokalną walutę do query hurtowni ("hurtownia papierosów zł",
"velkoobchod tabák Kč") — odfiltrowuje zagraniczne strony.

---

## Pułapki (numerowane, unikalne dla ogólnej metodologii — country-specific w sekcji kraju)

1. **Halucynacje w danych źródłowych.** Iteracja 1: 3/6 KRS z listy → obce firmy, 5
   placeholderów "Oddział #1-5" nieistniejących, 1 NIP → CREMER zamiast FORTIS-DB.
   Zawsze weryfikuj identyfikator w oficjalnym API, nie ufaj etykiecie.
2. **KRS API = lookup only, nie search.** Workflow PL spółka: web_search → znajdź KRS →
   API lookup → (opcjonalnie) `x-ray-a-company` do głębszego researchu.
3. **CEIDG = tylko JDG.** Sp. z o.o. nigdy tam nie będzie — nie traktuj braku wyniku
   jako "firma nie istnieje".
4. **Nie tłumacz kodów między krajami.** Każdy rejestr ma własne pola/kody — sprawdź
   lokalne API zamiast zakładać analogię.
5. **macOS `._*` metadata files.** Zaśmiecają repo — `._*` musi być w `.gitignore`
   zawsze (już jest).
6. **Puste CSV w git.** Jeśli `*.csv` w `.gitignore`, potrzebna jawna allow-list:
   `!data/catalog-*.csv`.
7. **Mały LLM najpierw.** Llama 8B ~$0.0001/call vs Sonnet ~$0.003/call — eskaluj do
   Sonnet tylko do finalnej syntezy.
8. **PKD/NACE to trop, nie potwierdzenie.** Ludzie dodają kody przy rejestracji bez
   realnej działalności — zawsze cross-validate przez web_search oferty.
9. **DDG HTML scraping = silent fail.** `html.duckduckgo.com` blokuje boty → 14KB
   "you are a bot" page, regex parsing zwraca fałszywe "0 wyników znaleziono ✅".
   Fix: `test_11_levels.py` ma `is_ddg_blocked()` + 3-state PASS/SKIP/FAIL. Użyj
   `BRAVE_API_KEY` albo scrapuj domenę bezpośrednio.
10. **AppleDouble pollution na `/Volumes/MC-BRAIN` (sieciowy mount, nie APFS).**
    Każdy `npm install`/`git pull`/`cp` tworzy `._<plik>` shadow files (1 install
    frontend = 1028 plików). Fix: `tools/clean_macos_metadata.sh` (woła `dot_clean` +
    drugi pass na osierocone `._*`) — uruchamiaj po każdym `npm install` na tym mouncie.

---

## Gotowe wzorce query

**Pattern 1 — szybka weryfikacja 1 firmy (~30s):** znajdź identyfikator z listy →
API call → porównaj nazwa+adres → wpisz do CSV lub oznacz status.

**Pattern 2 — batch (10-30 firm, ~15-30 min):** web_search każdej → identyfikator →
loop API calls → diff lista vs API → `verification-report-{date}.md`.

**Pattern 3 — discovery nowego rynku (~2-4h):** web_search hurtowni w lokalnym
języku → sprawdź rejestr (np. BCE dla Belgii) → filtruj po PKD/NACE tobacco →
outreach list.

**Pattern 4 — cross-validation przez LLM:**
```python
import json, urllib.request
api_key = [l.split('=',1)[1].strip() for l in open('.env')
           if l.startswith('OPENROUTER_API_KEY=')][0]
prompt = f"""Oceń firmy pod kątem branży tytoniowej. Dla każdej: real_pct, type
(A=z nabijarkami/B=branza/nieznane), komentarz. NIE WYMYŚLAJ DANYCH.
{json.dumps(firms, ensure_ascii=False)}"""
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=json.dumps({"model": "meta-llama/llama-3.1-8b-instruct",
                      "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.1, "max_tokens": 1500}).encode(),
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
print(json.loads(urllib.request.urlopen(req).read())['choices'][0]['message']['content'])
```

## Pipeline weryfikacji (proponowany, per firma)

```
CSV (NIP/IČO/CUI/SIREN/IDNO/OIB) → rejestr podstawowy (status/adres/forma) →
VIES (VAT aktywny?) → rejestr upadłości → rejestr finansowy (opcjonalnie) →
✅ FROZEN (wszystko OK) lub ⚠️ DO-WERYFIKACJI (czegoś brak)
```
Stan: PL (KRS/REGON) zautomatyzowane. LT, EE zautomatyzowane (skrypty w sekcjach
krajów). Reszta → manual przez `verify_api.py` + recipe z sekcji kraju.

## §AUTO_ENRICH — decydent/stanowisko/telefon/email/linkedin pipeline

`tools/auto_enrich.py` — agent web_search → OpenRouter DeepSeek extract → CSV apply.

```bash
python3 tools/auto_enrich.py leads                       # firmy z decydent == "do ustalenia"
python3 tools/auto_enrich.py process --csv data/Polska/catalog-B-PL.csv \
  --id PL-B-XX-001 --name "FIRMA SP. Z O.O." --city "Warszawa" --country "PL" \
  --search-results "$(cat /tmp/search.txt)"               # extract+apply+mark_done
python3 tools/auto_enrich.py extract --name "FIRMA" --city "..." --country "PL" \
  --search-results "..."                                  # tylko extract, bez zapisu
python3 tools/auto_enrich.py apply --csv ... --id ... --json '{...}'  # tylko apply
```
Progress: `data/.verify-state/enrichment-progress.json` (resumable, `{done: {key@csv:
{ts, name, country, confidence, fields, had_error}}}`).

**Wynik 2026-08-11:** 57/59 = 96.6% success. Kraje: BG/HR/CZ/PL/FR/RO/SK/EE/MD.
**Limity:** brak search API key → agent musi wołać `web_search` tool manualnie (2
calls/lead); LLM czasem zwraca opis roli zamiast URL w polu `linkedin`.
**Apollo alternatywa** (nieaktywna, Free plan 403): `tools/apollo_enrich.py` — gotowy
do wpięcia w `verify_api.py` dispatcher po upgrade planu.

## Kontakty weryfikacyjne (gdy API nie wystarcza)

| Kraj | Kto | URL |
|---|---|---|
| PL | KAS, rejestr pośredników tytoniowych | gov.pl/web/kas/rejestr-posredniczacych-podmiotow-tytoniowych |
| CZ | Celní správa | celnisprava.cz |
| EU | EU Common VAT Register | ec.europa.eu/taxation_customs/vies |

## Dodawanie nowego kraju (nie z listy 12)

1. `useosint` skill → corporate-registries subskill
2. Wikipedia: "Company register [Country]" — sprawdź czy jest otwarte API
3. Dodaj sekcję `### 🇽🇽 KOD` do tabeli krajów wyżej (jeden pass, nie trzy)
4. Jeśli brak API: web_search + lokalny rejestr .gov
5. Dodaj wiersz do Language reference
6. Utwórz `data/countries/{KOD}.md` + CSV stub w `data/`

## Changelog

| Data | Zmiana |
|---|---|
| 2026-08-10 | v1 — iteracja 1, 30 firm z listy: 5 OK, 4 ZŁY, 5 FABRYKAT, 11 DO_WERYFIKACJI |
| 2026-08-10 | DDG blocking fix (`is_ddg_blocked`), macOS metadata cleanup tool |
| 2026-08-11 | §AUTO_ENRICH pipeline: 57/59 decydentów w 9 krajach, 96.6% sukces |
| — | v2 — skonsolidowano 3 powielone sekcje per-kraj w jedną; skrócono ~45% |
