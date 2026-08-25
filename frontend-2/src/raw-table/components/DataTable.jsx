import { useState, useRef, useMemo, useEffect, useCallback, useDeferredValue, memo } from "react";
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  DndContext,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  closestCenter,
} from "@dnd-kit/core";
import { restrictToHorizontalAxis } from "@dnd-kit/modifiers";
import {
  SortableContext,
  horizontalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";
import { CellRenderer } from "./CellRenderer";
import { FilterInput } from "./FilterInput";
import { SortableHeader } from "./SortableHeader";
import { getEnumValues } from "@/lib/csv";
import { cn } from "@/lib/utils";

const STICKY_COLS_MOBILE = 2; // first 2 cols sticky on mobile

export function DataTable({
  columns,
  rows,
  schema,
  columnOrder,
  columnVisibility,
  setColumnOrder,
  setColumnVisibility,
  onColumnHide,
  onFilteredCountChange,
  sortStack,
  setSortStack,
  filters,
  setFilters,
  density,
  onFocusedColumnChange,
  focusedColumn,
  selectedRowId,
  selectedRowIndex,
  onRowClick,
  globalFilter,
}) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor)
  );

  const tableContainerRef = useRef(null);

  // Defer the global filter so typing stays snappy. The deferred value
  // lags behind by one render, so the table re-filter happens at a
  // lower priority than the input update.
  const deferredGlobalFilter = useDeferredValue(globalFilter);
  const isFilterStale = globalFilter !== deferredGlobalFilter;

  // Stable row identity from id_unikalne. Without this, TanStack defaults
  // to the row's array index, so when the sort order changes the keys
  // shift and React re-mounts every row — re-firing the row-settle
  // animation and re-rendering 5,000 components.
  const getRowId = useCallback(
    (row, index) => String(row?.id_unikalne ?? `__row-${index}`),
    []
  );

  // Column defs — attach the right filterFn per type so TanStack knows how to
  // apply each filter value shape (array, {min,max}, {from,to}) against row data.
  const tableColumns = useMemo(() => {
    return columns.map((colId) => {
      const colType = schema?.find((s) => s.id === colId)?.type || "text";
      const width = defaultWidth(colId, colType);
      let filterFn;
      if (colType === "enum") {
        // Cell values are comma-separated strings ("A, B, C"); filter is an array
        // of checked labels. Match: cell contains ANY of the selected labels.
        filterFn = "enumContains";
      } else if (colType === "number") {
        filterFn = "inNumberRange";
      } else if (colType === "date") {
        filterFn = "dateRange";
      }
      return {
        id: colId,
        accessorKey: colId,
        header: colId,
        enableSorting: true,
        sortingFn: getSortingFn(colType),
        filterFn,
        size: width,
        meta: { type: colType, width, align: colType === "number" ? "right" : "left" },
        cell: ({ getValue }) => (
          <CellRenderer
            value={getValue()}
            type={colType}
            columnId={colId}
          />
        ),
      };
    });
  }, [columns, schema]);

  // Total table width (for horizontal scroll)
  const totalTableWidth = useMemo(
    () => tableColumns.reduce((sum, c) => sum + (c.size || 160), 0),
    [tableColumns]
  );

  // Pre-compute enum values once per (rows, schema) change.
  // Previously this ran `getEnumValues(rows, columnId)` on every render of
  // every column — O(N) per column per render = O(C·N) work per render.
  // For 5 enum columns × 5,000 rows = 25,000 ops on every keystroke.
  const enumValuesByColumn = useMemo(() => {
    if (!schema) return {};
    const out = {};
    for (const s of schema) {
      if (s.type === "enum") {
        const v = getEnumValues(rows, s.id);
        if (v && v.length > 0) out[s.id] = v;
      }
    }
    return out;
  }, [rows, schema]);

  // Derive columnFilters in the same shape TanStack expects: [{id, value}, ...]
  // Applied directly in table state — no useEffect, no stale-dep bugs.
  const columnFilters = useMemo(
    () =>
      Object.entries(filters || {})
        .filter(([id]) => columns.includes(id))
        .map(([id, value]) => ({ id, value })),
    [filters, columns]
  );

  const table = useReactTable({
    data: rows,
    columns: tableColumns,
    state: {
      ...(columnOrder && columnOrder.length > 0 ? { columnOrder } : {}),
      ...(Object.keys(columnVisibility).length > 0 ? { columnVisibility } : {}),
      sorting: sortStack,
      globalFilter: deferredGlobalFilter,
      columnFilters,
    },
    getRowId,
    onColumnOrderChange: setColumnOrder,
    onColumnVisibilityChange: setColumnVisibility,
    onSortingChange: setSortStack,
    onGlobalFilterChange: () => {},
    globalFilterFn: "includesString",
    filterFns: { dateRange: dateRangeFilter, enumContains: enumContainsFilter },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    enableMultiSort: true,
    isMultiSortEvent: (e) => Boolean(e?.shiftKey),
    enableColumnResizing: false,
  });

  const visibleColumns = table.getVisibleLeafColumns();
  const visibleColumnIds = visibleColumns.map((c) => c.id);
  const tableRows = table.getRowModel().rows;
  const rowHeight = density === "compact" ? 32 : 44;

  // The settle-in fade should run once per data load, not on every
  // sort/filter. We flip `showSettle` true on (rows, schema) change, then
  // schedule it off ~700 ms later (past the longest 60×4 ms stagger).
  // Using a counter so the second flip still triggers a re-render to
  // remove the class.
  const dataVersion = useMemo(() => `${rows.length}|${rows[0]?.id_unikalne ?? ""}`, [rows]);
  const [settleTick, setSettleTick] = useState(0);
  useEffect(() => {
    if (tableRows.length === 0) return;
    setSettleTick((n) => n + 1);
    const t = setTimeout(() => setSettleTick((n) => n + 1), 700);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataVersion]);
  const showSettle = settleTick % 2 === 0 && tableRows.length > 0;

  // Report filtered count up
  useEffect(() => {
    onFilteredCountChange?.(tableRows.length);
  }, [tableRows.length, onFilteredCountChange]);

  // Column reorder (dnd-kit)
  const handleDragEnd = useCallback(
    (event) => {
      const { active, over } = event;
      if (active && over && active.id !== over.id) {
        const oldIndex = visibleColumnIds.indexOf(active.id);
        const newIndex = visibleColumnIds.indexOf(over.id);
        if (oldIndex < 0 || newIndex < 0) return;
        const next = arrayMove(visibleColumnIds, oldIndex, newIndex);
        // merge with hidden cols (preserve their order)
        const hidden = columns.filter((c) => !next.includes(c));
        setColumnOrder([...next, ...hidden]);
      }
    },
    [visibleColumnIds, columns, setColumnOrder]
  );

  // Per-column filter
  const updateColumnFilter = useCallback(
    (colId, value) => {
      setFilters((prev) => {
        const next = { ...prev };
        if (value === undefined || value === "" || (Array.isArray(value) && value.length === 0)) {
          delete next[colId];
        } else {
          next[colId] = value;
        }
        return next;
      });
    },
    [setFilters]
  );

  // Column header context menu
  const [menu, setMenu] = useState(null);
  const handleHeaderContextMenu = (e, column) => {
    e.preventDefault();
    setMenu({ x: e.clientX, y: e.clientY, column });
  };

  // Report column focus (click) so the parent can drive ⌘F
  // — wires the previously-dead onFocusedColumnChange prop.
  const lastFocusedRef = useRef(null);
  const reportColumnFocus = useCallback(
    (colId) => {
      if (lastFocusedRef.current !== colId) {
        lastFocusedRef.current = colId;
        onFocusedColumnChange?.(colId);
      }
    },
    [onFocusedColumnChange]
  );

  return (
    <div className="relative h-full">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        modifiers={[restrictToHorizontalAxis]}
        onDragEnd={handleDragEnd}
      >
        <div
          ref={tableContainerRef}
          className="h-full overflow-auto scrollbar-thin"
          onScroll={() => setMenu(null)}
          onClick={() => menu && setMenu(null)}
        >
          <table className="border-collapse text-sm" style={{ tableLayout: "fixed", width: totalTableWidth }}>
            <thead className="sticky top-0 z-30 bg-card">
              <SortableContext
                items={visibleColumnIds}
                strategy={horizontalListSortingStrategy}
              >
                <tr>
                  {visibleColumns.map((column) => {
                    if (!column) return null;
                    const sortIndex = (sortStack || []).findIndex((s) => s && s.id === column.id);
                    return (
                      <SortableHeader
                        key={column.id}
                        column={column}
                        sortIndex={sortIndex >= 0 ? sortIndex : null}
                        onContextMenu={handleHeaderContextMenu}
                        onClick={() => reportColumnFocus(column.id)}
                        focused={focusedColumn === column.id}
                        onHide={(id) => {
                          setColumnVisibility((prev) => ({ ...prev, [id]: false }));
                          onColumnHide?.(id);
                        }}
                      />
                    );
                  })}
                </tr>
              </SortableContext>
              <tr className="bg-muted/30 border-b">
                {visibleColumns.map((column) => {
                  if (!column) return null;
                  const colType = column.columnDef.meta?.type || "text";
                  const enumVals = enumValuesByColumn[column.id];
                  return (
                    <th
                      key={column.id}
                      data-col-filter={column.id}
                      style={{ width: column.columnDef.meta?.width ? `${column.columnDef.meta.width}px` : undefined }}
                      className="px-1.5 py-1 border-r border-border"
                    >
                      <FilterInput
                        columnId={column.id}
                        type={colType}
                        value={filters[column.id]}
                        onChange={(v) => updateColumnFilter(column.id, v)}
                        enumValues={enumVals}
                      />
                    </th>
                  );
                })}
              </tr>
            </thead>

            <tbody style={{ opacity: isFilterStale ? 0.6 : 1, transition: "opacity 100ms" }}>
              {tableRows.map((row, i) => {
                if (!row) return null;
                const isSelected = selectedRowId
                  ? row.id === selectedRowId
                  : selectedRowIndex === i;
                return (
                  <Row
                    key={row.id}
                    row={row}
                    index={i}
                    rowHeight={rowHeight}
                    isSelected={isSelected}
                    onClick={onRowClick}
                    showSettle={showSettle}
                  />
                );
              })}
              {tableRows.length === 0 && (
                <tr>
                  <td colSpan={visibleColumns.length} className="text-center py-16">
                    <div className="text-sm text-muted-foreground">
                      <p className="font-medium mb-1">Brak wyników dla obecnych filtrów</p>
                      <button
                        onClick={() => setFilters({})}
                        className="text-xs text-primary hover:underline"
                      >
                        Wyczyść filtry
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </DndContext>

      {menu && (
        <HeaderContextMenu
          x={menu.x}
          y={menu.y}
          column={menu.column}
          onClose={() => setMenu(null)}
          onAction={(action) => {
            setMenu(null);
            if (action === "sort-asc") {
              setSortStack((prev) => mergeSort(prev, menu.column.id, false));
            } else if (action === "sort-desc") {
              setSortStack((prev) => mergeSort(prev, menu.column.id, true));
            } else if (action === "clear-sort") {
              setSortStack((prev) => prev.filter((s) => s.id !== menu.column.id));
            } else if (action === "hide") {
              setColumnVisibility((prev) => ({ ...prev, [menu.column.id]: false }));
              onColumnHide?.(menu.column.id);
            } else if (action === "pin") {
              // simple: move to front
              setColumnOrder((prev) => {
                const order = prev || columns;
                return [menu.column.id, ...order.filter((c) => c !== menu.column.id)];
              });
            }
          }}
        />
      )}
    </div>
  );
}

/**
 * Memoized row. Re-renders only when its data, selection, or props
 * change. With stable getRowId, sort/filter reuses these DOM nodes —
 * only the row becoming selected and the one losing selection re-render
 * (down from "every row in the table" before).
 */
// Brand-name matcher for "nabijarka" (rolling-machine) vendors — rows that
// carry any of these brands get a gentle blue tint + a small "maszynka"
// badge so they're easy to spot when scanning the catalog. Extend the
// brand list when new machine brands land.
const NABIJARKA_BRANDS = ["PowerMatic", "Hawk"];
const NABIJARKA_BG = "bg-sky-50/40 hover:bg-sky-100/60 dark:bg-sky-950/20 dark:hover:bg-sky-950/30";

function isNabijarkaRow(row) {
  const brands = String(row?.marki_nabijarki || "");
  if (!brands) return false;
  return NABIJARKA_BRANDS.some((b) => brands.includes(b));
}

const Row = memo(function Row({ row, index, rowHeight, isSelected, onClick, showSettle }) {
  const settleDelay = showSettle && index < 60 ? index * 4 : 0;
  const isNabijarka = isNabijarkaRow(row.original);
  return (
    <tr
      data-cv="row"
      onClick={() => onClick?.(index, row.original)}
      className={cn(
        "border-b border-border/50 cursor-pointer group",
        "hover:bg-muted/40",
        isNabijarka && NABIJARKA_BG,
        settleDelay > 0 && "row-settle",
        isSelected && "bg-accent"
      )}
      style={{
        height: rowHeight,
        animationDelay: settleDelay ? `${settleDelay}ms` : undefined,
      }}
    >
      {row.getVisibleCells().map((cell, j) => {
        if (!cell?.column) return null;
        const isSticky = j < STICKY_COLS_MOBILE;
        return (
          <td
            key={cell.id}
            style={{ width: cell.column.columnDef.meta?.width }}
            className={cn(
              "px-3 align-middle border-r border-border/30 overflow-hidden text-ellipsis whitespace-nowrap",
              isSticky &&
                cn(
                  "sticky left-0 z-10 after:absolute after:right-0 after:top-0 after:bottom-0 after:w-px after:bg-border/50 after:shadow-[2px_0_4px_-2px_rgba(0,0,0,0.05)] md:static md:after:hidden",
                  isNabijarka
                    ? `${NABIJARKA_BG} md:bg-transparent`
                    : "bg-card group-hover:bg-muted/40"
                )
            )}
          >
            {j === 0 && isNabijarka && (
              <span
                className="mr-2 inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wider bg-sky-100/80 text-sky-700 border border-sky-200/80 dark:bg-sky-900/30 dark:text-sky-300 dark:border-sky-800/60 shrink-0 align-middle"
                title="Firma sprzedaje maszynki (nabijarki) — PowerMatic, Hawk itp."
              >
                maszynka
              </span>
            )}
            {flexRender(cell.column.columnDef.cell, cell.getContext())}
          </td>
        );
      })}
    </tr>
  );
});

function defaultWidth(colId, type) {
  if (colId === "id_unikalne") return 130;
  if (colId === "nazwa_firmy") return 280;
  if (colId === "adres") return 240;
  if (colId === "notatki" || colId === "flagi" || colId === "zrodlo_danych") return 260;
  if (colId === "www") return 200;
  if (colId === "email") return 220;
  if (colId === "telefon") return 160;
  if (colId === "linkedin" || colId === "facebook" || colId === "instagram" || colId === "tiktok") return 180;
  if (colId === "nip_vat") return 140;
  if (colId === "rejestr_id") return 150;
  if (colId === "decydent" || colId === "email_decydent") return 200;
  if (colId === "data_weryfikacji") return 110;
  if (colId === "kanal_zamiennik" || colId === "marki_nabijarki" || colId === "marka_wlasna_oem" || colId === "sourcing" || colId === "kanal_sprzedaży" || colId === "powinowactwo_nabijarki" || colId === "cross_sell_potential") return 200;
  if (type === "url" || type === "email") return 200;
  if (type === "date") return 110;
  if (type === "number") return 90;
  if (type === "phone") return 140;
  if (type === "enum") return 130;
  return 160;
}

function getSortingFn(type) {
  switch (type) {
    case "number":
      return (a, b, id) => {
        const av = a.getValue(id);
        const bv = b.getValue(id);
        if (av == null && bv == null) return 0;
        if (av == null) return 1; // nulls last
        if (bv == null) return -1;
        return av - bv;
      };
    case "date":
      return (a, b, id) => {
        const av = a.getValue(id);
        const bv = b.getValue(id);
        const ad = av instanceof Date ? av.getTime() : av ? new Date(av).getTime() : null;
        const bd = bv instanceof Date ? bv.getTime() : bv ? new Date(bv).getTime() : null;
        if (ad == null && bd == null) return 0;
        if (ad == null) return 1;
        if (bd == null) return -1;
        return ad - bd;
      };
    case "url":
    case "email":
      return (a, b, id) => {
        const av = String(a.getValue(id) || "");
        const bv = String(b.getValue(id) || "");
        return av.localeCompare(bv);
      };
    default:
      return "alphanumeric";
  }
}

/**
 * Custom filterFn for date-range columns. Filter value is {from?, to?}.
 * Coerces both the row value and the bound inputs to Date.getTime() so
 * {min,max} numeric comparison works on dates.
 */
const dateRangeFilter = (row, columnId, filterValue) => {
  if (!filterValue) return true;
  const raw = row.getValue(columnId);
  if (raw == null) return false;
  const cellMs = raw instanceof Date ? raw.getTime() : new Date(raw).getTime();
  if (isNaN(cellMs)) return true;
  if (filterValue.from) {
    const fromMs = new Date(filterValue.from).getTime();
    if (!isNaN(fromMs) && cellMs < fromMs) return false;
  }
  if (filterValue.to) {
    const toMs = new Date(filterValue.to).getTime();
    if (!isNaN(toMs) && cellMs > toMs) return false;
  }
  return true;
};

/**
 * Custom filterFn for enum columns. Cell values are comma-separated strings
 * ("A, B, C"); filter value is an array of checked labels ["A", "B"].
 * Match: the cell contains AT LEAST ONE of the selected labels (OR logic).
 */
const enumContainsFilter = (row, columnId, filterValue) => {
  if (!filterValue || filterValue.length === 0) return true;
  const raw = row.getValue(columnId);
  if (raw == null || raw === "") return false;
  // Cell may be a string ("A, B") or already an array.
  const cellItems = Array.isArray(raw) ? raw : String(raw).split(",").map((s) => s.trim());
  return filterValue.some((label) =>
    cellItems.some((item) => item.toLowerCase() === label.toLowerCase())
  );
};

function mergeSort(stack, id, desc) {
  const existing = stack.find((s) => s.id === id);
  if (existing) {
    if (existing.desc === desc) {
      // toggle off
      return stack.filter((s) => s.id !== id);
    }
    return stack.map((s) => (s.id === id ? { ...s, desc } : s));
  }
  return [...stack, { id, desc }];
}

function HeaderContextMenu({ x, y, onAction }) {
  return (
    <div
      className="fixed z-50 min-w-[180px] rounded-md border bg-popover p-1 shadow-md text-sm"
      style={{ left: x, top: y }}
      onClick={(e) => e.stopPropagation()}
    >
      <button
        onClick={() => onAction("sort-asc")}
        className="flex items-center gap-2 w-full px-2 py-1.5 rounded hover:bg-accent text-left"
      >
        <span>↑</span> Sortuj rosnąco
      </button>
      <button
        onClick={() => onAction("sort-desc")}
        className="flex items-center gap-2 w-full px-2 py-1.5 rounded hover:bg-accent text-left"
      >
        <span>↓</span> Sortuj malejąco
      </button>
      <button
        onClick={() => onAction("clear-sort")}
        className="flex items-center gap-2 w-full px-2 py-1.5 rounded hover:bg-accent text-left"
      >
        <span className="opacity-50">×</span> Wyczyść sort
      </button>
      <div className="border-t my-1" />
      <button
        onClick={() => onAction("pin")}
        className="flex items-center gap-2 w-full px-2 py-1.5 rounded hover:bg-accent text-left"
      >
        <span>📌</span> Przypnij do lewej
      </button>
      <button
        onClick={() => onAction("hide")}
        className="flex items-center gap-2 w-full px-2 py-1.5 rounded hover:bg-accent text-left text-destructive"
      >
        <span>👁</span> Ukryj kolumnę
      </button>
    </div>
  );
}
