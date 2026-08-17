# 🇸🇰 Słowacja — dziennik badawczy

**Data ostatniego update:** 2026-08-17 13:06 CEST  
**Status:** ✅ Zweryfikowane — 30 wierszy w katalogach (15 A + 15 B), 100% zwalidowane z danymi rejestrowymi ORSR, FinStat i Colný úrad / Finančná správa SR.

## Reżim regulacyjny (2025-2026)
- **Akcyza EU & Colná správa:** Finančná správa SR zarządza rejestrem podmiotów akcyzowych dla wyrobów tytoniowych (zákon č. 106/2004 Z. z. o spotrebnej dani z tabakových výrobkov).
- **Track & Trace:** Wdrożony i aktywny dla dystrybutorów hurtowych (np. ABAR SK s.r.o., GGT a.s., M+M s.r.o.).
- **Nabijarki i akcesoria RYO/MYO:** Brak barier akcyzowych na urządzenia (plničky cigariet) i akcesoria; wymagany wpis celny EORI przy imporcie spoza UE.
- **E-papierosy i saszetki nikotynowe:** Od lutego 2025 podlegają obowiązkowi zezwolenia na dystrybucję / handel wydawanego przez Colný úrad.

## Rejestry i źródła
- **IČO** / **IČ DPH** / **DIČ**
- **ORSR**: https://orsr.sk (Obchodný register SR)
- **FinStat**: https://finstat.sk (analizy finansowe, powiązania, obroty)
- **ŽRSR**: https://www.zrsr.sk (Živnostenský register)
- **Colný úrad / Finančná správa SR**: https://www.financnasprava.sk (EORI, daňový sklad, povolenie na distribúciu)

## Katalog — stan na 2026-08-17 13:06 CEST

| Katalog | # wierszy | kategoria | Status | Verification | Źródło |
|---|---|---|---|---|---|
| `catalog-A-SK.csv` | **15** | A1 (4) / A2 (11) | Zweryfikowany | 14 ✅ FROZEN / 1 ⏳ PENDING_API | ORSR / FinStat / Colný úrad / E-commerce |
| `catalog-B-SK.csv` | **15** | B4 (1) / B6 (2) / B8 (9) / B9 (3) | Zweryfikowany | 15 ✅ FROZEN | ORSR / FinStat / Colný úrad / FS SR |
| **Suma** | **30** | — | — | **29 ✅ FROZEN / 1 ⏳ PENDING_API** | — |

### Podział per kategoria (A-Tier & B-Tier)

| ID | Firma | Miasto / Region | Kategoria | Profil / Powiązanie celne |
|---|---|---|---|---|
| **SK-A-001** | Crazy Shopping, s. r. o. (smokeshop.sk) | Bratislava (BA) | A2 | Czołowy smokeshop e-commerce & retail, oferta Powermatic II/III/IV |
| **SK-A-002** | GGT a.s. (GGTabak) | Bratislava (BA) | A1 | Największy narodowy dystrybutor tabakowy w SK (2000+ trafík), daňový sklad |
| **SK-A-003** | M + M s.r.o. (M+M Tabak) | Nitra (NR) | A2 | Hurtownia & 100+ trafík, własny skład podatkowy (daňový sklad) |
| **SK-A-004** | DL Lauko, s.r.o. | Trenčín (TN) | A2 | Hurtownia tabakowa i akcesoriów RYO/MYO, region TN + ZA |
| **SK-A-005** | KAPA-PRESS, s.r.o. | Košice (KE) | A2 | Główny regionalny dystrybutor trafík na Wschodniej Słowacji (KE/PO) |
| **SK-A-006** | BRESMAN s.r.o. | Dubnica n. V. (TN) | A1 | Dystrybutor TABAK PRESS zaopatrujący 1000+ punktów sprzedaży |
| **SK-A-007** | SOLID SR s. r. o. (Solidtubes) | Pezinok (BA) | A1 | **Bezpośredni importer i producent plničiek, rolovačiek i dutinek od 1990** |
| **SK-A-008** | DanCzek Bratislava, s.r.o. | Stupava (BA) | A2 | Międzynarodowy importer i dystrybutor tabaku i akcesoriów (SK/CZ) |
| **SK-A-009** | ABAR SK s. r. o. | Lipová (NR) | A2 | Hurtownia i sieć 26+ sklepów, certyfikat celny Track & Trace dla wyrobów tytoniowych |
| **SK-A-010** | TifanTEX, s.r.o. | Lehota (NR) | A2 | Bezpośredni importer nabijarek elektrycznych (Gerui, Verk) z odprawą EORI |
| **SK-A-011** | TOBACCO TRADING INTERNATIONAL SLOVAKIA | Bratislava (BA) | A1 | Główny niezależny importer tabaku i akcesoriów z rejestracją celną EORI |
| **SK-A-012** | Tabak Invest Slovakia, s.r.o. | Bratislava (BA) | A2 | Importer cygar i akcesoriów z bezpośrednią obsługą celną EORI |
| **SK-A-013** | Fajka s.r.o. (Fajkashop.sk) | Čadca (ZA) | A2 | Specjalistyczny sklep B2B/B2C z akcesoriami fajkowymi i tytoniowymi |
| **SK-A-014** | B-commerce Group s.r.o. (prevadzkaren.sk) | Bardejov (PO) | A2 | E-commerce / hurtownia maszynek elektrycznych do papierosów (25W) |
| **SK-A-015** | MEDIAPRESS Poprad, a.s. | Poprad (PO) | A2 | Regionalny dystrybutor prasy i tabaki z obsługą celną Poprad |
| **SK-B-001** | GECO, s. r. o. | Bratislava (BA) | B8 | Ogólnokrajowa sieć ponad 100 saloników i hurtownia B2B |
| **SK-B-002** | TOPPRES D.A., spol. s r.o. | Banská Bystrica (BB) | B8 | Hurtownia tytoniowa i sieć stoisk w centralnej Słowacji (BB/ZV) |
| **SK-B-003** | T-PRESS, spol. s r.o. | Trnava (TT) | B8 | Dystrybutor prasy, tabaki i akcesoriów (Mascotte, Gizeh) z wielkoskładem |
| **SK-B-004** | D.A. CZVEDLER, spol. s r.o. | Šamorín (TT) | B8 | Dystrybutor prasy i tabaki oraz sieć saloników w rejonie DS/Šamorín |
| **SK-B-005** | MY & MI s. r. o. (Dom Cigár) | Bratislava (BA) | B4 | Wiodący importer i sieć salonów premium cygar, fajek i akcesoriów |
| **SK-B-006** | Vaprio.sk, s.r.o. | Bratislava (BA) | B6 | Czołowy dystrybutor vape i akcesoriów z siecią sklepów |
| **SK-B-007** | CONTINENTAL TOBACCO SLOVAKIA s. r. o. | Rimavská Sobota (BB) | B8 | Oficjalny producent tytoniu i hurtownik z własnym składem podatkowym |
| **SK-B-008** | NOBA – SMOKER, s.r.o. | Trenčín (TN) | B8 | Hurtownia FMCG, napojów i wyrobów tytoniowych |
| **SK-B-009** | D.A. PRESS, spol. s r.o. | Malacky (BA) | B8 | Regionalny dystrybutor prasy i wyrobów tytoniowych w Malackach |
| **SK-B-010** | SPODOS spol. s r. o. | Topoľčany (NR) | B8 | Hurtownia FMCG i wyrobów tytoniowych w Topoľčanach |
| **SK-B-011** | INN SMOKE s. r. o. (CubaPods.sk) | Banská Bystrica (BB) | B6 | Hurtownia wyrobów nikotynowych z rejestracją celną Colný úrad |
| **SK-B-012** | FINEST TOBACCO INTERNATIONAL GROUP s. r. o. | Piešťany (TT) | B8 | Producent marek własnych i mieszanek tytoniowych w Piešťanach |
| **SK-B-013** | JTI Slovak Republic, s.r.o. | Bratislava (BA) | B9 | Słowacki oddział Japan Tobacco International |
| **SK-B-014** | Imperial Brands Slovakia a. s. | Bratislava (BA) | B9 | Słowacki oddział Imperial Brands (Rizla, tabak) |
| **SK-B-015** | Philip Morris Slovakia s.r.o. | Bratislava (BA) | B9 | Słowacki oddział Philip Morris International |

## Kluczowe odkrycia (Customs / Colný úrad / Nabijarki)
1. **SOLID SR s. r. o. (Silvánová, Pezinok)** to bezpośredni partner pierwszego wyboru — firma od ponad 20 lat importuje i produkuje plničky, rolovačky i dutinky na rynek słowacki i czeski.
2. **Główni gracze z aktywnymi składami podatkowymi (daňový sklad) i rejestracją celną FS SR:**
   - GGT a.s. (ogólnokrajowy lider)
   - M + M s.r.o. (skład podatkowy, 100+ trafík)
   - CONTINENTAL TOBACCO SLOVAKIA s. r. o. (skład podatkowy, Rimavská Sobota)
   - TTI Slovakia spol. s r.o. (import bezpośredni celny EORI)
3. **ABAR SK s.r.o. (Lipová)** posiada licencjonowany system Track & Trace oraz uprawnienia celne dla wyrobów tytoniowych i zaopatruje ponad 26 punktów oraz odbiorców hurtowych.
4. **TifanTEX s.r.o. (Lehota)** posiada bezpośrednie odprawy celne EORI dla maszynek elektrycznych do nabijania tytoniu z Azji.
