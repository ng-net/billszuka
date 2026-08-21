import * as React from "react"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { cn } from "@/lib/utils"

/**
 * Per-column filter input. Renders the right control for the column's
 * detected type: text, number range, date range, or enum multi-select.
 */
export function TypeFilter({ column, value, onChange }) {
  const t = column.type
  const v = value ?? (t === "text" ? "" : t === "number" ? { min: "", max: "" } : t === "date" ? { from: "", to: "" } : t === "enum" ? [] : "")

  if (t === "text" || t === "url" || t === "email" || t === "phone") {
    return (
      <Input
        type="text"
        value={v}
        onChange={(e) => onChange(e.target.value)}
        placeholder="contains…"
        className="h-7 w-full px-2 text-xs"
        aria-label={`Filter ${column.name}`}
      />
    )
  }

  if (t === "number") {
    return (
      <div className="flex items-center gap-1">
        <Input
          type="number"
          value={v.min}
          onChange={(e) => onChange({ ...v, min: e.target.value })}
          placeholder="min"
          className="h-7 w-full px-2 text-xs"
          aria-label={`${column.name} min`}
        />
        <span className="text-muted-foreground/50 text-xs">–</span>
        <Input
          type="number"
          value={v.max}
          onChange={(e) => onChange({ ...v, max: e.target.value })}
          placeholder="max"
          className="h-7 w-full px-2 text-xs"
          aria-label={`${column.name} max`}
        />
      </div>
    )
  }

  if (t === "date") {
    return (
      <div className="flex items-center gap-1">
        <Input
          type="date"
          value={v.from}
          onChange={(e) => onChange({ ...v, from: e.target.value })}
          className="h-7 w-full px-2 text-xs"
          aria-label={`${column.name} from`}
        />
        <span className="text-muted-foreground/50 text-xs">–</span>
        <Input
          type="date"
          value={v.to}
          onChange={(e) => onChange({ ...v, to: e.target.value })}
          className="h-7 w-full px-2 text-xs"
          aria-label={`${column.name} to`}
        />
      </div>
    )
  }

  if (t === "enum" && column.enumValues) {
    return (
      <div className="flex max-h-24 flex-col gap-1 overflow-y-auto rounded border bg-background p-1.5">
        {column.enumValues.map((opt) => {
          const checked = v.includes(opt)
          return (
            <label
              key={opt}
              className={cn(
                "flex cursor-pointer items-center gap-2 rounded px-1 py-0.5 text-xs hover:bg-muted/60",
                checked && "text-foreground",
              )}
            >
              <Checkbox
                checked={checked}
                onCheckedChange={() => {
                  const next = checked ? v.filter((x) => x !== opt) : [...v, opt]
                  onChange(next)
                }}
              />
              <span className="truncate" title={opt}>
                {opt}
              </span>
            </label>
          )
        })}
      </div>
    )
  }

  return null
}

/** Predicate that decides if a row passes a single column's filter. */
export function matchFilter(rowValue, filterValue, type) {
  if (filterValue == null) return true
  const v = rowValue == null ? "" : String(rowValue)
  if (type === "text" || type === "url" || type === "email" || type === "phone") {
    if (filterValue === "") return true
    return v.toLowerCase().includes(String(filterValue).toLowerCase())
  }
  if (type === "number") {
    if (!filterValue.min && !filterValue.max) return true
    const n = Number(v.replace(/\s/g, "").replace(/,/g, "."))
    if (Number.isNaN(n)) return false
    if (filterValue.min !== "" && n < Number(filterValue.min)) return false
    if (filterValue.max !== "" && n > Number(filterValue.max)) return false
    return true
  }
  if (type === "date") {
    if (!filterValue.from && !filterValue.to) return true
    const t = Date.parse(v)
    if (Number.isNaN(t)) return false
    if (filterValue.from && t < Date.parse(filterValue.from)) return false
    if (filterValue.to && t > Date.parse(filterValue.to) + 86_400_000) return false
    return true
  }
  if (type === "enum") {
    if (!filterValue || filterValue.length === 0) return true
    return filterValue.includes(v)
  }
  return true
}
