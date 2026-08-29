import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileSpreadsheet, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn, formatNumber } from "@/lib/utils";

const MAX_SIZE = 50 * 1024 * 1024; // 50 MB

export function EmptyState({ onFile, onLoadSample, hasSample = false, sampleSize = 0 }) {
  const [isDragging, setIsDragging] = useState(false);
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
      setError(`Plik za duży (${formatNumber(file.size / 1024 / 1024)} MB). Maks 50 MB.`);
      return;
    }
    onFile(file);
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100dvh-3.5rem)] p-6">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        onDragEnter={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setIsDragging(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={cn(
          "relative w-full max-w-2xl rounded-2xl border-2 border-dashed p-6 transition-all duration-200 sm:p-12",
          isDragging
            ? "border-primary bg-accent scale-[1.01]"
            : "border-border bg-zinc-100/60 dark:bg-zinc-900/40 hover:border-muted-foreground/40"
        )}
      >
        <AnimatePresence>
          {isDragging && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 flex items-center justify-center rounded-2xl bg-background/80 backdrop-blur-sm pointer-events-none"
            >
              <div className="text-center">
                <Upload className="h-12 w-12 mx-auto text-primary mb-2" />
                <p className="text-lg font-medium">Upuść, żeby załadować</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="text-center">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-muted mb-6">
            <FileSpreadsheet className="h-8 w-8 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight mb-2">
            Wgraj CSV
          </h1>
          <p className="text-sm text-muted-foreground mb-8 max-w-md mx-auto">
            Przeciągnij i upuść albo wybierz plik
          </p>

          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Button
              size="lg"
              onClick={() => inputRef.current?.click()}
              className="gap-2"
            >
              <Upload className="h-4 w-4" />
              Wybierz plik
            </Button>
            {hasSample && (
              <Button
                size="lg"
                variant="outline"
                onClick={onLoadSample}
                className="gap-2"
              >
                <Sparkles className="h-4 w-4" />
                Załaduj master.csv
              </Button>
            )}
          </div>

          {error && (
            <motion.p
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 text-sm text-destructive flex items-center justify-center gap-1.5"
            >
              <X className="h-3.5 w-3.5" />
              {error}
            </motion.p>
          )}

          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>
      </motion.div>
    </div>
  );
}
