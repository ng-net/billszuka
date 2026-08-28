import { useState, useEffect, useMemo, useCallback, useRef, useTransition, forwardRef, useImperativeHandle } from "react";
import { motion } from "framer-motion";
import { toast, Toaster } from "sonner";
import {
  Search,
  X,
  Rows3,
  Rows4,
  Undo2,
  Redo2,
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
import { useUndoRedo } from "@/lib/useUndoRedo";
import { debounce } from "@/lib/utils";

import { EmptyState } from "./components/EmptyState";
import { DataTable } from "./components/DataTable";
import { ColumnToggle } from "./components/ColumnToggle";
import { StatusBar } from "./components/StatusBar";
import { CommandPalette } from "./components/CommandPalette";
import { LoadingState } from "./components/LoadingState";

import { getActiveDatasetInfo, getCustomDataset, clearCustomDataset, saveSnapshot } from "@/lib/datasetStorage";

const SAMPLE_URL = "/sample.csv";
const SAMPLE_SIZE = 214000; // approximate
// Append ?v=Date.now() on every load to bust browser + vite proxy cache.
// The API also sends Cache-Control: no-cache (see api_server.py), but
// some browser/cache layers still ignore that for CSV MIME; the version
// query param is the belt-and-braces guarantee that after Marceli edits
// data/master.csv manually, the next reload picks up the new content.
const MASTER_URL = "/api/master.csv";
const withCacheBuster = (url) => `${url}?v=${Date.now()}`;

export const RawTable = forwardRef(function RawTable(_props, ref) {
  const csv = useCsv();
  const history = useUndoRedo(loadPrefs());
  const prefs = history.state;

  const setPrefs = useCallback((updater) => {
    history.set(typeof updater === "function" ? updater(history.state) : updater);
  }, [history]);

  // Automatic data pre-load after the gate:
  // 1. Check if the user previously uploaded a custom CSV (stored in IndexedDB).
  // 2. If not, try the full master.csv from backend; if unreachable, fall back to sample;
  // 3. If that also fails, leave the EmptyState's manual button for the user.
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
        loadUrlRef.current(SAMPLE_URL, "master.csv (sample)", SAMPLE_SIZE);
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
  // and directly loads master.csv from the backend.
  const tryLoadData = useCallback(async () => {
    await clearCustomDataset();
    bootRef.current = 2;
    csv.loadUrl(withCacheBuster(MASTER_URL), "master.csv", 0);
  }, [csv]);

  const onCsvStateChange = _props.onCsvStateChange;

  useEffect(() => {
    onCsvStateChange?.({
      status: csv.status,
      progress: csv.progress,
      fileMeta: csv.fileMeta,
      activeDataset: csv.fileMeta?.name || "master.csv",
      cancel: csv.cancel,
      loadFile: csv.loadFile,
    });
  }, [
    onCsvStateChange,
    csv.status,
    csv.progress,
    csv.fileMeta,
    csv.cancel,
    csv.loadFile,
  ]);
  const [globalFilter, setGlobalFilter] = useState("");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [focusedColumn, setFocusedColumn] = useState(null);
  const [selectedRowIndex, setSelectedRowIndex] = useState(-1);
  const [toolbarVisible, setToolbarVisible] = useState(true);
  const [filteredCount, setFilteredCount] = useState(0);
  const lastScrollY = useRef(0);

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

  // Persist prefs (debounced)
  useEffect(() => {
    const t = setTimeout(() => savePrefs(prefs), 300);
    return () => clearTimeout(t);
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
      Object.entries(prefs.filters || {}).filter(([k]) => csv.columns.includes(k))
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
  const [pageIndex, setPageIndex] = useState(() => prefs.pageIndex ?? 0);
  const pageSize = prefs.pageSize ?? 0;
  const pagination = useMemo(() => ({
    pageIndex,
    pageSize,
  }), [pageIndex, pageSize]);

  const onPageChange = useCallback((newPageIndex) => {
    setPageIndex(newPageIndex);
    setPrefs((p) => ({ ...p, pageIndex: newPageIndex }));
  }, [setPrefs]);

  const onPageSizeChange = useCallback((newSize) => {
    setPageIndex(0);
    setPrefs((p) => ({ ...p, pageSize: newSize, pageIndex: 0 }));
  }, [setPrefs]);

  const setColumnOrder = useCallback((updater) =>
    setPrefs((p) => ({ ...p, columnOrder: typeof updater === "function" ? updater(p.columnOrder || csv.columns) : updater })), [setPrefs, csv.columns]);
  const setColumnVisibility = useCallback((updater) =>
    setPrefs((p) => ({ ...p, columnVisibility: typeof updater === "function" ? updater(p.columnVisibility || {}) : updater })), [setPrefs]);
  const setSortStack = useCallback((updater) => {
    setPageIndex(0);
    startSortTransition(() =>
      setPrefs((p) => ({ ...p, sortStack: typeof updater === "function" ? updater(p.sortStack) : updater, pageIndex: 0 }))
    );
  }, [setPrefs]);
  const setFilters = useCallback((updater) => {
    setPageIndex(0);
    startFilterTransition(() =>
      setPrefs((p) => ({ ...p, filters: typeof updater === "function" ? updater(p.filters) : updater, pageIndex: 0 }))
    );
  }, [setPrefs]);
  const setDensity = useCallback((d) => setPrefs((p) => ({ ...p, density: d })), [setPrefs]);
  const setTheme = useCallback((t) => setPrefs((p) => ({ ...p, theme: t })), [setPrefs]);

  // Global filter (across all visible cells) — debounced
  const [globalSearch, setGlobalSearch] = useState(() => prefs.globalSearch || "");
  const debouncedGlobalRef = useRef();
  useEffect(() => {
    debouncedGlobalRef.current = debounce((v) => {
      setPageIndex(0);
      setGlobalFilter(v);
      setPrefs((p) => ({ ...p, globalSearch: v, pageIndex: 0 }));
    }, 200);
    return () => debouncedGlobalRef.current?.cancel();
  }, [setPrefs]);
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

  // Toolbar hide-on-scroll
  useEffect(() => {
    if (csv.status !== "ready") return;
    const onScroll = () => {
      const y = window.scrollY;
      const delta = y - lastScrollY.current;
      if (delta > 8 && y > 100) setToolbarVisible(false);
      else if (delta < -4) setToolbarVisible(true);
      lastScrollY.current = y;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [csv.status]);

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
  }, [prefs.density, paletteOpen, focusedColumn, globalSearch, csv.status, csv.rows.length, setDensity, setFilters, setSortStack]);

  // Expose methods for App-level controls (⌘K, Upload, etc.)
  useImperativeHandle(ref, () => ({
    openCommandPalette: () => setPaletteOpen(true),
    loadFile: (file) => csv.loadFile(file),
    cancelUpload: () => csv.cancel(),
    csvStatus: csv.status,
    csvProgress: csv.progress,
    fileMeta: csv.fileMeta,
    saveSnapshot: async (profileId) => {
      await saveSnapshot(profileId, {
         name: csv.fileMeta?.name || "master.csv",
         size: csv.fileMeta?.size || 0,
         columns: csv.columns,
         rows: csv.rows,
         schema: csv.schema,
         prefs: prefs,
         parseTimeMs: csv.parseTimeMs
      });
      toast.success("Zapisano zrzut sesji", { duration: 2000 });
    }
  }), [csv, prefs]);

  // Persist last focused column. Done inline in the change handler so
  // we don't need a setState-in-effect.
  const onFocusedColumnChange = useCallback((colId) => {
    setFocusedColumn(colId);
    if (colId) setPrefs((p) => ({ ...p, lastFocusedColumn: colId }));
  }, [setPrefs]);

  // Per-column filters and sort are derived from prefs (cleaned of any
  // column references that no longer exist in the CSV). The setters
  // above still write to the underlying prefs; these derived values
  // automatically reflect the writes.
  const effectiveFilters = filters;

  // Handle palette actions
  const handlePaletteAction = (item) => {
    if (item.id === "upload") {
      document.querySelector('input[type="file"]')?.click();
    } else if (item.id === "clear-filters") {
      setFilters({});
      setGlobalFilter("");
      setGlobalSearch("");
      setPageIndex(0);
      toast.success("Wyczyszczono wszystkie filtry", { duration: 1200 });
    } else if (item.id === "clear-sort") {
      setSortStack([]);
      setPageIndex(0);
      toast.success("Wyczyszczono sortowanie", { duration: 1200 });
    } else if (item.id === "reset") {
      setFilters({});
      setSortStack([]);
      setColumnVisibility({});
      setGlobalFilter("");
      setGlobalSearch("");
      setPageIndex(0);
      toast.success("Zresetowano cały widok (filtry, kolumny i sortowanie)", { duration: 1500 });
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
    let n = 0;
    for (const [, v] of Object.entries(filters || {})) {
      if (v == null || v === "") continue;
      if (Array.isArray(v)) {
        if (v.length > 0) n += 1;
      } else if (typeof v === "object") {
        if (v.min != null || v.max != null || v.from != null || v.to != null) n += 1;
      } else {
        n += 1;
      }
    }
    if (globalFilter && String(globalFilter).trim()) n += 1;
    return n;
  }, [filters, globalFilter]);

  // Header component
  const Header = (
    <motion.header
      initial={false}
      animate={{ height: toolbarVisible ? "auto" : 0, opacity: toolbarVisible ? 1 : 0 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      className="sticky top-0 z-40 border-b bg-card/80 backdrop-blur-md overflow-hidden"
    >
      <div className="h-14 flex items-center gap-2 sm:gap-3 px-3 sm:px-4">
        {csv.status === "ready" && (
          <>
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

            <ColumnToggle
              columns={csv.columns}
              visibility={columnVisibility}
              onChange={setColumnVisibility}
              schema={csv.schema}
            />

            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                disabled={!history.canUndo}
                onClick={() => {
                  history.undo();
                  toast.info("Cofnięto zmianę", { duration: 1000 });
                }}
                aria-label="Cofnij (Cmd+Z)"
                title="Cofnij (Cmd+Z)"
              >
                <Undo2 className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                disabled={!history.canRedo}
                onClick={() => {
                  history.redo();
                  toast.info("Przywrócono zmianę", { duration: 1000 });
                }}
                aria-label="Ponów (Cmd+Shift+Z)"
                title="Ponów (Cmd+Shift+Z)"
              >
                <Redo2 className="h-4 w-4" />
              </Button>
            </div>

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
              sampleSize={0}
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
                rows={csv.rows}
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
                pagination={pagination}
                setPagination={onPageChange}
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
                pagination={pagination}
                onPageChange={onPageChange}
                onPageSizeChange={onPageSizeChange}
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
