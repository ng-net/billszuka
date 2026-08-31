/**
 * Aggregation helpers used by AnalyticsView.
 *
 * Pure functions: takes a row array + a column name, returns counts/distributions.
 * No React, no DOM. Memoization is up to the caller.
 */

/**
 * Coerce a possibly-Date value to a YYYY-MM-DD string, or "" if unparseable.
 * Required because useCsv's applySchema() turns `data_weryfikacji` into a
 * Date instance — calling `.trim()` on it would throw "trim is not a function".
 * Mirrors the Date/string fallback already in ModernLeadsTable.jsx,
 * ExperimentView.jsx, and ModernLeadsTableV2.jsx's `fmtDate`.
 */
function toIsoDate(v) {
  if (v == null || v === "") return "";
  if (v instanceof Date) {
    return isNaN(v.getTime()) ? "" : v.toISOString().slice(0, 10);
  }
  return String(v).trim();
}

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
  NL: "#0e7490", // cyan-700 (planned, 0 rows)
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

// ---------------------------------------------------------------------------
// v1.2 helpers — Analytics tab redesign
// ---------------------------------------------------------------------------

/**
 * Region map (BILLSzuka 12-kraj scope, post-FR-removal 2026-08-31).
 * Order is intentional: V4 → Balkans → Baltics (matches BILLSzuka research order in AGENTS.md).
 * FR / NL are future scope, not included.
 */
export const REGION_MAP = {
  "V4":      ["PL", "CZ", "SK"],
  "Balkans": ["BG", "HR", "SI", "RS", "MD", "RO"],
  "Baltics": ["LT", "LV", "EE"],
};

/**
 * Build the Kraje × PowerMatic matrix.
 * Returns: { countries: [{kraj, pm, hawk, both, brak, total, pmPct}], max }
 * Sorted by PM count desc, then by total desc.
 */
export function powerMaticMatrix(rows) {
  const m = new Map();
  for (const r of rows || []) {
    const k = (r.kraj || "").trim() || "—";
    if (!m.has(k)) m.set(k, { kraj: k, pm: 0, hawk: 0, both: 0, brak: 0, total: 0 });
    const s = m.get(k);
    s.total++;
    const brand = (r.marki_nabijarki || "").toLowerCase();
    const hasPM = brand.includes("powermatic");
    const hasHK = /\bhawk\b/i.test(r.marki_nabijarki || "");
    if (hasPM && hasHK) s.both++;
    else if (hasPM) s.pm++;
    else if (hasHK) s.hawk++;
    else s.brak++;
  }
  const list = [...m.values()].map(c => ({
    ...c,
    pmPct: c.total ? Math.round(100 * (c.pm + c.both) / c.total) : 0,
  }));
  list.sort((a, b) => (b.pm + b.both) - (a.pm + a.both) || b.total - a.total);
  const max = Math.max(1, ...list.map(c => Math.max(c.pm, c.hawk, c.both, c.brak)));
  return { countries: list, max };
}

/**
 * Region rollup — for each region, compute totals, PM%, FROZEN%, and per-kraje breakdown.
 * Returns: [{ name, kraje, total, pm, pmPct, fr, frPct, krajeRows: [{ kraj, total, pm, fr, frPct, anomaly }] }]
 */
export function regionRollup(rows) {
  const out = [];
  for (const [name, kraje] of Object.entries(REGION_MAP)) {
    const rr = (rows || []).filter(r => kraje.includes((r.kraj || "").trim()));
    const pm = rr.filter(r => /powermatic/i.test(r.marki_nabijarki || "")).length;
    const fr = rr.filter(r => deriveStatus(r.flagi) === "FROZEN").length;
    const krajeRows = kraje.map(k => {
      const kk = rr.filter(r => (r.kraj || "").trim() === k);
      const kkPM = kk.filter(r => /powermatic/i.test(r.marki_nabijarki || "")).length;
      const kkFR = kk.filter(r => deriveStatus(r.flagi) === "FROZEN").length;
      const kkPct = kk.length ? Math.round(100 * kkPM / kk.length) : 0;
      const kkFRPct = kk.length ? Math.round(100 * kkFR / kk.length) : 0;
      // Anomaly: large market, 0% PM (signal that research vs result is off).
      const anomaly = kk.length >= 30 && kkPM === 0;
      // Importer hint: if any firm has "dovozce" / "importer" / "importator" / "імпортер" in marki_nabijarki
      const importer = kk.some(r => /\b(dovozce|importator|імпортер|importer|dovoz)\b/i.test(r.marki_nabijarki || ""));
      return { kraj: k, total: kk.length, pm: kkPM, fr: kkFR, pmPct: kkPct, frPct: kkFRPct, anomaly, importer };
    });
    out.push({
      name, kraje,
      total: rr.length,
      pm, pmPct: rr.length ? Math.round(100 * pm / rr.length) : 0,
      fr, frPct: rr.length ? Math.round(100 * fr / rr.length) : 0,
      krajeRows,
    });
  }
  return out;
}

/**
 * Coverage by country: FROZEN / DO-WERYFIKACJI / PENDING_API / OTHER counts.
 * Returns: [{ kraj, FROZEN, DO_W, PEND, OTHER, total, frPct }] sorted by FROZEN% desc.
 */
export function coverageByCountry(rows) {
  const m = new Map();
  for (const r of rows || []) {
    const k = (r.kraj || "").trim() || "—";
    if (!m.has(k)) m.set(k, { kraj: k, FROZEN: 0, DO_W: 0, PEND: 0, OTHER: 0 });
    const s = m.get(k);
    s.total = (s.total || 0) + 1;
    const st = deriveStatus(r.flagi);
    if (st === "FROZEN") s.FROZEN++;
    else if (st === "DO-WERYFIKACJI") s.DO_W++;
    else if (st === "PENDING_API") s.PEND++;
    else s.OTHER++;
  }
  const list = [...m.values()].map(c => ({
    ...c,
    total: c.FROZEN + c.DO_W + c.PEND + c.OTHER,
    frPct: (c.FROZEN + c.DO_W + c.PEND + c.OTHER) > 0
      ? Math.round(100 * c.FROZEN / (c.FROZEN + c.DO_W + c.PEND + c.OTHER))
      : 0,
  }));
  list.sort((a, b) => b.frPct - a.frPct || b.FROZEN - a.FROZEN);
  return list;
}

/**
 * Research-vs-result anomalies.
 * Returns: { anomalies: [...], unverified: [...], ideal: [...] }
 * Each item: { kraj, total, pm, fr, pmPct, frPct, text }.
 */
export function researchAnomalies(rows) {
  const byKraj = new Map();
  for (const r of rows || []) {
    const k = (r.kraj || "").trim() || "—";
    if (!byKraj.has(k)) byKraj.set(k, { kraj: k, total: 0, pm: 0, fr: 0 });
    const s = byKraj.get(k);
    s.total++;
    if (/powermatic/i.test(r.marki_nabijarki || "")) s.pm++;
    if (deriveStatus(r.flagi) === "FROZEN") s.fr++;
  }
  const list = [...byKraj.values()].map(s => ({
    ...s,
    pmPct: s.total ? Math.round(100 * s.pm / s.total) : 0,
    frPct: s.total ? Math.round(100 * s.fr / s.total) : 0,
  }));
  const anomalies = list
    .filter(s => s.total >= 30 && s.pm === 0)
    .map(s => ({
      ...s,
      icon: "warn",
      text: `${s.total} firm przebadanych, 0 z PowerMatic. Albo rynek nie ma PM, albo kanały dystrybucji nieprzeszukane.`,
    }))
    .sort((a, b) => b.total - a.total);
  const unverified = list
    .filter(s => s.fr === 0 && s.total > 0)
    .map(s => ({
      ...s,
      icon: "info",
      text: `${s.total} firm, ${s.pm} PM, 0% zweryfikowanych. Niezweryfikowane — to nie "brak PM", to brak badań.`,
    }))
    .sort((a, b) => b.total - a.total);
  const ideal = list
    .filter(s => s.pmPct >= 20 && s.frPct >= 90)
    .map(s => ({
      ...s,
      icon: "check",
      text: s.pmPct >= 25
        ? `${s.total} firm, ${s.pm} PM (${s.pmPct}%), ${s.fr} FROZEN. Wysoki PM + prawie pełna weryfikacja.`
        : `${s.total} firm, ${s.pm} PM, ${s.fr} FROZEN. Idealny ROI researchu — wzorcowy kraj.`,
    }))
    .sort((a, b) => b.pmPct - a.pmPct);
  return { anomalies, unverified, ideal };
}

/**
 * Top single research anomaly for the headline banner.
 * Returns: { country, text } or null if nothing meets the threshold.
 */
export function topResearchAnomaly(rows) {
  const { anomalies, unverified } = researchAnomalies(rows);
  if (anomalies.length > 0) {
    const a = anomalies[0];
    return {
      country: a.kraj,
      text: `${a.total} firm przebadanych, 0 z PowerMatic — największa luka researchu.`,
    };
  }
  if (unverified.length > 0) {
    const u = unverified[0];
    return {
      country: u.kraj,
      text: `${u.total} firm, ${u.pm} PM, 0% zweryfikowanych — priorytet: weryfikacja.`,
    };
  }
  return null;
}

/**
 * Verification velocity — cumulative FROZEN count per country, last N months.
 * Parses data_weryfikacji (YYYY-MM-DD) and falls back to date in flagi string.
 * Returns: [{ kraj, spark: [n0..n5], total, lastMonth, hasData }]
 * Sorted by lastMonth desc.
 */
export function verificationTimeline(rows, monthsBack = 6) {
  const today = new Date();
  const months = [];
  for (let i = monthsBack - 1; i >= 0; i--) {
    const d = new Date(today.getFullYear(), today.getMonth() - i, 1);
    months.push({ y: d.getFullYear(), m: d.getMonth(), key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}` });
  }
  const byKraj = new Map();
  let hasAnyDate = false;
  for (const r of rows || []) {
    if (deriveStatus(r.flagi) !== "FROZEN") continue;
    // Try data_weryfikacji first, then parse date from flagi.
    // data_weryfikacji is schema-coerced to a Date by useCsv/applySchema,
    // so `.trim()` would throw — coerce to YYYY-MM-DD ourselves.
    let dateStr = toIsoDate(r.data_weryfikacji);
    if (!dateStr) {
      const m = String(r.flagi || "").match(/(\d{4}-\d{2}-\d{2})/);
      if (m) dateStr = m[1];
    }
    if (!dateStr) continue;
    hasAnyDate = true;
    const key = dateStr.slice(0, 7); // YYYY-MM
    const k = (r.kraj || "").trim() || "—";
    if (!byKraj.has(k)) byKraj.set(k, { kraj: k, monthly: new Map() });
    const slot = byKraj.get(k);
    slot.monthly.set(key, (slot.monthly.get(key) || 0) + 1);
  }
  const out = [];
  for (const [kraj, slot] of byKraj) {
    const spark = [];
    for (const m of months) spark.push(slot.monthly.get(m.key) || 0);
    // Cumulative (running total, oldest → newest).
    for (let i = 1; i < spark.length; i++) spark[i] += spark[i - 1];
    const lastMonth = spark[spark.length - 1] || 0;
    const total = spark[spark.length - 1] || 0;
    out.push({ kraj, spark, total, lastMonth, hasData: true });
  }
  // Also include countries with 0 FROZEN rows (they need an entry so the row is visible).
  const allKraje = new Set((rows || []).map(r => (r.kraj || "").trim()).filter(Boolean));
  for (const k of allKraje) {
    if (!byKraj.has(k)) {
      out.push({ kraj: k, spark: new Array(monthsBack).fill(0), total: 0, lastMonth: 0, hasData: false });
    }
  }
  out.sort((a, b) => b.lastMonth - a.lastMonth || b.total - a.total || a.kraj.localeCompare(b.kraj));
  return { months, countries: out, hasAnyDate };
}

/**
 * Group PowerMatic listings by parent company (heuristic, for cross-country players).
 * Strips common legal suffixes (SRL, EOOD, S.A., etc.) and groups on first 2 words.
 * Returns: { groups: [{ parent, kraje: [...], rows: [...] }], singles: [...] }
 */
export function powerMaticGroups(rows) {
  const pm = powerMaticListings(rows);
  const LEGAL_RE = /\b(S\.?R\.?L\.?|S\.?A\.?|EOOD|spol\.? ?s\.? ?r\.? ?o\.? ?|LTD|LLC|SARL|AS|BG|RO|S\.r\.o\.|sp\. ?z\. ?o\. ?o\. ?|OÜ|UAB|SIA|S\.p\.A\.)\b/gi;
  const buckets = new Map();
  for (const r of pm) {
    const name = String(r.nazwa_firmy || "").replace(LEGAL_RE, "").replace(/\(.*?\)/g, "").trim();
    const words = name.split(/\s+/).filter(Boolean).slice(0, 2);
    if (words.length < 2) {
      buckets.set(`__singleton__${Math.random()}`, { parent: name, rows: [r] });
      continue;
    }
    const key = words.join(" ").toLowerCase();
    if (!buckets.has(key)) buckets.set(key, { parent: words.join(" "), rows: [] });
    buckets.get(key).rows.push(r);
  }
  const groups = [];
  const singles = [];
  for (const [key, b] of buckets) {
    const kraje = [...new Set(b.rows.map(r => r.kraj))];
    if (kraje.length > 1) {
      groups.push({ parent: b.parent, kraje, rows: b.rows });
    } else {
      singles.push(...b.rows);
    }
  }
  groups.sort((a, b) => b.rows.length - a.rows.length);
  return { groups, singles };
}

