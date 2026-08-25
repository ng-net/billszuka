# Gills FAQ + Knowledge Corpus Design

**Date:** 2026-08-25 (v2 — revised after security/robustness review)
**Status:** Approved design (pre-implementation)
**Owner:** Marceli (BILLSzuka)

## Goal

Make Gills (the chat bot in frontend-2) trustworthy and cheap: a permanent,
growing `.md` knowledge corpus grounded in chat with source citations, a
verified FAQ catalog served with zero tokens, chat answer persistence, a
"save this fact" command with verified username marking, and rich answer
formatting. A one-time batch session (deterministic numeric answers + Gemini
answers with an OpenRouter judge) builds the FAQ; runtime hits are free.

**Review revision (v2):** all mutable state moves into a SQLite database
(stdlib `sqlite3`, WAL mode). No lost updates, no torn reads, no whole-file
rewrites for hot counters. Matching is token-set based with an entity-token
guard and a measured threshold (not a guessed 0.85 char ratio). Numeric FAQ
answers are generated deterministically from ground truth (no LLM, no regex
verification). Mutating endpoints are authenticated server-side.

## Architecture

```
Runtime chat (POST /api/chat, auth: X-Billszuka-User header)
  1. Save-command check  → phrase dictionary (PL/EN), token-prefix +
     question-token guard → save last answer to inbox, zero tokens
  2. FAQ lookup (exact → token-set Jaccard ≥ measured threshold,
     entity-token guard, staleness check) → HIT: provider="faq", hits+1
     (SQL UPDATE), zero tokens
  3. MISS → existing chain (gemini → mock → openrouter), grounded with:
     - dataset context (master.csv histograms, already built)
     - data/knowledge/md/*.md corpus (labeled blocks, source citations)
  4. Every Q&A → chat_log table

FAQ build session (tools/faq_build_session.py, single-flight, on demand)
  1. Facts: pandas over master.csv → data/faq-facts.json (deterministic)
     + facts_hash (content hash of facts-relevant columns) in faq_meta
  2. Question bank (~100 full / ~15 per doc): templates + QUICK_PROMPTS
     + Gemini-generated variants, deduped by normalized key
  3. Numeric questions → answer computed directly from faq-facts.json
     (ground_key), no LLM, correct by construction
     Qualitative questions → Gemini 3.6-flash answer (context = facts +
     corpus, "NIE WIEM" rule) → OpenRouter judge votes agree/disagree
  4. Judge disagree → one retry with correction hint, then reject.
     Rejected answers never enter the DB — they appear in the report.
  5. Upsert entries into faq_entries (never touching hits); export
     data/faq.json + data/faq.csv artifacts with timestamped .bak
     rotation (keep last 5)
  6. Resumable via checkpoint in faq_session; one session at a time (409)
```

## Data store — SQLite (`data/billszuka.db`)

Single file, stdlib `sqlite3`, WAL mode, `busy_timeout=5000`. **Note:** this
project runs no Postgres; SQLite gives the same concurrency guarantees the
review demanded (real transactions, atomic counters) with zero new
infrastructure.

```sql
CREATE TABLE IF NOT EXISTS faq_entries (
  id TEXT PRIMARY KEY,
  q TEXT NOT NULL,
  a TEXT NOT NULL,                  -- answer in the markup contract (§9)
  category TEXT,
  sources TEXT NOT NULL DEFAULT '[]',   -- JSON array of source names
  ground_key TEXT,                  -- faq-facts.json key for numeric entries
  verified_kind TEXT NOT NULL,      -- 'numeric' | 'judge' | 'manual'
  judge_model TEXT,
  verified_at TEXT,
  created_at TEXT NOT NULL,
  hits INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS faq_meta (
  key TEXT PRIMARY KEY, value TEXT  -- facts_hash, generated_at, norm_version
);
CREATE TABLE IF NOT EXISTS faq_session (
  id INTEGER PRIMARY KEY CHECK (id = 1),   -- single-flight row
  state TEXT NOT NULL,             -- idle | running | paused | interrupted | done
  mode TEXT, progress TEXT, report TEXT, checkpoint TEXT, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS chat_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT, user TEXT, query TEXT, response TEXT, provider TEXT,
  dataset TEXT, knowledge_ids TEXT, faq_hit INTEGER, sources TEXT
);
CREATE TABLE IF NOT EXISTS knowledge_files (
  file TEXT PRIMARY KEY, title TEXT, uploaded_by TEXT, added_at TEXT,
  original_pdf TEXT
);
CREATE TABLE IF NOT EXISTS knowledge_inbox (
  file TEXT PRIMARY KEY, saved_by TEXT, question TEXT,
  content_hash TEXT UNIQUE, status TEXT, saved_at TEXT
);
```

Rules:
- `hits` increments only via `UPDATE faq_entries SET hits = hits + 1 WHERE id=?`.
- Session upserts via `INSERT … ON CONFLICT(id) DO UPDATE SET q=…, a=…, …`
  (hits excluded) — a rebuild can never clobber hit counts.
- The `.md` corpus files and inbox `.md` files stay on disk (human-authored,
  append-mostly); their metadata lives in the tables above. `index.json` is
  dropped entirely.
- Chat log is a table — no line-cap/rotation needed (retention can be added
  later by date).

## Files

**New:**
- `tools/db.py` — SQLite connection helper, schema init, migrations by `PRAGMA user_version`
- `tools/faq.py` — normalize, tokenize, facts computation, FAQ lookup (Jaccard + entity guard), save-command detection
- `tools/faq_build_session.py` — generation session: question bank, numeric ground-truth answers, LLM answers + judge, report, checkpoint
- `tools/md_corpus.py` — corpus load (mtime cache), context injection, inbox save, DB metadata sync
- `data/knowledge/md/` — permanent corpus (reviewed `.md` files)
- `data/knowledge/md/save-phrases.json` — PL/EN save-command phrases
- `data/knowledge/md/inbox/` — saved facts awaiting review (`.md` files)
- `data/billszuka.db` — SQLite store (gitignored)
- `data/faq.json`, `data/faq.csv` — exported artifacts after each session (+ timestamped `.bak`, keep last 5)
- `data/faq-facts.json` — pandas ground-truth facts
- `frontend-2/src/components/AnswerMarkup.jsx` — safe answer renderer
- `frontend-2/src/components/FaqView.jsx` — FAQ view inside the Gills drawer
- `tests/test_faq.py`, `tests/test_db.py`, `tests/test_md_corpus.py`, `tests/fixtures/faq_eval.jsonl`, `frontend-2/src/components/AnswerMarkup.test.js`

**Modified:**
- `tools/api_server.py` — /api/chat flow (command, FAQ, corpus, log), /api/faq endpoints, upload marking, session runner, server-side auth for mutating endpoints
- `tools/config.py` — FAQ constants (measured threshold, judge model, context budget, question tokens)
- `frontend-2/src/components/GeminiDrawer.jsx` — view switching chat↔FAQ, save button, AnswerMarkup rendering
- `frontend-2/src/components/KnowledgeDrawer.jsx` — marking badges, extraction offer after upload, inbox pending-count badge
- `frontend-2/src/lib/access.js` + `AccessGate.jsx` — persist signed-in name (session marker) + expose it to API calls
- `frontend-2/src/App.jsx` — pass user name to drawers

## 1. Permanent knowledge corpus — `data/knowledge/md/`

- Each PDF becomes its **own reviewed, cleaned `.md`** with a meaningful name,
  e.g. `01-rynek-hurtowy-polska.md`. Never one merged file.
- Marceli drops PDFs in chat → the agent reviews and transforms them.
- Backend injects each file as a labeled block:

```
[DOKUMENT: 01-rynek-hurtowy-polska.md]
<content>
[/DOKUMENT]
```

- System prompt: cite sources as `(źródło: <file>)` whenever content from a
  document is used. FAQ entries store `sources` (JSON array).
- **Context cap (token-based, not char-based):** corpus budget =
  `CORPUS_CONTEXT_BUDGET_TOKENS` (default 6000 tokens, estimate 4 chars/token,
  configurable in `tools/config.py`), applied **after** the dataset-histogram
  context. Per-file truncation with `[obcięto — pełne źródło w pliku X]`.
  Phase 1 includes a task to measure real histogram token usage and adjust
  the constant; tests assert the cap holds.
- Corpus files cached with mtime check; metadata in `knowledge_files` table.

## 2. Facts extraction — deterministic ground truth

`compute_facts()` (pandas over `master.csv`) → `data/faq-facts.json`:
row count, per-kraj counts, tier counts, wolumen counts, status counts
(FROZEN / DO-WERYFIKACJI / …), brand-presence counts, top-10 kraj,
tier×kraj matrix, wolumen×kraj matrix. Zero LLM.

`facts_hash` = SHA-256 over the canonical serialization of the
facts-relevant columns only (`FACTS_COLUMNS` constant), stored in
`faq_meta`. This is the staleness source of truth (§10).

## 3. FAQ generation session

- Entry points: (a) terminal `python3 tools/faq_build_session.py full`,
  (b) UI "Generuj" button in FAQ view, (c) doc-scoped extraction offered
  after every document upload.
- Modes: `full` (~100 questions) / `doc` (~15 questions from one document).
- **Single-flight:** the `faq_session` row is the lock. `POST /api/faq/generate`
  returns **409 Conflict** if `state` is `running` (double-click, two users).
  `GET /api/faq/session` reflects live state.
- **Lifecycle:** the runner is an in-process `threading.Thread` started by the
  API server. On restart it dies; the checkpoint row leaves `state =
  "interrupted"` and the UI offers "Wznów" (resume from checkpoint). This is
  stated behavior, not an accident.
- **Numeric questions:** each numeric template carries a `ground_key` into
  `faq-facts.json`; the answer is computed and rendered by template — no LLM,
  no free-text digit extraction, no false-accept/false-reject ambiguity.
  `verified_kind = "numeric"`.
- **Qualitative questions:** Gemini 3.6-flash answers (context = facts +
  corpus) → OpenRouter judge with the same context votes TAK/NIE.
  `judge_model` recorded. One retry with correction hint, then reject.
- Models: answerer = Gemini 3.6-flash (free tier); judge = OpenRouter
  (`FAQ_JUDGE_MODEL` in `tools/config.py`). If OpenRouter is unavailable (no
  keys / no balance) → judge falls back to Gemini with an alternate judge
  prompt; `judge_model` records which ran.
- Report: accepted / rejected / failed + per-entry verdicts, in UI and
  terminal. After success: export `data/faq.json` + `data/faq.csv` artifacts
  and rotate timestamped backups (keep last 5).

## 4. Runtime FAQ matching — token-set, measured, entity-guarded

1. `normalize(q)`: casefold, strip diacritics (unicodedata), remove
   punctuation, collapse whitespace. `tokenize()`: split on whitespace.
   `q_norm` is **not stored** — computed on load via the single normalizer
   (`NORM_VERSION` in `faq_meta`; bumping it invalidates any tuning state).
2. Exact match on normalized string → hit.
3. Fuzzy: **Jaccard on token sets** — `|A∩B| / |A∪B| ≥ FAQ_FUZZY_THRESHOLD`.
   Threshold is **measured**, not guessed: swept on the eval set (below),
   chosen as the highest value with zero false accepts; stored in
   `tools/config.py` with a comment pointing at the eval run.
4. **Entity-token guard (hard miss):** `PROTECTED_ENTITIES` is built from the
   dataset (kraj codes, tier values, status values, wolumen values). If a
   protected token appears in either the query or the candidate and the two
   protected-token sets differ → force miss, regardless of similarity.
   Example: "ile firm frozen w pl" vs "ile firm frozen w cz" → PL ≠ CZ → miss.
5. HIT → respond `provider: "faq"`, `hits+1` (SQL), write chat log. Zero LLM
   calls. Staleness check first (§10).
6. MISS → normal chain + corpus grounding.

**Eval set** `tests/fixtures/faq_eval.jsonl`: 50 paraphrase positives + 50
near-miss negatives (PL/CZ swaps, tier swaps, status swaps, partial overlap).
A regression test enforces **zero false accepts on the negative set** for the
shipped threshold; a tuning script (`tools/faq_tune.py`) sweeps thresholds
and prints the selected value with recall.

## 5. Chat log — `chat_log` table

One row per Q&A: `{ts, user, query, response, provider, dataset,
knowledge_ids, faq_hit, sources}`. Inserts are transactional; no rotation
logic. Write failure is non-fatal (logged to stderr). Raw material for
future FAQ expansion sessions.

## 6. Authentication + marking — server-side, verified

- The access gate stays hash-only client-side. New: after successful name
  verification the frontend persists the entered name
  (`billszuka.access.name.v1`, lowercase) and sends it as `X-Billszuka-User`
  on every API call.
- **Mutating endpoints require verified auth server-side:**
  `POST /api/faq/generate`, `DELETE /api/faq/{id}`,
  `POST /api/knowledge/upload`, `DELETE /api/knowledge/{id}`,
  `POST /api/knowledge/{id}/refresh`, `POST /api/knowledge/md/save-fact`.
  The server reads `public/access.json` and verifies
  `sha256(trim+lower(name))` against the name hashes → otherwise 403.
  GET endpoints stay open (local tool). A self-declared name can no longer
  spoof marking, delete entries, or burn generation money.
- Marking uses the **verified** name → `uploaded_by` / `saved_by`. Badge in
  the knowledge list: `marceli` / `jaro` / `—`.
- **Path sanitation:** any user-derived filename component is normalized to
  `re.sub(r"[^a-z0-9_-]", "_", name.lower())` before touching the filesystem
  (path-traversal guard on inbox/corpus writes).

## 7. "Save this fact" command

- Triggers: natural-language command or a small "Zapisz do wiedzy" button on
  each answer bubble. Same action, zero tokens.
- Phrase dictionary `data/knowledge/md/save-phrases.json` (editable):

```json
{
  "pl": ["zapisz ten fakt", "zapisz to", "zapisz to zdanie", "zachowaj to",
         "zachowaj to zdanie", "zapamiętaj to", "zapisz odpowiedź", "zachowaj odpowiedź"],
  "en": ["save this", "save this fact", "remember this", "save the answer", "save it"]
}
```

- **Detection (disambiguated, not just "starts with"):** all three must hold —
  1. query tokens start with a phrase's tokens (per-token difflib ≥ 0.9
     tolerance, so "zamietaj" matches "zapamiętaj"),
  2. the query contains **no question token** (`QUESTION_TOKENS` constant:
     ile, jak, jaki, która, kto, co, gdzie, kiedy, dlaczego, czy / how, what,
     who, where, when, why, which),
  3. a last assistant answer exists (otherwise reply "nie ma jeszcze
     odpowiedzi do zapisania", zero tokens).
  Tokens after the phrase become the note. Checked before FAQ lookup and
  before any LLM call.
- Effect: last assistant answer → `data/knowledge/md/inbox/fact-{ts}-{user}.md`
  (sanitized `user`) with a provenance header (fact text, original question,
  sources, `saved_by`, timestamp). Dedupe by content hash —
  `knowledge_inbox.content_hash UNIQUE`, second save of the same fact is
  rejected with "już zapisano".
- Reply: `Zapisano fakt do skrzynki wiedzy (marceli) — do przeglądu ✓`.
  The agent reviews and promotes inbox facts into the corpus; the knowledge
  drawer shows a **pending count badge** on the Baza wiedzy button.

## 8. FAQ view in the Gills drawer

- GeminiDrawer gains two internal views: `chat` and `faq`.
- Small button at the bottom of the drawer: `100 pytań do…` (BookOpen icon) →
  slides the FAQ view in (AnimatePresence slide-x) — same active drawer.
- FAQ view: search/filter input, entries grouped by category, expandable
  answers rendered with AnswerMarkup, verification badges (`✓ dane` /
  `✓ sędzia`), hit counters, staleness banner, `Generuj` button (409-safe),
  per-entry delete.
- After any document upload (KnowledgeDrawer): toast
  `Wygenerować pytania z tego dokumentu?` → doc-scoped extraction.
- Session progress via `GET /api/faq/session` polling.

## 9. Answer markup — formatting contract + hardened renderer

Gills emits a light markup (no external markdown lib; custom renderer). The
system prompt instructs this contract:

| Intent | Markup |
|---|---|
| Heading | `## Title` |
| Bold | `**text**` |
| Bullet list | `- item` (nested via two-space indent) |
| Numbered list | `1. item` |
| Link | `[text](https://…)` |
| Fact box | fenced block ``` ```fakt … ``` ``` |
| Errata/warning | fenced block ``` ```errata … ``` ``` |
| Columns (2–4) | fenced block ``` ```cols … ``` ``` (one item per line) |

Renderer `AnswerMarkup.jsx` — this is the **XSS boundary for untrusted LLM
output**; its tests are security tests:
- Builds React elements only — **never `dangerouslySetInnerHTML`**.
- Links: the destination is trimmed and decoded, then the scheme must match
  `^https?://` after lowercasing. Everything else — `javascript:`,
  `data:`, `vbscript:`, scheme disguised with whitespace/entities — renders
  as plain text. Only `href` is ever emitted, with `target="_blank"
  rel="noopener noreferrer"`, highlighted style.
- Bullets: small indentation (`ml-1`), tight spacing; numbered lists styled
  with counters.
- `fakt` → emerald/amber callout box with icon + "FAKT" label; `errata` →
  red/orange callout with icon.
- `cols` → responsive grid: 2 items → 2 cols, 3 → 3, 4+ → 4 capped
  (`grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4`), each item a card.
- **Parser limits:** max nesting depth 6, max 500 blocks per answer, cols
  capped at 4 — malformed fences or adversarial nesting degrade to plain
  text, never crash, never loop.
- Long descriptive answers: heading + body paragraphs with vertical gaps.

## 10. Staleness — content hash, not mtime

- `faq_meta.facts_hash` = SHA-256 of the canonical serialization of
  `FACTS_COLUMNS` rows (sorted). Catching a touch or a silent byte change is
  both wrong and dangerous — hash is the only signal used.
- Runtime: on FAQ hit, `os.stat(master.csv)` mtime is checked first; if
  unchanged since the last in-process hash computation, the cached verdict
  is reused (hash is computed at most once per mtime per process). If
  changed → recompute hash.
- Hash mismatch:
  - **numeric entries → not served**; fall through to the live chain
    (fresh data, correct numbers), log `faq_hit="stale-skip"`.
  - qualitative entries → served with
    `⚠️ Dane mogły się zmienić od wygenerowania FAQ — odśwież sesję FAQ.`
- The FAQ view shows the same staleness banner.

## 11. API endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/chat` | name header (log only) | save-command → FAQ lookup → chain → log |
| GET | `/api/faq` | open | entries + categories + hits + staleness |
| POST | `/api/faq/generate` | **verified** | `{mode: "full" \| "doc", doc_id?}`; 409 if running |
| GET | `/api/faq/session` | open | `{state, progress, report}` |
| DELETE | `/api/faq/{id}` | **verified** | remove a bad entry |
| POST | `/api/knowledge/upload` | **verified** | stamps `uploaded_by` from verified name |
| GET | `/api/knowledge` | open | files + corpus + inbox with markings |
| DELETE | `/api/knowledge/{id}` | **verified** | remove a file |
| POST | `/api/knowledge/{id}/refresh` | **verified** | re-upload to Gemini Files API |
| POST | `/api/knowledge/md/save-fact` | **verified** | `{content, question, sources}` → inbox file |

## 12. Error handling

- DB unavailable/corrupt → skip FAQ layer + log warning, normal chain.
- Session crash → checkpoint in `faq_session`, state `interrupted`, resume.
- Gemini quota during session → `paused:quota`, resumable.
- Judge API failure → entry `verified_kind="manual"`, listed for review.
- Log/inbox write failure → non-fatal.
- Renderer: unknown markup → plain text; non-http links → text; parse
  limits degrade safely.

## 13. Testing plan

- `tests/test_db.py` — schema init/migration; **concurrency**: hits increment
  during a simulated rebuild preserves counts; two concurrent upserts don't
  lose entries; WAL busy handling.
- `tests/test_faq.py` — normalization (diacritics/case); exact hit;
  **near-miss negatives (PL vs CZ, tier/status swaps) → forced miss**;
  paraphrase hits; **eval-set gate: zero false accepts on the 50 negatives
  at the shipped threshold**; facts computation on fixture CSV; staleness
  hash behavior (touch ≠ change, change → numeric skip).
- `tests/test_md_corpus.py` — corpus load/truncation (token budget), injection
  format; inbox save + dedupe; filename sanitization (path traversal input).
- API tests (pytest) — FAQ hit returns `provider="faq"` with zero LLM calls;
  **save-command vs question disambiguation**; **403 on mutating endpoints
  without/with bad `X-Billszuka-User`**; 409 on second `generate`;
  upload marking from verified name.
- `frontend-2/src/components/AnswerMarkup.test.js` (node --test) —
  **adversarial markup: `javascript:` variants (case/whitespace/entity),
  `data:`, malformed fences, deeply nested lists, link attribute injection**
  → renders as text or degrades, never emits non-http href, never
  `dangerouslySetInnerHTML`.
- Update `access.test.js` — name persistence marker.

## 14. Token economics

- Runtime FAQ hits: 0 tokens forever; save-command: 0 tokens.
- Session: ~100 questions ≈ 60 numeric (0 LLM calls) + 40 qualitative
  (40 Gemini free-tier + 40 OpenRouter judge calls, a few cents).
  Doc-scoped: ~15 questions ≈ ~8 judge calls.
- Corpus grounding: bounded by `CORPUS_CONTEXT_BUDGET_TOKENS` (free tier).

## 15. Implementation sequencing

- **Phase 1 — backend core (no UI polish):** `tools/db.py`, `tools/faq.py`
  (normalize/facts/matching/eval), `tools/md_corpus.py`,
  `tools/faq_build_session.py` (single-flight, checkpoint, numeric
  ground-truth answers, judge), server-side auth, endpoints, and all backend
  tests including concurrency/adversarial/auth cases. Ship the FAQ/verify
  core first; the drawer UI waits.
- **Phase 2 — frontend:** AnswerMarkup (+ security tests), FaqView,
  GeminiDrawer view switch + save button, KnowledgeDrawer badges +
  extraction offer + pending count, access-gate name persistence.

## Out of scope (v2 candidates)

- Embeddings/vector search for corpus relevance ranking
- FAQ export to PDF (CSV/JSON artifacts ship in v1)
- Thumbs up/down feedback loop
- Per-user chat history restore in UI (log exists, viewer later)
- Chat-log retention policy by date
