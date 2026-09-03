#!/usr/bin/env python3
"""
check_urls.py — wolne, delikatne sprawdzanie URL-i z katalogów BILLSzuka.

Tryb: HEAD request, 1 URL / 4s, rotacja User-Agent. Wynik do sqlite
(url_status table) + opcjonalnie stdout podsumowanie.

Użycie:
    python3 tools/check_urls.py --country PL
    python3 tools/check_urls.py --all
    python3 tools/check_urls.py --country PL --delay 5 --timeout 8
    python3 tools/check_urls.py --country PL --ids PL-B-001 PL-B-002  # tylko te

Narzędzie NIE panikuje serwerów:
- delay 4s między requestami (configurowalny)
- HEAD zamiast GET (zero body)
- timeout 8s, max 2 retry
- UA rotacja: Mozilla/Firefox/Chrome/Safari

Zielona = 2xx/3xx, Czerwona = wszystko inne + timeout/DNS/SSL error.
"""
from __future__ import annotations

import argparse
import csv
import random
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402

DATA = ROOT / "data"

# Mapowanie ISO code → folder name (polskie nazwy folderów)
ISO_TO_FOLDER = {
    "PL": "Polska", "CZ": "Czechy", "SK": "Słowacja", "SI": "Słowenia",
    "HR": "Chorwacja", "BG": "Bułgaria", "RO": "Rumunia", "MD": "Mołdawia",
    "RS": "Serbia", "LT": "Litwa", "LV": "Łotwa", "EE": "Estonia",
    "FR": "Francja",
}

# Schema migration: dodaj tabelę url_status jeśli nie istnieje
# Production schema (id_unikalne not id) per tools/db.py — synced 2026-09-03.
URL_STATUS_SCHEMA = """
CREATE TABLE IF NOT EXISTS url_status (
  id_unikalne TEXT NOT NULL,
  kraj TEXT NOT NULL,
  url TEXT NOT NULL,
  status TEXT NOT NULL,
  http_code INTEGER,
  error TEXT,
  checked_at TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'unknown',
  redirect_url TEXT,
  response_ms INTEGER,
  PRIMARY KEY (id_unikalne, url)
);
CREATE INDEX IF NOT EXISTS idx_url_status_kraj ON url_status(kraj);
CREATE INDEX IF NOT EXISTS idx_url_status_status ON url_status(status);
"""

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def ensure_schema() -> None:
    """Dodaj url_status table do billszuka.db (idempotent)."""
    with db.connect() as conn:
        conn.executescript(URL_STATUS_SCHEMA)


def _is_http_url(u: str) -> bool:
    u = (u or "").strip().lower()
    return u.startswith("http://") or u.startswith("https://")


def _classify(http_code: int | None) -> str:
    """2xx/3xx = green, reszta = red, brak odpowiedzi = red."""
    if http_code is None:
        return "red"
    if 200 <= http_code < 400:
        return "green"
    return "red"


def _classify_state(http_code: int | None, error: str | None) -> str:
    """Szczegółowa klasyfikacja: ok | redirect | 4xx | 5xx | timeout | ssl | dns | empty | unknown"""
    if http_code is None or http_code == 0:
        e = (error or "").lower()
        if "timeout" in e or "timed out" in e:
            return "timeout"
        if "ssl" in e or "certificate" in e or "handshake" in e:
            return "ssl"
        if "dns" in e or "name or service" in e or "resolve" in e or "nodename" in e or "host" in e:
            return "dns"
        if "no response" in e or "connection refused" in e or "couldn't connect" in e or "failed to connect" in e or "reset" in e or "recv failure" in e or "empty reply" in e or "stream" in e:
            return "timeout"  # traktujemy jako unreachable
        return "unknown"
    if 200 <= http_code < 300:
        return "ok"
    if 300 <= http_code < 400:
        return "redirect"
    if 400 <= http_code < 500:
        return "4xx"
    if 500 <= http_code < 600:
        return "5xx"
    return "unknown"


def collect_urls_for_country(country: str) -> list[dict]:
    """Zbierz URL-e z catalog-*.csv + extra-leads-*.csv + relationships.csv.

    `country` to ISO kod ("PL") — mapujemy na folder ("Polska").
    W `kraj` zapisujemy ISO kod (dla spójności z id prefiks).

    Returns: [{'id': 'PL-B-001', 'kraj': 'PL', 'url': 'https://...'}, ...]
    """
    iso = country.upper()
    folder = ISO_TO_FOLDER.get(iso, iso)
    country_dir = DATA / folder
    if not country_dir.exists():
        return []

    out: list[dict] = []
    seen: set[tuple[str, str]] = set()

    # Catalog A + B + extras
    csv_patterns = ["catalog-*.csv", "extra-leads-*.csv"]
    for pat in csv_patterns:
        for csv_path in sorted(country_dir.glob(pat)):
            if ".pre-fix" in csv_path.name or ".bak" in csv_path.name:
                continue
            try:
                with csv_path.open(newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        uid = (row.get("id") or "").strip()
                        url = (row.get("www") or row.get("url") or "").strip()
                        flagi = (row.get("flagi") or "").strip()
                        if not uid or not _is_http_url(url):
                            continue
                        key = (uid, url)
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append({"id": uid, "kraj": iso, "url": url, "flagi": flagi})
            except Exception as e:
                print(f"  ! skip {csv_path.name}: {e}", file=sys.stderr)

    # relationships.csv (root level)
    rel_path = DATA / "relationships.csv"
    if rel_path.exists():
        try:
            with rel_path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    uid = (row.get("id_a") or row.get("id") or "").strip()
                    url = (row.get("url") or row.get("www") or "").strip()
                    flagi = (row.get("flagi") or "").strip()
                    if not uid.startswith(f"{iso}-") or not _is_http_url(url):
                        continue
                    key = (uid, url)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({"id": uid, "kraj": iso, "url": url, "flagi": flagi})
        except Exception as e:
            print(f"  ! skip relationships.csv: {e}", file=sys.stderr)

    return out


def check_one(url: str, timeout: int = 8) -> tuple[int | None, str | None, str | None, int | None]:
    """HEAD request. Returns (http_code, error_msg, redirect_url, response_ms)."""
    ua = random.choice(USER_AGENTS)
    try:
        result = subprocess.run(
            [
                "curl",
                "-I",                  # HEAD
                "-s",                  # silent
                "-S",                  # show error if fails
                "-o", "/dev/null",     # nie wypisuj body
                "-w", "%{http_code}|%{redirect_url}|%{time_total}",
                "-L",                  # follow redirects
                "--max-time", str(timeout),
                "--retry", "1",
                "--retry-delay", "2",
                "-A", ua,
                url,
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 4,
        )
        out = (result.stdout or "").strip()
        parts = out.split("|")
        code_str = parts[0] if len(parts) >= 1 else ""
        redirect_url = parts[1] if len(parts) >= 2 and parts[1] else None
        time_str = parts[2] if len(parts) >= 3 else ""
        response_ms = int(float(time_str) * 1000) if time_str.replace(".", "").isdigit() else None
        err = (result.stderr or "").strip()[:200]
        if result.returncode != 0 or not code_str or not code_str.isdigit() or int(code_str) == 0:
            return None, err or "no response", None, response_ms
        return int(code_str), None, redirect_url, response_ms
    except subprocess.TimeoutExpired:
        return None, "timeout", None, None
    except Exception as e:
        return None, str(e)[:200], None, None


def save_result(conn: sqlite3.Connection, item: dict, status: str, state: str,
                http_code: int | None, error: str | None,
                redirect_url: str | None, response_ms: int | None) -> None:
    for attempt in range(15):
        try:
            conn.execute(
                """
                INSERT INTO url_status (
                  id_unikalne, kraj, url, status, state, http_code,
                  redirect_url, response_ms, error, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(id_unikalne, url) DO UPDATE SET
                  status=excluded.status,
                  state=excluded.state,
                  http_code=excluded.http_code,
                  redirect_url=excluded.redirect_url,
                  response_ms=excluded.response_ms,
                  error=excluded.error,
                  checked_at=excluded.checked_at
                """,
                (
                    item["id"], item["kraj"], item["url"],
                    status, state, http_code, redirect_url, response_ms, error,
                ),
            )
            return
        except sqlite3.OperationalError as e:
            if "locked" not in str(e):
                raise
            time.sleep(2)


def run(country: str | None, delay: float, timeout: int,
        ids_filter: set[str] | None, missing_only: bool = False, force: bool = False) -> dict:
    """Główna pętla. Zwraca statystyki.
    
    Tryb domyślny: INKREMENTALNY (skipuje FROZEN sprawdzone w ciągu ostatnich 30 dni
    oraz wcześniej zweryfikowane zielone/stabilne).
    Flaga --force wymusza pełny re-skan od zera.
    """
    ensure_schema()

    if country and country.lower() != "all":
        # Normalizuj ISO → folder
        iso = country.upper()
        folder = ISO_TO_FOLDER.get(iso, iso)
        countries = [(iso, folder)] if (DATA / folder).exists() else [(iso, iso)]
    else:
        # Wszystkie kraje — po nazwie folderu
        countries = [
            (iso, folder) for iso, folder in ISO_TO_FOLDER.items()
            if (DATA / folder).exists()
        ]

    grand_total = {"green": 0, "red": 0, "skipped": 0, "checked": 0}
    eta_started = time.time()

    known_status = {}
    with db.connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id_unikalne, url, status, state, http_code, checked_at FROM url_status")
        for r in cur.fetchall():
            known_status[(r[0], r[1])] = (r[2], r[3], r[4], r[5])

    now_ts = time.time()
    thirty_days_s = 30 * 86400

    for c_iso, c_folder in countries:
        items = collect_urls_for_country(c_iso)
        if ids_filter:
            items = [i for i in items if i["id"] in ids_filter]

        if not force:
            filtered = []
            for item in items:
                key = (item["id"], item["url"])
                is_frozen = "FROZEN" in item.get("flagi", "")

                if key not in known_status:
                    # Nowy URL — musi zostać sprawdzony
                    filtered.append(item)
                    continue

                st, state, code, chk_at = known_status[key]

                # Sprawdź wiek ostatniego skanu
                chk_age_s = 999999999
                if chk_at:
                    try:
                        # obsługa formatów "YYYY-MM-DD HH:MM:SS" lub ISO
                        t_parsed = time.mktime(time.strptime(str(chk_at)[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S"))
                        chk_age_s = now_ts - t_parsed
                    except Exception:
                        pass

                if is_frozen:
                    # Zasada 1: FROZEN nie ruszamy, jeśli stan znany i zbadany <30 dni
                    if chk_age_s < thirty_days_s and state != "unknown":
                        grand_total["skipped"] += 1
                        continue
                    if state == "unknown":
                        filtered.append(item)
                    else:
                        grand_total["skipped"] += 1
                        continue
                else:
                    # Rekordy niefrozen: skipuj jeśli stan jest znany i zbadany <30 dni
                    if missing_only:
                        if st == "green" or (state != "unknown" and chk_age_s < thirty_days_s):
                            grand_total["skipped"] += 1
                            continue
                        filtered.append(item)
                    else:
                        if state != "unknown" and chk_age_s < thirty_days_s:
                            grand_total["skipped"] += 1
                            continue
                        filtered.append(item)

            items = filtered

        if not items:
            print(f"[{c_iso}] no URLs to check (all skipped or up to date)")
            continue
        print(f"[{c_iso}] {len(items)} URLs to scan (~{int(len(items) * delay)}s)")
        c_stats = {"green": 0, "red": 0, "checked": 0}
        c_started = time.time()

        # db.connect() może trafić na lock (inny proces w tle) — retry
        conn_ctx = None
        for attempt in range(30):
            try:
                conn_ctx = db.connect()
                break
            except sqlite3.OperationalError as e:
                if "locked" not in str(e):
                    raise
                time.sleep(2)
        if conn_ctx is None:
            print(f"[{c_iso}] could not acquire DB after 60s, skipping", file=sys.stderr)
            continue
        with conn_ctx as conn:
            for idx, item in enumerate(items, 1):
                code, err, redir, ms = check_one(item["url"], timeout=timeout)
                status = _classify(code)
                state = _classify_state(code, err)
                save_result(conn, item, status, state, code, err, redir, ms)
                c_stats[status] += 1
                c_stats["checked"] += 1
                elapsed = time.time() - c_started
                avg = elapsed / idx
                eta = avg * (len(items) - idx)
                tag = "🟢" if status == "green" else "🔴"
                print(
                    f"  [{idx:>3}/{len(items)}] {tag} {code or '---':<4} "
                    f"({state:<8}) {item['id']:<14} "
                    f"{item['url'][:50]:<50} ETA {int(eta)}s"
                )
                if idx < len(items):
                    time.sleep(delay)

        grand_total["green"] += c_stats["green"]
        grand_total["red"] += c_stats["red"]
        grand_total["checked"] += c_stats["checked"]
        print(
            f"[{c_iso}] DONE: {c_stats['green']} green, {c_stats['red']} red "
            f"in {int(time.time() - c_started)}s"
        )

    total_time = int(time.time() - eta_started)
    print(
        f"\n=== ALL DONE: {grand_total['checked']} URLs checked in {total_time}s "
        f"({grand_total['green']} green / {grand_total['red']} red / {grand_total['skipped']} skipped) ==="
    )
    return grand_total


def main() -> None:
    p = argparse.ArgumentParser(description="Delikatny inkrementalny URL checker dla BILLSzuka")
    p.add_argument("--country", default=None, help="np. PL, CZ (lub 'all')")
    p.add_argument("--all", action="store_true", help="sprawdź wszystkie kraje")
    p.add_argument("--force", action="store_true", help="wymuś pełny re-skan (ignoruj status FROZEN i wiek)")
    p.add_argument("--missing-only", action="store_true", help="sprawdź tylko brakujące lub z błędem/timeoutem")
    p.add_argument("--delay", type=float, default=4.0, help="sekundy między requestami")
    p.add_argument("--timeout", type=int, default=8, help="curl --max-time")
    p.add_argument("--ids", nargs="*", default=None, help="tylko te id")
    args = p.parse_args()
    ids_filter = set(args.ids) if args.ids else None
    country = "all" if args.all else args.country
    run(country, args.delay, args.timeout, ids_filter, missing_only=args.missing_only, force=args.force)


if __name__ == "__main__":
    main()
