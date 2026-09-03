"""
tools/csv_backfill.py — Shared CSV back-fill helper.

Used by all 3 enrichment types in verify_api.py (EE, LT, Apollo).
Replaces 3 near-identical 60-line apply_*_enrichments() functions with
one general-purpose helper. Each enrichment type just provides a
field_map; the placeholders-set and atomic-write pattern are shared.

Public API:
    backfill_placeholder_cells(csv_path, enrichments, field_map, placeholders=None) -> int
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

# Default placeholder set. Matches the 3 original apply_*_enrichments()
# functions exactly — do not change without auditing all callers.
DEFAULT_PLACEHOLDERS = {
    "", "brak", "brak danych", "do weryfikacji", "do ustalenia", "n/a", "—",
}


def backfill_placeholder_cells(
    csv_path: Path,
    enrichments: dict[str, dict],
    field_map: dict[str, str],
    placeholders: set[str] | None = None,
) -> int:
    """Back-fill placeholder cells in a BILLSzuka catalog CSV.

    Args:
        csv_path: Path to the catalog CSV (must have an "id" column).
        enrichments: id → dict-of-field-values. Only fields in `field_map`
            are written.
        field_map: dict mapping CSV-column-name → enrichment-dict-key.
            Example: {"nip_vat": "nip_vat", "rejestr_id": "rejestr_id"}.
        placeholders: Set of lowercase strings considered "empty" cells.
            Defaults to DEFAULT_PLACEHOLDERS.

    Returns:
        Count of cells written. Cells are only written when:
          - the enrichment has a non-empty value for that field, AND
          - the current cell is in the placeholders set (case-insensitive)

    Write is atomic: writes to `<csv_path>.tmp` then `os.replace()`.
    Never leaves a partial CSV if the process is killed mid-write.
    """
    if not enrichments:
        return 0
    if placeholders is None:
        placeholders = DEFAULT_PLACEHOLDERS
    placeholders = {p.lower() for p in placeholders}

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    n_cols = len(header)
    if "id" not in header:
        return 0

    id_idx = header.index("id")
    field_idxs = {col: header.index(col) for col in field_map if col in header}

    n = 0
    for row in rows:
        if len(row) == 0:
            continue
        if len(row) < n_cols:
            row += [""] * (n_cols - len(row))
        id_ = row[id_idx]
        if id_ not in enrichments:
            continue
        data = enrichments[id_]
        for col, key in field_map.items():
            if key not in field_idxs:
                continue
            idx = field_idxs[key]
            current = (row[idx] or "").strip()
            new = data.get(key, "")
            if new and current.lower() in placeholders:
                row[idx] = new
                n += 1

    tmp_path = csv_path.with_suffix(csv_path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        os.replace(tmp_path, csv_path)
    except OSError:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise
    return n
