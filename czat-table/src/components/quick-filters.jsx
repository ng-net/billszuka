import * as React from "react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { ChevronDown, Sliders } from "lucide-react"
import { cn } from "@/lib/utils"

const MAX_ENUM_VALUES = 6 // only auto-derive quick filters for enums with ≤ this many values
const MAX_QUICK_FILTERS = 5 // cap the number of quick filters shown

/**
 * Quick filter bar: small chips derived from enum/boolean columns.
 *
 * Props:
 *  - columns: the parsed schema
 *  - filters: the current filters object { [colId]: value }
 *  - onChange: (colId, nextValue | null) => void
 *    nextValue of `null` removes the filter on that column.
 */
export function QuickFilters({ columns, filters, onChange }) {
  const candidates = React.useMemo(
    () =>
      columns.filter((c) => {
        if (c.type === "enum" && c.enumValues && c.enumValues.length > 0 && c.enumValues.length <= MAX_ENUM_VALUES) {
          return true
        }
        if (
          c.type === "text" &&
          c.enumValues &&
          c.enumValues.length === 2 &&
          c.enumValues.includes("true") &&
          c.enumValues.includes("false")
        ) {
          return true
        }
        return false
      }),
    [columns],
  )
  if (candidates.length === 0) return null

  const shown = candidates.slice(0, MAX_QUICK_FILTERS)
  const overflow = candidates.length - shown.length

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <Sliders className="size-3.5 text-muted-foreground" />
      {shown.map((col) => (
        <QuickFilterChip
          key={col.id}
          column={col}
          value={filters[col.id]}
          onChange={(v) => onChange(col.id, v)}
        />
      ))}
      {overflow > 0 && (
        <span className="text-xs text-muted-foreground">+ {overflow} more</span>
      )}
    </div>
  )
}

function QuickFilterChip({ column, value, onChange }) {
  const isBool =
    column.enumValues &&
    column.enumValues.length === 2 &&
    column.enumValues.includes("true") &&
    column.enumValues.includes("false")
  const [open, setOpen] = React.useState(false)

  if (isBool) {
    const arr = Array.isArray(value) ? value : value ? [String(value)] : []
    const v = arr.includes("true") ? "true" : arr.includes("false") ? "false" : null
    return (
      <Button
        type="button"
        variant="outline"
        size="sm"
        className={cn("h-7 gap-1 px-2 text-xs", v && "border-primary/50 text-primary")}
        onClick={() => onChange(v === "true" ? null : v === "false" ? ["true"] : ["false"])}
        title={`Toggle ${column.name}`}
      >
        {column.name}
        {v && <span className="text-muted-foreground">: {v}</span>}
      </Button>
    )
  }

  const arr = Array.isArray(value) ? value : []
  const active = arr.length > 0

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className={cn("h-7 gap-1 px-2 text-xs", active && "border-primary/50 text-primary")}
        >
          {column.name}
          {active && <span className="text-muted-foreground">: {arr.length}</span>}
          <ChevronDown className="size-3 opacity-60" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-56 p-2">
        <div className="mb-1 px-1 text-xs font-medium text-muted-foreground">
          {column.name}
        </div>
        <div className="flex max-h-56 flex-col gap-1 overflow-y-auto">
          {column.enumValues.map((opt) => {
            const checked = arr.includes(opt)
            return (
              <label
                key={opt}
                className="flex cursor-pointer items-center gap-2 rounded px-1.5 py-1 text-sm hover:bg-muted/60"
              >
                <Checkbox
                  checked={checked}
                  onCheckedChange={() => {
                    const next = checked ? arr.filter((x) => x !== opt) : [...arr, opt]
                    onChange(next.length === 0 ? null : next)
                  }}
                />
                <span className="truncate" title={opt}>
                  {opt}
                </span>
              </label>
            )
          })}
        </div>
        {active && (
          <button
            type="button"
            onClick={() => {
              onChange(null)
              setOpen(false)
            }}
            className="mt-2 w-full rounded px-2 py-1 text-left text-xs text-muted-foreground hover:bg-muted"
          >
            Clear
          </button>
        )}
      </PopoverContent>
    </Popover>
  )
}
