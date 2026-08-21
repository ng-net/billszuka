/**
 * Persisted prefs for czat-table.
 * NEVER persists CSV content — only UI state. See localStorage key.
 */
import { storage } from "./storage"

const KEY = "czat-table.prefs.v1"

const DEFAULTS = {
  version: 1,
  density: "compact", // "compact" | "comfortable"
  theme: "system", // "light" | "dark" | "system"
  // column state keyed by the original column id
  columns: {}, // { [colId]: { visible, pinned, width, order } }
  sort: [], // [{ colId, dir }]
  filters: {}, // { [colId]: { kind: "text"|"range"|"date"|"enum", value } }
  pagination: { page: 1, perPage: 100 },
  // ephemeral (not persisted but kept here for type symmetry): "lastFocusedCol"
}

export function loadPrefs() {
  const raw = storage.get(KEY)
  if (!raw) return { ...DEFAULTS, pagination: { ...DEFAULTS.pagination } }
  try {
    const parsed = JSON.parse(raw)
    if (parsed && parsed.version === DEFAULTS.version) {
      return {
        ...DEFAULTS,
        ...parsed,
        // Always start at page 1, even after migration
        pagination: {
          perPage: parsed.pagination?.perPage ?? DEFAULTS.pagination.perPage,
          page: 1,
        },
      }
    }
    return { ...DEFAULTS, pagination: { ...DEFAULTS.pagination } }
  } catch {
    return { ...DEFAULTS, pagination: { ...DEFAULTS.pagination } }
  }
}

export function savePrefs(prefs) {
  // Don't persist large or transient fields.
  // page is intentionally NOT persisted — the user always comes back to page 1.
  const safe = {
    version: DEFAULTS.version,
    density: prefs.density,
    theme: prefs.theme,
    columns: prefs.columns,
    sort: prefs.sort,
    filters: prefs.filters,
    pagination: { perPage: prefs.pagination?.perPage ?? DEFAULTS.pagination.perPage },
  }
  storage.set(KEY, JSON.stringify(safe))
}

export function resetPrefs() {
  storage.del(KEY)
}

export { DEFAULTS as PREFS_DEFAULTS }
