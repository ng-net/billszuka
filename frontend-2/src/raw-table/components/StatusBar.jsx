import { Undo2, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";
import { formatNumber } from "@/lib/utils";
import { getColumnLabel } from "@/lib/schema";

export function StatusBar({
  totalRows,
  filteredRows,
  visibleColumns,
  totalColumns,
  activeFilters,
  sortStack,
  parseTimeMs: _parseTimeMs,
  density,
  fileMeta,
  filtersHistory = [],
  onRestoreFilters,
  pagination,
  onPageChange,
  onPageSizeChange,
}) {
  const pageIndex = pagination?.pageIndex ?? 0;
  const pageSize = pagination?.pageSize ?? 100;
  const isAll = pageSize === 0;

  const pageCount = isAll || filteredRows === 0 ? 1 : Math.ceil(filteredRows / pageSize);
  const startRow = filteredRows === 0 ? 0 : pageIndex * pageSize + 1;
  const endRow = isAll ? filteredRows : Math.min((pageIndex + 1) * pageSize, filteredRows);

  const canPrev = pageIndex > 0;
  const canNext = pageIndex < pageCount - 1;

  // Show "↩ Przywróć" only when filters are currently empty AND we have
  // something in history. Otherwise the button would be noise.
  const canRestore = activeFilters === 0 && filtersHistory.length > 0;

  return (
    <div className="border-t bg-card/60 backdrop-blur-sm">
      <div className="px-3 sm:px-4 h-9 flex items-center justify-between text-xs text-muted-foreground gap-4 overflow-x-auto">
        {/* Left: Result & Filter stats */}
        <div className="flex items-center gap-3 shrink-0">
          <span className="tabular-nums font-medium text-foreground">
            <span>
              Wyniki: <strong className="text-primary font-semibold">{formatNumber(filteredRows)}</strong> / {formatNumber(totalRows)}
            </span>
            {!isAll && filteredRows > pageSize && (
              <span className="text-muted-foreground font-normal ml-1.5 hidden sm:inline">
                ({startRow}–{endRow})
              </span>
            )}
          </span>

          <span className="text-muted-foreground/40">·</span>
          <span className="tabular-nums">
            <span className="text-foreground">{visibleColumns}</span>/{totalColumns} kolumn
          </span>

          {activeFilters > 0 && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <span className="tabular-nums">
                <span className="text-foreground">{activeFilters}</span>{" "}
                {activeFilters === 1 ? "filtr" : "filtrów"}
              </span>
            </>
          )}

          {sortStack.length > 0 && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <span className="hidden sm:inline">
                Sortowanie: {sortStack.map((s) => `${getColumnLabel(s.id)} ${s.desc ? "↓" : "↑"}`).join(" · ")}
              </span>
            </>
          )}

          {canRestore && onRestoreFilters && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <button
                onClick={() => onRestoreFilters(filtersHistory[0])}
                className="inline-flex items-center gap-1 text-primary hover:underline"
                title={`Przywróć ${Object.keys(filtersHistory[0]).length} filtrów`}
              >
                <Undo2 className="h-3 w-3" />
                <span>Przywróć filtry</span>
                {filtersHistory.length > 1 && (
                  <span className="text-muted-foreground/60">({filtersHistory.length})</span>
                )}
              </button>
            </>
          )}
        </div>

        {/* Center/Right: Pagination Controls & Page Size Selector */}
        <div className="flex items-center gap-4 shrink-0">
          {/* Page navigation */}
          {!isAll && pageCount > 1 && (
            <div className="flex items-center gap-1 tabular-nums">
              <button
                onClick={() => onPageChange?.(0)}
                disabled={!canPrev}
                className="p-1 rounded hover:bg-muted disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Pierwsza strona"
              >
                <ChevronsLeft className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => onPageChange?.(pageIndex - 1)}
                disabled={!canPrev}
                className="p-1 rounded hover:bg-muted disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Poprzednia strona"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
              </button>

              <span className="px-1 text-foreground font-medium">
                Strona {pageIndex + 1} z {pageCount}
              </span>

              <button
                onClick={() => onPageChange?.(pageIndex + 1)}
                disabled={!canNext}
                className="p-1 rounded hover:bg-muted disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Następna strona"
              >
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => onPageChange?.(pageCount - 1)}
                disabled={!canNext}
                className="p-1 rounded hover:bg-muted disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Ostatnia strona"
              >
                <ChevronsRight className="h-3.5 w-3.5" />
              </button>
            </div>
          )}

          {/* Page size buttons */}
          <div className="flex items-center gap-1 bg-muted/60 p-0.5 rounded border border-border/40 text-[11px]">
            <span className="text-muted-foreground px-1 hidden md:inline">Na stronę:</span>
            {[50, 100, 250, 0].map((size) => {
              const active = pageSize === size;
              return (
                <button
                  key={size}
                  onClick={() => onPageSizeChange?.(size)}
                  className={`px-1.5 py-0.5 rounded transition-all font-medium ${
                    active
                      ? "bg-background text-foreground shadow-xs font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {size === 0 ? "Wszystkie" : size}
                </button>
              );
            })}
          </div>

          {/* Meta & Density */}
          <div className="flex items-center gap-2 tabular-nums">
            <span className="text-muted-foreground/40 hidden lg:inline">·</span>
            <span className="capitalize hidden lg:inline">{density}</span>
            {fileMeta?.name && (
              <>
                <span className="text-muted-foreground/40 hidden lg:inline">·</span>
                <span className="truncate max-w-[160px] hidden lg:inline" title={fileMeta.name}>
                  {fileMeta.name}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
