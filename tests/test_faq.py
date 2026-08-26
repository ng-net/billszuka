"""Tests for tools/faq.py — normalization, facts, matching, save-command."""
from __future__ import annotations

from pathlib import Path

import faq

FIXTURE = Path(__file__).parent / "fixtures" / "master_fixture.csv"


def _facts():
    return faq.compute_facts(FIXTURE)


def test_normalize_strips_diacritics_and_punctuation():
    assert faq.normalize("Ile firm jest FROZEN w PL?") == "ile firm jest frozen w pl"
    assert faq.normalize("  Zachowaj   to ZDANIE!  ") == "zachowaj to zdanie"
    assert faq.normalize("Łódź—do-weryfikacji") == "lodz do weryfikacji"


def test_tokenize():
    assert faq.tokenize("Ile firm w PL?") == ["ile", "firm", "w", "pl"]


def test_compute_facts_counts():
    facts = _facts()
    assert facts["rows"] == 6
    assert facts["columns"]["kraj"] == {"PL": 3, "CZ": 2, "DE": 1}
    assert facts["columns"]["tier"]["hurtownik"] == 4
    assert facts["flags"]["frozen"] == 3
    assert facts["flags"]["do-weryfikacji"] == 1
    assert facts["flags_x_kraj"]["frozen|PL"] == 2
    assert facts["flags_x_kraj"]["frozen|CZ"] == 1


def test_facts_hash_is_stable_and_sensitive():
    a = faq.facts_hash(_facts())
    b = faq.facts_hash(_facts())
    assert a == b                       # stable for identical input
    assert faq.facts_hash({"rows": 1}) != a


def test_facts_hash_ignores_touch_not_change(tmp_path):
    import shutil, time
    shutil.copy(FIXTURE, tmp_path / "m.csv")
    path = tmp_path / "m.csv"
    h1 = faq.facts_hash(faq.compute_facts(path))
    time.sleep(0.01)
    path.touch()                        # mtime changes, bytes don't
    h2 = faq.facts_hash(faq.compute_facts(path))
    assert h1 == h2
