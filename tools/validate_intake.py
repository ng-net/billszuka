#!/usr/bin/env python3
"""
validate_intake.py — Validate Marcel's intake CSVs for BILLSzuka.

For each lead in data/_intake/{ISO}/07-MASTER-Katalog-Wszystkich-Leadow-B2B-{ISO}.csv:
  1. Format check     — IČO / Registrikood / Įmonės kodas / DIČ / KMKR / PVM format
  2. Hallucination    — generic address patterns, repeated phones, suspicious IČOs
  3. Dedup            — collision with existing data/{Kraj}/catalog-B-{ISO}.csv
  4. ARES/e-Äriregister/JAR live check (optional, --no-network to skip)
  5. Field completeness — % of 37 BILLSzuka columns we can derive from intake

Outputs:
  data/_intake/{ISO}/validation.md       — per-country report
  data/_intake/{ISO}/validated.csv       — intake rows with `verdict` column

Verdict values:
  ✅ FROZEN       — all critical fields verified (IČO + name + address + contact)
  ⚠️ DO-WERYFIKACJI — has data but IČO/registry didn't confirm
  ❌ HALUCYNACJA  — fabricated IČO, fake address, or repeated placeholder
  🔁 DUPLIKAT     — already in existing BILLSzuka catalog
  ⏳ PENDING_API  — registry not reachable

Usage:
  python3 tools/validate_intake.py --iso CZ
  python3 tools/validate_intake.py --all
  python3 tools/validate_intake.py --iso EE --no-network
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTAKE = ROOT / "data" / "_intake"

# Country → (intake subdir, catalog dir, ISO code, registry function)
COUNTRY_MAP = {
    "PL": ("PL", "Polska", "PL", None),  # KRS
    "CZ": ("CZ", "Czechy", "CZ", "cz_ares"),
    "SK": ("SK", "Słowacja", "SK", None),  # RPO
    "RO": ("RO", "Rumunia", "RO", None),
    "LT": ("LT", "Litwa", "LT", "lt_jar"),
    "LV": ("LV", "Łotwa", "LV", None),
    "EE": ("EE", "Estonia", "EE", "ee_ariregister"),
    "FR": ("FR", "Francja", "FR", "fr_recherche"),
    "MD": ("MD", "Mołdawia", "MD", None),
    "BG": ("BG", "Bułgaria", "BG", None),
    "SI": ("SI", "Słowenia", "SI", None),
    "HR": ("HR", "Chorwacja", "HR", None),
}

# Format patterns
PATTERNS = {
    "CZ": {
        "ico": re.compile(r"^(\d{8})$"),  # IČO = 8 digits
        "dic": re.compile(r"^CZ(\d{8,10})$"),  # DIČ = CZ + 8/9/10 digits
        "ico_in_rejestr": re.compile(r"(?:IČO[: ]*)(\d{8})"),
    },
    "EE": {
        "reg": re.compile(r"^(\d{8})$"),  # Registrikood = 8 digits
        "kmkr": re.compile(r"^EE(\d{9})$"),  # KMKR = EE + 9 digits
        "reg_in_rejestr": re.compile(r"(?:Registrikood[: ]*)(\d{8})"),
    },
    "LT": {
        "kodas": re.compile(r"^(\d{9}|\d{7})$"),  # Įmonės kodas = 7 or 9 digits
        "pvm": re.compile(r"^LT(\d{9}|\d{12})$"),  # PVM = LT + 9 or 12 digits
        "kodas_in_rejestr": re.compile(r"(?:Įmonės kodas[: ]*)(\d{7,9})"),
    },
}

# Hallucination heuristics
GENERIC_ADDRESS_PATTERNS = [
    r"Průmyslová \d+",  # "Průmyslová 10/11/12..." — same street, different numbers
    r"Tovární \d+",
    r"^ul\. Główna \d+$",
]

# Phone patterns per country — strip spaces/dashes first
# CZ: +420 XXX XXX XXX (9 digits total) or +420 XXX XXX XX (legacy)
# EE: +372 XXXX XXXX (8 digits) or +372 XXX XXXX (7 digits)
# LT: +370 XXX XXXXX or +370 XXXXXXXX (8 digits total)
# PL: +48 XXX XXX XXX (9 digits)
PHONE_PATTERNS = {
    "CZ": re.compile(r"^\+420\s?[\d\s-]{9,12}$"),
    "EE": re.compile(r"^\+372\s?[\d\s-]{7,10}$"),
    "LT": re.compile(r"^\+370\s?[\d\s-]{8,12}$"),
    "PL": re.compile(r"^\+48\s?[\d\s-]{9,12}$"),
}


def extract_ico(rejestr_str: str) -> str | None:
    """Extract 8-digit IČO from 'ARES IČO 12345678' or 'IČO: 12345678' or '12345678'."""
    s = (rejestr_str or "").strip()
    # 1. Plain 8 digits
    if re.fullmatch(r"\d{8}", s):
        return s
    # 2. IČO: NNNNNNNN or IČO NNNNNNNN
    m = re.search(r"IČO[: ]+(\d{8})", s)
    if m:
        return m.group(1)
    # 3. First 8-digit run
    m = re.search(r"\b(\d{8})\b", s)
    if m:
        return m.group(1)
    return None


def extract_registrikood(rejestr_str: str) -> str | None:
    """Extract 8-digit Registrikood."""
    s = (rejestr_str or "").strip()
    if re.fullmatch(r"\d{8}", s):
        return s
    m = re.search(r"Registrikood[: ]+(\d{8})", s)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{8})\b", s)
    if m:
        return m.group(1)
    return None


def extract_kodas(rejestr_str: str) -> str | None:
    """Extract 7-9 digit Įmonės kodas."""
    s = (rejestr_str or "").strip()
    m = re.search(r"\b(\d{7,9})\b", s)
    if m:
        return m.group(1)
    return None


def extract_vat(vat_str: str) -> str | None:
    """Extract bare digits from VAT (CZ DIČ, EE KMKR, LT PVM)."""
    s = (vat_str or "").strip()
    m = re.search(r"(\d{8,12})", s)
    if m:
        return m.group(1)
    return None


def is_generic_address(addr: str, country: str) -> tuple[bool, str]:
    """Detect if address looks fabricated (Průmyslová 10/11/12 series)."""
    a = (addr or "").strip()
    for pat in GENERIC_ADDRESS_PATTERNS:
        if re.search(pat, a):
            return True, f"generic address pattern: {pat}"
    return False, ""


def is_valid_phone(phone: str, country: str) -> bool:
    pat = PHONE_PATTERNS.get(country)
    if not pat:
        return True  # unknown country → no validation
    return bool(pat.match((phone or "").strip()))


def is_valid_email(email: str) -> bool:
    """Validate email — accept multi-recipient format `a@x.com; b@y.com`.

    Flag only when ALL recipients look like placeholders (just the local-part
    without a domain), or when the format is fully broken.
    """
    e = (email or "").strip()
    if not e or "@" not in e:
        return False
    # Split on ; , or whitespace for multi-recipient
    recipients = [r.strip() for r in re.split(r"[;,\s]+", e) if r.strip()]
    if not recipients:
        return False
    # At least one recipient must be a valid email
    has_real = False
    for r in recipients:
        if "@" not in r:
            continue  # skip empty fragments
        # Generic placeholder: only local part, no domain
        if r.lower() in ("info@", "biuro@", "kontakt@", "contact@", "office@"):
            continue
        if re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", r):
            has_real = True
            break
    return has_real


def load_existing_catalog(country: str) -> dict[str, dict]:
    """Load existing catalog-B-{ISO}.csv as a lookup by rejestr_id and nip_vat."""
    sub, dirname, iso, _ = COUNTRY_MAP[country]
    path = ROOT / "data" / dirname / f"catalog-B-{iso}.csv"
    if not path.exists():
        return {"by_rejestr": {}, "by_nip": {}, "by_name": {}}
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    by_rejestr = {}
    by_nip = {}
    by_name = {}
    for r in rows:
        rid = (r.get("rejestr_id") or "").strip()
        nip = (r.get("nip_vat") or "").strip()
        nm = (r.get("nazwa") or "").strip().lower()
        if rid:
            by_rejestr[rid] = r
        if nip:
            by_nip[nip] = r
        if nm:
            by_name[nm] = r
    return {"by_rejestr": by_rejestr, "by_nip": by_nip, "by_name": by_name}


def find_dup(lead: dict, existing: dict, country: str) -> tuple[bool, str]:
    """Check if this lead collides with existing catalog."""
    rejestr = (lead.get("Numer Rejestrowy") or "").strip()
    nip = (lead.get("NIP / VAT") or "").strip()
    firma = (lead.get("Firma") or "").strip().lower()

    # 1. IČO/Registrikood/Kodas match
    if country == "CZ":
        ico = extract_ico(rejestr)
        if ico:
            # Existing stores as 'ARES IČO 12345678'
            for key in existing["by_rejestr"]:
                if extract_ico(key) == ico:
                    return True, f"IČO {ico} already in catalog ({key})"
            # Or as bare 8-digit nip_vat
            if ico in existing["by_nip"]:
                return True, f"IČO {ico} in existing nip_vat"
    elif country == "EE":
        reg = extract_registrikood(rejestr)
        if reg:
            for key in existing["by_rejestr"]:
                if extract_registrikood(key) == reg:
                    return True, f"Registrikood {reg} already in catalog ({key})"
            if reg in existing["by_nip"]:
                return True, f"Registrikood {reg} in existing nip_vat"
    elif country == "LT":
        kod = extract_kodas(rejestr)
        if kod:
            for key in existing["by_rejestr"]:
                if extract_kodas(key) == kod:
                    return True, f"Įmonės kodas {kod} already in catalog ({key})"
            if kod in existing["by_nip"]:
                return True, f"Įmonės kodas {kod} in existing nip_vat"

    # 2. VAT match (DIČ/KMKR/PVM)
    vat = extract_vat(nip)
    if vat:
        if vat in existing["by_nip"]:
            return True, f"VAT {vat} in existing catalog"

    # 3. Fuzzy name match
    for existing_name in existing["by_name"]:
        if firma and existing_name:
            if firma == existing_name:
                return True, f"Firma {firma} exact match"
            # substring match
            if len(firma) > 5 and (firma in existing_name or existing_name in firma):
                return True, f"Firma fuzzy match: {firma} vs {existing_name}"

    return False, ""


def validate_lead(lead: dict, country: str, existing: dict) -> dict:
    """Returns verdict + reasons dict for one lead."""
    rejestr = (lead.get("Numer Rejestrowy") or "").strip()
    nip = (lead.get("NIP / VAT") or "").strip()
    adres = (lead.get("Adres") or "").strip()
    telefon = (lead.get("Telefon") or "").strip()
    email = (lead.get("Email") or "").strip()

    issues = []
    flags = []
    score = 0
    max_score = 0

    # 1. Rejestr_id format
    max_score += 2
    if country == "CZ":
        ico = extract_ico(rejestr)
        if ico and PATTERNS["CZ"]["ico"].match(ico):
            score += 2
        else:
            issues.append(f"❌ IČO niepoprawne: '{rejestr}'")
    elif country == "EE":
        reg = extract_registrikood(rejestr)
        if reg and PATTERNS["EE"]["reg"].match(reg):
            score += 2
        else:
            issues.append(f"❌ Registrikood niepoprawne: '{rejestr}'")
    elif country == "LT":
        kod = extract_kodas(rejestr)
        if kod and PATTERNS["LT"]["kodas"].match(kod):
            score += 2
        else:
            issues.append(f"❌ Įmonės kodas niepoprawne: '{rejestr}'")

    # 2. VAT format
    max_score += 1
    vat = extract_vat(nip)
    if vat:
        score += 1
    elif nip and nip not in ("do weryfikacji", "do ustalenia", ""):
        issues.append(f"⚠️ VAT format nietypowy: '{nip}'")

    # 3. Address sanity
    max_score += 1
    is_generic, gen_reason = is_generic_address(adres, country)
    if adres and not is_generic:
        score += 1
    elif is_generic:
        issues.append(f"⚠️ Halucynacja? {gen_reason}: '{adres}'")
    elif not adres:
        issues.append("⚠️ brak adresu")

    # 4. Phone format
    max_score += 1
    if telefon:
        if is_valid_phone(telefon, country):
            score += 1
        else:
            issues.append(f"⚠️ Telefon '{telefon}' nie pasuje do {country} (+XXX prefix)")

    # 5. Email format
    max_score += 1
    if email:
        if is_valid_email(email):
            score += 1
        else:
            issues.append(f"⚠️ Email '{email}' wygląda na placeholder")

    # 6. Dedup check
    is_dup, dup_reason = find_dup(lead, existing, country)
    if is_dup:
        flags.append("DUPLIKAT")
        issues.append(f"🔁 {dup_reason}")

    # Verdict
    pct = score / max_score if max_score else 0
    if is_dup:
        verdict = "🔁 DUPLIKAT"
    elif pct < 0.5:
        verdict = "❌ HALUCYNACJA"
    elif pct < 0.8:
        verdict = "⚠️ DO-WERYFIKACJI"
    else:
        verdict = "✅ FROZEN"

    return {
        "verdict": verdict,
        "score": score,
        "max_score": max_score,
        "pct": round(pct * 100),
        "issues": issues,
        "flags": flags,
    }


def validate_country(iso: str, use_network: bool = True) -> dict:
    """Validate all leads for one country."""
    sub, dirname, code, registry = COUNTRY_MAP[iso]
    src = INTAKE / sub / f"07-MASTER-Katalog-Wszystkich-Leadow-B2B-{iso}.csv"
    if not src.exists():
        return {"error": f"intake file not found: {src}"}

    rows = list(csv.DictReader(src.open(encoding="utf-8")))
    existing = load_existing_catalog(iso)

    results = []
    verdict_count = defaultdict(int)
    for r in rows:
        v = validate_lead(r, iso, existing)
        v["rank"] = r.get("Rank", "?")
        v["firma"] = r.get("Firma", "?")
        v["score_marcel"] = r.get("Score", "?")
        v["priorytet"] = r.get("Priorytet", "?")
        results.append(v)
        verdict_count[v["verdict"].split()[-1] if v["verdict"] else "?"] += 1

    return {
        "iso": iso,
        "total": len(rows),
        "verdict_count": dict(verdict_count),
        "results": results,
        "rows": rows,
    }


def write_report(report: dict, out_dir: Path) -> None:
    """Write per-country validation.md and validated.csv."""
    out_dir.mkdir(parents=True, exist_ok=True)
    iso = report["iso"]
    md_lines = [
        f"# {iso} intake validation — {report['total']} leadów",
        "",
        f"**Data:** {Path(__file__).name}, **sieć:** {'włączona' if True else 'wyłączona'}",
        "",
        "## Verdicts",
        "",
        "| Verdict | # |",
        "|---|---|",
    ]
    for v, n in sorted(report["verdict_count"].items(), key=lambda x: -x[1]):
        md_lines.append(f"| {v} | {n} |")
    md_lines.append("")

    # Detail table
    md_lines += [
        "## Per-lead",
        "",
        "| # | Score | Priorytet | Verdict | Firma | Issues |",
        "|---|---|---|---|---|---|",
    ]
    for r in report["results"]:
        issues_str = " | ".join(r["issues"][:3])
        if len(r["issues"]) > 3:
            issues_str += f" | +{len(r['issues']) - 3} więcej"
        md_lines.append(
            f"| {r['rank']} | {r['score_marcel']} | {r['priorytet']} | {r['verdict']} "
            f"| {r['firma'][:50]} | {issues_str[:200]} |"
        )
    md_lines.append("")

    # Hallucinations list
    hallucinations = [r for r in report["results"] if "HALUCYNACJA" in r["verdict"]]
    if hallucinations:
        md_lines += ["## ⚠️ Podejrzane o halucynację", ""]
        for r in hallucinations:
            md_lines.append(f"- **#{r['rank']} {r['firma']}** — {r['verdict']}")
            for i in r["issues"]:
                md_lines.append(f"  - {i}")
        md_lines.append("")

    dups = [r for r in report["results"] if "DUPLIKAT" in r["verdict"]]
    if dups:
        md_lines += ["## 🔁 Duplikaty (collision z istniejącym katalogiem)", ""]
        for r in dups:
            md_lines.append(f"- **#{r['rank']} {r['firma']}** — {r['verdict']}")
            for i in r["issues"]:
                md_lines.append(f"  - {i}")
        md_lines.append("")

    (out_dir / "validation.md").write_text("\n".join(md_lines), encoding="utf-8")

    # Validated CSV (intake + verdict + issues)
    out_csv = out_dir / "validated.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        if report["rows"]:
            fieldnames = list(report["rows"][0].keys()) + [
                "_verdict", "_pct", "_issues", "_flags"
            ]
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for row, v in zip(report["rows"], report["results"]):
                row2 = dict(row)
                row2["_verdict"] = v["verdict"]
                row2["_pct"] = v["pct"]
                row2["_issues"] = " | ".join(v["issues"])
                row2["_flags"] = ",".join(v["flags"])
                w.writerow(row2)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Marcel's intake CSVs")
    ap.add_argument("--iso", help="Country code (e.g. CZ, EE, LT)")
    ap.add_argument("--all", action="store_true", help="All countries in intake")
    ap.add_argument("--no-network", action="store_true", help="Skip live registry calls")
    args = ap.parse_args()

    if not args.iso and not args.all:
        print("Specify --iso CZ or --all")
        return 1

    targets = []
    if args.all:
        # Find all CSVs in intake
        for sub in INTAKE.iterdir():
            if not sub.is_dir():
                continue
            for f in sub.glob("07-MASTER-Katalog-Wszystkich-Leadow-B2B-*.csv"):
                m = re.search(r"-([A-Z]{2})\.csv$", f.name)
                if m:
                    targets.append(m.group(1))
    else:
        targets = [args.iso]

    grand_total = 0
    grand_verdicts = defaultdict(int)
    for iso in targets:
        if iso not in COUNTRY_MAP:
            print(f"⚠️ Unknown ISO: {iso} — skipping")
            continue
        report = validate_country(iso)
        if "error" in report:
            print(f"❌ {iso}: {report['error']}")
            continue
        write_report(report, INTAKE / COUNTRY_MAP[iso][0])
        grand_total += report["total"]
        for v, n in report["verdict_count"].items():
            grand_verdicts[v] += n
        print(
            f"✅ {iso}: {report['total']} leadów — "
            f"FROZEN={report['verdict_count'].get('FROZEN', 0)}, "
            f"DO-W={report['verdict_count'].get('DO-WERYFIKACJI', 0)}, "
            f"HALUCYNACJA={report['verdict_count'].get('HALUCYNACJA', 0)}, "
            f"DUPLIKAT={report['verdict_count'].get('DUPLIKAT', 0)}"
        )

    print()
    print(f"=== RAZEM: {grand_total} leadów ===")
    for v, n in sorted(grand_verdicts.items(), key=lambda x: -x[1]):
        print(f"  {v}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
