# Gills FAQ + Knowledge Corpus Design

**Date:** 2026-08-25
**Status:** Approved design (pre-implementation)
**Owner:** Marceli (BILLSzuka)

## Goal

Make Gills (the chat bot in frontend-2) trustworthy and cheap: a permanent,
growing `.md` knowledge corpus grounded in chat with source citations, a
verified FAQ catalog served with zero tokens, chat answer persistence, a
"save this fact" command with automatic username marking, and rich answer
formatting. A one-time batch session (Gemini answers, pandas + OpenRouter
judge verification) builds the FAQ; runtime hits are free forever.

## Architecture

```
Runtime chat (POST /api/chat)
  1. Save-command check  → "zapisz ten fakt" etc. (phrase dictionary, fuzzy)
                            → save last answer to inbox, zero tokens
  2. FAQ lookup (normalized exact → fuzzy ≥ 0.85)
     HIT  → serve from data/faq.json, provider="faq", hits+1, zero tokens
  3. MISS → existing chain (gemini → mock → openrouter), grounded with:
     - dataset context (master.csv histograms, already built)
     - data/knowledge/md/*.md corpus (labeled blocks, source citations)
  4. Every Q&A → data/chat-log.jsonl (append-only)

FAQ build session (tools/faq_build_session.py, on demand)
  1. Facts: pandas over master.csv → data/faq-facts.json (deterministic)
  2. Question bank (~100 full / ~15 per doc): templates + QUICK_PROMPTS
     + Gemini-generated variants, deduped by normalized key
  3. Answer: Gemini 3.6-flash (context = facts + corpus, "NIE WIEM" rule)
  4. Verify (hybrid):
     - numeric/aggregate → numbers compared against pandas ground truth
     - qualitative → OpenRouter judge votes agree/disagree
     - disagree/wrong → one retry with correction hint, then reject
  5. Verified pairs → data/faq.json (atomic write), report for review
  6. Resumable via checkpoint (data/faq-session.json)
```

## Files

**New:**
- `tools/faq.py` — normalize, FAQ load/match, facts computation, phrase dictionary, save-command detection
- `tools/faq_build_session.py` — generation session: question bank, answer, verify, report, checkpoint
- `tools/md_corpus.py` — corpus load (mtime cache), context injection, inbox save, index.json
- `data/knowledge/md/` — permanent corpus (reviewed `.md` files)
- `data/knowledge/md/index.json` — corpus + inbox metadata (markings)
- `data/knowledge/md/save-phrases.json` — PL/EN save-command phrases
- `data/knowledge/md/inbox/` — saved facts awaiting review
- `data/faq.json` — verified FAQ catalog
- `data/faq-facts.json` — pandas ground-truth facts
- `data/faq-session.json` — session state/checkpoint
- `data/chat-log.jsonl` — all chat Q&A (append-only, cap 5000 lines, rotate to `.bak`)
- `frontend-2/src/components/AnswerMarkup.jsx` — safe answer renderer
- `frontend-2/src/components/FaqView.jsx` — FAQ view inside the Gills drawer
- `tests/test_faq.py`, `tests/test_md_corpus.py`, `frontend-2/src/components/AnswerMarkup.test.js`

**Modified:**
- `tools/api_server.py` — /api/chat flow (command, FAQ, corpus, log), /api/faq endpoints, upload marking, session runner
- `tools/config.py` — FAQ constants (thresholds, judge model, context cap)
- `frontend-2/src/components/GeminiDrawer.jsx` — view switching chat↔FAQ, save button, AnswerMarkup rendering
- `frontend-2/src/components/KnowledgeDrawer.jsx` — marking badges, extraction offer after upload
- `frontend-2/src/lib/access.js` + `AccessGate.jsx` — persist signed-in name (session marker)
- `frontend-2/src/App.jsx` — pass user name to drawers

## 1. Permanent knowledge corpus — `data/knowledge/md/`

- Each PDF becomes its **own reviewed, cleaned `.md`** with a meaningful name,
  e.g. `01-rynek-hurtowy-polska.md`, `02-narracja-leady-b2b.md`. Never one merged file.
- Marceli drops PDFs in chat → the agent reviews and transforms them.
- Backend injects each file as a labeled block:

```
[DOKUMENT: 01-rynek-hurtowy-polska.md]
<content>
[/DOKUMENT]
```

- System prompt: cite sources as `(źródło: <file>)` whenever content from a
  document is used. FAQ entries store `sources: [<file>, "master.csv"]`.
- **Context cap:** total injected corpus ≤ 30,000 chars (per-file truncation
  with `[obcięto — pełne źródło w pliku X]` note). Corpus files cached with
  mtime check.
- `index.json` schema:

```json
{
  "files": [
    {"file": "01-rynek-hurtowy-polska.md", "title": "Rynek hurtowy w Polsce",
     "uploaded_by": "marceli", "added_at": "2026-08-25T…", "original_pdf": "00-Rynek_Hurtowy….pdf"}
  ],
  "inbox": [
    {"file": "fact-20260825T1010-marceli.md", "saved_by": "marceli",
     "question": "…", "status": "pending", "saved_at": "2026-08-25T…"}
  ]
}
```

## 2. Facts extraction — deterministic ground truth

`compute_facts()` (pandas over `master.csv`) → `data/faq-facts.json`:
row count, per-kraj counts, tier counts, wolumen counts, status counts
(FROZEN / DO-WERYFIKACJI / …), brand-presence counts, top-10 kraj,
tier×kraj matrix, wolumen×kraj matrix. Zero LLM. This is what numeric
answers are verified against.

## 3. FAQ generation session

- Entry points: (a) terminal `python3 tools/faq_build_session.py full`,
  (b) UI "Generuj" button in FAQ view, (c) doc-scoped extraction offered
  after every document upload (Baza wiedzy drawer or corpus add).
- Modes: `full` (~100 questions) / `doc` (~15 questions from one document).
- Models: answerer = Gemini 3.6-flash (free tier); judge = OpenRouter cheap
  model (`FAQ_JUDGE_MODEL` in `tools/config.py`, default the existing
  deepseek config). Cross-provider diversity.
- Verification: numeric answers have all numbers extracted (regex) and
  compared against `faq-facts.json`; qualitative answers go to the judge
  with the same context and a TAK/NIE verdict. One retry with correction
  hint per failure, then reject. Rejected answers never enter `faq.json` —
  they appear in the report as "needs manual review".
- Report: accepted / rejected / failed counts + per-entry verdicts, shown
  in UI and printed to terminal. Checkpoint file allows resume after
  network failure or Gemini quota pause (state `paused:quota`).

`data/faq.json` schema:

```json
{
  "version": 1,
  "generated_at": "2026-08-25T…",
  "master_mtime": "2026-08-25T…",
  "entries": [
    {
      "id": "faq-0001",
      "q": "Ile firm jest FROZEN w PL?",
      "q_norm": "ile firm jest frozen w pl",
      "a": "## FROZEN w PL\n…",
      "category": "status",
      "sources": ["master.csv"],
      "verified": {"numeric": true, "judge": null, "at": "…"},
      "hits": 3,
      "created_at": "…"
    }
  ]
}
```

## 4. Runtime FAQ layer in `/api/chat`

1. Normalize query: lowercase, strip diacritics, punctuation, collapse spaces.
2. Exact key hit (`q_norm`) → fuzzy (`difflib.SequenceMatcher` ratio ≥ 0.85).
3. HIT → respond `provider: "faq"`, increment `hits`, write chat log.
   **Zero LLM calls.**
4. Staleness: if `master.csv` mtime > `generated_at`, append
   `⚠️ Dane mogły się zmienić od wygenerowania FAQ — odśwież sesję FAQ.`
5. MISS → normal chain + corpus grounding.

## 5. Chat log — `data/chat-log.jsonl`

One JSON per line: `{ts, user, query, response, provider, dataset, knowledge_ids, faq_hit, sources}`.
Append-only, cap 5000 lines then rotate to `.bak`. Write failure is non-fatal
(logged to stderr). Raw material for future FAQ expansion sessions.

## 6. Marking system — automatic username

- AccessGate already verifies name against the hash allow-list. New: after
  successful name verification, persist the entered name locally
  (`billszuka.access.name.v1`, lowercase). The allow-list itself stays
  hash-only; the stored name is a session marker only.
- Frontend sends the name with `/api/chat` and `/api/knowledge/upload`
  (JSON field / form field). Backend stamps:
  - uploads → `uploaded_by` in knowledge index
  - saved facts → `saved_by` in inbox entry
- Knowledge list shows badges: `marceli` / `jaro` / `—`.

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

- Detection: normalized query **starts with** any normalized phrase, fuzzy
  tolerance ≥ 0.85 (typos like "zamietaj" match "zapamiętaj"). Checked
  before FAQ lookup and before any LLM call.
- Effect: last assistant answer → `data/knowledge/md/inbox/fact-{ts}-{user}.md`
  with a provenance header (fact text, original question, sources, `saved_by`,
  timestamp). Dedupe by content hash (no duplicate inbox entries).
- Reply: `Zapisano fakt do skrzynki wiedzy (marceli) — do przeglądu ✓`.
  The agent reviews and promotes inbox facts into the proper corpus `.md`.

## 8. FAQ view in the Gills drawer

- GeminiDrawer gains two internal views: `chat` and `faq`.
- Small button at the bottom of the drawer: `100 pytań do…` (BookOpen icon) →
  slides the FAQ view in (AnimatePresence slide-x) — same active drawer.
- FAQ view: search/filter input, entries grouped by category, expandable
  answers rendered with AnswerMarkup, verification badges
  (`✓ dane` / `✓ sędzia`), hit counters, staleness banner, `Generuj` button,
  per-entry delete.
- After any document upload (KnowledgeDrawer): toast
  `Wygenerować pytania z tego dokumentu?` → doc-scoped extraction.
- Session progress shown via `GET /api/faq/session` polling.

## 9. Answer markup — formatting contract + safe renderer

Gills emits a light markup (no external markdown lib; renderer is custom and
safe). System prompt instructs this contract:

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

Renderer `AnswerMarkup.jsx` rules:
- Builds React elements only — **never `dangerouslySetInnerHTML`** (LLM output
  is untrusted).
- Links: only `http/https` become anchors; always `target="_blank"
  rel="noopener noreferrer"`, highlighted style.
- Bullets: small indentation (`ml-1`), tight spacing; numbered lists styled
  with counters.
- `fakt` → emerald/amber callout box with icon + "FAKT" label; `errata` →
  red/orange callout with icon.
- `cols` → responsive grid: 2 items → 2 cols, 3 → 3, 4+ → 4 capped
  (`grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4`), each item a card.
- Long descriptive answers: heading + body paragraphs with vertical gaps.
- Unknown markup → plain text paragraph (never crash).

## 10. API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/chat` | + `user` field; save-command check → FAQ lookup → chain → log |
| GET | `/api/faq` | list entries + categories + hits + staleness |
| POST | `/api/faq/generate` | `{mode: "full" \| "doc", doc_id?}` → starts background session |
| GET | `/api/faq/session` | `{state, progress, report}` |
| DELETE | `/api/faq/{id}` | remove a bad entry |
| POST | `/api/knowledge/upload` | + `user` field → `uploaded_by` |
| GET | `/api/knowledge` | + corpus files + inbox list with markings |
| POST | `/api/knowledge/md/save-fact` | `{content, question, sources, user}` → inbox file |

## 11. Error handling

- `faq.json` missing/corrupt → skip layer, log warning, normal chain.
- Session crash → resume from checkpoint; Gemini quota → `paused:quota`.
- Judge API failure → entry marked unverified, listed for manual review.
- Chat-log/inbox write failure → non-fatal.
- Renderer: unknown markup → plain text; non-http links → text.

## 12. Testing plan

- `tests/test_faq.py` — normalization (diacritics/case), exact hit, paraphrase
  hit (≥0.85), non-hit, typo tolerance; facts on fixture CSV; faq.json schema
  validation; staleness detection.
- `tests/test_md_corpus.py` — corpus load/truncate/injection format; inbox
  save + dedupe; index.json round-trip.
- API tests (pytest, `tests/` style) — `/api/chat` FAQ hit returns
  `provider=faq` with zero LLM calls; save-command path; upload marking.
- `frontend-2/src/components/AnswerMarkup.test.js` (node --test) — lists,
  callouts, cols grid, links `target="_blank"`, no `dangerouslySetInnerHTML`.
- Update `access.test.js` — name persistence marker.
- Manual: FAQ view slide animation, extraction offer after upload, badges.

## 13. Token economics

- Runtime FAQ hits: 0 tokens forever; save-command: 0 tokens.
- Session: ~100 Gemini free-tier calls + ~50 OpenRouter judge calls (a few
  cents). Doc-scoped: ~15 + ~8.
- Corpus grounding: a few hundred extra chars per Gemini query (free tier).

## Out of scope (v2 candidates)

- Embeddings/vector search for corpus relevance ranking
- FAQ export to PDF/CSV
- Thumbs up/down feedback loop
- Per-user chat history restore in UI (log exists, viewer later)
