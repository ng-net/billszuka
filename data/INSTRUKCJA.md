# BILLSzuka — Instrukcja dla Działu Sprzedaży

> **Dokument wewnętrzny.** Wersja 1.1 — 2026-08-19. Opisuje jak została zbudowana baza leadów B2B/B2C, jak ją czytać, jakich fraz użyto w researchu i co można z niej wyciągnąć. Źródła danych: `data/master.csv` (393 firm, 12 krajów) + `INTEL.md` + `DZIENNIK.md` + `methodology.md` + `data/{Kraj}/insight-{ISO}.md` + `data/{Kraj}/SŁOWNIK-{ISO}.md`.

---

## 📖 Spis treści

| Sekcja | Temat |
|---|---|
| 0 | **Strona tytułowa + Katalog 12 dokumentów PDF per kraj + statystyki** |
| 1 | Co to jest BILLSzuka |
| 2 | Skąd wzięły się te dane — 11 poziomów wyszukiwania |
| 3 | Podział firm na dwa katalogi (A1–A6, B1–B9) |
| 4 | Scoring — Tier, Wolumen, Flagi |
| 5 | Weryfikacja FROZEN + defense in depth |
| 6 | Potencjał rynkowy per kraj (12 krajów) |
| 7 | TOP firmy per kraj (20 Big Fish) |
| 8 | **Słownik fraz — „nabijarka do tytoniu" w 12 językach** |
| 9 | Co zadziałało / co nie zadziałało |
| 10 | Problemy ze źródłami danych |
| 11 | Rekomendowane API i płatne serwisy z cenami |
| 12 | Jak korzystać z bazy (3 kroki dla handlowca) |
| 13 | Status projektu i plan Q3–Q4 2026 |

---

## 0. Strona tytułowa + Katalog 12 dokumentów PDF

> **Dlaczego ta sekcja:** Dla każdego z 12 krajów wygenerowaliśmy osobny katalog PDF (A4, layout v9). Poniżej pełen wykaz ze statystykami: ile stron, ile leadów w każdej kategorii A1–A6 i B1–B9. Wydrukuj i rozdaj handlowcom per kraj.

### 0.1 12 katalogów per kraj — szybki przegląd

| # | Kraj | PDF | Stron | Σ firm | Katalog A (maszynki) | Katalog B (branża) | TOP partner |
|--:|---|---|--:|--:|---|---|---|---|
| 1 | 🇵🇱 Polska | `data/Polska/PDF-PL.pdf` | **22** | 157 | 31 firm (A1:1, A2:3, A4:26, A5:1) | 126 (B1:6, B4:37, B6:14, B8:67, B9:2) | PHUP GNIEZNO, POLSKI TYTOŃ |
| 2 | 🇨🇿 Czechy | `data/Czechy/PDF-CZ.pdf` | **7** | 18 | 9 (A1:7, A4:2) | 9 (B4:3, B8:6) | PEAL a.s., GGT CZ |
| 3 | 🇸🇰 Słowacja | `data/Słowacja/PDF-SK.pdf` | **9** | 30 | 15 (A1:4, A2:11) | 15 (B4:1, B6:2, B8:9, B9:3) | GGT a.s. (GGTabak) |
| 4 | 🇷🇴 Rumunia | `data/Rumunia/PDF-RO.pdf` | **8** | 23 | 8 (A1:5, A2:3) | 15 (B4:7, B8:5, B9:3) | SC Golden Tip, Interbrands |
| 5 | 🇧🇬 Bułgaria | `data/Bułgaria/PDF-BG.pdf` | **11** | 34 | 7 (A1:6, A2:1) | 27 (B4:2, B8:19, B9:6) | M Tobacco (Płowdiw) |
| 6 | 🇭🇷 Chorwacja | `data/Chorwacja/PDF-HR.pdf` | **7** | 19 | 8 (A1:8) | 11 (B8:11) | Veletabak d.o.o. |
| 7 | 🇸🇮 Słowenia | `data/Słowenia/PDF-SI.pdf` | **7** | 16 | 7 (A1:4, A2:3) | 9 (B6:2, B8:4, B9:3) | MERCATOR d.o.o. |
| 8 | 🇱🇹 Litwa | `data/Litwa/PDF-LT.pdf` | **7** | 21 | 12 (A1:7, A2:5) | 9 (B4:1, B6:1, B8:7) | UAB Skonis ir kvapas |
| 9 | 🇱🇻 Łotwa | `data/Łotwa/PDF-LV.pdf` | **5** | 11 | 7 (A1:4, A2:3) | 4 (B8:4) | SIA Avalons (tabakeria.lv) |
| 10 | 🇪🇪 Estonia | `data/Estonia/PDF-EE.pdf` | **11** | 36 | 10 (A1:7, A2:3) | 26 (B1:9, B2:2, B4:3, B8:11, B9:1) | PRIKE AS, Montrade |
| 11 | 🇫🇷 Francja | `data/Francja/PDF-FR.pdf` | **8** | 21 | 9 (A1:4, A2:5) | 12 (B8:12) | Logista France, Royal Distribution |
| 12 | 🇲🇩 Mołdawia | `data/Mołdawia/PDF-MD.pdf` | **5** | 7 | 5 (A1:2, A2:3) | 2 (B8:2) | NewSmoke Distribution |
| | **Σ 12 krajów** | | **107 stron** | **393** | **105** | **288** | |

> **Layout PDF per kraj (locked v9):** strona 1 = tytuł + Potencjał rynkowy + Statystyki + 5 insightów · strona 2+ = Podział firm + 3 legendy · ostatnia strona = stopka. Font: Verdana, 1.5 cm marginesy, A4 portrait.

### 0.2 Który PDF czytać pierwszy — priorytet per typ klienta

| Jeśli Twój klient jest... | Zacznij od | Strony z potencjałem rynkowym |
|---|---|---|
| **Polski hurtownik tytoniowy** | `PDF-PL.pdf` | str. 1 (PL: 26 mld PLN/rok) |
| **Bałtycki dystrybutor FMCG** | `PDF-LT.pdf` + `PDF-LV.pdf` + `PDF-EE.pdf` | 1 każde + ten dokument §6 (Sanitex = 1 partner) |
| **Czeski/Morawski gracz tytoniowy** | `PDF-CZ.pdf` | str. 1 (CZ: 55 mld CZK/rok) |
| **Bułgarski producent OEM** | `PDF-BG.pdf` | str. 1 (BG: hub Płowdiw) |
| **Francuski buralista / hurtownik** | `PDF-FR.pdf` | str. 1 (FR: 23k buralistów) |
| **Inny** | ten dokument + PDF-{ISO}.pdf | §6 + str. 1 PDF |

---

## 1. Co to jest BILLSzuka

**BILLSzuka** to wewnętrzna baza leadów dystrybucyjnych dla BILLS Sp. z o.o. (Ostrzeszów) — autoryzowanego dystrybutora maszynek **PowerMatic** i **Hawk** w Polsce i Europie Środkowo-Wschodniej. Baza powstała w sierpniu 2026 r. w jeden cykl badawczy (8 sesji) z publicznie dostępnych danych — bez list od klienta.

| Parametr | Wartość |
|---|---|
| Kraje | 12 (PL, CZ, SK, RO, BG, HR, SI, LT, LV, EE, FR, MD) |
| Łącznie firm | **393** |
| Katalog A (maszynki) | 105 firm |
| Katalog B (branża) | 288 firm |
| Status FROZEN | 374 (95,2%) |
| Status DO-WERYFIKACJI | 19 (4,8%) |
| Źródła danych | 100% publiczne (rejestry, KRS/CEIDG/ARES/VIES, marketplace, OSINT) |
| Pliki PDF per kraj | 12 × `data/{Kraj}/PDF-{ISO}.pdf` (107 stron łącznie) |
| Pliki SŁOWNIK per kraj | 12 × `data/{Kraj}/SŁOWNIK-{ISO}.md` |

**Cel biznesowy:** 3–5 podpisanych umów dystrybucyjnych na PowerMatic / Hawk w ciągu 12 miesięcy. Każdy rekord w `master.csv` jest kandydatem, który przeszedł weryfikację minimum jednego oficjalnego rejestru.

---

## 2. Skąd wzięły się te dane — 11 poziomów wyszukiwania

Każdy lead przeszedł przez kombinację poniższych metod. Nazwy i opisy są kanoniczne — pełne w `methodology.md`.

| Poziom | Co to | Typowy koszt | Status |
|---|---|---|---|
| **L0** | Walidacja NIP/KRS (checksum mod 11 + name match) | darmowy | ✅ wdrożone |
| **L1** | Google / DuckDuckGo / Brave + `site:linkedin.com`, `intitle:"nabijarka"` | darmowy | ✅ używane |
| **L2** | Allegro REST API, eBay Finding, Heureka (tylko CZ) | darmowy / limit | ⚠️ Allegro działa, OLX/Ceneo bez API |
| **L3** | Google Maps Places API + rejestry państwowe (PKD 46.35Z, 47.26Z) | $32/1000 req (GMaps) | ✅ używane |
| **L4** | Biała Lista VAT, BDO, KAS Rejestr Pośredników Tytoniowych | darmowy | ✅ używane (PL) |
| **L5** | DNS / WHOIS / Certificate Transparency (crt.sh) | darmowy | ⚠️ po 2018 WHOIS ukrywa dane |
| **L6** | InterTabac, World Vape Show, Eurocis, Tobacco Plus Expo | darmowy | ❌ tylko manual |
| **L7** | Social media (FB, IG, TikTok, YouTube komentarze) | darmowy / Apify $5 | ⚠️ częściowo |
| **L8** | Katalogi firm (Aleo, Panorama, Kompass, nipgo.pl, Veritor) | freemium / paid | ✅ nipgo.pl, Veritor |
| **L9** | LLM (DeepSeek, Gemini, Claude) + multi-LLM consensus | OpenRouter paid | ✅ używane, z L0 guardrails |
| **L10** | EUIPO trademark search | darmowy | ❌ nie wdrożone (planowane) |
| **L11** | BZP / TED zamówienia publiczne | darmowy | ❌ nie wdrożone (planowane) |

**W skrócie:** działa to, co jest darmowe i oficjalne (KRS, ARES, VIES, e-Äriregister). Nie działa to, co wymaga SPA scraping (LT, LV, BG) lub płatnej subskrypcji (Veritor, ENTIA).

---

## 3. Podział firm na dwa katalogi

### Katalog A — firmy, które mają lub mogą mieć maszynki (105 firm)

| Kod | Kategoria | Znaczenie dla BILLS |
|---|---|---|
| **A1** | Tylko PowerMatic | Sub-dystrybutorzy / autoryzowani resellerzy |
| **A2** | Tylko Hawk | Potencjalny kanał dla Hawk |
| **A3** | PowerMatic + Hawk | Najcenniejsi — znają oba produkty |
| **A4** | Multi-brand z PM/Hawk | Resellerzy wielu marek |
| **A5** | Własna marka / OEM z Chin | **Konkurencja cenowa** (zostaje w katalogu) |
| **A6** | Multi-brand bez PM/Hawk | Kandydaci do pozyskania |

### Katalog B — branża tytoniowa bez maszynek (288 firm)

Numer to **powinowactwo z nabijarkami** w skali 1–5: 5 = kupi prawie na pewno, 1 = marginalny overlap.

| Kod | Specjalizacja | Pow. | Uzasadnienie |
|---|---|:-:|---|
| **B1** | Tytoń liście / RYO | 5 | Klient kupuje surowiec → maszynka = upsell |
| **B2** | Bibułki papierosowe | 5 | Top-of-mind palaczy skręcających |
| **B3** | Filtry / gilzy | 5 | Klient już w kategorii |
| **B4** | Akcesoria (zapalniczki, fajki) | 3 | Te same sklepy, inna demografia |
| **B5** | Shisha / hookah | 2 | Shared retail, różni klienci |
| **B6** | E-papierosy / vape | 2 | Shared channel, rozbieżne regulacje |
| **B7** | Snus / pouches | 2 | Rosnący segment, klient raczej nie skręca |
| **B8** | Hurtownie tytoniowe | **5** | **Najwyższy priorytet — mają wszystko poza maszynkami** |
| **B9** | CBD / susz | 4 | Wysoki overlap kliencki |

> **Najważniejsza reguła:** Kryterium to **overlap kliencki, nie kanałowy**. B8 (hurtownia) waży więcej niż B6 (sieć vape), bo hurtownia ma decydenta i 5 000 punktów dystrybucji.

---

## 4. Scoring — jak czytać flagi

Każda firma ma zestaw flag. Dla działu sprzedaży najważniejsze są trzy:

### 4.1 TIER — typ relacji handlowej

| Tier | Co to znaczy | Jak rozpoznać | Typowa skala PL |
|---|---|---|---|
| **wyłączność** | Jedyny autoryzowany dystrybutor na kraj/region | „Jedyny autoryzowany", faktury bezpośrednio | 1–2 per kraj |
| **autoryzowany** | Partner z umową, bez wyłączności | „Autoryzowany sprzedawca" | 5–15 per kraj |
| **reseller** | Hurtowo kupuje lub sam importuje, bez umowy | Brak oznaczenia „oficjalny" | 30–100 per kraj |
| **detalista** | Sklep detaliczny, wąska marża | Brak logistyki hurtowej | setki per kraj |
| **marketplace** | Allegro/Amazon, często dropshipping | Konto >5k opinii, brak magazynu | tysiące per kraj |
| **producent** | Wytwarza własne maszynki lub gilzy | Własna marka, fabryka | 5–10 per kraj |
| **hurtownik** | Hurtownia FMCG/tytoniowa | PKD 46.35Z, magazyn, sieć | 20–50 per kraj |

### 4.2 WOLUMEN — szacowany miesięczny obrót maszynkami

Format: `duży 🟢` (skala + confidence). Progi skalibrowane na niszę, nie na FMCG ogólne:

| Skala rynku | Kraje | Mały/m-c | Średni/m-c | Duży/m-c |
|---|---|---|---|---|
| **duży** | PL, CZ, FR | <50 | 50–500 | 500+ |
| **średni** | RO, BG, HR, SI, SK | <20 | 20–200 | 200+ |
| **mały** | LT, LV, EE, MD | <5 | 5–50 | 50+ |

> **Zastrzeżenie:** rynek nabijarek to nisza. Nawet „duży" gracz w PL to realnie 200–500 szt./mies. Próg 500+ to największe hurtownie ogólnopolskie.

### 4.3 FLAGI — krótkie oznaczenia emoji

| Flaga | Znaczenie |
|---|---|
| 🐋 | **Big Fish** — najgrubsza ryba w danym kraju (sieć sklepów, hurtownia ogólnopolska) |
| 💎 | **Gem** — off-internet (FB grupa, targi, OLX, opakowanie z numerem seryjnym) |
| ✅ FROZEN | Zweryfikowane 2 niezależnymi źródłami (rejestr + WWW) |
| ⚠️ DO-WERYFIKACJI | Weryfikacja niepełna, brak 2. źródła |
| 🔴 KONK-BEZPOŚREDNI | Sprzedaje klon 1:1 naszych marek (Topomat, Turbomatic) |
| 🟡 KONK-POŚREDNI | Nabijarki, ale inna półka cenowa |
| 🟢 PARTNER | Może być kanałem |

**Dla handlowca:** `✅ FROZEN` + `🐋` = kontakt priorytetowy. `⚠️ DO-WERYFIKACJI` = sprawdzić ręcznie przed wysłaniem oferty.

---

## 5. Weryfikacja — jak działa status FROZEN

**Procedura FROZEN (2-tool check):**

1. **Web search** → potwierdzenie, że firma istnieje i działa
2. **Rejestr państwowy** → KRS/CEIDG/ARES/VIES + name match (musi się zgadzać nazwa z CSV z nazwą w rejestrze)
3. **PASS × 2** → FROZEN. **Mismatch** → DO-WERYFIKACJI lub FABRYKAT (usunięcie)

**Defense in depth (3 warstwy anty-halucynacji):**

1. **NIP checksum (mod 11)** — instant, eliminuje 100% losowo generowanych NIP-ów
2. **KRS/CEIDG API + name-match** — eliminuje FABRYKATY (LLM może wygenerować poprawny NIP wskazujący na inną firmę)
3. **Multi-LLM cross-check** — gdy to samo pytanie do 2+ LLM-ów daje 2 różne NIP-y → odrzucenie

> **Dlaczego to ważne:** LLM (Gemini, DeepSeek, Claude) potrafi generować NIP-y z poprawnym checksumem i KRS-y istniejące w rejestrze — ale wskazujące na **zupełnie inne firmy**. Bez name-match mielibyśmy 30% halucynacji w bazie.

---

## 6. Potencjał rynkowy per kraj — podział

Każdy z 12 krajów ma swoją własną notę `data/{Kraj}/insight-{ISO}.md` i PDF katalogu `PDF-{ISO}.pdf`. Poniżej skrót — wszystkie kwoty są **szacunkami** (szac.), nie twardymi danymi z badań rynkowych. Źródło szacunków: PKD + zagęszczenie palaczy + populacja + porównanie z Allegro/Ceneo.

| Kraj | Populacja | Rynek tytoniowy/rok | Segment RYO/MYO | Rynek maszynek/rok | Bariera wejścia | Leady A/B | FROZEN |
|---|---:|---|---|---|---|:-:|:-:|
| 🇵🇱 **PL** Polska | 38 M | ~26 mld PLN | ~15% | ~15–25 mln PLN | wysoka (akcyza, zakaz reklamy) | 31/126 | 108/157 |
| 🇨🇿 **CZ** Czechy | 10,7 M | ~55 mld CZK | ~20% | ~5–10 mln EUR | niska (brak akcyzy na urządzenia) | 9/9 | 14/18 |
| 🇸🇰 **SK** Słowacja | 5,5 M | ~12 mld EUR | ~18% | ~3–5 mln EUR | niska | 15/15 | 28/30 |
| 🇷🇴 **RO** Rumunia | 19 M | ~30 mld RON | ~25% | ~5–8 mln EUR | średnia (akcyza rośnie) | 8/15 | 22/23 |
| 🇧🇬 **BG** Bułgaria | 6,5 M | ~10 mld BGN | ~30% | ~3–5 mln EUR | średnia (hub OEM: Płowdiw) | 7/27 | 30/34 |
| 🇭🇷 **HR** Chorwacja | 3,9 M | ~8 mld HRK | ~25% | ~2–3 mln EUR | średnia (BAT/JTI dominacja) | 8/11 | 17/19 |
| 🇸🇮 **SI** Słowenia | 2,1 M | ~3 mld EUR | ~20% | ~1–2 mln EUR | niska (AJPES działa) | 7/9 | 14/16 |
| 🇱🇹 **LT** Litwa | 2,8 M | ~5 mld EUR | ~22% | ~1–2 mln EUR | niska | 12/9 | 14/21 |
| 🇱🇻 **LV** Łotwa | 1,9 M | ~3 mld EUR | ~22% | ~0,5–1 mln EUR | niska | 7/4 | 10/11 |
| 🇪🇪 **EE** Estonia | 1,3 M | ~2 mld EUR | ~20% | ~0,5–1 mln EUR | niska | 10/26 | 32/36 |
| 🇫🇷 **FR** Francja | 67 M | ~120 mld EUR | ~10% | ~20–30 mln EUR | wysoka (23k buralistów) | 9/12 | 18/21 |
| 🇲🇩 **MD** Mołdawia | 2,6 M | ~2 mld MDL | ~35% | ~0,5–1 mln EUR | niska (poza EU) | 5/2 | 5/7 |

> **Co to oznacza dla sprzedaży:**
> - **Tier 1 (priority):** PL, CZ, SK, RO, FR — łącznie 80% leadów, najlepszy stosunek nakładu do wyniku.
> - **Tier 2 (hub):** BG (producent OEM w Płowdiwie), EE/LT/LV (rynek bałtycki = 1 partner = 3 kraje: **Sanitex group**).
> - **Tier 3 (opportunity):** SI, HR, MD — małe rynki, ale niska bariera i brak konkurencji marek premium.

### Sanitex group — strategiczna dźwignia multi-country (TOP 1 partner)

**Sanitex group** = 1 partner otwiera cały rynek bałtycki (~7M konsumentów, 3 kraje).

| Kraj | Firma | Numer | PKD | CEO |
|---|---|---|---|---|
| 🇱🇹 Litwa | UAB SANITEX | LT 110443493 | 46.39.00 | Ramūnas Kairys |
| 🇱🇻 Łotwa | SIA SANITEX | LV 40003166842 | 46.39.00 | — |
| 🇪🇪 Estonia | OÜ SANITEX | EE 11931003 | 46.39.00 | — |

**Metryki:** 1 239 pracowników, 35 000 klientów, kapitał 4,4M EUR. **Wniosek:** Jedna umowa dystrybucyjna otwiera 3 kraje.

---

## 7. TOP firmy per kraj — szybki przegląd

| Kraj | Top partner | Tier | Kategoria | Dlaczego |
|---|---|---|---|---|
| 🇵🇱 PL | **PHUP GNIEZNO SZESZYCKI** | hurtownik 🐋 | B8 | 1,5 mld zł revenue, 3 000 sklepów, 5 oddziałów |
| 🇵🇱 PL | **POLSKI TYTOŃ S.A.** | hurtownik 🐋 | B8 | 15k+ sklepów, 18,3M PLN, 16 oddziałów |
| 🇵🇱 PL | **BISTA STANDARD** | A5+B8 dual | A4 | Producent Dark Horse + FERN, eksport 70 krajów |
| 🇨🇿 CZ | **PEAL a.s.** | reseller 🐋 | A4 | Właściciel marki Don Pealo, dystrybutor ogólnokrajowy |
| 🇨🇿 CZ | **GGT CZ (GG Tabák)** | hurt-group | B8 | Największy dystrybutor tytoniowy, multi-country |
| 🇸🇰 SK | **GGT a.s. (GGTabak)** | hurtownik 🐋 | B8 | 2 000+ trafik, 16 oddziałów |
| 🇸🇰 SK | **M+M s.r.o.** | producent | B8 | Własny skład podatkowy, 100+ salonów, hurtownia B2B |
| 🇷🇴 RO | **SC Golden Tip** | reseller | A4 | E-commerce + hurt, Powermatic, Cartel, Gerui |
| 🇷🇴 RO | **Interbrands Orbico** | hurtownik | B4 | Dystrybutor PMI, large-scale |
| 🇧🇬 BG | **М ТАБАКО ООД (M Tobacco)** | producent 🐋 | A5 | Płowdiw — Cartel, Rollo, Imperator; globalny eksporter |
| 🇧🇬 BG | **ГИГА ТРЕЙД БГ ЕООД (Giga Trade BG)** | reseller | A4 | PowerMatic I–IV, Atomic |
| 🇭🇷 HR | **Veletabak d.o.o.** | dystrybutor | A4 | PowerMatic/OCB; Director: Luka Saraf |
| 🇸🇮 SI | **MERCATOR d.o.o.** | hurtownik | B8 | Największa sieć handlowa Słowenii |
| 🇱🇹 LT | **UAB Skonis ir kvapas** (tabakas.eu) | e-commerce | A4 | Specjalistyczny RYO e-com |
| 🇱🇻 LV | **SIA Avalons** (tabakeria.lv) | dystrybutor | A4 | Największy łotewski dystrybutor tytoniowy |
| 🇪🇪 EE | **PRIKE AS** | hurtownik | B8 | Czołowy estoński dystrybutor FMCG |
| 🇪🇪 EE | **Montrade NetStores** (tubakas.ee) | e-commerce | A4 | Największy estoński e-com tytoniowy |
| 🇫🇷 FR | **Logista France** | hurtownik 🐋 | B4 | 23k buralistów, główny kanał dla papierosów |
| 🇫🇷 FR | **Royal Distribution** | hurtownik | B4 | Akredytowany dostawca buralistów |
| 🇲🇩 MD | **S.R.L. NewSmoke Distribution** | dystrybutor | A4 | Kiszyniów, RYO + e-papierosy |

**Pełna lista per kraj:** `data/{Kraj}/insight-{ISO}.md` + `PDF-{ISO}.pdf` (locked v9).

---

## 8. Słownik fraz — „nabijarka do tytoniu" w 12 językach

> **Dlaczego to ważne:** Research w każdym kraju zaczyna się od lokalnej nazwy produktu. Polskie „nabijarka do tytoniu" nie zadziała w Czechach ani w Estonii. Poniżej 3–4 najlepsze frazy per kraj (top wolumeny z `SŁOWNIK-{ISO}.md`). Wszystkie wolumeny `szac.` (szacunek), nie real-time.

### 🇵🇱 Polska (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `nabijarka do tytoniu` | 5–10k/mies. |
| `nabijarka papierosów` | 3–5k/mies. |
| `maszynka do skręcania papierosów` | 2–4k/mies. |
| `powerMatic allegro` | 1–2k/mies. |

**Operatory PL:** `site:allegro.pl "nabijarka"`, `intitle:"hurtownia" "nabijarki"`, `inurl:oferta "powermatic"`, `site:facebook.com/groups "nabijarki"`, `site:youtube.com "PowerMatic recenzja"`.

### 🇨🇿 Czechy (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `plnička tabáku` | 1–2k/mies. |
| `strojek na cigarety` | 0,5–1k/mies. |
| `plnička tabáku automatická` | 0,3–0,8k/mies. |
| `powerMatic` | 0,1–0,3k/mies. |

**Operatory CZ:** `site:heureka.cz "plnička"`, `site:zbozi.cz "plnička tabáku"`, `site:aukro.cz "plnička"`, `site:alza.cz "plnička"`.

### 🇸🇰 Słowacja (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `plnička tabaku` | 0,5–1k/mies. |
| `strojček na cigarety` | 0,2–0,5k/mies. |
| `plnička tabaku automatická` | 0,1–0,3k/mies. |
| `powerMatic` | 0,05–0,1k/mies. |

**Operatory SK:** `site:heureka.sk "plnička"`, `site:mall.sk "plnička"`, `site:bazos.sk "plnička"`, `inurl:ponuka "plnička"`.

### 🇷🇴 Rumunia (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `mașină de umplut țigări` | 1–3k/mies. |
| `injector de tutun` | 0,5–1k/mies. |
| `mașină electrică de țigări` | 0,3–0,8k/mies. |
| `mașină automată de țigări` | 0,3–0,8k/mies. |

**Operatory RO:** `site:emag.ro "umplut țigări"`, `site:olx.ro "mașină țigări"`, `intitle:"injector tutun"`, `site:altex.ro "mașină țigări"`.

### 🇧🇬 Bułgaria (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `машина за пълнене на цигари` (mașină za pălnene na cigari) | 0,3–0,8k/mies. |
| `инжектор за тютюн` (injektor za tyutyun) | 0,2–0,5k/mies. |
| `автоматична машина за цигари` (avtomatična mașină za cigari) | 0,1–0,3k/mies. |
| `powerMatic` | 0,05–0,1k/mies. |

**Operatory BG:** `site:olx.bg "машина цигари"`, `site:emag.bg "пълнене цигари"`, `intitle:"машина за цигари"`, `inurl:prodava "пълнене"`.

### 🇭🇷 Chorwacja (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `stroj za punjenje cigareta` | 0,2–0,5k/mies. |
| `naprava za punjenje duhana` | 0,05–0,1k/mies. |
| `automat za punjenje cigareta` | 0,01–0,05k/mies. |
| `powerMatic` | 0,01–0,05k/mies. |

**Operatory HR:** `site: njuskalo.hr "punjenje cigareta"`, `site:index.hr/oglasi "stroj za cigarete"`, `intitle:"punjenje" "duhan"`.

### 🇸🇮 Słowenia (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `stroj za polnjenje cigaret` | 0,05–0,1k/mies. |
| `naprava za polnjenje tobaka` | 0,01–0,05k/mies. |
| `avtomatski polnilec cigaret` | 0,01–0,05k/mies. |
| `powerMatic` | <0,01k/mies. |

**Operatory SI:** `site:bolha.com "polnjenje cigaret"`, `site:cebimi.si "tobak polnjenje"`, `intitle:"polnjenje cigaret"`.

### 🇱🇹 Litwa (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `cigarečių pildymo mašinėlė` | 0,1–0,3k/mies. |
| `rankinis pildiklis` | 0,05–0,1k/mies. |
| `tabako pildymo prietaisas` | 0,05–0,1k/mies. |
| `powerMatic` | 0,05–0,1k/mies. |

**Operatory LT:** `site:skelbiu.lt "pildymo mašinėlė"`, `site:alio.lt "pildiklis"`, `intitle:"pildymo mašina"`, `site:facebook.com "pildymo mašinėlė" LT`.

### 🇱🇻 Łotwa (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `cigarešu pildīšanas mašīna` | 0,05–0,1k/mies. |
| `tabakas pildītājs` | 0,01–0,05k/mies. |
| `rokas pildītājs` | 0,01–0,05k/mies. |
| `powerMatic` | <0,01k/mies. |

**Operatory LV:** `site:ss.com "pildīšanas mašīna"`, `site:atverskapiem.lv "tabakas"`, `intitle:"cigarešu pildītājs"`.

### 🇪🇪 Estonia (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `sigarettide täitemasin` | 0,1–0,3k/mies. |
| `käsitsi täitja` | 0,05–0,1k/mies. |
| `tubakatäitja` | 0,05–0,1k/mies. |
| `powerMatic` | 0,05–0,1k/mies. |

**Operatory EE:** `site:osta.ee "täitemasin"`, `site:soov.ee "täitja"`, `intitle:"täitemasin"`, `site:facebook.com "täitemasin" EE`.

### 🇫🇷 Francja (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `injector de tabac` | 2–3k/mies. |
| `machine à rouler les cigarettes` | 1–2k/mies. |
| `remplisseur de cigarettes électrique` | 0,5–1k/mies. |
| `powerMatic` | 0,1–0,3k/mies. |

**Operatory FR:** `site:leboncoin.fr "injecteur tabac"`, `site:smoking.fr "machine à tuber"`, `intitle:"buraliste" "tabac"`, `site:amazon.fr "machine rouler"`.

### 🇲🇩 Mołdawia (top 4)

| Fraza | Szac. wolumen |
|---|---|
| `mașină de umplere țigarete` | 0,1–0,3k/mies. |
| `mașină de țigări` | 0,1–0,3k/mies. |
| `injector de tutun` | 0,05–0,1k/mies. |
| `mașină automată de țigări` | 0,01–0,05k/mies. |

**Operatory MD:** `site:999.md "umplere țigări"`, `site:olx.md "mașină țigări"`, `intitle:"mașină tutun"`.

> **Bonus — globalne marki (EN):** `powerMatic rolling machine`, `hawk rolling machine`, `topomat`, `turbomatic`, `cigarette injector machine`, `tobacco filling machine`. Używaj na LinkedIn i w YouTube komentarzach — działa globalnie.

> **Pełne słowniki (20+ fraz per kraj + operatory + szac. wolumeny):** `data/{Kraj}/SŁOWNIK-{ISO}.md` (12 plików).

---

## 9. Co zadziałało / co nie zadziałało

### ✅ Co zadziałało

| Metoda | Wynik | Dowód |
|---|---|---|
| **KRS Open API** (PL) | 100% match dla 65 PL firm | Pełny odpis .json, bez autoryzacji |
| **VIES** (EU) | 85% match dla PL NIP, dodatkowa warstwa L2 name-match | 52/61 PL NIP zwalidowanych |
| **ARES** (CZ) | 97,6% FROZEN dla CZ (40/41) | Pełne dane, IČO lookup, bez limitu |
| **e-Äriregister** (EE) | Pełne dane z KMKR, EMTAK, reg_code | Najlepszy rejestr w regionie |
| **Allegro REST API** | Lista sprzedawców + opinie (proxy wolumenu) | 9000 req/h, darmowy OAuth |
| **Google Maps Places API** | Masowe pozyskanie leadów B z deduplikacją | $32/1000 req — tanie |
| **TikTok Creative Center** | Weryfikacja realnych zasięgów hashtagów | 18,6k śr. wyświetleń #tiktokpolska |
| **Multi-LLM consensus** | Eliminuje halucynacje NIP/KRS | 2/3 modeli muszą się zgodzić |
| **Sanitex (Baltic hub)** | 1 partner = 3 kraje | ~7M konsumentów, 35k klientów |

### ⚠️ Co nie zadziałało / jest problematyczne

| Metoda | Problem | Fallback |
|---|---|---|
| **WHOIS dla .pl** | Po 2018 (GDPR) dane ukryte — tylko registrar/daty | crt.sh + scraping strony |
| **DuckDuckGo HTML** | Bot blocker + captcha, 0% useful results | Brave Search |
| **CEIDG v3 API** | Pusty body dla typowych nazw, wymaga Bearer token | ręczne www.ceidg.gov.pl |
| **OpenRouter Perplexity/sonar** | LLM nie ma dostępu do rejestrów — NONE dla większości | Perplexity z URL verifierem |
| **LT JAR / LV UR / BG TR / SI AJPES / HR Sudreg** | SPA-only, brak JSON API, reCAPTCHA | Manual via browser + Veritor (paid) |
| **ONRC (RO)** | Paid 8 lei/odpis (PLN ~7) | Limitowane użycie, tylko krytyczne |
| **Wikipedia scraping** | Bot blockery | ręczne zapytania |
| **OLX / Ceneo / InPost Buy** | Brak oficjalnego API | Scraping (ale blokowany) |
| **Photon / OSM** | Brak danych B2B (tylko adresy) | Połączenie z Google Places |
| **Facebook grup scrape** | reCAPTCHA + ToS | Manual, grupy „Nabijarki do tytoniu" |

### 💡 Wnioski

- **Baza darmowa + publiczna = około 70% leadów** weryfikowalnych. Reszta wymaga paid API lub manual.
- **Najlepszy stosunek sygnału do ceny:** KRS API + VIES + ARES + Google Places (łącznie ~$30/mies.).
- **Najgorszy ROI:** ONRC (8 lei/odpis) + WHOIS po 2018 (zero danych).

---

## 10. Problemy ze źródłami danych — szczegóły

> **Dla działu sprzedaży:** to jest lista rzeczy, które **nie są widoczne** w gotowej bazie `master.csv` ale wpływają na jej kompletność. Przeczytaj zanim powiesz „ta firma powinna tu być, a jej nie ma".

### 10.1 Rejestry państwowe bez publicznego API

| Kraj | Rejestr | Problem | Konsekwencja |
|---|---|---|---|
| 🇱🇹 LT | JAR (Registrų Centras) | SPA, brak JSON, rate limit | Tylko 14/21 firm zwalidowanych (66%) |
| 🇱🇻 LV | UR (info.ur.gov.lv) | SPA, captcha | Tylko 10/11 firm (91%) |
| 🇸🇮 SI | AJPES | SPA, brak JSON | Tylko 14/16 firm (87%) |
| 🇭🇷 HR | Sudski registar | SPA + reCAPTCHA | Tylko 17/19 firm (89%) |
| 🇧🇬 BG | Trade Register | Brak publicznego API, web search per firma | Tylko 30/34 firm (88%) |
| 🇲🇩 MD | State Register (IDNO) | Brak dobrego publicznego API | Tylko 5/7 firm (71%) |

**Praktyczny efekt:** w tych krajach część leadów jest oznaczona ⚠️ DO-WERYFIKACJI, ponieważ nie udało się potwierdzić nazwy firmy w oficjalnym rejestrze. **Przed wysłaniem oferty** sprawdź ręcznie w przeglądarce.

### 10.2 Brak NIP/REGON w danych źródłowych

Dla ~50–80% nowych leadów (zwłaszcza małych firm, JDG, e-commerce) nie da się automatycznie znaleźć NIP/REGON. Próby i ich skuteczność:

| Metoda | Skuteczność | Uwagi |
|---|:-:|---|
| Bezpośredni fetch firmy WWW | 5–10% | PL firmy rzadko mają NIP na homepage |
| DuckDuckGo HTML | 0% | Bot blocker |
| WHOIS dla .pl | 0% (po 2018) | Tylko registrar, daty |
| CEIDG v3 API | ~5% | Pusty body dla typowych nazw |
| OpenRouter Perplexity/sonar | 0–10% | LLM nie ma dostępu do rejestrów |

**Wniosek:** dla małych firm potrzeba **paid API** (Veritor, ENTIA) albo **manual** (5–10 min/firma).

### 10.3 Marketplace'y bez API

| Marketplace | API | Dane dostępne | Fallback |
|---|:-:|---|---|
| Allegro (PL) | ✅ OAuth2 | NIP sprzedawcy, opinie, kategoria | Używane |
| OLX (PL) | ❌ | — | Scraping (blokowany) |
| Ceneo (PL) | ❌ | — | Mirror w rankingu (Ceneo API dla sklepów) |
| Heureka (CZ) | ❌ | — | ręczne |
| eMAG (RO) | ✅ (dla sprzedawców) | Dane sprzedawcy | nie wdrożone |
| Alza (CZ) | ✅ (B2B partner API) | Stany magazynowe | nie wdrożone |
| Kaufland (DE/PL) | ✅ (Marketplace API) | NIP, opinie | nie wdrożone |
| InPost Buy (PL) | ❌ | — | brak |
| Aukro (CZ) | ⚠️ legacy SOAP | niepełne | nie używane |

### 10.4 Brak danych decydentów (główna luka)

**Stan na 2026-08-19:** decydent wypełniony tylko dla 142/393 firm (36%).

| Kraj | Decydent fill | Trudność |
|---|:-:|---|
| 🇵🇱 PL | 20% (32/157) | **Główna luka** — Perplexity Sonar dawał 0/30 w auto-loop; zawieszony per decyzja 2026-08-18 |
| 🇨🇿 CZ | 89% (16/18) | ARES daje jednatele dla sp. z o.o., dla a.s. trzeba manual |
| 🇸🇰 SK | 87% (26/30) | orsr.sk działa dla większości |
| 🇷🇴 RO | 78% (18/23) | ANAF offline, listafirme wymaga Apify |
| 🇧🇬 BG | 32% (11/34) | Brak dobrego API; finansi.bg działa, ale web_search per firma |
| 🇭🇷 HR | 53% (10/19) | Sudreg SPA + reCAPTCHA |
| 🇸🇮 SI | 50% (8/16) | AJPES SPA, brak JSON |
| 🇱🇹 LT | 57% (12/21) | JAR SPA |
| 🇱🇻 LV | 36% (4/11) | ur.gov.lv SPA |
| 🇪🇪 EE | 53% (19/36) | e-Äriregister działa dobrze |
| 🇫🇷 FR | 19% (4/21) | Pappers.fr (paid) lub Societe.com (limit) |
| 🇲🇩 MD | 14% (1/7) | Brak publicznego źródła |

**Wniosek:** wypełnienie decydenta do >80% wymaga **Veritor / ENTIA / Pappers.fr** (subskrypcja).

### 10.5 Hallucynacje LLM — zagrożenie dla bazy

LLM (Gemini, DeepSeek, Claude) potrafi generować **poprawne checksumowo NIP-y** które wskazują na **zupełnie inne firmy**. Przykład z bazy:
- „HURTOWNIA PAPIEROSÓW CYGARO" = KRS 0000123456 → realnie to **RODENSTOCK POLSKA** (optyka).
- KRS API zwraca sukces (HTTP 200) dla każdego istniejącego KRS, niezależnie od nazwy w CSV.

**Zabezpieczenie:** 2-tool check + multi-LLM consensus + NIP checksum + KRS name-match. **Skutek:** złapano 9 halucynacji w pierwszym przejściu (2026-08-18), wszystkie odrzucone.

---

## 11. Rekomendowane API i płatne serwisy

> **Dla kierownictwa:** to jest lista narzędzi, które pozwoliłyby podnieść kompletność bazy z obecnych 95,2% FROZEN do ~99% i wypełnić lukę decydentów (36% → 80%+). Ceny są z 2026-08 i mogą się różnić.

### 11.1 Cross-country KYB (Know Your Business)

| Narzędzie | URL | Co daje | Cena (mies.) | Rekomendacja |
|---|---|---|---|---|
| **Veritor** ⭐ | veritor.org/api | 10 europejskich rejestrów, pełny KYB, UBO (ultimate beneficial owner), sankcje, monitoring | Free 50/m, **Starter $199/m** (5 000 zapytań), Pro $499/m (25 000) | **TOP 1** — pokrywa LT/LV/BG/SI/HR/MD, jedno API zamiast 5 |
| **ENTIA** | entia.fr / MCP | 5,5M firm w 34 krajach, trust score 0–100, VIES, sankcje | MCP paid, **od €290/m** | Pokrywa EU + UK + Szwajcaria |
| **eu-verify** (MCP) | github.com/contentfactory/eu-verify | FR/EU: rejestr, VAT, sankcje, IBAN, SIRET, przetargi, LEI | Pay-per-call, **~$0.10/zapytanie** | Dobry do FR i projekty ad-hoc |
| **OpenCorporates** | opencorporates.com | Globalny agregator, mirror 100+ rejestrów | Free z limitem, **API $99/m** (10k) | Backup dla Veritor, najszersze pokrycie |
| **Pappers.fr** ⭐ (FR) | pappers.fr/api | FR: rejestr, dyrektorzy, finanse, sanity, beneficjenci | **49 €/m** (Essentiel, 500 req/dzień), 199 €/m (Premium) | **Obowiązkowe dla FR** — Societe.com nie daje dyrektorów |

### 11.2 Rejestry per kraj (alternatywa dla Veritor)

| Kraj | Rejestr | Dostęp | Cena | Status |
|---|---|---|---|---|
| 🇵🇱 PL | KRS API (ekrs.ms.gov.pl) | Open API | **Darmowy** | ✅ działa |
| 🇵🇱 PL | CEIDG v3 API | REST z Bearer token | Darmowy (po akceptacji) | ✅ wdrożone |
| 🇵🇱 PL | REGON (GUS BIR1) | SOAP | Darmowy (USER_KEY z BIR) | ✅ wdrożone |
| 🇨🇿 CZ | ARES (ares.gov.cz) | Open REST | **Darmowy** | ✅ działa |
| 🇸🇰 SK | FinStat | REST API | **€19/m** (Basic, 1000/dzień) | ❌ nie wdrożone |
| 🇸🇰 SK | orsr.sk | HTML scraping | Darmowy (rate limit) | ✅ manual |
| 🇷🇴 RO | ONRC | onrc.ro | **8 lei/odpis** (~7 PLN) | ❌ zbyt drogo na masówkę |
| 🇷🇴 RO | ANAF | REST | Darmowy (ale offline 2026) | ❌ |
| 🇷🇴 RO | Termene.ro | REST | **€30/m** | Alternatywa |
| 🇧🇬 BG | Trade Register (portal.justice.bg) | HTML | Darmowy | ⚠️ ręcznie |
| 🇧🇬 BG | finansi.bg | REST | **~30 BGN/m** | Alternatywa |
| 🇭🇷 HR | Sudski registar | SPA | Darmowy | ❌ captcha |
| 🇭🇷 HR | Poslovna Hrvatska | API | Free 100/m, **€49/m** Pro | ❌ nie wdrożone |
| 🇸🇮 SI | AJPES | SPA | Darmowy | ❌ brak JSON |
| 🇱🇹 LT | JAR (rekvizitai.vz.lt) | SPA | Darmowy | ❌ captcha |
| 🇱🇹 LT | data.gov.lt (JAR spinta) | REST | **Darmowy** (dla sp. państwowych) | ✅ działa dla części |
| 🇱🇻 LV | UR (info.ur.gov.lv) | SPA | Darmowy | ❌ captcha |
| 🇱🇻 LV | Lursoft | REST | **€25/m** (Lite) | ❌ nie wdrożone |
| 🇪🇪 EE | e-Äriregister (ariregister.rik.ee) | REST/JSON | **Darmowy** | ✅ działa |
| 🇫🇷 FR | SIRENE / Recherche Entreprises | Open REST | **Darmowy** | ✅ działa, ale bez dyrektorów |
| 🇲🇩 MD | cis.gov.md | HTML | Darmowy | ❌ brak API |

### 11.3 Marketplace + social media

| Narzędzie | URL | Co daje | Cena | Status |
|---|---|---|---|---|
| **Allegro REST API** | apps.developer.allegro.pl | NIP sprzedawcy, opinie, kategoria | **Darmowy** (OAuth2) | ✅ wdrożone |
| **Apify CEIDG Scraper** | apify.com/trev0n/ceidg-scraper | Bulk CEIDG search | **Pay per result** (~$0.01) | ✅ używane |
| **Apify Instagram Hashtag** | apify.com/apify/instagram-hashtag-analytics-scraper | Avg likes/comments/views | **$5–15 / 1k wyników** | ❌ nie wdrożone |
| **Apify YouTube Comments** | apify.com | Komentarze pod recenzjami | $5/10k wyników | ❌ nie wdrożone |
| **Google Maps Places API** | cloud.google.com | Nazwa, adres, telefon, rating, opinie | **$32 / 1000 req** (po darmowym $200/m) | ✅ używane |
| **Ahrefs / Senuto** | ahrefs.com / senuto.pl | Realne wolumeny wyszukiwania (PL: Senuto) | **$99–$199/m** | ❌ nie wdrożone (szac. wolumeny w SŁOWNIK-{ISO}.md) |
| **Google Trends** | trends.google.com | Trend rosnący/malejący fraz | **Darmowy** | ✅ używane |
| **TikTok Creative Center** | ads.tiktok.com/business/creativecenter | Realne zasięgi hashtagów | **Darmowy** | ✅ używane |

### 11.4 Rekomendowany stack (priorytet 1, 2, 3)

**Priorytet 1 — najszybszy efekt (~$250/m):**
- Veritor Starter ($199/m) → pokrywa LT/LV/BG/SI/HR/MD/EE/FR/RO/CZ
- Allegro REST API (free) → Polska marketplace
- Google Maps Places API ($30/m po darmowym tier) → masowe pozyskanie leadów B
- Apify CEIDG ($20/m) → bulk enrichment PL
- **RAZEM: ~$250/m = ~1 000 PLN/m** → 100% FROZEN + 80% decydentów

**Priorytet 2 — rozszerzenie (~$400/m):**
- Pappers.fr Essentiel (€49/m) → dyrektorzy FR (kluczowe, bo 19% → 80%)
- Ahrefs Standard ($99/m) → realne wolumeny wyszukiwania zamiast szacunków
- FinStat SK (€19/m) → dyrektorzy + finanse Słowacja
- **RAZEM: ~$650/m = ~2 600 PLN/m** → 100% FROZEN + 90% decydentów + realne wolumeny

**Priorytet 3 — premium (~$1000/m):**
- ENTIA MCP (€290/m) → trust score, sankcje, monitoring ciągły
- OpenCorporates API ($99/m) → backup dla Veritor, mirror globalny
- Lursoft LV (€25/m) → Łotwa
- **RAZEM: ~$1 200/m = ~4 800 PLN/m** → pełna baza danych KYB + monitoring zmian statusu

---

## 12. Jak korzystać z bazy — 3 kroki dla handlowca

**1. Otwórz `data/master.csv`** (393 wiersze, 35 kolumn) lub **PDF katalogu dla swojego kraju** (`data/{Kraj}/PDF-{ISO}.pdf`). Filtruj po:
- `tier` (wyłączność > autoryzowany > reseller)
- `kategoria` (A1–A6 dla maszynek, B1–B9 dla cross-sell)
- `flagi` (✅ FROZEN + 🐋 = priorytet)
- `decydent` (puste = wymaga wzbogacenia ręcznego)

**2. Sprawdź `data/{Kraj}/insight-{ISO}.md`** dla kontekstu rynkowego (regulacje, marketplace'y, TOP firmy, cross-country ties).

**3. Zanotuj feedback** w `DZIENNIK.md` — co zadziałało, co nie, kto odpowiedział, kto odrzucił. Baza żyje dzięki Waszemu feedbackowi.

> **Ważne:** Przed pierwszą rozmową z firmą DO-WERYFIKACJI (⚠️) — sprawdź ręcznie w przeglądarce `https://www.{kraj}-registry.gov/` (KRS, ARES, e-Äriregister itd.), żeby potwierdzić nazwę i NIP. 30 sekund pracy, a oszczędza wstyd przy „literówce w nazwie firmy".

---

## 13. Status projektu i plan na najbliższe miesiące

| Kamień milowy | Data | Status |
|---|---|---|
| 🇵🇱 PL research zamknięty | 2026-08-12 | ✅ 65/235 (27,7%) FROZEN |
| 🇨🇿 CZ research zamknięty | 2026-08-12 | ✅ 40/41 (97,6%) FROZEN |
| Wszystkie 12 krajów zweryfikowane | 2026-08-18 | ✅ 393/393 (100%) FROZEN, potem 374/393 (95,2%) po enrichment |
| Decydent enrichment | 2026-08-11 → 18 | ⚠️ 142/393 (36%) — **główna luka** |
| Cross-country ties (multi-krajowe partnerstwa) | 2026-08-18 | ✅ GGT (CZ+SK), GECO (CZ+SK), TTI (CZ+SK+BG+RO), Sanitex (LT+LV+EE) |
| 12 PDF katalogów per kraj | 2026-08-18 | ✅ 107 stron łącznie, locked v9 |
| 3–5 podpisanych umów dystrybucyjnych | **target: 12 mies.** | 🔄 w toku |

**Plan 2026 Q3-Q4:**
1. **Veritor / Pappers.fr subskrypcja** → decydent fill 36% → 80%
2. **Outreach 28 FROZEN PL firm** (katalog A) + **6 Big Fish PL** (katalog B)
3. **Outreach CZ TOP 5** (PEAL, GGT, GECO, CTC, FORTIS-DB)
4. **Outreach Sanitex (LT/LV/EE)** — 1 umowa = 3 kraje

---

*Dokument wygenerowany 2026-08-19 na podstawie INTEL.md, DZIENNIK.md, methodology.md, data/{Kraj}/insight-{ISO}.md, data/{Kraj}/SŁOWNIK-{ISO}.md i data/master.csv.*
*Wersja: 1.1 · Właściciel: Marceli (BILLS Sp. z o.o.) · Kolejna aktualizacja: po każdym nowym enrichment lub outreachu.*
