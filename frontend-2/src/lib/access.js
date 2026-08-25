/**
 * access.js — hashed allow-list gate logic (see design/LOGIN-RULES.md).
 * Hashes are SHA-256 hex of trim+lowercase input; the lists live in
 * public/access.json (hashes only — no plaintext names ship anywhere).
 */
const ACCESS_URL = "/access.json";
const GRANT_KEY = "billszuka.access.v1";

let listsPromise = null;

export function normalize(value) {
  return String(value ?? "").trim().toLowerCase();
}

function subtle() {
  const c = globalThis.crypto?.subtle;
  if (!c) throw new Error("Weryfikacja wymaga kontekstu HTTPS lub localhost");
  return c;
}

export async function sha256Hex(value) {
  const bytes = new TextEncoder().encode(normalize(value));
  const digest = await subtle().digest("SHA-256", bytes);
  return [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export async function verify(input, hashes) {
  const hash = await sha256Hex(input);
  return Array.isArray(hashes) && hashes.includes(hash);
}

export function loadLists() {
  if (!listsPromise) {
    listsPromise = fetch(ACCESS_URL).then((r) => {
      if (!r.ok) throw new Error(`access.json ${r.status}`);
      return r.json();
    });
  }
  return listsPromise;
}

export async function verifyName(input) {
  const lists = await loadLists();
  return verify(input, lists.names);
}

export async function verifyCompany(input) {
  const lists = await loadLists();
  return verify(input, lists.companies);
}

export function isGranted() {
  try { return localStorage.getItem(GRANT_KEY) === "granted"; } catch { return false; }
}

export function grant() {
  try { localStorage.setItem(GRANT_KEY, "granted"); } catch { /* private mode */ }
}

export function revoke() {
  try { localStorage.removeItem(GRANT_KEY); } catch { /* private mode */ }
}
