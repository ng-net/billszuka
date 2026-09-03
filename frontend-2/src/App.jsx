import { useCallback, useEffect, useRef, useState, lazy, Suspense } from "react";
import {
  Table as TableIcon,
  BarChart3,
  KeyRound,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Command as CommandIcon,
  Keyboard,
  Sun,
  Moon,
  Monitor,
  User,
  LogOut,
  Camera,
  FolderOpen,
  Sparkles,
  History,
  Bookmark,
  Library,
  Compass,
} from "lucide-react";
import { getActiveProfile, setActiveProfile } from "@/lib/auth";
import { ProfileSelector } from "@/components/ProfileSelector";
import { SnapshotsDialog } from "@/components/SnapshotsDialog";
import { fetchSettings } from "@/lib/secretsApi";
import { loadPrefs, savePrefs } from "@/lib/prefs";
import { DEFAULT_VIEWS } from "@/lib/views";
import { GeminiDrawer } from "@/components/GeminiDrawer";
import { KnowledgeDrawer } from "@/components/KnowledgeDrawer";
import { SettingsDrawer } from "@/components/SettingsDrawer";
import { FilesDrawer } from "@/components/FilesDrawer";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
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

const LeadsView = lazy(() => import("@/views/LeadsView").then((m) => ({ default: m.LeadsView })));
const TableView = lazy(() => import("@/views/TableView").then((m) => ({ default: m.TableView })));
const AnalyticsView = lazy(() => import("@/views/AnalyticsView").then((m) => ({ default: m.AnalyticsView })));
const AtlasGrokView = lazy(() => import("@/views/AtlasGrokView").then((m) => ({ default: m.AtlasGrokView })));

const TABS = [
  { id: "leads", label: "Katalog Leadów", icon: Sparkles, View: LeadsView },
  { id: "atlas", label: "Atlas Grok (Cyber Radar)", icon: Compass, View: AtlasGrokView },
  { id: "table", label: "Siatka Danych (36 col)", icon: TableIcon, View: TableView },
  { id: "analytics", label: "Analityka Rynku", icon: BarChart3, View: AnalyticsView },
];

export default function App() {
  const [activeProfile, setActiveProfileState] = useState(() => getActiveProfile());
  const [activeTab, setActiveTab] = useState(() => loadPrefs(activeProfile)?.activeTab || "leads");
  const [snapshotsOpen, setSnapshotsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [filesOpen, setFilesOpen] = useState(false);
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

  // Profile dropdown: lists built-in DEFAULT_VIEWS plus user-defined
  // savedViews from prefs. Clicking one delegates to RawTable via the
  // imperative ref — that's the single source of truth for "apply view".
  const handleApplyView = useCallback((view) => {
    if (activeTab !== "table") handleTabChange("table");
    // RawTable owns filter state; defer to its imperative handle.
    tableRef.current?.applyView?.(view);
  }, [activeTab, handleTabChange]);

  if (!activeProfile) {
    return (
      <ProfileSelector
        onSelect={(id) => {
          setActiveProfile(id);
          setActiveProfileState(id);
          setActiveTab(loadPrefs(id)?.activeTab || "table");
        }}
      />
    );
  }

  return (
    <div className="flex h-dvh flex-col bg-background text-foreground selection:bg-indigo-500/20 selection:text-indigo-700 dark:selection:text-indigo-300">
      <header className="flex h-14 shrink-0 items-center justify-between gap-2 border-b border-border/70 bg-background/85 px-3 backdrop-blur-md supports-[backdrop-filter]:bg-background/70 sm:px-5 z-40 sticky top-0 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
        <div className="flex min-w-0 items-center gap-3 sm:gap-6">
          {/* Top-left logo with glowing icon badge */}
          <a
            href="/"
            title="Wróć do strony głównej (odświeża widok)"
            aria-label="BILLSzuka — strona główna"
            className="flex items-center gap-2.5 rounded-lg px-1.5 py-1 transition-all hover:bg-muted/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 cursor-pointer group"
          >
            <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center text-white font-bold text-xs shadow-sm group-hover:scale-105 transition-transform">
              B
            </div>
            <div className="leading-none">
              <div className="font-bold tracking-tight text-sm text-foreground flex items-center gap-1.5">
                BILLSzuka
                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800/60">
                  v2.2
                </span>
              </div>
              <div className="hidden text-[10px] text-muted-foreground sm:block mt-0.5 font-medium">Katalog leadów B2B/B2C</div>
            </div>
          </a>

          {/* Navigation tabs */}
          <nav className="flex items-center gap-1 bg-muted/40 p-1 rounded-xl border border-border/50">
            {TABS.map(({ id, label, icon: Icon }) => {
              const active = activeTab === id;
              return (
                <button
                  key={id}
                  onClick={() => handleTabChange(id)}
                  aria-label={label}
                  title={label}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-semibold transition-all sm:px-3.5",
                    active
                      ? "bg-card text-foreground shadow-sm border border-border/60"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/60",
                  )}
                  aria-pressed={active}
                >
                  <Icon className={cn("h-3.5 w-3.5", active ? "text-primary font-bold" : "opacity-70")} />
                  <span className="hidden sm:inline">{label}</span>
                </button>
              );
            })}
          </nav>
        </div>
        <div className="flex shrink-0 items-center gap-1 sm:gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShortcutsOpen(true)}
            aria-label="Skróty klawiszowe"
            title="Skróty klawiszowe (?)"
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
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                title={`Profil: ${activeProfile}`}
                aria-label="Profil i konto"
                className="relative"
              >
                <User className="h-4 w-4" />
                {knowledgeIds.length > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-background" />
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-[16rem]">
              <DropdownMenuLabel className="flex flex-col gap-0.5">
                <span className="text-xs font-normal text-muted-foreground">Zalogowany jako</span>
                <span className="font-semibold">{activeProfile}</span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setSettingsOpen(true)}>
                <KeyRound className="h-4 w-4 mr-2" />
                <span className="flex-1">Klucze API</span>
                <span className="text-[10px] text-muted-foreground">
                  {vault
                    ? (vault.openrouter?.length || 0) + (vault.gemini?.length || 0)
                    : "…"}
                </span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setKnowledgeOpen(true)}>
                <Library className="h-4 w-4 mr-2" />
                <span className="flex-1">Baza wiedzy</span>
                {knowledgeIds.length > 0 && (
                  <span className="text-[10px] text-emerald-600 font-medium">
                    {knowledgeIds.length} aktywnych
                  </span>
                )}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSnapshotsOpen(true)}>
                <History className="h-4 w-4 mr-2" />
                <span className="flex-1">Historia sesji</span>
                <span className="text-[10px] text-muted-foreground">Zrzuty + logowania</span>
              </DropdownMenuItem>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Bookmark className="h-4 w-4 mr-2" />
                  <span className="flex-1">Zapisane widoki</span>
                  <span className="text-[10px] text-muted-foreground">
                    {DEFAULT_VIEWS.length + ((loadPrefs(activeProfile).savedViews) || []).length}
                  </span>
                </DropdownMenuSubTrigger>
                <DropdownMenuSubContent className="max-h-80 overflow-auto">
                  <DropdownMenuLabel className="text-[10px] uppercase tracking-wider text-muted-foreground">
                    Wbudowane
                  </DropdownMenuLabel>
                  {DEFAULT_VIEWS.map((v) => (
                    <DropdownMenuItem key={v.id} onClick={() => handleApplyView(v)}>
                      <Bookmark className="h-3.5 w-3.5 mr-2" />
                      {v.name}
                    </DropdownMenuItem>
                  ))}
                  {(() => {
                    const userViews = (loadPrefs(activeProfile).savedViews) || [];
                    if (!userViews.length) return null;
                    return (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel className="text-[10px] uppercase tracking-wider text-muted-foreground">
                          Moje
                        </DropdownMenuLabel>
                        {userViews.map((v) => (
                          <DropdownMenuItem key={v.id} onClick={() => handleApplyView(v)}>
                            <Bookmark className="h-3.5 w-3.5 mr-2 text-emerald-600" />
                            {v.name}
                          </DropdownMenuItem>
                        ))}
                      </>
                    );
                  })()}
                </DropdownMenuSubContent>
              </DropdownMenuSub>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => tableRef.current?.saveSnapshot?.(activeProfile)}>
                <Camera className="h-4 w-4 mr-2" />
                Zapisz zrzut tabeli
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => {
                // Auto-save snapshot on logout if possible
                tableRef.current?.saveSnapshot?.();
                setActiveProfile(null);
                setActiveProfileState(null);
              }}>
                <LogOut className="h-4 w-4 mr-2" />
                Wyloguj się
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <HealthBadge vault={vault} error={vaultError} />
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
            onClick={() => setFilesOpen(true)}
            aria-label="Moje Pliki"
            title="Moje Pliki"
          >
            <FolderOpen className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <main className="flex-1 min-h-0 relative">
        <ErrorBoundary>
          <Suspense
            fallback={
              <div className="absolute inset-0 flex items-center justify-center gap-2 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Ładowanie…</span>
              </div>
            }
          >
            <div className="relative w-full h-full">
              {TABS.map(({ id, View }) => (
                <div
                  key={id}
                  className={`absolute inset-0 overflow-auto transition-opacity duration-150 ${
                    id === activeTab
                      ? "opacity-100 pointer-events-auto z-10"
                      : "opacity-0 pointer-events-none z-0 hidden"
                  }`}
                >
                  <View
                    ref={id === "table" ? tableRef : undefined}
                    onCsvStateChange={id === "table" ? setCsvState : undefined}
                  />
                </div>
              ))}
            </div>
          </Suspense>
        </ErrorBoundary>
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
      <SnapshotsDialog
        open={snapshotsOpen}
        onOpenChange={setSnapshotsOpen}
        onRestore={() => {
           // On restore, simply reload the preferences and refresh
           setActiveTab(loadPrefs(activeProfile)?.activeTab || "table");
           // the dataset will be loaded by RawTable's boot function on mount since it's now in customDataset
        }}
      />
      <FilesDrawer open={filesOpen} onOpenChange={setFilesOpen} />
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

/* forced rebuild 1788208180 */
