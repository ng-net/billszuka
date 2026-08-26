# AGENTS.md — BILLSzuka



Loaded by Mavis at session start. Stable prefix — every line bills on every turn.

Keep this under 40 lines.



## What this is

B2B research project for BILLS Sp. z o.o. (Ostrzeszów, PL). Goal: distribution partners

for PowerMatic rolling machines + Hawk across PL first, then CZ/SK/UK/etc.

Operator: Marceli. Operator's company: BILLS Sp. z o.o. (NIP PL).

Canonical remote: `github.com/marlink/BILLSzuka` (private). Backup mirror: `github.com/ng-net/billszuka`. 2026-08-21 recovery: ng-net had GitHub phantom workflow ID cache bug (59/59 runs `startup_failure` for 9 days despite file rename + recreate). Switched canonical to `marlink/BILLSzuka` — clean workflow registration, no phantom cache. `marlink` OAuth token has scopes: `admin:gpg_key, admin:org, admin:ssh_signing_key, project, repo, workflow, write:packages` (more permissive than ng-net's). Pre-migration snapshot of marlink preserved as local branch `backup/marlink-pre-migration` (commit `73c766b`, 2026-08-10).



## Core files (don't read whole — read sections on demand)

- `methodology.md` — how to research, A1-A6 / B1-B9 framework

- `RUNBOOK.md` — verification toolbox per country (CANONICAL)

- `INTEL.md` — strategic discoveries, partner data, market insights (append only)

- `DZIENNIK.md` — session log, progress, feedback, action items

- `SETUP-REGON-KEY.md` — how to get the Polish REGON API key



## Iron rules

- **Always run `verify-data` skill** on new data in `data/{Kraj}/catalog-*.csv` or

  `data/relationships.csv`, on edits, after every research session, after bulk imports.

- **Decydent = public sources only** (KRS, LinkedIn, official registries). Don't ask

  Marceli to supply company lists.

- **Search volumes in SŁOWNIK-WYSZUKIWAŃ.md are estimates (szac.)** — not real Keyword

  Planner data. For real keyword research use Ahrefs / Senuto / Google Trends.

- **Skip Germany** unless Marceli explicitly says otherwise. Order: PL → CZ → SK → UK →

  Western EU → Scandinavia → Balkans.

- **CI workflow** is `.github/workflows/ci-python.yml` on `marlink/BILLSzuka`. Threshold: `assert critical < 200` (realistic floor for real B2B data). For Actions minutes (`/users/marlink/settings/billing/actions`) `user` scope is also needed — add with `gh auth refresh -s user` (one-time, browser auth). Helper: `tools/check-actions-minutes.sh`.

- **Frontend canonical = `frontend-2/`** (3-view shell + Analytics + Gemini + Settings drawers). `frontend/` is DEPRECATED. Backend: `tools/api_server.py` binds `127.0.0.1:8000` with `/api` proxy from vite (port 3001). 7 columns <10% fill in master.csv are hidden by default in the viewer (tiktok, kanal_zamiennik, linkedin, related_to, instagram, marka_wlasna_oem, facebook) — see `tools/config.py:HIDDEN_COLUMNS` and `frontend-2/src/lib/schema.js` (keep in sync).

- **LLM keys live in `tools/api_secrets.json`** (gitignored, 0600). Manage via Settings drawer (gear icon, top-right) — never via env files. **Default chain order: `gemini → mock → openrouter`** (NOT `openrouter → gemini → mock` — OpenRouter's free-tier DeepSeek hallucinates on structured-data Q&A; mock is deterministic, never fabricates numbers). Add OpenRouter (`sk-or-v1-...`) and/or Gemini (free tier from aistudio.google.com) keys there. The current default model is **`gemini-3.6-flash`** (2.5-flash returns *"no longer available to new users"*). Hidden `prefer_openrouter=True` flag in `ChatRequest` bypasses the reorder for power users.

- **`.env` is bootstrapped into the vault on every server start** (idempotent): `OPENROUTER_API_KEY`, `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, … Each becomes one vault entry tagged `source: ".env"`. User-added keys are `source: "ui"`. Deleting a `.env`-key from the vault via UI sticks (it's not auto-re-imported) — to re-import, edit `.env`, delete the vault entry, restart.

- **Knowledge base** (`data/knowledge/`) — files uploaded via the book-icon drawer → `/api/knowledge/upload` → Gemini Files API. The chat auto-promotes Gemini to the front of the provider chain when `knowledge_ids` are present (openrouter path doesn't see the files). Local copies live in `data/knowledge/files/<id>__<filename>` so the bot can re-upload if Gemini expires the file (48h TTL). NEVER run a global cache-purge that would touch `data/knowledge/` — that would orphan the local copies and lose the Gemini file refs (the same "lost custom model" gotcha from Qoder). 50 MB per file, types: pdf, csv, txt, md, xlsx, xls, docx.



## Memory rules

- Every insight lands in `INTEL.md` (strategic) or `DZIENNIK.md` (work log). Don't let

  discoveries stay only in chat.

- When asked "remember this" — append to the right file, not to user/agent memory.

- Output: Excel/GS + CSV. Multi-country CEE/EU coverage.



## Cache hygiene for this project

- Don't re-read `INTEL.md` or `DZIENNIK.md` unless asked — they're large and change often.

- `data/` is the verified output — read it but don't re-verify unless changed.

- One question at a time when asking Marceli (he's busy).

- Batch multi-part questions into single messages.



## Verification skill

`skills/verify-data/SKILL.md` — every CSV entry must pass through it.

## Column validator
`tools/validate_columns.py` — validates all catalog CSVs against the canonical schema. Run after every research session (`python tools/validate_columns.py`). Known sentinel values (`brak`, `n/a`, `do weryfikacji`, etc.) are normalised to empty. Remaining criticals (<200) are genuine data quality issues requiring human research. See `tools/fix_validation_criticals.py` for bulk data fixes.
