import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { normalize, sha256Hex, verify } from "./access.js";

const lists = JSON.parse(
  readFileSync(new URL("../../public/access.json", import.meta.url), "utf8"),
);

test("normalize trims and lowercases", () => {
  assert.equal(normalize(" BILLS "), "bills");
  assert.equal(normalize("Jarosław"), "jarosław");
});

test("sha256Hex is 64-char hex and deterministic", async () => {
  const a = await sha256Hex("karol");
  const b = await sha256Hex("karol");
  assert.match(a, /^[0-9a-f]{64}$/);
  assert.equal(a, b);
});

test("allowed names verify case-insensitively against access.json", async () => {
  for (const name of ["marceli", "KAROL", " Jarek ", "jarosław", "jaro", "jaroslaw"]) {
    assert.equal(await verify(name, lists.names), true, name);
  }
});

test("allowed companies verify with any formatting", async () => {
  for (const c of ["bills", "BILLS", "BiLLs", " smoks ", "SMOKS"]) {
    assert.equal(await verify(c, lists.companies), true, c);
  }
});

test("unknown names and companies are rejected", async () => {
  assert.equal(await verify("michael", lists.names), false);
  assert.equal(await verify("google", lists.companies), false);
});
