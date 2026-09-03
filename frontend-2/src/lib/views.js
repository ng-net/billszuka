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
  {
    id: "view-best-pl",
    name: "Best PL",
    userDefined: false,
    filters: { __bestInCountry: "PL" },
  },
  {
    id: "view-best-cz",
    name: "Best CZ",
    userDefined: false,
    filters: { __bestInCountry: "CZ" },
  },
  {
    id: "view-best-sk",
    name: "Best SK",
    userDefined: false,
    filters: { __bestInCountry: "SK" },
  },
  {
    id: "view-best-other",
    name: "Best Other",
    userDefined: false,
    filters: { __bestInCountry: "OTHER" },
  },
];

/**
 * Score a single row for "best lead" ranking. Higher = better.
 *
 * Signals (point values):
 *   - tier in {autoryzowany, producent, hurtownik}    → +3
 *   - tier in {reseller}                              → +1
 *   - wolumen == "duży"                                → +3
 *   - wolumen == "średni"                              → +1
 *   - cross_sell_potential == "High"                  → +2
 *   - cross_sell_potential == "Medium"                → +1
 *   - confidence_wolumen is "Jest NIP"                → +1
 *   - powinowactwo_nabijarki == "wysoki"              → +2
 *   - powinowactwo_nabijarki == "średni"              → +1
 *   - tier == "marketplace"                           → -3  (excluded by default)
 *   - tier == "detalista"                             → -1
 *
 * Returns a number; rows with score <= 0 are filtered out by
 * bestLeadsPerCountry().
 */
export function scoreRow(row) {
  if (!row) return 0;
  let score = 0;

  const tier = String(row.tier || "").toLowerCase();
  if (tier === "autoryzowany" || tier === "producent" || tier === "hurtownik") score += 3;
  else if (tier === "reseller") score += 1;
  else if (tier === "marketplace") score -= 3;
  else if (tier === "detalista") score -= 1;

  const vol = String(row.wolumen || "").toLowerCase();
  if (vol === "duży") score += 3;
  else if (vol === "średni") score += 1;

  const cs = String(row.cross_sell_potential || "").toLowerCase();
  if (cs === "high") score += 2;
  else if (cs === "medium") score += 1;

  if (String(row.confidence_wolumen || "").trim() === "Jest NIP") score += 1;

  const pow = String(row.powinowactwo_nabijarki || "").toLowerCase();
  if (pow === "wysoki") score += 2;
  else if (pow === "średni") score += 1;

  return score;
}

/**
 * Returns the top-N rows for a given country, ranked by scoreRow().
 *
 * - countryCode: "PL" | "CZ" | "SK" | "OTHER" (any non-PL/CZ/SK country)
 * - limit: defaults to 25 (fits a single "best per country" view nicely).
 *
 * Rows with score <= 0 are excluded — marketplace / detalista-only leads
 * are not "best". If a country has zero qualifying rows, returns [].
 */
export function bestLeadsPerCountry(rows, countryCode, limit = 25) {
  if (!Array.isArray(rows) || rows.length === 0) return [];
  const code = String(countryCode || "").toUpperCase();

  const filtered = rows.filter((r) => {
    const k = String(r?.kraj || "").toUpperCase();
    if (code === "OTHER") {
      return k && k !== "PL" && k !== "CZ" && k !== "SK";
    }
    return k === code;
  });

  return filtered
    .map((r) => ({ row: r, score: scoreRow(r) }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((x) => x.row);
}

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