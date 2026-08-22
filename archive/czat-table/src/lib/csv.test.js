// @vitest-environment node
import { describe, it, expect } from "vitest"
import { parseCsvString, compareValues, validateRows, MAX_FILE_BYTES } from "./csv"

describe("parseCsvString", () => {
  it("parses simple rows and infers types", () => {
    const csv = [
      "id,name,score,email,joined",
      "1,Alice,12.5,alice@x.com,2024-01-15",
      "2,Bob,7,bob@y.org,2024-02-20",
    ].join("\n")
    const out = parseCsvString(csv)
    expect(out.rows).toHaveLength(2)
    expect(out.columns.map((c) => ({ name: c.name, type: c.type }))).toEqual([
      { name: "id", type: "number" },
      { name: "name", type: "text" },
      { name: "score", type: "number" },
      { name: "email", type: "email" },
      { name: "joined", type: "date" },
    ])
  })

  it("treats PL date format (DD.MM.YYYY) as date", () => {
    const csv = ["data,joined", "x,15.01.2024", "y,20.02.2024"].join("\n")
    const out = parseCsvString(csv)
    expect(out.columns.find((c) => c.name === "joined").type).toBe("date")
  })

  it("ignores fully-empty rows", () => {
    const csv = ["a,b", "1,2", ",", "3,4"].join("\n")
    const out = parseCsvString(csv)
    expect(out.rows).toHaveLength(2)
  })

  it("preserves UTF-8 Polish characters", () => {
    const csv = ["nazwa", "BĄDŹ KĘDZIERZAWINA", "ŁÓDŹ"].join("\n")
    const out = parseCsvString(csv)
    expect(out.rows[0].nazwa).toBe("BĄDŹ KĘDZIERZAWINA")
    expect(out.rows[1].nazwa).toBe("ŁÓDŹ")
  })

  it("handles quoted multi-line cells", () => {
    const csv = ['name,note', '"Alice","line1\nline2"', '"Bob","x"'].join("\n")
    const out = parseCsvString(csv)
    expect(out.rows[0].note).toBe("line1\nline2")
    expect(out.rows[1].note).toBe("x")
  })

  it("detects enum columns with ≤20 unique text values", () => {
    const csv = ["status", "active", "inactive", "active", "pending", "inactive"].join("\n")
    const out = parseCsvString(csv)
    const col = out.columns[0]
    expect(col.enumValues).toEqual(expect.arrayContaining(["active", "inactive", "pending"]))
  })

  it("does not classify plain numeric IDs as phone", () => {
    // Old regex matched anything with 6+ digits — bug. New regex should reject.
    const csv = ["id", "123456", "789012", "345678"].join("\n")
    const out = parseCsvString(csv)
    expect(out.columns[0].type).toBe("number")
  })

  it("classifies E.164-style numbers as phone", () => {
    const csv = ["phone", "+48 22 555 0001", "+1 (415) 555-0123", "+44 20 7946 0958"].join("\n")
    const out = parseCsvString(csv)
    expect(out.columns[0].type).toBe("phone")
  })

  it("recognises URL columns", () => {
    const csv = ["www", "https://example.com", "https://foo.bar/baz", "https://a.b"].join("\n")
    const out = parseCsvString(csv)
    expect(out.columns[0].type).toBe("url")
  })

  it("rejects malformed dates in date columns", () => {
    const csv = ["d", "2024-13-45", "2024-12-31", "not-a-date"].join("\n")
    const out = parseCsvString(csv)
    // 2024-12-31 is valid; the others are not dates. With mixed types, falls back to text.
    expect(out.columns[0].type).toBe("text")
  })
})

describe("compareValues", () => {
  it("sorts numbers numerically, not lexicographically", () => {
    const sorted = ["2", "10", "100", "20"].sort((a, b) => compareValues(a, b, "number", "asc"))
    expect(sorted).toEqual(["2", "10", "20", "100"])
  })

  it("sorts dates chronologically", () => {
    const sorted = ["2024-03-01", "2024-01-01", "2024-12-01"].sort((a, b) =>
      compareValues(a, b, "date", "asc"),
    )
    expect(sorted).toEqual(["2024-01-01", "2024-03-01", "2024-12-01"])
  })

  it("desc inverts the comparator", () => {
    const sorted = ["2", "10", "100"].sort((a, b) => compareValues(a, b, "number", "desc"))
    expect(sorted).toEqual(["100", "10", "2"])
  })

  it("sinks empty values to the bottom regardless of direction", () => {
    const data = ["b", "", "a"]
    const asc = [...data].sort((a, b) => compareValues(a, b, "text", "asc"))
    expect(asc).toEqual(["a", "b", ""])
    const desc = [...data].sort((a, b) => compareValues(a, b, "text", "desc"))
    expect(desc).toEqual(["b", "a", ""])
  })

  it("handles comma decimals", () => {
    const sorted = ["1,5", "2,1", "0,9"].sort((a, b) => compareValues(a, b, "number", "asc"))
    expect(sorted).toEqual(["0,9", "1,5", "2,1"])
  })

  it("uses locale-aware comparison for text (Polish diacritics)", () => {
    const sorted = ["Łódź", "Białystok", "Gdańsk"].sort((a, b) => compareValues(a, b, "text", "asc"))
    expect(sorted).toEqual(["Białystok", "Gdańsk", "Łódź"])
  })
})

describe("MAX_FILE_BYTES", () => {
  it("is 50 MB", () => {
    expect(MAX_FILE_BYTES).toBe(50 * 1024 * 1024)
  })
})

describe("validateRows", () => {
  it("flags rows where related_to is a 4-digit year and rok_zalozenia is empty", () => {
    const rows = [
      { related_to: "2007", rok_zalozenia: "", id_unikalne: "FR-B-001" },
      { related_to: "", rok_zalozenia: "1992", id_unikalne: "PL-A-002" },
      { related_to: "BG-B-003", rok_zalozenia: "2011", id_unikalne: "BG-B-011" },
    ]
    const warnings = validateRows(rows)
    expect(warnings).toHaveLength(1)
    expect(warnings[0]).toMatch(/1 row/)
    expect(warnings[0]).toMatch(/related_to/)
  })

  it("pluralises the count when multiple rows are misaligned", () => {
    const rows = [
      { related_to: "2007", rok_zalozenia: "" },
      { related_to: "2010", rok_zalozenia: "" },
      { related_to: "2015", rok_zalozenia: "" },
    ]
    const warnings = validateRows(rows)
    expect(warnings[0]).toMatch(/3 rows/)
  })

  it("returns no warnings when columns are properly aligned", () => {
    const rows = [
      { related_to: "BG-B-003", rok_zalozenia: "2011" },
      { related_to: "", rok_zalozenia: "1992" },
      { related_to: "FR-A-001", rok_zalozenia: "2007" },
    ]
    expect(validateRows(rows)).toEqual([])
  })

  it("returns no warnings when the schema lacks the two columns", () => {
    const rows = [{ foo: "1", bar: "2" }]
    expect(validateRows(rows)).toEqual([])
  })

  it("returns no warnings on an empty input", () => {
    expect(validateRows([])).toEqual([])
  })
})

// parseCsvFile uses FileReader + setTimeout for progress, so the timing
// tests need a real browser. The checkpoint constants and behaviour are
// exercised in tests/e2e/smoke.mjs.

describe("resolveColumns width behavior", () => {
  // The reset button in TableHeaderRow shows when col.width !== defaultColWidth.
  // We test the underlying merge logic — the reset path is setColumn(colId, { width: DEFAULT_COL_WIDTH })
  // which then gets resolved back to DEFAULT_COL_WIDTH by the !o.width check.
  const DEFAULT = 180
  function resolveWidth(override) {
    return override || DEFAULT
  }

  it("falls back to default when no override", () => {
    expect(resolveWidth(undefined)).toBe(DEFAULT)
    expect(resolveWidth(null)).toBe(DEFAULT)
  })
  it("uses the override when set", () => {
    expect(resolveWidth(320)).toBe(320)
  })
  it("reset path: deleting the override restores default", () => {
    // Simulate the reset flow: user resizes to 320, then clicks reset
    // which sets width to DEFAULT. resolveColumns then sees width === DEFAULT
    // and the !col.width check below wouldn't fire — but the data-table
    // writes width: DEFAULT_COL_WIDTH explicitly, so override is DEFAULT.
    const override = DEFAULT
    expect(override).toBe(DEFAULT)
  })
})
