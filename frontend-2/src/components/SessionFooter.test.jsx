// SessionFooter.test.jsx — covers the running-tally row at the bottom
// of the chat panel. Render-to-static is enough here because we only
// care about the rendered text + className, not user interaction.
//
// The "✨ N 0 tok." badge is the call-to-action: when free > 0 it
// teaches the user that FAQ-shaped questions don't burn Gemini quota.
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import test from "node:test";
import assert from "node:assert/strict";
import { SessionFooter } from "./GeminiDrawer.jsx";

const KB_INDEX = [
  { id: "a", filename: "rynek-PL-2024.pdf" },
  { id: "b", filename: "hurtownicy-cz.csv" },
  { id: "c", filename: "notatki.md" },
];

test("SessionFooter: empty thread shows only the message counter", () => {
  const html = renderToStaticMarkup(
    <SessionFooter
      stats={{ total: 0, free: 0, llm: 0 }}
      knowledgeCount={0}
      knowledgeIndex={[]}
    />
  );
  // The total counter is always rendered.
  assert.match(html, /0<\/strong>/);
  // The free/llm badges are conditionally rendered and should be absent.
  assert.doesNotMatch(html, /0 tok\./);
  assert.doesNotMatch(html, />LLM</);
});

test("SessionFooter: shows free-tokens badge when stats.free > 0", () => {
  const html = renderToStaticMarkup(
    <SessionFooter
      stats={{ total: 3, free: 2, llm: 1 }}
      knowledgeCount={0}
      knowledgeIndex={[]}
    />
  );
  assert.match(html, /2<\/strong>\s*0 tok\./);
  assert.match(html, /<\/strong>\s*LLM</);
});

test("SessionFooter: hides free-tokens badge when stats.free === 0", () => {
  const html = renderToStaticMarkup(
    <SessionFooter
      stats={{ total: 5, free: 0, llm: 5 }}
      knowledgeCount={0}
      knowledgeIndex={[]}
    />
  );
  assert.doesNotMatch(html, /0 tok\./);
  assert.match(html, /<\/strong>\s*LLM</);
});

test("SessionFooter: hides LLM badge when no LLM calls happened", () => {
  const html = renderToStaticMarkup(
    <SessionFooter
      stats={{ total: 4, free: 4, llm: 0 }}
      knowledgeCount={0}
      knowledgeIndex={[]}
    />
  );
  assert.match(html, /4<\/strong>\s*0 tok\./);
  // LLM span only renders when llm > 0. Assert the LLM suffix is gone
  // (the free badge has no "LLM" text after it).
  assert.doesNotMatch(html, /0 tok\.[\s\S]*LLM/);
});

test("SessionFooter: counts match the totals passed in", () => {
  const html = renderToStaticMarkup(
    <SessionFooter
      stats={{ total: 7, free: 3, llm: 4 }}
      knowledgeCount={2}
      knowledgeIndex={KB_INDEX}
      parentsSelected={["a", "b"]}
    />
  );
  // 3 free hits
  assert.match(html, /3<\/strong>\s*0 tok\./);
  // 4 LLM calls
  assert.match(html, /4<\/strong>\s*LLM/);
});

test("SessionFooter: total counter uses tabular-nums for stable width", () => {
  const html = renderToStaticMarkup(
    <SessionFooter
      stats={{ total: 1, free: 0, llm: 1 }}
      knowledgeCount={0}
      knowledgeIndex={[]}
    />
  );
  // tabular-nums keeps the layout from jumping as numbers grow.
  assert.match(html, /tabular-nums/);
});
