// Quick performance sanity-check. Run with: node src/lib/bench.mjs
// Compares current matchFilter+compareValues vs. precomputed-index versions
// on a realistic 394-row × 35-col dataset.

import { parseCsvString } from "./csv.js"
import { readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"
import { dirname, join } from "node:path"

const __dirname = dirname(fileURLToPath(import.meta.url))
const csvText = readFileSync(join(__dirname, "..", "..", "..", "data", "master.csv"), "utf8")
const { rows, columns } = parseCsvString(csvText)
console.log(`Dataset: ${rows.length} rows × ${columns.length} columns`)

const columnsById = new Map(columns.map(c => [c.id, c]))

// ─── CURRENT: matchFilter (from type-filter.jsx) ─────────────────────────
function matchFilterCurrent(rowValue, filterValue, type) {
  if (filterValue == null) return true
  const v = rowValue == null ? "" : String(rowValue)
  if (type === "text" || type === "url" || type === "email" || type === "phone") {
    if (filterValue === "") return true
    return v.toLowerCase().includes(String(filterValue).toLowerCase())
  }
  if (type === "number") {
    if (!filterValue.min && !filterValue.max) return true
    const n = Number(v.replace(/\s/g, "").replace(/,/g, "."))
    if (Number.isNaN(n)) return false
    if (filterValue.min !== "" && n < Number(filterValue.min)) return false
    if (filterValue.max !== "" && n > Number(filterValue.max)) return false
    return true
  }
  if (type === "date") {
    if (!filterValue.from && !filterValue.to) return true
    const t = Date.parse(v)
    if (Number.isNaN(t)) return false
    if (filterValue.from && t < Date.parse(filterValue.from)) return false
    if (filterValue.to && t > Date.parse(filterValue.to) + 86_400_000) return false
    return true
  }
  if (type === "enum") {
    if (!filterValue || filterValue.length === 0) return true
    return filterValue.includes(v)
  }
  return true
}

function compareValuesCurrent(a, b, type, dir) {
  const aEmpty = a == null || a === ""
  const bEmpty = b == null || b === ""
  if (aEmpty && bEmpty) return 0
  if (aEmpty) return 1
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

// ─── OPTIMIZED: precomputed index ────────────────────────────────────────
// Build per-row, per-col pre-normalized values once.

const COLS_TEXT = ["text", "url", "email", "phone", "enum"]
const filterIdx = new Map()
for (const col of columns) {
  if (COLS_TEXT.includes(col.type)) {
    const lower = new Array(rows.length)
    for (let i = 0; i < rows.length; i++) {
      const v = rows[i][col.id]
      lower[i] = v == null ? "" : String(v).toLowerCase()
    }
    filterIdx.set(col.id, { type: col.type, lower })
  } else if (col.type === "number") {
    const nums = new Array(rows.length)
    for (let i = 0; i < rows.length; i++) {
      const v = rows[i][col.id]
      if (v == null || v === "") nums[i] = NaN
      else nums[i] = Number(String(v).replace(/\s/g, "").replace(/,/g, "."))
    }
    filterIdx.set(col.id, { type: col.type, nums })
  } else if (col.type === "date") {
    const dates = new Array(rows.length)
    for (let i = 0; i < rows.length; i++) {
      const v = rows[i][col.id]
      dates[i] = v == null || v === "" ? NaN : Date.parse(v)
    }
    filterIdx.set(col.id, { type: col.type, dates })
  }
}

// Intl.Collator instance — 3-5× faster than localeCompare with options
const COLLATOR = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" })

// Pre-compute sort keys per column (parallel array, indexed by row)
const sortKeys = new Map()
for (const col of columns) {
  if (COLS_TEXT.includes(col.type)) {
    const k = new Array(rows.length)
    for (let i = 0; i < rows.length; i++) {
      const v = rows[i][col.id]
      k[i] = v == null ? "" : String(v).toLowerCase()
    }
    sortKeys.set(col.id, k)
  } else if (col.type === "number") {
    const k = new Array(rows.length)
    for (let i = 0; i < rows.length; i++) {
      const v = rows[i][col.id]
      k[i] = v == null || v === "" ? NaN : Number(String(v).replace(/\s/g, "").replace(/,/g, "."))
    }
    sortKeys.set(col.id, k)
  } else if (col.type === "date") {
    const k = new Array(rows.length)
    for (let i = 0; i < rows.length; i++) {
      const v = rows[i][col.id]
      k[i] = v == null || v === "" ? NaN : Date.parse(v)
    }
    sortKeys.set(col.id, k)
  }
}

function matchFilterOpt(rowIdx, colId, filterValue) {
  if (filterValue == null) return true
  const idx = filterIdx.get(colId)
  if (!idx) return true
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
    return filterValue.includes(String(rows[rowIdx][colId] ?? ""))
  }
  return true
}

function makeSortOpt(sort) {
  if (sort.length === 0) return null
  return (ai, bi) => {
    for (const s of sort) {
      const ks = sortKeys.get(s.colId)
      if (!ks) continue
      const a = ks[ai]
      const b = ks[bi]
      const aEmpty = a === "" || (typeof a === "number" && Number.isNaN(a))
      const bEmpty = b === "" || (typeof b === "number" && Number.isNaN(b))
      let cmp
      if (aEmpty && bEmpty) cmp = 0
      else if (aEmpty) cmp = 1
      else if (bEmpty) cmp = -1
      else if (typeof a === "number") cmp = a - b
      else cmp = COLLATOR.compare(a, b)
      if (cmp !== 0) return s.dir === "desc" ? -cmp : cmp
    }
    return ai - bi
  }
}

// ─── BENCHMARKS ─────────────────────────────────────────────────────────
function bench(label, fn, runs = 5) {
  const times = []
  for (let i = 0; i < runs; i++) {
    const t0 = performance.now()
    const result = fn()
    times.push(performance.now() - t0)
  }
  times.sort((a, b) => a - b)
  const median = times[Math.floor(times.length / 2)]
  console.log(`  ${label}: ${median.toFixed(2)}ms (min ${times[0].toFixed(2)} / max ${times[times.length - 1].toFixed(2)}) result=${typeof result === "number" ? result : "—"}`)
  return median
}

// Test 1: text filter on "nazwa_firmy" with "SPÓŁKA"
console.log("\n--- Filter: text contains 'SPÓŁKA' on 'nazwa_firmy' ---")
bench("current", () => {
  return rows.filter(r => matchFilterCurrent(r["nazwa_firmy"], "SPÓŁKA", "text")).length
})
bench("optimized", () => {
  let n = 0
  for (let i = 0; i < rows.length; i++) if (matchFilterOpt(i, "nazwa_firmy", "SPÓŁKA")) n++
  return n
})

// Test 2: number filter
console.log("\n--- Filter: number range (100-999) on 'nip_vat' (won't match but tests path) ---")
bench("current", () => {
  return rows.filter(r => matchFilterCurrent(r["nip_vat"], { min: "100", max: "999" }, "number")).length
})
bench("optimized", () => {
  let n = 0
  for (let i = 0; i < rows.length; i++) if (matchFilterOpt(i, "nip_vat", { min: "100", max: "999" })) n++
  return n
})

// Test 3: multi-column text filter (3 text filters)
console.log("\n--- Filter: 3 text filters (nazwa_firmy + email + miasto) ---")
bench("current", () => {
  return rows.filter(r =>
    matchFilterCurrent(r["nazwa_firmy"], "SPÓŁKA", "text") &&
    matchFilterCurrent(r["email"], "biuro", "text") &&
    matchFilterCurrent(r["miasto"], "WAR", "text")
  ).length
})
bench("optimized", () => {
  let n = 0
  for (let i = 0; i < rows.length; i++) {
    if (matchFilterOpt(i, "nazwa_firmy", "SPÓŁKA") &&
        matchFilterOpt(i, "email", "biuro") &&
        matchFilterOpt(i, "miasto", "WAR")) n++
  }
  return n
})

// Test 4: single-column text sort
console.log("\n--- Sort: text column 'nazwa_firmy' asc ---")
bench("current", () => {
  const arr = [...rows]
  arr.sort((a, b) => compareValuesCurrent(a["nazwa_firmy"], b["nazwa_firmy"], "text", "asc"))
  return arr.length
})
bench("optimized", () => {
  const indices = new Array(rows.length)
  for (let i = 0; i < rows.length; i++) indices[i] = i
  indices.sort(makeSortOpt([{ colId: "nazwa_firmy", dir: "asc" }]))
  return indices.length
})

// Test 5: 3-column multi-sort
console.log("\n--- Sort: 3 columns (kraj + miasto + nazwa_firmy) ---")
const sort3 = [
  { colId: "kraj", dir: "asc" },
  { colId: "miasto", dir: "asc" },
  { colId: "nazwa_firmy", dir: "asc" },
]
bench("current", () => {
  const arr = [...rows]
  arr.sort((a, b) => {
    for (const s of sort3) {
      const cmp = compareValuesCurrent(a[s.colId], b[s.colId], "text", s.dir)
      if (cmp !== 0) return cmp
    }
    return 0
  })
  return arr.length
})
bench("optimized", () => {
  const indices = new Array(rows.length)
  for (let i = 0; i < rows.length; i++) indices[i] = i
  indices.sort(makeSortOpt(sort3))
  return indices.length
})

// Test 6: number sort
console.log("\n--- Sort: number column 'nip_vat' (numeric) ---")
bench("current", () => {
  const arr = [...rows]
  arr.sort((a, b) => compareValuesCurrent(a["nip_vat"], b["nip_vat"], "number", "asc"))
  return arr.length
})
bench("optimized", () => {
  const indices = new Array(rows.length)
  for (let i = 0; i < rows.length; i++) indices[i] = i
  indices.sort(makeSortOpt([{ colId: "nip_vat", dir: "asc" }]))
  return indices.length
})

// Test 7: filter + sort combined (most realistic flow)
console.log("\n--- Combined: filter (text on nazwa + email) THEN sort (3 cols) ---")
bench("current", () => {
  const filtered = rows.filter(r =>
    matchFilterCurrent(r["nazwa_firmy"], "SPÓŁKA", "text") &&
    matchFilterCurrent(r["email"], "biuro", "text")
  )
  filtered.sort((a, b) => {
    for (const s of sort3) {
      const cmp = compareValuesCurrent(a[s.colId], b[s.colId], "text", s.dir)
      if (cmp !== 0) return cmp
    }
    return 0
  })
  return filtered.length
})
bench("optimized", () => {
  const kept = []
  for (let i = 0; i < rows.length; i++) {
    if (matchFilterOpt(i, "nazwa_firmy", "SPÓŁKA") && matchFilterOpt(i, "email", "biuro")) {
      kept.push(i)
    }
  }
  kept.sort(makeSortOpt(sort3))
  return kept.length
})

// Index build cost (one-time per dataset)
console.log("\n--- Index build (one-time per data.rows reference) ---")
const t0 = performance.now()
let dummySum = 0
for (const col of columns) {
  if (COLS_TEXT.includes(col.type)) {
    const lower = new Array(rows.length)
    for (let i = 0; i < rows.length; i++) lower[i] = String(rows[i][col.id] ?? "").toLowerCase()
    dummySum += lower.length
  }
}
console.log(`  text lowercasing (${columns.length} cols): ${(performance.now() - t0).toFixed(2)}ms (sum=${dummySum})`)
