// ViewSwitcher.test.jsx — happy-dom component tests for the saved-view
// popover TRIGGER.
//
// We only test the trigger (the button that opens the popover) because
// Radix's popover content uses a portal + floating-ui positioning that
// doesn't fully render in happy-dom. The trigger reflects the active
// view state and is the only piece rendered eagerly, so it gives us
// decent coverage of the component's contract.
import "./_setup.js";
import test from "node:test";
import assert from "node:assert/strict";
import { afterEach } from "node:test";

const React = (await import("react")).default;
const { render, screen, cleanup } = await import("@testing-library/react");
const { ViewSwitcher } = await import("./ViewSwitcher.jsx");

afterEach(() => cleanup());

test("ViewSwitcher: trigger shows 'Wszystko' label when no view is active", () => {
  render(React.createElement(ViewSwitcher, { views: [], activeView: null }));
  const matches = screen.queryAllByText(/Wszystko/);
  assert.ok(matches.length > 0, "Trigger should render 'Wszystko' label");
});

test("ViewSwitcher: trigger shows active view name instead of 'Wszystko'", () => {
  const views = [{ id: "v1", name: "PL Big players" }];
  render(React.createElement(ViewSwitcher, { views, activeView: "v1" }));
  assert.ok(screen.queryAllByText(/PL Big players/).length > 0);
  assert.equal(screen.queryAllByText(/Wszystko/).length, 0);
});

test("ViewSwitcher: trigger has aria-haspopup='dialog' for a11y", () => {
  render(React.createElement(ViewSwitcher, { views: [], activeView: null }));
  const trigger = screen.getByRole("button");
  assert.equal(trigger.getAttribute("aria-haspopup"), "dialog");
});

test("ViewSwitcher: trigger starts collapsed (aria-expanded='false')", () => {
  render(React.createElement(ViewSwitcher, { views: [], activeView: null }));
  const trigger = screen.getByRole("button");
  assert.equal(trigger.getAttribute("aria-expanded"), "false");
});

test("ViewSwitcher: only one button (trigger) is rendered initially", () => {
  render(
    React.createElement(ViewSwitcher, {
      views: [],
      activeView: null,
      onSave: () => {},
    })
  );
  // Popover content (which has more buttons) only mounts after open.
  assert.equal(screen.getAllByRole("button").length, 1);
});