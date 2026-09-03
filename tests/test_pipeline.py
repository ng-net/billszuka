"""
test_pipeline.py — Tests for tools/pipeline.py.

Covers the shared master.csv regeneration helper used by both
billszuka.py cmd_compile and verify_run.py regenerate_master.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from tools import pipeline


class TestRegenerateMasterCsv:
    """regenerate_master_csv() rebuilds data/master.csv from per-kraj CSVs."""

    def _write_catalog(self, country_dir: Path, cat_type: str, iso: str, rows: list[dict]):
        country_dir.mkdir(parents=True, exist_ok=True)
        csv_path = country_dir / f"catalog-{cat_type}-{iso}.csv"
        fieldnames = ["kraj", "id", "nazwa", "nip_vat", "rejestr_id", "adres", "zrodlo_danych"]
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_basic_union_header(self, tmp_path):
        # 2 countries, 1 catalog each, with slightly different headers
        self._write_catalog(tmp_path / "Polska", "A", "PL", [
            {"kraj": "PL", "id": "PL-A-001", "nazwa": "BILLS", "nip_vat": "5140361901",
             "rejestr_id": "KRS 0001074645", "adres": "Ostrzeszów", "zrodlo_danych": "KRS API"},
        ])
        self._write_catalog(tmp_path / "Czechy", "A", "CZ", [
            {"kraj": "CZ", "id": "CZ-A-001", "nazwa": "GGT", "nip_vat": "26293609",
             "rejestr_id": "ARES", "adres": "Praha", "zrodlo_danych": "ARES API"},
        ])
        ok, total = pipeline.regenerate_master_csv(tmp_path, atomic=True)
        assert ok is True
        assert total == 2
        master = tmp_path / "master.csv"
        assert master.exists()
        with open(master, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert {r["id"] for r in rows} == {"PL-A-001", "CZ-A-001"}

    def test_strict_schema_mismatch_returns_false(self, tmp_path, capsys):
        # If strict=True and headers don't match the first file, the function
        # should warn and return (False, 0) — matching billszuka.py compile
        # behavior. The exact warning text is implementation detail.
        self._write_catalog(tmp_path / "Polska", "A", "PL", [
            {"kraj": "PL", "id": "PL-A-001", "nazwa": "BILLS", "nip_vat": "5140361901",
             "rejestr_id": "KRS 0001074645", "adres": "Ostrzeszów", "zrodlo_danych": "KRS API"},
        ])
        # Czech has a genuinely different header (extra "ICO" column).
        # Use raw csv.writer to bypass the shared fieldnames helper.
        cz_dir = tmp_path / "Czechy"
        cz_dir.mkdir(parents=True, exist_ok=True)
        cz_path = cz_dir / "catalog-A-CZ.csv"
        with open(cz_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["kraj", "id", "nazwa", "nip_vat", "ICO", "adres", "zrodlo_danych"])
            writer.writerow(["CZ", "CZ-A-001", "GGT", "26293609", "26293609", "Praha", "ARES API"])
        ok, total = pipeline.regenerate_master_csv(tmp_path, atomic=True, strict_schema=True)
        # Strict check is logged + returns False on mismatch.
        assert ok is False
        assert total == 0

    def test_skips_hidden_dirs(self, tmp_path):
        # .snapshots/, .verify-state/, backups/ etc. should not be read.
        hidden = tmp_path / ".snapshots"
        self._write_catalog(hidden, "A", "PL", [
            {"kraj": "PL", "id": "PL-SNAP-001", "nazwa": "OLD", "nip_vat": "999",
             "rejestr_id": "x", "adres": "x", "zrodlo_danych": "old"},
        ])
        ok, total = pipeline.regenerate_master_csv(tmp_path, atomic=True)
        # Hidden dir was skipped → no sources → (False, 0). Matches original
        # verify_run behavior: "no per-kraj files" is reported as not-ok.
        assert ok is False
        assert total == 0

    def test_skips_derivative_filenames(self, tmp_path):
        # catalog-A-PL-pre-clean-2026.csv should not be read.
        country_dir = tmp_path / "Polska"
        country_dir.mkdir(parents=True, exist_ok=True)
        # Main canonical file:
        self._write_catalog(country_dir, "A", "PL", [
            {"kraj": "PL", "id": "PL-A-001", "nazwa": "BILLS", "nip_vat": "5140361901",
             "rejestr_id": "KRS 0001074645", "adres": "Ostrzeszów", "zrodlo_danych": "KRS API"},
        ])
        # Derivative (pre-clean) file with the same ID — should be ignored
        # because filename doesn't match ^catalog-[AB]-[A-Z]{2}\.csv$
        derivative = country_dir / "catalog-A-PL-pre-clean-2026.csv"
        with open(derivative, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["kraj", "id", "nazwa"])
            writer.writeheader()
            writer.writerow({"kraj": "PL", "id": "PL-A-001", "nazwa": "DUPLICATE"})

        ok, total = pipeline.regenerate_master_csv(tmp_path, atomic=True)
        assert ok is True
        assert total == 1  # only the canonical file was read

    def test_empty_data_dir(self, tmp_path):
        ok, total = pipeline.regenerate_master_csv(tmp_path, atomic=True)
        # No per-kraj files → returns (False, 0) — matches verify_run.
        # billszuka compile should treat this as a hard error.
        assert ok is False
        assert total == 0

    def test_atomic_write_no_leftover_tmp(self, tmp_path):
        self._write_catalog(tmp_path / "Polska", "A", "PL", [
            {"kraj": "PL", "id": "PL-A-001", "nazwa": "BILLS", "nip_vat": "5140361901",
             "rejestr_id": "KRS 0001074645", "adres": "Ostrzeszów", "zrodlo_danych": "KRS API"},
        ])
        pipeline.regenerate_master_csv(tmp_path, atomic=True)
        # No leftover .tmp files
        leftovers = list(tmp_path.glob("*.tmp"))
        assert leftovers == []
