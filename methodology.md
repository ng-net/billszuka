# BILLSzuka — Methodology Reference

> **B2B research na PowerMatic + Hawk.** Dla: BILLS Sp. z o.o. (Ostrzeszów) — exclusive PM distributor PL + CEE.
>
> **Ten plik jest kanonicznym reference.** Reguły, schematy, definicje. Zmienia się rzadko.
> **Kronologiczny log:** `DZIENNIK.md`. **Strategiczne odkrycia:** `INTEL.md`.

***

## 📋 Spis treści

| #  | Sekcja                                                    | Opis                                         |
| -- | --------------------------------------------------------- | -------------------------------------------- |
| 1  | [Kontekst projektu](#1-kontekst)                          | Co, dla kogo, dlaczego                       |
| 2  | [Zasady dokumentacji](#2-zasady)                          | INTEL vs DZIENNIK vs methodology vs per-kraj |
| 3  | [Katalog A — Firmy z nabijarkami](#3-katalog-a)           | Kategoryzacja A1-A6 + flagi konkurencji      |
| 4  | [Katalog B — Branża tytoniowa (cross-sell)](#4-katalog-b) | Kategoryzacja B1-B9 + powinowactwo           |
| 5  | [Tier i Wolumen](#5-tier-wolumen)                         | Definicje + heurystyki estymacji             |
| 6  | [Rejestry i API per kraj](#6-rejestry)                    | 12 krajów: NIP/IČO/CUI/SIREN itp.            |
| 7  | [Marketplace per kraj](#7-marketplace)                    | Allegro, Heureka, eMAG, Skelbiu, etc.        |
| 8  | [Regulacje per kraj](#8-regulacje)                        | Reżim tytoniowy, e-papierosy, CBD            |
| 9  | [Kolejność geograficzna](#9-kolejnosc)                    | PL → CZ → ... → MD                           |
| 10 | [Schemat CSV (zunifikowany)](#10-schemat-csv)             | 38 kolumn, A i B razem                       |
| 11 | [Cele ilościowe](#11-cele)                                | Targety per kraj                             |
| 12 | [Struktura plików](#12-struktura)                         | Co gdzie żyje                                |
| 13 | [3 słabe punkty metodologii](#13-slabe-punkty)            | Zastrzeżenia + naprawa                       |
| 14 | [Dane pomocnicze od użytkownika](#14-dane-pomocnicze)     | Co user może dostarczyć                      |
| 15 | [Checklist przed pierwszym dostarczeniem](#15-checklist)  | Gotowość do produkcji                        |

***

## 1. Kontekst projektu

**Cel końcowy:** 3-5 nowych umów dystrybucyjnych PowerMatic / Hawk w PL lub CEE w ciągu 12 miesięcy. **Umowa = podpisana, nie rozmowa.**

**Cel pośredni:** ≥50 zweryfikowanych firm PL w katalogach A+B. Każda z: pełnym adresem, kontaktem, decydentem, statusem (FROZEN).

**Zakres pierwszej fali:** głęboki PL (12 krajów docelowo, ale PL = fundament).

**Stack technologiczny:** CEIDG v3, KRS API, REGON API, ARES, VIES, OpenRouter (LLM), 5+ OSINT skills.

**Output:** Excel/Google Sheets + CSV (dual).

***

## 2. Zasady dokumentacji

### 7 + 1 Metod Pozyskiwania Leadów (Framework Wyszukiwania B2B)

> **Organizacja:** 7 dużych grup metod (jak poniżej) + L0 (pre-flight walidacja) + L10/L11 (uzupełniające). Numeracja L0–L11 utrzymana dla kompatybilności wstecz z kodem (`tools/orchestrate_11_levels.py`).

| #     | Grupa                                    | Poziom(y)   | Źródła per kraj                                                                                                                                                                                                                                                                                                     |
| ----- | ---------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0** | **Pre-flight walidacja**                 | **L0**      | NIP checksum + KRS/CEIDG/ARES name-match — **WYMAGANE przed każdą metodą**                                                                                                                                                                                                                                          |
| **1** | **Targi i audyty wystawców**             | **L6**      | InterTabac (DE), Cannafest (CZ), CEE Retail Expo & FMCG Summit (HR), Romanian FMCG expos (RO)                                                                                                                                                                                                                       |
| **2** | **Rejestry państwowe + podatki + EORI**  | **L3 + L4** | CEIDG/KRS (PL), ARES (CZ), ORSR (SK), ONRC (RO), Registrų Centras (LT), Lursoft UR (LV), e-Äriregister (EE), Sudski Registar (HR), Camera Înregistrării (MD), Търговски регистър (BG), AJPES (SI), Pappers/Infogreffe (FR), APR (RS). Plus: VIES, PVM/LT, Biała Lista VAT, BDO, KAS Pośrednicy Tytoniowi, **EORI**. |
| **3** | **Marketplace'y i platformy e-commerce** | **L2**      | Allegro (PL/CZ), eMAG (RO), Bazoš.cz (CZ), Aukro (CZ/SK), CEL.ro, Okazii.ro, OLX (PL/RO/BG), Heureka (CZ/SK), Bolha (SI), Njuškalo (HR), Skelbiu (LT), SS.lv (LV), Osta.ee (EE), Leboncoin (FR).                                                                                                                    |
| **4** | **EMD + SEO footprint discovery**        | **L5**      | Discovery skryptami EMD: `powermatic.cz`, `plnickacigaret.cz`, `balicka.cz`, `dutinky.cz`, `vodnidymky.cz`, `skleptytoniowy.pl`, `twojepapierosy.pl`, `powermatic.store` (Armorica) i podobne exact-match domeny.                                                                                                   |
| **5** | **Katalogi firm i bazy B2B**             | **L8**      | PKT.pl, Panorama Firm, Biznesfinder, Aleo.com (PL); Firmy.cz, Kompass (CZ); ListaFirme, Bizoo, Termene (RO); nipgo.pl, Veritor (multi-EU); ENTIA MCP (5.5M EU firm).                                                                                                                                                |
| **6** | **Web OSINT (traffic + tech + DNS)**     | **L5.5**    | SimilarWeb (ruch), BuiltWith (tech-stack: WooCommerce B2B / Shoptet CZ / Magento / Pluriva ERP), WHOIS per TLD: WHOIS NASK (PL), CZ-NIC (CZ), EENet (EE), CARNet (HR), DOMREG.lt (LT), ROTLD (RO), crt.sh (cert transparency).                                                                                      |
| **7** | **AI-Driven OSINT + PKD machinery**      | **L9**      | OpenRouter AI OSINT (programatyczny crawl regionalny), PKD/CN kody dla maszyn (np. **Woton Sp. z o.o.** — krajowi producenci sprzętu do napełniania/pakowania). Multi-LLM consensus wymagany.                                                                                                                       |

**Poziomy uzupełniające (cross-cutting):**

| Poziom  | Metoda                       | Skąd                                                       | Dlaczego ważna                                     |
| ------- | ---------------------------- | ---------------------------------------------------------- | -------------------------------------------------- |
| **L1**  | Ogólne wyszukiwanie sieciowe | Google / DDG / Brave z operatorami + frazy ze SŁOWNIK      | Baseline discovery                                 |
| **L7**  | OSINT social media           | FB/IG/TT/Reddit/YouTube komentarze + Vinted                | Real leads z deklaracji kupujących                 |
| **L10** | EUIPO trademark              | euipo.europa.eu/eSearch                                    | Weryfikacja właściciela znaku PowerMatic/Hawk w EU |
| **L11** | Zamówienia publiczne         | BZP PL + TED EU + CPV 15800000-6 / 39200000-4 / 30100000-0 | Referencje dla sektora publicznego                 |

> **Definicja "EMD"** = Exact Match Domain — domena, która zawiera dokładnie szukaną frazę kluczową (np. `dutinky.cz` = "dutinky" = gilzy). Wskazuje firmy, które zainwestowały w SEO niszy i mają brand equity w produkcie.

***

#### L0 — Szczegóły: Pre-flight walidacja

**Kiedy:** PRZED każdym L1-L11 (a także po L9). Zawsze, gdy pojawia się NIP/KRS z nowego źródła.

**Dlaczego:** LLM (Gemini/Claude/DeepSeek) generuje NIP-y z poprawnym checksum i KRS-y istniejące w rejestrze — ale wskazujące na **zupełnie inne firmy**. Przykład: "HURTOWNIA PAPIEROSÓW CYGARO" = KRS 0000123456 → realnie to **RODENSTOCK POLSKA** (optyka). KRS API zwraca sukces (HTTP 200) dla każdego istniejącego KRS bez weryfikacji nazwy.

**Kod (Python):**

```python
# NIP checksum (mod 11)
def validate_nip(nip):
    nip = str(nip).replace("PL", "").replace(" ", "")
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    s = sum(int(nip[i]) * weights[i] for i in range(9))
    return s % 11 == int(nip[9])

# KRS name match
def krs_name_match(krs, expected_name, fuzzy=True):
    url = f"https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{krs}"
    data = json.loads(urllib.request.urlopen(url).read())
    api_name = data["odpis"]["dane"]["dzial1"]["danePodmiotu"]["nazwa"]
    if fuzzy:
        return api_name[:8].lower() in expected_name.lower() or expected_name[:8].lower() in api_name.lower()
    return api_name == expected_name
```

**Defense in depth (3 warstwy):**

1. **NIP checksum (mod 11)** — instant, 30ms, eliminuje 100% losowo generowanych NIP-ów
2. **KRS/CEIDG API + name-match** — dla każdego KRS, 200ms, eliminuje FABRYKATY
3. **Multi-LLM cross-check** — dla danych z LLM, 5-10s, eliminuje halucynacje modeli

***

#### L2 — Allegro REST API

**Setup:** OAuth2 client credentials flow. Rejestracja: <https://apps.developer.allegro.pl>

**Co daje (per sprzedawca):**

- `seller.login` → nazwa + NIP firmy

- `feedbackCount` + `positiveCount` → wolumen (proxy)

- `superSeller` → jakość

- `category.id` → asortyment

**Przykład endpointu:**

```
GET https://api.allegro.pl/sellers/{sellerId}/summary
Authorization: Bearer {access_token}
Accept: application/vnd.allegro.public.v1+json
```

**Workflow:** szukaj "powermatic" / "nabijarka" → dla każdego offer → GET seller info → NIP → CEIDG/KRS. **NIE trzeba scrapować Allegro UI** — API oficjalne, darmowe, 9000 req/h.

**Inne marketplace'y z API:**

- OLX: brak oficjalnego API, scraping

- Ceneo: brak API, scraping (ale mirror w rankingu Ceneo)

- Heureka.cz: brak API

- Amazon Seller Central: API dla zarejestrowanych sellerów

- eBay: Finding API (publiczny, darmowy)

***

#### L3 — Google Maps API (Places API - Text Search New)

**Setup:** Google Cloud Console → Places API → Text Search. Wymaga billing ale ma $200/mies. free tier.

**Przykład:**

```python
import googlemaps
gmaps = googlemaps.Client(key="AIza...")
results = gmaps.places(query="sklep tytoniowy hurtownia Warszawa", language="pl")
for r in results.get("results", []):
    print(r["name"], r["formatted_address"], r.get("rating"), r.get("user_ratings_total"))
```

**Co daje:** nazwa, adres, telefon, WWW, **rating (4.8+ = quality signal)**, liczba opinii, godziny otwarcia, kategorie Google.

**Koszt:** $32 per 1000 requests. Dla 100 miast × 1 query = 100 req = $3.20. Tani.

***

#### L4 — Bezpłatne źródła twardych danych

| Źródło                                  | URL                                                                        | Co daje                                                                                                                           |
| --------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Biała Lista VAT**                     | <https://www.podatki.gov.pl/wykaz-podatnikow-vat-wyszukiwarka>             | Status VAT active/zwolniony/wykreślony + rachunki bankowe                                                                         |
| **BDO**                                 | <https://rejestr-bdo.mos.gov.pl>                                           | Rejestr podmiotów wprowadzających produkty (wymagane dla importerów)                                                              |
| **KAS Rejestr Pośredników Tytoniowych** | <https://www.gov.pl/web/kas/rejestr-posredniczacych-podmiotow-tytoniowych> | **Tylko w PL** — firmy z koncesją na obrót suszem tytoniowym. **TOP discovery source**                                            |
| **CEIDG v3 API**                        | <https://dane.biznes.gov.pl>                                               | JDG z pełnymi danymi (wymaga token z .env)                                                                                        |
| **VIES (EU VAT)**                       | <https://ec.europa.eu/taxation_customs/vies>                               | Weryfikacja VAT-EU do transgranicznego handlu                                                                                     |
| **EORI**                                | <https://ec.europa.eu/taxation_customs/dds2/eos/eori_validation.jsp>       | Status EORI — zdolność do operacji celnych (import/eksport poza EU). **Wymagane** jeśli partner ma obsługiwać przesyłki spoza EU. |

#### L3.5 — Rejestry państwowe per kraj (pełna mapa 12 krajów)

> **Zasada:** dla każdego kraju, **najpierw** sprawdź rejestr (twarde dane prawne, PKD, status), **potem** uzupełniaj z marketplace'ów i OSINT. Każdy lead musi mieć **potwierdzoną formę prawną i aktywny status** przed FROZEN.

| Kraj    | Rejestr główny               | URL                                                                                                                          | Co daje                                                                                        | API?                                    |
| ------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------- |
| 🇵🇱 PL | KRS + CEIDG + REGON          | `https://api-krs.ms.gov.pl`, `https://dane.biznes.gov.pl`, `https://api.stat.gov.pl/Home/RegonApi`                           | NIP, KRS, REGON, PKD, zarząd, wspólnicy, adres, daty                                           | ✅ KRS open, CEIDG/REGON token           |
| 🇨🇿 CZ | ARES + OR + ŽR               | `https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ICO}`, `https://or.justice.cz`, `https://www.rzp.cz` | IČO, DIČ, nazwa, adres, forma prawna, PKD (NACE), zarząd, finanční údaje                       | ✅ ARES open, OR/ŽR open                 |
| 🇸🇺 SK | ORSR + ŽRSR + RUZ            | `https://orsr.sk`, `https://www.zrsr.sk`, `https://www.registeruz.sk`                                                        | IČO, IČ DPH, nazwa, adres, PKD, sprawozdania finansowe                                         | ✅ wszystkie open                        |
| 🇭🇷 HR | Sudski registar              | `https://sudreg.pravosudje.hr`                                                                                               | OIB (11 cyfr), MBS, nazwa, adres, zarząd, kapitał                                              | ✅ open                                  |
| 🇧🇬 BG | Търговски регистър           | `https://portal.justice.bg`                                                                                                  | EIK (9 cyfr), DDS (VAT), forma prawna, zarząd, PKD                                             | ✅ open                                  |
| 🇸🇪 SI | AJPES                        | `https://www.ajpes.si`                                                                                                       | ID za DDV (VAT), nazwa, adres, PKD, **bilans + RZiS w jednym miejscu** (najlepsze w regionie!) | ✅ open                                  |
| 🇷🇴 RO | ONRC + ANAF                  | `https://www.onrc.ro` (paid 8 lei/odpis), `https://www.anaf.ro`                                                              | CUI/CIF, nazwa, adres, forma prawna, PKD, finanční údaje                                       | ⚠️ ONRC paid (8 lei/extract), ANAF free |
| 🇪🇪 EE | e-Äriregister                | `https://ariregister.rik.ee`                                                                                                 | KM (VAT), EMTAK/NACE, zarząd, beneficjenci, sprawozdania. **Najlepszy w regionie**             | ✅ open, JSON                            |
| 🇱🇻 LV | UR + Lursoft                 | `https://info.ur.gov.lv`, `https://lursoft.lv`                                                                               | PVN (VAT), nazwa, adres, PKD, beneficjenci                                                     | ✅ UR open, Lursoft agregator            |
| 🇱🇹 LT | JAR (Registrų Centras)       | `https://rekvizitai.vz.lt`, `https://www.registrucentras.lt`                                                                 | VMN/PVM (VAT), NACE, zarząd, **PVM mokėtojas** (status VAT)                                    | ✅ open                                  |
| 🇫🇷 FR | RCS (Infogreffe) + Pappers   | `https://www.infogreffe.fr` (paid), `https://pappers.fr/api` (paid)                                                          | SIREN/SIRET, TVA, forma prawna, bilans, dirigeants                                             | ⚠️ oba paid; Pappers ma API             |
| 🇲🇩 MD | Camera Înregistrării de Stat | `https://www.cis.gov.md`                                                                                                     | IDNO (13 cyfr), TVA, nazwa, adres, PKD                                                         | ✅ open                                  |
| 🇷🇸 RS | APR                          | `https://www.apr.gov.rs`                                                                                                     | PIB (9 cyfr), nazwa, adres, PKD, zarząd                                                        | ✅ open                                  |

**Przykładowe kwerendy (rejestry per kraj):**

- PL: `GET https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{KRS}` → pełny odpis

- CZ: `GET https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ICO}` → JSON z ARES

- HR: GET Sudski registar → szukaj po OIB

- RO: scrape ONRC lub przez aggregator `listafirme.ro` (free read-only)

**Walidacja tożsamości (L3 + L0):**

1. Pobierz nazwę z rejestru
2. Porównaj z nazwą z leadu (fuzzy match, pierwsze 8 znaków)
3. Jeśli mismatch → FABRYKAT, odrzuć

**EORI (dla partnerów obsługujących cło spoza EU):**

- Wyszukiwarka: <https://ec.europa.eu/taxation_customs/dds2/eos/eori_validation.jsp>

- Format: `PL{10cyfr}` dla PL, `CZ{8cyfr}` dla CZ itd.

- **Wymagane** jeśli partner importuje z Chin lub eksportuje poza EU

- Sprawdź zawsze przy leadach które deklarują import z Chin (Topomat, Turbomatic, GM)

***

#### L5 — EMD / SEO Footprint Discovery

**Co to jest EMD:** Exact Match Domain = domena zawierająca dokładnie szukaną frazę kluczową. Firmy które zainwestowały w EMD-y SEO (`powermatic.cz`, `dutinky.cz`) zwykle:

- mają realny ruch organiczny

- są aktywne komercyjnie (nie wygasłe wizytówki)

- mają brand equity w niszy

**Discovery (skrypt per kraj):**

```python
import whois, requests

# Krok 1: generuj kandydatów EMD
KEYWORDS = {
    "CZ": ["powermatic", "plnickacigaret", "balicka", "dutinky", "vodnidymky",
           "tabak", "cigarety", "doutniky", "shisha", "bong", "vaporizer",
           "e-cigareta", "koureni", "krabicka", "sirky"],
    "PL": ["skleptytoniowy", "twojepapierosy", "powermatic", "nabijarka",
           "papieros", "tyton", "skret", "fajka", "szisza", "liquid", "vape"],
    "RO": ["tigara", "tutun", "masina", "umplere", "fumator", "tigari",
           "accesorii", "importator", "angrosist"],
    "HR": ["cigarete", "duhan", "punjenje", "filter", "shisha", "vape"],
}

TLD = {"CZ": "cz", "PL": "pl", "RO": "ro", "HR": "hr"}

def discover_emd(country):
    found = []
    for kw in KEYWORDS[country]:
        domain = f"{kw}.{TLD[country]}"
        try:
            w = whois.whois(domain)
            if w and w.get("creation_date"):
                # Krok 2: sprawdź czy aktywna (HTTP 200 + treść z produktem)
                r = requests.get(f"http://{domain}", timeout=5)
                if r.status_code == 200 and ("nabijark" in r.text.lower() or
                                              "powermatic" in r.text.lower() or
                                              "dutinky" in r.text.lower()):
                    found.append({
                        "domain": domain,
                        "created": str(w.creation_date),
                        "registrar": w.registrar,
                        "country": country,
                    })
        except Exception:
            pass
    return found
```

**EMD-y już zidentyfikowane (lekcja z istniejącego researchu):**

| Kraj    | Domena                        | Co sprzedaje                             |
| ------- | ----------------------------- | ---------------------------------------- |
| 🇨🇿 CZ | `powermatic.cz`               | Nabijarki, akcesoria do skręcania        |
| 🇨🇿 CZ | `plnickacigaret.cz`           | Plnicí strojek (maszynka do napełniania) |
| 🇨🇿 CZ | `balicka.cz`                  | Balička (maszyna pakująca)               |
| 🇨🇿 CZ | `dutinky.cz`                  | Dutinky (gilzy)                          |
| 🇨🇿 CZ | `vodnidymky.cz`               | Vodní dýmky (fajki wodne)                |
| 🇵🇱 PL | `skleptytoniowy.pl`           | Sklep tytoniowy online                   |
| 🇵🇱 PL | `twojepapierosy.pl`           | Twoje papierosy (twój brand klienta)     |
| 🇵🇱 PL | `powermatic.store` (Armorica) | Sklep marki własnej importera            |

**Dlaczego działa:** firmy z EMD zwykle mają też realny kanał B2B (hurtownia, własny magazyn, własna marka). Idealny target na partnera.

***

#### L5.5 — Web OSINT: SimilarWeb + BuiltWith + WHOIS

> **Kiedy:** po wstępnej liście domen (L5 EMD lub L2 marketplace) — **filtrowanie** inaktywnych sklepów.

**SimilarWeb (ruch):**

- URL: <https://www.similarweb.com> (free tier 5 domen/mies.)

- Sygnały: monthly visits > 10k = realny ruch; < 1k = martwa wizytówka

- **Country split** (jaki % ruchu z danego kraju) → dopasowanie do naszego rynku docelowego

- Top keywords → overlap z naszą niszą (powermatic, nabijarka, dutinky)

**BuiltWith (tech stack):**

- URL: <https://builtwith.com> (free tier 5 domen/mies.)

- Sygnały:

  - **WooCommerce B2B** → ma wtyczki hurtowe, cenniki B2B, możliwa integracja API/XML

  - **Shoptet (CZ)** → standard dla CZ e-commerce, łatwy dropshipping feed

  - **Magento / Adobe Commerce** → duży gracz, ma własny ERP

  - **Pluriva ERP** → CZ/SK ERP dla FMCG/tytoniu, sygnał profesjonalizacji

  - **Custom ERP** → mniejszy, ale często lepsza integracja

- **Brak CMS** lub 1-page site → drop, szukaj innego partnera

**WHOIS per TLD (DNS history):**

| TLD      | Serwer WHOIS             | Komenda                             |
| -------- | ------------------------ | ----------------------------------- |
| 🇵🇱 .pl | `whois.nask.pl`          | `whois -h whois.nask.pl example.pl` |
| 🇨🇿 .cz | `whois.nic.cz` (CZ-NIC)  | `whois example.cz`                  |
| 🇸🇺 .sk | `whois.sk-nic.sk`        | `whois example.sk`                  |
| 🇭🇷 .hr | `whois.dns.hr` (CARNet)  | `whois example.hr`                  |
| 🇪🇪 .ee | `whois.eenet.ee` (EENet) | `whois example.ee`                  |
| 🇱🇹 .lt | `whois.domreg.lt`        | `whois example.lt`                  |
| 🇷🇴 .ro | `whois.rotld.ro`         | `whois example.ro`                  |
| 🇱🇻 .lv | `whois.nic.lv`           | `whois example.lv`                  |

**Co sprawdzić w WHOIS:**

- `Creation Date` — wiek domeny. < 1 rok = nowy, ryzyko. > 5 lat = dojrzały.

- `Registrar` — polska/czeska firma czy anonimowy (GoDaddy, Namecheap) → anonimowy = mniej wiarygodne

- `Status` — `ok` / `active` vs `redemptionPeriod` / `pendingDelete` → wykreślony, drop

- `Country` registrant — czasem ukryty (privacy proxy), czasem jawny

**Certificate Transparency (crt.sh):**

- URL: <https://crt.sh>

- Wyszukaj domenę → lista wszystkich certyfikatów SSL (również sub-domen!)

- **Bonus:** znajdź staging/dev domeny (`staging.example.cz`, `dev.example.cz`) — czasem leakują strukturę firmy

**Intelligent Web Scraping via ScrapeGraphAI:**

- **Narzędzie:** `tools/scrapegraph_enricher.py` (CLI: `python3 tools/billszuka.py scrape --url <URL> --type [company|assortment|full]`)
- **Cel:** Automatyczna ekstrakcja strukturyzowanych metadanych B2B (nazwa, NIP/IČO, adres, telefon, decydent, asortyment nabijarek) bezpośrednio z dynamicznych stron sklepów i hurtowni za pomocą grafów LLM (`SmartScraperGraph`).
- **Zaleta:** Eliminuje ręczne parsowanie HTML i selektory CSS; odporny na zmiany layoutu portali dystrybutorów.

***

#### L6 — Targi i audyty wystawców

> **Dlaczego:** firmy które wystawiają się na targach = finansowo stabilne, z marketing budgetem, z produktem do pokazania. Idealny target na Tier "Authorized" / "Exclusive".

**Główne targi (per region):**

| Targi                             | Lokalizacja              | Cykl             | Co coverage                                                               | Sygnał dla BILLS                                                           |
| --------------------------------- | ------------------------ | ---------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **InterTabac**                    | Dortmund, DE             | Wrzesień, co rok | Top-tier międzynarodowe: hurtownie, właściciele marek, importerzy krajowi | ⭐⭐⭐ **MUST-VISIT** dla partnerów CEE i globalnych                          |
| **Cannafest**                     | Praga, CZ                | Listopad, co rok | Specjalistyczne akcesoria do palenia, headshopy, alternatywne produkty    | ⭐⭐⭐ dla CZ: **Eighty8**, **Bushplanet**, **Zelená Země**, **Konopný Táta** |
| **CEE Retail Expo & FMCG Summit** | Zagrzeb, HR              | Co rok           | FMCG, convenience, logistyka w Chorwacji i regionie Adriatyku             | ⭐⭐ dla HR + okolic                                                         |
| **Transilvania Retail Expo**      | Kluż-Napoka / region, RO | Co rok           | Dystrybutorzy FMCG w Transylwanii                                         | ⭐⭐ dla RO zachód                                                           |
| **Expo Retail & FMCG**            | Bukareszt, RO            | Co rok           | Największe targi FMCG w RO                                                | ⭐⭐ dla RO                                                                  |
| **Moldavia FMCG Expo**            | Kiszyniów, MD            | Co rok           | FMCG, dystrybutorzy Mołdawii                                              | ⭐⭐ dla MD                                                                  |
| **World Vape Show**               | Online/Dubai             | Co rok           | Vape/e-papierosy, cross-sell do B6                                        | ⭐ dla cross-sell                                                           |
| **Eurocis**                       | Düsseldorf, DE           | Luty, co rok     | Retail tech, FMCG, cash\&carry                                            | ⭐ dla logistyki hurtowej                                                   |
| **Tobacco Plus Expo USA**         | Las Vegas, USA           | Styczeń, co rok  | Największe targi tytoniowe w US                                           | ⭐ dla benchmark globalny                                                   |
| **Vapexpo**                       | Paryż / Berlin           | Co rok           | Vape, e-liquid                                                            | ⭐ dla B6                                                                   |

**Workflow:**

1. **Pobierz listę wystawców** (PDF/HTML z oficjalnej strony targów)
2. **Parsuj NIP-y / nazwy firm** (regex lub ręcznie dla PDF)
3. **L0 + L3 walidacja** — sprawdź w rejestrze czy firma aktywna
4. **Szukaj w leadach** — czy już mamy; jeśli nie → dodaj do katalogu A lub B
5. **Vizytówki** — jeśli Marceli jedzie na targi → zbiera wizytówki i NIP-y

**Przykładowe firmy już zidentyfikowane przez tę metodę (per kraj):**

| Kraj    | Firma                     | Źródło                                |
| ------- | ------------------------- | ------------------------------------- |
| 🇨🇿 CZ | **Eighty8 s.r.o.**        | Cannafest (specjalistyczne akcesoria) |
| 🇨🇿 CZ | **Bushplanet s.r.o.**     | Cannafest                             |
| 🇨🇿 CZ | **Zelená Země s.r.o.**    | Cannafest (CBD/konopie)               |
| 🇨🇿 CZ | **Konopný Táta**          | Cannafest (CBD/konopie)               |
| 🇷🇴 RO | **GTS Speciality SRL**    | Romanian FMCG expos                   |
| 🇷🇴 RO | **SC Tobaccoshop SRL**    | Romanian FMCG expos                   |
| 🇷🇴 RO | **Tabaccogifts.ro**       | Romanian FMCG expos (e-commerce)      |
| 🇭🇷 HR | **Delta d.o.o.** (Osijek) | CEE Retail Expo + L9 OSINT            |

***

#### L8 — Katalogi firm i bazy B2B (rozszerzenie regionalne)

> **Cel:** szerokie pokrycie regionalnych dystrybutorów, cash\&carry, sieci convenience. Katalogi krajowe lepiej niż globalne dla lokalnych graczy.

**Polska (PL):**

- **PKT.pl** — Polska Klasyfikacja Towarów i Usług, darmowe wyszukiwanie po PKD

- **Panorama Firm** — 2M+ firm, mapa, opinie

- **Biznesfinder.pl** — darmowe, filtry po PKD i województwie

- **Aleo.com** — 1.5M firm PL, freemium, podgląd NIP i przychodów

- **nipgo.pl** — 3M PL firm, freemium (podgląd NIP i nazw)

- **Bizraport.pl** — sprawozdania finansowe online

**Czechy (CZ):**

- **Firmy.cz** (Seznam) — największy CZ katalog, filtry po NACE

- **Kompass.cz** — międzynarodowy, dobra jakość

- **Peníze.cz firmy** — wyszukiwarka + finanční data

**Rumunia (RO):**

- **ListaFirme.ro** — 1M+ RO firm, free read-only, filtry po CAEN (PKD)

- **Bizoo.ro** — 500k+ firm, dobra dla dystrybutorów FMCG

- **Termene.ro** — finanční data + należności

- **kwerendy specjalistyczne:**

  - `"comert cu ridicata tutun accesorii srl"` (hurtownia tytoniu i akcesoriów)

  - `"importator accesorii fumat China"` (importer akcesoriów do palenia z Chin)

  - `"umplere tigari en-gros"` (hurtowe napełnianie papierosów)

**Multi-EU (cross-border):**

- **Veritor** — 10 EU rejestrów + KYB (Know Your Business)

- **ENTIA** (MCP) — 5.5M EU firm, integracja z AI assistant

- **Kompass** (multi-country) — 3M+ firm EU

**Filtr regionalny (hurtownie PL przykład):**

- **KDWT S.A.** — dystrybutor FMCG

- **Z.A.S.-Pol Sp. z o.o.** — hurtownia

- **Aksel FHU** — dystrybutor regionalny

**Workflow (L8):**

1. Wybierz katalog regionalny dla kraju (np. ListaFirme dla RO)
2. Kwerenda po PKD/CAEN + słowa kluczowe (hurtownia, importer, distributor)
3. Zbierz NIP + nazwę + adres → L0 + L3 walidacja
4. Dodaj do katalogu A lub B

***

#### L7 — YouTube komentarze (real leads)

**Dlaczego:** Pod każdą recenzją "PowerMatic recenzja" / "nabijarka test" kupujący piszą "kupiłem w \[sklep]" / "polecam \[firma]". To **real leads**, nie deklaratywne listy z katalogów.

**Tools:**

- `yt-dlp` (CLI) — pobiera komentarze jako JSON

- Apify YouTube Comments Scraper — gotowy actor

**Przykład:**

```bash
yt-dlp --skip-download --write-comments --print-json "https://www.youtube.com/watch?v=XXX" | jq '.comments'
```

**Następnie:** regex extract URL-ów i nazw sklepów → cross-check z L8/L3.

***

#### L9 — LLM safety (multi-LLM cross-check)

**Wymóg:** każdy NIP/KRS wygenerowany przez LLM musi przejść:

1. **L0 NIP checksum** (instant, eliminuje 70% halucynacji)
2. **L0 KRS name-match** (200ms, eliminuje 95% reszty)
3. **Multi-LLM consensus:** jeśli to samo pytanie do 2+ LLM-ów daje 2 różne NIP-y → odrzuć, szukaj w źródle

**Workflow:**

```python
# Bad: jedno LLM
nip = openrouter_call("Find NIP for X Sp. z o.o. in Poland", model="deepseek")

# Good: multi-LLM + consensus
def consensus_nip(name, country, models=["deepseek", "gemini", "claude"]):
    answers = {m: openrouter_call(name, country, model=m) for m in models}
    # Cross-check: 2/3 muszą się zgodzić
    from collections import Counter
    counter = Counter(answers.values())
    top = counter.most_common(1)[0]
    if top[1] >= 2:
        return top[0]  # consensus
    return None  # no consensus → reject
```

**Bonus:** użyj `o1-preview` lub `claude-opus-4` jako "arbitra" gdy mniejsze modele się nie zgadzają.

**PKD / CN machinery search (krajowi producenci sprzętu):**

> OpenRouter AI OSINT używany programatycznie do crawl regionalnych danych — ale z **konkretnymi PKD i kodami CN** żeby znaleźć krajowych producentów sprzętu do napełniania/pakowania.

- **PKD 28.29.Z** (Produkcja maszyn do ogólnego zastosowania, gdzie indziej niesklasyfikowana) — producenci sprzętu przemysłowego

- **PKD 28.93.Z** (Produkcja maszyn dla przemysłu spożywczego, tytoniowego) — bezpośrednio celuje w producentów maszyn tytoniowych

- **CN 8479 89 97 90** (maszyny i urządzenia mechaniczne, specjalne) — kod celny dla maszyn do napełniania

- **CN 8422 40 00** (maszyny do pakowania) — kod dla maszyn pakujących

**Przykład leada (PKD machinery):**

- 🇵🇱 PL: **Woton Sp. z o.o.** — krajowy producent sprzętu do napełniania/pakowania (PKD 28.93.Z). Nie jest konkurentem BILLS (inny segment przemysłowy), ale **może być partnerem OEM** dla componentów do PowerMatic lub dystrybutorem hurtowym.

**Workflow:**

```python
# 1. Zapytaj LLM o listę firm w danym PKD w danym kraju
results = openrouter_call(
    f"List Polish companies with PKD 28.93.Z that produce "
    f"tobacco or cigarette-filling machinery. Return name, NIP, city.",
    model="gemini"
)
# 2. Dla każdej firmy → L0 NIP checksum + KRS/CEIDG name-match
# 3. FROZEN dopiero po przejściu L0 + L3
```

**Bonus:** te same PKD/CN w innych krajach — np. **CN 8479 89** w RO/BG → producenci OEM w Europie Wschodniej, którzy mogą być partnerem produkcyjnym BILLS (white-label / private label).

***

#### L10 — EUIPO Trademark Search

**URL:** <https://euipo.europa.eu/eSearch> (oficjalne, bezpłatne)

**Workflow:**

1. Szukaj "PowerMatic" / "Hawk" / "Topomat" / "Turbomatic" w EUIPO
2. Pobierz właściciela znaku
3. Sprawdź status (active/lapsed/pending)
4. Cross-check z właścicielem marki w naszej ofercie (BILLS exclusive PL+CEE)

**Dlaczego:** EUIPO jest single source of truth dla EU trademarks. Kto jest właścicielem znaku w EU = kto ma prawo go dystrybuować. Jeśli ktoś w naszym katalogu A deklaruje PowerMatic ale EUIPO pokazuje że znak jest własnością innej firmy → **prawdopodobnie szara strefa**.

***

#### L11 — Zamówienia Publiczne (BZP / TED)

**BZP PL:** <https://ezamowienia.gov.pl> — polskie zamówienia publiczne
**TED EU:** <https://ted.europa.eu> — cała UE

**Filtr:**

- CPV 15800000-6 (diverse food products) — tytoń

- CPV 39200000-4 (furnishing) — akcesoria

- CPV 30100000-0 (office machinery) — maszynki

**Co daje:** twardy evidence kto dostarczał wyroby tytoniowe do instytucji publicznych (szpitale, więzienia, wojsko). Małe wolumeny ale **weryfikowalne referencje**.

**Format danych:** CPV + NIP wykonawcy + wartość umowy + data.

***

### Gdzie co zapisywać

| Plik                                       | Co tam trafia                                                                              |
| ------------------------------------------ | ------------------------------------------------------------------------------------------ |
| **methodology.md** ⭐ kanoniczny            | Reguły, schematy, definicje (tier, wolumen, flagi, CSV, rejestry)                          |
| **INTEL.md**                               | Strategiczne odkrycia: partnerzy 🐋, ryzyka, newsy, narzędzia, realne dane rynkowe         |
| **DZIENNIK.md**                            | Postęp prac, decyzje, pytania, feedback, schema changes                                    |
| **`data/{Kraj}/{KOD}.md`**                 | Dziennik badawczy per kraj: znalezione firmy, niespodzianki, czerwone flagi, gemy, wnioski |
| **`data/{Kraj}/SŁOWNIK-{KOD}.md`**         | Frazy do Google/DuckDuckGo/Brave + wolumeny (lokalne + EN + site: filtry + social)         |
| **`data/{Kraj}/catalog-{A\|B}-{KOD}.csv`** | Dane firm (katalog A i B osobno)                                                           |
| **`data/audit-log.md`**                    | Historia weryfikacji (per uruchomienie verify\_run)                                        |

**Reguły:**

- Po każdym researchu / scrape / search: jeśli coś warte zapisania → natychmiast do pliku

- Intel = strategic / zmienia decyzje

- Dziennik = reszta (praca, pytania, feedback)

- Jeśli nie wiesz gdzie → dziennik

### Struktura folderu kraju

```
data/{Kraj}/                          # np. data/Polska/, data/Czechy/
├── {KOD}.md                          # dziennik badawczy (free-form)
├── SŁOWNIK-{KOD}.md            # słownik fraz + wolumeny
├── catalog-A-{KOD}.csv              # firmy z nabijarkami
└── catalog-B-{KOD}.csv              # branża tytoniowa bez nabijarek
```

Foldery nazwane po polsku (Polska, Czechy, Bułgaria…). Kody ISO w nazwach plików (PL, CZ, BG, …).

***

## 3. Katalog A — Firmy z nabijarkami

### Oś główna: relacja z marką

| Kod    | Kategoria                 | Znaczenie dla BILLS                                                     |
| ------ | ------------------------- | ----------------------------------------------------------------------- |
| **A1** | Tylko PowerMatic          | Sub-dystrybutorzy / autoryzowani resellerzy BILLS                       |
| **A2** | Tylko Hawk                | Potencjalny kanał dla Hawk (osobna marka do zbudowania)                 |
| **A3** | PowerMatic + Hawk         | Najcenniejsi — sprawdzeni w branży, znają oba produkty                  |
| **A4** | Multi-brand z PM/Hawk     | Resellerzy wielu marek (Topomat, GM, Turbomatic + PM/Hawk)              |
| **A5** | Własna marka / OEM z Chin | **Konkurencja cenowa** — prywatne marki importerów (zostaje w katalogu) |
| **A6** | Multi-brand bez PM/Hawk   | Kandydaci do pozyskania — znają kanał, nie mają jeszcze naszych marek   |

### Oś uzupełniająca: typ relacji konkurencyjnej

| Flaga                   | Typ                                                                | Przykład                                            |
| ----------------------- | ------------------------------------------------------------------ | --------------------------------------------------- |
| 🔴 **KONK-BEZPOŚREDNI** | Sprzedaje dokładnie ten sam produkt (klon 1:1 z Chin)              | Topomat, Turbomatic, GM, Luxfux (część asortymentu) |
| 🟡 **KONK-POŚREDNI**    | Nabijarki, ale innej półce cenowej / mechanizmie                   | Ręczne injektory, tanie injektory no-name           |
| 🟢 **PARTNER**          | Nie konkurentem, może być kanałem                                  | Sklep tytoniowy, hurtownia wielobranżowa            |
| 🐋 **BIG FISH**         | Najgrubsza ryba w danym kraju                                      | Sieci sklepów, hurtownie ogólnokrajowe              |
| 💎 **GEM**              | Off-internet — FB grupa, targi, OLX, opakowanie z numerem seryjnym | Jednoosobowe JDG, małe sklepy bez WWW               |
| ✅ **BILLS-LIKE**        | Profil firmy podobny do BILLS (import + dystrybucja + serwis)      | Benchmark lub partnerstwo                           |

### Flagi weryfikacji relacji z marką

> **Domyślnie: 🔍 (niezweryfikowane).** Nie wiem czy firma faktycznie ma dostęp do PM/Hawk przez BILLS. Flagi weryfikacji wstawiam **tylko** z twardymi dowodami.

| Flaga          | Znaczenie                                  | Skąd to wiem                           |
| -------------- | ------------------------------------------ | -------------------------------------- |
| 📋 ORG-CEL     | Pojawiło się w dokumentach organów celnych | KAS, WSA, jawne rejestry               |
| 🧾 FV-PDF      | Faktura/CMR/Packing list publicznie        | FB grupy, Allegro opinie, case studies |
| 📦 OPAKOWANIE  | Numer seryjny / plomba wskazuje na kanał   | Zdjęcia produktu, recenzje             |
| 🗣️ DEKLARACJA | Firma deklaruje autoryzację                | Strona www, LinkedIn, komunikat        |
| 📜 KONTRAKT    | Zewnętrzna informacja o umowie             | Wywiad, case study, raport             |

**Kiedy stosować:**

- Lista "kto ma dostęp do PM/Hawk przez BILLS" → filtry tylko flagi weryfikacji

- Lista "kto handluje podobnym asortymentem" → bez filtra

- Konkurent — marka nie ma znaczenia, liczy się profil

### Status weryfikacji (FROZEN / DO-WERYFIKACJI / FABRYKAT)

Każdy wpis w CSV ma jeden z trzech statusów w `flagi`:

| Status            | Znaczenie                                   | Jak stwierdzić                                                       |
| ----------------- | ------------------------------------------- | -------------------------------------------------------------------- |
| ✅ FROZEN          | Firma zweryfikowana 2 niezależnymi źródłami | 2-tool check (web\_search + whois/registry) przeszedł, name match OK |
| ✅ FROZEN (API)    | Weryfikacja przez oficjalne API             | KRS API / CEIDG API / ARES / VIES + name match OK                    |
| ⚠️ DO-WERYFIKACJI | Weryfikacja niepełna, brak 2. źródła        | Tylko 1 źródło, lub brak danych                                      |
| 🔴 FABRYKAT       | Wpis halucynowany lub błędny                | KRS API → inna firma, NIP checksum fail, web\_search nie potwierdza  |

**🔴 FABRYKAT — sygnały ostrzegawcze:**

- LLM (Gemini, DeepSeek) generuje poprawne NIP/KRS które wskazują na zupełnie inne firmy

- KRS API zwraca sukces dla każdego istniejącego KRS, niezależnie od nazwy w CSV

- NIP checksum przechodzi dla poprawnie skonstruowanych (ale halucynowanych) numerów

- **Jedyna sensowna ochrona: name match + 2 niezależne źródła**

**Procedura FROZEN (2-tool check):**

1. **Web search** — `"<firma>" "<miasto>" tobacco wholesale verify` (albo odpowiednik w lokalnym języku)
2. **Whois** — `whois -h <TLD-server> <domain>` (jeśli firma ma www)
3. **Registry API** (opcjonalnie) — KRS / CEIDG / ARES / VIES, ale zawsze **name match** weryfikacją
4. **PASS × 2** → FROZEN. **Mismatch** → FABRYKAT (delete).

Szczegóły w `tools/VERIFICATION-PATTERN.md`.

***

## 4. Katalog B — Branża tytoniowa (cross-sell)

### Powinowactwo z nabijarkami (skala 1-5)

> 5 = klient niemal na pewno kupi nabijarkę. 1 = marginalny overlap.

| Kod    | Specjalizacja                                             | Pow.  | Uzasadnienie                                             |
| ------ | --------------------------------------------------------- | ----- | -------------------------------------------------------- |
| **B1** | Tytoń liście / tytoń do skręcania                         | 5     | Klient kupuje surowiec → nabijarka = upsell              |
| **B2** | Bibułki papierosowe                                       | 5     | Top-of-mind palaczy skręcających                         |
| **B3** | Filtry / gilzy                                            | 5     | Klient już w kategorii                                   |
| **B4** | Akcesoria (zapalniczki, popielniczki, fajki, cygarniczki) | 3     | Te same sklepy, inna demografia                          |
| **B5** | Shisha / hookah                                           | 2     | Shared retail channel, ale klienci się nie pokrywają     |
| **B6** | E-papierosy / vape                                        | 2     | Shared channel, ale rozbieżne regulacje                  |
| **B7** | Saszetki nikotynowe (snus / pouches)                      | 2     | Rosnący segment, klient raczej nie skręca                |
| **B8** | Pełne hurtownie tytoniowe                                 | **5** | **Najwyższy priorytet** — mają wszystko poza nabijarkami |
| **B9** | CBD / konopie / susz                                      | 4     | Wysoki overlap kliencki (jointy z suszu)                 |

**Kryterium: overlap kliencki, nie kanałowy.**

***

## 5. Tier i Wolumen

### TIER — typ relacji handlowej

| Tier            | Co to znaczy                                   | Jak rozpoznać                                                                  | Typowa skala PL  |
| --------------- | ---------------------------------------------- | ------------------------------------------------------------------------------ | ---------------- |
| **Exclusive**   | Wyłączność na kraj/region, umowa z producentem | "Jedyny autoryzowany dystrybutor na...", faktury bezpośrednio, plombowe numery | 1-2 per kraj     |
| **Authorized**  | Partner z umową, bez wyłączności terytorialnej | "Autoryzowany sprzedawca", karta gwarancyjna w ich nazwie                      | 5-15 per kraj    |
| **Reseller**    | Hurtowo kupuje lub sam importuje, bez umowy    | Brak oznaczenia "oficjalny", własna polityka cenowa                            | 30-100 per kraj  |
| **Retailer**    | Sklep detaliczny, wąska marża, 5-50 sztuk      | Brak logistyki hurtowej                                                        | Setki per kraj   |
| **Marketplace** | Allegro/Amazon/eBay/OLX, często dropshipping   | Konto >5k opinii, brak magazynu                                                | Tysiące per kraj |

> **Granica płynna.** Marketplace z 10k maszyn/rok = de facto reseller.

### WOLUMEN — heurystyki estymacji

**Sygnały mocne (od najłatwiejszego):**

1. **Opinie Allegro/Amazon** — opinie × \~20 = przybliżona sprzedaż roczna
2. **Pracownicy (KRS/CEIDG)** — 1-2 = mały, 5-20 = średni, 50+ = duży
3. **Powierzchnia magazynu** (Google Maps, wizytówki)
4. **Asortyment** — wąski z dużą rotacją vs szeroki z wolną
5. **Ceny** — 25-35% poniżej katalogu = hurt, +5% = detal
6. **Certyfikaty dealerskie / targi** → zwykle wyższy tier
7. **Flota pojazdów** widoczna na wizytówce
8. **Własna marka** → prawie zawsze duży wolumen

**Progi (kalibrowane na rynek niszowy, nie ogólny):**

| Skala rynku | Kraje                  | Mały/m-c | Średni/m-c | Duży/m-c |
| ----------- | ---------------------- | -------- | ---------- | -------- |
| **duży**    | PL, CZ, FR             | <50      | 50-500     | 500+     |
| **średni**  | RO, BG, HR, SI, SK, RS | <20      | 20-200     | 200+     |
| **mały**    | LT, LV, EE, MD         | <5       | 5-50       | 50+      |

**Skala rynku wypełnia się automatycznie po** **`kraj`** — nie wpisuj ręcznie.

> **⚠️ Zastrzeżenie:** Rynek nabijarek to nisza. Nawet "duży" gracz w PL to realnie 200-500 szt/m. Progi 500+ to naprawdę największe hurtownie ogólnopolskie (BILLS, Sanitex, Topomat).

**Confidence indicator:**

- 🟢 wysoka — twarde dane (opinie Allegro, faktury, deklaracje)

- 🟡 średnia — sygnały pośrednie (pracownicy, asortyment, ceny)

- 🔴 niska — zgadywanie, brak sygnałów

Format: `duży 🟢`, `mały 🔴`, itd.

***

## 6. Rejestry i API per kraj

### 🇵🇱 POLSKA

| Rejestr                               | URL API                                                                | Co dostaje                                                    | Auth                               |
| ------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------- | ---------------------------------- |
| **NIP** (10 cyfr)                     | —                                                                      | tax ID                                                        | —                                  |
| **KRS** (spółki)                      | `https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{KRS}`                | Pełny odpis: zarząd, wspólnicy, kapitał, PKD, adres, historia | ❌ brak (limit 20/min)              |
| **KRS wyszukiwarka**                  | `https://wyszukiwarka-krs.ms.gov.pl/`                                  | Search by name/NIP/REGON                                      | ❌ brak                             |
| **CEIDG v3** (JDG)                    | `https://dane.biznes.gov.pl/api/ceidg/v3/firmy?nazwa=X&status=AKTYWNY` | NIP, REGON, adres, status, PKD                                | ✅ Bearer token (`CEIDG_API_TOKEN`) |
| **REGON** (BIR1.1, GUS)               | `https://api.stat.gov.pl/Home/RegonApi`                                | NIP/REGON/KRS → nazwa, adres, PKD, forma prawna, daty         | ✅ USER\_KEY (`REGON_API_KEY`)      |
| **Przeglądarka DF**                   | `https://ekrs.ms.gov.pl/rdf/pd/search_df?Krs={KRS}`                    | Sprawozdania finansowe .xml                                   | ❌ brak                             |
| **KRZ** (Krajowy Rejestr Zadłużonych) | `https://prs.ms.gov.pl/krz`                                            | Dłużnicy, upadłości                                           | ❌ brak                             |
| **Biała lista VAT**                   | `https://www.podatki.gov.pl/wykaz-podatnikow-vat-wyszukiwarka`         | Status VAT, rachunki                                          | ❌ brak                             |
| **PKD**                               | —                                                                      | Kody działalności (46.35Z hurt tytoniowy, 47.11Z sklepy)      | —                                  |

**Wzorzec ładowania tokena (Python):**

```python
import os

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
with open(ENV_PATH) as f:
    for line in f:
        if "=" in line:
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

TOKEN = os.environ.get("CEIDG_API_TOKEN")
```

**Chain automatyczny (NIP/REGON → KRS):**

```bash
python3 tools/krs_search.py --nip 5140361901 --financials
```

***

### 🇨🇿 CZECHY

| Rejestr                        | URL                                                                           | Auth     |
| ------------------------------ | ----------------------------------------------------------------------------- | -------- |
| **IČO** (8 cyfr)               | —                                                                             | —        |
| **DIČ**                        | —                                                                             | CZ + IČO |
| **ARES**                       | `https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ICO}` | ❌        |
| **ARES finanční údaje**        | `…/ekonomicke-subjekty/{ICO}/financni-udaje`                                  | ❌        |
| **OR** (Obchodní rejstřík)     | `https://or.justice.cz`                                                       | ❌        |
| **ŽR** (Živnostenský rejstřík) | `https://www.rzp.cz`                                                          | ❌        |
| **ISIR** (upadłości)           | `https://isir.justice.cz`                                                     | ❌        |

***

### 🇸🇰 SŁOWACJA

| Rejestr                | URL                                  | Auth |
| ---------------------- | ------------------------------------ | ---- |
| **IČO**, **IČ DPH**    | —                                    | —    |
| **ORSR**               | `https://orsr.sk/hladaj_subjekt.asp` | ❌    |
| **ŽRSR**               | `https://www.zrsr.sk`                | ❌    |
| **RUZ** (sprawozdania) | `https://www.registeruz.sk`          | ❌    |
| **Finančná správa**    | `https://www.financnasprava.sk`      | ❌    |

***

### 🇷🇴 RUMUNIA

| Rejestr                     | URL                     | Auth                 |
| --------------------------- | ----------------------- | -------------------- |
| **CUI/CIF** (tax ID)        | —                       | —                    |
| **ONRC**                    | `https://www.onrc.ro`   | ✅ paid (8 lei/odpis) |
| **ANAF** (tax)              | `https://www.anaf.ro`   | ❌                    |
| **PFA** (JDG)               | ONRC                    | —                    |
| **ListaFirme** (aggregator) | `https://listafirme.ro` | ❌                    |
| **Termene** (finansowe)     | `https://termene.ro`    | ❌                    |

***

### 🇱🇹 LITWA

| Rejestr                         | URL                                                          | Auth |
| ------------------------------- | ------------------------------------------------------------ | ---- |
| **VMN** (kodas) / **PVM** (VAT) | —                                                            | —    |
| **JAR**                         | `https://rekvizitai.vz.lt`, `https://www.registrucentras.lt` | ❌    |
| **MB** (JDG)                    | też w JAR                                                    | —    |
| **VMI** (tax)                   | `https://www.vmi.lt`                                         | ❌    |

***

### 🇱🇻 ŁOTWA

| Rejestr                  | URL                      | Auth |
| ------------------------ | ------------------------ | ---- |
| **PVN** (VAT)            | —                        | —    |
| **UR**                   | `https://info.ur.gov.lv` | ❌    |
| **VID** (tax)            | `https://www.vid.gov.lv` | ❌    |
| **Lursoft** (aggregator) | `https://lursoft.lv`     | ❌    |

***

### 🇪🇪 ESTONIA

| Rejestr             | URL                          | Auth                     |
| ------------------- | ---------------------------- | ------------------------ |
| **KM** (VAT)        | —                            | —                        |
| **e-Äriregister** ⭐ | `https://ariregister.rik.ee` | ❌ (najlepszy w regionie) |
| **EMTA** (tax)      | `https://www.emta.ee`        | ❌                        |

***

### 🇫🇷 FRANCJA

| Rejestr                                  | URL                         | Auth                  |
| ---------------------------------------- | --------------------------- | --------------------- |
| **SIREN** (9 cyfr) / **SIRET** (14 cyfr) | —                           | —                     |
| **TVA**                                  | —                           | FR + 2 cyfry + SIREN  |
| **RCS** (Infogreffe)                     | `https://www.infogreffe.fr` | ✅ paid                |
| **INPI** (marki)                         | `https://www.inpi.fr`       | ❌                     |
| **Pappers.fr** ⭐                         | `https://pappers.fr/api`    | ✅ paid (najlepsze FR) |
| **Societe.com**                          | `https://www.societe.com`   | ❌ (z limitem)         |
| **Bodacc** (annonces)                    | `https://www.bodacc.fr`     | ❌                     |
| **Douanes** (cło)                        | —                           | —                     |

***

### 🇲🇩 MOŁDAWIA

| Rejestr                          | URL                      | Auth      |
| -------------------------------- | ------------------------ | --------- |
| **IDNO** (13 cyfr)               | —                        | —         |
| **Camera Înregistrării de Stat** | `https://www.cis.gov.md` | ❌         |
| **TVA**                          | —                        | MD + IDNO |
| **Serviciul Vamal** (cło)        | —                        | —         |

***

### 🇧🇬 BUŁGARIA

| Rejestr                          | URL                         | Auth |
| -------------------------------- | --------------------------- | ---- |
| **EIK** (9 cyfr) / **DDS** (VAT) | —                           | —    |
| **Търговски регистър**           | `https://portal.justice.bg` | ❌    |
| **НАП** (tax)                    | `https://www.nap.bg`        | ❌    |

***

### 🇸🇮 SŁOWENIA

| Rejestr             | URL                    | Auth                                      |
| ------------------- | ---------------------- | ----------------------------------------- |
| **ID za DDV** (VAT) | —                      | —                                         |
| **AJPES** ⭐         | `https://www.ajpes.si` | ❌ (dane + bilans + RZiS w jednym miejscu) |
| **FURS** (tax)      | `https://www.furs.si`  | ❌                                         |

***

### 🇭🇷 CHORWACJA

| Rejestr                  | URL                             | Auth |
| ------------------------ | ------------------------------- | ---- |
| **OIB** (11 cyfr)        | —                               | —    |
| **Sudski registar**      | `https://sudreg.pravosudje.hr`  | ❌    |
| **Porezna uprava** (tax) | `https://www.porezna-uprava.hr` | ❌    |

***

### 🇷🇸 SERBIA (poza scope — competitive intel)

| Rejestr          | URL                      | Auth |
| ---------------- | ------------------------ | ---- |
| **PIB** (9 cyfr) | —                        | —    |
| **APR**          | `https://www.apr.gov.rs` | ❌    |
| **Carina** (cło) | `https://www.carina.rs`  | ❌    |

***

## 7. Marketplace per kraj

| Kraj    | Główne                            | Drugorzędne                                | Notatki                                       |
| ------- | --------------------------------- | ------------------------------------------ | --------------------------------------------- |
| 🇵🇱 PL | **Allegro**                       | OLX, Ceneo, Kaufland, **InPost Buy**, Erli | Allegro = must-have. InPost Buy rośnie szybko |
| 🇨🇿 CZ | **Heureka**, Zboží.cz, Aukro      | Bazoš, Alza                                | Heureka = porównywarki, Aukro = aukcje        |
| 🇸🇰 SK | **Heureka.sk**, Bazoš             | Mall.sk, Alza                              | Mały rynek, Heureka daje dobre dane o cenach  |
| 🇷🇴 RO | **eMAG**, OLX                     | Okazii, Cel.ro                             | eMAG = Amazon regionu, OLX = ogłoszenia       |
| 🇱🇹 LT | **Skelbiu.lt**                    | Vinted, Aruodas                            | Skelbiu = ogłoszenia                          |
| 🇱🇻 LV | **SS.lv**                         | Vinted                                     | Mały rynek, SS.lv dominuje                    |
| 🇪🇪 EE | **Osta.ee**                       | Vinted                                     | Estonka scena bardzo cyfrowa                  |
| 🇫🇷 FR | **Leboncoin**, Rakuten, Cdiscount | Vinted, Amazon.fr                          | Leboncoin = must-have                         |
| 🇲🇩 MD | **999.md**, OLX                   | —                                          | Mały rynek, 999.md to lokalny portal          |
| 🇧🇬 BG | **OLX**, Bazar.bg                 | —                                          | OLX dominuje, Bazar.bg dla produktów          |
| 🇸🇮 SI | **Bolha.com**, Mimovrste, Ceneje  | —                                          | Bolha = OLX Slovenii                          |
| 🇭🇷 HR | **Njuškalo**, Index Oglasi        | —                                          | Njuškalo = must-have                          |
| 🇷🇸 RS | **KupujemProdajem**               | Limundo                                    | Poza scope — competitive intel                |

***

## 8. Regulacje per kraj

> Stan wiedzy: 2024-2025, do weryfikacji.

| Kraj    | Reżim tytoniowy               | E-papierosy                          | CBD/susz                                         | Nabijarki      | Uwagi                              |
| ------- | ----------------------------- | ------------------------------------ | ------------------------------------------------ | -------------- | ---------------------------------- |
| 🇵🇱 PL | Akcyza, zakaz reklamy         | Legalne, smakowe dyskutowane         | Susz legalny z limitem THC, CBD w szarej strefie | Bez ograniczeń | Sprawdzić akcyzę od 2025           |
| 🇨🇿 CZ | Akcyza, ograniczenia reklamy  | Legalne, smakowe w drodze            | CBD legalne, susz nielegalny                     | Bez ograniczeń | Otwarty rynek                      |
| 🇸🇰 SK | j.w. EU                       | Legalne, smakowe                     | CBD legalne, susz nielegalny                     | Bez ograniczeń | Mały rynek                         |
| 🇷🇴 RO | **Plain packaging od 2020**   | Surowe ograniczenia smakowe          | CBD w szarej strefi                              | Bez ograniczeń | Trudny rynek, antynikotynowe lobby |
| 🇱🇹 LT | Akcyza EU                     | **Zakaz smakowych liquidów od 2023** | CBD legalne, susz nielegalny                     | Bez ograniczeń | Surowe podejście                   |
| 🇱🇻 LV | Akcyza EU                     | Legalne, ograniczenia                | CBD legalne, susz nielegalny                     | Bez ograniczeń | Umiarkowane                        |
| 🇪🇪 EE | Akcyza EU                     | Legalne, smakowe dyskutowane         | CBD legalne, susz nielegalny                     | Bez ograniczeń | Cyfrowo zaawansowany               |
| 🇫🇷 FR | **Plain packaging od 2017**   | Legalne, mocno ograniczone           | CBD legalny, susz nielegalny                     | Bez ograniczeń | Wysokie akcyzy, surowe             |
| 🇲🇩 MD | Poza UE, własne               | Liberalne                            | Liberalne                                        | Bez ograniczeń | Szansa na szary rynek              |
| 🇧🇬 BG | Akcyza EU                     | Legalne, smakowe                     | CBD legalne, susz nielegalny                     | Bez ograniczeń | Rynek otwarty                      |
| 🇸🇮 SI | Akcyza EU                     | Legalne, ograniczenia                | CBD legalne, susz nielegalny                     | Bez ograniczeń | Mały rynek                         |
| 🇭🇷 HR | Akcyza EU                     | Legalne, ograniczenia                | CBD legalne, susz nielegalny                     | Bez ograniczeń | Wstęp do Bałkanów                  |
| 🇷🇸 RS | Akcyza (poza UE, TPD-aligned) | Do weryfikacji                       | Do weryfikacji                                   | Bez ograniczeń | Poza scope — competitive intel     |

**Ryzyka regulacyjne:**

- 🔴 **Wysokie**: FR, RO, LT (trudne rynki dystrybucji maszyn)

- 🟡 **Średnie**: PL, LV, SK (standardowe EU)

- 🟢 **Niskie**: CZ, BG, SI, HR, EE (otwarte)

- ⚠️ **Specjalne**: MD (szara strefa, poza UE — uwaga na cło i akcyzę)

***

## 9. Kolejność geograficzna

1. 🇵🇱 **Polska** — fundament
2. 🇨🇿 **Czechy** — blisko, szybki ROI
3. 🇸🇰 **Słowacja** — szybki
4. 🇭🇷 **Chorwacja** — wstęp do Bałkanów
5. 🇧🇬 **Bułgaria** — otwarty
6. 🇸🇮 **Słowenia** — mały, ale łatwy
7. 🇷🇴 **Rumunia** — wymaga strategii (duży, trudne regulacje)
8. 🇪🇪 **Estonia** — cyfrowa, mała
9. 🇱🇻 **Łotwa** — mała
10. 🇱🇹 **Litwa** — surowa
11. 🇫🇷 **Francja** — wymaga strategii (najtrudniejsza, ale największy potencjał)
12. 🇲🇩 **Mołdawia** — specyficzna, poza EU
13. 🇷🇸 **Serbia** — poza scope (competitive intel)

***

## 10. Schemat CSV (zunifikowany)

Każdy plik `data/{Kraj}/catalog-{A|B}-{KOD}.csv` ma **identyczny** zestaw 35 kolumn. Pola specyficzne dla A lub B są puste w rekordach drugiego katalogu.

### Kolumny (35)

| #  | Kolumna                  | Typ  | Opis                                                                                                 |
| -- | ------------------------ | ---- | ---------------------------------------------------------------------------------------------------- |
| 1  | `related_to`             | str  | ID firm powiązanych (sister firms, sukcesja)                                                         |
| 2  | `rok_zalozenia`          | YYYY | Rok rejestracji                                                                                      |
| 3  | `id`                     | str  | `{KOD}-{A\|B}-{NNN}`, np. `PL-A-001` (region-free)                                                   |
| 4  | `kategoria`              | enum | A1-A6 lub B1-B9                                                                                      |
| 5  | `nazwa`                  | str  | Pełna nazwa prawna lub handlowa                                                                      |
| 6  | `kraj`                   | ISO2 | Dwuliterowy kod                                                                                      |
| 7  | `miasto`                 | str  | <br />                                                                                               |
| 8  | `adres`                  | str  | Ulica + numer + kod                                                                                  |
| 9  | `nip_vat`                | str  | Lokalny odpowiednik NIP                                                                              |
| 10 | `rejestr_id`             | str  | KRS / IČO / ONRC / OIB (kanoniczna kolumna rejestrowa)                                               |
| 11 | `www`                    | str  | URL lub `brak`                                                                                       |
| 12 | `kanal_zamiennik`        | str  | Co mają zamiast WWW: FB, OLX, Allegro shop, Google                                                   |
| 13 | `email`                  | str  | Główny kontakt                                                                                       |
| 14 | `telefon`                | str  | Z numerem kierunkowym                                                                                |
| 15 | `linkedin`               | URL  | Profil firmy                                                                                         |
| 16 | `facebook`               | URL  | Strona firmy                                                                                         |
| 17 | `instagram`              | URL  | Profil firmy                                                                                         |
| 18 | `tiktok`                 | URL  | Profil firmy (TikTok)                                                                                |
| 19 | `tier`                   | enum | `wyłączność` / `autoryzowany` / `reseller` / `detalista` / `marketplace` / `producent` / `hurtownik` |
| 20 | `marki_nabijarki`        | list | A: PowerMatic, Hawk, Topomat, GM, Turbomatic                                                         |
| 21 | `marka_wlasna_oem`       | str  | A: nazwa marki własnej                                                                               |
| 22 | `sourcing`               | enum | Chiny / Europa / Polska / mix                                                                        |
| 23 | `wolumen`                | enum | mały / średni / duży                                                                                 |
| 24 | `confidence_wolumen`     | enum | 🟢 / 🟡 / 🔴                                                                                         |
| 25 | `kanal_sprzedaży`        | enum | B2B only / sklep stacjonarny / marketplace / własny e-commerce / mix                                 |
| 26 | `powinowactwo_nabijarki` | 1-5  | B: tylko (puste w A)                                                                                 |
| 27 | `cross_sell_potential`   | enum | B: wysoki / średni / niski                                                                           |
| 28 | `decydent`               | str  | Imię i nazwisko                                                                                      |
| 29 | `stanowisko`             | str  | CEO / właściciel / dyrektor                                                                          |
| 30 | `email_decydent`         | str  | Bezpośredni email (jeśli inny)                                                                       |
| 31 | `zrodlo_danych`          | str  | CEIDG, KRS, FB grupa X, OLX, targi Y, recenzja Z                                                     |
| 32 | `data_weryfikacji`       | date | YYYY-MM-DD                                                                                           |
| 33 | `flagi`                  | list | Kombinacja 🔴/🟡/🟢/🐋/💎/✅/🔍 + flagi weryfikacji                                                   |
| 34 | `notatki`                | str  | Dowolne obserwacje                                                                                   |
| 35 | `rynek_skala`            | enum | duży / średni / mały (auto po `kraj`)                                                                |

> **Usunięte 2026-08-12** (decyzja Marceli): `region_kod`, `region_typ`, `_reg_code`, `region_nazwa`.
>
> - `region_kod` → 61% wierszy w master miało "XX" (placeholder) — kolumna bez sygnału.
>
> - `region_typ` → typ jednostki adm. (województwo/kraj) bez użytecznej typologii poniżej PL.
>
> - `_reg_code` → kolumna nadmiarowa z `rejestr_id` (przeniesiona 2026-08-12 13:40).
>
> - `region_nazwa` → usunięta wraz z pozostałymi polami regionu — schema 35-kolumnowa bez pól regionu, `id` region-free.
>   Migrację wykonał `tools/drop_region_columns.py` (idempotentny, dry-run + --apply). Po migracji zregenerowano `data/.verify-state/row-hashes.json` przez `python3 tools/verify_run.py --init`, żeby schema-change nie triggerował masowej re-weryfikacji.

### Konwencje wartości

- **kategoria**: A1, A2, A3, A4, A5, A6, B1, B2, …, B9

- **flagi**: wieloznakowe, np. `🔴💎` (konkurent+gem), `🟢📦` (partner+zweryfikowany numerem seryjnym)

- **wolumen + confidence**: np. `mały 🟡`, `duży 🟢`

- **rynek\_skala**: duży (PL/CZ/FR) / średni (RO/BG/HR/SI/SK) / mały (LT/LV/EE/MD)

- **CSV**: UTF-8 z BOM (polskie znaki w Excelu), separator przecinek, cudzysłów `"…"` gdy przecinek, linie LF, daty YYYY-MM-DD

### 🔓 Ścieżka C (2026-08-25): loose matching w walidatorze

Metodologia trzyma **strict enum** dla nowych wpisów. Walidator (`tools/validate_columns.py`) akceptuje **loose warianty** żeby nie flagować historycznych danych jako błędy:

- `sourcing`: enum jest `{Chiny, Europa, Polska, mix}`. Walidator akceptuje też substring/first-word match z rozszerzonej listy: `import`, `hurt`, `hurtownia`, `veleprodaja`, `dystrybucja`, `produkcja`, `e-commerce`, `sieć`, `salon`, `skład`, `logistyka`, `agent`, `broker`, `sklepy`, `krajowa`, `regionalna`, `ogólnokrajowa`, `import + dystrybucja`, `własna produkcja`.

- `kanal_sprzedaży`: enum jest `{B2B only, sklep stacjonarny, marketplace, własny e-commerce, mix}`. Walidator akceptuje też: `hurt`, `hurtownia`, `veleprodaja`, `dystrybucja`, `e-commerce`, `sieć`, `salon`, `skład`, `logistyka`, `agent`, `broker`, `sklepy`.

- `cross_sell_potential`: enum jest `{wysoki, średni, niski}`. Walidator akceptuje też `bardzo wysoki` (substring match `wysoki`).

**Nowe wpisy** powinny używać strict enum. Historyczne dane z rozszerzonymi wartościami są akceptowane przez walidator (loose match) ale **nie są traktowane jako wzorzec** dla nowych rekordów. Decyzja 2026-08-25 (Marceli) — ścieżka C po audycie 1901 critical / 437 warning na 28 plikach.

Narzędzia pomocnicze:

- `tools/validate_columns.py` — loose-match validator (header mapping, per-column rules, cross-consistency A/B)

- `tools/normalize_kolumny.py` — idempotent fixes dla PL katalogów (FixA junk values, FixB misplaced digits, FixC A→B contamination, FixD B→A contamination)

- `tools/sync_verifier.py` — 1:1 diff master ↔ per-kraj katalogi

### Kody regionów PL (16 województw)

> Od 2026-08-12 `id` jest region-free (`PL-A-001`) — regiony nie są kodowane w ID ani w kolumnach CSV.
> Poniższa tabela to mapa pomocnicza do odczytu starych ID z regionem (`PL-A-WP-001`).

| Kod | Nazwa              | Kod | Nazwa               |
| --- | ------------------ | --- | ------------------- |
| DS  | dolnośląskie       | LU  | lubelskie           |
| KP  | kujawsko-pomorskie | LB  | lubuskie            |
| LD  | łódzkie            | MA  | małopolskie         |
| MZ  | mazowieckie        | OP  | opolskie            |
| PK  | podkarpackie       | PD  | podlaskie           |
| PM  | pomorskie          | SL  | śląskie             |
| SW  | świętokrzyskie     | WN  | warmińsko-mazurskie |
| WP  | wielkopolskie      | ZP  | zachodniopomorskie  |

> `SW` (nie SK — bo SK to Słowacja). Brak regionu → `XX` (placeholder w ID).

### Wypełnianie

- **Minimum**: `id`, `kategoria`, `nazwa`, `kraj`, `miasto`, JEDEN kontakt (email/tel/FB)

- **Pełne**: wszystkie kolumny + źródła zweryfikowane + flagi

- **Częściowe**: kluczowe kolumny + notatka co jeszcze trzeba

***

## 11. Cele ilościowe

**Filozofia:** mniej rekordów z polami wypełnionymi > więcej rekordów z dziurami. Każdy rekord musi mieć: nazwę, kraj, miasto, kontakt (email LUB tel LUB link).

### Katalog A (firmy z nabijarkami)

| Kraj    | Target    | Priorytet | Uwagi                                |
| ------- | --------- | --------- | ------------------------------------ |
| 🇵🇱 PL | **40-60** | ⭐⭐⭐       | Fundament, najgłębszy research       |
| 🇨🇿 CZ | **20-30** | ⭐⭐⭐       | Drugi pełny research                 |
| 🇸🇰 SK | 5-10      | ⭐         | Pokrycie z CZ                        |
| 🇭🇷 HR | 8-12      | ⭐         | Rosnący                              |
| 🇧🇬 BG | 8-12      | ⭐         | Otwarty                              |
| 🇸🇮 SI | 3-6       | ⭐         | Bardzo mały                          |
| 🇷🇴 RO | 10-15     | ⭐⭐        | Duży, trudne regulacje               |
| 🇪🇪 EE | 3-5       | ⭐         | Mały, zdigitalizowany                |
| 🇱🇻 LV | 2-4       | ⭐         | Pokrycie z LT/EE                     |
| 🇱🇹 LT | 3-5       | ⭐         | Surowy                               |
| 🇫🇷 FR | 15-25     | ⭐⭐        | Najtrudniejszy, największy potencjał |
| 🇲🇩 MD | 5-10      | ⭐         | Specyficzny, poza EU                 |

**Cel łączny A: \~120-200 firm** w pierwszej fali.

### Katalog B (cross-sell pool)

| Kraj    | Target    | Priorytet |
| ------- | --------- | --------- |
| 🇵🇱 PL | **20-30** | ⭐⭐⭐       |
| 🇨🇿 CZ | 10-15     | ⭐⭐        |
| 🇸🇰 SK | 3-6       | ⭐         |
| 🇭🇷 HR | 5-8       | ⭐         |
| 🇧🇬 BG | 5-8       | ⭐         |
| 🇸🇮 SI | 2-4       | ⭐         |
| 🇷🇴 RO | 8-12      | ⭐⭐        |
| 🇪🇪 EE | 2-3       | ⭐         |
| 🇱🇻 LV | 2-3       | ⭐         |
| 🇱🇹 LT | 2-4       | ⭐         |
| 🇫🇷 FR | 10-15     | ⭐⭐        |
| 🇲🇩 MD | 3-5       | ⭐         |

**Cel łączny B: \~70-110 firm.**

### Łączny target: \~190-310 firm

**Timeline realistyczny:**

- **Fala 1 (ten tydzień)**: PL A (40-60) + PL B (20-30) = 60-90

- **Fala 2 (następny tydzień)**: CZ A (20-30) + CZ B (10-15) = 30-45

- **Fala 3+**: pozostałe kraje, selektywnie

***

## 12. Struktura plików

```
/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/
├── methodology.md               # ten plik (kanoniczny)
├── INTEL.md                     # strategiczne odkrycia
├── DZIENNIK.md                  # postęp, pytania, feedback
├── RUNBOOK.md                   # per-country recipes + dokumenty finansowe
├── .env                         # sekrety (gitignored)
├── .env.example                 # template
├── .gitignore                   # `._*`, derived data, .verify-state
├── data/
│   ├── Polska/
│   │   ├── PL.md                # dziennik badawczy
│   │   ├── SŁOWNIK-{KOD}.md
│   │   ├── catalog-A-PL.csv
│   │   └── catalog-B-PL.csv
│   ├── Czechy/                  # j.w.
│   ├── Bułgaria/
│   ├── Estonia/
│   ├── Francja/
│   ├── Chorwacja/
│   ├── Litwa/
│   ├── Łotwa/
│   ├── Mołdawia/
│   ├── Rumunia/
│   ├── Słowacja/
│   ├── Słowenia/
│   ├── audit-log.md
│   └── verification/            # raporty weryfikacji
├── skills/
│   └── verify-data/             # skill weryfikacji FROZEN/DO-WERYFIKACJI
├── tools/
│   ├── verify_api.py            # live API verification (KRS, CEIDG, ARES, VIES) + --retrofix FABRYKAT — single source of truth
│   ├── verify_run.py            # hash diffing + snapshotting + audit log + regenerate_master() (delegates verification to verify_api)
│   ├── krs_search.py            # PL KRS lookup chain (NIP/REGON → KRS)
│   ├── vies_verify.py           # EU VIES VAT validation
│   ├── (verify_lead.py removed 2026-09-03 — stub, 2/3 tools returned PENDING)
│   ├── (l0_preflight.py removed 2026-09-03 — FABRYKAT logic folded into verify_api --retrofix)
│   ├── (kimi_client.py removed 2026-09-03 — no callers in repo)
│   ├── (gen_icons.py removed 2026-09-03 — one-shot PNG generator, no callers)
│   ├── (migrate_files.py removed 2026-09-03 — one-shot legacy migration, already done)
│   ├── fix_data_quality.py      # clean NIP/KRS, fill regions
│   ├── scrapers_registry.py     # web scrapers for non-API countries (SK/RO/LT/FR/EE/SI/HR)
│   ├── orchestrate_11_levels.py # master orchestrator for 11 lead-gen methods
│   ├── test_11_levels.py        # tests for orchestrator
│   ├── extract_intel.py         # automatic walkthrough & insight extraction
│   ├── VERIFICATION-PATTERN.md  # 2-tool protocol documentation
│   └── run_verify_cron.sh
├── frontend/                    # Vite + React (App.jsx, App.css, src/)
└── design/                      # design files
```

***

## 13. 3 słabe punkty metodologii

### 1. Progi wolumenowe kalibrowane na rynek ogólny, nie niszowy

Nabijarki to nie pasta do zębów. Nawet "duży" gracz w PL to 200-500 szt/m. Progi 50/500/5000 są przeskalowane.

**Naprawa:** benchmark — poprosić użytkownika o 2-3 znanych dystrybutorów i wstecznie oszacować ich wolumen. Dodana jest też skala `rynek_skala` (duży/średni/mały per kraj) z automatyczną kalibracją progów.

### 2. Atrybucja marek w Katalogu A jest nieweryfikowalna

Sklep może deklarować PowerMatic, ale sprzedawać go symbolicznie lub importować 5 sztuk prywatnie. Nie mam sposobu na potwierdzenie **realnej** relacji z marką.

**Ryzyko:** przeszacowuję kanał PowerMatic, niedoszacowuję szarą strefę.

**Naprawa:** podejście "domyślnie niezweryfikowane" — flaga `🔍` w kolumnie flagi. Flagi weryfikacji (📋 ORG-CEL, 🧾 FV-PDF, 📦 OPAKOWANIE, 🗣️ DEKLARACJA, 📜 KONTRAKT) wstawiam **tylko** z twardymi dowodami. NIE stosuję ✅ POTWIERDZONE bo nie mam dostępu do listy umów BILLS. Uczciwe — lepiej powiedzieć "nie wiem" niż udawać pewność.

### 3. Powinowactwo w Katalogu B to moja hipoteza, nie dane

Mówię "CBD/susz = 4" bo logicznie tak wygląda. Ale nie mam danych.

**Naprawa:** po zebraniu \~20-30 rekordów B, retrospektywna walidacja — sprawdzić czy firmy z B1-B3 faktycznie mają/mogą mieć nabijarki. To skalibruje skalę 1-5. Bez tego to educated guess.

***

## 14. Dane pomocnicze od użytkownika

Żeby poprawić jakość researchu, mogę wykorzystać:

- **Token CEIDG** (dostęp do API) — szybkie przeszukiwanie po PKD

- **Wynik zapytania CEIDG po PKD 46.35Z / 47.11Z** — lista firm tytoniowych z adresami i NIP-ami

- **Listę 2-3 znanych dystrybutorów** — do kalibracji progów wolumenowych

- **Listę 5-10 sklepów które pytały o nabijarki / kupiły cross-sell** — do kalibracji powinowactwa B

- **Dane z KAS** (jeśli są) — twarde info o importach prywatnych

- **Dostęp do panelu hurtowego BILLS** (<hurt@bills.pl>) — lista obecnych klientów hurtowych (nawet bez kwot, tylko NIP + nazwa) — benchmark tier

- **Dokumenty PDF faktur/CMR** (zanonimizowane) — analiza łańcuchów dostaw

- **Zdjęcia opakowań z numerami seryjnymi** — mapowanie kanałów

- **Notatki z targów / wizyt u klientów** — bezcenny "off-internet" kontekst

***

## 15. Checklist przed pierwszym dostarczeniem

- [x] Methodology zaktualizowana

- [x] 12 country journals utworzonych

- [x] 3 słabe punkty udokumentowane

- [x] Unified CSV schema zdefiniowany (35 kolumn)

- [x] Cele ilościowe per kraj ustalone

- [x] 24 stub CSV (12 × 2) utworzone

- [x] Podejście do weryfikacji relacji z marką zmienione (domyślnie 🔍)

- [x] KRS automation chain zbudowany (`tools/krs_search.py`)

- [x] Skill weryfikacji `skills/verify-data/SKILL.md`

- [x] Słowniki wyszukiwania per kraj (11) z wolumenami `szac.`

- [x] Lista dokumentów finansowych per kraj w RUNBOOK.md

- [ ] User zatwierdza schemat

- [ ] User daje scope (głęboki PL vs szerokie miotły) — **CONFIRMED: głęboki PL**

- [ ] User dostarcza token CEIDG — **CONFIRMED**

- [ ] User weryfikuje prognozowane progi wolumenowe (benchmark na 2-3 znanych firmach)

- [ ] User zatwierdza powinowactwo w Katalogu B

- [ ] User dostarcza dane pomocnicze (patrz sekcja 14)

