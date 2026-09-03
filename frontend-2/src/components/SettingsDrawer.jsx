import { useEffect, useState } from "react";
import {
  X,
  Plus,
  Trash2,
  Loader2,
  CheckCircle2,
  XCircle,
  KeyRound,
  ShieldCheck,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import {
  fetchSettings,
  addKey,
  deleteKey,
  testKey,
} from "@/lib/secretsApi";

/**
 * SettingsDrawer — manage OpenRouter + Gemini API keys + fallback chain.
 *
 * Controlled by parent (open, onOpenChange). Pulls secrets vault via
 * fetchSettings() — keys are returned already redacted by the backend
 * (we only ever see alias + fingerprint).
 *
 * Provider UX is provider-specific:
 *   - OpenRouter: 1 field (key). Alias optional (default "primary").
 *   - Gemini: key + optional "project" label (cosmetic, helps when
 *     managing multiple free-tier Google accounts). The Gemini API key
 *     format is AIza... (39 chars). The project label is just a memory
 *     aid — the key alone is enough to call the API.
 */
export function SettingsDrawer({ open, onOpenChange, onVaultChange }) {
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(false);
  const [busyAlias, setBusyAlias] = useState(null); // "openrouter:alias" | "gemini:alias"
  const [addDialog, setAddDialog] = useState({ open: false, provider: null });

  // Refresh vault. Always fetch on open to pick up external changes; pass
  // the result up via onVaultChange so the HealthBadge stays accurate.
  // The drawer only shows the "Ładowanie…" spinner on the very first
  // fetch (snapshot === null) — once we have data we keep showing it
  // while a silent background refresh runs.
  async function refresh({ silent = false } = {}) {
    const firstLoad = snapshot === null;
    if (!silent || firstLoad) setLoading(firstLoad);
    try {
      const s = await fetchSettings();
      setSnapshot(s);
      onVaultChange?.(s);
    } catch (e) {
      toast.error("Nie udało się pobrać ustawień", { description: e.message });
    } finally {
      if (firstLoad) setLoading(false);
    }
  }

  useEffect(() => {
    if (open) refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function onAddClick(provider) {
    setAddDialog({ open: true, provider });
  }

  async function handleAddSubmit(provider, values) {
    try {
      await addKey(provider, values);
      toast.success("Klucz dodany", { description: `${provider}:${values.alias}` });
      await refresh({ silent: true });
      setAddDialog({ open: false, provider: null });
    } catch (e) {
      toast.error("Błąd dodawania", { description: e.message });
    }
  }

  async function onDelete(provider, alias) {
    if (!window.confirm(`Usunąć klucz ${provider}:${alias}?`)) return;
    try {
      await deleteKey(provider, alias);
      toast.success("Klucz usunięty");
      await refresh({ silent: true });
    } catch (e) {
      toast.error("Błąd usuwania", { description: e.message });
    }
  }

  async function onTest(provider, alias) {
    setBusyAlias(`${provider}:${alias}`);
    try {
      const r = await testKey(provider, alias);
      if (r.ok) {
        toast.success(`OK (${r.latency_ms} ms)${r.model ? ` · ${r.model}` : ""}`, {
          description: `${provider}:${alias}`,
        });
      } else {
        toast.error("Test klucza nieudany", { description: r.error || "(brak szczegółów)" });
      }
      await refresh({ silent: true });
    } catch (e) {
      toast.error("Błąd testu", { description: e.message });
    } finally {
      setBusyAlias(null);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" showCloseButton={false} className="w-full sm:max-w-lg p-0 flex flex-col gap-0">
        <SheetHeader className="px-4 sm:px-5 pt-4 sm:pt-5 pb-3 border-b">
          <div className="flex items-center justify-between">
            <SheetTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-brand" />
              Klucze API
            </SheetTitle>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => onOpenChange(false)}
              aria-label="Zamknij"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </SheetHeader>

        <ScrollArea className="flex-1">
          <div className="p-5 space-y-6">
            {/* Security notice */}
            <div className="rounded-lg border bg-muted/30 p-3 text-xs text-muted-foreground flex gap-2">
              <ShieldCheck className="h-4 w-4 shrink-0 mt-0.5 text-green-600" />
              <div>
                <div className="font-medium text-foreground mb-1">Bezpieczeństwo</div>
                Klucze nigdy nie są wysyłane do przeglądarki w pełnej formie — backend
                zwraca tylko alias + odcisk (pierwsze 4 + ostatnie 4 znaki). Plik
                sejfu ma uprawnienia 0600 i jest ignorowany przez git.
              </div>
            </div>

            {/* OpenRouter */}
            <ProviderSection
              title="OpenRouter"
              description="Jeden klucz wystarczy — dostęp do wielu modeli (np. llama, qwen). Prefix: sk-or-v1-..."
              items={snapshot?.openrouter || []}
              loading={loading}
              busyAlias={busyAlias}
              onAdd={() => onAddClick("openrouter")}
              onDelete={(alias) => onDelete("openrouter", alias)}
              onTest={(alias) => onTest("openrouter", alias)}
              emptyHint="Brak kluczy. OpenRouter agreguje wiele modeli — dobry wybór 'primary'."
            />

            <Separator />

            {/* Gemini */}
            <ProviderSection
              title="Google Gemini"
              description="Darmowe konto Google → aistudio.google.com → API key. Format: AIza... Limity: 15 RPM, 1500 RPD na klucz — dlatego polecamy kilka."
              items={snapshot?.gemini || []}
              loading={loading}
              busyAlias={busyAlias}
              onAdd={() => onAddClick("gemini")}
              onDelete={(alias) => onDelete("gemini", alias)}
              onTest={(alias) => onTest("gemini", alias)}
              renderExtra={(it) =>
                it.project ? (
                  <Badge variant="outline" className="text-[10px]">
                    {it.project}
                  </Badge>
                ) : null
              }
              emptyHint="Brak kluczy Gemini. Polecamy dodać co najmniej jeden — Gemini 2.5 Flash jest darmowy i szybki."
            />
          </div>
        </ScrollArea>
      </SheetContent>

      {addDialog.open && (
        <AddKeyDialog
          open={addDialog.open}
          provider={addDialog.provider}
          onOpenChange={(v) => setAddDialog((prev) => ({ ...prev, open: v }))}
          onSubmit={handleAddSubmit}
        />
      )}
    </Sheet>
  );
}

function ProviderSection({
  title,
  description,
  items,
  loading,
  busyAlias,
  onAdd,
  onDelete,
  onTest,
  renderExtra,
  emptyHint,
}) {
  const provider = title.toLowerCase().includes("openrouter") ? "openrouter" : "gemini";
  return (
    <section>
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <KeyRound className="h-4 w-4" />
          {title}
        </h3>
        <Button size="sm" onClick={onAdd}>
          <Plus className="h-3.5 w-3.5 mr-1" />
          Dodaj klucz
        </Button>
      </div>
      <p className="text-xs text-muted-foreground mb-3">{description}</p>

      {loading && !items?.length ? (
        <div className="text-xs text-muted-foreground flex items-center gap-2 py-2">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          Ładowanie…
        </div>
      ) : items?.length ? (
        <ul className="space-y-1.5">
          {items.map((it) => {
            const busy = busyAlias === `${provider}:${it.alias}`;
            return (
              <li
                key={it.alias}
                className="flex items-center gap-2 rounded-md border bg-card px-3 py-2 text-sm"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium truncate">{it.alias}</span>
                    {renderExtra?.(it)}
                    <LastStatus ok={it.last_ok} err={it.last_err} />
                  </div>
                  <div className="font-mono text-[10px] text-muted-foreground mt-0.5 truncate">
                    {it.fingerprint || "(unknown)"}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => onTest(it.alias)}
                  disabled={busy}
                  aria-label="Testuj"
                  title="Testuj"
                >
                  {busy ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <ShieldCheck className="h-3.5 w-3.5" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-red-600 hover:text-red-700"
                  onClick={() => onDelete(it.alias)}
                  aria-label="Usuń"
                  title="Usuń"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="text-xs text-muted-foreground italic py-2">{emptyHint}</div>
      )}
    </section>
  );
}

function LastStatus({ ok, err }) {
  if (err) {
    return (
      <span
        className="text-[10px] text-red-600 flex items-center gap-1"
        title={err}
      >
        <XCircle className="h-3 w-3" />
        err
      </span>
    );
  }
  if (ok) {
    return (
      <span className="text-[10px] text-green-600 flex items-center gap-1" title={ok}>
        <CheckCircle2 className="h-3 w-3" />
        ok
      </span>
    );
  }
  return <span className="text-[10px] text-muted-foreground">—</span>;
}

function AddKeyDialog({ open, provider, onOpenChange, onSubmit }) {
  const [alias, setAlias] = useState("");
  const [key, setKey] = useState("");
  const [project, setProject] = useState("");

  useEffect(() => {
    if (open) {
      setAlias(provider === "gemini" ? "personal-free" : "primary");
      setKey("");
      setProject("");
    }
  }, [open, provider]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!alias.trim() || !key.trim()) return;
    onSubmit(provider, {
      alias: alias.trim(),
      key: key.trim(),
      project: provider === "gemini" ? project.trim() : undefined,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Dodaj klucz {provider === "gemini" ? "Gemini" : "OpenRouter"}</DialogTitle>
            <DialogDescription>
              {provider === "gemini"
                ? "Klucz Gemini powinien zaczynać się od AIza..."
                : "Klucz OpenRouter powinien zaczynać się od sk-or-v1-..."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label htmlFor="alias" className="text-sm font-medium">Alias</label>
              <Input
                id="alias"
                value={alias}
                onChange={(e) => setAlias(e.target.value)}
                placeholder={provider === "gemini" ? "np. personal-free, work" : "np. primary, backup-1"}
                required
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="key" className="text-sm font-medium">Klucz API</label>
              <Input
                id="key"
                type="password"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder={provider === "gemini" ? "AIza..." : "sk-or-v1-..."}
                required
              />
            </div>
            {provider === "gemini" && (
              <div className="space-y-2">
                <label htmlFor="project" className="text-sm font-medium">Projekt (opcjonalnie)</label>
                <Input
                  id="project"
                  value={project}
                  onChange={(e) => setProject(e.target.value)}
                  placeholder="np. billszuka"
                />
              </div>
            )}
          </div>
          <DialogFooter className="mt-2">
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Anuluj
            </Button>
            <Button type="submit" disabled={!alias.trim() || !key.trim()}>
              Zapisz
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}