import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FolderOpen, FileText, Database, Trash2, Loader2, X } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { formatBytes } from "@/lib/utils";
import { apiUrl, getAuthHeader } from "@/lib/api";
import { Progress } from "@/components/ui/progress";

export function FilesDrawer({ open, onOpenChange }) {
  const [files, setFiles] = useState([]);
  const [totalBytes, setTotalBytes] = useState(0);
  const [quotaBytes, setQuotaBytes] = useState(500 * 1024 * 1024);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(apiUrl("/api/files"), {
        headers: getAuthHeader(),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const body = await res.json();
      setFiles(body.files || []);
      setTotalBytes(body.total_bytes || 0);
      setQuotaBytes(body.quota_bytes || 500 * 1024 * 1024);
    } catch (e) {
      toast.error("Nie udało się pobrać plików", { description: e.message });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  const removeFile = async (file) => {
    setDeletingId(file.id || file.filename);
    try {
      let endpoint = "";
      if (file.type === "catalog") {
        endpoint = `/api/upload/${encodeURIComponent(file.filename)}`;
      } else {
        endpoint = `/api/knowledge/${file.id}`;
      }
      
      const res = await fetch(apiUrl(endpoint), {
        method: "DELETE",
        headers: getAuthHeader(),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || res.statusText);
      
      toast.success("Usunięto plik", { description: file.filename });
      await load();
    } catch (e) {
      toast.error("Nie udało się usunąć", { description: e.message });
    } finally {
      setDeletingId(null);
    }
  };

  const usagePercent = Math.min(100, Math.max(0, (totalBytes / quotaBytes) * 100));

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        showCloseButton={false}
        className="w-full sm:max-w-md p-0 flex flex-col gap-0"
      >
        <SheetHeader className="px-5 pt-5 pb-3 border-b">
          <div className="flex items-center justify-between">
            <SheetTitle className="flex items-center gap-2">
              <FolderOpen className="h-5 w-5 text-indigo-500" />
              Moje Pliki
            </SheetTitle>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => onOpenChange(false)}
                aria-label="Zamknij"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <SheetDescription>
            Zarządzaj swoimi plikami katalogowymi i bazą wiedzy.
          </SheetDescription>
        </SheetHeader>

        <div className="px-5 py-4 border-b bg-muted/30">
          <div className="flex items-center justify-between text-xs mb-1.5 font-medium">
            <span>Zużycie miejsca</span>
            <span>{formatBytes(totalBytes)} / {formatBytes(quotaBytes)}</span>
          </div>
          <Progress value={usagePercent} className="h-1.5" />
        </div>

        <ScrollArea className="flex-1">
          <div className="p-5 space-y-2">
            {loading && files.length === 0 ? (
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground py-8">
                <Loader2 className="h-4 w-4 animate-spin" />
                Ładowanie…
              </div>
            ) : files.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                Brak przesłanych plików.
              </p>
            ) : (
              files.map((file) => (
                <FileItem
                  key={file.id || file.filename}
                  file={file}
                  onRemove={() => removeFile(file)}
                  isDeleting={deletingId === (file.id || file.filename)}
                />
              ))
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}

function FileItem({ file, onRemove, isDeleting }) {
  const isCatalog = file.type === "catalog";
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border bg-card p-3 flex items-start gap-3"
    >
      <div className="shrink-0 mt-0.5 text-muted-foreground">
        {isCatalog ? <Database className="h-5 w-5 text-blue-500" /> : <FileText className="h-5 w-5 text-emerald-500" />}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate" title={file.filename}>
          {file.filename}
        </p>
        <p className="text-xs text-muted-foreground flex items-center gap-2 flex-wrap">
          <span>{formatBytes(file.size_bytes || 0)}</span>
          <span className="text-muted-foreground/60">· {isCatalog ? 'Katalog' : 'Wiedza'}</span>
          {file.uploaded_at && (
            <span className="text-muted-foreground/60">
              · {new Date(file.uploaded_at).toLocaleDateString()}
            </span>
          )}
        </p>
      </div>

      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
        onClick={onRemove}
        disabled={isDeleting}
        title="Usuń"
      >
        {isDeleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
      </Button>
    </motion.div>
  );
}
