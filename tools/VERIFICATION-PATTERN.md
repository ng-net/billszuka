# BILLSzuka verification pattern (reusable)

## Two-tool check protocol

For every lead in the master CSV, verify with **2 independent tools** before marking FROZEN.

### Tool 1: web_search (confirmation)
Query: `"<nazwa>" "<miasto>" "<kraj>" tobacco wholesale verify site:<firma_www>`
Pass: company name, address, contact info match
Fail: no result, or different company with same name

Side effect: may extract NIP/IČO/reg number from official sites (KRS, ARES, douane.gouv.fr, etc.)

### Tool 2: whois (domain validity)
Query: `whois -h <TLD-server> <domain>`
- ccTLD whois servers: see RIPE WHOIS database or tld-list.com per TLD
- For .com/.net: `whois.verisign-grs.com`
Pass: domain active, registered before, has working nameservers
Fail: domain not registered, available for purchase, or hijacked

### Tool 3 (optional): registry API
Only when NIP/IČO/reg number known:
- PL sp. z o.o.: KRS API (krs number) or CEIDG (NIP for JDG)
- PL JDG: CEIDG v3
- CZ: ARES (IČO)
- SK: ORSR
- LT: rekvizitai
- See `verify_api.py` for live calls

## Verdict logic

| Tool 1 | Tool 2 | Tool 3 | Verdict |
|---|---|---|---|
| ✓ pass | ✓ pass | (any) | ✅ FROZEN |
| ✓ pass | (no www) | ✓ pass | ✅ FROZEN |
| ✓ pass | ✗ fail | ✓ pass | ⚠️ CONCERN (whois only) |
| ✓ pass | ✗ fail | ✗ fail | ⚠️ DO-WERYFIKACJI |
| ✗ fail | (any) | (any) | ⚠️ DO-WERYFIKACJI |

## Output schema (per lead)

```json
{
  "id": "CZ-B-XX-001",
  "name": "GGT CZ a.s.",
  "country": "CZ",
  "verdict": "✅ FROZEN | ⚠️ CONCERN | ⚠️ DO-WERYFIKACJI | PENDING",
  "evidence": {
    "web_search": {"status": "pass", "snippet": "...", "extracted_nip": "26293609"},
    "whois": {"domain": "ggtabak.cz", "domain_active": true, "registrar": "REG-ZONER", "created": "2001-08-10"},
    "registry": {"status": "pass", "firma": "GGT CZ a.s.", "matches": true}
  }
}
```

## Storage

- Per-run output: `tools/.verify-runs/<timestamp>.jsonl` (one JSON per line)
- Checkpoint: `tools/.verify-checkpoint.json` (list of completed IDs for `--resume`)
- Audit log: appended to `data/audit-log.md` with summary
- Master CSV: `flagi` column updated with verdict

## Re-run command

Use `verify_api.py` for live registry verification. The legacy `verify_lead.py`
script was retired on 2026-09-03 — its verification logic now lives in
`verify_api.py` (registry) and the two-tool pattern is run by the agent
(web_search + whois on demand).

```bash
# Live registry verification for one country
python3 tools/verify_api.py --country PL

# Re-verify all FROZEN rows for FABRYKAT pattern
python3 tools/verify_api.py --all --retrofix

# Full sweep via billszuka CLI
python3 tools/billszuka.py verify --all
```

## Skills to chain

- `web_search` (host tool) — Tool 1
- `web_fetch` (host tool) — for specific URL content
- `apify-public-registries` — bulk registry check across 11 countries
- `vies-api` — VAT EU validation (NIP/IČO + country)
- `who-owns-this-domain` — alternative to whois with more detail
- `x-ray-a-company` — deep dive ownership/structure (when needed)
- `useosint` — router for misc verification
- `crawl4ai-skill` — for JS-rendered sites

## Notes

- whois for .hr / .ro / .md often blocked or privacy-protected → fall back to web search as Tool 2
- TLD whois server: query `whois.iana.org` for the right server, or check tld-list.com
- For new countries: extend the ccTLD list as needed

## Cron

```bash
mavis({ command: "cron create", args: {
  cron_name: "verify-billszuka-leads",
  schedule: "0 10 * * 1-5",  # weekdays 10am Warsaw
  prompt: "Run cd /Volumes/MC-BRAIN/Dev-Ext/BILLSzuka && python3 tools/verify_api.py --all. Report new FROZEN/DO-WERYFIKACJI counts.",
  session: { mode: "sessionId", session_id: "me" }
} })
```
