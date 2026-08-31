// _setup.js — install a fresh happy-dom window on globalThis so each
// .test.jsx file gets a clean DOM. Imported at the very top of every
// component test file.
//
// Usage:
//   import "./_setup.js";
//   import test from "node:test";
//   import { Window } from "happy-dom";   // ← don't use directly
//
// The setup replaces globalThis.window/document/Element/etc. so React
// and RTL find a real DOM to mount into. Each test file imports this
// once and the side effect installs fresh globals before its tests run.
//
// fake-indexeddb/auto polyfills globalThis.indexedDB (and friends) so
// IndexedDB-backed code paths (datasetStorage, datasetStorage.test.js)
// work under node:test. happy-dom does NOT ship indexedDB.
import "fake-indexeddb/auto";
import { Window } from "happy-dom";

const w = new Window();
globalThis.window = w;
globalThis.document = w.document;
globalThis.HTMLElement = w.HTMLElement;
globalThis.Element = w.Element;
globalThis.Node = w.Node;
globalThis.getComputedStyle = w.getComputedStyle;
globalThis.MutationObserver = w.MutationObserver;
globalThis.requestAnimationFrame = w.requestAnimationFrame || ((cb) => setTimeout(cb, 16));
globalThis.cancelAnimationFrame = w.cancelAnimationFrame || ((id) => clearTimeout(id));
globalThis.IS_REACT_ACT_ENVIRONMENT = true;