# BILLSzuka verification tools

Automated verification of per-kraj CSVs against official registries.

## Scripts

### `verify_run.py` — main verification round

Runs the verify-data protocol on every per-kraj CSV under `data/`.

**What it does:**
1. Diffs `data/{Kraj}/catalog-{A|B}-*.csv` against last-known row hashes (`data/.verify-state/row-hashes.json`)
2. Snapshots touched files to `data/.snapshots/<file>-<ts>.csv` (keeps last 5 per file)
3. Re-verifies each changed row using country-specific rules
4. Updates the `flagi` column (FROZEN / DO-WERYFIKACJI) on changed rows
5. Appends a block to `data/audit-log.md`
6. Regenerates `data/master.csv`
7. Saves new state

**Usage:**
```bash
cd /Volumes/MC-BRAIN/Dev-Ext/BILLSzuka

# First run — build state without re-verifying existing rows
python3 tools/verify_run.py --init

# Normal run — diffs vs state, verifies changes
python3 tools/verify_run.py

# Force re-verify every row
python3 tools/verify_run.py --all

# Dry run — show what would change
python3 tools/verify_run.py --dry-run
```

**Country API status:**
- PL: format check (CEIDG/KRS live call = TODO, needs CEIDG_API_TOKEN from .env)
- CZ: format check (ARES live call = TODO, no auth)
- SK, LT, LV, EE, BG, FR, HR, MD, RO, SI: format check only → DO-WERYFIKACJI with reason "no API yet"

### `run_verify_cron.sh` — cron wrapper

Run via cron. Logs to `data/verification/cron.log`.

## State

- `data/.verify-state/row-hashes.json` — per-file map of `id_unikalne → sha256[:16]`
- `data/.snapshots/<file>-<ts>.csv` — last 5 snapshots per file
- `data/audit-log.md` — human-readable audit trail (append-only)
- `data/master.csv` — rebuilt from per-kraj CSVs each run

## Scheduling

Recommended: cron every 15 min during research hours (09:00–18:00 Europe/Warsaw).

```bash
mavis({ command: "cron create", args: {
  agent_name: "verifier",
  cron_name: "verify-billszuka",
  schedule: "*/15 9-18 * * *",
  timezone: "Europe/Warsaw",
  prompt: "Run tools/run_verify_cron.sh. Report any new FROZEN or DO-WERYFIKACJI findings.",
  session: { mode: "sessionId", session_id: "<researcher-session-id>" }
} })
```

## What it catches

Per the verify-data skill:
- New rows from researcher → re-verify NIP/VAT format, source URL, registry match
- Modified rows → re-verify same
- Removed rows → report
- Hallucination template patterns: identical NIP/adres across multiple rows, `info@` emails on no-web companies
- Source URL liveness: TODO (need HEAD check on `zrodlo_danych` URLs)
- Cross-CSV consistency: TODO (master.csv regen catches direct mismatches)

## Limitations

- CEIDG/KRS/ARES live API calls are not wired yet — only format checks today
- Source URL liveness check (HEAD) not implemented
- No cross-file consistency check (e.g. PL master has same NIP as CZ master for same id)
- Hallucination template detection (identical patterns) not yet implemented
