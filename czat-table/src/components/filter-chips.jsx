import * as React from "react"
import { X, Filter } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

function describe(filter, column) {
  if (!column) return filter.colId
  const t = column.type
  if (t === "text" || t === "url" || t === "email" || t === "phone") {
    return filter.value ? `“${filter.value}”` : ""
  }
  if (t === "number") {
    const { min, max } = filter.value ?? {}
    if (!min && !max) return ""
    if (min && max) return `${min}–${max}`
    if (min) return `≥ ${min}`
    return `≤ ${max}`
  }
  if (t === "date") {
    const { from, to } = filter.value ?? {}
    if (!from && !to) return ""
    if (from && to) return `${from} → ${to}`
    if (from) return `from ${from}`
    return `to ${to}`
  }
  if (t === "enum") {
    const arr = filter.value ?? []
    if (arr.length === 0) return ""
    if (arr.length <= 2) return arr.join(", ")
    return `${arr.length} selected`
  }
  return ""
}

/** Horizontal chip strip showing the currently active filters. */
export function FilterChips({ filters, columnsById, onChange, onClear }) {
  const entries = React.useMemo(
    () =>
      filters
        .map((f) => ({ ...f, col: columnsById.get(f.colId) }))
        .filter((f) => describe(f, f.col) !== ""),
    [filters, columnsById],
  )

  if (entries.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
      <Filter className="size-3.5" />
      <span>Filters:</span>
      {entries.map((f) => {
        const label = describe(f, f.col)
        return (
          <span
            key={f.colId}
            className={cn(
              "inline-flex items-center gap-1 rounded-md border bg-accent/40 px-1.5 py-0.5 font-medium text-foreground",
              "border-accent",
            )}
          >
            <span className="text-muted-foreground">{f.col?.name}:</span>
            <span className="max-w-[160px] truncate" title={label}>
              {label}
            </span>
            <button
              type="button"
              aria-label={`Remove filter ${f.col?.name}`}
              onClick={() => onChange(filters.filter((x) => x.colId !== f.colId))}
              className="-mr-1 grid size-4 place-items-center rounded text-muted-foreground/70 hover:bg-background hover:text-foreground"
            >
              <X className="size-3" />
            </button>
          </span>
        )
      })}
      {entries.length > 1 && (
        <Button type="button" variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={onClear}>
          Clear all
        </Button>
      )}
    </div>
  )
}
