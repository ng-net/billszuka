// JSX test runner. Loads every src test file (jsx or tsx) via
// vite-node so JSX is transformed at runtime, then drains the
// node:test queue.
//
// Each test file must set up happy-dom (or jsdom) globally if it
// needs a DOM — see QuickChips.test.jsx for the pattern.
//
// Run: node scripts/test-jsx.mjs [substring]

import { createServer } from "vite";
import { ViteNodeRunner } from "vite-node/client";
import { ViteNodeServer } from "vite-node/server";
import { installSourcemapsSupport } from "vite-node/source-map";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { writeFile, mkdir, readdir } from "node:fs/promises";
import { run } from "node:test";
import process from "node:process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const SRC = resolve(ROOT, "src");
const pattern = process.argv[2] || "";

// Write a no-op framer-motion stub into a tmp dir and alias it in
// the Vite config. The real framer-motion package is ~600 KB and
// pulls in motion-dom + raf — that's what blew V8's old-space on
// CI when 4 component tests each imported GeminiDrawer.jsx. By
// swapping it for a stub we shrink the per-test heap by roughly
// an order of magnitude.
//
// The stub preserves the HTML tag that motion.* is called with
// (motion.button → <button>, motion.div → <div>, etc.) and drops
// the animation-only props (whileTap, whileHover, initial, animate,
// exit, transition, layout, layoutId, variants, custom) so they
// don't leak into the rendered DOM and break text queries.
const TMP_DIR = resolve(ROOT, "node_modules/.vite-test-stubs");
await mkdir(TMP_DIR, { recursive: true });
await writeFile(
  resolve(TMP_DIR, "framer-motion.js"),
  [
    "import * as React from 'react';",
    "const ANIM_PROPS = ['whileTap','whileHover','whileFocus','whileDrag','whileInView',",
    "  'initial','animate','exit','transition','layout','layoutId','variants','custom',",
    "  'transformValues','onAnimationStart','onAnimationComplete','onUpdate'];",
    "function makeMotion(tag) {",
    "  return React.forwardRef(function Motion({ children, ...rest }, ref) {",
    "    const clean = {};",
    "    for (const k in rest) if (!ANIM_PROPS.includes(k)) clean[k] = rest[k];",
    "    return React.createElement(tag, { ...clean, ref }, children);",
    "  });",
    "}",
    "export const motion = new Proxy({}, { get: (_t, tag) => makeMotion(String(tag)) });",
    "export const AnimatePresence = ({ children }) => React.createElement(React.Fragment, null, children);",
    "export const LayoutGroup = ({ children }) => React.createElement(React.Fragment, null, children);",
    "export const useAnimation = () => ({ start: () => {}, stop: () => {}, set: () => {} });",
    "export const useInView = () => false;",
    "export const useMotionValue = (v) => ({ get: () => v, set: () => {} });",
    "export const useTransform = () => ({ get: () => 0, set: () => {} });",
    "export const useReducedMotion = () => false;",
    "export const animate = () => ({ stop: () => {} });",
    "export default { motion, AnimatePresence };",
  ].join("\n"),
);

async function listTestFiles(dir) {
  const out = [];
  let entries;
  try { entries = await readdir(dir, { withFileTypes: true }); }
  catch { return out; }
  for (const e of entries) {
    const full = resolve(dir, e.name);
    if (e.isDirectory()) out.push(...(await listTestFiles(full)));
    else if (e.name.endsWith(".test.jsx") || e.name.endsWith(".test.tsx")) {
      if (!pattern || full.includes(pattern)) out.push(full);
    }
  }
  return out;
}

const files = await listTestFiles(SRC);
if (files.length === 0) {
  console.log("# No JSX test files found (looking under src)");
  process.exit(0);
}

console.log(`# Loading ${files.length} JSX test file(s) via vite-node:`);
for (const f of files) console.log(`#   ${f.replace(ROOT + "/", "")}`);

const server = await createServer({
  root: ROOT,
  server: { middlewareMode: true },
  appType: "custom",
  resolve: {
    alias: [
      { find: /^framer-motion$/, replacement: resolve(TMP_DIR, "framer-motion.js") },
    ],
  },
  optimizeDeps: { noDiscovery: true, include: [] },
  logLevel: "warn",
});
await server.pluginContainer.buildStart();

const node = new ViteNodeServer(server);
installSourcemapsSupport({ getSourceMap: (s) => node.getSourceMap(s) });
const runner = new ViteNodeRunner({
  root: server.config.root,
  base: server.config.base,
  fetchModule: (id) => node.fetchModule(id),
  resolveId: (id, importer) => node.resolveId(id, importer),
});

for (const file of files) {
  await runner.executeFile(file);
}

await server.close();

// Per-test timeout (ms) — honored by Node's node:test runner. If a
// test body hangs (e.g., unresolved Promise, sync infinite loop), the
// test fails after this many ms instead of waiting the full job cap.
// Override with TEST_TIMEOUT_MS env var for local debugging.
const PER_TEST_TIMEOUT = Number(process.env.TEST_TIMEOUT_MS) || 30000;

run({ files: files.map((f) => f), timeout: PER_TEST_TIMEOUT }).on("end", () => {
  process.exit(process.exitCode || 0);
});