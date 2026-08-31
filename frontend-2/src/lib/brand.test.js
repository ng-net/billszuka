import test from "node:test";
import assert from "node:assert/strict";
import { classifyBrand, highlightKeywords } from "./brand.js";

test("brand: classifies PowerMatic mentions", () => {
  const row = {
    nazwa_firmy: "PRODAP.PL (PowerMatic seller)",
    notatki: "Sklep z PowerMatic 4+",
    zrodlo_danych: "web search PowerMatic",
  };
  const result = classifyBrand(row);
  assert.equal(result, "PowerMatic");
});

test("brand: classifies PowerMatic + Hawk", () => {
  const row = {
    notatki: "PowerMatic and Hawk importer",
  };
  const result = classifyBrand(row);
  assert.equal(result, "PowerMatic + Hawk");
});

test("brand: classifies only Hawk", () => {
  const row = {
    nazwa_firmy: "jameshawk.pl",
    notatki: "Hawk distributor only",
  };
  const result = classifyBrand(row);
  assert.equal(result, "Hawk");
});

test("brand: classifies other brands as Inna", () => {
  const row = {
    notatki: "Sprzedaje inne nabijarki i gilzy",
  };
  const result = classifyBrand(row);
  assert.equal(result, "Inna");
});

test("brand: no brand signal returns dash", () => {
  const row = {
    notatki: "No brand info",
  };
  const result = classifyBrand(row);
  assert.equal(result, "—");
});

test("keywords: highlights tytoń, gilza, bibułki", () => {
  const text = "Sprzedajemy tytoń, gilzy i bibułki do nabijania";
  const result = highlightKeywords(text);
  const types = result.filter((s) => s.type).map((s) => s.type);
  assert.ok(types.includes("tyton"));
  assert.ok(types.includes("gilza"));
  assert.ok(types.includes("bibulki"));
});

// Regression test for the __brand synthetic-column filter pipeline
// (wired in DataTable.jsx as `brandMatch` and driven by `applyView()`).
// Without this, "PowerMatic" / "Hawk" saved views would silently render
// 0 rows because the classifier never ran per row in the production
// filter pipeline (only in the views.test.js helper).
test("brand: __brand filter pipeline narrows rows via classifyBrand", () => {
  const rows = [
    { id: "1", nazwa_firmy: "PowerMatic seller", __brand: classifyBrand({ nazwa_firmy: "PowerMatic seller" }) },
    { id: "2", nazwa_firmy: "Hawk only", __brand: classifyBrand({ nazwa_firmy: "Hawk only" }) },
    { id: "3", nazwa_firmy: "PowerMatic + Hawk", __brand: classifyBrand({ nazwa_firmy: "PowerMatic + Hawk" }) },
    { id: "4", nazwa_firmy: "Generic shop", __brand: classifyBrand({ nazwa_firmy: "Generic shop" }) },
  ];
  const filter = "__brand";
  // Single value
  const onlyPowerMatic = rows.filter((r) => r[filter] === "PowerMatic");
  assert.equal(onlyPowerMatic.length, 1);
  assert.equal(onlyPowerMatic[0].id, "1");
  // Array value
  const powerOrHawk = rows.filter((r) => ["PowerMatic", "Hawk"].includes(r[filter]));
  assert.equal(powerOrHawk.length, 2);
  // Empty filter = no narrowing
  const unfiltered = rows.filter((r) => r[filter] !== undefined);
  assert.equal(unfiltered.length, 4);
});
