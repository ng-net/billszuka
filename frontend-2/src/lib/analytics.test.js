import test from "node:test";
import assert from "node:assert/strict";
import { topByCountry, claimDistributors, powerMaticListings } from "./analytics.js";

const ROWS = [
  { id_unikalne: "PL-1", kraj: "PL", nazwa_firmy: "Alpha", tier: "hurtownik", notatki: "jesteśmy dystrybutorem PowerMatic", marki_nabijarki: "PowerMatic III+", wolumen: "duży", miasto: "Warszawa", confidence_wolumen: "95%" },
  { id_unikalne: "PL-2", kraj: "PL", nazwa_firmy: "Beta", tier: "reseller", notatki: "sprzedajemy i dystrybuujemy", marki_nabijarki: "PowerMatic, Hawk", wolumen: "średni", miasto: "Kraków", confidence_wolumen: "70%" },
  { id_unikalne: "PL-3", kraj: "PL", nazwa_firmy: "Gamma", tier: "detalista", notatki: "sklep", marki_nabijarki: "Hawk", wolumen: "mały", miasto: "Gdańsk", confidence_wolumen: "50%" },
  { id_unikalne: "CZ-1", kraj: "CZ", nazwa_firmy: "Delta", tier: "hurtownik", notatki: "oficialni distributor", marki_nabijarki: "PowerMatic V", wolumen: "duży", miasto: "Praga", confidence_wolumen: "90%" },
  { id_unikalne: "CZ-2", kraj: "CZ", nazwa_firmy: "Epsilon", tier: "producent", notatki: "produkujemy", marki_nabijarki: "PowerMatic", wolumen: "średni", miasto: "Brno", confidence_wolumen: "60%" },
  { id_unikalne: "PL-4", kraj: "PL", nazwa_firmy: "Zeta", tier: "hurtownik", notatki: "dystrybutor", marki_nabijarki: "PowerMatic, Hawk", wolumen: "duży", miasto: "Wrocław", confidence_wolumen: "85%" },
];

test("topByCountry: returns n companies per country", () => {
  const out = topByCountry(ROWS, 2, "wolumen");
  const pl = out.find((g) => g.country === "PL");
  const cz = out.find((g) => g.country === "CZ");
  assert.equal(pl.rows.length, 2);
  assert.equal(cz.rows.length, 2);
});

test("topByCountry: ranks by the chosen metric desc", () => {
  const out = topByCountry(ROWS, 5, "wolumen");
  const pl = out.find((g) => g.country === "PL");
  // Confidence-based ordering: 95 > 85 > 70 > 50
  assert.equal(pl.rows[0].id_unikalne, "PL-1");
  assert.equal(pl.rows[1].id_unikalne, "PL-4");
});

test("topByCountry: returns one group per present country", () => {
  const out = topByCountry(ROWS, 3, "wolumen");
  const countries = out.map((g) => g.country).sort();
  assert.deepEqual(countries, ["CZ", "PL"]);
});

test("claimDistributors: matches distributors in notatki", () => {
  const out = claimDistributors(ROWS);
  const ids = out.map((r) => r.id_unikalne).sort();
  assert.deepEqual(ids, ["CZ-1", "PL-1", "PL-2", "PL-4"]);
});

test("claimDistributors: returns rows with country and tier", () => {
  const out = claimDistributors(ROWS);
  const row = out[0];
  assert.ok(row.nazwa_firmy);
  assert.ok(row.kraj);
  assert.ok(row.tier);
  assert.ok(row.match_term);
});

test("claimDistributors: empty list when nothing claims distributor", () => {
  const out = claimDistributors([
    { id_unikalne: "X", kraj: "PL", nazwa_firmy: "Foo", notatki: "sklep" },
  ]);
  assert.equal(out.length, 0);
});

test("powerMaticListings: returns companies with PowerMatic in marki_nabijarki", () => {
  const out = powerMaticListings(ROWS);
  const ids = out.map((r) => r.id_unikalne).sort();
  // PL-1, PL-2, PL-4, CZ-1, CZ-2
  assert.deepEqual(ids, ["CZ-1", "CZ-2", "PL-1", "PL-2", "PL-4"]);
});

test("powerMaticListings: marks brand variants correctly", () => {
  const out = powerMaticListings(ROWS);
  const all = out.map((r) => r.brand_variant).sort();
  assert.ok(all.every((b) => ["PowerMatic", "PowerMatic + Hawk"].includes(b)));
});

test("topByCountry: defaults to n=5 when not provided", () => {
  const out = topByCountry(ROWS);
  const pl = out.find((g) => g.country === "PL");
  assert.equal(pl.rows.length, Math.min(5, ROWS.filter((r) => r.kraj === "PL").length));
});

test("topByCountry: handles empty rows", () => {
  const out = topByCountry([], 5, "wolumen");
  assert.deepEqual(out, []);
});
