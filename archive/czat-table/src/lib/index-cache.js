// Pre-computed column indexes for fast filter + sort.
//
// Building the index is O(rows × textCols) work (one pass through the dataset
// to lowercase strings / parse numbers / parse dates). After that, every
// filter keystroke and sort operation is a tight array lookup instead of
// re-converting strings per call.
//
// Bench (master.csv 394 rows × 35 cols):
//   text filter 1 col:        0.40ms → 0.16ms   (2.5×)
//   text filter 3 cols:       0.41ms → 0.17ms   (2.4×)
//   sort 1 col text:         39.24ms → 2.28ms  (17×)
//   sort 3 cols text:        56.24ms → 1.76ms  (32×)
//   filter+sort combined:     0.80ms → 0.30ms   (2.7×)
//   index build (one-time):       — → 3.68ms

const TEXT_TYPES = new Set(["text", "url", "email", "phone", "enum"])

// Reused across sort/filter comparators — Intl.Collator instance is 3-5×
// faster than `String(a).localeCompare(String(b), undefined, { numeric: true })`
// because we don't re-parse the options object on every call.
const TEXT_COLLATOR =
  typeof Intl !== "undefined" && Intl.Collator
    ? new Intl.Collator(undefined, { numeric: true, sensitivity: "base" })
    : null

/**
 * Build a per-column index of pre-normalized values for fast filter checks.
 *   - text/url/email/phone/enum → lowercased string array
 *   - number → parsed number array (NaN = empty)
 *   - date   → ms timestamp array (NaN = empty)
 *   - other  → not indexed; filter falls back to per-cell match
 *
 * @param {Array<object>} rows
 * @param {Array<{id: string, type: string}>} columns
 * @returns {Map<string, {type: string, lower?: string[], nums?: number[], dates?: number[]}>}
 */
export function buildFilterIndex(rows, columns) {
  const idx = new Map()
  for (const col of columns) {
    if (TEXT_TYPES.has(col.type)) {
      const lower = new Array(rows.length)
      for (let i = 0; i < rows.length; i++) {
        const v = rows[i][col.id]
        lower[i] = v == null ? "" : String(v).toLowerCase()
      }
      idx.set(col.id, { type: col.type, lower })
    } else if (col.type === "number") {
      const nums = new Array(rows.length)
      for (let i = 0; i < rows.length; i++) {
        const v = rows[i][col.id]
        if (v == null || v === "") nums[i] = NaN
        else nums[i] = Number(String(v).replace(/\s/g, "").replace(/,/g, "."))
      }
      idx.set(col.id, { type: col.type, nums })
    } else if (col.type === "date") {
      const dates = new Array(rows.length)
      for (let i = 0; i < rows.length; i++) {
        const v = rows[i][col.id]
        dates[i] = v == null || v === "" ? NaN : Date.parse(v)
      }
      idx.set(col.id, { type: col.type, dates })
    }
  }
  return idx
}

/**
 * Pre-compute per-column sort keys (parallel arrays indexed by row).
 * For text columns: lowercased string. For numbers: parsed number. For dates: timestamp.
 * Empty/missing values are normalized to "" (text) or NaN (number/date) so the
 * comparator can treat them consistently.
 */
export function buildSortKeyIndex(rows, columns) {
  const idx = new Map()
  for (const col of columns) {
    if (TEXT_TYPES.has(col.type)) {
      const k = new Array(rows.length)
      for (let i = 0; i < rows.length; i++) {
        const v = rows[i][col.id]
        k[i] = v == null ? "" : String(v).toLowerCase()
      }
      idx.set(col.id, k)
    } else if (col.type === "number") {
      const k = new Array(rows.length)
      for (let i = 0; i < rows.length; i++) {
        const v = rows[i][col.id]
        k[i] = v == null || v === "" ? NaN : Number(String(v).replace(/\s/g, "").replace(/,/g, "."))
      }
      idx.set(col.id, k)
    } else if (col.type === "date") {
      const k = new Array(rows.length)
      for (let i = 0; i < rows.length; i++) {
        const v = rows[i][col.id]
        k[i] = v == null || v === "" ? NaN : Date.parse(v)
      }
      idx.set(col.id, k)
    }
  }
  return idx
}

/**
 * Filter predicate using the pre-computed index. Returns true if the row
 * at `rowIdx` passes the `colId` filter.
 *
 *   matchFilterIndexed(rowIdx, "nazwa_firmy", "SPÓŁKA", index)
 *   matchFilterIndexed(rowIdx, "nip_vat",      {min:"100",max:"999"}, index)
 */
export function matchFilterIndexed(rowIdx, colId, filterValue, index) {
  if (filterValue == null) return true
  const idx = index.get(colId)
  if (!idx) return true // unindexed type — let it pass; UI doesn't filter unknown types
  if (idx.type === "text" || idx.type === "url" || idx.type === "email" || idx.type === "phone") {
    if (filterValue === "") return true
    return idx.lower[rowIdx].includes(String(filterValue).toLowerCase())
  }
  if (idx.type === "number") {
    if (!filterValue.min && !filterValue.max) return true
    const n = idx.nums[rowIdx]
    if (Number.isNaN(n)) return false
    if (filterValue.min !== "" && n < Number(filterValue.min)) return false
    if (filterValue.max !== "" && n > Number(filterValue.max)) return false
    return true
  }
  if (idx.type === "date") {
    if (!filterValue.from && !filterValue.to) return true
    const t = idx.dates[rowIdx]
    if (Number.isNaN(t)) return false
    if (filterValue.from && t < Date.parse(filterValue.from)) return false
    if (filterValue.to && t > Date.parse(filterValue.to) + 86_400_000) return false
    return true
  }
  if (idx.type === "enum") {
    if (!filterValue || filterValue.length === 0) return true
    // Support both: string filter (substring match, like text input) and
    // array filter (membership, e.g. from a multi-select dropdown).
    const lo = idx.lower[rowIdx]
    if (typeof filterValue === "string") {
      if (filterValue === "") return true
      return lo.includes(filterValue.toLowerCase())
    }
    return filterValue.some((v) => String(v).toLowerCase() === lo)
  }
  return true
}

/**
 * Sort an array of ROW INDICES using the pre-computed sort key index.
 * Returns a new sorted array of indices. The original rows array is untouched,
 * so the caller can map back: `sortedIdx.map(i => rows[i])`.
 *
 * Supports multi-column sort: each `{colId, dir}` is applied in order, the
 * first non-zero comparison wins. Empty values always sink to the bottom.
 */
export function makeIndexSort(sort, sortKeyIndex) {
  if (sort.length === 0) return null
  return (ai, bi) => {
    for (const s of sort) {
      const ks = sortKeyIndex.get(s.colId)
      if (!ks) continue
      const a = ks[ai]
      const b = ks[bi]
      const aEmpty = a === "" || (typeof a === "number" && Number.isNaN(a))
      const bEmpty = b === "" || (typeof b === "number" && Number.isNaN(b))
      // Empty values always sink to the bottom — handle BEFORE the direction
      // flip, so ASC and DESC both place empties at the end (matches the
      // current compareValues behavior, and is what users expect).
      if (aEmpty && bEmpty) continue
      if (aEmpty) return 1
      if (bEmpty) return -1
      let cmp
      if (typeof a === "number") cmp = a - b
      else if (TEXT_COLLATOR) cmp = TEXT_COLLATOR.compare(a, b)
      else cmp = a < b ? -1 : a > b ? 1 : 0
      if (cmp !== 0) return s.dir === "desc" ? -cmp : cmp
    }
    // Stable tiebreaker: original order
    return ai - bi
  }
}

/** Convenience: sort rows by the indexed comparator, return reordered rows. */
export function sortRowsByIndex(rows, sort, sortKeyIndex) {
  if (sort.length === 0) return rows
  const indices = new Array(rows.length)
  for (let i = 0; i < rows.length; i++) indices[i] = i
  const cmp = makeIndexSort(sort, sortKeyIndex)
  indices.sort(cmp)
  return indices.map((i) => rows[i])
}
