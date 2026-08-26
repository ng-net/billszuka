#!/usr/bin/env python3
"""FAQ runtime helpers: query normalization, deterministic facts,
entity-guarded FAQ matching, save-command detection, staleness digests.
stdlib only — no pandas, plain csv.DictReader is enough for 417 rows.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import config
import db

DATA_DIR = config.DATA_DIR
MASTER_CSV = DATA_DIR / "master.csv"
FACTS_PATH = DATA_DIR / "faq-facts.json"
PHRASES_PATH = DATA_DIR / "knowledge" / "md" / "save-phrases.json"

# Columns whose values feed the facts hash (staleness) and the protected
# entity list (matching guard). NOTE: `status` is empty in master.csv —
# statuses live in `flagi` free text (FROZEN / DO-WERYFIKACJI / PENDING_API).
FACTS_COLUMNS = ["kraj", "tier", "wolumen", "kategoria"]

FLAG_NEEDLES = {
    "frozen": "frozen",
    "do-weryfikacji": "do weryfikacji",
    "pending_api": "pending api",
}

QUESTION_TOKENS = {
    "ile", "ilu", "jak", "jaki", "jaka", "jakie", "ktory", "ktora", "ktore",
    "kto", "co", "gdzie", "kiedy", "dlaczego", "czemu", "czy",
    "how", "what", "who", "where", "when", "why", "which",
}

# Measured on the eval gate (tests/test_faq.py::test_eval_gate). See
# Task 3 — the tune step writes the measured value here.
FAQ_FUZZY_THRESHOLD = 0.6


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    # Ł/ł have no NFKD decomposition — map explicitly or the regex below
    # would strip the character entirely ("Łódź" → "odz" instead of "lodz").
    text = text.replace("ł", "l")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    return normalize(text).split()


# ---------------------------------------------------------------------------
# Facts (deterministic ground truth)
# ---------------------------------------------------------------------------

def compute_facts(master_csv: Path = MASTER_CSV) -> dict:
    """Deterministic facts over master.csv. Statuses are substrings of
    `flagi`; counts keys keep original casing (PL, hurtownik, …)."""
    with open(master_csv, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    def counts(col: str) -> dict:
        out: dict = {}
        for r in rows:
            v = (r.get(col) or "").strip() or "—"
            out[v] = out.get(v, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    def pairs(c1: str, c2: str) -> dict:
        out: dict = {}
        for r in rows:
            k = ((r.get(c1) or "").strip() or "—", (r.get(c2) or "").strip() or "—")
            out[k] = out.get(k, 0) + 1
        return {f"{k}|{v}": n for (k, v), n in sorted(out.items(), key=lambda kv: -kv[1])}

    flags: dict = {k: 0 for k in FLAG_NEEDLES}
    flags_x_kraj: dict = {}
    for r in rows:
        f = normalize(r.get("flagi") or "")
        kraj = (r.get("kraj") or "").strip() or "—"
        for key, needle in FLAG_NEEDLES.items():
            if needle in f:
                flags[key] += 1
                k2 = f"{key}|{kraj}"
                flags_x_kraj[k2] = flags_x_kraj.get(k2, 0) + 1

    return {
        "rows": len(rows),
        "columns": {c: counts(c) for c in FACTS_COLUMNS},
        "tier_x_kraj": pairs("tier", "kraj"),
        "wolumen_x_kraj": pairs("wolumen", "kraj"),
        "flags": flags,
        "flags_x_kraj": flags_x_kraj,
    }


def facts_hash(facts: dict) -> str:
    payload = json.dumps(facts, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


_facts_cache: tuple[object, dict | None] = (None, None)


def load_facts(master_csv: Path = MASTER_CSV) -> dict:
    """Facts with an mtime cache — recomputed at most once per mtime per
    process (hashing 417 rows on every chat query would be wasteful)."""
    global _facts_cache
    key = master_csv.stat().st_mtime_ns if master_csv.exists() else None
    if _facts_cache[0] == key and _facts_cache[1] is not None:
        return _facts_cache[1]
    facts = compute_facts(master_csv)
    _facts_cache = (key, facts)
    return facts


# ---------------------------------------------------------------------------
# faq_meta helpers
# ---------------------------------------------------------------------------

def get_meta(key: str, default: str | None = None) -> str | None:
    with db.connect() as conn:
        row = conn.execute("SELECT value FROM faq_meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_meta(key: str, value: str) -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO faq_meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
