"""
test_csv_backfill.py — Tests for tools/csv_backfill.py.

Covers the shared back-fill helper used by all 3 enrichment types in
verify_api.py (EE, LT, Apollo). Replaces 3 near-identical 60-line
apply_*_enrichments() functions with one general-purpose helper.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from tools import csv_backfill


class TestBackfillPlaceholderCells:
    """backfill_placeholder_cells() writes only into placeholder cells."""

    def _write_csv(self, tmp_path: Path, rows: list[dict]) -> Path:
        csv_path = tmp_path / "test.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "nip_vat", "telefon", "linkedin"])
            writer.writeheader()
            writer.writerows(rows)
        return csv_path

    def test_empty_enrichments_is_noop(self, tmp_path):
        csv_path = self._write_csv(tmp_path, [{"id": "PL-1", "nip_vat": "", "telefon": ""}])
        n = csv_backfill.backfill_placeholder_cells(
            csv_path, {}, field_map={"nip_vat": "nip_vat"}
        )
        assert n == 0

    def test_writes_into_placeholder_cells(self, tmp_path):
        csv_path = self._write_csv(tmp_path, [{"id": "PL-1", "nip_vat": "do weryfikacji", "telefon": ""}])
        n = csv_backfill.backfill_placeholder_cells(
            csv_path, {"PL-1": {"nip_vat": "5140361901"}},
            field_map={"nip_vat": "nip_vat"},
        )
        assert n == 1
        with open(csv_path, encoding="utf-8") as f:
            row = next(csv.DictReader(f))
        assert row["nip_vat"] == "5140361901"

    def test_does_not_overwrite_real_values(self, tmp_path):
        csv_path = self._write_csv(tmp_path, [{"id": "PL-1", "nip_vat": "5140361901"}])
        n = csv_backfill.backfill_placeholder_cells(
            csv_path, {"PL-1": {"nip_vat": "9999999999"}},
            field_map={"nip_vat": "nip_vat"},
        )
        assert n == 0
        with open(csv_path, encoding="utf-8") as f:
            row = next(csv.DictReader(f))
        assert row["nip_vat"] == "5140361901"

    def test_skips_rows_not_in_enrichments(self, tmp_path):
        csv_path = self._write_csv(tmp_path, [
            {"id": "PL-1", "nip_vat": "do weryfikacji"},
            {"id": "PL-2", "nip_vat": "do weryfikacji"},
        ])
        n = csv_backfill.backfill_placeholder_cells(
            csv_path, {"PL-1": {"nip_vat": "5140361901"}},
            field_map={"nip_vat": "nip_vat"},
        )
        assert n == 1

    def test_atomic_write_no_leftover_tmp(self, tmp_path):
        # If the write succeeds, no .tmp file should remain on disk.
        csv_path = self._write_csv(tmp_path, [{"id": "PL-1", "nip_vat": ""}])
        csv_backfill.backfill_placeholder_cells(
            csv_path, {"PL-1": {"nip_vat": "5140361901"}},
            field_map={"nip_vat": "nip_vat"},
        )
        tmp = csv_path.with_suffix(csv_path.suffix + ".tmp")
        assert not tmp.exists()

    def test_unknown_field_in_field_map_is_skipped(self, tmp_path):
        # If a field in field_map doesn't exist in the CSV header,
        # skip silently — matches existing apply_*_enrichments behavior.
        csv_path = self._write_csv(tmp_path, [{"id": "PL-1", "nip_vat": ""}])
        n = csv_backfill.backfill_placeholder_cells(
            csv_path, {"PL-1": {"does_not_exist": "x"}},
            field_map={"does_not_exist": "does_not_exist"},
        )
        assert n == 0

    def test_custom_placeholders(self, tmp_path):
        # Default placeholders are the BILLSzuka sentinels, but the
        # function accepts a custom set for callers that need different ones.
        csv_path = self._write_csv(tmp_path, [{"id": "PL-1", "nip_vat": "TODO"}])
        n = csv_backfill.backfill_placeholder_cells(
            csv_path, {"PL-1": {"nip_vat": "5140361901"}},
            field_map={"nip_vat": "nip_vat"},
            placeholders={"todo"},
        )
        assert n == 1
        with open(csv_path, encoding="utf-8") as f:
            row = next(csv.DictReader(f))
        assert row["nip_vat"] == "5140361901"
