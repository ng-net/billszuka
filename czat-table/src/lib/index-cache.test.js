// @vitest-environment node
import { describe, it, expect } from "vitest"
import {
  buildFilterIndex,
  buildSortKeyIndex,
  matchFilterIndexed,
  makeIndexSort,
  sortRowsByIndex,
} from "./index-cache"
import { matchFilter } from "../components/type-filter"
import { compareValues } from "./csv"

const columns = [
  { id: "name", type: "text" },
  { id: "url", type: "url" },
  { id: "qty", type: "number" },
  { id: "date", type: "date" },
  { id: "tag", type: "enum" },
  { id: "misc", type: "text" },
]
const rows = [
  { name: "BILLS Sp. z o.o.", url: "https://bills.pl", qty: "100", date: "2024-01-15", tag: "A", misc: "alpha" },
  { name: "Trober Polska", url: "https://trober.de", qty: "5,5", date: "2023-06-01", tag: "B", misc: "BRAVO" },
  { name: "CK Complex", url: "ckcomplex.pl", qty: "—", date: "2024-12-31", tag: "A", misc: "Charlie" },
  { name: "Ignis Company", url: null, qty: "", date: "", tag: "C", misc: "delta" },
  { name: "BISTA Standard", url: "https://bista.pl", qty: "1 234,5", date: "2022-03-10", tag: "A", misc: "echo" },
]

describe("buildFilterIndex", () => {
  it("lowercases text/url/email/phone/enum", () => {
    const idx = buildFilterIndex(rows, columns)
    expect(idx.get("name").lower[0]).toBe("bills sp. z o.o.")
    expect(idx.get("name").lower[3]).toBe("ignis company") // row 3 has name
    expect(idx.get("url").lower[3]).toBe("") // row 3 has null url
    expect(idx.get("url").lower[0]).toBe("https://bills.pl")
    expect(idx.get("tag").lower[0]).toBe("a")
  })
  it("parses numbers (Polish comma + space-grouped thousands)", () => {
    const idx = buildFilterIndex(rows, columns)
    expect(idx.get("qty").nums[0]).toBe(100)
    expect(idx.get("qty").nums[1]).toBe(5.5)
    expect(idx.get("qty").nums[2]).toBeNaN()
    expect(idx.get("qty").nums[3]).toBeNaN()
    expect(idx.get("qty").nums[4]).toBe(1234.5)
  })
  it("parses dates to ms timestamps", () => {
    const idx = buildFilterIndex(rows, columns)
    expect(idx.get("date").dates[0]).toBe(Date.parse("2024-01-15"))
    expect(idx.get("date").dates[3]).toBeNaN()
  })
})

describe("matchFilterIndexed matches matchFilter", () => {
  const idx = buildFilterIndex(rows, columns)

  // Cases where the optimized path is supposed to give identical results to the
  // original matchFilter. Enum with array input is identical; with string
  // input the optimized version is case-insensitive substring (the original
  // is case-sensitive substring).
  const cases = [
    ["name", "bills", "text"],
    ["name", "BILLS", "text"],
    ["name", "", "text"],
    ["name", null, "text"],
    ["url", "bills.pl", "url"],
    ["url", "https", "url"],
    ["qty", { min: "10", max: "200" }, "number"],
    ["qty", { min: "1", max: "1000" }, "number"],
    ["qty", { min: "", max: "" }, "number"],
    ["date", { from: "2024-01-01", to: "2024-12-31" }, "date"],
    ["tag", ["A"], "enum"], // array input
    ["tag", [], "enum"],    // empty filter
  ]

  for (const [colId, value, type] of cases) {
    it(`col=${colId} value=${JSON.stringify(value)}`, () => {
      for (let i = 0; i < rows.length; i++) {
        const expected = matchFilter(rows[i][colId], value, type)
        const actual = matchFilterIndexed(i, colId, value, idx)
        expect(actual).toBe(expected)
      }
    })
  }
})

describe("matchFilterIndexed — enum with STRING input (text input case)", () => {
  const idx = buildFilterIndex(rows, columns)

  it("substring match (case-insensitive)", () => {
    // "A" should match all rows with tag "A" (rows 0, 2, 4)
    let n = 0
    for (let i = 0; i < rows.length; i++) {
      if (matchFilterIndexed(i, "tag", "A", idx)) n++
    }
    expect(n).toBe(3)
  })
  it("empty string passes all", () => {
    for (let i = 0; i < rows.length; i++) {
      expect(matchFilterIndexed(i, "tag", "", idx)).toBe(true)
    }
  })
  it("case-insensitive (uppercase filter, lowercase in data)", () => {
    // data: ["A", "B", "A", "C", "A"] → lower: ["a", "b", "a", "c", "a"]
    // filter "a" → 3 matches
    let n = 0
    for (let i = 0; i < rows.length; i++) {
      if (matchFilterIndexed(i, "tag", "a", idx)) n++
    }
    expect(n).toBe(3)
  })
})

describe("sortRowsByIndex (text + date + multi-col where data has no empties)", () => {
  const sortKeyIdx = buildSortKeyIndex(rows, columns)

  const cases = [
    [{ colId: "name", dir: "asc" }],
    [{ colId: "name", dir: "desc" }],
    [{ colId: "date", dir: "asc" }],
    [{ colId: "date", dir: "desc" }],
    [
      { colId: "tag", dir: "asc" },
      { colId: "name", dir: "asc" },
    ],
  ]

  for (const sort of cases) {
    it(`sort=${JSON.stringify(sort)}`, () => {
      const expected = [...rows].sort((a, b) => {
        for (const s of sort) {
          const c = compareValues(a[s.colId], b[s.colId], columns.find((x) => x.id === s.colId).type, s.dir)
          if (c !== 0) return c
        }
        return 0
      })
      const actual = sortRowsByIndex(rows, sort, sortKeyIdx)
      expect(actual.map((r) => r.name)).toEqual(expected.map((r) => r.name))
    })
  }
})

describe("sortRowsByIndex (number column with empty values — empty sinks deterministically)", () => {
  const sortKeyIdx = buildSortKeyIndex(rows, columns)

  // The original compareValues has undefined behavior when comparing NaN to
  // a number (NaN - n = NaN, so the comparator is unstable for empty cells).
  // The optimized version explicitly puts empties last. We test that property
  // directly rather than asserting parity with the original.
  it("asc: empties sink to the bottom", () => {
    const result = sortRowsByIndex(rows, [{ colId: "qty", dir: "asc" }], sortKeyIdx)
    const lastTwo = result.slice(-2).map((r) => r.name)
    // Both CK Complex and Ignis have empty/NaN qty — they should be at the end
    expect(lastTwo).toContain("CK Complex")
    expect(lastTwo).toContain("Ignis Company")
    // Non-empty values come first
    const firstThree = result.slice(0, 3).map((r) => r.name)
    expect(firstThree).toContain("Trober Polska")   // 5.5
    expect(firstThree).toContain("BILLS Sp. z o.o.") // 100
    expect(firstThree).toContain("BISTA Standard")   // 1234.5
  })

  it("desc: empties still sink to the bottom", () => {
    const result = sortRowsByIndex(rows, [{ colId: "qty", dir: "desc" }], sortKeyIdx)
    const lastTwo = result.slice(-2).map((r) => r.name)
    expect(lastTwo).toContain("CK Complex")
    expect(lastTwo).toContain("Ignis Company")
  })
})

describe("sort stability", () => {
  it("preserves original order on ties (uses index as tiebreaker)", () => {
    const dupRows = [
      { name: "A", qty: "1" },
      { name: "B", qty: "1" },
      { name: "C", qty: "1" },
    ]
    const sortKeyIdx = buildSortKeyIndex(dupRows, [{ id: "qty", type: "number" }])
    const result = sortRowsByIndex(dupRows, [{ colId: "qty", dir: "asc" }], sortKeyIdx)
    expect(result.map((r) => r.name)).toEqual(["A", "B", "C"])
  })
})

describe("edge cases", () => {
  it("empty sort array returns rows unchanged", () => {
    const sortKeyIdx = buildSortKeyIndex(rows, columns)
    expect(sortRowsByIndex(rows, [], sortKeyIdx)).toBe(rows)
  })
  it("sort column not in index is skipped", () => {
    const sortKeyIdx = buildSortKeyIndex(rows, columns)
    const result = sortRowsByIndex(rows, [{ colId: "nonexistent", dir: "asc" }], sortKeyIdx)
    expect(result.length).toBe(rows.length)
  })
  it("null filter passes all rows", () => {
    const idx = buildFilterIndex(rows, columns)
    for (let i = 0; i < rows.length; i++) {
      expect(matchFilterIndexed(i, "name", null, idx)).toBe(true)
    }
  })
})
