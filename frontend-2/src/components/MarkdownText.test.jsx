// MarkdownText.test.jsx — covers the lightweight markup renderer used
// inside the assistant bubble. The interesting new bit is the
// ```followup … ``` block: it must be pulled OUT of the rendered text
// (so it can become clickable pills below the bubble), not rendered
// inline. This file asserts that contract plus a few of the older
// features (```fakt```, ```errata```, headings, lists) to lock down
// regressions when refactoring the parser.
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import test from "node:test";
import assert from "node:assert/strict";
import { MarkdownText } from "./GeminiDrawer.jsx";

function render(content) {
  // MarkdownText returns either a JSX element OR { elements, followups }
  // when followups are extracted. Flatten both shapes for assertions.
  const out = renderToStaticMarkup(
    React.createElement("div", null, React.createElement(MarkdownText, { content })),
  );
  return out;
}

test("MarkdownText: returns null for empty content", () => {
  const html = renderToStaticMarkup(
    React.createElement(MarkdownText, { content: "" }),
  );
  assert.equal(html, "");
});

test("MarkdownText: a plain paragraph renders inside a <p>", () => {
  const html = render("Cześć, jestem Gills.");
  assert.match(html, /<p[^>]*>/);
  assert.match(html, /Cześć, jestem Gills\./);
});

test("MarkdownText: ## heading renders as <h4>", () => {
  const html = render("## Kluczowe fakty");
  assert.match(html, /<h4[^>]*>Kluczowe fakty<\/h4>/);
});

test("MarkdownText: ### heading renders as <h5>", () => {
  const html = render("### Szczegóły");
  assert.match(html, /<h5[^>]*>Szczegóły<\/h5>/);
});

test("MarkdownText: bold **text** renders as <strong>", () => {
  const html = render("To jest **ważne** zdanie.");
  assert.match(html, /<strong[^>]*>ważne<\/strong>/);
});

test("MarkdownText: bullet list renders each line as a row", () => {
  const html = render("- pierwszy\n- drugi\n- trzeci");
  const bullets = html.match(/<span[^>]*>•<\/span>/g) || [];
  assert.equal(bullets.length, 3);
  assert.match(html, /pierwszy/);
  assert.match(html, /trzeci/);
});

test("MarkdownText: numbered list renders each line with its index", () => {
  const html = render("1. jeden\n2. dwa");
  assert.match(html, />1\.</);
  assert.match(html, />2\.</);
});

test("MarkdownText: ```fakt block renders as the emerald key-fact card", () => {
  const html = render("```fakt\nLiczba firm FROZEN: 23\n```");
  assert.match(html, /Kluczowy fakt/);
  assert.match(html, /Liczba firm FROZEN: 23/);
  assert.match(html, /emerald/);
});

test("MarkdownText: ```errata block renders as the amber warning card", () => {
  const html = render("```errata\nUwaga: liczby mogą być nieaktualne.\n```");
  assert.match(html, /Errata/);
  assert.match(html, /Uwaga/);
  assert.match(html, /amber/);
});

test("MarkdownText: ```followup block does NOT render inline", () => {
  // The whole point of the refactor: the followup block is extracted
  // out of the bubble so FollowupPills can render it as buttons. The
  // inline body must therefore not contain the followup text — it
  // should appear in a sibling <div> outside the bubble's <p>.
  const html = render(
    "Krótka odpowiedź.\n\n```followup\n- Ile firm w CZ?\n- Top 5 w DE\n```\n",
  );
  // The followup questions should NOT appear inside the bubble's body.
  // They will appear in the FollowupPills element — but in this test
  // we render MarkdownText alone, so the followup text should be
  // stripped from the output entirely.
  assert.doesNotMatch(html, /Ile firm w CZ/);
  assert.doesNotMatch(html, /Top 5 w DE/);
  // The prose must still render.
  assert.match(html, /Krótka odpowiedź\./);
});

test("MarkdownText: ```followup with list-style bullets is stripped", () => {
  const html = render("```followup\n* pytanie 1\n* pytanie 2\n```");
  // Both followup lines stripped from the inline body.
  assert.doesNotMatch(html, /pytanie 1/);
  assert.doesNotMatch(html, /pytanie 2/);
});

test("MarkdownText: ```followup without trailing newline still parses", () => {
  const html = render("```followup\ntylko jedno pytanie\n```");
  assert.doesNotMatch(html, /tylko jedno pytanie/);
});

test("MarkdownText: unknown code block (no language) renders as <pre>", () => {
  const html = render("```\nplain code\n```");
  assert.match(html, /<pre[^>]*>/);
  assert.match(html, /<code[^>]*>plain code<\/code>/);
});

test("MarkdownText: empty followup block (only whitespace lines) yields no text", () => {
  const html = render("```followup\n\n   \n```\n");
  assert.doesNotMatch(html, /undefined/);
});
