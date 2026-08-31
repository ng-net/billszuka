import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import test from "node:test";
import assert from "node:assert/strict";
import { CollapsibleFilters } from "./CollapsibleFilters.jsx";

// Note: "kraj" (country) is intentionally not in `sample` — country column
// has no filtering option in the UI. Tests use marki_nabijarki/tier instead.
const sample = {
  marki_nabijarki: ["PowerMatic", "Hawk", "Inna"],
  tier: ["hurtownik", "reseller", "detalista"],
};

test("CollapsibleFilters: renders expanded by default with all sections", () => {
  const html = renderToStaticMarkup(
    <CollapsibleFilters groups={sample} filters={{}} onToggle={() => {}} />
  );
  assert.match(html, /Marka/);
  assert.match(html, /Rola/);
  // Country filter must NOT be rendered.
  assert.doesNotMatch(html, /Kraj/);
});

test("CollapsibleFilters: shows a collapse button with chevron", () => {
  const html = renderToStaticMarkup(
    <CollapsibleFilters groups={sample} filters={{}} onToggle={() => {}} />
  );
  assert.match(html, /Zwiń|Ukryj|Zamknij/i);
});

test("CollapsibleFilters: when collapsed only shows section headers", () => {
  const html = renderToStaticMarkup(
    <CollapsibleFilters
      groups={sample}
      filters={{}}
      onToggle={() => {}}
      collapsed={true}
    />
  );
  assert.match(html, /Marka/);
  assert.doesNotMatch(html, /PowerMatic/);
});

test("CollapsibleFilters: renders section counts in collapsed mode", () => {
  const html = renderToStaticMarkup(
    <CollapsibleFilters
      groups={sample}
      filters={{ marki_nabijarki: ["PowerMatic"] }}
      onToggle={() => {}}
      collapsed={true}
    />
  );
  assert.match(html, /Marka/);
  assert.match(html, /1/);
});

test("CollapsibleFilters: clicking collapse button fires onToggleCollapse", () => {
  let called = 0;
  const html = renderToStaticMarkup(
    <CollapsibleFilters
      groups={sample}
      filters={{}}
      onToggle={() => {}}
      onToggleCollapse={() => called++}
    />
  );
  assert.match(html, /Zwiń|Ukryj|Zamknij|Rozwiń/i);
  assert.equal(called, 0);
});

test("CollapsibleFilters: country filter is not exposed even if data contains kraj", () => {
  // If a caller passes kraj in groups (e.g. legacy code), the UI should still
  // not render the Kraj filter section.
  const html = renderToStaticMarkup(
    <CollapsibleFilters
      groups={{ ...sample, kraj: ["PL", "CZ"] }}
      filters={{}}
      onToggle={() => {}}
    />
  );
  assert.doesNotMatch(html, /Kraj/);
});
