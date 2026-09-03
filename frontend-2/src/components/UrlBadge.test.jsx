// UrlBadge.test.jsx — tests for WwwStatusPill and parseWwwStatus.
import "../raw-table/components/_setup.js";
import test from "node:test";
import assert from "node:assert/strict";
import { afterEach } from "node:test";

const React = (await import("react")).default;
const { render, screen, cleanup } = await import("@testing-library/react");
const { parseWwwStatus, WwwStatusPill } = await import("./UrlBadge.jsx");

afterEach(() => cleanup());

test("parseWwwStatus: correctly parses green status with response time", () => {
  const res = parseWwwStatus("green|200|234ms");
  assert.equal(res.status, "green");
  assert.equal(res.http_code, 200);
  assert.equal(res.response_time, "234ms");
  assert.equal(res.label, "200 OK");
});

test("parseWwwStatus: correctly parses red errors (404, 403, timeout, dns, ssl, 500)", () => {
  assert.equal(parseWwwStatus("red|404").error, "404 Not Found");
  assert.equal(parseWwwStatus("red|403").error, "403 Forbidden");
  assert.equal(parseWwwStatus("red|dns").error, "DNS Error");
  assert.equal(parseWwwStatus("red|ssl").error, "SSL Error");
  assert.equal(parseWwwStatus("red|timeout").error, "Timeout");
  assert.equal(parseWwwStatus("red|500").error, "500 Server Error");
  assert.equal(parseWwwStatus("red|503").error, "503 Unavailable");
  assert.equal(parseWwwStatus("red|429").error, "429 Rate Limit");
});

test("WwwStatusPill: renders 200 OK pill with response time for green status", () => {
  render(React.createElement(WwwStatusPill, { rawStatus: "green|200|320ms" }));
  assert.ok(screen.getByText("200 OK"), "should render 200 OK text");
  assert.ok(screen.getByText("320ms"), "should render response time");
});

test("WwwStatusPill: renders mini pill with error label inside for 404", () => {
  render(React.createElement(WwwStatusPill, { rawStatus: "red|404" }));
  assert.ok(screen.getByText("404 Not Found"), "should render 404 Not Found inside pill");
});

test("WwwStatusPill: renders compact error label when compact is true", () => {
  render(React.createElement(WwwStatusPill, { rawStatus: "red|404", compact: true }));
  assert.ok(screen.getByText("404"), "should render compact 404 label");
});

test("WwwStatusPill: renders DNS Error pill", () => {
  render(React.createElement(WwwStatusPill, { rawStatus: "red|dns" }));
  assert.ok(screen.getByText("DNS Error"), "should render DNS Error");
});

test("WwwStatusPill: renders SSL Error pill", () => {
  render(React.createElement(WwwStatusPill, { rawStatus: "red|ssl" }));
  assert.ok(screen.getByText("SSL Error"), "should render SSL Error");
});

test("WwwStatusPill: renders Timeout pill", () => {
  render(React.createElement(WwwStatusPill, { rawStatus: "red|timeout" }));
  assert.ok(screen.getByText("Timeout"), "should render Timeout");
});

test("WwwStatusPill: renders 500 Server Error pill", () => {
  render(React.createElement(WwwStatusPill, { rawStatus: "red|500" }));
  assert.ok(screen.getByText("500 Server Error"), "should render 500 Server Error");
});
