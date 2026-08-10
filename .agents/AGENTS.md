# Project Environment & System Constraints

## System Environment Notes
- (machine-specific OS constraints removed 2026-08-10 — was macOS 13 Ventura, no longer relevant)

## Automated Walkthrough & Pipeline Insight Logging Rule
- **Mandatory Action**: Whenever a walkthrough (`walkthrough.md`) or verification pipeline run is generated or updated in this project, the agent MUST run `python3 tools/extract_intel.py --target both`.
- This automatically analyzes execution results, extracts 1-2 key strategic insights/discoveries, and appends them to [DZIENNIK.md](file:///Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/DZIENNIK.md) and [INTEL.md](file:///Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/INTEL.md).
