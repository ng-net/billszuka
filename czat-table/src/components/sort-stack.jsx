import * as React from "react"
import { ArrowUp, ArrowDown, X, ListOrdered } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

/**
 * Sort stack indicator: shows each active sort level with its direction and
 * ordinal. Click X to remove that level. Clicking the level itself toggles
 * asc/desc.
 */
export function SortStack({ sort, columnsById, onChange, onClear }) {
  if (!sort || sort.length === 0) return null
  return (
    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
      <ListOrdered className="size-3.5" />
      <span>Sort:</span>
      <div className="flex flex-wrap items-center gap-1">
        {sort.map((s, i) => {
          const col = columnsById.get(s.colId)
          return (
            <button
              key={`${s.colId}-${i}`}
              type="button"
              onClick={() => {
                const next = sort.map((x, idx) =>
                  idx === i ? { ...x, dir: x.dir === "asc" ? "desc" : "asc" } : x,
                )
                onChange(next)
              }}
              className={cn(
                "group inline-flex items-center gap-1 rounded-md border bg-background px-1.5 py-0.5 font-medium text-foreground shadow-sm transition-colors hover:bg-muted/60",
                "border-border",
              )}
              title={`Toggle direction`}
            >
              <span className="grid size-4 place-items-center rounded bg-muted text-[10px] text-muted-foreground">
                {i + 1}
              </span>
              {col?.name ?? s.colId}
              {s.dir === "asc" ? <ArrowUp className="size-3" /> : <ArrowDown className="size-3" />}
              <span
                role="button"
                aria-label="Remove from sort"
                onClick={(e) => {
                  e.stopPropagation()
                  onChange(sort.filter((_, idx) => idx !== i))
                }}
                className="-mr-1 grid size-4 place-items-center rounded text-muted-foreground/60 hover:bg-muted hover:text-foreground"
              >
                <X className="size-3" />
              </span>
            </button>
          )
        })}
      </div>
      <Button type="button" variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={onClear}>
        Clear
      </Button>
    </div>
  )
}
