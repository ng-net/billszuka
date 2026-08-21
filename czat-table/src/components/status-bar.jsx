import * as React from "react"
import { motion, useSpring, useMotionValue } from "framer-motion"
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn, prefersReducedMotion } from "@/lib/utils"

const PER_PAGE_OPTIONS = [25, 50, 100, 250, 500]

/**
 * Bottom status bar. Shows row range + page X of Y, parse time, column count,
 * density toggle, and per-page picker.
 */
export function StatusBar({
  parseMs,
  columnCount,
  density,
  onToggleDensity,
  pagination,
  onChangePage,
  onChangePerPage,
}) {
  const { page = 1, perPage = 100, totalPages = 1, totalRows = 0, pageStart = 0, pageEnd = 0 } = pagination || {}
  // Animate the "total" number for a soft wow on filter changes — unless the user prefers reduced motion.
  const reduceMotion = prefersReducedMotion()
  const mv = useMotionValue(totalRows)
  const spring = useSpring(mv, { stiffness: 140, damping: 22, mass: 0.4 })
  const [display, setDisplay] = React.useState(totalRows)

  React.useEffect(() => {
    if (reduceMotion) {
      // Skip the spring: jump straight to the new value.
      setDisplay(totalRows)
      return
    }
    mv.set(totalRows)
  }, [totalRows, mv, reduceMotion])

  React.useEffect(() => {
    if (reduceMotion) return
    return spring.on("change", (v) => setDisplay(Math.round(v)))
  }, [spring, reduceMotion])

  const rangeStart = totalRows === 0 ? 0 : pageStart + 1
  const rangeEnd = pageEnd

  return (
    <div className="flex h-8 items-center justify-between border-t bg-background/80 px-2 text-xs text-muted-foreground backdrop-blur">
      <div className="flex items-center gap-1.5">
        {/* Pagination controls */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-6"
          onClick={() => onChangePage(1)}
          disabled={page <= 1}
          aria-label="First page"
          title="First page"
        >
          <ChevronsLeft className="size-3.5" />
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-6"
          onClick={() => onChangePage(page - 1)}
          disabled={page <= 1}
          aria-label="Previous page"
          title="Previous page"
        >
          <ChevronLeft className="size-3.5" />
        </Button>

        <span className="tabular-nums">
          Page <span className="font-medium text-foreground">{page}</span> of{" "}
          <span className="font-medium text-foreground">{totalPages}</span>
        </span>

        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-6"
          onClick={() => onChangePage(page + 1)}
          disabled={page >= totalPages}
          aria-label="Next page"
          title="Next page"
        >
          <ChevronRight className="size-3.5" />
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-6"
          onClick={() => onChangePage(totalPages)}
          disabled={page >= totalPages}
          aria-label="Last page"
          title="Last page"
        >
          <ChevronsRight className="size-3.5" />
        </Button>

        <span className="mx-1 text-muted-foreground/40">·</span>
        <span>
          Showing{" "}
          <span className="font-medium text-foreground tabular-nums">
            {totalRows === 0 ? "0" : `${rangeStart}–${rangeEnd}`}
          </span>{" "}
          of{" "}
          <span className="font-medium text-foreground tabular-nums">{formatNumber(display)}</span>{" "}
          rows
        </span>
      </div>

      <div className="flex items-center gap-1.5">
        {parseMs > 0 && (
          <>
            <span>Parsed in {(parseMs / 1000).toFixed(2)} s</span>
            <span className="text-muted-foreground/40">·</span>
          </>
        )}
        <span>{columnCount} columns</span>
        <span className="text-muted-foreground/40">·</span>
        <PerPagePicker perPage={perPage} onChange={onChangePerPage} />
        <button
          type="button"
          onClick={onToggleDensity}
          className="rounded px-2 py-0.5 hover:bg-muted hover:text-foreground"
          title={`Switch to ${density === "compact" ? "comfortable" : "compact"} density`}
        >
          {density === "compact" ? "Compact" : "Comfortable"}
        </button>
      </div>
    </div>
  )
}

function PerPagePicker({ perPage, onChange }) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="inline-flex items-center gap-1 rounded px-2 py-0.5 hover:bg-muted hover:text-foreground"
          title="Rows per page"
        >
          <span className="tabular-nums">{perPage}/page</span>
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-40 p-1">
        {PER_PAGE_OPTIONS.map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onChange(n)}
            className={cn(
              "flex w-full items-center justify-between rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground",
              perPage === n && "bg-accent text-accent-foreground",
            )}
          >
            <span className="tabular-nums">{n}</span>
            {perPage === n && <Check className="size-4" />}
          </button>
        ))}
      </PopoverContent>
    </Popover>
  )
}

function formatNumber(n) {
  return new Intl.NumberFormat().format(n)
}
