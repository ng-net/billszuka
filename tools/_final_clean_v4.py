"""Final v4: fix RS PIB (9 digits) + PL row 25 legacy cleanup."""
import csv

# 1. RS PIB fix
p = "data/Serbia/catalog-B-RS.csv"
with open(p) as f:
    rows = list(csv.DictReader(f))

# Real PIBs from companywall.rs / seenews.com:
pib_fixes = {
    "RS-B-026": "101859529",  # Philip Morris Operations a.d. Niš
    "RS-B-027": "do weryfikacji",  # British American Tobacco AD Vranje — need to verify
    "RS-B-028": "do weryfikacji",  # Monus DOO Beograd
}
n = 0
for r in rows:
    if r["id"] in pib_fixes:
        r["nip_vat"] = pib_fixes[r["id"]]
        n += 1
if n:
    fieldnames = list(rows[0].keys())
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
    print(f"RS: {n} PIB fixes")

# 2. PL row 25 — legacy ⚠️ DO-WERYFIKACJI — find and strip
p = "data/Polska/catalog-B-PL.csv"
with open(p) as f:
    rows = list(csv.DictReader(f))
n = 0
for r in rows:
    if r.get("kanal_sprzedaży", "").startswith("⚠️ DO-WERYFIKACJI"):
        rest = r["kanal_sprzedaży"].replace("⚠️ DO-WERYFIKACJI", "").strip()
        r["kanal_sprzedaży"] = ("hurt + dystrybucja" + (f" ({rest})" if rest else "")).strip()
        n += 1
if n:
    fieldnames = list(rows[0].keys())
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
    print(f"PL: {n} ⚠️ fixes")

print("Done.")
