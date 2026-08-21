# AGENTS.md — BILLSzuka

Loaded by Mavis at session start. Stable prefix — every line bills on every turn.
Keep this under 40 lines.

## What this is
B2B research project for BILLS Sp. z o.o. (Ostrzeszów, PL). Goal: distribution partners
for PowerMatic rolling machines + Hawk across PL first, then CZ/SK/UK/etc.
Operator: Marceli. Operator's company: BILLS Sp. z o.o. (NIP PL).
Canonical remote: `github.com/ng-net/billszuka` (private). Backup mirror: `github.com/design-mc/billszuka`. 2026-08-12 recovery: marlink PAT lost access; ng-net OAuth token refreshed with `workflow` scope via `gh auth refresh --scopes "gist,read:org,repo,workflow"`. `marlink/BILLSzuka` is dead.

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
- **CI workflow is tracked** (`.github/workflows/ci-python.yml` added to git, id 339221395). `workflow` scope granted on `ng-net` OAuth token. **For Actions minutes** (`/users/ng-net/settings/billing/actions`) `user` scope is also needed — add with `gh auth refresh -s user` (one-time, browser auth). Helper: `tools/check-actions-minutes.sh`. 2026-08-21: 59/59 runs `startup_failure` since 2026-08-12 with 0 jobs, 0 minutes — **not quota** but GitHub phantom workflow ID cache (id 332616408 vs real 339221395). Diagnosis in DZIENNIK 2026-08-21. Workaround: push to `design-mc/billszuka` (backup mirror, fresh workflow).

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
