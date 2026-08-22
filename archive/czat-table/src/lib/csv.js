import Papa from "papaparse"

/** Hard cap to keep the browser tab alive. 50 MB ≈ ~500k rows of 35 cols. */
export const MAX_FILE_BYTES = 50 * 1024 * 1024

const URL_RE = /^(https?:\/\/)[^\s]+$/i
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
// Phone must look like a phone: at least one of `+`, parentheses, or a long
// enough digit run with at least one separator (space/dash/dot). This avoids
// classifying plain numeric IDs like "123456" as phone numbers.
const PHONE_RE = /^(?:\+\d|\(\d|\d{3,}[ \-./]\d)[\d ()\-./]+$/
const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$/
const PL_DATE_RE = /^\d{2}[./-]\d{2}[./-]\d{4}$/

/** Sample a value, return its inferred primitive type or null. */
function classifyValue(raw) {
  if (raw == null) return null
  const v = String(raw).trim()
  if (v === "" || v.toLowerCase() === "null" || v.toLowerCase() === "n/a") return null
  if (ISO_DATE_RE.test(v) && !Number.isNaN(Date.parse(v))) return "date"
  if (PL_DATE_RE.test(v)) return "date"
  // Number: allow thousands sep (space, comma) and decimal (dot or comma)
  const num = v.replace(/\s/g, "").replace(/,/g, ".")
  if (/^-?\d+(\.\d+)?$/.test(num)) return "number"
  if (EMAIL_RE.test(v)) return "email"
  if (URL_RE.test(v)) return "url"
  if (PHONE_RE.test(v) && v.replace(/\D/g, "").length >= 6) return "phone"
  return "text"
}

/** Score a column by sampling the first N non-empty values. */
function inferColumnType(samples) {
  const counts = { text: 0, number: 0, date: 0, url: 0, email: 0, phone: 0, null: 0 }
  for (const v of samples) {
    const t = classifyValue(v)
    counts[t ?? "null"] += 1
  }
  const total = samples.length
  if (total === 0) return "text"
  // URL/email/phone only win if super dominant — text often matches the phone regex incidentally.
  const order = ["email", "url", "phone", "date", "number", "text"]
  for (const t of order) {
    const ratio = counts[t] / total
    if (ratio >= 0.85) return t
  }
  return "text"
}

/** Enumerate unique values for a column to detect "enum" columns. */
function uniqueValues(rows, key, cap = 50) {
  const set = new Set()
  for (const r of rows) {
    const v = r[key]
    if (v == null || v === "") continue
    set.add(String(v))
    if (set.size > cap) return null // too many, not an enum
  }
  return [...set]
}

/**
 * Detect row-level data quality issues. Returned as an array of short,
 * human-readable messages — the caller decides how to surface them.
 *
 * Currently catches:
 *  - Misaligned related_to / rok_zalozenia: a 4-digit year in related_to
 *    while rok_zalozenia is empty (common copy-paste mistake).
 */
export function validateRows(rows) {
  const warnings = []
  if (rows.length === 0) return warnings
  // Use the keys from the first row to stay schema-agnostic.
  const keys = Object.keys(rows[0])
  if (!keys.includes("related_to") || !keys.includes("rok_zalozenia")) return warnings
  let misaligned = 0
  for (const r of rows) {
    const rt = String(r.related_to ?? "").trim()
    const rk = String(r.rok_zalozenia ?? "").trim()
    if (/^\d{4}$/.test(rt) && rk === "") misaligned++
  }
  if (misaligned > 0) {
    warnings.push(
      `${misaligned} row${misaligned === 1 ? "" : "s"} have a 4-digit year in "related_to" but empty "rok_zalozenia" — the year is likely in the wrong column.`,
    )
  }
  return warnings
}

/**
 * Parse a CSV string into columns (with inferred types) + rows.
 * Wraps PapaParse in our own thin layer so we control types and errors.
 */
export function parseCsvString(text, { sampleSize = 200 } = {}) {
  const result = Papa.parse(text, {
    header: true,
    skipEmptyLines: "greedy",
    dynamicTyping: false, // we do our own
    transformHeader: (h) => h.trim(),
  })
  if (result.errors && result.errors.length > 0) {
    // Only surface truly fatal errors. PapaParse's "Delimiter" type covers
    // both fatal delimiters and the `UndetectableDelimiter` warning that fires
    // for single-column CSVs (data still parses fine). We only treat `Quotes`
    // errors — unterminated quoted fields — as fatal.
    const fatal = result.errors.find((e) => e.type === "Quotes")
    if (fatal) {
      const err = new Error(`CSV parse error on row ${fatal.row ?? "?"}: ${fatal.message}`)
      err.code = "PARSE"
      throw err
    }
  }
  const rawRows = result.data || []
  const rows = rawRows
    .map((r) => {
      const out = {}
      for (const k of Object.keys(r)) out[k] = r[k] == null ? "" : String(r[k])
      return out
    })
    .filter((r) => Object.values(r).some((v) => v !== ""))

  const headerRow = result.meta?.fields ?? Object.keys(rows[0] ?? {})
  const columns = headerRow.map((name) => {
    const samples = []
    for (let i = 0; i < rows.length && samples.length < sampleSize; i++) {
      const v = rows[i][name]
      if (v != null && v !== "") samples.push(v)
    }
    const type = inferColumnType(samples)
    const uniques = type === "text" ? uniqueValues(rows, name, 20) : null
    return {
      id: name,
      name,
      type,
      enumValues: uniques && uniques.length > 0 && uniques.length <= 20 ? uniques : null,
    }
  })

  const warnings = validateRows(rows)
  return { columns, rows, parseMs: 0, warnings }
}

/**
 * Parse a File with smooth, visible progress reporting.
 *
 * The actual read+parse for small CSVs is sub-100ms, which would be invisible
 * to the user. We layer a set of "fake" checkpoints on top so the bar always
 * takes ~900ms to reach 100% — long enough to read but short enough not to
 * feel like the app is stuck. Each checkpoint lands inside the framer-motion
 * `transition: { duration: 0.2 }` on the bar, so they chain into one smooth
 * ease-out sweep rather than stuttery jumps.
 *
 * The promise is also gated by a 900ms minimum so the dropzone stays visible
 * for the full bar animation even when the actual parse is much faster.
 */
const MIN_DURATION_MS = 900

export function parseCsvFile(file, { onProgress, sampleSize = 200 } = {}) {
  // Validation (synchronous)
  if (!file) return Promise.reject(new Error("No file provided."))
  if (file.size > MAX_FILE_BYTES) {
    const err = new Error(
      `File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Max is 50 MB.`,
    )
    err.code = "TOO_LARGE"
    return Promise.reject(err)
  }
  if (!/\.csv$|^text\/csv$/i.test(file.name) && file.type && !/csv|text/.test(file.type)) {
    const err = new Error("Only .csv files are supported.")
    err.code = "BAD_TYPE"
    return Promise.reject(err)
  }

  // Drive the bar from 0 → 1 in 6 visible steps. Stops itself the moment
  // the real parse finishes (we clear the timers below).
  const CHECKPOINTS = [
    { p: 0.08, t:  60 },
    { p: 0.22, t: 160 },
    { p: 0.42, t: 320 },
    { p: 0.62, t: 500 },
    { p: 0.80, t: 700 },
    { p: 0.93, t: 880 },
  ]
  const timers = CHECKPOINTS.map(({ p, t }) =>
    setTimeout(() => onProgress?.(p), t),
  )

  return (async () => {
    try {
      if (onProgress) onProgress(0)
      const t0 = performance.now()
      const [text] = await Promise.all([
        awaitFileAsText(file),
        // Keep the bar visible for the full animation duration even on fast loads.
        new Promise((r) => setTimeout(r, MIN_DURATION_MS)),
      ])
      const out = parseCsvString(text, { sampleSize })
      out.parseMs = performance.now() - t0
      // Clear pending fake checkpoints; jump to 100%.
      for (const t of timers) clearTimeout(t)
      if (onProgress) onProgress(1)
      return out
    } catch (e) {
      for (const t of timers) clearTimeout(t)
      throw e
    }
  })()
}

function awaitFileAsText(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(String(r.result || ""))
    r.onerror = () => reject(new Error("Failed to read file."))
    r.readAsText(file)
  })
}

/** Comparator for a column with a known type. Empty/null always sorts last. */
export function compareValues(a, b, type, dir) {
  const aEmpty = a == null || a === ""
  const bEmpty = b == null || b === ""
  if (aEmpty && bEmpty) return 0
  if (aEmpty) return 1 // empty sinks
  if (bEmpty) return -1
  let cmp = 0
  if (type === "number") {
    const na = Number(String(a).replace(/\s/g, "").replace(/,/g, "."))
    const nb = Number(String(b).replace(/\s/g, "").replace(/,/g, "."))
    cmp = na - nb
  } else if (type === "date") {
    const ta = Date.parse(a)
    const tb = Date.parse(b)
    cmp = ta - tb
  } else {
    cmp = String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: "base" })
  }
  return dir === "desc" ? -cmp : cmp
}
