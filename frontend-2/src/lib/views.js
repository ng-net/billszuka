/**
 * Default saved views shipped with the app.
 *
 * Each view = { id, name, filters, columns? }
 * Filters may contain synthetic keys prefixed with `__`:
 *   - __brand: matched against classifyBrand() output (PowerMatic, Hawk, Inna, etc.)
 *
 * Kept here (not in RawTable.jsx) so it's testable in isolation.
 */

export const DEFAULT_VIEWS = [
  {
    id: "view-powermatic",
    name: "PowerMatic",
    userDefined: false,
    filters: { __brand: "PowerMatic" },
  },
  {
    id: "view-powermatic-hawk",
    name: "PowerMatic + Hawk",
    userDefined: false,
    filters: { __brand: "PowerMatic + Hawk" },
  },
  {
    id: "view-hawk-only",
    name: "Tylko Hawk",
    userDefined: false,
    filters: { __brand: "Hawk" },
  },
  {
    id: "view-inna",
    name: "Inna",
    userDefined: false,
    filters: { __brand: "Inna" },
  },
  {
    id: "view-big-players",
    name: "Big players",
    userDefined: false,
    filters: { tier: ["hurtownik", "producent", "autoryzowany"], wolumen: "duży" },
  },
  {
    id: "view-marketplace",
    name: "Marketplace fishes",
    userDefined: false,
    filters: { tier: "marketplace" },
  },
  {
    id: "view-pl",
    name: "Polska (PL)",
    userDefined: false,
    filters: { kraj: "PL" },
  },
  {
    id: "view-cz",
    name: "Czechy (CZ)",
    userDefined: false,
    filters: { kraj: "CZ" },
  },
  {
    id: "view-sk",
    name: "Słowacja (SK)",
    userDefined: false,
    filters: { kraj: "SK" },
  },
];

/**
 * Returns the unique top-N values for a column, sorted by frequency desc.
 * Used to populate quick filter chip dropdowns.
 */
export function topValues(rows, columnId, limit = 8) {
  if (!rows || !columnId) return [];
  const counts = new Map();
  for (const row of rows) {
    const v = row[columnId];
    if (v == null || v === "" || v === "brak" || v === "—") continue;
    counts.set(v, (counts.get(v) || 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([value, count]) => ({ value, count }));
}

/**
 * Toggle a value within a filter value (scalar, array, or undefined).
 * Returns the new filter value: undefined if all values removed, scalar if
 * exactly one value remains, array otherwise.
 */
export function toggleFilterValue(current, value) {
  if (current === undefined || current === null || current === "") {
    return value;
  }
  if (Array.isArray(current)) {
    const had = current.includes(value);
    const next = had ? current.filter((v) => v !== value) : [...current, value];
    if (next.length === 0) return undefined;
    if (next.length === 1) return next[0];
    return next;
  }
  if (current === value) return undefined;
  return [current, value];
}