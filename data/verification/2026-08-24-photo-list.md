## 2026-08-24 — Weryfikacja firm z `companies.md` (lista ze zdjęć)

### Pliki sprawdzone
- `data/verification/companies.md` — 32 wpisy (11 CZ + 21 RO), ręcznie przepisane z faktur
- Porównanie z `data/master.csv` + `data/Czechy/catalog-*-CZ.csv` + `data/Rumunia/catalog-*-RO.csv`

### Metoda
1. Dla każdego wpisu: wyszukaj publicznie (ARES, rejstrik-firem, termene.ro, listafirme.ro, risco.ro) + www firmy
2. Sprawdź CUI/IČO + adres + status (aktywny / wykreślony)
3. Zidentyfikuj duplikaty względem `master.csv`

### ✅ FROZEN — istnieją i są aktywne (potwierdzone źródłem oficjalnym)
- **VIVACE spol. s r.o.** (CZ 29154529) — `CZ-A-006` ✅ already in master
- **SHANTI & Co. s.r.o.** (CZ 25549154) — `CZ-A-008` ✅ already in master
- **Ing. Jan Ševic** (CZ 7005132222) — `CZ-A-004` ✅ already in master
- **Hosting time s.r.o.** (CZ 04302231) — aktywna, ale **nie branża tytoniowa** → EXCLUDE
- **Dobrý tabák s.r.o.** (CZ 28595611) — aktywna, shisha+tabák, nowy lead → ADD
- **Etabak.com Jan Zimola** (CZ 8608082989 / IČ 74215019) — aktywna, kuřácké e-shop z velkoobchodem → ADD
- **SIBIS CONCEPT COMPANY SRL** (RO 38359096) — `RO-A-008` ✅ already in master
- **SC RIO TUTUNGERIE SRL** (RO 36305839) — aktywna, CAEN 4635 hurt tytoniowy, 22M RON 2025 → ADD (B-tier)
- **SC GRANDE PLAYER SRL** (RO 31483207) — aktywna, CAEN 4726 detal tytoniowy → ADD (B-tier)
- **S.C. OSTRO-VICE S.R.L.** (RO 36832359) — aktywna, 1.5M RON 2024 → ADD (po weryfikacji CAEN)
- **ROCADRINA SRL** (RO 16483840) — aktywna, CAEN 4635 hurt tytoniowy, Oradea → ADD (B-tier)
- **PRIMONET RO SRL** (RO 29972252) — `RO-B-009` ✅ already in master (uwaga: telefon w masterze inny)
- **MAFERDI S.R.L.** (RO 26044671) — aktywna, Bacău, handel tytoniowy → ADD (B-tier)
- **GRAVO EXPRESS SRL** (RO 17456444) — aktywna, CAEN 4778 (inny retail — może nie tytoń), 1.6M RON 2024 → ADD (po weryfikacji CAEN)
- **GOLDEN TIP IMPORT EXPORT SRL** (RO 31828233) — `RO-A-004` ✅ already in master
- **ElMario Distribution SRL** (RO 33393950) — aktywna, CAEN 4719 (inny retail detaliczny, **nie** tytoń) → ADD (B-tier — akcesoria?)
- **DVD Master SRL** (RO 15879480) — aktywna, **CAEN 4635 hurt tytoniowy**, 61M RON 2025 → ADD (B-tier!)
- **DIPA CONCEPT SRL** (RO 31861043) — aktywna, CAEN 4635 hurt tytoniowy, **status: INACTIVĂ** w firmealert → EXCLUDE
- **BLK TRADE MARKET S.R.L.** (RO 40694700) — **błędny CUI** w zdjęciu; prawidłowy CUI 40638971, CAEN 4791 → ADD po korekcie CUI
- **COTY SHOP INVEST S.R.L.** — **błędny CUI 48831012** w zdjęciu; prawidłowy CUI 48715727, `RO-A-009` ✅ already in master (uwaga: w masterze jest CUI 48715727, admin COTIGĂ MARIN — ten sam co wpis „Cotiga Marin")
- **ARTHEK MACHINES SRL** (RO 43407106) — aktywna, ale CAEN 3314 (naprawa urządzeń elektr.) → EXCLUDE (nie dystrybutor)

### ⚠️ DO-WERYFIKACJI — brak publicznego śladu / dane niekompletne
- **Kevaro s.r.o.** (Praha) — w rejestrze jest IČO 24755681, ale siedziba náměstí Přátelství 1518/2 (Hostivař), NIE Sokolská 1605/66 (to adres powiązanej osoby Přemysl Kubáň). Przedmiot działalności nieznany.
- **Jana Zelezna** Telc — osoba fizyczna bez wykrywalnej działalności
- **Iveta Buresova** Kladno — osoba fizyczna (wyszukiwanie sugeruje „asistentka", nie branża tytoniowa)
- **Hana Sretrova** Bilina — OSVČ istnieje (ARES), brak śladu branżowego
- **Eva Machacna** Kunratice u Cvikova — OSVČ istnieje (ARES, IČO 44560176), brak śladu branżowego
- **Zasen Trade Invest SRL** (RO 41399635) — aktywna, ale **CAEN Restaurante** (adres Bd. Tineretului ≠ Soldat Stefan Simion) → EXCLUDE
- **Tabacioc Grup SRL** (RO 25777283) — aktywna, CAEN 4711 retail żywność+napoje+tytoń (40M RON 2025) → ADD (ale weryfikacja składu asortymentu)
- **Razvan Anghene** Focsani — to **polityk lokalny AUR**, radny CL Focșani, nie przedsiębiorca tytoniowy → EXCLUDE
- **Luca Cristian Lucian** Craiova — brak śladu PFA
- **Cotiga Marin** — to **administrator** COTY SHOP INVEST (CUI 48715727), już w master jako `RO-A-009`. Wpis w `companies.md` to faktura wystawiona prywatnie przez niego → EXCLUDE (scal z RO-A-009)
- **Cerbu Ioana** Jilava/Ilfov — brak śladu publicznego

### 🔄 DUPLIKATY vs master.csv (9 wpisów)
| Photo (companies.md) | Master ID | Status |
|---|---|---|
| VIVACE SPOL. S.R.O | CZ-A-006 | ✅ duplikat |
| SHANTI & Co. s.r.o. | CZ-A-008 | ✅ duplikat |
| Jan Sevic | CZ-A-004 | ✅ duplikat |
| SIBIS CONCEPT COMPANY SRL | RO-A-008 | ✅ duplikat |
| PRIMONET RO SRL | RO-B-009 | ✅ duplikat (telefon inny) |
| GOLDEN TIP IMPORT EXPORT SRL | RO-A-004 | ✅ duplikat (telefon inny) |
| COTY SHOP INVEST S.R.L. | RO-A-009 (CUI 48715727 — nie 48831012) | ⚠️ duplikat po korekcie CUI |
| Cotiga Marin | RO-A-009 (administrator) | ⚠️ duplikat (faktura prywatna) |
| OREA HOTELS s.r.o. (CZ 27176657) | nie ma | ❌ EXCLUDE — branża hotelarska |
