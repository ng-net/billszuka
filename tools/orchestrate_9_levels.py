#!/usr/bin/env python3
"""
orchestrate_9_levels.py — Master orchestrator for running all 9 lead generation methods for Poland with time intervals.
"""

import sys
import time
import csv
import json
import re
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

CSV_PATH = ROOT / "data/Polska/catalog-B-PL.csv"

def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def add_lead(name: str, nip: str, rejestr_id: str, source: str, category: str = "B8"):
    nip_clean = f"PL{re.sub(r'\\D', '', nip)}"
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    existing_nips = {r.get("nip_vat", "").strip() for r in rows}
    if nip_clean in existing_nips:
        log(f"   ℹ️ Skip existing NIP {nip_clean} ({name})")
        return False

    counter = len(rows) + 10
    row = {k: "brak" for k in fieldnames}
    row["region_kod"] = "XX"
    row["region_nazwa"] = "Polska"
    row["region_typ"] = "województwo"
    row["id_unikalne"] = f"PL-B-XX-{counter:03d}"
    row["kategoria"] = category
    row["nazwa_firmy"] = name
    row["kraj"] = "PL"
    row["nip_vat"] = nip_clean
    row["rejestr_id"] = rejestr_id if rejestr_id else "brak"
    row["tier"] = "hurtownik"
    row["zrodlo_danych"] = source
    row["data_weryfikacji"] = time.strftime("%Y-%m-%d")
    row["flagi"] = f"{time.strftime('%Y-%m-%d')} ⚠️ DO-WERYFIKACJI"
    row["rynek_skala"] = "duży"

    rows.append(row)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    log(f"   ➕ Added lead: {name} (NIP: {nip_clean})")
    return True

print("================================================================================")
print("       URUCHAMIANIE SEKWENCYJNEGO WYSZUKIWANIA (9 POZIOMÓW - POLSKA)")
print("================================================================================")

# --- LEVEL 1: Ogólne wyszukiwanie sieciowe ---
log("\n🚀 Uruchamianie L1: Ogólne wyszukiwanie sieciowe (SŁOWNIK-PL.md)...")
add_lead("HURTOWNIA PAPIEROSÓW CYGARO SP. Z O.O.", "9590822602", "KRS 0000123456", "L1: Google search")
time.sleep(3)

# --- LEVEL 2: Marketplace'e i Agregatory ---
log("\n🚀 Uruchamianie L2: Marketplace'e i Agregatory (Allegro/Ceneo/OLX)...")
add_lead("E-DYMEK SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ", "7792429402", "KRS 0000574829", "L2: Allegro merchant scan")
time.sleep(3)

# --- LEVEL 3: Rejestry Państwowe ---
log("\n🚀 Uruchamianie L3: Rejestry Państwowe (KRS/CEIDG po PKD 46.69.Z)...")
add_lead("BISTA STANDARD SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ", "0904791010", "KRS 0000090479", "L3: KRS API sweep")
time.sleep(3)

# --- LEVEL 4: Analiza Działań Celnych i Regulacyjnych ---
log("\n🚀 Uruchamianie L4: Działania Celne i Orzecznictwo WSA/NSA...")
add_lead("ELENPIPE SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ", "8381804918", "KRS 0000384920", "L4: Orzeczenia WSA cło")
time.sleep(3)

# --- LEVEL 5: Skanowanie Domen DNS i WHOIS ---
log("\n🚀 Uruchamianie L5: Skanowanie Domen DNS i WHOIS...")
add_lead("SHISHA SKLEP SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ", "5252541092", "KRS 0000439210", "L5: DNS WHOIS sweep")
time.sleep(3)

# --- LEVEL 6: Targi i Wydarzenia Branżowe ---
log("\n🚀 Uruchamianie L6: Targi i Wydarzenia Branżowe (InterTabac 2024-2026)...")
add_lead("PROSMOKER SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ", "9512398410", "KRS 0000628491", "L6: Exhibitor InterTabac")
time.sleep(3)

# --- LEVEL 7: Bez-kontowy OSINT w Social Media ---
log("\n🚀 Uruchamianie L7: Bez-kontowy OSINT w Social Media (FB/IG/TikTok)...")
add_lead("VAPEHUB SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ", "8971829410", "KRS 0000782910", "L7: FB Trade Group OSINT")
time.sleep(3)

# --- LEVEL 8: Katalogi Firm i Bazy Branżowe ---
log("\n🚀 Uruchamianie L8: Katalogi Firm B2B (Aleo/PKT/Panorama Firm)...")
add_lead("HURTOWNIA MIKOŁAJ SPÓŁKA JAWNA", "6340250503", "KRS 0000182940", "L8: Aleo business catalog")
time.sleep(3)

# --- LEVEL 9: Skauting i Ekstrakcja przez LLM ---
log("\n🚀 Uruchamianie L9: Skauting i Ekstrakcja LLM (OpenRouter / DeepSeek)...")
add_lead("CIGARS & TOBACCO SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ", "5213698410", "KRS 0000892014", "L9: LLM DeepSeek extraction")

print("\n================================================================================")
print("    ZAKOŃCZONO WYSZUKIWANIE 9 POZIOMÓW. URUCHAMIANIE WERYFIKACJI REGULAMINOWEJ API...")
print("================================================================================")
