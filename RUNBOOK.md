# BILLSzuka Runbook — odtwarzalne metody weryfikacji

> **Cel:** w 10-15 minut zweryfikować firmę (NIP/KRS/nazwa) w dowolnym kraju europejskim i uniknąć powtórzenia błędów z iteracji 1.
>
> **Zasada nadrzędna:** nie ufaj danym z listy — weryfikuj przez oficjalne API + web search.

---

## 🧰 TOOLBOX (co mam + jak używać)

### 1. Tokeny i sekrety (plik `.env`, gitignored)

```bash
# /Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/.env
CEIDG_API_TOKEN=eyJ...   # JWT do CEIDG v3 (Polska)
OPENROUTER_API_KEY=sk-or-v1-...  # OpenRouter (LLM, $2 budget)
```

Odczyt: `KEY=$(grep NAZWA .env | cut -d= -f2-)`

### 2. Programistyczne API rejestrów (free, szybkie)

| Kraj | API | Endpoint | Auth | Co zwraca |
|---|---|---|---|---|
| 🇵🇱 PL (JDG) | **CEIDG v3** | `https://dane.biznes.gov.pl/api/ceidg/v3/firmy?nazwa=X&status=AKTYWNY` | Bearer token | NIP, REGON, adres, status, PKD |
| 🇵🇱 PL (JDG by NIP) | CEIDG v3 | `?nip=X` | Bearer | j.w. |
| 🇵🇱 PL (KRS lookup) | KRS MS | `https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{KRS}` | **brak** | Pełny odpis firmy |
| 🇨🇿 CZ | **ARES** | `https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ICO}` | **brak** | Název, adres, NACE, datum vzniku, DIČ |
| 🇸🇰 SK | ORSR | `https://orsr.sk` (web search) | brak | Obchodný register, potrebuje IČO |
| 🇪🇪 EE | e-Äriregister | `https://ariregister.rik.ee` (web search) | brak | Najbardziej cyfrowy rejestr w regionie |
| 🇱🇹 LT | rekvizitai.vz.lt | `https://rekvizitai.vz.lt/en/company/...` (web search) | brak | Įmonės kodas, PVM, adres, vadovas |
| 🇸🇮 SI | AJPES | `https://www.ajpes.si` (web search) | brak | Davčna številka, matična |
| 🇪🇺 EU VAT | VIES | `http://ec.europa.eu/taxation_customs/vies/` | brak | Walidacja VAT EU |

### 3. Web search (do znajdywania KRS/NIP gdy nie znam)

Wzorce (z przykładami):
```
"<FIRMA>" KRS sp. z o.o. <miasto> NIP rejestracja   # PL firm
"<FIRMA>" IČO <miasto> ARES                          # CZ firm
"<FIRMA>" company code <miasto> register            # EU firm
"site:rejestr.io" "<FIRMA>"                          # PL KRS aggregator
```

**⚠️ NIE UŻYWAJ DuckDuckGo HTML scraping do production research.** `html.duckduckgo.com` blokuje niezautoryzowane boty i zwraca 14KB "you are a bot" landing page zamiast wyników. `tools/test_9_levels.py` (po fix z 2026-08-10) wykrywa to i raportuje jako `⚠️ SKIP` zamiast fałszywego `✅ PASS`.

**Zalecane (w kolejności preferencji):**
1. **Brave Search API** — `BRAVE_API_KEY` w `.env`. `tools/test_9_levels.py` automatycznie użyje Brave jeśli key jest obecny. Darmowy tier: 2000 queries/mies.
2. **SerpAPI / Google CSE** — płatne, niezawodne. Dodaj `SERPAPI_KEY` lub `GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX` i rozszerz `get_search_provider()` w `test_9_levels.py`.
3. **Headless browser** (Playwright) z rate-limiting + user-agent rotation — w `skills/crawl4ai-skill` lub bezpośrednio. Wymaga większej infra.
4. **Bezpośrednie scrape docelowych domen** (orzeczenia.nsa.gov.pl, aleo.com) — omijają ograniczenia wyszukiwarek, ale wymagają per-site parser.

### 4. Zainstalowane skille (do głębszego researchu)

| Skill | Co robi | Kiedy używać |
|---|---|---|
| `useosint` | Router do OSINT subskills (references na useosint.com) | Start głębokiej analizy |
| `x-ray-a-company` | Deep dive — owners, structure, financials | Gdy znam firmę i chcę pełny profil |
| `enrich-lead` | Lead enrichment (Hunter/Apollo-style) | Do masowego enrichementu (wymaga API) |
| `crawl4ai` | LLM-friendly crawling | Gdy strona wymaga JS/anti-bot |
| `apify-public-registries` | Apify scrapers do rejestrów | Duże wolumeny (>100/skan) |
| `vies-api` | Walidacja VAT EU | Szybka sanity check NIP/VAT |

### 5. OpenRouter (LLM batch, ~$0.0001-0.001 per call)

```python
# Tani model do cross-validation
model = "meta-llama/llama-3.1-8b-instruct"  # ~$0.0001/1k tokens
# Mądrzejszy model do syntezy
model = "anthropic/claude-3.5-sonnet"  # ~$3/1M tokens (używaj oszczędnie)
```

---

## 🌍 PER-KRAJU RECIPES

### 🇵🇱 POLSKA — 2-etapowa weryfikacja

**JDG (jednoosobowa działalność):**
```bash
TOKEN=$(grep CEIDG_API_TOKEN .env | cut -d= -f2-)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://dane.biznes.gov.pl/api/ceidg/v3/firmy?nip=NNNNNNNNNN" | python3 -m json.tool
```

**Sp. z o.o. / S.A. / Sp. k.:**
```bash
# 1. Znajdź KRS (CEIDG nie ma spółek)
web_search: "<FIRMA>" KRS NIP <miasto>
# 2. Lookup po KRS
curl -s "https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{KRS}" | python3 -m json.tool
```

**Typowe pułapki PL:**
- ⚠️ CEIDG NIE ma sp. z o.o. — używaj KRS API (tylko lookup, nie search!)
- ⚠️ KRS z listy użytkownika 3/6 wskazywał na obce firmy — zawsze weryfikuj
- ⚠️ Sp. cywilna (s.c.) = CEIDG, Sp. jawna (sp.j.) = KRS

### 🇨🇿 CZECHY — 1-etapowa weryfikacja (najłatwiejszy kraj)

```bash
curl -s "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/ICO" | python3 -m json.tool
```

ARES zwraca: `obchodniJmeno`, `sidlo`, `pravniForma`, `datumVzniku`, `dic`, `czNace[]`, status.

**Typowe pułapki CZ:**
- ⚠️ Nazwa firmy może być w `obchodniJmeno` (bez "Společnost s ručením omezeným")
- ⚠️ NACE 46350 = wholesale tobacco, 471 = retail
- ⚠️ 1 IČO z listy użytkownika (25221981) to zupełnie inna firma (CREMER nieruchomości)

### 🇸🇰 SŁOWACJA — web search IČO → ORSR

ORSR nie ma JSON API. Procedura:
1. Web search: `"<FIRMA>" IČO Slovensko` 
2. Pobierz IČO (8 cyfr, bez "SK")
3. Otwórz `https://orsr.sk/hladaj_subjekt.asp?ession=&O=ICO` (formularz HTML)

**Szybsza alternatywa:** użyj `web_search` z `site:orsr.sk "<FIRMA>"`

### 🇷🇴 RUMUNIA — ONRC + search aggregators

ONRC API wymaga opłaty (8 lei za odpis). Alternatywy:
- `web_search: "site:confidas.ro <FIRMA>"` (aggregator darmowy)
- `web_search: "site:listafirme.ro <FIRMA>"` 
- `web_search: "CUI <numer> <FIRMA>"` (rumuński tax ID)

**Sufiks:** Numer rejestrowy ma formę `J40/1234/2005` (sąd/numer/rok).

**Typowe pułapki RO:**
- ⚠️ CUI = fiscal code, NOT same as SIREN/SIRET
- ⚠️ Strong plain packaging — regulacje mogą wykluczać niektóre marki
- ⚠️ ONRC paid API = ~8 lei per query

### 🇱🇹 LITWA — rekvizitai.vz.lt

```bash
# Web search zazwyczaj wystarcza:
web_search: "site:rekvizitai.vz.lt <FIRMA>"
```

Litwa ma **jar.lt** (JAR) ale web search jest szybszy. PVM kod = LT + 9 lub 12 cyfr.

**Specjalny przypadek: Sanitex group** — LT/LV/EE mają sister firms pod jednym brandem.

### 🇱🇻 ŁOTWA — info.ur.gov.lv (web search)

Web search: `"<FIRMA>" reģistrs Latvija PVN`

### 🇪🇪 ESTONIA — ariregister.rik.ee (najlepszy w regionie)

```bash
# Bezpośredni URL (po wyszukaniu firmy)
https://ariregister.rik.ee/est?kood=XXXXXXXXX
```

KM = VAT, EE + 9 cyfr.

### 🇫🇷 FRANCJA — Pappers / Societe.com (najlepsze)

```bash
# Dla PL społeczności:
web_search: "site:pappers.fr <FIRMA>"
web_search: "site:societe.com <FIRMA> SIREN"
```

SIREN = 9 cyfr (firma), SIRET = 14 cyfr (z adresem).

**Specjalne:** Francuzi dużo palą tytoń tradycyjny — `rolling tobacco` to duży segment.

### 🇲🇩 MOŁDAWIA — cis.gov.md (poza UE)

IDNO = 13 cyfr. Procedura jak w Rumunii, ale poza UE = szara strefa.

### 🇧🇬 BUŁGARIA — portal.justice.bg

```bash
web_search: "site:portal.justice.bg <FIRMA>"
# lub
web_search: "ЕИК <numer> <FIRMA>"  # bułgarski EIK
```

### 🇸🇮 SŁOWENIA — AJPES

```bash
web_search: "site:ajpes.si <FIRMA>"
# lub
web_search: "davčna številka <FIRMA>"
```

### 🇭🇷 CHORWACJA — Sudski registar

```bash
web_search: "site:sudreg.pravosudje.hr <FIRMA>"
# OIB = 11 cyfr
```

---

## 🗣️ LANGUAGE REFERENCE — search terms per kraj

| Kraj | "dystrybutor wyrobów tytoniowych" | "hurtownia" | "nabijarka" / "maszynka" | "akcesoria dla palaczy" |
|---|---|---|---|---|
| 🇵🇱 PL | dystrybutor wyrobów tytoniowych | hurtownia papierosów | nabijarka do tytoniu / maszynka do papierosów | akcesoria dla palaczy |
| 🇨🇿 CZ | velkoobchodník tabákových výrobků | velkoobchod s tabákem | plnička cigaret / kuřácké potřeby | kuřácké potřeby |
| 🇸🇰 SK | distribútor tabakových výrobkov | veľkoobchod s tabakom | strojček na cigarety | fajčiarske potreby |
| 🇷🇴 RO | distribuitor de produse din tutun | depozit en-gros de țigări | mașină de umplut țigări | accesorii pentru fumători |
| 🇱🇹 LT | tabako gaminių platintojas | didmeninė prekyba tabako gaminiais | cigarečių pildymo mašina | rūkymo reikmenys |
| 🇱🇻 LV | tabakas izstrādājumu izplatītājs | vairumtirdzniecība tabaka | cigarešu pildīšanas mašīna | smēķētāju piederumi |
| 🇪🇪 EE | tubakatoodete edasimüüja | tubaka hulgimüük | sigarettide täitmise masin | suitsetamistarbed |
| 🇫🇷 FR | distributeur de produits du tabac | grossiste en tabac | machine à rouler les cigarettes | accessoires pour fumeurs |
| 🇲🇩 MD | distribuitor de produse din tutun | depozit en-gros țigări | mașină de umplut țigări | accesorii pentru fumători |
| 🇧🇬 BG | дистрибутор на тютюневи изделия | търговия на едро тютюн | машина за пълнене на цигари | аксесоари за пушачи |
| 🇸🇮 SI | distributer tobačnih izdelkov | trgovina na debelo tobak | strojček za cigarete | kadilski pripomočki |
| 🇭🇷 HR | distributer duhanskih proizvoda | veleprodaja duhana | stroj za punjenje cigareta | pribor za pušače |

**Tip:** Gdy szukasz hurtowni, **dodaj lokalną walutę**: "hurtownia papierosów zł", "velkoobchod tabák Kč" — pomaga odfiltrować zagraniczne strony.

---

## ⚠️ PUŁAPKI KTÓRE TRAWIAŁEM W ITERACJI 1

### 1. Halucynacje w danych źródłowych

**Co się stało:** Lista 30 firm od użytkownika zawierała 3 z 6 KRS wskazujących na obce firmy, 5 placeholderów "Oddział #1-5" które nie istnieją, 1 NIP prowadzący do CREMER nieruchomości zamiast FORTIS-DB.

**Lekcja:** ZAWSZE weryfikuj NIP/KRS/IČO w oficjalnym API. Jeśli użytkownik mówi "to firma X z KRS 12345", sprawdź czy KRS 12345 naprawdę należy do firmy X.

### 2. KRS API nie ma search endpoint

**Co się stało:** KRS API pozwala tylko na lookup po numerze KRS, NIE na search po nazwie/NIP.

**Lekcja:** Dla PL sp. z o.o. workflow to:
1. web_search → znajdź KRS
2. KRS API → lookup
3. (alternatywa) użyj `useosint/x-ray-a-company` skill do głębszego researchu

### 3. CEIDG jest TYLKO dla JDG

**Co się stało:** BILLS Sp. z o.o. (spółka) NIE jest w CEIDG. To wprowadza w błąd.

**Lekcja:**
- JDG (jednoosobowa) → CEIDG API
- Sp. z o.o., S.A., Sp. k., Sp. j. → KRS API (potrzebujesz KRS z web search)
- Sp. c. (spółka cywilna) → CEIDG (rejestracja wspólników)
- Sp. j. (spółka jawna) → KRS (rejestracja w KRS)

### 4. Brak pl z ARES / CEIDG z CN

W każdym kraju kody się zmieniają. Nie polegaj na tłumaczeniu — sprawdź lokalne API.

### 5. MacOS metadata files (._*)

Pliki `._*` to AppleDouble metadata. Zanieczyszczają repo. **Dodaj `._*` do .gitignore** zawsze.

### 6. Puste CSV w git

Jeśli `*.csv` jest w .gitignore, puste stub CSV nie wejdą do repo. Jawna allow-list: `!data/catalog-*.csv`.

### 7. Mniej LLM = lepiej przy bulk research

OpenRouter 8B Llama kosztuje ~$0.0001/call. 100 batch = $0.01. Claude 3.5 Sonnet = $0.003/call. **Zawsze zaczynaj od małego modelu**, eskaluj tylko do syntezy.

### 8. Nie ufaj "PKD 46.35Z = hurtownia tytoniowa" na ślepo

W CEIDG wiele osób dodaje PKD przy rejestracji bez realnej działalności. Wyszło 25 firm z PKD 46.35Z, ale żadna to realna hurtownia (wszystkie z dzisiejszą datą, nazwy z innych branż). **PKD to trop, nie potwierdzenie.**

### 9. DDG HTML scraping = silent fail (2026-08-10)

`https://html.duckduckgo.com/html/?q=...` blokuje boty bez JS/unauth headera. Zwraca 14KB "you are a bot" landing page (tytuł `DuckDuckGo`, brak `class="result__"`). Regex findall → 0 → **fałszywe `✅ Found 0 web results`**. Dotyczyło Levels 1, 2, 4, 6, 7, 8 w `tools/test_9_levels.py` przed fixem.

**Fix:** `test_9_levels.py` ma teraz `is_ddg_blocked()` check + 3-state outcome (PASS/SKIP/FAIL). Użyj `BRAVE_API_KEY` w `.env` albo bezpośrednio scrapuj docelowe domeny (orzeczenia.nsa.gov.pl, aleo.com).

### 10. macOS AppleDouble pollution na /Volumes/MC-BRAIN (2026-08-10)

`/Volumes/MC-BRAIN` to sieciowy mount (SMB/NFS, nie APFS). Każdy `npm install`, `git pull`, `cp` powoduje że kernel zapisuje `._<filename>` shadow files obok prawdziwych plików. Zaśmiecają `ls`, psują wildcard w shellach, zaśmiecają `git status`. Po jednym `npm install` dla `frontend/` znalazłem **888 plików `._*` w `node_modules/` + 76 w `data/.snapshots/` = 1028 łącznie**.

**Fix:**
- `tools/clean_macos_metadata.sh` — kanoniczne narzędzie, woła `dot_clean` + drugi pass na osieroconych `._*` (które `dot_clean` czasem pomija). Idempotentny.
- Uruchamiaj po każdym `npm install` na `/Volumes/MC-BRAIN` lub dodaj do post-install hook w `package.json`.
- `.gitignore` już poprawnie ma `._*` — nic nie wejdzie do repo nawet jeśli zapomnisz wyczyścić.

```bash
tools/clean_macos_metadata.sh           # czyści cały root
tools/clean_macos_metadata.sh frontend  # tylko frontend
```

---

## 🚀 QUICK START — 5 minut w nowej sesji

```bash
# 1. Sprawdź setup
cd /Volumes/MC-BRAIN/Dev-Ext/BILLSzuka
ls .env && echo "OK" || echo "Brak .env"
git status

# 2. Wczytaj tokeny
TOKEN=$(grep CEIDG_API_TOKEN .env | cut -d= -f2-)
KEY=$(grep OPENROUTER_API_KEY .env | cut -d= -f2-)

# 3. Sprawdź czy API działają
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://dane.biznes.gov.pl/api/ceidg/v3/firmy?nazwa=BILLS&status=AKTYWNY" | head -c 200
echo ""
curl -s "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/62586289" | head -c 200

# 4. Sprawdź ile masz budgetu OpenRouter
curl -s -H "Authorization: Bearer $KEY" "https://openrouter.ai/api/v1/auth/key" | python3 -m json.tool

# 5. Sprawdź git remote
git remote -v

# 6. Gotowe do pracy
```

---

## 📋 CHECKLIST — nowa firma w nowym kraju

- [ ] Sprawdź czy kraj ma API (tabela wyżej) — tak/nie
- [ ] Jeśli tak: wyciągnij NIP/IČO/CUI z listy użytkownika lub web_search
- [ ] Wykonaj API call
- [ ] Porównaj: nazwa z listy vs nazwa z API. **Inne? = zły identyfikator**
- [ ] Jeśli brak API: web_search `"<FIRMA>" <language> registry official`
- [ ] Sprawdź czy adres się zgadza
- [ ] Sprawdź datę powstania (jeśli zbyt świeża = podejrzane)
- [ ] Sprawdź NACE/PKD (jeśli nie pasuje do branży tytoniowej = inna firma)
- [ ] Cross-validate: web_search potwierdza ofertę tytoniową?
- [ ] Jeśli firma OK → dodaj do CSV z wypełnionymi polami
- [ ] Jeśli firma nie OK → oznacz status w verification-report

---

## 🔄 REPRODUKCJA DLA NOWEGO KRAJU (nie z 12)

1. Sprawdź useosint skill: `skill({name: "useosint"})` → corporate-registries
2. Sprawdź czy kraj ma otwarte API (Wikipedia: "Company register [Country]")
3. Jeśli tak: dodaj do tabeli API w tym pliku
4. Jeśli nie: użyj web_search + lokalny rejestr (często .gov)
5. Dodaj translation row do language reference
6. Dodaj nowy country journal: `data/countries/{KOD}.md`
7. Dodaj CSV stubs (już są w `data/`)
8. Zacznij research

---

## 💡 GOTOWE WZORCE QUERY

### Pattern 1: Szybka weryfikacja 1 firmy
```bash
# 1. Sprawdź listę → wyciągnij identyfikator
# 2. Wykonaj API call
# 3. Porównaj nazwę + adres
# 4. Jeśli OK → wpisz do CSV
# Czas: 30 sekund
```

### Pattern 2: Batch verification (10-30 firm)
```bash
# 1. Web search każdej po nazwie → znajdź identyfikator
# 2. Loop: API call per firma
# 3. Diff: lista vs API
# 4. Raport: verification-report-{date}.md
# Czas: 15-30 minut
```

### Pattern 3: Discovery nowego rynku (np. Belgia)
```bash
# 1. Szukaj hurtowni tytoniowych: web_search w lokalnym języku
# 2. Sprawdź rejestr: Banque Carrefour des Entreprises (BCE)
# 3. Filter: PKD/NACE tobacco wholesale
# 4. Outreach list
# Czas: 2-4 godziny
```

### Pattern 4: Cross-validation przez LLM
```python
import json, urllib.request
with open('.env') as f:
    api_key = [l.split('=',1)[1].strip() for l in f if l.startswith('OPENROUTER_API_KEY=')][0]

prompt = f"""Oceń firmy pod kątem branży tytoniowej. Dla każdej podaj: real_pct, type (A=z nabijarkami/B=branza/=nieznane), komentarz. NIE WYMYŚLAJ DANYCH.
{json.dumps(firms, ensure_ascii=False)}"""

req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
    data=json.dumps({
        "model": "meta-llama/llama-3.1-8b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1500
    }).encode(),
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    print(json.loads(r.read())['choices'][0]['message']['content'])
```

---

## 📞 KONTAKTY WERYFIKACYJNE PER KRAJ (gdy API nie wystarcza)

| Kraj | Kto pytać | Email/URL |
|---|---|---|
| 🇵🇱 PL | KAS (rejestr pośredników tytoniowych) | https://www.gov.pl/web/kas/rejestr-posredniczacych-podmiotow-tytoniowych |
| 🇨🇿 CZ | Celní správa (customs) | celnisprava.cz |
| 🇪🇺 EU | EU Common Register | ec.europa.eu/taxation_customs/vies/ |

---

## CHANGELOG METODOLOGII

- 2026-08-10: v1 — iteracja 1, 30 firm z listy, 5 OK + 4 ZŁY + 5 FABRYKAT + 11 DO_WERYFIKACJI
- Kolejne iteracje: dodaj nowe kraje, fix gaps, dodaj nowe API

---

## 🧰 TOOLBOX PER KRAJ (3-4 źródła na kraj)

> **Zasada:** każdy kraj = minimum 3-4 źródła: **rejestr podstawowy** + **rejestr finansowy** + **upadłości** + **VAT/tax**.
> Cross-country universals (VIES, OpenCorporates, OpenSanctions, GLEIF) działają wszędzie.

### 🇵🇱 POLSKA (priorytet)

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | KRS API (MS) | `https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{KRS}` | Pełny odpis: zarząd, wspólnicy, kapitał, PKD, adres, historia (free, no auth, 20/min) |
| 2 | REGON API (BIR1.1) | `api.stat.gov.pl/Home/RegonApi` | NIP/REGON/KRS → dane firmy, PKD, forma prawna (USER_KEY) |
| 3 | CEIDG v3 | `dane.biznes.gov.pl/api/ceidg/v3/firmy?nazwa=X` | JDG: NIP, REGON, adres, PKD, status (Bearer token) |
| 4 | Przeglądarka DF KRS | `ekrs.ms.gov.pl/rdf/pd/search_df?Krs={KRS}` | Sprawozdania finansowe .xml (bilans + RZiS) |

Plus: wyszukiwarka-krs.ms.gov.pl (search by name), KRZ (upadłości), biała lista VAT, KRZ.

**Automatyzacja:** `tools/krs_search.py --nip 5140361901 --financials`

### 🇨🇿 CZECHY

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | **ARES** (Ministerstvo Financí) | `ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ICO}` | IČO → nazwa, adres, NACE, DIČ, **finanční údaje** (bilans!) |
| 2 | Živnostenský rejstřík (RZP) | `rzp.cz` | Živnosti (JDG), koncesje |
| 3 | Insolvenční rejstřík (ISIR) | `isir.justice.cz` | Upadłości, restrukturyzacja |
| 4 | Obchodní rejstřík | `or.justice.cz` | Spółki — odpis .pdf, zmiany statutu |

### 🇸🇰 SŁOWACJA

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | Obchodný register (ORSR) | `orsr.sk/hladaj_subjekt.asp` | Odpis OR, zarząd, kapitał |
| 2 | **Register účtovných závierok (RUZ)** | `registeruz.sk` | Roczne sprawozdania .xml |
| 3 | Živnostenský register (ŽRSR) | `zrsr.sk` | Živnosti (JDG) |
| 4 | Finančná správa | `financnasprava.sk` | Status VAT/DIČ |

### 🇷🇴 RUMUNIA

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | **Termene.ro** | `termene.ro` | CUI, bilans .pdf, dłużnicy, powiązania (free) |
| 2 | ListaFirme.ro | `listafirme.ro` | Aggregator darmowy: CUI, adres, Cifra afaceri |
| 3 | ANAF | `anaf.ro` | Status TVA, bilanț |
| 4 | Buletinul Procedurilor de Insolvență | `bpi.just.ro` | Upadłości |

### 🇱🇹 LITWA

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | **rekvizitai.vz.lt** | `rekvizitai.vz.lt` | Įmonės kodas, PVM, adres, vadovas, **bilans**, powiązania |
| 2 | Registrų centras (JAR) | `registrucentras.lt` | Pełne dane JAR |
| 3 | VMI | `vmi.lt` | Status PVM |
| 4 | Nemokumo registras | `registrucentras.lt/nemokumoregistras` | Upadłości |

### 🇱🇻 ŁOTWA

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | info.ur.gov.lv (UR) | `info.ur.gov.lv` | Reģistrācijas nr, PVN, adrese |
| 2 | **Lursoft** (free preview) | `lursoft.lv` | Aggregator: bilans, powiązania, ryzyko |
| 3 | VID (tax) | `vid.gov.lv` | Status PVN |
| 4 | Maksātnespējas reģistrs (UR) | `ur.gov.lv/lv/maksatnespejas-regis…` | Upadłości |

### 🇪🇪 ESTONIA ⭐ (najlepszy w regionie)

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | **e-Äriregister** | `ariregister.rik.ee` | Pełne dane, e-aadress, kapitał, **bilans**, EMTA status |
| 2 | EMTA (tax) | `emta.ee` | Status KM (VAT), konta |
| 3 | Finantsinspektsioon | `fi.ee` | Licencje finansowe |
| 4 | (e-Äriregister wystarcza) | — | — |

### 🇫🇷 FRANCJA

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | **annuaire-entreprises.data.gouv.fr** | `annuaire-entreprises.data.gouv.fr` | SIREN/SIRET, dirigeants, **bilans** (oficjalne, darmowe) |
| 2 | Bodacc | `bodacc.fr` | Annonces légales, upadłości, likwidacja |
| 3 | INPI | `inpi.fr` | Marki, patenty |
| 4 | Societe.com (ograniczony) | `societe.com` | SIREN, dirigeants, publikacje |

### 🇲🇩 MOŁDAWIA

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | Camera Înregistrării de Stat | `cis.gov.md` | IDNO, statut, adresă |
| 2 | Serviciul Fiscal de Stat (SFS) | `sfs.md` | Status TVA |

### 🇧🇬 BUŁGARIA

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | **portal.justice.bg** | `portal.justice.bg` | EIK, status, zarząd, **bilans .pdf** |
| 2 | Registry Agency | `public.registryagency.bg` | Upadłości |
| 3 | НАП (tax) | `nap.bg` | Status DDS (VAT) |

### 🇸🇮 SŁOWENIA ⭐ (drugi najlepszy po PL)

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | **AJPES** | `ajpes.si` | Matična + **bilans + RZiS** w jednym miejscu |
| 2 | FURS (tax) | `furs.si` | Status DDV (VAT) |
| 3 | (AJPES wystarcza) | — | — |

### 🇭🇷 CHORWACJA

| # | Źródło | URL | Co daje |
|---|---|---|---|
| 1 | Sudski registar | `sudreg.pravosudje.hr` | OIB, MBS, zarząd |
| 2 | **FINA** | `fina.hr` | Roczne sprawozdania .xml |
| 3 | Porezna uprava (tax) | `porezna-uprava.hr` | Status PDV |
| 4 | Stečajni registar (Sudski registar) | `sudreg.pravosudje.hr` | Upadłości |

---

### 🌍 CROSS-COUNTRY UNIVERSALS

| Narzędzie | URL | Co daje |
|---|---|---|
| **VIES** | `ec.europa.eu/taxation_customs/vies/` | Walidacja VAT-EU (27 krajów) |
| **OpenCorporates** | `opencorporates.com` | ~200/m free, mirror 100+ rejestrów |
| **OpenSanctions** | `opensanctions.org` | Listy sankcyjne EU/ONZ/US/UK |
| **GLEIF** | `gleif.org` | LEI lookup globalny |
| **Wikidata** | `wikidata.org` | Linked open data, cross-references |
| **EU Open Data Portal** | `data.europa.eu` | Oficjalne dane EU |
| **DuckDuckGo / Brave** | — | Search by name, all languages |

---

### 🎯 PRIORYTET PO PL (TOP 3 do rozważenia)

1. **🇸🇮 SI (AJPES)** — jedno źródło daje pełen pakiet: dane + bilans + RZiS
2. **🇪🇪 EE (e-Äriregister)** — najlepszy cyfrowy rejestr w regionie
3. **🇨🇿 CZ (ARES + VIES)** — blisko PL, duży rynek, ARES daje finanční údaje bez paid

**Zasada ogólna:** rejestr + VIES + sankcje = minimum verification pack. Większość krajów ma te 3 za darmo.

---

## 📚 DOKUMENTY FINANSOWE I REJESTRY — DOSTĘP PER KRAJ

Lista dokumentów które powinniśmy mieć dostęp do weryfikacji firm per kraj. Bez tych źródeł verification = "wiarygodne tylko na podstawie tego co firma sama o sobie mówi".

### 🔑 Kluczowe źródła ogólne (wszystkie kraje EU)

| Źródło | Co daje | Dostęp |
|---|---|---|
| **VIES** (VAT Information Exchange System) | Walidacja VAT-EU (aktywny/nieaktywny) | http://ec.europa.eu/taxation_customs/vies/ — bezpłatny |
| **EU Open Data Portal** | Listy sankcyjne EU, dane korporacyjne | https://data.europa.eu/ |
| **OpenCorporates** | Agregator globalny (mirror wielu rejestrów) | https://opencorporates.com/ — bezpłatny z limitem |
| **NORSK / World-Bank** | Listy sankcyjne globalne | https://www.opensanctions.org/ — open data |

### 🇵🇱 POLSKA — kompletna lista

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **KRS** (Krajowy Rejestr Sądowy) — pełny odpis | https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{KRS} | Pełny odpis: zarząd, wspólnicy, kapitał, PKD, adres, historia | ❌ brak (limit 20/min) |
| **KRS — wyszukiwarka web** (search by name/NIP/REGON) | https://wyszukiwarka-krs.ms.gov.pl/ | Lista firm po nazwie, NIP, REGON, KRS | ❌ brak |
| **REGON** (BIR1.1 GUS) | https://api.stat.gov.pl/Home/RegonApi | NIP/REGON/KRS → nazwa, adres, PKD, forma prawna, daty | ✅ USER_KEY (email) |
| **CEIDG v3** (jednoosobowe) | https://dane.biznes.gov.pl/ | JDG: NIP, REGON, adres, PKD, status | ✅ Bearer token |
| **Sprawozdania finansowe KRS** (.xml) | https://ekrs.ms.gov.pl/rdf/pd/search_df | Bilans + RZiS + Cash flow + zmiany kapitałów | ❌ brak (download XML) |
| **Krajowy Rejestr Zadłużonych (KRZ)** | https://prs.ms.gov.pl/krz | Dłużnicy, postępowania upadłościowe | ❌ brak |
| **Lista sankcyjna MSWiA** | https://www.gov.pl/web/mswia/lista-osob-i-podmiotow-objetych-sankcjami | Osoby/podmioty z sankcjami | ❌ brak |
| **Wykaz podatników VAT (biała lista)** | https://www.podatki.gov.pl/wykaz-podatnikow-vat-wyszukiwarka | Status VAT, rachunki bankowe | ❌ brak |
| **Rejestr podmiotów tytoniowych (KAS)** | https://www.gov.pl/web/kas/rejestr-posredniczacych-podmiotow-tytoniowych | Legalni pośrednicy tytoniowi PL | ❌ brak |
| **Rejestr.io API** (paid) | https://rejestr.io/api | Search by name + bilans (.xml) | ✅ 0.5 zł/dokument |
| **Aleo.com** | https://aleo.com | KRS, bilans, powiązania | ❌ free z limitem |
| **Panoramafirm.pl** | https://panoramafirm.pl | Dane rejestrowe, PKD, linki | ❌ brak |
| **KRS-online.com.pl** (paid) | https://krs-online.com.pl | KRS + bilans | ✅ płatny |

**Automatyzacja PL (gotowe):**
```bash
# 1. NIP → REGON → KRS
python3 tools/krs_search.py --nip 5140361901
# 2. KRS → pełny odpis (po znalezieniu KRS)
python3 tools/krs_search.py --krs 0001074645
# 3. KRS → URL do sprawozdań finansowych
python3 tools/krs_search.py --krs 0001074645 --financials
```

### 🇨🇿 CZECHY

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **ARES** (Ministerstvo Financí) | https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ICO} | IČO → nazwa, adres, NACE, DIČ, forma prawna | ❌ brak |
| **ARES search by name** | https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty?obchodniJmeno={name} | Lista IČO po nazwie | ❌ brak |
| **Obchodní rejstřík** (justice.cz) | https://or.justice.cz | Odpis z OR (.pdf), zmiany statutu, likwidacja | ❌ brak |
| **Živnostenský rejstřík (RZP)** | https://www.rzp.cz | Živnosti (JDG), koncesje | ❌ brak |
| **Insolvenční rejstřík (ISIR)** | https://isir.justice.cz | Upadłości, restrukturyzacja | ❌ brak |
| **Registr ekonomických subjektů** | https://www.statnipokladna.cz | Subwencje z budżetu publicznego | ❌ brak |
| **ARES finanční data** | https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ICO}/financni-udaje | Bilans, RZiS, turnover (nielimitowane) | ❌ brak |
| **VIES** | http://ec.europa.eu/taxation_customs/vies/ | Walidacja VAT | ❌ brak |

### 🇸🇰 SŁOWACJA

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **Obchodný register (ORSR)** | https://orsr.sk/hladaj_subjekt.asp | Odpis OR, zarząd, kapitał | ❌ brak |
| **Živnostenský register (ŽRSR)** | https://www.zrsr.sk | Živnosti (JDG) | ❌ brak |
| **Register účtovných závierok (RUZ)** | https://www.registeruz.sk | Roczne sprawozdania finansowe (.xml) | ❌ brak |
| **Finančná správa** | https://www.financnasprava.sk | Status VAT, DIČ | ❌ brak |
| **Obchodný register Vestník** | https://www.justice.gov.sk | Ogłoszenia o likwidacji, upadłości | ❌ brak |
| **VIES** | http://ec.europa.eu/taxation_customs/vies/ | Walidacja VAT | ❌ brak |

### 🇷🇴 RUMUNIA

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **ONRC** (Registrul Comerțului) | https://www.onrc.ro | Odpis z RC (.pdf, 8 lei/opłata) | ✅ paid (8 lei/odpis) |
| **ListaFirme.ro** | https://listafirme.ro | Aggregator: CUI, adres, Cifra afaceri | ❌ brak |
| **Termene.ro** | https://termene.ro | CUI, bilans (.pdf), powiązania | ❌ brak |
| **Confidas.ro** | https://confidas.ro | KYC, ryzyko, finansowe | ❌ brak |
| **ANAF** (tax) | https://www.anaf.ro | Status TVA, bilanț | ❌ brak |
| **Buletinul Procedurilor de Insolvență** | https://bpi.just.ro | Upadłości | ❌ brak |
| **VIES** | http://ec.europa.eu/taxation_customs/vies/ | Walidacja VAT | ❌ brak |

### 🇱🇹 LITWA

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **JAR** (Juridinių asmenų registras) | https://rekvizitai.vz.lt | Įmonės kodas, PVM, adres, vadovas | ❌ brak |
| **Registrų centras** | https://www.registrucentras.lt | Pełne dane, finansowe | ❌ brak |
| **JAR finansiniai ataskaitos** | https://rekvizitai.vz.lt/company/{kodas}/financials | Bilans, RZiS | ❌ brak |
| **VMI** (tax) | https://www.vmi.lt | Status PVM | ❌ brak |
| **Nemokumo registras** | https://www.registrucentras.lt/nemokumoregistras | Upadłości | ❌ brak |
| **VIES** | http://ec.europa.eu/taxation_customs/vies/ | Walidacja VAT | ❌ brak |

### 🇱🇻 ŁOTWA

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **UR** (Uzņēmumu reģistrs) | https://info.ur.gov.lv | Reģistrācijas nr, PVN, adrese | ❌ brak |
| **Lursoft** | https://lursoft.lv | Agregator: bilans, powiązania, ryzyko | ❌ brak |
| **DataMe.lv** | https://datame.lv | Roczne sprawozdania (.pdf) | ❌ brak |
| **VID** (tax) | https://www.vid.gov.lv | Status PVN | ❌ brak |
| **Maksātnespējas reģistrs** | https://www.ur.gov.lv/lv/maksatnespejas-regis… | Upadłości | ❌ brak |
| **VIES** | http://ec.europa.eu/taxation_customs/vies/ | Walidacja VAT | ❌ brak |

### 🇪🇪 ESTONIA

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **e-Äriregister** (najlepszy w regionie!) | https://ariregister.rik.ee | Pełne dane, e-aadress, kapitał, EMTA status | ❌ brak |
| **EMTA** (tax) | https://www.emta.ee | Status KM (VAT), konta | ❌ brak |
| **Finantsinspektsioon** | https://www.fi.ee | Licencje finansowe | ❌ brak |
| **e-Äriregister financial reports** | https://ariregister.rik.ee/est?kood={KM}&tegevusala=EMTAK | Bilans (konsolidowany) | ❌ brak |
| **VIES** | http://ec.europa.eu/taxation_customs/vies/ | Walidacja VAT | ❌ brak |

### 🇫🇷 FRANCJA

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **Pappers.fr** ⭐ | https://pappers.fr/api | SIREN, dirigeants, bilans, status | ✅ paid (ale świetne) |
| **Societe.com** | https://www.societe.com | SIREN, dirigeants, publikacje | ❌ free z limitem |
| **Infogreffe (RCS)** | https://www.infogreffe.fr | Odpis z RCS (.pdf, paid) | ✅ paid |
| **INPI** (własność intelektualna) | https://www.inpi.fr | Marki, patenty | ❌ brak |
| **Bodacc** (annonces légales) | https://www.bodacc.fr | Ogłoszenia prawne, upadłości, likwidacja | ❌ brak |
| **Service-public.fr** | https://annuaire-entreprises.data.gouv.fr | Dane rejestrowe SIREN/SIRET | ❌ brak |
| **VIES** | http://ec.europa.eu/taxation_customs/vies/ | Walidacja VAT | ❌ brak |

### 🇲🇩 MOŁDAWIA (poza UE)

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **Camera Înregistrării de Stat** | https://www.cis.gov.md | IDNO, statut, adresă | ❌ brak |
| **Serviciul Fiscal de Stat** | https://www.sfs.md | Status TVA | ❌ brak |

### 🇧🇬 BUŁGARIA

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **Търговски регистър** (portal.justice.bg) | https://portal.justice.bg | EIK, status, zarząd | ❌ brak |
| **НАП** (tax) | https://www.nap.bg | Status DDS (VAT) | ❌ brak |
| **Търговски регистър финансови отчети** | https://portal.justice.bg | Bilans (.pdf) | ❌ brak |
| **Регистър на несъстоятелностите** | https://public.registryagency.bg | Upadłości | ❌ brak |
| **VIES** | http://ec.europa.eu/taxation_customs/vies/ | Walidacja VAT | ❌ brak |

### 🇸🇮 SŁOWENIA

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **AJPES** ⭐ | https://www.ajpes.si | Matična + **pełne bilansy** w jednym miejscu | ❌ brak |
| **FURS** (tax) | https://www.furs.si | Status DDV (VAT) | ❌ brak |
| **AJPES finančni podatki** | https://www.ajpes.si/prs/rezultati.asp?podrobno=true | Bilans + RZiS (.pdf, .xml) | ❌ brak |
| **Insolvenčni register** | https://www.ajpes.si/Register | Upadłości | ❌ brak |
| **VIES** | http://ec.europa.eu/taxation_customs/vies/ | Walidacja VAT | ❌ brak |

### 🇭🇷 CHORWACJA

| Dokument | URL | Co dostaje | Auth |
|---|---|---|---|
| **Sudski registar** | https://sudreg.pravosudje.hr | OIB, MBS, zarząd | ❌ brak |
| **Porezna uprava** | https://www.porezna-uprava.hr | Status PDV (VAT) | ❌ brak |
| **FINA** (finansowe) | https://www.fina.hr | Roczne sprawozdania (.xml) | ❌ brak |
| **Stečajni registar** | https://sudreg.pravosudje.hr | Upadłości | ❌ brak |
| **VIES** | http://ec.europa.eu/taxation_customs/vies/ | Walidacja VAT | ❌ brak |

---

### 📋 Cross-country — minimalny pakiet do weryfikacji

Aby zweryfikować firmę w dowolnym kraju na poziomie **minimum godnym zaufania**, potrzebujesz:

1. **Rejestr podstawowy** (każdy kraj ma) → nazwa, adres, forma prawna, status (aktywny/wykreślony)
2. **Rejestr finansowy** (AJPES, ARES, EKRS, Lursoft, Pappers, etc.) → obroty, zysk, zatrudnienie, kapitał
3. **VIES** → status VAT-EU (aktywny = nie jest karany)
4. **Rejestr upadłości** (ISIR, KRZ, Maksātnespējas, etc.) → czy nie w upadłości
5. **Lista sankcyjna** (UE/ONZ) → czy nie jest na czarnej liście

**Bez tych 5 źródeł = verification = "dane niepotwierdzone" ⚠️**

---

### 🔧 Pipeline weryfikacji per kraj (proponowany)

```
1. Firma w CSV (NIP/IČO/CUI/SIREN/IDNO/OIB itp.)
         ↓
2. Sprawdź rejestr podstawowy → status, adres, forma prawna
         ↓
3. Sprawdź VIES → VAT aktywny?
         ↓
4. Sprawdź rejestr upadłości → czy nie w postępowaniu?
         ↓
5. Sprawdź rejestr finansowy → obroty, zatrudnienie (opcjonalnie)
         ↓
6. Jeśli wszystko OK → flaga ✅ FROZEN
   Jeśli czegoś brak → flaga ⚠️ DO-WERYFIKACJI
```

**Stan na 2026-08-10:** narzędzia PL (KRS, REGON) zautomatyzowane (`tools/krs_search.py`). Inne kraje = manual przez `verify_api.py` + RUNBOOK recipes.

---

## 📋 NOTATKI: BRAKUJĄCE API

Nie mamy jeszcze integracji z:
- **rejestr.io API** (PL, paid 0.5 zł/dok) — dałby sprawozdania finansowe automatycznie
- **Pappers.fr API** (FR, paid) — najlepsze źródło dla FR
- **AJPES API** (SI, free!) — warto zautomatyzować, bo bilansy są w jednym miejscu
- **Lursoft API** (LV, paid) — alternatywa dla UR

Gdyby mieć budżet 100-200 PLN/mies. → rejestr.io + Pappers = pełna weryfikacja PL + FR.
