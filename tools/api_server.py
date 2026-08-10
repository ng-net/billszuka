#!/usr/bin/env python3
"""
api_server.py — FastAPI backend for the BILLSzuka Dashboard frontend.

Wired endpoints (matching frontend/src/App.jsx fetch calls):
  GET  /api/datasets         → list CSV files in data/
  GET  /api/dataset/{name}   → read CSV, return columns + first N rows
  POST /api/upload           → save uploaded CSV to data/
  POST /api/sync             → regenerate master.csv + run verify
  POST /api/chat             → LLM proxy (OpenRouter) or mock fallback

Start:
  python3 tools/api_server.py                 # binds 127.0.0.1:8000
  python3 tools/api_server.py --port 9000
  python3 tools/api_server.py --reload        # dev mode (uvicorn)

The Vite dev server proxies /api/* → http://localhost:8000 (see
frontend/vite.config.js), so the frontend never sees CORS in dev.

All data is read from / written to the project data/ directory — paths
are validated against path traversal (no `..` components allowed in
filenames).
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Sibling modules — same dir
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_run import regenerate_master  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Upload validation
ALLOWED_CSV_SUFFIX = ".csv"
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000
ALLOWED_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")  # no /, no .., no spaces

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BILLSzuka API",
    description="Backend for the BILLSzuka Dashboard Hub frontend.",
    version="0.1.0",
)

# CORS for Vite dev server (and any explicit browser access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models (for request/response shape)
# ---------------------------------------------------------------------------

class SyncRequest(BaseModel):
    source_type: str = "all"  # e.g. "all", "verify", "master"

class SyncResponse(BaseModel):
    ok: bool
    message: str
    master_rows: int | None = None
    verify_summary: dict | None = None

class ChatRequest(BaseModel):
    query: str
    active_dataset: str | None = None

class ChatResponse(BaseModel):
    response: str
    provider: str  # "openrouter" or "mock"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_filename(name: str) -> str:
    """Reject path traversal and weird characters. Returns the clean name."""
    if not name or name.startswith(".") or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="invalid filename")
    if not ALLOWED_FILENAME_RE.match(name):
        raise HTTPException(status_code=400, detail="filename must match [A-Za-z0-9_.-]+")
    if not name.lower().endswith(ALLOWED_CSV_SUFFIX):
        raise HTTPException(status_code=400, detail="only .csv files accepted")
    return name


def _csv_path(filename: str) -> Path:
    """Resolve a validated filename to a path under data/, raise 404 if missing.

    Looks first at the data/ root, then recursively in subdirs (catalogs
    live in data/{Kraj}/catalog-*.csv). This matches how the frontend
    references files: by basename, not by relative path.
    """
    # Try root first (faster, common case for top-level files)
    candidate = (DATA / filename).resolve()
    if not str(candidate).startswith(str(DATA.resolve())):
        raise HTTPException(status_code=400, detail="path traversal blocked")
    if candidate.exists():
        return candidate
    # Fall back to recursive search
    matches = [p for p in DATA.rglob(filename) if p.is_file() and not p.name.startswith("._")]
    if not matches:
        raise HTTPException(status_code=404, detail=f"{filename} not found in data/")
    # If multiple matches (e.g. catalog-A-PL in Polska + a snapshot copy),
    # prefer the one in the most recent country dir, not .snapshots
    real_matches = [m for m in matches if ".snapshots" not in str(m)]
    return (real_matches or matches)[0]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/datasets")
async def list_datasets() -> dict[str, Any]:
    """List all CSV files in data/ (and the derived master.csv at top)."""
    def _scan() -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        # Master first if present (it's the canonical aggregated view)
        master = DATA / "master.csv"
        if master.exists() and master.stat().st_size > 200:
            out.append({
                "filename": "master.csv",
                "size_bytes": master.stat().st_size,
                "kind": "master",
            })
        # Per-country catalogs (the A/B files)
        for sub in sorted(DATA.iterdir()):
            if not sub.is_dir() or sub.name.startswith("."):
                continue
            for csv_file in sorted(sub.glob("catalog-[AB]-*.csv")):
                if csv_file.name.startswith("._"):
                    continue
                out.append({
                    "filename": csv_file.name,
                    "country": sub.name,
                    "size_bytes": csv_file.stat().st_size,
                    "kind": "catalog",
                })
        # Top-level CSVs (e.g. sales_data.csv) — but skip master (already added)
        for f in sorted(DATA.glob("*.csv")):
            if f.name == "master.csv" or f.name.startswith("."):
                continue
            out.append({
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "kind": "standalone",
            })
        return out

    datasets = await asyncio.to_thread(_scan)
    return {"datasets": datasets, "count": len(datasets)}


@app.get("/api/dataset/{filename}")
async def get_dataset(filename: str, limit: int = DEFAULT_PAGE_SIZE) -> dict[str, Any]:
    """Read a CSV and return its columns + first `limit` rows as JSON."""
    if limit < 1 or limit > MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"limit must be 1..{MAX_PAGE_SIZE}")
    clean = _validate_filename(filename)
    path = _csv_path(clean)

    def _read() -> dict[str, Any]:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                return {"columns": [], "data": [], "total_rows": 0}
            rows: list[list[str]] = []
            for row in reader:
                if not row or all(c == "" for c in row):
                    continue
                # Pad short rows to header length
                if len(row) < len(header):
                    row = row + [""] * (len(header) - len(row))
                # Truncate long rows
                if len(row) > len(header):
                    row = row[: len(header)]
                rows.append(row)
        return {
            "columns": header,
            "data": rows[:limit],
            "total_rows": len(rows),
        }

    payload = await asyncio.to_thread(_read)
    payload["filename"] = clean
    payload["limit"] = limit
    return payload


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)) -> dict[str, Any]:
    """Save an uploaded CSV to data/. Rejects if file already exists."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="no filename in upload")
    clean = _validate_filename(file.filename)
    target = DATA / clean
    if target.exists():
        raise HTTPException(status_code=409, detail=f"{clean} already exists in data/")

    def _save() -> int:
        body = file.file.read()
        target.write_bytes(body)
        return len(body)

    size = await asyncio.to_thread(_save)
    return {
        "ok": True,
        "filename": clean,
        "size_bytes": size,
        "message": f"Uploaded {clean} ({size} bytes)",
    }


@app.post("/api/sync")
async def sync(req: SyncRequest) -> SyncResponse:
    """Regenerate master.csv from per-kraj CSVs. Optionally run verify_api."""
    def _do_sync() -> dict[str, Any]:
        ok, count = regenerate_master()
        result: dict[str, Any] = {"master_ok": ok, "master_rows": count}
        if req.source_type in ("all", "verify"):
            # Run verify_api as a subprocess — it has its own argv handling
            # and writes back to the per-kraj CSVs.
            import subprocess
            try:
                proc = subprocess.run(
                    [sys.executable, str(Path(__file__).parent / "verify_api.py"),
                     "--all", "--dry-run"],
                    capture_output=True, text=True, timeout=120,
                )
                result["verify_stdout_tail"] = proc.stdout[-1000:]
                result["verify_returncode"] = proc.returncode
            except Exception as e:
                result["verify_error"] = f"{type(e).__name__}: {e}"
        return result

    payload = await asyncio.to_thread(_do_sync)
    msg = f"master.csv: {payload['master_rows']} rows" if payload["master_ok"] else "master regen failed"
    return SyncResponse(
        ok=payload["master_ok"],
        message=msg,
        master_rows=payload.get("master_rows"),
        verify_summary={k: v for k, v in payload.items() if k.startswith("verify_")},
    )


@app.post("/api/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    """
    LLM proxy. Tries OpenRouter first (env: OPENROUTER_API_KEY).
    Falls back to a mock that returns dataset stats — useful for dev/demo
    without burning API quota.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="empty query")

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break

    if api_key:
        return await _chat_openrouter(req, api_key)
    return _chat_mock(req)


# ---------------------------------------------------------------------------
# Chat: OpenRouter (real LLM) + Mock fallback
# ---------------------------------------------------------------------------

async def _chat_openrouter(req: ChatRequest, api_key: str) -> ChatResponse:
    """Call OpenRouter's chat completions API. Model: deepseek/deepseek-chat (cheap)."""
    import urllib.error
    import urllib.request

    # Pull a tiny context from the active dataset (first 3 rows + total count)
    context = ""
    if req.active_dataset:
        try:
            clean = _validate_filename(req.active_dataset)
            path = _csv_path(clean)
            with path.open("r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                rows = []
                for r in reader:
                    if r and not all(c == "" for c in r):
                        rows.append(r)
                    if len(rows) >= 3:
                        break
            if header and rows:
                context = (
                    f"\n\nActive dataset: {clean}\n"
                    f"Total rows (excluding header): {len(rows) if len(rows) < 3 else '>=3 sampled'}\n"
                    f"Columns ({len(header)}): {', '.join(header[:20])}\n"
                    f"First row: {dict(zip(header, rows[0]))}"
                )
        except HTTPException:
            pass  # dataset not found — proceed without context

    body = json.dumps({
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": (
                "Jesteś asystentem BILLSzuka — polskiej platformy B2B research do dystrybucji "
                "maszynek do tytoniu. Odpowiadaj po polsku, zwięźle, z konkretnymi liczbami "
                "gdy to możliwe. Jeśli nie wiesz — powiedz wprost."
            )},
            {"role": "user", "content": req.query + context},
        ],
        "max_tokens": 400,
    }).encode("utf-8")

    def _call() -> dict[str, Any]:
        url = "https://openrouter.ai/api/v1/chat/completions"
        http_req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://billszuka.local",
            },
        )
        with urllib.request.urlopen(http_req, timeout=30) as resp:
            return json.loads(resp.read())

    try:
        data = await asyncio.to_thread(_call)
        text = data["choices"][0]["message"]["content"].strip()
        return ChatResponse(response=text, provider="openrouter")
    except (urllib.error.URLError, KeyError, TimeoutError) as e:
        # Real LLM failed — degrade to mock so the UI never breaks
        mock = _chat_mock(req)
        return ChatResponse(
            response=mock.response + f"\n\n[LLM error: {type(e).__name__}]",
            provider="mock-fallback",
        )


def _chat_mock(req: ChatRequest) -> ChatResponse:
    """Cheap deterministic mock: answers basic count/aggregate questions."""
    q = req.query.lower()
    target_name = req.active_dataset or "master.csv"

    def _count_rows(path: Path) -> int:
        if not path.exists():
            return 0
        with path.open("r", encoding="utf-8", newline="") as f:
            return max(0, sum(1 for _ in f) - 1)  # minus header

    # Resolve the target dataset
    try:
        clean = _validate_filename(target_name)
        path = _csv_path(clean)
    except HTTPException:
        return ChatResponse(
            response=f"Nie widzę datasetu {target_name!r}. Wybierz istniejący plik CSV.",
            provider="mock",
        )

    total = _count_rows(path)

    # Heuristic 1: "ile firm" / "how many companies"
    if "ile" in q and ("firm" in q or "wiersz" in q or "rows" in q or "rekord" in q):
        return ChatResponse(
            response=f"Dataset {clean} zawiera **{total} wierszy** (bez headera).",
            provider="mock",
        )

    # Heuristic 2: "kraj" / "country" — group by first column that looks like kraj
    if "kraj" in q or "country" in q or "państw" in q:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            kraj_col = next((k for k in reader.fieldnames or [] if k.lower() in ("kraj", "country", "kraj_kod")), None)
            if kraj_col:
                counts: dict[str, int] = {}
                for row in reader:
                    k = (row.get(kraj_col) or "?").strip() or "?"
                    counts[k] = counts.get(k, 0) + 1
                top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
                body = ", ".join(f"{k}: {n}" for k, n in top)
                return ChatResponse(
                    response=f"Rozkład wg `{kraj_col}` (top 8): {body}.",
                    provider="mock",
                )

    # Heuristic 3: "frozen" / status
    if "frozen" in q or "status" in q or "weryfik" in q:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            flagi_col = next((k for k in reader.fieldnames or [] if "flagi" in k.lower()), None)
            if flagi_col:
                counts = {"FROZEN": 0, "DO-WERYFIKACJI": 0, "PENDING_API": 0, "OTHER": 0}
                for row in reader:
                    f_val = (row.get(flagi_col) or "").upper()
                    if "FROZEN" in f_val:
                        counts["FROZEN"] += 1
                    elif "PENDING_API" in f_val:
                        counts["PENDING_API"] += 1
                    elif "DO-WERYFIKACJI" in f_val:
                        counts["DO-WERYFIKACJI"] += 1
                    else:
                        counts["OTHER"] += 1
                return ChatResponse(
                    response=(
                        f"Statusy w {clean}: ✅ FROZEN={counts['FROZEN']}, "
                        f"⚠️ DO-WERYFIKACJI={counts['DO-WERYFIKACJI']}, "
                        f"⏳ PENDING_API={counts['PENDING_API']}, "
                        f"❔ OTHER={counts['OTHER']} (z {total} wierszy)."
                    ),
                    provider="mock",
                )

    # Default: nudge the user
    return ChatResponse(
        response=(
            f"Mock AI (OPENROUTER_API_KEY not configured). Mam dostęp do {clean} "
            f"({total} wierszy). Spróbuj pytań typu: 'ile firm', 'rozkład wg kraj', "
            f"'status frozen'. Ustaw OPENROUTER_API_KEY w .env dla prawdziwego LLM."
        ),
        provider="mock",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="BILLSzuka API server (FastAPI)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--reload", action="store_true", help="dev mode (auto-reload)")
    args = ap.parse_args()

    import uvicorn
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
