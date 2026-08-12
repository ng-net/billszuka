# data/_intake/ — bufor wejściowy do normalizacji

Folder na surowe CSV od Marcelego przed zmergowaniem do mastera.

## Konwencja wrzutu

```
data/_intake/{ISO}/
├── source.csv              # surowe 34 kolumny Marcela (input)
├── mapping.md              # decyzje: która kolumna → co (auto-generowane przy pierwszym wrzucie)
└── normalized.csv          # wynik po normalizacji do 37 kolumn naszego szablonu (po akceptacji)
```

`{ISO}` = PL / CZ / SK / RO / LT / LV / EE / FR / MD / BG / SI / HR (PL=Polska, HR=Chorwacja itd.)

## Zasada naczelna

**Nie niszczymy unifikacji 37 kolumn.** Twój CSV ma 34 kryteria, my mamy 37. Mapowanie:

| Twój CSV (34) | Nasz master (37) | Co robimy |
|---|---|---|
| Kolumna 1:1 z naszą (np. `nazwa_firmy`) | ta sama | **bezpośrednio** — kopiujemy |
| Kolumna u nas brak (extra info) | — | **decyzja per case**: jeśli verified → dopisz do `notatki`; jeśli śmieć → drop |
| Nasza kolumna nieobecna u Ciebie | pusta w Twoim CSV | **uzupełniamy** z naszych źródeł (KRS/CEIDG/ARES) albo zostawiamy puste |
| Kolumny specyficzne dla katalogu | rozróżniamy | `marki_nabijarki/marka_wlasna_oem` tylko w A; `powinowactwo_nabijarki/cross_sell_potential` tylko w B |

## Strategia „richer doesn't mean smarter"

**Twój scoring IGNORUJEMY.** Masz własny system ocen, mamy swój (A1-A6 / B1-B9 + tier enum + flagi).
Re-klasyfikujemy każdy wpis od zera do naszej taksonomii, niezależnie od Twojej oceny.

Dla każdej kolumny extra (ponad nasze 37):

1. **Czy ma źródło?** (KRS, CEIDG, ARES, strona firmy, LinkedIn, FV, opakowanie, CMR)
   - **TAK** → treść zostaje, w `zrodlo_danych` dopisujemy `[extra_col_name]`
   - **NIE** → drop do `notatki` (krótka wzmianka) albo usuń całkiem
2. **Czy kolumna pasuje do naszego modelu A/B?**
   - **TAK** → integruj jako nową kolumnę lub dopisz do `notatki`
   - **NIE** → archiwum (folder `data/_intake/_archive/`)
3. **Czy to fixed value dla całej firmy, czy per-wpis variability?**
   - fixed → kandydat na wzbogacenie naszego schematu
   - variability → kandydat do `notatki`

## Pipeline (po każdym wrzucie)

1. **Drop** `data/_intake/{ISO}/source.csv`
2. **Map columns** — auto-generuję `mapping.md` (heurystyka: 1:1 po nazwie kolumny; reszta = decyzja manualna)
3. **Re-classify** — każdy wiersz przepuszczam przez NASZ klasyfikator:
   - **kategoria**: A1-A6 / B1-B9 wg `methodology.md` (marki, profil, kanał)
   - **tier**: `wyłączność` / `autoryzowany` / `reseller` / `detalista` / `marketplace` / `producent` / `hurtownik`
   - **wolumen**: mały/średni/duży wg progów per `rynek_skala` + `confidence_wolumen` 🟢/🟡/🔴
   - **flagi**: 🔴/🟡/🟢/🐋/💎/✅/🔍 wg faktów
   - **powinowactwo** (B): 1-5 wg overlap kliencki
   - **cross_sell_potential** (B): wysoki/średni/niski
   - **Twój scoring → IGNORE** (trzymamy w `zrodlo_danych` jako `"user_orig_score: X"` dla audytu)
4. **Verify L0** — dla każdego wiersza: NIP checksum (mod 11) + KRS/CEIDG name-match + VIES. Wynik: `MATCH / MISMATCH / NO_ID`
5. **Hallucination audit** — raport:
   - ile wierszy: `MATCH` vs `MISMATCH` vs `NO_ID`
   - ile wierszy: adres z Twojego CSV ≠ adres w rejestrze
   - ile wierszy: telefon/email z Twojego CSV = dead (HTTP fail / brak MX)
   - ile wierszy: tier deklarowany niespójny z realiami (np. „producent" + 1 pracownik + brak PKD 22/25/28)
   - ile wierszy: rok założenia ≠ rejestr
   - **% hallucinated** = (MISMATCH + dead-contact + tier-inconsistent) / total
6. **Diff** — pokazuję co doszło / co się zmieniło vs istniejący `data/{Kraj}/catalog-{A|B}-{ISO}.csv`
7. **Approve** — Marceli akceptuje (lub mówi co poprawić)
8. **Merge** — wpadam do `data/{Kraj}/catalog-{A|B}-{ISO}.csv`
9. **Verify full** — `tools/verify_run.py` + `tools/verify_api.py` na zmienionych wierszach
10. **Master regen** — komenda z `skills/verify-data/SKILL.md`
11. **Audit log** — wpis w `data/audit-log.md` (z halucynacją procent)

## Czego potrzebuję od Ciebie przy pierwszym wrzucie

1. **Plik** w `data/_intake/{ISO}/source.csv`
2. **Katalog** — A czy B? (albo 2 pliki: A i B osobno)
3. **Opcjonalnie**: krótka notka o kolumnach, których nie jesteś pewien

## Klasyfikacja — nasza taksonomia (kanoniczna)

**A (firmy z maszynami):**
- A1 — Tylko PowerMatic
- A2 — Tylko Hawk
- A3 — PowerMatic + Hawk
- A4 — Multi-brand z PM/Hawk
- A5 — Własna marka / OEM z Chin (KONKURENCJA)
- A6 — Multi-brand bez PM/Hawk (kandydaci do pozyskania)

**B (cross-sell, bez maszyn):**
- B1 — Tytoń liście (powinowactwo 5)
- B2 — Bibułki (5)
- B3 — Filtry/gilzy (5)
- B4 — Akcesoria (3)
- B5 — Shisha/hookah (2)
- B6 — E-papierosy/vape (2)
- B7 — Saszetki nikotynowe (2)
- B8 — Pełne hurtownie tytoniowe (**5**)
- B9 — CBD/konopie (4)

**Tier enum:** `wyłączność` / `autoryzowany` / `reseller` / `detalista` / `marketplace` / `producent` / `hurtownik`

**Wolumen progi per `rynek_skala`:**
- duży rynek (PL/CZ/FR): 50/500/5000 szt/m
- średni (RO/BG/HR/SI/SK): 20/200/1000
- mały (LT/LV/EE/MD): 10/50/300

→ szczegóły w `methodology.md` → „Słabe punkty #1"

## Co NIE robimy

- ❌ Nie nadpisujemy wierszy z istniejącego mastera bez Twojej akceptacji
- ❌ Nie dodajemy kolumn do naszego 37-schematu bez decyzji (każda nowa kolumna = zmiana kontraktu)
- ❌ Nie propagujemy do innych krajów (per-kraj independence)
- ❌ Nie pushujemy do GitHuba bez `verify-data` clean
