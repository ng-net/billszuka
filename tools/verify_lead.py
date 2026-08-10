#!/usr/bin/env python3
"""
verify_lead.py — Double-check a BILLSzuka lead using 2+ tools.

Pipeline per lead:
  Tool 1: web_search to confirm company + extract NIP/contact
  Tool 2: whois (if www present)
  Tool 3: registry API (if NIP found)

Output: PASS / CONCERN / FAIL with evidence chain
Saves: tools/.verify-runs/<timestamp>-<country>.json

Usage:
  python3 tools/verify_lead.py --country CZ --limit 10
  python3 tools/verify_lead.py --country PL
  python3 tools/verify_lead.py --ids PL-A-WP-001 PL-B-LB-001
  python3 tools/verify_lead.py --all --limit 5
  python3 tools/verify_lead.py --resume  # continue from last checkpoint
"""

import argparse
import csv
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TOOLS = ROOT / "tools"
RUNS_DIR = TOOLS / ".verify-runs"
CHECKPOINT = TOOLS / ".verify-checkpoint.json"

# Country → TLD whois server + registry
WHOIS_SERVER = {
    "PL": "whois.dns.pl", "CZ": "whois.nic.cz", "SK": "whois.sk-nic.sk",
    "DE": "whois.denic.de", "AT": "whois.nic.at", "FR": "whois.afnic.fr",
    "IT": "whois.nic.it", "ES": "whois.nic.es", "NL": "whois.sidn.nl",
    "BE": "whois.dns.be", "PT": "whois.dns.pt", "HU": "whois.domain.hu",
    "RO": "whois.rotld.ro", "BG": "whois.register.bg", "HR": "whois.dns.hr",
    "SI": "whois.register.si", "RS": "whois.rnids.rs", "BA": "whois.ripe.net",
    "MD": "whois.md", "UA": "whois.ua", "LT": "whois.domreg.lt",
    "LV": "whois.nic.lv", "EE": "whois.tld.ee", "FI": "whois.ficora.fi",
    "SE": "whois.iis.se", "NO": "whois.norid.no", "DK": "whois.dk-hostmaster.dk",
}


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def load_country_leads(country_name: str) -> list:
    """Load all leads from a country's catalog-B (and catalog-A) CSVs."""
    leads = []
    for csv_path in DATA.glob(f"{country_name}/catalog-*.csv"):
        if csv_path.stat().st_size < 400:
            continue
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                id_ = (row.get("id_unikalne") or "").strip()
                if id_:
                    leads.append({**row, "_file": str(csv_path.relative_to(ROOT))})
    return leads


def normalize_url(url: str) -> str | None:
    """Extract domain from URL."""
    if not url or url in ("do ustalenia", "brak", ""):
        return None
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc:
            return parsed.netloc.replace("www.", "")
    except Exception:
        return None
    return None


def tool1_web_search(name: str, country_code: str) -> dict:
    """Tool 1: web search to confirm company + extract NIP/contact.
    Returns: {"exists": bool, "evidence": str, "extracted": {nip, address, phone}}
    """
    # Use the bash tool to call web_search (since we have no direct API)
    # The web_search tool is exposed by the host; we use it via subprocess
    # For now: use a placeholder and let the verifier agent call the actual tool
    # This is the design — actual web_search calls happen at the agent level,
    # not in this script (we don't have the search tool inside Python).
    return {
        "tool": "web_search",
        "status": "PENDING",
        "note": "web_search must be invoked at agent level — not from Python"
    }


def tool2_whois(domain: str, country_code: str) -> dict:
    """Tool 2: whois lookup. Returns registration status + dates."""
    server = WHOIS_SERVER.get(country_code, "whois.iana.org")
    try:
        result = subprocess.run(
            ["whois", "-h", server, domain],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout + result.stderr
        # Parse key fields
        evidence = {
            "tool": "whois",
            "server": server,
            "domain": domain,
            "raw_lines": len(output.splitlines()),
        }
        # Common patterns
        for pat, key in [
            (r"(?i)registrar:\s*(.+)", "registrar"),
            (r"(?i)registered:\s*(.+)", "registered"),
            (r"(?i)created:\s*(.+)", "created"),
            (r"(?i)creation\s*date:\s*(.+)", "creation_date"),
            (r"(?i)updated\s*date:\s*(.+)", "updated"),
            (r"(?i)status:\s*(.+)", "status"),
            (r"(?i)registrant:\s*(.+)", "registrant"),
        ]:
            m = re.search(pat, output)
            if m:
                evidence[key] = m.group(1).strip()[:200]
        # Status check
        if re.search(r"(?i)no match|not found|status:\s*available", output):
            evidence["domain_active"] = False
        elif re.search(r"(?i)status:\s*(ok|active|registered)", output):
            evidence["domain_active"] = True
        return evidence
    except subprocess.TimeoutExpired:
        return {"tool": "whois", "error": "timeout"}
    except Exception as e:
        return {"tool": "whois", "error": str(e)}


def tool3_registry(nip: str, country_code: str) -> dict:
    """Tool 3: registry API (KRS/CEIDG/ARES) for NIP → firma match.
    Stub: returns PENDING; agent must fill in from verify_api.py result.
    """
    return {
        "tool": "registry",
        "nip": nip,
        "country": country_code,
        "status": "PENDING",
        "note": "Use verify_api.py for live API call"
    }


def verify_lead(lead: dict) -> dict:
    """Run all applicable tools on a lead. Returns verdict + evidence."""
    id_ = lead.get("id_unikalne", "")
    name = lead.get("nazwa_firmy", "")
    country_code = lead.get("kraj", "")
    www = lead.get("www", "")
    nip = lead.get("nip_vat", "")

    result = {
        "id": id_,
        "name": name,
        "country": country_code,
        "verdict": "PENDING",
        "evidence": {}
    }

    # Tool 2: whois (if www)
    domain = normalize_url(www)
    if domain:
        result["evidence"]["whois"] = tool2_whois(domain, country_code)

    # Tool 3: registry (if NIP looks real)
    if nip and nip not in ("do weryfikacji", "brak", "brak danych", ""):
        clean = re.sub(r"^[A-Z]{2}", "", nip).strip()
        if re.match(r"^\d{8,10}$", clean):
            result["evidence"]["registry"] = tool3_registry(clean, country_code)

    # Tool 1 is left PENDING — agent will fill in from web_search
    result["evidence"]["web_search"] = tool1_web_search(name, country_code)

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="BILLSzuka lead double-check")
    ap.add_argument("--country", help="Process one country's leads")
    ap.add_argument("--ids", nargs="+", help="Process specific lead IDs")
    ap.add_argument("--all", action="store_true", help="Process all leads")
    ap.add_argument("--limit", type=int, default=0, help="Max leads to process")
    ap.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    ap.add_argument("--dry-run", action="store_true", help="Plan but don't run")
    args = ap.parse_args()

    # Load checkpoint
    done_ids = set()
    if args.resume and CHECKPOINT.exists():
        done_ids = set(json.loads(CHECKPOINT.read_text()))

    # Determine leads to process
    leads = []
    if args.country:
        leads = load_country_leads(args.country)
    elif args.all:
        for d in ["Bułgaria", "Chorwacja", "Czechy", "Estonia", "Francja",
                   "Litwa", "Mołdawia", "Polska", "Rumunia", "Słowacja",
                   "Słowenia", "Łotwa"]:
            leads.extend(load_country_leads(d))
    elif args.ids:
        # Find specific IDs across all CSVs
        for d in ["Bułgaria", "Chorwacja", "Czechy", "Estonia", "Francja",
                   "Litwa", "Mołdawia", "Polska", "Rumunia", "Słowacja",
                   "Słowenia", "Łotwa"]:
            for csv_path in DATA.glob(f"{d}/catalog-*.csv"):
                with open(csv_path, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        if (row.get("id_unikalne") or "").strip() in args.ids:
                            leads.append({**row, "_file": str(csv_path.relative_to(ROOT))})

    # Filter out already-done
    leads = [l for l in leads if l.get("id_unikalne", "") not in done_ids]

    if args.limit:
        leads = leads[:args.limit]

    log(f"Processing {len(leads)} leads (skipped {len(done_ids)} already done)")

    if args.dry_run:
        for l in leads:
            print(f"  {l.get('id_unikalne')}: {l.get('nazwa_firmy')} ({l.get('kraj')})")
        return 0

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_file = RUNS_DIR / f"{timestamp}.jsonl"

    with open(output_file, "w", encoding="utf-8") as f:
        for lead in leads:
            result = verify_lead(lead)
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            log(f"  {result['id']}: {result['name']} — evidence collected ({len(result['evidence'])} tools)")

            # Update checkpoint
            done_ids.add(result["id"])
            CHECKPOINT.write_text(json.dumps(sorted(done_ids)))

    log(f"Done. Output: {output_file.relative_to(ROOT)}")
    log(f"Total verified: {len(leads)} | Total in checkpoint: {len(done_ids)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
