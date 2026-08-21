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
                <a
                  href="https://github.com/marlink/BILLSzuka"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                  aria-label="GitHub: marlink/BILLSzuka"
                  title="GitHub: marlink/BILLSzuka"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56v-2c-3.2.69-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.18-3.1-.12-.29-.51-1.46.11-3.04 0 0 .96-.31 3.15 1.18.92-.26 1.9-.39 2.88-.39s1.96.13 2.88.39c2.19-1.49 3.15-1.18 3.15-1.18.62 1.58.23 2.75.11 3.04.74.81 1.18 1.84 1.18 3.1 0 4.42-2.7 5.39-5.27 5.68.41.35.78 1.04.78 2.1v3.11c0 .31.21.68.8.56C20.21 21.39 23.5 17.08 23.5 12 23.5 5.65 18.35.5 12 .5z" />
                  </svg>
                </a>
              </TooltipTrigger>
              <TooltipContent>GitHub: marlink/BILLSzuka</TooltipContent>
            </Tooltip>
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
