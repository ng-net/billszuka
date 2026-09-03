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
    <div className="border-t bg-card/60 backdrop-blur-sm safe-bottom">
      <div className="px-3 sm:px-4 min-h-11 py-1.5 flex flex-col gap-1.5 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:h-10 sm:py-0 text-xs text-muted-foreground">
        {/* Left: Result & Filter stats */}
        <div className="flex items-center gap-2 sm:gap-3 overflow-x-auto touch-scroll-x hide-scrollbars">
          <span className="tabular-nums font-medium text-foreground shrink-0">
            <span>
              Wyniki: <strong className="text-brand font-semibold">{formatNumber(filteredRows)}</strong> / {formatNumber(totalRows)}
            </span>
            {!isAll && filteredRows > pageSize && (
              <span className="text-muted-foreground font-normal ml-1.5 hidden sm:inline">
                ({startRow}–{endRow})
              </span>
            )}
          </span>

          <span className="text-muted-foreground/40 shrink-0">·</span>
          <span className="tabular-nums shrink-0">
            <span className="text-foreground">{visibleColumns}</span>/{totalColumns} kolumn
          </span>

          {activeFilters > 0 && (
            <>
              <span className="text-muted-foreground/40 shrink-0">·</span>
              <span className="tabular-nums shrink-0">
                <span className="text-foreground">{activeFilters}</span>{" "}
                {activeFilters === 1 ? "filtr" : "filtrów"}
              </span>
            </>
          )}

          {sortStack.length > 0 && (
            <>
              <span className="text-muted-foreground/40 shrink-0">·</span>
              <span className="hidden md:inline truncate">
                Sortowanie: {sortStack.map((s) => `${getColumnLabel(s.id)} ${s.desc ? "↓" : "↑"}`).join(" · ")}
              </span>
            </>
          )}

          {canRestore && onRestoreFilters && (
            <>
              <span className="text-muted-foreground/40 shrink-0">·</span>
              <button
                onClick={() => onRestoreFilters(filtersHistory[0])}
                className="inline-flex items-center gap-1 text-brand hover:underline min-h-[36px] px-1"
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
        <div className="flex items-center gap-2 sm:gap-4 shrink-0 overflow-x-auto touch-scroll-x hide-scrollbars">
          {/* Page navigation */}
          {!isAll && pageCount > 1 && (
            <div className="flex items-center gap-0.5 tabular-nums shrink-0">
              <button
                onClick={() => onPageChange?.(0)}
                disabled={!canPrev}
                className="inline-flex h-9 w-9 sm:h-8 sm:w-8 items-center justify-center rounded-md hover:bg-muted disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Pierwsza strona"
                aria-label="Pierwsza strona"
              >
                <ChevronsLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() => onPageChange?.(pageIndex - 1)}
                disabled={!canPrev}
                className="inline-flex h-9 w-9 sm:h-8 sm:w-8 items-center justify-center rounded-md hover:bg-muted disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Poprzednia strona"
                aria-label="Poprzednia strona"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>

              <span className="px-2 text-foreground font-medium text-[11px] sm:text-xs shrink-0">
                {pageIndex + 1}/{pageCount}
              </span>

              <button
                onClick={() => onPageChange?.(pageIndex + 1)}
                disabled={!canNext}
                className="inline-flex h-9 w-9 sm:h-8 sm:w-8 items-center justify-center rounded-md hover:bg-muted disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Następna strona"
                aria-label="Następna strona"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
              <button
                onClick={() => onPageChange?.(pageCount - 1)}
                disabled={!canNext}
                className="inline-flex h-9 w-9 sm:h-8 sm:w-8 items-center justify-center rounded-md hover:bg-muted disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Ostatnia strona"
                aria-label="Ostatnia strona"
              >
                <ChevronsRight className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Page size buttons */}
          <div className="flex items-center gap-1 bg-muted/60 p-0.5 rounded-md border border-border/40 text-[11px] shrink-0">
            {[50, 100, 250, 0].map((size) => {
              const active = pageSize === size;
              return (
                <button
                  key={size}
                  onClick={() => onPageSizeChange?.(size)}
                  className={`inline-flex items-center justify-center min-w-[32px] sm:min-w-[28px] h-8 sm:h-7 px-1.5 rounded transition-all font-medium ${
                    active
                      ? "bg-background text-foreground shadow-xs font-semibold"
                      : "text-muted-foreground hover:text-foreground hover:bg-background/50"
                  }`}
                  aria-pressed={active}
                >
                  {size === 0 ? "All" : size}
                </button>
              );
            })}
          </div>

          {/* Meta & Density */}
          <div className="hidden lg:flex items-center gap-2 tabular-nums shrink-0">
            <span className="text-muted-foreground/40">·</span>
            <span className="capitalize">{density}</span>
            {fileMeta?.name && (
              <>
                <span className="text-muted-foreground/40">·</span>
                <span className="truncate max-w-[160px]" title={fileMeta.name}>
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
