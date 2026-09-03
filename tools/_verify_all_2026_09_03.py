"""Run validate_columns.py on all 13 country catalogs."""
import subprocess
from pathlib import Path

ROOT = Path("/Users/ciepolml/Documents/Bills-Drive/BILLSzuka-28-Aug")
files = [
    "data/Mołdawia/catalog-B-MD.csv", "data/Łotwa/catalog-B-LV.csv", "data/Słowenia/catalog-B-SI.csv",
    "data/Polska/catalog-B-PL.csv", "data/Czechy/catalog-B-CZ.csv", "data/Słowacja/catalog-B-SK.csv",
    "data/Chorwacja/catalog-B-HR.csv", "data/Bułgaria/catalog-B-BG.csv", "data/Rumunia/catalog-B-RO.csv",
    "data/Estonia/catalog-B-EE.csv", "data/Litwa/catalog-B-LT.csv", "data/Francja/catalog-B-FR.csv",
    "data/Serbia/catalog-B-RS.csv",
]
for f in files:
    p = ROOT / f
    if not p.exists():
        print(f"{f}: NOT FOUND")
        continue
    res = subprocess.run(["python3", "tools/validate_columns.py", "--csv", str(p)],
                          capture_output=True, text=True, cwd=ROOT)
    out_lines = [l for l in res.stdout.strip().splitlines() if "Files:" in l]
    out = out_lines[0] if out_lines else "(no summary)"
    print(f"  {f.split('/')[-1]:20s}: {out}")
