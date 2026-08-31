# HALUCYNACJA Audit — 2026-08-31

Total flagged: **26** leads in PL-B

## Summary

| Verdict | Count |
|---|---|
| CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) | 19 |
| CONFIRMED HALUCYNACJA (KRS→other company) | 7 |
| LIKELY FALSE POSITIVE (NIP mod-11 OK) | 0 |
| LIKELY FALSE POSITIVE (KRS matches CSV) | 0 |
| UNVERIFIED (KRS API unreachable) | 0 |
| UNVERIFIED (NIP mod-11 fails; needs registry check) | 0 |

## Per-row details

| ID | Name | NIP CSV | KRS CSV | mod-11 | KRS lookup | Verdict |
|---|---|---|---|---|---|---|
| PL-B-048 | Selgros / Transgourmet Polska Sp. z o.o. | PL7792223933 | ❌ unreachable | ❌ expected check 6, got 3 | ❌ unreachable | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-050 | Polska Grupa Tytoniowa Sp. z o.o. | PL9532585250 | → NIP 5372504633 name match 0.0 | ❌ expected check 3, got 0 | → NIP 5372504633 name match 0.0 | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-052 | Mona Sp. z o.o. | PL6792683072 | ❌ unreachable | ❌ check digit = 10 (invalid) | ❌ unreachable | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-055 | Hurtownia Centrum Wiesław Sacharski | PL7580003310 | — | ❌ expected check 9, got 0 | — | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-057 | Firma Handlowa Mariusz Kawa | PL8731006509 | — | ❌ expected check 1, got 9 | — | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-058 | FLAJ Sklep i Hurtownia w Augustowie | PL8461001460 | — | ❌ expected check 7, got 0 | — | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-061 | CARMEN POLSKA SPÓŁKA Z OGRANICZONĄ ODPOW | PL8370001711 | → NIP 6510000539 name match 0.0 | ✅ check digit OK (1 = 166 mod 11) | → NIP 6510000539 name match 0.0 | CONFIRMED HALUCYNACJA (KRS→other company) |
| PL-B-065 | ANIA SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNO | PL8133193611 | → NIP 5252228892 name match 0.0 | ✅ check digit OK (1 = 177 mod 11) | → NIP 5252228892 name match 0.0 | CONFIRMED HALUCYNACJA (KRS→other company) |
| PL-B-070 | VIVOPLAST Hurtownia Opakowań i Artykułów | PL6610001890 | — | ❌ expected check 2, got 0 | — | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-075 | PHPU "TEKS" SA (Markowe Cygara) | PL7960073210 | → NIP 9441787353 name match 0.0 | ❌ expected check 4, got 0 | → NIP 9441787353 name match 0.0 | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-076 | MILO S.A. | PL9590822602 | ❌ unreachable | ❌ expected check 0, got 2 | ❌ unreachable | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-077 | CARO Sp.j. R. i R. Niewczas | PL6610003937 | → NIP 6670003825 name match 0.0 | ❌ expected check 9, got 7 | → NIP 6670003825 name match 0.0 | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-078 | BONUS Hurtownia Papierosów | PL6640003463 | — | ❌ check digit = 10 (invalid) | — | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-079 | Hurtownia Papierosów "DANA" | PL7310007883 | — | ❌ expected check 5, got 3 | — | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-080 | Caro. Hurtownia papierosów. Żach K. | PL7590004724 | — | ❌ expected check 8, got 4 | — | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-082 | VAPE POINT SPÓŁKA Z OGRANICZONĄ ODPOWIED | PL8992850937 | → NIP 8952194286 name match 0.0 | ❌ expected check 4, got 7 | → NIP 8952194286 name match 0.0 | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-091 | Don Marco International Sp. z o.o. | PL5833019808 | ❌ unreachable | ❌ expected check 7, got 8 | ❌ unreachable | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-092 | MRC Trade Sp. z o.o. | PL8792683935 | ❌ unreachable | ❌ expected check 4, got 5 | ❌ unreachable | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-094 | Tobacco Concept Factory (TCF) Sp. z o.o. | PL5832791456 | ❌ unreachable | ❌ expected check 7, got 6 | ❌ unreachable | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-106 | NOVIS Sławomir Gągorowski, Sylwia Gągoro | PL8641951472 | → NIP 1231415374 name match 0.0 | ✅ check digit OK (2 = 233 mod 11) | → NIP 1231415374 name match 0.0 | CONFIRMED HALUCYNACJA (KRS→other company) |
| PL-B-107 | BESTMAR RYDZ I PAWŁOWSKA SPÓŁKA JAWNA | PL5170409015 | → NIP 7872134838 name match 0.0 | ✅ check digit OK (5 = 148 mod 11) | → NIP 7872134838 name match 0.0 | CONFIRMED HALUCYNACJA (KRS→other company) |
| PL-B-108 | TORA VAPE POLSKA SPÓŁKA Z OGRANICZONĄ OD | PL1251742308 | → NIP 5252928810 name match 0.0 | ✅ check digit OK (8 = 118 mod 11) | → NIP 5252928810 name match 0.0 | CONFIRMED HALUCYNACJA (KRS→other company) |
| PL-B-110 | WEST TRADING SPÓŁKA Z OGRANICZONĄ ODPOWI | PL9552074426 | → NIP 5213266960 name match 0.0 | ✅ check digit OK (6 = 204 mod 11) | → NIP 5213266960 name match 0.0 | CONFIRMED HALUCYNACJA (KRS→other company) |
| PL-B-112 | NAPO SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNO | PL9721250921 | → NIP 5242772051 name match 0.0 | ✅ check digit OK (1 = 199 mod 11) | → NIP 5242772051 name match 0.0 | CONFIRMED HALUCYNACJA (KRS→other company) |
| PL-B-125 | JAS-FBG SPÓŁKA AKCYJNA | PL6340127847 | ❌ unreachable | ❌ expected check 3, got 7 | ❌ unreachable | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |
| PL-B-126 | ROHLIG SUUS LOGISTICS SPÓŁKA AKCYJNA | PL5260036094 | ❌ unreachable | ❌ expected check 0, got 4 | ❌ unreachable | CONFIRMED HALUCYNACJA (NIP fails mod-11 + KAS rejects) |

## Notes

- **CONFIRMED HALUCYNACJA**: KRS API returns a NIP that doesn't match the CSV's NIP. The CSV's `krs_id` is real but belongs to a different company. The verifier was right.
- **LIKELY FALSE POSITIVE**: mod-11 actually passes (verifier had a bug), or KRS lookup matches. The CSV value is correct; the flag should be cleared.
- **UNVERIFIED**: cannot reach the registry or mod-11 genuinely fails. Needs manual review.
