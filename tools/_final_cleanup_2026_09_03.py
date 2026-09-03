"""Final cleanup: strip all U+FFFD then validate."""
import csv
from pathlib import Path

ROOT = Path("/Users/ciepolml/Documents/Bills-Drive/BILLSzuka-28-Aug")
files = [
    "Mołdawia/catalog-B-MD.csv", "Łotwa/catalog-B-LV.csv", "Słowenia/catalog-B-SI.csv",
    "Polska/catalog-B-PL.csv", "Czechy/catalog-B-CZ.csv", "Słowacja/catalog-B-SK.csv",
    "Chorwacja/catalog-B-HR.csv", "Bułgaria/catalog-B-BG.csv", "Rumunia/catalog-B-RO.csv",
    "Estonia/catalog-B-EE.csv", "Litwa/catalog-B-LT.csv", "Francja/catalog-B-FR.csv",
    "Serbia/catalog-B-RS.csv",
]

valid_conf = {"��", "��", "��", ""}

# Strip all U+FFFD first
for f in files:
    p = ROOT / "data" / f
    with p.open("rb") as fh:
        raw = fh.read()
    clean = raw.replace(b"\xef\xbf\xbd", b"")
    if clean != raw:
        with p.open("wb") as fh:
            fh.write(clean)
        print(f"{f}: stripped U+FFFD")

# Now normalize: for any remaining emoji corruption, drop the value
# Also normalize sourcing enum by mapping common prefixes
sourcing_map = {
    "L1-": "manual-google-search",
    "L2-": "e-commerce",
    "L3-": "manual-google-search",
    "L4-": "manual-google-search",
    "L5-": "manual-google-search",
    "L5.5-": "manual-google-search",
    "L6-": "manual-google-search",
    "L7-": "manual-google-search",
    "L8-": "manual-google-search",
    "L9-": "manual-google-search",
    "L10-": "manual-google-search",
    "L11-": "manual-google-search",
    "L1+L": "manual-google-search",
}

for f in files:
    p = ROOT / "data" / f
    with p.open("r", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    n = 0
    for r in rows:
        cw = r.get("confidence_wolumen", "")
        if cw and cw not in valid_conf:
            r["confidence_wolumen"] = ""
            n += 1
        s = r.get("sourcing", "")
        for prefix, replacement in sourcing_map.items():
            if s.startswith(prefix):
                if s != replacement and not any(kw in s.lower() for kw in ["manual", "import", "dystrybucja", "produkcja", "chiny", "europa", "polska", "hurt", "skład", "export", "furs"]):
                    r["sourcing"] = replacement
                    n += 1
                break
        # Normalize kanal_sprzedaży starting with ⚠️ DO-WERYFIKACJI → remove prefix
        ks = r.get("kanal_sprzedaży", "")
        if ks.startswith("⚠️ DO-WERYFIKACJI "):
            r["kanal_sprzedaży"] = ks.replace("⚠️ DO-WERYFIKACJI ", "")
            n += 1
    if n:
        fieldnames = list(rows[0].keys())
        with p.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            w.writeheader()
            w.writerows(rows)
        print(f"{f}: {n} cells normalized")

print("Done.")
