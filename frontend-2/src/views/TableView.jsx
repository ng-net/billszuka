import { forwardRef } from "react";
import { motion } from "framer-motion";
import { RawTable } from "@/raw-table/RawTable";

/**
 * TableView — wraps the existing RawTable with a header tab strip that the
 * App-level shell can render alongside. Keeps its own CSV loading state —
 * the RawTable already manages dropzone + sample.csv loading.
 *
 * Forwards an imperative handle so the App-level navbar (e.g. ⌘K button
 * next to the gear) can open the command palette without prop-drilling
 * its visibility state through here. RawTable is already behind
 * React.lazy() + Suspense at the App level, so no local mount gate is
 * needed here — by the time this renders, the chunk is loaded.
 */
export const TableView = forwardRef(function TableView(_props, ref) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className="h-full"
    >
      <RawTable ref={ref} />
    </motion.div>
  );
});