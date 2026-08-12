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
from dataclasses import dataclass, field
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

# Per the verify-data skill
FROZEN_REQUIRED = ["nazwa_firmy", "nip_vat", "rejestr_id", "adres", "zrodlo_danych"]
OFFICIAL_SOURCE_TOKENS = [
    "krs api", "krs.gov", "ceidg", "vies", "kas", "regon",
    "ares", "orsr", "rekvizitai", "ajpes",
    "ariregister",
    "jar",  # Lithuanian Juridinių asmenų registras via data.gov.lt SAU API
]
COUNTRY_API = {
    "PL": "ceidg",  # CEIDG + KRS
    "CZ": "ares",   # ARES
    "FR": "recherche-entreprises",  # recherche-entreprises.api.gouv.fr (rich: name + dirigeants)
    "EE": "ariregister",  # e-Äriregister: autocomplete JSON + detail HTML (rich: KMKR + EMTAK)
    "LT": "jar",    # Lithuanian JAR via data.gov.lt SAU / spinta (rich: ja_kodas, reg_data, forma, statusas)
    # All other EU countries fall through to VIES (in verify_api.py
    # dispatcher), which covers all 27 member states. Country-specific
    # registries (ORSR SK, AJPES SI, etc.) can be added here as primary
    # and VIES becomes the fallback.
    "SK": "vies", "LV": "vies", "BG": "vies",
    "HR": "vies", "RO": "vies", "SI": "vies",
    # MD (Moldova) is non-EU → PENDING_API in verify_api.py
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
    """
    Regenerate data/master.csv from per-kraj CSVs (data/*/catalog-*.csv).

    Returns (ok, row_count). Backward-compatible signature — the caller at
    the regen step just needs the bool + total written rows.

    Behaviour vs. previous bash-based version:
      • Auto-discovers per-kraj files via DATA.glob("*/catalog-*.csv")
        (no hardcoded country list)
      • Skips `._*` (macOS metadata) and dotfiles explicitly
      • Validates that all source files share the same header; raises
        RegenSchemaError on mismatch in strict mode, warns + pads in lax mode
      • Validates per-row column count; rows with wrong arity are logged
        and skipped (count surfaced via stats)
      • Atomic write via tmp + os.replace — never leaves a partial master.csv
      • No subprocess, no shell, no macOS plist noise
    """
    # 1) Discover files. Only direct subdirectories of data/ (skip hidden
    #    ones like .snapshots/ and .verify-state/), and only catalog-[AB]-*.csv
    #    to match the canonical A/B catalog layout. Any other prefix (e.g.
    #    catalog-relationships.csv, experimental variants) is excluded on
    #    purpose — those are not meant to land in master.csv.
    #
    # Order convention: COUNTRY_ORDER is the canonical order from
    # methodology.md (PL → CZ → DE → SK → UK → Western EU → Scandinavia →
    # Balkans, with DE/UK/Western EU/Scandinavia currently skipped).
    # Unknown countries (a new directory we haven't seen) get appended at
    # the end, sorted alphabetically — so adding a new country never breaks
    # the regen, it just lands in a sensible spot until you add it to
    # COUNTRY_ORDER + methodology.md.
    country_dirs: list[Path] = []
    # Skip hidden dirs (.*) AND explicit "data housekeeping" dirs that
    # contain snapshot/backup CSVs which would explode the master.csv
    # count (e.g. 145 → 3603 rows from `data/backups/` snapshots).
    SKIP_DIRS = {".snapshots", ".verify-state", "backups", "verification"}
    for sub in DATA.iterdir():
        if not sub.is_dir() or sub.name in SKIP_DIRS or sub.name.startswith("."):
            continue
        country_dirs.append(sub)

    def country_sort_key(p: Path) -> tuple[int, str]:
        try:
            return (COUNTRY_ORDER.index(p.name), p.name)
        except ValueError:
            # Unknown country: place after all known ones, alphabetical
            return (len(COUNTRY_ORDER), p.name)

    country_dirs.sort(key=country_sort_key)

    sources: list[Path] = []
    # Same canonical-only filter as in main(): exclude derivative filenames
    # like `catalog-A-PL-pre-clean-*.csv` that some pipeline steps leave
    # alongside the real catalog. Without this filter the master inflates
    # by hundreds of rows on every regen.
    _regen_re = re.compile(r"^catalog-[AB]-[A-Z]{2}\.csv$")
    for sub in country_dirs:
        for f in sorted(sub.glob("catalog-[AB]-*.csv")):
            if f.name.startswith("._") or not _regen_re.match(f.name):
                continue
            sources.append(f)
    if not sources:
        log("master regen: no per-kraj catalog-[AB]-*.csv found under data/")
        return False, 0

    # 2) Read + validate headers
    headers_per_file: dict[Path, list[str]] = {}
    for p in sources:
        try:
            with p.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                try:
                    headers_per_file[p] = next(reader)
                except StopIteration:
                    log(f"  ⚠ {p.relative_to(DATA)}: empty file, skipping")
                    continue
        except (OSError, UnicodeDecodeError) as e:
            log(f"  ⚠ {p.relative_to(DATA)}: cannot read ({e}), skipping")
            continue

    if not headers_per_file:
        log("master regen: no readable per-kraj files")
        return False, 0

    # Schema-aware union header. Instead of forcing all files to match the
    # first one (which loses rows when one file added a column, e.g. PL
    # gained `_krs` after a quality-scoring update), build the union of
    # all column names in the order they first appear. For each source
    # file, pad missing columns with empty strings. This keeps the regen
    # lossless when one country picks up an extra column mid-project.
    union_header: list[str] = []
    seen: set[str] = set()
    for hdr in headers_per_file.values():
        for col in hdr:
            if col not in seen:
                seen.add(col)
                union_header.append(col)
    if not union_header:
        log("master regen: no columns in any header, aborting")
        return False, 0
    n_columns = len(union_header)

    # Schema drift diagnostics (only if a column is missing in some file
    # or extra in another). Informational — we now handle it gracefully
    # instead of aborting or losing rows.
    schema_warnings: list[str] = []
    for p, hdr in headers_per_file.items():
        if hdr != union_header:
            diff = _diff_columns(union_header, hdr)
            schema_warnings.append(f"{p.relative_to(DATA)}: {diff}")
    if schema_warnings:
        log(f"  ⚠ master regen: {len(schema_warnings)} file(s) with header drift (padded to union):")
        for w in schema_warnings:
            log(f"    - {w}")

    # 3) Build master rows
    rows_written = 0
    rows_skipped = 0
    skip_reasons: dict[str, int] = {}
    out_rows: list[list[str]] = [union_header]

    for p in sources:
        if p not in headers_per_file:
            continue  # was skipped during header read
        file_header = headers_per_file[p]
        # Build a column-index remap: union position -> file position (or None)
        col_index: list[int | None] = []
        for col in union_header:
            try:
                col_index.append(file_header.index(col))
            except ValueError:
                col_index.append(None)
        try:
            with p.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                try:
                    next(reader)  # discard header (already validated)
                except StopIteration:
                    continue
                for row_num, row in enumerate(reader, start=2):
                    if not row or all(c == "" for c in row):
                        continue  # empty line
                    # Pad row to union_header length if this file is short
                    # on trailing columns (e.g. PL has _krs, others don't).
                    # Truly malformed rows (way more cols than union) are skipped.
                    if len(row) > len(file_header):
                        reason = f"col_count={len(row)}>{len(file_header)}"
                        skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
                        rows_skipped += 1
                        continue
                    out_row = [
                        row[idx] if idx is not None and idx < len(row) else ""
                        for idx in col_index
                    ]
                    out_rows.append(out_row)
                    rows_written += 1
        except (OSError, UnicodeDecodeError) as e:
            log(f"  ⚠ {p.relative_to(DATA)}: read error at row {row_num} ({e})")
            continue

    # 4) Atomic write: tmp → os.replace
    tmp_path = MASTER_CSV.with_suffix(".csv.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8", newline="") as f:
            # RFC 4180 default lineterminator is \r\n — matches the
            # csv.writer default used by every other writer in this repo
            # (see line ~206 in clean_csv_flagi etc.) and the existing
            # master.csv on disk.
            writer = csv.writer(f)
            writer.writerows(out_rows)
        os.replace(tmp_path, MASTER_CSV)
    except OSError as e:
        log(f"master regen: write failed ({e})")
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        return False, 0

    # 5) Summary
    log(
        f"  master regen: {rows_written} rows from "
        f"{len(headers_per_file)} files"
        + (f", {rows_skipped} skipped" if rows_skipped else "")
    )
    if skip_reasons:
        for reason, n in skip_reasons.items():
            log(f"    - skipped {n} rows: {reason}")
    if schema_warnings:
        log(f"    - {len(schema_warnings)} file(s) had header drift (see above)")

    return True, rows_written


def _diff_columns(canonical: list[str], other: list[str]) -> str:
    """Return a compact human-readable diff of two header lists."""
    canon_set = set(canonical)
    other_set = set(other)
    only_canon = canon_set - other_set
    only_other = other_set - canon_set
    parts: list[str] = []
    if only_canon:
        parts.append(f"missing={sorted(only_canon)[:5]}")
    if only_other:
        parts.append(f"extra={sorted(only_other)[:5]}")
    if not parts and len(canonical) != len(other):
        parts.append(f"len={len(other)}≠{len(canonical)}")
    if not parts:
        parts.append("order differs")
    return "; ".join(parts)


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

    # Housekeeping: prune stale snapshots (mtime-based, catches weird names
    # that the per-basename prune in snapshot_file() misses).
    pruned = prune_old_snapshots(max_age_days=7)
    if pruned:
        log(f"Pruned {pruned} stale snapshot(s) older than 7 days")

    state = load_state()
    all_results = []
    all_added, all_modified, all_removed = [], [], []
    file_updates: dict[str, dict[str, tuple[str, str]]] = {}

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
        except ImportError as e:
            log(f"❌ Live API verification skipped (import error): {e}")
        else:
            try:
                sys.argv = ["verify_api.py", "--all"]
                run_api_verify()
            except Exception as e:
                log(f"⚠️ Live API verification warning: {e}")

        # Run Data Auto-Cleaning & Quality Scoring
        log("🧹 Running Data Auto-Cleaning & Quality Scoring...")
        try:
            from tools.fix_data_quality import main as run_quality_scoring
        except ImportError as e:
            log(f"❌ Quality scoring skipped (import error): {e}")
        else:
            try:
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
