import { useCallback, useEffect, useRef, useState, lazy, Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Table as TableIcon,
  BarChart3,
  KeyRound,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Command as CommandIcon,
  BookOpen,
  Keyboard,
  Sun,
  Moon,
  Monitor,
} from "lucide-react";
import { fetchSettings } from "@/lib/secretsApi";
import { loadPrefs, savePrefs } from "@/lib/prefs";
import { GeminiDrawer } from "@/components/GeminiDrawer";
import { KnowledgeDrawer } from "@/components/KnowledgeDrawer";
import { SettingsDrawer } from "@/components/SettingsDrawer";
import { UploadButton } from "@/raw-table/components/UploadButton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

/**
 * App — BILLSzuka Dashboard Hub shell.
 *
 * 3-pane layout:
 *   - Header (sticky): product name, Katalog/Analityka tabs, Skróty, Motyw,
 *     HealthBadge (fallback chain + #kluczy), Baza wiedzy, Command palette (⌘K),
 *     Settings gear, Upload button.
 *   - Active view (Katalog = RawTable CSV viewer, Analityka = dashboards).
 *   - Gemini FAB (chat panel, bottom-right).
 *
 * Views are lazy-loaded so the initial bundle stays small and the user
 * only pays for the view they actually open. Each view is its own chunk
 * (Recharts in AnalyticsView is ~100KB and only loads on the Analityka tab).
 */

const TableView = lazy(() => import("@/views/TableView").then((m) => ({ default: m.TableView })));
const AnalyticsView = lazy(() => import("@/views/AnalyticsView").then((m) => ({ default: m.AnalyticsView })));

const TABS = [
  { id: "table", label: "Katalog", icon: TableIcon, View: TableView },
  { id: "analytics", label: "Analityka", icon: BarChart3, View: AnalyticsView },
];

export default function App() {
  const [activeTab, setActiveTab] = useState(() => loadPrefs().activeTab || "table");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [knowledgeOpen, setKnowledgeOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [theme, setTheme] = useState(() => loadPrefs().theme || "system");
  const [vault, setVault] = useState(null); // redacted vault snapshot
  const [vaultError, setVaultError] = useState(null);
  const [csvState, setCsvState] = useState({
    status: "idle",
    progress: { bytesParsed: 0, rowsParsed: 0 },
    fileMeta: null,
    activeDataset: "master.csv",
    cancel: null,
    loadFile: null,
  });

  const handleTabChange = useCallback((tabId) => {
    setActiveTab(tabId);
    const prefs = loadPrefs();
    savePrefs({ ...prefs, activeTab: tabId });
  }, []);

  // Apply theme to <html> and react to system changes
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
    apply(theme);
    if (theme === "system") {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      const cb = () => apply("system");
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    }
  }, [theme]);

  const handleThemeChange = useCallback((t) => {
    setTheme(t);
    const prefs = loadPrefs();
    savePrefs({ ...prefs, theme: t });
  }, []);

  // Global shortcut listeners (? for help)
  useEffect(() => {
    const handler = (e) => {
      const tag = e.target.tagName?.toLowerCase();
      const isInput = tag === "input" || tag === "textarea" || e.target.isContentEditable;
      if (e.key === "?" && !isInput) {
        e.preventDefault();
        setShortcutsOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Ref to the active TableView, used to trigger its command palette
  // (the palette lives inside RawTable because it needs table context).
  const tableRef = useRef(null);
  // IDs of knowledge files the user has selected to attach to chat.
  // Lifted here so the GeminiDrawer FAB can include them in /api/chat
  // without needing to read state from the closed KnowledgeDrawer.
  const [knowledgeIds, setKnowledgeIds] = useState([]);

  // Fetch /api/settings once on mount so HealthBadge has an initial state.
  // No polling — the Settings drawer refreshes on its own when it opens
  // or after mutations. This avoids background traffic once data is loaded.
  useEffect(() => {
    let cancelled = false;
    const fetchOnce = async () => {
      try {
        const s = await fetchSettings();
        if (cancelled) return;
        setVault(s);
        setVaultError(null);
      } catch (e) {
        if (cancelled) return;
        setVaultError(e.message || String(e));
      }
    };
    fetchOnce();
    return () => {
      cancelled = true;
    };
  }, []);

  // Lift a snapshot from SettingsDrawer so the HealthBadge can stay in sync
  // without re-polling the API on a timer.
  const handleVaultChange = useCallback((s) => {
    setVault(s);
    setVaultError(null);
  }, []);

  return (
    <div className="flex h-dvh flex-col bg-background text-foreground">
      <header className="flex h-14 shrink-0 items-center justify-between gap-2 border-b bg-background/80 px-2 backdrop-blur supports-[backdrop-filter]:bg-background/60 sm:px-4">
        <div className="flex min-w-0 items-center gap-2 sm:gap-4">
          <div className="shrink-0 leading-tight">
            <div className="font-semibold tracking-tight">BILLSzuka</div>
            <div className="hidden text-[10px] text-muted-foreground sm:block">Katalog leadów B2B/B2C</div>
          </div>
          <nav className="flex items-center gap-1">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => handleTabChange(id)}
                aria-label={label}
                title={label}
                className={cn(
                  "inline-flex items-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium transition-colors sm:px-3",
                  activeTab === id
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
                )}
                aria-pressed={activeTab === id}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </nav>
        </div>
        <div className="flex shrink-0 items-center gap-1 sm:gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShortcutsOpen(true)}
            aria-label="Skróty klawiszowe"
            title="Skróty klawiszowe (?)"
            className="hidden sm:inline-flex"
          >
            <Keyboard className="h-4 w-4" />
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Motyw"
                title="Motyw"
              >
                {theme === "light" && <Sun className="h-4 w-4" />}
                {theme === "dark" && <Moon className="h-4 w-4" />}
                {theme === "system" && <Monitor className="h-4 w-4" />}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Motyw</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => handleThemeChange("light")}>
                <Sun className="h-4 w-4 mr-2" /> Jasny {theme === "light" && "✓"}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleThemeChange("dark")}>
                <Moon className="h-4 w-4 mr-2" /> Ciemny {theme === "dark" && "✓"}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleThemeChange("system")}>
                <Monitor className="h-4 w-4 mr-2" /> Systemowy {theme === "system" && "✓"}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <span className="hidden sm:contents">
            <HealthBadge vault={vault} error={vaultError} />
          </span>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setKnowledgeOpen(true)}
            aria-label="Baza wiedzy"
            title={`Baza wiedzy${knowledgeIds.length ? ` (${knowledgeIds.length} aktywnych)` : ""}`}
            className="relative"
          >
            <BookOpen className="h-4 w-4" />
            {knowledgeIds.length > 0 && (
              <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-background" />
            )}
          </Button>
          {activeTab === "table" && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => tableRef.current?.openCommandPalette()}
              aria-label="Polecenia (⌘K)"
              title="Polecenia (⌘K)"
            >
              <CommandIcon className="h-4 w-4" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSettingsOpen(true)}
            aria-label="Klucze API"
            title="Klucze API"
          >
            <KeyRound className="h-4 w-4" />
          </Button>
          <UploadButton
            onFile={(file) => {
              if (activeTab !== "table") handleTabChange("table");
              tableRef.current?.loadFile(file);
            }}
            status={csvState.status}
            progress={csvState.progress}
            fileMeta={csvState.fileMeta}
            onCancel={csvState.cancel}
            label="Upload"
            primary
          />
        </div>
      </header>

      <main className="relative flex-1 overflow-hidden">
        <Suspense
          fallback={
            <div className="absolute inset-0 flex items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Ładowanie…</span>
            </div>
          }
        >
          <AnimatePresence mode="wait">
            {TABS.map(({ id, View }) =>
              id === activeTab ? (
                <motion.div
                  key={id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.12 }}
                  className="absolute inset-0 overflow-auto"
                >
                  <View
                    ref={id === "table" ? tableRef : undefined}
                    onCsvStateChange={id === "table" ? setCsvState : undefined}
                  />
                </motion.div>
              ) : null,
            )}
          </AnimatePresence>
        </Suspense>
      </main>

      <Dialog open={shortcutsOpen} onOpenChange={setShortcutsOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Skróty klawiszowe</DialogTitle>
            <DialogDescription>Szybsze nawigowanie po katalogu</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 text-sm">
            {[
              ["⌘K", "Polecenia"],
              ["⌘O", "Upload CSV"],
              ["⌘F", "Fokus na filtr kolumny"],
              ["D", "Zmień gęstość"],
              ["R", "Wyczyść filtry i sortowanie"],
              ["↑ ↓", "Nawigacja po wierszach"],
              ["Esc", "Wyczyść fokus / zamknij"],
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

      <GeminiDrawer
        onOpenSettings={() => setSettingsOpen(true)}
        activeDataset={csvState.activeDataset || csvState.fileMeta?.name || "master.csv"}
        knowledgeIds={knowledgeIds}
      />
      <KnowledgeDrawer
        open={knowledgeOpen}
        onOpenChange={setKnowledgeOpen}
        onSelectionChange={setKnowledgeIds}
      />
      <SettingsDrawer open={settingsOpen} onOpenChange={setSettingsOpen} onVaultChange={handleVaultChange} />
    </div>
  );
}

/**
 * HealthBadge — compact status of the secrets vault + fallback chain.
 * Shows the active priority list and how many keys are loaded per provider.
 * Falls back to "OFFLINE" badge if the API is unreachable.
 */
function HealthBadge({ vault, error }) {
  // Minimal badge — no clutter. Only shows status, not key counts or chains.
  if (error && !vault) {
    return (
      <Badge variant="outline" className="text-[10px] border-red-300 bg-red-50 text-red-700">
        <AlertCircle className="h-3 w-3 mr-1" />
        OFFLINE
      </Badge>
    );
  }
  if (!vault) {
    return (
      <Badge variant="outline" className="text-[10px]">
        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
        Ładowanie…
      </Badge>
    );
  }
  return (
    <Badge
      variant="outline"
      className="text-[10px] border-green-300 bg-green-50 text-green-700"
    >
      <CheckCircle2 className="h-3 w-3 mr-1" />
      OK
    </Badge>
  );
}

