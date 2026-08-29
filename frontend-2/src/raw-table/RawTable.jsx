import { useState, useEffect, useLayoutEffect, useMemo, useCallback, useRef, useTransition, forwardRef, useImperativeHandle } from "react";
import { motion } from "framer-motion";
import { toast, Toaster } from "sonner";
import {
  Search,
  X,
  Rows3,
  Rows4,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { TooltipProvider } from "@/components/ui/tooltip";

import { useCsv } from "@/hooks/useCsv";
import { loadPrefs, savePrefs } from "@/lib/prefs";
import { classifyBrand } from "@/lib/brand";
import { DEFAULT_VIEWS, toggleFilterValue } from "@/lib/views";
import { debounce } from "@/lib/utils";
import { getActiveDatasetInfo, getCustomDataset, clearCustomDataset } from "@/lib/datasetStorage";

import { EmptyState } from "./components/EmptyState";
import { DataTable } from "./components/DataTable";
import { ColumnToggle } from "./components/ColumnToggle";
import { ViewSwitcher } from "./components/ViewSwitcher";
import { QuickChips } from "./components/QuickChips";
import { StatusBar } from "./components/StatusBar";
import { CommandPalette } from "./components/CommandPalette";
import { LoadingState } from "./components/LoadingState";

const STATIC_MASTER_URL = "/master.csv";
// The master dataset is served by FastAPI via /api/master.csv. The Date.now()
// query param is the belt-and-braces guarantee that after Marceli edits
// data/master.csv manually, the next reload picks up the new content.
const MASTER_URL = "/api/master.csv";
const withCacheBuster = (url) => `${url}?v=${Date.now()}`;

export const RawTable = forwardRef(function RawTable(_props, ref) {
  const csv = useCsv();
  // Automatic data pre-load after the gate:
  // 1. Check if the user previously uploaded a custom CSV (stored in IndexedDB).
  // 2. If not, try the full master.csv from backend; if unreachable, fall back to public/master.csv;
  // 3. If that also fails, fall back to sample.csv;
  const bootRef = useRef(0); // 0 = try load, 1 = pending, 2 = settled
  const loadUrl = csv.loadUrl;
  const loadUrlRef = useRef(loadUrl);
  loadUrlRef.current = loadUrl;
  const loadParsedData = csv.loadParsedData;
  const loadParsedDataRef = useRef(loadParsedData);
  loadParsedDataRef.current = loadParsedData;

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      if (bootRef.current === 0 && csv.status === "idle") {
        bootRef.current = 1;
        try {
          const activeInfo = await getActiveDatasetInfo();
          if (cancelled) return;
          if (activeInfo?.type === "custom") {
            const stored = await getCustomDataset();
            if (cancelled) return;
            if (stored && stored.rows && stored.rows.length > 0) {
              loadParsedDataRef.current(stored);
              bootRef.current = 2;
              return;
            }
          }
        } catch {
          // fall through to master.csv
        }
        loadUrlRef.current(withCacheBuster(MASTER_URL), "master.csv", 0);
      } else if (bootRef.current === 1 && csv.status === "error") {
        bootRef.current = 2;
        // Fall back to static public/master.csv
        loadUrlRef.current(withCacheBuster(STATIC_MASTER_URL), "master.csv", 0);
      } else if (bootRef.current === 1 && csv.status === "ready") {
        bootRef.current = 2;
      }
    }
    boot();
    return () => {
      cancelled = true;
    };
  }, [csv.status]);

  // Manual trigger for the empty-state button. Clears custom upload,
  // directly invokes loadUrl for master.csv.
  const tryLoadData = useCallback(async () => {
    await clearCustomDataset();
    bootRef.current = 1;
    csv.loadUrl(withCacheBuster(STATIC_MASTER_URL), "master.csv", 0);
  }, [csv]);

  const onCsvStateChangeRef = useRef(_props.onCsvStateChange);
  // Safe to assign in a layout effect — fires synchronously after DOM paint,
  // never during the render phase (avoids react-compiler ref-during-render warning).
  useLayoutEffect(() => {
    onCsvStateChangeRef.current = _props.onCsvStateChange;
  });

  useEffect(() => {
    onCsvStateChangeRef.current?.({
      status: csv.status,
      progress: csv.progress,
      fileMeta: csv.fileMeta,
      activeDataset: csv.fileMeta?.name || "master.csv",
      cancel: csv.cancel,
      loadFile: csv.loadFile,
    });
    // Depend on the primitive status + the stable function refs. Listing
    // sub-property paths (csv.progress?.bytesParsed) caused oxlint to
    // flag missing parent dependencies; using the parent objects directly
    // is correct — progress/fileMeta are replaced by reference on each
    // update, so this fires whenever any field changes.
  }, [csv.status, csv.progress, csv.fileMeta, csv.cancel, csv.loadFile]);
  const [prefs, setPrefs] = useState(() => loadPrefs());
  const [globalFilter, setGlobalFilter] = useState("");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [focusedColumn, setFocusedColumn] = useState(null);
  const [selectedRowIndex, setSelectedRowIndex] = useState(-1);
  const [filteredCount, setFilteredCount] = useState(0);

  // Apply theme to <html>
  useEffect(() => {
    const root = document.documentElement;
    const apply = (t) => {
      if (t === "dark") root.classList.add("dark");
      else if (t === "light") root.classList.remove("dark");
      else {
        const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        root.classList.toggle("dark", isDark);
      }
    };
    apply(prefs.theme);
    if (prefs.theme === "system") {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      const cb = () => apply("system");
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    }
  }, [prefs.theme]);

  // Persist prefs immediately on every change so page refresh never loses state.
  useEffect(() => {
    savePrefs(prefs);
  }, [prefs]);

  // Initialize column order from CSV columns when loaded.
  // Move id_unikalne and nazwa_firmy to the front (sticky on mobile).
  // We derive from prefs + csv.columns instead of mirroring into prefs —
  // this is a one-time migration done on the fly, and avoids the
  // setState-in-effect antipattern.
  const rawColumnOrder = prefs.columnOrder;
  const columnOrder = useMemo(() => {
    if (csv.columns.length === 0) return rawColumnOrder || csv.columns;
    const base = rawColumnOrder && rawColumnOrder.every((c) => csv.columns.includes(c))
      ? rawColumnOrder
      : csv.columns;
    const pinned = ["id_unikalne", "nazwa_firmy"].filter((c) => base.includes(c));
    const rest = base.filter((c) => !pinned.includes(c));
    return [...pinned, ...rest];
  }, [rawColumnOrder, csv.columns]);
  // Filter out sort/filter entries that point to columns no longer in the CSV.
  const sortStack = useMemo(
    () => (prefs.sortStack || []).filter((s) => csv.columns.includes(s.id)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [prefs.sortStack, csv.columns]
  );
  const filters = useMemo(
    () => Object.fromEntries(
      Object.entries(prefs.filters || {}).filter(([k]) => csv.columns.includes(k) || k.startsWith("__"))
    ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [prefs.filters, csv.columns]
  );

  // Toast on parse complete. The message references row count and parse
  // time, so the effect re-fires when those change (i.e. on a fresh
  // CSV load) — that's the intended behavior, not a cascading render.
  useEffect(() => {
    if (csv.status === "ready") {
      toast.success(`Załadowano ${csv.rows.length.toLocaleString("pl-PL")} wierszy w ${(csv.parseTimeMs / 1000).toFixed(2)}s`, {
        duration: 2200,
      });
    }
  }, [csv.status, csv.rows.length, csv.parseTimeMs]);

  // Toast on error
  useEffect(() => {
    if (csv.status === "error" && csv.error) {
      toast.error(csv.error, { duration: 4000 });
    }
  }, [csv.status, csv.error]);

  // Wrap prefs writes for sort/filter in useTransition. The re-sort and
  // re-filter are the most expensive operations in the table; running
  // them as a transition lets the UI stay responsive (e.g. the cell you
  // clicked stays visually clickable) while the new order is computed.
  const [, startSortTransition] = useTransition();
  const [, startFilterTransition] = useTransition();

  // Effective column visibility — whatever the user last set in localStorage.
  const columnVisibility = prefs.columnVisibility || {};
  const setColumnOrder = (updater) =>
    setPrefs((p) => ({ ...p, columnOrder: typeof updater === "function" ? updater(p.columnOrder || csv.columns) : updater }));
  const setColumnVisibility = (updater) =>
    setPrefs((p) => ({ ...p, columnVisibility: typeof updater === "function" ? updater(p.columnVisibility || {}) : updater }));
  const setSortStack = (updater) =>
    startSortTransition(() =>
      setPrefs((p) => ({ ...p, sortStack: typeof updater === "function" ? updater(p.sortStack) : updater }))
    );
  const setFilters = (updater) =>
    startFilterTransition(() =>
      setPrefs((p) => ({ ...p, filters: typeof updater === "function" ? updater(p.filters) : updater }))
    );
  const setDensity = (d) => setPrefs((p) => ({ ...p, density: d }));
  const setTheme = (t) => setPrefs((p) => ({ ...p, theme: t }));

  // Global filter (across all visible cells) — debounced
  const [globalSearch, setGlobalSearch] = useState("");
  const debouncedGlobalRef = useRef();
  useEffect(() => {
    debouncedGlobalRef.current = debounce((v) => setGlobalFilter(v), 200);
    return () => debouncedGlobalRef.current?.cancel();
  }, []);
  const onGlobalSearchChange = (v) => {
    setGlobalSearch(v);
    debouncedGlobalRef.current?.(v);
  };

  // Memoized so the memoized Row in DataTable can rely on a stable
  // function reference across renders.
  const onRowClick = useCallback((_index, original) => {
    const first = Object.values(original)[0];
    if (first) {
      navigator.clipboard?.writeText(String(first));
      toast.success("Skopiowano pierwszą komórkę", { duration: 1000 });
    }
  }, []);

  // Synthetic filter columns (e.g. __brand) are computed from row data
  // and handled by pre-filtering rows before TanStack sees them.
  // Strip them from the TanStack-bound filters so it doesn't choke.
  const effectiveFilters = useMemo(
    () => Object.fromEntries(Object.entries(filters).filter(([k]) => !k.startsWith("__"))),
    [filters]
  );

  // Map row.id_unikalne -> brand label (computed once per dataset change).
  const brandByRow = useMemo(() => {
    const map = new Map();
    for (const row of csv.rows) {
      map.set(row.id_unikalne, classifyBrand(row));
    }
    return map;
  }, [csv.rows]);

  // Pre-filter rows by synthetic columns (currently only __brand) before
  // passing to DataTable. This keeps TanStack's filter machinery focused on
  // real CSV columns.
  const visibleRows = useMemo(() => {
    const brandFilter = filters.__brand;
    if (!brandFilter) return csv.rows;
    if (Array.isArray(brandFilter)) {
      if (brandFilter.length === 0) return csv.rows;
      return csv.rows.filter((r) => brandFilter.includes(brandByRow.get(r.id_unikalne)));
    }
    return csv.rows.filter((r) => brandByRow.get(r.id_unikalne) === brandFilter);
  }, [csv.rows, filters.__brand, brandByRow]);

  // Saved views = default views + user-defined views.
  const allViews = useMemo(
    () => [...DEFAULT_VIEWS, ...(prefs.savedViews || [])],
    [prefs.savedViews]
  );

  const activateView = useCallback((view) => {
    if (!view) {
      // Deactivate view but preserve the user's manual sort — only clear filters.
      setPrefs((p) => ({ ...p, activeView: null, filters: {} }));
      setGlobalFilter("");
      setGlobalSearch("");
      return;
    }
    // Merge view filters with brand-classification: __brand entries are
    // replaced with a filterFn that matches the derived brand label.
    const nextFilters = { ...(view.filters || {}) };
    setPrefs((p) => ({
      ...p,
      activeView: view.id,
      filters: nextFilters,
      // Apply view's own sort if it has one; otherwise keep the user's current sort.
      sortStack: view.sortStack || p.sortStack || [],
    }));
    setGlobalFilter("");
    setGlobalSearch("");
  }, []);

  const saveCurrentView = useCallback(
    (name) => {
      const id = `view-user-${Date.now()}`;
      setPrefs((p) => ({
        ...p,
        savedViews: [
          ...(p.savedViews || []),
          { id, name, userDefined: true, filters: p.filters || {}, columns: csv.columns },
        ],
        activeView: id,
      }));
      toast.success(`Zapisano widok: ${name}`, { duration: 1500 });
    },
    [csv.columns]
  );

  const deleteView = useCallback((viewId) => {
    setPrefs((p) => ({
      ...p,
      savedViews: (p.savedViews || []).filter((v) => v.id !== viewId),
      activeView: p.activeView === viewId ? null : p.activeView,
    }));
  }, []);

  // Toggle a value into the prefs.filters entry for a column.
  // Also clear the global text search — the combination of a chip filter
  // and a full-text search is rarely intentional and often leaves 0 results.
  const toggleQuickFilter = useCallback((columnId, value) => {
    setPrefs((p) => {
      const current = (p.filters || {})[columnId];
      const next = toggleFilterValue(current, value);
      const filters = { ...(p.filters || {}) };
      if (next === undefined) delete filters[columnId];
      else filters[columnId] = next;
      return { ...p, filters };
    });
    setGlobalFilter("");
    setGlobalSearch("");
  }, []);

  // Toolbar pinned — previously hid on scroll, removed because controls
  // (search, filters, view switcher) should stay reachable while exploring
  // a long table.

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      // ignore if typing in input
      const tag = e.target.tagName?.toLowerCase();
      const isInput = tag === "input" || tag === "textarea" || e.target.isContentEditable;
      const mod = e.metaKey || e.ctrlKey;

      if (mod && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen(true);
        return;
      }
      if (mod && e.key.toLowerCase() === "o") {
        e.preventDefault();
        document.querySelector('input[type="file"]')?.click();
        return;
      }
      if (mod && e.key.toLowerCase() === "f" && !isInput) {
        e.preventDefault();
        if (focusedColumn) {
          // focus the filter for the focused column
          const el = document.querySelector(`[data-col-filter="${focusedColumn}"] input`);
          el?.focus();
        }
        return;
      }
      if (e.key === "Escape") {
        if (paletteOpen) setPaletteOpen(false);
        else if (globalSearch) onGlobalSearchChange("");
        return;
      }
      if (isInput) return;
      if (e.key.toLowerCase() === "d") {
        e.preventDefault();
        setDensity(prefs.density === "compact" ? "comfortable" : "compact");
        toast.success(`Gęstość: ${prefs.density === "compact" ? "wygodna" : "kompaktowa"}`, { duration: 1000 });
        return;
      }
      if (e.key.toLowerCase() === "r" && !mod) {
        e.preventDefault();
        setFilters({});
        setSortStack([]);
        setGlobalFilter("");
        setGlobalSearch("");
        toast.success("Wyczyszczono filtry i sortowanie", { duration: 1000 });
        return;
      }
      // Arrow keys for row nav
      if (e.key === "ArrowDown" && csv.status === "ready") {
        e.preventDefault();
        setSelectedRowIndex((i) => Math.min(i + 1, csv.rows.length - 1));
      } else if (e.key === "ArrowUp" && csv.status === "ready") {
        e.preventDefault();
        setSelectedRowIndex((i) => Math.max(i - 1, 0));
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [prefs.density, paletteOpen, focusedColumn, globalSearch, csv.status, csv.rows.length]);

  // Expose methods for App-level controls (⌘K, Upload, etc.)
  useImperativeHandle(ref, () => ({
    openCommandPalette: () => setPaletteOpen(true),
    loadFile: (file) => csv.loadFile(file),
    cancelUpload: () => csv.cancel(),
    csvStatus: csv.status,
    csvProgress: csv.progress,
    fileMeta: csv.fileMeta,
  }), [csv]);

  // Persist last focused column. Done inline in the change handler so
  // we don't need a setState-in-effect.
  const onFocusedColumnChange = useCallback((colId) => {
    setFocusedColumn(colId);
    if (colId) setPrefs((p) => ({ ...p, lastFocusedColumn: colId }));
  }, []);

  // Per-column filters and sort are derived from prefs (cleaned of any
  // column references that no longer exist in the CSV). The setters
  // above still write to the underlying prefs; these derived values
  // automatically reflect the writes.
  // (effectiveFilters is declared earlier — it strips synthetic __ keys.)

  // Handle palette actions
  const handlePaletteAction = (item) => {
    if (item.id === "upload") {
      document.querySelector('input[type="file"]')?.click();
    } else if (item.id === "clear-filters") {
      setFilters({});
      setGlobalFilter("");
      setGlobalSearch("");
    } else if (item.id === "clear-sort") {
      setSortStack([]);
    } else if (item.id === "reset") {
      setFilters({});
      setSortStack([]);
      setColumnVisibility({});
      setGlobalFilter("");
      setGlobalSearch("");
    } else if (item.id === "density-compact") {
      setDensity("compact");
    } else if (item.id === "density-comfortable") {
      setDensity("comfortable");
    } else if (item.id.startsWith("theme-")) {
      setTheme(item.id.replace("theme-", ""));
    } else if (item.id.startsWith("col-")) {
      const colId = item.id.replace("col-", "");
      setColumnVisibility((prev) => ({ ...prev, [colId]: prev[colId] === false ? true : false }));
    } else if (item.id.startsWith("sort-")) {
      const colId = item.id.replace("sort-", "");
      setSortStack((prev) => {
        const existing = prev.find((s) => s.id === colId);
        if (existing) {
          if (existing.desc) return prev.filter((s) => s.id !== colId);
          return prev.map((s) => (s.id === colId ? { ...s, desc: true } : s));
        }
        return [...prev, { id: colId, desc: false }];
      });
    }
  };

  const activeFilterCount = useMemo(() => {
    let n = Object.keys(filters).length;
    if (globalFilter) n += 1;
    return n;
  }, [filters, globalFilter]);

  // Header component
  const Header = (
    <motion.header
      initial={false}
      animate={{ height: "auto", opacity: 1 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      className="sticky top-0 z-40 border-b bg-card/80 backdrop-blur-md overflow-hidden"
    >
      <div className="flex flex-col gap-1.5 py-2 px-3 sm:px-4">
        {csv.status === "ready" && (
          <>
            <div className="flex items-center gap-2 sm:gap-3 h-8">
              <div className="relative flex-1 max-w-md min-w-0">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/50" />
                <Input
                  value={globalSearch}
                  onChange={(e) => onGlobalSearchChange(e.target.value)}
                  placeholder="Szukaj we wszystkich kolumnach…"
                  className="h-8 pl-8 pr-7 text-sm"
                />
                {globalSearch && (
                  <button
                    onClick={() => onGlobalSearchChange("")}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-foreground"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              <ViewSwitcher
                views={allViews}
                activeView={prefs.activeView}
                activeViewDef={allViews.find((v) => v.id === prefs.activeView)}
                currentFilters={prefs.filters}
                onActivate={activateView}
                onSave={saveCurrentView}
                onDelete={deleteView}
              />

              <ColumnToggle
                columns={csv.columns}
                visibility={columnVisibility}
                onChange={setColumnVisibility}
                schema={csv.schema}
              />

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8 hidden sm:inline-flex"
                    aria-label="Gęstość"
                    title="Gęstość"
                  >
                    {prefs.density === "compact" ? <Rows3 className="h-4 w-4" /> : <Rows4 className="h-4 w-4" />}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>Gęstość</DropdownMenuLabel>
                  <DropdownMenuItem onClick={() => setDensity("compact")}>
                    <Rows3 className="h-4 w-4 mr-2" /> Kompaktowy {prefs.density === "compact" && "✓"}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setDensity("comfortable")}>
                    <Rows4 className="h-4 w-4 mr-2" /> Wygodny {prefs.density === "comfortable" && "✓"}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {/* Quick filter chips row — one-click toggles for tier/kraj/brand */}
            <div className="flex items-center gap-3 flex-wrap min-w-0">
              <QuickChips
                label="Kraj"
                columnId="kraj"
                rows={csv.rows}
                filter={filters.kraj}
                onToggle={(v) => toggleQuickFilter("kraj", v)}
              />
              <QuickChips
                label="Marka"
                columnId="__brand"
                rows={csv.rows}
                filter={filters.__brand}
                onToggle={(v) => toggleQuickFilter("__brand", v)}
                limit={5}
              />
              <QuickChips
                label="Rola"
                columnId="tier"
                rows={csv.rows}
                filter={filters.tier}
                onToggle={(v) => toggleQuickFilter("tier", v)}
              />
            </div>
          </>
        )}
      </div>
    </motion.header>
  );

  // Render
  return (
    <TooltipProvider delayDuration={200}>
      <div className="h-screen flex flex-col bg-background text-foreground transition-theme">
        <Toaster position="bottom-right" theme={prefs.theme === "system" ? "system" : prefs.theme} richColors closeButton />

        {Header}

        <main className="flex-1 min-h-0 relative">
          {csv.status === "idle" && (
            <EmptyState
              onFile={csv.loadFile}
              onLoadSample={tryLoadData}
              hasSample
              sampleSize={216000}
            />
          )}

          {csv.status === "loading" && (
            <LoadingState
              fileName={csv.fileMeta?.name}
              fileSize={csv.fileMeta?.size}
              progress={csv.progress}
              startedAt={csv.startedAt}
              onCancel={csv.cancel}
            />
          )}

          {csv.status === "error" && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md px-6">
                <p className="text-sm text-destructive mb-2">Błąd parsowania</p>
                <p className="text-xs text-muted-foreground mb-4">{csv.error}</p>
                <Button onClick={csv.reset} variant="outline" size="sm">
                  Spróbuj ponownie
                </Button>
              </div>
            </div>
          )}

          {csv.status === "ready" && (
            <>
              <DataTable
                columns={columnOrder}
                rows={visibleRows}
                schema={csv.schema}
                columnOrder={columnOrder}
                columnVisibility={columnVisibility}
                setColumnOrder={setColumnOrder}
                setColumnVisibility={setColumnVisibility}
                onFilteredCountChange={setFilteredCount}
                onColumnHide={(id) => {
                  toast(`Ukryto kolumnę: ${id}`, {
                    description: "Kliknij „Pokaż\", żeby przywrócić",
                    duration: 4000,
                    action: {
                      label: "Pokaż",
                      onClick: () => {
                        setColumnVisibility((prev) => {
                          const next = { ...prev };
                          delete next[id];
                          return next;
                        });
                      },
                    },
                  });
                }}
                sortStack={sortStack}
                setSortStack={setSortStack}
                filters={effectiveFilters}
                setFilters={setFilters}
                density={prefs.density}
                onFocusedColumnChange={onFocusedColumnChange}
                focusedColumn={focusedColumn}
                selectedRowIndex={selectedRowIndex}
                onRowClick={onRowClick}
                globalFilter={globalFilter}
              />
              <StatusBar
                totalRows={csv.rows.length}
                filteredRows={filteredCount}
                visibleColumns={csv.columns.filter((c) => columnVisibility[c] !== false).length}
                totalColumns={csv.columns.length}
                activeFilters={activeFilterCount}
                sortStack={sortStack}
                parseTimeMs={csv.parseTimeMs}
                density={prefs.density}
                fileMeta={csv.fileMeta}
              />
            </>
          )}
        </main>

        <CommandPalette
          open={paletteOpen}
          onOpenChange={setPaletteOpen}
          onAction={handlePaletteAction}
          context={{
            columns: csv.columns,
            visibility: columnVisibility,
            schema: csv.schema,
            density: prefs.density,
            theme: prefs.theme,
          }}
        />
      </div>
    </TooltipProvider>
  );
});
