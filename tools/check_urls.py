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
URL_STATUS_SCHEMA = """
CREATE TABLE IF NOT EXISTS url_status (
  id TEXT NOT NULL,
  kraj TEXT NOT NULL,
  url TEXT NOT NULL,
  status TEXT NOT NULL,        -- 'green' | 'red' | 'unknown'
  http_code INTEGER,
  error TEXT,
  checked_at TEXT NOT NULL,
  PRIMARY KEY (id, url)
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
    if http_code is None:
        e = (error or "").lower()
        if "timeout" in e or "timed out" in e:
            return "timeout"
        if "ssl" in e or "certificate" in e or "handshake" in e:
            return "ssl"
        if "dns" in e or "name or service" in e or "resolve" in e or "nodename" in e:
            return "dns"
        if "no response" in e or "connection refused" in e or "couldn't connect" in e:
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
                        if not uid or not _is_http_url(url):
                            continue
                        key = (uid, url)
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append({"id": uid, "kraj": iso, "url": url})
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
                    if not uid.startswith(f"{iso}-") or not _is_http_url(url):
                        continue
                    key = (uid, url)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({"id": uid, "kraj": iso, "url": url})
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
        if not code_str or not code_str.isdigit():
            err = (result.stderr or "").strip()[:200] or "no response"
            return None, err, None, response_ms
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
                  id, kraj, url, status, state, http_code,
                  redirect_url, response_ms, error, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(id, url) DO UPDATE SET
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
        ids_filter: set[str] | None) -> dict:
    """Główna pętla. Zwraca statystyki."""
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

    for c_iso, c_folder in countries:
        items = collect_urls_for_country(c_iso)
        if ids_filter:
            items = [i for i in items if i["id"] in ids_filter]
        if not items:
            print(f"[{c_iso}] no URLs to check")
            continue
        print(f"[{c_iso}] {len(items)} URLs (~{int(len(items) * delay)}s)")
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
        f"\n=== ALL DONE: {grand_total['checked']} URLs in {total_time}s "
        f"({grand_total['green']} green / {grand_total['red']} red) ==="
    )
    return grand_total


def main() -> None:
    p = argparse.ArgumentParser(description="Delikatny URL checker dla BILLSzuka")
    p.add_argument("--country", default=None, help="np. PL, CZ (lub 'all')")
    p.add_argument("--all", action="store_true", help="sprawdź wszystkie kraje")
    p.add_argument("--delay", type=float, default=4.0, help="sekundy między requestami")
    p.add_argument("--timeout", type=int, default=8, help="curl --max-time")
    p.add_argument("--ids", nargs="*", default=None, help="tylko te id")
    args = p.parse_args()
    ids_filter = set(args.ids) if args.ids else None
    country = "all" if args.all else args.country
    run(country, args.delay, args.timeout, ids_filter)


if __name__ == "__main__":
    main()
