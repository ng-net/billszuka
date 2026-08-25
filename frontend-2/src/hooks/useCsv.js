import { useState, useRef, useCallback, useEffect } from "react";
import { parseCsvFile, parseCsvUrl } from "@/lib/csv";

/**
 * Hook: load + parse CSV with progress + cancel.
 * State: { status: "idle" | "loading" | "ready" | "error", columns, rows, schema, parseTimeMs, error, progress }
 *
 * Enforces a minimum display time for the loading state so fast parses
 * (e.g. 209 KB sample) don't flash by in 100ms — feels intentional.
 */
const MIN_LOADING_MS = 500;

export function useCsv({ minLoadingMs = MIN_LOADING_MS } = {}) {
  const [status, setStatus] = useState("idle");
  const [data, setData] = useState({ columns: [], rows: [], schema: [] });
  const [parseTimeMs, setParseTimeMs] = useState(0);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState({ rowsParsed: 0, bytesParsed: 0 });
  const [fileMeta, setFileMeta] = useState(null); // { name, size }
  const [startedAt, setStartedAt] = useState(null);
  const abortRef = useRef(null);

  const reset = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    setStatus("idle");
    setData({ columns: [], rows: [], schema: [] });
    setParseTimeMs(0);
    setError(null);
    setProgress({ rowsParsed: 0, bytesParsed: 0 });
    setFileMeta(null);
    setStartedAt(null);
  }, []);

  const loadFile = useCallback(async (file) => {
    if (!file) return;
    if (abortRef.current) abortRef.current.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    setStatus("loading");
    setError(null);
    setProgress({ rowsParsed: 0, bytesParsed: 0 });
    setFileMeta({ name: file.name, size: file.size });
    setStartedAt(performance.now());
    const start = performance.now();
    try {
      const result = await parseCsvFile(file, {
        onProgress: (p) => setProgress(p),
        signal: ac.signal,
      });
      if (ac.signal.aborted) return;
      const elapsed = performance.now() - start;
      if (elapsed < minLoadingMs) {
        await new Promise((r) => setTimeout(r, minLoadingMs - elapsed));
      }
      if (ac.signal.aborted) return;
      setData({ columns: result.columns, rows: result.rows, schema: result.schema });
      setParseTimeMs(result.parseTimeMs);
      setStatus("ready");
    } catch (e) {
      if (e?.name === "AbortError") {
        setStatus("idle");
        setFileMeta(null);
        setStartedAt(null);
        return;
      }
      setError(e?.message || String(e));
      setStatus("error");
    }
  }, [minLoadingMs]);

  const loadUrl = useCallback(async (url, displayName, sizeHint) => {
    if (abortRef.current) abortRef.current.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    setStatus("loading");
    setError(null);
    setProgress({ rowsParsed: 0, bytesParsed: 0 });
    setFileMeta({ name: displayName || url, size: sizeHint || 0 });
    setStartedAt(performance.now());
    const start = performance.now();
    try {
      const result = await parseCsvUrl(url, {
        onProgress: (p) => setProgress(p),
        signal: ac.signal,
      });
      if (ac.signal.aborted) return;
      const elapsed = performance.now() - start;
      if (elapsed < minLoadingMs) {
        await new Promise((r) => setTimeout(r, minLoadingMs - elapsed));
      }
      if (ac.signal.aborted) return;
      setData({ columns: result.columns, rows: result.rows, schema: result.schema });
      setParseTimeMs(result.parseTimeMs);
      setStatus("ready");
    } catch (e) {
      if (e?.name === "AbortError") {
        setStatus("idle");
        setFileMeta(null);
        setStartedAt(null);
        return;
      }
      setError(e?.message || String(e));
      setStatus("error");
    }
  }, [minLoadingMs]);

  const cancel = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
  }, []);

  // cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, []);

  return { status, ...data, parseTimeMs, error, progress, fileMeta, startedAt, loadFile, loadUrl, reset, cancel };
}
