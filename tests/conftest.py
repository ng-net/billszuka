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

# Make `import verify_api`, `import verify_lead`, etc. work
TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

# Repo root for any tests that need to read data/
ROOT = Path(__file__).resolve().parent.parent
