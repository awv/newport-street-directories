#!/usr/bin/env python3
"""
Newport Street Directory Project: Comprehensive 4-Stage Automated Dataset Healing Pipeline.
Executes deterministic, cross-year verified repairs across all 319,838+ records in data.csv:
  Stage 1: Global Street Name Normalization, Casing/Hyphenation/Suffix Unification & Verified OCR Typos
  Stage 2: Surgical Field-Level Contamination, Column-Shift & Surname-Forename Inversion Repair
           (executed before cross-street splicing so newly un-inverted surnames power the Resident Index)
  Stage 3: False Street Resolution (Ad Banners, Map Grid Headers, 3-Letter Headers, Landmarks, Chambers & Arcades)
  Stage 4: Contiguous Cross-Street Bleed Splicing (via Cross-Year Resident & House Number Continuity)
"""

import csv
import json
import os
import re
import statistics
from collections import Counter, defaultdict

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
MASTER_STREETS_JSON = os.path.join(PROJECT_ROOT, "master_streets.json")

PLACEHOLDER_SURNAMES = {
    "void", "vacant", "house", "null", "nan", "ull", "flat", "flats", "do", "ditto",
    "shop", "office", "offices", "stores", "works", "building", "buildings", "unbuilt",
    "rebuilding", "return", "here", "left", "right", "side", "cross", "over", "ltd",
    "sons", "bros", "co", "the", "and", "from", "to"
}


def parse_house_int(h_str):
    if not h_str:
        return None
    h_str = h_str.strip()
    m = re.match(r"^(\d+)[A-Za-z]?(?:\s*[\-&/]\s*\d+[A-Za-z]?)?$", h_str)
    if m:
        val = int(m.group(1))
        if 0 < val < 2000:
            return val
    return None


def normalize_surname(s):
    if not s:
        return ""
    norm = re.sub(r"[^a-z]", "", s.lower())
    if norm in PLACEHOLDER_SURNAMES or len(norm) < 3:
        return ""
    return norm


# =============================================================================
# STAGE 1 DEFINITIONS: CANONICAL STREET NORMALIZATION & VERIFIED TYPO MAP
# =============================================================================

VERIFIED_OCR_STREET_TYPO_MAP = {
    "vicarage avenue": "Victoria Avenue",
    "caeru road": "Caerleon Road",
    "carleon road": "Caerleon Road",
    "carleon-road": "Caerleon Road",
    "carlton road": "Caerleon Road",
    "caerleon": "Caerleon Road",
    "dewstreet street": "Devon Place",
    "grenville street": "Granville Street",
    "glanville street": "Granville Street",
    "grantsville street": "Granville Street",
    "grenville square": "Granville Square",
    "hewerton street": "Hewertson Street",
    "hewerton st": "Hewertson Street",
    "clifford crescent": "Clyffard Crescent",
    "cliffard crescent": "Clyffard Crescent",
    "clyta crescent": "Clytha Crescent",
    "clytha. park road": "Clytha Park Road",
    "clytha park & road": "Clyffard Crescent",
    "llarthewy road": "Llanthewy Road",
    "llanthwey road": "Llanthewy Road",
    "llanthewey road": "Llanthewy Road",
    "llanthamthi street": "Llanarth Street",
    "acadia terrace": "Acacia Terrace",
    "academia terrace": "Acacia Terrace",
    "line street": "Lime Street",
    "crowmell road": "Cromwell Road",
    "crowwell road": "Cromwell Road",
    "sudbury terrace": "Sidbury Terrace",
    "blewit street": "Blewitt Street",
    "poffey terrace": "Pottery Terrace",
    "potter terrace": "Pottery Terrace",
    "potter road": "Potter Street",
    "mendalgfief road": "Mendalgief Road",
    "upperra street": "Ruperra Street",
    "new ruperta. street": "New Ruperra Street",
    "new ruperta street": "New Ruperra Street",
    "woolseley street": "Wolseley Street",
    "wolesly": "Wolseley Street",
    "witham": "Witham Street",
    "downing": "Downing Street",
    "dorset": "Dos Road",
    "dorset road": "Dos Road",
    "courtbybella street": "Courtybella Street",
    "courtbybella st": "Courtybella Street",
    "courtybella st": "Courtybella Street",
    "courtybella": "Courtybella Street",
    "courtbybella terrace": "Courtybella Terrace",
    "courtbybella ter": "Courtybella Terrace",
    "courtbella ter": "Courtybella Terrace",
    "courtybella ter": "Courtybella Terrace",
    "comassie street": "Coomassie Street",
    "commassie street": "Coomassie Street",
    "comomassie street": "Coomassie Street",
    "oriewald road": "Oswald Road",
    "wington terrace": "Wrington Terrace",
    "kenworth road": "Kenilworth Road",
    "walis street": "Wallis Street",
    "walllis street": "Wallis Street",
    "caerleau crescent": "Caerau Crescent",
    "esweswell terrace": "Eveswell Terrace",
    "eseswell terrace": "Eveswell Terrace",
    "esveswell terrace": "Eveswell Terrace",
    "eweswell terrace": "Eveswell Terrace",
    "eweswell street": "Eveswell Street",
    "eve eveswell street": "Eveswell Street",
    "eseswell park": "Eveswell Park Road",
    "eveswell-park": "Eveswell Park Road",
    "eveswell park": "Eveswell Park Road",
    "banewell road": "Baneswell Road",
    "shaffersbury street": "Shaftesbury Street",
    "shaftesbury st": "Shaftesbury Street",
    "shaftsbury park": "Shaftesbury Park",
    "modern road": "Morden Road",
    "newport junction road": "Junction Road",
    "kingsand terrace": "Kingsland Terrace",
    "gear street": "Kear Street",
    "fotherthingham place": "Fotheringham Place",
    "fothergilling place": "Fotheringham Place",
    "kingswill gardens": "Kingsmill Gardens",
    "tgare street": "Tregare Street",
    "llewynderi road": "Llwynderi Road",
    "llwyderi road": "Llwynderi Road",
    "catsach road": "Catsash Road",
    "depôt street": "Depot Street",
    "dewpost street": "Depot Street",
    "colder road": "Coldra Road",
    "caston place": "Caxton Place",
    "winmilli street": "Winmill Street",
    "winnill street": "Winmill Street",
    "harry street": "Harrhy Street",
    "iftfon street": "Ifton Street",
    "doc street": "Dock Street",
    "dorrington street": "Donnington Street",
    "vicarrage lane": "Vicarage Lane",
    "roberts street": "Robert Street",
    "mansell street": "Mansel Street",
    "mountoy place": "Mountjoy Place",
    "gedar road": "Cedar Road",
    "annsley road": "Annesley Road",
    "colner street": "Colne Street",
    "roselyn road": "Rosslyn Road",
    "philip street": "Phillip Street",
    "f. oak ter": "Fairoak Terrace",
    "fair oak ter": "Fairoak Terrace",
    "fair oak terrace": "Fairoak Terrace",
    "and fairoak avenue": "Fairoak Avenue",
    "summer hill rd": "Summerhill Road",
    "summer hill road": "Summerhill Road",
    "summer hill avenue": "Summerhill Avenue",
    "tredgar place": "Tredegar Place",
    "bisshopsgate parade": "Bishopsgate Parade",
    "clkvedon terrace": "Clevedon Terrace",
    "bryngblas road": "Brynglas Road",
    "bryngwas road": "Brynglas Road",
    "bryngblas crescent": "Brynglas Crescent",
    "brynghyfryd road": "Brynhyfryd Road",
    "clarance street": "Clarence Street",
    " keen street": "Keene Street",
    "keen street": "Keene Street",
    "woodland": "Woodland Road",
    "tyllwyyd road": "Tyllwyd Road",
    "glos'ter place": "Gloster Place",
    "glo'ster place": "Gloster Place",
    "glos'ter street": "Gloster Street",
    "glo'ster street": "Gloster Street",
    "water's lane": "Waters Lane",
    "waters's lane": "Waters Lane",
    "constable's lane": "Constables Lane",
    "constables' lane": "Constables Lane",
    "toombs' court": "Toomb's Court",
    "moulders arms terrace": "Moulders' Arms Terrace",
    "st. vincent's road": "St. Vincent Road",
    "st. vincent's rd": "St. Vincent Road",
    "st. michael's st": "High Street, Pill",
    "st. michael's street": "High Street, Pill",
    "and spencer-road": "Caerleon Road",
    "and spencer road": "Caerleon Road",
    "cor corporation road": "Corporation Road",
    "beth jones, caretaker st. woolos road": "St. Woolos Road",
    "alexandra docks alexandra road": "Alexandra Road",
    "edward vii. avenue": "Edward VII Avenue",
    "edward vii avenue": "Edward VII Avenue",
    "edward vii crescent": "Edward VII Crescent",
    "ciderhill wharf": "Cinderhill Wharf",
    "cimbrian wharf": "Cambrian Wharf",
    "& cambrian wharf": "Cambrian Wharf",
    "bankruptcy — g. h. commercial wharf": "Commercial Wharf",
    "packet wharf": "Screw Packet Wharf",
}

SUFFIX_EXPANSIONS = [
    (r"(?<=[\s\-])St\.?$", "Street"),
    (r"(?<=[\s\-])St\.?(?=\s*,)", "Street"),
    (r"(?<=[\s\-])Rd\.?$", "Road"),
    (r"(?<=[\s\-])Rd\.?(?=\s*,)", "Road"),
    (r"(?<=[\s\-])Ave?\.?$", "Avenue"),
    (r"(?<=[\s\-])Ter\.?$", "Terrace"),
    (r"(?<=[\s\-])Pl\.?$", "Place"),
    (r"(?<=[\s\-])Cres\.?$", "Crescent"),
    (r"(?<=[\s\-])Sq\.?$", "Square"),
    (r"(?<=[\s\-])Pde\.?$", "Parade"),
    (r"(?<=[\s\-])Gdns\.?$", "Gardens"),
]


def normalize_street_stage1(raw_st):
    if not raw_st:
        return ""
    s = raw_st.strip()
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"^[\|\t\s]+", "", s).strip()
    s = re.sub(r"^(?:Up|Upp)[\.\s]+", "Upper ", s, flags=re.I).strip()
    s = re.sub(r"[\s\-—–_]+(?:continued|contd|cont|cont\.|contd\.)\s*$", "", s, flags=re.I).strip()
    s = re.sub(r"\s+[A-F]\s+\d+(?:[\s/]+\d+[A-Za-z]?)?\s*$", "", s).strip()
    s = re.sub(r"^(?:E\s+S|Cs)\s+(?=[A-Z][a-z]+\s+(?:Road|Street|Avenue|Place|Terrace))", "", s).strip()
    s = re.sub(r"\s*\(\d+\)\s*$", "", s).strip()
    s = s.rstrip(":,.-—– ")

    s = re.sub(
        r"([A-Za-z\.\']+)[\-—–]+(Street|St\.?|Road|Rd\.?|Avenue|Ave?\.?|Terrace|Ter\.?|Crescent|Cres\.?|Place|Pl\.?|Parade|Pde\.?|Lane|Square|Sq\.?|Hill|Park|Gardens|Gdns\.?|Court|Drive|Way|Close|Walk|Grove|Row|Villas|Cottages|Bridge|Wharf)\b",
        r"\1 \2",
        s,
        flags=re.I,
    )

    for pat, repl in SUFFIX_EXPANSIONS:
        s = re.sub(pat, repl, s, flags=re.I)

    s = re.sub(r"'S\b", "'s", s)

    s = re.sub(
        r"\b(road|street|avenue|place|terrace|lane|crescent|square|parade|gardens|court|drive|hill|walk|way|close|grove|park|wharf|bridge|arch|row|villas|cottages|buildings|chambers|arcade)\b",
        lambda m: m.group(1).capitalize(),
        s,
        flags=re.I,
    )

    s_low = s.lower().strip()
    if s_low in VERIFIED_OCR_STREET_TYPO_MAP:
        return VERIFIED_OCR_STREET_TYPO_MAP[s_low]

    return s


# =============================================================================
# STAGE 2 DEFINITIONS: GIVEN NAMES, TRADES, & COLUMN SHIFT RULES
# =============================================================================

ABBREV_FORENAMES = {
    "wm", "thos", "chas", "geo", "jas", "jno", "robt", "fredk", "saml", "benj", "edwd", "herbt",
    "herb", "alf", "hy", "dd", "richd", "jos", "archd", "regd", "eben", "nathl", "danl", "michl",
    "elizth", "margt", "clar", "matt", "arth", "albt", "edw", "zach", "steph", "ern"
}

GIVEN_NAMES_ONLY = {
    "william", "frederick", "ernest", "albert", "harold", "horace", "percy", "sidney", "sydney",
    "archibald", "reginald", "wilfred", "horatio", "cornelius", "theophilus", "ebenezer", "zachariah",
    "gwendoline", "beatrice", "gertrude", "minnie", "gladys", "sarah", "elizabeth", "louisa", "emily",
    "mary", "hannah", "martha", "alice", "clara", "annie", "edith", "ethel", "florence", "mabel",
    "maud", "maude", "ada", "bertha", "bridget", "caroline", "catherine", "charlotte", "dinah",
    "eleanor", "eliza", "ellen", "emma", "esther", "eva", "fanny", "georgina", "harriet", "helen",
    "hester", "ida", "isabella", "jane", "jessie", "julia", "kate", "laura", "lavinia", "lilian",
    "lily", "lucy", "lydia", "margaret", "maria", "marion", "matilda", "millicent", "miriam",
    "nellie", "norah", "olive", "phoebe", "priscilla", "rachel", "rebecca", "rhoda", "rosina",
    "ruth", "selina", "sophia", "susan", "susannah", "theresa", "victoria", "violet", "winifred",
    "edgar", "cecil", "clarence", "claude", "eric", "geoffrey", "gerald", "gordon", "kenneth",
    "laurence", "leslie", "lionel", "maurice", "noel", "oswald", "ralph", "roland", "ronald",
    "roy", "rupert", "victor", "gustave"
}

DUAL_GIVEN_OR_SURNAME = {
    "john", "thomas", "james", "george", "charles", "henry", "arthur", "walter", "frank", "david",
    "edwin", "edward", "samuel", "joseph", "richard", "robert", "herbert", "alfred", "stephen",
    "daniel", "benjamin", "patrick", "michael", "peter", "hugh", "ivor", "trevor", "cyril", "evan",
    "owen", "morgan", "lewis", "harry", "francis", "martin", "philip", "phillip", "bernard", "leonard",
    "stanley", "hubert", "abraham", "isaac", "jacob", "moses", "solomon", "timothy", "matthew",
    "mark", "luke", "paul", "andrew", "simon", "alexander", "nicholas", "christopher", "anthony",
    "clifford", "desmond", "douglas", "gilbert", "norman", "raymond", "wallace"
}

ALL_GIVEN_NAMES = GIVEN_NAMES_ONLY | DUAL_GIVEN_OR_SURNAME | ABBREV_FORENAMES | {
    "rosser", "caleb", "valentine", "edm", "edmund", "llewellyn", "griffith", "howell", "rees",
    "gwyn", "gwilym", "idris", "bryn", "emrys", "gomer", "tudor", "christmas", "joshua",
    "josiah", "elijah", "elisha", "enoch", "reuben", "samson", "silas", "simeon", "tobias", "uriah",
    "hurriet", "harrict", "rehd", "theo", "mich", "nat", "ann", "anne", "bessie", "blanche",
    "constance", "daisy", "dora", "doris", "dorothy", "elsie", "enid", "evelyn", "flora", "grace",
    "gwen", "hilda", "irene", "iris", "ivy", "jean", "joan", "josephine", "kathleen", "katie",
    "maggie", "marjorie", "may", "mildred", "molly", "muriel", "nancy", "nora", "pearl",
    "phyllis", "polly", "rose", "ruby", "stella", "sybil", "sylvia", "vera", "winnie"
}

PURE_TRADES_LOWER = {
    "labourer", "carpenter", "butcher", "grocer", "tailor", "draper", "bootmaker",
    "shoemaker", "painter", "plumber", "mason", "plasterer", "blacksmith", "fitter",
    "machinist", "ironworker", "steelworker", "haulier", "trimmer", "coal trimmer",
    "seaman", "mariner", "solicitor", "accountant", "architect", "builder", "confectioner",
    "fruiterer", "greengrocer", "hairdresser", "tobacconist", "newsagent", "chemist",
    "stationer", "printer", "watchmaker", "jeweller", "pawnbroker", "dairyman",
    "dressmaker", "laundress", "charwoman", "gardener", "engineman", "fireman",
    "guard", "porter", "clerk", "agent", "wheelwright", "cooper", "boilermaker",
    "shipwright", "moulder", "pilot", "waterman", "cabman", "innkeeper", "shopkeeper",
    "baker", "miller", "bookseller", "surgeon", "physician", "surveyor", "schoolmaster",
}

NON_SURNAME_TOKENS = {
    "mrs", "miss", "mr", "dr", "rev", "jun", "sen", "jr", "sr", "esq", "capt", "maj", "col", "sgt",
    "inspr", "widow", "madame", "sisters", "bros", "brothers", "son", "sons", "co", "ltd", "limited",
    "chambers", "buildings", "house", "villa", "villas", "cottage", "cottages", "lodge", "hall",
    "works", "stores", "shop", "hotel", "inn", "tavern", "arms", "bank", "office", "offices",
    "school", "schools", "church", "chapel", "mission", "institute", "club", "station", "yard",
    "wharf", "arcade", "market", "ferry", "void", "vacant", "here", "return", "left", "right",
    "north", "south", "east", "west", "upper", "lower", "newport", "wales", "mon", "gwr",
    "null", "nan", "ull", "flat", "flats"
} | PURE_TRADES_LOWER

EXCLUDE_HOUSE_SURNAME = {
    "void", "vacant", "here", "return", "from", "left", "right", "east", "west", "north", "south",
    "floor", "ltd", "sons", "storage", "cardiff", "newport", "curriers", "salesmen", "contractor",
    "merchants", "engineering", "boot", "grindery", "dealer", "null", "nan", "ull", "flat", "flats",
    "house", "shop", "stores", "office", "offices", "works", "yard", "wharf", "hall", "church", "chapel",
    "hotel", "inn", "tavern", "arms", "bank", "villa", "villas", "cottage", "cottages", "terrace",
    "place", "buildings", "chambers", "school", "schools", "mission", "club", "station", "lodge",
    "pri", "cor", "can", "alb", "com", "bri", "che", "new", "sto", "vic", "hig", "doc", "mar", "que"
}


# =============================================================================
# STAGE 3 DEFINITIONS: FALSE STREETS (ADS, MAP CODES, LANDMARKS, CHAMBERS)
# =============================================================================

PURE_HEADER_OR_LANDMARK_PATTERNS = re.compile(
    r"^(?:"
    r"the newport steam laundry.*|"
    r"the steam laundry.*|"
    r"p\.\s*e\.\s*gane.*|"
    r"francis'\s*dye\s*works.*|"
    r"r\.\s*h\.\s*johns.*|"
    r"edwards\s*ltd.*|"
    r"herbert\s*edwards\s*ltd.*|"
    r"geo\.\s*greenland.*|"
    r"mourning\s*orders\s*promptly.*|"
    r"largest\s*furniture\s*showrooms.*|"
    r"suits\s*and\s*costumes\s*cleaned.*|"
    r"suppliers\s*of\s*best\s*grade.*|"
    r"furniture\s*manufacturers\s*for\s*nearly.*|"
    r"newport\s*street\s*directory.*|"
    r"tel\.\s*\d+.*|"
    r"[a-f]\s*\d+(?:\s+\d+[a-z]?)?|"
    r"c\s*50b|"
    r"gg2|"
    r"cor|can|dd|st|edw|exe|stow|higher|service|telephone|t\.s\.o|m\.r\.c\.s|l\.r\.c\.p|f\.s\.i|p\.t\.\s*centre|void|house|street|price|dock|church|offices|city\s*station|"
    r"maindee\s*schools|"
    r"alexandra\s*schools?|"
    r"durham\s*road\s*schools|"
    r"bolt\s*street\s*schools|"
    r"lliswerry\s*schools|"
    r"spring\s*gard'ns\s*schools|"
    r"shire\s*hospital|"
    r"allt-yr-yn\s*hospital|"
    r"m\.o\.,\s*s\.b\..*|"
    r"commercial\s*road\s*post\s*office.*|"
    r"pillgwenlly\s*post\s*office.*|"
    r"west\s*park\s*post\s*office|"
    r"stow\s*park\s*post\s*office|"
    r"p\.o\.\s*tel\.\s*call\s*office|"
    r"victoria\s*road\s*congregational\s*church|"
    r"llanth?e?wy\s*road\s*baptist\s*church|"
    r"baptist\s*chapel|"
    r"baptist\s*temple|"
    r"congregational\s*church|"
    r"gational\s*church|"
    r"presbyterian\s*chapel|"
    r"st\.\s*matthew's\s*church|"
    r"st\.\s*james'\s*church|"
    r"st\.\s*woolos\s*church|"
    r"st\.\s*mary\s*street\s*baptist\s*chapel|"
    r"stow\s*hill\s*bapt\.\s*chapel|"
    r"wesleyan\s*mission\s*hall|"
    r"wesleyan|"
    r"holy\s*cross|"
    r"holy\s*trinity|"
    r"navvies'\s*mission\s*room|"
    r"alma\s*st\.\s*baptist\s*sunday\s*school|"
    r"duckpool\s*road\s*baptist|"
    r"christchurch\s*cemetery|"
    r"public\s*park|"
    r"newport\s*athletic\s*grounds|"
    r"athletic\s*club's\s*office|"
    r"corporation\s*baths\s*and\s*gymnasium|"
    r"school\s*medical\s*department|"
    r"newport\s*education\s*offices|"
    r"tive\s*club|"
    r"r\.s\.p\.c\.a|"
    r"l\.\s*&\s*n\.w\.r|"
    r"g\.w\.r|"
    r"transporter\s*bridge|"
    r"27\s*phillips\s*memorial\s*hall|"
    r"35-35a|23-23a|11|"
    r"rt\.-hand\s*side\s*corporation[\s\-]*r(?:oa)?d|"
    r"east\s*side,\s*albany\s*street|"
    r"streets\s*each\s*side\s*of\s*church\s*r(?:oa)?d|"
    r"nos\s*59-71\s*church\s*road|"
    r"street\s*and\s*dock\s*street|"
    r"hale\s*mrs,\s*1\s*vine\s*place|"
    r"farmer\s*a\.\s*w\.,\s*2\s*glen\s*view|"
    r"allen\s*septimus,\s*mount\s*view|"
    r"thompson\s*wm\.,\s*the\s*avenue|"
    r"poole\s*g|"
    r"gibbon\s*h\.\s*railway\s*gu'r(?:oa)?d"
    r")$",
    re.I,
)

DIRECT_FALSE_STREET_PARENT = {
    "35-35a": "High Street",
    "rt.-hand side corporation-rd": "Corporation Road",
    "rt.-hand side corporation road": "Corporation Road",
    "east side, albany street": "Albany Street",
    "east side, albany-street": "Albany Street",
    "streets each side of church rd": "Church Road",
    "streets each side of church road": "Church Road",
    "nos 59-71 church road": "Church Road",
    "cor": "Corporation Road",
    "can": "Canal Parade",
    "maindee schools": "Chepstow Road",
    "durham road schools": "Durham Road",
    "victoria road congregational church": "Hoskins Street",
    "llanthwey road baptist church": "Llanthewy Road",
    "baptist chapel": "Commercial Road",
    "baptist temple": "Commercial Road",
    "commercial road post office, m.o.,s.b., & a.& i. office": "Commercial Road",
    "pillgwenlly post office t. & m.o., s.b., and a. and i. office": "Commercial Road",
    "27 phillips memorial hall": "Dock Street",
    "r.s.p.c.a": "Stockton Road",
    "tive club": "Commercial Road",
    "christchurch cemetery": "Church Road",
    "public park": "Ombersley Road",
    "duckpool road baptist": "Seamoor Terrace",
    "allen septimus, mount view": "Llanthewy Road",
    "thompson wm., the avenue": "Clytha Square",
    "gibbon h. railway gu'rd": "Commercial Street",
    "gibbon h. railway gu'road": "Commercial Street",
    "city station": "High Street",
    "church": "Stow Hill",
    "dock": "Dock Street",
    "screw packet wharf": "High Street",
}

CHAMBER_TO_PARENT_STREET = {
    "austin friars chambers": ("Dock Street", "Austin Friars Chambers"),
    "friars chambers": ("Dock Street", "Friars Chambers"),
    "westgate chambers": ("Commercial Street", "Westgate Chambers"),
    "commercial st.. westgate chambers": ("Commercial Street", "Westgate Chambers"),
    "ltd. , westgate' buildings": ("Commercial Street", "Westgate Buildings"),
    "westgate buildings": ("Commercial Street", "Westgate Buildings"),
    "albion chambers": ("Commercial Street", "Albion Chambers"),
    "guildhall chambers": ("Commercial Street", "Guildhall Chambers"),
    "metro. bank chambers": ("Commercial Street", "Metro. Bank Chambers"),
    "metropolitan bank chambers": ("Commercial Street", "Metropolitan Bank Chambers"),
    "lloyd's bank chambers": ("Commercial Street", "Lloyd's Bank Chambers"),
    "wesley chambers": ("Commercial Street", "Wesley Chambers"),
    "wesley buildings": ("Commercial Street", "Wesley Buildings"),
    "town hall": ("Commercial Street", "Town Hall"),
    "town hall chambers": ("Commercial Street", "Town Hall Chambers"),
    "tredegar hall": ("Commercial Street", "Tredegar Hall"),
    "market buildings": ("Market Street", "Market Buildings"),
    "albert hall chambers": ("Stow Hill", "Albert Hall Chambers"),
    "central chambers": ("Stow Hill", "Central Chambers"),
    "victoria chambers": ("Bridge Street", "Victoria Chambers"),
    "tredegar chambers": ("Bridge Street", "Tredegar Chambers"),
    "cambrian chambers": ("Bridge Street", "Cambrian Chambers"),
    "london city & midland bank": ("Bridge Street", "London City & Midland Bank"),
    "pembroke chambers": ("High Street", "Pembroke Chambers"),
    "winchester chambers": ("High Street", "Winchester Chambers"),
    "highbury chambers": ("High Street", "Highbury Chambers"),
    "glo'ster bank chambers": ("High Street", "Glo'ster Bank Chambers"),
    "glo'ster bank": ("High Street", "Glo'ster Bank"),
    "corn exchange": ("High Street", "Corn Exchange"),
    "corn exchange chambers": ("High Street", "Corn Exchange Chambers"),
    "council chambers": ("Corn Street", "Council Chambers"),
    "eldon chambers": ("Skinner Street", "Eldon Chambers"),
    "borough chambers": ("Skinner Street", "Borough Chambers"),
    "skinner street chambers": ("Skinner Street", "Skinner Street Chambers"),
    "albany chambers": ("Commercial Road", "Albany Chambers"),
    "arlington chambers": ("Commercial Road", "Arlington Chambers"),
    "emlyn chambers": ("Commercial Road", "Emlyn Chambers"),
    "bank chambers": ("Baneswell Road", "Bank Chambers"),
    "queen's buildings": ("Queen Street", "Queen's Buildings"),
    "brown's buildings": ("Shaftesbury Street", "Brown's Buildings"),
    "britannia buildings": ("Carlisle Place", "Britannia Buildings"),
    "fair oak buildings": ("Chepstow Road", "Fair Oak Buildings"),
    "west end buildings": ("Chepstow Road", "West End Buildings"),
    "crown chambers": ("Commercial Street", "Crown Chambers"),
    "arcade chambers": ("High Street", "Arcade Chambers"),
    "stow chambers": ("Stow Hill", "Stow Chambers"),
    "steam packet chambers": ("Dock Street", "Steam Packet Chambers"),
    "maindee municipal bldgs": ("Chepstow Road", "Maindee Municipal Buildings"),
    "the provision market": ("Market Street", "Provision Market"),
    "the market": ("Henry Street", ""),
}


def resolve_slice_by_residents(slice_rows, yr, resident_house_streets, default_street):
    n = len(slice_rows)
    if n == 0:
        return []

    row_votes = []
    for r in slice_rows:
        key = (r["_norm_sur"], r["_h_int"])
        votes = Counter()
        if key[0] and key[1] is not None and key in resident_house_streets:
            for ost, oyrs in resident_house_streets[key].items():
                if ost != r["street"]:
                    votes[ost] += len(oyrs)
        row_votes.append(votes.most_common(1)[0][0] if votes else None)

    overall = Counter(v for v in row_votes if v is not None)
    if not overall:
        return [default_street] * n

    top_st, top_cnt = overall.most_common(1)[0]
    if len(overall) >= 2:
        sec_st, sec_cnt = overall.most_common(2)[1]
        if sec_cnt >= 3 and top_cnt >= 3:
            best_split = None
            best_score = 0
            for k in range(1, n):
                left_c = Counter(v for v in row_votes[:k] if v is not None)
                right_c = Counter(v for v in row_votes[k:] if v is not None)
                if left_c and right_c:
                    l_top, l_sc = left_c.most_common(1)[0]
                    r_top, r_sc = right_c.most_common(1)[0]
                    if l_top != r_top and l_sc >= 3 and r_sc >= 3:
                        if l_sc + r_sc > best_score:
                            best_score = l_sc + r_sc
                            best_split = (k, l_top, r_top)
            if best_split:
                k, l_top, r_top = best_split
                return [l_top] * k + [r_top] * (n - k)

    if top_cnt >= 2:
        return [top_st] * n
    return [default_street] * n


def main():
    print("=" * 80)
    print("EXECUTING 4-STAGE MACRO DATASET HEALING PIPELINE (PASS 2)")
    print("=" * 80)

    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows):,} initial records from {DATA_CSV}.")

    # =========================================================================
    # STAGE 1: GLOBAL STREET NAME NORMALIZATION & TYPO UNIFICATION
    # =========================================================================
    stage1_changes = 0
    for r in rows:
        old_st = r["street"]
        new_st = normalize_street_stage1(old_st)
        if new_st != old_st:
            r["street"] = new_st
            stage1_changes += 1

    print(f"[Stage 1] Normalized & unified street names on {stage1_changes:,} records.")

    # =========================================================================
    # STAGE 2: FIELD CONTAMINATION, COLUMN-SHIFT & INVERSION REPAIR
    # (Executed BEFORE Resident Index build so newly restored surnames participate!)
    # =========================================================================
    stage2_field_stats = Counter()

    LAYOUT_ROW_PAT = re.compile(
        r"^(?:"
        r"(?:first|second|third|top|1st|2nd|3rd|ground)\s+floor\.?|"
        r"newport\s+street\s+directory\.?|"
        r"newport\s+stret\s+list\.?|"
        r"street\s+directory\.?|"
        r"high|"
        r"\(?return(?:\s+upperside|\s+lowerside)?\.?\)?|"
        r"(?:left|right)[\s\-]+hand\s+side\.?|"
        r"here\s+(?:is|are|cross\s+over)\s*[a-z0-9\s\.\-']*|"
        r"\(here\s+cross\s+over\)"
        r")$",
        re.I,
    )

    INLINE_HERE_IS_PAT = re.compile(
        r"(?:,?\s*\bhere\s+(?:is|are)\s+[A-Za-z0-9\s\.\-']+|\s*\(?return\.?\)?\s*)$",
        re.I,
    )

    FORENAME_TRADE_SUFFIX_PAT = re.compile(
        r"^([A-Za-z\.\s\']+?)(?:[\.,]+\s*|\s+)(labourer|labr|ironworker|steelworker|trimmer|coal trimmer|haulier|carpenter|fitter|seaman|mariner|mason|painter|plumber|bootmaker|shoemaker|tailor|grocer|butcher|clerk|engine driver|boilermaker|blacksmith|plasterer|machinist|gardener|fireman|guard|porter|baker|draper|fruiterer|greengrocer|hairdresser|hairdressr|watchmaker|printer|policeman|signalman|platelayer|moulder|shipwright|wheelwright|cooper|dairyman|solicitor|rivetter|platelyr|sheetwghr|gaswkr|gasworker|firemn|draper's asst|leather drssr|carman|iron moulder|cab driver|fishmonger|glsblwer|pork bther)\.?\s*$",
        re.I,
    )

    SUR_WITH_TRADE_PAT = re.compile(
        r"^([A-Za-z\.\s\']+?)(?:[\.,]+\s*|\s+)(labourer|labr|trimmer|coal trimmer|haulier|carpenter|fitter|seaman|mariner|mason|painter|plumber|bootmaker|shoemaker|tailor|grocer|butcher|clerk|engine driver|boilermaker|blacksmith|plasterer|machinist|gardener|fireman|guard|porter|baker|draper|fruiterer|greengrocer|hairdresser|hairdressr|watchmaker|printer|policeman|signalman|platelayer|moulder|shipwright|wheelwright|cooper|dairyman|solicitor|gas worker|gasworker|ironworker|steelworker|docker|foreman|inspr|inspector|manager|agent|builder|contractor|confectioner|cab driver|carman|stoker|shunter|pointsman|checker|timekeeper|storekeeper|fishmonger)\.?\s*$",
        re.I,
    )

    # Pre-pass: Clean literal NaN / NULL / ULL artifacts across all fields
    for r in rows:
        for k in ("house_number", "building_name", "surname", "forename", "trade"):
            val = r[k].strip()
            if val in ("NaN", "Nan", "nan", "NULL", "null", "ULL", "LL"):
                r[k] = ""
                stage2_field_stats["cleaned_literal_nan_or_null"] += 1
            else:
                r[k] = val
        # Rejoin split "Na" | "N, trade" or "N" | "ULL, trade"
        if r["forename"].endswith(" Na") and r["trade"].startswith("N"):
            r["forename"] = r["forename"][:-3].strip()
            r["trade"] = re.sub(r"^N[\s,\.]*", "", r["trade"]).strip()
            stage2_field_stats["rejoined_nan_split_trade"] += 1
        if r["forename"].endswith(" N") and r["trade"].startswith("ULL"):
            r["forename"] = r["forename"][:-2].strip()
            r["trade"] = re.sub(r"^ULL[\s,\.]*", "", r["trade"]).strip()
            stage2_field_stats["rejoined_null_split_trade"] += 1
        if r["trade"].startswith("NULL,") or r["trade"].startswith("NaN,"):
            r["trade"] = re.sub(r"^(?:NULL|NaN)[\s,\.]*", "", r["trade"]).strip()
        r["forename"] = re.sub(r"\s+(?:Na\s*N|NaN|N\s*U|NULL)\b", "", r["forename"]).strip()
        r["surname"] = re.sub(r"\s+(?:Na\s*N|NaN|N\s*U|NULL)\b", "", r["surname"]).strip()
        if r["surname"].endswith(" Na") and r["forename"] == "N":
            r["surname"] = r["surname"][:-3].strip()
            r["forename"] = ""

    cleaned_rows = []
    n_rows = len(rows)
    for idx in range(n_rows):
        r = rows[idx]
        h = r["house_number"].strip()
        b = r["building_name"].strip()
        s = r["surname"].strip()
        f = r["forename"].strip()
        t = r["trade"].strip()

        # Check if this row is ONLY a house number range stuck in `surname`
        if not h and not b and not f and not t and re.match(r"^\d+[A-Za-z]?\s*[\-&/]\s*\d+[A-Za-z]?$", s):
            if idx + 1 < n_rows and rows[idx + 1]["street"] == r["street"] and not rows[idx + 1]["house_number"].strip():
                rows[idx + 1]["house_number"] = s
                stage2_field_stats["attached_orphan_house_range"] += 1
                continue

        # Check if this row is completely empty except `house_number` (including phantom NaN/NULL duplicate rows)
        if not b and not s and not f and not t:
            if h:
                # If it duplicates the preceding row's house number on the same street, drop phantom NaN row
                if cleaned_rows and cleaned_rows[-1]["street"] == r["street"] and cleaned_rows[-1]["house_number"] == h:
                    stage2_field_stats["dropped_phantom_nan_duplicate_row"] += 1
                    continue
                elif idx + 1 < n_rows and rows[idx + 1]["street"] == r["street"] and not rows[idx + 1]["house_number"].strip():
                    rows[idx + 1]["house_number"] = h
                    stage2_field_stats["attached_orphan_house_num"] += 1
                    continue
                else:
                    stage2_field_stats["dropped_empty_orphan_num"] += 1
                    continue
            else:
                stage2_field_stats["dropped_pure_layout_row"] += 1
                continue

        # Check if pure layout marker row
        combined_text = f"{s} {f}".strip()
        if not b and not t and (
            LAYOUT_ROW_PAT.match(combined_text)
            or (LAYOUT_ROW_PAT.match(s) and not f)
            or (LAYOUT_ROW_PAT.match(f) and not s)
        ):
            stage2_field_stats["dropped_pure_layout_row"] += 1
            continue

        # Strip inline 'here is ...' or '(return)' from trade or forename
        if t and INLINE_HERE_IS_PAT.search(t):
            new_t = INLINE_HERE_IS_PAT.sub("", t).strip(" ,.-")
            if new_t != t:
                t = new_t
                stage2_field_stats["stripped_inline_here_is"] += 1
        if f and INLINE_HERE_IS_PAT.search(f):
            new_f = INLINE_HERE_IS_PAT.sub("", f).strip(" ,.-")
            if new_f != f:
                f = new_f
                stage2_field_stats["stripped_inline_here_is"] += 1

        # 2A. House number or range in `surname` when `forename` has the resident name (e.g. sur='13', fore='Chappell Mrs Elizabeth')
        if re.match(r"^\d+[A-Za-z]?(?:\s*[\-&/]\s*\d+[A-Za-z]?)?$", s) and f:
            if not h:
                h = s
            elif re.match(r"^[A-Z][a-zA-Z'\-]{2,}$", h) and h.lower() not in EXCLUDE_HOUSE_SURNAME:
                # e.g. h='Capnos', s='34', f='P' -> h='34' (or drop if page number > 250), s='Capnos'
                s_val = int(re.match(r"^(\d+)", s).group(1))
                s = h
                h = str(s_val) if s_val <= 250 else ""
                stage2_field_stats["swapped_house_surname_with_num"] += 1
            if s.isdigit() or re.match(r"^\d+[A-Za-z]?(?:\s*[\-&/]\s*\d+[A-Za-z]?)?$", s):
                parts = f.split(None, 1)
                s = parts[0].strip(" ,.")
                f = parts[1].strip() if len(parts) > 1 else ""
                stage2_field_stats["realigned_num_in_surname"] += 1

        # 2B. Left-shifted unnumbered resident where `house_number` holds the Surname!
        # e.g. `#Edwards | sur='T' | fore='S' | tr='Solicitor'` or `#Beach | sur='Richd' | fore='factory hand'`
        if re.match(r"^[A-Z][a-zA-Z'\-]{2,}$", h) and h.lower() not in EXCLUDE_HOUSE_SURNAME:
            if not s:
                s = h
                h = ""
                stage2_field_stats["moved_surname_from_house_num"] += 1
            elif (
                re.match(r"^(?:[A-Z]\.?\s*){1,3}$", s)
                or s.lower().rstrip(".") in ALL_GIVEN_NAMES
                or re.match(r"^(Mrs|Miss|Rev|Dr)\b", s)
            ):
                # Check if `f` is a lowercase occupation or broken trade (`'p' | 'atelayer'`)
                if f and t and len(f) <= 2 and f.islower() and t[0].islower():
                    t = (f + t).capitalize()
                    f = s
                elif f and f[0].islower() and not t:
                    t = f.capitalize()
                    f = s
                else:
                    f = f"{s} {f}".strip()
                s = h
                h = ""
                stage2_field_stats["shifted_house_surname_with_forename"] += 1

        # 2C. Pure lowercase trade in `surname` with resident name in `forename` (e.g. sur='shoemaker', fore='Deacon H', tr='')
        if s.lower() in PURE_TRADES_LOWER and not t and f and re.match(r"^[A-Z]", f):
            t = s.capitalize()
            parts = f.split(None, 1)
            s = parts[0].strip(" ,.")
            f = parts[1].strip() if len(parts) > 1 else ""
            stage2_field_stats["swapped_pure_trade_in_surname"] += 1

        # 2D. Inverted `surname` <-> `forename` (Rules A, B, C, D)
        if s and f:
            m_tr = SUR_WITH_TRADE_PAT.match(s)
            if m_tr and re.match(r"^[A-Z][a-zA-Z'\-]{2,}$", f) and f.lower() not in NON_SURNAME_TOKENS:
                # Rule B: sur="Benj. labourer", fore="Shakesheff"
                s, f = f, m_tr.group(1).strip(" .,")
                if not t:
                    t = m_tr.group(2).capitalize()
                stage2_field_stats["uninverted_forename_with_trade_in_surname"] += 1
            elif re.match(r"^(Mrs|Miss)\s+([A-Z][a-zA-Z'\-]{2,})(?:\s+(.*))?$", f):
                # Rule C: sur="Elizabeth", fore="Mrs Stockwell"
                mt = re.match(r"^(Mrs|Miss)\s+([A-Z][a-zA-Z'\-]{2,})(?:\s+(.*))?$", f)
                cand_sur = mt.group(2)
                s_toks = [tok.rstrip(".").lower() for tok in s.split()]
                if (
                    cand_sur.lower() not in ALL_GIVEN_NAMES
                    and cand_sur.lower() not in NON_SURNAME_TOKENS
                    and (re.match(r"^(?:[A-Z]\.?\s*){1,3}$", s) or (s_toks and s_toks[0] in ALL_GIVEN_NAMES))
                ):
                    rem = mt.group(3) or ""
                    s, f = cand_sur, f"{mt.group(1)} {s} {rem}".strip()
                    stage2_field_stats["uninverted_titled_surname_in_forename"] += 1
            elif (
                re.match(r"^[A-Z][a-zA-Z'\-]{2,}$", f)
                and f.lower().rstrip(".") not in ALL_GIVEN_NAMES
                and f.lower().rstrip(".") not in NON_SURNAME_TOKENS
            ):
                # Rule A & D: `f` is a single capitalized non-given Surname, while `s` is Initials, Abbrev Forename, or Given Name
                s_toks = [tok.rstrip(".").lower() for tok in s.split()]
                if (
                    re.match(r"^(?:[A-Z]\.?\s*){1,3}$", s)
                    or (s_toks and s_toks[0] in ABBREV_FORENAMES and len(s_toks) <= 2)
                    or (s_toks and s_toks[0] in ALL_GIVEN_NAMES and len(s_toks) <= 2 and all(tk in ALL_GIVEN_NAMES or len(tk) == 1 for tk in s_toks))
                ):
                    s, f = f, s
                    stage2_field_stats["uninverted_surname_forename"] += 1

        # 2E. Empty `surname` with full `"Surname Forename, trade"` or `"Mrs Surname Forename"` or `"Surname Forename"` in `forename`
        if not s and f:
            if "," in f:
                f_name_part, f_trade_part = [p.strip() for p in f.split(",", 1)]
                if not t or t.isdigit() or "here is" in t.lower():
                    t = f_trade_part
                name_tokens = f_name_part.split(None, 1)
                s = name_tokens[0]
                f = name_tokens[1] if len(name_tokens) > 1 else ""
                stage2_field_stats["unpacked_1892_forename_trade"] += 1
            elif re.match(r"^(Mrs|Miss|Rev|Dr)\.?\s+([A-Z][a-zA-Z'\-]+)(?:\s+(.*))?$", f):
                m_title = re.match(r"^(Mrs|Miss|Rev|Dr)\.?\s+([A-Z][a-zA-Z'\-]+)(?:\s+(.*))?$", f)
                title_tok, sur_tok, rem_fore = m_title.group(1), m_title.group(2), m_title.group(3) or ""
                s = sur_tok
                f = f"{title_tok} {rem_fore}".strip()
                stage2_field_stats["extracted_titled_surname_from_forename"] += 1
            elif not b and re.match(r"^[A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z\.\s'\-]*)?$", f) and "between " not in f.lower():
                tokens = f.split()
                if len(tokens) == 1:
                    s = tokens[0]
                    f = ""
                    stage2_field_stats["restored_single_surname_from_forename"] += 1
                elif len(tokens) >= 2 and tokens[0].lower() not in {"here", "from", "left", "right", "east", "west", "north", "south", "the"}:
                    s = tokens[0]
                    f = " ".join(tokens[1:])
                    stage2_field_stats["split_surname_forename_from_forename"] += 1

        # 2F. Empty `surname` & `forename` where business/institution is in `trade`
        if not s and not f and not b and t and re.match(r"^[A-Z]", t) and t.lower() not in PURE_TRADES_LOWER:
            s = t
            t = ""
            stage2_field_stats["promoted_business_trade_to_surname"] += 1

        # 2G. Trade bleed at the end of `forename` (e.g. `fore='William. labourer'`, `fore='Frederick. rivetter'`)
        if s and f:
            m_ft = FORENAME_TRADE_SUFFIX_PAT.match(f)
            if m_ft:
                f = m_ft.group(1).strip(" ,.")
                if not t:
                    t = m_ft.group(2).capitalize()
                stage2_field_stats["extracted_trade_from_forename"] += 1

        # 2H. Unsplit `surname="Surname Forename, trade"` or `"Surname, trade"` when `forename == ""` and `trade == ""`
        if s and not f and not t and "," in s:
            s_left, s_right = [p.strip() for p in s.split(",", 1)]
            if s_right.lower().rstrip(".") in PURE_TRADES_LOWER:
                t = s_right.capitalize()
                tokens = s_left.split(None, 1)
                s = tokens[0]
                f = tokens[1] if len(tokens) > 1 else ""
                stage2_field_stats["split_surname_comma_trade"] += 1

        r["house_number"] = h
        r["building_name"] = b
        r["surname"] = s
        r["forename"] = f
        r["trade"] = t
        r["_h_int"] = parse_house_int(h)
        r["_norm_sur"] = normalize_surname(s)
        cleaned_rows.append(r)

    rows = cleaned_rows
    print("[Stage 2] Field Contamination, Column-Shift & Inversion Repairs:")
    for k, v in stage2_field_stats.most_common():
        print(f"  * {k:<44}: {v:,} records")

    # Build Cross-Year Resident Index using all newly un-inverted & shifted surnames!
    def build_resident_index(current_rows):
        res_idx = defaultdict(lambda: defaultdict(set))
        for r in current_rows:
            st = r["street"]
            st_low = st.lower()
            if PURE_HEADER_OR_LANDMARK_PATTERNS.match(st_low) or st_low in CHAMBER_TO_PARENT_STREET or st_low in DIRECT_FALSE_STREET_PARENT:
                continue
            sur = r["_norm_sur"]
            h_int = r["_h_int"]
            if sur and h_int is not None:
                res_idx[(sur, h_int)][st].add(r["year"])
        return res_idx

    resident_house_streets = build_resident_index(rows)

    # =========================================================================
    # STAGE 3: FALSE STREET RESOLUTION (ADS, MAP CODES, LANDMARKS, CHAMBERS)
    # =========================================================================
    stage3_ad_landmark_healed = 0
    stage3_chamber_healed = 0
    stage3_arcade_healed = 0

    rows_by_year = defaultdict(list)
    for r in rows:
        rows_by_year[r["year"]].append(r)

    for yr, yrows in rows_by_year.items():
        i = 0
        n = len(yrows)
        prev_valid_street = "Commercial Street"
        while i < n:
            st = yrows[i]["street"]
            st_low = st.lower().strip()

            # Case 3A: Pure Ad Banner / Map Grid Code / 3-Letter Header / School / Church / Post Office
            if PURE_HEADER_OR_LANDMARK_PATTERNS.match(st_low) or st_low in DIRECT_FALSE_STREET_PARENT:
                j = i + 1
                while j < n and yrows[j]["street"].lower().strip() == st_low:
                    j += 1
                slice_rows = yrows[i:j]
                default_st = DIRECT_FALSE_STREET_PARENT.get(st_low, prev_valid_street)
                assigned_sts = resolve_slice_by_residents(slice_rows, yr, resident_house_streets, default_st)
                for r, new_st in zip(slice_rows, assigned_sts):
                    r["street"] = new_st
                    stage3_ad_landmark_healed += 1
                prev_valid_street = assigned_sts[-1]
                i = j
                continue

            # Case 3B: Chambers / Buildings / Halls
            if st_low in CHAMBER_TO_PARENT_STREET:
                j = i + 1
                while j < n and yrows[j]["street"].lower().strip() == st_low:
                    j += 1
                slice_rows = yrows[i:j]
                parent_st, bldg_label = CHAMBER_TO_PARENT_STREET[st_low]
                assigned_sts = resolve_slice_by_residents(slice_rows, yr, resident_house_streets, parent_st)

                still_in_chamber = True
                for idx_in_slice, (r, new_st) in enumerate(zip(slice_rows, assigned_sts)):
                    h_int = r["_h_int"]
                    if st_low == "brown's buildings" and h_int is not None and h_int > 10:
                        still_in_chamber = False
                    elif st_low == "austin friars chambers" and h_int is not None and h_int >= 27:
                        still_in_chamber = False
                    elif idx_in_slice > 0 and h_int is not None and h_int > 20 and "chambers" in st_low:
                        still_in_chamber = False

                    r["street"] = new_st if not still_in_chamber else parent_st
                    if still_in_chamber and bldg_label:
                        if not r["building_name"]:
                            r["building_name"] = bldg_label
                        elif bldg_label.lower() not in r["building_name"].lower():
                            r["building_name"] = f"{bldg_label} ({r['building_name']})"
                    stage3_chamber_healed += 1
                prev_valid_street = slice_rows[-1]["street"]
                i = j
                continue

            # Case 3C: The Newport Arcade / New Arcade
            if st_low in ("the newport arcade", "new arcade"):
                j = i + 1
                while j < n and yrows[j]["street"].lower().strip() == st_low:
                    j += 1
                slice_rows = yrows[i:j]
                bled_to_high_st = False
                for r in slice_rows:
                    h_int = r["_h_int"]
                    sur_low = (r["surname"] + " " + r["building_name"]).lower()
                    if (h_int is not None and h_int >= 44) or any(
                        kw in sur_low for kw in ("greyhound", "newport castle", "highbury chambers", "fennell", "dobell")
                    ):
                        bled_to_high_st = True
                    if bled_to_high_st:
                        r["street"] = "High Street"
                    else:
                        r["street"] = "Newport Arcade"
                    stage3_arcade_healed += 1
                prev_valid_street = slice_rows[-1]["street"]
                i = j
                continue

            prev_valid_street = st
            i += 1

    print(
        f"[Stage 3] Resolved False Streets: {stage3_ad_landmark_healed:,} ad/landmark/grid records, "
        f"{stage3_chamber_healed:,} chamber/building records, {stage3_arcade_healed:,} arcade/High St records."
    )

    # Rebuild Resident Index after Stage 3
    resident_house_streets = build_resident_index(rows)

    # =========================================================================
    # STAGE 4: CONTIGUOUS CROSS-STREET BLEED SPLICING
    # =========================================================================
    stage4_spliced_blocks = 0
    stage4_spliced_records = 0

    street_year_rows = defaultdict(lambda: defaultdict(list))
    for r in rows:
        street_year_rows[r["street"]][r["year"]].append(r)

    # Compute historical house number ceiling per street
    street_ceilings = {}
    for st, yr_map in street_year_rows.items():
        annual_maxes = []
        for yr, rlist in yr_map.items():
            nums = sorted(r["_h_int"] for r in rlist if r["_h_int"] is not None)
            if len(nums) >= 3:
                annual_maxes.append(nums[-1])
        if len(annual_maxes) >= 3:
            annual_maxes.sort()
            med = statistics.median(annual_maxes)
            p80 = annual_maxes[min(len(annual_maxes) - 1, int(len(annual_maxes) * 0.80))]
            street_ceilings[st] = max(med * 1.25, p80 * 1.15, med + 15)

    for st, yr_map in list(street_year_rows.items()):
        st_ceil = street_ceilings.get(st, 9999)
        for yr, rlist in list(yr_map.items()):
            n = len(rlist)
            if n < 5:
                continue

            row_top_attr = []
            row_cand_sets = []
            for r in rlist:
                key = (r["_norm_sur"], r["_h_int"])
                matched_top = None
                cand_set = set()
                if key[0] and key[1] is not None and key in resident_house_streets:
                    st_map = resident_house_streets[key]
                    other_yrs_on_st = st_map.get(st, set()) - {yr}
                    is_outlier_on_st = r["_h_int"] > st_ceil
                    candidates = []
                    for ost, oyrs in st_map.items():
                        if ost == st or ost.lower() == st.lower():
                            continue
                        ost_cnt = len(oyrs - {yr})
                        if ost_cnt == 0:
                            continue
                        # Valid candidate if host street has 0 other years, OR row is an upper-bound outlier on host street,
                        # OR candidate street has at least 3x as many other years as host street!
                        if (
                            not other_yrs_on_st
                            or (is_outlier_on_st and r["_h_int"] <= street_ceilings.get(ost, 9999))
                            or ost_cnt >= max(2, len(other_yrs_on_st) * 3)
                        ):
                            candidates.append((ost, ost_cnt))
                            cand_set.add(ost)
                    if candidates:
                        candidates.sort(key=lambda x: -x[1])
                        matched_top = candidates[0][0]
                row_top_attr.append(matched_top)
                row_cand_sets.append(cand_set)

            i = 0
            while i < n:
                target_st = row_top_attr[i]
                if not target_st:
                    i += 1
                    continue
                j = i + 1
                match_count = 1
                gap = 0
                while j < n:
                    if target_st in row_cand_sets[j]:
                        match_count += 1
                        gap = 0
                        j += 1
                    else:
                        key_j = (rlist[j]["_norm_sur"], rlist[j]["_h_int"])
                        is_outlier_j = rlist[j]["_h_int"] is not None and rlist[j]["_h_int"] > st_ceil
                        host_other_cnt = (
                            len(resident_house_streets[key_j].get(st, set()) - {yr})
                            if (key_j[0] and key_j[1] is not None and key_j in resident_house_streets)
                            else 0
                        )
                        if host_other_cnt > 0 and not is_outlier_j:
                            break
                        max_allowed_gap = 10 if (rlist[j]["_h_int"] is None or is_outlier_j) else 4
                        if gap < max_allowed_gap:
                            gap += 1
                            j += 1
                        else:
                            break
                while j > i and target_st not in row_cand_sets[j - 1]:
                    j -= 1

                if match_count >= 5 and target_st != st:
                    start_idx = i
                    end_idx = j
                    while start_idx > 0:
                        prev_r = rlist[start_idx - 1]
                        curr_r = rlist[start_idx]
                        key_p = (prev_r["_norm_sur"], prev_r["_h_int"])
                        is_out_p = prev_r["_h_int"] is not None and prev_r["_h_int"] > st_ceil
                        if (
                            not is_out_p
                            and key_p[0]
                            and key_p[1] is not None
                            and key_p in resident_house_streets
                            and (resident_house_streets[key_p].get(st, set()) - {yr})
                        ):
                            break
                        if prev_r["_h_int"] is not None and curr_r["_h_int"] is not None:
                            if 0 <= abs(curr_r["_h_int"] - prev_r["_h_int"]) <= 4:
                                start_idx -= 1
                                continue
                        break
                    while end_idx < n:
                        next_r = rlist[end_idx]
                        prev_r = rlist[end_idx - 1]
                        key_n = (next_r["_norm_sur"], next_r["_h_int"])
                        is_out_n = next_r["_h_int"] is not None and next_r["_h_int"] > st_ceil
                        if (
                            not is_out_n
                            and key_n[0]
                            and key_n[1] is not None
                            and key_n in resident_house_streets
                            and (resident_house_streets[key_n].get(st, set()) - {yr})
                        ):
                            break
                        if next_r["_h_int"] is not None and prev_r["_h_int"] is not None:
                            if 0 <= abs(next_r["_h_int"] - prev_r["_h_int"]) <= 4:
                                end_idx += 1
                                continue
                        break

                    for k in range(start_idx, end_idx):
                        rlist[k]["street"] = target_st
                        stage4_spliced_records += 1
                    stage4_spliced_blocks += 1
                    i = end_idx
                else:
                    i = max(i + 1, j)

    print(
        f"[Stage 4] Spliced {stage4_spliced_blocks:,} high-confidence contiguous cross-street bleed blocks "
        f"({stage4_spliced_records:,} resident records restored to their true streets)."
    )

    # Clean isolated 3-digit directory page numbers (> 300) stuck in house_number on short streets (ceiling <= 100)
    stripped_page_nums = 0
    for r in rows:
        st_c = street_ceilings.get(r["street"], 9999)
        hi = r["_h_int"]
        if hi is not None and hi >= 300 and st_c <= 150:
            key = (r["_norm_sur"], hi)
            if not (key[0] and key in resident_house_streets and len(resident_house_streets[key]) > 1):
                r["house_number"] = ""
                r["_h_int"] = None
                stripped_page_nums += 1
    if stripped_page_nums:
        print(f"[Stage 4b] Stripped {stripped_page_nums:,} isolated directory page numbers (>= 300) from house_number on short streets.")

    out_fields = [fn for fn in fieldnames if not fn.startswith("_")]
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows):,} healed records to {DATA_CSV}.")


if __name__ == "__main__":
    main()
