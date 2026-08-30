import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import test from "node:test";
import assert from "node:assert/strict";
import { ExperimentViewV3 } from "./ExperimentViewV3.jsx";

const sampleLeads = [
  {
    id_unikalne: "PL-B-001",
    nazwa_firmy: "PowerMatic Polska Distribution",
    kraj: "Polska",
    miasto: "Warszawa",
    www: "https://powermatic.pl",
    wolumen: "duży",
    confidence_wolumen: "95%",
    rejestr_id: "KRS 0000237218",
    nip_vat: "PL9291744080",
    rok_zalozenia: 2005,
    tier: "hurtownik",
    marki_nabijarki: "PowerMatic III+, Hawk",
    powinowactwo_nabijarki: "wysoki",
    cross_sell_potential: "High",
    kategoria: "A1",
    decydent: "Marek Wiśniewski",
    email_decydent: "m.wisniewski@powermatic.pl",
    telefon: "+48 22 800 10 20",
  },
  {
    id_unikalne: "CZ-001",
    nazwa_firmy: "Hawk Rollers CZ",
    kraj: "Czechy",
    miasto: "Praga",
    www: "https://hawk.cz",
    wolumen: "średni",
    confidence_wolumen: "70%",
    rejestr_id: "CZ 12345",
    nip_vat: "CZ1234567890",
    rok_zalozenia: 2018,
    tier: "reseller",
    marki_nabijarki: "Hawk",
    powinowactwo_nabijarki: "średni",
    cross_sell_potential: "Medium",
    kategoria: "B2",
    decydent: "Tomáš Novák",
    email_decydent: "t.novak@hawk.cz",
    telefon: "+420 220 500 600",
  },
];

function withLeads(Component) {
  return <Component leads={sampleLeads} />;
}

test("ExperimentViewV3: renders the left filter rail with sections", () => {
  const html = renderToStaticMarkup(withLeads(ExperimentViewV3));
  assert.match(html, /Kraj/i);
  assert.match(html, /Tier/i);
  assert.match(html, /Wolumen/i);
  assert.match(html, /Marka/i);
});

test("ExperimentViewV3: renders rows count summary", () => {
  const html = renderToStaticMarkup(withLeads(ExperimentViewV3));
  assert.match(html, /<b[^>]*>2<\/b>\s*wynik/);
});

test("ExperimentViewV3: renders company names from leads", () => {
  const html = renderToStaticMarkup(withLeads(ExperimentViewV3));
  assert.match(html, /PowerMatic Polska Distribution/);
  assert.match(html, /Hawk Rollers CZ/);
});

test("ExperimentViewV3: shows facet counts next to filter options", () => {
  const html = renderToStaticMarkup(withLeads(ExperimentViewV3));
  assert.match(html, /Polska/);
  assert.match(html, /Czechy/);
});

test("ExperimentViewV3: hides all non-selected columns by default", () => {
  const html = renderToStaticMarkup(withLeads(ExperimentViewV3));
  assert.match(html, /Firma/);
  assert.match(html, /Miasto/);
  assert.match(html, /Kraj/);
});
