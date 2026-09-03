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
  Eye,
  EyeOff,
  PanelLeft,
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
import { useUrlStatus } from "@/hooks/useUrlStatus";
import { useKeywordScan } from "@/hooks/useKeywordScan";
import { loadPrefs, savePrefs } from "@/lib/prefs";
import { useUndoRedo } from "@/lib/useUndoRedo";
import { debounce } from "@/lib/utils";
import { classifyBrand } from "@/lib/brand";
import { toggleFilterValue, bestLeadsPerCountry } from "@/lib/views";

import { EmptyState } from "./components/EmptyState";
import { DataTable } from "./components/DataTable";
import { ColumnToggle } from "./components/ColumnToggle";
import { StatusBar } from "./components/StatusBar";
import { CommandPalette } from "./components/CommandPalette";
import { LoadingState } from "./components/LoadingState";
import { BrandQuickBar } from "./components/BrandQuickBar";
import { ActiveFilterChips } from "./components/ActiveFilterChips";
import { CollapsibleFilters } from "./components/CollapsibleFilters";
import { CountryPills } from "./components/CountryPills";

import { getActiveDatasetInfo, getCustomDataset, clearCustomDataset, saveSnapshot, saveMasterCache, getMasterCache } from "@/lib/datasetStorage";

const SAMPLE_URL = "/sample.csv";
const SAMPLE_SIZE = 214000; // approximate
// Append ?v=Date.now() on every load to bust browser + vite proxy cache.
// The API also sends Cache-Control: no-cache (see api_server.py), but
// some browser/cache layers still ignore that for CSV MIME; the version
// query param is the belt-and-braces guarantee that after Marceli edits
// data/master.csv manually, the next reload picks up the new content.
const MASTER_URL = "/api/master.csv";
const withCacheBuster = (url) => `${url}?v=${Date.now()}`;

// Synthetic column id for the brand classifier (PowerMatic / Hawk / etc.).
// Lives in `filters` as `__brand`, but DataTable declares it as a real
// column so TanStack can run its filter pipeline. NEVER put it in
// columnOrder or columnVisibility — keeping it out of the display path is
// what makes it "filterable but invisible".
const SYNTHETIC_BRAND_COL = "__brand";

// Synthetic column id for the "best leads per country" view selector.
// Lives in `filters` as `__bestInCountry` with value "PL" | "CZ" | "SK" |
// "OTHER". DataTable uses it as a real column for TanStack filter matching.
// Rows are augmented once with their country code (or "OTHER" for anything
// not in {PL, CZ, SK}) so equality matching just works.
const SYNTHETIC_BEST_IN_COUNTRY_COL = "__bestInCountry";

// Country codes that get their own "Best" view. Anything else collapses
// into "OTHER" so the synth column has a small, finite value set.
const PRIMARY_BEST_COUNTRIES = new Set(["PL", "CZ", "SK"]);

// Per-row brand cache keyed on id. Module-scoped so it survives
// every RawTable mount/unmount cycle within a session: snapshot restore,
// custom-upload rehydrate, view switches, profile change — all hit the
// cache after the first pass. classifyBrand() is regex-only so even an
// unbounded cache is fine in practice (one ~50-char string per row).
// 25k rows × 50 chars ≈ 1.25 MB worst case — well under localStorage budget.
const brandCache = new Map();

/**
 * Classify a row's brand, consulting the module cache first. Falls back to
 * classifyBrand() on a miss and writes the result back so subsequent calls
 * for the same id are O(1).
 *
 * Rows without id (rare; mostly blanks in the upload phase) bypass
 * the cache — they're keyed by reference identity instead, so the worst
 * case is "classify twice in a session".
 */
function classifyRowCached(row) {
  if (!row) return "";
  const key = row.id;
  if (key == null || key === "") {
    return row[SYNTHETIC_BRAND_COL] ?? classifyBrand(row);
  }
  const cached = brandCache.get(key);
  if (cached !== undefined) return cached;
  const result = classifyBrand(row);
  brandCache.set(key, result);
  return result;
}

export const RawTable = forwardRef(function RawTable(_props, ref) {
  const csv = useCsv();
  const history = useUndoRedo(loadPrefs());
  const prefs = history.state;

  const setPrefs = useCallback((updater) => {
    history.set(typeof updater === "function" ? updater(history.state) : updater);
  }, [history]);

  // Automatic data pre-load after the gate:
  // 1. Check if the user previously uploaded a custom CSV (stored in IndexedDB).
  // 2. If not, restore the cached master.csv payload from IndexedDB — renders
  //    instantly on refresh without waiting for the network.
  // 3. Background: kick off a fresh /api/master.csv fetch so the cache stays
  //    current; the rows swap in once the new parse completes.
  // 4. If neither works, fall back to /sample.csv (bundled static copy).
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
        let hasCache = false;
        try {
          const activeInfo = await getActiveDatasetInfo();
          if (cancelled) {
            bootRef.current = 0;
            return;
          }
          if (activeInfo?.type === "custom") {
            const stored = await getCustomDataset();
            if (cancelled) {
              bootRef.current = 0;
              return;
            }
            if (stored && stored.rows && stored.rows.length > 0) {
              loadParsedDataRef.current(stored);
              bootRef.current = 2;
              return;
            }
          }
          // No active custom dataset — try the per-profile master cache so
          // the user sees their last-known rows on refresh while the
          // background fetch lands. Boot remains "pending" so the network
          // load still fires below.
          const masterCached = await getMasterCache();
          if (cancelled) {
            bootRef.current = 0;
            return;
          }
          if (masterCached && masterCached.rows && masterCached.rows.length > 0) {
            loadParsedDataRef.current(masterCached);
            hasCache = true;
          }
        } catch {
          // fall through to master.csv
        }
        if (cancelled) {
          bootRef.current = 0;
          return;
        }
        loadUrlRef.current(withCacheBuster(MASTER_URL), "master.csv", 0, { background: hasCache });
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
      if (bootRef.current === 1) {
        bootRef.current = 0;
      }
    };
  }, [csv.status]);

  // Persist master.csv loads to IndexedDB after a successful parse so the
  // next refresh restores instantly. Skip when the load came from the
  // bundled sample fallback (no point caching a static file we already have)
  // or from a custom user upload (those go through a separate save path in
  // useCsv.loadFile).
  useEffect(() => {
    if (csv.status !== "ready" || !csv.rows || csv.rows.length === 0) return;
    const name = csv.fileMeta?.name || "";
    if (!name.startsWith("master.csv")) return; // skip sample + custom
    saveMasterCache(undefined, {
      columns: csv.columns,
      rows: csv.rows,
      schema: csv.schema,
      parseTimeMs: csv.parseTimeMs,
      size: csv.fileMeta?.size || 0,
    });
    // Intentionally only fires on (status, name, row count) — the row
    // contents are deep so listing them would re-run on every cell change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [csv.status, csv.fileMeta?.name, csv.rows.length]);

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
  // Hydrate from persisted prefs so reload shows consistent input + filtered rows.
  const [globalFilter, setGlobalFilter] = useState(() => prefs.globalSearch || "");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [focusedColumn, setFocusedColumn] = useState(null);
  const [selectedRowIndex, setSelectedRowIndex] = useState(-1);
  const [toolbarVisible, setToolbarVisible] = useState(true);
  const [filteredCount, setFilteredCount] = useState(0);
  const [expandedRowId, setExpandedRowId] = useState(null);
  const [facetsOpen, setFacetsOpen] = useState(() => Boolean(prefs.facetsOpen));
  const maskDecydenci = prefs.maskDecydenci !== false;
  const setMaskDecydenci = useCallback((v) => {
    setPrefs((p) => {
      const current = p.maskDecydenci !== false;
      const next = typeof v === "function" ? v(current) : v;
      return { ...p, maskDecydenci: next };
    });
  }, [setPrefs]);

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
  // Pin id, kraj, nazwa to the front (id pierwsze jako identyfikator,
  // potem kraj dla grupowania, na końcu nazwa do szybkiego skanowania)
  // — nawet gdy użytkownik ma stary columnOrder w localStorage sprzed
  // tej reguły. Migracja na locie, bez setState-in-effect.
  const rawColumnOrder = prefs.columnOrder;
  const columnOrder = useMemo(() => {
    if (!csv.columns || csv.columns.length === 0) return rawColumnOrder || [];
    const base = rawColumnOrder && rawColumnOrder.length > 0 && rawColumnOrder.every((c) => csv.columns.includes(c))
      ? rawColumnOrder
      : csv.columns;
    const pinned = ["id", "kraj", "nazwa"].filter((c) => base.includes(c));
    const rest = base.filter((c) => !pinned.includes(c));
    return [...pinned, ...rest];
  }, [rawColumnOrder, csv.columns]);

  // Augment each row with the synthetic __brand classifier value once
  // per (rows) change. Results are cached in a module-scoped Map keyed by
  // id, so snapshot restores / custom-upload rehydrates / view
  // switches skip re-classification after the first pass. Memoized on
  // csv.rows so filter/sort/prefs changes don't re-allocate the array.
  //
  // Also stamps __bestInCountry per row. The "Best PL" / "Best CZ" /
  // "Best SK" / "Best Other" views work by setting a simple equality
  // filter on this column: rows that are in the top-N for their country
  // get their country code stamped here; everyone else gets "". This
  // keeps the filter shape uniform with __brand (no custom filterFn
  // needed) and makes the saved view definition trivially serializable.
  const rowsWithBrand = useMemo(() => {
    if (!csv.rows || csv.rows.length === 0) return csv.rows;
    const topByCountry = {
      PL: new Set(bestLeadsPerCountry(csv.rows, "PL", 25).map((r) => r.id)),
      CZ: new Set(bestLeadsPerCountry(csv.rows, "CZ", 25).map((r) => r.id)),
      SK: new Set(bestLeadsPerCountry(csv.rows, "SK", 25).map((r) => r.id)),
      OTHER: new Set(bestLeadsPerCountry(csv.rows, "OTHER", 25).map((r) => r.id)),
    };
    return csv.rows.map((r) => {
      if (r && r[SYNTHETIC_BRAND_COL] !== undefined && r[SYNTHETIC_BEST_IN_COUNTRY_COL] !== undefined) {
        return r;
      }
      const k = String(r?.kraj || "").toUpperCase();
      const bucket = k ? (PRIMARY_BEST_COUNTRIES.has(k) ? k : "OTHER") : "";
      const bestBucket = bucket && topByCountry[bucket]?.has(r?.id) ? bucket : "";
      return {
        ...r,
        [SYNTHETIC_BRAND_COL]: classifyRowCached(r),
        [SYNTHETIC_BEST_IN_COUNTRY_COL]: bestBucket,
      };
    });
  }, [csv.rows]);

  // Columns the DataTable declares — csv.columns plus the synthetic
  // __brand and __bestInCountry columns. The synthetic entries are what
  // let saved views (which store filters like { __brand: "PowerMatic" }
  // or { __bestInCountry: "PL" }) actually narrow the table.
  const tableColumnsList = useMemo(
    () =>
      csv.columns.length > 0
        ? [...csv.columns, SYNTHETIC_BRAND_COL, SYNTHETIC_BEST_IN_COUNTRY_COL]
        : csv.columns,
    [csv.columns]
  );
  // Filter out sort/filter entries that point to columns no longer in the CSV.
  const sortStack = useMemo(
    () => {
      if (!csv.columns || csv.columns.length === 0) return prefs.sortStack || [];
      return (prefs.sortStack || []).filter((s) => csv.columns.includes(s.id));
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [prefs.sortStack, csv.columns]
  );
  // Keep `__brand` and `__bestInCountry` filter entries (synthetic
  // columns) alongside real CSV columns. The CSV-column sanitizer stays
  // for everything else so stale filters don't sneak through after a
  // schema change.
  const filters = useMemo(
    () => {
      if (!csv.columns || csv.columns.length === 0) return prefs.filters || {};
      return Object.fromEntries(
        Object.entries(prefs.filters || {}).filter(
          ([k]) =>
            k === SYNTHETIC_BRAND_COL ||
            k === SYNTHETIC_BEST_IN_COUNTRY_COL ||
            csv.columns.includes(k)
        )
      );
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [prefs.filters, csv.columns]
  );

  // Active country ISO code (PL/CZ/...) or null when "Wszystkie" is selected.
  // Driven by the CountryPills bar above the table. The `filters.kraj` value
  // is still the single source of truth so it composes with other code paths
  // (e.g. saved prefs / URL state / bulk resets), but the pill bar is the
  // canonical UI for changing it.
  const activeCountryIso = useMemo(() => {
    const k = filters?.kraj;
    if (typeof k === "string" && k.trim()) return k.trim().toUpperCase();
    if (Array.isArray(k) && k.length > 0) return String(k[0]).trim().toUpperCase();
    return null;
  }, [filters?.kraj]);

  // Translate ISO → directory name for the URL/keyword hooks (they expect
  // the Polish folder name OR an ISO code, but historically used the name).
  // "Polska" stays the historical default for empty/legacy filter state.
  const activeCountry = useMemo(() => {
    if (!activeCountryIso) return null;
    const ISO_TO_NAME = {
      PL: "Polska", CZ: "Czechy", SK: "Słowacja", SI: "Słowenia", HR: "Chorwacja",
      BG: "Bułgaria", RO: "Rumunia", MD: "Mołdawia", RS: "Serbia",
      LT: "Litwa", LV: "Łotwa", EE: "Estonia", FR: "Francja",
    };
    return ISO_TO_NAME[activeCountryIso] || activeCountryIso;
  }, [activeCountryIso]);

  const { byId: urlStatusById } = useUrlStatus(activeCountry);
  const { byId: keywordById } = useKeywordScan(activeCountry);

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
  const [pageIndex, setPageIndex] = useState(() => (typeof prefs.pageIndex === "number" ? prefs.pageIndex : 0));
  const pageSize = typeof prefs.pageSize === "number" ? prefs.pageSize : 100;
  const pagination = useMemo(() => ({
    pageIndex: typeof pageIndex === "number" ? pageIndex : 0,
    pageSize: typeof pageSize === "number" ? pageSize : 100,
  }), [pageIndex, pageSize]);

  const onPaginationChange = useCallback((updater) => {
    setPageIndex((old) => {
      const current = typeof old === "number" ? old : 0;
      const next = typeof updater === "function" ? updater({ pageIndex: current, pageSize }) : updater;
      const nextIndex = typeof next === "number" ? next : (typeof next?.pageIndex === "number" ? next.pageIndex : 0);
      setPrefs((p) => ({ ...p, pageIndex: nextIndex }));
      return nextIndex;
    });
  }, [pageSize, setPrefs]);

  const onPageChange = useCallback((newPageIndex) => {
    const idx = typeof newPageIndex === "number" ? newPageIndex : 0;
    setPageIndex(idx);
    setPrefs((p) => ({ ...p, pageIndex: idx }));
  }, [setPrefs]);

  const onPageSizeChange = useCallback((newSize) => {
    const size = typeof newSize === "number" ? newSize : 0;
    setPageIndex(0);
    setPrefs((p) => ({ ...p, pageSize: size, pageIndex: 0 }));
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

  // When a country pill is clicked: update the underlying `kraj` filter.
  // Passing null clears the filter (CountryPills "Wszystkie" button).
  // We go through the same setFilters path so the change persists in
  // prefs and composes with reset / saved state.
  const handleCountrySelect = useCallback(
    (iso) => {
      setFilters((prev) => {
        const next = { ...prev };
        if (iso == null) {
          delete next.kraj;
        } else {
          next.kraj = iso;
        }
        return next;
      });
      setPageIndex(0);
    },
    [setFilters]
  );

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

  // Expose methods for App-level controls (command palette, Upload, etc.)
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
    },
    applyView: (view) => {
      if (!view || !view.filters) return;
      // Apply filters; if the view lists columns, switch column visibility too.
      // Sort is intentionally not touched — saved views are filter+column views.
      setPrefs((p) => ({
        ...p,
        filters: { ...view.filters },
        columnVisibility:
          Array.isArray(view.columns) && view.columns.length
            ? Object.fromEntries(csv.columns.map((c) => [c.id, view.columns.includes(c.id)]))
            : p.columnVisibility,
        activeView: view.id || null,
      }));
      // Make sure we're on the table tab (paranoia — caller is App).
      setPaletteOpen(false);
    },
  }), [csv, prefs, setPrefs]);

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
      // Reset both states atomically so the search input and the table
      // never desync (the input binds to globalSearch; the table binds
      // to globalFilter).
      setGlobalSearch("");
      setGlobalFilter("");
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
      setGlobalSearch("");
      setGlobalFilter("");
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
            <div className="relative flex-1 min-w-0 max-w-md">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/50 pointer-events-none" />
              <Input
                value={globalSearch}
                onChange={(e) => onGlobalSearchChange(e.target.value)}
                placeholder="Szukaj we wszystkich kolumnach…"
                className="h-10 sm:h-8 pl-9 pr-9 text-sm"
              />
              {globalSearch && (
                <button
                  onClick={() => onGlobalSearchChange("")}
                  className="absolute right-1 top-1/2 -translate-y-1/2 inline-flex h-9 w-9 sm:h-7 sm:w-7 items-center justify-center rounded-md text-muted-foreground/50 hover:text-foreground hover:bg-muted/60 transition-colors"
                  aria-label="Wyczyść wyszukiwanie"
                >
                  <X className="h-4 w-4 sm:h-3.5 sm:w-3.5" />
                </button>
              )}
            </div>

            <ColumnToggle
              columns={csv.columns}
              visibility={columnVisibility}
              onChange={setColumnVisibility}
              schema={csv.schema}
            />

            <Button
              variant={facetsOpen ? "secondary" : "outline"}
              size="sm"
              onClick={() => {
                const next = !facetsOpen;
                setFacetsOpen(next);
                setPrefs((p) => ({ ...p, facetsOpen: next }));
              }}
              className="hidden sm:inline-flex"
              title={facetsOpen ? "Ukryj panel fasad" : "Pokaż panel fasad"}
            >
              <PanelLeft className="h-3.5 w-3.5" />
              <span className="hidden lg:inline">Fasady</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const next = !maskDecydenci;
                setMaskDecydenci(next);
                toast.info(next ? "Włączono maskowanie decydentów (RODO)" : "Odkryto pełne nazwiska decydentów", { duration: 1200 });
              }}
              title={maskDecydenci ? "Odkryj pełne nazwiska decydentów" : "Maskuj nazwiska (RODO)"}
            >
              {maskDecydenci ? <Eye className="h-3.5 w-3.5 text-muted-foreground" /> : <EyeOff className="h-3.5 w-3.5 text-brand" />}
              <span className="hidden md:inline">{maskDecydenci ? "Maskuj" : "Odkryj"}</span>
            </Button>

            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon-sm"
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
                size="icon-sm"
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
                  size="icon-sm"
                  className="hidden sm:inline-flex"
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

      {csv.status === "ready" && (
        <div className="border-t border-border/40 bg-card/40 px-3 sm:px-4 py-1.5 flex flex-wrap items-center justify-between gap-2 overflow-x-auto touch-scroll-x">
          <BrandQuickBar
            rows={rowsWithBrand}
            activeBrand={effectiveFilters.__brand}
            onSelectBrand={(b) => {
              setFilters((prev) => {
                const next = { ...prev };
                if (!b) {
                  delete next.__brand;
                } else {
                  next.__brand = b;
                }
                return next;
              });
            }}
          />
        </div>
      )}
    </motion.header>
  );

  // Render
  return (
    <TooltipProvider delayDuration={200}>
      <div className="h-full flex flex-col bg-background text-foreground transition-theme overflow-hidden">
        <Toaster position="bottom-right" theme={prefs.theme === "system" ? "system" : prefs.theme} richColors closeButton />

        {Header}

        {csv.status === "ready" && csv.rows && csv.rows.length > 0 && (
          <CountryPills
            rows={csv.rows}
            activeIso={activeCountryIso}
            onSelect={handleCountrySelect}
          />
        )}

        {csv.status === "ready" && (
          <ActiveFilterChips
            filters={effectiveFilters}
            globalSearch={globalSearch}
            onRemoveFilter={(colId, valItem) => {
              setFilters((prev) => {
                const next = { ...prev };
                if (valItem !== undefined && Array.isArray(next[colId])) {
                  const filtered = next[colId].filter((v) => v !== valItem);
                  if (filtered.length === 0) delete next[colId];
                  else next[colId] = filtered;
                } else {
                  delete next[colId];
                }
                return next;
              });
            }}
            onClearGlobalSearch={() => onGlobalSearchChange("")}
            onResetAll={() => {
              setFilters({});
              setGlobalSearch("");
              setGlobalFilter("");
              setPageIndex(0);
              toast.success("Wyczyszczono wszystkie filtry", { duration: 1000 });
            }}
          />
        )}

        <main className="flex-1 min-h-0 relative flex flex-col">
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
              <div className="flex-1 min-h-0 relative flex overflow-hidden">
                {facetsOpen && (
                  <aside className="w-full sm:w-72 md:w-80 border-r bg-card/40 overflow-y-auto p-3 shrink-0 animate-in slide-in-from-left-2 duration-150 sm:block">
                    <CollapsibleFilters
                      rows={rowsWithBrand}
                      filters={effectiveFilters}
                      onToggle={(key, val) => {
                        setFilters((prev) => ({
                          ...prev,
                          [key]: toggleFilterValue(prev[key], val),
                        }));
                      }}
                      onToggleCollapse={() => {
                        setFacetsOpen(false);
                        setPrefs((p) => ({ ...p, facetsOpen: false }));
                      }}
                    />
                  </aside>
                )}

                <div className="flex-1 min-w-0 relative flex flex-col">
                  <div className="flex-1 min-h-0 relative">
                    <DataTable
                      columns={tableColumnsList}
                      rows={rowsWithBrand}
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
                      setPagination={onPaginationChange}
                      maskDecydenci={maskDecydenci}
                      expandedRowId={expandedRowId}
                      onToggleExpandRow={setExpandedRowId}
                      urlStatusById={urlStatusById}
                      keywordById={keywordById}
                    />
                  </div>
                </div>
              </div>
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
