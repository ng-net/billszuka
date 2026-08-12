# Mapping PL — Twoje 25 kolumn → nasze 37 (master)

**Data:** 2026-08-10 · **Plik:** `data/_intake/PL/source.csv` · **Wierszy:** 376 (po odjęciu nagłówka)

> **Uwaga:** deklarowałeś 34 kolumny — faktycznie CSV ma **25 kolumn**. Poniżej mapowanie 25→37.

## Twoje 25 kolumn (intake) — diagnostyka

| # | Twoja kolumna | Twoja unikalna semantyka | Jakość | Decyzja |
|---|---|---|---|---|
| 1 | Rank | 1-377, brak znaczenia biznesowego | śmieć | **DROP** (do audytu) |
| 2 | Priorytet | A1/A2/B/C/D — Twój scoring | Twój system | **IGNORE** (per Twoja decyzja) → log do `zrodlo_danych` jako `user_orig_priorytet: X` |
| 3 | Score | 0-100, Twój scoring | Twój system | **IGNORE** → log do `zrodlo_danych` jako `user_orig_score: X` |
| 4 | Firma | Nazwa firmy | OK | **→ `nazwa_firmy`** |
| 5 | Relacja | 8 wariantów (reseller/partner/producent/cross-sell/BILLS/...) | enum Twój | **→ `tier`** (mapowanie niżej) |
| 6 | Segment | S1-S7 (RYO/hurtownie/akcesoria/vape/cygara/retail/pozostałe) | enum Twój | **IGNORE** (do re-klasyfikacji) → log `user_orig_segment: X` |
| 7 | Kanał | 10 wariantów (hurt/detal/marketplace/sieć/...) | enum Twój | **→ `kanal_sprzedaży`** (best-fit) |
| 8 | Województwo | Pełna nazwa PL | string | **→ `region_nazwa`** + lookup do `region_kod` (16 województw) |
| 9 | Miasto | String | string | **→ `miasto`** |
| 10 | Skala | Duży/Średni/Mały/Mały-średni/**235× "Nieustalona"** | Twój scoring, **62% brak** | **→ `wolumen`** + `confidence_wolumen=🔴` gdy brak |
| 11 | Email | 144/376 OK (38%), 232 brak | string | **→ `email`** |
| 12 | Telefon | z kierunkowym +48 | string | **→ `telefon`** |
| 13 | Osoba/Dział decyzyjny | Imię lub dział | string | **→ `decydent`** |
| 14 | Stanowisko | string | string | **→ `stanowisko`** |
| 15 | WWW | 317/376 OK, 57 brak | URL | **→ `www`** |
| 16 | Adres | "ul. X, 00-000 Miasto" | string | **→ `adres`** |
| 17 | NIP | 77/376 OK (20%), 299 brak | 10 cyfr, **0 checksum-fail** | **→ `nip_vat`** |
| 18 | KRS | 1/376 OK, 23/376 **wrong_len** (5-7 cyfr zamiast 8-10), 352 brak | **dirty** | **→ `rejestr_id`** z suffix `(?)` gdy wrong_len |
| 19 | Produkty/marki | lista pipe-separated | string | **→ `marki_nabijarki` (A)** lub **→ `notatki` (B)** |
| 20 | Status | **dirty — column shift**: ma NIP-y, KRS-y, kody pocztowe, "BILLS — hurt@bills.pl", "17" | **CHAOS** | **DROP column** — do rekonstrukcji z L0 |
| 21 | Owner | zawsze "BILLS — hurt@bills.pl" | constant | **DROP** — do `notatki` tylko jeśli inny |
| 22 | Następny krok | akcja (telefon + email tego samego dnia) | operational | **→ `notatki`** (merged) |
| 23 | Uzasadnienie potencjału | string, krótki | string | **→ `notatki`** (merged) |
| 24 | Źródła | URL-e pipe-separated | URL | **→ `zrodlo_danych`** |
| 25 | Uwagi | "Status źródłowy: X" + ewentualne notatki | string | **→ `notatki`** (merged) + ewentualnie do `flagi` |

## Klasyfikacja A/B (re-classify, IGNORE Twojego Segment)

**Logika:**

```
1. Czy Segment (Twój) jest S1 (RYO/MYO, gilzy i nabijarki)?
   TAK → KATALOG A (kandydat na A1-A6)
   NIE → KATALOG B (cross-sell)
2. Wewnątrz A — klasyfikuj wg Produkty/marki:
   - ma "PowerMatic" w produktach → A1 (lub A3 jeśli ma też Hawk)
   - ma "Hawk" w produktach → A2 (lub A3 jeśli ma też PowerMatic)
   - ma "nabijarki & zwijarki" / "rolling machin" + wiele marek → A4 (multi-brand z PM/Hawk jeśli mają)
   - ma "własna marka" / "OEM" / "Dark Horse" / "Mascotte" / "Gerui" → A5
   - multi-brand bez PM/Hawk → A6
3. Wewnątrz B — klasyfikuj wg Segment:
   - S2 (Hurtownie FMCG) → B8 (powinowactwo 5)
   - S3 (Akcesoria/headshop) → B4 (3)
   - S4 (Vape) → B6 (2)
   - S5 (Cygara/trafiki premium) → B4 lub B5 (3 lub 2)
   - S6 (Retail/e-commerce) → B4 (3)
   - S7 (Niezweryfikowane) → B9 lub DO-WERYFIKACJI
4. Jeśli Segment=S1 ale Produkty bez słowa "nabijarka" → A4 lub A6
   (RYO reseller, multi-brand)
```

## Tier (z Relacja)

| Twoja `Relacja` | Nasz `tier` |
|---|---|
| `Potencjalny reseller / odbiorca hurtowy` | `reseller` |
| `Partner dystrybucyjny/importer` | `autoryzowany` |
| `Partner strategiczny / producent` | `producent` |
| `Partner strategiczny / możliwy konflikt produktowy` | `konkurent` (niestety nie ma w enum — flaga 🔴) |
| `Partner cross-sell / kanał sąsiedni` | `hurtownik` |
| `Sprzedawca detaliczny/e-commerce` | `detalista` |
| `Do weryfikacji` | `marketplace` (best guess) + flaga 🔍 |
| `Wykluczyć — podmiot własny BILLS` | **EXCLUDE** (już mamy w katalogu) |

## Kanał sprzedaży (z Kanał)

| Twój `Kanał` | Nasz `kanal_sprzedaży` |
|---|---|
| `Hurt ogólnopolski` | `B2B only` |
| `Hurt B2B + detal` | `mix` |
| `Hurt B2B regionalny` | `B2B only` |
| `Importer/dystrybutor krajowy` | `B2B only` |
| `Detal/e-commerce` | `własny e-commerce` |
| `Sieć detaliczna/omnichannel` | `mix` |
| `Producent` | `mix` (jeśli mają własny e-commerce) / `B2B only` (jeśli tylko hurt) |
| `Producent/importer/dystrybutor` | `mix` |
| (puste) | **DO-WERYFIKACJI** |

## Województwo → `region_kod`

Polska = 16 województw. Lookup table (znasz lepiej niż ja):

| Twoja `Województwo` | Nasz `region_kod` | `region_nazwa` |
|---|---|---|
| Dolnośląskie | DS | dolnośląskie |
| Kujawsko-pomorskie | KP | kujawsko-pomorskie |
| Lubelskie | LB | lubelskie |
| Lubuskie | LB | lubuskie (kolizja z LB lubelskie — patrz niżej) |
| Łódzkie | LD | łódzkie |
| Małopolskie | MA | małopolskie |
| Mazowieckie | MZ | mazowieckie |
| Opolskie | OP | opolskie |
| Podkarpackie | PK | podkarpackie |
| Podlaskie | PD | podlaskie |
| Pomorskie | PM | pomorskie |
| Śląskie | SL | śląskie |
| Świętokrzyskie | SK | świętokrzyskie |
| Warmińsko-mazurskie | WM | warmińsko-mazurskie |
| Wielkopolskie | WP | wielkopolskie |
| Zachodniopomorskie | ZP | zachodniopomorskie |
| Ogólnopolska / Ogólnokrajowy | (puste) | (puste) |
| (puste) | (puste) | (puste) |

> **Uwaga:** brak kodu dla `LB` — bo lubuskie i lubelskie mają tę samą literę. W naszym masterze mamy konwencję: `LB` = lubuskie (historycznie), lubelskie = `LU`. Sprawdzić w DZIENNIK.md → REGION.

## Wolumen (ze Skala, 62% brak)

| Twoja `Skala` | Nasz `wolumen` | `confidence_wolumen` |
|---|---|---|
| `Duży` / `Duża` | `duży` | 🟢 |
| `Średni` / `Średnia` | `średni` | 🟢 |
| `Mały–średni` | `średni` | 🟡 |
| `Mały` | `mały` | 🟢 |
| `Nieustalona` / puste | (puste) | 🔴 |
| (dziwne: `BILLS — hurt@bills.pl`, `mm f/...`) | (puste) | 🔴 |

> **PL = duży rynek → progi: 50/500/5000 szt/m.** Jeśli Skala=`Duży` i mamy NIP+pracownicy z KRS, to wolumen pewny. Bez danych = 🔴.

## Decyzja per kolumna (podsumowanie)

| Operacja | Kolumny |
|---|---|
| **1:1 do mastera** | Firma, Email, Telefon, Osoba/Dział, Stanowisko, WWW, Adres, NIP, KRS, Miasto, Źródła |
| **Map z enum** | Relacja→tier, Kanał→kanal_sprzedaży, Województwo→region_kod, Skala→wolumen, Produkty→marki_nabijarki(A) lub notatki(B) |
| **IGNORE (log do zrodlo_danych)** | Rank, Priorytet, Score, Segment |
| **DROP (śmieć)** | Status (column shift), Owner (constant), Następny krok (do notatki) |
| **→ notatki (merged)** | Uzasadnienie + Uwagi + Następny krok + fragmenty Status |
| **SPECJALNIE** | "Wykluczyć — podmiot własny BILLS" → **EXCLUDE** (mamy już w masterze) |

## Co wyrzucamy (NOT do merge)

- ❌ Row #1 (BILLS — już w katalogu z `user_orig_relacja = "Wykluczyć — podmiot własny BILLS"`)
- ❌ Rows z `user_orig_priorytet = "D — niski priorytet/wykluczyć"` (78 szt) — ale **tylko jeśli** w Kolumnie Relacja jest `Do weryfikacji` i brak NIP+WWW
- ❌ Rows z column-shift errors (segment zawiera `FOREST GREEN`, `tan papierosy`, etc) — do manual review

## Co zostawiamy (do re-klasyfikacji)

Wszystkie 376 wierszy przejdą przez:
1. **Re-classify** (heurystyka powyżej)
2. **L0 verify** (NIP checksum → KRS API name-match → VIES)
3. **Cleanup** (deduplikacja po NIP/nazwa+miasto, normalizacja adresu)
4. **Output** = `data/_intake/PL/normalized_A.csv` + `data/_intake/PL/normalized_B.csv`

## Następne kroki (po Twojej akceptacji)

1. ⏳ Czekam na **OK od Ciebie** na powyższe mapowanie
2. ▶️ Odpalam `normalize_PL.py` (auto-mapper)
3. 📊 Pokazuję **diff vs istniejący `data/Polska/catalog-A-PL.csv` + `catalog-B-PL.csv`**
4. 📈 Pokazuję **hallucination audit** (ile % wierszy ma NIP/KRS mismatch, dead email, itp)
5. ✅ Po Twoim OK → merge do mastera → verify_run
