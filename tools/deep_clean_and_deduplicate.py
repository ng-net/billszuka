#!/usr/bin/env python3
"""
deep_clean_and_deduplicate.py — Comprehensive cleanup, deduplication,
placeholder removal, and verification across all 24 BILLSzuka catalogs.
"""

import csv
import glob
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

sys.path.insert(0, str(ROOT / "tools"))
from config import CANONICAL_SCHEMA, COUNTRY_MAP


def clean_pl_specifics(rows: list[dict]) -> list[dict]:
    """Clean and deduplicate Polish catalog B rows."""
    cleaned = []
    seen_nips = set()
    
    for r in rows:
        nip = re.sub(r"\W", "", r.get("nip_vat", "").upper())
        name = r.get("nazwa_firmy", "")
        
        # Fix Selgros NIP (was Eurocash's NIP by mistake)
        if "Selgros" in name or "Transgourmet" in name:
            r["nip_vat"] = "PL7792223933"
            r["rejestr_id"] = "KRS 0000203325"
            nip = "PL7792223933"
            
        # Deduplicate Carmen Polska (drop second identical entry)
        if nip == "PL8370001711":
            if "PL8370001711" in seen_nips:
                continue
            r["adres"] = "ul. Warszawska 93, 96-500 Sochaczew"
            r["rejestr_id"] = "KRS 0000108390"
            r["www"] = "https://www.carmen.pl"
            r["kategoria"] = "B8"
            
        # Deduplicate JUKA Akcesoria (keep rich entry)
        if nip == "PL9531380750":
            if "PL9531380750" in seen_nips:
                continue
            r["adres"] = "ul. Jabłoniowa 56B, 80-175 Gdańsk"
            r["rejestr_id"] = "CEIDG (NIP 9531380750)"
            r["www"] = "https://jukaakcesoria.pl"
            r["kategoria"] = "B4"
            
        # Deduplicate Eurocash Serwis (drop stub, keep rich entry)
        if nip == "PL7772304755":
            if "PL7772304755" in seen_nips:
                continue
            r["adres"] = "ul. Wiśniowa 11, 62-052 Komorniki"
            r["rejestr_id"] = "KRS 0000519553"
            r["www"] = "https://eurocashserwis.pl"
            r["kategoria"] = "B8"
            
        # Deduplicate Tabak Grupa in B (drop stub, keep rich entry)
        if nip == "PL6181914183":
            if "PL6181914183" in seen_nips:
                continue
            r["adres"] = "ul. Złota 126, 62-800 Kalisz"
            r["rejestr_id"] = "KRS 0000119343"
            r["www"] = "https://skleptytoniowy.pl"
            r["kategoria"] = "B4"
            
        if nip:
            seen_nips.add(nip)
        cleaned.append(r)
        
    return cleaned


def clean_all_catalogs():
    total_retained = 0
    
    for iso, cdir_name in COUNTRY_MAP.items():
        cdir = DATA_DIR / cdir_name
        if not cdir.is_dir():
            continue
            
        for cat_type in ["A", "B"]:
            cfile = cdir / f"catalog-{cat_type}-{iso}.csv"
            if not cfile.exists():
                continue
                
            with open(cfile, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            # Country-specific deduplication
            if iso == "PL" and cat_type == "B":
                rows = clean_pl_specifics(rows)
            elif iso == "LT" and cat_type == "B":
                # Philip Morris Baltic is already in Catalog A
                rows = [r for r in rows if r.get("nip_vat") != "LT100002442812" or "Lietuva" in r.get("nazwa_firmy", "")]
            elif iso == "MD" and cat_type == "B":
                # Tutun-CTC is in Catalog A
                rows = [r for r in rows if "Tutun-CTC" not in r.get("nazwa_firmy", "")]
            elif iso == "LV" and cat_type == "B":
                # Tabakas Nams Grupa is in Catalog A
                rows = [r for r in rows if r.get("nip_vat") != "LV50003223511"]
                
            # Clean fields for every row
            clean_rows = []
            for i, row in enumerate(rows, 1):
                # Clean unique ID
                row["id"] = f"{iso}-{cat_type}-{i:03d}"
                row["kraj"] = iso
                
                # Clean phone
                phone = (row.get("telefon") or "").strip()
                if phone in ["brak", "n/a", "-", "none", "null"]:
                    row["telefon"] = ""
                    
                # Clean email
                email = (row.get("email") or "").strip().lower()
                if email in ["brak", "n/a", "-", "none", "null"] or any(p in email for p in ["example.com", "test.com", "domain.com"]):
                    row["email"] = ""
                else:
                    row["email"] = email
                    
                # Clean URL
                www = (row.get("www") or "").strip()
                if www in ["brak", "n/a", "-", "none", "null"] or any(p in www.lower() for p in ["example.com", "test.com", "domain.com"]):
                    row["www"] = ""
                elif www and not (www.startswith("http://") or www.startswith("https://")):
                    row["www"] = "https://" + www
                    
                # Clean Decydent
                dec = (row.get("decydent") or "").strip()
                if dec.lower() in ["brak", "n/a", "-", "none", "null", "jan kowalski", "john doe", "director", "ceo", "owner", "manager"]:
                    row["decydent"] = ""
                    row["stanowisko"] = ""
                    
                # Ensure 35 canonical columns
                clean_row = {col: (row.get(col) or "").strip() for col in CANONICAL_SCHEMA}
                clean_rows.append(clean_row)
                
            # Write back atomically
            tmp_cfile = cfile.with_suffix(".csv.tmp")
            with open(tmp_cfile, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
                writer.writeheader()
                writer.writerows(clean_rows)
            os.replace(tmp_cfile, cfile)
                
            total_retained += len(clean_rows)
            print(f"  ✓ {cdir_name}/catalog-{cat_type}-{iso}.csv: {len(clean_rows)} clean records")
            
    print(f"\nTotal Clean Grounded Leads: {total_retained}")

if __name__ == "__main__":
    clean_all_catalogs()
