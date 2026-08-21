import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Upload, FileSpreadsheet, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

/**
 * The full empty state. The whole panel is a drop target.
 * Click anywhere or drop a CSV to load it. "Try sample" previews bundled data.
 *
 * Props:
 *  - onFile(file): receive a File from picker or drop
 *  - onTrySample(): receive a request to load the bundled sample
 *  - progress: 0..1 (or null) — shows an animated progress bar
 *  - error: string | null — shows an error message
 */
export function Dropzone({ onFile, onTrySample, progress, error, busy }) {
  const inputRef = React.useRef(null)
  const [isDragging, setIsDragging] = React.useState(false)
  const dragCounter = React.useRef(0)

  function onDragEnter(e) {
    e.preventDefault()
    dragCounter.current += 1
    if (e.dataTransfer?.types?.includes("Files")) setIsDragging(true)
  }
  function onDragLeave(e) {
    e.preventDefault()
    dragCounter.current -= 1
    if (dragCounter.current <= 0) {
      dragCounter.current = 0
      setIsDragging(false)
    }
  }
  function onDragOver(e) {
    e.preventDefault()
  }
  function onDrop(e) {
    e.preventDefault()
    dragCounter.current = 0
    setIsDragging(false)
    const f = e.dataTransfer?.files?.[0]
    if (f) onFile?.(f)
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => !busy && inputRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === "Enter" || e.key === " ") && !busy) {
          e.preventDefault()
          inputRef.current?.click()
        }
      }}
      onDragEnter={onDragEnter}
      onDragLeave={onDragLeave}
      onDragOver={onDragOver}
      onDrop={onDrop}
      className={cn(
        "group relative flex h-full w-full cursor-pointer flex-col items-center justify-center gap-6 px-6 outline-none",
        "rounded-xl border-2 border-dashed transition-colors",
        isDragging
          ? "border-primary bg-accent/40"
          : "border-border bg-background hover:border-muted-foreground/40 hover:bg-muted/30",
        busy && "pointer-events-none",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) onFile?.(f)
          e.target.value = ""
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="flex flex-col items-center gap-3"
      >
        <div
          className={cn(
            "grid size-16 place-items-center rounded-2xl border bg-background shadow-sm transition-colors",
            isDragging ? "border-primary text-primary" : "text-muted-foreground",
          )}
        >
          <Upload className="size-7" />
        </div>
        <div className="text-center">
          <h2 className="text-lg font-medium tracking-tight text-foreground">
            {isDragging ? "Release to load" : "Drop a CSV here"}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            or <span className="font-medium text-foreground underline-offset-4 group-hover:underline">click to browse</span> · up to 50 MB
          </p>
        </div>
      </motion.div>

      <div className="flex items-center gap-3" onClick={(e) => e.stopPropagation()}>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="gap-2 text-muted-foreground hover:text-foreground"
          onClick={() => inputRef.current?.click()}
          disabled={busy}
        >
          <FileSpreadsheet className="size-4" />
          Choose file
        </Button>
        <span className="text-xs text-muted-foreground/60">or</span>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="gap-2 text-primary hover:text-primary"
          onClick={() => onTrySample?.()}
          disabled={busy}
        >
          <Sparkles className="size-4" />
          Try sample
        </Button>
      </div>

      {/* Progress bar */}
      <AnimatePresence>
        {progress != null && (
          <motion.div
            key="progress"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="w-80 max-w-full"
          >
            <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
              <motion.div
                className="h-full bg-primary"
                initial={{ width: 0 }}
                animate={{ width: `${Math.round(progress * 100)}%` }}
                transition={{ duration: 0.22, ease: "easeOut" }}
              />
              {/* tiny shine sweep so the motion reads as "alive" not "tween" */}
              <motion.div
                aria-hidden
                className="pointer-events-none absolute inset-y-0 -left-1/2 w-1/2 bg-gradient-to-r from-transparent via-white/15 to-transparent"
                animate={{ x: ["0%", "500%"] }}
                transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
              />
            </div>
            <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
              <span>{progress < 1 ? "Parsing CSV…" : "Ready"}</span>
              <span className="font-medium tabular-nums text-foreground">
                {Math.round((progress || 0) * 100)}%
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="max-w-md rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-sm text-destructive"
            onClick={(e) => e.stopPropagation()}
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
