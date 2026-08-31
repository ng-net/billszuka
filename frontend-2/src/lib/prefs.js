/**
 * Persisted preferences — localStorage v1 schema.
 * NEVER persists CSV data.
 * Versioned: if schema changes, bump key suffix and ignore old data.
 */

const KEY = "czat-table.prefs.v2";

const DEFAULTS = {
  version: 2,
  activeTab: "table", // "table" | "analytics" | "experiment"
  density: "compact", // "compact" | "comfortable"
  theme: "system", // "light" | "dark" | "system"
  columnOrder: null, // array of column ids, null = default order
  columnVisibility: null, // { [colId]: boolean }, null = all visible
  columnWidths: null, // { [colId]: number px }, null = auto
  sortStack: [], // [{ id, desc }]
  filters: {}, // { [colId]: filterValue } — shape depends on type
  lastFocusedColumn: null,
  savedViews: [], // array of { id, name, filters, columns, sortStack? }
  activeView: null, // id of currently active saved view
};

export function loadPrefs() {
  if (typeof localStorage === "undefined") return { ...DEFAULTS };
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return { ...DEFAULTS };
    const parsed = JSON.parse(raw);
    // Any non-v2 pref blob (legacy v1) is migrated by merging defaults;
    // new fields (savedViews, activeView) fall back to their defaults.
    if (parsed.version !== 2) {
      return { ...DEFAULTS, ...parsed, version: 2 };
    }
    return { ...DEFAULTS, ...parsed };
  } catch {
    return { ...DEFAULTS };
  }
}

export function savePrefs(prefs) {
  if (typeof localStorage === "undefined") return;
  try {
    const trimmed = {
      ...prefs,
      version: 2,
      savedViews: prefs.savedViews || [],
      activeView: prefs.activeView || null,
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
