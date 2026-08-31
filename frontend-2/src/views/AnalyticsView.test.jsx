import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import test from "node:test";
import assert from "node:assert/strict";
import { AnalyticsView } from "./AnalyticsView.jsx";

test("AnalyticsView: renders without crashing", () => {
  const html = renderToStaticMarkup(<AnalyticsView />);
  assert.ok(typeof html === "string", "Should render to static markup string");
  assert.ok(html.length > 0, "Rendered HTML should not be empty");
});
