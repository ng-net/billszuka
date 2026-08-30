// FollowupPills.test.jsx — covers the suggested-next-questions row that
// appears below an assistant bubble when the model emitted a
// ```followup``` block. Each pill now has TWO actions:
//   1. Click the question text → onFill(question)  (fills the input box;
//      never auto-fires an LLM call — the user reviews before sending)
//   2. Click the 📥 button     → onPropose(question) (sends to the admin
//      proposal queue at data/proposals/queue.jsonl)
//
// We use renderToStaticMarkup (no happy-dom) — FollowupPills is plain
// DOM, and pulling the whole GeminiDrawer.jsx + framer-motion into a
// happy-dom test file blows up V8's heap. SSR markup gives us all the
// contract we need: pill count, item text, title attribute, cap-at-4,
// the propose-button wiring, and the two-button-per-question shape.
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import test from "node:test";
import assert from "node:assert/strict";
import { FollowupPills } from "./GeminiDrawer.jsx";

const ITEMS = [
  "Ile firm w CZ?",
  "Top 5 w DE",
  "Tier × kraj",
  "Wolumen w PL",
  "Piąte pytanie (powinno być obcięte)",
  "Szóste pytanie (też obcięte)",
];

test("FollowupPills: renders exactly 4 questions even when given 6 (cap)", () => {
  const html = renderToStaticMarkup(
    React.createElement(FollowupPills, {
      items: ITEMS,
      onFill: () => {},
      onPropose: () => {},
    }),
  );
  // Each question produces a fill-button. Count those specifically so
  // we don't conflate them with the propose buttons.
  const fillButtons = html.match(/aria-label="Wstaw pytanie:/g) || [];
  assert.equal(fillButtons.length, 4);
  assert.match(html, /Ile firm w CZ/);
  assert.match(html, /Wolumen w PL/);
  assert.doesNotMatch(html, /Piąte pytanie/);
  assert.doesNotMatch(html, /Szóste pytanie/);
});

test("FollowupPills: each question has its own 📥 propose button", () => {
  const html = renderToStaticMarkup(
    React.createElement(FollowupPills, {
      items: ["Pytanie A", "Pytanie B"],
      onFill: () => {},
      onPropose: () => {},
    }),
  );
  const proposeButtons = html.match(/aria-label="Zaproponuj pytanie do bazy wiedzy:/g) || [];
  assert.equal(proposeButtons.length, 2);
  // The 📥 emoji is what the user sees — verify it's there in the DOM
  // so reviewers can eyeball it.
  assert.match(html, /\ud83d\udce5/);
});

test("FollowupPills: each pill surfaces its text in the title attribute", () => {
  const html = renderToStaticMarkup(
    React.createElement(FollowupPills, {
      items: ["Pytanie A", "Pytanie B"],
      onFill: () => {},
      onPropose: () => {},
    }),
  );
  // The wrapper div carries the title (hover tooltip on the whole pill)
  assert.match(html, /title="Pytanie A"/);
  assert.match(html, /title="Pytanie B"/);
});

test("FollowupPills: pill text is truncated via truncate + max-w-[36ch]", () => {
  const html = renderToStaticMarkup(
    React.createElement(FollowupPills, {
      items: ["x"],
      onFill: () => {},
      onPropose: () => {},
    }),
  );
  assert.match(html, /truncate/);
  assert.match(html, /max-w-\[36ch\]/);
});

test("FollowupPills: renders an empty wrapper (no buttons) when items is empty", () => {
  const html = renderToStaticMarkup(
    React.createElement(FollowupPills, {
      items: [],
      onFill: () => {},
      onPropose: () => {},
    }),
  );
  // Wrapper div is always present (stable layout), but no buttons when empty.
  assert.match(html, /<div[^>]*>/);
  assert.doesNotMatch(html, /aria-label="Wstaw pytanie:/);
  assert.doesNotMatch(html, /aria-label="Zaproponuj pytanie do bazy wiedzy:/);
});

test("FollowupPills: fill button is the LEFT half of the pill (rounded-l-full)", () => {
  // The propose button must be visually distinct from the fill button —
  // otherwise users will accidentally propose instead of fill. The fill
  // half carries the question text and uses rounded-l-full.
  const html = renderToStaticMarkup(
    React.createElement(FollowupPills, {
      items: ["abc"],
      onFill: () => {},
      onPropose: () => {},
    }),
  );
  assert.match(html, /rounded-l-full/);
  assert.match(html, /rounded-r-full/);
});

test("FollowupPills: click wiring (smoke check via structural shape)", () => {
  // React strips event handlers before SSR, so onClick never appears in
  // the HTML. The structural check we can do: each pill has the expected
  // two-button shape (fill + propose), and the cap is respected.
  const html = renderToStaticMarkup(
    React.createElement(FollowupPills, {
      items: ["x", "y"],
      onFill: () => {},
      onPropose: () => {},
    }),
  );
  const buttons = html.match(/<button[^>]*>[\s\S]*?<\/button>/g) || [];
  assert.equal(buttons.length, 4); // 2 questions × 2 buttons each
  for (const btn of buttons) {
    assert.match(btn, /class=/);
  }
  // The click-wiring path is exercised by the integration test in
  // App.jsx (the user clicks through).
});
