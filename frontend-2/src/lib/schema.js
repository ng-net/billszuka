// schema.js — schema constants and column display mappings shared across frontend-2 views.
//
// Mirrors tools/config.py on the Python side.

/** Friendly, professional human-readable Polish labels for all canonical columns. */
export const COLUMN_LABELS = {
  kraj: "Kraj",
  id_unikalne: "ID Unikalne",
  nazwa_firmy: "Nazwa firmy",
  miasto: "Miasto",
  adres: "Adres",
  www: "Strona WWW",
  wolumen: "Wolumen",
  confidence_wolumen: "Pewność wolumenu",
  rejestr_id: "Nr rejestru (KRS/IČO)",
  nip_vat: "NIP / VAT",
  rok_zalozenia: "Rok założenia",
  tier: "Rola w kanale",
  marki_nabijarki: "Marki maszynek",
  marka_wlasna_oem: "Marka własna / OEM",
  powinowactwo_nabijarki: "Powinowactwo maszynek",
  kategoria: "Kategoria",
  rynek_skala: "Skala rynku",
  cross_sell_potential: "Potencjał cross-sell",
  kanal_sprzedaży: "Kanał sprzedaży",
  kanal_sprzedazy: "Kanał sprzedaży",
  kanal_zamiennik: "Kanał zamienników",
  decydent: "Decydent",
  stanowisko: "Stanowisko",
  email_decydent: "Email decydenta",
  email: "Email ogólny",
  telefon: "Telefon",
  notatki: "Notatki",
  linkedin: "LinkedIn",
  facebook: "Facebook",
  instagram: "Instagram",
  tiktok: "TikTok",
  data_weryfikacji: "Data weryfikacji",
  sourcing: "Sourcing",
  zrodlo_danych: "Źródło danych",
  flagi: "Flagi",
  related_to: "Powiązany z",
};

/** Returns the display name for a column ID, falling back to capitalized words. */
export function getColumnLabel(columnId) {
  if (!columnId) return "";
  if (COLUMN_LABELS[columnId]) return COLUMN_LABELS[columnId];
  return columnId.replace(/_/g, " ");
}

/** Always-empty — removed to avoid confusing overrides. Visibility is CSV-driven. */
export const HIDDEN_COLUMNS = [];

/** Identity pass-through — no hardcoded filtering applied to CSV columns. */
export function visibleColumns(columns) {
  return columns;
}

