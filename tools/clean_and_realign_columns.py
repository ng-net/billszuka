#!/usr/bin/env python3
"""
clean_and_realign_columns.py — Cleans company names, realigns misplaced data,
and normalizes columns across BILLSzuka catalog files.

Rules:
1. Removes parenthetical website domains from nazwa -> populates www / notatki.
2. Removes parenthetical descriptors (e.g. "(hurtownia tytoniu)", "(maszynki...)") -> populates notatki / marki_nabijarki.
3. Fixes emails mistakenly placed in telefon field (e.g. CZ-X-002, PL-X-034, SI-X-001).
4. Normalizes misplaced sourcing text (e.g. LT-B-011).
"""

import csv
import glob
import os
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def clean_row(row: dict, filename: str) -> tuple[dict, list[str]]:
    changes = []
    
    # 1. Fix emails and multi-values in telefon column
    telefon = str(row.get("telefon") or "").strip()
    if "@" in telefon and not re.search(r"^\+?[0-9\s\-()]{7,}$", telefon):
        email_cand = telefon
        if not row.get("email") or str(row.get("email")).strip() in ("", "-", "n/a", "brak"):
            row["email"] = email_cand
            changes.append(f"telefon -> email: {email_cand}")
        elif not row.get("email_decydent") or str(row.get("email_decydent")).strip() in ("", "-", "n/a", "brak"):
            row["email_decydent"] = email_cand
            changes.append(f"telefon -> email_decydent: {email_cand}")
        row["telefon"] = ""
        changes.append("cleared invalid phone string")
    elif "do potwierdzenia" in telefon.lower() or "xx" in telefon.lower():
        notatki = str(row.get("notatki") or "")
        row["notatki"] = (notatki + f" | Telefon roboczy: {telefon}").strip(" |")
        row["telefon"] = ""
        changes.append(f"moved placeholder phone to notatki: {telefon}")
    elif "|" in telefon or "(" in telefon:
        # Extract primary phone
        phones = [p.strip() for p in telefon.split("|") if p.strip()]
        primary = re.sub(r"\(.*?\)", "", phones[0]).strip()
        if re.search(r"[\+\d][\d\s\-\(\)]{5,}", primary):
            row["telefon"] = primary
            if len(phones) > 1 or "(" in telefon:
                notatki = str(row.get("notatki") or "")
                if telefon not in notatki:
                    row["notatki"] = (notatki + f" | Wszystkie telefony: {telefon}").strip(" |")
            changes.append(f"cleaned multi-phone: {telefon} -> {primary}")

    # 1b. Fix URLs and clean notes from www / socials
    for url_col in ["www", "facebook", "instagram", "linkedin", "tiktok", "kanal_zamiennik"]:
        val = str(row.get(url_col) or "").strip()
        if val:
            if "(do potwierdzenia)" in val.lower():
                cleaned_val = re.sub(r"\s*\(do potwierdzenia\)\s*", "", val, flags=re.I).strip()
                row[url_col] = cleaned_val
                notatki = str(row.get("notatki") or "")
                if f"{url_col} do potwierdzenia" not in notatki.lower():
                    row["notatki"] = (notatki + f" | {url_col}: do potwierdzenia").strip(" |")
                changes.append(f"stripped (do potwierdzenia) from {url_col}: {cleaned_val}")
                val = cleaned_val

            if url_col == "www" and "|" in val:
                urls = [u.strip() for u in val.split("|") if u.strip()]
                row["www"] = urls[0]
                if len(urls) > 1 and not row.get("kanal_zamiennik"):
                    row["kanal_zamiennik"] = urls[1]
                    changes.append(f"split www: primary={urls[0]}, kanal_zamiennik={urls[1]}")
                else:
                    notatki = str(row.get("notatki") or "")
                    row["notatki"] = (notatki + f" | Dodatkowe WWW: {', '.join(urls[1:])}").strip(" |")
                    changes.append(f"split www: primary={urls[0]}, extra to notatki")

    # 2. Fix misplaced sourcing text
    sourcing = str(row.get("sourcing") or "").strip()
    if sourcing and len(sourcing) > 30 and not any(k.lower() in sourcing.lower() for k in ["chiny", "europa", "polska", "mix", "import", "dystrybucja", "produkcja"]):
        kraj_code = str(row.get("kraj") or "krajowa").strip()
        row["sourcing"] = f"{kraj_code} (dystrybucja krajowa)"
        notatki = str(row.get("notatki") or "")
        row["notatki"] = (notatki + " | Profil/Sourcing: " + sourcing).strip(" |")
        changes.append(f"fixed verbose sourcing: {sourcing[:25]}... -> {row['sourcing']}")

    # 3. Clean nazwa
    nazwa = str(row.get("nazwa") or "").strip()
    if nazwa:
        # Check for trailing parentheses: "Firma Sp. z o.o. (something)"
        m_paren = re.search(r"\s*\((.*?)\)\s*$", nazwa)
        if m_paren:
            content = m_paren.group(1).strip()
            clean_name = nazwa[:m_paren.start()].strip()
            
            # Check if content is a domain / URL (e.g. cotyshop.ro, Plnicky-Powermatic.cz)
            is_domain = bool(re.search(r"\.[a-z]{2,4}(\/.*)?$", content, re.I)) or "www." in content.lower() or "http" in content.lower()
            # Check if content is a brand or descriptor
            is_brand = bool(re.search(r"^brand:\s*", content, re.I))
            is_product_desc = bool(re.search(r"maszyn|nabijark|hurtowni|dystryb|sklep|tyto|fmcg|vape|bongo|shisha|blet|art\.|sprzeda|import", content, re.I))
            
            # Do not strip official legal forms or Cyrillic translations if they are the primary entity description
            is_cyrillic_translit = bool(re.search(r"^[A-Za-z0-9\s\.\,\-\&]+$", content)) and bool(re.search(r"[\u0400-\u04FF]", clean_name)) and not (is_domain or is_product_desc)

            if (is_domain or is_brand or is_product_desc) and not is_cyrillic_translit:
                if len(clean_name) >= 3:
                    row["nazwa"] = clean_name
                    changes.append(f"cleaned nazwa: \"{nazwa}\" -> \"{clean_name}\"")
                    
                    # Handle domain
                    if is_domain:
                        domain_clean = re.sub(r"^brand:\s*", "", content, flags=re.I).strip()
                        if not row.get("www") or str(row.get("www")).strip() in ("", "-", "n/a", "brak"):
                            url_formatted = domain_clean if domain_clean.startswith("http") else f"https://{domain_clean}"
                            row["www"] = url_formatted
                            changes.append(f"set www from name: {url_formatted}")
                        else:
                            # Append to notatki if not present
                            notatki = row.get("notatki", "")
                            if domain_clean.lower() not in notatki.lower():
                                row["notatki"] = (notatki + f" | Brand/Web: {domain_clean}").strip(" |")
                                changes.append(f"added domain to notatki: {domain_clean}")
                    
                    # Handle product/machine descriptor
                    if is_product_desc:
                        # If mentions maszynki/nabijarki, ensure marki_nabijarki has context
                        if re.search(r"maszyn|nabijark", content, re.I):
                            marki = row.get("marki_nabijarki", "")
                            if not marki or marki.strip() in ("", "-", "n/a", "brak"):
                                row["marki_nabijarki"] = content
                                changes.append(f"set marki_nabijarki from name: {content}")
                            else:
                                notatki = row.get("notatki", "")
                                if content.lower() not in notatki.lower():
                                    row["notatki"] = (notatki + f" | Asortyment: {content}").strip(" |")
                                    changes.append(f"added machine desc to notatki: {content}")
                        else:
                            notatki = row.get("notatki", "")
                            if content.lower() not in notatki.lower():
                                row["notatki"] = (notatki + f" | Profil: {content}").strip(" |")
                                changes.append(f"added profile desc to notatki: {content}")

    return row, changes


def process_all_catalogs():
    all_files = sorted(glob.glob(str(DATA_DIR / "**/*.csv"), recursive=True))
    total_modified_files = 0
    total_changes = 0
    
    for fpath in all_files:
        if "validation-reports" in fpath or "archive" in fpath or "relationships" in fpath or "faq" in fpath:
            continue
        
        try:
            with open(fpath, "r", encoding="utf-8") as fp:
                reader = csv.DictReader(fp)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
            
            file_changes = 0
            cleaned_rows = []
            for r in rows:
                r_clean = {k: v for k, v in r.items() if k is not None}
                cleaned_r, chgs = clean_row(r_clean, os.path.basename(fpath))
                if chgs:
                    file_changes += len(chgs)
                # Keep only valid fieldnames
                final_r = {k: cleaned_r.get(k, "") for k in fieldnames if k is not None}
                cleaned_rows.append(final_r)
            
            if file_changes > 0:
                with open(fpath, "w", encoding="utf-8", newline="") as fp:
                    writer = csv.DictWriter(fp, fieldnames=[k for k in fieldnames if k is not None], extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(cleaned_rows)
                
                total_modified_files += 1
                total_changes += file_changes
                print(f"Updated {os.path.basename(fpath)}: {file_changes} modifications.")
        except Exception as e:
            print(f"Error processing {fpath}: {e}")

    print(f"\nCompleted: {total_changes} changes across {total_modified_files} files.")

if __name__ == "__main__":
    process_all_catalogs()
