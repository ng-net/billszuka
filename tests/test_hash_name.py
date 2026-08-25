"""Tests for tools/hash_name.py — hashes must match the frontend gate."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from hash_name import hash_value, normalize


def test_normalize_trims_and_lowercases():
    assert normalize("  Jarek  ") == "jarek"
    assert normalize("BILLS") == "bills"
    assert normalize("BiLLs") == "bills"


def test_hash_is_sha256_hex_of_normalized_value():
    assert hash_value(" Jarek ") == hashlib.sha256(b"jarek").hexdigest()
    assert len(hash_value("karol")) == 64


def test_distinct_variants_produce_distinct_hashes():
    assert hash_value("jarosław") != hash_value("jaroslaw")


def test_main_prints_hash(capsys):
    import sys as _sys
    _sys.argv = ["hash_name.py", "karol"]
    from hash_name import main
    assert main() == 0
    assert capsys.readouterr().out.strip() == hashlib.sha256(b"karol").hexdigest()
