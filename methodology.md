# BILLSzuka — Methodology Reference

B2B research on PowerMatic / Hawk rolling machines market. Dla: BILLS Sp. z o.o. (Ostrzeszów) — exclusive PM distributor PL + CEE.

---

## ZASADA DOKUMENTACJI — GDZIE CO ZAPISYWAĆ

Po każdym researchu / scrape / search: jeśli znalazłem coś wartego zapisania → zapisuję od razu, zanim przejdę dalej.

| Plik | Co tam trafia |
|---|---|
| **INTEL.md** | Strategiczne odkrycia — partnerzy 🐋, błędy w danych (zły KRS!), zmiany priorytetów, ryzykowni konkurenci, newsy z rynku |
| **DZIENNIK.md** | Postęp prac, struktura projektu, metodologia, pytania do klienta, feedback |

**Prosta reguła:**
- Intel → coś, co zmienia strategię lub jest kluczową wiedzą na przyszłość
- Dziennik → reszta (praca, struktura, pytania, feedback)

Jeśli nie wiesz gdzie coś wrzucić → dziennik.

---

## KATALOG A — Firmy z nabijarkami w ofercie

### Oś główna: relacja z marką

| Kod | Kategoria | Znaczenie dla BILLS |
|---|---|---|
| A1 | Tylko PowerMatic | Sub-dystrybutorzy / autoryzowani resellerzy BILLS |
| A2 | Tylko Hawk | Potencjalny kanał dla Hawk (osobna marka do zbudowania) |
| A3 | PowerMatic + Hawk | Najcenniejsi — sprawdzeni w branży, znają oba produkty |
| A4 | Multi-brand z PM/Hawk | Resellerzy wielu marek (Topomat, GM, Turbomatic + PM/Hawk) |
| A5 | Własna marka / OEM z Chin | **Konkurencja cenowa** — prywatne marki importerów |
| A6 | Multi-brand bez PM/Hawk | Kandydaci do pozyskania — znają kanał, nie mają jeszcze naszych marek |

**A5 zostaje w katalogu** (nie usuwam konkurencji). W kalkulacjach oznaczam flagą.

### Oś uzupełniająca: typ relacji konkurencyjnej

| Flaga | Typ | Przykład |
|---|---|---|
| 🔴 **KONK-BEZPOŚREDNI** | Sprzedaje dokładnie ten sam produkt (klon 1:1 z Chin) | Topomat, Turbomatic, GM, Luxfux (część asortymentu) |
| 🟡 **KONK-POŚREDNI** | Nabijarki, ale w innej półce cenowej / innym mechanizmie | Ręczne injektory, tanie injektory no-name |
| 🟢 **PARTNER** | Nie jest konkurentem, może być kanałem | Sklep tytoniowy, hurtownia wielobranżowa |
| 🐋 **BIG FISH** | Najgrubsza ryba w danym kraju — wymaga osobnej strategii | Sieci sklepów, hurtownie ogólnokrajowe |
| 💎 **GEM** | Firma, którą trudno znaleźć w internecie — znaleziona innym kanałem (targi, FB grupa, OLX, papierosy papierowe, opakowanie z numerem seryjnym) | Jednoosobowe działalności, małe sklepy bez WWW |
| ✅ **BILLS-LIKE** | Profil firmy podobny do BILLS (import + dystrybucja + serwis) | Kandydat do benchmarku lub partnerstwa |

### Relacja z marką — podejście do weryfikacji

**Nie dostaję listy firm w umowach z BILLS.** To znaczy, że dla większości rekordów **nie jestem w stanie zweryfikować czy firma faktycznie ma kanał autoryzowany, czy importuje prywatnie z innego źródła (szara strefa).**

Domyślnie traktuję to jako **niezweryfikowane** — flaga `🔍` w kolumnie `flagi`. To nie jest "wpis niepewny" — to **uczciwe przyznanie, że nie wiem**.

**Flagi weryfikacji (tylko gdy znalazłem pośrednie dowody):**

| Flaga | Znaczenie | Skąd to wiem |
|---|---|---|
| 📋 ORG-CEL | Pojawiło się w dokumentach organów celnych (KAS, analogi zagraniczne) | Jawne rejestry, publikacje, wyroki, kontrole |
| 🧾 FV-PDF | Faktura/CMR/Packing list w PDF znaleziona publicznie | FB grupy, Allegro opinie, case studies, posty |
| 📦 OPAKOWANIE | Numer seryjny / plomba na opakowaniu wskazuje na konkretny kanał | Zdjęcia produktu, recenzje, reklamacje |
| 🗣️ DEKLARACJA | Firma sama publicznie deklaruje że jest autoryzowana | Strona www, LinkedIn, komunikat prasowy |
| 📜 KONTRAKT | Zewnętrzna informacja o umowie dystrybucyjnej | Wywiad, case study, raport branżowy |

**Brak flagi = domyślnie niezweryfikowane** (nie wpisuję nic, flaga `🔍` jest też OK gdy chcę podkreślić).

**Kiedy to ma znaczenie:**
- Gdy buduję listę "kto faktycznie ma dostęp do PM/Hawk przez BILLS" → filtry tylko flagi weryfikacji
- Gdy buduję listę "kto handluje podobnym asortymentem" → bez filtra, bo marka nie ma znaczenia
- Gdy konkurent — marka nie ma znaczenia, liczy się profil firmy

**Jak szukać dowodów:**
- **Organy celne**: KAS publikuje dane o kontrolach, wyroki WSA. Mało publiczne, ale tam gdzie są — twarde dane
- **PDF-y faktów**: firmy z BG/CEE często wrzucają faktury na FB (case study, reklamacja), tam widać cały łańcuch
- **Numery seryjne PM**: każda maszyna ma plombę z numerem — w zdjęciach/opiniach widać. Można zmapować na "dystrybuowane przez..."
- **LinkedIn**: w opisach stanowisk ludzie piszą "exclusive distributor of..." — twarde dane

### Flagi podsumowanie (finalna lista)

| Flaga | Znaczenie |
|---|---|
| 🔴 | Konkurent bezpośredni |
| 🟡 | Konkurent pośredni |
| 🟢 | Partner potencjalny |
| 🐋 | Big fish |
| 💎 | Gem (off-internet) |
| ✅ | BILLS-like profil (import+dystrybucja+serwis) |
| 🔍 | Niezweryfikowana relacja z marką (default) |
| 📋 ORG-CEL | Zweryfikowane przez organy celne |
| 🧾 FV-PDF | Zweryfikowane przez fakturę PDF |
| 📦 OPAKOWANIE | Zweryfikowane przez numer seryjny |
| 🗣️ DEKLARACJA | Zweryfikowane przez deklarację firmy |
| 📜 KONTRAKT | Zweryfikowane przez zewnętrzne info o umowie |

Przykład kombinacji: `🟢📦` (partner + zweryfikowany numerem seryjnym), `🔴🔍` (konkurent + relacja nieznana)

---

## KATALOG B — Branża tytoniowa BEZ nabijarek (cross-sell pool)

### Powinowactwo z nabijarkami (nowa oś!)

Skala **1-5**, gdzie 5 = klient niemal na pewno kupi nabijarkę przy okazji, 1 = marginalny overlap.

| Kod | Specjalizacja | Powinowactwo | Uzasadnienie |
|---|---|---|---|
| B1 | Tytoń liście / tytoń do skręcania | **5** | Klient już kupuje surowiec — nabijarka to naturalny upsell |
| B2 | Bibułki papierosowe | **5** | Top-of-mind dla palaczy skręcających, łatwy cross-sell |
| B3 | Filtry / gilzy | **5** | j.w. — klient już jest w kategorii |
| B4 | Akcesoria (zapalniczki, popielniczki, fajki, cygarniczki) | **3** | Te same sklepy, ale klient fajczarski to inna demografia |
| B5 | Shisha / hookah | **2** | Inny segment, ale **shared retail channel** (sklepy tytoniowe) — overlap handlowy, nie kliencki |
| B6 | E-papierosy / vape | **2** | Inna technologia, ale shared retail channel. Uwaga: regulacje coraz bardziej rozbieżne |
| B7 | Saszetki nikotynowe (snus / pouches) | **2** | Rosnący segment, shared channel. Klient raczej nie skręca |
| B8 | Pełne hurtownie tytoniowe | **5** | **Najwyższy priorytet** — mają wszystko poza nabijarkami, znają klienta |
| B9 | CBD / konopie / susz | **4** | **Wysoki overlap kliencki** — susz = joint = potrzebuje akcesoriów. W wielu krajach ten sam profil sklepu. Specyficzne regulacje! |

**Kryterium: overlap kliencki, nie kanałowy.** CBD/susz ma overlap kliencki (ktoś kto kupuje susz, skręca jointy), ale overlap kanałowy jest mniejszy (specjalistyczne sklepy CBD).

**Wyjątek B5 (shisha) i B6 (vape) — shared channel mocny, ale klienci się nie pokrywają.** Traktuję to osobno.

---

## TIER (definicje — krótkie, do tooltipa)

| Tier | Co to | Jak rozpoznać |
|---|---|---|
| **Exclusive** | Wyłączność na kraj/region, umowa z producentem/głównym dystrybutorem | "Jedyny autoryzowany dystrybutor na...", faktury bezpośrednio, plombowe numery |
| **Authorized** | Wybrany partner z umową, bez wyłączności terytorialnej, wsparcie serwisowe | "Autoryzowany sprzedawca", karta gwarancyjna w ich nazwie |
| **Reseller** | Hurtowo kupuje od dystrybutora lub sam importuje, bez umowy, miesza marki | Brak oznaczenia "oficjalny", własna polityka cenowa |
| **Retailer** | Sklep detaliczny (online lub stacjonarny), wąska marża, asortyment 5-50 sztuk | Brak logistyki hurtowej |
| **Marketplace** | Allegro/Amazon/eBay/OLX, często dropshipping lub jednoosobowa skala | Konto z >5k opinii, brak magazynu |

Granica płynna. Marketplace z 10k maszyn/rok = de facto reseller.

---

## VOLUME (heurystyki)

### Sygnały (od najmocniejszych)
1. **Opinie Allegro/Amazon** — opinie × ~20 = przybliżona sprzedaż roczna
2. **Pracownicy (KRS/CEIDG)** — 1-2 = mały, 5-20 = średni, 50+ = duży
3. **Powierzchnia magazynu** (Google Maps, wizytówki)
4. **Asortyment** — wąski z dużą rotacją vs szeroki z wolną
5. **Ceny** — 25-35% poniżej katalogu = hurt, +5% = detal
6. **Certyfikaty dealerskie / obecność na targach** → zwykle wyższy tier
7. **Flota pojazdów** widoczna na wizytówce
8. **Własna marka** → prawie zawsze duży wolumen

### Progi

| Kategoria | Miesięcznie | Rocznie |
|---|---|---|
| Mały | <50 szt | <600 szt |
| Średni | 50-500 szt | 600-6000 szt |
| Duży | 500+ szt | 6000+ szt |

### Zastrzeżenie ważne ⚠️

Progi kalibrowane na rynek ogólny. **Rynek nabijarek to nisza** — nawet "duży" gracz w PL to ~200-500szt/m. **Próg 500+ to naprawdę największe hurtownie.** Patrz słabe punkty #1.

### Confidence indicator (dodane!)

Przy każdym wpisie wolumenu oznaczam pewność estymacji:
- 🟢 wysoka — mam twarde dane (opinie, faktury, deklaracje)
- 🟡 średnia — synekury pośrednie (pracownicy, asortyment, ceny)
- 🔴 niska — zgadywanie, brak sygnałów

---

## CEIDG i rejestry per kraj

### Polska
- **NIP** (10 cyfr) — tax ID
- **KRS** (Krajowy Rejestr Sądowy) — spółki
- **CEIDG** — jednoosobowe działalności. **API: https://dane.biznes.gov.pl/api/ceidg/v2** (wymaga tokena). Publiczna wersja: https://www.ceidg.gov.pl — wyszukiwarka bez tokena

#### CEIDG API — token i wzorzec skryptu

Token: **`CEIDG_API_TOKEN`** w pliku `.env` w tym samym folderze co skrypt (nie trzymać w commicie — jest w `.gitignore`).

**Standardowy wzorzec ładowania tokena (Python):**
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

**Public endpoint** (bez tokena, rate-limited): `https://dane.biznes.gov.pl/api/ceidg/v2/firmy?name=<nazwa>`
**Autoryzowany endpoint**: `https://dane.biznes.gov.pl/api/ceidg/v2/firmy?name=<nazwa>` z `Authorization: Bearer <TOKEN>` w nagłówku.
- **REGON** — statystyczny numer podmiotu
- **PKD** — kody działalności (46.35Z = hurt handlu wyrobami tytoniowymi, 46.17Z = pośrednictwo w handlu, 47.11Z = sklepy)

### Czechy 🇨🇿
- **IČO** (8 cyfr) — numer identyfikacyjny
- **DIČ** —税owy (CZ + IČO)
- **OR** (Obchodní rejstřík) — spółki, https://or.justice.cz
- **ŽR** (Živnostenský rejstřík) — jednoosobowe, https://www.rzp.cz/cgi-bin/aps_cacheWEB.sh
- **ARES** (Administrativní registr ekonomických subjektů) — baza ministerialna, https://ares.gov.cz

### Słowacja 🇸🇰
- **IČO**, **IČ DPH** (SK + IČO)
- **ORSR** (Obchodný register SR) — https://orsr.sk
- **ŽRSR** (Živnostenský register) — jednoosobowe, https://www.zrsr.sk
- **Finančná správa** — VAT/TPD

### Rumunia 🇷🇴
- **CUI** (Cod Unic de Înregistrare) / **CIF** — tax ID
- **ONRC** (Registrul Comerțului) — https://www.onrc.ro
- **ANAF** — tax office, https://www.anaf.ro
- Rejestr jednoosobowych: PFA w ONRC

### Litwa 🇱🇹
- **VMN** (kodas) / **PVM** (VAT, LT + 9 lub 12 cyfr)
- **JAR** (Juridinių asmenų registras) — https://rekvizitai.vz.lt, https://www.registrucentras.lt
- Jednoosobowe: MB (mažoji bendrija) też w JAR

### Łotwa 🇱🇻
- **PVN** (VAT, LV + 11 cyfr)
- **UR** (Uzņēmumu reģistrs) — https://info.ur.gov.lv
- **VID** — tax office

### Estonia 🇪🇪
- **KM** (VAT, EE + 9 cyfr)
- **e-Äriregister** (e-Business Register) — https://ariregister.rik.ee — **najlepszy w regionie, otwarty**
- **EMTA** — tax office

### Francja 🇫🇷
- **SIREN** (9 cyfr) / **SIRET** (14 cyfr z adresem) — firm ID
- **TVA intracommunautaire** (FR + 2 cyfry + SIREN)
- **RCS** (Registre du Commerce et des Sociétés) — spółki
- **INPI** — własność intelektualna, marki
- **Societe.com**, **Pappers.fr** — agregatory (lepsze niż oficjalne strony)
- **Douanes** — cło/akcyza tytoniowa

### Mołdawia 🇲🇩
- **IDNO** (13 cyfr) — firm ID
- **Camera Înregistrării de Stat** — rejestr, https://www.cis.gov.md
- **TVA** (MD + IDNO)
- **Serviciul Vamal** — cło

### Bułgaria 🇧🇬
- **EIK** (9 cyfr) / **DDS** (VAT, BG + EIK)
- **Търговски регистър** — https://portal.justice.bg
- **НАП** (НАционална агенция за приходите) — tax

### Słowenia 🇸🇮
- **ID za DDV** (VAT, SI + 8 cyfr)
- **AJPES** (Agencija za javnopravne evidence) — https://www.ajpes.si
- **FURS** — tax

### Chorwacja 🇭🇷
- **OIB** (11 cyfr) — osobisty/firmowy
- **Sudski registar** — https://sudreg.pravosudje.hr
- **Porezna uprava** — tax, https://www.porezna-uprava.hr

---

## MARKETPLACES per kraj

| Kraj | Główne | Drugorzędne | Notatki |
|---|---|---|---|
| 🇵🇱 PL | **Allegro** | OLX, Ceneo, Kaufland, **InPost Buy** (nowy), Erli | Allegro = must-have. InPost Buy rośnie szybko |
| 🇨🇿 CZ | **Heureka**, Zboží.cz, Aukro | Bazoš, Alza | Heureka = porównywarki, Aukro = aukcje |
| 🇸🇰 SK | **Heureka.sk**, Bazoš | Mall.sk, Alza | Mały rynek, ale Heureka daje dobre dane o cenach |
| 🇷🇴 RO | **eMAG**, OLX | Okazii, Cel.ro | eMAG = Amazon regionu, OLX = główne ogłoszenia |
| 🇱🇹 LT | **Skelbiu.lt** | Vinted, Aruodas | Skelbiu = główne ogłoszenia |
| 🇱🇻 LV | **SS.lv** | Vinted | Rynek mały, SS.lv dominuje |
| 🇪🇪 EE | **Osta.ee** | Vinted | Estonka scena bardzo cyfrowa |
| 🇫🇷 FR | **Leboncoin** (gigant!), Rakuten, Cdiscount | Vinted, Amazon.fr | Leboncoin = must-have, format ogłoszeń |
| 🇲🇩 MD | **999.md**, OLX | — | Mały rynek, 999.md to lokalny portal |
| 🇧🇬 BG | **OLX**, Bazar.bg | — | OLX dominuje, Bazar.bg dla produktów |
| 🇸🇮 SI | **Bolha.com** (wiodący), Mimovrste, Ceneje | — | Bolha = OLX Slovenii, Mimovrste = porównywarki |
| 🇭🇷 HR | **Njuškalo** (gigant!), Index Oglasi | — | Njuškalo = must-have |

---

## REGULACJE — per kraj (stan wiedzy: 2024-2025, do weryfikacji)

| Kraj | Reżim tytoniowy | E-papierosy | CBD/susz | Nabijarki | Uwagi |
|---|---|---|---|---|---|
| 🇵🇱 PL | Akcyza, zakaz reklamy, ograniczenia sprzedaży | Legalne, ograniczenia smakowe dyskutowane | Susz legalny z limitem THC, CBD w szarej strefie | Bez ograniczeń jako urządzenie | Sprawdzić akcyzę od 2025 |
| 🇨🇿 CZ | Akcyza, ograniczenia reklamy | Legalne, ograniczenia smakowe w drodze | CBD legalne, susz nielegalny | Bez ograniczeń | Otwarty rynek, łatwy start |
| 🇸🇰 SK | j.w. EU | Legalne, regulacje smakowe | CBD legalne, susz nielegalny | Bez ograniczeń | Mały rynek, mniejsza skala |
| 🇷🇴 RO | **Plain packaging od 2020** | Surowe ograniczenia smakowe, e-papierosy mocno regulowane | CBD w szarej strefi | Bez ograniczeń jako urządzenie | Trudny rynek, antynikotynowe lobby |
| 🇱🇹 LT | Akcyza EU | **Zakaz smakowych liquidów od 2023** | CBD legalne, susz nielegalny | Bez ograniczeń | Surowe podejście |
| 🇱🇻 LV | Akcyza EU | Legalne, ograniczenia | CBD legalne, susz nielegalny | Bez ograniczeń | Umiarkowane |
| 🇪🇪 EE | Akcyza EU | Legalne, smakowe dyskutowane | CBD legalne, susz nielegalny | Bez ograniczeń | Cyfrowo zaawansowany, mały rynek |
| 🇫🇷 FR | **Plain packaging od 2017** | Legalne, mocno ograniczone smakowe | CBD legalny, susz nielegalny | Bez ograniczeń | **Wysokie akcyzy, surowe podejście** |
| 🇲🇩 MD | Poza UE, własne reguły | Liberalne | Liberalne | Bez ograniczeń | Szansa na szary rynek |
| 🇧🇬 BG | Akcyza EU | Legalne, regulacje smakowe | CBD legalne, susz nielegalny | Bez ograniczeń | Rynek otwarty |
| 🇸🇮 SI | Akcyza EU | Legalne, ograniczenia smakowe | CBD legalne, susz nielegalny | Bez ograniczeń | Mały rynek |
| 🇭🇷 HR | Akcyza EU | Legalne, ograniczenia smakowe | CBD legalne, susz nielegalny | Bez ograniczeń | Rosnący rynek, wstęp do Bałkanów |

**Ryzyka regulacyjne:**
- **Wysokie**: 🇫🇷 FR, 🇷🇴 RO, 🇱🇹 LT (trudne rynki dla dystrybucji maszyn, ale też klienci szukający alternatyw)
- **Średnie**: 🇵🇱 PL, 🇱🇻 LV, 🇸🇰 SK (standardowe EU)
- **Niskie**: 🇨🇿 CZ, 🇧🇬 BG, 🇸🇮 SI, 🇭🇷 HR, 🇪🇪 EE (stosunkowo otwarte)
- **Specjalne**: 🇲🇩 MD (szara strefa, poza UE — uwaga na cło i akcyzę)

---

## KOLEJNOŚĆ GEOGRAFICZNA (zaktualizowana)

1. 🇵🇱 **Polska** — fundament
2. 🇨🇿 **Czechy** — blisko, podobna kultura
3. 🇸🇰 **Słowacja** — szybki
4. 🇭🇷 **Chorwacja** — wstęp do Bałkanów, rośnie
5. 🇧🇬 **Bułgaria** — otwarty
6. 🇸🇮 **Słowenia** — mały, ale łatwy
7. 🇷🇴 **Rumunia** — **wymaga strategii**, wysokie regulacje ale duży rynek
8. 🇪🇪 **Estonia** — cyfrowa, mała, ale ciekawa
9. 🇱🇻 **Łotwa** — mała
10. 🇱🇹 **Litwa** — surowa
11. 🇫🇷 **Francja** — **wymaga strategii**, najtrudniejsza
12. 🇲🇩 **Mołdawia** — specyficzna, poza EU

---

## DZIENNIK UWAG PER KRAJ

Będę prowadził plik `data/countries/{KOD}.md` dla każdego kraju z:
- Czego się dowiedziałem
- Źródła (CEIDG, KRS, targi, FB, OLX, etc.)
- Niespodzianki (np. "znalazłem 3 hurtownie w Pradze, których nie ma w Google")
- Czerwone flagi (np. "ta firma wygląda jak dystrybutor ale to jeden człowiek w mieszkaniu")
- Gemy 💎 (off-internet)
- Big fish 🐋

---

## 3 SŁABE PUNKTY METODOLOGII

### 1. Progi wolumenowe kalibrowane na rynek ogólny, nie niszowy

Nabijarki to nie pasta do zębów. Nawet **"duży" gracz w PL to 200-500 szt/m**. Moje progi 50/500/5000 są przeskalowane — przez to wszystko w PL wychodzi "mały". 

**Co zrobić:** dodać drugą skalę "rynek niszowy" (np. <20 / 20-100 / 100+ dla PL), trzymać obie. Albo: zrobić benchmark — poprosić Cię o 2-3 znanych dystrybutorów i wstecznie oszacować ich wolumen, żeby skalibrować.

### 2. Atrybucja marek w Katalogu A jest nieweryfikowalna

Sklep może deklarować PowerMatic, ale sprzedawać go symbolicznie. Albo importować 5 sztuk prywatnie. Nie mam sposobu na potwierdzenie **realnej** relacji z marką — mogę liczyć deklaracje, nie kontrakty. 

**Ryzyko:** przeszacowuję kanał PowerMatic, niedoszacowuję szarą strefę. Ktoś kto realnie jest dużym graczem PM, może u mnie wyglądać jak mały marketplace seller.

**Co zrobić:** Przyjąć podejście "domyślnie niezweryfikowane" — większość rekordów dostaje `🔍` lub nie ma flagi weryfikacyjnej. Flagi weryfikacyjne (📋 ORG-CEL, 🧾 FV-PDF, 📦 OPAKOWANIE, 🗣️ DEKLARACJA, 📜 KONTRAKT) wstawiam **tylko** gdy faktycznie znalazłem pośrednie dowody. NIE stosuję ✅ POTWIERDZONE bo nie mam dostępu do listy umów BILLS. To uczciwe — lepiej powiedzieć "nie wiem" niż udawać pewność.

### 3. Powinowactwo w Katalogu B to moja hipoteza, nie dane

Mówię "CBD/susz = 4" bo logicznie wygląda na wysoki overlap. Ale nie mam danych — być może w praktyce sklepy CBD w Czechach to zupełnie inny segment niż zakładam. Vape może mieć wyższy overlap kanałowy niż myślę.

**Co zrobić:** po zebraniu ~20-30 rekordów z B, zrobić **retrospektywną walidację** — sprawdzić czy faktycznie firmy z B1-B3 mają nabijarki w ofercie (albo w komentarzach, social media, zamówieniach). To skalibruje skalę 1-5. Bez tego to educated guess.

---

## STRUKTURA PLIKÓW

```
/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/
├── methodology.md          # ten plik
├── README.md               # legenda kolumn CSV, szybki start
├── data/
│   ├── catalog-A-pl.csv    # PL firmy z nabijarkami
│   ├── catalog-B-pl.csv    # PL firmy branżowe bez nabijarek
│   ├── catalog-A-cz.csv
│   ├── catalog-B-cz.csv
│   └── ...
├── data/countries/
│   ├── PL.md               # dziennik per kraj
│   ├── CZ.md
│   └── ...
└── assets/
    └── (opcjonalnie: wykresy, mapy)
```

---

## UNIFIKOWANY SCHEMAT CSV (A i B — te same kolumny)

Każdy plik `data/catalog-{A|B}-{KOD}.csv` ma **identyczny** zestaw kolumn. Pola specyficzne dla A lub B są puste w rekordach drugiego katalogu.

```
id_unikalne              # wewnętrzne ID, np. PL-A-001
kategoria                # A1-A6 lub B1-B9
nazwa_firmy
kraj
miasto
adres
nip_vat                  # NIP / IČO+DIČ / CUI / SIREN / IDNO / OIB itp.
rejestr_id               # KRS / IČO / ONRC / OIB itp.
www                      # pełny URL lub "brak"
kanal_zamiennik          # co mają zamiast WWW (FB page, OLX, Allegro shop, wizytówka Google)
email
telefon
linkedin
facebook
instagram
tier                     # exclusive / authorized / reseller / retailer / marketplace
marki_nabijarki          # A: PowerMatic, Hawk, Topomat, GM, Turbomatic, inne (lista)
marka_wlasna_oem         # A: tak/nie + nazwa marki własnej
sourcing                 # Chiny / Europa / Polska producent / mix
wolumen                  # mały / średni / duży
confidence_wolumen       # 🟢/🟡/🔴
kanal_sprzedaży          # B2B only / sklep stacjonarny / marketplace / własny e-commerce / mix
powinowactwo_nabijarki   # B: 1-5 (puste dla A)
cross_sell_potential     # B: wysoki/średni/niski (puste dla A)
decydent
stanowisko
email_decydent
zrodlo_danych            # CEIDG, KRS, Facebook grupa X, OLX, targi Y, recenzja Z, itp.
data_weryfikacji         # YYYY-MM-DD
flagi                    # 🔴/🟡/🟢/🐋/💎/✅/🔍 w kombinacji
notatki
```

**Konwencje wartości:**
- **kategoria**: A1, A2, A3, A4, A5, A6, B1, B2, B3, B4, B5, B6, B7, B8, B9
- **flagi**: wieloznakowe, np. `🔴💎` (konkurent+gem) lub `🟢📦` (partner+zweryfikowany numerem seryjnym)
- **wolumen + confidence**: np. `mały 🟡` lub `duży 🟢`
- **pola opcjonalne** (A-only / B-only) → puste w rekordach drugiego katalogu

---

## CELE ILOŚCIOWE (targets per kraj i katalog)

**Filozofia:** mniej rekordów z polami wypełnionymi > więcej rekordów z dziurami. Każdy rekord musi mieć: nazwę, kraj, miasto, kontakt (email LUB tel LUB link). Reszta progresywnie.

### Katalog A (firmy z nabijarkami)

| Kraj | Target A | Priorytet | Uwagi |
|---|---|---|---|
| 🇵🇱 PL | **40-60** | ⭐⭐⭐ | Fundament, najgłębszy research, pełne dane |
| 🇨🇿 CZ | **20-30** | ⭐⭐⭐ | Blisko, łatwy ROI, drugi pełny research |
| 🇸🇰 SK | 5-10 | ⭐ | Mały rynek, prawdopodobnie pokrycie z CZ |
| 🇭🇷 HR | 8-12 | ⭐ | Rosnący, dobra szansa |
| 🇧🇬 BG | 8-12 | ⭐ | Otwarty rynek |
| 🇸🇮 SI | 3-6 | ⭐ | Bardzo mały |
| 🇷🇴 RO | 10-15 | ⭐⭐ | Duży, trudne regulacje — wymaga selekcji |
| 🇪🇪 EE | 3-5 | ⭐ | Mały, zdigitalizowany |
| 🇱🇻 LV | 2-4 | ⭐ | Pokrycie z LT/EE |
| 🇱🇹 LT | 3-5 | ⭐ | Surowy rynek |
| 🇫🇷 FR | 15-25 | ⭐⭐ | Najtrudniejszy, ale największy potencjał |
| 🇲🇩 MD | 5-10 | ⭐ | Specyficzny, poza EU |

**Cel łączny Katalog A: ~120-200 firm** w pierwszej fali (PL + CZ szczegółowo, reszta selektywnie).

### Katalog B (branża tytoniowa bez nabijarek)

| Kraj | Target B | Priorytet | Uwagi |
|---|---|---|---|
| 🇵🇱 PL | **20-30** | ⭐⭐⭐ | Hurtownie tytoniowe, dilerzy, sklepy, CBD — pełne dane |
| 🇨🇿 CZ | 10-15 | ⭐⭐ | Drugi pełny research |
| 🇸🇰 SK | 3-6 | ⭐ | Pokrycie z CZ |
| 🇭🇷 HR | 5-8 | ⭐ | |
| 🇧🇬 BG | 5-8 | ⭐ | |
| 🇸🇮 SI | 2-4 | ⭐ | |
| 🇷🇴 RO | 8-12 | ⭐⭐ | Duży rynek hurtowy |
| 🇪🇪 EE | 2-3 | ⭐ | |
| 🇱🇻 LV | 2-3 | ⭐ | |
| 🇱🇹 LT | 2-4 | ⭐ | |
| 🇫🇷 FR | 10-15 | ⭐⭐ | CBD-legalny, duży rynek |
| 🇲🇩 MD | 3-5 | ⭐ | Specyficzny |

**Cel łączny Katalog B: ~70-110 firm**.

### Łączny target: ~190-310 firm

To dużo. Realistyczny timeline:
- **Fala 1 (ten tydzień)**: PL A (40-60) + PL B (20-30) = 60-90
- **Fala 2 (następny tydzień)**: CZ A (20-30) + CZ B (10-15) = 30-45
- **Fala 3+**: pozostałe kraje, selektywnie

---

## CHECKLIST PRZED PIERWSZYM DOSTARCZENIEM

- [x] Methodology zaktualizowana
- [x] 12 country journals utworzonych
- [x] 3 weak points udokumentowane
- [x] Unified CSV schema zdefiniowany
- [x] Cele ilościowe per kraj ustalone
- [x] 24 stub CSV (12 × 2) utworzone
- [x] Podejście do weryfikacji relacji z marką zmienione (domyślnie 🔍, flagi weryfikacji rzadko)
- [ ] User zatwierdza schemat
- [ ] User daje scope (głęboki PL vs szerokie miotły)
- [ ] User dostarcza token CEIDG lub potwierdza publiczną wersję
- [ ] User weryfikuje prognozowane progi wolumenowe (benchmark na 2-3 znanych firmach)
- [ ] User zatwierdza powinowactwo w Katalogu B
- [ ] User dostarcza dane pomocnicze (patrz sekcja poniżej)

---

## DANE POMOCNICZE KTÓRE USER MOŻE DOSTARCZYĆ

Żeby poprawić jakość researchu, mogę wykorzystać:

- **Token CEIDG** (dostęp do API) — szybkie przeszukiwanie po PKD
- **Wynik zapytania CEIDG po PKD 46.35Z / 47.11Z** — lista firm tytoniowych z adresami i NIP-ami
- **Listę 2-3 znanych dystrybutorów** — do kalibracji progów wolumenowych
- **Listę 5-10 sklepów które pytały o nabijarki / kupiły cross-sell** — do kalibracji powinowactwa B
- **Dane z KAS** (jeśli są) — twarde info o importach prywatnych
- **Dostęp do panelu hurtowego BILLS** (hurt@bills.pl) — lista obecnych klientów hurtowych (nawet bez kwot, tylko NIP + nazwa) — to daje benchmark tier
- **Dokumenty PDF faktur/CMR** (zanonimizowane) — do analizy łańcuchów dostaw
- **Zdjęcia opakowań z numerami seryjnymi** — do mapowania kanałów
- **Twoje notatki z targów / wizyt u klientów** — bezcenny "off-internet" kontekst
