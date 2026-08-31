/**
 * Brand classification + keyword highlighting.
 * All matching is case-insensitive and works across nazwa, notatki,
 * zrodlo_danych and sourcing columns. No data or backend changes.
 */

const POWERMATIC_PATTERNS = [
  /powermatic/i,
  /power\s*matic/i,
  /\b(?:1|2|3|4|5)[+\s]*[ivx]?\b/i, // numeric + roman variants
];

const HAWK_PATTERNS = [/\b(?:james)?hawk\b/i];

const TOBACCO_PATTERNS = [/tytoń/i, /tobacco/i, /tyton/i];
const GILZA_PATTERNS = [/gilza/i, /gilzy/i, /gilz/i];
const BIBULKI_PATTERNS = [/bibułk/i, /bibulki/i, /rolling papers?/i, /bibuł/i];

export function classifyBrand(row = {}) {
  const text = [
    row.nazwa || "",
    row.notatki || "",
    row.zrodlo_danych || "",
    row.sourcing || "",
  ].join(" ").toLowerCase();

  const hasPower = POWERMATIC_PATTERNS.some((p) => p.test(text));
  const hasHawk = HAWK_PATTERNS.some((p) => p.test(text));

  if (hasPower && hasHawk) return "PowerMatic + Hawk";
  if (hasPower) return "PowerMatic";
  if (hasHawk) return "Hawk";

  // Any other brand/machine signal → Inna
  if (/nabijark|nabijarki|machine|roller|gilz|tyton|tobacco/i.test(text)) {
    return "Inna";
  }

  return "—";
}

export const KEYWORD_TYPES = ["tyton", "gilza", "bibulki"];

const KEYWORD_PATTERNS = [
  ...TOBACCO_PATTERNS.map((p) => ({ type: "tyton", regex: p })),
  ...GILZA_PATTERNS.map((p) => ({ type: "gilza", regex: p })),
  ...BIBULKI_PATTERNS.map((p) => ({ type: "bibulki", regex: p })),
];

/**
 * Returns an array of segments: { text, type? } where type is one of
 * KEYWORD_TYPES when the segment matched a keyword. Used by CellRenderer
 * to render highlighted spans safely (no dangerouslySetInnerHTML).
 */
export function highlightKeywords(text = "") {
  if (!text) return [{ text: text || "" }];

  // Collect all match spans.
  const matches = [];
  for (const { type, regex } of KEYWORD_PATTERNS) {
    let m;
    const re = new RegExp(regex.source, regex.flags.includes("g") ? regex.flags : regex.flags + "g");
    while ((m = re.exec(text)) !== null) {
      matches.push({ start: m.index, end: m.index + m[0].length, type });
      if (m.index === re.lastIndex) re.lastIndex++;
    }
  }

  if (matches.length === 0) return [{ text }];

  // Sort by start, then resolve overlaps by keeping the earlier match.
  matches.sort((a, b) => a.start - b.start || a.end - b.end);
  const merged = [];
  for (const m of matches) {
    const last = merged[merged.length - 1];
    if (last && m.start < last.end) continue; // overlap: skip
    merged.push(m);
  }

  // Build segments.
  const out = [];
  let pos = 0;
  for (const m of merged) {
    if (m.start > pos) out.push({ text: text.slice(pos, m.start) });
    out.push({ text: text.slice(m.start, m.end), type: m.type });
    pos = m.end;
  }
  if (pos < text.length) out.push({ text: text.slice(pos) });
  return out;
}
