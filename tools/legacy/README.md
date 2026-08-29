# tools/legacy/ — one-shot scripts from the early catalog cleanup era

This directory is **archive-only**. The scripts here were run during the
first months of BILLSzuka to clean, migrate, and verify catalog CSVs.
They are kept for historical reference and to reproduce specific cleanup
steps if needed, but **they are not part of the regular workflow** and
nothing in `tools/` imports them.

## If you need to clean catalogs today

Use:

- `tools/validate_columns.py` — current schema validator (run after every
  research session; outputs a CSV the verify-data skill can consume).
- `tools/fix_validation_criticals.py` — bulk fixes for sentinel values
  like `brak`, `n/a`, `do weryfikacji` and obvious typos.
- `skills/verify-data/SKILL.md` — the canonical verification pipeline.

The legacy scripts below were the predecessors of those tools. Most of
them mutate `data/{Kraj}/catalog-*.csv` in place and were superseded by
the schema-driven workflow around mid-2026.

## Script index

### Deep cleans (versions 2 → 11)
Sequential iterations of `deep_clean_v{N}.py`. Each one tightened
quality rules, fixed specific row patterns, and was superseded by the
next version. `v11` is the most recent and includes 100% FROZEN
verification across the dataset.

### Catalog normalizers
- `clean_and_rebuild_verified_catalogs.py` — rebuild verified subset
  from scratch.
- `clean_backups.py` — prune `data/backups/` (AppleDouble `._*` files,
  chained-timestamp duplicates, identical-content backups).
- `clean_macos_metadata.sh` — strip macOS metadata from CSVs (`.DS_Store`,
  `._*`, xattr).
- `normalize_PL.py` — Polish-specific normalization (NIP, KRS, nazwa
  casing, address format).
- `fix_catalog_quality.py` / `fix_data_quality.py` — early quality
  fixers that predate `fix_validation_criticals.py`.

### Migrations
- `migrate_strip_regions.py` — strip `region_*` fields and re-index
  IDs to `PL-A-001`, `PL-A-002`, …  shape.
- `drop_region_columns.py` — narrower version of the above.
- `refresh_row_hashes.py` — recompute `_hash` columns after schema
  changes.

### Google Maps sweeps (early lead discovery)
The `gmaps_*.py` files were one-off sweeps used to bulk-discover
companies in underrepresented regions. The current flow uses
`skills/gmaps-sweep/` instead — those scripts are obsolete.

### Country-specific enrichers
- `ee_ariregister.py` — Estonia Äriregister enrichment.
- `fr_recherche.py` — France SIREN/SIRET enrichment.
- `lt_open_data.py` — Lithuania open-data enrichment.
- `enrich_pl_dow.py` — Poland DOW (departament) enrichment.
- `enrich_contacts_pass2.py` — second-pass contact enrichment.

### Lead intake / verification
- `poc_dow_resolver.py` — proof-of-concept DOW resolver (superseded by
  the production flow).
- `rescue_intake_leads.py` — recover leads from staging intake.
- `freeze_baseline_sk.py` — freeze SK baseline after first pass.

## Don't run these unless you mean it

Most of these scripts mutate `data/` in place and were tuned to a
specific snapshot of the dataset. Running them now will likely corrupt
the verified catalogs.

If you genuinely need to run one (e.g. to reproduce a historical fix),
copy it out of `legacy/` first, edit it for the current `config.py`
schema, and verify the output with `skills/verify-data/` before
committing.