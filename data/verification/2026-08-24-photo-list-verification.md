# Weryfikacja listy firm ze zdjęć (companies.md)

> **Data:** 24 sierpnia 2026
> **Źródło:** `data/verification/companies.md`
> **Metoda:** ARES + rejstrik-firem + termene.ro + listafirme.ro + risco.ro (gentle, public sources only)

---

## Podsumowanie dokumentu

Łączna liczba wpisów: **33** (12 CZ + 21 RO)

| Status | Liczba |
|:---|:---:|
| ACTIVE (nowe leady) | 13 |
| DUPLIKAT (już w master) | 7 |
| EXCLUDE (odrzucone) | 12 |
| HOLD (wymaga follow-up) | 1 |

---

## 🇨🇿 Czechy

| Kod | Nazwa | Adres | NIP | Telefon | Status | Powód wykluczenia | Notatki |
|---|---|---|---|---|---|---|---|
| VIVACE SPOL.- CZECHY | VIVACE spol. s r.o. | Jaurisova 515/4, 140 00 Praha 4 - Michle | CZ 29154529 | +420 777 680 940 | **DUPLIKAT** | Duplikat — już w master jako CZ-A-006 (hurtownik, dobra-trafika.com) | Pełna zgodność NIP + adres z ARES. Już zweryfikowany <font color='#0E7490'><b>[ZAMROŻONY]</b></font> w master. |
| HZ/SHANTI & CO. S.R. | SHANTI & Co. s.r.o. | Zábrdovická 801/11, 615 00 Brno 15 | CZ 25549154 | (+420) 777 749 789 | **DUPLIKAT** | Duplikat — już w master jako CZ-A-008 (hurtownik, shanti.cz) | Pełna zgodność NIP + adres z ARES. Już zweryfikowany <font color='#0E7490'><b>[ZAMROŻONY]</b></font> w master. |
| OREA | OREA HOTELS s.r.o. | Na Pankráci 1062/58, 140 00 Praha 4 | CZ 27176657 | — | **EXCLUDE** | Zła branża — hotelarstwo (CZ-NACE 55100), NIE dystrybutor tytoniowy | ARES: 'Ubytování v hotelích'. Właściciel największej czeskiej sieci hoteli OREA HOTELS & RESORTS. Na fakturze prawdopodobnie noclegi z delegacji handlowej. |
| HZ/KEVARO S.R.O. | Kevaro s.r.o. | Sokolská 1605/66, 2 Praha (dawniej, adres 29.10.2010 - 2.8.2021) | CZ 24755681 | +420 725 506 654 | **HOLD** | Adres niezgodny z rejestrem; brak info o branży tytoniowej | ARES IČO 24755681 (znaleziony 2026-08-24). Aktualny adres: náměstí Přátelství 1518/2, Praha - Hostivař (od 26.6.2023). Sokolská 1605/66 to historyczny adres firmy (29.10.2010–2.8.2021). Vlastník: Invest Rom Service s.r.o. (SK, Banská Bystrica, IČO 51208091) od 26.6.2023. Předmět podnikání: Výroba, obchod a služby + Prodej kvasného lihu. **NIE branża tytoniowa**. |
| 281268 | Jana Zelezna | Jana Žižky 348, 58856 Telč | (brak — brak śladu w ARES) | — | **EXCLUDE** | Osoba fizyczna — brak śladu OSVČ w ARES | Sprawdzono 2026-08-24: brak Jana Železná (ani podobnych nazwisk) w ARES dla Telč 58856. Brak powiązania z branżą tytoniową. Jednorazowa faktura prywatna. |
| JAN SEVIC | Jan Ševic (Ing.) | Hviezdoslavova 1162, 356 01 Sokolov | CZ 7005132222 | +420 608 062 713 | **DUPLIKAT** | Duplikat — już w master jako CZ-A-004 (plnicky-powermatic.cz) | Autoryzowany dystrybutor PowerMatic (I+, II+, III+, IV, V). W master <font color='#A87500'><b>[DO-WERYFIKACJI]</b></font>. |
| 281017 | Iveta Buresova | Arménská 2763/314, 272 01 Kladno | (brak — brak potwierdzonej Ivety Burešovej w Kladno) | — | **EXCLUDE** | Osoba fizyczna — brak potwierdzenia tożsamości w Kladno | Sprawdzono 2026-08-24: w ARES istnieją 3 różne Ivety Burešovej (IČO 87360501 Praha/Chodov, IČO 45574251 Náchod, IČO 63557843 Ostrov, IČO 74305417 Praha) — ŻADNA nie ma siedziby w Kladno. Žadna nie odpowiada danym z faktury (Arménská 2763/314, 272 01 Kladno). Tożsamość niepotwierdzona. |
| HOSTING TIME S.R.O. | Hosting time s.r.o. | Švabinského 1700/4, 702 00 Ostrava 2 | CZ 04302231 | +420 608 184 599 | **EXCLUDE** | Zła branża — nazwa sugeruje hosting IT, brak śladu handlu tytoniem | ARES potwierdza rejestrację (Moravská Ostrava, 6-9 pracowników), ale brak CAEN tytoniowego. Prawdopodobnie usługa hostingowa / IT. |
| 281267 | Hana Sretrova | M. Švabinského 662, 418 01 Bílina | (brak — Mgr. Hana Šretrová v Luhačovice to INNA osoba) | +420 606 084 673 | **EXCLUDE** | Osoba fizyczna — znaleziona Mgr. Hana Šretrová to inna osoba (Luhačovice, NIE Bílina) | Sprawdzono 2026-08-24: Mgr. Hana Šretrová IČO 76140598 (psycholożka, předmět: poradenská činnost + mimoškolní výchova + textil), sídlo Družstevní 883, Luhačovice 76326 — to NIE ta sama osoba co na fakturze (M. Švabinského 662, 418 01 Bílina). Brak powiązania z tytoniem. |
| 281265 | Eva Machacna (OSVČ — z reconsideracji 2026-08-24) | Kunratice u Cvikova 393, 471 55 | CZ 44560176 | — | **ACTIVE** | Nowy lead po deep re-verification — CZ-NACE: Maloobchod s převahou potravin, nápojů a tabákových výrobků | ARES IČO 44560176 (znaleziony 2026-08-24). Datum vzniku 28.9.1992. Sídlo Kunratice u Cvikova 393. CZ-NACE: Maloobchod s převahou potravin, nápojů a tabákových výrobků v nespecializovaných prodejnách. Předmět podnikání: Prodej smíšeného zboží (potraviny + tytoń). Rekomendacja: B4 (akcesoria + artykuły dla palaczy). Mały wolumen. |
| ETABAK.COM JAN ZIMOL | Etabak.com — Jan Zimola | Osvoboditelů 1107, 438 01 Žatec (aktualny adres; Pekařská 2386 to stary adres) | CZ 74215019 (8608082989 to rodné číslo) | +420 777 593 840 | **ACTIVE** | Nowy lead — aktywny e-shop + velkoobchod z kuřáckými potřeby | IČO 74215019 (znaleziony 2026-08-24 w ARES, podnikatel.cz, Finmag). Vlastnik osobiście Jan Zimola (od 1.11.2006). CZ-NACE: 471 Maloobchod v nespecializovaných prodejnách + 20 Výroba chemických látek. Živnosti: Prodej chemických látek (vázaná od 24.10.2022) + Výroba, obchod a služby - Velkoobchod a maloobchod (volná od 1.11.2006). DIČ CZ8608082989 (to jest numer rodny, nie IČO). Adres w zdjęciu (Pekařská 2386) to stary adres; aktualnie Osvoboditelů 1107. 1-5 pracowników. Prawdopodobnie A4 multi-brand lub B4 akcesoria. Wysoki priorytet dla CZ. |
| HZ/DOBRY TABAK | Dobrý tabák s.r.o. | Ruská 83/24, 703 00 Ostrava 3 | CZ 28595611 | +420 737 611 301 | **ACTIVE** | Nowy lead — aktywny kamenný obchod + e-shop + velkoobchod (vodní dýmky, tabáky) | IČO 28595611, dobrytabak.cz. Sklep stacjonarny Ostrava-Vítkovice + e-shop. Prawdopodobnie B4 (shisha/akcesoria) z cross-sell na PowerMatic. |

---

## 🇷🇴 Rumunia

| Kod | Nazwa | Adres | NIP | Telefon | Status | Powód wykluczenia | Notatki |
|---|---|---|---|---|---|---|---|
| COTIGA MARIN ZESEN | Zasen Trade Invest SRL | Soldat Stefan Simion 41, 040588 Bucharest | RO 41399635 | 0723 019 747 | **EXCLUDE** | Zła branża + błędny adres — CAEN Restaurante, zarejestrowany adres Bd. Tineretului 2 | CUI aktywny (J40/9305/2019), ale cautarefirme.ro klasyfikuje jako 'Restaurante'. Adres na fakturze ≠ adres w rejestrze. Możliwa faktura od podmiotu powiązanego. |
| TABACIOC GRUP SRL | Tabacioc Grup SRL | Soseaua Stefan cel Mare, 020152 Bucuresti | RO 25777283 | +40 723 564 876 | **ACTIVE** | Nowy lead — aktywny retail żywność+napoje+tytoń (40M RON 2025) | CUI 25777283, J2009007894407, Stefan cel Mare 60 Sector 2. CAEN 4711. Duży gracz — sprawdzić asortyment tytoniowy w intake. |
| SIBIS CONCEPT COMPAN | SIBIS CONCEPT COMPANY SRL | Strada ZIZINULUI 106A/ D3-B-P-05, 500407 Brașov | RO 38359096 | — | **DUPLIKAT** | Duplikat — już w master jako RO-A-008 (etutun.ro) | Specjalistyczny e-com Powermatic (II+ | III+ | IV) w Braszowie. Już zweryfikowany <font color='#0E7490'><b>[ZAMROŻONY]</b></font> w master. |
| SC RIO TUTUNGERIE SR | SC RIO TUTUNGERIE SRL | STR. ȘTEFAN CEL MARE NR.22, SATU MARE | RO 36305839 | +40 751 551 169 | **ACTIVE** | Nowy lead — aktywny hurt tytoniowy CAEN 4635 (22M RON 2025) | CUI 36305839, J2016000651308. Duży gracz w Satu Mare. TOP priorytet dla hurtu RO. B8. |
| SC GRANDE PLAYER SRL | SC GRANDE PLAYER SRL | Șos. Pantelimon, nr. 291, bl. 9, sc. C, 014459 București | RO 31483207 | +40 741 673 074 | **ACTIVE** | Nowy lead — aktywny detal tytoniowy CAEN 4726 (București) | CUI 31483207, J2013004687409, Pantelimon 291, Sector 2. Mniejszy lead detaliczny. B4. |
| S.C. OSTRO-VICE S.R. | S.C. OSTRO-VICE S.R.L. | Pandurilor 13, bl. A8/2, 240087 Râmnicu Vâlcea | RO 36832359 | +40 755 943 429 | **ACTIVE** | Nowy lead — aktywny (1.5M RON 2024), CAEN do weryfikacji | CUI 36832359, J38/889/2016. W intake sprawdzić CAEN + asortyment. Kategoria B. |
| ROCADRINA SRL | ROCADRINA SRL | CIHEIULUI 144, 410600 Oradea | RO 16483840 | +40 770 304 803 | **ACTIVE** | Nowy lead — aktywny hurt tytoniowy CAEN 4635 (Oradea) | CUI 16483840, J05/1024/2004. CAEN 4635 potwierdzone. Hurtownik tytoniowy w Oradei. B8. |
| RAZVAN ANGHENE | Răzvan Anghene (Dragoș) | Unirea Principatelor nr. 2, Focșani, 620091 | (brak — Răzvan Anghene NIE ma firmy/PFA; to polityk) | +40 755 000 006 | **EXCLUDE** | Brak firmy/PFA — to polityk lokalny AUR, byly dyrektor OTP Bank | Sprawdzono 2026-08-24: brak Răzvan Anghene w ONRC jako PFA/II/SRL/SA. To osoba publiczna — byly dyrektor OTP Bank Focșani, kandydat AUR na burmistrza Focșani (2024), radny CL Focșani (rezygnacja 2026 po powołaniu do CA CUP SA Vrancea). NIE przedsiębiorca tytoniowy. Możliwe: prywatna faktura za usługe doradczą lub podobne. |
| PRIMONET RO SRL | PRIMONET RO SRL | AMATIULUI 47, 440252 Satu Mare | RO 29972252 | +40 751 551 169 | **DUPLIKAT** | Duplikat — już w master jako RO-B-009 (primonet.ro) | UWAGA: telefon w master '+40 21 318 90 00', w zdjęciu '+40 751 551 169' — rozbieżność. Już zweryfikowany <font color='#0E7490'><b>[ZAMROŻONY]</b></font> w master. |
| MAFERDI S.R.L. | MAFERDI S.R.L. | MIORITEI 2/2, Bacău (adres częściowy) | RO 26044671 | 0748 609 163 | **ACTIVE** | Nowy lead — aktywny handel tytoniowy w Bacău | CUI 26044671. Widoczny na afacerist.ro jako sprzedawca țigări electronice + țigări + trabucuri. B4 (akcesoria + e-papierosy). |
| 12.10.2018DZI | Luca Cristian Lucian (PFA?) | Str. Maramureș, bl. C19, ap. 6, 200024 Craiova | (brak — brak potwierdzonego PFA w ONRC dla tego adresu) | +40 742 009 158 | **EXCLUDE** | Osoba fizyczna — brak potwierdzenia PFA w ONRC/ANAF | Sprawdzono 2026-08-24: brak Luca Cristian Lucian PFA z adresem Str. Maramureș, bl. C19, ap. 6, 200024 Craiova w ONRC/ANAF. Istnieje Luca Cristian PFA w Sibiu (handel tekstyl/obuwie, CUI F2002000224327, N. North Data) — ale inna osoba, inny adres. Tożsamość niepotwierdzona. Jednorazowa faktura prywatna. |
| HZ/GRAVO | GRAVO EXPRESS SRL | Str. Sănătății Nr.7, BL8, Ap11, 520064 Sfântu Gheorghe | RO 17456444 | 0721 569 270 | **ACTIVE** | Nowy lead — aktywny retail (CAEN 4778 — inny retail), 1.6M RON 2024 | CUI 17456444, J2005000177141. CAEN 4778 (Comert cu amanuntul — nowe wyroby). Sprawdzić czy obejmuje tytoń. B4. |
| GOLDEN TIP | GOLDEN TIP IMPORT EXPORT SRL | STR.UNIRII 21/25 (+ magazyn Rășinari 429), 400113 Cluj-Napoca | RO 31828233 | +40 761 250 819 | **DUPLIKAT** | Duplikat — już w master jako RO-A-004 (tuburipentrutigari.ro) | UWAGA: telefon w master '0744 545 936', w zdjęciu '+40 761 250 819' — rozbieżność. Już zweryfikowany <font color='#0E7490'><b>[ZAMROŻONY]</b></font> w master. |
| ELMARIO DISTRIBUTION | ElMario Distribution SRL | Comuna VALEA CĂLUGĂREASCĂ 99, 135949 Jud. Prahova | RO 33393950 | +40 726 268 874 | **ACTIVE** | Nowy lead — aktywny retail (CAEN 4719 — inny detal, NIE tytoń stricte) | CUI 33393950, J29/1003/2014, Blejoi/Prahova. CAEN 4719. Prawdopodobnie B4 (akcesoria). Średni priorytet. |
| DVD MASTER SRL | DVD Master SRL | Bucharest (Giurgiu) — bd.54/2D, ap.45, 080122 Giurgiu | RO 15879480 | 0040 723 550 358 | **ACTIVE** | Nowy lead — aktywny hurt tytoniowy CAEN 4635 (61M RON 2025!) | CUI 15879480, J2003000403523. DUŻY gracz hurtowy w Giurgiu. TOP priorytet dla działu sprzedaży. B8. |
| 150713-14 | DIPA CONCEPT SRL | BLD. SCHITU MĂGUREANU Nr. 27-33 27/33, București | RO 31861043 | +40 758 550 055 | **EXCLUDE** | Działalność zawieszona — status INACTIVĂ w firmealert.ro | CUI 31861043, J40/7708/2013. CAEN 4635 (hurt tytoniowy), ale firma wykreślona. Dodać do archiwum. |
| COTIGA MARIN COTY SH | COTY SHOP INVEST S.R.L. | STR.IZVORUL MUREȘULUI NR.9, BL. D9 SC.6, 040588 BUCUREȘTI | RO 48831012 | 0723 019 747 | **DUPLIKAT** | Duplikat — już w master jako RO-A-009 (prawidłowy CUI 48715727, NIE 48831012) | BŁĄD W CUI: foto podaje 48831012, prawidłowy CUI 48715727. Administrator: COTIGĂ MARIN (ten sam co wpis 'Cotiga Marin'). |
| COTIGA MARIN | Cotiga Marin (osoba fizyczna) | Soldat Stefan Simion 41, 040588 Bucharest | (brak osobistego CUI; admin 2 firm) | 0723 019 747 | **EXCLUDE** | Duplikat admina — COTIGĂ MARIN to administrator COTY SHOP INVEST + ZASEN TRADE INVEST | Sprawdzono 2026-08-24 (datasrl.ro): COTIGĂ MARIN (Buzău) jest administratorem 2 firm: (1) COTY SHOP INVEST S.R.L. (CUI 48715727, Sector 4, AKTYWNA); (2) ZASEN TRADE INVEST S.R.L. (CUI 41399635, Sector 4, INAKTYWNA/radiată). Własnego PFA/II NIE ma. Telefon +40723019747 widoczny w odpowiedziach na Facebook (Cotiga Marin jako admin COTY SHOP). Faktura prywatna wystawiona przez admina. **Scal z istniejącym RO-A-009 (COTY SHOP)**. |
| AM/CERBU IOANA | Cerbu Ioana | Jilava, Str. Toamnei nr 5, 077120 Jud. Ilfov | (brak osobistego CUI; admin GRAND PRODUCT SRL) | +40 764 088 453 | **EXCLUDE** | Osoba fizyczna — administrator GRAND PRODUCT SRL (mobilier, suspendată) | Sprawdzono 2026-08-24 (datasrl.ro): CERBU IOANA (București) administrator firmy GRAND PRODUCT SRL (CUI 16049841, J23/27/2004, Sat Jilava, CAEN 4647 comerț cu ridicata al mobilei/covoarelor/iluminatului). GRAND PRODUCT: wtrerupere temporară de activitate (firmeo.ro) + suspendată (firme360.ro). Własnego PFA/II NIE znaleziono. Brak powiązania z branżą tytoniową. |
| BLK TRADE | BLK TRADE MARKET S.R.L. | Bulevard Tudor Vladimirescu 15, 700305 Iași | RO 40694700 | 0040 740 768 387 | **ACTIVE** | Nowy lead — aktywny e-commerce (CAEN 4791). UWAGA: błędny CUI w zdjęciu | BŁĄD W CUI: foto podaje 40694700, prawidłowy CUI 40638971, J22/855/2019. W intake wpisać 40638971. |
| ARTHEK MACHINES SRL | ARTHEK Machines SRL | Noua 49, 505100 Codlea | RO 43407106 | +40 771 643 634 | **EXCLUDE** | Zła branża — CAEN 3314 (naprawa urządzeń elektr.), nie dystrybutor | CUI 43407106. Domena 'Machines' sugeruje maszynki, ale firma to serwis (naprawa sprzętu elektr.). Opcjonalnie: dodać jako anti-pattern / competitor intel. |

---

## Rekomendacja — co przenieść do data/_intake/

Po akceptacji Marcelego, 13 firm powinno zostać zrzuconych do data/_intake/:

- [CZ] **Eva Machacna (OSVČ — z reconsideracji 2026-08-24)** (CZ 44560176) — Nowy lead po deep re-verification — CZ-NACE: Maloobchod s převahou potravin, nápojů a tabákových výrobků
- [CZ] **Etabak.com — Jan Zimola** (CZ 74215019 (8608082989 to rodné číslo)) — Nowy lead — aktywny e-shop + velkoobchod z kuřáckými potřeby
- [CZ] **Dobrý tabák s.r.o.** (CZ 28595611) — Nowy lead — aktywny kamenný obchod + e-shop + velkoobchod (vodní dýmky, tabáky)
- [RO] **Tabacioc Grup SRL** (RO 25777283) — Nowy lead — aktywny retail żywność+napoje+tytoń (40M RON 2025)
- [RO] **SC RIO TUTUNGERIE SRL** (RO 36305839) — Nowy lead — aktywny hurt tytoniowy CAEN 4635 (22M RON 2025)
- [RO] **SC GRANDE PLAYER SRL** (RO 31483207) — Nowy lead — aktywny detal tytoniowy CAEN 4726 (București)
- [RO] **S.C. OSTRO-VICE S.R.L.** (RO 36832359) — Nowy lead — aktywny (1.5M RON 2024), CAEN do weryfikacji
- [RO] **ROCADRINA SRL** (RO 16483840) — Nowy lead — aktywny hurt tytoniowy CAEN 4635 (Oradea)
- [RO] **MAFERDI S.R.L.** (RO 26044671) — Nowy lead — aktywny handel tytoniowy w Bacău
- [RO] **GRAVO EXPRESS SRL** (RO 17456444) — Nowy lead — aktywny retail (CAEN 4778 — inny retail), 1.6M RON 2024
- [RO] **ElMario Distribution SRL** (RO 33393950) — Nowy lead — aktywny retail (CAEN 4719 — inny detal, NIE tytoń stricte)
- [RO] **DVD Master SRL** (RO 15879480) — Nowy lead — aktywny hurt tytoniowy CAEN 4635 (61M RON 2025!)
- [RO] **BLK TRADE MARKET S.R.L.** (RO 40694700) — Nowy lead — aktywny e-commerce (CAEN 4791). UWAGA: błędny CUI w zdjęciu
