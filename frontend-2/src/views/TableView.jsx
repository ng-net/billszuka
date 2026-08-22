import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { RawTable } from "@/raw-table/RawTable";

/**
 * TableView — wraps the existing RawTable with a header tab strip that the
 * App-level shell can render alongside. Keeps its own CSV loading state —
 * the RawTable already manages dropzone + sample.csv loading.
 *
 * The wrapping <div> is mostly a no-op so the parent shell can apply the
 * "active" animation when this view is visible.
 */
export function TableView() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className="h-full"
    >
      {mounted ? (
        <RawTable />
      ) : (
        <div className="flex h-full items-center justify-center text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      )}
    </motion.div>
  );
}