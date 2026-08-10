# BILLSzuka — Token & Context Brief

> Project-level optimization. Canonical reference: `/Volumes/MC-BRAIN/dev-ext/MINIMAX.md`
> Keep under 50 lines. Only the project-specific rules.

## What burns tokens in this project
- `data/` has 12 countries × multiple CSVs — glob first, never blanket read
- `DZIENNIK.md` + `INTEL.md` change every session — don't re-read
- `RUNBOOK.md` is 35K — read the section you need (it has clear headers)
- `methodology.md` is 40K — same, read targeted sections
- `frontend/` and `design/` are design artifacts, not for reading

## Cache strategy
- Load this file + `AGENTS.md` once per session → cached as stable prefix
- Marceli's project context (BILLSzuka memory) is also in user_profile → cached
- Big files: read with offset/limit, never full
- Tool outputs > 2K lines: summarize, don't keep raw

## Verification discipline
- Every new catalog row → `verify-data` skill → audit-log.md
- Cron `billszuka-verify-5-new` is a backstop, not the primary trigger
- Proactive verification: run after every data change, not just on entry

## Output rules
- Excel/GS + CSV. No PDFs unless Marceli asks.
- Skip Germany unless told otherwise.
- Public sources only (KRS, LinkedIn, official registries).

## Commands Mavis should use
- `bash /Volumes/MC-BRAIN/dev-ext/bin/mavis-optimize.sh .` — re-apply optimization
- glob `data/{Kraj}/*.csv` for country-specific data
- `cat INTEL.md | head -100` for recent intel
- `tail -50 DZIENNIK.md` for last session
