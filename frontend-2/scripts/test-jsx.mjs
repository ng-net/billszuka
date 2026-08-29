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
import { readdir } from "node:fs/promises";
import { run } from "node:test";
import process from "node:process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const SRC = resolve(ROOT, "src");
const pattern = process.argv[2] || "";

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

run({ files: files.map((f) => f) }).on("end", () => {
  process.exit(process.exitCode || 0);
});