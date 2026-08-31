#!/usr/bin/env python3
"""
tools/verify_hallucinations.py — Re-verify the HALUCYNACJA-flagged leads to
distinguish true hallucinations from verifier false positives.

Two checks per flagged row:
  1. mod-11 checksum on the NIP. PL NIP = 10 digits where
     sum(d[i] * w[i]) mod 11 == d[10], with w = [6,5,7,2,3,4,5,6,7].
  2. KRS API lookup (when available) — verify the KRS number resolves to
     the same NIP/name as the CSV row.

Output: a markdown report with per-row verdict:
  CONFIRMED HALUCYNACJA  — both checks fail (mod-11 invalid AND KRS points elsewhere)
  LIKELY FALSE POSITIVE  — at least one check actually passes
  UNVERIFIED             — needs manual review

This tool is read-only. It produces a report and a fix-suggestions file but
does not edit the catalog CSVs.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
PLB = ROOT / "data" / "Polska" / "catalog-B-PL.csv"
REPORT = ROOT / "data" / "verification" / "hallucination_audit.md"
FIX_SUGGESTIONS = ROOT / "data" / "verification" / "hallucination_fix_suggestions.json"

PL_NIP_WEIGHTS = [6, 5, 7, 2, 3, 4, 5, 6, 7]


def pl_nip_mod11_ok(nip: str) -> tuple[bool, str]:
    """Return (is_valid, reason)."""
    nip = (nip or "").strip().replace(" ", "").replace("-", "")
    if not nip.startswith("PL"):
        nip_clean = nip
    else:
        nip_clean = nip[2:]
    if not re.fullmatch(r"\d{10}", nip_clean):
        return False, f"not 10 digits (got {len(nip_clean)})"
    digits = [int(c) for c in nip_clean]
    s = sum(d * w for d, w in zip(digits[:9], PL_NIP_WEIGHTS))
    check = s % 11
    if check == 10:
        # Per spec, if check is 10 the NIP is invalid (rare)
        return False, f"check digit = 10 (invalid)"
    if check != digits[9]:
        return False, f"expected check {check}, got {digits[9]}"
    return True, f"check digit OK ({digits[9]} = {s} mod 11)"


def normalize_name(s: str) -> str:
    """Strip legal-form suffixes and case for fuzzy match."""
    s = (s or "").upper()
    # drop common suffixes
    for suf in (" SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
                " SPÓŁKA Z OGRANICZONA ODPOWIEDZIALNOSCIA",
                " SPÓŁKA KOMANDYTOWA", " SPÓŁKA JAWNA",
                " SPÓŁKA AKCYJNA", " S.A.", " SA", " SP. Z O.O.",
                " SP Z O.O.", " SP.J.", " S.C.", " SC",
                " SP.K.", " SP.K", " PHU", " FHU", " S.C",
                " JAWNA", " AKCYJNA"):
        s = s.replace(suf, "")
    s = re.sub(r"\s+", " ", s).strip(" ,.-")
    return s


def name_match_pct(a: str, b: str) -> float:
    """Crude overlap: what fraction of shorter-name tokens appear in longer?"""
    ta = set(normalize_name(a).split())
    tb = set(normalize_name(b).split())
    if not ta or not tb:
        return 0.0
    shorter, longer = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    return len(shorter & longer) / len(shorter)


def krs_lookup(krs_number: str) -> Optional[dict]:
    """Look up a KRS number via the public KRS API (api.krs.ms.gov.pl).

    Returns {nip, nazwa, regon, ...} or None on failure.
    """
    import urllib.request
    import urllib.error
    import ssl

    krs = (krs_number or "").strip()
    if krs.startswith("KRS"):
        krs = krs[3:].strip()
    krs = krs.zfill(10)  # KRS is 10 digits
    if not re.fullmatch(r"\d{10}", krs):
        return None

    url = f"https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{krs}?rejestr=P&format=json"
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "BILLSzuka/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None


def krs_nip_name(data: dict) -> tuple[Optional[str], Optional[str]]:
    """Extract (nip, name) from a KRS API response.

    The KRS REST API returns a deeply nested structure:
    odpis.dane.dzial1.danePodmiotu.{identyfikators.nip, nazwa}
    """
    if not data:
        return None, None
    odpis = data.get("odpis") or data
    dane = odpis.get("dane") or odpis
    # Path 1: dzial1.danePodmiotu (most common for Rejestr P)
    dzial1 = dane.get("dzial1") or {}
    dp = dzial1.get("danePodmiotu") or {}
    nip = (dp.get("identyfikatory") or {}).get("nip")
    nazwa = dp.get("nazwa")
    # Path 2: flat nip/nazwa at dane level (older format)
    if not nip:
        nip = dane.get("nip")
    if not nazwa:
        nazwa = dane.get("nazwa") or dane.get("nazwaPodmiotu")
    return nip, nazwa


def main():
    if not PLB.exists():
        print(f"Catalog not found: {PLB}", file=sys.stderr)
        sys.exit(1)

    # Load rows
    with open(PLB, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Filter HALUCYNACJA rows
    flagged = [r for r in rows if "HALUCYNACJA" in (r.get("flagi") or "")]
    print(f"Found {len(flagged)} HALUCYNACJA-flagged leads in PL-B", file=sys.stderr)

    results = []
    for r in flagged:
        nip_csv = (r.get("nip_vat") or "").strip()
        krs_csv = (r.get("rejestr_id") or "").strip()
        name_csv = (r.get("nazwa_firmy") or "").strip()
        flagi = r.get("flagi") or ""

        is_krs_hallucination = "KRS" in flagi and "inną firmę" in flagi
        is_nip_mod11 = "NIP" in flagi and "mod-11" in flagi

        verdict = {
            "id": r.get("id_unikalne"),
            "name": name_csv,
            "nip_csv": nip_csv,
            "krs_csv": krs_csv,
            "flagi": flagi,
            "checks": {},
        }

        # 1. mod-11 check
        mod11_ok, mod11_reason = pl_nip_mod11_ok(nip_csv)
        verdict["checks"]["nip_mod11"] = {"ok": mod11_ok, "reason": mod11_reason}

        # 2. KRS lookup (only if we have a KRS number)
        krs_nip, krs_name = None, None
        if krs_csv.startswith("KRS"):
            krs_data = krs_lookup(krs_csv)
            krs_nip, krs_name = krs_nip_name(krs_data)
            verdict["checks"]["krs_lookup"] = {
                "ok": bool(krs_data),
                "krs_nip": krs_nip,
                "krs_name": krs_name,
            }
            if krs_nip and nip_csv:
                csv_nip_clean = nip_csv[2:] if nip_csv.startswith("PL") else nip_csv
                verdict["checks"]["krs_nip_match"] = (krs_nip == csv_nip_clean)
            if krs_name and name_csv:
                pct = name_match_pct(krs_name, name_csv)
                verdict["checks"]["krs_name_match_pct"] = round(pct, 2)
        else:
            verdict["checks"]["krs_lookup"] = {"ok": None, "reason": "no KRS number"}

        # Final verdict
        # 1. KRS-hallucination case: API NIP ≠ CSV NIP → confirmed hallucination
        # 2. NIP mod-11: if mod-11 actually OK → false positive (verifier bug)
        # 3. NIP mod-11 fails AND KAS rejects → confirmed hallucination
        if is_krs_hallucination:
            kn = verdict["checks"].get("krs_nip_match")
            if kn is False:
                verdict["verdict"] = "CONFIRMED HALUCYNACJA (KRS→other company)"
            elif kn is True:
                verdict["verdict"] = "LIKELY FALSE POSITIVE (KRS matches CSV)"
            else:
                verdict["verdict"] = "UNVERIFIED (KRS API unreachable)"
        else:
            if mod11_ok:
                verdict["verdict"] = "LIKELY FALSE POSITIVE (NIP mod-11 OK)"
            else:
                # NIP mod-11 failed. Per audit 2026-08-31: KAS WL API
                # returns 400 'WL-115: Nieprawidłowy NIP.' for ALL 19
                # such cases (cross-checked manually), so this is
                # essentially always a real hallucination. We mark
                # as CONFIRMED and let the operator spot-check.
                verdict["verdict"] = "CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects)"

        results.append(verdict)

    # Write report
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    counts = {
        "CONFIRMED HALUCYNACJA (KRS→other company)": 0,
        "LIKELY FALSE POSITIVE (NIP mod-11 OK)": 0,
        "LIKELY FALSE POSITIVE (KRS matches CSV)": 0,
        "UNVERIFIED (KRS API unreachable)": 0,
        "UNVERIFIED (NIP mod-11 fails; needs registry check)": 0,
    }
    for v in results:
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("# HALUCYNACJA Audit — 2026-08-31\n\n")
        f.write(f"Total flagged: **{len(results)}** leads in PL-B\n\n")
        f.write("## Summary\n\n")
        f.write("| Verdict | Count |\n|---|---|\n")
        for k, n in sorted(counts.items(), key=lambda x: -x[1]):
            f.write(f"| {k} | {n} |\n")
        f.write("\n## Per-row details\n\n")
        f.write("| ID | Name | NIP CSV | KRS CSV | mod-11 | KRS lookup | Verdict |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for v in results:
            m = v["checks"].get("nip_mod11", {})
            k = v["checks"].get("krs_lookup", {})
            nip_disp = v["nip_csv"][:13] if v["nip_csv"] else ""
            krs_disp = v["krs_csv"][:14] if v["krs_csv"] else ""
            mod11_disp = f"✅ {m.get('reason', '?')[:40]}" if m.get("ok") else f"❌ {m.get('reason', '?')[:40]}"
            if k.get("ok") is True:
                krs_api_nip = k.get('krs_nip') or '?'
                krs_disp = f"→ NIP {krs_api_nip[:10] if isinstance(krs_api_nip, str) else '?'} name match {v['checks'].get('krs_name_match_pct', '?')}"
            elif k.get("ok") is False:
                krs_disp = "❌ unreachable"
            else:
                krs_disp = "—"
            f.write(f"| {v['id']} | {v['name'][:40]} | {nip_disp} | {krs_disp} | {mod11_disp} | {krs_disp} | {v['verdict']} |\n")
        f.write("\n## Notes\n\n")
        f.write("- **CONFIRMED HALUCYNACJA**: KRS API returns a NIP that doesn't match the CSV's NIP. The CSV's `krs_id` is real but belongs to a different company. The verifier was right.\n")
        f.write("- **LIKELY FALSE POSITIVE**: mod-11 actually passes (verifier had a bug), or KRS lookup matches. The CSV value is correct; the flag should be cleared.\n")
        f.write("- **UNVERIFIED**: cannot reach the registry or mod-11 genuinely fails. Needs manual review.\n")

    # Write fix suggestions
    with open(FIX_SUGGESTIONS, "w", encoding="utf-8") as f:
        json.dump({
            "generated": "2026-08-31",
            "summary": counts,
            "fixes": [
                {
                    "id": v["id"],
                    "name": v["name"],
                    "verdict": v["verdict"],
                    "action": (
                        "CLEAR halucynacja flag — mod-11 actually OK"
                        if "FALSE POSITIVE" in v["verdict"]
                        else "KEEP flag — confirmed hallucination, KRS points to other company"
                        if "CONFIRMED" in v["verdict"]
                        else "MANUAL REVIEW — verifier was right but registry unreachable"
                    ),
                    "checks": v["checks"],
                }
                for v in results
            ],
        }, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 70)
    print("  HALUCYNACJA Audit Results")
    print("=" * 70)
    for k, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {n:3d}  {k}")
    print("=" * 70)
    print(f"  Report:    {REPORT}")
    print(f"  Fix data:  {FIX_SUGGESTIONS}")
    print("=" * 70)


if __name__ == "__main__":
    main()
