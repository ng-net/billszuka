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
