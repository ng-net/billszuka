/** Tiny typed wrapper around localStorage with safe JSON handling. */
export const storage = {
  get(key) {
    if (typeof window === "undefined") return null
    try {
      return window.localStorage.getItem(key)
    } catch {
      return null
    }
  },
  set(key, value) {
    if (typeof window === "undefined") return
    try {
      window.localStorage.setItem(key, value)
    } catch {
      /* quota or private mode — silently drop */
    }
  },
  del(key) {
    if (typeof window === "undefined") return
    try {
      window.localStorage.removeItem(key)
    } catch {
      /* ignore */
    }
  },
}
