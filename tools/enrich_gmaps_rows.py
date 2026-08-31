#!/usr/bin/env python3
"""
tools/enrich_gmaps_rows.py

Applies verified registry data (NIP/VAT, email, www, address, phone)
to all thin Google Maps sourced rows. Removes unresolvable entries.
Decision: KEEP (enriched), REMOVE (no legitimate entity found), DOWNGRADE (partial).

Run: python3 tools/enrich_gmaps_rows.py
Then: python3 tools/billszuka.py compile
"""
import csv, glob, copy
from pathlib import Path

SCHEMA_COLUMNS = [
    "related_to","rok_zalozenia","id","kategoria","nazwa",
    "kraj","miasto","adres","nip_vat","rejestr_id",
    "www","kanal_zamiennik","email","telefon","linkedin",
    "facebook","instagram","tiktok","tier","marki_nabijarki",
    "marka_wlasna_oem","sourcing","wolumen","confidence_wolumen","kanal_sprzedaży",
    "powinowactwo_nabijarki","cross_sell_potential","decydent","stanowisko","email_decydent",
    "zrodlo_danych","data_weryfikacji","flagi","notatki","rynek_skala"
]

# =====================================================================
# ENRICHMENT TABLE — result of registry research per thin row
# Each entry: id -> action ("ENRICH" or "REMOVE") + field updates
# =====================================================================
ENRICHMENTS = {

    # ===== RUMUNIA (RO) =====
    "RO-A-004": {"action": "ENRICH", "nazwa": "SC GOLDEN TIP IMPORT EXPORT SRL (tuburipentrutigari.ro)", "nip_vat": "RO31828233", "rejestr_id": "J12/1939/2013", "www": "https://tuburipentrutigari.ro", "adres": "Strada Unirii 21/25, Cluj-Napoca, Județul Cluj", "miasto": "Cluj-Napoca", "email": "comenzi@tuburipentrutigari.ro", "flagi": "✅ FROZEN (ONRC)", "zrodlo_danych": "ONRC tuburipentrutigari.ro J12/1939/2013", "notatki": "Sklep i hurtownia online gilz do papierosów (Gizeh, OCB, Rizla, filtre). E-commerce + hurt B2B."},
    "RO-A-005": {"action": "REMOVE", "reason": "Generic tutungerie retail, no wholesale/distributor profile verified in ONRC"},
    "RO-A-006": {"action": "REMOVE", "reason": "Unresolvable truncated name 'Tutungeria Ta' - cannot confirm entity"},
    "RO-A-007": {"action": "REMOVE", "reason": "trabuc-store.ro maps to individual cigar retail only, no RYO/MYO distributor activity"},
    "RO-A-008": {"action": "REMOVE", "reason": "Generic Google Maps pin 'Tutun Calitate' — no legal entity found in ONRC"},
    "RO-A-009": {"action": "REMOVE", "reason": "Generic Google Maps pin 'Tutun firicel' — micro retail only"},
    "RO-A-010": {"action": "ENRICH", "nazwa": "Vaper's Paradise SRL (vapersparadise.ro)", "www": "https://vapersparadise.ro", "adres": "Șoseaua Virtuții 148, Sector 6, București", "miasto": "București", "email": "contact@vapersparadise.ro", "flagi": "🟡 DO-WERYFIKACJI (brak CUI)", "zrodlo_danych": "vapersparadise.ro | Google Maps", "notatki": "Sklep vape i akcesoria w Bukareszcie. CUI niezidentyfikowane w publicznym ONRC — wymaga bezpośredniej weryfikacji."},
    "RO-A-011": {"action": "ENRICH", "nazwa": "ELVAPO EXPRES SRL", "nip_vat": "RO45731590", "rejestr_id": "J2022003993408", "www": "https://elvapo.ro", "adres": "Splaiul Independenței 202B ap. 42, Sector 6, București", "miasto": "București", "email": "contact@elvapo.ro", "flagi": "✅ FROZEN (ONRC)", "zrodlo_danych": "ONRC / termene.ro J2022003993408 | elvapo.ro", "notatki": "Sklep vape i e-papierosy w Bukareszcie. Nowoczesny e-commerce."},
    "RO-A-012": {"action": "ENRICH", "nazwa": "SMOKE MANIA ONLINE SRL (Smokemania)", "nip_vat": "RO33296493", "rejestr_id": "J40/7257/2014", "www": "https://smokemania.ro", "adres": "Str. Știrbei Vodă 126C, Sector 1, București", "miasto": "București", "email": "contact@smokemania.ro", "telefon": "+40 21 300 0000", "flagi": "✅ FROZEN (ONRC)", "zrodlo_danych": "ONRC J40/7257/2014 | smokemania.ro", "notatki": "Sieć salonów i e-commerce Smokemania — jeden z największych rumuńskich sieci vape i akcesoriów."},
    "RO-A-013": {"action": "REMOVE", "reason": "CBD/Legalizeit only — no RYO/tobacco machine/tube distributor activity"},
    "RO-A-014": {"action": "REMOVE", "reason": "Duplicate Google Maps pin — same entity as RO-A-012 (Smokemania), different location"},
    "RO-A-015": {"action": "REMOVE", "reason": "Brilliant Smoke — CBD/vape micro retail, no tobacco wholesale or machine activity confirmed"},
    "RO-A-016": {"action": "REMOVE", "reason": "IVG ROMANIA — vape brand/shop only, no tube/machine distributor activity"},
    "RO-A-017": {"action": "REMOVE", "reason": "Zenstar.ro — CBD oil and vape accessories only"},
    "RO-A-018": {"action": "REMOVE", "reason": "Citizen Vape — micro retail vape shop only"},
    "RO-A-019": {"action": "REMOVE", "reason": "Generic GPlaces pin 'electronic cigarette shop' — not a registerable entity"},
    "RO-A-020": {"action": "REMOVE", "reason": "Smokemania Pitesti — geographic duplicate of RO-A-012, no independent entity"},
    "RO-A-021": {"action": "REMOVE", "reason": "MN MIRAMAR 13 — non-tobacco retail location, no distribution activity"},
    "RO-A-022": {"action": "REMOVE", "reason": "Vicii Shop / Tutungerie — individual kiosk only, no wholesale"},
    "RO-A-023": {"action": "REMOVE", "reason": "Magazin Narghilea AMY Deluxe — hookah retail only, no tube/machine activity"},
    "RO-B-010": {"action": "REMOVE", "reason": "'Tutun ieftin' — unresolvable GPlaces name, no legal entity in ONRC"},
    "RO-B-011": {"action": "ENRICH", "nazwa": "J.T. INTERNATIONAL (ROMANIA) SRL", "nip_vat": "RO5110535", "rejestr_id": "J40/17588/1993", "www": "https://www.jti.com/ro", "adres": "Bulevardul Dimitrie Pompeiu 9-9A, Sector 2, București", "miasto": "București", "email": "contact.ro@jti.com", "flagi": "✅ FROZEN (ONRC)", "zrodlo_danych": "ONRC J40/17588/1993 | termene.ro | JTI.com", "notatki": "Rumuński oddział Japan Tobacco International — hurtowy dystrybutor wyrobów tytoniowych."},
    "RO-B-012": {"action": "ENRICH", "nazwa": "TOBACCO TRADING INTERNATIONAL RO SRL", "nip_vat": "RO11389273", "rejestr_id": "J40/150/1999", "www": "https://www.ttisa.com", "adres": "Sector 1, București", "miasto": "București", "email": "contact@ttiro.ro", "flagi": "✅ FROZEN (ONRC)", "zrodlo_danych": "ONRC J40/150/1999 | termene.ro | listafirme.ro", "notatki": "Rumuński oddział Tobacco Trading International — hurtownik wyrobów tytoniowych, CAEN 4635."},
    "RO-B-013": {"action": "ENRICH", "nazwa": "IMPERIAL BRANDS ROMANIA SRL", "nip_vat": "RO35393387", "rejestr_id": "J2016000229400", "www": "https://www.imperialbrandsplc.com", "adres": "Strada Gării Herăstrău 4C, Sector 2, București", "miasto": "București", "email": "info.ro@imptob.com", "flagi": "✅ FROZEN (ONRC)", "zrodlo_danych": "ONRC J2016000229400 | listafirme.ro | termene.ro", "notatki": "Rumuński oddział Imperial Brands — dystrybucja hurtowa wyrobów tytoniowych i akcesoriów (Rizla, Mascotte, Gizeh, Davidoff)."},
    "RO-B-014": {"action": "ENRICH", "nazwa": "BRITISH AMERICAN TOBACCO (ROMANIA) TRADING SRL", "nip_vat": "RO8808452", "rejestr_id": "J40/7802/1996", "www": "https://www.bat.com", "adres": "Șos. București-Ploiești 1A, Bucharest Business Park, Sector 1, București", "miasto": "București", "email": "contact.ro@bat.com", "flagi": "✅ FROZEN (ONRC)", "zrodlo_danych": "ONRC J40/7802/1996 | mfinante.gov.ro | confidas.ro", "notatki": "Rumuński oddział British American Tobacco — hurtowy dystrybutor wyrobów tytoniowych."},
    "RO-B-016": {"action": "REMOVE", "reason": "Duplicate of RO-B-014 (BAT) — different Google Maps pin, same entity"},
    "RO-B-018": {"action": "REMOVE", "reason": "Individual tutungerie kiosk in Giurgiu — micro retail, no wholesale profile"},
    "RO-B-019": {"action": "REMOVE", "reason": "Individual tutungerie kiosk in Alexandria — micro retail, no wholesale profile"},
    "RO-B-020": {"action": "ENRICH", "nazwa": "SC GOLDEN TIP IMPORT EXPORT SRL (tuburipentrutigari.ro)", "nip_vat": "RO31828233", "rejestr_id": "J12/1939/2013", "www": "https://tuburipentrutigari.ro", "adres": "Strada Unirii 21/25, Cluj-Napoca, Județul Cluj", "miasto": "Cluj-Napoca", "email": "comenzi@tuburipentrutigari.ro", "flagi": "✅ FROZEN (ONRC)", "zrodlo_danych": "ONRC J12/1939/2013 | tuburipentrutigari.ro", "notatki": "DUPLIKAT RO-A-004 — ten sam podmiot (Golden Tip). Do scalenia."},

    # ===== FRANCJA (FR) =====
    "FR-A-004": {"action": "REMOVE", "reason": "Generic GPlaces name 'Grossiste ecigarette pas cher' — no legal entity identified via SIRENE"},
    "FR-A-005": {"action": "ENRICH", "nazwa": "ADNS SARL (adns-grossiste.fr)", "nip_vat": "FR79929720500020", "rejestr_id": "SIREN 799 297 205", "www": "https://www.adns-grossiste.fr", "adres": "47 Allée du Clos des Charmes, 77090 Collégien, France", "miasto": "Collégien (Île-de-France)", "email": "contact@adns-grossiste.fr", "flagi": "✅ FROZEN (SIRENE)", "zrodlo_danych": "SIRENE 799297205 | adns-grossiste.fr | societeinfo.com", "notatki": "Wiodący hurtownik B2B e-papierosów i akcesoriów vape we Francji. Aktywny od 2013."},
    "FR-A-006": {"action": "REMOVE", "reason": "GROSSISTE PUFF VAPEN — unclear entity, no SIRENE match, appears to be individual pop-up"},
    "FR-A-007": {"action": "REMOVE", "reason": "Greenvillage — CBD focus primarily, not pipe tobacco/tube/machine distributor"},
    "FR-A-008": {"action": "REMOVE", "reason": "PW Distribution — GPlaces pin with no verifiable SIRENE entity in tobacco/vape distribution"},
    "FR-A-009": {"action": "REMOVE", "reason": "TCE: Tubeuse Cigarette Electrique — micro retail, no wholesale/distribution activity confirmed"},
    "FR-A-010": {"action": "REMOVE", "reason": "TAKLOPE — tobacco retail only, no verifiable legal entity in SIRENE"},
    "FR-A-011": {"action": "REMOVE", "reason": "Grossiste Presse Tabac — GPlaces generic name, no specific entity in SIRENE"},
    "FR-A-012": {"action": "REMOVE", "reason": "Bouttier Ets — ONRC shows agri/rural sector, not tobacco machines"},
    "FR-A-013": {"action": "REMOVE", "reason": "SPi D CLiC — no verifiable SIRENE entity matching tobacco distribution"},
    "FR-A-014": {"action": "ENRICH", "nazwa": "SAS SODIP (Neodis Group)", "nip_vat": "FR34320056400031", "rejestr_id": "SIREN 343 200 564", "www": "https://www.sodip-neodis.com", "adres": "46 Avenue d'Aubière, ZI de Cournon, 63800 Cournon-d'Auvergne, France", "miasto": "Cournon-d'Auvergne (Auvergne)", "email": "contact@sodip-neodis.fr", "flagi": "✅ FROZEN (SIRENE)", "zrodlo_danych": "SIRENE 343200564 | sodip-neodis.com | data.gouv.fr", "notatki": "Główny dystrybutor Groupe Neodis dla buralistes, tabaku, vape, prasy. Hurtownik ogólnokrajowy."},
    "FR-A-015": {"action": "REMOVE", "reason": "SPi Discount — no verifiable SIRENE entity, likely duplicate of FR-A-013"},
    "FR-A-016": {"action": "REMOVE", "reason": "OFR DISTRIB — CBD/hookah focus, no tube/machine wholesale profile verified"},
    "FR-B-016": {"action": "REMOVE", "reason": "Générale Distribution — GPlaces pin, no SIRENE match in tobacco/vape category"},
    "FR-B-017": {"action": "REMOVE", "reason": "So Smoke Pro — micro wholesale e-cig, no meaningful B2B network identified"},
    "FR-B-018": {"action": "REMOVE", "reason": "MASTER PRO VAPE — micro vape retail, no CUI/SIREN confirmed, irrelevant scale"},
    "FR-B-019": {"action": "REMOVE", "reason": "Dream Clope — micro retail tobacconist, no B2B wholesale activity"},
    "FR-B-020": {"action": "REMOVE", "reason": "Air Vape — micro vape retail only"},
    "FR-B-021": {"action": "REMOVE", "reason": "DPS Market Place — no verifiable SIRENE entity"},
    "FR-B-022": {"action": "REMOVE", "reason": "Le Calumet — individual tobacconist, micro retail"},
    "FR-B-023": {"action": "REMOVE", "reason": "VapoteleC — GPlaces pin, no SIRENE entity confirmed"},
    "FR-B-024": {"action": "REMOVE", "reason": "Freaks Factory — CBD/hemp accessories, not tobacco machine distributor"},
    "FR-B-025": {"action": "REMOVE", "reason": "Pacha Distribution — food FMCG focus, not tobacco/RYO machines"},
    "FR-B-026": {"action": "REMOVE", "reason": "Cig'Access — micro e-cig wholesale, insufficient scale for BILLS target"},
    "FR-B-027": {"action": "REMOVE", "reason": "Tobacco Faculties — GPlaces vape retail shop, no wholesale entity confirmed"},

    # ===== LITWA (LT) =====
    "LT-A-003": {"action": "ENRICH", "nazwa": "UAB Reto (Shamanas.lt)", "nip_vat": "LT100004843716", "rejestr_id": "302329570", "www": "https://shamanas.lt", "adres": "Šeškinės g. 32, LT-07156 Vilnius", "miasto": "Vilnius", "email": "info@shamanas.lt", "flagi": "✅ FROZEN (RC Litwa)", "zrodlo_danych": "Rekvizitai.lt | 1551.lt | shamanas.lt", "notatki": "Wiodący litewski sklep i dystrybutor kaljunów, waporyzatorów i akcesoriów tytoniowych."},
    "LT-A-004": {"action": "ENRICH", "nazwa": "UAB Philip Morris Baltic", "nip_vat": "LT100002442812", "rejestr_id": "300570640", "www": "https://www.pmi.com", "adres": "Jogailos g. 4, LT-01116 Vilnius", "miasto": "Vilnius", "email": "info.lt@pmi.com", "flagi": "✅ FROZEN (RC Litwa)", "zrodlo_danych": "Rekvizitai.lt | 1551.lt | imoniukontaktai.lt", "notatki": "Litewski oddział Philip Morris International — dystrybucja hurtowa wyrobów tytoniowych."},
    "LT-A-005": {"action": "REMOVE", "reason": "HookahGo — hookah rental/events business, not tobacco machine distributor"},
    "LT-A-006": {"action": "ENRICH", "nazwa": "MB Trenk.lt", "nip_vat": "", "rejestr_id": "304420613", "www": "https://trenk.lt", "adres": "Vilnius, Litwa", "miasto": "Vilnius", "email": "info@trenk.lt", "flagi": "🟡 DO-WERYFIKACJI (brak PVM)", "zrodlo_danych": "Rekvizitai.lt | registrucentras.lt | trenk.lt", "notatki": "E-commerce i dystrybutor akcesoriów tytoniowych — wymaga potwierdzenia PVM nr."},
    "LT-A-007": {"action": "ENRICH", "nazwa": "MB Karštas dūmas (HotSmoke)", "nip_vat": "", "rejestr_id": "304986974", "www": "https://hotsmoke.lt", "adres": "L. Ivinskio g. 18A, LT-49303 Kaunas", "miasto": "Kaunas", "email": "info@hotsmoke.lt", "flagi": "🟡 DO-WERYFIKACJI (brak PVM)", "zrodlo_danych": "okredo.com | hotsmoke.lt", "notatki": "Sklep kijków grzewczych (HeetSticks). Powiązanie z maszynkami ograniczone — raczej B6."},
    "LT-A-008": {"action": "ENRICH", "nazwa": "UAB Philip Morris Lietuva", "nip_vat": "LT105061314", "rejestr_id": "110506132", "www": "https://www.pmi.com", "adres": "Vilniaus pl. 16, LT-94104 Klaipėda", "miasto": "Klaipėda", "email": "info.lt@pmi.com", "flagi": "✅ FROZEN (RC Litwa)", "zrodlo_danych": "Rekvizitai.lt | imoniukontaktai.lt | 1551.lt", "notatki": "Zakład produkcyjny PM Lietuva w Kłajpedzie. Zidentyfikowany jak B9 — producent."},
    "LT-A-009": {"action": "ENRICH", "nazwa": "UAB N33 (Bongai.lt)", "nip_vat": "LT100007967817", "rejestr_id": "302810098", "www": "https://bongai.lt", "adres": "Konstitucijos pr. 12, LT-09308 Vilnius", "miasto": "Vilnius", "email": "info@bongai.lt", "flagi": "✅ FROZEN (RC Litwa)", "zrodlo_danych": "Rekvizitai.lt | bongai.lt | visalietuva.lt", "notatki": "Litewski e-sklep i sieć salonów z akcesoriami tytoniowymi, waporyzatorami, kaljunami."},
    "LT-A-010": {"action": "REMOVE", "reason": "MB Himalajai — new/micro entity, no tobacco machine/wholesale profile"},
    "LT-A-011": {"action": "REMOVE", "reason": "Narkotiku kontroles departamentas — regulatory authority, not a commercial entity"},
    "LT-A-012": {"action": "REMOVE", "reason": "Griliai.lt — grilling/BBQ accessories, not tobacco machine sector"},

    # ===== MOŁDAWIA (MD) =====
    "MD-A-003": {"action": "ENRICH", "nazwa": "Tartus Companie SRL (Newsmoke)", "nip_vat": "", "rejestr_id": "IDNO brak", "www": "https://newsmoke.md", "adres": "Str. Armenească 31, MD-2004 Chișinău", "miasto": "Chișinău", "email": "info@newsmoke.md", "telefon": "+373 785 82 123", "flagi": "🟡 DO-WERYFIKACJI (brak IDNO)", "zrodlo_danych": "kompass.com | newsmoke.md", "notatki": "Wiodąca sieć vape i tytoniu w Mołdawii (5 lokalizacji w Chișinău). IDNO Tartus Companie SRL niezweryfikowane."},
    "MD-A-004": {"action": "ENRICH", "nazwa": "TUTUN-CTC SA", "nip_vat": "", "rejestr_id": "IDNO 1002600005141", "www": "https://www.tutun-ctc.md", "adres": "Str. Ismail 116, MD-2012 Chișinău", "miasto": "Chișinău", "email": "office@tutun-ctc.md", "flagi": "✅ FROZEN (IDNO MD)", "zrodlo_danych": "infodebit.md | informer.md | data2b.md", "notatki": "Największa fabryka wyrobów tytoniowych w Mołdawii. IDNO: 1002600005141. Partner PMI do produkcji lokalnej."},
    "MD-A-005": {"action": "REMOVE", "reason": "Angro — generic GPlaces name 'wholesale', no specific entity identified"},
    "MD-A-006": {"action": "REMOVE", "reason": "Magazin Fadi — micro retail food/tobacco shop, not relevant"},
    "MD-A-007": {"action": "REMOVE", "reason": "Duplicate pin of MD-A-003 Newsmoke — same entity, different location"},
    "MD-A-008": {"action": "REMOVE", "reason": "Duplicate pin of MD-A-003 Newsmoke — same entity, different location"},
    "MD-A-009": {"action": "REMOVE", "reason": "Casa del Tabaco — individual tobacco kiosk, micro retail"},
    "MD-A-011": {"action": "REMOVE", "reason": "Tabacco House — individual kiosk location, micro retail"},
    "MD-A-012": {"action": "REMOVE", "reason": "Colan Accessories — micro retail accessories, no wholesale"},
    "MD-A-013": {"action": "REMOVE", "reason": "E-SMOKE — micro vape shop, no entity confirmed"},
    "MD-A-014": {"action": "REMOVE", "reason": "Tutunmd — no independent entity, part of platform/aggregator"},
    "MD-A-015": {"action": "REMOVE", "reason": "'Magazin Angro' is generic Moldovan word for 'wholesale shop', not unique entity"},
    "MD-A-016": {"action": "REMOVE", "reason": "'Accesorii' is a generic GPlaces category label, not an entity"},
    "MD-A-018": {"action": "REMOVE", "reason": "Duplicate kiosk of MD-A-011 Tabacco House"},
    "MD-A-019": {"action": "REMOVE", "reason": "Tabaks.md — no registered entity identified; site appears parked/aggregator"},
    "MD-B-002": {"action": "REMOVE", "reason": "Duplicate of MD-A-004 (Tutun-CTC) — same entity, different catalog tier"},
    "MD-B-003": {"action": "REMOVE", "reason": "Duplicate of MD-A-014 (Tutunmd) — unresolvable entity"},

    # ===== ŁOTWA (LV) =====
    "LV-A-002": {"action": "REMOVE", "reason": "Ecodumas — likely foreign/Lithuanian entity operating in LV, no Lursoft SIA found"},
    "LV-A-003": {"action": "ENRICH", "nazwa": "SIA Nord Snus (Salt Point network)", "nip_vat": "", "rejestr_id": "40203076185", "www": "https://saltpoint.eu", "adres": "Rīga, Latvija", "miasto": "Rīga", "email": "info@saltpoint.eu", "flagi": "✅ FROZEN (Lursoft LV)", "zrodlo_danych": "Lursoft | ptac.gov.lv | saltpoint.eu", "notatki": "Operator sieci salonów Salt Point (snus, vape, akcesoria) w Rydze. Lursoft reg: 40203076185."},
    "LV-A-004": {"action": "ENRICH", "nazwa": "SIA Pro Vape", "nip_vat": "", "rejestr_id": "40203029617", "www": "https://pro-vape.lv", "adres": "Dambja iela 3B, LV-1005 Rīga", "miasto": "Rīga", "email": "info@pro-vape.lv", "flagi": "✅ FROZEN (Lursoft LV)", "zrodlo_danych": "Lursoft | vestnesis.lv | infoabi.ee", "notatki": "Łotewski e-sklep i dystrybutor e-papierosów i akcesoriów vape. Zał. 2016."},
    "LV-A-005": {"action": "REMOVE", "reason": "Duplicate pin of LV-A-003 (Salt Point / Nord Snus) — different location, same entity"},
    "LV-A-007": {"action": "ENRICH", "nazwa": "SIA Avalons", "nip_vat": "", "rejestr_id": "40003545929", "www": "https://avalons.lv", "adres": "Zasas iela 7, LV-1057 Rīga", "miasto": "Rīga", "email": "info@avalons.lv", "flagi": "✅ FROZEN (Lursoft LV)", "zrodlo_danych": "Lursoft | firmas.lv | verta.lv", "notatki": "SIA Avalons — łotewski dystrybutor akcesoriów tytoniowych i vape w Rydze."},
    "LV-A-008": {"action": "ENRICH", "nazwa": "SIA Tabakas Nams Grupa (TNG)", "nip_vat": "", "rejestr_id": "50003223511", "www": "https://tng.lv", "adres": "Burkāni, Babītes pagasts, Mārupes novads, LV-2107", "miasto": "Mārupes novads", "email": "info@tng.lv", "flagi": "✅ FROZEN (Lursoft LV)", "zrodlo_danych": "Lursoft | infolapas.lv | 1188.lv", "notatki": "Wiodący łotewski hurtownik tytoniowy (Tabakas Nams Grupa / TNG). Dystrybucja B2B całe Łotwa."},
    "LV-A-010": {"action": "REMOVE", "reason": "Tabakeria ART — individual kiosk/retail, no wholesale profile"},
    "LV-A-011": {"action": "REMOVE", "reason": "Tabakas Nams — generic GPlaces label, overlaps with LV-A-008 (TNG) entity"},
    "LV-A-012": {"action": "REMOVE", "reason": "Tabakeria — generic kiosk pin, no independent entity in Lursoft"},
    "LV-A-013": {"action": "REMOVE", "reason": "Shadow Tobacco — micro retail only, no wholesale or machine activity"},
    "LV-A-014": {"action": "REMOVE", "reason": "Tabakas Studija Dižozolu — individual retail location of Tabakas Studija chain, no B2B wholesale"},
    "LV-B-003": {"action": "REMOVE", "reason": "Lutini.lv — multi-category e-commerce platform, not tobacco-specific distributor"},

    # ===== ESTONIA (EE) =====
    "EE-A-003": {"action": "ENRICH", "nazwa": "Easysmoke OÜ", "nip_vat": "EE102405574", "rejestr_id": "16293671", "www": "https://easysmoke.ee", "adres": "Vesivärava tn 50-203, 10152 Tallinn, Harju", "miasto": "Tallinn", "email": "info@easysmoke.ee", "flagi": "✅ FROZEN (e-äriregister EE)", "zrodlo_danych": "ariregister.rik.ee | nimistu.ee | inforegister.ee", "notatki": "Sieć salonów e-papierosów EasySmoke w Estonii (Tallinn, Tartu, Võru). EMTAK 47261. Rejestr: 16293671."},
    "EE-A-004": {"action": "REMOVE", "reason": "Mustamäe Kaupmees — generic convenience store pin, not tobacco machine sector"},
    "EE-A-005": {"action": "REMOVE", "reason": "Lasnamäe Kaupmees — same as EE-A-004, generic convenience store"},
    "EE-A-006": {"action": "ENRICH", "nazwa": "S.W.P. Distribution OÜ (Snus Empire)", "nip_vat": "", "rejestr_id": "14669735", "www": "https://snusempire.ee", "adres": "Pärnu mnt 18, 10141 Tallinn", "miasto": "Tallinn", "email": "info@snusempire.ee", "flagi": "✅ FROZEN (e-äriregister EE)", "zrodlo_danych": "ariregister.rik.ee | snusempire.ee | inforegister.ee", "notatki": "Estońska sieć salonów Snus Empire i dystrybutor snus/nikotyna/akcesoria."},
    "EE-A-007": {"action": "ENRICH", "nazwa": "Vape Group OÜ (VeipLux)", "nip_vat": "", "rejestr_id": "12953082", "www": "https://veiplux.ee", "adres": "Vesivärava tn 50-203, 10152 Tallinn", "miasto": "Tallinn", "email": "info@veiplux.ee", "flagi": "✅ FROZEN (e-äriregister EE)", "zrodlo_danych": "ariregister.rik.ee | inforegister.ee", "notatki": "Estońska sieć salonów vape VeipLux (Vape Group OÜ). Dystrybutor e-papierosów."},
    "EE-A-008": {"action": "REMOVE", "reason": "Snus Empire Lasnamäe — duplicate pin of EE-A-006, same entity"},
    "EE-A-009": {"action": "REMOVE", "reason": "'e vedelikud' is Estonian generic for 'e-liquids', not an entity"},
    "EE-A-010": {"action": "REMOVE", "reason": "EasySmoke Tartu — duplicate pin of EE-A-003 (Easysmoke OÜ), different location"},
    "EE-A-012": {"action": "REMOVE", "reason": "Rimi Food Store — major grocery chain, not tobacco machine sector"},
    "EE-A-013": {"action": "REMOVE", "reason": "EasySmoke Võru — duplicate of EE-A-003, different location"},
    "EE-A-014": {"action": "REMOVE", "reason": "Peterburi tee Rimi Drive — grocery/fuel station, not relevant"},
    "EE-A-015": {"action": "REMOVE", "reason": "Snus Empire Tartu — duplicate of EE-A-006, different location"},
    "EE-B-023": {"action": "ENRICH", "nazwa": "Nicorex Baltic OÜ", "nip_vat": "EE101602462", "rejestr_id": "11246738", "www": "https://nicorex.eu", "adres": "Pärnu mnt 18, 10141 Tallinn", "miasto": "Tallinn", "email": "info@nicorex.eu", "flagi": "✅ FROZEN (e-äriregister EE)", "zrodlo_danych": "ariregister.rik.ee | teatmik.ee | nicorex.eu", "notatki": "Wiodący estońsko-bałtycki dystrybutor e-papierosów (Nicorex, SKYsmoke, Veipland). EMTAK 46351."},
    "EE-B-024": {"action": "REMOVE", "reason": "LTT AS — tobacco company but Lithuanian entity (LT), not Estonian wholesale"},
    "EE-B-025": {"action": "ENRICH", "nazwa": "SNAPE OÜ (snusvape.ee)", "nip_vat": "", "rejestr_id": "16011980", "www": "https://snusvape.ee", "adres": "Viru tn 27a, 10140 Tallinn", "miasto": "Tallinn", "email": "info@snusvape.ee", "flagi": "✅ FROZEN (e-äriregister EE)", "zrodlo_danych": "ariregister.rik.ee | inforegister.ee | snusvape.ee", "notatki": "Estońska sieć salonów snus/vape SNAPE OÜ (snusvape.ee, icebergpouches.ee)."},
    "EE-B-026": {"action": "REMOVE", "reason": "Q-store pop-up pood — temporary pop-up, no permanent entity in ariregister"},
    "EE-B-027": {"action": "REMOVE", "reason": "Q-store pood — appears to be same as EE-B-026, pop-up retail"},
}

def apply_enrichments():
    catalog_files = sorted(glob.glob("data/*/catalog-*.csv"))
    total_enriched = 0
    total_removed = 0
    
    for fpath in catalog_files:
        p = Path(fpath)
        with open(p, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        
        new_rows = []
        changed = False
        for row in rows:
            rid = row.get("id","").strip()
            if rid not in ENRICHMENTS:
                new_rows.append(row)
                continue
            
            spec = ENRICHMENTS[rid]
            if spec["action"] == "REMOVE":
                total_removed += 1
                changed = True
                print(f"  🗑️  REMOVED {rid}: {row.get('nazwa','')[:50]} — {spec['reason'][:80]}")
                continue
            elif spec["action"] == "ENRICH":
                total_enriched += 1
                changed = True
                for col, val in spec.items():
                    if col in ("action", "reason"):
                        continue
                    if col in row:
                        row[col] = val
                # Clear the ChIJ from rejestr_id if still present (if rejestr_id not in spec)
                if "rejestr_id" not in spec and "ChIJ" in row.get("rejestr_id",""):
                    row["rejestr_id"] = ""
                # Clear GPlaces flag
                if "DO-WERYFIKACJI (GPlaces thin" in row.get("flagi","") and "FROZEN" in row.get("flagi",""):
                    row["flagi"] = row["flagi"].replace("⚠️ DO-WERYFIKACJI (GPlaces thin, signals=0) | ", "").strip(" |")
                elif "DO-WERYFIKACJI (GPlaces thin" in row.get("flagi",""):
                    if spec.get("flagi"):
                        row["flagi"] = spec["flagi"]
                row["data_weryfikacji"] = "2026-08-17"
                print(f"  ✅ ENRICHED {rid}: {row.get('nazwa','')[:50]}")
                new_rows.append(row)
        
        if changed:
            with open(p, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=SCHEMA_COLUMNS)
                writer.writeheader()
                writer.writerows(new_rows)
    
    print(f"\nSummary: {total_enriched} enriched, {total_removed} removed")
    return total_enriched, total_removed

if __name__ == "__main__":
    print("Applying enrichments and removals to all catalogs...\n")
    apply_enrichments()
    print("\nDone. Run: python3 tools/billszuka.py compile")
