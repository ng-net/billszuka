/**
 * Persisted preferences — localStorage v1 schema.
 * NEVER persists CSV data.
 * Versioned: if schema changes, bump key suffix and ignore old data.
 */

import { getActiveProfile } from "./auth.js";

function getKey(profileId = getActiveProfile() || "default") {
  return `czat-table.prefs.v1.${profileId}`;
}

const DEFAULTS = {
  version: 1,
  activeTab: "table", // "table" | "analytics"
  density: "compact", // "compact" | "comfortable"
  theme: "system", // "light" | "dark" | "system"
  pageSize: 0, // 50 | 100 | 250 | 0 (all)
  pageIndex: 0,
  globalSearch: "",
  columnOrder: null, // array of column ids, null = default order
  columnVisibility: null, // { [colId]: boolean }, null = all visible
  columnWidths: null, // { [colId]: number px }, null = auto
  sortStack: [], // [{ id, desc }]
  filters: {}, // { [colId]: filterValue } — shape depends on type
  lastFocusedColumn: null,
};

export function loadPrefs(profileId) {
  if (typeof localStorage === "undefined") return { ...DEFAULTS };
  try {
    const raw = localStorage.getItem(getKey(profileId));
    if (!raw) return { ...DEFAULTS };
    const parsed = JSON.parse(raw);
    if (parsed.version !== 1) return { ...DEFAULTS };
    return { ...DEFAULTS, ...parsed };
  } catch {
    return { ...DEFAULTS };
  }
}

export function savePrefs(prefs, profileId) {
  if (typeof localStorage === "undefined") return;
  try {
    const trimmed = {
      version: 1,
      activeTab: prefs.activeTab,
      density: prefs.density,
      theme: prefs.theme,
      pageSize: prefs.pageSize ?? 0,
      pageIndex: prefs.pageIndex ?? 0,
      globalSearch: prefs.globalSearch ?? "",
      columnOrder: prefs.columnOrder,
      columnVisibility: prefs.columnVisibility,
      columnWidths: prefs.columnWidths,
      sortStack: prefs.sortStack,
      filters: prefs.filters,
      lastFocusedColumn: prefs.lastFocusedColumn,
    };
    localStorage.setItem(getKey(profileId), JSON.stringify(trimmed));
  } catch {
    // quota or disabled — silently ignore
  }
}

export function clearPrefs(profileId) {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.removeItem(getKey(profileId));
  } catch {}
}
