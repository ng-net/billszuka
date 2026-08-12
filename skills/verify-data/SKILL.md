# Skill: BILLSzuka — Weryfikacja Danych

## Kiedy używać

Uruchom po **każdym** zapisie nowych danych do `data/{Kraj}/*.csv` lub `data/master.csv`. Nie zależnie od tego czy nowy wpis czy edycja istniejącego.

## Źródło prawdy (master)

`data/master.csv` — agregat wszystkich wpisów ze wszystkich krajów (35 kolumn). Każdy wpis ma unikalne `id_unikalne` w formacie `{KOD}-{A|B}-{NNN}` (np. `PL-A-001`, `CZ-B-012`).

**Regeneracja master.csv** (po każdej edycji per-kraj):

```bash
python3 tools/billszuka.py compile
```

## Struktura plików (per-kraj)

```
data/
├── master.csv                    # agregat — źródło prawdy dla analizy
├── audit-log.md                  # historia weryfikacji
├── relationships.csv             # krawędzie grafu relacji (korporacyjne + łańcuch dostaw)
├── relationships-audit.md        # historia weryfikacji relacji
├── README.md                     # schemat kolumn + konwencje
├── Polska/                       # PL — katalog A + B + dziennik
│   ├── PL.md
│   ├── catalog-A-PL.csv
│   └── catalog-B-PL.csv
├── Czechy/                       # CZ
│   ├── CZ.md
│   ├── catalog-A-CZ.csv
│   └── catalog-B-CZ.csv
├── Bułgaria/  Chorwacja/  Estonia/  Francja/  Litwa/  Łotwa/
├── Mołdawia/  Rumunia/  Słowacja/  Słowenia/
└── verification/                 # raporty weryfikacji
```

## Co to robi

1. Przechodzi przez wszystkie nowe / zmienione wpisy w **per-kraj CSV** (`data/{Kraj}/catalog-*.csv`) i/lub w `data/master.csv`
2. Dla każdego wpisu: ocenia **źródło** i **pewność** danych
3. Dodaje status: `✅ FROZEN` / `⚠️ DO-WERYFIKACJI`
4. Zapisuje wynik do `data/audit-log.md`

---

## Zasady statusu

### ✅ FROZEN

Wpis jest zweryfikowany i **nie podlega halucynacji**. Spełnia WSZYSTKIE:

- Dane podstawowe (nazwa, NIP, KRS, adres) pochodzą z **oficjalnego źródła publicznego**
- Dodatkowe info (tier, marki, wolumen) potwierdzone przez ≥1 niezależne źródło (WWW firmy, Allegro, LinkedIn, recenzje)
- Wpis nie był zmieniany od ostatniej weryfikacji
- Istnieje logiczna spójność między polami (np. hurtownia z 100+ sklepami = wolumen duży)

**Źródła oficjalne (automatycznie FROZEN):**
- KRS API / KRS.gov.pl
- CEIDG API / CEIDG.gov.pl
- VIES (walidacja VAT-EU)
- Organy celne (KAS), oficjalne rejestry sądowe
- Rejestr REGON

**Źródła pół-oficjalne (wymagają dodatkowego potwierdzenia):**
- Allegro/OLX — widać firmę, ale brak pełnych danych rejestrowych
- Google Maps / wizytówki — adres OK, ale brak NIP/KRS
- Panoramafirm.pl, pkt.pl — agregatory, mogą być nieaktualne
- LinkedIn — weryfikacja osób, nie firm

**Nigdy FROZEN bez dodatkowego potwierdzenia:**
- Tylko "web search" / "wyszukiwarka"
- Tylko Facebook
- Samo KRS bez adresu lub na odwrót

### ⚠️ DO-WERYFIKACJI

Wpis jest w pracy — może być poprawny, może nie. Oznacza: "zapisz, ale nie buduj na tym strategii dopóki nie zweryfikujesz".

**Automatycznie DO-WERYFIKACJI:**
- Tylko jedno źródło danych
- Brak NIP lub KRS
- Konflikt między polami (np. "reseller" + "10M kapitału" + "1 pracownik")
- Puste kluczowe pola: adres, www, email, telefon
- Marki_nabijarki = "do weryfikacji"

---

## Pola wymagane do FROZEN

Dla każdego wpisu w CSV — FROZEN wymaga WSZYSTKICH poniższych:

| Pole | Wymaganie |
|---|---|
| `nazwa_firmy` | Zgodna z KRS lub CEIDG |
| `nip_vat` | Zweryfikowany w VIES lub KRS/CEIDG |
| `rejestr_id` | KRS lub CEIDG numer |
| `adres` | Zgodny z rejestrem lub Google Maps |
| `zrodlo_danych` | ≥1 źródło oficjalne |

**Opcjonalne ale mocne:**
- `www` = strona firmy (potwierdza nazwę + adres)
- `telefon` = z wizytówki Google lub strony
- `email` = z strony firmy

---

## Proces

### Krok 1: Lista zmian

Porównaj obecny stan (per-kraj CSVs + master.csv) z poprzednią wersją. Zidentyfikuj:
- Nowe wpisy w `data/{Kraj}/catalog-*.csv` (od ostatniej weryfikacji)
- Zmienione wpisy (którekolwiek pole zmienione) w per-kraj CSV
- Rozbieżności między per-kraj CSV a `master.csv` (master musi być zregenerowany po edycji)

Per-kraj ścieżki do sprawdzenia (24 pliki):

```
data/Polska/catalog-A-PL.csv      data/Polska/catalog-B-PL.csv
data/Czechy/catalog-A-CZ.csv      data/Czechy/catalog-B-CZ.csv
data/Bułgaria/catalog-A-BG.csv    data/Bułgaria/catalog-B-BG.csv
data/Chorwacja/catalog-A-HR.csv   data/Chorwacja/catalog-B-HR.csv
data/Estonia/catalog-A-EE.csv     data/Estonia/catalog-B-EE.csv
data/Francja/catalog-A-FR.csv     data/Francja/catalog-B-FR.csv
data/Litwa/catalog-A-LT.csv       data/Litwa/catalog-B-LT.csv
data/Łotwa/catalog-A-LV.csv       data/Łotwa/catalog-B-LV.csv
data/Mołdawia/catalog-A-MD.csv    data/Mołdawia/catalog-B-MD.csv
data/Rumunia/catalog-A-RO.csv     data/Rumunia/catalog-B-RO.csv
data/Słowacja/catalog-A-SK.csv    data/Słowacja/catalog-B-SK.csv
data/Słowenia/catalog-A-SI.csv    data/Słowenia/catalog-B-SI.csv
```

Wszystkie puste pliki (348 bytes = sam nagłówek) zlicz jako "0 wpisów, brak do weryfikacji".

### Krok 2: Ocena każdego wpisu

Dla każdego zmienionego/nowego wpisu:

1. Sprawdź źródło w `zrodlo_danych`
2. Zastosuj tabelę powyżej — FROZEN lub DO-WERYFIKACJI
3. Jeśli FROZEN: wpisz `✅ FROZEN` w kolumnie `flagi`
4. Jeśli DO-WERYFIKACJI: wpisz `⚠️ DO-WERYFIKACJI` w kolumnie `flagi`

### Krok 3: Aktualizuj CSV

Dodaj / zaktualizuj `flagi` w CSV dla każdego ocenionego wpisu.

### Krok 4: Zapisz audit log

Dodaj wpis do `data/audit-log.md`:

```
## YYYY-MM-DD HH:MM

### Pliki sprawdzone
- data/Polska/catalog-A-PL.csv: 4 wpisy
- data/Polska/catalog-B-PL.csv: 7 wpisów
- data/Czechy/catalog-A-CZ.csv: 3 wpisy
- (pozostałe 19 plików: 0 wpisów)

### ✅ FROZEN
- PL-X-XXX: [powód]

### ⚠️ DO-WERYFIKACJI
- PL-X-XXX: [co trzeba sprawdzić]
```

### Krok 5: Zaktualizuj master.csv

Jeśli którykolwiek per-kraj CSV został zaktualizowany w kroku 3 — przebuduj `data/master.csv` (komenda w sekcji "Źródło prawdy" wyżej). Wpisz w audit log: `master.csv: zregenerowany, X wierszy łącznie`.

---

## Zasada FROZEN — dlaczego

Gdy wpis jest FROZEN = "sprawdzone, prawdziwe, zapamiętane". Możesz na nim budować strategię bez obawy że Mavis kiedykolwiek "zmyśli" / "doprecyzuje" / "doda" informacji którego nie ma.

FROZEN = immunologia na halucynacje.

---

## Przykład audit log

```
## 2026-08-10 08:45

### ✅ FROZEN
- PL-A-001: KRS + NIP + strona www — wszystko zgodne, oficjalne źródła
- PL-B-004: CEIDG potwierdzony + polskagt.pl + koncesja KAS — 3 źródła

### ⚠️ DO-WERYFIKACJI
- PL-A-003: Tylko KRS, brak www/email/telefonu — do uzupełnienia
- PL-B-005: Tylko pkt.pl — KRS do sprawdzenia w KRS.gov.pl
- PL-B-007: Brak NIP/KRS — do weryfikacji CEIDG
```
