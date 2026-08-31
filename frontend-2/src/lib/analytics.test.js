import test from "node:test";
import assert from "node:assert/strict";
import {
  topByCountry, claimDistributors, powerMaticListings,
  powerMaticMatrix, regionRollup, coverageByCountry,
  researchAnomalies, topResearchAnomaly, verificationTimeline,
  powerMaticGroups, REGION_MAP, deriveStatus,
} from "./analytics.js";

const ROWS = [
  { id: "PL-1", kraj: "PL", nazwa: "Alpha", tier: "hurtownik", notatki: "jesteśmy dystrybutorem PowerMatic", marki_nabijarki: "PowerMatic III+", wolumen: "duży", miasto: "Warszawa", confidence_wolumen: "95%" },
  { id: "PL-2", kraj: "PL", nazwa: "Beta", tier: "reseller", notatki: "sprzedajemy i dystrybuujemy", marki_nabijarki: "PowerMatic, Hawk", wolumen: "średni", miasto: "Kraków", confidence_wolumen: "70%" },
  { id: "PL-3", kraj: "PL", nazwa: "Gamma", tier: "detalista", notatki: "sklep", marki_nabijarki: "Hawk", wolumen: "mały", miasto: "Gdańsk", confidence_wolumen: "50%" },
  { id: "CZ-1", kraj: "CZ", nazwa: "Delta", tier: "hurtownik", notatki: "oficialni distributor", marki_nabijarki: "PowerMatic V", wolumen: "duży", miasto: "Praga", confidence_wolumen: "90%" },
  { id: "CZ-2", kraj: "CZ", nazwa: "Epsilon", tier: "producent", notatki: "produkujemy", marki_nabijarki: "PowerMatic", wolumen: "średni", miasto: "Brno", confidence_wolumen: "60%" },
  { id: "PL-4", kraj: "PL", nazwa: "Zeta", tier: "hurtownik", notatki: "dystrybutor", marki_nabijarki: "PowerMatic, Hawk", wolumen: "duży", miasto: "Wrocław", confidence_wolumen: "85%" },
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
  assert.equal(pl.rows[0].id, "PL-1");
  assert.equal(pl.rows[1].id, "PL-4");
});

test("topByCountry: returns one group per present country", () => {
  const out = topByCountry(ROWS, 3, "wolumen");
  const countries = out.map((g) => g.country).sort();
  assert.deepEqual(countries, ["CZ", "PL"]);
});

test("claimDistributors: matches distributors in notatki", () => {
  const out = claimDistributors(ROWS);
  const ids = out.map((r) => r.id).sort();
  assert.deepEqual(ids, ["CZ-1", "PL-1", "PL-2", "PL-4"]);
});

test("claimDistributors: returns rows with country and tier", () => {
  const out = claimDistributors(ROWS);
  const row = out[0];
  assert.ok(row.nazwa);
  assert.ok(row.kraj);
  assert.ok(row.tier);
  assert.ok(row.match_term);
});

test("claimDistributors: empty list when nothing claims distributor", () => {
  const out = claimDistributors([
    { id: "X", kraj: "PL", nazwa: "Foo", notatki: "sklep" },
  ]);
  assert.equal(out.length, 0);
});

test("powerMaticListings: returns companies with PowerMatic in marki_nabijarki", () => {
  const out = powerMaticListings(ROWS);
  const ids = out.map((r) => r.id).sort();
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

// ---------------------------------------------------------------------------
// v1.2 helper tests
// ---------------------------------------------------------------------------

test("REGION_MAP: has 3 regions, no EU-W (FR removed 2026-08-31)", () => {
  assert.equal(Object.keys(REGION_MAP).length, 3);
  assert.ok("V4" in REGION_MAP);
  assert.ok("Balkans" in REGION_MAP);
  assert.ok("Baltics" in REGION_MAP);
  assert.ok(!("EU-W" in REGION_MAP));
});

test("powerMaticMatrix: counts PM / Hawk / both / brak correctly", () => {
  const out = powerMaticMatrix(ROWS);
  const pl = out.countries.find(c => c.kraj === "PL");
  // PL-1: PM only, PL-2: PM+Hawk, PL-3: Hawk only, PL-4: PM+Hawk
  // So PL: pm=1, hawk=1, both=2, brak=0, total=4
  assert.equal(pl.pm, 1);
  assert.equal(pl.hawk, 1);
  assert.equal(pl.both, 2);
  assert.equal(pl.brak, 0);
  assert.equal(pl.total, 4);
});

test("powerMaticMatrix: sorts by PM count desc", () => {
  const out = powerMaticMatrix(ROWS);
  // PL has 1+2=3 PM listings, CZ has 2 PM listings.
  // So PL should come first.
  assert.equal(out.countries[0].kraj, "PL");
  assert.equal(out.countries[1].kraj, "CZ");
});

test("powerMaticMatrix: computes pmPct", () => {
  const out = powerMaticMatrix(ROWS);
  const pl = out.countries.find(c => c.kraj === "PL");
  // 3 PM out of 4 total = 75%
  assert.equal(pl.pmPct, 75);
});

test("regionRollup: returns 3 regions with breakdown", () => {
  const out = regionRollup(ROWS);
  assert.equal(out.length, 3);
  const v4 = out.find(r => r.name === "V4");
  assert.ok(v4);
  assert.equal(v4.krajeRows.length, 3);
  // ROWS only has PL and CZ, so SK is empty.
  const sk = v4.krajeRows.find(k => k.kraj === "SK");
  assert.equal(sk.total, 0);
});

test("regionRollup: marks anomaly when total >= 30 and pm=0", () => {
  const bigNoPM = Array.from({ length: 35 }, (_, i) => ({
    id: `PL-${i}`,
    kraj: "PL",
    nazwa: `Firm ${i}`,
    marki_nabijarki: "OCB",
    flagi: "FROZEN",
  }));
  const out = regionRollup(bigNoPM);
  const pl = out.find(r => r.name === "V4").krajeRows.find(k => k.kraj === "PL");
  assert.equal(pl.anomaly, true);
});

test("coverageByCountry: counts FROZEN / DO-W / PEND / OTHER", () => {
  const out = coverageByCountry([
    { kraj: "PL", flagi: "FROZEN" },
    { kraj: "PL", flagi: "FROZEN" },
    { kraj: "PL", flagi: "DO-WERYFIKACJI" },
    { kraj: "PL", flagi: "PENDING_API" },
    { kraj: "PL", flagi: "" },
  ]);
  const pl = out.find(c => c.kraj === "PL");
  assert.equal(pl.FROZEN, 2);
  assert.equal(pl.DO_W, 1);
  assert.equal(pl.PEND, 1);
  assert.equal(pl.OTHER, 1);
  assert.equal(pl.frPct, 40);
});

test("researchAnomalies: categorises correctly", () => {
  const rows = [
    ...Array.from({ length: 35 }, (_, i) => ({ id: `PL-${i}`, kraj: "PL", marki_nabijarki: "OCB", flagi: "FROZEN" })),
    { id: "RS-1", kraj: "RS", marki_nabijarki: "PowerMatic", flagi: "" },
    { id: "BG-1", kraj: "BG", marki_nabijarki: "PowerMatic", flagi: "FROZEN" },
  ];
  const out = researchAnomalies(rows);
  assert.equal(out.anomalies.length, 1);
  assert.equal(out.anomalies[0].kraj, "PL");
  assert.equal(out.unverified.length, 1);
  assert.equal(out.unverified[0].kraj, "RS");
  // BG has 1 PM out of 1 total = 100%, FROZEN, so it's "ideal" (>20%, >90%)
  assert.equal(out.ideal.length, 1);
  assert.equal(out.ideal[0].kraj, "BG");
});

test("topResearchAnomaly: returns the worst-case country", () => {
  const rows = [
    ...Array.from({ length: 35 }, (_, i) => ({ id: `PL-${i}`, kraj: "PL", marki_nabijarki: "OCB", flagi: "FROZEN" })),
  ];
  const out = topResearchAnomaly(rows);
  assert.equal(out.country, "PL");
  assert.ok(out.text.includes("0 z PowerMatic"));
});

test("topResearchAnomaly: returns null when no anomalies", () => {
  const out = topResearchAnomaly([
    { id: "BG-1", kraj: "BG", marki_nabijarki: "PowerMatic", flagi: "FROZEN" },
  ]);
  assert.equal(out, null);
});

test("verificationTimeline: returns 6 months of cumulative counts", () => {
  // Build a row FROZEN today.
  const today = new Date();
  const ym = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
  const rows = [
    { kraj: "PL", flagi: "FROZEN", data_weryfikacji: `${ym}-15` },
    { kraj: "PL", flagi: "FROZEN", data_weryfikacji: `${ym}-20` },
  ];
  const out = verificationTimeline(rows, 6);
  assert.equal(out.months.length, 6);
  assert.ok(out.hasAnyDate);
  const pl = out.countries.find(c => c.kraj === "PL");
  assert.equal(pl.spark[pl.spark.length - 1], 2);
});

test("verificationTimeline: parses date from flagi when data_weryfikacji empty", () => {
  const today = new Date();
  const ym = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
  const rows = [
    { kraj: "PL", flagi: `${ym}-10 FROZEN (API)`, data_weryfikacji: "" },
  ];
  const out = verificationTimeline(rows, 6);
  const pl = out.countries.find(c => c.kraj === "PL");
  assert.equal(pl.spark[pl.spark.length - 1], 1);
});

test("verificationTimeline: includes countries with 0 FROZEN", () => {
  const out = verificationTimeline([
    { kraj: "PL", flagi: "FROZEN", data_weryfikacji: "2026-08-15" },
    { kraj: "LV", flagi: "DO-WERYFIKACJI", data_weryfikacji: "" },
  ], 6);
  const lv = out.countries.find(c => c.kraj === "LV");
  assert.ok(lv);
  assert.equal(lv.total, 0);
  assert.equal(lv.hasData, false);
});

// Regression test for the production crash: useCsv's applySchema()
// coerces data_weryfikacji to a Date object, so `(r.data_weryfikacji
// || "").trim()` throws "trim is not a function" in AnalyticsView. The
// helper now accepts Date | string | null and returns a YYYY-MM-DD string.
test("verificationTimeline: handles Date-typed data_weryfikacji from applySchema", () => {
  const today = new Date(2026, 7, 15); // 2026-08-15 local
  const out = verificationTimeline([
    { kraj: "PL", flagi: "FROZEN", data_weryfikacji: today },
  ], 6);
  assert.ok(out.hasAnyDate, "Date input should be recognized");
  const pl = out.countries.find(c => c.kraj === "PL");
  assert.ok(pl);
  assert.equal(pl.total, 1);
});

test("verificationTimeline: ignores invalid Date instances silently", () => {
  const out = verificationTimeline([
    { kraj: "PL", flagi: "FROZEN", data_weryfikacji: new Date("not-a-date") },
  ], 6);
  const pl = out.countries.find(c => c.kraj === "PL");
  assert.ok(pl);
  assert.equal(pl.total, 0, "Invalid Date should fall through to the flagi regex (which also won't match)");
});

test("powerMaticGroups: groups cross-country parents", () => {
  const rows = [
    { id: "BG-1", kraj: "BG", nazwa: "Tobacco Trading International Bulgaria EOOD", marki_nabijarki: "PowerMatic" },
    { id: "RO-1", kraj: "RO", nazwa: "TOBACCO TRADING INTERNATIONAL RO SRL", marki_nabijarki: "PowerMatic" },
    { id: "PL-1", kraj: "PL", nazwa: "Local Co", marki_nabijarki: "PowerMatic" },
  ];
  const out = powerMaticGroups(rows);
  assert.equal(out.groups.length, 1);
  assert.equal(out.groups[0].kraje.length, 2);
  assert.equal(out.singles.length, 1);
});

test("powerMaticGroups: returns empty singles for empty rows", () => {
  const out = powerMaticGroups([]);
  assert.equal(out.groups.length, 0);
  assert.equal(out.singles.length, 0);
});

test("deriveStatus: handles all 4 status strings", () => {
  assert.equal(deriveStatus("2026-08-15 FROZEN (API)"), "FROZEN");
  assert.equal(deriveStatus("DO-WERYFIKACJI"), "DO-WERYFIKACJI");
  assert.equal(deriveStatus("PENDING_API"), "PENDING_API");
  assert.equal(deriveStatus(""), "OTHER");
  assert.equal(deriveStatus(null), "OTHER");
});
