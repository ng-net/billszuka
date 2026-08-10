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
