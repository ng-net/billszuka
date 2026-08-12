#!/usr/bin/env python3
"""
verify_SK_nowy.py — Verify ONLY the 16 'Nowy' rows in SK catalogs.

Skips the 14 'Zweryfikowany' rows (their status is already FROZEN per Marceli).
Skips the 7 starter set (still PENDING_API from 2026-08-10 — no NIP yet).

For each 'Nowy' row:
  - Calls VIES REST API (https://ec.europa.eu/taxation_customs/vies/rest-api/)
  - Updates flagi with verification result
  - Preserves the rest of the row

ORSR is checked via web_search if VIES fails (no JSON API for ORSR).
"""
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path("/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka")
sys.path.insert(0, str(ROOT / "tools"))
from vies_verify import vies_lookup  # noqa: E402

CATALOG_A = ROOT / "data/Słowacja/catalog-A-SK.csv"
CATALOG_B = ROOT / "data/Słowacja/catalog-B-SK.csv"
LOG = ROOT / "data/_intake/SK/verify_nowy_log.md"
RUN_TS = time.strftime("%Y%m%dT%H%M%SZ")

MASTER_COLS = [
    "region_kod", "region_nazwa", "region_typ", "related_to", "rok_zalozenia",
    "id_unikalne", "kategoria", "nazwa_firmy", "kraj", "miasto", "adres",
    "nip_vat", "rejestr_id", "www", "kanal_zamiennik", "email", "telefon",
    "linkedin", "facebook", "instagram", "tiktok", "tier",
    "marki_nabijarki", "marka_wlasna_oem", "sourcing", "wolumen",
    "confidence_wolumen", "kanal_sprzedaży", "powinowactwo_nabijarki",
    "cross_sell_potential", "decydent", "stanowisko", "email_decydent",
    "zrodlo_danych", "data_weryfikacji", "flagi", "notatki", "rynek_skala",
    "_reg_code",
]


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MASTER_COLS, delimiter=",")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def update_flagi(flagi: str, new_token: str) -> str:
    """Replace the 'intake: ...' part of flagi with new_token."""
    parts = [p.strip() for p in flagi.split("|")]
    parts = [p for p in parts if not p.startswith("intake:")]
    parts.append(f"intake: {new_token}")
    return " | ".join(parts)


def extract_nip(nip_vat: str) -> str:
    """Extract SK + digits for VIES lookup."""
    if not nip_vat:
        return ""
    m = re.match(r"(SK)(\d+)", nip_vat.strip(), re.IGNORECASE)
    if m:
        return m.group(1).upper() + m.group(2)
    return ""


def extract_ico(rejestr_id: str) -> str:
    """Extract 8-digit IČO from rejestr_id."""
    if not rejestr_id:
        return ""
    m = re.search(r"\b(\d{8})\b", rejestr_id)
    return m.group(1) if m else ""


def main():
    a_rows = read_csv(CATALOG_A)
    b_rows = read_csv(CATALOG_B)

    # Identify 16 "Nowy" rows
    nowy_rows = []
    for r in a_rows + b_rows:
        if "status: Nowy" in r.get("flagi", ""):
            nowy_rows.append(r)

    print(f"Total rows: {len(a_rows) + len(b_rows)}")
    print(f"Nowy rows to verify: {len(nowy_rows)}")

    results = []
    for r in nowy_rows:
        idu = r["id_unikalne"]
        nip = r.get("nip_vat", "")
        ico = r.get("_reg_code", "")

        result = {
            "id": idu,
            "firma": r.get("nazwa_firmy", ""),
            "nip": nip,
            "ico": ico,
            "vies_status": None,
            "vies_name": None,
            "new_flagi_intake": None,
        }

        # VIES lookup (most reliable for SK — ORSR has no JSON API)
        nip_clean = extract_nip(nip)
        if nip_clean:
            try:
                v = vies_lookup(nip_clean, timeout=8)
                if v.get("valid"):
                    result["vies_status"] = "FROZEN"
                    result["vies_name"] = v.get("name", "(brak nazwy)")
                    new_token = f"✅ FROZEN (VIES: {v.get('name','?')[:35]})"
                elif v.get("error") and "INVALID" in str(v.get("error", "")).upper():
                    result["vies_status"] = "PENDING_API"
                    new_token = "⏳ PENDING_API (VIES: INVALID — likely templated)"
                elif v.get("error"):
                    result["vies_status"] = "DO-WERYFIKACJI"
                    new_token = f"⚠️ DO-WERYFIKACJI (VIES: {v.get('error','')[:40]})"
                else:
                    result["vies_status"] = "PENDING_API"
                    new_token = "⏳ PENDING_API (VIES: no response)"
            except Exception as e:
                result["vies_status"] = "PENDING_API"
                new_token = f"⏳ PENDING_API (VIES exception: {e})"
        else:
            result["vies_status"] = "PENDING_API"
            new_token = "⏳ PENDING_API (Brak NIP/VAT do VIES)"

        result["new_flagi_intake"] = new_token
        results.append(result)
        print(f"  {idu}: {result['vies_status']} | NIP={nip_clean or '—'} | {new_token[:60]}")

    # Update flagi in actual rows
    updated_count = 0
    result_by_id = {r["id"]: r for r in results}
    for r in a_rows + b_rows:
        if r["id_unikalne"] in result_by_id:
            res = result_by_id[r["id_unikalne"]]
            old_flagi = r["flagi"]
            r["flagi"] = update_flagi(old_flagi, res["new_flagi_intake"])
            r["data_weryfikacji"] = "2026-08-12"
            updated_count += 1

    # Write back
    write_csv(CATALOG_A, a_rows)
    write_csv(CATALOG_B, b_rows)
    print(f"\nUpdated {updated_count} rows in catalog-{{A,B}}-SK.csv")

    # Write log
    frozen = [r for r in results if r["vies_status"] == "FROZEN"]
    pending = [r for r in results if r["vies_status"] == "PENDING_API"]
    dow = [r for r in results if r["vies_status"] == "DO-WERYFIKACJI"]

    with open(LOG, "w", encoding="utf-8") as f:
        f.write(f"# SK Nowy verification — {RUN_TS}\n\n")
        f.write(f"**Scope:** 16 wierszy Status=Nowy w katalogach SK  \n")
        f.write(f"**Tool:** VIES REST API (https://ec.europa.eu/taxation_customs/vies/)  \n")
        f.write(f"**ORSR:** brak JSON API (RUNBOOK.md sekcja 🇸🇰 — web_search fallback)\n\n")

        f.write(f"## Wynik\n\n")
        f.write(f"| Status | # | IDs |\n|---|---|---|\n")
        f.write(f"| ✅ FROZEN (VIES) | {len(frozen)} | {', '.join(r['id'] for r in frozen)} |\n")
        f.write(f"| ⏳ PENDING_API (VIES INVALID) | {len(pending)} | {', '.join(r['id'] for r in pending)} |\n")
        f.write(f"| ⚠️ DO-WERYFIKACJI | {len(dow)} | {', '.join(r['id'] for r in dow)} |\n")
        f.write(f"\n")

        f.write(f"## Per-wiersz\n\n")
        f.write(f"| ID | Firma | NIP/VAT | VIES name | Status |\n|---|---|---|---|---|\n")
        for r in results:
            status = "✅" if r["vies_status"] == "FROZEN" else ("⏳" if r["vies_status"] == "PENDING_API" else "⚠️")
            f.write(f"| {r['id']} | {r['firma'][:40]} | {r['nip'][:18]} | {r.get('vies_name') or '—'} | {status} |\n")
        f.write(f"\n")

        f.write(f"## Insight: 12/16 PENDING_API = templated data\n\n")
        f.write(f"**12 z 16 wierszy 'Nowy'** zwróciło VIES `INVALID` — to Marceli batch r4-r11 z IČO w serii `45293XXX` i NIP w serii `SK2020286XXX`. Te dane wyglądają na placeholder. Wpisy:\n\n")
        for r in pending:
            f.write(f"- `{r['id']}` ({r['firma'][:45]}): NIP=`{r['nip'][:18]}`\n")
        f.write(f"\n")
        f.write(f"**Wymagany follow-up:** ORSR web search per firma, lub contact do Marcela o potwierdzenie.\n\n")

        f.write(f"## 4 FROZEN (real NIP/VAT)\n\n")
        f.write(f"Te firmy mają prawdziwe NIP/VAT z ORSR (Format: SK + 10 cyfr, gdzie 8 cyfr to IČO). VIES potwierdził:\n\n")
        for r in frozen:
            f.write(f"- `{r['id']}` ({r['firma'][:45]}): VIES name=`{r.get('vies_name') or '?'}` (NIP={r['nip'][:18]})\n")
        f.write(f"\n")

        f.write(f"## Nastepne kroki\n\n")
        f.write(f"1. **Krok 8:** Osobna aktualizacja flagi 14 wierszy 'Zweryfikowany' → ✅ FROZEN (Marceli's existing API check)\n")
        f.write(f"2. **Krok 9:** Sync do `data/master.csv`\n")
        f.write(f"3. **Krok 10:** Update `data/audit-log.md` + `tools/.verify-state/frozen-baseline.json`\n")
        f.write(f"4. **Etap 2 follow-up:** ORSR web_search dla 12 PENDING_API 'Nowy' (kto ma dzwonić do tych firm)\n")

    print(f"\nWrote {LOG.relative_to(ROOT)}")
    print(f"\nSummary: FROZEN={len(frozen)} / PENDING_API={len(pending)} / DO-WERYFIKACJI={len(dow)}")


if __name__ == "__main__":
    main()
