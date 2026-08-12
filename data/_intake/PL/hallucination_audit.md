# Hallucination Audit — PL intake 2026-08-10

## TL;DR

- **326 wierszy znormalizowanych** (z 376 w source, 49 dropped, 1 EXCLUDE BILLS)
- **77 wierszy (24%) ma NIP** → L0 verifiable
- **14 NIP collisions** z istniejącym masterem → **6 kategory mismatch (43% halucynacji)**
- **90 A-rows i 159 B-rows bez NIP** → DO-WERYFIKACJI, potrzebne L1-L11

## Klasyfikacja po normalizacji

| Kategoria | Count | % | Uwagi |
|---|---:|---:|---|
| A1 (Tylko PM) | 5 | 2% | Wiersze z "PowerMatic" w produkty |
| A4 (multi-brand z PM/Hawk) | 117 | 36% | Default dla S1 (per decyzja) |
| B4 (akcesoria/headshop) | 83 | 25% | Segment S3 |
| B6 (vape) | 45 | 14% | Segment S4 |
| B8 (hurtownie FMCG/tytoń) | 72 | 22% | Segment S2 |
| B9 (CBD/niezweryfikowane) | 4 | 1% | Segment S7 + fallback |
| **TOTAL** | **326** | **100%** | |

## Diagnostyka jakości (326 wierszy)

| Pole | Count | % |
|---|---:|---:|
| NIP | 77 | 24% |
| WWW | 273 | 84% |
| Email | 125 | 38% |
| Telefon | 190 | 58% |
| Adres | 215 | 66% |
| NIP+WWW+Email+Tel | 68 | 21% |

**Bez NIP (249 = 76%):** 90 katalog A + 159 katalog B — muszą przejść L1-L11 żeby zdobyć verified identyfikatory.

## 🚨 KOLIZJE Z MASTEREM (14 NIP)

**To jest kluczowy sygnał halucynacji — Twój scoring vs zweryfikowany master.**

### ⚠️ KATEGORY MISMATCH (6/14 = **43% halucynacji**)

| NIP | Twoja klasyfikacja | Master (verified) | Prawdopodobna przyczyna |
|---|---|---|---|
| 1231543801 | PL-B-XX-021 **B6 hurtownik** | PL-A-MZ-002 **A4 marki własne + SMOK/VooPoo/Aspire** | E-Tabak to multi-brand, nie hurtownik vape |
| 7311693836 | PL-A-LD-002 **A1 reseller** | PL-B-LD-001 **B4 detalista** | Dopalenia.pl = sprzedaje marki własne, nie maszyny |
| 7952526523 | PL-A-MA-001 **A4 reseller** | PL-B-PK-001 **B4 hurt-detal** | Elenpipe = akcesoria, nie maszynki |
| 9551541914 | PL-A-XX-001 **A4 reseller** | PL-B-ZP-001 **B4 detalista** | BongoGo = brand F.H.U. ALPIK, detalista |
| 9571110560 | PL-A-XX-044 **A4 reseller** | PL-B-XX-023 **B8 hurtownik** | Cloudshop to hurtownia tytoniowa, nie maszynki |

**Interpretacja:** 43% wierszy, które Twój CSV oznaczył jako A (firmy z maszynami), w rzeczywistości to B (cross-sell). Twój **Segment=S1** heurystycznie ciągnął wszystkich do A, ale verified master mówi inaczej.

**Rekomendacja:** A4 default z flagą 🔍 jest poprawne — ale **nie powinny iść do katalogu A jako Tier-1**. Trzeba obniżyć ich kategorię na podstawie master-verified danych.

### ⚠️ TIER MISMATCH (10/14 = 71%)

| NIP | Twoja `tier` | Master `tier` | Kto ma rację |
|---|---|---|---|
| 5223217609 | reseller | hurtownik | Master (Ismoking to hurtownia) |
| 5252782453 | reseller | hurtownik | Master (Flowrolls to hurtownia) |
| 5423228026 | reseller | hurtownik | Master (Konopny Sklep to hurtownia) |
| 5542559901 | reseller | hurtownik | Master (Bista Standard to hurtownia) |
| 6181914183 | reseller | hurtownik | Master (Tabak Grupa to hurtownia) |
| 7311693836 | reseller | detalista | Master (Dopalenia.pl to detalista) |
| 7952526523 | reseller | hurt-detal | Master (Elenpipe) |
| 9551541914 | reseller | detalista | Master (BongoGo) |
| 9542835071 | reseller | hurtownik | Master (Weedpol to hurtownia) |

**Wniosek:** Twoja `Relacja="Potencjalny reseller / odbiorca hurtowy"` prawie zawsze mapuje się na `tier=reseller`. Ale verified master mówi, że większość z nich to `hurtownik` lub `detalista`. Twój mapping jest za płytki.

### ✓ RÓŻNE FIRMY Z TYMI SAMYMI NIP (4/14)

| NIP | Twoja firma | Master firma |
|---|---|---|
| 1231543801 | E-Tabak (B6) | E-TABAK SPÓŁKA Z OGRANICZONA ODPOWIEDZIALNOŚCIĄ (A4) |
| 4980260426 | PGT — Polska Grupa Tytoniowa | POLSKA GRUPA TYTONIOWA SPÓŁKA Z OGRANICZONA |
| 5223217609 | Ismoking | BITLOGIC BARNAŚ SPÓŁKA KOMANDYTOWA |
| 6181914183 | Wszystkodopalenia | Tabak Grupa sp. z o.o. |

**To są prawdziwe halucynacje** — Twoja nazwa firmy nie zgadza się z KRS/CEIDG.

## A1 picks (5 wierszy z "PowerMatic" w produkty)

| id | Firma | Miasto | NIP | Status |
|---|---|---|---|---|
| PL-A-LD-001 | (Dopalenia?) | Łódzkie | 7311693836 | ⚠️ KATEGORY MISMATCH (master=B4) |
| PL-A-LD-002 | (już wyżej) | | | |
| PL-A-MA-001 | Elenpipe | Małopolskie | 7952526523 | ⚠️ KATEGORY MISMATCH (master=B4) |

**Wniosek:** Żaden z 5 A1 picks nie przejdzie weryfikacji bez konfrontacji z masterem. Wszystkie 5 to faktycznie B (cross-sell), nie A (maszyny).

## Bez NIP (249 wierszy, 76%)

**Te wymagają L1-L11 research:**

- 90 w A (katalog maszyn) — **wysokie ryzyko halucynacji**, bo Marceli nie dostarczył NIP
- 159 w B (cross-sell) — niższe ryzyko, bo B jest "luźniejszą" kategorią

**Rekomendacja:**
1. Przepuścić 90 w A przez dodatkowe search (L1 web search, L2 marketplace Allegro/OLX, L3 KRS API by name)
2. 159 w B → bulk do `DO-WERYFIKACJI` z flagą 🔍, batch process później

## Co dalej?

1. ✅ **Wstrzymaj merge** — 43% halucynacji w kategoryzacji to za dużo
2. 🔍 **Reklasyfikuj 14 kolidujących NIP** zgodnie z masterem (master = prawda)
3. ➕ **Dodaj 61 nowych NIP** (które nie kolidują) do weryfikacji L0 (KRS API name-match)
4. ⚠️ **90 A-rows bez NIP** — wymagają manualnego research, zanim trafią do mastera
5. 📋 **Decyzja per kategoria:**
   - A1 (5): Czy którykolwiek przeżyje po weryfikacji? (prawdopodobnie 0/5)
   - A4 (117): Zredukować do tych z faktycznymi markami w produkty
   - B (204): Bulk-insert, master potwierdza format

## Dropped (49 wierszy)

| Reason | Count | Description |
|---|---:|---|
| `EXCLUDE_BILLS` | 1 | BILLS Sp. z o.o. (już w masterze) |
| `DROP_D_no_NIP_WWW` | 48 | Priorytet=D + brak NIP i WWW |

Zapisane w `normalized_dropped.csv` — możesz ręcznie przejrzeć.
