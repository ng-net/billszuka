import * as React from "react"
import { motion } from "framer-motion"
import { HelpCircle, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { UploadButton } from "@/components/upload-button"
import { QuickFilters } from "@/components/quick-filters"
import { SortStack } from "@/components/sort-stack"
import { FilterChips } from "@/components/filter-chips"
import { ThemeToggle } from "@/components/theme-toggle"
import { cn } from "@/lib/utils"

export function Toolbar({
  data,
  prefs,
  onFile,
  onPrefsChange,
  onShowShortcuts,
  onShowSampleInfo,
}) {
  // Auto-hide-on-scroll was removed when we switched to paginated rows:
  // the body now scrolls within a fixed-height page, so the toolbar
  // vanishing mid-page was worse than useless. The toolbar is always visible.

  const setFilters = (next) => {
    // next is { [colId]: value } or already-shaped { [colId]: value } from quick-filters
    const merged = { ...(prefs.filters || {}) }
    for (const [k, v] of Object.entries(next)) {
      const isEmpty =
        v == null ||
        v === "" ||
        (Array.isArray(v) && v.length === 0) ||
        (typeof v === "object" && !Array.isArray(v) && !v.min && !v.max && !v.from && !v.to)
      if (isEmpty) delete merged[k]
      else merged[k] = v
    }
    onPrefsChange({ ...prefs, filters: merged })
  }

  const quickFiltersOnChange = (colId, value) => {
    setFilters({ [colId]: value })
  }

  return (
    <TooltipProvider delayDuration={300}>
      <motion.div
        key="toolbar"
        initial={{ y: -8, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.18, ease: "easeOut" }}
        className="relative z-30 border-b bg-background/80 backdrop-blur"
      >
        <div className="flex flex-wrap items-center gap-2 px-3 py-2">
          <UploadButton onFile={onFile} />
          <div className="mx-1 h-5 w-px bg-border" />
          <QuickFilters
            columns={data.columns}
            filters={prefs.filters || {}}
            onChange={quickFiltersOnChange}
          />
          <div className="ml-auto flex items-center gap-1">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="hidden gap-1.5 text-xs text-muted-foreground hover:text-foreground sm:inline-flex"
              onClick={onShowSampleInfo}
            >
              <Sparkles className="size-3.5" />
              {data.rows.length} rows
            </Button>
            <ThemeToggle
              theme={prefs.theme}
              onChange={(t) => onPrefsChange({ ...prefs, theme: t })}
            />
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  onClick={onShowShortcuts}
                  aria-label="Shortcuts"
                >
                  <HelpCircle className="size-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Shortcuts (?)</TooltipContent>
            </Tooltip>
          </div>
        </div>
        {(prefs.sort?.length > 0 || Object.keys(prefs.filters || {}).length > 0) && (
          <div className="flex flex-wrap items-center gap-3 border-t bg-muted/20 px-3 py-1.5">
            {prefs.sort?.length > 0 && (
              <SortStack
                sort={prefs.sort}
                columnsById={new Map(data.columns.map((c) => [c.id, c]))}
                onChange={(next) => onPrefsChange({ ...prefs, sort: next })}
                onClear={() => onPrefsChange({ ...prefs, sort: [] })}
              />
            )}
            <FilterChips
              filters={Object.entries(prefs.filters || {}).map(([colId, value]) => ({ colId, value }))}
              columnsById={new Map(data.columns.map((c) => [c.id, c]))}
              onChange={(next) => onPrefsChange({ ...prefs, filters: Object.fromEntries(next.map((f) => [f.colId, f.value])) })}
              onClear={() => onPrefsChange({ ...prefs, filters: {} })}
            />
          </div>
        )}
      </motion.div>
    </TooltipProvider>
  )
}
