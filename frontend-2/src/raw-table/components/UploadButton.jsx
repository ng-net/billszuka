import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { formatNumber } from "@/lib/utils";

const MAX_SIZE = 50 * 1024 * 1024;

export function UploadButton({ onFile, status, progress, fileMeta, onCancel, compact = false }) {
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const handleFiles = (files) => {
    setError(null);
    const file = files?.[0];
    if (!file) return;
    if (!/\.csv$/i.test(file.name) && file.type !== "text/csv") {
      setError("Tylko .csv");
      return;
    }
    if (file.size > MAX_SIZE) {
      setError("Max 50 MB");
      return;
    }
    onFile(file);
  };

  if (status === "loading") {
    const pct = fileMeta?.size
      ? Math.min(99, Math.round((progress.bytesParsed / fileMeta.size) * 100))
      : null;
    return (
      <div className="flex items-center gap-3 min-w-0">
        <div className="flex items-center gap-2 text-sm text-muted-foreground min-w-0">
          <Loader2 className="h-4 w-4 animate-spin shrink-0" />
          <span className="truncate max-w-[180px]" title={fileMeta?.name}>
            {fileMeta?.name}
          </span>
          {pct != null && (
            <span className="tabular-nums text-xs">· {pct}%</span>
          )}
          <span className="tabular-nums text-xs">
            · {formatNumber(progress.rowsParsed)} rows
          </span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 shrink-0"
          onClick={onCancel}
          title="Anuluj"
        >
          <X className="h-3.5 w-3.5" />
        </Button>
        {pct != null && (
          <div className="w-24">
            <Progress value={pct} className="h-1" />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Button
        variant={compact ? "outline" : "default"}
        size={compact ? "sm" : "default"}
        onClick={() => inputRef.current?.click()}
        className="gap-2"
      >
        <Upload className="h-4 w-4" />
        {compact ? "Zmień CSV" : "Upload CSV"}
      </Button>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <AnimatePresence>
        {error && (
          <motion.span
            initial={{ opacity: 0, x: -4 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0 }}
            className="text-xs text-destructive"
          >
            {error}
          </motion.span>
        )}
      </AnimatePresence>
    </div>
  );
}
