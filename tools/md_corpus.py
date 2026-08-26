#!/usr/bin/env python3
"""Permanent .md knowledge corpus: load (mtime-cached), inject labeled
blocks into prompts within a token budget, and save facts into the inbox
with provenance + content-hash dedupe. stdlib only."""
from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from pathlib import Path

import config
import db

CORPUS_DIR = config.DATA_DIR / "knowledge" / "md"
INBOX_DIR = CORPUS_DIR / "inbox"
CORPUS_CONTEXT_BUDGET_TOKENS = 6000
CHARS_PER_TOKEN = 4

_cache: dict[str, tuple[float, str]] = {}


def sanitize_component(name: str) -> str:
    """User-derived filename part → [a-z0-9_-] only (path-traversal guard).
    Leading/trailing illegal chars are STRIPPED and internal runs collapse
    to a single '_' — a per-char substitution would keep '../../' as a
    '_' prefix ('../../etc/passwd' → '______etc_passwd', which still
    looks like a traversal path and fails the spec test)."""
    s = name.strip().lower()
    s = re.sub(r"^[^a-z0-9_-]+", "", s)
    s = re.sub(r"[^a-z0-9_-]+$", "", s)
    s = re.sub(r"[^a-z0-9_-]+", "_", s)
    return s[:80] or "doc"


def load_corpus() -> list[tuple[str, str]]:
    """[(filename, content)] for *.md in CORPUS_DIR, mtime-cached."""
    out: list[tuple[str, str]] = []
    if not CORPUS_DIR.is_dir():
        return out
    for p in sorted(CORPUS_DIR.glob("*.md")):
        mtime = p.stat().st_mtime
        cached = _cache.get(str(p))
        if cached and cached[0] == mtime:
            content = cached[1]
        else:
            content = p.read_text(encoding="utf-8")
            _cache[str(p)] = (mtime, content)
        out.append((p.name, content))
    return out


def inject_corpus(existing_blocks: list[str],
                  budget_tokens: int = CORPUS_CONTEXT_BUDGET_TOKENS,
                  reserved_chars: int = 0) -> list[str]:
    """Append [DOKUMENT: …] blocks to existing_blocks within the budget.
    reserved_chars = chars already eaten by other context (histograms)."""
    budget_chars = budget_tokens * CHARS_PER_TOKEN
    used = sum(len(b) for b in existing_blocks) + reserved_chars
    blocks = list(existing_blocks)
    for name, content in load_corpus():
        header, footer = f"[DOKUMENT: {name}]", "[/DOKUMENT]"
        room = budget_chars - used
        # Include as long as header+footer fit. The plan sketched a +120
        # slack here, but the spec test demands the first file IS included
        # (truncated) at a 10-token budget (40 chars) — any larger slack
        # skips it entirely and the budget test fails.
        if room <= len(header) + len(footer):
            continue
        limit = room - len(header) - len(footer)
        if len(content) > limit:
            keep = max(limit - 60, 40)
            body = content[-keep:] + f"\n[obcięto — pełne źródło w pliku {name}]"
        else:
            body = content
        blocks.append(f"{header}\n{body}\n{footer}")
        used += len(blocks[-1])
    return blocks


def save_fact_to_inbox(content: str, question: str, sources: list[str],
                       user: str) -> tuple[bool, str]:
    """Write a fact .md into the inbox with a provenance header. Dedupe by
    content hash (knowledge_inbox.content_hash UNIQUE). Returns (ok, msg)."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    safe_user = sanitize_component(user)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO knowledge_inbox (file, saved_by, question, content_hash, status, saved_at) "
                "VALUES ('', ?, ?, ?, 'pending', ?)",
                (user or "—", question, digest, now),
            )
    except sqlite3.IntegrityError:
        return False, "Ten fakt jest już zapisany w skrzynce wiedzy."
    ts = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    fname = f"fact-{ts}-{safe_user}.md"
    header = (
        "# Fakt zapisany z czatu\n\n"
        f"- saved_by: {user or '—'}\n"
        f"- question: {question}\n"
        f"- sources: {', '.join(sources) or '—'}\n"
        f"- saved_at: {now}\n\n"
    )
    (INBOX_DIR / fname).write_text(header + content + "\n", encoding="utf-8")
    with db.connect() as conn:
        conn.execute(
            "UPDATE knowledge_inbox SET file=? WHERE content_hash=?",
            (fname, digest),
        )
    return True, f"Zapisano fakt do skrzynki wiedzy ({user or '—'}) — do przeglądu ✓"
