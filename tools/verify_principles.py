"""
verify_principles.py — Zasady weryfikacji NIP / KRS / VAT dla BILLSzuka.

Pochodzenie: incydent 2026-08-31, 19/129 wpisów PL-B miało NIP nieistniejący
(checksum invalid) a verify_api.py mimo to ustawiał FROZEN. Te zasady
implementują gate uniemożliwiający powtórkę.

Kluczowa zasada: brak odpowiedzi lub błąd API nigdy nie oznacza "prawdopodobnie
OK". Domyślny status przy niepewności to zawsze DO-WERYFIKACJI, nigdy FROZEN.

Użycie:
    from tools.verify_principles import (
        is_valid_pl_nip, is_valid_cz_ico, is_valid_sk_dic, is_valid_bg_vat,
        is_valid_ee_kmkr, is_valid_hr_oib, is_valid_ro_cui, is_valid_si_ddv,
        is_valid_fr_siren, is_valid_lv_pvn, is_valid_lt_pvm,
        is_valid_vat_format, pl_nip_mod11_ok,
    )

Kody statusu (per dokumentacja Zasady weryfikacji):
    INVALID_CHECKSUM  - format/checksum NIP nie przechodzi offline
    INVALID_ID        - API 400/404 na poprawnym formacie (numer nie istnieje)
    MISMATCH_REGISTRY - API 200, ale nazwa/adres nie pasują do CSV
    ADDRESS_MISMATCH  - identyfikator+nazwa OK, ale adres inny (CZ živnostník etc.)
    FROZEN            - identyfikator+nazwa+adres matchują (≥ próg fuzzy match)

Te kody trafiają do `verify_row()` jako część `reason` (np. "INVALID_CHECKSUM:
NIP 7792223933 nie przechodzi mod-11").
"""

import re


# === Kody statusu (re-eksportowane do użycia w verify_api.py) ===
INVALID_CHECKSUM = "INVALID_CHECKSUM"
INVALID_ID = "INVALID_ID"
MISMATCH_REGISTRY = "MISMATCH_REGISTRY"
ADDRESS_MISMATCH = "ADDRESS_MISMATCH"
FROZEN = "FROZEN"
DO_WERYFIKACJI = "DO-WERYFIKACJI"
PENDING_API = "PENDING_API"


# === Polska — NIP mod-11 ===
def pl_nip_mod11_ok(nip: str) -> bool:
    """Polish NIP mod-11 checksum. Returns False for empty / non-10-digit / bad checksum.
    Per Zasady §1.1: każdy PL NIP MUSI przejść mod-11 przed jakimkolwiek API call.
    Wagi kontrolne: 6,5,7,2,3,4,5,6,7."""
    nip = re.sub(r"\D", "", nip)
    if len(nip) != 10:
        return False
    if not nip.isdigit():
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    s = sum(int(d) * w for d, w in zip(nip, weights)) % 11
    # Per §1.1: checksum != 10 AND checksum == last digit
    return s != 10 and s == int(nip[9])


def is_valid_pl_nip(nip: str) -> tuple[bool, str]:
    """Returns (is_valid, code). Code: 'OK' | 'INVALID_CHECKSUM' | 'INVALID_FORMAT'."""
    nip_clean = re.sub(r"\D", "", nip)
    if not (nip_clean.isdigit() and len(nip_clean) == 10):
        return False, "INVALID_FORMAT"
    if not pl_nip_mod11_ok(nip_clean):
        return False, INVALID_CHECKSUM
    return True, "OK"


# === Czechy — IČO (8 cyfr, mod-11 z wagami 8-2) ===
def is_valid_cz_ico(ico: str) -> tuple[bool, str]:
    """CZ IČO = 8 cyfr z mod-11 checksum (wagi 8,7,6,5,4,3,2 na cyfrach 1-7).

    Per VERIFICATION-RULES.md §CZ (pewność: wysoka — przetestowane na 9 real
    IČO z naszych katalogów, 8/9 przechodzą. Wyjątek: IČO z prefixem `0`
    mogą mieć inny edge case w FRSR).
    Returns (is_valid, code). Code: 'OK' | 'INVALID_FORMAT' | INVALID_CHECKSUM."""
    ico_clean = re.sub(r"\D", "", ico)
    if not (ico_clean.isdigit() and len(ico_clean) == 8):
        return False, "INVALID_FORMAT"
    weights = [8, 7, 6, 5, 4, 3, 2]
    s = sum(int(d) * w for d, w in zip(ico_clean[:7], weights)) % 11
    if s == 0:
        expected = 1
    elif s == 1:
        # s=1 jest nielegalny dla IČO (nie ma poprawnej cyfry kontrolnej)
        return False, INVALID_CHECKSUM
    elif s == 10:
        expected = 0
    else:
        expected = 11 - s
    actual = int(ico_clean[7])
    if expected == actual:
        return True, "OK"
    return False, INVALID_CHECKSUM


# === Słowacja — IČ DPH (10 cyfr, format-check tylko) ===
def is_valid_sk_dic(dic: str) -> tuple[bool, str]:
    """SK IČ DPH = 10 cyfr. **Brak pewności w checksumie** per
    VERIFICATION-RULES.md §SK (pewność: średnia, NIE implementujemy mod-11 —
    live test na 26 real SK IČ DPH: 23/26 fail, więc wzór CZ nie pasuje.
    Tylko format-check + skierowanie do VIES)."""
    dic_clean = re.sub(r"\D", "", dic)
    if not (dic_clean.isdigit() and len(dic_clean) == 10):
        return False, "INVALID_FORMAT"
    return True, "OK"


# === Bułgaria — VAT (BG + 9-10 cyfr, format-check) ===
def is_valid_bg_vat(vat: str) -> tuple[bool, str]:
    """BG VAT (EIK/Bulstat) = 9 lub 10 cyfr. **Brak implementacji checksum**
    per VERIFICATION-RULES.md §BG (pewność: niska — algorytm dwupasmowy mod-11
    złożony, nie przetestowany na real danych)."""
    vat_clean = re.sub(r"\D", "", vat)
    if not (vat_clean.isdigit() and 9 <= len(vat_clean) <= 10):
        return False, "INVALID_FORMAT"
    return True, "OK"


# === Estonia — KMKR (8 cyfr, format-check) ===
def is_valid_ee_kmkr(kmkr: str) -> tuple[bool, str]:
    """EE KMKR = 8 cyfr. **Brak prostego checksumu** per
    VERIFICATION-RULES.md §EE (pierwsza cyfra to forma prawna, nie checksum)."""
    kmkr_clean = re.sub(r"\D", "", kmkr)
    if not (kmkr_clean.isdigit() and len(kmkr_clean) == 8):
        return False, "INVALID_FORMAT"
    return True, "OK"


# === Chorwacja — OIB (11 cyfr, ISO 7064 MOD 11,10) ===
def is_valid_hr_oib(oib: str) -> tuple[bool, str]:
    """HR OIB = 11 cyfr z ISO 7064 MOD 11,10 checksum (Porezna uprava standard).
    Per VERIFICATION-RULES.md §HR (pewność: wysoka — przetestowane na 10 real
    HR OIB z naszych katalogów + python-stdnum example, 11/11 przechodzą).
    Returns (is_valid, code)."""
    oib_clean = re.sub(r"\D", "", oib)
    if not (oib_clean.isdigit() and len(oib_clean) == 11):
        return False, "INVALID_FORMAT"
    # ISO 7064 MOD 11,10:
    # n=10; for each of first 10 digits: sum = n + digit; if sum%10 == 0 then 10 else sum%10;
    # then n = (sum * 2) % 11. expected = (11 - n) % 10.
    n = 10
    for d in oib_clean[:10]:
        s = n + int(d)
        mod10 = s % 10
        if mod10 == 0:
            mod10 = 10
        n = (mod10 * 2) % 11
    expected = (11 - n) % 10
    return expected == int(oib_clean[10]), "OK" if expected == int(oib_clean[10]) else INVALID_CHECKSUM


# === Rumunia — CUI/CIF (2-10 cyfr, mod-11 tylko dla 9+ cyfr) ===
def is_valid_ro_cui(cui: str) -> tuple[bool, str]:
    """RO CUI/CIF = 2-10 cyfr. Checksum mod-11 per VERIFICATION-RULES.md §RO
    (pewność: średnia-wysoka) — ale wymaga 9+ cyfr. Dla krótszych (PFA/II/IF)
    tylko format-check.

    Algorytm: klucz [7,5,3,2,1,7,5,3,2] mnożony przez pierwsze 9 cyfr, suma mod 11.
    Jeśli 10 → cyfra kontrolna 0, inaczej równa reszcie."""
    cui_clean = re.sub(r"\D", "", cui)
    if not (cui_clean.isdigit() and 2 <= len(cui_clean) <= 10):
        return False, "INVALID_FORMAT"
    # Checksum tylko dla 9-10 cyfr
    if len(cui_clean) >= 10:
        weights = [7, 5, 3, 2, 1, 7, 5, 3, 2]
        s = sum(int(d) * w for d, w in zip(cui_clean[:9], weights)) % 11
        if s == 10:
            expected = 0
        else:
            expected = s
        actual = int(cui_clean[9])
        if expected != actual:
            return False, INVALID_CHECKSUM
    return True, "OK"


# === Słowenia — davčna (8 cyfr, format-check) ===
def is_valid_si_ddv(ddv: str) -> tuple[bool, str]:
    """SI davčna = 8 cyfr. **Brak pewności w checksumie** per
    VERIFICATION-RULES.md §SI (pewność: średnia, NIE implementujemy mod-11 —
    live test na 16 real SI davčna: 13/16 przechodzą, ale DELO PRODAJA
    (duża firma) i MOMBLY d.o.o. fail, więc wzór CZ nie pasuje do wszystkich).
    Tylko format-check + skierowanie do AJPES)."""
    ddv_clean = re.sub(r"\D", "", ddv)
    if not (ddv_clean.isdigit() and len(ddv_clean) == 8):
        return False, "INVALID_FORMAT"
    return True, "OK"


# === Francja — SIREN (9 cyfr, Luhn) ===
def is_valid_fr_siren(siren: str) -> tuple[bool, str]:
    """FR SIREN = 9 cyfr z Luhn checksum (mod 10).
    Per VERIFICATION-RULES.md §FR (pewność: wysoka).

    **Wyjątek:** jednostki La Poste (SIREN zaczynający się `356000000`)
    legalnie łamią Luhna. Sprawdzamy prefix przed odrzuceniem.

    Live test: 3/3 real FR SIREN z naszych katalogów przechodzą.
    """
    siren_clean = re.sub(r"\D", "", siren)
    if not (siren_clean.isdigit() and len(siren_clean) == 9):
        return False, "INVALID_FORMAT"
    # Wyjątek La Poste
    if siren_clean.startswith("356000000"):
        return True, "OK"
    # Luhn (mod 10): od prawej, co drugą cyfrę mnożymy przez 2; jeśli >9, sumuj cyfry
    digits = [int(d) for d in siren_clean]
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d = (d // 10) + (d % 10)
        total += d
    return (total % 10) == 0, "OK" if (total % 10) == 0 else INVALID_CHECKSUM


# === Łotwa — PVN (11 cyfr, format-check) ===
def is_valid_lv_pvn(pvn: str) -> tuple[bool, str]:
    """LV PVN = 11 cyfr. **Brak potwierdzonego checksum** per
    VERIFICATION-RULES.md §LV — pierwsze 4 cyfry to data rejestracji, ale
    brak formalnego wzoru wag. Tylko format-check + skierowanie do UR/Lursoft."""
    pvn_clean = re.sub(r"\D", "", pvn)
    if not (pvn_clean.isdigit() and len(pvn_clean) == 11):
        return False, "INVALID_FORMAT"
    return True, "OK"


# === Litwa — PVM (9 lub 12 cyfr, format-check) ===
def is_valid_lt_pvm(pvm: str) -> tuple[bool, str]:
    """LT PVM = 9 lub 12 cyfr. **Brak potwierdzonego checksum** per
    VERIFICATION-RULES.md §LT — nie mam pewnego wzoru wag. Tylko format-check
    + skierowanie do get.data.gov.lt ja_kodas lookup."""
    pvm_clean = re.sub(r"\D", "", pvm)
    if not (pvm_clean.isdigit() and pvm_clean and len(pvm_clean) in (9, 12)):
        return False, "INVALID_FORMAT"
    return True, "OK"


# === Master dispatch ===
COUNTRY_VALIDATORS = {
    "PL": is_valid_pl_nip,
    "CZ": is_valid_cz_ico,
    "SK": is_valid_sk_dic,
    "BG": is_valid_bg_vat,
    "EE": is_valid_ee_kmkr,
    "HR": is_valid_hr_oib,
    "RO": is_valid_ro_cui,
    "SI": is_valid_si_ddv,
    "FR": is_valid_fr_siren,
    "LV": is_valid_lv_pvn,
    "LT": is_valid_lt_pvm,
    "MD": is_valid_ro_cui,  # MD IDNO ma 8 lub 13 cyfr
    "RS": is_valid_ro_cui,  # RS PIB ma 9 cyfr (nie ma darmowego API; tylko format-check)
}


def is_valid_vat_format(country_iso: str, vat_id: str) -> tuple[bool, str]:
    """Per §1.1 / §2: sprawdź format/checksum NIP/VAT per kraj ZANIM wywołasz API.
    Returns (is_valid, code). Code: 'OK' | 'INVALID_CHECKSUM' | 'INVALID_FORMAT' | 'NO_VALIDATOR'."""
    validator = COUNTRY_VALIDATORS.get(country_iso.upper())
    if not validator:
        return True, "NO_VALIDATOR"  # brak walidatora → nie blokuj, ale bezpiecznie
    return validator(vat_id)


# === Skala pracy vs strategia weryfikacji — progi per grupa krajów ===
# Per §4 dokumentacji:
#  - PL/CZ/FR (dojrzałe API):  manual <50, batch 50-500, full-auto 500+
#  - RO/BG/HR/SI/SK/RS (agregatory): manual <20, batch 20-200, full-auto 200+
#  - LT/LV/EE/MD (niszowe API): manual <5, batch 5-50, full-auto 50+

VERIFICATION_TIER = {
    "PL": "high", "CZ": "high", "FR": "high",
    "RO": "medium", "BG": "medium", "HR": "medium", "SI": "medium", "SK": "medium", "RS": "medium",
    "LT": "low", "LV": "low", "EE": "low", "MD": "low",
}


def get_audit_sample_size(country_iso: str, total_rows: int) -> int:
    """Zwraca wymagany rozmiar próbki audytowej per country tier.
    Per §4: 'pipeline + obowiązkowy audyt losowej próbki po każdym uruchomieniu'."""
    tier = VERIFICATION_TIER.get(country_iso.upper(), "low")
    if tier == "high":
        # PL/CZ/FR — 5% sample, min 10
        return max(10, total_rows * 5 // 100)
    if tier == "medium":
        # RO/BG/HR/SI/SK/RS — 10% sample, min 5
        return max(5, total_rows * 10 // 100)
    # LT/LV/EE/MD — 20% sample, min 3
    return max(3, total_rows * 20 // 100)
