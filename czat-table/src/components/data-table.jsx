import * as React from "react"
import { motion, AnimatePresence, LayoutGroup } from "framer-motion"
import { Table, TableBody, TableCell } from "@/components/ui/table"
import { TypeCell } from "@/components/type-cell"
import { matchFilter } from "@/components/type-filter"
import { compareValues } from "@/lib/csv"
import { cn, prefersReducedMotion } from "@/lib/utils"
import { TableHeaderRow } from "@/components/table-header"
import { ColumnMenu } from "@/components/column-menu"

const PINNED_DEFAULT = 2 // first N columns stay sticky on mobile (id + name)
const MIN_COL_WIDTH = 80
const DEFAULT_COL_WIDTH = 180

/**
 * Resolved column model merging parsed schema + persisted state.
 */
function resolveColumns(parsed, prefs) {
  const overrides = prefs.columns || {}
  return parsed.columns.map((c, idx) => {
    const o = overrides[c.id] || {}
    return {
      ...c,
      visible: o.visible !== false,
      pinned: idx < PINNED_DEFAULT, // first 2 always pinned on mobile
      order: typeof o.order === "number" ? o.order : idx,
      width: o.width || DEFAULT_COL_WIDTH,
    }
  })
}

export const DataTable = React.forwardRef(function DataTable({ data, prefs, onPrefsChange, onCopy, onVisibleCountChange, onPaginationChange }, scrollRef) {
  // Stable references for lookup
  const columns = React.useMemo(() => resolveColumns(data, prefs), [data, prefs])
  const visibleColumns = React.useMemo(
    () => [...columns].filter((c) => c.visible).sort((a, b) => a.order - b.order),
    [columns],
  )
  const columnsById = React.useMemo(() => {
    const m = new Map()
    for (const c of columns) m.set(c.id, c)
    return m
  }, [columns])

  // Sort state mirrors prefs.sort, normalized
  const sort = prefs.sort || []
  // Filters as object { colId: value } mirrors prefs.filters
  const filters = prefs.filters || {}
  // Pagination
  const perPage = prefs.pagination?.perPage ?? 100
  const page = prefs.pagination?.page ?? 1

  // Row highlight for keyboard navigation. { rowIndex, colIndex } are indices into
  // pageRows/visibleColumns. Start at (0, 0) so the first cell is visibly
  // selected on load and ↑/↓ move naturally (0 → 1 → 2).
  const [selected, setSelected] = React.useState({ rowIndex: 0, colIndex: 0 })

  // Defer the heavy work (filter + sort + paginate) so typing in a filter
  // input or clicking a sort header never blocks the input — React renders
  // the keystroke immediately, then catches up with the recompute.
  const deferredFilters = React.useDeferredValue(filters)
  const deferredSort = React.useDeferredValue(sort)

  // Apply filters (deferred — see above)
  const filteredRows = React.useMemo(() => {
    const entries = Object.entries(deferredFilters).filter(([_, v]) => {
      if (v == null) return false
      if (typeof v === "string") return v !== ""
      if (Array.isArray(v)) return v.length > 0
      if (typeof v === "object") return Boolean(v.min || v.max || v.from || v.to)
      return true
    })
    if (entries.length === 0) return data.rows
    return data.rows.filter((row) =>
      entries.every(([colId, value]) => {
        const col = columnsById.get(colId)
        if (!col) return true
        return matchFilter(row[colId], value, col.type)
      }),
    )
  }, [data.rows, deferredFilters, columnsById])

  // Apply sort (deferred)
  const sortedRows = React.useMemo(() => {
    if (deferredSort.length === 0) return filteredRows
    const arr = [...filteredRows]
    arr.sort((a, b) => {
      for (const s of deferredSort) {
        const col = columnsById.get(s.colId)
        if (!col) continue
        const cmp = compareValues(a[s.colId], b[s.colId], col.type, s.dir)
        if (cmp !== 0) return cmp
      }
      return 0
    })
    return arr
  }, [filteredRows, deferredSort, columnsById])

  // Pagination math
  const totalRows = sortedRows.length
  const totalPages = Math.max(1, Math.ceil(totalRows / perPage))
  const safePage = Math.min(Math.max(1, page), totalPages)
  const pageStart = (safePage - 1) * perPage
  const pageEnd = Math.min(pageStart + perPage, totalRows)
  const pageRows = sortedRows.slice(pageStart, pageEnd)

  // Notify parent of pagination state (for status bar)
  React.useEffect(() => {
    onPaginationChange?.({ page: safePage, perPage, totalPages, totalRows, pageStart, pageEnd })
  }, [safePage, perPage, totalPages, totalRows, pageStart, pageEnd, onPaginationChange])

  // Reset to page 1 when filters or sort change (so user always sees "the first page" of the new view).
  // Compare by JSON hash so we don't read stale `prefs` from the outer closure.
  const sortKey = React.useMemo(() => JSON.stringify(sort), [sort])
  const filterKey = React.useMemo(() => JSON.stringify(filters), [filters])
  const prevSortKey = React.useRef(sortKey)
  const prevFilterKey = React.useRef(filterKey)
  React.useEffect(() => {
    if (prevSortKey.current === sortKey && prevFilterKey.current === filterKey) return
    prevSortKey.current = sortKey
    prevFilterKey.current = filterKey
    onPrefsChange((p) => {
      if (p.pagination?.page === 1) return p
      return { ...p, pagination: { ...(p.pagination || {}), page: 1 } }
    })
  }, [sortKey, filterKey, onPrefsChange])

  // Density
  const density = prefs.density || "compact"
  const rowHeight = density === "compact" ? 32 : 44

  // Scroll ref (not used for virtualization anymore; used by toolbar's auto-hide)
  const parentRef = React.useRef(null)
  React.useImperativeHandle(scrollRef, () => parentRef.current, [])

  // Persist prefs (memoize identity so we don't thrash on every render)
  const updatePrefs = React.useCallback(
    (patch) => {
      onPrefsChange({ ...prefs, ...patch })
    },
    [onPrefsChange, prefs],
  )

  const setSort = (next) => updatePrefs({ sort: next })
  const setFilters = (next) => updatePrefs({ filters: next })
  const setColumn = (colId, patch) =>
    updatePrefs({
      columns: {
        ...(prefs.columns || {}),
        [colId]: { ...(prefs.columns?.[colId] || {}), ...patch },
      },
    })

  // Keyboard navigation on the body: ↑/↓ rows, ←/→ cols, Enter to copy, Cmd+F to focus filter
  function onBodyKeyDown(e) {
    const isMod = e.metaKey || e.ctrlKey
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setSelected((s) => {
        const r = s?.rowIndex ?? -1
        const next = Math.min(pageRows.length - 1, r + 1)
        return { rowIndex: Math.max(0, next), colIndex: s?.colIndex ?? 0 }
      })
      return
    }
    if (e.key === "ArrowUp") {
      e.preventDefault()
      setSelected((s) => {
        const r = s?.rowIndex ?? pageRows.length
        const next = Math.max(0, r - 1)
        return { rowIndex: next, colIndex: s?.colIndex ?? 0 }
      })
      return
    }
    if (e.key === "ArrowRight") {
      e.preventDefault()
      setSelected((s) => ({
        rowIndex: s?.rowIndex ?? 0,
        colIndex: Math.min(visibleColumns.length - 1, (s?.colIndex ?? -1) + 1),
      }))
      return
    }
    if (e.key === "ArrowLeft") {
      e.preventDefault()
      setSelected((s) => ({
        rowIndex: s?.rowIndex ?? 0,
        colIndex: Math.max(0, (s?.colIndex ?? visibleColumns.length) - 1),
      }))
      return
    }
    if (e.key === "Enter") {
      e.preventDefault()
      const row = pageRows[selected.rowIndex]
      const col = visibleColumns[selected.colIndex]
      if (row && col) {
        const value = row[col.id] ?? ""
        if (navigator.clipboard?.writeText) {
          navigator.clipboard.writeText(String(value)).catch(() => {})
        }
        onCopy?.({ value: String(value), colId: col.id, rowIndex: selected.rowIndex, colIndex: selected.colIndex })
      }
      return
    }
    if (isMod && e.key.toLowerCase() === "f") {
      e.preventDefault()
      const col = visibleColumns[selected?.colIndex ?? 0]
      if (col) {
        // Query from document root — the filter input lives in the sticky
        // header, not inside the body scroll container.
        const input = document.querySelector(`input[aria-label="Filter ${col.name}"]`)
        if (input) input.focus()
      }
    }
  }

  // Header sort click handler
  function onHeaderClick(col, e) {
    const existing = sort.find((s) => s.colId === col.id)
    if (e.shiftKey) {
      if (existing) {
        // Toggle dir
        setSort(sort.map((s) => (s.colId === col.id ? { ...s, dir: s.dir === "asc" ? "desc" : "asc" } : s)))
      } else {
        setSort([...sort, { colId: col.id, dir: "asc" }])
      }
    } else {
      if (existing) {
        if (existing.dir === "asc") setSort([{ colId: col.id, dir: "desc" }])
        else setSort([]) // was desc → clear
      } else {
        setSort([{ colId: col.id, dir: "asc" }])
      }
    }
  }

  // Column resize
  const resizingRef = React.useRef(null)
  function startResize(col, e) {
    e.preventDefault()
    e.stopPropagation()
    const startX = e.clientX
    const startW = col.width
    function onMove(ev) {
      const dx = ev.clientX - startX
      const w = Math.max(MIN_COL_WIDTH, startW + dx)
      // direct set without going through React state to keep it snappy
      const th = document.querySelector(`[data-col="${CSS.escape(col.id)}"]`)
      if (th) th.style.width = `${w}px`
      resizingRef.current = { colId: col.id, w }
    }
    function onUp() {
      window.removeEventListener("mousemove", onMove)
      window.removeEventListener("mouseup", onUp)
      const r = resizingRef.current
      resizingRef.current = null
      if (r) setColumn(col.id, { width: r.w })
    }
    window.addEventListener("mousemove", onMove)
    window.addEventListener("mouseup", onUp)
  }

  // Column drag reorder
  const dragRef = React.useRef(null)
  function startDrag(col, e) {
    e.preventDefault()
    e.stopPropagation()
    dragRef.current = { colId: col.id, startX: e.clientX, moved: false }
    function onMove(ev) {
      if (!dragRef.current) return
      const dx = ev.clientX - dragRef.current.startX
      if (Math.abs(dx) > 4) dragRef.current.moved = true
    }
    function onUp() {
      window.removeEventListener("mousemove", onMove)
      window.removeEventListener("mouseup", onUp)
      dragRef.current = null
    }
    window.addEventListener("mousemove", onMove)
    window.addEventListener("mouseup", onUp)
  }

  // Right-click / long-press context menu
  const [context, setContext] = React.useState(null) // { col, x, y }
  const longPressRef = React.useRef(null)

  function openContext(col, x, y) {
    setContext({ col, x, y })
  }
  function closeContext() {
    setContext(null)
  }

  React.useEffect(() => {
    if (!context) return
    function onKey(e) {
      if (e.key === "Escape") closeContext()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [context])

  function onContextMenu(col, e) {
    e.preventDefault()
    openContext(col, e.clientX, e.clientY)
  }
  function onHeaderPointerDown(col, e) {
    if (e.button !== 0) return
    // Long-press for mobile
    longPressRef.current = setTimeout(() => {
      const r = e.currentTarget.getBoundingClientRect()
      openContext(col, r.left + r.width / 2, r.bottom + 4)
    }, 500)
  }
  function onHeaderPointerUp() {
    if (longPressRef.current) {
      clearTimeout(longPressRef.current)
      longPressRef.current = null
    }
  }
  function onHeaderPointerLeave() {
    if (longPressRef.current) {
      clearTimeout(longPressRef.current)
      longPressRef.current = null
    }
  }

  // Render rows for the current page (pagination, no virtualization)
  const reduceMotion = prefersReducedMotion()

  // For pinned columns, set CSS variables on the table so headers/cells can
  // position themselves with `left: var(--pinned-w-1)` etc.
  const pinnedCols = visibleColumns.filter((c) => c.pinned)
  const pinnedVars = pinnedCols.reduce((acc, c, i) => {
    acc[`--pinned-w-${i + 1}`] = `${pinnedCols.slice(0, i).reduce((s, cc) => s + cc.width, 0)}px`
    return acc
  }, {})

  return (
    <div
      className={cn(
        "relative isolate flex h-full min-h-0 flex-col",
        "bg-background",
      )}
    >
      {/* Sticky header — extracted to TableHeaderRow */}
      <TableHeaderRow
        visibleColumns={visibleColumns}
        pinnedCols={pinnedCols}
        sort={sort}
        filters={filters}
        defaultColWidth={DEFAULT_COL_WIDTH}
        onHeaderClick={onHeaderClick}
        onHeaderContextMenu={onContextMenu}
        onHeaderPointerDown={onHeaderPointerDown}
        onHeaderPointerUp={onHeaderPointerUp}
        onHeaderPointerLeave={onHeaderPointerLeave}
        onResizeStart={startResize}
        onResetWidth={(colId) => setColumn(colId, { width: DEFAULT_COL_WIDTH })}
        onFilterChange={(colId, v) => {
          const next = { ...filters }
          const emptyText = v === ""
          const emptyArr = Array.isArray(v) && v.length === 0
          const emptyRange =
            typeof v === "object" && !Array.isArray(v) && !v.min && !v.max && !v.from && !v.to
          if (emptyText || emptyArr || emptyRange) delete next[colId]
          else next[colId] = v
          setFilters(next)
        }}
      />

      {/* Body — paginated */}
      <div
        ref={parentRef}
        data-scroll-body="1"
        tabIndex={0}
        onKeyDown={onBodyKeyDown}
        className="relative min-h-0 flex-1 overflow-auto outline-none focus-visible:ring-1 focus-visible:ring-ring"
        style={{ touchAction: "pan-x pan-y" }}
      >
        <LayoutGroup>
          <Table style={{ width: "max-content", minWidth: "100%", position: "relative", ...pinnedVars }}>
            <TableBody>
              <AnimatePresence initial={false}>
                {pageRows.map((row, i) => {
                  const absoluteIndex = pageStart + i
                  const isSelectedRow = selected?.rowIndex === i
                  return (
                    <motion.tr
                      key={`${safePage}-${absoluteIndex}`}
                      layout={!reduceMotion ? "position" : false}
                      transition={{ type: "spring", stiffness: 380, damping: 36, mass: 0.6 }}
                      data-row-index={absoluteIndex}
                      onClick={(e) => {
                        // Clicking anywhere on the row sets the highlight to that row, col 0
                        setSelected((s) => ({ rowIndex: i, colIndex: s?.rowIndex === i ? s.colIndex : 0 }))
                      }}
                      className={cn(
                        "border-b text-sm transition-colors",
                        absoluteIndex % 2 === 1 && "bg-muted/20",
                        isSelectedRow && "bg-accent/30 hover:bg-accent/40",
                        !isSelectedRow && "hover:bg-muted/40",
                      )}
                      style={{ height: rowHeight }}
                    >
                      {visibleColumns.map((col, ci) => {
                        const value = row[col.id]
                        const pinnedIdx = col.pinned ? pinnedCols.findIndex((p) => p.id === col.id) : -1
                        const pinnedLeftStyle = pinnedIdx >= 0
                          ? { left: `var(--pinned-w-${pinnedIdx + 1})` }
                          : undefined
                        const isSelectedCell = isSelectedRow && selected?.colIndex === ci
                        return (
                          <TableCell
                            key={col.id}
                            style={{ width: col.width, minWidth: col.width, maxWidth: 480, ...pinnedLeftStyle }}
                            className={cn(
                              "border-r align-middle",
                              col.pinned && "sticky z-10 bg-inherit",
                              pinnedIdx === pinnedCols.length - 1 && "after:absolute after:right-0 after:top-0 after:z-10 after:h-full after:w-px after:bg-border after:shadow-[2px_0_4px_-2px_rgba(0,0,0,0.15)]",
                              isSelectedCell && "ring-2 ring-inset ring-primary",
                            )}
                            data-cell-row={i}
                            data-cell-col={ci}
                          >
                            <TypeCell
                              value={value}
                              type={col.type}
                              colId={col.id}
                              rowIndex={absoluteIndex}
                              colIndex={ci}
                              selected={isSelectedCell}
                              onCopy={onCopy}
                            />
                          </TableCell>
                        )
                      })}
                    </motion.tr>
                  )
                })}
              </AnimatePresence>
              {pageRows.length === 0 && (
                <tr>
                  <td colSpan={visibleColumns.length} className="px-3 py-16 text-center text-sm text-muted-foreground">
                    {totalRows === 0 ? "No rows match the current filters." : "This page is empty."}
                  </td>
                </tr>
              )}
            </TableBody>
          </Table>
        </LayoutGroup>
      </div>

      {/* Context menu — extracted to ColumnMenu */}
      {context && context.col && (
        <ColumnMenu
          col={context.col}
          x={context.x}
          y={context.y}
          onClose={closeContext}
          onSortAsc={() => {
            setSort([{ colId: context.col.id, dir: "asc" }])
            closeContext()
          }}
          onSortDesc={() => {
            setSort([{ colId: context.col.id, dir: "desc" }])
            closeContext()
          }}
          onAddSortAsc={() => {
            if (sort.find((s) => s.colId === context.col.id)) {
              setSort(sort.map((s) => (s.colId === context.col.id ? { ...s, dir: "asc" } : s)))
            } else {
              setSort([...sort, { colId: context.col.id, dir: "asc" }])
            }
            closeContext()
          }}
          onAddSortDesc={() => {
            if (sort.find((s) => s.colId === context.col.id)) {
              setSort(sort.map((s) => (s.colId === context.col.id ? { ...s, dir: "desc" } : s)))
            } else {
              setSort([...sort, { colId: context.col.id, dir: "desc" }])
            }
            closeContext()
          }}
          onClearSort={() => {
            setSort(sort.filter((s) => s.colId !== context.col.id))
            closeContext()
          }}
          onHide={() => {
            setColumn(context.col.id, { visible: false })
            closeContext()
          }}
          onResetWidth={() => {
            setColumn(context.col.id, { width: DEFAULT_COL_WIDTH })
            closeContext()
          }}
          onReset={() => {
            const next = { ...(prefs.columns || {}) }
            delete next[context.col.id]
            updatePrefs({ columns: next })
            closeContext()
          }}
        />
      )}
    </div>
  )
})
