import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

/** Debounce a value: returns the latest value only after `ms` of inactivity. */
export function debounce(fn, ms) {
  let t
  return (...args) => {
    clearTimeout(t)
    t = setTimeout(() => fn(...args), ms)
  }
}

/** Classify reduced motion preference once, reactively. */
export function prefersReducedMotion() {
  if (typeof window === "undefined") return false
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

/** Format a number with locale grouping, e.g. 1,234 / 12.5K / 3.4M. */
export function formatCompact(n, locale = "en-US") {
  if (n == null || Number.isNaN(n)) return ""
  return new Intl.NumberFormat(locale, { notation: "compact", maximumFractionDigits: 1 }).format(n)
}
