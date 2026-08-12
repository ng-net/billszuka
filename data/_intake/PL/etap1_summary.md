# Etap 1 — Summary

**Data:** 2026-08-10

## Korekty zastosowane

| Operacja | Liczba | Szczegóły |
|---|---:|---|
| A→B moves (kategory mismatch per master) | 4 | Dopalenia, Elenpipe, BongoGo, Cloudshop |
| Tier-only fixes (reseller → master_verified) | 7 | Ismoking, Flowrolls, Konopnysklep, Bista Standard, Wszystkodopalenia, Trafika.pl, Weedpol |
| A-bez-NIP przeniesione do B4 (cross-sell) | 86 | Wszystkie A4 z brakującym NIP |
| A1-bez-NIP zostawione w A (heavily flagged 🔍⚠️) | 4 | PowerMatic candidates, wymaga L1 research |
| Łącznie poprawionych/oznaczonych | 101 | |

## Skład po Etap 1

| | Master PL | Normalized (po Etap 1) | Delta |
|---|---:|---:|---:|
| Katalog A | 3 | 32 | +29 |
| Katalog B | 27 | 294 | +267 |
| **Razem** | **30** | **326** | **+296** |

## NIP overlap

| | Count |
|---|---:|
| Master unikalne NIPy | 29 |
| Normalized unikalne NIPy | 75 |
| Wspólne | 0 |
| Nowe w normalized (do dodania) | 75 |
| W master, brak w normalized | 29 |

## Flagi

| Flaga | Count | Znaczenie |
|---|---:|---|
| 🔧 | 11 | tier/kategoria poprawione wg master verified |
| 🔍 | 326 | DO-WERYFIKACJI (L1 research needed) |
| 🔍⚠️ | 4 | A1 no-NIP, heavy flag — NIE merge przed L1 |

## Wstrzymane

⚠️ **Merge do mastera WSTRZYMANY** — czeka na:
1. Akceptację tych poprawek
2. Decyzję o A1-bez-NIP (4 wiersze) — czy idą do merge jako A1 z flagą 🔍⚠️, czy też przenieść do B
3. Decyzję o scope Etap 2 (rozszerzenie kolumn master PL + wypełnienie)
