import * as React from "react"
import { GripVertical, ArrowUp, ArrowDown, RotateCcw } from "lucide-react"
import { Table, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { TypeFilter } from "@/components/type-filter"
import { cn } from "@/lib/utils"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"

const MIN_COL_WIDTH = 80

/**
 * Sticky table header row. Each <th> holds:
 *  - a click target for sort (whole button)
 *  - a left grip span for column reorder (visual only — drag is wired in the parent)
 *  - a right-edge resize handle
 *  - a per-column type-aware filter input
 *  - a hover-revealed "reset to default width" button (only when width != default)
 *
 * The parent owns sort, filter, and resize state via callbacks.
 */
export function TableHeaderRow({
  visibleColumns,
  pinnedCols,
  sort,
  filters,
  defaultColWidth = 180,
  onHeaderClick,
  onHeaderContextMenu,
  onHeaderPointerDown,
  onHeaderPointerUp,
  onHeaderPointerLeave,
  onResizeStart,
  onResetWidth,
  onFilterChange,
}) {
  return (
    <div className="relative overflow-hidden border-b">
      <div
        data-scroll-parent="1"
        className="relative max-h-full overflow-auto"
        style={{ touchAction: "pan-x pan-y" }}
      >
        <Table style={{ width: "max-content", minWidth: "100%" }}>
          <TableHeader>
            <TableRow>
              {visibleColumns.map((col, idx) => {
                const sortIdx = sort.findIndex((s) => s.colId === col.id)
                const sortDir = sortIdx >= 0 ? sort[sortIdx].dir : null
                const pinnedIdx = col.pinned ? pinnedCols.findIndex((p) => p.id === col.id) : -1
                const pinnedLeftStyle = pinnedIdx >= 0
                  ? { left: `var(--pinned-w-${pinnedIdx + 1})` }
                  : undefined
                return (
                  <TableHead
                    key={col.id}
                    data-col={col.id}
                    style={{ width: col.width, minWidth: col.width, maxWidth: 480, ...pinnedLeftStyle }}
                    aria-sort={sortDir === "asc" ? "ascending" : sortDir === "desc" ? "descending" : "none"}
                    className={cn(
                      "group/th relative select-none border-r bg-background p-0",
                      "sticky top-0 z-20",
                      col.pinned && "z-30",
                      pinnedIdx === pinnedCols.length - 1 && "after:absolute after:right-0 after:top-0 after:z-10 after:h-full after:w-px after:bg-border after:shadow-[2px_0_4px_-2px_rgba(0,0,0,0.15)]",
                    )}
                  >
                    <div
                      className={cn(
                        "flex h-full min-h-[40px] items-center gap-1 px-3",
                        sortDir && "bg-accent/30",
                      )}
                    >
                      <button
                        type="button"
                        onPointerDown={(e) => onHeaderPointerDown(col, e)}
                        onPointerUp={onHeaderPointerUp}
                        onPointerLeave={onHeaderPointerLeave}
                        onClick={(e) => onHeaderClick(col, e)}
                        onContextMenu={(e) => onHeaderContextMenu(col, e)}
                        className={cn(
                          "flex min-w-0 flex-1 items-center gap-1 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground transition-colors hover:text-foreground",
                          sortDir && "text-foreground",
                        )}
                      >
                        <span className="grid size-3.5 shrink-0 cursor-grab place-items-center text-muted-foreground/30 opacity-0 transition-opacity group-hover/th:opacity-100">
                          <GripVertical className="size-3" />
                        </span>
                        <span className="truncate" title={col.name}>
                          {col.name}
                        </span>
                        <span className="ml-auto inline-flex items-center gap-0.5">
                          {sortIdx >= 0 && sort.length > 1 && (
                            <span className="grid size-3.5 place-items-center rounded bg-primary/15 text-[9px] font-bold text-primary">
                              {sortIdx + 1}
                            </span>
                          )}
                          {sortDir === "asc" && <ArrowUp className="size-3.5 text-primary" />}
                          {sortDir === "desc" && <ArrowDown className="size-3.5 text-primary" />}
                        </span>
                      </button>
                      <span
                        role="separator"
                        onMouseDown={(e) => onResizeStart(col, e)}
                        className="absolute right-0 top-0 z-10 h-full w-1.5 cursor-col-resize bg-transparent transition-colors hover:bg-primary/40"
                        aria-label={`Resize ${col.name}`}
                      />
                      {col.width !== defaultColWidth && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              onClick={() => onResetWidth?.(col.id)}
                              className="absolute right-2 top-1/2 z-10 -translate-y-1/2 grid size-5 place-items-center rounded text-muted-foreground/60 opacity-0 transition-opacity hover:bg-muted hover:text-foreground group-hover/th:opacity-100"
                              aria-label={`Reset ${col.name} width to default`}
                            >
                              <RotateCcw className="size-3" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="top">
                            Reset width ({col.width}px → {defaultColWidth}px)
                          </TooltipContent>
                        </Tooltip>
                      )}
                    </div>
                    <div className="border-t bg-background px-2 pb-2 pt-1.5">
                      <TypeFilter
                        column={col}
                        value={filters[col.id]}
                        onChange={(v) => onFilterChange(col.id, v)}
                      />
                    </div>
                  </TableHead>
                )
              })}
            </TableRow>
          </TableHeader>
        </Table>
      </div>
    </div>
  )
}
