import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn, formatNumber } from "@/lib/utils";

const MAX_SIZE = 50 * 1024 * 1024;

export function UploadButton({
  onFile,
  status = "idle",
  progress = { bytesParsed: 0, rowsParsed: 0 },
  fileMeta = null,
  onCancel,
  label = "Upload",
  primary = true,
  className,
}) {
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const handleFiles = (files) => {
    setError(null);
    const file = files?.[0];
    if (!file) return;
    if (!/\.csv$/i.test(file.name) && file.type !== "text/csv") {
      setError("Tylko pliki .csv");
      return;
    }
    if (file.size > MAX_SIZE) {
      setError("Maks. 50 MB");
      return;
    }
    onFile?.(file);
  };

  if (status === "loading") {
    const pct = fileMeta?.size
      ? Math.min(99, Math.round(((progress?.bytesParsed || 0) / fileMeta.size) * 100))
      : null;
    return (
      <div className="flex items-center gap-2 min-w-0">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground min-w-0">
          <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0 text-foreground" />
          <span className="truncate max-w-[120px] font-medium text-foreground" title={fileMeta?.name}>
            {fileMeta?.name || "Ładowanie…"}
          </span>
          {pct != null && (
            <span className="tabular-nums">· {pct}%</span>
          )}
          {progress?.rowsParsed > 0 && (
            <span className="tabular-nums hidden md:inline">
              · {formatNumber(progress.rowsParsed)} wierszy
            </span>
          )}
        </div>
        {onCancel && (
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 shrink-0 text-muted-foreground hover:text-foreground"
            onClick={onCancel}
            title="Anuluj"
          >
            <X className="h-3.5 w-3.5" />
          </Button>
        )}
        {pct != null && (
          <div className="w-16 hidden lg:block">
            <Progress value={pct} className="h-1" />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1.5">
      <Button
        variant={primary ? "default" : "outline"}
        size="sm"
        onClick={() => inputRef.current?.click()}
        aria-label={label}
        title={label}
        className={cn(
          "gap-1.5 h-8 px-3 text-xs font-semibold",
          primary && "bg-black text-white hover:bg-black/85 dark:bg-white dark:text-black dark:hover:bg-white/90 shadow-xs",
          className
        )}
      >
        <Upload className="h-3.5 w-3.5 shrink-0" />
        <span>{label}</span>
      </Button>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        className="hidden"
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
      />
      <AnimatePresence>
        {error && (
          <motion.span
            initial={{ opacity: 0, x: -4 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0 }}
            className="text-[11px] text-destructive font-medium"
          >
            {error}
          </motion.span>
        )}
      </AnimatePresence>
    </div>
  );
}

