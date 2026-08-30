/**
 * Resolve the set of selected knowledge-base file ids to a list of
 * filenames, skipping unknown ids. Used by the KnowledgeFilesChip in
 * GeminiDrawer to render the "you have N files attached" pill.
 *
 * Kept in lib/ (not in GeminiDrawer.jsx) so React Fast Refresh works
 * and so unit tests don't have to import the whole drawer component
 * (which transitively pulls in framer-motion + Radix Tooltip).
 */
export function resolveAttachedFilenames(index, parentsSelected) {
  if (!Array.isArray(index) || !Array.isArray(parentsSelected)) return [];
  const sel = new Set(parentsSelected);
  return index.filter((it) => sel.has(it.id)).map((it) => it.filename).filter(Boolean);
}
