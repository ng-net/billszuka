const NUMBER_FMT = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 })
const INT_FMT = new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 })
const DATE_FMT = new Intl.DateTimeFormat(undefined, { year: "numeric", month: "short", day: "2-digit" })

/** Format a numeric cell. Empty → "". Non-numeric → original string. */
function formatNumber(v) {
  if (v == null || v === "") return ""
  const n = Number(String(v).replace(/\s/g, "").replace(/,/g, "."))
  if (Number.isNaN(n)) return String(v)
  return Number.isInteger(n) ? INT_FMT.format(n) : NUMBER_FMT.format(n)
}

/** Format a date cell. Empty → "". Unparseable → original string. */
function formatDate(v) {
  if (v == null || v === "") return ""
  const t = Date.parse(v)
  if (Number.isNaN(t)) return String(v)
  return DATE_FMT.format(new Date(t))
}

/** Render a cell with type-aware formatting (number / date / pass-through). */
export function formatCell(v, type) {
  if (v == null || v === "") return ""
  if (type === "number") return formatNumber(v)
  if (type === "date") return formatDate(v)
  return String(v)
}

/** Strip protocol + www for a clean display label. */
export function cleanUrl(v) {
  if (!v) return ""
  return String(v).replace(/^https?:\/\//i, "").replace(/^www\./, "")
}
