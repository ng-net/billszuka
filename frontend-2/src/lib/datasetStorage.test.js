// datasetStorage.test.js — exercises the master.csv cache helpers added
// alongside the existing custom-dataset storage.

// _setup.js lives under raw-table/components — relative import so node:test
// finds the happy-dom globals it installs. We then install an in-memory
// IndexedDB shim on top — happy-dom's IDB doesn't actually persist writes
// reliably, and datasetStorage.js never had tests before because of that.
import "../raw-table/components/_setup.js";
import { installIdbMock } from "./idb-mock.js";
installIdbMock();

import test from "node:test";
import assert from "node:assert/strict";
import {
  saveMasterCache,
  getMasterCache,
  clearMasterCache,
  clearCustomDataset,
  getCustomDataset,
  saveCustomDataset,
} from "./datasetStorage.js";

// datasetStorage.js falls back to getActiveProfile() when no profileId
// is passed; under happy-dom localStorage is empty, so without a stub
// every test would collapse into the "default" bucket and stomp on each
// other. Mock localStorage so each test gets an isolated key.
const mockStorage = new Map();
globalThis.localStorage = {
  getItem: (k) => (mockStorage.has(k) ? mockStorage.get(k) : null),
  setItem: (k, v) => mockStorage.set(k, String(v)),
  removeItem: (k) => mockStorage.delete(k),
  clear: () => mockStorage.clear(),
};

function payload(overrides = {}) {
  return {
    columns: [{ id: "kraj" }, { id: "nazwa" }],
    rows: [{ kraj: "PL", nazwa: "ACME" }],
    schema: [],
    parseTimeMs: 12,
    size: 225319,
    ...overrides,
  };
}

// IndexedDB state persists across tests in the same process — each test
// opens a fresh DB but the STORE is shared. We rely on per-test profileId
// keys to avoid bleed-through, plus we delete on teardown.

test("saveMasterCache then getMasterCache round-trips rows + columns", async () => {
  await clearMasterCache("test_profile_a");
  await saveMasterCache("test_profile_a", payload());
  const restored = await getMasterCache("test_profile_a");
  assert.ok(restored, "expected cache hit");
  assert.equal(restored.rows.length, 1);
  assert.equal(restored.rows[0].nazwa, "ACME");
  assert.equal(restored.columns.length, 2);
  assert.equal(restored.size, 225319);
});

test("getMasterCache returns null when nothing has been saved", async () => {
  await clearMasterCache("test_profile_empty");
  const got = await getMasterCache("test_profile_empty");
  assert.equal(got, null);
});

test("clearMasterCache removes only the master cache, not custom datasets", async () => {
  // Seed both kinds of data under the same profile
  await saveMasterCache("test_profile_b", payload());
  await saveCustomDataset("test_profile_b", payload({ rows: [{ kraj: "CZ", nazwa: "Foo" }] }));

  await clearMasterCache("test_profile_b");

  assert.equal(await getMasterCache("test_profile_b"), null, "master cache should be cleared");
  const custom = await getCustomDataset("test_profile_b");
  assert.ok(custom, "custom dataset should still exist");
  assert.equal(custom.rows[0].nazwa, "Foo");
});

test("clearCustomDataset wipes the master cache too (logout semantics)", async () => {
  // Marceli's request: logging out should clear every cached dataset so
  // the next session starts from a clean slate (no stale rows leaking
  // through to a different profile or a re-login).
  await saveMasterCache("test_profile_c", payload());
  await saveCustomDataset("test_profile_c", payload());

  await clearCustomDataset("test_profile_c");

  assert.equal(await getMasterCache("test_profile_c"), null);
  assert.equal(await getCustomDataset("test_profile_c"), null);
});

test("different profiles get independent caches", async () => {
  await saveMasterCache("test_profile_d1", payload({ rows: [{ kraj: "PL", nazwa: "D1" }] }));
  await saveMasterCache("test_profile_d2", payload({ rows: [{ kraj: "PL", nazwa: "D2" }] }));

  const a = await getMasterCache("test_profile_d1");
  const b = await getMasterCache("test_profile_d2");
  assert.equal(a.rows[0].nazwa, "D1");
  assert.equal(b.rows[0].nazwa, "D2");
});