# BILLSzuka — Data directory

Pliki CSV z rekordami firm. Każdy kraj ma swój folder z 2 plikami CSV (A i B) + dziennikiem `.md`. Dodatkowo istnieje `master.csv` w katalogu głównym — agregat wszystkich wpisów ze wszystkich krajów. Relacje między firmami trzymane są **oddzielnie** w `relationships.csv`.

## Pliki

```
data/
├── master.csv                    # agregat — źródło prawdy dla analizy/BI
├── audit-log.md                  # historia weryfikacji
├── relationships.csv             # krawędzie grafu relacji (korporacyjne + łańcuch dostaw)
├── relationships-audit.md        # historia weryfikacji relacji
├── verification/                 # raporty weryfikacji
├── Polska/                       # PL
│   ├── PL.md                     # dziennik badawczy
│   ├── catalog-A-PL.csv          # firmy z nabijarkami (kategorie A1-A6)
│   └── catalog-B-PL.csv          # firmy branżowe bez nabijarek (B1-B9)
├── Czechy/                       # CZ (catalog-A-CZ.csv + catalog-B-CZ.csv + CZ.md)
├── Bułgaria/                     # BG
├── Chorwacja/                    # HR
├── Estonia/                      # EE
├── Francja/                      # FR
├── Litwa/                        # LT
├── Łotwa/                        # LV
├── Mołdawia/                     # MD
├── Rumunia/                      # RO
├── Słowacja/                     # SK
└── Słowenia/                     # SI
```

Kody {ISO} w nazwach plików CSV (PL, CZ, BG, HR, EE, FR, LT, LV, MD, RO, SK, SI).

## master.csv + relationships.csv

`data/master.csv` = zagregowany widok wszystkich wpisów ze wszystkich 12 folderów. Każdy wpis ma `id` w formacie `{KOD}-{A|B}-{NNN}` (np. `PL-A-001`, `CZ-B-012`). Przebudowa po każdej edycji per-kraj (`python3 tools/billszuka.py compile`).

`data/relationships.csv` = graf relacji (krawędzie). Schemat: `from_id,to_id,relation_type,direction,evidence,verified_date,notes`. Patrz DZIENNIK.md → Relacje.

Kody krajów w `id`: PL, CZ, SK, RO, LT, LV, EE, FR, MD, BG, SI, HR

## Schemat kolumn (unifikowany A i B — 35 kolumn)

| Kolumna | Typ | Opis |
|---|---|---|
| `related_to` | str | ID firm powiązanych po przecinku (sister firms, sukcesja, pokolenie). |
| `rok_zalozenia` | YYYY | Rok rejestracji (KRS/CEIDG). Wiek = bieżący rok − rok. |
| `id` | str | `{KOD}-{A\|B}-{NNN}`, np. `PL-A-001`, `CZ-B-012` |
| `kategoria` | enum | A1-A6 lub B1-B9 |
| `nazwa` | str | Pełna nazwa prawna lub handlowa |
| `kraj` | ISO2 | Dwuliterowy kod |
| `miasto` | str | |
| `adres` | str | Ulica + numer + kod |
| `nip_vat` | str | Lokalny odpowiednik NIP — patrz methodology.md per kraj |
| `rejestr_id` | str | KRS / IČO / ONRC / OIB itp. |
| `www` | str | Pełny URL lub `brak` |
| `kanal_zamiennik` | str | Co mają zamiast WWW: FB page, OLX, Allegro shop, wizytówka Google |
| `email` | str | Główny kontakt |
| `telefon` | str | Z numerem kierunkowym |
| `linkedin` | URL | Profil firmy |
| `facebook` | URL | Strona firmy |
| `instagram` | URL | Profil firmy |
| `tiktok` | URL | Profil firmy / profil TikTok |
| `tier` | enum | `wyłączność` / `autoryzowany` / `reseller` / `detalista` / `marketplace` / `producent` / `hurtownik` |
| `marki_nabijarki` | list | A: lista marek (PowerMatic, Hawk, Topomat, GM, Turbomatic, inne) |
| `marka_wlasna_oem` | str | A: nazwa marki własnej (lub puste) |
| `sourcing` | enum | Chiny / Europa / Polska / mix |
| `wolumen` | enum | mały / średni / duży (progi per `rynek_skala`) |
| `confidence_wolumen` | enum | 🟢 / 🟡 / 🔴 |
| `kanal_sprzedaży` | enum | B2B only / sklep stacjonarny / marketplace / własny e-commerce / mix |
| `powinowactwo_nabijarki` | int 1-5 | B: tylko (puste w A) |
| `cross_sell_potential` | enum | B: wysoki / średni / niski (puste w A) |
| `decydent` | str | Imię i nazwisko osoby decyzyjnej |
| `stanowisko` | str | CEO / właściciel / dyrektor sprzedaży / itp. |
| `email_decydent` | str | Bezpośredni email jeśli inny niż firmowy |
| `zrodlo_danych` | str | CEIDG, KRS, Facebook grupa X, OLX, targi Y, recenzja Z, link |
| `data_weryfikacji` | date | YYYY-MM-DD |
| `flagi` | list | Kombinacja 🔴/🟡/🟢/🐋/💎/✅/🔍 (+ flagi weryfikacji) |
| `notatki` | str | Dowolne obserwacje |
| `rynek_skala` | enum | Auto: `duży` (PL/CZ/FR) / `średni` (RO/BG/HR/SI/SK) / `mały` (LT/LV/EE/MD). Kalibruje progi wolumenu. |

## Konwencje

- **CSV UTF-8 z BOM** (polskie znaki w Excelu)
- **Separator**: przecinek
- **Cudzysłów**: `"..."` gdy wartość zawiera przecinek
- **Linie**: LF (nie CRLF)
- **Daty**: YYYY-MM-DD

## Wypełnianie

- **Minimum** dla każdego rekordu: `id`, `kategoria`, `nazwa`, `kraj`, `miasto`, JEDEN kontakt (email/tel/FB)
- **Pełne dane**: wszystkie kolumny, źródła zweryfikowane, flagi ustawione
- **Częściowe**: wypełnione kluczowe kolumny + notatka co jeszcze trzeba

## Flagi

| Flaga | Znaczenie |
|---|---|
| 🔴 | Konkurent bezpośredni (klon 1:1 z Chin) |
| 🟡 | Konkurent pośredni |
| 🟢 | Partner potencjalny |
| 🐋 | Big fish — najgrubszy gracz w kraju |
| 💎 | Gem — znaleziony off-internet (FB grupa, targi, OLX, opakowanie) |
| ✅ | Profil BILLS-like (import + dystrybucja + serwis) |
| 🔍 | Relacja z marką niezweryfikowana (default dla większości rekordów) |
| 📋 ORG-CEL | Zweryfikowane w dokumentach organów celnych |
| 🧾 FV-PDF | Zweryfikowane przez fakturę/CMR PDF |
| 📦 OPAKOWANIE | Zweryfikowane numerem seryjnym/plombą na opakowaniu |
| 🗣️ DEKLARACJA | Zweryfikowane publiczną deklaracją firmy |
| 📜 KONTRAKT | Zweryfikowane zewnętrzną informacją o umowie |

**Domyślnie nie wstawiamy flag weryfikacji** — większość rekordów ma `🔍` lub nic w sekcji weryfikacyjnej, bo nie mamy dostępu do listy umów BILLS. Flagi weryfikacji stosujemy tylko gdy znajdziemy pośrednie dowody (celne, faktury, opakowania, deklaracje).

## Wolumen — kiedy stosować

Wartości `mały / średni / duży` są zależne od rynku. Dla rynku ogólnego to 50/500/5000 szt/m. Dla rynku **niszowego** (nabijarki) realia to 20/100/200+. Szczegóły w `methodology.md` → "Słabe punkty #1".

Zawsze ustawiaj `confidence_wolumen`:
- 🟢 mam twarde dane
- 🟡 szacuję z pośrednich
- 🔴 zgaduję

## Powinowactwo (tylko Katalog B)

Skala 1-5, gdzie:
- **5** = klient niemal na pewno kupi nabijarkę
- **1** = marginalny overlap

Szczegóły per kategoria B1-B9 w `methodology.md`.

## Cross-sell potential (tylko Katalog B)

Trzy poziomy:
- **wysoki** — hurtownia/sklep z asortymentem pasującym 1:1
- **średni** — poboczny product, wymaga przekonywania
- **niski** — sprzedaż tylko jeśli klient sam szuka
