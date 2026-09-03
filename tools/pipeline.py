"""
tools/pipeline.py — Shared CSV pipeline operations.

Public API:
    regenerate_master_csv(data_dir, *, atomic=True, strict_schema=False) -> tuple[bool, int]

Reads per-kraj catalogs from `<data_dir>/<Country>/catalog-[AB]-<ISO>.csv`,
unions their headers (lax mode) or requires strict match (strict mode),
and writes the result to `<data_dir>/master.csv`.

Used by:
    - tools/billszuka.py:cmd_compile (with strict_schema=True)
    - tools/verify_run.py:regenerate_master (default = strict_schema=False)
"""
from __future__ import annotations

import csv
import logging
import os
import re
from pathlib import Path

log = logging.getLogger(__name__)

# Country directories that are housekeeping, not catalogs. Match the
# existing list in verify_run.regenerate_master().
SKIP_DIRS = {".snapshots", ".verify-state", "backups", "verification"}
# Canonical filename pattern. Excludes pre-clean backups, Apollo cache
# dumps, and other derivative names that some pipeline steps leave
# alongside the real catalog.
_CANONICAL_RE = re.compile(r"^catalog-[AB]-[A-Z]{2}\.csv$")


def _discover_sources(data_dir: Path) -> list[Path]:
    """Return per-kraj catalog CSV paths.

    Skips hidden directories, housekeeping dirs, and derivative filenames.
    Country directories are sorted by COUNTRY_ORDER (PL → CZ → SK → ... → RS)
    when available, then alphabetically for unknown countries. Matches the
    order that the old billszuka.cmd_compile produced.
    """
    sources: list[Path] = []
    if not data_dir.is_dir():
        return sources

    # Best-effort import — keep pipeline.py independent of config.py so it
    # can be tested in isolation. If config.py is unavailable we fall back
    # to alphabetical sort.
    try:
        from config import COUNTRY_MAP, COUNTRY_ORDER  # type: ignore
        country_order = [(COUNTRY_MAP[iso], iso) for iso in COUNTRY_ORDER]
    except Exception:
        country_order = []

    country_dirs = [
        sub for sub in data_dir.iterdir()
        if sub.is_dir() and sub.name not in SKIP_DIRS and not sub.name.startswith(".")
    ]

    def sort_key(p: Path) -> tuple[int, str]:
        for i, (dir_name, _) in enumerate(country_order):
            if p.name == dir_name:
                return (i, p.name)
        return (len(country_order), p.name)

    country_dirs.sort(key=sort_key)

    for sub in country_dirs:
        for f in sorted(sub.glob("catalog-[AB]-*.csv")):
            if f.name.startswith("._") or not _CANONICAL_RE.match(f.name):
                continue
            sources.append(f)
    return sources


def _read_headers(sources: list[Path]) -> dict[Path, list[str]]:
    """Read the header row from each source. Skips unreadable files."""
    headers: dict[Path, list[str]] = {}
    for p in sources:
        try:
            with p.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                try:
                    headers[p] = next(reader)
                except StopIteration:
                    log.warning("  ⚠ %s: empty file, skipping", p.name)
                    continue
        except (OSError, UnicodeDecodeError) as e:
            log.warning("  ⚠ %s: cannot read (%s), skipping", p.name, e)
            continue
    return headers


def regenerate_master_csv(
    data_dir: Path,
    *,
    atomic: bool = True,
    strict_schema: bool = False,
) -> tuple[bool, int]:
    """Regenerate `<data_dir>/master.csv` from per-kraj catalog CSVs.

    Args:
        data_dir: Path to the data/ directory containing per-country
            subdirectories with catalog-*.csv files.
        atomic: If True, write to `<data_dir>/master.csv.tmp` then
            `os.replace()` — never leaves a partial master.csv.
        strict_schema: If True, fail (return False) if any source file's
            header doesn't match the first file's header. If False (the
            default), use the union of all headers and pad missing
            columns with empty strings.

    Returns:
        (ok, row_count) tuple.
        - ok=False, row_count=0 if no source files were found or if
          strict_schema=True and a mismatch was detected.
        - ok=True, row_count=N if N rows were written.
    """
    sources = _discover_sources(data_dir)
    if not sources:
        log.info("master regen: no per-kraj catalog-[AB]-*.csv found under %s", data_dir)
        return False, 0

    headers_per_file = _read_headers(sources)
    if not headers_per_file:
        log.info("master regen: no readable per-kraj files in %s", data_dir)
        return False, 0

    if strict_schema:
        first_header = next(iter(headers_per_file.values()))
        for p, hdr in headers_per_file.items():
            if hdr != first_header:
                diff = set(first_header) ^ set(hdr)
                log.warning("  ⚠ %s: schema mismatch (strict mode): diff=%s",
                            p.name, sorted(diff)[:5])
                return False, 0
        union_header = first_header
    else:
        # Union of all column names in the order they first appear.
        # For each source file, pad missing columns with empty strings.
        union_header = []
        seen: set[str] = set()
        for hdr in headers_per_file.values():
            for col in hdr:
                if col not in seen:
                    seen.add(col)
                    union_header.append(col)
        # Schema drift diagnostics (informational only).
        schema_warnings: list[str] = []
        for p, hdr in headers_per_file.items():
            if hdr != union_header:
                diff = set(union_header) ^ set(hdr)
                schema_warnings.append(f"{p.name}: diff={sorted(diff)[:5]}")
        if schema_warnings:
            log.info("  ⚠ master regen: %d file(s) with header drift (padded to union)",
                     len(schema_warnings))
            for w in schema_warnings:
                log.info("    - %s", w)

    out_rows: list[list[str]] = [union_header]
    rows_written = 0
    rows_skipped = 0
    for p, file_header in headers_per_file.items():
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
                    next(reader)  # discard header
                except StopIteration:
                    continue
                for row in reader:
                    if not row or all(c == "" for c in row):
                        continue
                    if len(row) > len(file_header):
                        rows_skipped += 1
                        continue
                    out_row = [
                        row[idx] if idx is not None and idx < len(row) else ""
                        for idx in col_index
                    ]
                    out_rows.append(out_row)
                    rows_written += 1
        except (OSError, UnicodeDecodeError) as e:
            log.warning("  ⚠ %s: read error (%s)", p.name, e)
            continue

    master_path = data_dir / "master.csv"
    if atomic:
        tmp_path = master_path.with_suffix(".csv.tmp")
        try:
            with tmp_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(out_rows)
            os.replace(tmp_path, master_path)
        except OSError as e:
            log.error("master regen: write failed (%s)", e)
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            return False, 0
    else:
        with master_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(out_rows)

    log.info("  master regen: %d rows from %d files%s",
             rows_written, len(headers_per_file),
             f", {rows_skipped} skipped" if rows_skipped else "")
    return True, rows_written
