import test from "node:test";
import assert from "node:assert/strict";
import { loadPrefs, savePrefs } from "./prefs.js";

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