import { forwardRef, useEffect, useImperativeHandle, useState } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { RawTable } from "@/raw-table/RawTable";

/**
 * TableView — wraps the existing RawTable with a header tab strip that the
 * App-level shell can render alongside. Keeps its own CSV loading state —
 * the RawTable already manages dropzone + sample.csv loading.
 *
 * Forwards an imperative handle so the App-level navbar (e.g. ⌘K button
 * next to the gear) can open the command palette without prop-drilling
 * its visibility state through here.
 */
export const TableView = forwardRef(function TableView(_props, ref) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  // Imperative handle so the App navbar can trigger the command palette.
  // The actual palette lives inside RawTable (it needs table context), so
  // we just forward an `openCommandPalette` method up.
  useImperativeHandle(ref, () => ({}), []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className="h-full"
    >
      {mounted ? (
        <RawTable ref={ref} />
      ) : (
        <div className="flex h-full items-center justify-center text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      )}
    </motion.div>
  );
});