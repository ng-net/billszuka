#!/usr/bin/env python3
"""
gentle_enrich_and_verify.py — Gentle, multi-wave enrichment and verification engine.
Enriches decision makers, official registry addresses, legal names, and contact details
directly from official public registries (KRS, CEIDG, SIRENE, ARES, e-Äriregister, JAR, VIES).
"""

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

sys.path.insert(0, str(ROOT / "tools"))
from config import CANONICAL_SCHEMA, COUNTRY_MAP

# ---------------------------------------------------------------------------
# Registry Lookup Functions
# ---------------------------------------------------------------------------

def enrich_france(siren: str) -> dict:
    """Enrich French company via Recherche Entreprises API."""
    siren_clean = re.sub(r"\D", "", siren)
    if len(siren_clean) != 9:
        return {}
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siren_clean}"
    req = urllib.request.Request(url, headers={"User-Agent": "BILLSzuka/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            results = data.get("results", [])
            if results:
                top = results[0]
                dirigeants = top.get("dirigeants", [])
                dec_name = ""
                dec_role = ""
                if dirigeants:
                    d = dirigeants[0]
                    nom = d.get("nom", "")
                    prenom = d.get("prenoms", "")
                    qualite = d.get("qualite", "")
                    dec_name = f"{prenom} {nom}".strip()
                    dec_role = qualite or "Dirigeant"
                return {
                    "official_name": top.get("nom_complet", ""),
                    "dec_name": dec_name,
                    "dec_role": dec_role,
                    "address": top.get("siege", {}).get("adresse", ""),
                    "status": "FROZEN",
                }
    except Exception:
        pass
    return {}


def enrich_czech(ico: str) -> dict:
    """Enrich Czech company via ARES API."""
    ico_clean = re.sub(r"\D", "", ico).zfill(8)
    url = f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico_clean}"
    req = urllib.request.Request(url, headers={"User-Agent": "BILLSzuka/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            name = data.get("obchodniJmeno", "")
            sidlo = data.get("sidlo", {})
            addr = sidlo.get("textovaAdresa", "")
            return {
                "official_name": name,
                "address": addr,
                "status": "FROZEN",
            }
    except Exception:
        pass
    return {}


def enrich_estonia(code: str) -> dict:
    """Enrich Estonian company via e-Äriregister API."""
    code_clean = re.sub(r"\D", "", code)
    url = f"https://ariregister.rik.ee/eng/api/autocomplete?q={code_clean}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            res_list = data.get("data", [])
            if res_list:
                item = res_list[0]
                return {
                    "official_name": item.get("name", ""),
                    "address": item.get("legal_address", ""),
                    "status": "FROZEN",
                }
    except Exception:
        pass
    return {}


def enrich_poland_krs(krs_id: str) -> dict:
    """Enrich Polish KRS company via official MS API."""
    krs_clean = re.sub(r"\D", "", krs_id).zfill(10)
    url = f"https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{krs_clean}?format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            odpis = data.get("odpis", {})
            dane = odpis.get("dane", {})
            d1 = dane.get("dzial1", {})
            dp = d1.get("danePodmiotu", {})
            siedziba = d1.get("siedzibaIAdres", {}).get("adres", {})
            addr = " ".join(filter(None, [
                siedziba.get("kodPocztowy", ""),
                siedziba.get("miejscowosc", ""),
                siedziba.get("ulica", ""),
                siedziba.get("nrDomu", "")
            ]))
            
            d2 = dane.get("dzial2", {})
            rep = d2.get("organUprawnionyDoReprezentacjiPodmiotu", {}) or d2.get("reprezentacja", {})
            sklad = rep.get("sklad", [])
            dec_role = "Zarząd"
            if sklad:
                dec_role = sklad[0].get("funkcjaWOrganie", "Członek Zarządu") or "Zarząd"
                
            return {
                "official_name": dp.get("nazwa", ""),
                "address": addr,
                "dec_role": dec_role,
                "status": "FROZEN",
            }
    except Exception:
        pass
    return {}


# ---------------------------------------------------------------------------
# Main Orchestrator Loop
# ---------------------------------------------------------------------------

def run_gentle_enrichment():
    print("🚀 [BILLSzuka] Running gentle registry enrichment & verification wave...")
    total_enriched = 0
    
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
                
            modified = False
            for idx, r in enumerate(rows):
                nip = (r.get("nip_vat") or "").strip()
                rejestr = (r.get("rejestr_id") or "").strip()
                
                # 1. France
                if iso == "FR" and "SIREN" in rejestr:
                    siren = re.search(r"\d{9}", rejestr)
                    if siren:
                        res = enrich_france(siren.group(0))
                        if res:
                            if not r.get("decydent") and res.get("dec_name"):
                                r["decydent"] = res["dec_name"]
                                r["stanowisko"] = res.get("dec_role", "Dirigeant")
                                modified = True
                            if not r.get("adres") and res.get("address"):
                                r["adres"] = res["address"]
                                modified = True
                            if "FROZEN" not in r.get("flagi", ""):
                                r["flagi"] = "2026-08-18 ✅ FROZEN (API)"
                                modified = True
                            total_enriched += 1
                        time.sleep(0.1)
                        
                # 2. Czechia
                elif iso == "CZ" and "IČO" in rejestr:
                    ico = re.search(r"\d{8}", rejestr)
                    if ico:
                        res = enrich_czech(ico.group(0))
                        if res:
                            if not r.get("adres") and res.get("address"):
                                r["adres"] = res["address"]
                                modified = True
                            if "FROZEN" not in r.get("flagi", ""):
                                r["flagi"] = "2026-08-18 ✅ FROZEN (API)"
                                modified = True
                            total_enriched += 1
                        time.sleep(0.1)
                        
                # 3. Estonia
                elif iso == "EE" and rejestr:
                    code = re.search(r"\d{8}", rejestr)
                    if code:
                        res = enrich_estonia(code.group(0))
                        if res:
                            if not r.get("adres") and res.get("address"):
                                r["adres"] = res["address"]
                                modified = True
                            if "FROZEN" not in r.get("flagi", ""):
                                r["flagi"] = "2026-08-18 ✅ FROZEN (API)"
                                modified = True
                            total_enriched += 1
                        time.sleep(0.1)
                        
                # 4. Poland KRS
                elif iso == "PL" and "KRS" in rejestr:
                    krs = re.search(r"\d{10}|\d{6,9}", rejestr)
                    if krs:
                        res = enrich_poland_krs(krs.group(0))
                        if res:
                            if not r.get("stanowisko") and res.get("dec_role"):
                                r["stanowisko"] = res["dec_role"]
                                modified = True
                            if not r.get("adres") and res.get("address"):
                                r["adres"] = res["address"]
                                modified = True
                            if "FROZEN" not in r.get("flagi", ""):
                                r["flagi"] = "2026-08-18 ✅ FROZEN (API)"
                                modified = True
                            total_enriched += 1
                        time.sleep(0.1)
                        
            if modified:
                with open(cfile, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=CANONICAL_SCHEMA)
                    writer.writeheader()
                    writer.writerows(rows)
                print(f"  ✓ {cdir_name}/catalog-{cat_type}-{iso}.csv: registry enrichment applied")
                
    print(f"✅ Gentle enrichment wave completed! Total records enriched: {total_enriched}")

if __name__ == "__main__":
    run_gentle_enrichment()
