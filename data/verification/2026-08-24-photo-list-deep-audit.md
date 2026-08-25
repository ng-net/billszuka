## 2026-08-24 — DEEP RE-VERIFICATION (rec. analysis)

### Scope
Re-audit of 13 EXCLUDE companies from initial verification (companies.md).
Metoda: ARES + rejstrik-firem + datasrl.ro + firmealert.ro + firme.euro.cz + listafirme.ro + WebSearch.
Focus: false negatives (companies wrongly excluded), NIP/CUI discrepancies, network analysis.

### Key discoveries

#### ✅ RECONSIDER (1 firma) — przeniesienie z EXCLUDE → ACTIVE
- **Eva Machačná** (IČO 44560176, Kunratice u Cvikova 393, CZ) — z EXCLUDE → ACTIVE B4
  - **ARES CZ-NACE hlavní: Maloobchod s převahou potravin, nápojů a tabákových výrobků v nespecializovaných prodejnách**
  - To jest **sklep z artykułami spożywczymi + wyrobami tytoniowymi** (B-tier). Powiązanie z miejscowością Kunratice u Cvikova 411 = "Smíšené zboží" + KOLONIÁL — JOACHIMSTÁLOVÁ.
  - Rekomendacja: B4 (akcesoria + artykuły dla palaczy)
  - Wolumen: mały (1 OSVČ, mała wieś)

#### 🔍 HOSTING TIME s.r.o. — POTWIERDZONY EXCLUDE (ale uwaga na sygnał)
- **Hosting time s.r.o.** (IČO 04302231, Švabinského 1700/4, Ostrava) — z EXCLUDE → EXCLUDE
- **WAŻNE odkrycie:** od 24.6.2025 ma předmět podnikání: **Velkoobchod a maloobchod** + Výroba chemických látek + Reklamní činnost
- **ALE:** vlastnik Monika Dąbkowska (Polska, Boruja Kościelna) → sídlí pod zahraniční kontrolou (virtual office pattern)
- **W tym samym adresie (Švabinského 1700/4, Ostrava) inne firmy:** ACCOUNT NEW CORPORATE CZ a.s. (28616715), TOKMO GLOBAL s.r.o. (03077161), Scrap Leader s.r.o. (04124715), CZECH SOLVATO s.r.o. (03051315), JBB Franchise s.r.o., Flex Step, DESOFT...
- To wyraźnie **virtual office / mailbox** dla polskich firm na CZ — NIE realna firma tytoniowa
- Obrat 10-30M Kč (2024) per ČSÚ — to jest wielu firm łącznie na ten adres (nie jedna)
- **EXCLUDE — to nie lead dla BILLS** (brak specjalizacji tytoniowej + shell company pattern)
- **ALE:** warto monitorować adres pod kątem nowych firm z branżą tytoniową (prospecting future)

#### 🔍 CERBU IOANA — sieć firmy
- **Cerbu Ioana** (Jilava/Ilfov) — administrator firmy **GRAND PRODUCT SRL** (CUI 16049841, J23/27/2004)
- GRAND PRODUCT: **CAEN 4647 (Comert cu ridicata al mobilei, covoarelor si a articolelor de iluminat)** — NIE branża tytoniowa
- Status GRAND PRODUCT: **întrerupere temporară de activitate** (firmeo.ro) + **suspendată** (firme360.ro)
- Cerbu Ioana = osoba prywatna, brak widocznego powiązania z tytoniem
- **EXCLUDE potwierdzony**

### ❌ WYKLUCZONE POTWIERDZONE (po ponownej analizie)

#### Branża wyklucza
- **OREA HOTELS s.r.o.** (CZ 27176657) — CZ-NACE 55100 Ubytování v hotelích. POSIADA sieć 20+ hoteli (Praha, Brno, mountains, spa). NIE branża tytoniowa. Brak śladu zakupów kuřáckých potřeby hurtowo. **EXCLUDE — nie lead**
- **Hosting time s.r.o.** (CZ 04302231) — patrz wyżej. **EXCLUDE — virtual office pattern**
- **Zasen Trade Invest SRL** (RO 41399635) — CAEN 5610 Restaurante. Adres rejestrowy Bd. Tineretului 2 ≠ Soldat Stefan Simion 41 (z faktury). **EXCLUDE — restauracja + adres się nie zgadza**
- **ARTHEK Machines SRL** (RO 43407106) — CAEN 3314 (naprawa urządzeń elektr.). 1 pracownik, 800K RON obrotu. **EXCLUDE — serwis, nie dystrybutor**
- **DIPA CONCEPT SRL** (RO 31861043) — **STATUS INACTIVĂ (radiată z Registrul Comerțului od 26.02.2026)**. CAEN 4635 (hurt tytoniowy) ale firma nie operuje. Ostatni bilant 2015 (477K RON). **EXCLUDE — wykreślona**

#### Osoby fizyczne bez śladu branżowego
- **Jana Zelezna** (Telc) — brak IČO w ARES, brak powiązania. **EXCLUDE — za mało danych**
- **Iveta Burešová** (Kladno) — w ARES są 3 różne Iveta Burešová (Praha/Chodov, Katovice, Ostrov). **Żadna nie w Kladno**. Możliwe: tożsamość niepotwierdzona lub firma wygasła. **EXCLUDE — brak potwierdzenia tożsamości**
- **Hana Sretrova** (Bílina) — Mgr. Hana Šretrová (IČO 76140598) istnieje, ale sídlo: Družstevní 883, **Luhačovice** (NIE Bílina). Předmět: poradenská činnost + mimoškolní výchova + textil. **NIE branża tytoniowa**. Tożsamość: inna osoba. **EXCLUDE — inna osoba, nie-branża**
- **Luca Cristian Lucian** (Craiova) — brak śladu w ONRC/ANAF pod dokładnym imieniem i adresem (Str. Maramures, bl. C19, ap. 6, 200024). Istnieje Luca Cristian PFA w Sibiu (handel tekstylny/obuwie) — ale inna osoba. **EXCLUDE — brak potwierdzenia**
- **Răzvan Anghene** (Focșani) — **polityk AUR**, **były dyrektor OTP Bank Focșani**, członek CA CUP SA Vrancea. **EXCLUDE — to nie przedsiębiorca**

#### Duplikaty (scalić z istniejącymi)
- **Cotiga Marin** — to **administrator COTY SHOP INVEST S.R.L.** (CUI 48715727, J40/16278/2023, Sector 4). Nr tel. +40723019747 = ten sam co na fakturze prywatnej admina. **EXCLUDE (scal z RO-A-009)**

### 🔢 NIP / CUI — weryfikacja rozbieżności

#### COTY SHOP INVEST — POTWIERDZONE
- **Foto:** CUI `48831012`
- **Prawidłowy:** CUI `48715727` (J40/16278/2023, demoanaf.ro + datasrl.ro)
- **Cross-check (4 źródła):** datasrl.ro, demoanaf.ro, termene.ro, listafirme.ro — wszystkie potwierdzają **48715727**
- **48831012** — NIE istnieje w ONRC. Błąd pisowni przy przepisywaniu z faktury (transpozycja cyfr: 4883-1012 vs 4871-5727).
- **Decyzja:** Prawidłowy CUI = **48715727** → duplikat `RO-A-009` (już FROZEN)

#### BLK TRADE MARKET — POTWIERDZONE
- **Foto:** CUI `40694700`
- **Prawidłowy:** CUI `40638971` (J22/855/2019, Iași)
- **Cross-check (5 źródeł):** termene.ro, listafirme.ro, targetare.ro, eMAG.ro, firmealert.ro — wszystkie potwierdzają **40638971**
- **40694700** — NIE istnieje w ONRC. Różnica 55771 cyfr — błąd OCR przy przepisywaniu.
- **Decyzja:** Prawidłowy CUI = **40638971** → nowy lead ACTIVE (e-commerce CAEN 4791)

#### Cotiga Marin (osoba) — POTWIERDZONE
- **Foto:** brak NIP
- **Prawidłowa interpretacja:** administrator COTY SHOP INVEST (CUI 48715727, Sector 4) + rolnik z Asociația crescătorilor de animale
- **Decyzja:** **EXCLUDE (scal z RO-A-009)** — to osoba prywatna-administrator, nie firma. Faktura prywatna wystawiona przez admina.

#### Cotiga Monica PFA (CUI 37030493) — POWIĄZANIE RODZINNE
- **Odkrycie:** istnieje Cotiga Monica PFA (CUI 37030493, Sector 3, București) — czy to żona COTIGĂ MARIN?
- **Wartość:** jeśli tak — możliwy **dual business** (mąż hurtownia + żona PFA detaliczny). Do follow-up przy uzupełnianiu `RO-A-009`.

### 🌐 ANALIZA SIECIOWA — kto z kim

#### Wspólne adresy (virtual office pattern)
- **Švabinského 1700/4, 702 00 Ostrava-Moravská Ostrava** (adres Hosting time):
  - Hosting time s.r.o. (IČO 04302231) — Monika Dąbkowska (PL)
  - ACCOUNT NEW CORPORATE CZ a.s. (IČO 28616715)
  - TOKMO GLOBAL s.r.o. (IČO 03077161)
  - Scrap Leader s.r.o. (IČO 04124715)
  - CZECH SOLVATO s.r.o. (IČO 03051315)
  - JBB Franchise s.r.o. (IČO 08945080) — gastron
  - Flex Step s.r.o. (IČO 04011111) — v likvidaci
  - DESOFT s.r.o. (IČO 08204098)
  - → **9 firm pod jednym adresem = virtual office dla polskich shell companies. NIE dla BILLS.**

#### Sieci OREA HOTELS (20+ hoteli w CZ)
- Praha (OREA Hotel Pyramida, 340 pokoi), Brno (OREA Congress Hotel), Šumava, Jeseniky, Beskydy, ...
- **NIE lead** (brak zakupów hurtowych kuřáckých potřeb; hotele mają własne umowy z BAT/JTI/PMI)
- **Wniosek:** jeśli kiedyś wejdziemy w segment hoteli (np. dla klientów biznesowych), OREA to kanał — ale obecnie ICP nie pasuje

### 📊 Finalna decyzja — zaktualizowany status

| # | Firma | Poprzednia decyzja | Nowa decyzja | Uzasadnienie |
|---|---|---|---|---|
| 1 | Eva Machačná (CZ 44560176) | EXCLUDE | **ACTIVE → B4** | CZ-NACE: Maloobchod s převahou potravin, nápojů a tabákových výrobků |
| 2 | OREA HOTELS s.r.o. | EXCLUDE | EXCLUDE (potwierdzone) | 20+ hoteli, ale brak śladu zakupów hurtowych kuřácké potřeby |
| 3 | Hosting time s.r.o. | EXCLUDE | EXCLUDE (potwierdzone) | Velkoobchod license, ale virtual office pattern + obca właścicielka |
| 4 | Zasen Trade Invest SRL | EXCLUDE | EXCLUDE (potwierdzone) | Restaurante CAEN 5610, błędny adres |
| 5 | ARTHEK Machines SRL | EXCLUDE | EXCLUDE (potwierdzone) | CAEN 3314 serwis, nie dystrybutor |
| 6 | DIPA CONCEPT SRL | EXCLUDE | EXCLUDE (potwierdzone) | Inactiva/ radiata od 26.02.2026 |
| 7 | Jana Zelezna | EXCLUDE | EXCLUDE | Brak IČO, brak śladu |
| 8 | Iveta Burešová | EXCLUDE | EXCLUDE | Tożsamość niepotwierdzona (3 różne Iveta Burešová w CZ) |
| 9 | Hana Sretrova | EXCLUDE | EXCLUDE | Mgr. Hana Šretrová istnieje, ale w Luhačovice, nie Bílina; poradenství+textil |
| 10 | Luca Cristian Lucian | EXCLUDE | EXCLUDE | Brak potwierdzenia (istnieje inny Luca Cristian PFA w Sibiu — handel tekstylny) |
| 11 | Răzvan Anghene | EXCLUDE | EXCLUDE | Polityk AUR, były dyrektor OTP Bank |
| 12 | Cerbu Ioana | EXCLUDE | EXCLUDE | Administrator GRAND PRODUCT SRL (mobilier, suspendowana) |
| 13 | Cotiga Marin | EXCLUDE | EXCLUDE (scal z RO-A-009) | Administrator COTY SHOP INVEST |

### 📁 Pliki zaktualizowane
- `data/verification/2026-08-24-photo-list-deep-audit.md` (ten plik)
- `tools/pdf_photo_verification.py` — zaktualizować status Eva Machačná na ACTIVE
- `data/audit-log.md` — wpisać wynik deep re-verification
- `data/_intake/CZ/source.csv` — dodać Eva Machačná jako nowy lead B4