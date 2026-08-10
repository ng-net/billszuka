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

### KATALOG B — Branża tytoniowa, BEZ nabijarek (cross-sell pool)

| Kod | Specjalizacja | Dlaczego cross-sell ma sens |
|---|---|---|
| B1 | Tytoń liście / tytoń do skręcania | Klient już kupuje surowiec — nabijarka to naturalne uzupełnienie |
| B2 | Bibułki papierosowe | Top-of-mind dla palaczy, łatwy upsell |
| B3 | Filtry / gilzy | Jak B2 — klient już jest w kategorii |
| B4 | Akcesoria (zapalniczki, popielniczki, fajki) | Sklepy tytoniowe często mają mix |
| B5 | Shisha / hookah | Inny segment, ale wspólne sklepy i hurtownie |
| B6 | E-papierosy / vape | Częściowo nakłada się z tradycyjnym |
| B7 | Saszetki nikotynowe (snus / pouches) | Rosnący segment, te same kanały |
| B8 | Pełne hurtownie tytoniowe | Najwyższy priorytet cross-sell |
| B9 | CBD / konopie / susz | Overlap mocny — te same sklepy, ten sam profil klienta |

Pola analogiczne, plus: potencjał cross-sell i decydent.

---

### METODY POZYSKIWANIA

**Tier 1 — Bazy i rejestry (zautomatyzowane)**
- Polska: CEIDG, KRS, GUS, VIES
- Europa: Europages, Kompass, ThomasNet, Dun & Bradstreet
- Marketplace: Allegro API, Amazon Seller Central, eBay profiles
- Google Maps API: "nabijarki" / "tytoń" w promieniu

**Tier 2 — Kanały branżowe (pół-automatyczne)**
- Targi: Intertabac (Dortmund), World Tobacco, Vapexpo, Tobacco Plus Expo USA
- Czasopisma: Tobacco Asia, Tobacco Reporter, TobMag
- Stowarzyszenia: FEDIOL, IMAT
- LinkedIn Sales Navigator: frazy branżowe

**Tier 3 — Social + "szara strefa" (ręczne, kluczowe)**
- FB grupy: "Nabijarki do tytoniu", "Tytoń do skręcania", "PowerMatic club"
- YouTube recenzje, TikTok / Instagram Reels
- OLX / Allegro: profil sprzedawcy + opinie
- Google Maps recenzje: sklepy 4.8+ to ci co dobrze sprzedają

**Tier 4 — Fizyczny rekonesans**
- Wizyty w sklepach, rozmowy na targach
- Reverse engineering opakowań — NIP, EU VAT, numer seryjny PowerMatic → identyfikacja kanału

---

### KOLEJNOŚĆ GEOGRAFICZNA

1. 🇵🇱 Polska — fundament, masz najwięcej danych
2. 🇨🇿 Czechy — blisko, szybki ROI
3. 🇩🇪 Niemcy — największy rynek EU, twardy
4. 🇸🇰 Słowacja — mały, łatwy
5. 🇬🇧 UK — duży, własne reguły
6. 🇫🇷 🇮🇹 🇪🇸 🇳🇱 — kolejna fala
7. 🇸🇪 🇩🇰 🇳🇴 — Skandynawia
8. 🇷🇴 🇧🇬 🇭🇷 — Bałkany
9. 🇺🇦 dalej na wschód — ostrożnie

---

### PYTANIE OPERACYJNE (oczekuje odpowiedzi)

1. **Output format:** CSV/Excel / Notion / markdown? Dla ~50+ firm polecam Excel/Google Sheets z kolumnami zgodnymi z powyższym schematem.
2. **Zakres pierwszego dostarczenia:** głęboki research PL (50+ firm, wszystkie kanały) → Czechy? Czy szeroka miotła po kilka firm z każdego kraju?

---

### TIER — definicje

| Tier | Co to znaczy | Jak rozpoznać | Typowa skala PL |
|---|---|---|---|
| **Exclusive** | Wyłączność na kraj/region, umowa z producentem | "Jedyny autoryzowany dystrybutor na..." w opisie. Numery plombowe. Faktury bezpośrednio od producenta | 1-2 per kraj |
| **Authorized** | Partner z umową, bez wyłączności | "Autoryzowany sprzedawca", karta gwarancyjna | 5-15 per kraj |
| **Reseller** | Kupuje hurtowo, miesza marki, brak umowy | Brak oznaczenia "oficjalny", własna polityka cenowa | 30-100 per kraj |
| **Retailer** | Sklep detaliczny, wąska marża | Asortyment 5-50 maszynek, brak logistyki hurtowej | Setki per kraj |
| **Marketplace** | Allegro/Amazon/eBay, często dropshipping | Konto Allegro >5k opinii, brak magazynu | Tysiące per kraj |

*Marketplace seller z 10k sprzedanych rocznie = de facto reseller. Granica płynna.*

---

### WOLUMEN — heurystyki estymacji

**Sygnały mocne:**
- Opinie Allegro/Amazon → opinie × ~20 = przybliżona sprzedaż roczna
- Pracownicy z KRS/CEIDG: 1-2 = mały, 5-20 = średni, 50+ = duży
- Powierzchnia magazynu (Google Maps)
- Ceny: 25-35% poniżej katalogu = hurt (duży), +5% = detal (mały)
- Własna marka → prawie zawsze duży wolumen

**Progi (tymczasowe):**

| Kategoria | Miesięcznie | Rocznie |
|---|---|---|
| Mały | <50 szt | <600 szt |
| Średni | 50-500 szt | 600-6000 szt |
| Duży | 500+ szt | 6000+ szt |

⚠️ **Uwaga:** rynek nabijarek to nisza — "duży" w PL to realnie 200-500szt/m. Progi do kalibracji.

---

### KATALOG A — CZY SĄ TAM KONKURENCI?

Tak. I powinni tam być. A5 (OEM z Chin, np. Luxfux, Topomat, GM, Turbomatic) = bezpośrednia konkurencja cenowa. Dlaczego ich trzymam:
- Wiedzieć z kim walczysz
- Śledzić ruchy konkurencji (Turbomatic wchodzi do Czech → możesz reagować)
- Kandydaci M&A
- Benchmark cenowy

Wizualnie oznaczam: 🔴 konkurent bezpośredni / 🟡 konkurent pośredni / 🟢 partner potencjalny.

---

## 2026-08-09

**Słabe punkty — 3 punkty w 1 zdaniu każdy**

🔴 **Słabe punkt 1: Progi wolumenowe przeskalowane**
Nabijarki to nisza. Twoje "duży" to może być 200-500szt/m, nie 500+. Progi 50/500/5000 są z rynku ogólnego (pasta, elektronika).
*Naprawa: potrzebuję benchmarku — daj mi 2-3 znanych dystrybutorów (nazwy lub NIPy), a ja wstecznie oszacuję ich wolumen i przeskaluję progi. Bez tego wszystko w PL wychodzi "mały".*

🔴 **Słabe punkt 2: Atrybucja marek w A nieweryfikowalna**
Sklep może deklarować PowerMatic, ale realnie mieć 5 sztuk prywatnego importu. Nie wiem kto faktycznie ma umowę z BILLS, a kto w szarej strefie.
*Naprawa: dodałem flagę 🔍 DO-WERYFIKACJI vs ✅ POTWIERDZONE. Potrzebuję od Ciebie listy "kto ma umowę" — wtedy oznaczam ich jako pewnych, a resztę filtruję.*

🔴 **Słabe punkt 3: Powinowactwo w B to hipoteza**
Mówię "CBD = 4" bo logicznie tak wygląda. Ale nie mam danych. Po zebraniu ~30 rekordów B zrobię retrospektywną walidację — sprawdzę czy te firmy faktycznie mają/mogą mieć nabijarki w ofercie.

---

## 2026-08-10

**08:05 CEST**
🚨 **KRYTYCZNE ODKRYCIE:** KRS 0000523412 z listy to nie Don Marco — to **ARCHMO MOLDZYŃSKI PRACOWNIA PROJEKTOWA** (firma architektoniczna w Warszawie). Twój KRS jest całkowicie błędny.

---

## Struktura katalogów — pełna specyfikacja

### KATALOG A — Firmy z nabijarkami w ofercie

Podział wg relacji z marką (najważniejsza oś, bo od razu mówi, czy to konkurent, partner czy szara strefa):

| Kod | Kategoria | Co to znaczy dla Ciebie |
|---|---|---|
| A1 | Tylko PowerMatic | Twoi sub-dystrybutorzy / autoryzowani resellerzy |
| A2 | Tylko Hawk | Potencjalny kanał dla Hawk (Twoja marka?) |
| A3 | PowerMatic + Hawk | Najcenniejsi — sprawdzeni w branży, znają produkt |
| A4 | Multi-brand z PM/Hawk | Resellerzy wielu marek (Topomat, GM, Turbomatic...) |
| A5 | Własna marka / OEM z Chin | Konkurencja cenowa — prywatne marki importerów |
| A6 | Multi-brand bez PM/Hawk | Kandydaci do pozyskania — znają kanał, nie mają jeszcze Twojej marki |

**Pola w rekordzie (każda firma):**
- Kraj / miasto
- Tier: exclusive / authorized / reseller / retailer / marketplace seller
- Sourcing: import z Chin / import z Europy / producent PL
- Wolumen (estymacja: mały <50szt/m, średni 50-500, duży 500+)
- Kanał: B2B only / sklep stacjonarny / marketplace / własny e-commerce
- Kontakt: email / tel / LinkedIn / FB page
- WWW: tak/nie — jeśli nie, to co mają zamiast (FB, OLX, Allegro shop, wizytówka Google)
- Notatki

---

### KATALOG B — Branża tytoniowa, BEZ nabijarek (cross-sell pool)

Podział wg specjalizacji, bo każda kategoria ma inną logikę sprzedaży:

| Kod | Specjalizacja | Dlaczego cross-sell ma sens |
|---|---|---|
| B1 | Tytoń liście / tytoń do skręcania | Klient już kupuje surowiec — nabijarka to naturalne uzupełnienie |
| B2 | Bibułki papierosowe | Top-of-mind dla palaczy, łatwy upsell |
| B3 | Filtry / gilzy | Jak B2 — klient już jest w kategorii |
| B4 | Akcesoria (zapalniczki, popielniczki, fajki) | Sklepy tytoniowe często mają mix |
| B5 | Shisha / hookah | Inny segment, ale wspólne sklepy i hurtownie |
| B6 | E-papierosy / vape | Częściowo nakłada się z tradycyjnym (te same sklepy convenience) |
| B7 | Saszetki nikotynowe (snus / pouches) | Rosnący segment, te same kanały |
| B8 | Pełne hurtownie tytoniowe | Najwyższy priorytet cross-sell — mają wszystko poza nabijarkami |
| B9 | CBD / konopie / susz | Overlap mocny — te same sklepy, ten sam profil klienta |

Pola analogicznie, plus dodatkowo: potencjał cross-sell (wysoki/średni/niski) i decydent do kontaktu.

---

### METODY POZYSKIWANIA — szczególnie firm BEZ stron WWW

Trzy poziomy, od najtańszego do najdroższego:

**Tier 1 — Bazy i rejestry (zautomatyzowane)**
- Polska: CEIDG (jednoosobowe), KRS (spółki), GUS, VIES (walidacja VAT-EU)
- Europa: Europages, Kompass, ThomasNet, Dun & Bradstreet, Bloomberg
- Marketplace seller DB: Allegro API (masz listę sprzedawców po nazwie), Amazon Seller Central scraping, eBay seller profiles
- Google Maps API: wyszukiwanie po frazie "nabijarki" / "tytoń" w określonym promieniu

**Tier 2 — Kanały branżowe (pół-automatyczne)**
- Targi: Intertabac (Dortmund), World Tobacco, Vapexpo, Tobacco Plus Expo USA — listy wystawców to kopalnia
- Czasopisma: Tobacco Asia, Tobacco Reporter, TobMag — reklamy i artykuły ujawniają dystrybutorów
- Stowarzyszenia: FEDIOL, IMAT, Polskie Zrzeszenie Plantatorów Tytoniu (jeśli istnieje coś analogicznego dla dystrybutorów)
- LinkedIn Sales Navigator: frazy "nabijarki", "tobacco accessories", "rolling machine"

**Tier 3 — Social + "szara strefa" (ręczne, ale kluczowe)**
- Facebook grupy: "Nabijarki do tytoniu", "Tytoń do skręcania", "PowerMatic club" — tu jest prawdziwa masa małych firm, które nie mają WWW
- YouTube recenzje: każdy recenzent podaje skąd kupił
- TikTok / Instagram Reels: nowy kanał, dużo młodych sprzedawców
- OLX / Allegro: profil sprzedawcy + opinie = dane firmy
- Google Maps recenzje: sklepy tytoniowe 4.8+ to zwykle te, które dobrze sprzedają

**Tier 4 — Fizyczny rekonesans (drogi, ale nie do zastąpienia)**
- Wizyty w sklepach tytoniowych — pytanie "od kogo bierzecie maszynki"
- Targi — rozmowy z wystawcami
- Reverse engineering opakowań — numer NIP, EU VAT, numer seryjny (PowerMatic ma plombę z numerem → identyfikujesz kanał)

---

### KOLEJNOŚĆ GEOGRAFICZNA

1. 🇵🇱 Polska — fundament, masz najwięcej danych
2. 🇨🇿 Czechy — blisko, podobna kultura zakupowa, szybki ROI
3. 🇩🇪 Niemcy — największy rynek EU, ale twardy (Habufa, Powermatic.de?)
4. 🇸🇰 Słowacja — mały rynek, ale łatwy
5. 🇬🇧 UK — duży po brexicie, własne reguły
6. 🇫🇷 🇮🇹 🇪🇸 🇳🇱 — kolejna fala
7. 🇸🇪 🇩🇰 🇳🇴 — Skandynawia
8. 🇷🇴 🇧🇬 🇭🇷 — Bałkany
9. 🇺🇦 i dalej na wschód — ostrożnie (regulacje)

