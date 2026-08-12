# 🇸🇰 Słowacja — dziennik badawczy

**Data ostatniego update:** 2026-08-12 13:50 CEST  
**Status:** ✅ etap 1 closed — 37 wierszy w katalogach (14 A + 23 B), w trakcie weryfikacji (16 Nowy / 14 Zweryfikowany).

## Reżim regulacyjny (2024-2025)
- Akcyza EU, ograniczenia reklamy
- E-papierosy: legalne, ograniczenia smakowe
- CBD: legalne, susz nielegalny
- Nabijarki: bez ograniczeń

## Rejestry
- **IČO** / **IČ DPH**
- **ORSR**: https://orsr.sk (web search; brak JSON API — patrz RUNBOOK.md)
- **ŽRSR**: https://www.zrsr.sk

## Marketplaces
- **Heureka.sk**
- **Bazoš.sk** (główny OLX-ekwiwalent)
- **Mall.sk**
- **Alza.sk**

## Katalog — stan na 2026-08-12 13:50 CEST

| Katalog | # wierszy | kategoria | Marceli Status | Verification | Źródło |
|---|---|---|---|---|---|
| `catalog-A-SK.csv` | **14** | A1 (2) / A2 (12) | 1 Zweryfikowany + 13 Nowy | 1 FROZEN / 13 ⏳ PENDING_API | intake 2026-08-12 |
| `catalog-B-SK.csv` | **23** | B1 (4) / B4 (1) / B6 (4) / B8 (7) + 7 starter | 13 Zweryfikowany + 3 Nowy + 7 starter | 13 FROZEN / 3 ⏳ / 7 ⏳ PENDING_API | intake 2026-08-12 + starter 2026-08-10 |
| **Suma** | **37** | — | — | 14 FROZEN / 16 ⏳ PENDING_API + 7 ⏳ PENDING_API starter | — |

### Podział per kategoria (po re-kategoryzacji)

| Kategoria | Tier logiczny | # | IDs |
|---|---|---|---|
| **A1** — kontakt natychmiast (S1) | A (PowerMatic direct) | 2 | SK-A-BA-002 (GGT a.s. GGTabak), SK-A-TN-002 (BRESMAN s.r.o.) |
| **A2** — partner regionalny (S1) | A (regionalny partner) | 12 | SK-A-BA-001, 003-007; SK-A-TN-001; SK-A-ZA-001; SK-A-KE-001; SK-A-NR-001; SK-A-TT-001; SK-A-PO-001 |
| **B1** — hurtownia tytoniowa (S2) | B | 4 | SK-B-BA-003, 005, 006, SK-B-NR-001 |
| **B4** — akcesoria (Smoking Accessories) | B | 1 | SK-B-BB-003 (Fajčiarske Potreby) |
| **B6** — e-papierosy (S3 + Vape) | B | 4 | SK-B-BB-001, 002; SK-B-KE-002; SK-B-ZA-001 |
| **B8** — pełne hurtownie tytoniowe (S4) | B | 7 | SK-B-BA-001, 002, 004; SK-B-KE-001; SK-B-PO-001; SK-B-TT-001; SK-B-TN-001 |
| (B4 starter) — duże firmy tytoniowe | B | 7 | SK-B-XX-004 do 009, 011 (Imperial, PMI, JTI, Mediapress BA, Continental, MOSTEX, MY&MI) |

### Pokrycie regionalne (A-tier)

| Region | # A | # B |
|---|---|---|
| BA (Bratislavský) | 7 | 6 |
| BB (Banskobystrický) | — | 3 |
| KE (Košický) | 1 | 2 |
| NR (Nitriansky) | 1 | 1 |
| PO (Prešovský) | 1 | 1 |
| TN (Trenčiansky) | 2 | 1 |
| TT (Trnavský) | 1 | 1 |
| ZA (Žilinský) | 1 | 1 |
| XX (nieznany / multi) | — | 7 (starter) |

## Verification pipeline (etap 2 → 3)

### W trakcie (per krok 7-8):
- **14 wierszy "Zweryfikowany"** → bezpośrednio `✅ FROZEN` (Marceli's existing API check).  
  Skład: 13 B-tier + 1 A-tier (Smokeshop SK-A-BA-001 — IČO 45293006 z serii templated; **follow-up needed**).
- **16 wierszy "Nowy"** → `tools/verify_api.py --country SK` (ORSR + VIES).  
  Skład: 13 A-tier + 3 B-tier (Vaprio s.r.o. SK-B-BA-005, TopVape SK-B-NR-001, Royal SMOK SK-B-BA-006).
- **7 wierszy starter set** (Imperial, PMI, JTI, Continental, MOSTEX, Mediapress BA, MY&MI) → zostają `⏳ PENDING_API` (Marceli follow-up OSINT).

### Halucynacja / audyt (z `data/_intake/SK/normalize_audit.md`)

**18 flag** w danych Marcela, z czego najważniejsze:
1. **Seria IČO `45293XXX`** (8 wierszy) — wygląda na placeholder, wymaga ORSR potwierdzenia:
   - Smokeshop BA, Labaš, Metro, E-smoke BB, Libex, Kon-Rad, Tabak-Press, Vaprio KE
2. **Templated email/phone pattern:** `b2b.sk[N]@<domena>.sk` + `+421 2 40000N` + `Centralna ulica N` — ten sam batch 8 wierszy
3. **2× GGT a.s. z różnymi NIP/VAT** (SK-B-BA-001 IČO 31362781 NIP SK2020286950 vs SK-A-BA-002 NIP SK2021651817) — parent + subsidiary LUB literówka w intake
4. **2× Tabak Invest z różnymi IČO** (SK-A-BA-007 IČO 36788694 vs SK-A-TT-001 IČO 36759244) — dwa podmioty w grupie
5. **2× Decydent='Unknown'** (E-Smoke s.r.o., Fajčiarske Potreby SK)

## Źródła startowe (do follow-up)
- Google: "strojčeky na cigarety veľkoobchod"
- Bazoš.sk szukaj "PowerMatic", "Hawk"
- Firmy z BISTA (Bydgoszcz) — mają eksport do SK?

## Pliki powiązane

- `data/_intake/SK/` — folder intake (mapping.md, normalized_A/B.csv, normalize_audit.md, etap1_summary.md, merge_dedup.md, normalize.py, merge.py)
- `data/Słowacja/catalog-A-SK.csv` (14 wierszy)
- `data/Słowacja/catalog-B-SK.csv` (23 wiersze)
- `data/Słowacja/SŁOWNIK-SK.md` — keyword dictionary
- `RUNBOOK.md` — SK verification recipe (ORSR web search + VIES)
- `INTEL.md` — strategic findings (per Marceli: tu dopisujemy spostrzeżenia)
- `DZIENNIK.md` — session log
