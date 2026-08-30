import Papa from "papaparse";

/**
 * Treat "brak" / "—" / "n/a" / "n/d" / "—" as empty for inference purposes.
 * These are common Polish/English "no data" placeholders that pollute type detection.
 */
const EMPTY_LIKE = new Set(["brak", "—", "n/a", "n/d", "nd", "none", "null", "-"]);

export function isEmptyLike(v) {
  if (v == null) return true;
  const s = String(v).trim().toLowerCase();
  return s === "" || EMPTY_LIKE.has(s);
}

/** Known column types for BILLSzuka canonical schemas */
export const CANONICAL_COLUMN_TYPES = {
  kraj: "enum",
  kategoria: "enum",
  tier: "enum",
  wolumen: "enum",
  confidence_wolumen: "enum",
  powinowactwo_nabijarki: "enum",
  cross_sell_potential: "enum",
  rynek_skala: "enum",
  flagi: "enum",
  marka_wlasna_oem: "enum",
  sourcing: "enum",
  rok_zalozenia: "number",
  data_weryfikacji: "date",
  www: "url",
  email: "email",
  email_decydent: "email",
  telefon: "phone",
  linkedin: "url",
  facebook: "url",
  instagram: "url",
  tiktok: "url",
};

/**
 * Column type detection. Sniffs the first ~200 non-empty values.
 * Returns one of: text | number | date | url | email | phone | enum
 */
export function inferColumnType(values, columnId) {
  if (columnId && CANONICAL_COLUMN_TYPES[columnId]) {
    return CANONICAL_COLUMN_TYPES[columnId];
  }

  const sample = values.filter((v) => !isEmptyLike(v)).slice(0, 200);
  if (sample.length === 0) return "text";

  const n = sample.length;

  // Date: ISO-like (YYYY-MM-DD, YYYY-MM-DDTHH:mm:ss, YYYY/MM/DD)
  const dateLike = sample.filter((v) => /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$|^\d{4}\/\d{2}\/\d{2}$/.test(String(v).trim()));
  if (dateLike.length / n > 0.85) return "date";

  // URL (with protocol or domain)
  const urlLike = sample.filter((v) => /^(https?:\/\/|[a-zA-Z0-9-]+\.[a-zA-Z]{2,})[^\s]*$/i.test(String(v).trim()));
  if (urlLike.length / n > 0.85) return "url";

  // Email
  const emailLike = sample.filter((v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(v).trim()));
  if (emailLike.length / n > 0.85) return "email";

  // Phone: contains 9+ digits with optional + - space ( )
  const phoneLike = sample.filter((v) => {
    const s = String(v).trim();
    if (s.length < 7 || s.length > 30) return false;
    const digits = s.replace(/[^\d]/g, "");
    return digits.length >= 9 && /^\+?[\d\s\-()]+$/.test(s);
  });
  if (phoneLike.length / n > 0.85) return "phone";

  // Number — 100% numeric
  const numLike = sample.filter((v) => {
    const s = String(v).trim();
    return /^-?\d+(\.\d+)?$/.test(s);
  });
  if (numLike.length === n) return "number";

  // Enum: ≤30 unique non-empty values across the column
  const uniques = new Set();
  for (const v of sample) {
    const s = String(v).trim();
    if (s.includes(",") && !["adres", "nazwa_firmy", "notatki"].includes(columnId)) {
      s.split(",").forEach((t) => {
        const item = t.trim();
        if (item && !isEmptyLike(item)) uniques.add(item);
      });
    } else {
      uniques.add(s);
    }
  }
  if (uniques.size > 0 && uniques.size <= 30 && sample.length >= 10) return "enum";

  return "text";
}

/**
 * Detect schema (column -> type) from rows.
 * Returns array of { id, type } in the same order as columns.
 */
export function inferSchema(columns, rows) {
  return columns.map((col) => {
    const values = rows.map((r) => r[col]);
    return { id: col, type: inferColumnType(values, col) };
  });
}

/**
 * Convert raw value to typed value for the inferred type.
 */
export function coerceValue(value, type) {
  if (value == null || value === "") return null;
  const s = String(value).trim();
  if (s === "" || s === "brak" || s === "—") return null;
  switch (type) {
    case "number": {
      const n = Number(s.replace(",", "."));
      return isNaN(n) ? null : n;
    }
    case "date": {
      const d = new Date(s);
      return isNaN(d.getTime()) ? null : d;
    }
    default:
      return s;
  }
}

/**
 * Apply type coercion to all rows based on schema.
 */
export function applySchema(rows, schema) {
  const typeMap = Object.fromEntries(schema.map((c) => [c.id, c.type]));
  return rows.map((row) => {
    const out = {};
    for (const k in row) {
      out[k] = coerceValue(row[k], typeMap[k]);
    }
    return out;
  });
}

/**
 * Parse a File (browser File API) into { columns, rows } using PapaParse worker.
 * Calls onProgress({ rowsParsed, total }) when worker reports step events.
 * Returns a Promise that resolves to { columns, rows, schema, parseTimeMs } or rejects with error.
 */
export function parseCsvFile(file, { onProgress, signal } = {}) {
  return new Promise((resolve, reject) => {
    const start = performance.now();
    const rows = [];
    let columns = [];

    Papa.parse(file, {
      header: true,
      skipEmptyLines: "greedy",
      worker: true,
      step: (results, parser) => {
        if (signal?.aborted) {
          parser.abort();
          return;
        }
        if (results.errors && results.errors.length > 0) {
          // ignore per-row errors (common in real CSV), but capture fatal
          const fatal = results.errors.find((e) => e.type === "Delimiter" || e.type === "Quotes");
          if (fatal) {
            parser.abort();
            reject(new Error(`Parse error on line ${results.meta?.lines ?? "?"}: ${fatal.message}`));
            return;
          }
        }
        if (columns.length === 0 && results.meta?.fields) {
          columns = results.meta.fields;
        }
        if (results.data) rows.push(results.data);
        onProgress?.({
          rowsParsed: rows.length,
          bytesParsed: results.meta?.cursor ?? 0,
        });
      },
      complete: () => {
        if (signal?.aborted) {
          reject(new DOMException("Parse cancelled", "AbortError"));
          return;
        }
        // trim headers in-place (since transformHeader can't run in worker)
        const trimmedCols = columns.map((c) => c.trim());
        const trimmedRows = rows.map((r) => {
          const out = {};
          for (const k in r) {
            const trimmedKey = k.trim();
            out[trimmedKey] = r[k];
          }
          return out;
        });
        const schema = inferSchema(trimmedCols, trimmedRows);
        const typed = applySchema(trimmedRows, schema);
        const parseTimeMs = performance.now() - start;
        resolve({ columns: trimmedCols, rows: typed, schema, parseTimeMs });
      },
      error: (err) => reject(err),
    });
  });
}

/**
 * Fetch + parse a URL (e.g. /api/master.csv). Reads Content-Length so the
 * caller can show a real progress percentage. Falls back gracefully when
 * Content-Length is absent (chunked encoding, CORS, etc.).
 */
export async function parseCsvUrl(url, { onProgress, signal } = {}) {
  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.status}`);

  // Try to get file size from headers so the progress ring shows a real %.
  const contentLength = Number(res.headers.get("content-length") || 0);

  const blob = await res.blob();
  // Use the actual blob size as a reliable fallback (blob.size is always known
  // once the download finishes, even if Content-Length was missing).
  const totalBytes = contentLength || blob.size || 0;

  const file = new File([blob], url.split("/").pop() || "sample.csv", { type: "text/csv" });
  return parseCsvFile(file, {
    signal,
    onProgress: (p) => onProgress?.({ ...p, totalBytes }),
  });
}

/**
 * Get enum values (≤50) for a column from rows — for filter chips.
 * Excludes empty-like values ("brak", "—", "n/a").
 *
 * Scans a SAMPLE of rows only (default: first 2 000), not the full dataset.
 * This keeps filter loading fast regardless of file size (5 k vs 500 k rows).
 * The 50-value cap is still enforced — if >50 unique values appear in the
 * sample the column is treated as non-enum (text filter).
 */
export function getEnumValues(rows, columnId, max = 50) {
  const SAMPLE = 2000;
  const end = Math.min(rows.length, SAMPLE);
  const set = new Set();
  for (let i = 0; i < end; i++) {
    const r = rows[i];
    if (!r) continue;
    const v = r[columnId];
    if (v == null) continue;
    const s = String(v).trim();
    if (!s || EMPTY_LIKE.has(s.toLowerCase())) continue;
    
    if (s.includes(",") && !["adres", "nazwa_firmy", "notatki", "miasto"].includes(columnId)) {
      s.split(",").forEach((item) => {
        const trimmed = item.trim();
        if (trimmed && !EMPTY_LIKE.has(trimmed.toLowerCase())) {
          set.add(trimmed);
        }
      });
    } else {
      set.add(s);
    }
    if (set.size > max) return null;
  }
  const arr = Array.from(set);
  
  if (columnId === "wolumen" || columnId === "wolumen_szac") {
    const order = {
      "mały": 1,
      "mały-średni": 2,
      "średni": 3,
      "średni-duży": 4,
      "duży": 5
    };
    return arr.sort((a, b) => {
      const rankA = order[a.toLowerCase()] || 99;
      const rankB = order[b.toLowerCase()] || 99;
      if (rankA !== rankB) return rankA - rankB;
      return a.localeCompare(b);
    });
  }
  
  return arr.sort();
}
