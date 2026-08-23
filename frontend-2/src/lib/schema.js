// schema.js — schema constants shared across frontend-2 views.
//
// Mirrors tools/config.py on the Python side. If you change one, change the
// other. Audit 2026-08-23 fill rates in master.csv (417 rows): tiktok 0.2%,
// kanal_zamiennik 1.9%, linkedin 2.2%, related_to 3.4%, instagram 3.8%,
// marka_wlasna_oem 5.8%, facebook 9.4% → 7 columns hidden by default to
// give a clean 28-column view. Data is kept on disk; users can re-enable
// any hidden column via the Column toggle in the toolbar.

/** Columns hidden by default in the table view. UI-only — data not deleted. */
export const HIDDEN_COLUMNS = [
  "tiktok",
  "kanal_zamiennik",
  "linkedin",
  "related_to",
  "instagram",
  "marka_wlasna_oem",
  "facebook",
];

/**
 * Filter a list of column IDs to exclude HIDDEN_COLUMNS.
 * Idempotent and order-preserving.
 */
export function visibleColumns(columns) {
  if (!Array.isArray(columns)) return columns;
  const hidden = new Set(HIDDEN_COLUMNS);
  return columns.filter((c) => !hidden.has(c));
}
