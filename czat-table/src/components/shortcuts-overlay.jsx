import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"

const SHORTCUTS = [
  { keys: ["Click"], label: "Copy cell value" },
  { keys: ["⌘", "Click"], label: "Open link (email, url, phone)" },
  { keys: ["Click", "header"], label: "Sort ascending → descending → none" },
  { keys: ["Shift", "Click header"], label: "Add to multi-column sort" },
  { keys: ["Right-click", "header"], label: "Open column menu" },
  { keys: ["Long-press", "header"], label: "Open column menu (mobile)" },
  { keys: ["Drag", "edge"], label: "Resize column" },
  { keys: ["⌘", "K"], label: "Open command palette" },
  { keys: ["⌘", "F"], label: "Focus filter of selected column" },
  { keys: ["Esc"], label: "Clear filter or close dialog" },
  { keys: ["↑", "↓", "←", "→"], label: "Move row highlight" },
  { keys: ["Enter"], label: "Copy focused cell" },
  { keys: ["?"], label: "Show this overlay" },
]

export function ShortcutsOverlay({ open, onClose }) {
  React.useEffect(() => {
    if (!open) return
    function onKey(e) {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, onClose])

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            className="w-full max-w-md rounded-lg border bg-popover p-5 text-popover-foreground shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Keyboard shortcuts</h2>
              <Button type="button" variant="ghost" size="icon" className="size-7" onClick={onClose} aria-label="Close">
                <X className="size-4" />
              </Button>
            </div>
            <ul className="space-y-1.5">
              {SHORTCUTS.map((s, i) => (
                <li key={i} className="flex items-center justify-between gap-4 text-sm">
                  <div className="flex shrink-0 items-center gap-1">
                    {s.keys.map((k, j) => (
                      <kbd
                        key={j}
                        className="inline-flex h-5 min-w-5 items-center justify-center rounded border bg-muted px-1.5 font-mono text-[10px] text-muted-foreground"
                      >
                        {k}
                      </kbd>
                    ))}
                  </div>
                  <span className="flex-1 truncate text-right text-muted-foreground">{s.label}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
