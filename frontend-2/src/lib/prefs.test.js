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
  clearPrefs();
  const prefs = loadPrefs();
  assert.equal(prefs.activeTab, "table");
  assert.equal(prefs.density, "compact");
  assert.equal(prefs.theme, "system");
  assert.deepEqual(prefs.sortStack, []);
  assert.deepEqual(prefs.filters, {});
});

test("prefs: persists and restores activeTab and customized settings", () => {
  clearPrefs();
  savePrefs({
    activeTab: "analytics",
    density: "comfortable",
    theme: "dark",
    columnOrder: ["id_unikalne", "nazwa_firmy"],
    columnVisibility: { notatki: false },
    sortStack: [{ id: "nazwa_firmy", desc: false }],
    filters: { kraj: "PL" },
  });

  const restored = loadPrefs();
  assert.equal(restored.activeTab, "analytics");
  assert.equal(restored.density, "comfortable");
  assert.equal(restored.theme, "dark");
  assert.deepEqual(restored.columnOrder, ["id_unikalne", "nazwa_firmy"]);
  assert.deepEqual(restored.columnVisibility, { notatki: false });
  assert.deepEqual(restored.sortStack, [{ id: "nazwa_firmy", desc: false }]);
  assert.deepEqual(restored.filters, { kraj: "PL" });
});
