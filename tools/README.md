# BILLSzuka Tools & Pipeline Architecture

Automated verification of per-country catalog CSVs against official registries and master aggregation.

## Primary Entrypoint: `billszuka.py`

`python3 tools/billszuka.py` is the unified CLI wrapper for all lead operations:

```bash
# Validate schemas across all 24 catalogs and rebuild data/master.csv (35 columns)
python3 tools/billszuka.py compile

# Run automated verification loop, update row hashes, flag status, and rebuild master
python3 tools/billszuka.py verify [--init | --all | --dry-run]

# Normalize raw intake leads from data/_intake/{ISO}/
python3 tools/billszuka.py intake --iso CZ

# Execute 11-level search strategy or view search options for a country
python3 tools/billszuka.py search --country SK [--level L1]
```

---

## Tool Categories & Active Suite

### Core Pipeline & Orchestration
- **`billszuka.py`**: Unified Master CLI entrypoint.
- **`config.py`**: Central configuration (35-column canonical schema, country maps, auto AppleDouble `._*` cleanup).
- **`orchestrate_11_levels.py`**: 11-level search strategy runner and manual lead adder.
- **`map_intake.py`**: Standardized intake normalizer (maps raw 35-col intake CSVs → 35-col master schema).
- **`validate_intake.py`**: Intake validation & hallucination detection.
- **`extract_intel.py`**: Automated strategic insight extractor for `DZIENNIK.md` and `INTEL.md`.

### Verification & Registry Lookup
- **`verify_run.py`**: Core hash diffing, verification protocol, and master rebuild trigger.
- **`verify_api.py`**: Live registry API verification engine (CEIDG v3, ARES, VIES, Pappers, e-Äriregister, etc.).
- **`l0_preflight.py`**: Pre-flight validation (NIP checksum mod 11 + KRS/ARES name match).
- **`scrapers_registry.py`**: Web scrapers for non-API countries (SK, RO, LT, FR).
- **`krs_search.py`**: KRS registry lookup.
- **`ee_ariregister.py`**: Estonia e-Äriregister API/web lookup.
- **`lt_open_data.py`**: Lithuania JAR open data lookup.
- **`fr_recherche.py`**: France Pappers / Recherche lookup.
- **`vies_verify.py`**: EU VIES VAT validation.

### Enrichment & Applications
- **`auto_enrich.py`**: Multi-source lead enrichment.
- **`apollo_enrich.py`**: Apollo.io fallback enricher for non-EU markets (e.g. MD).
- **`api_server.py`**: FastAPI backend server for local dashboard interface.

---

## Archival & One-Off Scripts (`tools/legacy/`)

Historical, completed migration, or experimental one-off scripts are archived under `tools/legacy/`:
- `drop_region_columns.py`: Previous schema migration script.
- `migrate_strip_regions.py`: Region field stripping & ID re-indexing migration.
- `refresh_row_hashes.py`: Replaced by `verify_run.py --init`.
- `clean_backups.py`: Backup CSV cleaner.
- `clean_macos_metadata.sh`: Superceded by `config.py:clean_apple_double()`.
- `poc_dow_resolver.py` & `enrich_pl_dow.py`: Experimental DOW proof-of-concept scripts.
- `normalize_PL.py`: One-off PL normalizer (superceded by `map_intake.py`).
