import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Table as TableIcon,
  BarChart3,
  KeyRound,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { fetchSettings } from "@/lib/secretsApi";
import { GeminiDrawer } from "@/components/GeminiDrawer";
import { SettingsDrawer } from "@/components/SettingsDrawer";
import { TableView } from "@/views/TableView";
import { AnalyticsView } from "@/views/AnalyticsView";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

/**
 * App — BILLSzuka Dashboard Hub shell.
 *
 * 3-pane layout:
 *   - Header (sticky): product name, Tabela/Analityka tabs, HealthBadge
 *     (shows fallback chain + #kluczy, polls /api/settings every 10s),
 *     Settings gear.
 *   - Active view (Tabela = RawTable CSV viewer, Analityka = dashboards).
 *   - Gemini FAB (chat panel, bottom-right).
 *
 * Settings drawer is opened from the gear icon or from the Gemini header
 * button. Both drawers are siblings of the main content — they overlay.
 */

const TABS = [
  { id: "table", label: "Tabela", icon: TableIcon, View: TableView },
  { id: "analytics", label: "Analityka", icon: BarChart3, View: AnalyticsView },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("table");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [vault, setVault] = useState(null); // redacted vault snapshot
  const [vaultError, setVaultError] = useState(null);

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
      <header className="flex h-14 shrink-0 items-center justify-between border-b bg-background/80 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center gap-4">
          <div className="leading-tight">
            <div className="font-semibold tracking-tight">BILLSzuka</div>
            <div className="text-[10px] text-muted-foreground">Katalog leadów B2B/B2C</div>
          </div>
          <nav className="flex items-center gap-1">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={cn(
                  "inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  activeTab === id
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
                )}
                aria-pressed={activeTab === id}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <HealthBadge vault={vault} error={vaultError} />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSettingsOpen(true)}
            aria-label="Klucze API"
            title="Klucze API"
          >
            <KeyRound className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <main className="relative flex-1 overflow-hidden">
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
                <View />
              </motion.div>
            ) : null,
          )}
        </AnimatePresence>
      </main>

      <GeminiDrawer onOpenSettings={() => setSettingsOpen(true)} activeDataset="master.csv" />
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
