import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import test from "node:test";
import assert from "node:assert/strict";
import { CollapsibleFilters } from "./CollapsibleFilters.jsx";

const sample = {
  kraj: ["PL", "CZ", "SK"],
  marki_nabijarki: ["PowerMatic", "Hawk", "Inna"],
  tier: ["hurtownik", "reseller", "detalista"],
};

test("CollapsibleFilters: renders expanded by default with all sections", () => {
  const html = renderToStaticMarkup(
    <CollapsibleFilters groups={sample} filters={{}} onToggle={() => {}} />
  );
  assert.match(html, /Kraj/);
  assert.match(html, /Marka/);
  assert.match(html, /Rola/);
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
  assert.match(html, /Kraj/);
  assert.doesNotMatch(html, /PL/);
});

test("CollapsibleFilters: renders section counts in collapsed mode", () => {
  const html = renderToStaticMarkup(
    <CollapsibleFilters
      groups={sample}
      filters={{ kraj: ["PL"] }}
      onToggle={() => {}}
      collapsed={true}
    />
  );
  assert.match(html, /Kraj/);
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
