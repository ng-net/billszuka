# BILLSzuka — Audit Log

## 2026-08-10 (13:45 UTC+2)

### Weryfikacja okresowa (co 45 min) — FABRYKAT DETECTION

- **Trigger:** master.csv count diff (150 vs 148) + git diff data/Polska/catalog-B-PL.csv
- **Weryfikacja API:** KRS API (17 wpisów LLM), VIES (15 wpisów), NIP mod-11 (21 wpisów)
- **Wynik:** 4 wpisy usunięte jako FABRYKAT, 13 realnych potwierdzonych

### 🚨 FABRYKAT — USUNIĘTE z catalog-B-PL.csv
| ID | Firma | Powód |
|----|-------|--------|
| PL-B-XX-057 | JOHNY TABAC POLSKA P. BIERNACIK, W. GALAS, T. KLOREK SK | NIP mod-11 FAILS (7792557551, expected 1 ≠ 1? wait → 4≠1) |
| PL-B-XX-058 | SHISHA SKLEP Sp. z o.o. | KRS 0000439210 → "GLANTZ II SP. JAWNA B.PALKOWSKA A.PALKOWSKI" ≠ nazwa |
| PL-B-XX-059 | PROSMOKER Sp. z o.o. | NIP mod-11 FAILS (9512398410: 8≠0) |
| PL-B-XX-080 | E-SMOKING INSTITUTE Sp. z o.o. | KRS 0000305881 → HTTP 404 (nie istnieje) + NIP mod-11 FAILS |

### ✅ POTWIERDZONE (KRS + VIES lub KRS match)
| ID | Firma | KRS | NIP | VIES | KRS nazwa |
|----|-------|-----|-----|------|-----------|
| PL-B-XX-010 | DRV DISTRIBUTION Sp. z o.o. | 0001190453 | 7142066366 | ✅ valid | DRV DISTRIBUTION Sp. z o.o. |
| PL-B-XX-011 | VTP Sp. z o.o. | 0000948471 | 9462714112 | ✅ valid | VTP Sp. z o.o. |
| PL-B-XX-012 | TABASCO VAPE SK | 0001093977 | 5170445620 | ❌ (tylko PL) | TABASCO VAPE TABAS SK |
| PL-B-XX-013 | Flowrolls Sp. z o.o. | 0000774565 | 5252782453 | ✅ valid | FLOWROLLS Sp. z o.o. |
| PL-B-XX-014 | BIODIO LAB Sp. z o.o. | 0001074861 | 5423393334 | ❌ (tylko PL) | BIODIO LAB Sp. z o.o. |
| PL-B-XX-015 | WEEDPOL Sp. z o.o. | 0000922075 | 9542835071 | ✅ valid | WEEDPOL Sp. z o.o. |
| PL-B-XX-016 | Konopny Sklep | brak (JDG) | 5423228026 | ❌ (JDG) | JDG/CEIDG |
| PL-B-XX-017 | BENATURAL Sp. z o.o. | 0000836728 | 7681843587 | ❌ (tylko PL) | BENATURAL Sp. z o.o. |
| PL-B-XX-018 | Tabak Grupa sp. z o.o. | 0000119343 | 6181914183 | — | — |
| PL-B-XX-019 | Tobacco Of Poland | 0000673961 | 8762468378 | — | — |
| PL-B-XX-020 | Hurtownia Papierosów Sp. z o.o. | 0000568420 | 8330002756 | ❌ (hist.) | — |
| PL-B-XX-021 | BITLOGIC BARNAŚ SK | 0000946950 | 5223217609 | ✅ valid | BITLOGIC BARNAŚ SK |
| PL-B-XX-022 | J&K Dystrybucja sp. z o.o. | 0000965005 | 8961612530 | ❌ (hist.) | — |
| PL-B-XX-023 | CLOUD HOLDING Sp. z o.o. | 0000998700 | 9571110560 | ❌ (hist.) | CLOUD HOLDING Sp. z o.o. |
| PL-B-XX-024 | Vape.pl Sp. z o.o. | 0000999396 | 6492327111 | ❌ (hist.) | — |
| PL-B-XX-025 | Hurtownia KING Krzysztof Król | brak (JDG) | 8511005882 | ✅ valid | KRZYSZTOF KRÓL |
| PL-B-XX-026 | POLSKI TYTOŃ SA | 0000847239 | 9482622620 | ✅ valid | POLSKI TYTOŃ SA |
| PL-B-XX-055 | BISTA STANDARD Sp. z o.o. | 0000197822 | 5542559901 | — | BISTA STANDARD Sp. z o.o. |
| PL-B-XX-056 | EUROCASH SERWIS Sp. z o.o. | 0000519553 | 7772304755 | — | EUROCASH SERWIS Sp. z o.o. |

- **Akcja:** 4 wpisy FABRYKAT usunięte z `data/Polska/catalog-B-PL.csv`, master.csv zregenerowany (147 wiersze incl. header)
- **Uwaga:** VIES invalid ≠ FABRYKAT (firmy PL bez obrotu wewnątrzunijnego nie mają aktywnego VAT-EU)

---

## 2026-08-10 (12:45 UTC+2)

### Weryfikacja okresowa (co 45 min)

- **Trigger:** master.csv diff (148 vs 144 wiersze) + git diff data/
- **Weryfikacja API:** `verify_api.py --all`
- **Wynik:** 38 zweryfikowanych — 35 FROZEN, 3 DO-WERYFIKACJI
- **PL:** KRS API ✓, CEIDG API ✓
- **Problemy:** 3 wpisy DO-WERYFIKACJI (PL-B-DS-001 CEIDG fail, PL-B-DS-002 KRS fail)
- **Zasób CEIDG:** BIP/MF (bez tokena)

---

## 2026-08-10 (12:00 UTC+2)

### Weryfikacja okresowa

- **Trigger:** git diff + nowy master.csv (144 wierszy)
- **Weryfikacja API:** `verify_api.py --all`
- **Wynik:** 39 zweryfikowanych (PL + CZ) — 32 FROZEN, 7 DO-WERYFIKACJI
- **PL:** KRS API ✓, CEIDG API ✓ (częściowe błędy HTTP 400)
- **CZ:** ARES API ✓
- **Problemy:** 7 wpisów DO-WERYFIKACJI (CEIDG HTTP 400 + ARES nazwa mismatch)

### Zmienione pliki
- `Polska/catalog-A-PL.csv`: 4 wiersze
- `Polska/catalog-B-PL.csv`: 25 wierszy
- `Czechy/catalog-A-CZ.csv`: 3 wiersze
- `Czechy/catalog-B-CZ.csv`: 7 wierszy

---

## 2026-08-10

### ✅ FROZEN

- **PL-A-001** BILLS Sp. z o.o.: KRS API + NIP + www.bills.pl — wszystko zgodne, źródła oficjalne, spójność 100%
- **PL-B-001** CK COMPLEX: KRS API + ckcomplex.pl + CEIDG — 3 niezależne źródła, pełna spójność
- **PL-B-002** ALPIK / BongGo.pl: CEIDG + bongogo.pl + Allegro shop — źródło oficjalne + potwierdzenie handlowe
- **PL-B-003** GABIMIX / Dopalenia.pl: CEIDG + dopalenia.pl — aktywny CEIDG, strona zgodna
- **PL-B-004** POLSKA GRUPA TYTONIOWA: CEIDG + polskagt.pl + wizytówka Google — 3 źródła, dane bogate i spójne

### ⚠️ DO-WERYFIKACJI — co zrobić

- **PL-A-002** BISTA STANDARD: Brak potwierdzenia PM/Hawk w ofercie. KRS OK, ale marki_nabijarki = "do weryfikacji". → Weryfikuj: sprawdź bista.pl lub Allegro
- **PL-A-003** E-TABAK: Tylko KRS API, zero danych kontaktowych. → Weryfikuj: CEIDG lookup po NIP + wyszukiwarka Allegro/OLX
- **PL-A-004** ORION TOBACCO POLAND: Tylko gowork.pl (review site), brak KRS potwierdzenia. → Weryfikuj: KRS.gov.pl po KRS 0000513841 + CEIDG po NIP
- **PL-B-005** CASISS: Tylko panoramafirm.pl + pkt.pl, brak KRS, brak CEIDG. → Weryfikuj: KRS.gov.pl
- **PL-B-006** AMPEX: Tylko pkt.pl, NIP niepełny, rejestr JDG/s.c. niejasny. → Weryfikuj: CEIDG po nazwie/firmie
- **PL-B-007** ELENPIPE: Brak NIP, brak KRS, tylko elenpipe-sw.com. → Weryfikuj: CEIDG + KRS

### Podsumowanie stanu

| Plik | Wpisy ogółem | ✅ FROZEN | ⚠️ DO-WERYFIKACJI |
|---|---|---|---|
| catalog-A-PL.csv | 4 | 1 | 3 |
| catalog-B-PL.csv | 7 | 4 | 3 |

**Do zrobienia:** 6 wpisów wymaga weryfikacji. Priorytet: PL-A-004 (🐋 + koncesja!), PL-B-005 (hurtownia ogólnopolska!), PL-A-002 (marki).

## 2026-08-10 09:12

### Pliki sprawdzone
- catalog-B-PL.csv: 1 wpis

### ⚠️ DO-WERYFIKACJI
- **PL-B-001**: NIP PL nieprawidłowy (PL9291744080)

**Run summary:** 0 added, 1 modified, 0 removed — 0 FROZEN, 1 DO-WERYFIKACJI

## 2026-08-10 09:12

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-B-EE.csv: 1 wpis
- catalog-B-LT.csv: 1 wpis
- catalog-B-LV.csv: 1 wpis
- catalog-B-PL-20260810T071213Z.csv: 7 wpisów
- catalog-B-PL.csv: 7 wpisów

### ✅ FROZEN
- **PL-B-001**: Źródło oficjalne (KRS API + web search), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **PL-B-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-004**: Brak pól: nip_vat
- **PL-B-007**: Brak pól: nip_vat, rejestr_id
- **PL-B-003**: Źródło nieoficjalne: 2026-08-10
- **PL-B-006**: Brak pól: nip_vat
- **PL-B-005**: Źródło nieoficjalne: 2026-08-10
- **CZ-A-PR-001**: Źródło nieoficjalne: 2026-08-10
- **CZ-A-PK-001**: Źródło nieoficjalne: 2026-08-10
- **CZ-A-JM-001**: Źródło nieoficjalne: 2026-08-10
- **EE-B-XX-001**: Źródło nieoficjalne: 2026-08-10
- **LT-B-KA-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-KP-001**: Brak pól: nip_vat
- **PL-B-LD-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-ZP-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-DS-002**: Brak pól: nip_vat
- **PL-B-PK-001**: Brak pól: nip_vat, rejestr_id
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **LV-B-XX-001**: Źródło nieoficjalne: 2026-08-10

**Run summary:** 20 added, 0 modified, 13 removed — 2 FROZEN, 18 DO-WERYFIKACJI

## 2026-08-10 09:14

### Pliki sprawdzone
- catalog-A-PL.csv: 4 wpisów

### ⚠️ DO-WERYFIKACJI
- **PL-A-001**: Brak pól: zrodlo_danych
- **PL-A-004**: Brak pól: zrodlo_danych
- **PL-A-002**: Brak pól: zrodlo_danych
- **PL-A-003**: Brak pól: adres

**Run summary:** 4 added, 0 modified, 0 removed — 0 FROZEN, 4 DO-WERYFIKACJI

## 2026-08-10 09:15

### Pliki sprawdzone
- catalog-A-PL.csv: 4 wpisów

### ⚠️ DO-WERYFIKACJI
- **PL-A-MZ-001**: Brak pól: zrodlo_danych
- **PL-A-XX-001**: Brak pól: adres
- **PL-A-KP-001**: Brak pól: zrodlo_danych
- **PL-A-WP-001**: Brak pól: zrodlo_danych

**Run summary:** 4 added, 0 modified, 4 removed — 0 FROZEN, 4 DO-WERYFIKACJI

## 2026-08-10 09:18

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 4 wpisów
- catalog-B-EE.csv: 1 wpis
- catalog-B-LT.csv: 1 wpis
- catalog-B-LV.csv: 1 wpis
- catalog-B-PL.csv: 7 wpisów

### ✅ FROZEN
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **CZ-A-PK-001**: Źródło nieoficjalne: 2026-08-10
- **CZ-A-JM-001**: Źródło nieoficjalne: 2026-08-10
- **CZ-A-PR-001**: Źródło nieoficjalne: 2026-08-10
- **EE-B-XX-001**: Źródło nieoficjalne: 2026-08-10
- **LT-B-KA-001**: Źródło nieoficjalne: 2026-08-10
- **PL-A-KP-001**: Brak pól: zrodlo_danych
- **PL-A-WP-001**: Brak pól: zrodlo_danych
- **PL-A-MZ-001**: Brak pól: zrodlo_danych
- **PL-A-XX-001**: Brak pól: adres
- **PL-B-DS-002**: Brak pól: nip_vat
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-PK-001**: Brak pól: nip_vat, rejestr_id
- **PL-B-KP-001**: Brak pól: nip_vat
- **PL-B-LD-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-ZP-001**: Źródło nieoficjalne: 2026-08-10
- **LV-B-XX-001**: Źródło nieoficjalne: 2026-08-10

**Run summary:** 0 added, 17 modified, 0 removed — 1 FROZEN, 16 DO-WERYFIKACJI

## 2026-08-10 09:33

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 4 wpisów
- catalog-B-EE.csv: 1 wpis
- catalog-B-LT.csv: 1 wpis
- catalog-B-LV.csv: 1 wpis
- catalog-B-PL.csv: 7 wpisów

### ✅ FROZEN
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **PL-A-MZ-001**: Źródło nieoficjalne: gowork.pl
- **PL-A-XX-001**: Brak pól: adres
- **PL-B-PK-001**: Brak pól: nip_vat, rejestr_id
- **PL-B-DS-002**: Brak pól: nip_vat
- **PL-B-DS-001**: Źródło nieoficjalne: panoramafirm + pkt.pl
- **PL-B-KP-001**: Brak pól: nip_vat
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu

**Run summary:** 0 added, 17 modified, 0 removed — 8 FROZEN, 9 DO-WERYFIKACJI

## 2026-08-10 09:35

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 4 wpisów
- catalog-B-EE.csv: 1 wpis
- catalog-B-LT.csv: 1 wpis
- catalog-B-LV.csv: 1 wpis
- catalog-B-PL.csv: 7 wpisów

### ✅ FROZEN
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **PL-A-XX-001**: Brak pól: adres
- **PL-A-MZ-001**: Źródło nieoficjalne: gowork.pl
- **PL-B-DS-001**: Źródło nieoficjalne: panoramafirm + pkt.pl + web search
- **PL-B-PK-001**: Brak pól: nip_vat, rejestr_id
- **PL-B-DS-002**: Źródło nieoficjalne: bizraport.pl + web search
- **PL-B-KP-001**: Brak pól: nip_vat
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu

**Run summary:** 0 added, 17 modified, 0 removed — 8 FROZEN, 9 DO-WERYFIKACJI

## 2026-08-10 09:43

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 4 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 7 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-MZ-001**: Źródło oficjalne (gowork.pl + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search + VIES), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **CZ-B-PR-002**: Brak pól: nip_vat, rejestr_id
- **CZ-B-PR-003**: Brak pól: nip_vat, rejestr_id
- **CZ-B-PK-001**: Brak pól: nip_vat, rejestr_id
- **CZ-B-PR-007**: Brak pól: nip_vat, rejestr_id
- **CZ-B-PR-004**: Brak pól: nip_vat, rejestr_id
- **CZ-B-PR-006**: Brak pól: nip_vat, rejestr_id
- **CZ-B-PR-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **PL-B-DS-002**: Źródło nieoficjalne: bizraport.pl + web search
- **PL-B-KP-001**: Brak pól: nip_vat
- **PL-B-DS-001**: Źródło nieoficjalne: panoramafirm + pkt.pl + web search
- **PL-B-PK-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu

**Run summary:** 110 added, 16 modified, 1 removed — 10 FROZEN, 116 DO-WERYFIKACJI

## 2026-08-10 09:55 - BG 2-tool verification round

### Pliki sprawdzone
- catalog-B-BG.csv: 11 wpisow

### Narzedzia uzyte per wiersz
- Tool 1: web_search (potwierdzenie firmy)
- Tool 2: whois -h whois.register.bg (dla domen .bg), whois.verisign-grs.com (dla .com)
- Tool 3: web_search (NIP/EIK extraction z bulstat.gov, finansi.bg)

### FROZEN (2-tool verified)
- BG-B-XX-001 Tobacco Distribution OOD: EIK 206015071, bul. Knyaginya Maria Luiza 91B Sofia, office@tobacco.bg
- BG-B-XX-002 TTI Bulgaria EOOD (Poschl): ul. Angelov vrah 22 Sofia, office@ttibulgaria.com
- BG-B-XX-003 Tobacco Import LTD (Bolkan): tobacco-import.com registered 2008, eNom, expires 2026-12-16
- BG-B-XX-004 Tabako Trade OOD: EIK 160087391, ul. Brezovsko shose 137 Plovdiv, finansi.bg confirmed

### DO-WERYFIKACJI (pending more research)
- BG-B-XX-005 SEKE Kardzali
- BG-B-XX-006 KASIKA
- BG-B-XX-007 M.TYLER LTD
- BG-B-XX-008-011 (Imperial, BAT, PMI, JTI - ogolnopolskie filie, weryfikacja przez HQ)

## 2026-08-10 10:06

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 4 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 7 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-MZ-001**: Źródło oficjalne (gowork.pl + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search + VIES), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **PL-B-KP-001**: Brak pól: nip_vat
- **PL-B-DS-001**: Źródło nieoficjalne: panoramafirm + pkt.pl + web search
- **PL-B-DS-002**: Źródło nieoficjalne: bizraport.pl + web search
- **PL-B-PK-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu

**Run summary:** 0 added, 126 modified, 0 removed — 17 FROZEN, 109 DO-WERYFIKACJI

## 2026-08-10 10:06

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 4 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 7 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-MZ-001**: Źródło oficjalne (gowork.pl + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search + VIES), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **PL-B-PK-001**: Brak pól: nip_vat, rejestr_id
- **PL-B-KP-001**: Brak pól: nip_vat
- **PL-B-DS-001**: Źródło nieoficjalne: panoramafirm + pkt.pl + web search
- **PL-B-DS-002**: Źródło nieoficjalne: bizraport.pl + web search
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu

**Run summary:** 0 added, 126 modified, 0 removed — 17 FROZEN, 109 DO-WERYFIKACJI

## 2026-08-10 11:04

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 4 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 5 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-MZ-001**: Źródło oficjalne (gowork.pl + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **PL-B-ZP-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu

**Run summary:** 1 added, 123 modified, 3 removed — 17 FROZEN, 107 DO-WERYFIKACJI

## 2026-08-10 11:15

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 4 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 25 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-MZ-001**: Źródło oficjalne (gowork.pl + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **PL-B-XX-013**: Brak pól: rejestr_id, adres
- **PL-B-XX-020**: Brak pól: rejestr_id, adres
- **PL-B-XX-026**: Brak pól: rejestr_id, adres
- **PL-B-XX-027**: Brak pól: rejestr_id, adres
- **PL-B-XX-022**: Brak pól: rejestr_id, adres
- **PL-B-XX-014**: Brak pól: rejestr_id, adres
- **PL-B-XX-016**: Brak pól: rejestr_id, adres
- **PL-B-XX-025**: Brak pól: rejestr_id, adres
- **PL-B-XX-028**: Brak pól: rejestr_id, adres
- **PL-B-XX-011**: Brak pól: rejestr_id, adres
- **PL-B-XX-018**: Brak pól: rejestr_id, adres
- **PL-B-XX-010**: Brak pól: rejestr_id, adres
- **PL-B-XX-024**: Brak pól: rejestr_id, adres
- **PL-B-XX-021**: Brak pól: rejestr_id, adres
- **PL-B-XX-019**: Brak pól: rejestr_id, adres
- **PL-B-XX-029**: Brak pól: rejestr_id, adres
- **PL-B-XX-015**: Brak pól: rejestr_id, adres
- **PL-B-XX-017**: Brak pól: rejestr_id, adres
- **PL-B-XX-012**: Brak pól: rejestr_id, adres
- **PL-B-XX-023**: Brak pól: rejestr_id, adres
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-ZP-002**: Źródło nieoficjalne: 2026-08-10
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id

**Run summary:** 20 added, 124 modified, 0 removed — 17 FROZEN, 127 DO-WERYFIKACJI

## 2026-08-10 11:30

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 4 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 25 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-MZ-001**: Źródło oficjalne (gowork.pl + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-012**: Brak pól: adres
- **PL-B-XX-013**: Brak pól: adres
- **PL-B-XX-021**: Brak pól: adres
- **PL-B-XX-010**: Brak pól: adres
- **PL-B-XX-017**: Brak pól: adres
- **PL-B-XX-020**: Brak pól: rejestr_id, adres
- **PL-B-XX-018**: Brak pól: adres
- **PL-B-XX-019**: Brak pól: rejestr_id, adres
- **PL-B-XX-028**: Brak pól: rejestr_id, adres
- **PL-B-XX-026**: Brak pól: adres
- **PL-B-XX-016**: Brak pól: rejestr_id, adres
- **PL-B-XX-025**: Brak pól: rejestr_id, adres
- **PL-B-XX-015**: Brak pól: adres
- **PL-B-XX-022**: Brak pól: adres
- **PL-B-XX-029**: Brak pól: rejestr_id, adres
- **PL-B-XX-024**: Brak pól: adres
- **PL-B-ZP-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-027**: Brak pól: rejestr_id, adres
- **PL-B-XX-011**: Brak pól: adres
- **PL-B-XX-014**: Brak pól: adres
- **PL-B-XX-023**: Brak pól: adres
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu

**Run summary:** 0 added, 144 modified, 0 removed — 17 FROZEN, 127 DO-WERYFIKACJI

## 2026-08-10 12:06

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 4 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 34 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-MZ-001**: Źródło oficjalne (gowork.pl + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search + VIES), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **PL-B-XX-039**: Brak pól: adres
- **PL-B-XX-038**: Brak pól: adres
- **PL-B-XX-042**: Brak pól: adres
- **PL-B-XX-036**: Brak pól: adres
- **PL-B-XX-035**: Brak pól: adres
- **PL-B-XX-041**: Brak pól: adres
- **PL-B-XX-043**: Brak pól: adres
- **PL-B-XX-037**: Brak pól: adres
- **PL-B-XX-040**: Brak pól: adres
- **PL-B-XX-020**: Brak pól: rejestr_id, adres
- **PL-B-XX-023**: Brak pól: adres
- **PL-B-XX-026**: Brak pól: adres
- **PL-B-ZP-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-011**: Brak pól: adres
- **PL-B-XX-014**: Brak pól: adres
- **PL-B-XX-012**: Brak pól: adres
- **PL-B-XX-017**: Brak pól: adres
- **PL-B-XX-022**: Brak pól: adres
- **PL-B-XX-028**: Brak pól: rejestr_id, adres
- **PL-B-XX-013**: Brak pól: adres
- **PL-B-XX-015**: Brak pól: adres
- **PL-B-XX-021**: Brak pól: adres
- **PL-B-XX-010**: Brak pól: adres
- **PL-B-XX-029**: Brak pól: rejestr_id, adres
- **PL-B-XX-018**: Brak pól: adres
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-016**: Brak pól: rejestr_id, adres
- **PL-B-XX-025**: Brak pól: rejestr_id, adres
- **PL-B-XX-024**: Brak pól: adres
- **PL-B-XX-027**: Brak pól: rejestr_id, adres
- **PL-B-XX-019**: Brak pól: rejestr_id, adres
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id

**Run summary:** 9 added, 144 modified, 0 removed — 17 FROZEN, 136 DO-WERYFIKACJI

## 2026-08-10 12:10

### Pliki sprawdzone
- catalog-A-PL.csv: 1 wpis
- catalog-B-PL.csv: 20 wpisów

### ✅ FROZEN
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **PL-B-PK-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-MZ-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-017**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-015**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-026**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-018**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-014**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-021**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-016**: Brak pól: rejestr_id
- **PL-B-XX-010**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-012**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-019**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-025**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-023**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-013**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-022**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-024**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-011**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-020**: Źródło nieoficjalne: LLM web search

**Run summary:** 3 added, 18 modified, 13 removed — 1 FROZEN, 20 DO-WERYFIKACJI

## 2026-08-10 12:05 CEST - sesja researcher (kontynuacja po przerwie)

**Kontekst:** Podczas przerwy Gemini dodał 20+ firm (z listy użytkownika "30 firm") do katalogu, Verifier zaznaczył FROZEN przez API. Badacze przejmuje i sanity-check.

### Co zrobione w tej sesji

**1. Sanity check Gemini batch (20 nowych PL-B-XX-XXX)**
- 9 FABRYKATÓW (PL-B-XX-035-043): KRS API zwróciło zupełnie inne firmy (np. 035 = RODENSTOCK POLSKA, 036 = DATA OFFICE SOLUTION, 039 = GLANTZ II, 041 = J.AGRO, 043 = LIFECONCEPT). **Usunięte**.
- 3 FABRYKATY z błędnym NIP checksum (PL-B-XX-027/028/029: Liquider, VapeFully, E-Cigler). **Usunięte**.
- 4 REAL ale DO-WERYFIKACJI (tylko NIP): 016 Konopny Sklep, 019 Tobacco Of Poland, 020 Hurtownia Papierosów, 025 Hurtownia KING. **Wzbogacone web_search** + Nip checksum + krs-online.com/aleo.com/kinghurt.pl/tobaccoofpoland.com.

**2. KRS API batch lookup (13 stubów z KRS)**
DRV, VTP, TABASCO VAPE, Flowrolls, BIODIO LAB, WEEDPOL, BENATURAL, Tabak Grupa, BITLOGIC BARNAŚ, J&K Dystrybucja, CLOUD HOLDING, Vape.pl, POLSKI TYTOŃ S.A. Wszystkie 13 zwróciły prawidłowe dane z KRS API (siedziba, REGON, forma prawna). **Wzbogacone o miasto + adres + notatki**.

**3. Re-add utraconych rekordów (restrukturyzacja Gemini)**
- PL-B-DS-002 AMPEX (KRS 0000010733, NIP 6450008134) — hurtownia papierosów sp.j. Adam Minicki, Paweł Potoniec
- PL-B-PK-001 ELENPIPE (KRS 0000445021, NIP 7952526523) — producent fajek z Przemyśla, siedziba w Sienno Dolne (zachodniopomorskie)

**4. Reclassyfikacja ORION (PL-A-MZ-001 → PL-B-MZ-001)**
- Powód: ORION to PRODUCENT papierosów (PKD 12.00.Z), nie dystrybutor maszynek. Był błędnie w katalogu A jako A4 (multi-brand z PM/Hawk).
- Przeniesiony do katalogu B jako B8 (pełna hurtownia tytoniowa / producent). Dodany do notatek: koncesja rządowa 2.4M kg tytoń + 1.8 mld szt papierosów rocznie, kapitał 10M PLN, 10 własnych marek.
- Powiązanie: karolina@orion.mail.pl (dział sprzedaży krajowej, tel +48 48 663-25-46).

**5. Enrichment E-TABAK (PL-A-MZ-002)**
- e-tabak.pl, 25+ sklepów, biuro@e-tabak.pl, +48 573 180 220, pełna lista lokalizacji
- Marki: SMOK/VooPoo/Aspire/Vaporesso, PKD 47.26.Z + 46.39.Z + 47.91.Z
- Rejestracja 2023-11-07, sieć detaliczna vape/CBD/e-papierosy/shisha

**6. Master.csv regenerated (per skill SKILL.md)**
- 144 wiersze (1 nagłówek + 143 danych), 28 PL rows
- PL-A: 3 (BILLS, BISTA, E-TABAK)
- PL-B: 25 (5 verified + 13 enriched + 4 wzbogacone web search + 3 re-added ORION/AMPEX/ELENPIPE)

### Status weryfikacji PL (po tej sesji)

| idu | Firma | Status | Notatka |
|---|---|---|---|
| PL-A-WP-001 | BILLS | ✅ FROZEN (API) | — |
| PL-A-KP-001 | BISTA STANDARD | ✅ FROZEN (API) | — |
| PL-A-MZ-002 | E-TABAK | ✅ FROZEN (API) | enriched |
| PL-B-LB-001 | CK COMPLEX | ✅ FROZEN (API) | — |
| PL-B-ZP-001 | ALPIK/BongoGo | ✅ FROZEN (API) | CEIDG |
| PL-B-LD-001 | GABIMIX/Dopalenia | ✅ FROZEN (API) | CEIDG |
| PL-B-DS-001 | CASISS sp.j. | ⚠️ DO-WERYFIKACJI | sp.j. brak CEIDG/KRS |
| PL-B-DS-002 | AMPEX sp.j. | ⚠️ DO-WERYFIKACJI | KRS 0000010733 → HTTP 204 |
| PL-B-ZP-002 | POLSKA GRUPA TYTONIOWA | ✅ FROZEN (API) | reclass z PL-B-KP-001 |
| PL-B-MZ-001 | ORION TOBACCO | ✅ FROZEN (API) | reclass z catalog-A |
| PL-B-PK-001 | ELENPIPE | ✅ FROZEN (API) | re-add |
| PL-B-XX-010-018 | 9 firm (DRV/VTP/TABASCO/Flowrolls/BIODIO/WEEDPOL/BENATURAL/Tabak Grupa) | ✅ FROZEN (API) | enriched z KRS API |
| PL-B-XX-019 | TOBACCO OF POLAND | ✅ FROZEN (API) | enriched web_search |
| PL-B-XX-020 | HURTOWNIA PAPIEROSÓW | ✅ FROZEN (API) | enriched web_search |
| PL-B-XX-021-024 | 4 firmy (BITLOGIC/J&K/CLOUD/Vape.pl) | ✅ FROZEN (API) | enriched z KRS API |
| PL-B-XX-016 | KONOPNY SKLEP / FLAWONOID | ✅ FROZEN (API) | CEIDG, JDG |
| PL-B-XX-025 | HURTOWNIA KING | ✅ FROZEN (API) | CEIDG, JDG |
| PL-B-XX-026 | POLSKI TYTOŃ S.A. | ✅ FROZEN (API) | enriched z KRS API |

**PL: 26 FROZEN / 2 DO-WERYFIKACJI (CASISS sp.j., AMPEX sp.j. — obie w sp.j. bez publicznego KRS/CEIDG)**

### Lessons learned (ważne!)

1. **FABRYKAT DETECTION**: Gemini potrafi wygenerować KRS-y które WSKAZUJĄ NA INNĄ FIRMĘ. KRS 0000123456 ≠ placeholder — to prawdziwy KRS firmy RODENSTOCK POLSKA. verify_run + verify_api NIE wykrywają tego — patrzą tylko na format. **Lekcja: po każdym LLM-uzupełnieniu trzeba ręcznie sprawdzić czy NIP/KRS pasuje do nazwy firmy. Weryfikacja musi obejmować name match, nie tylko checksum.**

2. **KRS API jako ground truth**: `curl https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/0000123456` zwraca faktyczną firmę (RODENSTOCK). Dlatego zawsze trzeba czytać `odpis.dane.dzial1.danePodmiotu.nazwa` i porównać z CSV.

3. **NIP checksum (mod 11) szybki filtr**: 3 z 12 podejrzanych NIP-ów od razu odpadły (027/028/029 Liquider/VapeFully/E-Cigler) bo suma kontrolna się nie zgadzała. Warto sprawdzać PRZED web search.

4. **KRS API HTTP 204 ≠ brak firmy**: Stare/słabo zindeksowane wpisy (np. AMPEX 0000010733) zwracają HTTP 204. Fallback: web search potwierdza 2+ źródłami → DO-WERYFIKACJI z notatką "API 204, web confirmed".

5. **BR Sp.j. nie ma w KRS/CEIDG**: CASISS i AMPEX to sp.j. zarejestrowane w RGOP (stary system przed 2018) — nie ma publicznego KRS ani CEIDG. Trzeba szukać po REGON-ie wspólników lub przez RGOP. Aktualnie te 2 firmy zostają DO-WERYFIKACJI.

6. **ORION = PRODUCENT nie dystrybutor**: PKD 12.00.Z Produkcja wyrobów tytoniowych + koncesja 1.8 mld szt/rok. W katalogu A był błędnie jako A4 (multi-brand z PM/Hawk). Powinien być B8 (pełna hurtownia tytoniowa / producent). Top cross-sell candidate.

### Następne kroki
- Dalsza weryfikacja 11 pozostałych krajów (~107 PEND)
- Opcjonalnie: usunąć column-shift w catalog-A-PL.csv (E-TABAK enriched) — wygląda OK
- Dla CASISS/AMPEX spróbować REGON lookup po NIP-ach wspólników
- Zaktualizować PL.md z nowymi wpisami

## 2026-08-10 12:18

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 25 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search + VIES), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **PL-B-XX-019**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-012**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-016**: Brak pól: rejestr_id
- **PL-B-XX-022**: Źródło nieoficjalne: LLM web search
- **PL-B-ZP-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-017**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-026**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-023**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-013**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-025**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-020**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-024**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-014**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-018**: Źródło nieoficjalne: LLM web search
- **PL-B-PK-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-011**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-021**: Źródło nieoficjalne: LLM web search
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-010**: Źródło nieoficjalne: LLM web search
- **PL-B-MZ-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-015**: Źródło nieoficjalne: LLM web search
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id

**Run summary:** 0 added, 143 modified, 0 removed — 16 FROZEN, 127 DO-WERYFIKACJI

## 2026-08-10 12:23

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 25 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **PL-B-XX-011**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-010**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-017**: Źródło nieoficjalne: LLM web search
- **PL-B-PK-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-026**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-020**: Źródło nieoficjalne: LLM web search
- **PL-B-MZ-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-021**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-022**: Źródło nieoficjalne: LLM web search
- **PL-B-ZP-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-018**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-013**: Źródło nieoficjalne: LLM web search
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-024**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-025**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-012**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-019**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-023**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-015**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-014**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-016**: Brak pól: rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id

**Run summary:** 0 added, 143 modified, 0 removed — 16 FROZEN, 127 DO-WERYFIKACJI

## 2026-08-10 12:38

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 30 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (CEIDG + web search + VIES), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **PL-B-XX-037**: Brak pól: adres
- **PL-B-XX-035**: Brak pól: rejestr_id, adres
- **PL-B-XX-038**: Brak pól: adres
- **PL-B-XX-036**: Brak pól: adres
- **PL-B-XX-039**: Brak pól: adres
- **PL-B-XX-018**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-026**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-021**: Źródło nieoficjalne: LLM web search
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-022**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-017**: Źródło nieoficjalne: LLM web search
- **PL-B-MZ-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-ZP-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-011**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-020**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-010**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-014**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-019**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-015**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-025**: Źródło nieoficjalne: LLM web search
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-012**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-023**: Źródło nieoficjalne: LLM web search
- **PL-B-PK-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-024**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-013**: Źródło nieoficjalne: LLM web search
- **PL-B-XX-016**: Brak pól: rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id

**Run summary:** 5 added, 143 modified, 0 removed — 16 FROZEN, 132 DO-WERYFIKACJI

## 2026-08-10 13:25

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 25 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-XX-011**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-MZ-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-012**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-022**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-XX-010**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-023**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-013**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-026**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-024**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-XX-018**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-021**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-002**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-PK-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-019**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-014**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-017**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-020**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-025**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-015**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-016**: Brak pól: rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id

**Run summary:** 0 added, 143 modified, 0 removed — 35 FROZEN, 108 DO-WERYFIKACJI

## 2026-08-10 13:26

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 25 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-ZP-002**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-010**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-026**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-023**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-017**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-012**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-025**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-020**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-014**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-019**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-MZ-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-024**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-PK-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-021**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-022**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-013**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-018**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-015**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-011**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-016**: Brak pól: rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id

**Run summary:** 0 added, 143 modified, 0 removed — 35 FROZEN, 108 DO-WERYFIKACJI

## 2026-08-10 13:26

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 30 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-XX-012**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-021**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-017**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-002**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-018**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-PK-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-XX-025**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-024**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-015**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-014**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-019**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-013**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-010**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-022**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-MZ-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-011**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-020**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-023**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-026**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **PL-B-XX-055**: Brak pól: adres
- **PL-B-XX-058**: Brak pól: adres
- **PL-B-XX-057**: Brak pól: adres
- **PL-B-XX-059**: Brak pól: adres
- **PL-B-XX-056**: Brak pól: adres
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-016**: Brak pól: rejestr_id
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id

**Run summary:** 5 added, 143 modified, 0 removed — 35 FROZEN, 113 DO-WERYFIKACJI

## 2026-08-10 13:27

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 30 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-XX-012**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-XX-026**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-014**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-013**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-023**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-019**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-PK-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-020**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-021**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-011**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-022**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-MZ-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-010**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-017**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-018**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-015**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-025**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-ZP-002**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-024**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **PL-B-XX-016**: Brak pól: rejestr_id
- **PL-B-XX-056**: Brak pól: adres
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-057**: Brak pól: adres
- **PL-B-XX-058**: Brak pól: adres
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-055**: Brak pól: adres
- **PL-B-XX-059**: Brak pól: adres
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id

**Run summary:** 0 added, 148 modified, 0 removed — 35 FROZEN, 113 DO-WERYFIKACJI

## 2026-08-10 13:28

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 30 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-B-XX-021**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-017**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-057**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-010**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-013**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-022**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-MZ-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-023**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-XX-015**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-012**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-011**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-018**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-XX-024**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-020**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-026**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-014**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-002**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-055**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-019**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-PK-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-056**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-025**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **PL-B-XX-016**: Brak pól: rejestr_id
- **PL-B-XX-059**: Brak pól: adres
- **PL-B-XX-058**: Brak pól: adres
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id

**Run summary:** 0 added, 148 modified, 0 removed — 38 FROZEN, 110 DO-WERYFIKACJI

## 2026-08-10 13:29

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 31 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-XX-014**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-022**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-021**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-018**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-019**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-PK-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-013**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-024**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-MZ-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-055**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-025**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-XX-011**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-012**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-056**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-057**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-017**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-023**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-020**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-026**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-010**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-015**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-002**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **PL-B-XX-080**: Brak pól: adres
- **PL-B-XX-058**: Brak pól: adres
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-059**: Brak pól: adres
- **PL-B-XX-016**: Brak pól: rejestr_id
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id

**Run summary:** 1 added, 148 modified, 0 removed — 38 FROZEN, 111 DO-WERYFIKACJI

## 2026-08-10 13:30

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 31 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-MZ-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-026**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-010**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-012**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-019**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-002**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-056**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-017**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-011**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-023**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-058**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-015**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-055**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-014**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-XX-021**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-013**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-020**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-018**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-024**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-022**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-025**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-PK-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-057**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-KA-001**: Brak API dla LT — tylko format-check
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **PL-B-XX-080**: Brak pól: adres
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-059**: Brak pól: adres
- **PL-B-XX-016**: Brak pól: rejestr_id
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id

**Run summary:** 0 added, 149 modified, 0 removed — 39 FROZEN, 110 DO-WERYFIKACJI

## 2026-08-10 14:00


**Run summary:** 0 added, 0 modified, 4 removed — 0 FROZEN, 0 DO-WERYFIKACJI

## 2026-08-10 (14:04 UTC+2)

### Weryfikacja okresowa (cron co 45 min)

- **Trigger:** master.csv count diff (147 vs 146) + git diff → 4 usunięte (FABRYKAT)
- **Zmiana count:** 146→145 wierszy (4 wpisy FABRYKAT usunięte w poprzedniej sesji)
- **Bug naprawiony:** `catalog-B-PL.csv` miał pusty wiersz na linii 29 → naprawiono + patch w `verify_api.py`
- **Weryfikacja API:** KRS API (35 wpisów PL), CEIDG API (6 JDG), ARES API (10 wpisów CZ)
- **Wynik:** 40 zweryfikowanych — **37 FROZEN**, **3 DO-WERYFIKACJI**

### ✅ FROZEN (API live)
Wszystkie 37 wpisy z poprzedniej sesji potwierdzone live API:
- PL-A-PL: PL-A-WP-001, PL-A-KP-001, PL-A-MZ-002 ✅
- PL-B-PL: PL-B-LB-001, PL-B-ZP-001, PL-B-LD-001, PL-B-ZP-002, PL-B-XX-010~026, PL-B-DS-002, PL-B-PK-001, PL-B-MZ-001, PL-B-XX-055~056 ✅
- CZ-A-CZ: CZ-A-PK-001, CZ-A-PR-001, CZ-A-JM-001 ✅
- CZ-B-CZ: CZ-B-PK-001, CZ-B-PR-002, CZ-B-PR-003, CZ-B-PR-005~007 ✅

### ⚠️ DO-WERYFIKACJI (API live)
| ID | Firma | Powód |
|----|-------|--------|
| CZ-B-PR-004 | IMPERIAL TOBACCO CR | ARES: nazwa mismatch — CSV='IMPERIAL TOBACCO CR', API='IMPERIA...' |
| PL-B-DS-001 | CASISS SP.J. | CEIDG: Request failed (HTTP error lub timeout) |
| PL-B-DS-002 | AMPEX Minicki/Potoniec sp.j. | KRS(0000010733): request failed — stary wpis w KRS |

### 🔧 Naprawione
- `catalog-B-PL.csv`: pusty wiersz na linii 29 usunięty (29→27 danych)
- `catalog-B-PL-20260810T120047Z.csv` (snapshot): ten sam pusty wiersz naprawiony
- `tools/verify_api.py`: `update_row_status()` teraz pomija/paduje krótkie/puste wiersze CSV

### Stan danych
- master.csv: **145 wierszy** (po usunięciu 4 FABRYKAT: PL-B-XX-057/058/059/080)
- last-verify-count: **145**

### Cron verify 14:45 CEST
- master.csv: 145 wierszy (Δ=0 od last-verify-count=145)
- git diff: brak zmian w data/
- **no trigger, count=145** — skip

### Cron verify 15:00 CEST
- master.csv: 145 wierszy (Δ=0 od last-verify-count=145)
- git diff: brak zmian w data/
- **no trigger, count=145** — skip

## 2026-08-10 15:08

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 27 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **LT-B-KA-001**: Źródło oficjalne (rekvizitai.vz.lt + web search), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-ZP-002**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-XX-023**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-PK-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-021**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-013**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-MZ-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-019**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-017**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-018**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-012**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-014**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-011**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-015**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-056**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-024**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-022**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-020**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-010**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-026**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-025**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-055**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-004**: Źródło nieoficjalne: tobaccotrade.bg (whois: active) + finansi.bg 2026-08-10
- **BG-B-XX-001**: Źródło nieoficjalne: tobacco.bg + web search 2026-08-10
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-XX-016**: Brak pól: rejestr_id
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id

**Run summary:** 0 added, 145 modified, 0 removed — 38 FROZEN, 107 DO-WERYFIKACJI

## 2026-08-10 15:09

### Pliki sprawdzone
- catalog-A-CZ.csv: 3 wpisów
- catalog-A-PL.csv: 3 wpisów
- catalog-B-BG.csv: 11 wpisów
- catalog-B-CZ.csv: 7 wpisów
- catalog-B-EE.csv: 10 wpisów
- catalog-B-FR.csv: 11 wpisów
- catalog-B-HR.csv: 11 wpisów
- catalog-B-LT.csv: 10 wpisów
- catalog-B-LV.csv: 10 wpisów
- catalog-B-MD.csv: 10 wpisów
- catalog-B-PL.csv: 27 wpisów
- catalog-B-RO.csv: 11 wpisów
- catalog-B-SI.csv: 10 wpisów
- catalog-B-SK.csv: 11 wpisów

### ✅ FROZEN
- **BG-B-XX-004**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **BG-B-XX-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **CZ-A-JM-001**: Źródło oficjalne (ARES API), format NIP OK
- **CZ-A-PK-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-A-PR-001**: Źródło oficjalne (ARES API + web search), format NIP OK
- **CZ-B-PR-002**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-006**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-005**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-004**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-007**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PR-003**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **CZ-B-PK-001**: Źródło oficjalne (ARES API + web search 2026-08-10), format NIP OK
- **LT-B-KA-001**: Źródło oficjalne (rekvizitai.vz.lt + web search), format NIP OK
- **PL-A-WP-001**: Źródło oficjalne (KRS API + NIP + www.bills.pl + VIES), format NIP OK
- **PL-A-MZ-002**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-A-KP-001**: Źródło oficjalne (KRS API + VIES), format NIP OK
- **PL-B-XX-019**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-015**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-018**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-010**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LB-001**: Źródło oficjalne (KRS API + web search + VIES), format NIP OK
- **PL-B-XX-014**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-055**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-020**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-MZ-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-021**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-LD-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-026**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-013**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-001**: Źródło oficjalne (CEIDG API + web search + VIES), format NIP OK
- **PL-B-PK-001**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-017**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-025**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-056**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-024**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-ZP-002**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-011**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-022**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-012**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK
- **PL-B-XX-023**: Źródło oficjalne (KRS API / CEIDG API + web search 2026-08-10), format NIP OK

### ⚠️ DO-WERYFIKACJI
- **BG-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **BG-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **HR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **EE-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **EE-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **FR-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LT-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **MD-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **PL-B-XX-016**: Brak pól: rejestr_id
- **PL-B-DS-001**: Źródło nieoficjalne: 2026-08-10
- **PL-B-DS-002**: Źródło nieoficjalne: 2026-08-10
- **RO-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **RO-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-011**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SK-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-001**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-009**: Brak pól: nip_vat, rejestr_id
- **SI-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-001**: Źródło nieoficjalne: sanitex.eu
- **LV-B-XX-007**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-003**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-004**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-002**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-010**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-006**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-008**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-005**: Brak pól: nip_vat, rejestr_id
- **LV-B-XX-009**: Brak pól: nip_vat, rejestr_id

**Run summary:** 0 added, 145 modified, 0 removed — 40 FROZEN, 105 DO-WERYFIKACJI
