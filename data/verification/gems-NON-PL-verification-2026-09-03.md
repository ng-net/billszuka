# gems-NON-PL.csv — weryfikacja 2026-09-03

## Kontekst
Plik `data/gems-NON-PL.csv` zawiera 127 'gem'ów' (wysokiej jakości leady B2B) wyekstrahowanych
z narzędzia `tools/find_gems.py` w sesji 2026-08-31 19:25 CEST.

**Stan przed 2026-09-03:**
- 124/127 unikalnych ID jest już w `data/master.csv` (w katalogach per-kraj).
- Brakuje 2 ID: **SK-B-029** i **SK-X-001**.

## Wynik weryfikacji brakujących 2 ID (2026-09-03)

### SK-B-029: D.A. CZVEDLER, spol. s r.o. (Šamorín)
- **WERYFIKACJA:** ❌ **DISSOLVED — NIE DODAWAĆ**
- IČO: 34114726
- DIČ: 2020369835
- IČ DPH: SK2020369835
- Sídlo: Kláštorná 4, 931 01 Šamorín
- Dátum vzniku: 24.01.1995
- **Dátum výmazu: 1.6.2026** ← spoločnosť zrušená
- Základné imanie: 11 554 €
- Zdroj: FinStat.sk/34114726, registeruz.sk/cruz-public/domain/accountingentity/show/418556, azet.sk/firma/11070
- **Akcia:** successor = MEDIAPRESS Bratislava a.s. (už v master ako SK-A-015).
  Wpis w gems został zachowany jako wpis historyczny, ale **nie dodajemy nowego wpisu** do master.

### SK-X-001: KON - RAD spol. s r.o. (Bratislava)
- **WERYFIKACJA:** ✅ **VERIFIED — DODANY JAKO SK-B-019**
- IČO: 00684104
- DIČ: 2020301195
- IČ DPH: SK2020301195
- Sídlo: Cesta na Senec 15725/24, 830 06 Bratislava
- Konateľ: Mgr. František Paller (od 20.09.1990)
- OR: Mestský súd Bratislava III, odd. Sro, vl. 98/B
- Tržby 2025: 35,232,788 EUR (35M EUR)
- Aktíva 2025: 21,250,124 EUR
- Základné imanie: 2,258,030 EUR (165k EUR konvertované zo SKK)
- Počet zamestnancov: 100-149
- 7000 tovarových položiek (FMCG + tabakové výrobky — cigarety, cigary)
- Distribúcia celé Slovensko
- Zdroje: FinStat.sk/00684104, kon-rad.eu/o-nas
- **Akcia:** ✅ dodany do `data/Słowacja/catalog-B-SK.csv` jako **SK-B-019** (B5 - adjacent FMCG)
  z flagą `✅ FROZEN (API)` i powinowactwo 1 (nie core tabak, ale wiarygodny i duży kanał).

## Rekomendacja
- Usunąć SK-B-029 z `data/gems-NON-PL.csv` (dead lead) — lub zostawić jako historyczny,
  oznaczony flagą DISSOLVED, żeby nie był brany do kolejnych sesji.
- SK-X-001 może zostać w gems-NON-PL.csv jako archive record (zaktualizowany do SK-B-019).
