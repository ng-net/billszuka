# Project Environment & System Constraints

## System Environment Notes
- **Primary Machine OS**: macOS 13 (Ventura). Cannot upgrade OS on this machine. Ensure tools, Node packages, and dependencies remain compatible with macOS 13 (e.g. Node 20 / standard tools).
- **Secondary Machine OS**: macOS 15 (Sequoia) available if advanced OS features or newer CLI dependencies require it.

## Automated Walkthrough & Pipeline Insight Logging Rule
- **Mandatory Action**: Whenever a walkthrough (`walkthrough.md`) or verification pipeline run is generated or updated in this project, the agent MUST run `python3 tools/extract_intel.py --target both`.
- This automatically analyzes execution results, extracts 1-2 key strategic insights/discoveries, and appends them to [DZIENNIK.md](file:///Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/DZIENNIK.md) and [INTEL.md](file:///Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/INTEL.md).

