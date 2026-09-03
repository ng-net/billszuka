# BILLSzuka Tools & Pipeline Architecture

Automated verification of per-country catalog CSVs against official registries and master aggregation.

## Primary Entrypoint: `billszuka.py`

`python3 tools/billszuka.py` is the unified CLI wrapper for all lead operations:

```bash
# Validate schemas across all 24 catalogs and rebuild data/master.csv (36 columns)
python3 tools/billszuka.py compile

# Run automated verification loop, update row hashes, flag status, and rebuild master
python3 tools/billszuka.py verify [--init | --all | --dry-run]

# Normalize raw intake leads from data/_intake/{ISO}/
python3 tools/billszuka.py intake --iso CZ
```

---

## Tool Categories & Active Suite

### Core Pipeline & Orchestration
- **`billszuka.py`**: Unified Master CLI entrypoint.
- **`config.py`**: Central configuration (36-column canonical schema, country maps, auto AppleDouble `._*` cleanup).
- **`validate_columns.py`**: Strict 36-column canonical schema validator.
- **`check_urls.py`**: Asynchronous HTTP scanner for domain/URL health and live status recording.
- **`inject_www_status.py`**: Injects live URL health and response time status (`www_status`) into catalogs.
- **`map_intake.py`**: Standardized intake normalizer (maps raw intake CSVs → 36-col master schema).
- **`validate_intake.py`**: Intake validation & hallucination detection.
- **`extract_intel.py`**: Automated strategic insight extractor for `DZIENNIK.md` and `INTEL.md`.

### Verification & Registry Lookup
- **`verify_run.py`**: Core hash diffing, verification protocol, and master rebuild trigger.
- **`verify_api.py`**: Live registry API verification engine (CEIDG v3, ARES, VIES, Pappers, e-Äriregister, etc.).
- **`verify_lead.py`**: Multi-tool lead double-checker and evidence validator.
- **`checksums.py`**: 12-country official registry ID checksum & format validator (mod 11, Luhn, ISO 7064).
- **`l0_preflight.py`**: Pre-flight validation (NIP checksum mod 11 + KRS/ARES name match).
- **`scrapers_registry.py`**: Web scrapers for non-API countries (SK, RO, LT, FR).
- **`krs_search.py`**: KRS registry lookup.
- **`vies_verify.py`**: EU VIES VAT validation.
- **`gmaps_search.py`**: Places API search tool for tobacco distributor leads.

### Enrichment, Backend & Server
- **`auto_enrich.py`**: Multi-source lead enrichment.
- **`apollo_enrich.py`**: Apollo.io fallback enricher for non-EU markets (e.g. MD).
- **`api_server.py`**: FastAPI backend server for local dashboard interface.
- **`auth.py`**: User authentication & permissions.
- **`db.py`**: SQLite database interface for fast local state (`billszuka.db`).
- **`faq.py` & `faq_build_session.py`**: Knowledge base and FAQ management.
- **`md_corpus.py`**: Permanent markdown corpus parser and indexer.
- **`run_verify_cron.sh`**: Verification cron trigger script.

---

## Archival & One-Off Scripts (`tools/legacy/`)

Historical, completed migration, or experimental one-off scripts are archived under `tools/legacy/`:
- `fix_cz_bad_rows.py`, `fix_remaining_42.py`, `fix_nonpl_schema.py`, `fix_validation_criticals.py`
- `deep_clean_and_deduplicate.py`, `clean_and_realign_columns.py`, `clean_notatki.py`, `dedup_notatki.py`
- `gentle_60min_lead_gem_scout.py`, `gentle_enrich_and_verify.py`, `autonomous_20min_verifier.py`
- `purge_hallucinations_and_normalize.py`, `uniform_data.py`, `finalize_and_freeze_all.py`
- `orchestrate_11_levels.py`, `test_11_levels.py`, `test_tokens.py`
- Full archive of earlier sweep and catalog cleanup helpers.
