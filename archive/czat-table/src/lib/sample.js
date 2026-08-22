// Bundles the BILLSzuka master.csv as the "Try sample" payload.
// Vite's `?raw` inlines the file as a string at build time — fully client-side.
import sampleCsv from "../../../data/master.csv?raw"
import { parseCsvString } from "./csv"

export const SAMPLE_NAME = "data/master.csv"
export const SAMPLE_SIZE = new Blob([sampleCsv]).size

// Same checkpoint ramp + min duration as parseCsvFile, so the bar looks
// identical whether the user uploads or hits Try sample.
const CHECKPOINTS = [
  { p: 0.08, t:  60 },
  { p: 0.22, t: 160 },
  { p: 0.42, t: 320 },
  { p: 0.62, t: 500 },
  { p: 0.80, t: 700 },
  { p: 0.93, t: 880 },
]
const MIN_DURATION_MS = 900

/** Parse the bundled sample into { columns, rows, parseMs } like a real upload. */
export async function loadSample({ onProgress } = {}) {
  const timers = CHECKPOINTS.map(({ p, t }) =>
    setTimeout(() => onProgress?.(p), t),
  )
  try {
    if (onProgress) onProgress(0)
    const t0 = performance.now()
    // Defer one frame so React paints the bar at 0% before the parse fills it.
    await new Promise((r) => requestAnimationFrame(r))
    const out = parseCsvString(sampleCsv)
    out.parseMs = performance.now() - t0
    // Hold for the full bar animation even though parse is sub-100ms.
    await new Promise((r) => setTimeout(r, MIN_DURATION_MS))
    for (const t of timers) clearTimeout(t)
    if (onProgress) onProgress(1)
    return out
  } catch (e) {
    for (const t of timers) clearTimeout(t)
    throw e
  }
}
