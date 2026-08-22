// End-to-end smoke test for czat-table.
// Spins up the running dev server (assumed on http://localhost:5173), drives a
// few interactions via Puppeteer, and screenshots the result. Exits non-zero on
// any console/page error or failed expectation.
//
// Usage: pnpm dev (in another terminal) && pnpm test:e2e

import puppeteer from "puppeteer-core"
import { mkdirSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const __dirname = dirname(fileURLToPath(import.meta.url))
const URL = process.env.E2E_URL || "http://localhost:5173/"
const SHOTS = resolve(__dirname, "shots")
mkdirSync(SHOTS, { recursive: true })

const browser = await puppeteer.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: "new",
  args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
})

const errors = []
let exitCode = 0

function fail(msg) {
  console.error(`✗ ${msg}`)
  exitCode = 1
}
function pass(msg) {
  console.log(`✓ ${msg}`)
}

try {
  const page = await browser.newPage()
  await page.setViewport({ width: 1400, height: 900, deviceScaleFactor: 1 })
  page.on("pageerror", (e) => errors.push(`[pageerror] ${e.message}`))
  page.on("console", (m) => {
    if (m.type() === "error") {
      const txt = m.text()
      // Favicon 404 is expected; ignore.
      if (!/favicon/i.test(txt)) errors.push(`[console.error] ${txt}`)
    } else if (m.type() === "log" && /\[czat\]/.test(m.text())) {
      console.log("  " + m.text())
    }
  })

  // 1. Load + clear prefs + try sample
  await page.goto(URL, { waitUntil: "networkidle0", timeout: 30000 })
  await page.evaluate(() => localStorage.clear())
  await page.reload({ waitUntil: "networkidle0" })
  await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find((b) =>
      /try sample/i.test(b.textContent || ""),
    )
    btn?.click()
  })
  await new Promise((r) => setTimeout(r, 2500))
  const loaded = await page.evaluate(() => {
    // Master.csv row count varies as the dataset grows. Accept any 3-digit
    // number in the "Loaded N rows" toast.
    return /Loaded\s+\d{2,4}\s+rows/.test(document.body.innerText)
  })
  if (loaded) {
    const m = await page.evaluate(() => document.body.innerText.match(/Loaded\s+(\d+)\s+rows/)?.[0])
    pass(`Try sample: ${m}`)
  } else {
    fail("Try sample did not load rows")
  }
  await page.screenshot({ path: `${SHOTS}/01-loaded.png` })

  // 2. Sort by KRAJ header
  await page.evaluate(() => {
    const heads = [...document.querySelectorAll("thead th button")]
    const kraj = heads.find((b) => /kraj/i.test(b.textContent || ""))
    kraj?.click()
  })
  await new Promise((r) => setTimeout(r, 500))
  const sorted = await page.evaluate(() => {
    const stack = document.body.innerText.match(/Sort:\s+(\d+\s+\w+)/)
    return stack ? stack[1] : null
  })
  if (sorted) pass(`Single-column sort applied: ${sorted}`)
  else fail("Single-column sort did not show in sort stack")

  // 3. Multi-sort (shift+click)
  await page.evaluate(() => {
    const heads = [...document.querySelectorAll("thead th button")]
    const name = heads.find((b) => /nazwa_firmy/i.test(b.textContent || ""))
    if (name) {
      const evt = new MouseEvent("click", { bubbles: true, shiftKey: true })
      name.dispatchEvent(evt)
    }
  })
  await new Promise((r) => setTimeout(r, 500))
  const multi = await page.evaluate(() => {
    return /Sort:\s+1\s+\w+\s+2\s+\w+/.test(document.body.innerText)
  })
  if (multi) pass("Multi-column sort works (kraj + nazwa_firmy)")
  else fail("Multi-column sort not visible")
  await page.screenshot({ path: `${SHOTS}/02-multisort.png` })

  // 4. Filter via kategoria column
  // Capture the original total BEFORE applying the filter, so we can verify
  // the filter actually reduced the row count.
  const totalBefore = await page.evaluate(() => {
    const m = document.body.innerText.match(/of\s+([\d,]+)\s+rows/)
    return m ? Number(m[1].replace(/,/g, "")) : 0
  })
  await page.evaluate(() => {
    const input = document.querySelector("input[aria-label='Filter kategoria']")
    if (input) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set
      setter.call(input, "A4")
      input.dispatchEvent(new Event("input", { bubbles: true }))
    }
  })
  await new Promise((r) => setTimeout(r, 2000))
  const filtered = await page.evaluate(() => {
    const m = document.body.innerText.match(/Showing\s+(\d+)[–\-](\d+)\s+of\s+(\d+)\s+rows/)
    if (!m) return null
    const total = Number(m[3])
    return { range: m[0], total }
  })
  if (filtered && totalBefore > 0 && filtered.total < totalBefore) {
    pass(`Filter applied: ${filtered.range} (${totalBefore} → ${filtered.total} rows)`)
  } else {
    fail(`Filter did not reduce rows (before=${totalBefore}, after=${filtered?.total ?? "?"})`)
  }
  // Page should have auto-reset to 1
  const pageReset = await page.evaluate(() => {
    return /Page\s+1\s+of\s+1/.test(document.body.innerText)
  })
  if (pageReset) pass("Page auto-reset to 1 on filter change")
  else fail("Page did not auto-reset to 1 on filter change")

  // 5. Keyboard navigation: focus body, press ArrowDown 2x, ArrowRight
  await page.evaluate(() => {
    const filter = document.querySelector("input[aria-label='Filter kategoria']")
    if (filter) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set
      setter.call(filter, "")
      filter.dispatchEvent(new Event("input", { bubbles: true }))
    }
    document.querySelector("[data-scroll-body]")?.focus()
  })
  await new Promise((r) => setTimeout(r, 200))
  await page.keyboard.press("ArrowDown")
  await page.keyboard.press("ArrowDown")
  await page.keyboard.press("ArrowRight")
  await new Promise((r) => setTimeout(r, 200))
  const kb = await page.evaluate(() => {
    const c = document.querySelector(".ring-primary")
    return c ? { r: c.getAttribute("data-cell-row"), col: c.getAttribute("data-cell-col") } : null
  })
  if (kb?.r === "2" && kb?.col === "1") pass("Keyboard nav: row 2, col 1 highlighted")
  else fail(`Keyboard nav wrong: ${JSON.stringify(kb)}`)

  // 6. Enter to copy
  // Re-focus the body in case the focus drifted.
  await page.evaluate(() => document.querySelector("[data-scroll-body]")?.focus())
  await new Promise((r) => setTimeout(r, 100))
  const beforeEnter = await page.evaluate(() => ({
    active: document.activeElement?.tagName + "[" + (document.activeElement?.getAttribute("data-scroll-body") || "") + "]",
    selected: (() => {
      const c = document.querySelector(".ring-primary")
      return c ? { r: c.getAttribute("data-cell-row"), col: c.getAttribute("data-cell-col") } : null
    })(),
  }))
  console.log("  pre-Enter state:", JSON.stringify(beforeEnter))
  await page.keyboard.press("Enter")
  await new Promise((r) => setTimeout(r, 600))
  const toastShown = await page.evaluate(() => {
    return /Copied/i.test(document.body.innerText)
  })
  if (toastShown) pass("Enter triggers copy toast")
  else fail("Enter did not trigger copy toast")
  await page.screenshot({ path: `${SHOTS}/03-keyboard.png` })

  // 7. Cmd+F to focus filter
  await page.keyboard.down("Meta")
  await page.keyboard.press("f")
  await page.keyboard.up("Meta")
  await new Promise((r) => setTimeout(r, 200))
  const focused = await page.evaluate(() => {
    const el = document.activeElement
    return el?.getAttribute("aria-label")
  })
  // Cmd+F should focus a filter control for the selected column. The
  // aria-label varies by column type:
  //   text/url/email/phone  → "Filter <name>"
  //   number               → "<name> min"
  //   date                 → "<name> from"
  const isFilterInput =
    focused?.startsWith("Filter ") ||
    focused?.match(/(min|max|from|to)$/) !== null
  if (isFilterInput) pass(`Cmd+F focused: ${focused}`)
  else fail(`Cmd+F did not focus a filter input (got: ${focused})`)

  // 8. Pagination
  await page.evaluate(() => {
    const input = document.activeElement
    if (input) input.blur()
  })
  await page.keyboard.press("Escape")
  await new Promise((r) => setTimeout(r, 200))
  await page.evaluate(() => {
    document.querySelector("button[aria-label='Last page']")?.click()
  })
  await new Promise((r) => setTimeout(r, 500))
  const lastPg = await page.evaluate(() => {
    // Match "Page N of M" where N === M (i.e. on the last page)
    const m = document.body.innerText.match(/Page\s+(\d+)\s+of\s+(\d+)/)
    return m ? Number(m[1]) === Number(m[2]) : false
  })
  if (lastPg) pass("Jump to last page works")
  else fail("Jump to last page failed")
  await page.screenshot({ path: `${SHOTS}/04-lastpage.png` })

  // 9. No console errors
  if (errors.length === 0) pass("No console errors during full flow")
  else {
    fail(`Got ${errors.length} console error(s):`)
    for (const e of errors) console.error("  " + e)
  }
} finally {
  await browser.close()
}

process.exit(exitCode)
