# HALUCYNACJA Audit — 2026-08-31

Total flagged: **0** leads in PL-B

## Summary

| Verdict | Count |
|---|---|
| CONFIRMED HALUCYNACJA (KRS→other company) | 0 |
| LIKELY FALSE POSITIVE (NIP mod-11 OK) | 0 |
| LIKELY FALSE POSITIVE (KRS matches CSV) | 0 |
| UNVERIFIED (KRS API unreachable) | 0 |
| UNVERIFIED (NIP mod-11 fails; needs registry check) | 0 |

## Per-row details

| ID | Name | NIP CSV | KRS CSV | mod-11 | KRS lookup | Verdict |
|---|---|---|---|---|---|---|

## Notes

- **CONFIRMED HALUCYNACJA**: KRS API returns a NIP that doesn't match the CSV's NIP. The CSV's `krs_id` is real but belongs to a different company. The verifier was right.
- **LIKELY FALSE POSITIVE**: mod-11 actually passes (verifier had a bug), or KRS lookup matches. The CSV value is correct; the flag should be cleared.
- **UNVERIFIED**: cannot reach the registry or mod-11 genuinely fails. Needs manual review.
