#!/usr/bin/env python3
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Import db directly
sys.path.insert(0, str(ROOT / "tools"))
import db

def migrate():
    print("Migrating catalog CSVs to legacy user...")
    legacy_cat = DATA / "users" / "legacy" / "catalogs"
    legacy_cat.mkdir(parents=True, exist_ok=True)
    
    with db.connect() as conn:
        for csv_file in DATA.glob("*.csv"):
            if csv_file.name in ("master.csv", "relationships.csv"):
                continue
            
            size = csv_file.stat().st_size
            dest = legacy_cat / csv_file.name
            if not dest.exists():
                shutil.move(str(csv_file), str(dest))
                print(f"Moved {csv_file.name}")
                conn.execute(
                    "INSERT OR IGNORE INTO catalog_files (filename, uploaded_by, uploaded_at, size_bytes) VALUES (?, ?, ?, ?)",
                    (csv_file.name, "legacy", datetime.now(timezone.utc).isoformat(), size)
                )

    print("Migrating knowledge files...")
    legacy_know = DATA / "users" / "legacy" / "knowledge"
    legacy_know.mkdir(parents=True, exist_ok=True)
    
    index_path = DATA / "knowledge" / "index.json"
    if index_path.exists():
        import json
        items = json.loads(index_path.read_text(encoding="utf-8"))
        changed = False
        for item in items:
            if "uploaded_by" not in item or not item["uploaded_by"]:
                item["uploaded_by"] = "legacy"
                changed = True
            
            local_path = ROOT / item["local_path"]
            if local_path.exists():
                user = item["uploaded_by"]
                user_know = DATA / "users" / user / "knowledge"
                user_know.mkdir(parents=True, exist_ok=True)
                
                dest = user_know / local_path.name
                if not dest.exists() and dest != local_path:
                    shutil.move(str(local_path), str(dest))
                    item["local_path"] = str(dest.relative_to(ROOT))
                    changed = True
        
        if changed:
            index_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
            print("Updated knowledge index.")
            
    print("Done.")

if __name__ == "__main__":
    db.init()
    migrate()
