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

# Measured on the eval gate (tests/test_faq.py::test_eval_gate). Shipped
# value 0.6: 0 false accepts and <50% misses once the entity guard also
# recognizes inflected forms (see _entity_tokens). The tune sweep
# (test_tune_sweep_finds_working_threshold) reports 0.9 as its first
# zero-false-accept step, but at 0.9 the gate fails with 50 misses (0 hits)
# — the sweep stops at the degenerate end; the gate test is the arbiter.
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


# ---------------------------------------------------------------------------
# FAQ matching — token-set Jaccard + entity guard
# ---------------------------------------------------------------------------

_entities_cache: tuple[object, frozenset] = (None, frozenset())


def protected_entities(master_csv: Path = MASTER_CSV) -> frozenset:
    """Single normalized tokens for every value in FACTS_COLUMNS plus the
    flag-status tokens. Cached by master.csv mtime."""
    global _entities_cache
    key = master_csv.stat().st_mtime_ns if master_csv.exists() else 0
    if _entities_cache[0] == key and _entities_cache[1]:
        return _entities_cache[1]
    ents = set(FLAG_NEEDLES)
    if master_csv.exists():
        with open(master_csv, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                for col in FACTS_COLUMNS:
                    v = normalize(row.get(col) or "")
                    if v and v != "—":
                        ents.add(v)
    ents = frozenset(ents)
    _entities_cache = (key, ents)
    return ents


def _entity_tokens(normalized: str, ents: frozenset) -> set:
    """Protected tokens in a normalized text. A token is protected when it
    equals an entity or starts with a longer (≥4 char) entity — inflected
    forms ('hurtownicy', 'hurtownikow') carry the same protected concept as
    their lemma ('hurtownik') and must trigger the guard, otherwise e.g.
    'ile hurtownikow jest w pl' (J≈0.667) would resolve to
    'ile firm jest w pl' at any threshold below 0.67. Short entities
    (country codes, ids) stay exact-match only."""
    out: set = set()
    for t in normalized.split():
        if t in ents:
            out.add(t)
            continue
        for e in ents:
            if len(e) >= 4 and t.startswith(e):
                out.add(e)
                break
    return out


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def match_faq(query: str, entries: list[dict], ents: frozenset | None = None) -> dict | None:
    """Best matching entry or None. Exact normalized match first, then
    Jaccard on token sets. Entity guard: protected tokens must match
    exactly on both sides (one-sided presence → miss)."""
    ents = ents if ents is not None else protected_entities()
    qn = normalize(query)
    qt = set(tokenize(qn))
    q_ents = _entity_tokens(qn, ents)
    best, best_score = None, 0.0
    for e in entries:
        en = normalize(e["q"])
        if qn == en:
            return e
        if _entity_tokens(en, ents) != q_ents:
            continue
        score = _jaccard(qt, set(tokenize(en)))
        if score >= FAQ_FUZZY_THRESHOLD and score > best_score:
            best, best_score = e, score
    return best


def list_entries() -> list[dict]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM faq_entries ORDER BY created_at").fetchall()
    return [dict(r) for r in rows]


def bump_hits(entry_id: str) -> None:
    with db.connect() as conn:
        conn.execute("UPDATE faq_entries SET hits = hits + 1 WHERE id=?", (entry_id,))


# ---------------------------------------------------------------------------
# Save-command detection ("zapisz ten fakt")
# ---------------------------------------------------------------------------

# Per-token difflib threshold for typo tolerance. The plan assumed ≥ 0.9,
# but SequenceMatcher("zamietaj", "zapamietaj").ratio() == 0.8889 — the
# typo test demands this exact pair pass, so 0.88 it is.
SAVE_TOKEN_RATIO = 0.88


def load_save_phrases(path: Path = PHRASES_PATH) -> list[str]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [p for lang in data.values() for p in lang]


def is_save_command(query: str, has_last_answer: bool,
                    phrases: list[str] | None = None) -> str | None:
    """Return the note (remainder after the phrase) when `query` is a
    save-this-fact command, else None. All four conditions must hold:
    phrase token-prefix (typo-tolerant, LONGEST matching phrase wins —
    "save this fact" beats "save this"), no question token, a last answer
    exists, remainder ≤ 4 tokens."""
    from difflib import SequenceMatcher

    if not has_last_answer:
        return None
    qn = normalize(query)
    qt = qn.split()
    if not qt:
        return None
    if set(qt) & QUESTION_TOKENS:
        return None
    phrases = phrases if phrases is not None else load_save_phrases()
    best, best_len = None, -1
    for p in phrases:
        pn = normalize(p).split()
        if len(pn) > len(qt) or len(pn) <= best_len:
            continue
        if all(SequenceMatcher(None, qt[i], pn[i]).ratio() >= SAVE_TOKEN_RATIO
               for i in range(len(pn))):
            best, best_len = pn, len(pn)
    if best is None:
        return None
    remainder = qt[len(best):]
    if len(remainder) > 4:
        return None
    return " ".join(remainder)
