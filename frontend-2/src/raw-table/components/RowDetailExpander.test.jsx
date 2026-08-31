// RowDetailExpander.test.jsx — component tests.
import "./_setup.js";
import test from "node:test";
import assert from "node:assert/strict";
import { afterEach } from "node:test";

const React = (await import("react")).default;
const { render, screen, cleanup } = await import("@testing-library/react");
const { RowDetailExpander } = await import("./RowDetailExpander.jsx");

const SAMPLE_LEAD = {
  id: "LEAD-1001",
  nazwa_firmy: "PowerMatic Polska Sp. z o.o.",
  adres: "ul. Przemysłowa 10, 00-001 Warszawa",
  kraj: "Polska",
  miasto: "Warszawa",
  nip_vat: "PL1234567890",
  rejestr_id: "KRS 0000123456",
  marki_nabijarki: "PowerMatic III+, Hawk Roller",
  decydent: "Jan Kowalski",
  stanowisko: "Dyrektor Handlowy",
  email_decydent: "jan.k@powermatic.pl",
  email: "kontakt@powermatic.pl",
  telefon: "+48 500 100 200",
  notatki: "Kluczowy dystrybutor maszyn na rynku polskim.",
  zrodlo_danych: "KRS Online",
  data_weryfikacji: "2026-08-28",
};

afterEach(() => cleanup());

test("RowDetailExpander: renders business details (address, NIP, KRS, brands)", () => {
  render(React.createElement(RowDetailExpander, { lead: SAMPLE_LEAD, maskNames: false }));
  assert.ok(screen.getByText(/ul\. Przemysłowa 10/));
  assert.ok(screen.getByText("PL1234567890"));
  assert.ok(screen.getByText("KRS 0000123456"));
  assert.ok(screen.getByText("PowerMatic III+"));
  assert.ok(screen.getByText("Hawk Roller"));
});

test("RowDetailExpander: masks decydent surname when maskNames is true (default)", () => {
  render(React.createElement(RowDetailExpander, { lead: SAMPLE_LEAD, maskNames: true }));
  assert.ok(screen.getByText("Jan Ko***i"));
});

test("RowDetailExpander: reveals full decydent name when maskNames is false", () => {
  render(React.createElement(RowDetailExpander, { lead: SAMPLE_LEAD, maskNames: false }));
  assert.ok(screen.getByText("Jan Kowalski"));
});

test("RowDetailExpander: renders contact info and operational notes", () => {
  render(React.createElement(RowDetailExpander, { lead: SAMPLE_LEAD }));
  assert.ok(screen.getByText(/Dyrektor Handlowy/));
  assert.ok(screen.getByText("+48 500 100 200"));
  assert.ok(screen.getByText(/Kluczowy dystrybutor maszyn/));
  assert.ok(screen.getByText(/KRS Online/));
});
