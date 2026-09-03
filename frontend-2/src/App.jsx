import { useCallback, useEffect, useMemo, useRef, useState, lazy, Suspense } from "react";
import {
  Table as TableIcon,
  BarChart3,
  KeyRound,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Command as CommandIcon,
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
 *     HealthBadge (fallback chain + #kluczy), Baza wiedzy, Command palette,
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
  // Read prefs once per profile change instead of every render.
  // Old code called loadPrefs() 3x in JSX — every render hit localStorage + JSON.parse.
  const prefs = useMemo(() => loadPrefs(activeProfile), [activeProfile]);
  const [activeTab, setActiveTab] = useState(() => loadPrefs(activeProfile)?.activeTab || "leads");
  const [snapshotsOpen, setSnapshotsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [filesOpen, setFilesOpen] = useState(false);
  const [knowledgeOpen, setKnowledgeOpen] = useState(false);
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
    <div className="flex h-dvh flex-col bg-background text-foreground selection:bg-brand/20 selection:text-brand-muted-foreground dark:selection:text-brand">
      <header className="flex h-14 shrink-0 items-center justify-between gap-2 border-b border-border/70 bg-background/85 px-3 backdrop-blur-md supports-[backdrop-filter]:bg-background/70 safe-top sm:px-5 z-40 sticky top-0 shadow-xs">
        <div className="flex min-w-0 items-center gap-2 sm:gap-4">
          {/* Top-left logo with glowing icon badge */}
          <a
            href="/"
            title="Wróć do strony głównej (odświeża widok)"
            aria-label="BILLSzuka — strona główna"
            className="flex items-center gap-2.5 rounded-lg p-1.5 transition-all hover:bg-muted/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 cursor-pointer group"
          >
            <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-brand via-brand-indigo to-brand-rose flex items-center justify-center text-brand-foreground font-bold text-xs shadow-sm group-hover:scale-105 transition-transform">
              B
            </div>
            <div className="leading-none">
              <div className="font-bold tracking-tight text-sm text-foreground flex items-center gap-1.5">
                BILLSzuka
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-brand-muted text-brand-muted-foreground border border-brand-muted-foreground/20">
                  v2.2
                </span>
              </div>
              <div className="hidden text-[10px] text-muted-foreground sm:block mt-0.5 font-medium">Katalog leadów B2B/B2C</div>
            </div>
          </a>

          {/* Navigation tabs */}
          <nav className="flex items-center gap-1 bg-muted/40 p-1 rounded-xl border border-border/50" aria-label="Widoki">
            {TABS.map(({ id, label, icon: Icon }) => {
              const active = activeTab === id;
              return (
                <button
                  key={id}
                  onClick={() => handleTabChange(id)}
                  aria-label={label}
                  title={label}
                  className={cn(
                    "inline-flex items-center justify-center gap-1.5 rounded-lg px-2.5 text-xs font-semibold transition-all min-h-[36px] sm:px-3 sm:gap-2",
                    active
                      ? "bg-card text-foreground shadow-sm border border-border/60"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/60",
                  )}
                  aria-pressed={active}
                  aria-current={active ? "page" : undefined}
                >
                  <Icon className={cn("h-4 w-4 shrink-0", active ? "text-brand font-bold" : "opacity-70")} />
                  <span className="hidden sm:inline truncate">{label}</span>
                </button>
              );
            })}
          </nav>
        </div>
        <div className="flex shrink-0 items-center gap-1 sm:gap-2">
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
                  <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-success ring-2 ring-background" />
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-[16rem]">
              <DropdownMenuLabel className="flex flex-col gap-0.5">
                <span className="text-xs font-normal text-muted-foreground">Zalogowany jako</span>
                <span className="font-semibold truncate">{activeProfile}</span>
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
                  <span className="text-[10px] text-success font-medium">
                    {knowledgeIds.length} aktywnych
                  </span>
                )}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSnapshotsOpen(true)}>
                <History className="h-4 w-4 mr-2" />
                <span className="flex-1">Historia sesji</span>
                <span className="text-[10px] text-muted-foreground hidden sm:inline">Zrzuty + logowania</span>
              </DropdownMenuItem>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  {theme === "light" && <Sun className="h-4 w-4 mr-2" />}
                  {theme === "dark" && <Moon className="h-4 w-4 mr-2" />}
                  {theme === "system" && <Monitor className="h-4 w-4 mr-2" />}
                  <span className="flex-1">Motyw</span>
                  <span className="text-[10px] text-muted-foreground capitalize">{theme}</span>
                </DropdownMenuSubTrigger>
                <DropdownMenuSubContent>
                  <DropdownMenuItem onClick={() => handleThemeChange("light")}>
                    <Sun className="h-4 w-4 mr-2" /> Jasny {theme === "light" && "✓"}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleThemeChange("dark")}>
                    <Moon className="h-4 w-4 mr-2" /> Ciemny {theme === "dark" && "✓"}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleThemeChange("system")}>
                    <Monitor className="h-4 w-4 mr-2" /> Systemowy {theme === "system" && "✓"}
                  </DropdownMenuItem>
                </DropdownMenuSubContent>
              </DropdownMenuSub>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Bookmark className="h-4 w-4 mr-2" />
                  <span className="flex-1">Zapisane widoki</span>
                  <span className="text-[10px] text-muted-foreground">
                    {DEFAULT_VIEWS.length + ((prefs.savedViews) || []).length}
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
                    const userViews = (prefs.savedViews) || [];
                    if (!userViews.length) return null;
                    return (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel className="text-[10px] uppercase tracking-wider text-muted-foreground">
                          Moje
                        </DropdownMenuLabel>
                        {userViews.map((v) => (
                          <DropdownMenuItem key={v.id} onClick={() => handleApplyView(v)}>
                            <Bookmark className="h-3.5 w-3.5 mr-2 text-success" />
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
              aria-label="Polecenia"
              title="Polecenia"
              className="hidden sm:inline-flex"
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
           setActiveTab(loadPrefs(activeProfile)?.activeTab || "table");
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
  if (error && !vault) {
    return (
      <Badge variant="error" size="sm" className="hidden sm:inline-flex">
        <AlertCircle className="h-3 w-3 mr-1" />
        OFFLINE
      </Badge>
    );
  }
  if (!vault) {
    return (
      <Badge variant="outline" size="sm" className="hidden sm:inline-flex">
        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
        Ładowanie…
      </Badge>
    );
  }
  return (
    <Badge variant="success" size="sm" className="hidden sm:inline-flex">
      <CheckCircle2 className="h-3 w-3 mr-1" />
      OK
    </Badge>
  );
}

/* forced rebuild 1788208180 */
