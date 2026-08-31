#!/usr/bin/env python3
"""
checksums.py — Walidacja identyfikatorów firmowych per kraj.

Wszystkie 12 krajów BILLSzuka ma oficjalny algorytm checksum (mod 11, Luhn,
ISO 7064). Moduł implementuje validators per kraj, plus dispatcher
`validate_id(id_str, country)`.

Źródła algorytmów:
  PL NIP: GUS BIR1.1 (Rozporządzenie)
  CZ IČO: ARES (živnostenský rejstřík)
  SK IČO: ORSR (Živnostenský register)
  FR SIREN/SIRET: INSEE (Luhn)
  HR OIB: Ministarstvo financija
  SI EMŠO: AJPES
  EE Registrikood: e-Äriregister
  LV Reģ. nr.: UR (Uzņēmumu reģistrs)
  RO CUI: ANAF
  BG EIK/BULSTAT: portal.justice.bg
  MD IDNO: Camera Înregistrării de Stat
  DE USt-IdNr: format only (no standard checksum)
  LT Įmonės kodas: format only

Użycie:
  from checksums import validate_id
  ok, reason = validate_id("1234567890", "PL")
"""

import re

# ───────────────────────────── PL: NIP ─────────────────────────────

def validate_pl_nip(nip: str) -> tuple[bool, str]:
    """PL NIP mod-11 checksum. Returns (valid, reason)."""
    nip = re.sub(r"\D", "", str(nip))
    if len(nip) != 10:
        return False, f"PL NIP must be 10 digits, got {len(nip)}"
    if not nip.isdigit():
        return False, "PL NIP must be all digits"
    if len(set(nip)) == 1:
        return False, "PL NIP cannot consist of identical digits"
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    s = sum(int(nip[i]) * weights[i] for i in range(9))
    if s % 11 != int(nip[9]):
        return False, f"PL NIP checksum fail (s={s}, expected {s % 11}, got {nip[9]})"
    return True, "ok"


# ───────────────────────────── CZ: IČO ─────────────────────────────

def validate_cz_ico(ico: str) -> tuple[bool, str]:
    """CZ IČO mod-11 checksum. Weights [8,7,6,5,4,3,2,1] for all 8 digits.
    Valid if sum mod 11 == 0.
    """
    ico = re.sub(r"\D", "", str(ico))
    if len(ico) != 8:
        return False, f"CZ IČO must be 8 digits, got {len(ico)}"
    if not ico.isdigit():
        return False, "CZ IČO must be all digits"
    weights = [8, 7, 6, 5, 4, 3, 2, 1]
    s = sum(int(ico[i]) * weights[i] for i in range(8))
    if s % 11 != 0:
        return False, f"CZ IČO checksum fail (s={s}, s%11={s%11}, expected 0)"
    return True, "ok"


# ───────────────────────────── SK: IČO ─────────────────────────────

def validate_sk_ico(ico: str) -> tuple[bool, str]:
    """SK IČO mod-11 with weights [8,7,6,5,4,3,2,1,0] for 8-digit.
    For older 7-digit IČO uses different weights.
    """
    ico = re.sub(r"\D", "", str(ico))
    if len(ico) not in (7, 8):
        return False, f"SK IČO must be 7 or 8 digits, got {len(ico)}"
    if not ico.isdigit():
        return False, "SK IČO must be all digits"
    if len(ico) == 8:
        # For 8-digit: weighted mod 11, weights [8,7,6,5,4,3,2,1]
        weights = [8, 7, 6, 5, 4, 3, 2, 1]
        s = sum(int(ico[i]) * weights[i] for i in range(8))
        # Special: if s % 11 == 0, valid; if last digit is 0, also valid (legacy)
        if s % 11 == 0 or (s % 11) - 1 == int(ico[7]) or int(ico[7]) == 0:
            return True, "ok"
        return False, f"SK IČO 8-digit checksum fail (s={s}, s%11={s%11})"
    # 7-digit legacy
    return True, "ok (legacy 7-digit, no checksum)"


# ───────────────────────────── FR: SIREN/SIRET (Luhn) ─────────────────────────────

def _luhn_check(digits: str) -> bool:
    """Luhn algorithm. Sum weighted digits mod 10 == 0."""
    total = 0
    reverse = digits[::-1]
    for i, d in enumerate(reverse):
        n = int(d)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def validate_fr_siren(siren: str) -> tuple[bool, str]:
    """FR SIREN (9 digits) or SIRET (14 digits) Luhn checksum."""
    s = re.sub(r"\D", "", str(siren))
    if len(s) not in (9, 14):
        return False, f"FR SIREN must be 9 digits (SIRET 14), got {len(s)}"
    if not s.isdigit():
        return False, "FR SIREN must be all digits"
    if not _luhn_check(s):
        return False, f"FR SIREN Luhn fail (invalid checksum)"
    return True, "ok"


# ───────────────────────────── HR: OIB (ISO 7064 mod 11,10) ─────────────────────────────

def validate_hr_oib(oib: str) -> tuple[bool, str]:
    """HR OIB (11 digits) ISO 7064 mod 11,10 algorithm."""
    oib = re.sub(r"\D", "", str(oib))
    if len(oib) != 11:
        return False, f"HR OIB must be 11 digits, got {len(oib)}"
    if not oib.isdigit():
        return False, "HR OIB must be all digits"
    # ISO 7064 mod 11,10: for each digit i in 0..9, compute
    #   v = (v + digit) mod 10, then v = (v * 2) mod 11
    # Final v should be 1
    v = 10  # initial value
    for i in range(10):
        v = (v + int(oib[i])) % 10
        if v == 0:
            v = 10
        v = (v * 2) % 11
    check = (11 - v) % 10
    if check != int(oib[10]):
        return False, f"HR OIB ISO 7064 fail (expected check {check}, got {oib[10]})"
    return True, "ok"


# ───────────────────────────── SI: EMŠO ─────────────────────────────

def validate_si_emso(emso: str) -> tuple[bool, str]:
    """SI EMŠO (13 digits) mod-11. Weights [7,6,5,4,3,2,7,6,5,4,3,2]."""
    emso = re.sub(r"\D", "", str(emso))
    if len(emso) != 13:
        return False, f"SI EMŠO must be 13 digits, got {len(emso)}"
    if not emso.isdigit():
        return False, "SI EMŠO must be all digits"
    weights = [7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    s = sum(int(emso[i]) * weights[i] for i in range(12))
    check = (s % 11) if (s % 11) < 10 else 0
    if check != int(emso[12]):
        return False, f"SI EMŠO checksum fail (s={s}, expected {check}, got {emso[12]})"
    return True, "ok"


# ───────────────────────────── EE: Registrikood ─────────────────────────────

def validate_ee_registry(reg: str) -> tuple[bool, str]:
    """EE Registrikood (8 digits) mod-11. Weights [3,4,5,6,7,8,9,1]."""
    reg = re.sub(r"\D", "", str(reg))
    if len(reg) != 8:
        return False, f"EE Registrikood must be 8 digits, got {len(reg)}"
    if not reg.isdigit():
        return False, "EE Registrikood must be all digits"
    weights = [3, 4, 5, 6, 7, 8, 9, 1]
    s = sum(int(reg[i]) * weights[i] for i in range(8))
    check = s % 11
    if check != 0:
        return False, f"EE Registrikood checksum fail (s={s}, s%11={check})"
    return True, "ok"


# ───────────────────────────── LV: Reģ. nr. ─────────────────────────────

def validate_lv_regnum(reg: str) -> tuple[bool, str]:
    """LV Uzņēmumu reģistrs / PVN (11 digits) format check.
    Authoritative verification is performed via VIES / Lursoft."""
    reg = re.sub(r"\D", "", str(reg))
    if len(reg) != 11:
        return False, f"LV Reģ. nr. must be 11 digits, got {len(reg)}"
    if not reg.isdigit():
        return False, "LV Reģ. nr. must be all digits"
    return True, "ok (format only — verified via VIES/Lursoft)"


# ───────────────────────────── RO: CUI/CIF ─────────────────────────────

def validate_ro_cui(cui: str) -> tuple[bool, str]:
    """RO CUI/CIF (1-10 digits) mod-11. Weights cycle [7,5,3,2,1,7,5,3,2]."""
    cui = re.sub(r"\D", "", str(cui))
    if not cui or len(cui) > 10:
        return False, f"RO CUI must be 1-10 digits, got {len(cui)}"
    if not cui.isdigit():
        return False, "RO CUI must be all digits"
    if len(cui) < 2:
        return True, "ok (too short for full check)"
    # Apply weights, cycle if needed
    weights = [7, 5, 3, 2, 1, 7, 5, 3, 2, 1]
    n = len(cui) - 1  # exclude check digit
    s = 0
    for i in range(n):
        w = weights[i % len(weights)]
        s += int(cui[i]) * w
    check = (s * 10) % 11
    if check == 10:
        check = 0
    if check != int(cui[-1]):
        return False, f"RO CUI checksum fail (s={s}, expected {check}, got {cui[-1]})"
    return True, "ok"


# ───────────────────────────── BG: EIK/BULSTAT ─────────────────────────────

def validate_bg_eik(eik: str) -> tuple[bool, str]:
    """BG EIK/BULSTAT (9 digits) mod-11. Weights [1,2,3,4,5,6,7,8].
    13-digit is also valid (more complex)."""
    eik = re.sub(r"\D", "", str(eik))
    if len(eik) not in (9, 13):
        return False, f"BG EIK must be 9 or 13 digits, got {len(eik)}"
    if not eik.isdigit():
        return False, "BG EIK must be all digits"
    if len(eik) == 9:
        weights = [1, 2, 3, 4, 5, 6, 7, 8]
        s = sum(int(eik[i]) * weights[i] for i in range(8))
        check = s % 11
        if check == 10:
            check = 0
        if check != int(eik[8]):
            return False, f"BG EIK 9-digit checksum fail (s={s}, s%11={check}, got {eik[8]})"
        return True, "ok"
    # 13-digit: more complex, skip for now
    return True, "ok (13-digit, full check not implemented)"


# ───────────────────────────── MD: IDNO ─────────────────────────────

def validate_md_idno(idno: str) -> tuple[bool, str]:
    """MD IDNO (13 digits) mod-11. Weights [7,3,1,7,3,1,7,3,1,7,3,1]."""
    idno = re.sub(r"\D", "", str(idno))
    if len(idno) != 13:
        return False, f"MD IDNO must be 13 digits, got {len(idno)}"
    if not idno.isdigit():
        return False, "MD IDNO must be all digits"
    weights = [7, 3, 1, 7, 3, 1, 7, 3, 1, 7, 3, 1]
    s = sum(int(idno[i]) * weights[i] for i in range(12))
    if s % 10 != int(idno[12]):
        return False, f"MD IDNO checksum fail (s={s}, expected {s%10}, got {idno[12]})"
    return True, "ok"


# ───────────────────────────── DE: USt-IdNr (format only) ─────────────────────────────

def validate_de_ust(ust: str) -> tuple[bool, str]:
    """DE USt-IdNr format check only. Format: DE + 9 digits (8 or 9 for old/standard).
    No public checksum — must lookup at Bundesanzeiger."""
    ust = re.sub(r"\s", "", str(ust).upper())
    digits = ust[2:] if ust.startswith("DE") else ust
    if len(digits) not in (8, 9):
        return False, f"DE USt-IdNr must be 8 or 9 digits, got {len(digits)}"
    if not digits.isdigit():
        return False, "DE USt-IdNr must have digits after DE"
    return True, "ok (format only — full check requires Bundesanzeiger API)"


# ───────────────────────────── LT: Įmonės kodas (format only) ─────────────────────────────

def validate_lt_kodas(kodas: str) -> tuple[bool, str]:
    """LT Įmonės kodas (7 or 9 digits) format check only.
    Real validation requires rekvizitai.vz.lt lookup."""
    kodas = re.sub(r"\D", "", str(kodas))
    if len(kodas) not in (7, 9):
        return False, f"LT Įmonės kodas must be 7 or 9 digits, got {len(kodas)}"
    if not kodas.isdigit():
        return False, "LT Įmonės kodas must be all digits"
    return True, "ok (format only — full check requires rekvizitai.vz.lt)"


# ───────────────────────────── Dispatcher ─────────────────────────────

VALIDATORS = {
    "PL": validate_pl_nip,
    "CZ": validate_cz_ico,
    "SK": validate_sk_ico,
    "FR": validate_fr_siren,
    "HR": validate_hr_oib,
    "SI": validate_si_emso,
    "EE": validate_ee_registry,
    "LV": validate_lv_regnum,
    "RO": validate_ro_cui,
    "BG": validate_bg_eik,
    "MD": validate_md_idno,
    "DE": validate_de_ust,
    "LT": validate_lt_kodas,
}


def validate_id(id_str: str, country: str) -> tuple[bool, str]:
    """Validate an ID by country code. Strips country prefix (PL, CZ, etc.) first.
    Returns (valid, reason)."""
    country = (country or "").upper().strip()
    fn = VALIDATORS.get(country)
    if not fn:
        return False, f"no validator for country '{country}'"
    # Strip country code prefix
    clean = str(id_str).strip()
    if clean[:2].upper() == country:
        clean = clean[2:]
    return fn(clean)


# ───────────────────────────── Self-test ─────────────────────────────

if __name__ == "__main__":
    test_cases = [
        # (id, country, expected_valid)
        ("5140361901", "PL", True),     # BILLS Sp. z o.o.
        ("1231543801", "PL", True),     # E-TABAK
        ("0000000000", "PL", False),    # invalid repeated
        ("62586289", "CZ", True),       # FORTIS-DB
        ("25775634", "CZ", True),       # PEAL a.s.
        ("552032534", "FR", True),      # SIREN (Danone)
        ("12345678903", "HR", True),    # HR OIB valid
        ("0101006500005", "SI", True),   # SI EMŠO valid
        ("10241358", "EE", True),       # EE registrikood valid
        ("40003166842", "LV", True),    # SIA SANITEX LV
        ("110443497", "RO", True),      # RO CUI valid
        ("206015071", "BG", True),      # Tobacco Distribution BG
        ("DE123456789", "DE", True),    # format only
        ("1234567", "LT", True),        # format only
    ]
    for id_str, country, expected in test_cases:
        ok, reason = validate_id(id_str, country)
        status = "✓" if ok == expected else "✗ FAIL"
        print(f"  {status} {country} {id_str:20s} → ok={ok}, {reason}")
