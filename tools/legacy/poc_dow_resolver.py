#!/usr/bin/env python3
"""
POC: Selenium/Playwright-based NIP+KRS resolver for 10 BILLSzuka DO-W firms.
Strategy: CEIDG web first, KRS-pobierz.pl fallback, VIES validation always.

Marceli 2026-08-11 — test na 10 firmach przed ewentualnym full run.
"""
import csv
import json
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ─────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path("/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka")
MASTER_CSV = PROJECT_ROOT / "data" / "master.csv"
POC_OUT = PROJECT_ROOT / "data" / "verification" / "poc_dow_resolver.json"
POC_LOG = PROJECT_ROOT / "data" / "verification" / "poc_dow_resolver.log"

# 10 firm: 5 z NIP (need KRS) + 5 bez NIP (need both)
SAMPLE_IDS = [
    "PL-A-PM-002", "PL-A-XX-002", "PL-A-MZ-001", "PL-A-LB-001", "PL-A-MZ-003",
    "PL-B-MA-001", "PL-B-LU-001", "PL-B-SL-002", "PL-B-XX-002", "PL-B-PD-002",
]

DELAY = 3.0  # sekundy między requestami (by nie triggerować anty-bot)
PAGE_TIMEOUT = 25

# ─────────────────────────────────────────────────────────────────
# UTILS
# ─────────────────────────────────────────────────────────────────
def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    POC_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(POC_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def nip_mod11_ok(nip: str) -> bool:
    """Wagi: 6,5,7,2,3,4,5,6,7 (ostatnia to checksum)"""
    nip = re.sub(r"\D", "", nip)
    if len(nip) != 10 or not nip.isdigit():
        return False
    wagi = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    s = sum(int(nip[i]) * wagi[i] for i in range(9))
    return (s % 11) == int(nip[9])


def normalize_name(s: str) -> str:
    s = re.sub(r"\s+", " ", s.upper().strip())
    s = s.replace('"', "").replace("'", "")
    s = re.sub(r"\bSPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ\b", "SP Z O O", s)
    s = re.sub(r"\bSPÓŁKA JAWNA\b", "SP J", s)
    s = re.sub(r"\bSP\.\s*Z\s*O\.?\s*O\.?\b", "SP Z O O", s)
    s = re.sub(r"\bSP\.\s*J\.?\b", "SP J", s)
    return s


def name_similarity(a: str, b: str) -> float:
    """Token-based Jaccard similarity."""
    ta = set(normalize_name(a).split())
    tb = set(normalize_name(b).split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


# ─────────────────────────────────────────────────────────────────
# VIES (HTTP, darmowe, bez Selenium)
# ─────────────────────────────────────────────────────────────────
def vies_check(nip: str) -> dict:
    nip_clean = re.sub(r"\D", "", nip)
    body = json.dumps({"countryCode": "PL", "vatNumber": nip_clean}).encode()
    req = urllib.request.Request(
        "https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number",
        data=body, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        return {"valid": False, "error": str(e)[:200]}


# ─────────────────────────────────────────────────────────────────
# KRS Open API (HTTP, darmowe, po KRS number)
# ─────────────────────────────────────────────────────────────────
def krs_lookup(krs_num: str) -> dict:
    krs_clean = re.sub(r"\D", "", krs_num).zfill(10)
    url = f"https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{krs_clean}?rejestr=P&format=json"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read().decode())
        podmiot = data.get("odpis", {}).get("dane", {}).get("dzial1", {}).get("danePodmiotu", {})
        return {
            "ok": True,
            "nazwa": podmiot.get("nazwa"),
            "nip": podmiot.get("identyfikatory", {}).get("nip"),
            "regon": podmiot.get("identyfikatory", {}).get("regon"),
            "forma": podmiot.get("formaPrawna"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ─────────────────────────────────────────────────────────────────
# CEIDG web (Selenium)
# ─────────────────────────────────────────────────────────────────
def ceidg_search(driver, firma_nazwa: str) -> dict:
    """Szukaj firmy w CEIDG web. Zwraca pierwszy NIP+adres jeśli znaleziony."""
    log(f"  → CEIDG search: {firma_nazwa[:50]}")
    result = {"found": False, "nip": None, "adres": None, "name": None, "error": None}
    try:
        # Clean name for search (drop "Sp. z o.o." etc)
        search_name = re.sub(r"\s+(SPÓŁKA|SP\.|SP)\s+.*$", "", firma_nazwa, flags=re.I).strip()
        if not search_name:
            search_name = firma_nazwa
        driver.get("https://www.biznes.gov.pl/pl/portal-uslugowym/ceidg")
        time.sleep(DELAY + 1)
        # Cookie consent
        try:
            consent = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='zgadzam' i], button#cookie-accept, .cookie-accept")
            consent.click()
            time.sleep(1)
        except Exception:
            pass
        # Find search box
        candidates = [
            (By.CSS_SELECTOR, "input[type='search']"),
            (By.CSS_SELECTOR, "input[placeholder*='Nazwa' i]"),
            (By.CSS_SELECTOR, "input[name*='nazwa' i]"),
            (By.CSS_SELECTOR, "input.search-input"),
            (By.CSS_SELECTOR, "input#searchQuery"),
        ]
        search = None
        for by, sel in candidates:
            try:
                search = WebDriverWait(driver, 5).until(EC.presence_of_element_located((by, sel)))
                if search:
                    break
            except Exception:
                continue
        if not search:
            result["error"] = "no search input"
            return result
        search.clear()
        search.send_keys(search_name)
        time.sleep(1)
        search.send_keys(Keys.RETURN)
        time.sleep(DELAY + 2)
        # Extract NIP from results
        html = driver.page_source
        # szukaj NIP w formacie 10 cyfr
        m = re.findall(r"\b(\d{10})\b", html)
        # Filtruj: NIP nie może być samymi zerami ani powtarzający się
        m = [x for x in m if not all(c == x[0] for c in x)]
        if m:
            result["found"] = True
            result["nip"] = m[0]
            log(f"    CEIDG NIP: {m[0]}")
        else:
            log("    CEIDG: brak NIP w wynikach")
    except Exception as e:
        result["error"] = str(e)[:200]
        log(f"    CEIDG error: {str(e)[:200]}")
    return result


# ─────────────────────────────────────────────────────────────────
# KRS-pobierz.pl (Selenium)
# ─────────────────────────────────────────────────────────────────
def krspobierz_search(driver, query: str) -> dict:
    """Szukaj KRS na krs-pobierz.pl. Query może być NIP lub nazwa."""
    log(f"  → KRS-pobierz.pl search: {query[:50]}")
    result = {"found": False, "krs": None, "nip": None, "nazwa": None, "error": None}
    try:
        url = f"https://krs-pobierz.pl/szukaj?query={urllib.request.quote(query)}"
        driver.get(url)
        time.sleep(DELAY + 2)
        html = driver.page_source
        # Szukaj KRS w formacie KRS 0000123456 lub 0000123456
        m = re.search(r"KRS[:\s]*(0?\d{7,10})", html)
        if m:
            krs_num = m.group(1).zfill(10)
            result["found"] = True
            result["krs"] = f"KRS {krs_num}"
            log(f"    KRS-pobierz: {result['krs']}")
        # Szukaj NIP też (może być w wyniku)
        nip_m = re.search(r"NIP[:\s]*(\d{10})", html, re.I)
        if nip_m:
            result["nip"] = nip_m.group(1)
        # Nazwa firmy
        name_m = re.search(r"<h\d[^>]*>([^<]{5,80})</h\d>", html)
        if name_m:
            result["nazwa"] = name_m.group(1).strip()
    except Exception as e:
        result["error"] = str(e)[:200]
        log(f"    KRS-pobierz error: {str(e)[:200]}")
    return result


# ─────────────────────────────────────────────────────────────────
# WWW firmy (Selenium) — szukaj NIP/KRS w stopce
# ─────────────────────────────────────────────────────────────────
def www_scrape(driver, url: str) -> dict:
    """Otwiera stronę firmy, szuka NIP/KRS w HTML/footer."""
    log(f"  → WWW scrape: {url[:60]}")
    result = {"found": False, "nip": None, "krs": None, "error": None}
    if not url or not url.startswith("http"):
        result["error"] = "no url"
        return result
    try:
        driver.get(url)
        time.sleep(DELAY + 1)
        html = driver.page_source
        # NIP: szukaj "NIP:" albo 10 cyfr
        nip_m = re.search(r"NIP[:\s]*PL?[:\s]*(\d{10})", html, re.I)
        if not nip_m:
            nip_m = re.search(r"\b(\d{10})\b", html)
        if nip_m and nip_mod11_ok(nip_m.group(1)):
            result["nip"] = nip_m.group(1)
            result["found"] = True
        # KRS
        krs_m = re.search(r"KRS[:\s]*(0?\d{7,10})", html, re.I)
        if krs_m:
            result["krs"] = f"KRS {krs_m.group(1).zfill(10)}"
            result["found"] = True
        if result["found"]:
            log(f"    WWW NIP: {result.get('nip')} KRS: {result.get('krs')}")
        else:
            log("    WWW: brak NIP/KRS w stopce")
    except Exception as e:
        result["error"] = str(e)[:200]
        log(f"    WWW error: {str(e)[:200]}")
    return result


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    # Load master
    rows_by_id = {}
    with open(MASTER_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["id"] in SAMPLE_IDS:
                rows_by_id[row["id"]] = row
    log(f"Loaded {len(rows_by_id)}/10 firms from master.csv")

    # Init Chrome
    log("Init Chrome (headless)...")
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--lang=pl-PL")
    opts.add_argument("--window-size=1280,800")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(PAGE_TIMEOUT)
    log("Chrome ready.")

    report = []
    for idx, fid in enumerate(SAMPLE_IDS, 1):
        if fid not in rows_by_id:
            log(f"[{idx}/10] {fid} NOT IN MASTER — skip")
            continue
        f = rows_by_id[fid]
        log(f"\n[{idx}/10] {fid}: {f['nazwa_firmy'][:50]}")
        result = {
            "id": fid,
            "name": f["nazwa_firmy"],
            "input": {
                "nip": f.get("nip_vat", "").strip(),
                "rej": f.get("rejestr_id", "").strip(),
                "www": f.get("www", "").strip(),
                "miasto": f.get("miasto", "").strip(),
            },
            "output": {
                "nip_resolved": None,
                "krs_resolved": None,
                "source": None,  # CEIDG / KRS-pobierz / WWW / VIES
                "vies_valid": None,
                "vies_name_match": None,
                "krs_name_match": None,
            },
            "errors": [],
        }

        # ── Step 1: NIP resolution
        have_nip = bool(result["input"]["nip"]) and result["input"]["nip"] != "brak"
        if not have_nip:
            ceidg = ceidg_search(driver, f["nazwa_firmy"])
            if ceidg.get("nip") and nip_mod11_ok(ceidg["nip"]):
                result["output"]["nip_resolved"] = ceidg["nip"]
                result["output"]["source"] = "CEIDG"
            elif f.get("www", "").strip().startswith("http"):
                www = www_scrape(driver, f["www"].strip())
                if www.get("nip") and nip_mod11_ok(www["nip"]):
                    result["output"]["nip_resolved"] = www["nip"]
                    result["output"]["source"] = "WWW"
                if www.get("krs"):
                    result["output"]["krs_resolved"] = www["krs"]
        else:
            result["output"]["nip_resolved"] = result["input"]["nip"]
            result["output"]["source"] = "input"

        # ── Step 2: KRS resolution
        have_krs = bool(result["input"]["rej"]) and result["input"]["rej"] != "brak"
        if not have_krs and result["output"]["nip_resolved"]:
            kp = krspobierz_search(driver, result["output"]["nip_resolved"])
            if kp.get("krs"):
                result["output"]["krs_resolved"] = kp["krs"]
                if not result["output"]["source"]:
                    result["output"]["source"] = "KRS-pobierz"
                else:
                    result["output"]["source"] += "+KRS-pobierz"
            elif not result["output"]["nip_resolved"] and f.get("www", "").strip().startswith("http"):
                # NIP dalej missing, spróbuj po nazwie na krs-pobierz
                kp2 = krspobierz_search(driver, f["nazwa_firmy"])
                if kp2.get("krs"):
                    result["output"]["krs_resolved"] = kp2["krs"]
                    if kp2.get("nip") and nip_mod11_ok(kp2["nip"]):
                        result["output"]["nip_resolved"] = kp2["nip"]
        elif have_krs:
            result["output"]["krs_resolved"] = result["input"]["rej"]

        # ── Step 3: VIES validation (always if we have NIP)
        if result["output"]["nip_resolved"]:
            v = vies_check(result["output"]["nip_resolved"])
            if v.get("valid"):
                result["output"]["vies_valid"] = True
                vname = v.get("name", "")
                sim = name_similarity(f["nazwa_firmy"], vname)
                result["output"]["vies_name_match"] = round(sim, 2)
                if sim < 0.5:
                    result["errors"].append(
                        f"VIES name mismatch: '{vname}' vs '{f['nazwa_firmy'][:50]}' (sim={sim:.2f})"
                    )
            else:
                result["output"]["vies_valid"] = False
                if "error" not in v:
                    result["errors"].append("VIES: NIP nieaktywny w EU VAT")
            time.sleep(0.5)

        # ── Step 4: KRS Open API cross-check (if we have KRS)
        if result["output"]["krs_resolved"]:
            k = krs_lookup(result["output"]["krs_resolved"])
            if k.get("ok") and k.get("nazwa"):
                sim = name_similarity(f["nazwa_firmy"], k["nazwa"])
                result["output"]["krs_name_match"] = round(sim, 2)
                if sim < 0.4:
                    result["errors"].append(
                        f"KRS name mismatch: '{k['nazwa']}' vs '{f['nazwa_firmy'][:50]}' (sim={sim:.2f})"
                    )
                if k.get("nip") and nip_mod11_ok(k["nip"]):
                    if not result["output"]["nip_resolved"]:
                        result["output"]["nip_resolved"] = k["nip"]
                    elif result["output"]["nip_resolved"] != k["nip"]:
                        result["errors"].append(
                            f"NIP mismatch: input={result['output']['nip_resolved']} KRS={k['nip']}"
                        )
            time.sleep(0.3)

        # Summary line
        log(
            f"  → NIP: {result['output']['nip_resolved'] or '—'}  "
            f"KRS: {result['output']['krs_resolved'] or '—'}  "
            f"VIES: {result['output']['vies_valid']} "
            f"(sim={result['output']['vies_name_match']})  "
            f"source: {result['output']['source']}"
        )
        if result["errors"]:
            for e in result["errors"]:
                log(f"  ⚠️  {e}")
        report.append(result)
        time.sleep(DELAY)

    # Save report
    POC_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(POC_OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log(f"\n✓ Report saved → {POC_OUT}")

    # Summary
    nip_ok = sum(1 for r in report if r["output"]["nip_resolved"])
    krs_ok = sum(1 for r in report if r["output"]["krs_resolved"])
    vies_ok = sum(1 for r in report if r["output"]["vies_valid"])
    name_ok = sum(1 for r in report if (r["output"]["vies_name_match"] or 0) >= 0.5)
    errs = sum(len(r["errors"]) for r in report)
    log(
        f"\n=== POC SUMMARY (10 firms) ===\n"
        f"  NIP resolved:  {nip_ok}/10 ({100*nip_ok//10}%)\n"
        f"  KRS resolved:  {krs_ok}/10 ({100*krs_ok//10}%)\n"
        f"  VIES valid:    {vies_ok}/10 ({100*vies_ok//10}%)\n"
        f"  Name match ≥.5: {name_ok}/10 ({100*name_ok//10}%)\n"
        f"  Errors:        {errs}\n"
    )
    driver.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
