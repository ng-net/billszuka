#!/usr/bin/env python3
"""Detached FAQ generation session.

Run directly:
  python3 tools/faq_build_session.py full
  python3 tools/faq_build_session.py full --force    (recover stuck session)
  python3 tools/faq_build_session.py doc 01-rynki.md

The API endpoint /api/faq/generate claims the single-flight lock itself
(db.claim_session → 409 on conflict) and then launches this process with
start_new_session=True, so an API restart never kills a running session.
A crash leaves state='interrupted'; `--force` allows re-claiming.

Numeric questions are answered deterministically from the facts via
`ground_key` dot-paths — zero LLM calls, correct by construction.
Qualitative: Gemini 3.6-flash answers, OpenRouter judges (TAK/NIE); judge
fallback = Gemini with an alternate prompt; one retry with a correction
hint, then the question lands in faq_rejects.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_server  # noqa: E402  (reuses the vault + battle-tested LLM callers)
import db          # noqa: E402
import faq         # noqa: E402
import md_corpus   # noqa: E402
from api_server import ChatRequest  # noqa: E402

ANSWERER = "gemini-2.5-flash-lite"        # free tier, 3x cheaper than 2.5-flash
JUDGE_MODEL = "deepseek/deepseek-chat"   # via OpenRouter (same as api_server)
RETRY_LIMIT = 1
BACKUP_KEEP = 5

ARTIFACT_JSON = faq.DATA_DIR / "faq.json"
ARTIFACT_CSV = faq.DATA_DIR / "faq.csv"

QUALITATIVE_SEEDS = [
    "Jaka jest różnica między tierem hurtownik a reseller?",
    "Co oznacza status DO-WERYFIKACJI i co z nim zrobić?",
    "Jak wygląda proces weryfikacji firmy w BILLSzuka?",
    "Dlaczego firmy ze statusem FROZEN są najcenniejsze?",
    "Które kraje są priorytetem ekspansji i dlaczego?",
    "Jakie są typowe wolumeny u hurtowników tytoniowych?",
    "Co robić, gdy firma ma flagę PENDING_API?",
    "Jak BILLSzuka zbiera dane o firmach?",
]


# ---------------------------------------------------------------------------
# Question bank (pure — unit tested)
# ---------------------------------------------------------------------------

def build_numeric_bank(facts: dict) -> list[dict]:
    """Numeric templates expanded over the countries present in the data.
    ground_key is a dot-path into the facts (a value may contain '|')."""
    bank = [
        {"q": "Ile firm jest w katalogu?", "ground_key": "rows"},
        {"q": "Jaki jest rozkład tierów?", "ground_key": "columns.tier"},
        {"q": "Jaki jest rozkład wolumenów?", "ground_key": "columns.wolumen"},
        {"q": "Jaki jest rozkład kategorii?", "ground_key": "columns.kategoria"},
    ]
    for kraj in sorted(facts["columns"]["kraj"]):
        bank.append({"q": f"Ile firm jest w {kraj}?",
                     "ground_key": f"columns.kraj.{kraj}"})
        bank.append({"q": f"Ile firm FROZEN w {kraj}?",
                     "ground_key": f"flags_x_kraj.frozen|{kraj}"})
        bank.append({"q": f"Ile firm DO-WERYFIKACJI w {kraj}?",
                     "ground_key": f"flags_x_kraj.do-weryfikacji|{kraj}"})
    return bank


def render_numeric(ground_key: str, facts: dict) -> str:
    """Resolve a dot-path into facts and render text. Dicts render as
    'key: value' pairs; a missing key renders 'brak danych'."""
    node: object = facts
    try:
        for part in ground_key.split("."):
            node = node[part]  # type: ignore[index]
    except (KeyError, TypeError):
        return "brak danych"
    if isinstance(node, dict):
        return "; ".join(f"{k}: {v}" for k, v in node.items())
    return str(node)


def build_qual_bank(doc_file: str | None = None) -> list[str]:
    """Seeds + corpus document headings (doc mode = one file's headings)."""
    questions: list[str] = [] if doc_file else list(QUALITATIVE_SEEDS)
    for name, content in md_corpus.load_corpus():
        if doc_file and name != doc_file:
            continue
        for line in content.splitlines():
            m = re.match(r"^#{1,3}\s+(.+)$", line)
            if m and len(m.group(1).strip()) > 6:
                questions.append(m.group(1).strip())
    return questions


def parse_judge(text: str) -> bool | None:
    """Judge verdict → True / False / None (inconclusive)."""
    t = faq.normalize(text)[:120]
    if t.startswith("tak") or "odpowiedz zgodna" in t or "jest zgodna" in t:
        return True
    if t.startswith("nie") and "nie wiem" not in t[:40]:
        return False
    return None


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _entry_id(q: str) -> str:
    return hashlib.sha256(faq.normalize(q).encode("utf-8")).hexdigest()[:16]


def reject_question(q: str, reason: str) -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO faq_rejects (q, q_norm, reason, rejected_at) "
            "VALUES (?, ?, ?, datetime('now'))",
            (q, faq.normalize(q), reason),
        )


def upsert_entry(entry: dict) -> None:
    """Insert or refresh one entry — hits are NEVER touched (spec §Data store)."""
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO faq_entries (id, q, a, category, sources, ground_key, "
            " verified_kind, judge_model, verified_at, created_at, hits) "
            "VALUES (:id, :q, :a, :category, :sources, :ground_key, :verified_kind, "
            " :judge_model, :verified_at, :created_at, 0) "
            "ON CONFLICT(id) DO UPDATE SET q=excluded.q, a=excluded.a, "
            " category=excluded.category, sources=excluded.sources, "
            " ground_key=excluded.ground_key, verified_kind=excluded.verified_kind, "
            " judge_model=excluded.judge_model, verified_at=excluded.verified_at, "
            " created_at=excluded.created_at",
            entry,
        )


def rotate_backups(path: Path, keep: int = BACKUP_KEEP) -> None:
    """Move the existing artifact aside with a unique timestamp name and
    trim backups to the newest `keep`."""
    if not path.exists():
        return
    ns = path.stat().st_mtime_ns
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(ns // 10**9))
    backup = path.with_name(f"{path.stem}-{stamp}-{ns % 10**9:09d}{path.suffix}")
    path.replace(backup)
    for old in sorted(path.parent.glob(f"{path.stem}-*{path.suffix}"))[:-keep]:
        old.unlink()


def write_artifacts(entries: list[dict]) -> None:
    """Immutable session outputs — the runtime never rewrites these."""
    rotate_backups(ARTIFACT_JSON)
    rotate_backups(ARTIFACT_CSV)
    ARTIFACT_JSON.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    if entries:
        fields = ["id", "q", "a", "category", "sources", "verified_kind",
                  "judge_model", "verified_at"]
        with open(ARTIFACT_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for e in entries:
                w.writerow({k: e.get(k) for k in fields})


def _skip_rejects(questions: list[str]) -> list[str]:
    """Questions already on the blocklist are never re-generated."""
    with db.connect() as conn:
        blocked = {r["q_norm"] for r in conn.execute("SELECT q_norm FROM faq_rejects")}
    return [q for q in questions if faq.normalize(q) not in blocked]


# ---------------------------------------------------------------------------
# LLM part (async, reused callers from api_server)
# ---------------------------------------------------------------------------

def _facts_block(facts: dict) -> str:
    return "DANE Z KATALOGU (jedyny autorytet liczb):\n" + json.dumps(
        {"rows": facts["rows"], "columns": facts["columns"],
         "flags": facts["flags"], "flags_x_kraj": facts["flags_x_kraj"]},
        ensure_ascii=False)


async def answer_qualitative(q: str, facts: dict, corpus_blocks: list[str]) -> str:
    vault = api_server._bootstrap_vault_from_env()
    keys = [k for k in vault.get("gemini", []) if k.get("key")]
    if not keys:
        raise RuntimeError("no Gemini key in vault")
    context = _facts_block(facts) + "\n\n" + "\n\n".join(corpus_blocks)
    result = await api_server._call_gemini(ChatRequest(query=f"PYTANIE: {q}\n\n{context}"),
                                           keys[0]["key"])
    if not result:
        raise RuntimeError("gemini call failed")
    return result.response


async def judge_answer(q: str, answer: str, facts: dict,
                       corpus_blocks: list[str]) -> tuple[bool, str]:
    """(verdict, judge_model) — raises RuntimeError when no judge answers."""
    vault = api_server._bootstrap_vault_from_env()
    context = _facts_block(facts) + "\n\n" + "\n\n".join(corpus_blocks)
    prompt = (
        "Jesteś sędzią odpowiedzi. Oceń, czy ODPOWIEDŹ jest zgodna z DANYMI "
        "i KORPUSEM. Odpowiedz jednym słowem: TAK lub NIE.\n\n"
        f"PYTANIE: {q}\n\nODPOWIEDŹ: {answer}\n\n{context}"
    )
    for entry in [k for k in vault.get("openrouter", []) if k.get("key")]:
        result = await api_server._call_openrouter(ChatRequest(query=prompt), entry["key"])
        if result:
            verdict = parse_judge(result.response)
            if verdict is not None:
                return verdict, f"openrouter:{JUDGE_MODEL}"
    for entry in [k for k in vault.get("gemini", []) if k.get("key")]:
        alt = ("Odpowiedz TYLKO jednym słowem: TAK lub NIE. Czy odpowiedź "
               "jest zgodna z danymi?\n\n" + prompt)
        result = await api_server._call_gemini(ChatRequest(query=alt), entry["key"])
        if result:
            verdict = parse_judge(result.response)
            if verdict is not None:
                return verdict, f"gemini:{ANSWERER}"
    raise RuntimeError("no judge available")


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _make_entry(q: str, a: str, verified_kind: str, judge_model: str | None,
                sources: str, ground_key: str | None = None) -> dict:
    return {"id": _entry_id(q), "q": q, "a": a, "category": "dane katalogowe",
            "sources": sources, "ground_key": ground_key, "verified_kind": verified_kind,
            "judge_model": judge_model, "verified_at": _now(), "created_at": _now()}


async def run_session(mode: str, doc_file: str | None, force: bool) -> int:
    db.init()
    if not db.claim_session(force=force):
        print("SESSION_CONFLICT: inna sesja generowania już trwa")
        return 3
    try:
        facts = faq.load_facts()
        corpus_blocks = md_corpus.inject_corpus([])
        numeric = [] if mode == "doc" else build_numeric_bank(facts)
        qual = _skip_rejects(build_qual_bank(doc_file))
        total = len(numeric) + len(qual)
        done = 0

        def checkpoint():
            with db.connect() as conn:
                conn.execute(
                    "UPDATE faq_session SET progress=?, updated_at=datetime('now') WHERE id=1",
                    (f"{done}/{total}",))

        report = {"accepted": 0, "rejected": 0, "manual": 0, "numeric": len(numeric),
                  "verdicts": []}
        entries: list[dict] = []
        sources = json.dumps(["master.csv"], ensure_ascii=False)

        for item in numeric:
            entries.append(_make_entry(
                item["q"], render_numeric(item["ground_key"], facts),
                "numeric", None, sources, ground_key=item["ground_key"]))
            done += 1
            checkpoint()

        for q in qual:
            attempts = 0
            while True:
                answer = None
                try:
                    ask_q = q if attempts == 0 else (
                        q + " (sędzia odrzucił poprzednią odpowiedź jako "
                        "niezgodną z danymi — popraw ją)")
                    answer = await answer_qualitative(ask_q, facts, corpus_blocks)
                    ok, judge_model = await judge_answer(q, answer, facts, corpus_blocks)
                except RuntimeError:
                    ok, judge_model = None, None
                if ok is True:
                    entries.append(_make_entry(q, answer, "judge", judge_model, sources))
                    report["accepted"] += 1
                    report["verdicts"].append({"q": q, "verdict": "tak"})
                    break
                if ok is None:
                    if answer is not None:
                        # judge unavailable but the answer exists → save as
                        # manual (human review later).
                        entries.append(_make_entry(q, answer, "manual", None, sources))
                        report["manual"] += 1
                        report["verdicts"].append({"q": q, "verdict": "brak sędziego"})
                    else:
                        # Answerer down (e.g. Gemini quota): nothing to save
                        # and nothing to judge. Do NOT blocklist — a temporary
                        # outage must not permanently reject the question
                        # (regression: UnboundLocalError on `answer`).
                        report["answer_failed"] = report.get("answer_failed", 0) + 1
                        report["verdicts"].append({"q": q, "verdict": "brak odpowiedzi"})
                    break
                if attempts < RETRY_LIMIT:
                    attempts += 1
                    continue
                reject_question(q, "judge rejected twice")
                report["rejected"] += 1
                report["verdicts"].append({"q": q, "verdict": "nie"})
                break
            done += 1
            checkpoint()

        for e in entries:
            upsert_entry(e)
        faq.update_source_digests(["master.csv"] + [n for n, _ in md_corpus.load_corpus()])
        write_artifacts(entries)
        with db.connect() as conn:
            conn.execute(
                "UPDATE faq_session SET state='done', progress=?, report=?, "
                "updated_at=datetime('now') WHERE id=1",
                (f"{done}/{total}", json.dumps(report, ensure_ascii=False)))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:  # noqa: BLE001 — a crashed session must leave a marker
        try:
            with db.connect() as conn:
                conn.execute(
                    "UPDATE faq_session SET state='interrupted', "
                    "updated_at=datetime('now') WHERE id=1")
        except Exception:
            pass
        print(f"SESSION_INTERRUPTED: {e}")
        return 1


def main() -> int:
    p = argparse.ArgumentParser(description="FAQ generation session")
    p.add_argument("mode", choices=["full", "doc"])
    p.add_argument("doc_file", nargs="?", default=None,
                   help="corpus .md filename (doc mode)")
    p.add_argument("--force", action="store_true",
                   help="claim the session even if state='running'")
    args = p.parse_args()
    if args.mode == "doc" and not args.doc_file:
        p.error("doc mode requires a corpus file name (data/knowledge/md/<name>.md)")
    return asyncio.run(run_session(args.mode, args.doc_file, args.force))


if __name__ == "__main__":
    sys.exit(main())
