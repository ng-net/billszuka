/**
 * Persisted preferences — localStorage v1 schema.
 * NEVER persists CSV data.
 * Versioned: if schema changes, bump key suffix and ignore old data.
 */

const KEY = "czat-table.prefs.v1";

const DEFAULTS = {
  version: 1,
  activeTab: "table", // "table" | "analytics"
  density: "compact", // "compact" | "comfortable"
  theme: "system", // "light" | "dark" | "system"
  columnOrder: null, // array of column ids, null = default order
  columnVisibility: null, // { [colId]: boolean }, null = all visible
  columnWidths: null, // { [colId]: number px }, null = auto
  sortStack: [], // [{ id, desc }]
  filters: {}, // { [colId]: filterValue } — shape depends on type
  lastFocusedColumn: null,
};

export function loadPrefs() {
  if (typeof localStorage === "undefined") return { ...DEFAULTS };
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return { ...DEFAULTS };
    const parsed = JSON.parse(raw);
    if (parsed.version !== 1) return { ...DEFAULTS };
    return { ...DEFAULTS, ...parsed };
  } catch {
    return { ...DEFAULTS };
  }
}

export function savePrefs(prefs) {
  if (typeof localStorage === "undefined") return;
  try {
    const trimmed = {
      version: 1,
      activeTab: prefs.activeTab,
      density: prefs.density,
      theme: prefs.theme,
      columnOrder: prefs.columnOrder,
      columnVisibility: prefs.columnVisibility,
      columnWidths: prefs.columnWidths,
      sortStack: prefs.sortStack,
      filters: prefs.filters,
      lastFocusedColumn: prefs.lastFocusedColumn,
    };
    localStorage.setItem(KEY, JSON.stringify(trimmed));
  } catch {
    // quota or disabled — silently ignore
  }
}

export function clearPrefs() {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.removeItem(KEY);
  } catch {}
}
