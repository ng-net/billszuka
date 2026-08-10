#!/bin/bash
# run_verify_cron.sh — wrapper for cron / scheduled runs
# Logs to data/verification/cron.log

set -e
ROOT="/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka"
LOG_DIR="$ROOT/data/verification"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/cron.log"

cd "$ROOT"
python3 tools/verify_run.py >> "$LOG" 2>&1
echo "---" >> "$LOG"
echo "$(date -Iseconds) verify_run done" >> "$LOG"
