// schema.js — schema constants shared across frontend-2 views.
//
// Mirrors tools/config.py on the Python side. If you change one, change the
// other. Column visibility is driven entirely by what the CSV provides and
// localStorage prefs — no hardcoded HIDDEN_COLUMNS override here.

/** Always-empty — removed to avoid confusing overrides. Visibility is CSV-driven. */
export const HIDDEN_COLUMNS = [];

/** Identity pass-through — no hardcoded filtering applied to CSV columns. */
export function visibleColumns(columns) {
  return columns;
}
