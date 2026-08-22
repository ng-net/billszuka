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
- **CI workflow is tracked** (`.github/workflows/ci-python.yml` added to git, id 339221395 on ng-net). 2026-08-21: pushed to `marlink/BILLSzuka` to escape phantom workflow ID cache on ng-net. New workflow registration should give fresh ID on marlink. **For Actions minutes** (`/users/marlink/settings/billing/actions`) `user` scope is also needed — add with `gh auth refresh -s user` (one-time, browser auth). Helper: `tools/check-actions-minutes.sh`. Diagnosis in DZIENNIK 2026-08-21.
- **Frontend canonical = `frontend-2/`** (3-view shell + Analytics + Gemini + Settings drawers). `czat-table/` moved to `archive/czat-table/` (do not resurrect). `frontend/` is DEPRECATED (see `frontend/DEPRECATED.md`). Backend: `tools/api_server.py` binds 127.0.0.1:8000 with `/api` proxy from vite (port 3001).
- **LLM keys live in `tools/api_secrets.json`** (gitignored, 0600). Manage via Settings drawer (gear icon, top-right) — never via env files. Fallback chain order: openrouter → gemini → mock. Add OpenRouter (sk-or-v1-...) and/or Gemini (AIza..., free tier from aistudio.google.com) keys there.
- **`.env` is bootstrapped into the vault on every server start** (idempotent): `OPENROUTER_API_KEY`, `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, … Each becomes one vault entry tagged `source: ".env"`. User-added keys are `source: "ui"`. Deleting a `.env`-key from the vault via UI sticks (it's not auto-re-imported) — to re-import, edit `.env`, delete the vault entry, restart.

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
