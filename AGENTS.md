# AGENTS.md — BILLSzuka

Loaded by Mavis at session start. Stable prefix — every line bills on every turn.
Keep this under 40 lines.

## What this is

B2B research project for BILLS Sp. z o.o. (Ostrzeszów, PL). Goal: distribution partners
for PowerMatic rolling machines + Hawk across PL first, then CZ/SK/UK/etc.
Operator: Marceli. Operator's company: BILLS Sp. z o.o. (NIP PL).

## Core files (read sections on demand, not whole files)

- `methodology.md` — how to research, A1-A6 / B1-B9 framework
- `RUNBOOK.md` — verification toolbox per country, deploy/auth/keep-alive setup (CANONICAL)
- `INTEL.md` — strategic discoveries, partner data, market insights (append only)
- `DZIENNIK.md` — session log, progress, feedback, action items, migration history
- `SETUP-REGON-KEY.md` — how to get the Polish REGON API key

## Iron rules

- **Canonical remote:** `github.com/ng-net/billszuka` (private, 2026-08-30). Backup: `github.com/marlink/BILLSzuka`.
- **Always run `verify-data` skill** on new/edited data in `data/{Kraj}/catalog-*.csv`
  or `data/relationships.csv`, after every research session and bulk import.
- Run `python tools/validate_columns.py` after every research session — same rule,
  see `tools/fix_validation_criticals.py` for bulk fixes. Don't merge these two checks.
- **Decydent = public sources only** (KRS, LinkedIn, official registries). Don't ask
  Marceli to supply company lists.
- Search volumes in `SŁOWNIK-WYSZUKIWAŃ.md` are estimates (szac.), not real Keyword
  Planner data. For real numbers use Ahrefs / Senuto / Google Trends.
- **Skip Germany** unless Marceli explicitly says otherwise. Order: PL → CZ → SK → UK →
  Western EU → Scandinavia → Balkans.
- **Frontend canonical = `frontend-2/`**; `frontend/` is DEPRECATED. Backend:
  `tools/api_server.py` on `127.0.0.1:8000`, proxied by vite on port 3001.
- **LLM keys** live only in `tools/api_secrets.json` (gitignored, 0600), managed via the
  Settings drawer — never env files directly. Provider chain default is
  `gemini → mock → openrouter` (OpenRouter's free DeepSeek hallucinates on structured
  data). Full `.env` bootstrap / knowledge-base / Basic Auth setup details → `RUNBOOK.md`.
- **Never run a global cache-purge touching `data/knowledge/`** — it orphans local file
  copies and loses Gemini file refs (same failure mode as the Qoder "lost custom model" bug).

## Memory rules

- Every insight lands in `INTEL.md` (strategic) or `DZIENNIK.md` (work log) — never
  only in chat, and never in agent/user memory.
- One question at a time when asking Marceli (he's busy); batch multi-part questions.

## Cache hygiene

- Don't re-read `INTEL.md` or `DZIENNIK.md` unless asked — large, changes often.
- `data/` is verified output — read it but don't re-verify unless changed.
