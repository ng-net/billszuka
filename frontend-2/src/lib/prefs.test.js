import test from "node:test";
import assert from "node:assert/strict";
import { loadPrefs, savePrefs, clearPrefs } from "./prefs.js";

// Mock localStorage for Node.js test environment
const mockStorage = new Map();
global.localStorage = {
  getItem: (k) => mockStorage.get(k) ?? null,
  setItem: (k, v) => mockStorage.set(k, String(v)),
  removeItem: (k) => mockStorage.delete(k),
  clear: () => mockStorage.clear(),
};

test("prefs: loads default preferences when empty", () => {
  mockStorage.clear();
  const prefs = loadPrefs();
  assert.equal(prefs.activeTab, "table");
  assert.equal(prefs.density, "compact");
  assert.equal(prefs.theme, "system");
  assert.deepEqual(prefs.sortStack, []);
  assert.deepEqual(prefs.filters, {});
  assert.deepEqual(prefs.savedViews, []);
  assert.equal(prefs.activeView, null);
});

test("prefs: supports savedViews and activeView (v2)", () => {
  mockStorage.clear();
  const views = [
    { id: "powermatic", name: "PowerMatic", filters: { brand: "PowerMatic" } },
  ];

  savePrefs({
    savedViews: views,
    activeView: "powermatic",
  });

  const restored = loadPrefs();
  assert.equal(restored.savedViews.length, 1);
  assert.equal(restored.savedViews[0].id, "powermatic");
  assert.equal(restored.activeView, "powermatic");
  assert.equal(restored.version, 2);
});

test("prefs: migrates legacy v1 prefs to v2 (adds savedViews and activeView)", () => {
  mockStorage.clear();
  // Simulate old v1 prefs (no version or version 1, missing new fields)
  mockStorage.set(
    "czat-table.prefs.v2",
    JSON.stringify({
      activeTab: "analytics",
      density: "comfortable",
      theme: "dark",
      columnOrder: ["kraj", "nazwa_firmy"],
      columnVisibility: { wolumen: false },
      sortStack: [{ id: "wolumen", desc: true }],
      filters: { kraj: ["PL", "CZ"] },
      lastFocusedColumn: "nip_vat",
    })
  );

  const restored = loadPrefs();
  assert.equal(restored.version, 2);
  assert.equal(restored.activeTab, "analytics");
  assert.equal(restored.density, "comfortable");
  assert.equal(restored.theme, "dark");
  assert.deepEqual(restored.columnOrder, ["kraj", "nazwa_firmy"]);
  assert.deepEqual(restored.columnVisibility, { wolumen: false });
  assert.deepEqual(restored.sortStack, [{ id: "wolumen", desc: true }]);
  assert.deepEqual(restored.filters, { kraj: ["PL", "CZ"] });
  assert.equal(restored.lastFocusedColumn, "nip_vat");
  // New v2 fields get defaults
  assert.deepEqual(restored.savedViews, []);
  assert.equal(restored.activeView, null);
});

test("prefs: clearPrefs removes the key", () => {
  mockStorage.clear();
  savePrefs({ activeTab: "analytics" });
  assert.ok(mockStorage.has("czat-table.prefs.v2"));
  clearPrefs();
  assert.ok(!mockStorage.has("czat-table.prefs.v2"));
});