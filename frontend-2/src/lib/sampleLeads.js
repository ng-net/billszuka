// Hardcoded 120 leads for ExperimentView demos.
// Mix of PL / CZ / SK / DE / UK, real-looking distributors, hurtownie,
// marketplace fishes, and PowerMatic / Hawk / Inna brands.
// Used by ExperimentView and ModernLeadsTable so demos always have rich data.

const CITIES = {
  PL: ["Warszawa", "Kraków", "Wrocław", "Gdańsk", "Poznań", "Łódź", "Katowice", "Bydgoszcz", "Lublin", "Szczecin"],
  CZ: ["Praga", "Brno", "Ostrava", "Plzeň", "Liberec", "Olomouc"],
  SK: ["Bratysława", "Koszyce", "Preszów", "Żylina", "Nitra"],
  DE: ["Berlin", "Hamburg", "Monachium", "Frankfurt"],
  UK: ["Londyn", "Manchester", "Birmingham"],
};

const SUFFIXES = [
  "Sp. z o.o.", "Sp. J.", "S.A.", "S.C.", "GmbH", "Ltd.", "Group",
  "Distribution", "Hurtownia", "Trading", "Wholesale", "Import-Export", "Tobacco",
  "International", "Europe", "Polska", "Czechy", "Slovakia",
];

const TIERS = ["hurtownik", "reseller", "detalista", "marketplace", "producent", "autoryzowany"];
const VOLUMES = ["duży", "średni", "mały"];
const BRAND_PROFILES = [
  { variant: "PowerMatic", marki: "PowerMatic III+" },
  { variant: "PowerMatic", marki: "PowerMatic V+" },
  { variant: "PowerMatic + Hawk", marki: "PowerMatic, Hawk" },
  { variant: "PowerMatic + Hawk", marki: "PowerMatic II+, Hawk Electric" },
  { variant: "Hawk", marki: "Hawk Roller" },
  { variant: "Hawk", marki: "Hawk Industrial" },
  { variant: "Inna", marki: "BongGo" },
  { variant: "Inna", marki: "Dark Horse" },
  { variant: "Inna", marki: "TopMatic" },
  { variant: "Inna", marki: "Royal Filter" },
];

const DISTRIBUTOR_NOTES = [
  "Oficjalny dystrybutor maszyn do tytoniu. Prowadzimy sprzedaż hurtową i detaliczną.",
  "Jesteśmy dystrybutorem PowerMatic na Polskę. Obsługujemy sieci sklepów.",
  "Dystrybutor i serwis maszyn Hawk. Sprzedaż hurtowa + leasing.",
  "Sprzedajemy i dystrybuujemy asortyment tytoniowy w całym regionie.",
  "Oficjalni dystrybutorzy — dystrybucja hurtowa od 100 szt.",
  "Hurtownia tytoniowa, dystrybuujemy maszynki automatyczne i gilzy.",
  "Distributor of rolling machines across CEE. Wholesale + retail.",
  "Hurtownia; dystrybutor maszyn do papierosów i akcesoriów.",
];

const NON_DISTRIBUTOR_NOTES = [
  "Sklep stacjonarny, sprzedaż detaliczna.",
  "Własna marka producenta gilz i bibułek.",
  "Marketplace Allegro — sprzedaż wysyłkowa.",
  "Import własnej marki OEM z Chin.",
  "Sklep internetowy, niski wolumen.",
  "Hurtownia papierosów elektronicznych.",
  "Producent gilz papierosowych.",
  "Sklep tytoniowy, asortyment mieszany.",
];

const STREETS = ["ul. Przemysłowa", "ul. Handlowa", "ul. Towarowa", "ul. Polna", "ul. Lipowa", "ul. Kwiatowa", "al. Jerozolimskie", "ul. Marszałkowska"];
const FIRST_NAMES = ["Marek", "Tomasz", "Jan", "Adam", "Piotr", "Krzysztof", "Paweł", "Andrzej", "Marcin", "Łukasz", "Anna", "Katarzyna", "Magdalena", "Joanna", "Tomáš", "Petr", "Martin", "Jiří", "Eva", "Lucia", "Stefan", "Lukáš"];
const LAST_NAMES = ["Kowalski", "Wiśniewski", "Nowak", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski", "Zieliński", "Szymański", "Woźniak", "Dvořák", "Novák", "Svoboda", "Novotný", "Horváth", "Kováč", "Müller", "Schmidt", "Smith", "Brown"];

function pick(arr, i) {
  return arr[i % arr.length];
}

function pickRandom(arr, seed) {
  return arr[(seed * 9301 + 49297) % arr.length];
}

function makeId(country, i) {
  const prefix = { PL: "PL-B", CZ: "CZ-B", SK: "SK-B", DE: "DE-B", UK: "UK-B" }[country] || "XX-B";
  return `${prefix}-${String(i + 1).padStart(4, "0")}`;
}

function makeName(country, i, sector) {
  const seed = i * 7 + (country.charCodeAt(0) || 0);
  const adj = pickRandom(["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Vega", "Orion", "Apex", "Nova", "Prime", "Euro", "Royal", "Elite", "Vita", "Nord", "Pol", "East", "West", "Star", "Sun"], seed);
  const core = sector === "PowerMatic" ? "PowerMatic" : sector === "Hawk" ? "Hawk" : pickRandom(["BongGo", "DarkHorse", "TopMatic", "VapeHub", "TobaccoCo", "CigarPro", "FilterKing", "SmokeShop"], seed);
  const suf = pick(SUFFIXES, seed);
  return `${adj} ${core} ${suf}`;
}

function makePhone(country, i) {
  if (country === "PL") return `+48 ${500 + (i % 200)} ${100 + (i % 800)} ${10 + (i % 90)}`;
  if (country === "CZ") return `+420 ${600 + (i % 200)} ${100 + (i % 800)} ${10 + (i % 90)}`;
  if (country === "SK") return `+421 9${10 + (i % 80)} ${100 + (i % 800)} ${10 + (i % 90)}`;
  if (country === "DE") return `+49 30 ${1000000 + i * 17}`;
  if (country === "UK") return `+44 20 ${1000 + i * 13}`;
  return "+00 000 000 000";
}

function makeEmail(name, i) {
  const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-+|-+$/g, "").slice(0, 30);
  return `kontakt-${i}@${slug || "firma"}.pl`;
}

function makeDomain(name, country) {
  const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-+|-+$/g, "").slice(0, 20);
  const tld = { PL: "pl", CZ: "cz", SK: "sk", DE: "de", UK: "co.uk" }[country] || "com";
  return `https://${slug || "firma"}.${tld}`;
}

function dateString(daysAgo) {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString().slice(0, 10);
}

let CACHED = null;

export function getSampleLeads() {
  if (CACHED) return CACHED;

  const countries = ["PL", "PL", "PL", "PL", "PL", "PL", "PL", "PL", "CZ", "CZ", "CZ", "SK", "SK", "DE", "UK"];
  const out = [];
  let i = 0;
  while (out.length < 120) {
    const country = pickRandom(countries, i);
    const profile = pickRandom(BRAND_PROFILES, i);
    const tier = pickRandom(TIERS, i);
    const volume = pickRandom(VOLUMES, i + 3);
    const confidence = 50 + ((i * 13) % 51);
    const isDistributor = (i % 3) !== 0; // ~2/3 claim distribution
    const city = pickRandom(CITIES[country] || ["—"], i + 1);
    const name = makeName(country, i, profile.variant === "PowerMatic" ? "PowerMatic" : profile.variant === "Hawk" ? "Hawk" : "Other");
    const first = pickRandom(FIRST_NAMES, i + 2);
    const last = pickRandom(LAST_NAMES, i + 5);
    const phone = makePhone(country, i);
    const email = makeEmail(name, i);
    const www = makeDomain(name, country);
    const street = pickRandom(STREETS, i + 4);
    const streetNum = 1 + (i % 200);
    const postal = (10 + (i % 90)).toString().padStart(2, "0") + "-" + (100 + (i % 800));
    const rejestr = country === "PL"
      ? (tier === "marketplace" ? `JDG (CEIDG)` : `KRS ${String(100000 + i).padStart(10, "0")}`)
      : country === "CZ"
      ? `CZ ${100000 + i}`
      : country === "SK"
      ? `SK ${100000 + i}`
      : country === "DE"
      ? `HRB ${100000 + i}`
      : `UK ${100000 + i}`;
    const nip = country === "PL"
      ? `PL${1000000000 + i * 31}`
      : country === "CZ"
      ? `CZ${1000000000 + i * 31}`
      : country === "SK"
      ? `SK${1000000000 + i * 31}`
      : country === "DE"
      ? `DE${100000000 + i * 11}`
      : `GB${100000000 + i * 11}`;
    const category = pickRandom(["A1", "A2", "B1", "B2", "B3", "B6", "B8", "C1"], i);
    const notes = isDistributor
      ? pickRandom(DISTRIBUTOR_NOTES, i + 7)
      : pickRandom(NON_DISTRIBUTOR_NOTES, i + 7);

    out.push({
      id: makeId(country, i),
      nazwa_firmy: name,
      kraj: country,
      miasto: city,
      adres: `${street} ${streetNum}, ${postal} ${city}`,
      www,
      wolumen: volume,
      confidence_wolumen: `${confidence}%`,
      rejestr_id: rejestr,
      nip_vat: nip,
      rok_zalozenia: 2000 + (i % 25),
      tier,
      marki_nabijarki: profile.marki,
      marka_wlasna_oem: i % 5 === 0 ? "tak" : "nie",
      powinowactwo_nabijarki: profile.variant.startsWith("PowerMatic")
        ? (i % 2 === 0 ? "wysoki" : "średni")
        : profile.variant === "Hawk"
        ? "średni"
        : "niski",
      cross_sell_potential: confidence > 80 ? "High" : confidence > 60 ? "Medium" : "Low",
      kategoria: category,
      rynek_skala: pickRandom(["Lokalny", "Krajowy", "Krajowy / UE", "Regionalny", "Międzynarodowy"], i + 6),
      kanal_sprzedaży: tier === "marketplace"
        ? "Allegro / własny sklep"
        : tier === "reseller"
        ? "Hurtownia + sieci"
        : tier === "detalista"
        ? "Sklep stacjonarny"
        : "Hurt + Detal",
      kanal_zamiennik: "—",
      decydent: `${first} ${last}`,
      stanowisko: tier === "marketplace" ? "właściciel" : tier === "producent" ? "Prezes Zarządu" : "Dyrektor Handlowy",
      email_decydent: email,
      email: `biuro@${name.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 15) || "firma"}.${country === "PL" ? "pl" : country === "CZ" ? "cz" : "com"}`,
      telefon: phone,
      notatki: notes,
      linkedin: `https://linkedin.com/company/${name.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 20)}`,
      facebook: `https://facebook.com/${name.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 20)}`,
      instagram: i % 2 === 0 ? `https://instagram.com/${name.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 20)}` : "",
      tiktok: i % 4 === 0 ? `https://tiktok.com/@${name.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 15)}` : "",
      data_weryfikacji: dateString(i % 30),
      sourcing: "KRS / CEIDG + web search",
      zrodlo_danych: "API + manual",
      flagi: ["FROZEN (API)", "Verified"].concat(isDistributor ? ["ClaimDistributor"] : []),
      related_to: null,
    });
    i++;
  }
  CACHED = out;
  return out;
}
