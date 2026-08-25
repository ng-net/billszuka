# Gills FAQ — Phase 1 (Backend Core) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the verified FAQ/anti-hallucination core: SQLite store, deterministic facts, entity-guarded matching, save-command detection, `.md` corpus injection, FAQ generation session (numeric ground truth + Gemini/OpenRouter judge), server-side auth, and the chat integration — all tested before any UI work.

**Architecture:** stdlib-only. `tools/db.py` (SQLite, WAL) holds all mutable state; `tools/faq.py` (normalize/facts/matching/save-command), `tools/md_corpus.py` (corpus + inbox), `tools/faq_build_session.py` (detached runner). `api_server.py` gains the FAQ-first chat path + endpoints. Phase 2 (frontend drawer) is a separate plan.

**Tech Stack:** Python 3.12 (FastAPI, pydantic, sqlite3 stdlib), pytest (existing `tests/` harness, `tools/` on sys.path via `tests/conftest.py`).

**Phases:** Phase 1 = this plan (backend core, Tasks 1–8). Phase 2 = frontend drawer, its own plan: `docs/superpowers/plans/2026-08-25-gills-faq-phase2-frontend.md`. **REST between phases** — see protocol below.

**Work hygiene — rest between tasks (anti-hallucination protocol):**
1. Never trust memory of file contents. Each task header lists exact paths — re-read the relevant range before editing.
2. Every task ends with a test run + commit. If output differs from "Expected:", stop and investigate before continuing.
3. **REST POINT after Task 5** (half of Phase 1): run the full suite, commit, re-read spec §6/§10/§11/§12 before continuing.
4. **REST POINT at the end of Phase 1**: run the full suite, do a live curl smoke check (FAQ hit + save command against the running dev server), commit, and STOP for user review. Phase 2 starts only after the user confirms.

---

## Scope and simplifications (deliberate, vs the spec)

- **No `tools/llm.py` extraction.** The session runner reuses `_call_gemini` / `_call_openrouter` / `_bootstrap_vault_from_env` by importing `api_server` directly (registering the app object is harmless; nothing binds a port). Zero refactor risk; existing `tests/test_api_server.py` stays green.
- **`data/knowledge/index.json` stays** as the Gemini-Files registry (its upload/refresh/delete mechanics are untouched). The new `knowledge_files` table only adds `uploaded_by` marking; the spec's "drop index.json" is deferred — it's a registry, not a counter, so it's not the concurrency risk.
- **No `POST /api/knowledge/md/save-fact` endpoint.** The chat command path does the save; the Phase-2 button will reuse `/api/chat` with the command phrase. One less surface to auth and test.
- **Status facts come from `flagi`, not `status`.** Verified live: `status` is empty for all 417 rows; FROZEN / DO-WERYFIKACJI / PENDING_API are substrings of `flagi` free text.
- **Eval set is generated programmatically** in the test (50 pos + 50 neg from a compact base list) — one source of truth, no 100-line fixture file to maintain by hand.
- **Corpus budget counts corpus only** (6000 tokens ≈ 24k chars). The histogram context is measured in Task 8 and the constant adjusted if needed — one number, one place (`md_corpus.CORPUS_CONTEXT_BUDGET_TOKENS`).
- **Lock claim happens in the API process.** `/api/faq/generate` calls `db.claim_session()` itself (atomic) → 409 on conflict, then launches the detached runner. The runner never re-claims; terminal runs claim for themselves and `--force` recovers a SIGKILL-stuck row.
- **Marking lives in `index.json` items** (`uploaded_by` set on upload). No `knowledge_files` table — one less table to keep in sync. The inbox table stays (dedupe needs `content_hash` UNIQUE).
- **No config.py changes.** The fuzzy threshold lives in `faq.py`; the judge model name lives in `faq_build_session.py`.

## File map

| File | Responsibility |
|---|---|
| `tools/db.py` (new) | SQLite connect/init, schema, single-flight claim |
| `tools/faq.py` (new) | normalize/tokenize, facts, entity-guarded matching, save-command detection, meta + digests |
| `tools/md_corpus.py` (new) | corpus load/inject, inbox save with dedupe, filename sanitization |
| `tools/faq_build_session.py` (new) | detached session runner: bank → answers → verify → upsert/rejects → artifacts |
| `tools/api_server.py` (modify) | chat flow (command → FAQ → corpus-grounded chain → log), `/api/faq*` endpoints, auth helper, upload marking |
| `tests/conftest.py` (modify) | autouse DB-isolation fixture (throwaway SQLite per test) |
| `data/knowledge/md/save-phrases.json` (new) | PL/EN save-command phrases |
| `data/billszuka.db` (generated) | SQLite store — add `data/billszuka.db*` to `.gitignore` |
| `tests/test_db.py`, `tests/test_faq.py`, `tests/test_md_corpus.py`, `tests/test_faq_api.py`, `tests/test_faq_session.py` (new) | backend tests |
| `tests/fixtures/master_fixture.csv` (new) | tiny deterministic dataset |

---

### Task 1: SQLite store — `tools/db.py`

**Files:**
- Create: `tools/db.py`
- Create: `tests/test_db.py`
- Modify: `tests/conftest.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write the failing test** — `tests/test_db.py`:

```python
"""Tests for tools/db.py — schema, atomic counters, single-flight claim."""
from __future__ import annotations

import sqlite3

import db


def _tmp_db(tmp_path):
    db.init(tmp_path / "t.db")
    return tmp_path / "t.db"


def test_init_creates_all_tables(tmp_path):
    db.init(tmp_path / "t.db")
    with db.connect(tmp_path / "t.db") as conn:
        names = {r["name"] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"faq_entries", "faq_meta", "faq_session", "chat_log",
            "knowledge_inbox", "faq_rejects"} <= names


def test_hits_increment_is_atomic(tmp_path):
    path = _tmp_db(tmp_path)
    with db.connect(path) as conn:
        conn.execute(
            "INSERT INTO faq_entries (id, q, a, category, sources, verified_kind, created_at, hits) "
            "VALUES ('e1', 'q', 'a', 'c', '[]', 'numeric', 'now', 0)")
    # two separate connections, interleaved increments — nothing lost
    with db.connect(path) as a, db.connect(path) as b:
        a.execute("UPDATE faq_entries SET hits = hits + 1 WHERE id='e1'")
        a.commit()
        b.execute("UPDATE faq_entries SET hits = hits + 1 WHERE id='e1'")
        b.commit()
    with db.connect(path) as conn:
        hits = conn.execute("SELECT hits FROM faq_entries WHERE id='e1'").fetchone()["hits"]
    assert hits == 2


def test_upsert_preserves_hits(tmp_path):
    path = _tmp_db(tmp_path)
    with db.connect(path) as conn:
        conn.execute(
            "INSERT INTO faq_entries (id, q, a, category, sources, verified_kind, created_at, hits) "
            "VALUES ('e1', 'q', 'a', 'c', '[]', 'numeric', 'now', 7)")
    with db.connect(path) as conn:
        conn.execute(
            "INSERT INTO faq_entries (id, q, a, category, sources, verified_kind, created_at, hits) "
            "VALUES ('e1', 'q2', 'a2', 'c', '[]', 'numeric', 'now2', 0) "
            "ON CONFLICT(id) DO UPDATE SET q=excluded.q, a=excluded.a")
    with db.connect(path) as conn:
        row = conn.execute("SELECT hits, q FROM faq_entries WHERE id='e1'").fetchone()
    assert row["hits"] == 7   # rebuild never clobbers hits
    assert row["q"] == "q2"


def test_rejects_are_unique(tmp_path):
    path = _tmp_db(tmp_path)
    with db.connect(path) as conn:
        conn.execute("INSERT INTO faq_rejects (q, q_norm, reason) VALUES ('a', 'a', 'judge')")
        with __import__("pytest").raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO faq_rejects (q, q_norm, reason) VALUES ('b', 'a', 'judge')")


def test_claim_session_single_flight(tmp_path):
    path = _tmp_db(tmp_path)
    assert db.claim_session(path) is True      # idle → running
    assert db.claim_session(path) is False     # running → nobody else
    assert db.claim_session(path, force=True) is True   # force recovers stuck
    with db.connect(path) as conn:
        conn.execute("UPDATE faq_session SET state='done' WHERE id=1")
    assert db.claim_session(path) is True      # done → running (re-run allowed)


def test_claim_session_resumes_interrupted(tmp_path):
    path = _tmp_db(tmp_path)
    with db.connect(path) as conn:
        conn.execute("UPDATE faq_session SET state='interrupted' WHERE id=1")
    assert db.claim_session(path) is True
```

- [ ] **Step 2: Run it — must fail:**

```bash
cd /Users/ciepolml/Documents/Bills-Drive/BILLSzuka-24-Aug && pytest tests/test_db.py -q
```

Expected: FAIL — `ModuleNotFoundError: No module named 'db'`.

- [ ] **Step 3: Implement** — `tools/db.py`:

```python
#!/usr/bin/env python3
"""SQLite store (stdlib) for FAQ entries, chat log, knowledge metadata,
rejects blocklist and the single-flight session row.

WAL + busy_timeout make the rare concurrent write safe; the session row
is claimed with an atomic UPDATE so only one generation session runs.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "billszuka.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS faq_entries (
  id TEXT PRIMARY KEY,
  q TEXT NOT NULL,
  a TEXT NOT NULL,
  category TEXT,
  sources TEXT NOT NULL DEFAULT '[]',
  ground_key TEXT,
  verified_kind TEXT NOT NULL,
  judge_model TEXT,
  verified_at TEXT,
  created_at TEXT NOT NULL,
  hits INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS faq_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS faq_session (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  state TEXT NOT NULL DEFAULT 'idle',
  mode TEXT,
  progress TEXT,
  report TEXT,
  checkpoint TEXT,
  updated_at TEXT
);
CREATE TABLE IF NOT EXISTS chat_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  user TEXT,
  query TEXT NOT NULL,
  response TEXT,
  provider TEXT,
  dataset TEXT,
  knowledge_ids TEXT,
  faq_hit INTEGER,
  sources TEXT
);
CREATE TABLE IF NOT EXISTS knowledge_inbox (
  file TEXT PRIMARY KEY,
  saved_by TEXT,
  question TEXT,
  content_hash TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending',
  saved_at TEXT
);
CREATE TABLE IF NOT EXISTS faq_rejects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  q TEXT NOT NULL,
  q_norm TEXT NOT NULL UNIQUE,
  reason TEXT,
  rejected_at TEXT
);
"""


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    # NOTE: default resolved at call time (not a bound default arg) so
    # tests can monkeypatch db.DB_PATH.
    path = Path(db_path) if db_path is not None else DB_PATH
    conn = sqlite3.connect(str(path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init(db_path: Path | str | None = None) -> None:
    with connect(db_path) as conn:
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT OR IGNORE INTO faq_session (id, state, updated_at) "
            "VALUES (1, 'idle', '')"
        )


def claim_session(db_path: Path | str | None = None, force: bool = False) -> bool:
    """Atomically claim the single-flight session row. True = we own it.
    Claimable from any state except 'running'; force recovers a stuck row
    (a SIGKILLed runner left state='running')."""
    where = "id=1" if force else "id=1 AND state != 'running'"
    with connect(db_path) as conn:
        cur = conn.execute(
            f"UPDATE faq_session SET state='running', updated_at=datetime('now') "
            f"WHERE {where}"
        )
        return cur.rowcount == 1
```

- [ ] **Step 4: Isolate the DB in ALL tests** — append to `tests/conftest.py` (every test then writes to a throwaway DB, never the repo's `data/billszuka.db`):

```python
import pytest


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Every test gets a throwaway SQLite store — never data/billszuka.db."""
    import db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "billszuka-test.db")
```

(`db.connect()` resolves `DB_PATH` at call time, so the monkeypatch is effective.)

- [ ] **Step 5: Add `data/billszuka.db*` to `.gitignore`** — append after the existing data ignores (one line, keep other entries untouched):

```
data/billszuka.db
data/billszuka.db-wal
data/billszuka.db-shm
```

- [ ] **Step 6: Run tests — must pass:**

```bash
pytest tests/test_db.py -q
```

Expected: PASS — 6 passed.

- [ ] **Step 7: Commit**

```bash
git add tools/db.py tests/test_db.py tests/conftest.py .gitignore
git commit -m "feat: sqlite store for FAQ, chat log, knowledge metadata and session lock"
```

---

### Task 2: Normalization + deterministic facts — `tools/faq.py` (part 1)

**Files:**
- Create: `tools/faq.py`
- Create: `tests/test_faq.py`
- Create: `tests/fixtures/master_fixture.csv`

- [ ] **Step 1: Write the failing test** — `tests/test_faq.py` (first block; later tasks append):

```python
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
```

- [ ] **Step 2: Create the fixture** — `tests/fixtures/master_fixture.csv` (columns matching real master.csv; `flagi` carries the statuses):

```csv
related_to,rok_zalozenia,id_unikalne,kategoria,nazwa_firmy,kraj,tier,wolumen,flagi
,2022,PL-A-001,A1,FIRMA ALFA,PL,hurtownik,duży,"2026-08-18 ✅ FROZEN (API)"
,2023,PL-B-001,B4,FIRMA BETA,PL,hurtownik,średni,"2026-08-18 ✅ FROZEN (API)"
,2021,PL-C-001,A2,FIRMA GAMMA,PL,reseller,mały,"2026-08-18 ⚠️ DO-WERYFIKACJI (API)"
,2020,CZ-A-001,B8,FIRMA DELTA,CZ,hurtownik,duży,"2026-08-18 ✅ FROZEN (API)"
,2019,CZ-B-001,B9,FIRMA EPSILON,CZ,producent,brak,"2026-08-18 ⏳ PENDING_API"
,2018,DE-A-001,A1,FIRMA ZETA,DE,hurtownik,brak,"🆕 NEW 2026-08-19"
```

- [ ] **Step 3: Run — must fail:** `pytest tests/test_faq.py -q` → `ModuleNotFoundError: No module named 'faq'`.

- [ ] **Step 4: Implement** — `tools/faq.py`:

```python
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
```

- [ ] **Step 5: Run — must pass:** `pytest tests/test_faq.py -q` → PASS.

- [ ] **Step 6: Commit**

```bash
git add tools/faq.py tests/test_faq.py tests/fixtures/master_fixture.csv
git commit -m "feat: faq normalization and deterministic facts over master.csv flagi"
```

---

### Task 3: Entity-guarded FAQ matching + eval gate

**Files:**
- Modify: `tools/faq.py` (append matching section)
- Modify: `tests/test_faq.py` (append tests)
- Modify: `tools/config.py` (constant — created in step 4 if tuning changes the value)

- [ ] **Step 1: Append failing tests** to `tests/test_faq.py`:

```python
# --- matching ---------------------------------------------------------------

ENTRIES = [
    {"id": "e1", "q": "Ile firm jest FROZEN w PL?", "a": "A1", "verified_kind": "numeric"},
    {"id": "e2", "q": "Ile firm jest FROZEN w CZ?", "a": "A2", "verified_kind": "numeric"},
    {"id": "e3", "q": "Rozkład tierów", "a": "A3", "verified_kind": "numeric"},
]

ENTS = frozenset({"pl", "cz", "de", "ee", "frozen", "do-weryfikacji",
                  "pending_api", "hurtownik", "reseller", "duży", "mały", "a1", "b4"})


def test_match_exact():
    assert faq.match_faq("Ile firm jest FROZEN w PL?", ENTRIES, ENTS)["id"] == "e1"


def test_match_paraphrase():
    # token overlap high, no entity conflict
    assert faq.match_faq("powiedz ile firm ma frozen w pl", ENTRIES, ENTS)["id"] == "e1"


def test_match_entity_guard_country_swap_is_miss():
    # one country token differs → hard miss (the PL/CZ trap)
    assert faq.match_faq("Ile firm jest FROZEN w CZ?", ENTRIES, ENTS)["id"] == "e2"
    assert faq.match_faq("Ile firm jest frozen w pl", ENTRIES, ENTS) is not None
    # a DE query must never resolve to the PL or CZ entry
    assert faq.match_faq("Ile firm jest FROZEN w DE?", ENTRIES, ENTS) is None


def test_match_entity_guard_one_sided_is_miss():
    # query carries a country, candidate doesn't (or vice versa) → miss
    assert faq.match_faq("Rozkład tierów w PL", ENTRIES, ENTS) is None
    assert faq.match_faq("Ile firm jest FROZEN?", ENTRIES, ENTS) is None


def test_match_unrelated_is_miss():
    assert faq.match_faq("jacy hurtownicy działają w niemczech", ENTRIES, ENTS) is None


# --- eval gate ---------------------------------------------------------------

# (base question, [paraphrases], [near-miss negatives])
EVAL_BASE = [
    ("ile firm jest frozen w pl",
     ["powiedz ile firm ma frozen w polsce", "podaj liczbę firm frozen z pl",
      "ile jest firm ze statusem frozen w kraju pl", "frozen w pl ile firm",
      "ile firm w polsce ma flagę frozen"],
     ["ile firm jest frozen w cz", "ile firm jest frozen w de", "ile firm jest frozen w ee",
      "ile firm jest frozen", "ile firm ma do-weryfikacji w pl",
      "ile firm jest frozen w pl i cz"]),
    ("rozklad tierow",
     ["jaki jest rozklad tierow", "podaj rozklad tierow w katalogu",
      "rozklad tierow prosze", "tier rozklad", "jak wyglada rozklad tierow"],
     ["rozklad tierow w pl", "rozklad tierow w cz", "rozklad wolumenu",
      "rozklad kategorii", "tier w pl rozklad"]),
    ("ile firm jest w pl",
     ["ile firm znajduje sie w polsce", "podaj liczbe firm z pl",
      "liczba firm w kraju pl", "ile mamy firm pl", "pl ile firm"],
     ["ile firm jest w cz", "ile firm jest w de", "ile firm jest",
      "ile hurtownikow jest w pl", "ile firm jest w pl i cz"]),
]


def _build_eval_set() -> list[tuple[str, str | None]]:
    """50 positives + 50 negatives (near-misses: country swaps, missing
    entities, extra entities, wrong column)."""
    pos: list[tuple[str, str | None]] = []
    neg: list[tuple[str, str | None]] = []
    for base, paras, nearmiss in EVAL_BASE:
        pos += [(p, base) for p in paras]
        neg += [(n, None) for n in nearmiss]
    # extra negatives built from entity swaps across bases
    for _ in range(50 - len(neg)):
        for base, _, _ in EVAL_BASE:
            swapped = base.replace("pl", "cz")
            if swapped != base and len(neg) < 50:
                neg.append((swapped, None))
    for _ in range(50 - len(pos)):
        for base, paras, _ in EVAL_BASE:
            if len(pos) < 50:
                pos.append((paras[0] + " ?", base))
    return pos + neg


def test_eval_gate_zero_false_accepts():
    """The shipped threshold must never accept a negative. Run
    `pytest tests/test_faq.py::test_eval_gate -q` after changing
    FAQ_FUZZY_THRESHOLD."""
    eval_rows = _build_eval_set()
    assert len(eval_rows) >= 100
    # every positive must map to its base entry; build entries from bases
    entries = [{"id": f"b{i}", "q": b, "a": "A", "verified_kind": "numeric"}
               for i, (b, _, _) in enumerate(EVAL_BASE)]
    false_accepts = []
    misses = []
    for q, expected in eval_rows:
        hit = faq.match_faq(q, entries, ENTS)
        if expected is None and hit is not None:
            false_accepts.append((q, hit["q"]))
        elif expected is not None and (hit is None or faq.normalize(hit["q"]) != expected):
            misses.append((q, expected, hit["q"] if hit else None))
    assert false_accepts == [], f"false accepts at {faq.FAQ_FUZZY_THRESHOLD}: {false_accepts}"
    assert len(misses) < len(eval_rows) // 2, f"too many misses: {misses}"


def test_tune_sweep_finds_working_threshold():
    """Sweep helper: highest threshold with zero false accepts. Used once
    to measure FAQ_FUZZY_THRESHOLD — then the constant is set and this
    documents the measurement."""
    import tools  # noqa: F401  (ensure module importable)
    eval_rows = _build_eval_set()
    entries = [{"id": f"b{i}", "q": b, "a": "A", "verified_kind": "numeric"}
               for i, (b, _, _) in enumerate(EVAL_BASE)]
    for t in [0.9, 0.8, 0.7, 0.65, 0.6, 0.55, 0.5]:
        faq.FAQ_FUZZY_THRESHOLD = t
        fa = [q for q, exp in eval_rows if exp is None and faq.match_faq(q, entries, ENTS)]
        hits = sum(1 for q, exp in eval_rows if exp is not None and faq.match_faq(q, entries, ENTS))
        if not fa:
            print(f"threshold {t}: 0 false accepts, {hits}/{sum(1 for _, e in eval_rows if e)} positives hit")
            break
    faq.FAQ_FUZZY_THRESHOLD = 0.6
```

- [ ] **Step 2: Run — must fail:** `pytest tests/test_faq.py -q` → `AttributeError: module 'faq' has no attribute 'match_faq'`.

- [ ] **Step 3: Implement** — append to `tools/faq.py`:

```python
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
    return {t for t in normalized.split() if t in ents}


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
```

- [ ] **Step 4: Run — must pass:**

```bash
pytest tests/test_faq.py -q
```

Expected: PASS. Also print the measured threshold and paste it into `tools/config.py` + the `FAQ_FUZZY_THRESHOLD` constant (only if the sweep in `test_tune_sweep_finds_working_threshold` output differs from 0.6):

```bash
pytest tests/test_faq.py::test_tune_sweep_finds_working_threshold -q -s
```

- [ ] **Step 5: Commit**

```bash
git add tools/faq.py tests/test_faq.py tools/config.py
git commit -m "feat: token-set FAQ matching with entity guard and eval gate"
```

---

### Task 4: Save-command detection + phrase dictionary

**Files:**
- Create: `data/knowledge/md/save-phrases.json`
- Modify: `tools/faq.py` (append `is_save_command` + `load_save_phrases`)
- Modify: `tests/test_faq.py` (append tests)

- [ ] **Step 1: Create the dictionary** — `data/knowledge/md/save-phrases.json`:

```json
{
  "pl": [
    "zapisz ten fakt",
    "zapisz to",
    "zapisz to zdanie",
    "zachowaj to",
    "zachowaj to zdanie",
    "zapamiętaj to",
    "zapisz odpowiedź",
    "zachowaj odpowiedź"
  ],
  "en": [
    "save this",
    "save this fact",
    "remember this",
    "save the answer",
    "save it"
  ]
}
```

- [ ] **Step 2: Append failing tests** to `tests/test_faq.py`:

```python
# --- save-command -----------------------------------------------------------

PHRASES = [
    "zapisz ten fakt", "zapisz to", "zapisz to zdanie", "zachowaj to",
    "zapamiętaj to", "zapisz odpowiedź", "save this", "save this fact",
    "remember this",
]


def test_save_command_basic():
    assert faq.is_save_command("zapisz ten fakt", True, PHRASES) == ""
    assert faq.is_save_command("Save this fact", True, PHRASES) == ""


def test_save_command_with_short_note():
    assert faq.is_save_command("zapisz to zdanie o rynku", True, PHRASES) == "o rynku"


def test_save_command_typo_tolerance():
    # "zamietaj" ≈ "zapamiętaj" (per-token difflib ≥ 0.9)
    assert faq.is_save_command("zamietaj to", True, PHRASES) == ""


def test_save_command_question_token_blocks():
    assert faq.is_save_command("zapisz ile firm jest w pl", True, PHRASES) is None
    assert faq.is_save_command("zapisz to jakie firmy", True, PHRASES) is None


def test_save_command_long_remainder_falls_through():
    # long tail = a question, not a command
    assert faq.is_save_command("zapisz to zdanie o rynku w polsce i niemczech", True, PHRASES) is None


def test_save_command_needs_last_answer():
    assert faq.is_save_command("zapisz ten fakt", False, PHRASES) is None


def test_save_command_plain_question_is_none():
    assert faq.is_save_command("ile firm jest frozen w pl", True, PHRASES) is None
```

- [ ] **Step 3: Run — must fail:** `pytest tests/test_faq.py -q` → `AttributeError: module 'faq' has no attribute 'is_save_command'`.

- [ ] **Step 4: Implement** — append to `tools/faq.py`:

```python
# ---------------------------------------------------------------------------
# Save-command detection ("zapisz ten fakt")
# ---------------------------------------------------------------------------

def load_save_phrases(path: Path = PHRASES_PATH) -> list[str]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [p for lang in data.values() for p in lang]


def is_save_command(query: str, has_last_answer: bool,
                    phrases: list[str] | None = None) -> str | None:
    """Return the note (remainder after the phrase) when `query` is a
    save-this-fact command, else None. All four conditions must hold:
    phrase token-prefix (typo-tolerant), no question token, a last answer
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
    for p in phrases:
        pn = normalize(p).split()
        if len(pn) > len(qt):
            continue
        if all(SequenceMatcher(None, qt[i], pn[i]).ratio() >= 0.9
               for i in range(len(pn))):
            remainder = qt[len(pn):]
            if len(remainder) > 4:
                return None
            return " ".join(remainder)
    return None
```

- [ ] **Step 5: Run — must pass:** `pytest tests/test_faq.py -q` → PASS.

- [ ] **Step 6: Commit**

```bash
git add tools/faq.py tests/test_faq.py data/knowledge/md/save-phrases.json
git commit -m "feat: save-this-fact command detection with PL/EN phrase dictionary"
```

---

### Task 5: Corpus load + injection + inbox — `tools/md_corpus.py`

**Files:**
- Create: `tools/md_corpus.py`
- Create: `tests/test_md_corpus.py`

- [ ] **Step 1: Write the failing test** — `tests/test_md_corpus.py`:

```python
"""Tests for tools/md_corpus.py — load, inject, inbox save, sanitization."""
from __future__ import annotations

import db
import md_corpus


def _setup(tmp_path, monkeypatch):
    corpus = tmp_path / "md"
    inbox = corpus / "inbox"
    corpus.mkdir(parents=True)
    (corpus / "01-a.md").write_text("treść pierwszego pliku", encoding="utf-8")
    (corpus / "02-b.md").write_text("treść drugiego", encoding="utf-8")
    monkeypatch.setattr(md_corpus, "CORPUS_DIR", corpus)
    monkeypatch.setattr(md_corpus, "INBOX_DIR", inbox)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    db.init()
    return corpus


def test_load_corpus_lists_md_files(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    names = [n for n, _ in md_corpus.load_corpus()]
    assert names == ["01-a.md", "02-b.md"]


def test_inject_corpus_labeled_blocks_and_budget(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    blocks = md_corpus.inject_corpus([])
    assert len(blocks) == 2
    assert blocks[0].startswith("[DOKUMENT: 01-a.md]")
    assert blocks[0].endswith("[/DOKUMENT]")
    # tiny budget → first file gets truncated with a note, second skipped
    blocks = md_corpus.inject_corpus([], budget_tokens=10)
    assert len(blocks) == 1
    assert "[obcięto" in blocks[0]


def test_inject_corpus_respects_reserved_chars(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    blocks = md_corpus.inject_corpus([], budget_tokens=100, reserved_chars=90_000)
    assert blocks == []


def test_sanitize_component_blocks_path_traversal():
    assert md_corpus.sanitize_component("../../etc/passwd") == "etc_passwd"
    assert md_corpus.sanitize_component("jaro!@#") == "jaro"
    assert md_corpus.sanitize_component("") == "doc"


def test_save_fact_to_inbox_with_dedupe(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    ok, msg = md_corpus.save_fact_to_inbox("fakt A", "pytanie?", ["master.csv"], "marceli")
    assert ok and "marceli" in msg
    ok2, msg2 = md_corpus.save_fact_to_inbox("fakt A", "pytanie?", ["master.csv"], "jaro")
    assert not ok2 and "już" in msg2
    # header carries provenance
    files = list(md_corpus.INBOX_DIR.glob("fact-*.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "saved_by: marceli" in text and "pytanie?" in text
```

- [ ] **Step 2: Run — must fail:** `pytest tests/test_md_corpus.py -q` → `ModuleNotFoundError: No module named 'md_corpus'`.

- [ ] **Step 3: Implement** — `tools/md_corpus.py`:

```python
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
    """User-derived filename part → [a-z0-9_-] only (path-traversal guard)."""
    return re.sub(r"[^a-z0-9_-]", "_", name.strip().lower())[:80] or "doc"


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
        if room <= len(header) + len(footer) + 120:
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
```

- [ ] **Step 4: Run — must pass:** `pytest tests/test_md_corpus.py -q` → PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/md_corpus.py tests/test_md_corpus.py
git commit -m "feat: md corpus loader with token budget and inbox fact saving"
```

---

### Task 6: Staleness digests (spec §10)

**Files:**
- Modify: `tools/md_corpus.py` (append `file_digest`)
- Modify: `tools/faq.py` (append digest helpers)
- Modify: `tests/test_md_corpus.py` (append tests)
- Modify: `tests/test_faq.py` (append tests)

- [ ] **Step 1: Write the failing tests** — append to `tests/test_md_corpus.py`:

```python
def test_file_digest_is_content_not_mtime(tmp_path, monkeypatch):
    import os

    _setup(tmp_path, monkeypatch)
    p = md_corpus.CORPUS_DIR / "01-a.md"
    d1 = md_corpus.file_digest("01-a.md")
    t = p.stat().st_mtime_ns
    os.utime(p, ns=(t, t + 1_000_000))     # touch only — bytes unchanged
    assert md_corpus.file_digest("01-a.md") == d1
    p.write_text("inna treść", encoding="utf-8")
    assert md_corpus.file_digest("01-a.md") != d1


def test_file_digest_missing_file(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    assert md_corpus.file_digest("nie-ma.md") == "missing"
```

Append to `tests/test_faq.py`:

```python
# --- staleness (§10) ---------------------------------------------------------
import json as _json

import db as _db
import md_corpus as _md


def _db_setup(tmp_path, monkeypatch):
    monkeypatch.setattr(_db, "DB_PATH", tmp_path / "t.db")
    _db.init()


def test_check_stale_master(tmp_path, monkeypatch):
    _db_setup(tmp_path, monkeypatch)
    copy = tmp_path / "master.csv"
    copy.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(faq, "MASTER_CSV", copy)
    monkeypatch.setattr(faq, "DATA_DIR", tmp_path)
    faq.set_meta("source_digests",
                 _json.dumps({"master.csv": faq.facts_hash(faq.compute_facts(copy))}))
    entry = {"sources": _json.dumps(["master.csv"])}
    assert faq.check_stale(entry) is False            # fresh
    copy.write_text(copy.read_text(encoding="utf-8") + "\n,2024,X, ,X,X, , ,",
                    encoding="utf-8")
    assert faq.check_stale(entry) is True             # bytes changed → stale


def test_check_stale_corpus_only_citing_entries(tmp_path, monkeypatch):
    import hashlib

    _db_setup(tmp_path, monkeypatch)
    corpus = tmp_path / "md"
    corpus.mkdir()
    (corpus / "01-a.md").write_text("v1", encoding="utf-8")
    (corpus / "02-b.md").write_text("v1", encoding="utf-8")
    monkeypatch.setattr(_md, "CORPUS_DIR", corpus)
    monkeypatch.setattr(_md, "INBOX_DIR", corpus / "inbox")
    monkeypatch.setattr(_md, "_cache", {})
    monkeypatch.setattr(faq, "DATA_DIR", tmp_path)
    faq.set_meta("source_digests", _json.dumps({
        "master.csv": "x",
        "01-a.md": hashlib.sha256(b"v1").hexdigest(),
        "02-b.md": hashlib.sha256(b"v1").hexdigest(),
    }))
    citing_a = {"sources": _json.dumps(["01-a.md"])}
    citing_b = {"sources": _json.dumps(["02-b.md"])}
    (corpus / "01-a.md").write_text("v2", encoding="utf-8")   # only a.md changes
    assert faq.check_stale(citing_a) is True
    assert faq.check_stale(citing_b) is False
```

- [ ] **Step 2: Run — must fail:**

```bash
pytest tests/test_md_corpus.py tests/test_faq.py -q
```

Expected: FAIL — `AttributeError: module 'md_corpus' has no attribute 'file_digest'` (or the equivalent for `check_stale`).

- [ ] **Step 3: Implement** — append to `tools/md_corpus.py`:

```python
_digest_cache: dict[str, tuple[int, str]] = {}


def file_digest(name: str) -> str:
    """sha256 of one corpus file's content, cached by mtime. mtime only
    avoids recomputation — the digest itself is the staleness signal."""
    path = CORPUS_DIR / name
    if not path.exists():
        return "missing"
    mtime = path.stat().st_mtime_ns
    cached = _digest_cache.get(name)
    if cached and cached[0] == mtime:
        return cached[1]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    _digest_cache[name] = (mtime, digest)
    return digest
```

Append to `tools/faq.py` (and add `import md_corpus` next to the existing `import db`):

```python
# ---------------------------------------------------------------------------
# Staleness — per-source digests (§10). Digests are the only staleness
# signal; mtime only caches digest computation (touch ≠ change, and a
# silent byte change must not go unnoticed).
# ---------------------------------------------------------------------------

def current_digest(source: str) -> str:
    """Digest of one cited source: 'master.csv' → facts_hash; anything
    else → md_corpus.file_digest (sha256 of the corpus .md content)."""
    if source == "master.csv":
        return facts_hash(load_facts())
    return md_corpus.file_digest(source)


def update_source_digests(sources: list[str]) -> None:
    """Snapshot digests of the session's sources into faq_meta (called by
    the session runner after a successful build)."""
    set_meta("source_digests", json.dumps({s: current_digest(s) for s in sources}))


def check_stale(entry: dict) -> bool:
    """True when any source cited by the entry differs from the snapshot
    in faq_meta.source_digests (or has no snapshot at all)."""
    raw = get_meta("source_digests")
    stored = json.loads(raw) if raw else {}
    sources = json.loads(entry.get("sources") or "[]")
    return any(current_digest(s) != stored.get(s) for s in sources)
```

- [ ] **Step 4: Run — must pass:**

```bash
pytest tests/test_md_corpus.py tests/test_faq.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/faq.py tools/md_corpus.py tests/test_faq.py tests/test_md_corpus.py
git commit -m "feat: per-source digest staleness for FAQ entries"
```

---

### Task 7: Session runner — `tools/faq_build_session.py`

**Files:**
- Create: `tools/faq_build_session.py`
- Create: `tests/test_faq_session.py`

**Design:** numeric questions are answered deterministically from the facts (`ground_key` dot-paths — zero LLM, correct by construction); qualitative questions go Gemini (answer) → judge (OpenRouter, fallback Gemini alt prompt), one retry, then `faq_rejects`. The runner reuses the battle-tested LLM callers by importing `api_server` (registering the app is harmless — nothing binds a port). Progress checkpoints live in the `faq_session` row; a crash leaves `state='interrupted'`.

- [ ] **Step 1: Write the failing test** — `tests/test_faq_session.py` (pure parts only — no network):

```python
"""Tests for tools/faq_build_session.py — bank, verdicts, artifacts, lock
(pure parts only; LLM callers are never invoked in tests)."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import db
import faq
import md_corpus
from faq_build_session import (
    build_numeric_bank,
    build_qual_bank,
    parse_judge,
    reject_question,
    render_numeric,
    rotate_backups,
    run_session,
    upsert_entry,
    write_artifacts,
)

FIXTURE = Path(__file__).parent / "fixtures" / "master_fixture.csv"


def _facts():
    return faq.compute_facts(FIXTURE)


def test_numeric_bank_expands_countries():
    bank = build_numeric_bank(_facts())
    keys = {b["ground_key"] for b in bank}
    assert {"rows", "columns.tier", "columns.kraj.PL", "columns.kraj.CZ",
            "flags_x_kraj.frozen|PL"} <= keys


def test_render_numeric_scalar_dict_missing():
    facts = _facts()
    assert render_numeric("rows", facts) == "6"
    assert render_numeric("columns.kraj.PL", facts) == "3"
    assert "hurtownik" in render_numeric("columns.tier", facts)
    assert render_numeric("nie.ma.takiej", facts) == "brak danych"


def test_parse_judge_verdicts():
    assert parse_judge("TAK, odpowiedź jest zgodna z danymi.") is True
    assert parse_judge("Nie.") is False
    assert parse_judge("Nie wiem, trudno ocenić.") is None
    assert parse_judge("Może być.") is None


def test_qual_bank_seeds_and_headings(tmp_path, monkeypatch):
    corpus = tmp_path / "md"
    corpus.mkdir()
    (corpus / "01-a.md").write_text(
        "## Rynek hurtowy w Polsce\ntekst\n### Duzi hurtownicy\n", encoding="utf-8")
    monkeypatch.setattr(md_corpus, "CORPUS_DIR", corpus)
    monkeypatch.setattr(md_corpus, "INBOX_DIR", corpus / "inbox")
    monkeypatch.setattr(md_corpus, "_cache", {})
    questions = build_qual_bank(None)
    assert "Rynek hurtowy w Polsce" in questions
    assert "Duzi hurtownicy" in questions
    assert any("weryfikacji" in q for q in questions)      # seeds present
    assert build_qual_bank("01-a.md") == ["Rynek hurtowy w Polsce", "Duzi hurtownicy"]


def test_rejects_and_upsert(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    db.init()
    reject_question("Ile firm w PL?", "judge rejected twice")
    reject_question("Ile firm w PL?", "again")             # UNIQUE — no crash
    upsert_entry({"id": "e1", "q": "Q?", "a": "A", "category": "c",
                  "sources": "[]", "ground_key": None, "verified_kind": "judge",
                  "judge_model": "x", "verified_at": "t", "created_at": "t"})
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM faq_rejects").fetchone()["n"] == 1
        assert conn.execute("SELECT hits FROM faq_entries WHERE id='e1'").fetchone()["hits"] == 0


def test_artifacts_and_backup_rotation(tmp_path, monkeypatch):
    import faq_build_session as fbs

    monkeypatch.setattr(fbs, "ARTIFACT_JSON", tmp_path / "faq.json")
    monkeypatch.setattr(fbs, "ARTIFACT_CSV", tmp_path / "faq.csv")
    entries = [{"id": "e1", "q": "Q?", "a": "A", "category": "c", "sources": "[]",
                "ground_key": None, "verified_kind": "numeric", "judge_model": None,
                "verified_at": "t"}]
    write_artifacts(entries)
    assert (tmp_path / "faq.json").exists() and (tmp_path / "faq.csv").exists()
    for _ in range(7):                            # 7 rebuilds → 5 backups kept
        write_artifacts(entries)
    assert len(list(tmp_path.glob("faq-*.json"))) == 5


def test_run_session_conflict_when_running(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    db.init()
    with db.connect() as conn:
        conn.execute("UPDATE faq_session SET state='running' WHERE id=1")
    assert asyncio.run(run_session("full", None, force=False)) == 3
```

- [ ] **Step 2: Run — must fail:**

```bash
pytest tests/test_faq_session.py -q
```

Expected: FAIL — `ModuleNotFoundError: No module named 'faq_build_session'`.

- [ ] **Step 3: Implement** — `tools/faq_build_session.py`:

```python
#!/usr/bin/env python3
"""Detached FAQ generation session.

Run directly:
  python3 tools/faq_build_session.py full
  python3 tools/faq_build_session.py full --force    (recover stuck session)
  python3 tools/faq_build_session.py doc 01-rynki.md

The API endpoint /api/faq/generate claims the single-flight lock itself
(db.claim_session → 409 on conflict) and then launches this process with
start_new_session=True, so an API restart never kills a running session.
A crash leaves state='interrupted'; `--force` allows re-claiming.

Numeric questions are answered deterministically from the facts via
`ground_key` dot-paths — zero LLM calls, correct by construction.
Qualitative: Gemini 3.6-flash answers, OpenRouter judges (TAK/NIE); judge
fallback = Gemini with an alternate prompt; one retry with a correction
hint, then the question lands in faq_rejects.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_server  # noqa: E402  (reuses the vault + battle-tested LLM callers)
import db          # noqa: E402
import faq         # noqa: E402
import md_corpus   # noqa: E402
from api_server import ChatRequest  # noqa: E402

ANSWERER = "gemini-3.6-flash"            # free tier
JUDGE_MODEL = "deepseek/deepseek-chat"   # via OpenRouter (same as api_server)
RETRY_LIMIT = 1
BACKUP_KEEP = 5

ARTIFACT_JSON = faq.DATA_DIR / "faq.json"
ARTIFACT_CSV = faq.DATA_DIR / "faq.csv"

QUALITATIVE_SEEDS = [
    "Jaka jest różnica między tierem hurtownik a reseller?",
    "Co oznacza status DO-WERYFIKACJI i co z nim zrobić?",
    "Jak wygląda proces weryfikacji firmy w BILLSzuka?",
    "Dlaczego firmy ze statusem FROZEN są najcenniejsze?",
    "Które kraje są priorytetem ekspansji i dlaczego?",
    "Jakie są typowe wolumeny u hurtowników tytoniowych?",
    "Co robić, gdy firma ma flagę PENDING_API?",
    "Jak BILLSzuka zbiera dane o firmach?",
]


# ---------------------------------------------------------------------------
# Question bank (pure — unit tested)
# ---------------------------------------------------------------------------

def build_numeric_bank(facts: dict) -> list[dict]:
    """Numeric templates expanded over the countries present in the data.
    ground_key is a dot-path into the facts (a value may contain '|')."""
    bank = [
        {"q": "Ile firm jest w katalogu?", "ground_key": "rows"},
        {"q": "Jaki jest rozkład tierów?", "ground_key": "columns.tier"},
        {"q": "Jaki jest rozkład wolumenów?", "ground_key": "columns.wolumen"},
        {"q": "Jaki jest rozkład kategorii?", "ground_key": "columns.kategoria"},
    ]
    for kraj in sorted(facts["columns"]["kraj"]):
        bank.append({"q": f"Ile firm jest w {kraj}?",
                     "ground_key": f"columns.kraj.{kraj}"})
        bank.append({"q": f"Ile firm FROZEN w {kraj}?",
                     "ground_key": f"flags_x_kraj.frozen|{kraj}"})
        bank.append({"q": f"Ile firm DO-WERYFIKACJI w {kraj}?",
                     "ground_key": f"flags_x_kraj.do-weryfikacji|{kraj}"})
    return bank


def render_numeric(ground_key: str, facts: dict) -> str:
    """Resolve a dot-path into facts and render text. Dicts render as
    'key: value' pairs; a missing key renders 'brak danych'."""
    node: object = facts
    try:
        for part in ground_key.split("."):
            node = node[part]  # type: ignore[index]
    except (KeyError, TypeError):
        return "brak danych"
    if isinstance(node, dict):
        return "; ".join(f"{k}: {v}" for k, v in node.items())
    return str(node)


def build_qual_bank(doc_file: str | None = None) -> list[str]:
    """Seeds + corpus document headings (doc mode = one file's headings)."""
    questions: list[str] = [] if doc_file else list(QUALITATIVE_SEEDS)
    for name, content in md_corpus.load_corpus():
        if doc_file and name != doc_file:
            continue
        for line in content.splitlines():
            m = re.match(r"^#{1,3}\s+(.+)$", line)
            if m and len(m.group(1).strip()) > 6:
                questions.append(m.group(1).strip())
    return questions


def parse_judge(text: str) -> bool | None:
    """Judge verdict → True / False / None (inconclusive)."""
    t = faq.normalize(text)[:120]
    if t.startswith("tak") or "odpowiedz zgodna" in t or "jest zgodna" in t:
        return True
    if t.startswith("nie") and "nie wiem" not in t[:40]:
        return False
    return None


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _entry_id(q: str) -> str:
    return hashlib.sha256(faq.normalize(q).encode("utf-8")).hexdigest()[:16]


def reject_question(q: str, reason: str) -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO faq_rejects (q, q_norm, reason, rejected_at) "
            "VALUES (?, ?, ?, datetime('now'))",
            (q, faq.normalize(q), reason),
        )


def upsert_entry(entry: dict) -> None:
    """Insert or refresh one entry — hits are NEVER touched (spec §Data store)."""
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO faq_entries (id, q, a, category, sources, ground_key, "
            " verified_kind, judge_model, verified_at, created_at, hits) "
            "VALUES (:id, :q, :a, :category, :sources, :ground_key, :verified_kind, "
            " :judge_model, :verified_at, :created_at, 0) "
            "ON CONFLICT(id) DO UPDATE SET q=excluded.q, a=excluded.a, "
            " category=excluded.category, sources=excluded.sources, "
            " ground_key=excluded.ground_key, verified_kind=excluded.verified_kind, "
            " judge_model=excluded.judge_model, verified_at=excluded.verified_at, "
            " created_at=excluded.created_at",
            entry,
        )


def rotate_backups(path: Path, keep: int = BACKUP_KEEP) -> None:
    """Move the existing artifact aside with a unique timestamp name and
    trim backups to the newest `keep`."""
    if not path.exists():
        return
    ns = path.stat().st_mtime_ns
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(ns // 10**9))
    backup = path.with_name(f"{path.stem}-{stamp}-{ns % 10**9:09d}{path.suffix}")
    path.replace(backup)
    for old in sorted(path.parent.glob(f"{path.stem}-*{path.suffix}"))[:-keep]:
        old.unlink()


def write_artifacts(entries: list[dict]) -> None:
    """Immutable session outputs — the runtime never rewrites these."""
    rotate_backups(ARTIFACT_JSON)
    rotate_backups(ARTIFACT_CSV)
    ARTIFACT_JSON.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    if entries:
        fields = ["id", "q", "a", "category", "sources", "verified_kind",
                  "judge_model", "verified_at"]
        with open(ARTIFACT_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for e in entries:
                w.writerow({k: e.get(k) for k in fields})


def _skip_rejects(questions: list[str]) -> list[str]:
    """Questions already on the blocklist are never re-generated."""
    with db.connect() as conn:
        blocked = {r["q_norm"] for r in conn.execute("SELECT q_norm FROM faq_rejects")}
    return [q for q in questions if faq.normalize(q) not in blocked]


# ---------------------------------------------------------------------------
# LLM part (async, reused callers from api_server)
# ---------------------------------------------------------------------------

def _facts_block(facts: dict) -> str:
    return "DANE Z KATALOGU (jedyny autorytet liczb):\n" + json.dumps(
        {"rows": facts["rows"], "columns": facts["columns"],
         "flags": facts["flags"], "flags_x_kraj": facts["flags_x_kraj"]},
        ensure_ascii=False)


async def answer_qualitative(q: str, facts: dict, corpus_blocks: list[str]) -> str:
    vault = api_server._bootstrap_vault_from_env()
    keys = [k for k in vault.get("gemini", []) if k.get("key")]
    if not keys:
        raise RuntimeError("no Gemini key in vault")
    context = _facts_block(facts) + "\n\n" + "\n\n".join(corpus_blocks)
    result = await api_server._call_gemini(ChatRequest(query=f"PYTANIE: {q}\n\n{context}"),
                                           keys[0]["key"])
    if not result:
        raise RuntimeError("gemini call failed")
    return result.response


async def judge_answer(q: str, answer: str, facts: dict,
                       corpus_blocks: list[str]) -> tuple[bool, str]:
    """(verdict, judge_model) — raises RuntimeError when no judge answers."""
    vault = api_server._bootstrap_vault_from_env()
    context = _facts_block(facts) + "\n\n" + "\n\n".join(corpus_blocks)
    prompt = (
        "Jesteś sędzią odpowiedzi. Oceń, czy ODPOWIEDŹ jest zgodna z DANYMI "
        "i KORPUSEM. Odpowiedz jednym słowem: TAK lub NIE.\n\n"
        f"PYTANIE: {q}\n\nODPOWIEDŹ: {answer}\n\n{context}"
    )
    for entry in [k for k in vault.get("openrouter", []) if k.get("key")]:
        result = await api_server._call_openrouter(ChatRequest(query=prompt), entry["key"])
        if result:
            verdict = parse_judge(result.response)
            if verdict is not None:
                return verdict, f"openrouter:{JUDGE_MODEL}"
    for entry in [k for k in vault.get("gemini", []) if k.get("key")]:
        alt = ("Odpowiedz TYLKO jednym słowem: TAK lub NIE. Czy odpowiedź "
               "jest zgodna z danymi?\n\n" + prompt)
        result = await api_server._call_gemini(ChatRequest(query=alt), entry["key"])
        if result:
            verdict = parse_judge(result.response)
            if verdict is not None:
                return verdict, f"gemini:{ANSWERER}"
    raise RuntimeError("no judge available")


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _make_entry(q: str, a: str, verified_kind: str, judge_model: str | None,
                sources: str, ground_key: str | None = None) -> dict:
    return {"id": _entry_id(q), "q": q, "a": a, "category": "dane katalogowe",
            "sources": sources, "ground_key": ground_key, "verified_kind": verified_kind,
            "judge_model": judge_model, "verified_at": _now(), "created_at": _now()}


async def run_session(mode: str, doc_file: str | None, force: bool) -> int:
    db.init()
    if not db.claim_session(force=force):
        print("SESSION_CONFLICT: inna sesja generowania już trwa")
        return 3
    try:
        facts = faq.load_facts()
        corpus_blocks = md_corpus.inject_corpus([])
        numeric = [] if mode == "doc" else build_numeric_bank(facts)
        qual = _skip_rejects(build_qual_bank(doc_file))
        total = len(numeric) + len(qual)
        done = 0

        def checkpoint():
            with db.connect() as conn:
                conn.execute(
                    "UPDATE faq_session SET progress=?, updated_at=datetime('now') WHERE id=1",
                    (f"{done}/{total}",))

        report = {"accepted": 0, "rejected": 0, "manual": 0, "numeric": len(numeric),
                  "verdicts": []}
        entries: list[dict] = []
        sources = json.dumps(["master.csv"], ensure_ascii=False)

        for item in numeric:
            entries.append(_make_entry(
                item["q"], render_numeric(item["ground_key"], facts),
                "numeric", None, sources, ground_key=item["ground_key"]))
            done += 1
            checkpoint()

        for q in qual:
            attempts = 0
            while True:
                try:
                    ask_q = q if attempts == 0 else (
                        q + " (sędzia odrzucił poprzednią odpowiedź jako "
                        "niezgodną z danymi — popraw ją)")
                    answer = await answer_qualitative(ask_q, facts, corpus_blocks)
                    ok, judge_model = await judge_answer(q, answer, facts, corpus_blocks)
                except RuntimeError:
                    ok, judge_model = None, None
                if ok is True:
                    entries.append(_make_entry(q, answer, "judge", judge_model, sources))
                    report["accepted"] += 1
                    report["verdicts"].append({"q": q, "verdict": "tak"})
                    break
                if ok is None:
                    entries.append(_make_entry(q, answer, "manual", None, sources))
                    report["manual"] += 1
                    report["verdicts"].append({"q": q, "verdict": "brak sędziego"})
                    break
                if attempts < RETRY_LIMIT:
                    attempts += 1
                    continue
                reject_question(q, "judge rejected twice")
                report["rejected"] += 1
                report["verdicts"].append({"q": q, "verdict": "nie"})
                break
            done += 1
            checkpoint()

        for e in entries:
            upsert_entry(e)
        faq.update_source_digests(["master.csv"] + [n for n, _ in md_corpus.load_corpus()])
        write_artifacts(entries)
        with db.connect() as conn:
            conn.execute(
                "UPDATE faq_session SET state='done', progress=?, report=?, "
                "updated_at=datetime('now') WHERE id=1",
                (f"{done}/{total}", json.dumps(report, ensure_ascii=False)))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:  # noqa: BLE001 — a crashed session must leave a marker
        try:
            with db.connect() as conn:
                conn.execute(
                    "UPDATE faq_session SET state='interrupted', "
                    "updated_at=datetime('now') WHERE id=1")
        except Exception:
            pass
        print(f"SESSION_INTERRUPTED: {e}")
        return 1


def main() -> int:
    p = argparse.ArgumentParser(description="FAQ generation session")
    p.add_argument("mode", choices=["full", "doc"])
    p.add_argument("doc_file", nargs="?", default=None,
                   help="corpus .md filename (doc mode)")
    p.add_argument("--force", action="store_true",
                   help="claim the session even if state='running'")
    args = p.parse_args()
    if args.mode == "doc" and not args.doc_file:
        p.error("doc mode requires a corpus file name (data/knowledge/md/<name>.md)")
    return asyncio.run(run_session(args.mode, args.doc_file, args.force))


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run — must pass:**

```bash
pytest tests/test_faq_session.py -q
```

Expected: PASS — 7 passed.

- [ ] **Step 5: Run the existing suite to prove nothing broke:**

```bash
pytest tests/test_db.py tests/test_faq.py tests/test_md_corpus.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tools/faq_build_session.py tests/test_faq_session.py
git commit -m "feat: detached FAQ generation session with numeric ground truth and judge"
```

---

### Task 8: API integration — `tools/api_server.py`

**Files:**
- Modify: `tools/api_server.py`
- Create: `tests/test_faq_api.py`

**Design:** chat becomes save-command → FAQ lookup → LLM chain, everything logged to `chat_log`. Mutating endpoints require the verified `X-Billszuka-User` header. `_call_gemini` gains the budgeted corpus injection. The DB is isolated in tests by the conftest autouse fixture (Task 1) — this file's fixture must NOT re-monkeypatch `db.DB_PATH` (it calls `db.init()` after the autouse fixture has already pointed it at a throwaway path).

- [ ] **Step 1: Write the failing tests** — `tests/test_faq_api.py`:

```python
"""API tests for the FAQ layer — chat integration, endpoints, auth."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api_server
import db
import faq
import md_corpus

FIXTURE = Path(__file__).parent / "fixtures" / "master_fixture.csv"


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(api_server, "ROOT", tmp_path)
    monkeypatch.setattr(api_server, "DATA", tmp_path)
    monkeypatch.setattr(api_server, "SECRETS_PATH", tmp_path / "api_secrets.json")
    monkeypatch.setattr(api_server, "KNOWLEDGE_DIR", tmp_path / "knowledge")
    monkeypatch.setattr(api_server, "KNOWLEDGE_FILES_DIR", tmp_path / "knowledge" / "files")
    monkeypatch.setattr(api_server, "KNOWLEDGE_INDEX_PATH", tmp_path / "knowledge" / "index.json")
    monkeypatch.setattr(faq, "MASTER_CSV", FIXTURE)
    monkeypatch.setattr(faq, "PHRASES_PATH", tmp_path / "save-phrases.json")
    monkeypatch.setattr(md_corpus, "CORPUS_DIR", tmp_path / "knowledge" / "md")
    monkeypatch.setattr(md_corpus, "INBOX_DIR", tmp_path / "knowledge" / "md" / "inbox")
    monkeypatch.setattr(md_corpus, "_cache", {})
    monkeypatch.setattr(api_server, "_chat_mock",
                        lambda req: api_server.ChatResponse(response="MOCK-ODP", provider="mock"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY_1", "")
    (tmp_path / "frontend-2" / "public").mkdir(parents=True)
    (tmp_path / "frontend-2" / "public" / "access.json").write_text(
        json.dumps({"names": [hashlib.sha256(b"marceli").hexdigest()]}), encoding="utf-8")
    (tmp_path / "save-phrases.json").write_text(
        json.dumps({"pl": ["zapisz ten fakt"], "en": ["save this"]}), encoding="utf-8")
    db.init()   # conftest autouse fixture already pointed DB_PATH at a throwaway file
    return TestClient(api_server.app)


def _headers(name="marceli"):
    return {"X-Billszuka-User": name}


def _seed_entry(entry_id="e1", q="Ile firm jest w katalogu?", a="SZEŚĆ",
                sources="[]", kind="numeric"):
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO faq_entries (id, q, a, category, sources, verified_kind, "
            "created_at, hits) VALUES (?, ?, ?, 'dane', ?, ?, 't', 0)",
            (entry_id, q, a, sources, kind))


def test_chat_miss_uses_chain_and_logs(client):
    r = client.post("/api/chat", json={"query": "co to jest maszynka do tytoniu"})
    assert r.status_code == 200 and r.json()["provider"] == "mock"
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM chat_log").fetchone()["n"] == 1


def test_chat_faq_hit_zero_llm(client):
    _seed_entry()
    r = client.post("/api/chat", json={"query": "ile firm jest w katalogu"})
    body = r.json()
    assert body["provider"] == "faq" and body["response"] == "SZEŚĆ"
    with db.connect() as conn:
        assert conn.execute("SELECT hits FROM faq_entries WHERE id='e1'").fetchone()["hits"] == 1


# Captured BEFORE the fixture monkeypatches _chat_mock, so the nudge-text
# regression test can verify the real default (regression: the old text
# blamed OPENROUTER_API_KEY while the quota note blamed Gemini — two
# contradictory explanations in one answer).
REAL_CHAT_MOCK = api_server._chat_mock


def test_mock_default_text_is_provider_agnostic(client, monkeypatch):
    monkeypatch.setattr(api_server, "_chat_mock", REAL_CHAT_MOCK)
    r = api_server._chat_mock(api_server.ChatRequest(
        query="opowiedz coś o projekcie", active_dataset="master.csv", knowledge_ids=[]))
    assert "OPENROUTER_API_KEY not configured" not in r.response
    assert "100 pytań do…" in r.response


def test_gemini_quota_note_is_coherent(client, tmp_path, monkeypatch):
    (tmp_path / "api_secrets.json").write_text(json.dumps({
        "priority": ["gemini", "mock", "openrouter"],
        "gemini": [{"key": "AIza-TEST"}],
        "openrouter": [],
    }), encoding="utf-8")

    async def no_gemini(req, key):
        return None

    monkeypatch.setattr(api_server, "_call_gemini", no_gemini)
    monkeypatch.setattr(api_server, "_last_call_was_quota", lambda: True)
    r = client.post("/api/chat", json={"query": "opowiedz coś o projekcie"})
    body = r.json()
    assert body["provider"] == "mock-gemini-quota"
    assert "OPENROUTER_API_KEY not configured" not in body["response"]
    assert "FAQ" in body["response"]


def test_chat_faq_stale_numeric_falls_through(client):
    _seed_entry(q="Ile firm jest w katalogu?", sources='["master.csv"]')
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO faq_meta (key, value) VALUES ('source_digests', '{\"master.csv\": \"stary\"}')")
    r = client.post("/api/chat", json={"query": "ile firm jest w katalogu"})
    assert r.json()["provider"] == "mock"          # fell through — no stale number served


def test_save_command_writes_inbox(client):
    client.post("/api/chat", json={"query": "co to jest maszynka"}, headers=_headers())
    r = client.post("/api/chat", json={"query": "zapisz ten fakt"}, headers=_headers())
    body = r.json()
    assert body["provider"] == "save" and "Zapisano" in body["response"]
    files = list(md_corpus.INBOX_DIR.glob("fact-*.md"))
    assert len(files) == 1
    assert "saved_by: marceli" in files[0].read_text(encoding="utf-8")


def test_save_command_without_last_answer_falls_through(client):
    r = client.post("/api/chat", json={"query": "zapisz ten fakt"}, headers=_headers())
    assert r.json()["provider"] != "save"


def test_generate_requires_user_and_locks(client, monkeypatch):
    calls = []
    monkeypatch.setattr(api_server.subprocess, "Popen",
                        lambda *a, **k: calls.append(a) or type("P", (), {"pid": 1})())
    assert client.post("/api/faq/generate", json={"mode": "full"}).status_code == 403
    assert client.post("/api/faq/generate", json={"mode": "full"},
                       headers={"X-Billszuka-User": "hacker"}).status_code == 403
    ok = client.post("/api/faq/generate", json={"mode": "full"}, headers=_headers())
    assert ok.status_code == 200 and ok.json()["state"] == "running"
    assert len(calls) == 1
    conflict = client.post("/api/faq/generate", json={"mode": "full"}, headers=_headers())
    assert conflict.status_code == 409


def test_delete_faq_verified_and_blocks(client):
    _seed_entry()
    assert client.delete("/api/faq/e1").status_code == 403
    assert client.delete("/api/faq/e1", headers=_headers()).status_code == 200
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM faq_entries").fetchone()["n"] == 0
        row = conn.execute("SELECT q_norm FROM faq_rejects").fetchone()
        assert row and row["q_norm"] == "ile firm jest w katalogu"


def test_faq_list_and_session(client):
    _seed_entry()
    r = client.get("/api/faq")
    assert r.status_code == 200
    assert r.json()["items"][0]["q"] == "Ile firm jest w katalogu?"
    assert client.get("/api/faq/session").json()["state"] in {"idle", "running", "done"}


def test_knowledge_upload_marks_uploaded_by(client, monkeypatch):
    monkeypatch.setattr(api_server, "_get_first_gemini_key", lambda: "fake-key")
    monkeypatch.setattr(api_server, "_gemini_files_upload",
                        lambda *a, **k: {"name": "files/x", "uri": "u", "state": "ACTIVE"})
    files = {"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")}
    assert client.post("/api/knowledge/upload", files=files).status_code == 403
    r = client.post("/api/knowledge/upload", files=files, headers=_headers())
    assert r.status_code == 200
    assert r.json()["uploaded_by"] == "marceli"
```

- [ ] **Step 2: Run — must fail:**

```bash
pytest tests/test_faq_api.py -q
```

Expected: FAIL — first failure is the chat-log assertion (`assert 0 == 1` in `test_chat_miss_uses_chain_and_logs`, because the current `/api/chat` does not log yet).

- [ ] **Step 3: Implement** — 9 exact edits to `tools/api_server.py`:

**(a) Stdlib imports** — replace:

```python
import argparse
import asyncio
import csv
import json
import os
import re
import sys
import time
```

with:

```python
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
```

**(b) FastAPI imports + sibling modules** — replace:

```python
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Sibling modules — same dir
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_run import regenerate_master  # noqa: E402
```

with:

```python
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Sibling modules — same dir
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_run import regenerate_master  # noqa: E402

import db         # noqa: E402  (SQLite store)
import faq        # noqa: E402  (FAQ matching/save-command/staleness)
import md_corpus  # noqa: E402  (permanent .md corpus + inbox)
```

**(c) Auth helpers** — after `VALID_PROVIDERS = {"openrouter", "gemini", "mock"}` insert:

```python
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
```

**(d) GenerateRequest model** — after the `PriorityRequest` class insert:

```python
class GenerateRequest(BaseModel):
    mode: str = "full"          # "full" | "doc"
    doc_id: str | None = None   # corpus .md filename for doc mode
```

**(e) Rewrite `/api/chat`** — replace the ENTIRE current handler (from `@app.post("/api/chat")` down to the line before `# ---------------------------------------------------------------------------\n# Chat: OpenRouter (real LLM) + Mock fallback`) with:

```python
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
                        "(widok „100 pytań do…"), żeby pytania o dane działały "
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
```

**(f) Corpus grounding in `_call_gemini`** — right after the `if refs:` block that ends with:

```python
        if refs:
            attached = ", ".join(r["filename"] or r["id"] for r in refs)
            system_text += (
                f"\n\nDo tej rozmowy dołączono {len(refs)} plik(ów) z bazy wiedzy: "
                f"{attached}. Możesz się na nich opierać przy odpowiedzi."
            )
```

insert:

```python
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
```

**(j) Mock fallback text — no provider blame** — the default nudge in `_chat_mock` currently claims `OPENROUTER_API_KEY not configured` even when the real reason is a Gemini quota hit; combined with the note above, the user gets two contradictory explanations. Replace its default return:

```python
    # Default: nudge the user
    return ChatResponse(
        response=(
            f"Mock AI (OPENROUTER_API_KEY not configured). Mam dostęp do {clean} "
            f"({total} wierszy). Spróbuj pytań typu: 'ile firm', 'rozkład wg kraj', "
            f"'status frozen'. Ustaw OPENROUTER_API_KEY w .env dla prawdziwego LLM."
        ),
        provider="mock",
    )
```

with:

```python
    # Default: nudge the user — provider-agnostic. The chat() fallback notes
    # explain WHY the mock answered; this text must not blame a specific key.
    return ChatResponse(
        response=(
            f"To odpowiedź deterministyczna z mocka (bez LLM). Mam dostęp do {clean} "
            f"({total} wierszy). Spróbuj pytań typu: 'ile firm', 'rozkład wg kraj', "
            f"'status frozen' — a dla pytań o dane bez tokenów wygeneruj sesję FAQ "
            f"(widok „100 pytań do…" w Gills)."
        ),
        provider="mock",
    )
```

**(g) FAQ endpoints** — insert right BEFORE `@app.get("/api/settings")`:

```python
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

```

**(h) Knowledge endpoints — auth + marking + inbox info.** Five precise edits:

1. `upload_knowledge` signature → add the header param:

```python
@app.post("/api/knowledge/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    x_billszuka_user: str | None = Header(None, alias="X-Billszuka-User"),
) -> dict[str, Any]:
```

and right after the `if not file.filename:` 400 check insert `user = _require_user(x_billszuka_user)` (403 before any Gemini work), then add `"uploaded_by": user,` to the `item` dict right after the `"uploaded_at"` line.

2. `delete_knowledge` — replace the signature and add the auth line:

```python
@app.delete("/api/knowledge/{file_id}")
async def delete_knowledge(
    file_id: str,
    x_billszuka_user: str | None = Header(None, alias="X-Billszuka-User"),
) -> dict[str, Any]:
    """Remove a file from the knowledge index and from Gemini Files API."""
    _require_user(x_billszuka_user)
    items = _read_knowledge_index()
```

3. `refresh_knowledge` — same pattern: add the header param to the signature and insert `_require_user(x_billszuka_user)` right before `items = _read_knowledge_index()`.

4. `list_knowledge` — replace the whole function with:

```python
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
```

**(i) `db.init()` at server start** — in `main()`, replace:

```python
    args = ap.parse_args()

    # Pre-flight: bootstrap the secrets vault from .env (idempotent).
```

with:

```python
    args = ap.parse_args()

    # FAQ/knowledge store — idempotent schema init.
    db.init()

    # Pre-flight: bootstrap the secrets vault from .env (idempotent).
```

- [ ] **Step 4: Run — must pass:**

```bash
pytest tests/test_faq_api.py -q
```

Expected: PASS — 9 passed.

- [ ] **Step 5: Full backend suite:**

```bash
pytest -q
```

Expected: PASS — all tests, including the untouched `tests/test_api_server.py` (the conftest autouse fixture keeps its chat tests off the real DB).

- [ ] **Step 6: Commit**

```bash
git add tools/api_server.py tests/test_faq_api.py
git commit -m "feat: FAQ-first chat flow, faq endpoints, server-side auth and upload marking"
```

---

## PHASE 1 END — REST POINT (mandatory stop)

- [ ] Run the full suite once more: `pytest -q` → all green.
- [ ] Live smoke check (dev server running: `python3 tools/api_server.py --port 8000`):
  - `curl -s localhost:8000/api/faq` → `{"items": [], ...}` (empty store is fine).
  - Terminal session: `python3 tools/faq_build_session.py full` → watch progress, expect numeric entries + qualitative verdicts; then `curl -s localhost:8000/api/faq` → entries present.
  - Chat FAQ hit: `curl -s -X POST localhost:8000/api/chat -H 'Content-Type: application/json' -d '{"query": "ile firm jest w katalogu"}'` → `provider: "faq"`, zero delay.
  - Save command: `curl -s -X POST localhost:8000/api/chat -H 'Content-Type: application/json' -H 'X-Billszuka-User: marceli' -d '{"query": "zapisz ten fakt"}'` → `provider: "save"`, inbox file written.
- [ ] Commit any remaining changes.
- [ ] **STOP and ask Marceli to review.** Do NOT start Phase 2 (`docs/superpowers/plans/2026-08-25-gills-faq-phase2-frontend.md`) until he confirms.


