"""
append_market_section.py — dodaje sekcję '## Rynek — wolumen wyszukiwań (szac. 2026-09-04)'
do pliku <Kraj>.md (lub Serbia.md dla RS) na podstawie SŁOWNIK-<CC>.md.

Atomic write (tmp + os.replace). Jeśli sekcja już istnieje — skip.

Użycie:
    python3 tools/append_market_section.py          # wszystkie kraje
    python3 tools/append_market_section.py --dry    # tylko pokaż co doda
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (kod, nazwa_katalogu, nazwa_pliku_md, populacja_M, wniosek_skrot)
COUNTRIES = [
    ("PL", "Polska", "PL.md", 38.0, "🇵🇱 Rynek macierzysty. Najwyższy wolumen 'nabijarka do tytoniu' w regionie, marketplace Allegro w pełni rozwinięty. BILLS jako exclusive importer PM ma silną pozycję do zagospodarowania 100% polskiego rynku."),
    ("CZ", "Czechy", "CZ.md", 10.5, "🇨🇿 2. rynek CEE. Silna tradycja RYO, konkurencja ze strony Fortis-DB (autoryzowany PM). PEAL a.s. jako TOP hurtownia — partner kanałowy do negocjacji."),
    ("SK", "Słowacja", "SK.md", 5.4, "🇸🇰 Mały rynek, blisko CZ — dystrybucja via Fortis-DB/PEAL pokrywa 70%. Potencjał w cross-border e-commerce (alza.sk)."),
    ("BG", "Bułgaria", "BG.md", 6.5, "🇧🇬 Rosnący rynek Bałkanów, liberalne regulacje, blisko Turcji/Rosji — kanał re-eksportowy. 6.5M ludzi, % palaczy wyższy niż PL."),
    ("HR", "Chorwacja", "HR.md", 3.9, "🇭🇷 Mały rynek (3.9M) + 15M turystów/rok = niszowa szansa w sklepach strefowych. Brak autoryzowanego dystrybutora PM."),
    ("RO", "Rumunia", "RO.md", 19.0, "🇷🇴 2. co do wielkości rynek CEE po PL. Duża tradycja RYO, plain packaging od 2020. PowerMatic jako brand już rozpoznawalny. Brak autoryzowanego importera PL."),
    ("LT", "Litwa", "LT.md", 2.8, "🇱🇹 Mały rynek bałtycki. Pozytyw: silna cyfryzacja, łatwa dystrybucja e-commerce przez Baltics. Negatyw: restrykcje liquidów smakowych."),
    ("LV", "Łotwa", "LV.md", 1.9, "🇱🇻 Najmniejszy z bałtyckich. Tabakeria.lv jako wiodąca sieć specjalistycznych sklepów tytoniowych w Rydze — partner typu 'sieć'."),
    ("EE", "Estonia", "EE.md", 1.3, "🇪🇪 Cyfrowo zaawansowany, mały. Dobry rynek testowy dla e-commerce i direct-to-consumer. Prike/Sanitex jako duzi hurtownicy FMCG."),
    ("SI", "Słowenia", "SI.md", 2.1, "🇸🇮 Mały rynek, tradycja 'trafika'. Powiązanie z HR (wspólny bałkański kanał). Brak autoryzowanego dystrybutora PM."),
    ("MD", "Mołdawia", "MD.md", 2.6, "🇲🇩 Poza UE, liberalne regulacje. Dobry punkt wejścia do regionu. Licencja na przetwarzanie tytoniu to rzadkość — partnerzy typu Tutun-CTC to TOP B1."),
    ("FR", "Francja", "FR.md", 67.0, "🇫🇷 **NAJWIĘKSZY RYNEK UE** dla tradycji bourdinot. 8-15k/mies. dla 'machine à tuber' to 6x więcej niż PL. Wymaga dedykowanego partnera FR z logistyką (Komori-Chambon to benchmark maszyn, nie dystrybutor)."),
    ("RS", "Serbia", "Serbia.md", 6.7, "🇷🇸 Poza scope exclusive BILLS, ale tracking dla competitive intel. KupujemProdajem = główny marketplace. PFE/Imperial/BAT mają tu silne pozycje."),
]

MARKER = "## Rynek — wolumen wyszukiwań (szac. 2026-09-04)"


def parse_top_phrases(slownik_path: Path, n_per_section: int = 3):
    text = slownik_path.read_text(encoding="utf-8")
    sections = re.split(r"^## ", text, flags=re.MULTILINE)
    out = {}
    for sec in sections[1:]:
        title = sec.split("\n", 1)[0].strip()
        matches = re.findall(
            r"^- (.+?)\s*\(szac\.\s*([\d.]+)-([\d.]+)([km]?)/mies\.\)",
            sec, flags=re.MULTILINE,
        )
        enriched = []
        for fraza, lo, hi, unit in matches:
            lo_v = float(lo) * (1000 if unit == "k" else 1)
            hi_v = float(hi) * (1000 if unit == "k" else 1)
            enriched.append((fraza, lo_v, hi_v, unit))
        enriched.sort(key=lambda x: x[2], reverse=True)
        if enriched:
            out[title] = enriched[:n_per_section]
    return out


def fmt_int(n):
    if n >= 1000:
        return f"{int(n/100)/10:.1f}k"
    return f"{int(n)}"


def build_section(code, name, pop, wniosek, top_phrases) -> str:
    lines = [MARKER, ""]
    lines.append(f"> **Auto-gen 2026-09-04** z `SŁOWNIK-{code}.md`. Wolumeny szacunkowe (szac.) "
                 f"— nie real-time Keyword Planner. Weryfikuj w Ahrefs/Senuto/Google Trends "
                 f"przed kampanią. Populacja: {pop}M.")
    lines.append("")
    # Top 5 kategorii po sumie wolumenu
    cat_totals = []
    for cat, items in top_phrases.items():
        total_hi = sum(item[2] for item in items)
        cat_totals.append((cat, total_hi, items))
    cat_totals.sort(key=lambda x: x[1], reverse=True)
    lines.append("### Top kategorie (suma top-3 fraz)")
    lines.append("")
    lines.append("| Kategoria | Top frazy | Wolumen (suma top-3, szac./mies.) |")
    lines.append("|---|---|---|")
    for cat, total, items in cat_totals[:6]:
        frazy = ", ".join(f"`{item[0]}`" for item in items)
        lines.append(f"| {cat} | {frazy} | {fmt_int(total)} |")
    lines.append("")
    # TikTok / social — top hashtagi z SŁOWNIK
    text = (ROOT / "data" / name / f"SŁOWNIK-{code}.md").read_text(encoding="utf-8")
    hash_matches = re.findall(
        r"^- (#\S+)\s*\(szac\.\s*([\d.]+)-([\d.]+)([km]?)/mies\.\)",
        text, flags=re.MULTILINE,
    )
    hash_enriched = []
    for tag, lo, hi, unit in hash_matches:
        lo_v = float(lo) * (1000 if unit == "k" else 1)
        hi_v = float(hi) * (1000 if unit == "k" else 1)
        hash_enriched.append((tag, lo_v, hi_v, unit))
    hash_enriched.sort(key=lambda x: x[2], reverse=True)
    if hash_enriched:
        lines.append("### Top hashtagi TikTok/Instagram (szac./mies.)")
        lines.append("")
        for tag, lo, hi, unit in hash_enriched[:5]:
            lines.append(f"- {tag} → {fmt_int(lo)}-{fmt_int(hi)} wyświetleń/mies.")
        lines.append("")
    # Wniosek
    lines.append(f"### Wniosek dla BILLSzuka")
    lines.append("")
    lines.append(wniosek)
    lines.append("")
    return "\n".join(lines)


def process_country(code, name, md_fname, pop, wniosek, dry: bool):
    country_dir = ROOT / "data" / name
    md_path = country_dir / md_fname
    slownik_path = country_dir / f"SŁOWNIK-{code}.md"
    if not md_path.exists():
        print(f"SKIP {code}: brak {md_path}")
        return False
    if not slownik_path.exists():
        print(f"SKIP {code}: brak {slownik_path}")
        return False
    text = md_path.read_text(encoding="utf-8")
    if MARKER in text:
        # Sprawdź czy jest aktualna (znacznik 2026-09-04)
        if "2026-09-04" in text.split(MARKER, 1)[1].split("\n## ", 1)[0]:
            print(f"OK   {code}: sekcja już aktualna")
            return False
    top = parse_top_phrases(slownik_path)
    section = build_section(code, name, pop, wniosek, top)
    # Wstaw sekcję przed pierwszą sekcję "## " jeśli istnieje, inaczej na końcu
    if "\n## " in text:
        head, _, tail = text.partition("\n## ")
        new_text = head.rstrip() + "\n\n" + section + "\n## " + tail
    else:
        new_text = text.rstrip() + "\n\n" + section
    if dry:
        print(f"[DRY] {code}/{md_fname}: dodaję {len(section)} znaków")
        return True
    tmp = md_path.with_suffix(".md.tmp")
    tmp.write_text(new_text, encoding="utf-8")
    os.replace(tmp, md_path)
    print(f"OK   {code}/{md_fname}: +{len(section)} znaków")
    return True


def main():
    dry = "--dry" in sys.argv
    total = 0
    for code, name, md_fname, pop, wniosek in COUNTRIES:
        if process_country(code, name, md_fname, pop, wniosek, dry):
            total += 1
    print(f"\n{'[DRY] ' if dry else ''}TOTAL: {total}/{len(COUNTRIES)} krajów zaktualizowanych")


if __name__ == "__main__":
    main()