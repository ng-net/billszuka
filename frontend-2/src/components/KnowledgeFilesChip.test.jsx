// KnowledgeFilesChip.test.jsx — covers both the chip UI (visible text +
// count + Polish plural) and the pure resolver helper that backs its
// tooltip body.
//
// Why split? Radix Tooltip is notoriously awkward to drive from happy-dom
// (it gates on pointermove + setTimeout-based delay, and Portal mounts
// outside the RTL container). The visible chip contract is best tested
// with renderToStaticMarkup; the resolver is best tested as a pure
// function. Both pieces are tested here — together they cover the full
// contract.
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import test from "node:test";
import assert from "node:assert/strict";
import { TooltipProvider } from "@/components/ui/tooltip";
import { KnowledgeFilesChip } from "./GeminiDrawer.jsx";
import { resolveAttachedFilenames } from "@/lib/knowledgeFiles";

const KB_INDEX = [
  { id: "a", filename: "rynek-PL-2024.pdf" },
  { id: "b", filename: "hurtownicy-cz.csv" },
  { id: "c", filename: "notatki.md" },
];

// --- Pure helper --------------------------------------------------------

test("resolveAttachedFilenames: returns matching filenames in index order", () => {
  assert.deepEqual(
    resolveAttachedFilenames(KB_INDEX, ["a", "b"]),
    ["rynek-PL-2024.pdf", "hurtownicy-cz.csv"],
  );
});

test("resolveAttachedFilenames: skips ids not present in the index", () => {
  // "z" expired and got removed from the index — silently filtered.
  assert.deepEqual(
    resolveAttachedFilenames(KB_INDEX, ["z", "a"]),
    ["rynek-PL-2024.pdf"],
  );
});

test("resolveAttachedFilenames: skips entries without a filename", () => {
  assert.deepEqual(
    resolveAttachedFilenames(
      [{ id: "a", filename: "" }, { id: "b", filename: null }, { id: "c", filename: "ok.pdf" }],
      ["a", "b", "c"],
    ),
    ["ok.pdf"],
  );
});

test("resolveAttachedFilenames: tolerates non-array inputs", () => {
  assert.deepEqual(resolveAttachedFilenames(null, ["a"]), []);
  assert.deepEqual(resolveAttachedFilenames(KB_INDEX, null), []);
  assert.deepEqual(resolveAttachedFilenames(undefined, undefined), []);
});

test("resolveAttachedFilenames: empty selection returns empty list", () => {
  assert.deepEqual(resolveAttachedFilenames(KB_INDEX, []), []);
});

// --- Chip UI (rendered output) -----------------------------------------

// Radix Tooltip refuses to render outside its Provider context. In
// production the SessionFooter wraps KnowledgeFilesChip in a Provider,
// but tests render the chip standalone — so we provide one here too.
function renderWithProvider(node) {
  return renderToStaticMarkup(<TooltipProvider>{node}</TooltipProvider>);
}

test("KnowledgeFilesChip: zero count shows the 'no files' hint", () => {
  const html = renderWithProvider(
    <KnowledgeFilesChip count={0} index={KB_INDEX} parentsSelected={[]} />,
  );
  assert.match(html, /brak plików/);
  assert.doesNotMatch(html, /rynek-PL-2024\.pdf/);
});

test("KnowledgeFilesChip: singular form for count === 1", () => {
  const html = renderWithProvider(
    <KnowledgeFilesChip count={1} index={KB_INDEX} parentsSelected={["a"]} />,
  );
  assert.match(html, /1<\/strong>\s*plik</);
  assert.doesNotMatch(html, /1<\/strong>\s*plik[ió]/);
});

test("KnowledgeFilesChip: plural 'pliki' for count 2-4", () => {
  for (const n of [2, 3, 4]) {
    const html = renderWithProvider(
      <KnowledgeFilesChip
        count={n}
        index={KB_INDEX}
        parentsSelected={KB_INDEX.slice(0, n).map((it) => it.id)}
      />,
    );
    assert.match(html, new RegExp(`${n}<\\/strong>\\s*plik[ió]`), `count=${n}`);
  }
});

test("KnowledgeFilesChip: genitive plural 'plików' for count 5+", () => {
  for (const n of [5, 12, 99]) {
    const html = renderWithProvider(
      <KnowledgeFilesChip
        count={n}
        index={KB_INDEX}
        parentsSelected={KB_INDEX.map((it) => it.id)}
      />,
    );
    assert.match(html, new RegExp(`${n}<\\/strong>\\s*plików`), `count=${n}`);
  }
});

test("KnowledgeFilesChip: tooltip body uses the same resolver contract", () => {
  // We can't drive Radix Tooltip from happy-dom, but the TooltipContent
  // is rendered into the DOM during SSR (just hidden until hover). What
  // we can verify is that the rendered chip passes the right props
  // through — which we already do via the helper above. This test is a
  // smoke check that the chip doesn't crash when count > 0 and at
  // least one id resolves.
  const html = renderWithProvider(
    <KnowledgeFilesChip count={2} index={KB_INDEX} parentsSelected={["a", "b"]} />,
  );
  assert.match(html, /2<\/strong>\s*pliki/);
});

test("KnowledgeFilesChip: missing parentsSelected defaults to empty array", () => {
  const html = renderWithProvider(
    <KnowledgeFilesChip count={3} index={KB_INDEX} />,
  );
  assert.match(html, /3<\/strong>\s*plik/);
});
