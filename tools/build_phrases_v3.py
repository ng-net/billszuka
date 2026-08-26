#!/usr/bin/env python3
"""
Build /tmp/phrases_v3.json — phrases from SŁOWNIK-{ISO}.md with proper token-based
PL translations. v2 had 76-83% of phrases untranslated (just copy of original).
v3 uses a token-level translator for 11 languages.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # project root (BILLSzuka-24-Aug)

# === Brand names (do not translate) ===
BRANDS = {
    "powermatic", "powerMatic", "PowerMatic", "POWERMATIC",
    "hawk", "Hawk", "HAWK", "hawk rolling machine", "rolling machine",
    "topomat", "Topomat", "TOPOMAT",
    "turbomatic", "Turbomatic", "TURBOMATIC",
    "luxfux", "Luxfux", "LUXFUX",
    "ocb", "OCB", "Smoking", "smoking", "smok",
    "SMOKS", "Intenze", "INTENZE",
    "Cartel", "cartel", "Don Pealo", "Dark Horse", "FERN", "Atomic",
    "GGT", "PEAL", "GGTabak", "GG Tabák", "Roland",
    "TikTok", "tiktok", "Allegro", "allegro", "Ceneo", "ceneo",
    "Heureka", "heureka", "Zboží", "Zbozi",
    "BILLA", "Billa", "Sanitex",
    "CBD",
    "Shisha", "shisha",
    "Vape", "vape", "Vaping", "vaping",
    "e-cigarety", "e-cigarete", "e-cigaret", "e-cigariet", "e-cigary",
    "e-papierosy", "e-papierosa",
}

# === Brand PL descriptors (for proper rendering in italic) ===
BRAND_PL = {
    "powermatic": "marka maszynki",
    "powerMatic": "marka maszynki",
    "PowerMatic": "marka maszynki",
    "hawk": "marka maszynki",
    "Hawk": "marka maszynki",
    "hawk rolling machine": "marka maszynki (dosł. \"hawk\" = jastrząb)",
    "rolling machine": "maszynka do skręcania",
    "topomat": "marka maszynki",
    "Topomat": "marka maszynki",
    "turbomatic": "marka maszynki",
    "Turbomatic": "marka maszynki",
    "luxfux": "marka maszynki",
    "Luxfux": "marka maszynki",
}

# === Country ISO → (label, native name) ===
COUNTRY = {
    "PL": ("[PL] Polska", "Polska"),
    "CZ": ("[CZ] Czechy", "Česko"),
    "SK": ("[SK] Słowacja", "Slovensko"),
    "RO": ("[RO] Rumunia", "România"),
    "BG": ("[BG] Bułgaria", "България"),
    "HR": ("[HR] Chorwacja", "Hrvatska"),
    "SI": ("[SI] Słowenia", "Slovenija"),
    "LT": ("[LT] Litwa", "Lietuva"),
    "LV": ("[LV] Łotwa", "Latvija"),
    "EE": ("[EE] Estonia", "Eesti"),
    "FR": ("[FR] Francja", "France"),
    "MD": ("[MD] Mołdawia", "Moldova"),
}

# === Token translator: ISO → {foreign_token: pl_token} ===
# Lowercase key. Match is case-insensitive.
DICT = {
    "CZ": {
        # === Devices / actions ===
        "plnička": "nabijarka", "plničky": "nabijarki", "plničce": "nabijarce",
        "plničku": "nabijarkę", "plnění": "nabijania", "plnit": "nabijać",
        "plnící": "napełniająca", "plnohodnotná": "pełnowartościowa",
        "cigaret": "papierosów", "cigarety": "papierosy", "cigaretami": "papierosami",
        "cigaretových": "papierosowych", "cigaretové": "papierosowe",
        "ruční": "ręczna", "ručně": "ręcznie", "ručnička": "ręczna nabijarka",
        "automatická": "automatyczna", "automatické": "automatyczne", "automat": "automat",
        "elektrická": "elektryczna", "elektrické": "elektryczne",
        "strojek": "maszynka", "stroj": "maszyna", "strojky": "maszynki",
        "strojky": "maszynki", "strojek": "maszynka",
        "kuřácký": "dla palaczy", "kuřácké": "dla palaczy", "kuřáckých": "dla palaczy",
        "kuřáckým": "dla palaczy", "kuřáckými": "dla palaczy",
        "potřeby": "potrzeby", "potřeb": "potrzeb", "potřebami": "potrzebami",
        "potřeby": "akcesoria",
        "tabáku": "tytoniu", "tabák": "tytoń", "tabákové": "tytoniowe",
        "tabákových": "tytoniowych", "tabáková": "tytoniowa", "tabákový": "tytoniowy",
        "tabákovými": "tytoniowymi", "tabáku": "tytoniu",
        "doutník": "cygaro", "doutníky": "cygara", "doutníků": "cygar",
        "cigareta": "papieros", "cigaret": "papierosów",
        "balící": "pakująca", "balicí": "pakujący",
        "jak": "jak", "plnit": "nabijać", "naplnit": "napełnić",
        # === Wholesale / retail ===
        "velkoobchod": "hurtownia", "velkoobchodní": "hurtowy", "velkoobchodně": "hurtowo",
        "velkoobchodu": "hurtowni", "velkoobchodem": "hurtownią",
        "distributor": "dystrybutor", "distributora": "dystrybutora",
        "distribuce": "dystrybucja", "distribuční": "dystrybucyjny",
        "prodejna": "sklep", "prodejny": "sklepu", "prodejně": "sklepie",
        "prodejen": "sklepów", "prodejnami": "sklepami",
        "prodej": "sprzedaż", "prodeje": "sprzedaże",
        "obchod": "sklep", "obchodě": "sklepie", "obchodu": "sklepu",
        "obchody": "sklepy", "obchodů": "sklepów",
        "obchodní": "handlowy", "obchodní": "handlowy",
        "e-shop": "e-sklep", "eshop": "e-sklep", "e-shopu": "e-sklepie",
        "kuřák": "palacz", "kuřáka": "palacza", "kuřáky": "palacze",
        "výrobků": "produktów", "výrobky": "produkty", "výrobkem": "produktem",
        "zákazník": "klient", "zákazníka": "klienta",
        # === Common ===
        "skupina": "grupa", "skupiny": "grupy", "skupin": "grup",
        "skupinou": "grupą", "skupinu": "grupę",
        "česko": "Czechy", "čechy": "Czechy", "čech": "Czech",
        "praha": "Praga", "brno": "Brno", "ostrava": "Ostrawa",
        "diskuse": "dyskusja", "diskusi": "dyskusji", "diskuzí": "dyskusji",
        "hledat": "szukać", "najít": "znaleźć", "najdete": "znajdziecie",
        "koupit": "kupić", "kupte": "kup", "koupíte": "kupicie",
        "cena": "cena", "ceny": "ceny", "cenou": "ceną", "ceně": "cenie",
        "akce": "promocja", "akcí": "promocji",
        "nový": "nowy", "nové": "nowe", "nejlepší": "najlepszy",
        "velký": "duży", "velké": "duże", "malý": "mały",
        "online": "online",
        "kuřáckých": "dla palaczy",
        "balení": "opakowanie", "balení": "opakowanie",
        "město": "miasto", "města": "miasta", "městě": "mieście",
        "městský": "miejski", "městské": "miejskie",
    },
    "SK": {
        # === Devices / actions ===
        "plnička": "nabijarka", "plničky": "nabijarki", "plničke": "nabijarce",
        "plnenie": "nabijanie", "plniť": "nabijać", "plniacich": "napełniających",
        "cigariet": "papierosów", "cigarety": "papierosy", "cigaret": "papierosów",
        "ručná": "ręczna", "ručne": "ręcznie", "ručný": "ręczny",
        "automatická": "automatyczna", "automatické": "automatyczne",
        "elektrická": "elektryczna", "elektrické": "elektryczne",
        "strojček": "maszynka", "stroj": "maszyna",
        "fajčiarske": "dla palaczy", "fajčiarskych": "dla palaczy",
        "fajčiarsky": "dla palaczy", "fajčiar": "palacz",
        "potreby": "potrzeby", "potrieb": "potrzeb", "potrebami": "potrzebami",
        "potrebné": "potrzebne", "potrieb": "potrzeb",
        "tabaku": "tytoniu", "tabak": "tytoń", "tabakové": "tytoniowe",
        "tabakových": "tytoniowych", "tabaková": "tytoniowa",
        "tabakový": "tytoniowy", "tabakom": "tytoniem",
        "cigareta": "papieros", "cigarete": "papierosy", "cigaret": "papierosów",
        "doutník": "cygaro", "doutníky": "cygara",
        "strojov": "maszyn", "strojček": "maszynka",
        "elektrické": "elektryczne", "elektronické": "elektroniczne",
        "elektronická": "elektroniczna",
        "ako": "jak", "ako": "jak",
        "naplniť": "napełnić", "naplňte": "napełnij",
        # === Wholesale / retail ===
        "veľkoobchod": "hurtownia", "veľkoobchodný": "hurtowy",
        "veľkoobchode": "hurtowni", "veľkoobchodu": "hurtowni",
        "veľkoobchodne": "hurtowo",
        "distribútor": "dystrybutor", "distribútora": "dystrybutora",
        "distribúcia": "dystrybucja", "distribučný": "dystrybucyjny",
        "predajňa": "sklep", "predajne": "sklepu", "predajni": "sklepie",
        "predaj": "sprzedaż", "predaje": "sprzedaży",
        "obchod": "sklep", "obchode": "sklepie", "obchodu": "sklepu",
        "obchody": "sklepy",
        "e-shop": "e-sklep", "eshop": "e-sklep",
        "výrobkov": "produktów", "výrobky": "produkty",
        "fajčenie": "palenie", "fajčí": "pali",
        "predajca": "sprzedawca", "predajcovia": "sprzedawcy",
        # === Common ===
        "skupina": "grupa", "skupiny": "grupy", "skupín": "grup",
        "slovensko": "Słowacja", "slovenská": "słowacka", "slovenský": "słowacki",
        "bratislava": "Bratysława", "košice": "Koszyce",
        "online": "online",
        "cena": "cena", "ceny": "ceny", "cenou": "ceną",
        "akcia": "promocja", "akcií": "promocji",
        "nový": "nowy", "nové": "nowe",
        "najlepší": "najlepszy", "najlepšie": "najlepsze",
        "veľký": "duży", "veľké": "duże", "malý": "mały",
        "mesto": "miasto", "mesta": "miasta", "mestský": "miejski",
        "fajka": "fajka", "fajky": "fajki", "vodná fajka": "fajka wodna",
        "vodný": "wodna", "vodné": "wodne",
    },
    "RO": {
        # === Devices / actions ===
        "mașină": "maszyna", "mașini": "maszyny", "mașinile": "maszyny",
        "mașinile": "maszyny", "mașinii": "maszyny",
        "umplut": "napełniać", "umplere": "napełnianie",
        "umplută": "napełniona", "umplute": "napełnione",
        "țigări": "papierosy", "țigara": "papieros", "țigările": "papierosy",
        "țigaretă": "papieros", "țigarete": "papierosy", "țigaretei": "papierosa",
        "dispozitiv": "urządzenie", "dispozitive": "urządzenia",
        "injector": "wstrzykiwacz", "injectorul": "wstrzykiwacz",
        "automată": "automatyczna", "automat": "automat",
        "manuală": "ręczna", "manual": "ręczny",
        "electrică": "elektryczna", "electric": "elektryczny",
        "articol": "artykuł", "articole": "artykuły",
        "pentru": "dla", "fumul": "dym", "fumător": "palacz",
        "fumători": "palacze", "fumătorilor": "palaczy",
        "tutun": "tytoń", "tutunului": "tytoniu", "tutunul": "tytoń",
        "tutun": "tytoń", "tutunului": "tytoniu",
        "cumpera": "kupić", "cumpăra": "kupić", "cumpără": "kup",
        "ambalaj": "opakowanie", "ambalaje": "opakowania",
        "ieftin": "tani", "ieftine": "tanie", "scump": "drogi",
        "nou": "nowy", "noi": "nowe", "nouă": "nowa", "noua": "nowa",
        "cel mai bun": "najlepszy", "cea mai bună": "najlepsza",
        "ieftine": "tanie", "ieftin": "tani",
        "mare": "duży", "mari": "duże", "mic": "mały", "mici": "małe",
        "cum": "jak", "umplu": "napełniam", "umpli": "napełniasz",
        "cumpăr": "kupuję", "cumperi": "kupujesz",
        "umplere": "napełnianie", "umplutul": "napełniony",
        "aparat": "aparat", "aparatul": "aparat", "aparate": "aparaty",
        # === Wholesale / retail ===
        "distribuitor": "dystrybutor", "distribuitori": "dystrybutorzy",
        "distribuitorul": "dystrybutor", "distribuitori": "dystrybutorzy",
        "angro": "hurtowo", "angrosiști": "hurtownicy",
        "magazin": "sklep", "magazine": "sklepy", "magazinul": "sklep",
        "depozit": "magazyn", "depozite": "magazyny",
        "comerț": "handel", "comerțul": "handel",
        "produs": "produkt", "produse": "produkty", "produsul": "produkt",
        "vânzare": "sprzedaż", "vânzări": "sprzedaże", "vânzări": "sprzedaże",
        "vânzător": "sprzedawca", "vânzători": "sprzedawcy",
        "fierar": "sprzedawca", "fierari": "sprzedawcy",
        "fabrică": "fabryka", "fabrici": "fabryki",
        "centru": "centrum", "centrul": "centrum",
        "e-shop": "e-sklep", "eshop": "e-sklep",
        "import": "import", "importator": "importer",
        "producător": "producent", "producători": "producenci",
        # === Common ===
        "românia": "Rumunia", "român": "Rumun", "română": "rumuńska",
        "românesc": "rumuński", "românești": "rumuńskie",
        "bucurești": "Bukareszt", "cluj": "Kluż", "iași": "Jassy",
        "timișoara": "Temeszwar", "constanța": "Konstanca",
        "grup": "grupa", "grupuri": "grupy", "grupul": "grupa",
        "online": "online",
        "ieftin": "tani", "scump": "drogi",
        "nou": "nowy", "vechi": "stary", "veche": "stara",
        "cel mai bun": "najlepszy",
        "mare": "duży", "mic": "mały",
        "ieftin": "tani",
    },
    "BG": {
        # Cyrillic → Polish
        "машина": "maszyna", "машини": "maszyny", "машината": "maszyna",
        "машини": "maszyny",
        "пълнене": "napełnianie", "пълни": "napełnia", "пълначка": "nabijarka",
        "пълначки": "nabijarki", "пълначката": "nabijarka",
        "ръчна": "ręczna", "ръчно": "ręcznie", "ръчен": "ręczny",
        "автоматична": "automatyczna", "автоматично": "automatycznie",
        "автоматичен": "automatyczny",
        "електрическа": "elektryczna", "електрически": "elektryczny",
        "електронна": "elektroniczna", "електронни": "elektroniczne",
        "електронни": "elektroniczne",
        "цигари": "papierosy", "цигара": "papieros", "цигарета": "papieros",
        "цигарени": "papierosowe",
        "тютюн": "tytoń", "тютюна": "tytoniu", "тютюнев": "tytoniowy",
        "тютюневи": "tytoniowe", "тютюнева": "tytoniowa",
        "тютюневите": "tytoniowe", "тютюневи": "tytoniowe",
        "тютюневите": "tytoniowe",
        "тютюнопушене": "palenie tytoniu",
        "устройство": "urządzenie", "устройства": "urządzenia",
        "уред": "przyrząd", "уреди": "przyrządy",
        "машинка": "maszynka", "машинки": "maszynki",
        "пушач": "palacz", "пушачи": "palacze", "пушачите": "palacze",
        "аксесоари": "akcesoria", "аксесоар": "akcesorium",
        "аксесоарите": "akcesoria", "аксесоари": "akcesoria",
        "дистрибутор": "dystrybutor", "дистрибутори": "dystrybutorzy",
        "дистрибуторът": "dystrybutor",
        "дистрибуция": "dystrybucja", "дистрибуцията": "dystrybucja",
        "търговия": "handel", "търговията": "handel",
        "търговец": "handlowiec", "търговци": "handlowcy",
        "търговски": "handlowy",
        "търговска": "handlowa",
        "едро": "hurtowo", "на едро": "hurtowy",
        "производител": "producent", "производители": "producenci",
        "производство": "produkcja",
        "продукт": "produkt", "продукти": "produkty", "продуктите": "produkty",
        "магазин": "sklep", "магазини": "sklepy", "магазинът": "sklep",
        "магазина": "sklepu",
        "продажба": "sprzedaż", "продажби": "sprzedaże", "продажбата": "sprzedaż",
        "продавач": "sprzedawca", "продавачи": "sprzedawcy",
        "вносител": "importer", "внос": "import",
        "вносител": "importer",
        "склад": "magazyn", "складова": "magazynowa",
        "онлайн": "online",
        "евтин": "tani", "евтино": "tanio", "евтина": "tania", "евтини": "tanie",
        "скъп": "drogi", "скъпо": "drogo", "скъпа": "droga", "скъпи": "drogie",
        "нов": "nowy", "ново": "nowe", "нова": "nowa",
        "стара": "stara", "старо": "stare", "стар": "stary",
        "най-добър": "najlepszy", "най-добра": "najlepsza", "най-добро": "najlepsze",
        "голям": "duży", "голямо": "duże", "голяма": "duża",
        "малък": "mały", "малко": "małe", "малка": "mała",
        "как": "jak", "как се": "jak się", "както": "jak",
        "купи": "kup", "купува": "kupuje", "купуване": "kupowanie",
        "пакетиране": "pakowanie", "опаковка": "opakowanie", "опаковки": "opakowania",
        "хора": "ludzie", "хората": "ludzie",
        "българия": "Bułgaria", "българия": "Bułgaria",
        "българин": "Bułgar", "български": "bułgarski", "българска": "bułgarska",
        "българско": "bułgarskie",
        "софия": "Sofia", "варна": "Warna", "пловдив": "Płowdiw",
        "бургас": "Burgas", "русе": "Ruse",
        "група": "grupa", "групи": "grupy", "групата": "grupa",
    },
    "HR": {
        # === Devices / actions ===
        "stroj": "maszyna", "stroj za": "maszyna do", "stroj za punjenje": "maszyna do napełniania",
        "punjenje": "napełnianie", "puniti": "napełniać", "punilica": "nabijarka",
        "punilice": "nabijarki", "punilicu": "nabijarkę",
        "ručna": "ręczna", "ručno": "ręcznie", "ručni": "ręczny",
        "automatska": "automatyczna", "automatski": "automatyczny",
        "električna": "elektryczna", "električni": "elektryczny",
        "cigareta": "papieros", "cigarete": "papierosy", "cigareta": "papieros",
        "cigarete": "papierosy",
        "cigaretama": "papierosami",
        "duhan": "tytoń", "duhana": "tytoniu", "duhanski": "tytoniowy",
        "duhanske": "tytoniowe", "duhanu": "tytoniu", "duhanom": "tytoniem",
        "duhanskim": "tytoniowym", "duhan": "tytoń",
        "pušačke": "dla palaczy", "pušačkih": "dla palaczy",
        "pušački": "dla palaczy", "pušačkim": "dla palaczy",
        "pušač": "palacz", "pušača": "palacza", "pušači": "palacze",
        "potrepštine": "potrzeby", "potrepština": "potrzeba",
        "potrebama": "potrzebami",
        "naprava": "urządzenie", "naprave": "urządzenia", "napravu": "urządzenie",
        "napravom": "urządzeniem", "napravama": "urządzeniami",
        "strojčić": "maszynka", "strojčići": "maszynki",
        "kako": "jak", "kako napuniti": "jak napełnić",
        "napuniti": "napełnić", "napunite": "napełnij",
        "kupiti": "kupić", "kupujem": "kupuję", "kupuje": "kupuje",
        "kupljenje": "zakup", "kupovina": "zakupy",
        "prodavatelj": "sprzedawca", "prodavatelji": "sprzedawcy",
        "vape shop": "sklep z waporyzatorami", "vape": "waporyzator",
        "vape shopovi": "sklepy z waporyzatorami",
        "shop": "sklep", "shopovi": "sklepy", "shops": "sklepy",
        # === Wholesale / retail ===
        "veleprodaja": "hurtownia", "veleprodajni": "hurtowy",
        "veleprodajna": "hurtowa", "veleprodajom": "hurtownią",
        "distribucija": "dystrybucja", "distributer": "dystrybutor",
        "distributera": "dystrybutora", "distributeri": "dystrybutorzy",
        "proizvoda": "produktów", "proizvodi": "produkty", "proizvod": "produkt",
        "proizvođač": "producent", "proizvođači": "producenci",
        "prodajno": "sprzedażowe", "prodajni": "sprzedażowy",
        "prodavati": "sprzedawać", "prodaje": "sprzedaje", "prodajem": "sprzedaję",
        "prodavaonica": "sklep", "prodavaonice": "sklepy",
        "prodavaonicu": "sklep", "prodavaonici": "sklepie",
        "trgovina": "sklep", "trgovine": "sklepy", "trgovinu": "sklep",
        "trgovinom": "sklepem", "trgovinama": "sklepami",
        "trgovački": "handlowy", "trgovačka": "handlowa",
        "veletrgovina": "hurtownia", "veletrgovine": "hurtownie",
        "veletrgovina": "hurtownia",
        "centar": "centrum", "centri": "centra",
        "uvoznik": "importer", "uvoz": "import",
        "uvoznici": "importerzy",
        "skladište": "magazyn", "skladišta": "magazyny",
        # === Common ===
        "grupa": "grupa", "grupe": "grupy", "grupu": "grupę",
        "grupi": "grupy", "grupom": "grupą", "grupe": "grupy",
        "hrvatska": "Chorwacja", "hrvatski": "chorwacki", "hrvatska": "Chorwacja",
        "hrvatsko": "chorwackie",
        "hrvatske": "chorwackie", "hrvatskom": "chorwackim",
        "zagreba": "Zagrzebia", "zagreb": "Zagrzeb", "split": "Split",
        "rijeka": "Rijeka", "osijek": "Osijek",
        "nargile": "fajki wodne", "nargila": "fajka wodna",
        "nargilama": "fajkami wodnymi",
        "online": "online",
        "jeftino": "tanio", "jeftin": "tani", "jeftina": "tania", "jeftine": "tanie",
        "skupo": "drogo", "skup": "drogi", "skupa": "droga", "skupe": "drogie",
        "novi": "nowy", "novo": "nowe", "nova": "nowa", "nove": "nowe",
        "stari": "stary", "staro": "stare", "stara": "stara", "stare": "stare",
        "najbolji": "najlepszy", "najbolja": "najlepsza", "najbolje": "najlepsze",
        "veliki": "duży", "veliko": "duże", "velika": "duża", "velike": "duże",
        "mali": "mały", "malo": "małe", "mala": "mała", "male": "małe",
        "grad": "miasto", "gradovi": "miasta", "grada": "miasta",
        "gradu": "mieście", "gradom": "miastem",
    },
    "SI": {
        "stroj": "maszyna", "stroj za": "maszyna do", "stroj za polnjenje": "maszyna do napełniania",
        "polnjenje": "napełnianie", "polniti": "napełniać", "polnilnik": "nabijarka",
        "polnilniki": "nabijarki", "polnilnike": "nabijarki",
        "ročni": "ręczny", "ročna": "ręczna", "ročno": "ręcznie",
        "avtomatski": "automatyczny", "avtomatska": "automatyczna",
        "električni": "elektryczny", "električna": "elektryczna",
        "cigarete": "papierosy", "cigareta": "papieros", "cigaret": "papierosów",
        "cigaretami": "papierosami",
        "tobak": "tytoń", "tobaka": "tytoniu", "tobaku": "tytoniu",
        "tobakom": "tytoniem", "tobačni": "tytoniowy", "tobačne": "tytoniowe",
        "kadilske": "dla palaczy", "kadilski": "dla palaczy",
        "kadilskih": "dla palaczy", "kadilci": "palacze", "kadilec": "palacz",
        "pripomočki": "artykuły", "pripomoček": "artykuł",
        "za kadilce": "dla palaczy", "kadilce": "palacze",
        "potrebščine": "potrzeby", "potrebščina": "potrzeba",
        "naprava": "urządzenie", "naprave": "urządzenia",
        "kako": "jak", "kako napolniti": "jak napełnić",
        "napolniti": "napełnić", "napolnite": "napełnij",
        "kupiti": "kupić", "kupim": "kupię", "kupi": "kupi",
        "veleprodaja": "hurtownia", "veleprodajni": "hurtowy",
        "distributer": "dystrybutor", "distributerji": "dystrybutorzy",
        "distribucija": "dystrybucja",
        "trgovina": "sklep", "trgovine": "sklepy",
        "prodajalna": "sklep", "prodajalne": "sklepy",
        "trafika": "kiosk tytoniowy", "trafike": "kiosku tytoniowego",
        "izdelki": "produkty", "izdelek": "produkt",
        "proizvajalec": "producent", "proizvajalci": "producenci",
        "uvoznik": "importer", "uvozniki": "importerzy",
        "skupina": "grupa", "skupine": "grupy", "skupin": "grup",
        "slovenija": "Słowenia", "slovenski": "słoweński",
        "slovenska": "słoweńska", "slovensko": "słoweńskie",
        "ljubljana": "Lublana", "maribor": "Maribor",
        "online": "online",
        "cene": "ceny", "cena": "cena", "ceni": "ceny",
        "poceni": "tanio", "poceni": "tanio", "drag": "drogi", "draga": "droga",
        "novo": "nowe", "nov": "nowy", "nova": "nowa", "nove": "nowe",
        "staro": "stare", "star": "stary", "stara": "stara",
        "najboljše": "najlepsze", "najboljša": "najlepsza", "najboljši": "najlepszy",
        "velik": "duży", "veliko": "duże", "velika": "duża",
        "majhen": "mały", "majhno": "małe", "majhna": "mała",
        "mesto": "miasto", "mesta": "miasta",
    },
    "LT": {
        "mašina": "maszyna", "mašinos": "maszyny", "mašiną": "maszynę",
        "mašinomis": "maszynami", "mašinų": "maszyn",
        "pildymo": "napełniania", "pildyti": "napełniać", "pildyklė": "nabijarka",
        "pildyklės": "nabijarki", "pildyklę": "nabijarkę",
        "užpildymo": "napełniania", "užpildyti": "napełnić",
        "užpildykite": "napełnij", "užpildo": "napełnia",
        "rankinis": "ręczny", "rankinė": "ręczna", "rankiniu": "ręcznym",
        "automatinis": "automatyczny", "automatinė": "automatyczna",
        "elektrinis": "elektryczny", "elektrinė": "elektryczna",
        "cigarečių": "papierosów", "cigaretes": "papierosy",
        "cigaretė": "papieros", "cigarečių": "papierosów",
        "cigaretėmis": "papierosami",
        "tabako": "tytoniu", "tabakas": "tytoń", "tabaką": "tytoń",
        "tabako": "tytoniowe", "rūkymo": "palenia", "rūkymas": "palenie",
        "rūkaliai": "palacze", "rūkalius": "palaczy", "rūkalius": "palacze",
        "rūkymo": "palenia", "rūkymo": "palenia",
        "rūkytojas": "palacz", "rūkytojai": "palacze",
        "reikmenys": "przybory", "reikmenų": "przyborów",
        "reikalingi": "potrzebne", "reikia": "potrzeba",
        "kaip": "jak", "kaip užpildyti": "jak napełnić",
        "užpildyti": "napełnić", "užpildykite": "napełnij",
        "pirkti": "kupić", "nupirkti": "kupić",
        "didmenininkas": "hurtownik", "didmeninė": "hurtowa",
        "didmeninės": "hurtowe", "didmenininkai": "hurtownicy",
        "didmenine": "hurtowo", "didmenininku": "hurtownika",
        "platintojas": "dystrybutor", "platintojai": "dystrybutorzy",
        "platintojo": "dystrybutora", "platinimas": "dystrybucja",
        "parduotuvė": "sklep", "parduotuvės": "sklepy",
        "parduotuvėje": "sklepie", "parduotuvę": "sklep",
        "prekyba": "handel", "prekybos": "handlu",
        "prekės": "towary", "prekė": "towar", "prekių": "towarów",
        "produktas": "produkt", "produktai": "produkty",
        "gamintojas": "producent", "gamintojai": "producenci",
        "importuotojas": "importer", "importas": "import",
        "importuotojai": "importerzy",
        "sandėlis": "magazyn", "sandėliai": "magazyny",
        "centras": "centrum", "centrai": "centra",
        "grupe": "grupa", "grupės": "grupy", "grupę": "grupę",
        "grupei": "grupie", "grupe": "grupa",
        "lietuva": "Litwa", "lietuvos": "Litwy", "lietuviškas": "litewski",
        "lietuviška": "litewska", "lietuviškos": "litewskie",
        "lietuviški": "litewskie", "lietuvos": "Litewskie",
        "vilnius": "Wilno", "vilniaus": "Wilna",
        "kaunas": "Kowno", "klaipėda": "Kłajpeda",
        "šiauliai": "Szawle", "panevėžys": "Poniewież",
        "elektroninės": "elektroniczne", "elektroniniai": "elektroniczne",
        "elektroninė": "elektroniczna",
        "online": "online",
        "kaina": "cena", "kainos": "ceny", "kainą": "cenę",
        "pigu": "tanio", "pigus": "tani", "pigi": "tania", "pigios": "tanie",
        "brangu": "drogo", "brangus": "drogi", "brangi": "droga", "brangios": "drogie",
        "naujas": "nowy", "nauja": "nowa", "naujo": "nowe", "nauji": "nowe",
        "geriausias": "najlepszy", "geriausia": "najlepsza", "geriausiai": "najlepiej",
        "geriausios": "najlepsze",
        "didelis": "duży", "didelė": "duża", "didelės": "duże", "dideli": "duże",
        "mažas": "mały", "maža": "mała", "mažos": "małe", "maži": "małe",
        "miestas": "miasto", "miestai": "miasta", "miesto": "miasta",
    },
    "LV": {
        "mašīna": "maszyna", "mašīnas": "maszyny", "mašīnu": "maszynę",
        "mašīnai": "maszyny", "mašīnām": "maszynami",
        "pildīšana": "napełnianie", "pildīt": "napełniać", "pildītājs": "nabijarka",
        "pildītāji": "nabijarki", "pildītāju": "nabijarkę",
        "rokas": "ręczny", "roka": "ręczna", "rokasspēks": "ręczny",
        "automātisks": "automatyczny", "automātiska": "automatyczna",
        "elektrisks": "elektryczny", "elektriska": "elektryczna",
        "cigarešu": "papierosów", "cigaretes": "papierosy",
        "cigarete": "papieros", "cigaretēm": "papierosami",
        "tabakas": "tytoń", "tabaku": "tytoniu", "tabakas": "tytoń",
        "tabakas": "tytoniowy", "tabakas": "tytoniowe",
        "smēķētāju": "palaczy", "smēķētājs": "palacz", "smēķētāji": "palacze",
        "piederumi": "przybory", "piederumu": "przyborów",
        "kā": "jak", "kā pildīt": "jak napełniać",
        "nopirkt": "kupić", "nopērk": "kupuje", "nopirktu": "kupić",
        "pircējs": "kupujący", "pircēji": "kupujący",
        "vairumtirgotājs": "hurtownik", "vairumtirgotāji": "hurtownicy",
        "vairumtirdzniecība": "hurtownia", "vairumtirdzniecības": "hurtowni",
        "izplatītājs": "dystrybutor", "izplatītāji": "dystrybutorzy",
        "izplatīšana": "dystrybucja",
        "veikals": "sklep", "veikali": "sklepy", "veikalā": "sklepie",
        "veikalu": "sklepu",
        "tirdzniecība": "handel", "tirdzniecības": "handlu",
        "prece": "towar", "preces": "towary", "preču": "towarów",
        "produkts": "produkt", "produkti": "produkty",
        "ražotājs": "producent", "ražotāji": "producenci",
        "importētājs": "importer", "importētāji": "importerzy",
        "noliktava": "magazyn", "noliktavas": "magazyny",
        "centrs": "centrum", "centri": "centra",
        "grupa": "grupa", "grupas": "grupy", "grupai": "grupy",
        "latvija": "Łotwa", "latvijas": "Łotwy", "latviešu": "łotewski",
        "latviešu": "łotewski", "latviešu": "łotewskie",
        "rīga": "Ryga", "rīgas": "Rygi",
        "liepāja": "Lipawa", "jelgava": "Jełgawa",
        "elektroniskā": "elektroniczna", "elektroniskie": "elektroniczne",
        "elektroniskās": "elektroniczne",
        "tiešsaistes": "online", "tiešsaistē": "online",
        "cena": "cena", "cenas": "ceny", "cenu": "cenę",
        "lēts": "tani", "lēta": "tania", "lēti": "tanie", "lētas": "tanie",
        "dārgs": "drogi", "dārga": "droga", "dārgi": "drogie", "dārgas": "drogie",
        "jauns": "nowy", "jauna": "nowa", "jauns": "nowy", "jauni": "nowe",
        "labākais": "najlepszy", "labākā": "najlepsza", "labākie": "najlepsze",
        "liels": "duży", "liela": "duża", "lieli": "duże", "lielas": "duże",
        "mazs": "mały", "maza": "mała", "mazi": "małe", "mazas": "małe",
        "pilsēta": "miasto", "pilsētas": "miasta", "pilsētā": "mieście",
    },
    "EE": {
        "masin": "maszyna", "masina": "maszyny", "masinat": "maszynę",
        "masinaga": "maszyną", "masinatega": "maszynami",
        "täitmine": "napełnianie", "täita": "napełniać",
        "täitemasin": "maszyna do napełniania", "täitja": "napełniacz",
        "täitjad": "nabijarki", "täitjat": "nabijarkę",
        "tubakatäitja": "nabijarka tytoniowa", "tubakatäitjad": "nabijarki tytoniowe",
        "sigaretimasin": "maszyna do papierosów", "sigaretimasina": "maszyny do papierosów",
        "käsitsi": "ręcznie", "käsitsi": "ręczny", "käsi": "ręka",
        "automaatne": "automatyczna", "automaatne": "automatyczny",
        "automaat": "automat", "automaatse": "automatycznego",
        "elektri": "elektryczny", "elektri-": "elektryczny",
        "elektrooniline": "elektroniczny", "elektroonilised": "elektroniczne",
        "sigarettide": "papierosów", "sigaretid": "papierosy",
        "sigarett": "papieros", "sigarette": "papierosy",
        "sigarettidega": "papierosami",
        "tubakas": "tytoń", "tubaka": "tytoniu", "tubakasse": "tytoniowego",
        "tubakatööstus": "przemysł tytoniowy",
        "suitsetajate": "palaczy", "suitsetaja": "palacz",
        "suitsetajad": "palacze", "suitsetama": "palić",
        "suitsetamine": "palenie",
        "suitsetarbed": "artykuły dla palaczy", "suitsetarbeid": "artykułów dla palaczy",
        "suitsetarvete": "artykułów dla palaczy",
        "tarvikud": "akcesoria", "tarvikute": "akcesoriów",
        "tarvikutele": "akcesoriom",
        "kuidas": "jak", "kuidas täita": "jak napełnić",
        "täita": "napełnić", "täitke": "napełnij",
        "osta": "kupić", "ostma": "kupowanie", "ostsin": "kupiłem",
        "ostja": "kupujący", "ostjad": "kupujący",
        "hulgimüüja": "hurtownik", "hulgimüüjad": "hurtownicy",
        "hulgimüük": "sprzedaż hurtowa", "hulgimüügi": "hurtowej",
        "edasimüüja": "dystrybutor", "edasimüüjad": "dystrybutorzy",
        "edasimüük": "dystrybucja",
        "pood": "sklep", "poed": "sklepy", "poes": "sklepie",
        "tubakapood": "sklep tytoniowy", "tubakapoed": "sklepy tytoniowe",
        "tubakapoe": "sklepu tytoniowego",
        "e-pood": "e-sklep", "epood": "e-sklep",
        "kauplus": "sklep", "kaubandus": "handel",
        "kaubanduse": "handlu", "kaupleja": "handlowiec",
        "tooted": "produkty", "toode": "produkt", "tootega": "produktem",
        "tootja": "producent", "tootjad": "producenci",
        "importija": "importer", "importijad": "importerzy",
        "ladu": "magazyn", "laod": "magazyny",
        "keskus": "centrum", "keskused": "centra",
        "rühm": "grupa", "rühmad": "grupy", "rühma": "grupy",
        "rühmade": "grup", "rühmaga": "grupą",
        "eesti": "Estonia", "eesti": "Estonia",
        "eesti": "estoński", "eesti": "estońska", "eesti": "estońskie",
        "tallinn": "Tallinn", "tartu": "Tartu",
        "pärnu": "Parnawa", "narva": "Narwa",
        "elektroonilised": "elektroniczne",
        "elektrooniline": "elektroniczny",
        "online": "online", "e-poes": "online",
        "hind": "cena", "hinnad": "ceny", "hinda": "cenę",
        "odav": "tani", "odavad": "tanie", "odava": "tania",
        "kallis": "drogi", "kallid": "drogie", "kallist": "drogiego",
        "uus": "nowy", "uued": "nowe", "uue": "nowego", "uusi": "nowe",
        "parim": "najlepszy", "parimad": "najlepsze", "parima": "najlepszego",
        "suur": "duży", "suured": "duże", "suure": "dużego", "suuri": "dużych",
        "väike": "mały", "väiksed": "małe", "väikese": "małego",
        "linn": "miasto", "linnad": "miasta", "linnas": "mieście",
    },
    "FR": {
        "machine": "maszyna", "machines": "maszyny", "machine à": "maszyna do",
        "machine à rouler": "maszyna do skręcania",
        "machine de": "maszyna do", "machine pour": "maszyna do",
        "rouler": "skręcać", "roulage": "skręcanie", "roulés": "skręcane",
        "cigarette": "papieros", "cigarettes": "papierosy", "cigarette électronique": "e-papieros",
        "cigarettes électroniques": "e-papierosy",
        "électronique": "elektroniczny", "électroniques": "elektroniczne",
        "électronique à": "elektroniczna do",
        "tabac": "tytoń", "tabacs": "tytonie", "tabac à": "tytoń do",
        "à rouler": "do skręcania", "à tuber": "do napełniania",
        "tubeuse": "maszyna do napełniania", "tubage": "napełnianie",
        "à tube": "do napełniania",
        "appareil": "urządzenie", "appareils": "urządzenia",
        "appareil à tuber": "urządzenie do napełniania",
        "injecteur": "wstrzykiwacz", "injecteurs": "wstrzykiwacze",
        "manuel": "ręczny", "manuelle": "ręczna", "manuellement": "ręcznie",
        "automatique": "automatyczny", "automatique à": "automatyczna do",
        "automatiquement": "automatycznie",
        "électrique": "elektryczna", "électriques": "elektryczne",
        "fumeur": "palacz", "fumeurs": "palacze", "fumeuse": "palaczka",
        "fume": "pali", "fumer": "palić",
        "accessoires": "akcesoria", "accessoire": "akcesorium",
        "pour fumeur": "dla palacza", "pour fumeurs": "dla palaczy",
        "acheter": "kupić", "achète": "kupuję", "achetez": "kup",
        "achat": "zakup", "achats": "zakupy",
        "vente": "sprzedaż", "ventes": "sprzedaże", "vendu": "sprzedany",
        "vendre": "sprzedawać", "vend": "sprzedaje", "vendez": "sprzedawaj",
        "grossiste": "hurtownik", "grossistes": "hurtownicy",
        "en gros": "hurtowo", "vente en gros": "sprzedaż hurtowa",
        "distributeur": "dystrybutor", "distributeurs": "dystrybutorzy",
        "distribution": "dystrybucja", "distribuer": "dystrybuować",
        "magasin": "sklep", "magasins": "sklepy", "magasin de": "sklep z",
        "boutique": "sklepik", "boutiques": "sklepiki",
        "shop": "sklep", "shops": "sklepy",
        "vape shop": "sklep z waporyzatorami", "vape shops": "sklepy z waporyzatorami",
        "shop vape": "sklep z waporyzatorami", "shops vape": "sklepy z waporyzatorami",
        "supermarché": "supermarket", "supermarchés": "supermarkety",
        "hypermarché": "hipermarket",
        "buraliste": "buralista", "buralistes": "buraliści",
        "tabac": "tytoń", "tabacs": "tytonie", "tabac à": "tytoń do",
        "tabac à rouler": "tytoń do skręcania",
        "débit": "sklep", "débit de tabac": "sklep tytoniowy",
        "débitant": "sprzedawca tytoniu", "débitants": "sprzedawcy tytoniu",
        "producteur": "producent", "producteurs": "producenci",
        "production": "produkcja", "produire": "produkować",
        "produit": "produkt", "produits": "produkty",
        "importateur": "importer", "importateurs": "importerzy",
        "importation": "import", "importer": "importować",
        "usine": "fabryka", "usines": "fabryki",
        "entrepôt": "magazyn", "entrepôts": "magazyny",
        "centre": "centrum", "centres": "centra",
        "groupe": "grupa", "groupes": "grupy", "groupe de": "grupa",
        "groupement": "zrzeszenie", "groupements": "zrzeszenia",
        "france": "Francja", "français": "francuski", "française": "francuska",
        "paris": "Paryż", "lyon": "Lyon", "marseille": "Marsylia",
        "bordeaux": "Bordeaux", "lille": "Lille", "toulouse": "Tuluza",
        "nice": "Nicea", "strasbourg": "Strasburg", "nantes": "Nantes",
        "rennes": "Rennes", "montpellier": "Montpellier",
        "pas cher": "tani", "pas chers": "tanie", "pas chère": "tania",
        "bon marché": "tani", "peu coûteux": "niedrogi",
        "cher": "drogi", "chers": "drogie", "chère": "droga",
        "neuf": "nowy", "neuve": "nowa", "neufs": "nowe", "neuves": "nowe",
        "meilleur": "najlepszy", "meilleure": "najlepsza", "meilleurs": "najlepsze",
        "grand": "duży", "grande": "duża", "grands": "duże", "grandes": "duże",
        "petit": "mały", "petite": "mała", "petits": "małe", "petites": "małe",
        "ville": "miasto", "villes": "miasta", "ville de": "miasto",
        "en ligne": "online", "en-ligne": "online", "online": "online",
        "prix": "cena", "prix de": "cena", "prix du": "cena",
        "promo": "promocja", "promotion": "promocja", "promotions": "promocje",
    },
    "MD": {  # Moldovan = Romanian mostly
        "mașină": "maszyna", "mașini": "maszyny",
        "umplut": "napełniać", "umplere": "napełnianie",
        "țigări": "papierosy", "țigarete": "papierosy",
        "tutun": "tytoń", "tutunului": "tytoniu",
        "dispozitiv": "urządzenie", "injector": "wstrzykiwacz",
        "automată": "automatyczna", "manuală": "ręczna",
        "electrică": "elektryczna",
        "fumători": "palacze", "articole": "artykuły",
        "distribuitor": "dystrybutor", "angro": "hurtowo",
        "magazin": "sklep", "depozit": "magazyn",
        "comerț": "handel", "produse": "produkty",
        "vânzare": "sprzedaż", "vânzători": "sprzedawcy",
        "moldova": "Mołdawia", "chișinău": "Kiszyniów",
        "grup": "grupa", "grupuri": "grupy",
        "ieftin": "tani", "scump": "drogi", "nou": "nowy",
    },
}


def translate_phrase(phrase: str, iso: str) -> str:
    """Token-based PL translation. Preserves brands, + operators, quotes."""
    if iso == "PL":
        return phrase
    d = DICT.get(iso, {})
    if not d:
        return phrase
    # Add common prepositions/articles/connectors (always lowercase)
    prepositions = {
        # RO
        "de": "do", "din": "z", "cu": "z", "la": "w", "pe": "na",
        "şi": "i", "și": "i", "sau": "lub", "fără": "bez", "cel": "ten",
        # BG (Cyrillic)
        "за": "do", "на": "na", "с": "z", "от": "od", "по": "po",
        "и": "i", "или": "lub", "без": "bez", "във": "w", "във": "w",
        "до": "do", "при": "przy", "сред": "wśród",
        # SK/CZ
        "s": "z", "z": "z", "do": "do", "na": "na", "od": "od",
        "pre": "dla", "so": "z", "po": "po", "pri": "przy",
        "alebo": "lub", "a": "i", "aj": "i", "i": "i",
        # HR/SI
        "sa": "z", "u": "w", "iz": "z", "k": "do", "kod": "u",
        "ili": "lub", "bez": "bez", "iznad": "nad",
        # LT
        "ir": "i", "su": "z", "be": "bez", "iš": "z", "ant": "na",
        "po": "po", "apie": "o", "ties": "u",
        # LV
        "un": "i", "ar": "lub", "bez": "bez", "pie": "u", "gar": "przy",
        "par": "o", "no": "od", "uz": "na",
        # EE
        "ja": "i", "või": "lub", "ilma": "bez", "juurde": "do", "kõrval": "obok",
        "peal": "na", "all": "pod", "kohta": "o", "jaoks": "dla",
        # FR
        "et": "i", "ou": "lub", "sans": "bez", "avec": "z", "pour": "dla",
        "par": "przez", "sur": "na", "le": "", "la": "", "les": "",
        "de": "z", "des": "", "du": "",
        # MD same as RO
    }
    # Merge prepositions into dict
    d = {**d, **prepositions}

    # Strip quotes for tokenization, restore at end
    # Handle the special marker " (for group names)
    parts = phrase.split("\"")
    # parts[0] = before quote, parts[1] = in quote, parts[2] = after quote
    out_parts = []
    for i, part in enumerate(parts):
        if i == 1:
            # The quoted part (group name) — keep but translate tokens
            tokens = re.findall(r'\+|"[^"]*"|[^\s+]+', part)
            out_parts.append(_translate_tokens(tokens, d))
        else:
            tokens = re.findall(r'\+|"[^"]*"|[^\s+]+', part)
            out_parts.append(_translate_tokens(tokens, d))
    result = "\"".join(out_parts)
    return result


def _translate_tokens(tokens, d):
    """Translate a list of tokens using dictionary d."""
    out = []
    for tok in tokens:
        if not tok:
            continue
        if tok in ("+", "|"):
            out.append(tok)
            continue
        # Strip leading/trailing punctuation for lookup
        stripped = tok.strip('.,;:()[]{}')
        if not stripped:
            out.append(tok)
            continue
        # If quoted, translate content
        if stripped.startswith('"') and stripped.endswith('"'):
            inner = stripped[1:-1]
            tl = d.get(inner.lower(), inner)
            out.append(f'"{tl}"')
            continue
        # Try exact match
        low = stripped.lower()
        if low in BRANDS or any(b.lower() == low for b in BRANDS):
            out.append(tok)
            continue
        if low in d:
            trans = d[low]
            # Skip empty translations (FR articles)
            if not trans:
                continue
            # Preserve original capitalization
            if stripped.isupper():
                trans = trans.upper()
            elif stripped[0].isupper():
                trans = trans[0].upper() + trans[1:]
            out.append(trans)
        else:
            out.append(tok)
    return " ".join(out)


def annotate_brands(phrase: str) -> str:
    """If phrase is purely a brand name, append a PL descriptor."""
    low = phrase.lower().strip()
    if low in [b.lower() for b in BRAND_PL]:
        # Find the canonical key (case-preserving)
        for k in BRAND_PL:
            if k.lower() == low:
                return f"{k} ({BRAND_PL[k]})"
    return phrase


# === Parse SŁOWNIK-{ISO}.md files ===
def parse_slownik(iso: str) -> dict:
    """Parse SŁOWNIK-{ISO}.md into categorized phrase list."""
    country_label, country_native = COUNTRY[iso]
    if iso == "PL":
        path = ROOT / "data" / "Polska" / "SŁOWNIK-PL.md"
    else:
        # Map ISO to Polish folder name
        folder_map = {
            "CZ": "Czechy", "SK": "Słowacja", "RO": "Rumunia",
            "BG": "Bułgaria", "HR": "Chorwacja", "SI": "Słowenia",
            "LT": "Litwa", "LV": "Łotwa", "EE": "Estonia",
            "FR": "Francja", "MD": "Mołdawia",
        }
        folder = folder_map.get(iso)
        if not folder:
            return {}
        path = ROOT / "data" / folder / f"SŁOWNIK-{iso}.md"

    if not path.exists():
        return {}

    text = path.read_text(encoding="utf-8")
    result = {"device": [], "brand": [], "wholesale": [], "retail": []}
    current_section = None
    section_to_cat = {
        "Nabijarki": "device", "Hurtownie": "wholesale", "Sklepy": "retail",
        "Marketplace": "wholesale", "Marki": "brand",
        # Different section names per country
        "Марки": "brand",  # BG
    }
    # Lines that look like "## Nabijarki" or "## Марки"
    for line in text.split("\n"):
        m = re.match(r'^##\s+(.+?)\s*$', line)
        if m:
            sec = m.group(1).strip()
            current_section = section_to_cat.get(sec)
            continue
        # Phrase line: "- phrase (szac. 1-2k/mies.)"
        m = re.match(r'^\s*-\s+(.+?)\s+\(szac\.\s+([^)]+)\)', line)
        if m and current_section:
            phrase = m.group(1).strip()
            vol = m.group(2).strip()
            pl = translate_phrase(phrase, iso)
            if pl == phrase:
                pl = annotate_brands(phrase)
            result[current_section].append({"phrase": phrase, "vol": vol, "pl": pl})
        else:
            # Phrase without explicit volume
            m2 = re.match(r'^\s*-\s+(.+?)$', line)
            if m2 and current_section:
                # Skip if line contains only markdown or empty after -
                phrase = m2.group(1).strip()
                if phrase and not phrase.startswith('>'):
                    pl = translate_phrase(phrase, iso)
                    if pl == phrase:
                        pl = annotate_brands(phrase)
                    result[current_section].append({"phrase": phrase, "vol": "—", "pl": pl})

    return result


def main():
    out = {}
    for iso in ['PL', 'CZ', 'SK', 'RO', 'BG', 'HR', 'SI', 'LT', 'LV', 'EE', 'FR', 'MD']:
        parsed = parse_slownik(iso)
        # PL: leave as-is (no translation needed)
        if iso == "PL":
            for cat in parsed:
                for item in parsed[cat]:
                    item['pl'] = item['phrase']
        out[iso] = parsed
        # Stats
        total = sum(len(parsed[c]) for c in parsed)
        translated = sum(1 for c in parsed for it in parsed[c] if it['pl'] != it['phrase'])
        if total:
            print(f"  {iso}: {total} phrases, {translated} translated ({100*translated/total:.0f}%)")

    with open("/tmp/phrases_v3.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to /tmp/phrases_v3.json")


if __name__ == "__main__":
    main()
