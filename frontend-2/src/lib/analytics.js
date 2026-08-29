/**
 * Aggregation helpers used by AnalyticsView.
 *
 * Pure functions: takes a row array + a column name, returns counts/distributions.
 * No React, no DOM. Memoization is up to the caller.
 */

/**
 * Group rows by a column value, returning [{ key, count }] sorted by count desc.
 * Empty/whitespace cells are bucketed as "—" (em-dash, common placeholder).
 * Values are trimmed before comparison (case-sensitive).
 *
 * @param {Array<Object>} rows — row objects (e.g. parsed master.csv rows)
 * @param {string} col — column name
 * @param {Object} [opts]
 * @param {number} [opts.top=20] — keep top N values; remainder goes into "Inne"
 * @returns {Array<{key: string, count: number}>}
 */
export function groupBy(rows, col, { top = 20 } = {}) {
  const counts = new Map();
  for (const r of rows || []) {
    const raw = r?.[col];
    const v = (raw == null ? "" : String(raw)).trim() || "—";
    counts.set(v, (counts.get(v) || 0) + 1);
  }
  const all = [...counts.entries()].map(([key, count]) => ({ key, count }));
  all.sort((a, b) => b.count - a.count || a.key.localeCompare(b.key));
  if (all.length <= top) return all;
  const head = all.slice(0, top);
  const rest = all.slice(top);
  const restTotal = rest.reduce((s, x) => s + x.count, 0);
  if (restTotal > 0) head.push({ key: `Inne (${rest.length})`, count: restTotal });
  return head;
}

/**
 * Build a numeric histogram with equal-width bins.
 * Non-numeric cells are skipped. NaN/Infinity skipped.
 *
 * @param {Array<Object>} rows
 * @param {string} col
 * @param {number} [bins=10]
 * @returns {Array<{binStart: number, binEnd: number, count: number, label: string}>}
 */
export function histogram(rows, col, bins = 10) {
  const nums = [];
  for (const r of rows || []) {
    const raw = r?.[col];
    if (raw == null) continue;
    const n = typeof raw === "number" ? raw : Number(String(raw).replace(",", "."));
    if (Number.isFinite(n)) nums.push(n);
  }
  if (nums.length === 0) return [];
  const min = Math.min(...nums);
  const max = Math.max(...nums);
  if (min === max) {
    return [{ binStart: min, binEnd: max, count: nums.length, label: `${min}` }];
  }
  const width = (max - min) / bins;
  const out = Array.from({ length: bins }, (_, i) => ({
    binStart: min + i * width,
    binEnd: min + (i + 1) * width,
    count: 0,
    label: "",
  }));
  for (const n of nums) {
    let idx = Math.floor((n - min) / width);
    if (idx >= bins) idx = bins - 1;
    if (idx < 0) idx = 0;
    out[idx].count += 1;
  }
  for (const b of out) {
    const fmt = (v) =>
      Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(1)}k` : `${Math.round(v)}`;
    b.label = `${fmt(b.binStart)}–${fmt(b.binEnd)}`;
  }
  return out;
}

/**
 * Parse the "flagi" column into a status category.
 * The flag format is: "2026-08-18 ✅ FROZEN (API)" or "⚠️ DO-WERYFIKACJI (API)"
 * We look for the first matching keyword.
 */
export function deriveStatus(flagiValue) {
  const s = (flagiValue == null ? "" : String(flagiValue)).toUpperCase();
  if (s.includes("FROZEN")) return "FROZEN";
  if (s.includes("DO-WERYFIKACJI")) return "DO-WERYFIKACJI";
  if (s.includes("PENDING_API")) return "PENDING_API";
  return "OTHER";
}

/**
 * Country color palette (consistent across charts).
 */
export const COUNTRY_COLORS = {
  PL: "#dc2626", // red-600 — primary
  CZ: "#2563eb", // blue-600
  SK: "#0891b2", // cyan-600
  RO: "#ea580c", // orange-600
  BG: "#7c3aed", // violet-600
  HR: "#db2777", // pink-600
  SI: "#16a34a", // green-600
  RS: "#0d9488", // teal-600 — added 2026-08-22
  LT: "#ca8a04", // yellow-600
  LV: "#9333ea", // purple-600
  EE: "#65a30d", // lime-600
  MD: "#be185d", // fuchsia-700
  FR: "#1d4ed8", // blue-700
  NL: "#0e7490", // cyan-700
  OT: "#525252", // neutral-600 (other)
};

/**
 * Pick a color for an unknown key by hashing to one of the palette colors.
 */
export function colorFor(key, palette = Object.values(COUNTRY_COLORS)) {
  let h = 0;
  for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) >>> 0;
  return palette[h % palette.length];
}
/**
 * Numeric weight for ordering rows in top-N lists.
 * Uses confidence_wolumen (parsed as % 0-100) if available, else a fallback
 * by tier / wolumen.
 */
function rowScore(row, metric) {
  if (metric === "confidence_wolumen" || metric == null) {
    const raw = row?.confidence_wolumen;
    if (raw == null || raw === "") return 0;
    const s = String(raw).replace(/[^\d.]/g, "");
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : 0;
  }
  if (metric === "wolumen") {
    const v = String(row?.wolumen || "").toLowerCase().trim();
    if (v.startsWith("duż")) return 4;
    if (v.startsWith("śred")) return 2;
    if (v.startsWith("mał")) return 1;
    return 0;
  }
  return 0;
}

/**
 * Return top N rows per country, grouped by country.
 *
 * @param {Array<Object>} rows
 * @param {number} [n=5] — how many per country
 * @param {string} [metric='wolumen'] — sort metric key
 * @returns {Array<{country: string, rows: Array<Object>}>}
 */
export function topByCountry(rows, n = 5, metric = "wolumen") {
  if (!Array.isArray(rows) || rows.length === 0) return [];
  const buckets = new Map();
  for (const r of rows) {
    const c = (r?.kraj || "").toString().trim() || "—";
    if (!buckets.has(c)) buckets.set(c, []);
    buckets.get(c).push(r);
  }
  const out = [];
  for (const [country, list] of buckets) {
    const sorted = list
      .slice()
      .sort((a, b) => rowScore(b, metric) - rowScore(a, metric));
    out.push({ country, rows: sorted.slice(0, n) });
  }
  out.sort((a, b) => a.country.localeCompare(b.country));
  return out;
}

const CLAIM_PATTERNS = [
  /\bdystrybutor/i,
  /\bdystrybuuj/i,
  /\bdystrybu\b/i,
  /\bdistributor/i,
  /\bdistribu/i,
  /\bsprzedaż\s+hurtowa/i,
  /\bsprzedajemy\s+i\s+dystrybu/i,
];

/**
 * Companies that *claim* in their notes they are distributors / wholesalers.
 * Returns rows annotated with match_term.
 *
 * @param {Array<Object>} rows
 * @returns {Array<Object>}
 */
export function claimDistributors(rows) {
  if (!Array.isArray(rows) || rows.length === 0) return [];
  const out = [];
  for (const r of rows) {
    const notes = String(r?.notatki || "").trim();
    if (!notes) continue;
    for (const pat of CLAIM_PATTERNS) {
      const m = notes.match(pat);
      if (m) {
        out.push({ ...r, match_term: m[0] });
        break;
      }
    }
  }
  return out;
}

/**
 * Companies listing PowerMatic in their roller machine brands.
 * Annotates each row with brand_variant (PowerMatic / PowerMatic + Hawk / etc.)
 *
 * @param {Array<Object>} rows
 * @returns {Array<Object>}
 */
export function powerMaticListings(rows) {
  if (!Array.isArray(rows) || rows.length === 0) return [];
  const out = [];
  for (const r of rows) {
    const raw = String(r?.marki_nabijarki || "").trim();
    if (!raw) continue;
    const lower = raw.toLowerCase();
    if (!lower.includes("powermatic")) continue;
    let variant = "PowerMatic";
    if (/\bhawk\b/i.test(raw)) variant = "PowerMatic + Hawk";
    out.push({ ...r, brand_variant: variant });
  }
  return out;
}
