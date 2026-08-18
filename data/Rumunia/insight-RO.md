# 🇷🇴 Rumunia — insight

> **Data:** 2026-08-18 | **Status katalogu:** ✅ ZWERYFIKOWANE (23 firmy w master) | **Decydent fill:** 17/23 (74%)

## Szybkie fakty
- **Populacja:** 19M | **Palacze:** ~28% | **Status:** EU
- **Reżim regulacyjny — RYZYKO WYSOKIE:** plain packaging od 2020, surowe ograniczenia smakowe dla e-papierosów, silne lobby antynikotynowe
- **Rejestr:** CUI / CIF / **ONRC** https://www.onrc.ro / **ANAF** https://www.anaf.ro
- **Duży rynek, ale regulacje trudne** — może wymagać osobnej strategii

## Top firmy (z master.csv, FROZEN 2026-08-18)

### Tier hurtownik / e-com 🐋
| ID | Firma | Co robi | Decydent |
|---|---|---|---|
| **RO-A-001** | **JPB TRADE SRL** | Hurt tytoniowy | Silviu Petrescu |
| **RO-A-002** | **TOBACCO TRADING INTERNATIONAL RO SRL** | Hurt (Pöschl group) | Bogdan Ciocarlan |
| **RO-A-003** | **GOLD STEAM GARDEN SRL (mtabac.ro)** | Hurt + e-com | Lukács Attila |
| **RO-A-004** | **SC GOLDEN TIP IMPORT EXPORT SRL (tuburipentrutigari.ro)** | Hurt + e-com maszynek | — |
| **RO-A-005** | **ELVAPO EXPRES SRL** | Dystrybutor | — |
| **RO-A-006** | **SORIN NECULACHE (Owner)** | Broker | Sorin Neculache (Owner) | ⚠️ LLM-hallucination REJ |
| **RO-A-007** | **Stefan-marius Lazar (Business Development Manager)** | Hurt | Stefan Lazar (Owner) | ⚠️ LLM-hallucination REJ |
| **RO-A-008** | **SC SIBIS CONCEPT COMPANY S.R.L. (etutun.ro)** | E-com RYO | — |
| **RO-A-009** | **SC SIBIS CONCEPT COMPANY S.R.L.** | (alias) | — |
| **RO-B-001** | **SENSIMARK CONSULT S.R.L. (magazintrabucuri.ro / tobacco-online.ro)** | Wiodąca platforma e-com RYO | — |
| **RO-B-002** | **SC LUXURYGIFTS SRL** | Hurt | — |
| **RO-B-003** | **INTERBRANDS ORBICO SRL** | FMCG/tytoń dystrybutor | — |
| **RO-B-004** | **RHENUS LOGISTICS SRL** | Logistyka | — |
| **RO-B-005** | CSABA FULOP (Chairman) | Hurt | CSABA FULOP (Chairman/Administrator) | ⚠️ LLM-hallucination REJ |
| **RO-B-012** | Ram Addanki (CEO) | BAT oddział | Ram Addanki (CEO) | ⚠️ LLM-hallucination REJ |
| **RO-B-015** | Adrian Neacsu (General Manager) | Hurt | Adrian Neacsu (GM) | ⚠️ LLM-hallucination REJ |

## Reżim regulacyjny — **RYZYKO WYSOKIE**
- **Plain packaging od 2020** — mocno ogranicza branding.
- **Surowe ograniczenia smakowe** dla e-papierosów.
- **Antynikotynowe lobby silne** — presja legislacyjna rosnąca.
- **Akcyza wysoka.**
- **CBD:** szara strefa, susz nielegalny.
- **Nabijarki: bez ograniczeń jako urządzenia.**

## Kanały dystrybucji
- **Marketplaces:** **eMAG** (Amazon regionu), OLX.ro (główny), Okazii.ro, Cel.ro
- **Specjalistyczne e-com:** tuburipentrutigari.ro, mtabac.ro, etutun.ro, magazintrabucuri.ro, tobacco-online.ro

## Cross-country ties
- **TTI RO** (RO-A-002) ↔ **TTI SK (SK-A-011) + TTI CZ (CZ-B-003) + TTI BG (BG-A-001)** — Pöschl group (austriacko-niemiecki koncern).
- **MD firmy importują przez RO** (bliskość językowa, kulturowa, logistyczna).
- **BAT România** (Ram Addanki) + **BAT Bulgaria** (Mila Marechkova) — ten sam koncern.

## Weryfikacja
- ✅ 23/23 firm FROZEN, ONRC zwalidowany.
- ✅ 17/23 decydentów zweryfikowanych.
- ⚠️ **5 decydentów RO oznaczonych "✗ REJ"** przez `_enrich_with_verify.py` — to LLM-hallucination odrzucone przez name-matching (FABRYKAT detection). Traktować jako **niezweryfikowane** dopóki nie potwierdzone w ONRC.

## Otwarte luki
- **5 decydentów RO wymaga ręcznej weryfikacji** (Sorin Neculache, Stefan Lazar, CSABA FULOP, Ram Addanki, Adrian Neacsu — wszystkie odrzucone przez weryfikator).
- 6× decydent DO-WERYFIKACJI (bez danych publicznych).
- **Czy są lokalne marki konkurencyjne?** — do zbadania (np. mtabac.ro to GOLD STEAM GARDEN, nie lokalny producent).
- Wysoki rynek szarej strefy — niektóre leady mogą być nieaktywne.

## Ryzyka / uwagi
- **Plain packaging** = trudny rynek dla marek własnych. Nacisk na **kanał B2B / hurt** zamiast retail brand.
- **Silne lobby antynikotynowe** = potencjalne zaostrzenie regulacji 2026-2027 (śledzić).
- **BAT/JTI/PMI obecne** = kanał oligopolowy.
- **TTI (Pöschl)** = niezależny import, szansa dla partnerstwa.

## Strategia RO
- Skupić się na **e-com specialistach** (tuburipentrutigari.ro, etutun.ro, magazintrabucuri.ro) — mniejsza ekspozycja na retail regulacyjny.
- TTI Romania = naturalny partner Pöschl group (cross-country B8+B9).
- Rumunia = rynek **duży ale trudny** — może wymagać **osobnej strategii** lub **partnera lokalnego** (eMAG seller agreement?).

## Źródła do dalszej pracy
- ONRC.onrc.ro — CUI lookup
- ANAF.anaf.ro — VAT + bilans
- eMAG sellers section — kto sprzedaje maszynki
- LinkedIn: "rolling machine Romania"
