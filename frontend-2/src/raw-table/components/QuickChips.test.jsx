// QuickChips.test.jsx — happy-dom component tests.
import "./_setup.js";
import test from "node:test";
import assert from "node:assert/strict";
import { afterEach } from "node:test";

const React = (await import("react")).default;
const { render, screen, cleanup, fireEvent } = await import("@testing-library/react");
const { QuickChips } = await import("./QuickChips.jsx");

// Use `tier` as a sample filterable column (country/kraj has no filtering option).
const ROWS = [
  { tier: "hurtownik" },
  { tier: "hurtownik" },
  { tier: "reseller" },
  { tier: "reseller" },
  { tier: "detalista" },
  { tier: "producent" },
];

afterEach(() => cleanup());

function renderChips(props = {}) {
  return render(React.createElement(QuickChips, { columnId: "tier", rows: ROWS, ...props }));
}

test("QuickChips: shows top values sorted by frequency", () => {
  renderChips();
  const buttons = screen.getAllByRole("button").map((b) => b.textContent);
  const hurtIdx = buttons.findIndex((t) => t.startsWith("hurtownik"));
  const detIdx = buttons.findIndex((t) => t.startsWith("detalista"));
  assert.ok(hurtIdx > -1, "hurtownik chip should exist");
  assert.ok(detIdx > -1, "detalista chip should exist");
  assert.ok(hurtIdx < detIdx, "hurtownik should render before detalista");
});

test("QuickChips: shows count next to each value", () => {
  renderChips();
  const chip = screen.getByText(/^hurtownik/).closest("button");
  assert.match(chip.textContent, /2/, "hurtownik chip should display count");
});

test("QuickChips: active filter value is visually distinct", () => {
  renderChips({ filter: "hurtownik" });
  const chip = screen.getByText(/^hurtownik/).closest("button");
  assert.match(chip.className, /bg-primary/);
});

test("QuickChips: returns null when no values found", () => {
  const { container } = renderChips({ rows: [] });
  assert.equal(container.firstChild, null);
});

test("QuickChips: limit caps number of chips", () => {
  renderChips({ limit: 2 });
  const buttons = screen.getAllByRole("button");
  assert.equal(buttons.length, 2);
  const labels = buttons.map((b) => b.textContent);
  assert.ok(labels.some((l) => l.startsWith("hurtownik")));
  assert.ok(labels.some((l) => l.startsWith("reseller")));
  assert.ok(!labels.some((l) => l.startsWith("detalista")));
  assert.ok(!labels.some((l) => l.startsWith("producent")));
});

test("QuickChips: clicking a chip fires onToggle with the value", () => {
  let toggled = null;
  renderChips({ onToggle: (v) => { toggled = v; } });
  fireEvent.click(screen.getByText(/^hurtownik/).closest("button"));
  assert.equal(toggled, "hurtownik");
});