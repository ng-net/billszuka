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
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STATE_DIR = DATA / ".verify-state"
SNAPSHOT_DIR = DATA / ".snapshots"
STATE_FILE = STATE_DIR / "row-hashes.json"
AUDIT_LOG = DATA / "audit-log.md"
MASTER_CSV = DATA / "master.csv"

# Make `from tools.X import ...` work when this script is run directly
# (i.e. `python3 tools/verify_run.py`). Without this, Python doesn't see
# `tools` as a package because the script lives inside it. The try/except
# blocks below would silently catch ImportError and the cron would log
# "No module named 'tools'" while doing nothing — see git log for the
# incident on 2026-08-10.
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from config import CANONICAL_SCHEMA, COUNTRY_MAP, COUNTRY_ORDER as CONF_COUNTRY_ORDER

COUNTRY_ORDER: list[str] = [COUNTRY_MAP[iso] for iso in CONF_COUNTRY_ORDER]

def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def hash_row(row: dict) -> str:
    """Stable hash of a row, excluding verification metadata columns."""
    h = hashlib.sha256()
    skip = {"flagi", "data_weryfikacji", "www_status", None, ""}
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


def prune_old_snapshots(max_age_days: int = 7) -> int:
    """Delete snapshot CSVs older than max_age_days. Catches files with weird
    names (e.g. multi-timestamped) that the per-basename prune misses.

    Returns count of files deleted.
    """
    if not SNAPSHOT_DIR.exists():
        return 0
    cutoff = time.time() - (max_age_days * 86400)
    deleted = 0
    for f in SNAPSHOT_DIR.glob("*.csv"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                deleted += 1
        except OSError:
            pass
    return deleted


def find_changed(csv_path: Path, state: dict, force_all: bool):
    """Returns (added, modified, removed, current) for one CSV vs state."""
    rel = csv_path.relative_to(ROOT).as_posix()
    prev = state["files"].get(rel, {})
    prev_ids = set(prev.keys())

    current: dict[str, dict] = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_ = (row.get("id") or "").strip()
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

    if "id" not in header or "flagi" not in header:
        return 0

    id_idx = header.index("id")
    flagi_idx = header.index("flagi")
    n = 0
    skipped_api = 0
    for row in rows:
        if not row or len(row) <= id_idx:
            continue
        id_ = row[id_idx]
        if id_ in updates:
            existing = row[flagi_idx] if len(row) > flagi_idx and row[flagi_idx] else ""
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
            if len(row) > flagi_idx:
                row[flagi_idx] = f"{cleaned.strip()} {marker}".strip()
            n += 1

    tmp_path = csv_path.with_suffix(csv_path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        os.replace(tmp_path, csv_path)
    except OSError as e:
        log(f"  → {csv_path.name}: atomic write failed ({e})")
        if tmp_path.exists():
            try: tmp_path.unlink()
            except OSError: pass
        raise
    if skipped_api:
        log(f"  (skipped {skipped_api} API-verified rows — use --force to override)")
    return n


def regenerate_master() -> tuple[bool, int]:
    """Re-export of pipeline.regenerate_master_csv() for backward compat.

    tools/api_server.py:65 imports this function. The implementation
    moved to tools/pipeline.py in the 2026-09-03 seam extraction.
    """
    from tools.pipeline import regenerate_master_csv
    return regenerate_master_csv(DATA, atomic=True, strict_schema=False)


def append_audit(results, added, modified, removed):
    """Append an audit-log block per verify-data skill format.

    Note: as of the 2026-09-03 verify consolidation, verify_run no longer
    computes FROZEN/DO-W status itself — that's verify_api's job. The
    audit log here records change-detection only; per-row status lives in
    data/verification/run_latest.json (written by verify_api).
    """
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

    lines.append(
        f"\n**Run summary:** {len(added)} added, {len(modified)} modified, "
        f"{len(removed)} removed — see verify_api output for FROZEN/DO-W breakdown"
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

    # Housekeeping: prune stale snapshots (mtime-based, catches weird names
    # that the per-basename prune in snapshot_file() misses).
    pruned = prune_old_snapshots(max_age_days=7)
    if pruned:
        log(f"Pruned {pruned} stale snapshot(s) older than 7 days")

    state = load_state()
    all_results = []
    all_added, all_modified, all_removed = [], [], []

    # Skip dotfile dirs (.snapshots, .verify-state, .intake) and
    # data-housekeeping dirs (backups, verification). Without this filter,
    # the glob matches thousands of snapshot files (e.g.
    # data/.snapshots/<subdir>/catalog-*.csv) and burns hours hashing them.
    # See git log: 2026-08-10 cron hit 10k+ files before being killed.
    SKIP_PATH_PARTS = (".snapshots", ".verify-state", ".intake", "backups", "verification")
    # Match only canonical `catalog-A-CC.csv` / `catalog-B-CC.csv` (CC = 2-letter
    # ISO country code). Excludes pre-clean backups (catalog-A-PL-pre-clean-*.csv),
    # Apollo cache dumps, or any other derivative filename that may sit alongside
    # the canonical file. Without this filter the glob catches every derivative
    # name and treats it as a "new file" on first scan, inflating the run summary.
    _CANONICAL_RE = re.compile(r"^catalog-[AB]-[A-Z]{2}\.csv$")
    csv_files = sorted(
        p for p in DATA.glob("*/catalog-*.csv")
        if p.is_file()
        and not any(part in SKIP_PATH_PARTS for part in p.relative_to(DATA).parts)
        and _CANONICAL_RE.match(p.name)
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
                current = {(row.get("id") or "").strip(): hash_row(row)
                           for row in reader if (row.get("id") or "").strip()}
            rel = csv_path.relative_to(ROOT).as_posix()
            state["files"][rel] = current
            log(f"{csv_path.name}: init hashed {len(current)} rows")
            continue

        added, modified, removed, current = find_changed(csv_path, state, force_all=args.all)
        if not (added or modified or removed):
            continue

        log(f"{csv_path.name}: +{len(added)} ~{len(modified)} -{len(removed)}")
        snapshot_file(csv_path)

        # We don't compute verification status here — verify_api.main() is
        # the single source of truth for FROZEN/DO-WERYFIKACJI assignments
        # (it has the live CEIDG/ARES/VIES/etc. calls). This loop just
        # records the diff for the audit log and state file.
        for r in added + modified:
            r["row"]["__file__"] = str(csv_path)
            all_results.append({
                "id": r["id"],
                "status": "PENDING_API",  # placeholder; verify_api will overwrite
                "reason": "see verify_api output",
            })

        all_added.extend(added)
        all_modified.extend(modified)
        all_removed.extend(removed)

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
        # Audit log (FROZEN/DO-W counts will be filled by verify_api's own metric file)
        append_audit(all_results, all_added, all_modified, all_removed)

        # Regen master.csv if anything changed
        if all_added or all_modified or all_removed:
            ok, total = regenerate_master()
            if ok:
                log(f"master.csv: regenerated ({total} wierszy)")

        # Save state
        save_state(state)

        # Run Live API verification & VIES validation.
        # verify_api.main() is the single source of truth for FROZEN/DO-W
        # status assignments — it owns the live CEIDG/ARES/VIES/etc. calls
        # and writes the authoritative flagi column.
        log("🚀 Running live API verification & VIES validation...")
        try:
            from tools.verify_api import main as run_api_verify
        except ImportError as e:
            log(f"❌ Live API verification skipped (import error): {e}")
        else:
            try:
                sys.argv = ["verify_api.py", "--all"]
                run_api_verify()
            except Exception as e:
                log(f"⚠️ Live API verification warning: {e}")

        # Save metric report to data/verification/run_latest.json.
        # Real FROZEN/DO-W counts come from verify_api's own output; we
        # record our own change detection here.
        run_metric_dir = DATA / "verification"
        run_metric_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "added": len(all_added),
            "modified": len(all_modified),
            "removed": len(all_removed),
            "results": all_results,
            "note": "FROZEN/DO-W counts are populated by verify_api — see its output above",
        }
        (run_metric_dir / "run_latest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
        log(f"✅ Saved metrics to {run_metric_dir.relative_to(ROOT)}/run_latest.json")

        # Auto-extract walkthrough/verification insights into DZIENNIK.md and INTEL.md
        log("💡 Auto-extracting key insights into DZIENNIK.md & INTEL.md...")
        try:
            from tools.extract_intel import main as run_extract_intel
        except ImportError as e:
            log(f"❌ Insight logging skipped (import error): {e}")
        else:
            try:
                sys.argv = ["extract_intel.py", "--target", "both"]
                run_extract_intel()
            except Exception as e:
                log(f"⚠️ Insight logging warning: {e}")
    else:
        log("(dry-run — nothing written)")

    # Report to stdout (JSON). FROZEN/DO-W counts are filled by verify_api
    # downstream — verify_run only knows about changes, not statuses.
    report = {
        "added": len(all_added),
        "modified": len(all_modified),
        "removed": len(all_removed),
        "results": all_results,
        "note": "FROZEN/DO-W counts are populated by verify_api — see its output above",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
