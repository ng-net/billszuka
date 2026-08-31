#!/usr/bin/env python3
"""
scan_keywords.py — skanuje strony firm (z url_status) i szuka słów kluczowych
z data/{Kraj}/SŁOWNIK-{ISO}.md.

Dla każdej firmy:
  1. GET do 50KB strony (delikatne, max 7s)
  2. Strip HTML → plain text lowercase
  3. Z słownika wyciągnij listę fraz (regex z '^- (.+?) (szac')
  4. Policz które frazy występują (substring match w case-insensitive)
  5. score_pct = round(100 * found / total)
  6. Zapisz do sqlite (keyword_scan table)

Tryb delikatny: 7s delay, 1 request na raz, UA rotacja, timeout 8s.

Użycie:
    python3 tools/scan_keywords.py --all
    python3 tools/scan_keywords.py --country PL
    python3 tools/scan_keywords.py --country PL --ids PL-B-001 PL-B-002
    python3 tools/scan_keywords.py --all --delay 10 --max-bytes 30000

Narzędzie NIE panikuje serwerów — to firmy, nie Google.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import random
import re
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

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Strip HTML → text (lightweight, bez BS4)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_SCRIPT_RE = re.compile(r"<script[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE)
_STYLE_RE = re.compile(r"<style[^>]*>.*?</style>", re.DOTALL | re.IGNORECASE)
_META_DESC_RE = re.compile(
    r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_META_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _is_http_url(u: str) -> bool:
    u = (u or "").strip().lower()
    return u.startswith("http://") or u.startswith("https://")


def parse_slownik(path: Path) -> list[str]:
    """Wyciągnij listę fraz z pliku SŁOWNIK-XX.md.

    Regex: '^- (.+?) (szac' — łapie bullet z opisem wolumenu w nawiasach.
    Filtr: min 3 znaki, nie zaczyna się od '#' (nagłówki).
    """
    if not path.exists():
        return []
    out = []
    seen = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"^\s*-\s+(.+?)\s*\(szac", line)
        if not m:
            continue
        phrase = m.group(1).strip().strip("'\"")
        if len(phrase) < 3:
            continue
        # Pomiń jeśli phrase to "foo + bar" — zostawiamy bo "+" to operator AND
        if phrase.lower() in seen:
            continue
        seen.add(phrase.lower())
        out.append(phrase)
    return out


def html_to_text(raw: str) -> str:
    """Strip HTML → plain text. Delikatny, bez parsera."""
    raw = _SCRIPT_RE.sub(" ", raw)
    raw = _STYLE_RE.sub(" ", raw)
    # Wyciągnij meta description i title — dodaj do tekstu
    meta_desc = _META_DESC_RE.search(raw)
    title_m = _META_TITLE_RE.search(raw)
    extra = []
    if title_m:
        extra.append(title_m.group(1).strip())
    if meta_desc:
        extra.append(meta_desc.group(1).strip())
    raw = _TAG_RE.sub(" ", raw)
    raw = html.unescape(raw)
    raw = _WS_RE.sub(" ", raw)
    if extra:
        raw = " ".join(extra) + " " + raw
    return raw.strip().lower()


def fetch_page(url: str, max_bytes: int = 50000, timeout: int = 8) -> tuple[str | None, int | None, str | None, int | None]:
    """GET request, max 50KB body. Returns (text, http_code, error, html_size)."""
    ua = random.choice(USER_AGENTS)
    try:
        result = subprocess.run(
            [
                "curl",
                "-s",                      # silent
                "-L",                      # follow redirects
                "--max-time", str(timeout),
                "--max-filesize", str(max_bytes),
                "-A", ua,
                "-w", "\n%{http_code}|%{size_download}",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 4,
        )
        out = result.stdout or ""
        # Ostatnia linia to metadata
        parts = out.rsplit("\n", 1)
        body = parts[0] if len(parts) == 2 else out
        meta = parts[1] if len(parts) == 2 else ""
        code_str, size_str = (meta.split("|") + ["", ""])[:2]
        try:
            http_code = int(code_str) if code_str.isdigit() else None
        except Exception:
            http_code = None
        try:
            html_size = int(size_str) if size_str.isdigit() else None
        except Exception:
            html_size = None
        err = (result.stderr or "").strip()[:200]
        if not body:
            return None, http_code, err or "empty body", html_size
        return body, http_code, None, html_size
    except subprocess.TimeoutExpired:
        return None, None, "timeout", None
    except Exception as e:
        return None, None, str(e)[:200], None


def score_text(text: str, keywords: list[str]) -> tuple[list[str], int]:
    """Zwraca (list_of_hits, total_keywords)."""
    if not text or not keywords:
        return [], len(keywords)
    hits = []
    text_lower = text.lower()
    for kw in keywords:
        kw_l = kw.lower()
        # substring match (case-insensitive)
        if kw_l in text_lower:
            hits.append(kw)
    return hits, len(keywords)


def collect_urls_for_country(country: str) -> list[dict]:
    """Zbiera URL-e z catalog-*.csv + extra-leads + relationships.
    country = ISO (PL, CZ, ...)."""
    iso = country.upper()
    folder = ISO_TO_FOLDER.get(iso, iso)
    country_dir = DATA / folder
    if not country_dir.exists():
        return []

    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for pat in ["catalog-*.csv", "extra-leads-*.csv"]:
        for csv_path in sorted(country_dir.glob(pat)):
            if ".pre-fix" in csv_path.name or ".bak" in csv_path.name:
                continue
            try:
                with csv_path.open(newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
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

    rel_path = DATA / "relationships.csv"
    if rel_path.exists():
        try:
            with rel_path.open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
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


def save_scan(conn: sqlite3.Connection, item: dict, hits: list[str],
              total: int, http_code: int | None, html_size: int | None,
              error: str | None) -> None:
    score_pct = round(100 * len(hits) / total) if total else 0
    conn.execute(
        """
        INSERT INTO keyword_scan (
          id, kraj, url, keywords_found, keywords_total,
          score_pct, http_code, html_size, error, scanned_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(id, url) DO UPDATE SET
          keywords_found=excluded.keywords_found,
          keywords_total=excluded.keywords_total,
          score_pct=excluded.score_pct,
          http_code=excluded.http_code,
          html_size=excluded.html_size,
          error=excluded.error,
          scanned_at=excluded.scanned_at
        """,
        (
            item["id"], item["kraj"], item["url"],
            json.dumps(hits, ensure_ascii=False), total, score_pct,
            http_code, html_size, error,
        ),
    )


def run(country: str | None, delay: float, timeout: int, max_bytes: int,
        ids_filter: set[str] | None) -> dict:
    """Główna pętla."""
    # Upewnij się, że schema (z migracjami) jest zaaplikowana.
    # url-check w tle może trzymać lock (WAL) — retry z backoff.
    for attempt in range(30):
        try:
            db.init()
            break
        except sqlite3.OperationalError as e:
            if "locked" not in str(e):
                raise
            time.sleep(2)
    else:
        print("ERROR: could not acquire DB after 60s", file=sys.stderr)
        return {}

    if country and country.lower() != "all":
        iso = country.upper()
        folder = ISO_TO_FOLDER.get(iso, iso)
        countries = [(iso, folder)] if (DATA / folder).exists() else [(iso, iso)]
    else:
        countries = [
            (iso, folder) for iso, folder in ISO_TO_FOLDER.items()
            if (DATA / folder).exists()
        ]

    grand = {"scanned": 0, "hit_any": 0, "errors": 0, "kw_total_avg": 0}
    grand_kw_sum = 0
    t0 = time.time()

    for c_iso, c_folder in countries:
        items = collect_urls_for_country(c_iso)
        if ids_filter:
            items = [i for i in items if i["id"] in ids_filter]
        if not items:
            print(f"[{c_iso}] no URLs")
            continue

        # Parsuj słownik
        slownik_path = DATA / c_folder / f"SŁOWNIK-{c_iso}.md"
        keywords = parse_slownik(slownik_path)
        if not keywords:
            print(f"[{c_iso}] no SŁOWNIK at {slownik_path}, skipping")
            continue
        print(f"[{c_iso}] {len(items)} URLs, {len(keywords)} keywords, "
              f"~{int(len(items) * delay)}s")

        c_stats = {"scanned": 0, "hit_any": 0, "errors": 0}
        c_kw_sum = 0
        c_started = time.time()

        with db.connect() as conn:
            for idx, item in enumerate(items, 1):
                raw, code, err, size = fetch_page(
                    item["url"], max_bytes=max_bytes, timeout=timeout,
                )
                if raw:
                    text = html_to_text(raw)
                    hits, total = score_text(text, keywords)
                else:
                    hits, total = [], len(keywords)
                save_scan(conn, item, hits, total, code, size, err)
                c_stats["scanned"] += 1
                if hits:
                    c_stats["hit_any"] += 1
                if err or not raw:
                    c_stats["errors"] += 1
                c_kw_sum += len(hits)
                elapsed = time.time() - c_started
                avg = elapsed / idx
                eta = avg * (len(items) - idx)
                score = round(100 * len(hits) / total) if total else 0
                tag = "🎯" if score >= 30 else "·" if score >= 10 else "—"
                print(
                    f"  [{idx:>3}/{len(items)}] {tag} {score:>3}% "
                    f"({len(hits):>2}/{total}) {item['id']:<14} "
                    f"{item['url'][:50]:<50} ETA {int(eta)}s"
                )
                if idx < len(items):
                    time.sleep(delay)

        grand["scanned"] += c_stats["scanned"]
        grand["hit_any"] += c_stats["hit_any"]
        grand["errors"] += c_stats["errors"]
        grand_kw_sum += c_kw_sum
        grand["kw_total_avg"] = round(grand_kw_sum / max(1, grand["scanned"]), 1)
        print(
            f"[{c_iso}] DONE: {c_stats['hit_any']}/{c_stats['scanned']} "
            f"have keywords, {c_stats['errors']} errors, "
            f"{int(time.time() - c_started)}s"
        )

    print(
        f"\n=== ALL DONE: {grand['scanned']} scans in {int(time.time() - t0)}s ==="
    )
    print(
        f"  With keywords (≥1 hit): {grand['hit_any']}/{grand['scanned']}"
    )
    print(f"  Errors: {grand['errors']}")
    print(f"  Avg keywords/scanned: {grand['kw_total_avg']}")
    return grand


def main() -> None:
    p = argparse.ArgumentParser(description="Keyword scanner dla BILLSzuka")
    p.add_argument("--country", default=None, help="np. PL, CZ (lub 'all')")
    p.add_argument("--all", action="store_true", help="skanuj wszystkie kraje")
    p.add_argument("--delay", type=float, default=7.0, help="sekundy między requestami")
    p.add_argument("--timeout", type=int, default=8, help="curl --max-time")
    p.add_argument("--max-bytes", type=int, default=50000, help="max body do pobrania")
    p.add_argument("--ids", nargs="*", default=None, help="tylko te id")
    args = p.parse_args()
    ids_filter = set(args.ids) if args.ids else None
    country = "all" if args.all else args.country
    run(country, args.delay, args.timeout, args.max_bytes, ids_filter)


if __name__ == "__main__":
    main()
