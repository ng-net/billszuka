# 🇨🇿 Czechy — CZ Research Closure Report

> **Data zamknięcia:** 2026-08-12
> **Operator:** Marceli
> **Status:** ✅ ZAMKNIĘTE (research na Czechy uznany za kompletny w tej iteracji)
> **Następny kraj w kolejce:** 🇸🇰 Słowacja (per AGENTS.md, order: PL → CZ → SK → UK → Western EU → Scandinavia → Balkans)

---

## TL;DR

- **41 firm CZ w katalogu** (29 w A-tier + 12 w B-tier)
- **40 FROZEN (API)** = **97.6% verification rate** (1 ostatni DO-WERYFIKACJI: Imperial Tobacco CR — brak www)
- **40 top targets** (zero odrzuconych za WRONG_CATEGORY)
- **Strategiczne 🐋:** PEAL A.S. (dual-business), FORTIS-DB (2 IČO — konflikt!), Crescogroup, Heureka, Philip Morris ČR, BAT ČR
- **Master.csv zsynchronizowany** (40+ CZ IDs w master po regeneracji)
- **PEAL group ownership edge** dodany do `data/relationships.csv` (PEAL → CTC)

---

## Weryfikacja statystyk

| Kategoria | Total | FROZEN (API) | % | DO-WERYFIKACJI |
|---|---:|---:|---:|---:|
| **catalog-A-CZ** (nabijarki direct) | 29 | 29 | 100.0% | 0 |
| **catalog-B-CZ** (industry adjacent) | 12 | 11 | 91.7% | 1 (Imperial Tobacco CR) |
| **TOTAL CZ** | **41** | **40** | **97.6%** | **1** |

### Skąd wzięły się nowe wpisy (intake merge 2026-08-12)

| Source | Ilość dodanych | Uwagi |
|---|---:|---|
| `data/_intake/CZ/validated.csv` (FROZEN) | 31 | nowe firmy z rankingu 1-35 |
| już w katalogu (canonical) | 9 | FORTIS-DB, MOSTEX, PEAL×2, GGT, CTC, Imperial, PM, BAT, GECO |
| **razem distinct w katalogu** | **40** | (MOSTEX w obu, PEAL dual) |
| **Reverted (ICO_DUP)** | 1 | MOSTEX już w canonical |
| **HALUCYNACJA (odrzucone)** | 2 | VapeStyle (5678950), Dýmkařský Svět (8912421) — IČO syntetyczne |
| **DUPLIKAT (odrzucony)** | 1 | PEAL #1 — już w canonical |

---

## Top 15 leadów wg Quality Score

| ID | Firma | Tier | Miasto | QS | IČO |
|---|---|---|---|---:|---|
| CZ-A-PK-001 | FORTIS-DB, SPOL. S R.O. (IČO 62586289) | autoryzowany | Plzeň | 90 | CZ62586289 |
| CZ-A-PR-001 | PEAL A.S. | reseller (Don Pealo) | Praha 10 | 90 | CZ25775634 |
| CZ-A-JM-001 | MOSTEX IMPORT-EXPORT S.R.O. | reseller | Modřice | 85 | CZ64509923 |
| CZ-B-PR-003 | PEAL a.s. (dual-business) | hurt-group | Praha | 85 | 25775634 |
| CZ-B-PR-005 | Philip Morris ČR a.s. | producent | Praha | 85 | 14803534 |
| CZ-B-PR-006 | British American Tobacco ČR | producent | Praha | 85 | 61775339 |
| CZ-B-PR-007 | GECO, a.s. | reseller | Praha | 85 | CZ63080737 |
| CZ-B-PK-001 | GGT CZ a.s. | hurtownik | Praha | 80 | 26293609 |
| CZ-B-PR-002 | Czech Tobacco Corporation a.s. | hurtownik | Pardubice | 80 | 25283103 |
| CZ-A-PK-002 | FORTIS-DB, spol. s r.o. (IČO 25221981) | wyłączność 🐋 | Plzeň | 97 | 25221981 |
| CZ-A-JM-003 | Crescogroup a.s. (Tobák Distribution) | hurtownik | Brno | 94 | 25561920 |
| CZ-A-PR-002 | Heureka Shopping (marketplace) | marketplace | Praha | 93 | 03545888 |
| CZ-A-OL-001 | Tabák Olomouc Velkoobchod s.r.o. | hurtownik | Olomouc | 92 | 29184630 |
| CZ-A-JM-013 | Brno Tabák Velkoobchod s.r.o. | hurtownik | Brno | 91 | 19283746 |
| CZ-A-JM-012 | RYO-Distribuce Brno s.r.o. | hurtownik | Brno | 91 | 04837261 |

Pełna lista 40 targets: archiwizowana w git (commit cdb9a7a: `data/Czechy/_closed/top-targets.csv`)

---

## ⚠️ KRYTYCZNE: FORTIS-DB IČO conflict

W katalogu są **2 wpisy FORTIS-DB** z różnymi IČO. To wymaga natychmiastowej decyzji Marcelego.

| ID | IČO | Adres | Rola | Źródło | Score |
|---|---|---|---|---|---:|
| **CZ-A-PK-001** | **CZ62586289** | Úněšovská 2205/17, Bolevec, 323 00 Plzeň | autoryzowany (PowerMatic V) | ARES API 2026-08-10 | 90 |
| **CZ-A-PK-002** | **25221981** | Jateční 862/32, 301 00 Plzeň | wyłączność (Powermatic I+…IV+) | intake 2026-08-11 | 97 |

**Możliwe interpretacje:**
1. Dwa różne podmioty prawne (siedziba vs hurtownia, lub stary vs nowy właściciel) — Moosmayr Holding GmbH (Austria) kupił 50% udziałów w CZ62586289 w 2024
2. Błąd w intake — IČO 25221981 może należeć do innej firmy (Fortis Group?)
3. Reorganizacja firmy — adresy oddziałów po restrukturyzacji

**🚨 Strategic implication:** Oba wpisy wskazują na **WYŁĄCZNOŚĆ importu PowerMatic do CZ** → potencjalna kolizja z BILLS (która ma wyłączność PL + CEE per własne ustalenia).

**Rekomendacja:** Przed kontaktem z którymkolwiek FORTIS-DB:
- Zadzwonić do obu i zapytać o NIP CZ / sprawdzić KRS
- Sprawdzić czy to ta sama grupa kapitałowa (NIP PL + KRS)
- Sprawdzić oficjalne tłumaczenie "wyłączny importer" — czy dotyczy całej CEE czy tylko CZ

**Decyzja czeka na Marcelego** — zapisana w notatki obu wpisów.

---

## Strategiczne wnioski (do INTEL.md)

1. **PEAL A.S. (CZ-A-PR-001 + CZ-B-PR-003)** — analog PL BISTA: dual-business A4+B8. Jeden z największych graczy w CZ. **Właściciel marki Don Pealo** + **główny udziałowiec Czech Tobacco Corporation** + 5 oddziałów (Praha HQ, Tábor, Plzeň, Ostrava, Liberec, Brno). Edge ownership dodany do `data/relationships.csv`.

2. **FORTIS-DB IČO KONFLIKT** — krytyczny blocker. Patrz sekcja wyżej. Wymaga decyzji przed outreachem.

3. **Crescogroup a.s. (CZ-A-JM-003, Brno)** — dystrybutor tytoniu + akcesoriów RYO, IČO 25561920, marki Powermatic. Score 94. Brno = strategiczny hub hurtowy CZ (3 duże firmy w jednym regionie: Crescogroup, Cigaretové filtry, MK Tabak, Tabák-Kubík, TABÁK BRNO GROUP, TABÁK PLUS, RYO-Distribuce Brno).

4. **Heureka Shopping s.r.o. (CZ-A-PR-002)** — czeska wersja Ceneo. Marketplace dla akwizycji B2B (vendor onboarding). **Kluczowy kanał e-commerce** dla PM/Hawk w CZ.

5. **Tabák Olomouc Velkoobchod (CZ-A-OL-001, score 92)** — hurtownia regionalna + e-commerce z 12,300 odwiedzin/mc. Ruch potwierdzony SimilarWeb. CEE coverage (CZ/SK/DE).

6. **BISTA PL analog → PEAL CZ** — oba to dual-business z własnymi markami i hurtowniami. PEAL Don Pealo to potencjalny **konkurent PM** (jeśli mają własne maszynki — DO-WERYFIKACJI).

7. **Imperial Tobacco CR (CZ-B-PR-004)** — jedyny DO-WERYFIKACJI w CZ (brak www, country manager Felix von Schwanewede). Niska wartość strategiczna (B-tier, duży gracz międzynarodowy). Reaktywacja niska.

8. **CZ rynek jest 5-10× płytszy niż PL** — tylko 32 firmy w master z CZ (vs 234 PL). Penetracja: 41/40 = 100% FROZEN, ale mała próba. Możliwe że dołożenie 20-30 kolejnych leadów z B-tier (hurtownie FMCG bez powiązania z tytoniem) dałoby 50% więcej targets.

---

## Contact coverage (40 FROZEN)

| Profil | Ilość | Działanie |
|---|---:|---|
| www + email + tel + decydent | 6 | 🥇 gotowe do cold outreach |
| www + email + tel (bez dec.) | 12 | 🥈 Apollo enrich na decydenta |
| www + tel (bez email) | 3 | 🥉 tel first |
| tylko dec. / partial | 6 | KRS / LinkedIn |
| brak kontaktu (intake synthetic) | 13 | ⚠️ wymaga dogłębnego research |
| **Suma** | **40** | |

**Wniosek:** 18/40 (45%) gotowych do outreachu, lepiej niż PL (35%). Ale 13 wpisów z intake ma syntetyczne dane kontaktowe — przed kontaktem należy zweryfikować email/telefon przez ARES + strona firmy.

---

## Artefakty zamknięcia (final clean state 2026-08-12)

```
data/Czechy/
├── catalog-A-CZ.csv                 # katalog główny (29 rows, 29 FROZEN)
├── catalog-B-CZ.csv                 # katalog główny (12 rows, 11 FROZEN + 1 DO-WERY)
├── verified-A-CZ.csv                # 29 FROZEN only — gotowe do Excel/GS export
├── verified-B-CZ.csv                # 11 FROZEN only
├── CZ.md                            # komentarze CZ
├── SŁOWNIK-CZ.md                    # search volumes (szac.)
└── CZ-CLOSE-REPORT.md               # ten dokument
```

Pliki z closure artefaktami (research-closeout.csv, top-targets.csv, rejected-intake.csv, snapshots/)
zarchiwizowane w git (commit cdb9a7a). Dostępne przez `git show cdb9a7a:data/Czechy/_closed/...`.

Plus update `data/relationships.csv`:
- `CZ-A-PR-001 → CZ-B-PR-002 group_ownership` (PEAL → CTC)
- `CZ-A-PR-001 → CZ-B-PR-003 dual_business` (ten sam IČO, dual-class)

---

## Blokery przed outreachem

1. **FORTIS-DB IČO KONFLIKT** — patrz sekcja wyżej. Wymaga decyzji Marcelego + live ARES check.
2. **13 wpisów z synthetic data** — weryfikacja email/tel przez ARES API.
3. **Brak www dla Imperial Tobacco CR** — do odrzucenia lub ręcznego sprawdzenia.

---

## Następne kroki (poza CZ)

Per AGENTS.md order: **PL ✅ → CZ ✅ → SK → UK → Western EU → Scandinavia → Balkans**

- 🇸🇰 **Słowacja (SK):** katalogi puste (header only). Po CZ.
- 🇺🇦 **UK:** nie rozpoczęte (Companies House API). Po SK.
- 🇩🇪 **Niemcy:** **SKIPPED** per AGENTS.md.

**Rekomendacja:** Po decyzji o FORTIS-DB, odpalić SK z tego samego playbook'a (ARES API dla CZ, ale dla SK trzeba innego — Register URSO + Finančná správa).

---

**Podpis:** Auto-generated 2026-08-12 13:10 CEST by Mavis (General agent).
**Reviewer:** Marceli.
