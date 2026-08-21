import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast, Toaster } from "sonner";
import {
  Table as TableIcon,
  Search,
  X,
  Sun,
  Moon,
  Monitor,
  Rows3,
  Rows4,
  Keyboard,
  Command as CommandIcon,
  Plus,
  Minus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { TooltipProvider } from "@/components/ui/tooltip";

import { useCsv } from "@/hooks/useCsv";
import { loadPrefs, savePrefs } from "@/lib/prefs";
import { cn, debounce } from "@/lib/utils";

import { EmptyState } from "./components/EmptyState";
import { UploadButton } from "./components/UploadButton";
import { DataTable } from "./components/DataTable";
import { ColumnToggle } from "./components/ColumnToggle";
import { StatusBar } from "./components/StatusBar";
import { CommandPalette } from "./components/CommandPalette";
import { LoadingState } from "./components/LoadingState";

const SAMPLE_URL = "/sample.csv";
const SAMPLE_SIZE = 214000; // approximate

export function RawTable() {
  const csv = useCsv();
  const [prefs, setPrefs] = useState(() => loadPrefs());
  const [globalFilter, setGlobalFilter] = useState("");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
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
  useEffect(() => {
    if (csv.columns.length > 0) {
      setPrefs((p) => {
        const baseOrder =
          p.columnOrder && p.columnOrder.every((c) => csv.columns.includes(c))
            ? p.columnOrder
            : csv.columns;
        // Pin id_unikalne and nazwa_firmy to the front
        const pinned = ["id_unikalne", "nazwa_firmy"].filter((c) => baseOrder.includes(c));
        const rest = baseOrder.filter((c) => !pinned.includes(c));
        const newOrder = [...pinned, ...rest];
        return {
          ...p,
          columnOrder: newOrder,
          columnVisibility: p.columnVisibility ?? Object.fromEntries(csv.columns.map((c) => [c, true])),
          sortStack: p.sortStack.filter((s) => csv.columns.includes(s.id)),
          filters: Object.fromEntries(
            Object.entries(p.filters).filter(([k]) => csv.columns.includes(k))
          ),
        };
      });
    }
  }, [csv.columns.join(",")]);

  // Toast on parse complete
  useEffect(() => {
    if (csv.status === "ready") {
      toast.success(`Załadowano ${csv.rows.length.toLocaleString("pl-PL")} wierszy w ${(csv.parseTimeMs / 1000).toFixed(2)}s`, {
        duration: 2200,
      });
    }
  }, [csv.status]);

  // Toast on error
  useEffect(() => {
    if (csv.status === "error" && csv.error) {
      toast.error(csv.error, { duration: 4000 });
    }
  }, [csv.status, csv.error]);

  // Effective column order & visibility
  const columnOrder = prefs.columnOrder || csv.columns;
  const columnVisibility = prefs.columnVisibility || {};
  const setColumnOrder = (updater) =>
    setPrefs((p) => ({ ...p, columnOrder: typeof updater === "function" ? updater(p.columnOrder || csv.columns) : updater }));
  const setColumnVisibility = (updater) =>
    setPrefs((p) => ({ ...p, columnVisibility: typeof updater === "function" ? updater(p.columnVisibility || {}) : updater }));
  const setSortStack = (updater) =>
    setPrefs((p) => ({ ...p, sortStack: typeof updater === "function" ? updater(p.sortStack) : updater }));
  const setFilters = (updater) =>
    setPrefs((p) => ({ ...p, filters: typeof updater === "function" ? updater(p.filters) : updater }));
  const setDensity = (d) => setPrefs((p) => ({ ...p, density: d }));
  const setTheme = (t) => setPrefs((p) => ({ ...p, theme: t }));

  // Global filter (across all visible cells) — debounced
  const [globalSearch, setGlobalSearch] = useState("");
  const debouncedGlobalRef = useRef();
  useEffect(() => {
    debouncedGlobalRef.current = debounce((v) => setGlobalFilter(v), 200);
    return () => clearTimeout(debouncedGlobalRef.current?.timer);
  }, []);
  const onGlobalSearchChange = (v) => {
    setGlobalSearch(v);
    debouncedGlobalRef.current?.(v);
  };

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
        else if (shortcutsOpen) setShortcutsOpen(false);
        else if (globalSearch) onGlobalSearchChange("");
        return;
      }
      if (isInput) return;
      if (e.key === "?") {
        e.preventDefault();
        setShortcutsOpen(true);
        return;
      }
      if (e.key.toLowerCase() === "d") {
        e.preventDefault();
        setDensity(prefs.density === "compact" ? "comfortable" : "compact");
        toast.success(`Gęstość: ${prefs.density === "compact" ? "Comfortable" : "Compact"}`, { duration: 1000 });
        return;
      }
      if (e.key.toLowerCase() === "r" && !mod) {
        e.preventDefault();
        setFilters({});
        setSortStack([]);
        setGlobalFilter("");
        setGlobalSearch("");
        toast.success("Filtry i sort wyczyszczone", { duration: 1000 });
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
  }, [prefs.density, paletteOpen, shortcutsOpen, focusedColumn, globalSearch, csv.status, csv.rows.length]);

  // Persist last focused column
  useEffect(() => {
    if (focusedColumn) setPrefs((p) => ({ ...p, lastFocusedColumn: focusedColumn }));
  }, [focusedColumn]);

  // Per-column filters are passed to DataTable as-is. Global filter is
  // handled by TanStack's separate `globalFilter` state (line 97 in DataTable),
  // so it must NOT be mixed in here — the old `__global` override wiped out
  // per-column filters whenever the user typed in the global search box.
  const effectiveFilters = prefs.filters;

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
    let n = Object.keys(prefs.filters).length;
    if (globalFilter) n += 1;
    return n;
  }, [prefs.filters, globalFilter]);

  // Header component
  const Header = (
    <motion.header
      initial={false}
      animate={{ height: toolbarVisible ? "auto" : 0, opacity: toolbarVisible ? 1 : 0 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      className="sticky top-0 z-40 border-b bg-card/80 backdrop-blur-md overflow-hidden"
    >
      <div className="h-14 flex items-center gap-2 sm:gap-3 px-3 sm:px-4">
        <div className="flex items-center gap-2 shrink-0">
          <div className="h-7 w-7 rounded-md bg-primary flex items-center justify-center">
            <TableIcon className="h-3.5 w-3.5 text-primary-foreground" />
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-semibold leading-none">czat-table</p>
            <p className="text-[10px] text-muted-foreground leading-none mt-0.5">BILLSzuka katalog</p>
          </div>
        </div>

        <Separator orientation="vertical" className="h-6 hidden sm:block" />

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

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-1.5 hidden sm:flex">
                  {prefs.density === "compact" ? <Rows3 className="h-4 w-4" /> : <Rows4 className="h-4 w-4" />}
                  <span className="hidden md:inline capitalize">{prefs.density}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Gęstość</DropdownMenuLabel>
                <DropdownMenuItem onClick={() => setDensity("compact")}>
                  <Rows3 className="h-4 w-4 mr-2" /> Compact {prefs.density === "compact" && "✓"}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setDensity("comfortable")}>
                  <Rows4 className="h-4 w-4 mr-2" /> Comfortable {prefs.density === "comfortable" && "✓"}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon" className="h-8 w-8">
                  {prefs.theme === "light" && <Sun className="h-4 w-4" />}
                  {prefs.theme === "dark" && <Moon className="h-4 w-4" />}
                  {prefs.theme === "system" && <Monitor className="h-4 w-4" />}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Motyw</DropdownMenuLabel>
                <DropdownMenuItem onClick={() => setTheme("light")}>
                  <Sun className="h-4 w-4 mr-2" /> Light {prefs.theme === "light" && "✓"}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("dark")}>
                  <Moon className="h-4 w-4 mr-2" /> Dark {prefs.theme === "dark" && "✓"}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("system")}>
                  <Monitor className="h-4 w-4 mr-2" /> System {prefs.theme === "system" && "✓"}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => setShortcutsOpen(true)}
              title="Skróty klawiszowe (?)"
            >
              <Keyboard className="h-4 w-4" />
            </Button>
          </>
        )}

        {csv.status === "loading" ? (
          <UploadButton
            onFile={csv.loadFile}
            status={csv.status}
            progress={csv.progress}
            fileMeta={csv.fileMeta}
            onCancel={csv.cancel}
            compact
          />
        ) : csv.status === "ready" ? (
          <UploadButton
            onFile={csv.loadFile}
            status={csv.status}
            progress={csv.progress}
            fileMeta={csv.fileMeta}
            onCancel={csv.cancel}
            compact
          />
        ) : (
          <UploadButton
            onFile={csv.loadFile}
            status={csv.status}
            progress={csv.progress}
            fileMeta={csv.fileMeta}
            onCancel={csv.cancel}
          />
        )}

        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => setPaletteOpen(true)}
          title="Paleta komend (⌘K)"
        >
          <CommandIcon className="h-4 w-4" />
        </Button>
      </div>
    </motion.header>
  );

  // Render
  return (
    <TooltipProvider delayDuration={200}>
      <div className="h-screen flex flex-col bg-background text-foreground">
        <Toaster position="bottom-right" theme={prefs.theme === "system" ? "system" : prefs.theme} richColors closeButton />

        {Header}

        <main className="flex-1 min-h-0 relative">
          {csv.status === "idle" && (
            <EmptyState
              onFile={csv.loadFile}
              onLoadSample={() => csv.loadUrl(SAMPLE_URL, "master.csv (sample)")}
              hasSample
              sampleSize={SAMPLE_SIZE}
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
                    description: "Kliknij przycisk, żeby przywrócić",
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
                sortStack={prefs.sortStack}
                setSortStack={setSortStack}
                filters={effectiveFilters}
                setFilters={setFilters}
                density={prefs.density}
                onFocusedColumnChange={setFocusedColumn}
                focusedColumn={focusedColumn}
                selectedRowIndex={selectedRowIndex}
                onRowClick={(_, original) => {
                  // copy first cell on row click
                  const first = Object.values(original)[0];
                  if (first) {
                    navigator.clipboard?.writeText(String(first));
                    toast.success("Skopiowano pierwszą komórkę", { duration: 1000 });
                  }
                }}
                globalFilter={globalFilter}
              />
              <StatusBar
                totalRows={csv.rows.length}
                filteredRows={filteredCount}
                visibleColumns={csv.columns.filter((c) => columnVisibility[c] !== false).length}
                totalColumns={csv.columns.length}
                activeFilters={activeFilterCount}
                sortStack={prefs.sortStack}
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

        <Dialog open={shortcutsOpen} onOpenChange={setShortcutsOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Skróty klawiszowe</DialogTitle>
              <DialogDescription>Szybsze nawigowanie po tabeli</DialogDescription>
            </DialogHeader>
            <div className="space-y-3 text-sm">
              {[
                ["⌘K", "Otwórz paletę komend"],
                ["⌘O", "Upload CSV"],
                ["⌘F", "Focus na filtr kolumny"],
                ["D", "Zmień gęstość"],
                ["R", "Wyczyść filtry i sort"],
                ["↑ ↓", "Nawigacja po wierszach"],
                ["Esc", "Wyczyść focus / zamknij"],
                ["?", "Pokaż te skróty"],
              ].map(([k, v]) => (
                <div key={k} className="flex items-center justify-between">
                  <span className="text-muted-foreground">{v}</span>
                  <kbd className="px-2 py-0.5 rounded bg-muted text-xs font-mono">{k}</kbd>
                </div>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
