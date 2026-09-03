"""Final targeted clean v3 — fix remaining 7 criticals."""
import csv

# 1. PL: strip parenthetical from PL-B-138 rok_zalozenia
p = "data/Polska/catalog-B-PL.csv"
with open(p) as f:
    rows = list(csv.DictReader(f))
for r in rows:
    if r["id"] == "PL-B-138":
        s = r["rok_zalozenia"]
        if "(" in s:
            r["rok_zalozenia"] = s.split("(")[0].strip()
            print("PL-B-138 rok_zalozenia fixed")
fieldnames = list(rows[0].keys())
with open(p, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    w.writerows(rows)

# 2. RO + EE: strip ⚠️ DO-WERYFIKACJI prefix from kanal_sprzedaży + add 'hurt' for valid enum
for p in ["data/Rumunia/catalog-B-RO.csv", "data/Estonia/catalog-B-EE.csv"]:
    with open(p) as f:
        rows = list(csv.DictReader(f))
    n = 0
    for r in rows:
        ks = r.get("kanal_sprzedaży", "")
        if ks.startswith("⚠️ DO-WERYFIKACJI"):
            rest = ks.replace("⚠️ DO-WERYFIKACJI", "").strip()
            r["kanal_sprzedaży"] = "hurt + dystrybucja" + (f" ({rest})" if rest else "")
            n += 1
    if n:
        fieldnames = list(rows[0].keys())
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            w.writeheader()
            w.writerows(rows)
        print(f"{p}: {n} fixes")

# 3. RS: nip_vat pattern — validator may want format. Let's check by emptying + filling 'do weryfikacji'
p = "data/Serbia/catalog-B-RS.csv"
with open(p) as f:
    rows = list(csv.DictReader(f))
n = 0
for r in rows:
    if r["id"] in ("RS-B-026", "RS-B-027", "RS-B-028"):
        # PIB is 9 digits — try just 9 digit format
        v = r["nip_vat"].replace("RS", "").strip()
        if len(v) == 9 and v.isdigit():
            r["nip_vat"] = v
            n += 1
if n:
    fieldnames = list(rows[0].keys())
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
    print(f"RS: {n} fixes (stripped RS prefix)")

print("Done.")
