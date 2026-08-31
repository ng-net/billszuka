// ActiveFilterChips.test.jsx — component tests.
import "./_setup.js";
import test from "node:test";
import assert from "node:assert/strict";
import { afterEach } from "node:test";

const React = (await import("react")).default;
const { render, screen, cleanup, fireEvent } = await import("@testing-library/react");
const { ActiveFilterChips } = await import("./ActiveFilterChips.jsx");

afterEach(() => cleanup());

test("ActiveFilterChips: returns null when no filters or search", () => {
  const { container } = render(React.createElement(ActiveFilterChips, { filters: {}, globalSearch: "" }));
  assert.equal(container.firstChild, null);
});

test("ActiveFilterChips: renders global search chip with X button", () => {
  let cleared = false;
  render(React.createElement(ActiveFilterChips, {
    filters: {},
    globalSearch: "Kowalski",
    onClearGlobalSearch: () => { cleared = true; },
  }));
  assert.ok(screen.getByText(/"Kowalski"/));
  fireEvent.click(screen.getByRole("button", { name: /Usuń filtr/i }));
  assert.equal(cleared, true);
});

test("ActiveFilterChips: renders brand and range chips (country is excluded)", () => {
  render(React.createElement(ActiveFilterChips, {
    filters: {
      __brand: "PowerMatic",
      kraj: "PL", // country filter intentionally suppressed
      rok_zalozenia: { min: 2010, max: 2024 },
    },
    onRemoveFilter: () => {},
  }));

  assert.ok(screen.getByText("PowerMatic"));
  assert.ok(screen.getByText("2010 – 2024"));
  // Country chip must NOT be shown even when filter state has kraj set.
  assert.equal(screen.queryByText("PL"), null);
});

test("ActiveFilterChips: clicking reset button calls onResetAll", () => {
  let reset = false;
  render(React.createElement(ActiveFilterChips, {
    filters: { tier: "hurtownik" },
    onResetAll: () => { reset = true; },
  }));
  const resetBtn = screen.getByRole("button", { name: /Resetuj/i });
  fireEvent.click(resetBtn);
  assert.equal(reset, true);
});
