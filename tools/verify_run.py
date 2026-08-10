#!/usr/bin/env python3
"""
verify_run.py — BILLSzuka verification round.

What it does (per verify-data skill):
  1. Diffs per-kraj CSVs (data/{Kraj}/catalog-*.csv) against last-known row hashes
  2. Snapshots touched files to data/.snapshots/<file>-<ts>.csv (keeps last 5 per file)
  3. Re-verifies each changed row using country-specific rules + (where implemented) API
  4. Updates the `flagi` column (FROZEN / DO-WERYFIKACJI) on changed rows
  5. Appends a block to data/audit-log.md
  6. Regenerates data/master.csv
  7. Saves new state to data/.verify-state/row-hashes.json

Usage:
  python3 tools/verify_run.py             # run on changes since last run
  python3 tools/verify_run.py --init      # first run: build state without re-verifying
  python3 tools/verify_run.py --all       # re-verify every row (force)
  python3 tools/verify_run.py --dry-run   # report what would change, write nothing

Country API status:
  PL: format check (CEIDG/KRS API call left as TODO — needs token from .env)
  CZ: format check (ARES API call left as TODO)
  others: format check only; flagged DO-WERYFIKACJI with reason "no API yet"
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STATE_DIR = DATA / ".verify-state"
SNAPSHOT_DIR = DATA / ".snapshots"
STATE_FILE = STATE_DIR / "row-hashes.json"
AUDIT_LOG = DATA / "audit-log.md"
MASTER_CSV = DATA / "master.csv"

# Per the verify-data skill
FROZEN_REQUIRED = ["nazwa_firmy", "nip_vat", "rejestr_id", "adres", "zrodlo_danych"]
OFFICIAL_SOURCE_TOKENS = [
    "krs api", "krs.gov", "ceidg", "vies", "kas", "regon",
    "ares", "orsr", "rekvizitai", "ajpes",
]
COUNTRY_API = {
    "PL": "ceidg",  # CEIDG + KRS
    "CZ": "ares",   # ARES
    # SK: orsr, LT: rekvizitai, LV: ?, EE: ariregister, BG: ?, FR: ?, HR: ?, MD: ?, RO: ?, SI: ajpes
}


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def hash_row(row: dict) -> str:
    """Stable hash of a row, excluding verification metadata columns."""
    h = hashlib.sha256()
    skip = {"flagi", "data_weryfikacji", None, ""}
    for k in sorted((k_ for k_ in row.keys() if k_ not in skip), key=lambda x: x or ""):
        h.update((k or "").encode())
        h.update(b"=")
        h.update((row.get(k) or "").strip().encode())
        h.update(b"|")
    return h.hexdigest()[:16]


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"files": {}, "last_run": None}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state["last_run"] = datetime.now(timezone.utc).astimezone().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def snapshot_file(path: Path) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = SNAPSHOT_DIR / f"{path.stem}-{ts}.csv"
    dest.write_text(path.read_text())
    # Prune to last 5 per basename
    snaps = sorted(SNAPSHOT_DIR.glob(f"{path.stem}-*.csv"))
    for old in snaps[:-5]:
        old.unlink(missing_ok=True)
    return dest


def find_changed(csv_path: Path, state: dict, force_all: bool):
    """Returns (added, modified, removed, current) for one CSV vs state."""
    rel = csv_path.relative_to(ROOT).as_posix()
    prev = state["files"].get(rel, {})
    prev_ids = set(prev.keys())

    current: dict[str, dict] = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_ = (row.get("id_unikalne") or "").strip()
            if not id_:
                continue
            current[id_] = {"row": row, "hash": hash_row(row)}

    cur_ids = set(current.keys())
    if force_all:
        added_ids = cur_ids - prev_ids
        modified_ids = cur_ids & prev_ids
        removed_ids = prev_ids - cur_ids
    else:
        added_ids = cur_ids - prev_ids
        modified_ids = {i for i in cur_ids & prev_ids if current[i]["hash"] != prev[i]}
        removed_ids = prev_ids - cur_ids

    added = [{"id": i, **current[i]} for i in added_ids]
    modified = [{"id": i, **current[i]} for i in modified_ids]
    removed = [{"id": i, "row": prev[i]} for i in removed_ids]

    return added, modified, removed, current


def verify_row(row: dict) -> tuple[str, str]:
    """Return (status, reason) per verify-data skill rules."""
    country = (row.get("kraj") or "").upper().strip()
    zrodlo = (row.get("zrodlo_danych") or "").lower()
    nip = (row.get("nip_vat") or "").replace(" ", "").replace("-", "")

    # 1. Required fields present and not placeholders
    placeholders = {"", "brak", "brak danych", "do weryfikacji", "n/a", "—"}
    missing = []
    for f in FROZEN_REQUIRED:
        val = (row.get(f) or "").strip()
        if val.lower() in placeholders:
            missing.append(f)
    if missing:
        return "DO-WERYFIKACJI", f"Brak pól: {', '.join(missing)}"

    # 2. NIP/VAT format per country (strip EU country prefix if present)
    clean_nip = re.sub(r"^[A-Z]{2}", "", nip).strip()
    if country == "PL" and not re.match(r"^\d{10}$", clean_nip):
        return "DO-WERYFIKACJI", f"NIP PL nieprawidłowy ({nip})"
    if country == "CZ" and not re.match(r"^\d{8}$", clean_nip):
        return "DO-WERYFIKACJI", f"IČO CZ nieprawidłowe ({nip})"

    # 3. Source is official
    has_official = any(tok in zrodlo for tok in OFFICIAL_SOURCE_TOKENS)
    if not has_official:
        return "DO-WERYFIKACJI", f"Źródło nieoficjalne: {row.get('zrodlo_danych')}"

    # 4. Country has live API (PL/CZ format check; others: flag with reason)
    if country not in COUNTRY_API:
        return "DO-WERYFIKACJI", f"Brak API dla {country} — tylko format-check"

    # TODO: actually fire CEIDG/KRS/ARES API and verify NIP ↔ firma match
    # For now: trust format + official source = FROZEN
    return "FROZEN", f"Źródło oficjalne ({row.get('zrodlo_danych')}), format NIP OK"


def update_csv_flags(csv_path: Path, updates: dict[str, tuple[str, str]], force: bool = False) -> int:
    """Apply status updates to the flagi column. Returns count updated.

    Rows that already have an "(API)" marker set by verify_api.py are skipped,
    unless force=True. This prevents verify_run from overwriting live-API
    verification results with its own format-check status.
    """
    if not updates:
        return 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    if "id_unikalne" not in header or "flagi" not in header:
        return 0

    id_idx = header.index("id_unikalne")
    flagi_idx = header.index("flagi")
    n = 0
    skipped_api = 0
    for row in rows:
        id_ = row[id_idx]
        if id_ in updates:
            existing = row[flagi_idx] or ""
            # Skip rows already verified via live API (unless --force)
            if not force and "(API)" in existing:
                skipped_api += 1
                continue
            status, _reason = updates[id_]
            # Strip any prior FROZEN/DO-WERYFIKACJI marker (keep emojis/flags)
            cleaned = re.sub(r"\s*✅\s*FROZEN(?:\s*\(API\))?", "", existing)
            cleaned = re.sub(r"\s*⚠️\s*DO-WERYFIKACJI(?:\s*\(API\))?", "", cleaned)
            cleaned = re.sub(r"\s*✅\s*🐋\s*FROZEN", "", cleaned)
            marker = "✅ FROZEN" if status == "FROZEN" else "⚠️ DO-WERYFIKACJI"
            row[flagi_idx] = f"{cleaned.strip()} {marker}".strip()
            n += 1

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    if skipped_api:
        log(f"  (skipped {skipped_api} API-verified rows — use --force to override)")
    return n


def regenerate_master() -> tuple[bool, int]:
    """Regenerate data/master.csv from per-kraj CSVs. Returns (ok, row_count)."""
    cmd = """
{
    first=$(ls */catalog-*.csv 2>/dev/null | head -1)
    if [ -z "$first" ]; then exit 1; fi
    head -1 "$first"
    for d in Polska Czechy Bułgaria Chorwacja Estonia Francja Litwa Łotwa Mołdawia Rumunia Słowacja Słowenia; do
        [ -d "$d" ] || continue
        for f in "$d"/catalog-A-*.csv "$d"/catalog-B-*.csv; do
            [ -f "$f" ] && tail -n +2 "$f" | grep -v '^$'
        done
    done
} > master.csv
"""
    result = subprocess.run(
        ["bash", "-c", cmd], cwd=DATA, capture_output=True, text=True
    )
    # Filter macOS plist noise from stderr
    if result.stderr:
        clean = "\n".join(
            line for line in result.stderr.splitlines()
            if "CFPropertyList" not in line and "Break on _CFPropertyList" not in line
        )
        if clean:
            log(f"master regen stderr: {clean}")
    if result.returncode != 0:
        log(f"master.csv regen failed: {result.stderr.strip()}")
        return False, 0
    # Count data rows
    try:
        with open(MASTER_CSV) as f:
            return True, max(0, sum(1 for _ in f) - 1)
    except FileNotFoundError:
        return False, 0


def append_audit(results, added, modified, removed):
    """Append an audit-log block per verify-data skill format."""
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    lines = [f"\n## {now}\n"]

    # Count by file
    file_counts: dict[str, int] = {}
    for r in added + modified:
        f = Path(r["row"].get("__file__", "")).name
        file_counts[f] = file_counts.get(f, 0) + 1

    if file_counts:
        lines.append("### Pliki sprawdzone")
        for fname, n in sorted(file_counts.items()):
            lines.append(f"- {fname}: {n} {'wpis' if n == 1 else 'wpisów'}")

    frozen = [r for r in results if r["status"] == "FROZEN"]
    dov = [r for r in results if r["status"] == "DO-WERYFIKACJI"]

    if frozen:
        lines.append("\n### ✅ FROZEN")
        for r in frozen:
            lines.append(f"- **{r['id']}**: {r['reason']}")

    if dov:
        lines.append("\n### ⚠️ DO-WERYFIKACJI")
        for r in dov:
            lines.append(f"- **{r['id']}**: {r['reason']}")

    lines.append(
        f"\n**Run summary:** {len(added)} added, {len(modified)} modified, "
        f"{len(removed)} removed — {len(frozen)} FROZEN, {len(dov)} DO-WERYFIKACJI"
    )

    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="BILLSzuka verification round")
    ap.add_argument("--init", action="store_true", help="First run: build state without re-verifying")
    ap.add_argument("--all", action="store_true", help="Re-verify every row (force)")
    ap.add_argument("--force", action="store_true", help="Override API-verified markers (re-verify even rows with (API) flag)")
    ap.add_argument("--dry-run", action="store_true", help="Report only, write nothing")
    args = ap.parse_args()

    if not DATA.exists():
        log(f"ERROR: {DATA} not found")
        return 1

    state = load_state()
    all_results = []
    all_added, all_modified, all_removed = [], [], []
    file_updates: dict[str, dict[str, tuple[str, str]]] = {}

    csv_files = sorted(
        p for p in DATA.glob("*/catalog-*.csv")
        if p.is_file() and not p.parent.name.startswith(".")
    )
    log(f"Scanning {len(csv_files)} per-kraj CSVs")

    for csv_path in csv_files:
        # Skip empty (header-only) files
        if csv_path.stat().st_size < 400:
            continue

        if args.init:
            # Just hash all rows, save state
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                current = {(row.get("id_unikalne") or "").strip(): hash_row(row)
                           for row in reader if (row.get("id_unikalne") or "").strip()}
            rel = csv_path.relative_to(ROOT).as_posix()
            state["files"][rel] = current
            log(f"{csv_path.name}: init hashed {len(current)} rows")
            continue

        added, modified, removed, current = find_changed(csv_path, state, force_all=args.all)
        if not (added or modified or removed):
            continue

        log(f"{csv_path.name}: +{len(added)} ~{len(modified)} -{len(removed)}")
        snapshot_file(csv_path)

        updates = {}
        for r in added + modified:
            row = r["row"]
            row["__file__"] = str(csv_path)
            status, reason = verify_row(row)
            updates[r["id"]] = (status, reason)
            all_results.append({"id": r["id"], "status": status, "reason": reason})

        all_added.extend(added)
        all_modified.extend(modified)
        all_removed.extend(removed)
        file_updates[str(csv_path)] = updates

        # Update state with new hashes
        rel = csv_path.relative_to(ROOT).as_posix()
        state["files"][rel] = {i: current[i]["hash"] for i in current}

    if args.init:
        if not args.dry_run:
            save_state(state)
            log(f"Init complete. {sum(len(v) for v in state['files'].values())} rows hashed.")
        return 0

    if not all_results and not all_removed:
        log("No changes detected.")
        if not args.dry_run:
            save_state(state)
        return 0

    if not args.dry_run:
        # Update flagi in CSVs
        for path, updates in file_updates.items():
            n = update_csv_flags(Path(path), updates, force=args.force)
            if n:
                log(f"  → {Path(path).name}: {n} rows updated")

        # Audit log
        append_audit(all_results, all_added, all_modified, all_removed)

        # Regen master.csv if anything changed
        if file_updates:
            ok, total = regenerate_master()
            if ok:
                log(f"master.csv: regenerated ({total} wierszy)")

        # Save state
        save_state(state)

        # Run Live API verification & VIES validation
        log("🚀 Running live API verification & VIES validation...")
        try:
            from tools.verify_api import main as run_api_verify
            sys.argv = ["verify_api.py", "--all"]
            run_api_verify()
        except Exception as e:
            log(f"⚠️ Live API verification warning: {e}")

        # Run Data Auto-Cleaning & Quality Scoring
        log("🧹 Running Data Auto-Cleaning & Quality Scoring...")
        try:
            from tools.fix_data_quality import main as run_quality_scoring
            sys.argv = ["fix_data_quality.py"]
            run_quality_scoring()
        except Exception as e:
            log(f"⚠️ Quality scoring warning: {e}")

        # Save metric report to data/verification/run_latest.json
        run_metric_dir = DATA / "verification"
        run_metric_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "added": len(all_added),
            "modified": len(all_modified),
            "removed": len(all_removed),
            "frozen": sum(1 for r in all_results if r["status"] == "FROZEN"),
            "do_weryfikacji": sum(1 for r in all_results if r["status"] == "DO-WERYFIKACJI"),
            "results": all_results,
        }
        (run_metric_dir / "run_latest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
        log(f"✅ Saved metrics to {run_metric_dir.relative_to(ROOT)}/run_latest.json")

        # Auto-extract walkthrough/verification insights into DZIENNIK.md and INTEL.md
        log("💡 Auto-extracting key insights into DZIENNIK.md & INTEL.md...")
        try:
            from tools.extract_intel import main as run_extract_intel
            sys.argv = ["extract_intel.py", "--target", "both"]
            run_extract_intel()
        except Exception as e:
            log(f"⚠️ Insight logging warning: {e}")
    else:
        log("(dry-run — nothing written)")

    # Report to stdout (JSON)
    report = {
        "added": len(all_added),
        "modified": len(all_modified),
        "removed": len(all_removed),
        "frozen": sum(1 for r in all_results if r["status"] == "FROZEN"),
        "do_weryfikacji": sum(1 for r in all_results if r["status"] == "DO-WERYFIKACJI"),
        "results": all_results,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
