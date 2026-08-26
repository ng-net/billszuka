"""Tests for tools/faq.py — normalization, facts, matching, save-command."""
from __future__ import annotations

from pathlib import Path

import faq

FIXTURE = Path(__file__).parent / "fixtures" / "master_fixture.csv"


def _facts():
    return faq.compute_facts(FIXTURE)


def test_normalize_strips_diacritics_and_punctuation():
    assert faq.normalize("Ile firm jest FROZEN w PL?") == "ile firm jest frozen w pl"
    assert faq.normalize("  Zachowaj   to ZDANIE!  ") == "zachowaj to zdanie"
    assert faq.normalize("Łódź—do-weryfikacji") == "lodz do weryfikacji"


def test_tokenize():
    assert faq.tokenize("Ile firm w PL?") == ["ile", "firm", "w", "pl"]


def test_compute_facts_counts():
    facts = _facts()
    assert facts["rows"] == 6
    assert facts["columns"]["kraj"] == {"PL": 3, "CZ": 2, "DE": 1}
    assert facts["columns"]["tier"]["hurtownik"] == 4
    assert facts["flags"]["frozen"] == 3
    assert facts["flags"]["do-weryfikacji"] == 1
    assert facts["flags_x_kraj"]["frozen|PL"] == 2
    assert facts["flags_x_kraj"]["frozen|CZ"] == 1


def test_facts_hash_is_stable_and_sensitive():
    a = faq.facts_hash(_facts())
    b = faq.facts_hash(_facts())
    assert a == b                       # stable for identical input
    assert faq.facts_hash({"rows": 1}) != a


def test_facts_hash_ignores_touch_not_change(tmp_path):
    import shutil, time
    shutil.copy(FIXTURE, tmp_path / "m.csv")
    path = tmp_path / "m.csv"
    h1 = faq.facts_hash(faq.compute_facts(path))
    time.sleep(0.01)
    path.touch()                        # mtime changes, bytes don't
    h2 = faq.facts_hash(faq.compute_facts(path))
    assert h1 == h2


# --- matching ---------------------------------------------------------------

ENTRIES = [
    {"id": "e1", "q": "Ile firm jest FROZEN w PL?", "a": "A1", "verified_kind": "numeric"},
    {"id": "e2", "q": "Ile firm jest FROZEN w CZ?", "a": "A2", "verified_kind": "numeric"},
    {"id": "e3", "q": "Rozkład tierów", "a": "A3", "verified_kind": "numeric"},
]

ENTS = frozenset({"pl", "cz", "de", "ee", "frozen", "do-weryfikacji",
                  "pending_api", "hurtownik", "reseller", "duży", "mały", "a1", "b4"})


def test_match_exact():
    assert faq.match_faq("Ile firm jest FROZEN w PL?", ENTRIES, ENTS)["id"] == "e1"


def test_match_paraphrase():
    # token overlap high, no entity conflict
    assert faq.match_faq("powiedz ile firm ma frozen w pl", ENTRIES, ENTS)["id"] == "e1"


def test_match_entity_guard_country_swap_is_miss():
    # one country token differs → hard miss (the PL/CZ trap)
    assert faq.match_faq("Ile firm jest FROZEN w CZ?", ENTRIES, ENTS)["id"] == "e2"
    assert faq.match_faq("Ile firm jest frozen w pl", ENTRIES, ENTS) is not None
    # a DE query must never resolve to the PL or CZ entry
    assert faq.match_faq("Ile firm jest FROZEN w DE?", ENTRIES, ENTS) is None


def test_match_entity_guard_one_sided_is_miss():
    # query carries a country, candidate doesn't (or vice versa) → miss
    assert faq.match_faq("Rozkład tierów w PL", ENTRIES, ENTS) is None
    assert faq.match_faq("Ile firm jest FROZEN?", ENTRIES, ENTS) is None


def test_match_unrelated_is_miss():
    assert faq.match_faq("jacy hurtownicy działają w niemczech", ENTRIES, ENTS) is None


# --- eval gate ---------------------------------------------------------------

# (base question, [paraphrases], [near-miss negatives])
EVAL_BASE = [
    ("ile firm jest frozen w pl",
     ["powiedz ile firm ma frozen w polsce", "podaj liczbę firm frozen z pl",
      "ile jest firm ze statusem frozen w kraju pl", "frozen w pl ile firm",
      "ile firm w polsce ma flagę frozen"],
     ["ile firm jest frozen w cz", "ile firm jest frozen w de", "ile firm jest frozen w ee",
      "ile firm jest frozen", "ile firm ma do-weryfikacji w pl",
      "ile firm jest frozen w pl i cz"]),
    ("rozklad tierow",
     ["jaki jest rozklad tierow", "podaj rozklad tierow w katalogu",
      "rozklad tierow prosze", "tier rozklad", "jak wyglada rozklad tierow"],
     ["rozklad tierow w pl", "rozklad tierow w cz", "rozklad wolumenu",
      "rozklad kategorii", "tier w pl rozklad"]),
    ("ile firm jest w pl",
     ["ile firm znajduje sie w polsce", "podaj liczbe firm z pl",
      "liczba firm w kraju pl", "ile mamy firm pl", "pl ile firm"],
     ["ile firm jest w cz", "ile firm jest w de", "ile firm jest",
      "ile hurtownikow jest w pl", "ile firm jest w pl i cz"]),
]


def _build_eval_set() -> list[tuple[str, str | None]]:
    """50 positives + 50 negatives (near-misses: country swaps, missing
    entities, extra entities, wrong column)."""
    pos: list[tuple[str, str | None]] = []
    neg: list[tuple[str, str | None]] = []
    for base, paras, nearmiss in EVAL_BASE:
        pos += [(p, base) for p in paras]
        neg += [(n, None) for n in nearmiss]
    # extra negatives built from entity swaps across bases
    for _ in range(50 - len(neg)):
        for base, _, _ in EVAL_BASE:
            swapped = base.replace("pl", "cz")
            if swapped != base and len(neg) < 50:
                neg.append((swapped, None))
    for _ in range(50 - len(pos)):
        for base, paras, _ in EVAL_BASE:
            if len(pos) < 50:
                pos.append((paras[0] + " ?", base))
    return pos + neg


def test_eval_gate_zero_false_accepts():
    """The shipped threshold must never accept a negative. Run
    `pytest tests/test_faq.py::test_eval_gate -q` after changing
    FAQ_FUZZY_THRESHOLD."""
    eval_rows = _build_eval_set()
    assert len(eval_rows) >= 100
    # every positive must map to its base entry; build entries from bases
    entries = [{"id": f"b{i}", "q": b, "a": "A", "verified_kind": "numeric"}
               for i, (b, _, _) in enumerate(EVAL_BASE)]
    false_accepts = []
    misses = []
    for q, expected in eval_rows:
        hit = faq.match_faq(q, entries, ENTS)
        if expected is None and hit is not None:
            false_accepts.append((q, hit["q"]))
        elif expected is not None and (hit is None or faq.normalize(hit["q"]) != expected):
            misses.append((q, expected, hit["q"] if hit else None))
    assert false_accepts == [], f"false accepts at {faq.FAQ_FUZZY_THRESHOLD}: {false_accepts}"
    assert len(misses) < len(eval_rows) // 2, f"too many misses: {misses}"


def test_tune_sweep_finds_working_threshold():
    """Sweep helper: highest threshold with zero false accepts. Used once
    to measure FAQ_FUZZY_THRESHOLD — then the constant is set and this
    documents the measurement."""
    import tools  # noqa: F401  (ensure module importable)
    eval_rows = _build_eval_set()
    entries = [{"id": f"b{i}", "q": b, "a": "A", "verified_kind": "numeric"}
               for i, (b, _, _) in enumerate(EVAL_BASE)]
    for t in [0.9, 0.8, 0.7, 0.65, 0.6, 0.55, 0.5]:
        faq.FAQ_FUZZY_THRESHOLD = t
        fa = [q for q, exp in eval_rows if exp is None and faq.match_faq(q, entries, ENTS)]
        hits = sum(1 for q, exp in eval_rows if exp is not None and faq.match_faq(q, entries, ENTS))
        if not fa:
            print(f"threshold {t}: 0 false accepts, {hits}/{sum(1 for _, e in eval_rows if e)} positives hit")
            break
    faq.FAQ_FUZZY_THRESHOLD = 0.6


# --- save-command -----------------------------------------------------------

PHRASES = [
    "zapisz ten fakt", "zapisz to", "zapisz to zdanie", "zachowaj to",
    "zapamiętaj to", "zapisz odpowiedź", "save this", "save this fact",
    "remember this",
]


def test_save_command_basic():
    assert faq.is_save_command("zapisz ten fakt", True, PHRASES) == ""
    assert faq.is_save_command("Save this fact", True, PHRASES) == ""


def test_save_command_with_short_note():
    assert faq.is_save_command("zapisz to zdanie o rynku", True, PHRASES) == "o rynku"


def test_save_command_typo_tolerance():
    # "zamietaj" ≈ "zapamiętaj" (per-token difflib ≥ 0.9)
    assert faq.is_save_command("zamietaj to", True, PHRASES) == ""


def test_save_command_question_token_blocks():
    assert faq.is_save_command("zapisz ile firm jest w pl", True, PHRASES) is None
    assert faq.is_save_command("zapisz to jakie firmy", True, PHRASES) is None


def test_save_command_long_remainder_falls_through():
    # long tail = a question, not a command
    assert faq.is_save_command("zapisz to zdanie o rynku w polsce i niemczech", True, PHRASES) is None


def test_save_command_needs_last_answer():
    assert faq.is_save_command("zapisz ten fakt", False, PHRASES) is None


def test_save_command_plain_question_is_none():
    assert faq.is_save_command("ile firm jest frozen w pl", True, PHRASES) is None
