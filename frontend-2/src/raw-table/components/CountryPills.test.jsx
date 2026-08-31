// CountryPills.test.jsx — component tests for the country pill bar.
import "./_setup.js";
import test from "node:test";
import assert from "node:assert/strict";
import { afterEach } from "node:test";

const React = (await import("react")).default;
const { render, screen, cleanup, fireEvent } = await import("@testing-library/react");
const { CountryPills } = await import("./CountryPills.jsx");

afterEach(() => cleanup());

const ROWS = [
  { id: "PL-A-001", kraj: "PL" },
  { id: "PL-B-002", kraj: "PL" },
  { id: "PL-B-003", kraj: "PL" },
  { id: "CZ-B-001", kraj: "CZ" },
  { id: "CZ-B-002", kraj: "CZ" },
  { id: "SK-B-001", kraj: "SK" },
  { id: "RO-B-001", kraj: "RO" },
  { id: "DE-A-001", kraj: "DE" }, // not in canonical 13
];

test("CountryPills: renders Wszystkie + one pill per known ISO", () => {
  render(React.createElement(CountryPills, { rows: ROWS }));
  // Wszystkie pill always present
  assert.ok(screen.getByText(/Wszystkie/));
  // Canonical countries from COUNTRIES list
  for (const iso of ["PL", "CZ", "SK", "RO", "LT", "LV", "EE", "FR", "MD", "BG", "SI", "HR", "RS"]) {
    assert.ok(screen.getAllByText(iso).length > 0, `pill for ${iso} should exist`);
  }
});

test("CountryPills: shows row count for each country pill", () => {
  render(React.createElement(CountryPills, { rows: ROWS }));
  const plButton = screen.getByText("PL").closest("button");
  assert.ok(plButton, "PL pill exists");
  assert.match(plButton.textContent, /3/, "PL count = 3");
  const czButton = screen.getByText("CZ").closest("button");
  assert.match(czButton.textContent, /2/, "CZ count = 2");
});

test("CountryPills: shows total row count on Wszystkie pill", () => {
  render(React.createElement(CountryPills, { rows: ROWS }));
  const wszystkie = screen.getByText(/Wszystkie/).closest("button");
  assert.match(wszystkie.textContent, /8/, "Wszystkie count = 8 total rows");
});

test("CountryPills: Wszystkie pill is active when activeIso is null", () => {
  render(React.createElement(CountryPills, { rows: ROWS, activeIso: null }));
  const wszystkie = screen.getByText(/Wszystkie/).closest("button");
  assert.equal(wszystkie.getAttribute("aria-pressed"), "true");
});

test("CountryPills: active pill has aria-pressed=true", () => {
  render(React.createElement(CountryPills, { rows: ROWS, activeIso: "CZ" }));
  const czButton = screen.getByText("CZ").closest("button");
  assert.equal(czButton.getAttribute("aria-pressed"), "true");
  // others should be false
  const plButton = screen.getByText("PL").closest("button");
  assert.equal(plButton.getAttribute("aria-pressed"), "false");
});

test("CountryPills: clicking a pill calls onSelect with the ISO", () => {
  let selected = null;
  render(React.createElement(CountryPills, {
    rows: ROWS,
    activeIso: null,
    onSelect: (iso) => { selected = iso; },
  }));
  fireEvent.click(screen.getByText("CZ").closest("button"));
  assert.equal(selected, "CZ");
});

test("CountryPills: clicking Wszystkie calls onSelect with null", () => {
  let selected = "PL"; // start non-null
  render(React.createElement(CountryPills, {
    rows: ROWS,
    activeIso: "PL",
    onSelect: (iso) => { selected = iso; },
  }));
  fireEvent.click(screen.getByText(/Wszystkie/).closest("button"));
  assert.equal(selected, null);
});

test("CountryPills: pills for countries with no rows are disabled", () => {
  // Only PL rows — CZ pill should be disabled (no CZ rows)
  render(React.createElement(CountryPills, { rows: [{ kraj: "PL" }] }));
  const czButton = screen.getByText("CZ").closest("button");
  assert.equal(czButton.disabled, true, "CZ pill should be disabled when no CZ rows");
});

test("CountryPills: pills for countries with rows are enabled", () => {
  render(React.createElement(CountryPills, { rows: [{ kraj: "PL" }, { kraj: "PL" }] }));
  const plButton = screen.getByText("PL").closest("button");
  assert.equal(plButton.disabled, false);
});

test("CountryPills: handles empty rows array", () => {
  render(React.createElement(CountryPills, { rows: [] }));
  // No crash, all pills present
  assert.ok(screen.getByText(/Wszystkie/));
  // All country pills should be disabled (no rows)
  const plButton = screen.getByText("PL").closest("button");
  assert.equal(plButton.disabled, true);
});

test("CountryPills: handles rows with missing/blank kraj", () => {
  const messyRows = [
    { kraj: "" },
    { kraj: null },
    { kraj: "PL" },
  ];
  render(React.createElement(CountryPills, { rows: messyRows }));
  // PL pill should have count 1 (only one valid PL row)
  const plButton = screen.getByText("PL").closest("button");
  assert.match(plButton.textContent, /1/);
  // Wszystkie total = 3 (we count all rows in the Wszystkie pill)
  const wszystkie = screen.getByText(/Wszystkie/).closest("button");
  assert.match(wszystkie.textContent, /3/);
});

test("CountryPills: sr-only label shows active country name", () => {
  render(React.createElement(CountryPills, { rows: ROWS, activeIso: "CZ" }));
  assert.equal(screen.getByText(/Wybrano: Czechy/).textContent, "Wybrano: Czechy");
});

test("CountryPills: toolbar has aria-label for accessibility", () => {
  render(React.createElement(CountryPills, { rows: ROWS }));
  const toolbar = screen.getByRole("toolbar", { name: "Wybór kraju" });
  assert.ok(toolbar);
});

test("CountryPills: each pill has data-iso attribute for tests/automation", () => {
  render(React.createElement(CountryPills, { rows: ROWS }));
  for (const iso of ["PL", "CZ", "SK", "RS"]) {
    const btn = document.querySelector(`button[data-iso="${iso}"]`);
    assert.ok(btn, `button[data-iso="${iso}"] exists`);
  }
});
