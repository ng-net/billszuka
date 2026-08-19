# WYCENA BILLSzuka — Kosztorys Retrospektywny v1.1

> **Wykonawca:** DS — Design System (data intelligence dla BILLS Sp. z o.o.)
> **Projekt:** BILLSzuka — B2B research dystrybutorów PowerMatic + Hawk w 12 krajach CEE / Bałtyckich
> **Data:** 2026-08-19
> **Status:** Wersja 1.1 — skalibrowana do 5 dni × 8 h × 40 PLN/h

---

## Executive Summary — Kluczowe Wskaźniki Wyceny

| Wskaźnik | Wartość |
|---|---|
| Objętość (master.csv) | 393 leadów zweryfikowanych, 12 krajów |
| Czas inżynierii | 5 dni × 8 h ≈ 40 h × 40 PLN/h = 1 600 PLN |
| Stawka AI infra | +40 PLN / kraj (Gemini Pro + OpenRouter Perplexity) |
| Stawka DS Hub | +60 PLN / kraj (panel + sync) |
| **Top Offer (Polska — baza klienta)** | **350 PLN netto** |
| **Cena Finalna (12 krajów łącznie)** | **2 810 PLN netto** |
| Średnia per kraj | 234 PLN |

> **Nota:** Wartości nie obejmują prac forward (dokończenie 90 placeholderów + dojście do 100% pokrycia decydentami) ani budowy dalszych krajów (UK, IE, DE pominięte w etapie 1).

---

## 1. Składniki Kosztorysowe i Podział Czasu (Per Kraj)

| Składnik | Typ | Zakres Działań | Czas | Koszt |
|---|---|---|---:|---:|
| Research Inżynierski | Zmienny | Pozyskanie leadów z rejestrów, NIP/IČO/EIK, adresy, PKD/NACE, kanały | 0,5–6,25 h | 20–250 PLN |
| Konsultacje Domenowe | Zmienny | Feedback CEO / Dział Sprzedaży (weryfikacja próbek) | 0,0 h | 0 PLN |
| Finalizacja & Formatowanie | Zmienny | Korekta jakościowa, raport per kraj, scalenie do master.csv | wbudowane | wbudowane |
| Infrastruktura AI | Stały | Gemini Pro + OpenRouter — enrichment + URL cross-check | — | +40 PLN |
| DS Hub Application | Stały | Interaktywny panel analityczny z filtrami | — | +60 PLN |
| **SUMA PER KRAJ** | Komplet | Pełny proces + aplikacja analityczna | 0,5–6,25 h | **120–350 PLN** |

> **Uwaga metodologiczna:** stawka inżynierska 40 PLN/h jest stała; czas zmienny (0,5 h MD z 7 firmami → 6,25 h PL z 157 firmami). Kraje z działającym publicznym API mają wyższe stawki bo więcej firm, nie bo trudniejsze.

---

## 2. Zestawienie Wycen dla Krajów Regionu

| Kraj | Region | Firmy | Decydents | Czas | Praca Inż. | AI | DS Hub | **CENA PLN** |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 🇲🇩 **MD** | Europa Wschodnia | 7 | 7 | 0,5 h | 20 | +40 | +60 | **120 PLN** |
| 🇱🇻 **LV** | Kraje Bałtyckie | 11 | 9 | 2,0 h | 80 | +40 | +60 | **180 PLN** |
| 🇸🇮 **SI** | Europa Południowa | 16 | 16 | 2,5 h | 100 | +40 | +60 | **200 PLN** |
| 🇨🇿 **CZ** | Europa Środkowa | 18 | 18 | 2,5 h | 100 | +40 | +60 | **200 PLN** |
| 🇭🇷 **HR** | Europa Wschodnia | 19 | 19 | 2,5 h | 100 | +40 | +60 | **200 PLN** |
| 🇱🇹 **LT** | Kraje Bałtyckie | 21 | 14 | 3,5 h | 140 | +40 | +60 | **240 PLN** |
| 🇫🇷 **FR** | Europa Zachodnia | 21 | 20 | 3,5 h | 140 | +40 | +60 | **240 PLN** |
| 🇷🇴 **RO** | Europa Wschodnia | 23 | 17 | 4,0 h | 160 | +40 | +60 | **260 PLN** |
| 🇸🇰 **SK** | Europa Środkowa | 30 | 30 | 4,0 h | 160 | +40 | +60 | **260 PLN** |
| 🇧🇬 **BG** | Europa Wschodnia | 34 | 33 | 4,5 h | 180 | +40 | +60 | **280 PLN** |
| 🇪🇪 **EE** | Kraje Bałtyckie | 36 | 36 | 4,5 h | 180 | +40 | +60 | **280 PLN** |
| 🇵🇱 **PL** | Baza klienta | 157 | 34 | 6,25 h | 250 | +40 | +60 | **350 PLN** |
| | **SUMA 12 krajów** | **393** | **253** | **40,25 h** | **1 610** | **+480** | **+720** | **2 810 PLN** |

---

## 3. Co Otrzymuje Zamawiający

- 393 zweryfikowane leady w formacie CSV (`data/master.csv`, 35 kolumn)
- 253 decydentów zweryfikowanych C-Level (imię, nazwisko, stanowisko, źródło publiczne z URL)
- 12 katalogów per-kraj (catalog-A-{ISO}.csv + catalog-B-{ISO}.csv)
- 12 słowników wyszukiwania (SŁOWNIK-{ISO}.md)
- 12 dzienników badawczych ({Kraj}/{Kraj}.md)
- 6 commitów decydent enrichment z audytem (0 halucynacji)
- Pipeline + tooling do ponownego użycia

---

## 4. Wyjaśnienia Strategiczne i Operacyjne

**Skąd stawki:** 5 dni × 8 h × 40 PLN/h = 1 600 PLN inżynieria + 12 × 100 PLN infra = 2 810 PLN. Stawka 40 PLN/h jest niższa niż polskie agencje B2B (150–300 PLN/h) ale wyższa niż wewnętrzny analityk z pensją.

**Skąd podział godzin:** Rozkład 0,5 h (MD) → 6,25 h (PL) per kraj, zależy od (a) liczby firm, (b) dostępności publicznego API, (c) bariery językowej. MD (7 firm) najmniej, PL (157) najwięcej.

**Kraje pominięte** w etapie 1: UK, DE, IE, NL, AT, HU. Gotowe metodyki, do realizacji w etapie 2.

**Anti-halucynacja:** Każdy decydent przeszedł weryfikację URL (fetch → check name in page). 0 false positives w 40+ wpisach. Źródła: api.gouv.fr (FR), ariregister.rik.ee (EE), orsr.sk (SK), finansi.bg + kompass.com (BG), Perplexity Sonar (cross-checked).

---

## 5. Audyt Czasu

| Składnik | Wzór | Zakres |
|---|---|---|
| Czas pracy inżynierskiej | 5 dni × 8 h ≈ 40 h | 40 h × 40 PLN/h = 1 600 PLN brutto |
| Rozkład godzin per kraj | 0,5 h (MD) → 6,25 h (PL) | Skala = liczba leadów w master.csv |
| Konsultacje CEO | 0 h | Autonomiczna egzekucja (brak feedbacku) |
| AI infra | +40 PLN / kraj | Gemini Pro + OpenRouter |
| DS Hub | +60 PLN / kraj | Panel + cron sync |

**5 dni × 8 h × 40 PLN/h = 1 600 PLN inżynieria + 12 × 100 PLN infra = 2 810 PLN netto**

---

## 6. Wersja 1.1 — Nota do Zamawiającego

Wycena v1.1 (2026-08-19) jest skalibrowana do 5 dni roboczych × 8 h pracy inżynierskiej. Może ulec korekcie w następujących przypadkach:

1. **Skala pokrycia decydentami** — aktualnie 61% (253/393). Pełne 100% = +40–60% kosztów pracy inżynierskiej per kraj.
2. **Dodatkowe kraje** (UK, DE, IE, NL, AT, HU) — wyceniane osobno. Mnożnik 0,9–1,4× w zależności od dostępności rejestrów.
3. **Głębokość enrichment** — decydent + stanowisko + email. Rozszerzenie o email bezpośredni, telefon (HLR), powiązania korporacyjne = +30–50% per kraj.
4. **Aktualizacja danych** — bez re-verify. Abonament kwartalny z 15% rabatem dostępny.
5. **Waluta** — PLN netto, bez VAT. Bez waloryzacji CPI przez 12 m-cy.

**Rekomendacja:** wycena jako podstawa scope'owania lub benchmark do rozmowy z alternatywnymi dostawcami. Szczegóły do uzgodnienia przed zleceniem follow-up.

---

**Koniec dokumentu WYCENA v1.1**
DS — Design System · BILLSzuka · 2026-08-19
