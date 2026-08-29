// QuickChips.test.jsx — happy-dom component tests.
import "./_setup.js";
import test from "node:test";
import assert from "node:assert/strict";
import { afterEach } from "node:test";

const React = (await import("react")).default;
const { render, screen, cleanup, fireEvent } = await import("@testing-library/react");
const { QuickChips } = await import("./QuickChips.jsx");

const ROWS = [
  { kraj: "PL" },
  { kraj: "PL" },
  { kraj: "CZ" },
  { kraj: "CZ" },
  { kraj: "SK" },
  { kraj: "DE" },
];

afterEach(() => cleanup());

function renderChips(props = {}) {
  return render(React.createElement(QuickChips, { columnId: "kraj", rows: ROWS, ...props }));
}

test("QuickChips: shows top values sorted by frequency", () => {
  renderChips();
  const buttons = screen.getAllByRole("button").map((b) => b.textContent);
  const plIdx = buttons.findIndex((t) => t.startsWith("PL"));
  const skIdx = buttons.findIndex((t) => t.startsWith("SK"));
  assert.ok(plIdx > -1, "PL chip should exist");
  assert.ok(skIdx > -1, "SK chip should exist");
  assert.ok(plIdx < skIdx, "PL should render before SK");
});

test("QuickChips: shows count next to each value", () => {
  renderChips();
  const plChip = screen.getByText(/^PL/).closest("button");
  assert.match(plChip.textContent, /2/, "PL chip should display count");
});

test("QuickChips: active filter value is visually distinct", () => {
  renderChips({ filter: "PL" });
  const plChip = screen.getByText(/^PL/).closest("button");
  assert.match(plChip.className, /bg-primary/);
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
  assert.ok(labels.some((l) => l.startsWith("PL")));
  assert.ok(labels.some((l) => l.startsWith("CZ")));
  assert.ok(!labels.some((l) => l.startsWith("SK")));
  assert.ok(!labels.some((l) => l.startsWith("DE")));
});

test("QuickChips: clicking a chip fires onToggle with the value", () => {
  let toggled = null;
  renderChips({ onToggle: (v) => { toggled = v; } });
  fireEvent.click(screen.getByText(/^PL/).closest("button"));
  assert.equal(toggled, "PL");
});