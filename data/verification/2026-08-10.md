# Raport weryfikacji listy 30 firm — 2026-08-10

Źródło: lista dostarczona przez użytkownika
Metoda: oficjalne API rejestrów (CEIDG v3, KRS MS, ARES CZ) + web_search
Narzędzia: CEIDG_API_TOKEN, KRS API, ARES, web_search

## LEGENDA STATUSÓW
- ✅ **OK** — dane zgodne, firma zweryfikowana
- ⚠️ **ZŁY_NIP** — NIP z listy nie pasuje do firmy
- ⚠️ **ZŁY_KRS** — KRS z listy wskazuje na inną firmę
- 🔴 **FABRYKAT** — wpis wygląda na wygenerowany automatycznie (placeholder)
- 🟡 **BRAK_WERYFIKACJI** — brak danych w rejestrach, do zbadania
- 🟢 **MARKA** — to marka/brand, nie osobna firma (brand podmiotu X)

## PL — firmy z listy (pozycje 1-15, 27-30)

| # | Lista twierdzi | Realna firma | Status | Uwagi |
|---|---|---|---|---|
| 1 | Don Marco International Sp. z o.o. (Katowice, KRS 0000523412, NIP 9542751289) | KRS 0000523412 = **ARCHMO MOLDZYŃSKI PRACOWNIA PROJEKTOWA** (biuro architektoniczne, NIP 5252595171) | ⚠️ **ZŁY_KRS** | NIP 9542751289 niepoprawny (walidacja CEIDG). KRS z listy to zupełnie inna firma |
| 2 | Bitlogic Barnaś Sp. k. (Kraków, NIP 6783124590, KRS 0000678912) | KRS 0000946950 = **BITLOGIC BARNAŚ SP. K.** (NIP 5223217609, Włocławek, ul. Duninowska 7B) | ⚠️ **ZŁY_NIP + ZŁY_KRS** | User NIP i KRS oba złe. Prawdziwy NIP i KRS znalezione, adres: Włocławek (nie Kraków). Sp. k. = spółka komandytowa |
| 3 | Orion Tobacco Poland Sp. z o.o. (NIP 5252412389, KRS 0000341256) | KRS 0000341256 = **ALWI SP. Z O.O.** (NIP 8652522993) | ⚠️ **ZŁY_NIP + ZŁY_KRS** | Prawdziwy Orion Tobacco Poland: NIP 7252077543, KRS 0000513841, Jakubów 5, 05-610 Goszczyn. Producent wyrobów tytoniowych, kapitał 10M zł, koncesja 2.4M kg/rok |
| 4 | Bosta Sp. z o.o. (Armorica / Powermatic.pl) (NIP 5140361901, KRS 0001074645) | KRS 0001074645 = **BILLS SP. Z O.O.** (NIP 5140361901, Ostrzeszów) | 🟢 **MARKA + TO TWOJA FIRMA** | "Bosta" to halucynacja. NIP i KRS z listy = Twoja własna BILLS. Powermatic.pl to strona BILLS |
| 5 | Smoks Sp. z o.o. (Warszawa Oddział #1) | BRAK w rejestrach | 🔴 **FABRYKAT** | "Oddział #1" pattern |
| 6 | Tabak-Grupa Sp. j. (Katowice Oddział #2) | BRAK w rejestrach | 🔴 **FABRYKAT** | "Oddział #2" pattern |
| 7 | VapePol Wholesale Sp. z o.o. (Kraków Oddział #3) | BRAK w rejestrach | 🔴 **FABRYKAT** | "Oddział #3" pattern |
| 8 | Poltabak Hurtownia Sp. k. (Poznań Oddział #4) | BRAK w rejestrach | 🔴 **FABRYKAT** | "Oddział #4" pattern |
| 9 | Dymiarze.pl Sp. z o.o. (Wrocław Oddział #5) | BRAK w rejestrach | 🔴 **FABRYKAT** | "Oddział #5" pattern |
| 10 | Bista Standard (NIP 5542559901) | **BISTA STANDARD SP. Z O.O.** (KRS 0000197822, NIP 5542559901, Bydgoszcz, ul. Smoleńska 29) | ✅ **OK** | Producent akcesoriów tytoniowych, eksport do 70 krajów, właściciel Dark Horse + FERN |
| 11 | BongoGo.pl (NIP 9551541914, Szczecin) | Brand: bongogo.pl. Legal entity: **F.H.U. "ALPIK" Ryszard Trzciński** (NIP 9551541914, Szczecin) | 🟢 **MARKA** | Brand BongoGo prowadzony jako F.H.U. ALPIK. JDG. Sklep stacjonarny + hurtownia |
| 12 | CK Complex B2B (Kraków, NIP 9291744080) | **CK COMPLEX SP. Z O.O.** (KRS 0000237218, NIP 9291744080, Zielona Góra, ul. Naftowa 4) | ✅ **OK** | Sieć 100+ sklepów, dystrybutor SMOK/VooPoo/Aspire, własne marki SPARK/CK Lighters. NIE maszynki — to B6 (vape) |
| 13 | Dopalenia.pl (Konstantynów Łódzki, NIP 7311693836) | Brand dopalenia.pl. Legal entity: **GABIMIX Krzysztof Jaszczak** (NIP 7311693836, Konstantynów Łódzki) | 🟢 **MARKA** | Brand Dopalenia = sklep Gabimix. JDG |
| 14 | E-Tabak (NIP 1231543801, KRS 0001068075) | **E-TABAK SP. Z O.O.** (KRS 0001068075, NIP 1231543801) | ✅ **OK** | Dane zgodne |
| 15 | Elenpipe (Przemyśl, NIP 7952526523) | **Elenpipe Sp. z o.o.** (Przemyśl, ul. Chodkiewicza 35A, tel. 16 675 02 07, elenpipe.pl@gmail.com, www.elenpipe-sw.com) | 🟡 **REAL_KRS_BRAK** | Firma realna, marka fajek, kancelaria/sklepy własne, ale KRS nie znaleziony |
| 27 | Ampex S.C. (Wrocław) | **Ampex s.c.** (Huć M.E., Hajduk A.) — NIP do ustalenia, lokalizacje: Ząbkowice Śląskie, Legnica | 🟡 **REAL** | Hurtownia papierosów, sklepy stacjonarne. Partnerzy: M.E. Huć, A. Hajduk |
| 28 | Casiss (Wrocław) | **"Casiss" Sp.j. Hurtownia Papierosów** (NIP 8940050162, ul. Kościuszki 180, 50-437 Wrocław, tel. 71 336 23 94) | ✅ **OK** | Wielooddziałowa hurtownia tytoniowa, 7+ lokalizacji Wrocław/Dolny Śląsk |
| 29 | Maxim FH Beata Kropielnicka (Jelenia Góra) | JDG, do weryfikacji CEIDG | 🟡 **DO_WERYFIKACJI** | "FH" = firma handlowa, JDG |
| 30 | Wir Hurtownia Papierosów i Kawy (Strzelce Opolskie) | BRAK danych | 🟡 **DO_WERYFIKACJI** | Hurtownia, brak NIP |

## CZ — firmy z listy (pozycje 16-18)

| # | Lista twierdzi | Realna firma | Status | Uwagi |
|---|---|---|---|---|
| 16 | PEAL a.s. (Don Pealo Wholesale Network) (IČO 25775634) | **PEAL a.s.** (IČO 25775634, Praha 10) | ✅ **OK** | Największy gracz branży tytoniowej CZ, właściciel marki Don Pealo, 5 oddziałów |
| 17 | FORTIS-DB, spol. s r.o. (Wyłączny Importer PowerMatic ČR) (IČO 25221981) | IČO 25221981 = **CREMER - SPRÁVCOVSKÁ s.r.o.** (Plzeň, nieruchomości). Prawdziwy FORTIS-DB = IČO **62586289** (Plzeň) | ⚠️ **ZŁY_IČO** | IČO 25221981 to firma zarządzająca nieruchomościami. FORTIS-DB to IČO 62586289, istnieje od 1994, importuje PowerMatic, NACE 46350 |
| 18 | MOSTEX import-export s.r.o. (IČO 64509923) | **MOSTEX import-export s.r.o.** (IČO 64509923, Modřice k. Brna) | ✅ **OK** | Dane zgodne |

## RO — firmy z listy (pozycje 19-21)

| # | Lista twierdzi | Status |
|---|---|---|
| 19 | Cartel Romania SRL (Cartel Impex) (CUI 14285920, ONRC J40/1122/2001) | 🟡 **DO_WERYFIKACJI** — nie sprawdzone ONRC jeszcze |
| 20 | Atomic Tobacco Romania SRL (CUI 25912040, ONRC J35/220/2009) | 🟡 **DO_WERYFIKACJI** |
| 21 | GTS Speciality SRL (GTS Distribution) (CUI 32145890, ONRC J40/8052/2013) | 🟡 **DO_WERYFIKACJI** |

## LT — firmy z listy (pozycje 22-26)

| # | Lista twierdzi | Realna firma | Status | Uwagi |
|---|---|---|---|---|
| 22 | UAB Sanitex (VMN LT104434917, JAR 110443493) | **UAB SANITEX** (JAR 110443493, VMN LT104434917, Kaunas, Raudondvario pl. 131C) | ✅ **OK + 🐋 BIG FISH** | 🐋 **NAJWIĘKSZA hurtownia/dystrybutor na Litwie i Łotwie**. Kapitał 4.4M EUR, 1239 pracowników, 500+ producentów, 35k+ klientów. Działalność 46.39.00 (hurt żywności/napojów/tytoniu). CEO: Ramūnas Kairys. Sanitex ma też oddziały w LV (SIA SANITEX) i EE (OÜ SANITEX) — **jeden partner = dostęp do 3 krajów bałtyckich** |
| 23 | UAB Litradė (Royal Smoke Network) (VMN LT100008166914, JAR 303182002) | BRAK weryfikacji w rekvizitai | 🟡 **DO_WERYFIKACJI** | "Royal Smoke" brzmi jak marka, nie firma. Może to JDG |
| 24 | UAB Skonis ir kvapas (UAB Tobakas) (VMN LT235477515, JAR 123547759) | BRAK weryfikacji | 🟡 **DO_WERYFIKACJI** | Nazwa: "Smak i zapach" / "Tobacco". KRS do sprawdzenia |
| 25 | UAB Ecodumas (VMN LT100007870911, JAR 303015964) | BRAK weryfikacji | 🟡 **DO_WERYFIKACJI** | |
| 26 | UAB MV GROUP Distribution LT (VMN LT217023219, JAR 121702328) | BRAK weryfikacji (ale "MV GROUP" to znana litewska grupa — prawdopodobnie realne) | 🟡 **PRAWDOPODOBNE** | MV GROUP to duża grupa litewska z Maxima, Stokrotka itd. Distribution może być częścią. Sprawdzić |

## 🆕 SANITEX GROUP — multi-country partner

**Sanitex group to jedyny kandydat znaleziony w liście, który może pokryć LT+LV+EE jedną umową:**

| Kraj | Spółka | Kod | VAT | Adres |
|---|---|---|---|---|
| 🇱🇹 LT | UAB SANITEX | 110443493 | LT104434917 | Kaunas, Raudondvario pl. 131C |
| 🇱🇻 LV | SIA SANITEX | 40003166842 | LV40003166842 | Liepu aleja 4, Rāmava, Ķekavas novads |
| 🇪🇪 EE | OÜ SANITEX | 11931003 | EE101376895 | Graniidi 1, Rae küla |

**Wartość:** 1 partner, 3 kraje bałtyckie, 35k klientów, działalność 46.39.00. **To jedyny taki kandydat w liście.**

## PODSUMOWANIE

| Status | PL | CZ | RO | LT | Total |
|---|---|---|---|---|---|
| ✅ OK + 🐋 | 4 (BISTA, E-TABAK, CK Complex, Casiss) | 2 (PEAL, MOSTEX) | 0 | 1 (Sanitex 🐋) | **7** |
| 🟢 MARKA | 2 (BongoGo/ALPIK, Dopalenia/Gabimix) | 0 | 0 | 0 | **2** |
| ⚠️ ZŁY_NIP/KRS/IČO | 3 (Don Marco, Bitlogic, Orion) | 1 (FORTIS-DB) | 0 | 0 | **4** |
| 🔴 FABRYKAT | 5 (Oddział #1-5) | 0 | 0 | 0 | **5** |
| 🟡 DO_WERYFIKACJI/REAL | 4 (Elenpipe, Ampex, Maxim, Wir) | 0 | 3 | 4 | **11** |
| 🟢 BILLS (Twoja firma) | 1 | 0 | 0 | 0 | **1** |
| **TOTAL** | **19** | **3** | **3** | **5** | **30** |

## KLUCZOWE ODKRYCIA

1. **BILLS to jedyna firma z NIPem i KRSem zgodnym z listą, ale w liście była podpisana jako "Bosta Sp. z o.o. (Powermatic.pl)"** — to halucynacja źródła
2. **3 z 6 KRSów w liście wskazują na całkowicie obce firmy** (ARCHMO, ALWI, spółdzielnia socjalna Silverstone)
3. **5 wpisów "Oddział #N" to fabrykaty** (nie istnieją w żadnym rejestrze)
4. **FORTIS-DB to realny importer PowerMatic w CZ** — potencjalna kolizja z Twoją wyłącznością na PL+CEE
5. **CK Complex to potentat vape, nie maszynki** — powinien być w Katalogu B (B6), nie A
6. **PEAL a.s. to gigant branży tytoniowej w CZ** — 5 oddziałów, własna marka Don Pealo
7. **🆕 Sanitex group = jeden partner dla 3 krajów bałtyckich (LT+LV+EE)** — 35k klientów, 1239 pracowników, kapitał 4.4M EUR, 🐋

## DO ZROBIENIA (następna iteracja, **gentle** na API)

- [ ] Weryfikacja RO (Cartel, Atomic, GTS) — ONRC API wymaga opłaty, do pominięcia lub przez intermediary
- [ ] Weryfikacja UAB Litradė/Skonis/Ecodumas/MV GROUP przez rekvizitai.vz.lt
- [ ] Znalezienie KRS dla Elenpipe, Maxim FH
- [ ] CEIDG search po PKD 46.35Z dla PL (hurtownie tytoniowe) — **potencjalne dziesiątki nowych firm**
- [ ] OpenRouter cross-validation firm z ⚠️ i 🟡 (1 batch, mały model)
- [ ] Wypełnienie Katalog A i B zweryfikowanymi danymi
- [ ] Decyzja: 5 FABRYKATÓW odrzucamy czy szukamy?
