import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FileSpreadsheet, X, Gauge, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { formatNumber } from "@/lib/utils";

/**
 * Big loading state with circular % progress, stats, and cancel.
 * Shows for at least `minDisplayMs` so fast parses don't flash by.
 */
export function LoadingState({
  fileName,
  fileSize,
  progress,
  onCancel,
  minDisplayMs = 500,
  startedAt,
}) {
  const [minTimePassed, setMinTimePassed] = useState(false);
  const [now, setNow] = useState(() => performance.now());

  // Tick "now" at 10 Hz (100 ms). RAF at 60 Hz caused a re-render every
  // frame for a label that only changes at second resolution — 6x the work
  // for no perceivable difference.
  useEffect(() => {
    const id = setInterval(() => setNow(performance.now()), 100);
    return () => clearInterval(id);
  }, []);

  // Min display time
  useEffect(() => {
    const t = setTimeout(() => setMinTimePassed(true), minDisplayMs);
    return () => clearTimeout(t);
  }, [minDisplayMs]);

  // Derived stats
  const pct = fileSize
    ? Math.min(100, Math.round((progress.bytesParsed / fileSize) * 100))
    : 0;
  const elapsedMs = startedAt ? now - startedAt : 0;
  const rowsPerSec = elapsedMs > 100 ? (progress.rowsParsed / (elapsedMs / 1000)) : 0;
  const remainingRows = fileSize && progress.rowsParsed
    ? Math.max(0, Math.round((fileSize * (progress.rowsParsed / Math.max(1, progress.bytesParsed))) - progress.rowsParsed))
    : 0;
  const etaSec = rowsPerSec > 0 ? remainingRows / rowsPerSec : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="flex items-center justify-center min-h-[calc(100vh-3.5rem)] p-6"
    >
      <div className="w-full max-w-sm text-center">
        <CircularProgress value={pct} />

        <motion.h2
          key={fileName}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-lg font-semibold tracking-tight mt-6 truncate"
          title={fileName}
        >
          {fileName || "Ładowanie…"}
        </motion.h2>

        <p className="text-xs text-muted-foreground mt-1 tabular-nums">
          {fileSize ? `${formatBytes(fileSize)} · ${pct}%` : "Inicjalizacja…"}
        </p>

        <div className="mt-4">
          <Progress value={pct} className="h-1" />
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
          <Stat
            icon={FileSpreadsheet}
            label="Wiersze"
            value={formatNumber(progress.rowsParsed)}
          />
          <Stat
            icon={Gauge}
            label="Prędkość"
            value={rowsPerSec > 0 ? `${Math.round(rowsPerSec)}/s` : "—"}
          />
          <Stat
            icon={Clock}
            label="Pozostało"
            value={etaSec > 0.1 ? `~${etaSec.toFixed(1)}s` : minTimePassed ? "✓" : "…"}
          />
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={onCancel}
          className="mt-6 gap-1.5 text-muted-foreground"
        >
          <X className="h-3.5 w-3.5" />
          Anuluj
        </Button>
      </div>
    </motion.div>
  );
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="rounded-lg border bg-card/50 px-2 py-2">
      <div className="flex items-center justify-center gap-1 text-[10px] text-muted-foreground uppercase tracking-wider">
        <Icon className="h-2.5 w-2.5" />
        {label}
      </div>
      <div className="text-sm font-medium tabular-nums mt-0.5">{value}</div>
    </div>
  );
}

function CircularProgress({ value, size = 120, strokeWidth = 8 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value / 100);

  return (
    <div className="relative inline-block" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90 block">
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-muted/30"
        />
        {/* Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="text-primary transition-[stroke-dashoffset] duration-200 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          key={Math.round(value / 10)}
          initial={{ opacity: 0.5, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-2xl font-semibold tabular-nums"
        >
          {Math.round(value)}
          <span className="text-base text-muted-foreground">%</span>
        </motion.span>
      </div>
    </div>
  );
}

function formatBytes(bytes) {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}
