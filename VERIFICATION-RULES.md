# Zasady weryfikacji: NIP / KRS / VAT

> Powstało po incydencie 2026-08-31: 19/129 wpisów PL-B miało NIP nieistniejący
> (checksum invalid), a `verify_api.py` mimo to ustawiał `FROZEN`. Te zasady mają
> to uniemożliwić na stałe — implementuj jako gate w `verify_api.py`, nie tylko
> jako dokumentację.

## 0. Kolejność sprawdzania — zawsze w tej samej kolejności

1. **Walidacja formatu/checksumy — offline, przed jakimkolwiek API call.**
2. Zapytanie do rejestru podstawowego (CEIDG / KRS / ARES / etc.).
3. Porównanie nazwy + adresu z API vs to co jest w CSV (fuzzy match).
4. VAT/VIES — jako potwierdzenie dodatkowe, nie wymóg.
5. Klasyfikacja: `FROZEN` / `DO-WERYFIKACJI` / `INVALID_*`.

**Zasada żelazna:** brak odpowiedzi lub błąd API nigdy nie oznacza "prawdopodobnie
OK". Domyślny status przy niepewności to zawsze `DO-WERYFIKACJI`, nigdy `FROZEN`.
(To dokładnie ten bug, który wygenerował 19 fałszywych FROZEN w PL-B.)

---

## 1. Polska — NIP

### 1.1 Checksum (mod-11) — ZAWSZE przed wywołaniem API

NIP ma 10 cyfr, wagi kontrolne: `6,5,7,2,3,4,5,6,7`.

```python
def is_valid_nip(nip: str) -> bool:
    nip = nip.replace('-', '').replace(' ', '')
    if not (nip.isdigit() and len(nip) == 10):
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    checksum = sum(int(d) * w for d, w in zip(nip, weights)) % 11
    return checksum != 10 and checksum == int(nip[9])
```

- **Checksum fail → NIP to gwarantowana halucynacja/literówka.** Nie wołaj API
  w ogóle. Flaguj od razu `INVALID_CHECKSUM`.
- **Checksum OK, ale API zwraca inną firmę** → to inny typ błędu ("zły
  identyfikator", nie "fałszywy identyfikator"). Flaguj `MISMATCH_REGISTRY`,
  nigdy `FROZEN`.

### 1.2 CEIDG (tylko JDG i spółki cywilne)

- CEIDG **nie ma** sp. z o.o. / S.A. / sp.k. / sp.j. — brak wyniku dla
  poprawnego checksumu ≠ "firma nie istnieje", tylko "sprawdź KRS".
- HTTP 400 z `NIEPOPRAWNY_NUMER_NIP` = **numer nie istnieje**, nie "brak
  danych". Zawsze `DO-WERYFIKACJI`, nigdy `FROZEN`.

### 1.3 KRS (spółki)

- KRS API = **lookup po numerze, nigdy search po nazwie/NIP**.
- HTTP 404 na lookup = **numer KRS nie istnieje w rejestrze** — realny sygnał
  błędu, nie "spróbuj ponownie". Flaguj `INVALID_KRS`.
- **Nigdy nie ufaj `rejestr_id` z CSV bez potwierdzenia HTTP 200 + zgodności
  nazwy.** Wypełnione pole ≠ poprawny numer.
- KRS istnieje, ale nazwa nie pasuje → `MISMATCH_REGISTRY`, nigdy `FROZEN`.

### 1.4 Tabela klasyfikacji wyniku (implementować w `verify_api.py`)

| Sytuacja | Status | Nie rób |
|---|---|---|
| Checksum fail | `INVALID_CHECKSUM` | Nie wołaj API |
| API 400/404 na poprawnym formacie | `INVALID_ID` | Nie ustawiaj `FROZEN` |
| API 200, nazwa/adres nie pasuje | `MISMATCH_REGISTRY` | Nie ustawiaj `FROZEN` |
| API 200, nazwa+adres pasują (≥ próg fuzzy match) | `FROZEN` | — |
| Brak wyniku mimo poprawnego checksumu (np. sp. z o.o. w CEIDG) | przejdź do kolejnego rejestru | Nie kończ na "brak danych" |

---

## 2. VAT / VIES (dowolny kraj UE)

- VIES sprawdza tylko firmy zarejestrowane jako **podatnik VAT-UE**. Wynik
  `None` **nie znaczy, że firma nie istnieje** — może być zwolniona z VAT albo
  nie handlować wewnątrzunijnie.
- **Nie flaguj braku VIES jako błędu, jeśli rejestr krajowy (ARES/KRS/AJPES
  itd.) już potwierdził firmę.** VIES to potwierdzenie dodatkowe, nie wymóg.
- Format = prefix kraju (2 litery) + numer krajowy. Nie walidować checksumu
  ręcznie — VIES robi to za ciebie.

---

## 3. Adresy — osobna kategoria ryzyka (nie mylić z halucynacją identyfikatora)

- Rejestr może potwierdzić NIP/IČO/KRS + nazwę, ale adres bywa inny (np. w CZ
  živnostník ma "místo podnikání" ≠ adres zamieszkania).
- **Niezgodność adresu przy zgodnym identyfikatorze+nazwie ≠ automatyczna
  halucynacja.** Flaguj osobno `ADDRESS_MISMATCH`, dopuszczalny `FROZEN` z
  notatką — to inny poziom ryzyka niż zły NIP/KRS.

---

## 4. Skala pracy vs strategia weryfikacji — progi per grupa krajów

Progi mówią **kiedy przejść** z ręcznej weryfikacji → skrypt z spot-check →
w pełni automatyczny pipeline. Niższe progi tam, gdzie rejestr nie ma
darmowego/pełnego API (koszt ręcznej pracy na firmę jest wyższy, więc
automatyzacja opłaca się szybciej).

| Grupa krajów | Manual (1-po-1) | Batch (skrypt + spot-check) | Pełna automatyzacja (pipeline + audyt) |
|---|---|---|---|
| **PL, CZ, FR** — dojrzałe darmowe API (KRS/CEIDG/ARES/annuaire-entreprises) | <50 firm | 50–500 firm | 500+ firm |
| **RO, BG, HR, SI, SK, RS** — agregatory/web-only, brak lub słabe darmowe API | <20 firm | 20–200 firm | 200+ firm |
| **LT, LV, EE, MD** — API niszowe/niekompletne (brak name-search, UUID refs) | <5 firm | 5–50 firm | 50+ firm |

**Jak stosować:**
- **Poniżej progu manual** → sprawdzaj każdą firmę osobno (API call +
  web_search), dokumentuj ręcznie w `DZIENNIK.md`.
- **W paśmie środkowym** → napisz/dopracuj `tools/{iso}_verify.py`, ale zawsze
  spot-check ~10% wyników ręcznie przed uznaniem batcha za wiarygodny.
- **Powyżej górnego progu** → wymagany pipeline (`verify_run.py` routing przez
  `COUNTRY_API`) **plus obowiązkowy audyt losowej próbki po każdym uruchomieniu**
  — 100% automatycznych `FROZEN` bez audytu to dokładnie to, co wygenerowało
  19 fałszywych PL-B.

---

## 5. Krytyczna zasada anty-halucynacyjna

`FROZEN` wolno ustawić **tylko** gdy wszystkie trzy warunki są spełnione:

1. Checksum/format lokalny przeszedł (jeśli dotyczy, np. PL NIP).
2. Zapytanie do oficjalnego rejestru zwróciła HTTP 200 z realnymi danymi
   (nie pustym wynikiem, nie błędem interpretowanym jako "OK").
3. Nazwa firmy z rejestru fuzzy-matchuje nazwę z CSV (ustalony próg
   podobieństwa, np. Jaccard ≥ 0.5 lub zawieranie substring).

VIES / adres to potwierdzenia dodatkowe — ich brak nie blokuje `FROZEN`, ale
ich **niezgodność z NIP/KRS/IČO** blokuje zawsze.

Jeśli którykolwiek z warunków 1–3 zawiedzie → **nigdy `FROZEN`**, zawsze
`DO-WERYFIKACJI` z konkretnym kodem powodu: `INVALID_CHECKSUM` /
`INVALID_ID` / `MISMATCH_REGISTRY` / `ADDRESS_MISMATCH`.

**Zakaz:** interpretować brak odpowiedzi lub błąd API jako "prawdopodobnie OK"
i domyślnie ustawiać `FROZEN`. Domyślny stan przy niepewności = zawsze
`DO-WERYFIKACJI`.

---

## 6. Reszta krajów — zasady per kraj

**Zasada ogólna dla wszystkich poniżej:** stosuj tę samą tabelę klasyfikacji co
w §1.4 (checksum → API → fuzzy match nazwy → `FROZEN`/`DO-WERYFIKACJI`/`INVALID_*`).
Różnica jest tylko w: (a) czy formalny checksum istnieje i jak pewny jest jego
wzór, (b) jaki jest rejestr podstawowy, (c) jakie są country-specific pułapki
(pełny opis w `RUNBOOK.md`, tu tylko to co wpływa na klasyfikację).

**Ważne — poziom pewności checksumów poniżej jest różny.** Tam gdzie piszę
"pewność: średnia/niska" — **przetestuj wzór na 2-3 znanych, potwierdzonych
numerach z rejestru zanim wstawisz go do `verify_api.py`** (dokładnie tak jak
zrobiliście z BILLS NIP jako ground truth dla PL). Wdrożenie niepewnego
checksumu jest gorsze niż jego brak — może dawać fałszywe `INVALID_CHECKSUM`
na poprawnych numerach.

### 🇨🇿 CZ / 🇸🇰 SK — IČO (8 cyfr)

- **Checksum (pewność: wysoka dla CZ, średnia dla SK — sprawdź na przykładzie):**
  wagi `8,7,6,5,4,3,2` na cyfrach 1-7, `suma mod 11` → jeśli reszta `0` to
  cyfra kontrolna `1`; jeśli `1` to `0`; inaczej `11 - reszta` (a `10` → `0`).
  Ostatnia cyfra IČO musi się zgadzać.
- Rejestr podstawowy: ARES (CZ, no-auth, zwraca też finanční údaje) / ORSR (SK,
  tylko HTML formularz, brak JSON).
- **CZ-specific:** ARES zwraca dane dla żywnostników pod adresem "místo
  podnikání", który może różnić się od adresu w CSV — to `ADDRESS_MISMATCH`,
  nie `INVALID_ID` (patrz §3).
- **SK-specific:** brak API do lookup po nazwie — IČO trzeba najpierw znaleźć
  przez web_search, więc `INVALID_CHECKSUM` łap **przed** web_searchem, żeby
  nie tracić czasu na szukanie numeru, który i tak jest fabrykatem.

### 🇷🇴 RO — CUI

- **Checksum (pewność: średnia-wysoka):** klucz `7,5,3,2,1,7,5,3,2` mnożony
  przez cyfry CUI (bez cyfry kontrolnej), suma mod 11 → jeśli `10` cyfra
  kontrolna `0`, inaczej równa resztek.
- Rejestr: ONRC jest płatny (8 lei/odpis) — **nie traktuj braku dostępu do
  ONRC jako `INVALID_ID`.** Użyj darmowych agregatorów (termene.ro,
  listafirme.ro) do potwierdzenia nazwy+adresu, ale oznacz wynik jako
  `FROZEN (aggregator-confirmed)`, niżej priorytet zaufania niż ONRC bezpośrednio.
- Format rejestrowy `J40/1234/2005` (sąd/numer/rok) ≠ CUI — nie mylić przy
  walidacji, to dwa różne pola.

### 🇧🇬 BG — EIK/Bulstat

- **Checksum: pewność niska — algorytm różni się dla 9- i 13-cyfrowego EIK i
  jest bardziej złożony (dwupasmowy mod-11).** Nie hardkoduj własnej
  implementacji bez przetestowania na min. 3 znanych EIK z portal.justice.bg.
  Do czasu weryfikacji: polegaj wyłącznie na dopasowaniu w rejestrze
  (`MISMATCH_REGISTRY` jako jedyny tryb błędu, bez `INVALID_CHECKSUM`).
- Rejestr: portal.justice.bg (nazwa+status+zarząd), НАП (nap.bg) dla statusu
  DDS/VAT.

### 🇭🇷 HR — OIB (11 cyfr)

- **Checksum (pewność: wysoka):** ISO 7064 MOD 11-10. Standardowy,
  dobrze udokumentowany algorytm — bezpiecznie zaimplementować.
- Rejestr: sudreg.pravosudje.hr (podstawowy + upadłości), FINA (finansowy),
  porezna-uprava.hr (PDV/VAT status).

### 🇸🇮 SI — davčna številka (8 cyfr)

- **Checksum (pewność: średnia):** wagi `8,7,6,5,4,3,2`, suma mod 11 → analogicznie
  do CZ/SK (reszta `0`→`1`, reszta `1`→ numer niepoprawny/`10`, inaczej
  `11 - reszta`). Przetestuj na znanym numerze z AJPES przed wdrożeniem.
- Rejestr: AJPES — jedyne źródło, ale daje wszystko w jednym miejscu (dane +
  bilans + RZiS), więc `FROZEN` z AJPES jest wysokiej jakości gdy przechodzi.

### 🇷🇸 RS — PIB (9 cyfr) / matični broj (8 cyfr)

- **Checksum: pewność niska.** PIB podobno ma cyfrę kontrolną mod-11, ale nie
  mieliśmy okazji potwierdzić wzoru na żywym przykładzie. **Do czasu
  potwierdzenia: traktuj RS jako kraj bez formalnego checksumu** — jedyna
  bramka to zgodność z rejestrem APR (poza scope per AGENTS.md, więc i tak
  większość RS = `DO-WERYFIKACJI` z definicji, nie z powodu checksumu).
- Widoczny format problem: część PIB w CSV ma spację w środku numeru —
  to błąd formatu wejściowego, nie halucynacja; normalizuj (usuń spacje)
  przed próbą walidacji.

### 🇱🇹 LT — įmonės kodas (9 cyfr)

- **Checksum: pewność niska** — nie mam pewnego wzoru wag dla litewskiego
  kodu. **Nie implementuj offline checksumu bez potwierdzenia** — jedyna
  bramka to `ja_kodas` lookup w `get.data.gov.lt` (brak name-search, patrz
  RUNBOOK). Brak odpowiedzi z tego API = `INVALID_ID` (numer nie istnieje w
  otwartych danych), ale **nie** = "firma nie istnieje" — sprawdź manualnie
  rekvizitai.vz.lt (za Cloudflare, więc tylko ręcznie) przed odrzuceniem.

### 🇱🇻 LV — reģistrācijas numurs (11 cyfr)

- **Checksum: brak jawnie potwierdzonego prostego wzoru.** Polegaj wyłącznie
  na dopasowaniu w UR (info.ur.gov.lv) lub Lursoft. Bez formalnego
  checksumu, `INVALID_CHECKSUM` nie istnieje jako kategoria dla LV — tylko
  `MISMATCH_REGISTRY` / `FROZEN`.

### 🇪🇪 EE — registrikood (8 cyfr)

- **Brak prostego checksumu** — pierwsza cyfra koduje formę prawną (np. `1` =
  spółka prywatna), ale to nie jest cyfra kontrolna.
- Rejestr: `ariregister.rik.ee` autocomplete **działa tylko po nazwie, nie po
  kodzie** (patrz RUNBOOK) — nie próbuj walidować przez query po numerze,
  zawsze szukaj po nazwie i porównuj zwrócony `registrikood` z CSV.

### 🇫🇷 FR — SIREN (9 cyfr) / SIRET (14 cyfr)

- **Checksum (pewność: wysoka):** algorytm Luhna (mod 10) na obu numerach.
  **Wyjątek:** jednostki La Poste (SIREN zaczynający się `356000000`) legalnie
  łamią Luhna — nie flaguj ich jako `INVALID_CHECKSUM` automatycznie, sprawdź
  prefix przed odrzuceniem.
- Rejestr: `annuaire-entreprises.data.gouv.fr` (darmowy, oficjalny) jako
  pierwszy wybór; Pappers.fr (paid) tylko gdy potrzebny bilans.

### 🇲🇩 MD — IDNO (13 cyfr, poza UE)

- **Checksum: brak potwierdzonego wzoru.** Polegaj wyłącznie na
  `cis.gov.md`. Poza UE = brak VIES jako potwierdzenia dodatkowego — o jeden
  poziom weryfikacji mniej niż reszta krajów, uwzględnij to przy ocenie
  pewności `FROZEN` (traktuj MD `FROZEN` jako słabszy niż PL/CZ/FR `FROZEN`).

---

## 7. Skrócona tabela: co jest pewne, a co wymaga ostrożności

> **Live testy 2026-08-31 06:21 (per §7 — testowane na real numerach z
> katalogów BILLSzuka):** poniższa tabela zawiera wyniki weryfikacji
> implementacji poszczególnych wzorów checksumów.

| Kraj | Formalny checksum offline | Pewność wzoru | Live test (% pass) | Decyzja implementacji |
|---|---|---|---|---|
| PL | ✅ mod-11 NIP (wagi 6-7) | wysoka | 8/8 (100%) | ✅ Zaimplementowany, przetestowany |
| CZ | ✅ mod-11 IČO (wagi 8-2) | wysoka | 8/9 (89%) | ✅ Zaimplementowany, 1 znany edge case: G8 point s.r.o. (IČO 06941281, ARES potwierdza firmę ale mod-11 fail) |
| HR | ✅ ISO 7064 MOD 11,10 | wysoka | 11/11 (100%) | ✅ Zaimplementowany, przetestowany (10 real OIB + python-stdnum example) |
| FR | ✅ Luhn (wyjątek La Poste `356000000`) | wysoka | 3/3 (100%) | ✅ Zaimplementowany, La Poste bypass dodany |
| RO | ✅ klucz 7-5-3-2-1-7-5-3-2 | średnia-wysoka | N/A (wszystkie RO w katalogu mają 2-8 cyfr) | ⚠️ Zaimplementowany warunkowo (tylko 9+ cyfr; krótsze = format-check only) |
| SK | ❌ NIE implementujemy (wzór CZ-owy daje 3/26 = 12% pass) | — | 3/26 (12%) | ❌ Tylko format-check — 23/26 real IČ DPH failują mod-11 w stylu CZ, więc wzór jest inny niż CZ. Zostawiamy sprawdzenie w VIES |
| SI | ❌ NIE implementujemy (wzór CZ-owy daje 13/16 = 81% pass ale DELO PRODAJA + MOMBLY fail) | — | 13/16 (81%) | ❌ Tylko format-check — DELO PRODAJA (duża real firma) i MOMBLY d.o.o. nie przechodzą mod-11 w stylu CZ. Wzór SI davčna jest inny niż CZ. Zostawiamy AJPES |
| BG | ❌ NIE implementujemy (algorytm dwupasmowy mod-11, złożony) | — | — | ❌ Tylko format-check + `portal.justice.bg` lookup |
| RS | ❌ NIE implementujemy (wzór niepotwierdzony) | — | — | ❌ Tylko format-check (po normalizacji spacji) + APR |
| LT | ❌ NIE implementujemy (wzór wag niepotwierdzony) | — | — | ❌ Tylko format-check + `get.data.gov.lt` ja_kodas lookup |
| LV | ❌ NIE implementujemy (brak znanego wzoru) | — | — | ❌ Tylko format-check + UR/Lursoft lookup |
| EE | ❌ NIE implementujemy (pierwsza cyfra to forma prawna, nie checksum) | — | — | ❌ Tylko format-check + szukaj po nazwie → `registrikood` |
| MD | ❌ NIE implementujemy (wzór niepotwierdzony) | — | — | ❌ Tylko format-check + `cis.gov.md` lookup |

**Reguła praktyczna:** dla krajów bez pewnego checksumu, `INVALID_CHECKSUM`
jako kategoria po prostu nie istnieje — cała odpowiedzialność za łapanie
halucynacji spada na krok "zgodność z rejestrem" (`MISMATCH_REGISTRY`). To
znaczy, że dla LV/EE/MD/LT/RS/BG/SK/SI **spot-check ręczny w batch tier (§4) jest
ważniejszy niż dla PL/CZ/FR/HR/RO** — nie ma taniej bramki offline, która
złapie fabrykat przed wywołaniem API.

**Dlaczego niektóre checksumy NIE są implementowane mimo „działających" live testów:**
Wdrożenie niepewnego checksumu jest **gorsze niż jego brak**, bo może
generować fałszywe `INVALID_CHECKSUM` na poprawnych numerach. SK ma 12% pass
rate (3/26), SI ma 81% ale realne duże firmy (DELO PRODAJA, MOMBLY) fail.
Dla tych krajów lepiej jest polegać na cross-check z rejestrem
(`MISMATCH_REGISTRY` / `FROZEN`) niż na niestabilnym offline checksum.
Zasada: **nie implementuj checksumu dopóki nie masz 100% pass rate na min.
3 znanych, real numerach** — i to wciąż nie gwarantuje, że nie złapie false
positive (jak G8 point w CZ), więc dla SK/SI/BG/etc. wolimy nie ryzykować.

---

## Changelog

| Data | Zmiana |
|---|---|
| 2026-08-31 | v1 — spisano po incydencie 19 hallucinated NIP w PL-B + bug w `verify_api.py` (błędna klasyfikacja `NIEPOPRAWNY_NUMER_NIP` jako `FROZEN`) |
| 2026-08-31 | v2 — dodano zasady dla CZ/SK/RO/BG/HR/SI/RS/LT/LV/EE/FR/MD + tabela pewności checksumów |
| 2026-08-31 | v3 — live test na real numerach (Mavis): PL/HR/CZ/FR zaimplementowane, RO warunkowo, SK/SI/BG/EE/LV/LT/MD/RS świadomie tylko format-check. Tabela §7 zaktualizowana z % pass rate. Nowe testy: `tests/test_verify_principles.py` (65 testów), `tests/test_verify_run_hallucination.py` (19 testów). Edge case: G8 point s.r.o. (ARES potwierdza firmę ale IČO 06941281 fail mod-11) udokumentowany |
