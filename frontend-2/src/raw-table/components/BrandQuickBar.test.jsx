// BrandQuickBar.test.jsx — component tests.
import "./_setup.js";
import test from "node:test";
import assert from "node:assert/strict";
import { afterEach } from "node:test";

const React = (await import("react")).default;
const { render, screen, cleanup, fireEvent } = await import("@testing-library/react");
const { BrandQuickBar } = await import("./BrandQuickBar.jsx");

const SAMPLE_ROWS = [
  { nazwa: "PowerMatic Polska Sp. z o.o.", notatki: "Dystrybutor" },
  { nazwa: "Hawk Rollers B2B", notatki: "Sprzedawca maszyn" },
  { nazwa: "Firma Handlowa PM+Hawk", notatki: "PowerMatic oraz Hawk" },
  { nazwa: "Inna Hurtownia", notatki: "Brak maszynek" },
];

afterEach(() => cleanup());

function renderBar(props = {}) {
  return render(React.createElement(BrandQuickBar, { rows: SAMPLE_ROWS, ...props }));
}

test("BrandQuickBar: renders all segment buttons", () => {
  renderBar();
  const buttons = screen.getAllByRole("button").map((b) => b.textContent);
  assert.ok(buttons.some((t) => t.includes("Wszystko")), "Wszystko button should exist");
  assert.ok(buttons.some((t) => t.includes("PowerMatic")), "PowerMatic button should exist");
  assert.ok(buttons.some((t) => t.includes("Hawk")), "Hawk button should exist");
});

test("BrandQuickBar: computes total count for Wszystko", () => {
  renderBar();
  const allBtn = screen.getByText("Wszystko").closest("button");
  assert.match(allBtn.textContent, /4/);
});

test("BrandQuickBar: clicking a brand segment fires onSelectBrand", () => {
  let selected = undefined;
  renderBar({ onSelectBrand: (b) => { selected = b; } });
  fireEvent.click(screen.getByText("PowerMatic").closest("button"));
  assert.equal(selected, "PowerMatic");
});

test("BrandQuickBar: clicking active brand segment toggles off to null", () => {
  let selected = undefined;
  renderBar({ activeBrand: "PowerMatic", onSelectBrand: (b) => { selected = b; } });
  fireEvent.click(screen.getByText("PowerMatic").closest("button"));
  assert.equal(selected, null);
});

test("BrandQuickBar: returns null when rows are empty", () => {
  const { container } = render(React.createElement(BrandQuickBar, { rows: [] }));
  assert.equal(container.firstChild, null);
});
