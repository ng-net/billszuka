# Gems — non-PL B2B partner candidates

**Date:** 2026-08-31  
**Source:** `tools/find_gems.py` sweep across 12 non-PL countries  
**Total raw gems:** 112 across 9 countries with catalog-B data

## Criteria (gate)
- FROZEN flag (verifier-confirmed, not DO-WERYFIKACJI/PENDING/HALUCYNACJA)
- Has contact (email or telefon)
- Score ≥ 3: whale signal (5) + powinowactwo 4-5 (2) + B2B tier/category (2) + real sourcing (1)

## Per-country summary

| ISO | Country | Gems | Top score | Actionable (score≥5, no multi) |
|---|---|---|---|---|
| BG | Bułgaria | 24 | 10 | 13 |
| EE | Estonia | 19 | 9 | 3 |
| SK | Słowacja | 15 | 10 | 11 |
| RO | Rumunia | 13 | 9 | 1 |
| FR | Francja | 12 | 9 | 0 |
| HR | Chorwacja | 11 | 10 | 6 |
| LT | Litwa | 9 | 7 | 1 |
| SI | Słowenia | 6 | 10 | 4 |
| LV | Łotwa | 3 | 5 | 1 |

**Empty / no catalog-B:** CZ Czechy, MD Mołdawia, RS Serbia

Czechy uses `catalog-A-CZ.csv` only (no B-catalog yet). Mołdawia and Serbia
have catalog-B but no rows passed FROZEN+contact+score≥3 gate.

## Top 5 actionable leads per country (multinationals filtered)

Filter: score ≥ 5 AND name ∉ {Philip Morris, JTI, JT International, Imperial Tobacco, Imperial Brands, BAT (incl. BAT Adria), Logista, Japan Tobacco}.  
Rationale: multinationals typically have corporate procurement, not local buying — usually unreachable for B2B partnership.

### BG — Bułgaria (13 actionable)

| # | Score | 🐋 | Name | Pow | City | Contact |
|---|---|---|---|---|---|---|
| 1 | 10 | ✓ | БОЛКАН ЕДВЪРТАЙЗИНГ ЕНД ДИСТРИБЮШЪН ООД | 4 | София | office@tobacco-import.com |
| 2 | 10 | ✓ | ДЕЛИОН ООД (Delion OOD - VM Finance Grou | 4 | София | office@delion.bg |
| 3 | 9 | ✓ | Tobacco Distribution OOD | 5 | Sofia | office@tobacco.bg |
| 4 | 9 | ✓ | ЕКСПРЕС ЛОГИСТИКА И ДИСТРИБУЦИЯ ЕООД (EL | 3 | София | office@eld.bg |
| 5 | 5 |  | BEKI 2015 EOOD (БЕКИ 2015) | 5 | Dupnitsa | info@beki2015.bg |

### EE — Estonia (3 actionable)

| # | Score | 🐋 | Name | Pow | City | Contact |
|---|---|---|---|---|---|---|
| 1 | 9 | ✓ | RYO Paper & Tobacco OÜ | 3 | Tallinn | info@rollingpaper.ee |
| 2 | 5 |  | OÜ SANITEX | 5 | Rae küla | sanitex.estonia@sanitex.eu |
| 3 | 5 |  | Aleserk OÜ | 4 | Hüüru | info@aleserk.com |

### SK — Słowacja (11 actionable)

| # | Score | 🐋 | Name | Pow | City | Contact |
|---|---|---|---|---|---|---|
| 1 | 10 | ✓ | GECO, s. r. o. | 5 | Bratislava | info@geco.sk |
| 2 | 10 | ✓ | NOBA – SMOKER, s.r.o. | 4 | Trenčín | smoker@smoker.sk |
| 3 | 5 |  | TOPPRES D.A., spol. s r.o. | 4 | Banská Bystrica | toppres@toppres.sk |
| 4 | 5 |  | T-PRESS, spol. s r.o. | 4 | Trnava | velkosklad@t-press.sk |
| 5 | 5 |  | D.A. CZVEDLER, spol. s r.o. | 4 | Šamorín | sekretariat@czvedler.sk |

### RO — Rumunia (1 actionable)

| # | Score | 🐋 | Name | Pow | City | Contact |
|---|---|---|---|---|---|---|
| 1 | 9 | ✓ | INTERBRANDS ORBICO SRL | 5 | București | office.romania@orbico.com |

### HR — Chorwacja (6 actionable)

| # | Score | 🐋 | Name | Pow | City | Contact |
|---|---|---|---|---|---|---|
| 1 | 10 | ✓ | TISAK PLUS d.o.o. (Tisak / Fortenova Gru | 4 | Zagreb | info@tisak.hr |
| 2 | 10 | ✓ | ROX d.o.o. | 4 | Zagreb | info@rox.hr |
| 3 | 9 | ✓ | HRVATSKI DUHANI d.d. | 3 | Virovitica | info@hrvatskiduhani.hr |
| 4 | 9 | ✓ | ORBICO d.o.o. | 3 | Zagreb | info.croatia@orbico.com |
| 5 | 9 | ✓ | ATLANTIC TRADE d.o.o. (Atlantic Grupa) | 3 | Zagreb | kontakt@atlanticgrupa.com |

### LT — Litwa (1 actionable)

| # | Score | 🐋 | Name | Pow | City | Contact |
|---|---|---|---|---|---|---|
| 1 | 7 | ✓ | UAB Ecodumas | 2 | Kaunas | wholesale@ecodumas.com |

### SI — Słowenia (4 actionable)

| # | Score | 🐋 | Name | Pow | City | Contact |
|---|---|---|---|---|---|---|
| 1 | 10 | ✓ | TOBAČNA 3DVA, d.o.o. (Trafika 3DVA) | 5 | Ljubljana | 3dvainfo@si.imptob.com |
| 2 | 10 | ✓ | DELO PRODAJA, d.o.o. | 4 | Ljubljana | info@deloprodaja.si |
| 3 | 10 | ✓ | Poslovni sistem Mercator d.o.o. (Cash &  | 5 | Ljubljana | info@mercator.si |
| 4 | 5 |  | OTP, trgovina s tobakom, d.o.o. (Scandin | 4 | Ljubljana | info.si@st-group.com |

### LV — Łotwa (1 actionable)

| # | Score | 🐋 | Name | Pow | City | Contact |
|---|---|---|---|---|---|---|
| 1 | 5 |  | SIA SANITEX | 5 | Rāmava (Ķekavas no | sanitex@sanitex.eu |

## Multi-country group deal hints

Looking for cross-border leverage (one deal = multiple markets):

- **Baltic tobacco wholesale (SANITEX group)**: 2 matches
  - EE — OÜ SANITEX (score 5)
  - LV — SIA SANITEX (score 5)

- **BAT Adria network (Croatia)**: 2 matches
  - HR — TDR d.o.o. (Tvornica duhana Rovinj / BAT Adria) (score 10)
  - HR — iNOVINE d.d. (BAT Adria Network) (score 10)

- **Philip Morris regional**: 3 matches
  - SK — Philip Morris Slovakia s.r.o. (score 10)
  - SI — Philip Morris Ljubljana, d.o.o. (score 10)
  - EE — Philip Morris Eesti (score 4)

- **JTI regional**: 2 matches
  - SK — JTI Slovak Republic, s.r.o. (score 10)
  - SI — JT International Ljubljana, d.o.o. (score 10)

- **Imperial Tobacco regional**: 3 matches
  - SK — Imperial Brands Slovakia a. s. (score 10)
  - EE — Imperial Tobacco Estonia OÜ (score 9)
  - BG — IMPERIAL BRANDS BULGARIA EOOD (Imperial Tobacco) (score 4)

- **Mercator (SI) → cross-border HR**: 1 matches
  - SI — Poslovni sistem Mercator d.o.o. (Cash & Carry) (score 10)

- **Tobacco Trade Bulgaria chain (multi-city)**: 6 matches
  - BG — Табако Трейд Варна ООД (Tobacco Trade Varna Ltd) (score 5)
  - BG — Табако Трейд Стара Загора ООД (Tobacco Trade Stara Zago (score 5)
  - BG — Табако Трейд Русе ООД (Tobacco Trade Ruse Ltd) (score 5)
  - BG — Табако Трейд Хасково ООД (Tobacco Trade Haskovo Ltd) (score 5)
  - BG — Табако Трейд Благоевград ООД (Tobacco Trade Blagoevgrad (score 5)
  - BG — TOBACCO TRADE PLEVEN OOD (score 4)
