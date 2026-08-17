# Project Environment & System Constraints

## Automated Walkthrough & Pipeline Insight Logging Rule
- **Mandatory Action**: Whenever a walkthrough (`walkthrough.md`) or verification pipeline run is generated or updated in this project, the agent MUST run `python3 tools/extract_intel.py --target both`.
- This automatically analyzes execution results, extracts 1-2 key strategic insights/discoveries, and appends them to [DZIENNIK.md](file:///Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/DZIENNIK.md) and [INTEL.md](file:///Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/INTEL.md).

## Multi-Wave Gentle Search & Anti-Hallucination Guardrail
- Never invent or hallucinate tax IDs, CUI, or registration numbers.
- Always verify against official public registry APIs before assigning `✅ FROZEN`.
- Prune generic map keyword stubs lacking official company names and tax identifiers.
- Execute validation in gentle batches and maintain schema uniformity (`tools/uniform_data.py` + `tools/billszuka.py compile`).

