#!/usr/bin/env python3
"""
api_server.py — FastAPI backend for the BILLSzuka Dashboard frontend.

Wired endpoints (matching frontend/src/App.jsx fetch calls):
  GET  /api/datasets         → list CSV files in data/
  GET  /api/dataset/{name}   → read CSV, return columns + first N rows
  POST /api/upload           → save uploaded CSV to data/
  POST /api/sync             → regenerate master.csv + run verify
  POST /api/chat             → LLM proxy (multi-provider fallback chain)
  GET  /api/settings         → redacted secrets vault snapshot
  POST /api/settings/{provider}              → add a key
  DELETE /api/settings/{provider}/{alias}    → remove a key
  POST /api/settings/{provider}/{alias}/test → validate a key
  PUT  /api/settings/priority                → reorder fallback chain
  GET  /api/knowledge        → list indexed knowledge files
  POST /api/knowledge/upload → upload PDF/CSV to Gemini Files API
  DELETE /api/knowledge/{id} → remove file from index + Gemini

Start:
  python3 tools/api_server.py                 # binds 0.0.0.0:8000 (all interfaces)
  python3 tools/api_server.py --host 127.0.0.1 # loopback only (extra-restrictive)
  python3 tools/api_server.py --port 9000
  python3 tools/api_server.py --reload        # dev mode (uvicorn)

The Vite dev server proxies /api/* → http://127.0.0.1:8000 (see
frontend-2/vite.config.js), so the frontend never sees CORS in dev.

Binding to 0.0.0.0 (all interfaces) makes the API reachable from the LAN
(e.g. for testing on a phone or another machine on the same wifi) — the
same address Vite advertises on startup. The vault only contains
user-supplied keys; no secrets are exposed unless you also explicitly
hit /api/settings, which is localhost-equivalent in a normal workflow.

All data is read from / written to the project data/ directory — paths
are validated against path traversal (no `..` components allowed in
filenames).
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Sibling modules — same dir
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_run import regenerate_master  # noqa: E402

import db         # noqa: E402  (SQLite store)
import faq        # noqa: E402  (FAQ matching/save-command/staleness)
import md_corpus  # noqa: E402  (permanent .md corpus + inbox)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Secrets vault — stores OpenRouter + Gemini keys + priority order.
# Auto-bootstrapped from production env vars and local .env
# (OPENROUTER_API_KEY + GEMINI_API_KEY_1..N). After that, manage via the
# Settings drawer (UI) — keys added there persist across restarts on a
# persistent filesystem. File perms are forced to 0600 on every write.
# Gitignored.
SECRETS_PATH = Path(__file__).resolve().parent / "api_secrets.json"
SECRETS_DEFAULT: dict[str, Any] = {
    "openrouter": [],   # [{alias, key, created, last_ok, last_err, source}]
    "gemini": [],       # [{alias, key, project, created, last_ok, last_err, source}]
    "priority": ["openrouter", "gemini", "mock"],
}
VALID_PROVIDERS = {"openrouter", "gemini", "mock"}

# ---------------------------------------------------------------------------
# Server-side auth: X-Billszuka-User header verified against the hash
# allow-list in frontend-2/public/access.json (spec §6).
# ---------------------------------------------------------------------------

def _verified_user(header: str | None) -> str | None:
    """Verify X-Billszuka-User against the hash allow-list. Returns the
    verified lowercase name or None. ROOT is read at call time so tests
    can monkeypatch it."""
    if not header:
        return None
    access_json = ROOT / "frontend-2" / "public" / "access.json"
    try:
        allowed = set(json.loads(access_json.read_text(encoding="utf-8")).get("names", []))
    except (json.JSONDecodeError, OSError):
        return None
    name = header.strip().lower()
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
    return name if digest in allowed else None


def _require_user(header: str | None) -> str:
    """403 unless the header carries a verified allow-listed name."""
    user = _verified_user(header)
    if not user:
        raise HTTPException(status_code=403, detail="verified user required")
    return user

# Upload validation
ALLOWED_CSV_SUFFIX = ".csv"
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000
ALLOWED_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")  # no /, no .., no spaces

# Knowledge base — files uploaded to the Gemini Files API for grounding.
# `data/knowledge/` holds:
#   - index.json: list of {id, filename, size, mime_type, gemini_name,
#                          gemini_uri, uploaded_at, status}
#   - files/    : local copies (so we can re-upload if Gemini expires the
#                 file after 48h, which is the default Files API TTL).
# Gemini's Files API supports 20 MB per file inline, 2 GB via Files API.
# We default to the Files API path (multipart upload) for everything.
KNOWLEDGE_DIR = DATA / "knowledge"
KNOWLEDGE_FILES_DIR = KNOWLEDGE_DIR / "files"
KNOWLEDGE_INDEX_PATH = KNOWLEDGE_DIR / "index.json"
KNOWLEDGE_MAX_BYTES = 50 * 1024 * 1024  # 50 MB per file — keep uploads snappy
ALLOWED_KNOWLEDGE_MIME_PREFIXES = (
    "application/pdf",
    "text/csv",
    "text/plain",
    "text/markdown",
    "application/vnd.openxmlformats-officedocument",  # .xlsx, .docx
)
ALLOWED_KNOWLEDGE_EXTS = {".pdf", ".csv", ".txt", ".md", ".markdown", ".xlsx", ".xls", ".docx"}

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
    allow_origins=[
            "http://localhost:3000", "http://127.0.0.1:3000",
            "http://localhost:3001", "http://127.0.0.1:3001",
        ],
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
    # Optional list of knowledge file IDs (from /api/knowledge index) that
    # should be attached as Gemini `file_data` parts to the next chat call.
    # Empty = no knowledge context. The frontend sends the IDs; the backend
    # resolves them to Gemini file URIs at call time.
    knowledge_ids: list[str] = []
    # Power-user escape hatch: skip the Gemini-first chain reorder and use
    # the stored priority as-is. Hidden flag for now; the UI doesn't expose
    # it. Default False.
    prefer_openrouter: bool = False

class ChatResponse(BaseModel):
    response: str
    provider: str  # "openrouter" | "gemini" | "mock" | "*-fallback" | "error"

class AddKeyRequest(BaseModel):
    alias: str
    key: str
    project: str | None = None

class PriorityRequest(BaseModel):
    priority: list[str]

class GenerateRequest(BaseModel):
    mode: str = "full"          # "full" | "doc"
    doc_id: str | None = None   # corpus .md filename for doc mode


# ---------------------------------------------------------------------------
# Knowledge base helpers (Gemini Files API grounding)
# ---------------------------------------------------------------------------
import mimetypes
import uuid
from datetime import datetime, timezone


def _ensure_knowledge_dirs() -> None:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_FILES_DIR.mkdir(parents=True, exist_ok=True)
    if not KNOWLEDGE_INDEX_PATH.exists():
        KNOWLEDGE_INDEX_PATH.write_text("[]", encoding="utf-8")


def _read_knowledge_index() -> list[dict[str, Any]]:
    _ensure_knowledge_dirs()
    try:
        raw = json.loads(KNOWLEDGE_INDEX_PATH.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write_knowledge_index(items: list[dict[str, Any]]) -> None:
    _ensure_knowledge_dirs()
    KNOWLEDGE_INDEX_PATH.write_text(
        json.dumps(items, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _get_first_gemini_key() -> str | None:
    """Return the first active Gemini key from the vault, or None."""
    vault = _secrets_load()
    for entry in vault.get("gemini", []):
        if entry.get("key"):
            return entry["key"]
    return None


def _gemini_files_upload(api_key: str, file_path: Path, display_name: str, mime_type: str) -> dict[str, Any]:
    """Upload file to Gemini Files API via single-request multipart.

    Gemini's response shape is `{"file": {"name": "files/...", "uri": "...", "state": "..."}}`.
    We unwrap that here and return just the inner file resource so the rest
    of the code can use a flat shape.
    """
    import urllib.error
    import urllib.request

    file_bytes = file_path.read_bytes()
    boundary = f"----BILLSzuka{uuid.uuid4().hex}"
    json_part = json.dumps({"file": {"display_name": display_name}}).encode("utf-8")
    parts: list[bytes] = [
        f"--{boundary}\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        .encode("utf-8"),
        json_part,
        b"\r\n",
        f"--{boundary}\r\n"
        f"Content-Type: {mime_type}\r\n\r\n"
        .encode("utf-8"),
        file_bytes,
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)
    url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/related; boundary={boundary}",
            "X-Goog-Upload-Protocol": "multipart",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    # Response shape: {"file": {"name": "files/...", "uri": "...", ...}}
    inner = result.get("file") if isinstance(result, dict) else None
    if not isinstance(inner, dict):
        raise RuntimeError(f"unexpected Gemini Files API response: {result}")
    return inner


def _gemini_files_delete(api_key: str, file_name: str) -> bool:
    """Delete a file from Gemini Files API. `file_name` is the resource name like 'files/abc'."""
    import urllib.error
    import urllib.request
    url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={api_key}"
    try:
        req = urllib.request.Request(url, method="DELETE")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return False


def _resolve_knowledge_refs(ids: list[str]) -> list[dict[str, Any]]:
    """Look up knowledge files by id, return those with valid Gemini refs."""
    if not ids:
        return []
    items = _read_knowledge_index()
    by_id = {it["id"]: it for it in items if "id" in it}
    out = []
    for kid in ids:
        item = by_id.get(kid)
        if not item:
            continue
        if not item.get("gemini_name") or not item.get("gemini_uri"):
            continue
        if item.get("status") == "failed":
            continue
        out.append({
            "id": item["id"],
            "filename": item.get("filename"),
            "mime_type": item.get("mime_type"),
            "file_data": {
                "mime_type": item.get("mime_type") or "application/pdf",
                "file_uri": item["gemini_uri"],
            },
        })
    return out





# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_filename(name: str) -> str:
    """Reject path traversal and weird characters. Returns the clean name."""
    if not name or name.startswith(".") or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="invalid filename")
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

    Excludes data housekeeping dirs (snapshots, verify state, backups,
    intake) so a stale copy in there can't shadow the canonical file.
    """
    # Try root first (faster, common case for top-level files)
    candidate = (DATA / filename).resolve()
    if not str(candidate).startswith(str(DATA.resolve())):
        raise HTTPException(status_code=400, detail="path traversal blocked")
    if candidate.exists():
        return candidate
    # Fall back to recursive search, but only in real country subdirs.
    SKIP_DIRS = {
        ".snapshots", ".verify-state", "backups", "verification",
        "_intake", ".pre-clean-notatki", ".pre-dedup-20260821",
        ".pre-fix-20260821", ".enrichment-20260821",
    }
    matches = [
        p for p in DATA.rglob(filename)
        if p.is_file()
        and not p.name.startswith("._")
        and not any(part in SKIP_DIRS for part in p.relative_to(DATA).parts)
    ]
    if not matches:
        raise HTTPException(status_code=404, detail=f"{filename} not found in data/")
    return matches[0]


# ---------------------------------------------------------------------------
# Secrets vault helpers
# ---------------------------------------------------------------------------

def _secrets_load() -> dict[str, Any]:
    """Read vault from disk. Returns defaults if missing/corrupt."""
    if not SECRETS_PATH.exists():
        return json.loads(json.dumps(SECRETS_DEFAULT))
    try:
        data = json.loads(SECRETS_PATH.read_text(encoding="utf-8"))
        out = json.loads(json.dumps(SECRETS_DEFAULT))
        for prov in ("openrouter", "gemini"):
            if isinstance(data.get(prov), list):
                out[prov] = [
                    x for x in data[prov]
                    if isinstance(x, dict) and x.get("key")
                ]
        if isinstance(data.get("priority"), list):
            out["priority"] = [p for p in data["priority"] if p in VALID_PROVIDERS] \
                or list(SECRETS_DEFAULT["priority"])
        return out
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(SECRETS_DEFAULT))


def _secrets_save(data: dict[str, Any]) -> None:
    """Write vault atomically with 0600 perms."""
    SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SECRETS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    tmp.replace(SECRETS_PATH)
    try:
        os.chmod(SECRETS_PATH, 0o600)
    except OSError:
        pass


def _fingerprint(key: str) -> str:
    """4…4 chars. Returns '' if key is too short."""
    if not key or len(key) < 8:
        return ""
    return f"{key[:4]}…{key[-4:]}"


def _redact(vault: dict[str, Any]) -> dict[str, Any]:
    """Return snapshot with raw keys replaced by fingerprints."""
    return {
        "openrouter": [
            {k: v for k, v in entry.items() if k != "key"}
            | {"fingerprint": _fingerprint(entry.get("key", ""))}
            for entry in vault.get("openrouter", [])
        ],
        "gemini": [
            {k: v for k, v in entry.items() if k != "key"}
            | {"fingerprint": _fingerprint(entry.get("key", ""))}
            for entry in vault.get("gemini", [])
        ],
        "priority": vault.get("priority", []),
    }


def _read_env_keys() -> dict[str, list[dict[str, Any]]]:
    """Pull OPENROUTER_API_KEY + GEMINI_API_KEY_1..N from env and .env.

    Production hosts like Render expose secrets via os.environ; local
    development also supports ROOT/.env. Environment variables win when the
    same alias exists in both places. Returns
    {"openrouter": [{alias, key, source}], "gemini": [...]} and skips empty
    entries.
    """
    out = {"openrouter": [], "gemini": []}
    seen: dict[str, set[str]] = {"openrouter": set(), "gemini": set()}

    def add(provider: str, alias: str, key: str, source: str) -> None:
        key = (key or "").strip()
        if not key or alias in seen[provider]:
            return
        out[provider].append({"alias": alias, "key": key, "source": source})
        seen[provider].add(alias)

    # Production/runtime environment first.
    add("openrouter", "primary", os.environ.get("OPENROUTER_API_KEY", ""), "env")
    for k, v in sorted(os.environ.items()):
        if not k.startswith("GEMINI_API_KEY_"):
            continue
        num = k[len("GEMINI_API_KEY_"):]
        if num.isdigit():
            add("gemini", f"env-{num}", v, "env")

    # Local .env fallback (does not override runtime env aliases).
    env_file = ROOT / ".env"
    if not env_file.exists():
        return out
    for line in env_file.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        v = v.strip()
        if k == "OPENROUTER_API_KEY":
            add("openrouter", "primary", v, ".env")
        elif k.startswith("GEMINI_API_KEY_"):
            num = k[len("GEMINI_API_KEY_"):]
            if num.isdigit():
                add("gemini", f"env-{num}", v, ".env")
    return out


def _bootstrap_vault_from_env() -> dict[str, Any]:
    """Load vault, merge in any runtime env/.env keys that aren't present.

    Returns the final vault. Idempotent: running it twice with the same
    variables does not create duplicates (matched by alias).
    """
    vault = _secrets_load()
    env_keys = _read_env_keys()
    changed = False
    for prov in ("openrouter", "gemini"):
        existing_aliases = {k.get("alias") for k in vault[prov]}
        for entry in env_keys[prov]:
            if entry["alias"] not in existing_aliases:
                entry["created"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                vault[prov].append(entry)
                changed = True
    if changed:
        _secrets_save(vault)
    return vault


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
        SKIP_DIRS = {".snapshots", ".verify-state", "backups", "verification", "_intake", "temp"}
        # Per-country catalogs (the A/B files)
        for sub in sorted(DATA.iterdir()):
            if not sub.is_dir() or sub.name.startswith(".") or sub.name in SKIP_DIRS:
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


@app.get("/api/master.csv")
async def get_master_csv_raw() -> FileResponse:
    """Raw master.csv bytes for the frontend's boot-time fetch (RawTable.jsx
    parses this directly with PapaParse). Distinct from /api/dataset/{name},
    which returns paginated JSON, not a raw file — the frontend needs the
    full CSV to run its own client-side parsing/inference.

    Cache-Control: no-cache (NOT no-store) so the browser revalidates with
    If-None-Match / If-Modified-Since on every reload — essential when
    Marceli edits data/master.csv manually and expects to see changes on
    next reload. Without this, etag-based caching makes the browser serve
    a stale copy after a save. The frontend also appends ?v=<mtime> as a
    belt-and-braces cache-buster."""
    path = DATA / "master.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="master.csv not found in data/")
    response = FileResponse(path, media_type="text/csv", filename="master.csv")
    response.headers["Cache-Control"] = "no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response


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


# ---------------------------------------------------------------------------
# Knowledge base endpoints (Gemini Files API grounding)
# ---------------------------------------------------------------------------

@app.get("/api/knowledge")
async def list_knowledge() -> dict[str, Any]:
    """List files in the knowledge index plus the .md corpus inbox (with
    pending count). Each entry includes the Gemini file ref so the frontend
    can pass ids straight to /api/chat."""
    items = _read_knowledge_index()
    inbox: list[dict[str, Any]] = []
    pending = 0
    try:
        with db.connect() as conn:
            rows = conn.execute(
                "SELECT file, saved_by, question, status, saved_at FROM knowledge_inbox "
                "ORDER BY saved_at DESC").fetchall()
            inbox = [dict(r) for r in rows]
            pending = sum(1 for r in rows if r["status"] == "pending")
    except Exception:
        pass
    return {"items": items, "count": len(items), "inbox": inbox, "inbox_pending": pending}


@app.post("/api/knowledge/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    x_billszuka_user: str | None = Header(None, alias="X-Billszuka-User"),
) -> dict[str, Any]:
    """Upload a PDF / CSV / text file to the Gemini Files API and add it to
    the local knowledge index. The file is also cached locally under
    data/knowledge/files/ so we can re-upload to Gemini if it expires after
    the default 48h TTL.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="no filename in upload")
    user = _require_user(x_billszuka_user)  # 403 before any Gemini work

    # Validate extension + size
    raw_name = file.filename
    ext = Path(raw_name).suffix.lower()
    if ext not in ALLOWED_KNOWLEDGE_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported file type {ext!r}; allowed: {sorted(ALLOWED_KNOWLEDGE_EXTS)}",
        )

    _ensure_knowledge_dirs()
    body = await file.read()
    if len(body) > KNOWLEDGE_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"file too large ({len(body)} bytes); max {KNOWLEDGE_MAX_BYTES}",
        )
    if not body:
        raise HTTPException(status_code=400, detail="empty file")

    mime_type, _ = mimetypes.guess_type(raw_name)
    if not mime_type:
        mime_type = "application/octet-stream"

    api_key = _get_first_gemini_key()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="no Gemini key in vault — add one in Settings (gear icon) first",
        )

    # Save locally first (idempotent — overwrite existing copy)
    file_id = uuid.uuid4().hex[:12]
    safe_name = re.sub(r"[^A-Za-z0-9_.\-]+", "_", Path(raw_name).name)
    if not safe_name or safe_name.startswith("."):
        safe_name = f"upload_{file_id}{ext or '.bin'}"
    local_path = KNOWLEDGE_FILES_DIR / f"{file_id}__{safe_name}"
    local_path.write_bytes(body)

    # Push to Gemini Files API
    item: dict[str, Any] = {
        "id": file_id,
        "filename": raw_name,
        "safe_name": safe_name,
        "size": len(body),
        "mime_type": mime_type,
        "local_path": str(local_path.relative_to(ROOT)),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": user,
        "status": "uploading",
    }
    try:
        result = await asyncio.to_thread(
            _gemini_files_upload, api_key, local_path, safe_name, mime_type
        )
        # Gemini file resource shape:
        #   { "name": "files/abc123", "uri": "https://...", "state": "ACTIVE", ... }
        item["gemini_name"] = result.get("name")
        item["gemini_uri"] = result.get("uri")
        item["gemini_state"] = result.get("state", "ACTIVE")
        item["status"] = "ready"
    except Exception as e:
        item["status"] = "failed"
        item["error"] = str(e)
        # Still keep the local copy so the user can retry

    items = _read_knowledge_index()
    items.append(item)
    _write_knowledge_index(items)

    if item["status"] == "failed":
        raise HTTPException(
            status_code=502,
            detail=f"uploaded locally but Gemini Files API failed: {item.get('error')}",
        )
    return item


@app.delete("/api/knowledge/{file_id}")
async def delete_knowledge(
    file_id: str,
    x_billszuka_user: str | None = Header(None, alias="X-Billszuka-User"),
) -> dict[str, Any]:
    """Remove a file from the knowledge index and from Gemini Files API."""
    _require_user(x_billszuka_user)
    items = _read_knowledge_index()
    match = next((it for it in items if it.get("id") == file_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"knowledge id {file_id!r} not found")

    api_key = _get_first_gemini_key()
    gemini_name = match.get("gemini_name")
    if api_key and gemini_name:
        await asyncio.to_thread(_gemini_files_delete, api_key, gemini_name)

    # Best-effort local file cleanup
    try:
        local_rel = match.get("local_path")
        if local_rel:
            local = ROOT / local_rel
            if local.exists() and local.is_file():
                local.unlink()
    except OSError:
        pass

    items = [it for it in items if it.get("id") != file_id]
    _write_knowledge_index(items)
    return {"ok": True, "deleted": file_id}


@app.post("/api/knowledge/{file_id}/refresh")
async def refresh_knowledge(
    file_id: str,
    x_billszuka_user: str | None = Header(None, alias="X-Billszuka-User"),
) -> dict[str, Any]:
    """Re-upload a knowledge file to the Gemini Files API.

    Use this when the original Gemini upload expired (48h TTL) or the
    upstream file is otherwise unavailable — we have the local copy at
    `data/knowledge/files/<id>__<safe_name>`, so we just push it again and
    update the index with the new gemini_uri. The old Gemini file is
    best-effort deleted first to avoid orphans.
    """
    _require_user(x_billszuka_user)
    items = _read_knowledge_index()
    idx = next((i for i, it in enumerate(items) if it.get("id") == file_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"knowledge id {file_id!r} not found")
    match = items[idx]

    local_rel = match.get("local_path")
    if not local_rel:
        raise HTTPException(status_code=409, detail="no local copy available — re-upload via drag-drop")
    local = ROOT / local_rel
    if not local.exists() or not local.is_file():
        raise HTTPException(
            status_code=410,
            detail=f"local copy missing ({local_rel}) — re-upload via drag-drop",
        )

    api_key = _get_first_gemini_key()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="no Gemini key in vault — add one in Settings (gear icon) first",
        )

    mime_type = match.get("mime_type") or "application/octet-stream"
    safe_name = match.get("safe_name") or local.name

    # Best-effort: drop the old Gemini file before re-uploading
    old_gemini_name = match.get("gemini_name")
    if old_gemini_name:
        await asyncio.to_thread(_gemini_files_delete, api_key, old_gemini_name)

    try:
        new_file = await asyncio.to_thread(
            _gemini_files_upload, api_key, local, safe_name, mime_type
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini re-upload failed: {e}")

    items[idx]["gemini_name"] = new_file.get("name")
    items[idx]["gemini_uri"] = new_file.get("uri")
    items[idx]["gemini_state"] = new_file.get("state", "ACTIVE")
    items[idx]["status"] = "ready"
    if "error" in items[idx]:
        del items[idx]["error"]
    items[idx]["refreshed_at"] = datetime.now(timezone.utc).isoformat()
    _write_knowledge_index(items)
    return items[idx]


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


# ---------------------------------------------------------------------------
# Quota-aware key cooldown (avoids hammering a known-429'd key)
# ---------------------------------------------------------------------------

# Module-level state — updated by _call_gemini when a 429 is observed, read
# by the chain handler. A 429'd key is "cooled down" for this many seconds
# before we'll try it again. Conservative: 60s for free-tier RPM (15/min),
# longer if the error said "credits depleted".
QUOTA_COOLDOWN_SECONDS = 60
_quota_last_seen: dict[str, float] = {}


def _stamp_quota_error(api_key: str) -> None:
    _quota_last_seen[api_key] = time.time()


def _is_key_cooled_down(entry: dict[str, Any]) -> bool:
    """Skip this key if it 429'd less than QUOTA_COOLDOWN_SECONDS ago."""
    key = entry.get("key")
    if not key:
        return False
    last = _quota_last_seen.get(key)
    if last is None:
        return True
    return (time.time() - last) > QUOTA_COOLDOWN_SECONDS


def _last_call_was_quota() -> bool:
    """True if any Gemini key was quota-errored in the last call.
    Used by the chat handler to label the fallback as 'gemini-quota'."""
    if not _quota_last_seen:
        return False
    latest = max(_quota_last_seen.values())
    return (time.time() - latest) < 5  # within the last 5 seconds


# ---------------------------------------------------------------------------
# Chat: save-command → FAQ → chain → log
# ---------------------------------------------------------------------------

def _log_chat(user: str | None, query: str, response: str, provider: str,
              dataset: str | None, knowledge_ids: list[str], faq_hit: int,
              sources: str) -> None:
    """Non-fatal chat log write (spec §5)."""
    try:
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO chat_log (ts, user, query, response, provider, dataset, "
                "knowledge_ids, faq_hit, sources) VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)",
                (user, query, response, provider, dataset,
                 json.dumps(knowledge_ids), faq_hit, sources),
            )
    except Exception as e:
        print(f"[chat_log] write failed: {e}", file=sys.stderr)


def _last_chat_response() -> str | None:
    """Last non-save assistant response — the save-command target."""
    try:
        with db.connect() as conn:
            row = conn.execute(
                "SELECT response FROM chat_log WHERE provider != 'save' "
                "AND response IS NOT NULL AND response != '' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return row["response"] if row else None
    except Exception:
        return None


def _last_chat_query() -> str | None:
    try:
        with db.connect() as conn:
            row = conn.execute(
                "SELECT query FROM chat_log WHERE provider != 'save' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return row["query"] if row else None
    except Exception:
        return None


@app.post("/api/chat")
async def chat(
    req: ChatRequest,
    x_billszuka_user: str | None = Header(None, alias="X-Billszuka-User"),
) -> ChatResponse:
    """Gills chat: save-command → FAQ lookup → LLM chain. Every Q&A is
    logged to chat_log; FAQ hits and saves cost zero tokens."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="empty query")

    user = _verified_user(x_billszuka_user)  # None for anonymous — log only

    # 1. "Zapisz ten fakt" command — zero tokens, writes the inbox.
    last = _last_chat_response()
    note = faq.is_save_command(req.query, last is not None)
    if note is not None:
        ok, msg = md_corpus.save_fact_to_inbox(
            last or "", _last_chat_query() or req.query, [], user or "anonim")
        _log_chat(user, req.query, msg, "save", req.active_dataset,
                  req.knowledge_ids, 0, "[]")
        return ChatResponse(response=msg, provider="save")

    # 2. FAQ lookup — zero tokens when hit.
    try:
        hit = faq.match_faq(req.query, faq.list_entries())
    except Exception as e:
        print(f"[faq] lookup disabled: {e}", file=sys.stderr)
        hit = None
    if hit is not None:
        stale = faq.check_stale(hit)
        if stale and hit["verified_kind"] == "numeric":
            # Stale numbers are never served — fall through to the live
            # chain (fresh data, correct numbers).
            _log_chat(user, req.query, "", "faq-stale-skip", req.active_dataset,
                      req.knowledge_ids, 1, hit["sources"])
        else:
            response = hit["a"]
            if stale:
                response = ("⚠️ Dane mogły się zmienić od wygenerowania FAQ — "
                            "odśwież sesję FAQ.\n\n") + response
            faq.bump_hits(hit["id"])
            _log_chat(user, req.query, response, "faq", req.active_dataset,
                      req.knowledge_ids, 1, hit["sources"])
            return ChatResponse(response=response, provider="faq")

    # 3. LLM chain (unchanged behavior — gemini → mock → openrouter).
    vault = _bootstrap_vault_from_env()
    chain = vault.get("priority", list(SECRETS_DEFAULT["priority"]))
    if not getattr(req, "prefer_openrouter", False):
        order = ["gemini", "mock", "openrouter"]
        chain = [p for p in order if p in chain] + [p for p in chain if p not in order]

    all_gemini_quota = True
    gemini_attempted = False
    result: ChatResponse | None = None

    for provider in chain:
        if provider == "openrouter":
            for entry in [k for k in vault.get("openrouter", []) if k.get("key")]:
                result = await _call_openrouter(req, entry["key"])
                if result:
                    entry["last_ok"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    _secrets_save(vault)
                    break
                entry["last_err"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                _secrets_save(vault)
            if result:
                break
        elif provider == "gemini":
            for entry in [k for k in vault.get("gemini", []) if k.get("key")]:
                gemini_attempted = True
                if _is_key_cooled_down(entry) is False:
                    continue
                result = await _call_gemini(req, entry["key"])
                if result:
                    all_gemini_quota = False
                    entry["last_ok"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    _secrets_save(vault)
                    break
                if _last_call_was_quota():
                    entry["last_quota_err"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                entry["last_err"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                _secrets_save(vault)
            if result:
                break
        elif provider == "mock":
            mock = _chat_mock(req)
            if all_gemini_quota and gemini_attempted:
                # ONE coherent note. The default mock text must never blame a
                # provider itself — that's how the old code produced two
                # contradictory messages in one answer ("OPENROUTER_API_KEY
                # not configured" + "klucze Gemini wyczerpały limit").
                result = ChatResponse(
                    response=(
                        mock.response
                        + "\n\n_(Żaden klucz Gemini nie odpowiedział (limit "
                        "wyczerpany) — to odpowiedź deterministyczna z mocka. "
                        "Dodaj klucz w Ustawieniach albo wygeneruj sesję FAQ "
                        "(widok „100 pytań do…”), żeby pytania o dane działały "
                        "bez tokenów.)_"
                    ),
                    provider="mock-gemini-quota",
                )
            else:
                result = mock
            break

    if result is None:
        mock = _chat_mock(req)
        result = ChatResponse(
            response=(
                mock.response
                + "\n\n_(Wszyscy dostawcy LLM zawiedli — odpowiedź z mocka. "
                "Sprawdź klucze w Ustawieniach albo wygeneruj sesję FAQ, "
                "żeby pytania o dane działały bez tokenów.)_"
            ),
            provider="mock-fallback",
        )

    _log_chat(user, req.query, result.response, result.provider, req.active_dataset,
              req.knowledge_ids, 0, "[]")
    return result


# ---------------------------------------------------------------------------
# Chat: OpenRouter (real LLM) + Mock fallback
# ---------------------------------------------------------------------------

async def _call_openrouter(req: ChatRequest, api_key: str) -> ChatResponse | None:
    """Call OpenRouter. Returns None on failure (chain moves on)."""
    import urllib.error
    import urllib.request

    context = _build_dataset_context(req.active_dataset)

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

    def _do() -> dict[str, Any]:
        url = "https://openrouter.ai/api/v1/chat/completions"
        http_req = urllib.request.Request(
            url, data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://billszuka.local",
            },
        )
        with urllib.request.urlopen(http_req, timeout=30) as resp:
            return json.loads(resp.read())

    try:
        data = await asyncio.to_thread(_do)
        text = data["choices"][0]["message"]["content"].strip()
        return ChatResponse(response=text, provider="openrouter")
    except (urllib.error.URLError, KeyError, TimeoutError, json.JSONDecodeError):
        return None


async def _call_gemini(req: ChatRequest, api_key: str) -> ChatResponse | None:
    """Call Google Gemini (Gemini 3.6 Flash — free tier friendly).

    When req.knowledge_ids is non-empty, the matching files (uploaded to
    the Gemini Files API via /api/knowledge) are attached as `file_data`
    parts to the request so the model grounds its answer in them.

    Auto-recovery: if Gemini returns 404 (expired file — Files API TTL
    is 48h by default), we re-upload every attached file from its
    local copy under `data/knowledge/files/`, update the index with
    fresh `gemini_uri`s, and retry the call once. The user never has
    to click the manual refresh button.

    Returns None on unrecoverable failure (chain moves on).
    """
    import urllib.error
    import urllib.request

    context = _build_dataset_context(req.active_dataset)
    knowledge_refs = _resolve_knowledge_refs(req.knowledge_ids)
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.6-flash:generateContent?key={api_key}"
    )

    def _build_payload(refs: list[dict[str, Any]]) -> bytes:
        user_parts: list[dict[str, Any]] = [{"text": req.query + context}]
        for ref in refs:
            user_parts.append({"file_data": ref["file_data"]})
        system_text = (
            "Jesteś Gills — asystentem BILLSzuka (polskiej platformy B2B "
            "research do dystrybucji maszynek do tytoniu).\n\n"
            "JAK ODPOWIADAĆ:\n"
            "- Poniżej masz blok 'Active dataset' z PRAWDZIWYMI liczbami. "
            "Używaj TYLKO tych wartości — cytuj konkretne liczby, nie "
            "zaokrąglaj, nie domyślaj się.\n"
            "- Jeśli pytanie dotyczy danych firmy, kategorii, statusu, "
            "rozkładu — odpowiedź powinna opierać się na bloku poniżej.\n"
            "- Jeśli pytanie wykracza poza katalog (np. prognozy rynkowe, "
            "historia) — powiedz krótko: 'To wykracza poza dane w katalogu. "
            "Sprawdź źródła zewnętrzne.'\n"
            "- Odpowiadaj po polsku, zwięźle (2-4 zdania), z konkretnymi "
            "liczbami.\n"
            "- Jeśli masz załączone pliki, możesz się na nich opierać — "
            "ale cytuj fragmenty, nie streszczaj 'z głowy'."
        )
        if refs:
            attached = ", ".join(r["filename"] or r["id"] for r in refs)
            system_text += (
                f"\n\nDo tej rozmowy dołączono {len(refs)} plik(ów) z bazy wiedzy: "
                f"{attached}. Możesz się na nich opierać przy odpowiedzi."
            )
        corpus_blocks = md_corpus.inject_corpus([], reserved_chars=len(context) + len(req.query))
        if corpus_blocks:
            system_text += (
                "\n\nKORPUS WIEDZY (stałe dokumenty projektu — opieraj się na nich "
                "i wskazuj nazwę pliku źródłowego):\n" + "\n".join(corpus_blocks)
            )

        # Markup contract (spec §9) — the frontend renderer understands only
        # this subset; anything else degrades to plain text.
        system_text += (
            "\n\nFORMAT ODPOWIEDZI (lekki markup, renderowany po stronie UI): "
            "nagłówki pisz jako „## Tytuł”, listy punktowane jako „- element”, "
            "listy numerowane jako „1. element”, pogrubienia jako „**tekst**”, "
            "linki jako „[tekst](https://…)” (tylko adresy http/https). "
            "Kluczowe fakty umieszczaj w bloku ```fakt … ```, ostrzeżenia lub "
            "errata w bloku ```errata … ```, a grupy krótkich pozycji do ułożenia "
            "w kolumnach w bloku ```cols … ``` (jedna pozycja w linii). "
            "Nie używaj żadnego innego formatowania."
        )
        payload: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system_text}]},
            "contents": [{"role": "user", "parts": user_parts}],
            "generationConfig": {"maxOutputTokens": 400},
        }
        return json.dumps(payload).encode("utf-8")

    def _do_request(body: bytes) -> dict[str, Any]:
        http_req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(http_req, timeout=30) as resp:
            return json.loads(resp.read())

    def _is_file_404(err: "urllib.error.HTTPError") -> bool:
        # Gemini returns 404 for "not found" but 403 (PERMISSION_DENIED) for
        # expired/deleted files with a body mentioning "may not exist".
        # Either way, the user-visible effect is the same: the file_data
        # part is unusable. Trigger auto-recovery.
        if err.code not in (403, 404):
            return False
        try:
            body = err.read().decode("utf-8", errors="replace")
        except Exception:
            return True
        body_low = body.lower()
        return (
            "not found" in body_low
            or "not_found" in body_low
            or "not exist" in body_low
            or "expired" in body_low
            or "permission" in body_low  # 403 PERMISSION_DENIED on a file
        )

    async def _refresh_all_refs() -> int:
        """Re-upload every attached knowledge entry from local. Returns
        the number of entries that were successfully refreshed."""
        items = _read_knowledge_index()
        by_id = {it["id"]: it for it in items if "id" in it}
        refreshed = 0
        for ref in knowledge_refs:
            item = by_id.get(ref["id"])
            if not item:
                continue
            local_rel = item.get("local_path")
            if not local_rel:
                continue
            local = ROOT / local_rel
            if not local.exists() or not local.is_file():
                continue
            mime_type = item.get("mime_type") or "application/octet-stream"
            safe_name = item.get("safe_name") or local.name
            old_gemini_name = item.get("gemini_name")
            try:
                if old_gemini_name:
                    await asyncio.to_thread(
                        _gemini_files_delete, api_key, old_gemini_name
                    )
                new_file = await asyncio.to_thread(
                    _gemini_files_upload, api_key, local, safe_name, mime_type
                )
            except Exception:
                continue
            item["gemini_name"] = new_file.get("name")
            item["gemini_uri"] = new_file.get("uri")
            item["gemini_state"] = new_file.get("state", "ACTIVE")
            item["status"] = "ready"
            if "error" in item:
                del item["error"]
            item["refreshed_at"] = datetime.now(timezone.utc).isoformat()
            refreshed += 1
        _write_knowledge_index(items)
        return refreshed

    # Two attempts: initial + one auto-recovery if Gemini returns file 404
    for attempt in range(2):
        body = _build_payload(knowledge_refs)
        try:
            data = await asyncio.to_thread(_do_request, body)
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            suffix = f" (+{len(knowledge_refs)} file)" if knowledge_refs else ""
            if attempt == 1 and knowledge_refs:
                suffix += " (auto-recovered)"
            return ChatResponse(response=text, provider="gemini" + suffix)
        except urllib.error.HTTPError as e:
            # Quota / billing errors — remember the key is hot so the
            # chain handler can skip it for the next ~60s and the user
            # gets a clear "all keys quota'd" message instead of a silent
            # openrouter hallucination.
            if e.code == 429 or e.code == 402:
                _stamp_quota_error(api_key)
            if attempt == 0 and knowledge_refs and _is_file_404(e):
                refreshed = await _refresh_all_refs()
                if refreshed:
                    # Re-resolve refs (they have fresh URIs now) and retry
                    knowledge_refs = _resolve_knowledge_refs(req.knowledge_ids)
                    continue
            return None
        except (urllib.error.URLError, KeyError, TimeoutError, json.JSONDecodeError, IndexError):
            return None
    return None


def _build_dataset_context(active_dataset: str | None) -> str:
    """Aggregate stats for the active dataset, formatted for the LLM.

    The point of this is to anchor the model in real numbers so it can't
    hallucinate when answering "how many / how is X distributed" type
    questions. We pre-compute count + the most useful breakdowns (kraj,
    tier, wolumen, status) once per call and pass the full picture.
    """
    if not active_dataset:
        return ""
    try:
        clean = _validate_filename(active_dataset)
        path = _csv_path(clean)
    except HTTPException:
        return ""

    def _load() -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8", newline="") as f:
            return [r for r in csv.DictReader(f) if r and any((c or "").strip() for c in r.values())]

    try:
        rows = _load()
    except (OSError, csv.Error):
        return ""
    if not rows:
        return ""

    total = len(rows)

    def _hist(field: str) -> list[tuple[str, int]]:
        counts: dict[str, int] = {}
        for r in rows:
            v = (r.get(field) or "").strip() or "(puste)"
            counts[v] = counts.get(v, 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    def _format_hist(name: str, items: list[tuple[str, int]], top: int = 8) -> str:
        if not items:
            return ""
        lines = [f"  {name}:"]
        for k, v in items[:top]:
            lines.append(f"    - {k}: {v}")
        if len(items) > top:
            lines.append(f"    - … {len(items) - top} more values")
        return "\n".join(lines)

    parts: list[str] = [
        f"\n\n=== Active dataset: {clean} ===",
        f"Total rows: {total}",
    ]
    # Only include columns that actually have data
    for field, label in [
        ("kraj", "By kraj"),
        ("tier", "By tier"),
        ("wolumen", "By wolumen (rynek)"),
        ("flagi", "By status weryfikacji"),
        ("kategoria", "By kategoria (A1-A6 / B1-B9)"),
    ]:
        hist = _hist(field)
        if hist:
            parts.append(_format_hist(label, hist))

    return "\n".join(parts)


def _chat_mock(req: ChatRequest) -> ChatResponse:
    """Cheap deterministic mock: answers basic count/aggregate questions."""
    q = req.query.lower()
    target_name = req.active_dataset or "master.csv"

    def _count_rows(path: Path) -> int:
        if not path.exists():
            return 0
        with path.open("r", encoding="utf-8", newline="") as f:
            return max(0, sum(1 for _ in f) - 1)  # minus header

    # Resolve the target dataset. An invalid NAME is rejected outright; a
    # valid name whose file is missing on disk still gets deterministic
    # answers (count 0), so the default nudge stays reachable without a file
    # (spec: the nudge text must be provider-agnostic and always renderable).
    try:
        clean = _validate_filename(target_name)
    except HTTPException:
        return ChatResponse(
            response=f"Nie widzę datasetu {target_name!r}. Wybierz istniejący plik CSV.",
            provider="mock",
        )
    try:
        path = _csv_path(clean)
    except HTTPException:
        path = DATA / clean  # missing on disk — counts resolve to 0

    total = _count_rows(path)

    # Heuristic 1: "ile firm" / "how many companies"
    if "ile" in q and ("firm" in q or "wiersz" in q or "rows" in q or "rekord" in q):
        return ChatResponse(
            response=f"Dataset {clean} zawiera **{total} wierszy** (bez headera).",
            provider="mock",
        )

    # Heuristic 2: "kraj" / "country" — group by first column that looks like kraj
    if ("kraj" in q or "country" in q or "państw" in q) and path.exists():
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
    if ("frozen" in q or "status" in q or "weryfik" in q) and path.exists():
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

    # Default: nudge the user — provider-agnostic. The chat() fallback notes
    # explain WHY the mock answered; this text must not blame a specific key.
    return ChatResponse(
        response=(
            f"To odpowiedź deterministyczna z mocka (bez LLM). Mam dostęp do {clean} "
            f"({total} wierszy). Spróbuj pytań typu: 'ile firm', 'rozkład wg kraj', "
            f"'status frozen' — a dla pytań o dane bez tokenów wygeneruj sesję FAQ "
            f'(widok „100 pytań do…" w Gills).'
        ),
        provider="mock",
    )


# ---------------------------------------------------------------------------
# FAQ endpoints
# ---------------------------------------------------------------------------

@app.get("/api/faq")
async def list_faq() -> dict[str, Any]:
    """Entries with staleness flags, categories and the rejects count."""
    try:
        entries = sorted(faq.list_entries(), key=lambda e: (-(e["hits"] or 0), e["q"]))
        for e in entries:
            try:
                e["stale"] = faq.check_stale(e)
            except Exception:
                e["stale"] = False
        categories = sorted({e["category"] or "inne" for e in entries})
        with db.connect() as conn:
            rejects = conn.execute("SELECT COUNT(*) AS n FROM faq_rejects").fetchone()["n"]
        return {"items": entries, "categories": categories, "rejects": rejects}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"faq store unavailable: {e}")


@app.post("/api/faq/generate")
async def generate_faq(
    req: GenerateRequest,
    x_billszuka_user: str | None = Header(None, alias="X-Billszuka-User"),
) -> dict[str, Any]:
    """Launch a detached generation session. 409 when one is running."""
    _require_user(x_billszuka_user)
    try:
        db.init()
        if not db.claim_session():
            raise HTTPException(status_code=409, detail="session already running")
        cmd = [sys.executable, str(Path(__file__).parent / "faq_build_session.py"), req.mode]
        if req.doc_id:
            cmd.append(req.doc_id)
        subprocess.Popen(cmd, start_new_session=True)
        return {"ok": True, "mode": req.mode, "state": "running"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to start session: {e}")


@app.get("/api/faq/session")
async def faq_session() -> dict[str, Any]:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM faq_session WHERE id=1").fetchone()
    return dict(row) if row else {"state": "idle"}


@app.delete("/api/faq/{entry_id}")
async def delete_faq(
    entry_id: str,
    x_billszuka_user: str | None = Header(None, alias="X-Billszuka-User"),
) -> dict[str, Any]:
    """Remove a bad entry and block it from regeneration."""
    _require_user(x_billszuka_user)
    with db.connect() as conn:
        row = conn.execute("SELECT q FROM faq_entries WHERE id=?", (entry_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="entry not found")
        conn.execute(
            "INSERT OR IGNORE INTO faq_rejects (q, q_norm, reason, rejected_at) "
            "VALUES (?, ?, 'deleted-by-user', datetime('now'))",
            (row["q"], faq.normalize(row["q"])),
        )
        conn.execute("DELETE FROM faq_entries WHERE id=?", (entry_id,))
    return {"ok": True, "deleted": entry_id}


@app.get("/api/faq/rejects")
async def list_faq_rejects() -> dict[str, Any]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM faq_rejects ORDER BY id DESC").fetchall()
    return {"items": [dict(r) for r in rows]}


# ---------------------------------------------------------------------------
# Settings endpoints (secrets vault)
# ---------------------------------------------------------------------------

@app.get("/api/settings")
async def get_settings() -> dict[str, Any]:
    """Redacted vault snapshot — raw keys replaced by fingerprints."""
    vault = _bootstrap_vault_from_env()
    return _redact(vault)


@app.post("/api/settings/openrouter")
async def add_openrouter(req: AddKeyRequest) -> dict[str, Any]:
    return _add_key("openrouter", req.alias, req.key, project=None)


@app.post("/api/settings/gemini")
async def add_gemini(req: AddKeyRequest) -> dict[str, Any]:
    return _add_key("gemini", req.alias, req.key, project=req.project)


def _add_key(provider: str, alias: str, key: str, project: str | None) -> dict[str, Any]:
    if provider not in ("openrouter", "gemini"):
        raise HTTPException(status_code=400, detail=f"unknown provider {provider}")
    if not alias or not key:
        raise HTTPException(status_code=400, detail="alias and key required")
    vault = _bootstrap_vault_from_env()
    if any(k["alias"] == alias for k in vault[provider]):
        raise HTTPException(status_code=409, detail=f"alias '{alias}' exists for {provider}")
    entry: dict[str, Any] = {
        "alias": alias,
        "key": key,
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "ui",
    }
    if project:
        entry["project"] = project
    vault[provider].append(entry)
    _secrets_save(vault)
    return {"ok": True, "alias": alias, "fingerprint": _fingerprint(key)}


@app.delete("/api/settings/{provider}/{alias}")
async def delete_key(provider: str, alias: str) -> dict[str, Any]:
    if provider not in ("openrouter", "gemini"):
        raise HTTPException(status_code=400, detail=f"unknown provider {provider}")
    vault = _bootstrap_vault_from_env()
    before = len(vault[provider])
    vault[provider] = [k for k in vault[provider] if k["alias"] != alias]
    if len(vault[provider]) == before:
        raise HTTPException(status_code=404, detail=f"alias '{alias}' not found in {provider}")
    _secrets_save(vault)
    return {"ok": True}


@app.post("/api/settings/{provider}/{alias}/test")
async def test_key(provider: str, alias: str) -> dict[str, Any]:
    if provider not in ("openrouter", "gemini"):
        raise HTTPException(status_code=400, detail=f"unknown provider {provider}")
    vault = _bootstrap_vault_from_env()
    entry = next((k for k in vault[provider] if k["alias"] == alias), None)
    if not entry:
        raise HTTPException(status_code=404, detail=f"alias '{alias}' not found")
    t0 = time.time()
    if provider == "openrouter":
        ok, model, err = await _test_openrouter(entry["key"])
    else:
        ok, model, err = await _test_gemini(entry["key"])
    latency_ms = int((time.time() - t0) * 1000)
    if ok:
        entry["last_ok"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if model:
            entry["model"] = model
    else:
        entry["last_err"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _secrets_save(vault)
    return {"ok": ok, "latency_ms": latency_ms, "model": model, "error": err}


@app.put("/api/settings/priority")
async def set_priority(req: PriorityRequest) -> dict[str, Any]:
    if not req.priority:
        raise HTTPException(status_code=400, detail="priority cannot be empty")
    bad = [p for p in req.priority if p not in VALID_PROVIDERS]
    if bad:
        raise HTTPException(status_code=400, detail=f"unknown providers: {bad}")
    vault = _bootstrap_vault_from_env()
    vault["priority"] = list(req.priority)
    _secrets_save(vault)
    return {"ok": True, "priority": vault["priority"]}


@app.post("/api/settings/rotate-all")
async def rotate_all_keys() -> dict[str, Any]:
    """Re-order keys within each provider so the freshest (highest last_ok)
    comes first. Within each provider: last_ok desc → never used at end.

    `priority` chain itself (openrouter/gemini/mock order) is left alone —
    only per-provider key order changes. UI calls this when user clicks
    'Rotuj wg last_ok' so a failing key doesn't keep being hit first.
    """
    vault = _bootstrap_vault_from_env()
    changed = 0
    for prov in ("openrouter", "gemini"):
        keys = vault[prov]
        if len(keys) <= 1:
            continue
        before = [k["alias"] for k in keys]
        # last_ok desc; never used (None) sink to the bottom
        keys.sort(
            key=lambda k: (
                0 if k.get("last_ok") and not k.get("last_err") else 1,
                -(int(time.mktime(time.strptime(k["last_ok"], "%Y-%m-%dT%H:%M:%SZ")))
                  if k.get("last_ok") else 0),
                k["alias"],
            )
        )
        if [k["alias"] for k in keys] != before:
            changed += 1
    if changed:
        _secrets_save(vault)
    return {
        "ok": True,
        "rotated_providers": changed,
        "note": "per-provider order updated; priority chain unchanged",
    }


async def _test_openrouter(api_key: str) -> tuple[bool, str | None, str | None]:
    import urllib.error
    import urllib.request
    def _do() -> dict[str, Any] | None:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    try:
        data = await asyncio.to_thread(_do)
        if data and isinstance(data.get("data"), list) and data["data"]:
            return True, "deepseek/deepseek-chat", None
        return False, None, "empty response"
    except Exception as e:
        return False, None, type(e).__name__


async def _test_gemini(api_key: str) -> tuple[bool, str | None, str | None]:
    import urllib.error
    import urllib.request
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "ping"}]}],
        "generationConfig": {"maxOutputTokens": 1},
    }
    body = json.dumps(payload).encode("utf-8")
    def _do() -> dict[str, Any] | None:
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    try:
        data = await asyncio.to_thread(_do)
        if data and data.get("candidates"):
            return True, "gemini-2.5-flash", None
        return False, None, "no candidates"
    except Exception as e:
        return False, None, type(e).__name__


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="BILLSzuka API server (FastAPI)")
    ap.add_argument("--host", default="0.0.0.0",
                    help="Bind address (default 0.0.0.0 = all interfaces; "
                         "use 127.0.0.1 for loopback-only)")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--reload", action="store_true", help="dev mode (auto-reload)")
    args = ap.parse_args()

    # FAQ/knowledge store — idempotent schema init.
    db.init()

    # Pre-flight: bootstrap the secrets vault from .env (idempotent).
    # Reads OPENROUTER_API_KEY + GEMINI_API_KEY_1..N; imports any that
    # aren't already in the vault. Settings drawer can add more later.
    vault = _bootstrap_vault_from_env()
    n_keys = len(vault.get("openrouter", [])) + len(vault.get("gemini", []))
    if n_keys:
        print(f"[init] Vault has {n_keys} key(s) "
              f"({len(vault.get('openrouter', []))} openrouter, "
              f"{len(vault.get('gemini', []))} gemini)", flush=True)
    else:
        print("[init] Vault empty — add keys in .env (OPENROUTER_API_KEY, "
              "GEMINI_API_KEY_1..N) or via the Settings drawer.", flush=True)

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
