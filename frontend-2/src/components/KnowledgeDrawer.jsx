import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  Upload,
  FileText,
  Trash2,
  Loader2,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  RotateCw,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { cn, formatNumber } from "@/lib/utils";

function formatBytes(n) {
  if (!n || n < 1024) return `${n || 0} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
  return `${(n / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

const ALLOWED_EXTS = [".pdf", ".csv", ".txt", ".md", ".xlsx", ".xls", ".docx"];

/**
 * KnowledgeDrawer — uploads files (PDF / CSV / text) to the Gemini Files API
 * so the AI Assistant can ground its answers in them.
 *
 * Backend:
 *   GET    /api/knowledge            → list indexed files
 *   POST   /api/knowledge/upload    → multipart, returns {id, gemini_uri, ...}
 *   DELETE /api/knowledge/{id}     → remove from index + Gemini
 *
 * Selection model: per-file checkbox. Selected IDs are reported to the
 * parent via `onSelectionChange(ids)` so GeminiDrawer can include them in
 * the next /api/chat call. When the drawer is closed, selection persists
 * in the parent — the user can keep using the chat with knowledge attached.
 */
export function KnowledgeDrawer({ open, onOpenChange, onSelectionChange }) {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(() => new Set());
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/knowledge");
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const body = await res.json();
      const next = Array.isArray(body.items) ? body.items : [];
      setItems(next);
      // Drop any selected IDs that no longer exist
      setSelected((prev) => {
        const valid = new Set(next.map((it) => it.id));
        const filtered = new Set([...prev].filter((id) => valid.has(id)));
        if (filtered.size !== prev.size) {
          onSelectionChange?.(Array.from(filtered));
        }
        return filtered;
      });
    } catch (e) {
      toast.error("Nie udało się pobrać listy plików", { description: e.message });
    } finally {
      setLoading(false);
    }
  }, [onSelectionChange]);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  // Report selection up to parent whenever it changes
  useEffect(() => {
    onSelectionChange?.(Array.from(selected));
  }, [selected, onSelectionChange]);

  const handleFiles = async (fileList) => {
    if (!fileList || fileList.length === 0) return;
    setUploading(true);
    for (const file of fileList) {
      const ext = "." + (file.name.split(".").pop() || "").toLowerCase();
      if (!ALLOWED_EXTS.includes(ext)) {
        toast.error(`Niedozwolony typ pliku: ${ext}`, { description: file.name });
        continue;
      }
      const form = new FormData();
      form.append("file", file);
      try {
        const res = await fetch("/api/knowledge/upload", { method: "POST", body: form });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(body?.detail || res.statusText);
        }
        toast.success(`Wgrano: ${body.filename}`, {
          description: `${(body.size / 1024).toFixed(1)} KB`,
        });
      } catch (e) {
        toast.error(`Nie udało się wgrać ${file.name}`, { description: e.message });
      }
    }
    setUploading(false);
    await load();
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const remove = async (id) => {
    const item = items.find((it) => it.id === id);
    if (!item) return;
    try {
      const res = await fetch(`/api/knowledge/${id}`, { method: "DELETE" });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || res.statusText);
      toast.success("Usunięto", { description: item.filename });
      setSelected((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      await load();
    } catch (e) {
      toast.error("Nie udało się usunąć", { description: e.message });
    }
  };

  const [refreshing, setRefreshing] = useState(() => new Set());
  const refresh = async (id) => {
    if (refreshing.has(id)) return;
    setRefreshing((prev) => new Set(prev).add(id));
    try {
      const res = await fetch(`/api/knowledge/${id}/refresh`, { method: "POST" });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || res.statusText);
      toast.success("Odświeżono", { description: body.filename });
      await load();
    } catch (e) {
      toast.error("Nie udało się odświeżyć", { description: e.message });
    } finally {
      setRefreshing((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const toggleSelected = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-md p-0 flex flex-col gap-0"
      >
        <SheetHeader className="px-5 pt-5 pb-3 border-b">
          <div className="flex items-center justify-between">
            <SheetTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-emerald-500" />
              Baza wiedzy
            </SheetTitle>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={load}
                disabled={loading}
                title="Odśwież"
              >
                <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => onOpenChange(false)}
                aria-label="Zamknij"
              >
                <span aria-hidden>×</span>
              </Button>
            </div>
          </div>
          <SheetDescription>
            Pliki, które AI Assistant widzi przy odpowiedziach (PDF, CSV, dokumenty).
          </SheetDescription>
        </SheetHeader>

        {/* Drop zone */}
        <div className="px-5 pt-4">
          <div
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "rounded-xl border-2 border-dashed p-5 text-center cursor-pointer transition-colors",
              isDragging
                ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-950/30"
                : "border-muted-foreground/30 hover:border-muted-foreground/60",
              uploading && "pointer-events-none opacity-60"
            )}
          >
            {uploading ? (
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Wgrywanie…
              </div>
            ) : (
              <>
                <Upload className="h-6 w-6 mx-auto mb-1.5 text-muted-foreground" />
                <p className="text-sm font-medium">Upuść pliki tutaj</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  lub kliknij, żeby wybrać · PDF, CSV, TXT, MD, XLSX, DOCX
                </p>
              </>
            )}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.csv,.txt,.md,.markdown,.xlsx,.xls,.docx"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </div>
        </div>

        {/* File list */}
        <ScrollArea className="flex-1 mt-4">
          <div className="px-5 pb-5 space-y-2">
            {loading && items.length === 0 ? (
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground py-8">
                <Loader2 className="h-4 w-4 animate-spin" />
                Ładowanie…
              </div>
            ) : items.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                Brak plików. Wgraj pierwszy powyżej.
              </p>
            ) : (
              items.map((item) => (
                <KnowledgeItem
                  key={item.id}
                  item={item}
                  selected={selected.has(item.id)}
                  onToggle={() => toggleSelected(item.id)}
                  onRemove={() => remove(item.id)}
                  onRefresh={() => refresh(item.id)}
                  refreshing={refreshing.has(item.id)}
                />
              ))
            )}
          </div>
        </ScrollArea>

        {items.length > 0 && (
          <div className="px-5 py-3 border-t text-xs text-muted-foreground">
            {selected.size} z {items.length} wybranych dołączanych do czatu
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

function KnowledgeItem({ item, selected, onToggle, onRemove, onRefresh, refreshing }) {
  const isReady = item.status === "ready" && item.gemini_uri;
  const isFailed = item.status === "failed";

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "rounded-lg border p-3 flex items-start gap-3",
        selected && isReady
          ? "border-emerald-300 bg-emerald-50/40 dark:bg-emerald-950/20"
          : "bg-card"
      )}
    >
      <button
        onClick={onToggle}
        disabled={!isReady}
        className={cn(
          "shrink-0 mt-0.5 h-4 w-4 rounded border flex items-center justify-center transition-colors",
          selected && isReady
            ? "bg-emerald-500 border-emerald-500 text-white"
            : "border-muted-foreground/40 bg-background",
          !isReady && "opacity-40 cursor-not-allowed"
        )}
        title={isReady ? "Dołącz do czatu" : "Plik nie jest jeszcze gotowy"}
      >
        {selected && isReady && <CheckCircle2 className="h-3 w-3" />}
      </button>

      <FileText className="h-5 w-5 shrink-0 mt-0.5 text-muted-foreground" />

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate" title={item.filename}>
          {item.filename}
        </p>
        <p className="text-xs text-muted-foreground flex items-center gap-2 flex-wrap">
          <span>{formatBytes(item.size || 0)}</span>
          {item.mime_type && (
            <span className="text-muted-foreground/60">· {item.mime_type.replace("application/", "")}</span>
          )}
          {isFailed ? (
            <Badge variant="outline" className="text-[10px] py-0 px-1.5 border-red-300 text-red-700">
              <AlertCircle className="h-2.5 w-2.5 mr-0.5" />
              błąd
            </Badge>
          ) : isReady ? (
            <Badge variant="outline" className="text-[10px] py-0 px-1.5 border-emerald-300 text-emerald-700">
              <CheckCircle2 className="h-2.5 w-2.5 mr-0.5" />
              gotowy
            </Badge>
          ) : (
            <Badge variant="outline" className="text-[10px] py-0 px-1.5">
              <Loader2 className="h-2.5 w-2.5 mr-0.5 animate-spin" />
              {item.status || "przetwarzanie"}
            </Badge>
          )}
        </p>
      </div>

      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 shrink-0 text-muted-foreground hover:text-emerald-600"
        onClick={onRefresh}
        disabled={refreshing}
        title="Wyślij ponownie do Gemini (po wygaśnięciu pliku w Gemini Files API)"
      >
        {refreshing ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <RotateCw className="h-3.5 w-3.5" />
        )}
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
        onClick={onRemove}
        title="Usuń"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </motion.div>
  );
}
