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

***

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

- **`verify_run.py`**: Hash diffing, snapshotting, audit log, and `regenerate_master()`. Delegates verification to `verify_api.py`.

- **`verify_api.py`**: Single source of truth for verification. Owns format pre-flight (via `verify_principles`), live API calls (CEIDG v3, ARES, VIES, e-Äriregister, JAR, Apollo), status assignment, and CSV back-fill. Supports `--retrofix` for FABRYKAT re-detection.

- **`checksums.py`**: 12-country official registry ID checksum & format validator (mod 11, Luhn, ISO 7064).

- **`scrapers_registry.py`**: Web scrapers for non-API countries (SK, RO, LT, FR).

- **`krs_search.py`**: KRS registry lookup.

- **`vies_verify.py`**: EU VIES VAT validation.

- **`gmaps_search.py`**: Places API search tool for tobacco distributor leads.

### Enrichment, Backend & Server

- **`scrapegraph_enricher.py`**: Intelligent AI-driven web scraper (ScrapeGraphAI) for structured company and assortment extraction from dynamic websites.

- **`auto_enrich.py`**: Multi-source lead enrichment.

- **`apollo_enrich.py`**: Apollo.io fallback enricher for non-EU markets (e.g. MD).

- **`api_server.py`**: FastAPI backend server for local dashboard interface.

- **`auth.py`**: User authentication & permissions.

- **`db.py`**: SQLite database interface for fast local state (`billszuka.db`).

- **`faq.py`** **&** **`faq_build_session.py`**: Knowledge base and FAQ management.

- **`md_corpus.py`**: Permanent markdown corpus parser and indexer.

- **`run_verify_cron.sh`**: Verification cron trigger script.

