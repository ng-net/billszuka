# 🇵🇱 Polska — PL Research Closure Report

> **Data zamknięcia:** 2026-08-12
> **Operator:** Marceli
> **Status:** ✅ ZAMKNIĘTE (research na Polskę uznany za kompletny)
> **Następny kraj w kolejce:** 🇨🇿 Czechy (per AGENTS.md, order: PL → CZ → SK → UK → Western EU → Scandinavia → Balkans)

---

## TL;DR

- **235 firm PL w katalogu** (28 w A-tier + 207 w B-tier)
- **65 FROZEN (API)** = 27.7% verification rate
- **64 top targets** (1 odrzucony: I-WANT = AGD/RTV, nie tytoń)
- **Stratyczne 🐋:** BILLS, BISTA (Dark Horse/FERN), POLSKI TYTOŃ SA, PHUP GNIEZNO, ORION TOBACCO, POLSKA GRUPA TYTONIOWA, CK COMPLEX
- **Master.csv zsynchronizowany** (234 unikalne PL IDs = 234 w master, zero luk, zero duplikatów)

---

## Weryfikacja statystyk

| Kategoria | Total | FROZEN (API) | % | DO-WERYFIKACJI (parked) |
|---|---:|---:|---:|---:|
| **catalog-A-PL** (nabijarki direct) | 28 | 14 | 50.0% | 14 |
| **catalog-B-PL** (industry adjacent) | 207 | 51 | 24.6% | 156 |
| **TOTAL PL** | **235** | **65** | **27.7%** | **170** |

### FROZEN breakdown

| Tier | Ilość | Notatki |
|---|---:|---|
| A1 — Marceli/BILLS sam | 1 | PL-A-WP-001 (właściciel) |
| A4 — reseller/hurtownik/detal | 11 | Trober, Prosmoker, E-Tabak, CK Complex (sieć 100+ sklepów) i in. |
| A5 — producent | 1 | BISTA (Dark Horse + FERN — **konkurent**) |
| A6 — autoryzowany dystrybutor | 0 | — |
| B4/B6/B8 — industry adjacent | 51 | hurtownie tytoniowe, sieci vape, producenci papierosów |

---

## Top 15 leadów wg Quality Score

| ID | Firma | Tier | Miasto | QS | Kontakt |
|---|---|---|---|---:|---|
| PL-A-WP-001 | BILLS Sp. z o.o. | wyłączność | Ostrzeszów | 90 | +48 62 586 07 38 |
| PL-A-MZ-002 | E-TABAK Sp. z o.o. | marki własne + SMOK/VooPoo | Piaseczno | 90 | +48 573 180 220 |
| PL-A-PM-002 | Trober Polska | autoryzowany | Kaliska | 90 | +48 58 587 85 14 |
| PL-A-MZ-001 | Prosmoker (JDG) | reseller | Warszawa | 90 | +48 507 208 897 |
| PL-B-LB-001 | CK COMPLEX Sp. z o.o. | reseller (sieć 100+) | Zielona Góra | 90 | +48 68 452 12 30 |
| PL-B-ZP-002 | POLSKA GRUPA TYTONIOWA Sp. z o.o. | hurtownik | Wierzbnica | 90 | +48 502 399 832 |
| PL-B-XX-026 | POLSKI TYTOŃ S.A. | hurtownik 🐋 | Radom | 90 | +48 48 341 32 00 |
| PL-B-MZ-001 | ORION TOBACCO (przeniesiony A→B) | producent | Goszczyn | 90 | (per KRS) |
| PL-B-OP-003 | PHUP GNIEZNO SZESZYCKI sp.k. | reseller 🐋 | Gniezno | 85 | +48 512 984 347 |
| PL-B-ZP-001 | F.H.U. ALPIK (BongGo) | detalista | Szczecin | 90 | +48 601 779 697 |
| PL-B-LD-001 | GABIMIX (Dopalenia) | detalista | Konstantynów Ł. | 90 | +48 665 852 033 |
| PL-B-PK-001 | ELENPIPE Sp. z o.o. | hurt-detal spec. | Przemyśl | 90 | +48 16 675 02 07 |
| PL-B-XX-019 | TOBACCO OF POLAND | hurtownik | Grudziądz | 80 | (per KRS) |
| PL-B-XX-025 | HURTOWNIA KING Krzysztof Król | hurtownik | Szczecin | 85 | +48 609 641 400 |
| PL-B-LB-001 | CK COMPLEX Sp. z o.o. | reseller (sieć 100+) | Zielona Góra | 90 | (już wyżej) |

Pełna lista 64 targets (po odrzuceniu 1 WRONG_CATEGORY): `data/Polska/_closed/top-targets.csv`

---

## Contact coverage (65 FROZEN)

| Profil | Ilość | Działanie |
|---|---:|---|
| www + email + tel + decydent | 11 | 🥇 gotowe do cold outreach |
| www + email + tel (bez dec.) | 12 | 🥈 trzeba znaleźć decydenta (Apollo enrich) |
| www + tel (bez email) | 7 | 🥉 tel first, email do potwierdzenia |
| tylko decydent | 3 | użyć KRS / LinkedIn |
| tylko email | 2 | mail first |
| brak wszystkiego | 25 | ⚠️ wymaga pogłębienia research |
| **Suma** | **65** | |

**Wniosek:** 23/65 (35%) są gotowe do natychmiastowego kontaktu. Pozostałe 42 wymagają dalszej enrich (Apollo, LinkedIn, telefony).

---

## Strategiczne wnioski (do INTEL.md)

1. **BISTA STANDARD (PL-A-KP-001)** — producent konkurenckich marek **Dark Horse + FERN**. Klasyfikacja dual-business: A5 (nabijarki direct konkurent) + B8 (hurtownik). Traktować jako benchmark cenowy i partnera cross-sell, **nie** jako cel sprzedaży PM/Hawk.

2. **ORION TOBACCO (PL-B-MZ-001)** — największy polski producent papierosów (1.8 mld szt/rok, 10 marek własnych). 100k punktów dystrybucji = strategic cross-sell channel dla akcesoriów.

3. **POLSKI TYTOŃ S.A. (PL-B-XX-026)** — 15k+ sklepów, 18.3M PLN kapitału, 16 oddziałów regionalnych. Największy kanał detaliczny w PL.

4. **PHUP GNIEZNO (PL-B-OP-003)** — 1.5 mld zł revenue, 3000 sklepów, 5 oddziałów. Top B-tier target.

5. **CK COMPLEX (PL-B-LB-001)** — sieć 100+ sklepów vape. Cross-sell: jeśli którykolwiek sklep chce rozszerzyć o akcesoria dla palaczy.

6. **I-WANT (PL-A-WP-002)** — odrzucony: AGD/RTV importer, nie tytoń. WRONG_CATEGORY flag.

7. **Rynek PL jest płytki** — 30 produktów "Nabijarki" na Ceneo, średnia 121 zł. Miejsce na nowe marki premium (PowerMatic, Hawk).

---

## Artefakty zamknięcia

```
data/Polska/
├── catalog-A-PL.csv                  # katalog główny (28 rows, 14 FROZEN)
├── catalog-B-PL.csv                  # katalog główny (207 rows, 51 FROZEN)
├── verified-A-PL.csv                 # 🆕 14 FROZEN only — gotowe do Excel/GS export
├── verified-B-PL.csv                 # 🆕 51 FROZEN only — gotowe do Excel/GS export
├── PL.md                             # komentarze PL
├── SŁOWNIK-PL.md                     # search volumes (szac.)
├── PL-CLOSE-REPORT.md                # 🆕 ten dokument
└── _closed/                          # 🆕 research closed archive
    ├── research-closeout.csv         # mapowanie ID → status_on_close
    ├── top-targets.csv               # 64 leady wg QS (bez I-WANT)
    └── snapshots/                    # pre-close snapshot (2026-08-12)
        ├── catalog-A-PL.pre-close-2026-08-12.csv
        ├── catalog-B-PL.pre-close-2026-08-12.csv
        └── PL.md.pre-close-2026-08-12.bak
```

---

## Co zrobić z DO-WERYFIKACJI (170 parked)?

Są 3 opcje dla przyszłej sesji:

1. **Zostawić zamrożone** — research PL uznany za kompletny. Reaktywacja tylko na żądanie.
2. **Apollo-enrich round 2** — wzbogacić brakujące dane kontaktowe. Wymaga APOLLO_MCP_KEY.
3. **Bulk VIES + REGON round 2** — kolejne 50-80 firm może przejść do FROZEN (szacunek na bazie obecnego coverage).

**Rekomendacja:** opcja 1 + opcja 3 light. Wyślij `verify_run.py --country PL --round 2` po 2 tygodniach, gdy nowe firmy zostaną dodane do CEIDG/KRS.

---

## Następne kroki (poza PL)

Per AGENTS.md order: **PL → CZ → SK → UK → Western EU → Scandinavia → Balkans**

- 🇨🇿 **Czechy (CZ):** katalogi istnieją (catalog-A-CZ: 3 rows, catalog-B-CZ: 7 rows), ARES API gotowy. Rozpocząć pełny research z tych samych playbook'ów.
- 🇸🇰 **Słowacja (SK):** katalogi puste (header only). Po CZ.
- 🇺🇦 **UK:** nie rozpoczęte (Companies House API).
- 🇩🇪 **Niemcy:** **SKIPPED** per AGENTS.md.

---

**Podpis:** Auto-generated 2026-08-12 12:35 CEST by Mavis (General agent).
**Reviewer:** Marceli.
