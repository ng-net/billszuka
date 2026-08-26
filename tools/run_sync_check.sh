#!/usr/bin/env bash
# run_sync_check.sh — Gentle scheduled sync check: catalogs vs master.csv
# Runs silently via cron, logs output to tools/.verify-runs/sync_YYYY-MM-DD.log
# Automatically recompiles master.csv if drift detected.
#
# Cron example (every 30 min):
#   */30 * * * * /bin/bash "/Users/ciepolml/Documents/Bills-Drive/BILLSzuka-24-Aug/tools/run_sync_check.sh"
# Or (every 2 hours):
#   0 */2 * * *  /bin/bash "/Users/ciepolml/Documents/Bills-Drive/BILLSzuka-24-Aug/tools/run_sync_check.sh"

set -euo pipefail

# Resolve the project root relative to this script
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/tools/.verify-runs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/sync_$(date '+%Y-%m-%d').log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S %Z')

echo "[$TIMESTAMP] Running sync check..." >> "$LOG_FILE"

cd "$ROOT"
python3 tools/sync_verifier.py --recompile >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$TIMESTAMP] ✅ PERFECT_SYNC — no action needed." >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ⚠️ DRIFT detected — master.csv recompiled automatically." >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"
exit 0
