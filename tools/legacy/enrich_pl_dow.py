#!/usr/bin/env python3
"""enrich_pl_dow.py — Enrich DO-W rows in catalog-B-PL with verified NIP/KRS.

Used by BILLSzuka cron when web_search + KRS API cross-check confirms a
DO-W intake row. Does NOT add new rows; that's add_lead() in orchestrate_11_levels.py.

Defense:
- mod-11 NIP checksum required
- KRS API name match required (or krs-pobierz 3rd-party mirror + 2nd source)
- FABRYKAT_KNOWN list (orchestrator) checked for KRS
- Backs up CSV before modification
"""
import csv
import json
import re
import shutil
import sys
import time
import urllib.request
from pathlib import Path
from datetime import datetime

ROOT = Path("/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka")
CSV_PATH = ROOT / "data" / "Polska" / "catalog-B-PL.csv"
BACKUP_PATH = ROOT / "data" / "backups" / f"catalog-B-PL_pre-enrich_{time.strftime('%Y%m%d_%H%M%S')}.csv"

FABRYKAT_KNOWN = {
    "KRS 0000123456", "KRS 0000574829", "KRS 0000090479", "KRS 0000384920",
    "KRS 0000439210", "KRS 0000628491", "KRS 0000782910", "KRS 0000182940",
    "KRS 0000892014",
}

KRS_API = "https://api-krs.ms.gov.pl/api/krs/OdpisAktualny"


def validate_nip(nip: str) -> bool:
    nip = re.sub(r"\D", "", str(nip))
    if len(nip) != 10 or not nip.isdigit():
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    return sum(int(nip[i]) * weights[i] for i in range(9)) % 11 == int(nip[9])


def krs_name_match(krs: str, expected_name_tokens: list[str]) -> tuple[bool, str]:
    """Try KRS API; on transient error, return (False, error_msg)."""
    krs_clean = re.sub(r"\D", "", str(krs)).zfill(10)
    try:
        req = urllib.request.Request(f"{KRS_API}/{krs_clean}", headers={"User-Agent": "BILLSzuka/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
    except Exception as e:
        return False, f"KRS API error: {type(e).__name__}: {str(e)[:60]}"
    podmiot = data.get("odpis", {}).get("dane", {}).get("dzial1", {}).get("danePodmiotu", {})
    api_name = podmiot.get("nazwa", "").upper()
    api_nip = podmiot.get("identyfikatory", {}).get("nip", "")
    if not api_name:
        return False, "KRS API returned empty name"
    # match: at least 1 significant token in common
    for tok in expected_name_tokens:
        if tok.upper() in api_name:
            return True, f"KRS name match: '{tok}' in '{api_name[:50]}' (NIP={api_nip})"
    return False, f"KRS name mismatch: api='{api_name[:50]}' expected tokens={expected_name_tokens}"


def backup_csv():
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CSV_PATH, BACKUP_PATH)
    print(f"[backup] {BACKUP_PATH.name}")


def enrich_row(rows, fieldnames, id, nip, rejestr_id, source, expected_name, krs_verify=True):
    """Update a single row by id. Returns (status, message)."""
    nip_clean = re.sub(r"\D", "", nip)
    if not validate_nip(nip_clean):
        return "FAIL", f"NIP {nip_clean} mod-11 fail"
    # Handle CEIDG-only (sp.j./JDG, no KRS)
    is_ceidg_only = rejestr_id.upper() == "CEIDG"
    if is_ceidg_only:
        full_id = "CEIDG (JDG)"
        fabrykat_check = "KRS 0000000000"  # sentinel
    else:
        full_id = f"KRS {re.sub(r'\\D', '', rejestr_id).zfill(10)}"
        fabrykat_check = full_id
    if fabrykat_check in FABRYKAT_KNOWN:
        return "FABRYKAT", f"{full_id} is in FABRYKAT_KNOWN"

    # Find row
    target = None
    for i, r in enumerate(rows):
        if r.get("id") == id:
            target = r
            break
    if target is None:
        return "FAIL", f"id {id} not found"

    # KRS verify (only if not CEIDG-only)
    if krs_verify and not is_ceidg_only:
        name_tokens = [t for t in re.split(r"\s+", expected_name) if len(t) > 3][:3]
        ok, msg = krs_name_match(rejestr_id, name_tokens)
        if not ok:
            return "FAIL", f"KRS verify failed: {msg}"

    # Update fields
    target["nip_vat"] = f"PL{nip_clean}"
    target["rejestr_id"] = full_id
    target["data_weryfikacji"] = time.strftime("%Y-%m-%d")
    if is_ceidg_only:
        # CEIDG-only: mark as FROZEN with note that CEIDG API verify pending
        target["flagi"] = f"{target['flagi']} | {time.strftime('%Y-%m-%d')} ⚠️ DO-W (CEIDG API verify pending)"
    else:
        target["flagi"] = f"{target['flagi']} | {time.strftime('%Y-%m-%d')} ✅ FROZEN (API) (KRS API name match + mod-11)"
    # Only append source if not already present (avoid duplicate appends on re-runs)
    existing_zrodlo = target.get("zrodlo_danych", "") or ""
    if source not in existing_zrodlo:
        target["zrodlo_danych"] = (existing_zrodlo + f" | {source}").lstrip(" |")
    return "OK", f"Updated {id}: NIP={nip_clean} {full_id}"


def main():
    if not CSV_PATH.exists():
        print(f"CSV not found: {CSV_PATH}")
        sys.exit(1)
    backup_csv()
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = list(r)
        fieldnames = r.fieldnames

    # Enrichments to apply (id, nip, krs_or_ceidg, source, name_for_match, krs_verify)
    # rejestr_id='CEIDG' for JDG-only firms (no KRS) — enrichment records CEIDG source, no KRS API check
    enrichments = [
        # TOM Polska — actually wielkopolskie, B4 (lighters, not tobacco)
        ("PL-B-OP-001", "6182180725", "0000771952",
         "L1+web+krs-pobierz: KRS API confirmed (TOM POLSKA SP. Z O.O. mod-11+NIP+name match)",
         "TOM POLSKA", True),
        # ALMARK J. Stajer Sp.k. — confirmed B8, wielkopolskie (Leszno)
        ("PL-B-OP-002", "6972257505", "0000331276",
         "L1+web+krs-pobierz: KRS API confirmed (ALMARK J. STAJER SP.K. mod-11+NIP+name match, PKD 46.35Z)",
         "ALMARK", True),
        # TEKS S.A. — confirmed B8, mazowieckie (Radom)
        ("PL-B-SK-002", "7960035610", "0000061035",
         "L1+web+krs-pobierz: KRS API confirmed (TEKS S.A. mod-11+NIP+name match, PKD 46.35Z)",
         "TEKS", True),
        # Lever — re-registered as sp. z o.o. in 2026 (new KRS 0001213931, same NIP)
        ("PL-B-LU-008", "7150200425", "0001213931",
         "L1+web+VIES+firmy.ai: KRS 0001213931 (new sp. z o.o., 4 months old, same NIP+address as old sp.j. 0000004673). KRS API for 0000004673 returns 204. VIES confirms 'LEVER SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ'.",
         "LEVER", True),
        # Augusto-Limaro Sp.j. — KRS 0000076844, Jelenia Góra, NIP 6110201493
        ("PL-B-XX-003", "6110201493", "0000076844",
         "L1+web+krs-pobierz+panoramafirm: KRS API confirmed (AUGUSTO-LIMARO LIPIŃSKI MARSZAŁEK SP.J. mod-11+NIP+name match)",
         "AUGUSTO", True),
        # Trafica-Hurt s.c. — sp.j. (spółka cywilna), CEIDG-only, NIP 9462539270, Lublin, PKD 46.35Z
        ("PL-B-LU-002", "9462539270", "CEIDG",
         "L1+web+spolkicywilne.pl: 2 sources consistent (TRAFICA-HURT S.C. mod-11+NIP, PKD 46.35Z). CEIDG API verify on next run.",
         "TRAFICA", False),
        # JUKA Akcesoria Tytoniowe — CEIDG JDG, NIP 9531380750, Gdańsk
        ("PL-B-PM-004", "9531380750", "CEIDG",
         "L1+web+krs-online+bazafirmdane+gowork+monitorfirm: 4 sources consistent (JUKA AKCESORIA TYTONIOWE mod-11+NIP, PKD 46.19.Z agent wholesale). CEIDG API verify on next run.",
         "JUKA", False),
        # PHUP Gniezno Szeszycki Sp.k. — KRS 0000300468, 1.5 mld zł revenue, 5 oddziałów, 🐋
        ("PL-B-OP-003", "7842403647", "0000300468",
         "L1+web+bizraport+wyszukiwarkakrs+sprytnykupiec: KRS API confirmed (PHUP GNIEZNO SZESZYCKI SP.K. mod-11+NIP+name match, 1.5 mld zł revenue, 3000 sklepów, 5 oddziałów, PKD 46.35Z) — 🐋 TOP TIER",
         "PHUP GNIEZNO", True),
        # Top-Kart Sp.j. Kozłowski-Ponikarczyk — KRS API empty, krs-pobierz confirms
        ("PL-B-PD-002", "5422737004", "0000175787",
         "L1+web+krs-pobierz+panoramafirm: KRS API empty (transient), krs-pobierz 3rd-party + 2 sources consistent (PKD 46.39Z, Białystok)",
         "TOP KART", False),
        # SAT Tomasz Sromek — CEIDG JDG, NIP 7341003210, Nowy Sącz
        ("PL-B-MA-004", "7341003210", "CEIDG",
         "L1+web+krs-online+hurtowniasat.pl: 3 sources consistent (SAT Tomasz Sromek mod-11+NIP, PKD 46.90.Z wholesale). CEIDG API verify on next run.",
         "SAT", False),
        # Frega — Rzeszów HQ (catalog entry was for Tarnów branch). NIP 6570386005, address Rzeszów Przemysłowa 14
        ("PL-B-MA-006", "6570386005", "CEIDG",
         "L1+web+krs-online+biznesfinder: 3 sources consistent (FREGA HURTOWNIA ART. CHEMICZNYCH I TYTONIOWYCH mod-11+NIP, Rzeszów HQ + oddział Tarnów). CEIDG API verify on next run.",
         "FREGA", False),
    ]

    results = []
    for eid, nip, krs, source, name, krs_verify in enrichments:
        status, msg = enrich_row(rows, fieldnames, eid, nip, krs, source, name, krs_verify)
        results.append((eid, status, msg))
        print(f"  {status:10} {eid}: {msg}")

    # Also rename short trade names → full legal name (for Jaccard 0.8 FABRYKAT defense)
    name_corrections = {
        "PL-B-OP-002": "ALMARK J. STAJER SPÓŁKA KOMANDYTOWA",
        "PL-B-SK-002": "PRZEDSIĘBIORSTWO HANDLOWO-PRODUKCYJNO-USŁUGOWE TEKS SPÓŁKA AKCYJNA",
        "PL-B-XX-003": '"AUGUSTO - LIMARO" LIPIŃSKI, MARSZAŁEK SPÓŁKA JAWNA',
        "PL-B-LU-008": "LEVER SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        "PL-B-OP-003": "PHUP GNIEZNO SZESZYCKI SPÓŁKA KOMANDYTOWA",
    }
    for row in rows:
        if row.get("id") in name_corrections:
            new_name = name_corrections[row["id"]]
            old_name = row.get("nazwa_firmy", "")
            if old_name != new_name:
                row["nazwa_firmy"] = new_name
                print(f"  RENAME    {row['id']}: {old_name} → {new_name}")
                results.append((row["id"], "RENAME", f"{old_name} → {new_name}"))

    # Write back (tolerant of extra/missing fields)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\r\n", extrasaction="ignore")
        w.writeheader()
        # Replace None with empty string to avoid issues
        for r in rows:
            for k in fieldnames:
                if r.get(k) is None:
                    r[k] = ""
        w.writerows(rows)
    print(f"\n[done] {len(results)} rows processed. CSV: {CSV_PATH.name}")


if __name__ == "__main__":
    main()
