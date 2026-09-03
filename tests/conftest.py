"""
conftest.py — Test setup for BILLSzuka tools.

Adds the `tools/` directory to sys.path so tests can `import verify_api`,
`import verify_lead`, `import extract_intel` directly. Also exposes a
few fixtures used across test files.

Why not a package? The `tools/` scripts are intentionally runnable
standalone (`python3 tools/verify_api.py`) and live in a flat layout.
We don't want to force a package structure just to support tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `import verify_api`, etc. work
TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

# Repo root for any tests that need to read data/
ROOT = Path(__file__).resolve().parent.parent
# Also on sys.path so `import tools` resolves as a namespace package
# (the tools/ scripts are flat files, no __init__.py).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Every test gets a throwaway SQLite store — never data/billszuka.db."""
    import db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "billszuka-test.db")
