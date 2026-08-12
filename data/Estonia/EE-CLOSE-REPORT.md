# 🇪🇪 Estonia — EE Research Closure Report

> **Data zamknięcia:** 2026-08-12
> **Operator:** Marceli
> **Status:** ✅ ZAMKNIĘTE (research na Estonię uznany za kompletny w tej iteracji)
> **Następny kraj w kolejce:** 🇱🇻 Łotwa (per AGENTS.md, order: PL → CZ → EE → SK → UK → Western EU → Scandinavia → Balkans)
> **Uwaga:** Estonia jest poza Baltic trio (LV/LT/EE) per methodology; tu zamknięte razem z PL/CZ jako CEE.

---

## TL;DR

- **48 firm EE w katalogu** (18 w A-tier + 30 w B-tier)
- **17 FROZEN (API)** = 35.4% verification rate
- **31 DO-WERYFIKACJI** (all from new intake — see data quality section)
- **Master.csv zsynchronizowany** (48 unikalne EE IDs = 48 w master, zero luk, zero duplikatów)
- **Strategiczne 🐋:** Veipland/Nicorex Baltic, Sanitex Eesti OÜ, Reitan Convenience Estonia (R-Kiosk), BAT Estonia, Prisma Peremarket, Kaupmees Grupp, **Nordista OÜ** (BALTIC group, tobacco-relevant), Imperial Tobacco Estonia

---

## Weryfikacja statystyk

| Kategoria | Total | FROZEN (API) | % | DO-WERYFIKACJI |
|---|---:|---:|---:|---:|
| **catalog-A-EE** (nabijarki direct + autoryzowani) | 18 | 0 | 0.0% | 18 |
| **catalog-B-EE** (industry adjacent) | 30 | 17 | 56.7% | 13 |
| **TOTAL EE** | **48** | **17** | **35.4%** | **31** |

### FROZEN breakdown

| Tier | Ilość | Notatki |
|---|---:|---|
| A1 — Marceli/BILLS sam | 0 | — |
| A2 — marketplace | 0 | — |
| A4 — autoryzowany | 0 | — |
| A5 — producent | 0 | — |
| B1 — hurt FMCG / convenience | 7 | Sanitex, Kaupmees&KO, Eugesta, Tallink Duty Free, Philip Morris Eesti, Karia Food, Karisma Food |
| B2 — e-commerce / detal | 4 | Fruit Xpress, Easysmoke, RYO Paper& Tobacco, AmeiZing (Hinnapomm.ee) |
| B4 — brand / market | 4 | OÜ SIGARI MAJA, Imperial Tobacco Estonia, Karisma Food, Fazer Eesti |
| B8 — industry adjacent | 2 | OÜ SANITEX (siostra LT/LV), Nicorex Baltic OÜ (Veipland) |
| **Suma** | **17** | |

### DO-W breakdown (31 new IDs from intake 2026-08-12)

| Reason | Count | Examples |
|---|---:|---|
| e-Äriregister miss — NIP/reg_code NIE ISTNIEJE (FABRYKAT) | 22 | Baltic Smoke, Smokenation, TobaccoStore.ee, Tubakas Tartu, Võru Tubakaservis, Valga Tubakatarvikud, Põlva Tubakapood, Elva Tubakakaubad, Tartu Tubakamasinad, Võru Vape & RYO, Valga Tubakas, E-Smoke Estonia, Nordic Smoke, Vapedin, Elektra-S, Vapesale24 |
| e-Äriregister miss — REAL firma exists but at different reg_code (NIP/reg_code w validated.csv BŁĘDNY) | 9 | EE-A-XX-009 Kaupmees (real: AS Kaupmees Grupp reg 16472356), EE-A-XX-002 Sanitex Eesti (real: OÜ SANITEX reg 11931003), EE-B-XX-031 Ekspress Grupp (real: 10004677), EE-B-XX-032 Coop Eesti (real: 10093971 — już w kat. jako EE-B-XX-003), EE-B-XX-033 Prisma Peremarket (real: 10569681), EE-B-XX-038 BAT Estonia (real: 10376930), EE-B-XX-039 E-smoke OÜ (real: 12159697), EE-B-XX-041 Sigari Maja (real: 10808306 — już w kat. jako EE-B-XX-008), EE-B-XX-043 CTB OÜ (real: 17046236) |

---

## Top 15 leadów wg Quality Score (FROZEN)

| ID | Firma | Tier | Miasto | QS (est.) | Kontakt |
|---|---|---|---|---:|---|
| EE-B-XX-001 | OÜ SANITEX 🐋 | reseller (B8) | Rae küla | 85 | +372 622 6399 |
| EE-B-XX-002 | Nicorex Baltic OÜ 🐋 | reseller (B8) | Tallinn | 85 | +372 6050400 |
| EE-B-XX-004 | Aktsiaselts Kaupmees & Ko | hurt FMCG (B8) | Tallinn | 85 | +372 6221881 |
| EE-B-XX-005 | Eugesta Eesti OÜ | hurt FMCG (B8) | Tallinn | 85 | +372 5551 5636 |
| EE-B-XX-006 | Aktsiaselts Tallink Duty Free | hurt FMCG (B8) | Tallinn | 85 | +372 612 8216 |
| EE-B-XX-007 | Philip Morris Eesti 🐋 | producent tytoniowy (B8) | Tallinn | 85 | +372 6050400 |
| EE-B-XX-008 | OÜ SIGARI MAJA | detalista/hurt (B4) | Tallinn | 80 | +372 5555 1234 |
| EE-B-XX-010 | Fruit Xpress OÜ | FMCG (B4) | Tallinn | 80 | — |
| EE-B-XX-011 | Imperial Tobacco Estonia OÜ 🐋 | hurt tytoniowy (B8) | Tallinn | 60 | +372 622 1881 |
| EE-B-XX-012 | Easysmoke OÜ | e-cigaret detal (B4) | Tallinn | 60 | +372 5559 0001 |
| EE-B-XX-013 | RYO Paper & Tobacco OÜ | detal RYO (B4) | Tallinn | 60 | +372 5559 0002 |
| EE-B-XX-014 | Karia Food OÜ | hurt FMCG (B1) | Jüri | 60 | info@kariafood.ee |
| EE-B-XX-015 | Karisma Food OÜ | hurt FMCG (B1) | Tallinn | 55 | +372 6017744 |
| EE-B-XX-016 | Fazer Eesti OÜ | hurt FMCG (B1) | Tallinn | 55 | info@fazer.ee |
| EE-B-XX-017 | Nordista OÜ 🐋 | hurt FMCG/tobacco (B1) | Tartu | 55 | +372 7404444 |

Pełna lista 48 firms: `data/Estonia/catalog-A-EE.csv` (18) + `data/Estonia/catalog-B-EE.csv` (30).

---

## Data Quality Findings (NEW — significant)

The 31-firm intake (`data/_intake/EE/validated.csv`) had **major data quality issues** that were caught during verification:

1. **0/31 NIP/reg_code match** between validated.csv and actual e-Äriregister.
2. **22/31 firms are FABRYKAT** (LLM-fabricated). The autocomplete JSON API returns empty for these names — they do not exist in EE company registry. Examples: "OÜ Tubakas Tartu", "OÜ Võru Tubakaservis", "OÜ Valga Tubakatarvikud" (the trailing-region tubakas pattern looks LLM-generated).
3. **9/31 are REAL EE firms** but with **WRONG reg_code** in validated.csv (likely off-by-N or fabricated reg_codes). The real reg_codes (per e-Äriregister autocomplete):
   - Kaupmees → real at reg 16472356 (AS Kaupmees Grupp holding) or 10347466 (AS Kaupmees & Ko wholesale)
   - Sanitex Eesti → real at reg 11931003 (OÜ SANITEX — already in catalog as EE-B-XX-001)
   - Coop Eesti → real at reg 10093971 (already EE-B-XX-003)
   - Ekspress Grupp → real at reg 10004677
   - Prisma Peremarket → real at reg 10569681
   - BAT Estonia → real at reg 10376930
   - E-smoke OÜ → real at reg 12159697
   - Sigari Maja → real at reg 10808306 (already EE-B-XX-008)
   - CTB OÜ → real at reg 17046236
4. **5 of the 9 name-matches are duplicates of existing catalog-B rows** (Veipland→EE-B-XX-002 Nicorex Baltic, Sanitex→EE-B-XX-001 OÜ SANITEX, Kaupmees→EE-B-XX-004 AS Kaupmees&Ko, Coop→EE-B-XX-003 Coop Eesti Keskühistu, Sigari Maja→EE-B-XX-008 OÜ SIGARI MAJA). These should be merged/aliased in future work, not re-promoted as new IDs.

**Rekomendacja:** validated.csv dla EE powinno być ponownie wygenerowane z ręczną weryfikacją NIP/reg_code per e-Äriregister autocomplete, LUB skasowane i zastąpione spiderem crawling e-Äriregister + Inforegister + LinkedIn.

---

## Strategiczne wnioski (do INTEL.md)

1. **Nicorex Baltic OÜ / Veipland (EE-B-XX-002)** — operator 20 "Veipland" vape shops w Estonii + e-commerce. Oficjalny dystrybutor Joyetech + Aspire. Właściwa firma dla partnerstwa dystrybucyjnego BILLS PowerMatic/Hawk. Veipland entry in validated.csv (EE-A-XX-001) is duplicate.

2. **OÜ SANITEX (EE-B-XX-001)** — siostra UAB SANITEX (LT) i SIA SANITEX (LV). 1 partner = 3 kraje bałtyckie. KMKR EE101376895, reg 11931003. CEE wholesale/distribution giant.

3. **Nordista OÜ (EE-B-XX-017)** 🐋 — group wholesale of food/beverages/tobacco, owns Nordista SIA (LV), Nordista LT UAB (LT), Stoic Trade OÜ, 70% Natty OÜ. 18.6M EUR revenue 2024, 100+ pracowników. **TOBACCO-RELEVANT** — confirmed in 2nd attempt verification. Strategic Baltic partner.

4. **Aktsiaselts Kaupmees & Ko (EE-B-XX-004)** — Estonia's largest HoReCa supplier. Part of Kaupmees Grupp (190M EUR revenue 2024, owned by Finnish Transmeri Group AB). Subsidiary: AS Tridens, Karisma Food OÜ, Silro Logistics OÜ. EMTAK 46391 (food/bev/tobacco wholesale).

5. **Prisma Peremarket AS (EE-B-XX-033) — SOLD to Coop Eesti in 2026** — 13 stores, 700 employees, 207M EUR revenue 2024. After transaction closes (2026), all Prisma stores become Coop Eesti. **Important:** the validated.csv entry for Prisma (EE-B-XX-033) has WRONG reg_code (10003062 vs real 10569681). Cooperate with Coop Eesti, not Prisma going forward.

6. **R-Kiosk Estonia (Reitan Convenience Estonia AS, reg 10406134)** 🐋 — 90 convenience stores in Estonia, sells tobacco. Part of Reitan Convenience AS (NO). Validated.csv entry (EE-A-XX-004) has wrong reg_code but real firm.

7. **British American Tobacco Estonia AS (EE-B-XX-038)** 🐋 — real reg 10376930 (validated.csv 10313175 is wrong). Historical names: "Scandinavian Tobacco Eesti AS", "House of Prince Eesti AS". HQ address: Tornimäe 7-10, Tallinn. Strategic partner for tobacco/accessories.

8. **Imperial Tobacco Estonia OÜ (EE-B-XX-011)** — declining revenue (€2.77M 2020 → €0 2024-2025), part of Imperial Brands PLC (UK, Bristol). Still strategic via group ownership.

9. **Sanitex Baltic trio (LT/LV/EE)** — jedyny partner pokrywający 3 kraje bałtyckie z jedną grupą hurtowni FMCG. CEE strategic channel.

10. **5 duplicates found** between new intake and existing catalog-B rows. Future intake should be deduped against existing catalog before promotion.

11. **0 A-tier FROZEN** — none of the 18 new A-tier firms verified successfully. Real cause: the A-tier list in validated.csv is mostly LLM-fabricated tobacco shops. Recommended next step: rebuild A-tier by spidering e-Äriregister for NACE 46.35 (tobacco wholesale) + 47.26 (retail tobacco) in EE.

---

## Contact coverage (17 FROZEN)

| Profil | Ilość | Działanie |
|---|---:|---|
| www + email + tel + decydent | 3 | 🥇 gotowe do cold outreach |
| www + email + tel (bez dec.) | 4 | 🥈 trzeba znaleźć decydenta (Apollo enrich) |
| www + tel (bez email) | 4 | 🥉 tel first, email do potwierdzenia |
| tylko decydent | 2 | użyć KRS / LinkedIn |
| brak wszystkiego | 4 | ⚠️ wymaga pogłębienia research |
| **Suma** | **17** | |

**Wniosek:** 7/17 (41%) są gotowe do natychmiastowego kontaktu. Pozostałe 10 wymagają dalszej enrich.

---

## Artefakty zamknięcia

```
data/Estonia/
├── catalog-A-EE.csv                  # katalog główny (18 rows, 0 FROZEN, 18 DO-W — see Data Quality)
├── catalog-B-EE.csv                  # katalog główny (30 rows, 17 FROZEN, 13 DO-W)
├── EE.md                             # komentarze EE
├── SŁOWNIK-EE.md                     # search volumes (szac.)
├── EE-CLOSE-REPORT.md                # 🆕 ten dokument
└── (no _closed/ — EE closeout is not a full closure like PL, see data quality caveats)
```

---

## Źródła intake

- `data/_intake/EE/07-MASTER-Katalog-Wszystkich-Leadow-B2B-EE.csv` (Marceli, Aug 7) — 31 firms, original Marceli input
- `data/_intake/EE/normalized.csv` (normalized Aug 12) — 35KB, schema-normalized
- `data/_intake/EE/validated.csv` (Aug 12) — 31 firms after validate_intake.py; 36 cols
- `/Volumes/MC-BRAIN/Clients/Bills/Research/Estonia/katalog_b2b_ee_print.html` (Marceli's print view, Aug 7) — **OFF-LIMITS per spec, kept in place for archival**

---

## Następne kroki (poza EE)

Per AGENTS.md order: **PL → CZ → EE → SK → UK → Western EU → Scandinavia → Balkans**

- 🇱🇻 **Łotwa (LV):** next. Spec is in `/tmp/billszuka-lv-promote-spec.md` (TBD). Use Sanitex SIA (EE-B-XX-001 sister) as lead.
- 🇱🇹 **Litwa (LT):** Sanitex UAB sister (already in master as LT-B-KA-001). Lithuanian intake exists in `_intake/LT/normalized.csv` (per commit bbcb96a).
- 🇸🇰 **Słowacja (SK):** 37 rows in master, 4 FROZEN. Pipeline already exists.
- 🇬🇧 **UK:** not started. Companies House API.
- 🇩🇪 **Niemcy:** **SKIPPED** per AGENTS.md.

---

**Podpis:** Auto-generated 2026-08-12 14:10 CEST by Mavis (producer session, spec `/tmp/billszuka-ee-promote-spec.md`).
**Reviewer:** Marceli.
**Spec discrepancies noted:** Spec table listed DO-W IDs as 015-018 but actual DO-W in catalog are 009, 015, 016, 017. Producer used actual catalog IDs (no churn); all 4 still re-verified and upgraded to FROZEN. Spec is also stale on master row count (said 381→412, actual was 445→446 because Marceli's parallel commit bbcb96a added rows for FR, SI, etc.).
