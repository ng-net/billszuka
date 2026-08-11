#!/usr/bin/env python3
"""
auto_enrich.py — BILLSzuka lead enrichment via OpenRouter + agent web search.

Usage as a script (driver = agent):
  python3 tools/auto_enrich.py extract \
    --name "ACME SP. Z O.O." --city "Warszawa" --country PL \
    --search-results "$(cat search.txt)"

Usage as a library:
  from auto_enrich import enrich_from_search_results
  result = enrich_from_search_results(name=..., city=..., country=..., text=...)

The agent driver does the web_search (with web_search tool) and feeds the
resulting text here for LLM extraction via OpenRouter (DeepSeek).

State is tracked in data/.verify-state/enrichment-progress.json so the
recursive run is resumable across sessions.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STATE_DIR = DATA / ".verify-state"
STATE_FILE = STATE_DIR / "enrichment-progress.json"
ENV_FILE = ROOT / ".env"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-chat"


# ---------------------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------------------

def _load_env() -> dict[str, str]:
    """Load .env values as the source of truth (override OS env).

    OS env may contain a truncated/placeholder value (e.g. when running
    inside a sandboxed agent), so we read .env second and let it win.
    """
    env: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    # Then layer OS env on top only for keys not in .env
    for k, v in os.environ.items():
        env.setdefault(k, v)
    return env


# ---------------------------------------------------------------------------
# OpenRouter call
# ---------------------------------------------------------------------------

def _call_openrouter(prompt: str, system: str, model: str = DEFAULT_MODEL,
                     max_tokens: int = 400, timeout: int = 30) -> str:
    env = _load_env()
    api_key = env.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set in .env")

    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.0,  # deterministic for extraction
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://billszuka.local",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Extraction logic
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "Jesteś asystentem BILLSzuka — polskiej platformy B2B research. "
    "Dostaniesz wyniki wyszukiwania dla firmy. Wyciągnij z nich decydenta "
    "(osobę podejmującą decyzje): imię, nazwisko, stanowisko, e-mail, telefon, "
    "LinkedIn. Zwróć TYLKO JSON, bez żadnego tekstu dookoła. Gdy brak — pole null."
)


def enrich_from_search_results(name: str, city: str, country: str,
                               text: str, model: str = DEFAULT_MODEL) -> dict:
    """
    Given raw web search text for a company, extract decision-maker fields
    via OpenRouter. Returns a dict (possibly empty) ready to merge into a
    BILLSzuka catalog CSV row.
    """
    if not text or not text.strip():
        return {}

    user_prompt = (
        f"Firma: {name}\n"
        f"Miasto: {city or '?'}\n"
        f"Kraj: {country or '?'}\n\n"
        f"Wyniki wyszukiwania:\n{text[:3500]}\n\n"
        "Zwróć JSON:\n"
        "{\n"
        '  "name": "Jan Kowalski" | null,\n'
        '  "title": "CEO" | "właściciel" | null,\n'
        '  "email": "jan@acme.pl" | null,\n'
        '  "phone": "+48 22 123 45 67" | null,\n'
        '  "linkedin": "https://linkedin.com/in/..." | null,\n'
        '  "confidence": 0.0-1.0\n'
        "}"
    )

    try:
        raw = _call_openrouter(user_prompt, SYSTEM_PROMPT, model=model)
    except (urllib.error.URLError, KeyError, TimeoutError, RuntimeError, OSError) as e:
        return {"_error": f"{type(e).__name__}: {e}"}

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"```\s*$", "", raw)
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Last resort: find a JSON object in the response
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return {"_error": f"non-JSON response: {raw[:200]}"}
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError as e:
            return {"_error": f"JSON parse error: {e} | {raw[:200]}"}

    # Clean: drop null fields, keep _meta if present
    if isinstance(data, list):
        # LLM returned multiple decision-makers — pick the highest-confidence
        # one as the primary; keep the rest as "_alternates" for review.
        if not data:
            return {}
        primary_idx, primary = max(
            enumerate(data),
            key=lambda kv: kv[1].get("confidence", 0) if isinstance(kv[1], dict) else 0,
        )
        if not isinstance(primary, dict):
            return {"_error": f"unexpected list element: {primary}"}
        cleaned = {k: v for k, v in primary.items() if v and v != "null"}
        if len(data) > 1:
            cleaned["_alternates"] = [
                {k: v for k, v in d.items() if v and v != "null"}
                for i, d in enumerate(data) if i != primary_idx and isinstance(d, dict)
            ]
        return cleaned
    if not isinstance(data, dict):
        return {"_error": f"unexpected response type: {type(data).__name__}: {str(data)[:200]}"}
    cleaned = {k: v for k, v in data.items() if v and v != "null"}
    return cleaned


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Lead discovery: find rows with missing decydent
# ---------------------------------------------------------------------------

NEEDS_ENRICHMENT_VALUES = {"do ustalenia", "do ustalenia ", "brak", "n/a",
                            "do weryfikacji", "brak danych", "", "---", "?"}


def find_unenriched_leads() -> list[dict]:
    """Scan data/{Kraj}/catalog-*.csv for rows needing enrichment.

    Skips non-country subdirs (backups, snapshots, verify-state, verification)
    so we only scan the live country catalogs.
    """
    SKIP_DIRS = {".snapshots", ".verify-state", "backups", "verification"}
    leads: list[dict] = []
    for sub in sorted(DATA.iterdir()):
        if not sub.is_dir() or sub.name.startswith("."):
            continue
        if sub.name in SKIP_DIRS:
            continue
        # Only match canonical catalog files: catalog-A-XX.csv / catalog-B-XX.csv.
        # Skip pre-clean snapshots, splits, intermediates (anything with a
        # "-pre-clean-*" or extra suffix after the country code).
        for csv_path in sorted(sub.glob("catalog-[AB]-*.csv")):
            stem = csv_path.stem  # e.g. "catalog-A-PL" or "catalog-A-PL-pre-clean-20260811_023054"
            if not (stem.startswith("catalog-A-") or stem.startswith("catalog-B-")):
                continue
            # Canonical: "catalog-A-CC" or "catalog-B-CC" where CC is exactly 2 letters
            tail = stem[len("catalog-A-"):] if stem.startswith("catalog-A-") else stem[len("catalog-B-"):]
            if len(tail) != 2 or not tail.isalpha() or not tail.isupper():
                continue
            if csv_path.name.startswith("._"):
                continue
            with csv_path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    decydent = (row.get("decydent") or "").strip()
                    if decydent.lower() not in NEEDS_ENRICHMENT_VALUES:
                        continue
                    leads.append({
                        "country": (row.get("kraj") or "").strip(),
                        "country_dir": sub.name,
                        "id": (row.get("id_unikalne") or "").strip(),
                        "name": (row.get("nazwa_firmy") or "").strip(),
                        "city": (row.get("miasto") or "").strip(),
                        "www": (row.get("www") or "").strip(),
                        "csv_path": str(csv_path),
                    })
    return leads


def next_batch(limit: int = 10, skip_done: bool = True) -> list[dict]:
    """Return up to `limit` unenriched leads, optionally skipping already-processed."""
    state = load_state() if skip_done else {}
    done = set(state.get("done", {}).keys())
    out: list[dict] = []
    for lead in find_unenriched_leads():
        key = f"{lead['id']}@{lead['csv_path']}"
        if key in done:
            continue
        out.append(lead)
        if len(out) >= limit:
            break
    return out


def mark_done(lead: dict, result: dict) -> None:
    """Mark a lead as processed in the state file."""
    state = load_state()
    key = f"{lead['id']}@{lead['csv_path']}"
    state.setdefault("done", {})[key] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "name": lead["name"],
        "country": lead["country"],
        "confidence": result.get("confidence"),
        "fields": [k for k in result.keys() if not k.startswith("_")],
        "had_error": "_error" in result,
    }
    save_state(state)


# ---------------------------------------------------------------------------
# CSV update: write a single row's enrichment back
# ---------------------------------------------------------------------------

import csv


def update_csv_row(csv_path: str, row_id: str, fields: dict) -> bool:
    """
    Update the row with id_unikalne=row_id in csv_path with the given fields.
    Only fields with non-empty values are written; existing data is preserved.
    Returns True if the row was found and updated.
    """
    path = Path(csv_path)
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    if not header or "id_unikalne" not in header:
        return False

    target = None
    for r in rows:
        if (r.get("id_unikalne") or "").strip() == row_id:
            target = r
            break
    if target is None:
        return False

    # Map enrichment fields to CSV columns
    column_map = {
        "name": "decydent",
        "title": "stanowisko",
        "email": "email_decydent",
        "phone": "telefon",
        "linkedin": "linkedin",
    }

    def _is_placeholder(v: str) -> bool:
        return (v or "").strip().lower() in NEEDS_ENRICHMENT_VALUES

    for k, v in fields.items():
        col = column_map.get(k)
        if col and col in header and v:
            existing = target.get(col, "") or ""
            # Overwrite if the cell is empty OR holds a known placeholder
            if not existing.strip() or _is_placeholder(existing):
                target[col] = str(v)[:200]  # truncate to safe length

    # Bump data_weryfikacji if present
    if "data_weryfikacji" in header:
        target["data_weryfikacji"] = time.strftime("%Y-%m-%d")

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    return main_with_args(sys.argv[1:])


def main_with_args(argv: list[str]) -> int:
    """Testable entry point. argv is the arg list (without argv[0])."""
    ap = argparse.ArgumentParser(description="BILLSzuka lead enrichment (OpenRouter)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # extract: run LLM on given search results
    p_ext = sub.add_parser("extract", help="Extract decision-maker from search text")
    p_ext.add_argument("--name", required=True)
    p_ext.add_argument("--city", default="")
    p_ext.add_argument("--country", default="")
    p_ext.add_argument("--search-results", required=True, help="Raw text from web_search")
    p_ext.add_argument("--model", default=DEFAULT_MODEL)

    # leads: list unenriched leads
    sub.add_parser("leads", help="Print all leads that need enrichment")

    # apply: update a single CSV row from JSON
    p_app = sub.add_parser("apply", help="Update a CSV row with extracted JSON")
    p_app.add_argument("--csv", required=True)
    p_app.add_argument("--id", required=True, dest="row_id")
    p_app.add_argument("--json", required=True, help="JSON string with extracted fields")

    # process: extract + apply + mark_done in one call (agent driver uses this)
    p_proc = sub.add_parser("process", help="Full pipeline: extract+apply+mark")
    p_proc.add_argument("--csv", required=True)
    p_proc.add_argument("--id", required=True, dest="row_id")
    p_proc.add_argument("--name", required=True)
    p_proc.add_argument("--city", default="")
    p_proc.add_argument("--country", default="")
    p_proc.add_argument("--search-results", required=True,
                        help="Raw text from web_search (one lead)")
    p_proc.add_argument("--no-state", action="store_true",
                        help="Skip the mark_done state file write")
    p_proc.add_argument("--model", default=DEFAULT_MODEL)

    args = ap.parse_args()

    if args.cmd == "extract":
        result = enrich_from_search_results(
            name=args.name, city=args.city, country=args.country,
            text=args.search_results, model=args.model,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "leads":
        for lead in find_unenriched_leads():
            print(f"{lead['id']}\t{lead['country']}\t{lead['name']}\t{lead['city']}\t{lead['www']}\t{lead['csv_path']}")
        return 0

    if args.cmd == "apply":
        try:
            fields = json.loads(args.json)
        except json.JSONDecodeError as e:
            print(f"invalid JSON: {e}", file=sys.stderr)
            return 1
        ok = update_csv_row(args.csv, args.row_id, fields)
        print("OK" if ok else "NOT_FOUND")
        return 0 if ok else 1

    if args.cmd == "process":
        result = enrich_from_search_results(
            name=args.name, city=args.city, country=args.country,
            text=args.search_results, model=args.model,
        )
        # Strip _alternates for CSV write (we only update primary fields)
        write_fields = {k: v for k, v in result.items() if not k.startswith("_")}
        if write_fields:
            ok = update_csv_row(args.csv, args.row_id, write_fields)
        else:
            ok = False
        if not args.no_state:
            mark_done(
                {"id": args.row_id, "csv_path": args.csv, "name": args.name,
                 "country": args.country},
                result,
            )
        # Print summary on a single line for the agent to capture
        fields_written = [k for k in write_fields.keys() if k in ("name", "title", "email", "phone", "linkedin")]
        print(json.dumps({
            "id": args.row_id,
            "ok": ok,
            "primary": {k: result.get(k) for k in ("name", "title", "phone", "email", "linkedin")},
            "confidence": result.get("confidence"),
            "alternates_count": len(result.get("_alternates", [])),
            "error": result.get("_error"),
        }, ensure_ascii=False))
        return 0 if ok else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
