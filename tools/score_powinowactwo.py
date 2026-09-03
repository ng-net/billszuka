#!/usr/bin/env python3
"""
score_powinowactwo.py — Deterministic powinowactwo_nabijarki scoring.

Replaces ad-hoc guesswork with a rule-based on the company's name + assortment
text. Used to auto-score any new lead before adding to master.csv.

Score rules (deterministic):
  5: explicitly sells ROLLING MACHINES (powermatic/hawk/gerui/nabijarka/...)
  4: rolling machines + smoker accessories (filters/papers/tubes)
  3: tobacco wholesale with roller category in NACE/CAEN (4635/46.35)
  2: general tobacco wholesale (4635 OR 46.35 OR 47.26 etc.)
  1: adjacent (e-sig, snus, FMCG, e-liquid)

Usage:
  python3 tools/score_powinowactwo.py --name "POGON KOOLTURA" --text "MAŠINICE filter omotnice cigarete"
  python3 tools/score_powinowactwo.py --name "Tabák Plus" --nace 46350 --text "cigarety, kuřácké potřeby"
  # batch:
  python3 tools/score_powinowactwo.py --batch candidates.json

Output: prints score 1-5 with the rule hit.
Exit 0 = success.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path


# Tokens that indicate the company explicitly sells ROLLING MACHINES.
# Each tuple: (token_normalized, weight)
ROLLER_TOKENS = [
    # English / global brand names
    "powermatic", "power matic", "power-matic", "smoksmok", "smoks",
    # PL
    "nabijarka", "nabijarki", "maszynka", "maszynice", "maszynki",
    "maszyna do papieros", "do napełniania", "napełniarka", "napełniarki",
    "napelniarka", "napelniarki", "do napelniania",
    "plniczka", "plniczki", "plniczki",
    # CZ
    "plnička", "plničky", "plnicky", "plnicce", "plnic na cigarety",
    # SK
    "strojček", "strojceky", "plnička", "plnicky",
    # HR/SI/RS
    "mašinica", "masinica", "mašinice", "masinice", "punilica", "punilice",
    "punjač", "punjači", "mašina za cigarete",
    # RO
    "masina de umplut", "masina umplut", "masina tigari", "masina de facut",
    "masina pentru tigari", "umplut tigari",
    # BG
    "машина за цигари", "машина за пълнене", "пълначна машина", "машинка",
    # LT
    "cigarečių pildymo mašin", "cigareciu pildymo", "pildymo mašinėlė",
    # LV
    "cigarešu pildīšanas", "pildīšanas mašīna",
    # EE
    "täitmise masin", "täidismasin", "cigarettide täitmise",
    # MD
    "mașină de umplut", "mașină pentru țigări",
    # EN
    "rolling machine", "injector", "smoking machine", "cigarette making machine",
    "cigarette injector", "roll your own machine", "ryo machine",
    # German
    "stopfmaschine", "zigarettenstopfmaschine",
    # Hungarian (HU not in scope but good to have)
    "töltőgép", "cigarettatöltő",
]

# Smoker accessories: filters, papers, tubes
ACCESSORY_TOKENS = [
    # PL
    "gilzy", "gilza", "gilz", "filtry", "filtr", "bibułki", "bibulka",
    "papierki", "papier", "fajki", "fajka", "zapalniczki", "zapalniczka",
    # CZ
    "papírky", "papírek", "filtry", "filtr", "dutinky", "doutník", "doutníky",
    "špičky", "fajfky", "zapalovač",
    # SK
    "papieriky", "papier", "filtre", "filtrov", "dutinky", "cigaretové papieriky",
    "zapaľovač",
    # HR
    "filtera", "filter", "papirići", "papirici", "cigle", "cigla", "cigare",
    "upaljač", "upaljaci",
    # SI
    "filtri", "filter", "papirji", "cigare", "cigarete", "vžigalice",
    # RS
    "filteri", "filter", "papirići", "cigle", "cigarete", "upaljači",
    # RO
    "filtre", "filtru", "tigari", "tigară", "tigări", "brichete", "chibrituri",
    "hartie de tigari", "hârtie",
    # BG
    "филтри", "филтър", "хартия за цигари", "цигарени хартии",
    "цигари", "запалки",
    # LT
    "filtrai", "filtras", "popieriai cigaretėms", "cigaretes", "cigarečių",
    # LV
    "filtru", "filtrs", "cigarešu papīrs", "cigaretes",
    # EE
    "filtreid", "filter", "paberit", "sigaretipaber", "sigarette",
    # MD
    "filtru", "filtru de țigări", "țigări", "tigari",
]


def norm(s: str) -> str:
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower()).strip()


# Negative-context patterns. These mark a SENTENCE as "this is a caveat
# or commentary, not a real product listing". Tight list — only explicit
# negations like "nie ma", "brak", "raczej niski", "nie oferuje", or the word
# "adjacent" itself.
NEGATIVE_PATTERNS = [
    r"\braczej niski\b", r"\braczej nie\b", r"\bnie ma\b", r"\bnie oferuje\b",
    r"\bnie sprzedaje\b", r"\bnie są klasyczn", r"\bnie klasyczn",
    r"\bnisk[ie]?\b.{0,40}cross[-\s]?sell",  # "niski cross-sell" anywhere
    r"cross[-\s]?sell.{0,30}\bnisk",
    r"\badjacent\b",  # the word "adjacent" itself = a meta-flag
    r"\blow[-\s]?conf",  # low confidence flag
    r"⚠️",  # warning emoji
    r"\b(?:nie|brak)\b\s+nabijark",  # "no nabijarka"
    r"\bbrak .* (nabijarka|maszynka|plnička|mašinica|nabijarka)\b",
    r"\bniezwi[aą]zan[ay]? z\b", r"\bnie jest\b", r"\bnie są\b",
    r"\bnie pokrywa\b", r"\bbrak (?:oferty|publicznej|pokrycia)\b",
    r"\bsugeruj[eą]\b.*\bnazw", r"\bnazwa .* sugeruj",  # "name suggests"
    r"⚠️",  # warning emoji (Polish)
    r"\blow[-\s]?conf",  # low confidence
    r"prawdopodobnie niezwi[aą]zane?",
]


def has_any(text: str, tokens: list) -> list:
    """Return list of tokens that appear in text (normalized substring match).
    Tokens that appear in a sentence with negative context (e.g. "raczej niski",
    "nie oferuje", "weareszki nikotynowe") are excluded.
    """
    if not text:
        return []
    n = norm(text)
    # Split into sentences for negative context
    sentences = re.split(r"(?<=[.!?;])\s+|\.\s+|\n", n)
    hits = []
    for t in tokens:
        for sent in sentences:
            if t in sent:
                # Check if this sentence has negative context
                if any(re.search(p, sent) for p in NEGATIVE_PATTERNS):
                    continue
                hits.append(t)
                break  # one match per token is enough
    return hits


def score_lead(name: str = "", text: str = "", nace: str = "",
                 marki: str = "") -> dict:
    """Return {score, rule, roller_hits, accessory_hits, nace_hits}.

    `text` is the freeform notatki (may contain meta-references like "cross-sell
    PowerMatic raczej niski" or "powiazanie z nabijarkami pośrednie").

    `marki` is the explicit marki_nabijarki field — this is the AUTHORITATIVE
    signal of whether the company actually sells rolling machines. ROLLER hits
    are based on this field only; text is only used for accessory and adjacent.
    """
    full = f"{name} {text}".strip()
    marki_only = f"{name} {marki}".strip()  # what they actually sell
    # ROLLER hits come from marki only (authoritative). Token must be a real
    # product token, NOT a meta-reference.
    roller_hits = has_any(marki_only, ROLLER_TOKENS)
    accessory_hits = has_any(full, ACCESSORY_TOKENS)
    # NACE/CAEN detection — for "3" score
    nace_hits = []
    # Combine explicit nace arg with any NACE/CAEN text found in the body
    nace_text = f" {nace} {full} "
    n_clean = re.sub(r"\s+", "", nace_text)
    # 4635/46.35 = wholesale of tobacco; 12.00 = tobacco manufacturing
    if re.search(r"\b4635", n_clean) or re.search(r"\b46\.35", n_clean) or re.search(r"^4635", n_clean):
        nace_hits.append("4635_wholesale_tobacco")
    if re.search(r"\b4726", n_clean) or re.search(r"\b47\.26", n_clean):
        nace_hits.append("4726_retail_tobacco")
    if re.search(r"\b12", n_clean) and len(n_clean) <= 5:
        nace_hits.append("12_tobacco_manufacturing")
    # Also catch GICS / NACE variants in different formats
    if re.search(r"\bNACE[:\s]+4635", nace_text) or re.search(r"CAEN[:\s]+4635", nace_text):
        if "4635_wholesale_tobacco" not in nace_hits:
            nace_hits.append("4635_wholesale_tobacco")
    # Adjacent: e-sig / snus / FMCG keywords. These are stronger than NACE because
    # they explicitly indicate the company is NOT in the classic rolling-machine trade.
    # "fmcg" alone is too broad — many tobacco wholesalers also sell FMCG.
    adjacent_tokens = ["e-cigarett", "e-sigarett", "e-cig ", "e-cig\"", "e-cig.",
                       "vape ", "vaping", "snus", "weareszki nikotynowe",
                       "woreczki nikotynowe", "nikotínové sáčky",
                       "nikotinsäckchen", "pouches", "bägli",
                       "heets", "iqos", "glo ", "glo hyper", "terea",
                       "liquids", "e-liquid", "e-juice", "e cigaret",
                       "elektroninės cigaretės", "elektronines cigaretes",
                       "parowki", "vejp", "вейп",
                       "cash and carry", "cash & carry",
                       "nikotínov", "nikotynov", "nikotinov"]
    # Note: 'fmcg' alone is excluded — too generic. FMCG detection happens below
    # in the "no tobacco" branch (if FMCG is the dominant keyword, score 1).
    adjacent_hits = has_any(full, adjacent_tokens)
    # Scoring (priority order)
    if roller_hits and accessory_hits:
        return {"score": 4, "rule": "ROLLER+ACCESSORY", "roller_hits": roller_hits,
                "accessory_hits": accessory_hits, "nace_hits": nace_hits}
    if roller_hits:
        return {"score": 5, "rule": "ROLLER", "roller_hits": roller_hits,
                "accessory_hits": accessory_hits, "nace_hits": nace_hits}
    # Adjacent: e-cig/snus wholesale OR NACE 12 (tobacco manufacturing) of adjacent
    if adjacent_hits and "4635_wholesale_tobacco" in nace_hits:
        return {"score": 1, "rule": "ADJACENT_VAPE_SNUS_FMCG",
                "roller_hits": roller_hits, "accessory_hits": accessory_hits,
                "nace_hits": nace_hits, "adjacent_hits": adjacent_hits}
    if adjacent_hits:
        return {"score": 1, "rule": "ADJACENT_VAPE_SNUS_FMCG",
                "roller_hits": roller_hits, "accessory_hits": accessory_hits,
                "nace_hits": nace_hits, "adjacent_hits": adjacent_hits}
    # NACE 12 (tobacco manufacturing) + adjacent mentions in text → still adjacent
    if "12_tobacco_manufacturing" in nace_hits and adjacent_hits:
        return {"score": 1, "rule": "TOBACCO_MFG_ADJACENT",
                "roller_hits": roller_hits, "accessory_hits": accessory_hits,
                "nace_hits": nace_hits, "adjacent_hits": adjacent_hits}
    # FMCG check: if "fmcg" is in the name/text AND no tobacco NACE, score 1.
    # Require explicit "fmcg" or "cash and carry" — NOT just "hurtownia" or "hurt".
    fmcg_hits = has_any(full, ["fmcg", "cash and carry", "cash & carry",
                                "hurt fmcg", "hurtownia fmcg", "drogeria"])
    if fmcg_hits and not nace_hits and not roller_hits and not accessory_hits:
        return {"score": 1, "rule": "FMCG_NO_TOBACCO",
                "roller_hits": roller_hits, "accessory_hits": accessory_hits,
                "nace_hits": nace_hits}
    if nace_hits and "4635_wholesale_tobacco" in nace_hits:
        return {"score": 3, "rule": "NACE_4635", "roller_hits": roller_hits,
                "accessory_hits": accessory_hits, "nace_hits": nace_hits}
    if nace_hits:
        return {"score": 2, "rule": "NACE_GENERAL_TOBACCO", "roller_hits": roller_hits,
                "accessory_hits": accessory_hits, "nace_hits": nace_hits}
    return {"score": 2, "rule": "DEFAULT_GENERAL", "roller_hits": roller_hits,
            "accessory_hits": accessory_hits, "nace_hits": nace_hits}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="", help="Company name")
    ap.add_argument("--text", default="", help="Assortment / description / notatki text")
    ap.add_argument("--nace", default="", help="NACE/CAEN code(s)")
    ap.add_argument("--batch", help="JSON file with [{name, text, nace}, ...]")
    ap.add_argument("--marki", default="", help="Explicit marki_nabijarki field")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    if args.batch:
        with open(args.batch) as f:
            batch = json.load(f)
        results = [score_lead(item.get("name", ""), item.get("text", ""),
                                item.get("nace", ""), item.get("marki", ""))
                    for item in batch]
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for item, r in zip(batch, results):
                print(f"{r['score']}\t{r['rule']}\t{item.get('name','')[:50]}")
        return

    r = score_lead(args.name, args.text, args.nace, args.marki)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"score={r['score']} rule={r['rule']}")
        if r['roller_hits']:
            print(f"  roller_hits: {r['roller_hits']}")
        if r['accessory_hits']:
            print(f"  accessory_hits: {r['accessory_hits']}")
        if r['nace_hits']:
            print(f"  nace_hits: {r['nace_hits']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
