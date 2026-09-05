import csv
import json
import os
import re
from collections import defaultdict

INPUT_CSV = "data.csv"
OUTPUT_CSV = "data.csv"
EDGE_CASES_FILE = "edge_cases.json"

# Load Edge Cases Configuration
EDGE_CASES_FILE = "edge_cases.json"
EDGE_CASES = []
if os.path.exists(EDGE_CASES_FILE):
    with open(EDGE_CASES_FILE, "r", encoding="utf-8") as ef:
        try:
            EDGE_CASES = json.load(ef).get("overrides", [])
            print(f"Loaded {len(EDGE_CASES)} historical edge cases from {EDGE_CASES_FILE}")
        except Exception as e:
            print(f"Warning: Could not load {EDGE_CASES_FILE}: {e}")

# Load Master Streets Registry & Locked Streets
MASTER_STREETS_FILE = "master_streets.json"
MASTER_STREETS = {}
LOCKED_SLUGS = set()
if os.path.exists(MASTER_STREETS_FILE):
    with open(MASTER_STREETS_FILE, "r", encoding="utf-8") as mf:
        try:
            m_data = json.load(mf).get("streets", {})
            MASTER_STREETS = m_data
            for slug, info in m_data.items():
                status = info.get("audit_status") or info.get("audit", {}).get("status")
                if status in ["VERIFIED", "NAME_VERIFIED", "FULLY_ENRICHED"]:
                    LOCKED_SLUGS.add(slug)
            print(f"Loaded {len(MASTER_STREETS)} master streets ({len(LOCKED_SLUGS)} verified & locked).")
        except Exception as e:
            print(f"Warning: Could not load {MASTER_STREETS_FILE}: {e}")

# Dictionary of standard street suffix expansions
ABBREVIATIONS = {
    r"\bRd\b\.?": "Road",
    r"\bSt\b\.?$": "Street",
    r"\bAve\b\.?": "Avenue",
    r"\bTer\b\.?": "Terrace",
    r"\bPl\b\.?": "Place",
    r"\bSq\b\.?": "Square",
    r"\bCres\b\.?": "Crescent",
    r"\bPde\b\.?": "Parade",
    r"\bGdns\b\.?": "Gardens",
}

HEADER_SURNAMES = {"butcher's", "thompson's", "johns'", "johns's", "directory"}

CROSS_STREET_REGEX = re.compile(
    r'\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.)\b.*?\bto\b.*?\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.|square)\b'
    r'|^\s*\[?(?:here\s+are|here\s+is|here\s+cross|\[?return\]?|\(return\.?\)|return\.?)\]?\b'
    r'|^\s*[\(\[]?\s*return\.?\s*[\)\]]?\s*$'
    r'|\bsee\b'
    r'|\bsee\s+also\b'
    r'|\b[a-zA-Z]+see\b'
    r'|^\s*now\s+[a-z0-9\s\.\-\(\)]+'
    r'|^\s*(?:maindee|newport|pill)from\b'
    r'|^\s*from\s+[A-Za-z\s]+'
    r'|^\s*[A-Za-z\s]+street\s+from\b'
    r'|^\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s*(?:side)?\s*[\)\]]?\s*$'
    r'|^\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s+side\b'
    r'|^\s*(?:from\s+)?[a-z0-9\s\.\-]+\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s*[\)\]]?\s*(?:opposite\s+[a-z0-9\s\.\-]+)?\s*$'
    r'|^\s*opposite\s+(?:maindee\s+schools|board\s+schools|st\.\s*woolos\s+church|malpas\s+school|kensington\s+place|stow\s+park|stow-park)'
    r'|^\s*last\s+corporation[\s\-]*road\s+street\s+on\s+left[\s\-]+hand\s+side'
    r'|^\s*(?:west|east|north|south)\s+side\s+of\b'
    r'|\bcontinuation\b'
    r'|\btowards\b'
    r'|\bderives\s+its\s+name\s+from\s+the\s+well\b'
    r'|\biron\s+ring\s+let\s+into\s+the\s+pavement\b'
    r'|\bembraces\s+the\s+numerous\s+streets\b'
    r'|\bis\s+a\s+district\s+lying\s+between\b'
    r'|\bcommonly\s+called\s+pill\b'
    r'|^\s*(?:newport\s*)?bottom\s+of\b'
    r'|\boff\s+[a-z0-9\s\.\-]+(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.|square|estate)\b'
    r'|^\s*(?:west|east|north|south)\s+side\s+of\b'
    r'|\bcontinuation\b',
    re.I
)

LAYOUT_ONLY_REGEX = re.compile(
    r'^\s*(?:left|right|east|west|north|south)\s+side\b'
    r'|^\s*\(?no\s+thoroughfare\.?\)?\s*$'
    r'|^\s*map\s+[a-z]\s*\d+\.?\s*$'
    r'|^\s*map\s+[a-z]\d+\.?\s*$'
    r'|^\s*from\s+\d+\s+.*'
    r'|^\s*from\s+\d*\s*\b(?:rowan|melbourne|monnon|road|way|street|lane|place|drive|crescent|cres|av|ave|avenue)\b.*'
    r'|^\s*(?:its|ts)\s+junction\s+.*'
    r'|^\s*\(?junior\s+mixed\s+&\s+infants\)?\s*$'
    r'|^\s*fants\b\s*$'
    r'|^\s*mixed\s+&\s+infants\b\s*$'
    r'|^\s*primary\s+school\s+\(?junior\b'
    r'|^\s*\(junior\s*$'
    r'|^\s*\(?no\s+thoroughfare\)?\s*$'
    r'|^\s*vancouver\s+drive\s*\.?\s*map\s+[a-z]\d+\s*$'
    r'|^\s*here\s+(?:is|are)\b.*'
    r'|^\s*opposite\s+\b.*',
    re.I
)

LAYOUT_STRIP_REGEX = re.compile(
    r'\b(?:left|right)\s+side\b'
    r'|\bno\s+thoroughfare\b'
    r'|\bmap\s+[a-z]\s*\d+\b'
    r'|\bmap\s+[a-z]\d+\b'
    r'|\bfrom\s+\d*\s*\b(?:rowan|melbourne|monnon|road|way|street|lane|place|drive|crescent|cres|av|ave|avenue)\b\.?'
    r'|\b(?:its|ts)\s+junction\s+with\b\.?'
    r'|\b(?:its|ts)\s+junction\s+[A-Za-z0-9\s]+\b'
    r'|\bvancouver\s+drive\b',
    re.I
)


# Trade keywords to identify trade bleeding into forename
TRADE_KEYWORDS = [
    "mechanic", "clerk", "grocer", "mariner", "driver", "fitter", "carpenter",
    "platelayer", "labourer", "shoemaker", "draper", "baker", "mason", "rigger",
    "tailor", "painter", "smith", "builder", "haulier", "fireman", "guard",
    "boot", "joiner", "dealer", "assistant", "manager", "visitor", "shipper",
    "plasterer", "sail", "engineer", "inspector", "agent", "blacksmith",
    "ironworker", "steelworker", "trimmer", "pilot", "master", "brewer",
    "porter", "clerk", "nurse", "telegraph", "engine", "collector", "station",
    "booksellers", "stationers", "auctioneer", "dressmaker", "gardener",
    "milliner", "wine", "cabinet maker", "professor", "sorter"
]

# Trade normalization mappings to clean up typos, spacing variations, and abbreviations
TRADE_TYPO_MAP = {
    'accountnt': 'accountant', 'shopkeepr': 'shopkeeper', 'seamaqn': 'seaman',
    'glassblwr': 'glass blower', 'mouldr': 'moulder', 'agnt': 'agent',
    'stevedr': 'stevedore', 'plastrer': 'plasterer', 'sadler': 'saddler',
    'electician': 'electrician', 'furnceman': 'furnaceman', 'boilrmkr': 'boilermaker',
    'boilr mkr': 'boilermaker', 'joinr': 'joiner', 'photogrphr': 'photographer',
    'mechnc': 'mechanic', 'machinst': 'machinist', 'brklayer': 'bricklayer',
    'boor repairer': 'boot repairer', 'buildr': 'builder', 'coal merchnt': 'coal merchant',
    'dock wrkr': 'dock worker', 'warehseman': 'warehouseman', 'warehsemn': 'warehouseman',
    'warehousem': 'warehouseman', 'foremaqn': 'foreman', 'grocrs': 'grocers',
    'iron workr': 'iron worker', 'confectnrs': 'confectioners', 'sailmakr': 'sailmaker',
    'sailmkr': 'sailmaker', 'confectionr': 'confectioner', 'inspectr': 'inspector',
    'caretakr': 'caretaker', 'upholster': 'upholsterer', 'hailier': 'haulier',
    'shunterr': 'shunter', 'paintetr': 'painter', 'draughtsmn': 'draughtsman',
    'dairym': 'dairyman', 'dairymen': 'dairyman', 'solictrs': 'solicitors',

    # User additions:
    'carpntr': 'carpenter',
    'furnacemn': 'furnaceman',
    'furnaceman': 'furnaceman',
    'wiredrawr': 'wiredrawer',
    'salesmn': 'salesman',
    'machst': 'machinist',
    'greengrcr': 'greengrocer',
    'butchr': 'butcher',
    'hairdsr': 'hairdresser',
    'shipwgt': 'shipwright',
    'plumbr': 'plumber',
    'fnceman': 'financeman',
    'blrmkr': 'boilermaker',
    'schoolmstr': 'schoolmaster',
    'shopkpr': 'shopkeeper',
    'foremn': 'foreman',
    'shipwght': 'shipwright',
    'furncmn': 'furnaceman',
    'chauffr': 'chauffeur',
    'firemn': 'fireman',
    'acctnt': 'accountant',
    'wheelwght': 'wheelwright',
    'dairymn': 'dairyman',
    'newsagnt': 'newsagent',
    'decrtr': 'decorator',
    'slsman': 'salesman',
    'electricn': 'electrician',
    'hairdrssr': 'hairdresser',
    'electrcn': 'electrician',
    'haulr': 'haulier',
    'dressmkr': 'dressmaker',
    'patternmkr': 'patternmaker',
    'weighmn': 'weighman',
    'plbr': 'plumber',
    'fruitr': 'fruiterer',
    'whsmn': 'warehouseman',
    'schlmaster': 'schoolmaster',
    'dcrtr': 'decorator',
    'blrmaker': 'boilermaker',
    'watchmn': 'watchman',
    'trimmr': 'trimmer',
    'crane drivr': 'crane driver',
    'eng. drivr': 'engine driver',
    'platelayr': 'platelayer',
    'plastr': 'plasterer',
    'managr': 'manager',
    'stockbrkr': 'stockbroker',
    'gaswrkr': 'gasworker',
    'whseman': 'warehouseman',
    'dectr': 'decorator',
    'newsagt': 'newsagent',
    'travllr': 'traveller',
    'cranedrvr': 'crane driver',

    # Second list additions:
    'wheeleright': 'wheelwright',
    'master marnr': 'master mariner',
    'ironfdr': 'ironfoundry',
    'pattern makrs': 'patternmakers',
    'laundrs': 'launderers',
    'brushmakr': 'brushmaker',
    'bootdlr': 'bootdealer',
    'cabintmkr': 'cabinetmaker',
    'fu\'nsher': 'furnisher',
    'ourveyor': 'purveyor',
    'ploice': 'police',
    'berthing mas': 'berthing master',
    'insp. of works': 'inspector of works',
    'engne driver': 'engine driver',
    'travllng. draper': 'travelling draper',
    'ironmngr': 'ironmonger',
    'confect\'ner': 'confectioner',
    'railwaym': 'railwayman',
    'sculpt': 'sculptor',
    'stlwk': 'steelworker',
    'clerl': 'clerk',
    'blmaker': 'boilermaker',
    'hairdrsr': 'hairdresser',
    'boilermakr': 'boilermaker',
    'shipcarpenter': 'ship carpenter',
    ']sr. cooper': 'senior cooper',
    'ex-police insp': 'ex-police inspector',
    'dockwrkr': 'dockworker',
    'eng\'eer': 'engineer',
    'dectrs': 'decorators',
    'foundrymn': 'foundryman',
    'warehoman': 'warehouseman',
    'wagon repr': 'wagon repairer',
    'wiredrwr': 'wiredrawer',
    'laqbr': 'labourer',
}

TRADE_EXACT_MAP = {
    'iron worker': 'ironworker', 'ironworker': 'ironworker', 'steel worker': 'steelworker',
    'steelworker': 'steelworker', 'boiler maker': 'boilermaker', 'boilermaker': 'boilermaker',
    'plate layer': 'platelayer', 'platelayer': 'platelayer', 'brick layer': 'bricklayer',
    'bricklayer': 'bricklayer', 'boot maker': 'bootmaker', 'bootmaker': 'bootmaker',
    'hair dresser': 'hairdresser', 'hairdresser': 'hairdresser', 'black smith': 'blacksmith',
    'blacksmith': 'blacksmith', 'gasworker': 'gasworker', 'ship wright': 'shipwright',
    'shipwright': 'shipwright', 'furnace man': 'furnaceman', 'furnaceman': 'furnaceman',
    'dairy man': 'dairyman', 'dairyman': 'dairyman', 'shop keeper': 'shopkeeper',
    'shopkeeper': 'shopkeeper',

    # User additions:
    'gas worker': 'gasworker',
    'stl worker': 'steelworker',
    'st worker': 'steelworker',
    'pattern maker': 'patternmaker',
    'lathrender': 'lath render',

    # Second list additions:
    'boot dlrs': 'bootdealers',
    'shio carpenter': 'ship carpenter',
    'cabinetmkr': 'cabinetmaker',
    'cabinet mkr': 'cabinetmaker',
    'cabinet maker': 'cabinetmaker',
    'pattern makers': 'patternmakers',
    'master mariner': 'master mariner',
    'dockworker': 'dockworker'
}

TRADE_ABBREV_MAP = {
    'labr': 'labourer', 'lbr': 'labourer', 'laBR': 'labourer', 'ironwkr': 'ironworker',
    'iron wkr': 'ironworker', 'steelwkr': 'steelworker', 'steel wkr': 'steelworker',
    'clk': 'clerk', 'ptr': 'painter', 'dvr': 'driver', 'trm': 'trimmer',
    'car drvr': 'car driver', 'mtr drvr': 'motor driver', 'mtr dvr': 'motor driver',
    'lry dvr': 'lorry driver', 'lorry drv': 'lorry driver', 'dk. labourer': 'dock labourer',
    'dock labr': 'dock labourer', 'dock lbr': 'dock labourer', 'civ servant': 'civil servant',
    'civil srvt': 'civil servant', 'cargo wk': 'cargo worker', 'cargo wkr': 'cargo worker',
    'gen shp': 'general shop', 'gen shop': 'general shop',

    # User additions:
    'eng driver': 'engine driver',
    'eng. drvr': 'engine driver',
    'eng drvr': 'engine driver',
    'eng. driver': 'engine driver',
    'warehsman': 'warehouseman',
    'warehsmn': 'warehouseman',
    'warehousemn': 'warehouseman',
    'irn worker': 'ironworker',
    'iworker': 'ironworker',
    'ironwk': 'ironworker',
    'ironwr': 'ironworker',
    'iron wrkr': 'ironworker',
    'i\'worker': 'ironworker',
    'irnwr': 'ironworker',
    'dk labourer': 'dock labourer',
    'dk lab': 'dock labourer',
    'dk pilot': 'dock pilot',
    'tram drvr': 'tram driver',
    'motor mec': 'motor mechanic',
    'motor eng': 'motor engineer',
    'boot rpr': 'boot repairer',
    'trnspt worker': 'transport worker',
    'dckr': 'docker',
    'dockr': 'docker',
    'bus condctr': 'bus conductor',
    'steelwr': 'steelworker',
    'stworker': 'steelworker',
    'furniture dlr': 'furniture dealer',
    'motor dv': 'motor driver',
    'dk worker': 'dock worker',
    'dck worker': 'dock worker',
    'transpt worker': 'transport worker',
    'cargo wrkr': 'cargo worker',
    'grocer\'s asst': 'grocer\'s assistant',
    'mec': 'mechanic',
    'trans worker': 'transport worker',
    'lino optr': 'linotype operator',
    'rivet mkr': 'rivet maker',
    'ship stwd': 'ship steward',
    'coach bldr': 'coach builder',
    'conf': 'confectioner',
    'van drvr': 'van driver',
    'fitters hlp': 'fitters helper',
    'fitter\'s hlp': 'fitter\'s helper',
    'chimney swp': 'chimney sweep',
    'coal merc': 'coal merchant',
    'corn mcht': 'corn merchant',
    'cycle dlr': 'cycle dealer',
    'genrl shop': 'general shop',
    'bus drvr': 'bus driver',
    'park attdt': 'park attendant',

    # Second list additions:
    'rly. porter': 'railway porter',
    'pilots assist': 'pilot\'s assistant',
    'firewood yd': 'firewood yard',
    'jun. fireman': 'junior fireman',
    'train exmr': 'train examiner',
    'jno. clerk': 'junior clerk',
    'railway. porter': 'railway porter',
    'ship carp': 'ship carpenter',
    'spirit merchant, wine': 'wine and spirit merchant',
    'surg. assistant': 'surgeon\'s assistant',
    'junr. scale maker': 'junior scale maker',
    'pork bt': 'pork butcher',
    'cab proptr': 'cab proprietor',
    'bottle blwr': 'bottle blower',
    'wire drwr': 'wire drawer',
    'helve': 'helve maker',
    'baker,, etc': 'barker, etc',
    'coal tr': 'coal trimmer',
    'com trav': 'commercial traveller',
    'com. trav': 'commercial traveller',
    'insur manager': 'insurance manager',
    'fitters\' hlp': 'fitters\' helper',
    'grcr asst': 'grocer\'s assistant',
    'painter & dectr': 'painter and decorator',
    'chem wrkr': 'chemical worker',
    'com agent': 'commercial agent',
    'fitter\'s mate': 'fitters\' mate',
    'window clnr': 'window cleaner',
}

BUSINESS_SUFFIX_REGEX = re.compile(
    r"^(?:&|and|ltd|limited|co\.?|company|sons|bros|brothers|school|academy|place\s+school|house|depot|works|chambers|stores|hotel|inn|arms|vaults)\b",
    re.I
)

INSTITUTION_WORD = re.compile(
    r"^(?:chapel|church|office|association|board office|houses|seminary|school|infirmary|hospital|bank|association offices|society|works|depot|hall|chambers)\b",
    re.I
)

VILLA_WORD = re.compile(
    r"\b([A-Z][a-zA-Z\s'\-]+?\b(?:villa|cottage|house|inn|arms|hotel|chambers|lodge|court|hall|chapel))\b",
    re.I
)

NON_PERSON_WORDS = ['wagon', 'coal', 'iron', 'colliery', 'docks', 'railway', 'supply', 'stores', 'drapery']

COMPANY_SUFFIX_TRADE_REGEX = re.compile(r'^\s*(ltd\.?|limited|co\.?|& co\.?|co\.? ltd\.?|ld\.?)\s*$', re.I)

PAT_NAME_TRADE = re.compile(
    r'^([A-Z][a-zA-Z\x27\-]+),\s+([A-Z][a-zA-Z\.\s\x27\-]+?)(?:(?:\s*[\-\x97\u2013\u2014]\s*|\s*,\s*)(.*))?$'
)

PAT_FULL_CORONATION = re.compile(
    r'^(?:([A-Z][a-zA-Z\x27\-]+),\s+)?([A-Z][a-zA-Z\.\s\x27\-]*?)\s*[\-,]\s*(steward|manager|secretary|caretaker|curator|matron|superintendent|keeper|clerk|agent|collector|officer|warden|headmaster|headmistress|master|teacher|governor|attendant|proprietor|propr)\s*,\s*(.*)$',
    re.I
)

PAT_TRADE_INST = re.compile(
    r'^(steward|manager|secretary|caretaker|curator|matron|superintendent|keeper|clerk|agent|collector|officer|warden|headmaster|headmistress|master|teacher|governor|attendant|proprietor|propr)\s*,\s*(.*)$',
    re.I
)

PAT_TRADE_VILLA = re.compile(
    r'^([a-zA-Z\s\(\)\/\&\x27\-]+?)\.?\s*[\-,]\s*([A-Z][a-zA-Z\s\x27\-]+)$'
)

VILLA_WORDS = {
    'villa', 'cottage', 'house', 'inn', 'arms', 'hotel', 'chambers', 'lodge', 'court',
    'hall', 'chapel', 'bank', 'nook', 'grove', 'oaks', 'limes', 'firs', 'laurels',
    'knoll', 'bungalow', 'ferns', 'gables', 'mount', 'view', 'haven', 'lawn', 'dingle',
    'burn', 'park', 'croft', 'springfield', 'denbury', 'harlesden', 'font burn',
    'greencroft', 'rose cottage', 'le quatre saisons', 'villas', 'cottages'
}

NON_VILLA_WORDS = {
    'journeyman', 'docks', 'works', 'depot', 'stores', 'factory', 'company', 'office',
    'railway', 'gwr', 'ltd', 'limited', 'co', 'bros', 'sons', 'dept', 'station', 'co-op',
    'association', 'society', 'hospital', 'asylum', 'infirmary', 'school', 'schools',
    'quay', 'wharf', 'dock', 'yard', 'mills', 'foundry', 'brewery'
}

def is_trade_word(text):
    if not text:
        return False
    t_low = text.lower().strip(' ,.-')
    words = [w.strip(' ,.-') for w in t_low.split()]
    
    known_trade_parts = {
        'fitter', 'wiredrawer', 'secretary', 'accountant', 'cranedriver', 'supervisor',
        'joiner', 'clerk', 'painter', 'builder', 'driver', 'grocer', 'draper', 'mason',
        'baker', 'tailor', 'agent', 'manager', 'salesman', 'postman', 'seaman', 'docker',
        'butcher', 'traveller', 'foreman', 'electrician', 'plumber', 'machinist',
        'decorator', 'confectioner', 'shunter', 'moulder', 'printer', 'coal merchant',
        'warehouseman', 'signalman', 'general shop', 'fruiterer', 'checker', 'teacher',
        'chauffeur', 'roller', 'steward', 'laundress', 'police', 'dvr', 'srvnt', 'srvt',
        'clk', 'ptr', 'trm', 'labourer', 'labr', 'lbr', 'eng', 'drvr', 'pilot', 'porter'
    }
    
    for w in words:
        if w in TRADE_TYPO_MAP or w in TRADE_EXACT_MAP or w in TRADE_ABBREV_MAP or w in known_trade_parts or w in TRADE_KEYWORDS:
            return True
            
    if t_low in TRADE_TYPO_MAP or t_low in TRADE_EXACT_MAP or t_low in TRADE_ABBREV_MAP:
        return True
    return any(kw in t_low for kw in TRADE_KEYWORDS) or any(kw in t_low for kw in known_trade_parts)

BUILDING_NAME_TRADE_REGEX = re.compile(
    r'^\s*The\s+(?:Laurels|Firs|Knoll|Bungalow|Ferns|Nook|Grove|Oaks|Limes|Retreat|Woodlands|Mount|Hollies|Dell|Grange|Dingle|Beeches|Croft|Gables|Haven|Egg Market|Lawn|Poplars|Elms|Cedars|Willows|Pines|Vicarage|Rectory)\b',
    re.I
)

HOUSE_SUFX = re.compile(r'\b(?:villa|cottage|house|lodge|gables|mount|view|haven|knoll|lawn|dingle|house|home|place|court|hall|chambers)\b', re.I)

TITLES_AND_FORENAMES = {
    'mrs', 'mrs.', 'mr', 'mr.', 'miss', 'miss.', 'ms', 'dr', 'dr.', 'rev', 'rev.',
    'thos', 'thos.', 'jas', 'jas.', 'wm', 'wm.', 'john', 'geo', 'geo.', 'chas', 'chas.',
    'hy', 'hy.', 'richd', 'richd.', 'saml', 'saml.', 'robte', 'robt', 'robt.', 'harry',
    'ernest', 'fredk', 'fredk.', 'arthur', 'edwd', 'edwd.', 'edw', 'edw.', 'walt', 'walt.',
    'walter', 'david', 'danl', 'danl.', 'benj', 'benj.', 'stepn', 'stepn.',
    'iss e', 'mrs l', 'mrs elizabeth', 'mrs mizth', 'mrs nizth', 'mrs nizth.', 'mrs Elizth',
    'thos j', 'wm g', 'wm a', 'wm h', 'wm j', 'wm henry', 'john h', 'miss e', 'miss m',
    'mrs a', 'mrs e', 'mrs j', 'mrs m', 'mrs s', 'mrs ma', 'mrs lr', 'mrs af', 'mrs ee',
    'mrs mw', 'mrs fl', 'mrs ca', 'mrs gm', 'mrs ja', 'mrs maw', 'mrs gh', 'mrs aj',
    'mrs tj', 'mrs se', 'mrs hd', 'mrs mr', 'mrs hm', 'mrs mn', 'mrs ef', 'mrs ga',
    'mrs gw', 'mrs hl', 'mrs lf', 'mrs wm', 'mrs eb', 'mrs sm', 'mrs kl', 'mrs ad',
    'mrs lv', 'mrs mh', 'mrs aod', 'mrs ag', 'mrs eh', 'mrs sj', 'mrs dg', 'mrs wt',
    'mrs og', 'mrs js', 'mrs hw', 'mrs jw', 'mrs ms', 'mrs la', 'mrs tw', 'mrs ep',
    'mrs rh', 'mrs cd', 'mrs gf', 'mrs ew', 'mrs hg', 'mrs ee', 'mrs ft', 'mrs tg',
    'mrs hh', 'mrs we', 'mrs mg', 'mrs kc', 'mrs ke', 'mrs as', 'mrs te', 'mrs ec',
    'mrs be', 'mrs wa', 'miss ey', 'miss fl', 'miss emily e', 'miss s', 'miss i',
    'miss he', 'miss cj', 'miss lh', 'miss am', 'miss mab', 'miss ellen e', 'miss w',
    'miss gh', 'miss ei', 'miss mary o', 'miss phys', 'miss p', 'miss vm', 'miss ha',
    'miss dw', 'miss re', 'miss rem', 'miss fa', 'miss mb', 'miss ae', 'miss t',
    'miss eh', 'miss o', 'tom',
    'henry', 'joseph', 'albert', 'reginald', 'harold', 'william', 'thomas', 'james', 'george',
    'charles', 'frederick', 'fred', 'fredk', 'arthur', 'edward', 'edwd', 'edw', 'edwin',
    'walter', 'walt', 'david', 'daniel', 'danl', 'benjamin', 'benj', 'stephen', 'stepn',
    'robert', 'robt', 'robte', 'richard', 'richd', 'samuel', 'saml', 'harry', 'ernest',
    'alfred', 'alf', 'percy', 'herbert', 'hbt', 'sidney', 'sydney', 'leslie', 'norman',
    'stanley', 'victor', 'lewis', 'frank', 'clifford', 'cecil', 'horace', 'edgar', 'bernard',
    'leonard', 'raymond', 'gilbert', 'douglas', 'rowland', 'roland', 'arnold', 'reuben',
    'oscar', 'gordon', 'clarence', 'maurice', 'godfrey', 'hubert', 'wilfred', 'lionel',
    'perceval', 'percival', 'bertram', 'archibald', 'arch', 'montague', 'clement', 'hector',
    'algernon', 'basil', 'rupert', 'clive', 'evelyn', 'vivian', 'dennis', 'denys', 'eric',
    'ivor', 'trevor', 'brian', 'owen', 'john', 'jack', 'tom', 'jim', 'bill', 'bob', 'dick',
    'joe', 'bert', 'ted', 'charlie', 'willie', 'sammie', 'ben', 'dan', 'dave', 'sam',
    'freddie', 'archie', 'albie', 'ernie', 'alec', 'alander', 'alexander', 'abraham', 'abra',
    'alonsa', 'alonzo', 'ambrose', 'amur', 'anew', 'angus', 'anselm', 'anthony', 'antonio',
    'augustus', 'august', 'barnaby', 'bartholomew', 'benedic', 'benedict', 'bertrand', 'caleb',
    'mary', 'elizabeth', 'eliza', 'elizth', 'sarah', 'ann', 'anne', 'annie', 'jane',
    'florence', 'alice', 'edith', 'ellen', 'mabel', 'ethel', 'kate', 'clara', 'emily',
    'rose', 'maud', 'maude', 'ada', 'margaret', 'martha', 'hannah', 'caroline', 'grace',
    'violet', 'beatrice', 'daisy', 'amy', 'lilian', 'lily', 'linda', 'gladys', 'winifred',
    'dorothy', 'marjory', 'marjorie', 'ivy', 'phoebe', 'nora', 'norah', 'olive', 'dora',
    'hilda', 'elsie', 'may', 'marian', 'marion', 'eva', 'phyllis', 'gwladys', 'gwendoline',
    'gwen', 'megan', 'rhoda', 'celia', 'ruth', 'rachel', 'esther', 'naomi', 'leah', 'agnes',
    'harriet', 'harriett', 'frances', 'charlotte', 'louisa', 'louise', 'marianne', 'miriam',
    'selina', 'priscilla', 'susannah', 'susan', 'susie', 'maggie', 'katie', 'minnie',
    'jessie', 'bessie', 'nellie', 'flossie', 'lottie', 'tillie', 'dolly', 'winnie'
}

SINGLE_INITIALS = {'w', 'j', 'wh', 'h', 'jh', 'a', 'wj', 'e', 'ae', 't', 'r', 'we', 'aj', 'ej', 'hj', 'gh', 'jw', 'aw', 'fw', 'c', 'th', 'g', 'dj', 'he', 'hc', 'ew', 'd', 'rc', 'f', 'tg', 'wt', 'hb', 'm', 'jf', 'ta', 'cw', 'rs', 'jr', 'b', 'ed', 'ea', 'fj', 'ah', 'dw', 'jc', 'hs', 'am', 'wa', 'rj', 'ra', 'tj'}
VALID_ACRONYMS = {'gwr', 'g.w.r.', 'jp', 'j.p.', 'hmc', 'h.m.c.', 'gpo', 'g.p.o.', 'pc', 'p.c.', 'po', 'p.o.', 'rn', 'r.n.', 'ra', 'r.a.', 're', 'r.e.', 'alcm', 'a.l.c.m.', 'ba', 'b.a.', 'ma', 'm.a.', 'md', 'm.d.', 'bsc', 'b.sc.', 'ce', 'fc'}

def is_person_name_or_title(t):
    if not t:
        return False
    t_clean = t.strip()
    t_lower = t_clean.lower()

    if t_lower in VALID_ACRONYMS:
        return False

    if t_lower in TITLES_AND_FORENAMES:
        return True

    if t_lower in SINGLE_INITIALS:
        return True

    if re.match(r'^(mrs\.?|miss\.?|mr\.?)\s+[a-z\.\s]+$', t_lower):
        trade_keywords = {'grocer', 'draper', 'fruiterer', 'manageress', 'teacher', 'butcher', 'refreshments', 'school', 'midwife', 'chiropodist', 'grcr', 'stewardess', 'postmstrss', 'warden', 'secretary', 'baker', 'tailor', 'painter', 'smith', 'builder', 'agent', 'dealer', 'nurse', 'clerk'}
        if not any(kw in t_lower for kw in trade_keywords):
            return True

    return False

SAINT_STREET_MAP = {
    r'^(?:St\.|Street)\s*Annes?\b.*': "St. Anne's Crescent",
    r'^(?:St\.|Street)\s*Brides?\b.*': "St. Bride's Crescent",
    r'^(?:St\.|Street)\s*Edwards?\b.*': "St. Edward Street",
    r'^(?:St\.|Street)\s*Johns?\b.*': "St. John's Road",
    r'^(?:St\.|Street)\s*Julians?\s*Ave.*': "St. Julian's Avenue",
    r'^(?:St\.|Street)\s*Julians?\s*Rd.*': "St. Julian's Road",
    r'^(?:St\.|Street)\s*Julians?\s*St.*': "St. Julian Street",
    r'^(?:St\.|Street)\s*Marks?\b.*': "St. Mark's Crescent",
    r'^(?:St\.|Street)\s*Marys?\s*Rd.*': "St. Mary's Road",
    r'^(?:St\.|Street)\s*Marys?\s*St.*': "St. Mary Street",
    r'^(?:St\.|Street)\s*Michaels?\b.*': "St. Michael Street",
    r'^(?:St\.|Street)\s*Stephens?\b.*': "St. Stephen's Road",
    r'^(?:St\.|Street)\s*Streetephens?\b.*': "St. Stephen's Road",
    r'^(?:St\.|Street)\s*Vincents?\b.*': "St. Vincent's Road",
    r'^(?:St\.|Street)\s*Woollos?\s*Rd.*': "St. Woolos Road",
    r'^(?:St\.|Street)\s*Woolos?\s*Rd.*': "St. Woolos Road",
    r'^(?:St\.|Street)\s*Woolos?\s*Pl.*': "St. Woolos Place",
    r'^(?:St\.|Street)\s*Woollos?\s*Pl.*': "St. Woolos Place"
}

def clean_street_name(name):
    if not name:
        return ""
        
    # Strip trailing continued/contd indicators (e.g. -continued, —continued, contd)
    name = re.sub(r'[\s\-—–_]+(?:continued|contd|cont|cont\.|contd\.)\s*$', '', name, flags=re.I).strip()
        
    # Strip parenthesized ward/map codes like (B T), (B.T.), (BT), (P), (M), (T)
    name = re.sub(r'\s*\([\s\.]*[A-Za-z][\s\.]*(?:[A-Za-z][\s\.]*)?\)', '', name).strip()
        
    # If the street name is in all-caps, convert it to Capital Case
    if name.isupper():
        words = name.split()
        capitalized_words = []
        for word in words:
            word_clean = word.strip('.,()-"\'')
            if word_clean.lower() in {'g.w.r.', 'gwr', 'g.w.r', 'm.o.', 'y.m.c.a.', 'ymca', 'r.a.f.'}:
                capitalized_words.append(word.upper())
            elif word_clean.upper() in {'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'}:
                capitalized_words.append(word.upper())
            elif word.lower().startswith("glo'"):
                capitalized_words.append("Glo'" + word[4:].lower().capitalize())
            elif "'" in word:
                parts = word.split("'")
                capitalized_words.append("'".join(p.capitalize() for p in parts))
            else:
                capitalized_words.append(word.capitalize())
        name = " ".join(capitalized_words)
    
    # Normalize High Street, P. or High Street, P to High Street, Pill
    if re.search(r'\bHigh\s+Street\s*[\.,]?\s*P\b', name, flags=re.I):
        return 'High Street, Pill'

    clean = name.replace('"', '').strip(' ,.-~—–_')

    # Specific street name merges and corrections
    street_map = {
        'aberrthaw road': 'Aberthaw Road',
        'aberthaw road. 2': 'Aberthaw Road',
        'aberthaw road 2': 'Aberthaw Road',
        'abbots-york place': 'York Place',
        'albany': 'Albany Street',
        'all saints': "All Saints' Road",
        "all saints'": "All Saints' Road",
        "all saints' church": "All Saints' Road",
        'alma st. baptist church': 'Alma Street',
        'baptist': 'Commercial Road',
        'bible': 'Hoskins Street',
        "bible christian mis'n": 'Hoskins Street',
        'belle': 'Belle Vue Lane',
        'belle vue park': 'Belle Vue Lane',
        'bella-terrace': 'Courtybella Terrace',
        'bilton street': 'Bilston Street',
        'boilermakers\' institute': 'Commercial Road',
        'branch reading': 'Corporation Road',
        'branch reading room': 'Corporation Road',
        'britannia': 'Commercial Road',
        'capel': 'Capel Street',
        'central': 'Dock Street',
        'central bd. schools': 'Dock Street',
        'obersley road': 'Ombersley Road',
        'barnard': 'Caerleon Road',
        'corporation road baptist church': 'Corporation Road',
        'county': 'Commercial Street',
        'county council offices': 'Commercial Street',
        'county court offices': 'Commercial Street',
        'county police station': 'Commercial Street',
        'crindau gospel hall': 'Malpas Road',
        'dewsdland park road': 'Dewsland Park Road',
        'donnington': 'Donnington Street',
        'east market street. e.4': 'East Market Street',
        'east usk baptist chapel': 'East Usk Road',
        'easy loans—the star money society—the best': 'Caerleon Road',
        "edwards ltd. & sports' outfitters": 'St. Mary Street',
        "edwards ltd.' outfitters. tel. 531": 'St. Mary Street',
        "edwards ltd., 'sports' outfitters. tel. 531": 'St. Mary Street',
        "fenell's": 'High Street',
        "francis' dye works. estab": 'Commercial Street',
        "francis' dye works. estab. 1890. cc": 'Commercial Street',
        's. john baptist high school': 'St. John’s Road',
        '11': 'High Street',
        '28 fire brigade station': 'Commercial Street',
        '113-113a': 'Commercial Street',
        '32-32a': 'Commercial Street',
        '4a & 5': 'Commercial Street',
        '24 lane thos': 'Thomas Street',
        '3 lane alfred': 'Alfred Street',
        '3 michl.. mkr bream place': 'Bream Place',
        '33 lane thomas': 'Thomas Street',
        '5 lane thos': 'Thomas Street',
        '54 void north street': 'North Street',
        '8 dennis lane': 'Dennis Street',
        "francis' dye works. 1890": 'Commercial Street',
        'general post office': 'High Street',
        'geo. greenland & sons. nat. tel. 0180': 'Commercial Street',
        'geo. greenland & sons. telephone 2416': 'Commercial Street',
        "girls' evening home": 'St. Mary Street',
        'grafton-roadto athletic ground': 'Grafton Road',
        'gwent': 'Gwent Street',
        'grove': 'Grove Street',
        'hale mrs': 'Orchard Street',
        'head of alexandra dock': 'Alexandra Docks',
        'holy cross cath. school': 'Victoria Road',
        'holy trinity church': 'High Street',
        'house of rerefuge': 'Stow Hill',
        'houses building': 'Caerleon Road',
        'hubert': 'Hubert Road',
        'intermediate schoolsle': 'Risca Road',
        "king's-parade to castle-street": "King's Parade",
        'l. &': 'Commercial Street',
        'langmaid': 'Caerleon Road',
        'liberal': 'Commercial Street',
        'liberal club': 'Commercial Street',
        'lockee street': 'Locke Street',
        'lucas': 'Lucas Street',
        'lyceum chambers': 'Commercial Street',
        'm.b..ch': 'Commercial Road',
        'm.o..b.. &': 'Commercial Street',
        'marshes road board schools': 'Marshes Road',
        'maypole dairy co': 'High Street',
        'merchants': 'Commercial Street',
        'metropolitan bank': 'Bridge Street',
        'midland bank chambers': 'High Street',
        'mission church': 'Corporation Road',
        'mission hall': 'Mendalgief Road',
        "navdies' mission": 'Dock Street',
        'new buildings': 'Commercial Road',
        'new territorial drill hall': 'Stow Hill',
        'newport castle': 'High Street',
        'now allt-yr-yn avenue': 'Allt-yr-yn Avenue',
        'newport exchange': 'High Street',
        "orb working men's club": 'Corporation Road',
        'offices & pupil t. centre': 'Stow Hill',
        'p. e. gane ltd': 'Commercial Street',
        'p. e. gane ltd.–162 commercial street': 'Commercial Street',
        'parry howard': 'Howard Street',
        'particular bapt. chapel': 'Commercial Street',
        'poole': 'Poole Lane',
        'powell duffryn whf.—office': 'Dock Street',
        'primitive meth. mission': 'Commercial Road',
        'primitive meth. chapel': 'Commercial Street',
        'prim. meth. church': 'Commercial Road',
        'prim. meth. chapel': 'Commercial Street',
        "queen's": 'Queen Street',
        'r. h. johns ltd': 'Commercial Street',
        "s. marie's": 'St. Mary Street',
        "s. marie's catholic ch": 'St. Mary Street',
        'school': 'Stow Hill',
        'secretary': 'Commercial Street',
        'see baneswell road': 'Baneswell Road',
        'sidney': 'Sidney Street',
        'skinner': 'Skinner Street',
        'south of alexandra dock': 'Alexandra Docks',
        "st. julian's church": 'Caerleon Road',
        'stow-hill to cuerau-road': 'Stow Hill',
        'street, east-street, victoria': 'Victoria Street',
        'stow-hill to clyffard-crescent': 'Stow Hill',
        'talgarth': 'Talgarth Place',
        'temperance hall': 'Commercial Street',
        'the camp': 'Caerleon Road',
        'the cemetery': 'Bassaleg Road',
        'the drill hall': 'Stow Hill',
        'tional': 'Commercial Street',
        'tredecar place': 'Tredegar Place',
        'u. methodist free church': 'Commercial Street',
        'upton': 'Caerleon Road',
        'victoria': 'Chepstow Road',
        'victoria wesleyan chp': 'Victoria Road',
        'victoria road congregational': 'Victoria Road',
        'welsh': 'Commercial Street',
        'welsh calvinistic methodist chapel': 'Commercial Street',
        'y.m.c.a. institute': 'Commercial Street',
        'y.m.c.a. welfare insti': 'Commercial Street',
        '3 michl., har. mkr bream place': 'Bream Place',
        'alexandra': 'Alexandra Road',
        'alexandra bd. schools': 'Alexandra Road',
        'beer john': 'Commercial Street',
        'beledere terrace': 'Belvedere Terrace',
        'belvidere terrace': 'Belvedere Terrace',
        'board schools': 'Commercial Road',
        'carnegie free library': 'Corporation Road',
        'clevelod terrace:': 'Clevedon Terrace',
        'conway': 'Conway Road',
        'corporation baths': 'Stow Hill',
        'corporation hospital': 'Corporation Road',
        'dolphin street. 51': 'Dolphin Street',
        'edwards': 'Commercial Street',
        'edwards ltd., ‘sports’ outfitters. tel. 531': 'Commercial Street',
        'glass works cottaces': 'Glass Works Cottages',
        'glasso works': 'Glass Works Cottages',
        'glebe': 'Glebe Street',
        'junction-road': 'Junction Road',
        'masonic': 'Commercial Street',
        'masonic hall': 'Commercial Street',
        "moulders' arms terrace": "Moulders' Arms Terrace",
        'p. e. gane ltd.—162 commercial street': 'Commercial Street',
        'and merchants, steam-ship and colliery furnishers. large stock of hose packings, i.r. valves and sheets, delivery hose, brewers\' hose, leather cup leathers, guage glasses, machine beltings, &c., &c., 157 commercial-st': 'Commercial Street',
        'potter street': 'Potter Street',
        'r. h. johns ltd. & stationers': 'Commercial Street',
        'row': 'Protheroes Row',
        'royal gwent hospital': 'Cardiff Road',
        'beer john, mount view': 'Mount View',
        'bryngblas crescent': 'Brynglas Crescent',
        'bryngblas road': 'Brynglas Road',
        'constance': 'Constance Street',
        'courtybella ter': 'Courtybella Terrace',
        'auckland villas:': 'Auckland Villas',
        'arcade (the)': 'Market Arcade',
        'wharves (the)': 'Wharves (The)',
        'the old cemetery-place. woolos-road': 'St. Woolos Road',
        'crowwell road': 'Cromwell Road',
        'cambridge road, d. 8': 'Cambridge Road',
        'cardiff-rd. to alexandra-dock': 'Cardiff Road',
        'carlisle-st. to alexandra-rd': 'Carlisle Street',
        'catholic schools': 'Stow Hill',
        'church and schools': 'Church Road',
        "christians'": 'Hoskins Street',
        'clarence place post office, m.o., s.b. & a. & i. office': 'Clarence Place',
        's. market street': 'South Market Street',
        'station street': 'Station Street',
        'tabernacle congregational church': 'Commercial Street',
        'tel. no. 956': 'Caerleon Road',
        'lliswerry board schoo': 'Corporation Road',
        'logie john, river view': 'River View',
        'office, m.o. & s.b. & a. & i': 'Commercial Street',
        'wesleyan meth. chapel': 'Commercial Road',
        'wheeler': 'Wheeler Street',
        'whitby': 'Whitby Place',
        'whitstone': 'Whitstone Road',
        'wolseley': 'Wolseley Street',
        'commercial rd., e': 'Commercial Road',
        'commercial-st': 'Commercial Street',
        'fields park cres': 'Fields Park Crescent',
        'friars road': "Friars' Road",
        'marlborough rd': 'Marlborough Road',
        'screw packet rd': 'Screw Packet Road',
        'st. woolos pl': 'St. Woolos Place',
        'baneswell-rd. to clyffard-cres': 'Baneswell Road',
        'corporation-rd. to eton-rd': 'Corporation Road',
        'corporation-rd. to riverside': 'Corporation Road',
        'corporation-rd. to rodney-rd': 'Corporation Road',
        'end of george-st. to skinner-st': 'George Street',
        'frederick-st. to portland-st': 'Frederick Street',
        'grafton-rd.to athletic ground': 'Grafton Road',
        'john-st. to south market-st': 'John Street',
        'mendalgief-rd. to wolseley-st': 'Mendalgief Road',
        'mountjoy-rd. to clytha-cres': 'Mountjoy Road',
        'redland-st. to crindau-rd': 'Redland Street',
        'victoria-av. to woodland-rd': 'Victoria Avenue',
        'whitby-pl. to manchester-st': 'Whitby Place',
        'hereford-st. to london-st': 'Hereford Street',
        'potter street': 'Potter Street',
        '& i. office': 'Commercial Street',
        '5, 17a': 'Commercial Street',
        'a.t.s': 'Preston Avenue',
        'alt-yr-yn hospital': 'Allt-yr-yn Avenue',
        'b.s., lond': 'London Street',
        'beechwood public park': 'Chepstow Road',
        'beechwood park': 'Chepstow Road',
        'canns & taylor golf clubs': 'Shaftesbury Street',
        'agincourt street c': 'Agincourt Street',
        'albany street, c': 'Albany Street',
        'alexandra dock': 'Alexandra Docks',
        'bachelor road, m': 'Bachelor Road',
        'barthropp street. e': 'Barthropp Street',
        'beechwood road, ch': 'Beechwood Road',
        'bassalleg road': 'Bassaleg Road',
        'bryngwas road': 'Brynglas Road',
        'blewitt street, b': 'Blewitt Street',
        'bolt street, p': 'Bolt Street',
        'altery road': 'Alteryn Road',
        'alteryns road': 'Alteryn Road',
        'alteyn road': 'Alteryn Road',
        'bryngwyn': 'Bryngwyn Road',
        'bryngzas avenue': 'Brynglas Avenue',
        'belle vue court': 'Belle Vue Lane',
        'belgave place': 'Chepstow Road',
        'obersley road': 'Ombersley Road',
        'pill athletic ground': 'Mendalgief Road',
        's. john evangelist church': 'Oaklands Road',
        'united methodist chapel': 'Caerleon Road',
        'tional church': 'Commercial Street',
        'francis\' dye works, 26 church road, maindee. estab. 1890. cc': 'Church Road',
        'francis\' dye works, 26 church road, maindee': 'Church Road',
        'marshes rd. board schools': 'Marshes Road',
        'glass works cottaces, c': 'Corporation Road',
        'st. michael\'s catholic church and schools': 'Stow Hill',
        'commercial wharf, e': 'Commercial Wharf',
        'pottery terrace, p': 'Pottery Terrace',
        'wrington terrace, m': 'Wrington Terrace'
    }
    
    clean_low = clean.lower()
    if clean_low in street_map:
        return street_map[clean_low]

    # Fix OCR symbol typos & specific street name merges
    clean = re.sub(r'Eveswel\]', 'Eveswell', clean, flags=re.IGNORECASE)
    clean = re.sub(r'([a-z])\]', r'\1l', clean)
    clean = re.sub(r'\bMalpas\s*\(\s*Main\s*\)\s*Road\b', 'Malpas Road', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\bFair[\s\-]*Oak\s*Ave[nu]+e\b', 'Fairoak Avenue', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\bAlteryn\b', 'Allt-yr-yn', clean, flags=re.IGNORECASE)

    # Strip trailing map grid coordinates (e.g., ", E 2", ", C 5", ", B 4", ", D 3", ", C.4", ", C. 4", ", C.3")
    clean = re.sub(r'[,\s]+[A-Z][\.\s]*\d+$', '', clean, flags=re.IGNORECASE).strip()
        
    return clean.strip(" ,.-")

def title_case_name(name):
    if not name:
        return ""
    return re.sub(r"\w\S*", lambda m: m.group(0).capitalize() if m.group(0).islower() else m.group(0), name).strip()

def apply_edge_cases(record):
    """Applies structured edge-case overrides from edge_cases.json."""
    st = record["street"]
    yr = record["year"]
    h_num = record["house_number"]
    bldg = record["building_name"]
    s = record["surname"]
    f = record["forename"]
    t = record["trade"]

    for rule in EDGE_CASES:
        match = rule.get("match", {})
        
        # Match street
        if match.get("street") and match["street"].lower() != st.lower():
            continue
        # Match year
        if match.get("year") and match["year"] != yr:
            continue
        # Match house_number
        if "house_number" in match and match["house_number"] != h_num:
            continue
        # Match surname
        if match.get("surname") and match["surname"].lower() != s.lower():
            continue
        if match.get("surname_contains") and match["surname_contains"].lower() not in s.lower():
            continue
        if match.get("forename_contains") and match["forename_contains"].lower() not in f.lower():
            continue
        if match.get("building_name") and match["building_name"].lower() != bldg.lower():
            continue

        # Check for record exclusion / deletion rule
        if rule.get("action") == "exclude":
            return None

        # Apply direct override
        if "apply" in rule:
            for k, v in rule["apply"].items():
                record[k] = v

        # Apply conditional override
        if "apply_conditional" in rule:
            cond = rule["apply_conditional"]
            if cond.get("if_surname_contains") and cond["if_surname_contains"].lower() in s.lower():
                for k, v in cond["apply"].items():
                    record[k] = v

    return record

def split_surname_forename(full_name_str):
    name_str = full_name_str.strip()
    if not name_str or " " not in name_str:
        return name_str, ""
        
    name_lower = name_str.lower()
    
    # Common business, place, and institutional keywords to protect from splitting
    business_keywords = {
        '&', 'and', 'ltd', 'limited', 'co', 'co.', 'company', 'sons', 'brothers', 'bros',
        'works', 'gas', 'glass', 'railway', 'board', 'national', 'society', 'station',
        'club', 'office', 'hall', 'house', 'villa', 'cottage', 'yard', 'wharf', 'clinic',
        'hospital', 'trust', 'garage', 'hotel', 'arms', 'tavern', 'inn', 'vicarage',
        'rectory', 'chapel', 'church', 'school', 'schools', 'association', 'dept',
        'department', 'committee', 'council', 'corporation', 'board', 'post', 'firewood',
        'builders', 'drapers', 'butchers', 'grocers', 'machinist', 'laundry', 'works', 'mill',
        'army', 'barrack', 'barracks', 'police', 'constabulary', 'salvation', 'institute', 'mission',
        'motors', 'motor', 'engineering', 'coal', 'iron', 'steel', 'metal', 'steam', 'gasworks',
        'electric', 'electricity', 'water', 'dock', 'docks', 'shipping', 'transport', 'haulage',
        'wholesalers', 'retailers', 'stores', 'shop', 'market', 'bazaar', 'theatre', 'cinema',
        'baths', 'baths.', 'library', 'museum', 'gallery', 'estate', 'farm', 'nurseries',
        'villas', 'cottages', 'gardens', 'terrace', 'place', 'hill', 'lane', 'road', 'street',
        'avenue', 'crescent', 'square', 'gardens', 'park', 'view', 'grove', 'walk', 'close',
        'court', 'parade', 'wharf', 'dock', 'docks', 'quay', 'pier', 'harbour', 'port',
        'railway', 'g.w.r.', 'gwr', 'g.w.r', 'station', 'depot', 'works', 'factory', 'mills',
        'mill', 'foundry', 'forge', 'yard', 'office', 'chambers', 'hall', 'chapel', 'church',
        'cathedral', 'temple', 'synagogue', 'mosque', 'school', 'schools', 'college',
        'university', 'academy', 'institute', 'institution', 'hospital', 'infirmary', 'clinic',
        'sanatorium', 'asylum', 'home', 'hotel', 'inn', 'tavern', 'arms', 'vaults', 'bar',
        'saloon', 'club', 'society', 'association', 'union', 'lodge', 'order', 'post', 'office',
        'bank', 'exchange', 'mart', 'market', 'stores', 'co-operative', 'cooperative', 'cemetery',
        'crematorium', 'allotments', 'works', 'gasworks', 'gas', 'waterworks', 'reservoir',
        'power', 'electricity', 'telegraph', 'telephone', 'post-office', 'police', 'station',
        'barracks', 'barrack', 'camp', 'fort', 'castle', 'manor', 'hall', 'house', 'palace',
        'court', 'villa', 'cottage', 'bungalow', 'chalet', 'lodge', 'grange', 'priory', 'abbey',
        'convent', 'monastery', 'nunnery', 'rectory', 'vicarage', 'parsonage', 'manse', 'presbytery'
    }
    
    # Check if any business keyword is in the name
    words = re.findall(r'\b[a-zA-Z0-9\&\.\-\x27]+\b', name_lower)
    if any(w in business_keywords for w in words):
        return name_str, ""
        
    # Skip cross-references or layout cues
    layout_keywords = {
        'see', 'under', 'opposite', 'here', 'crosses', 'return', 'void', 'vacant',
        'site', 'closed', 'demolished', 'rebuilt', 'consolidated'
    }
    if any(w in layout_keywords for w in words):
        return name_str, ""
        
    # Split the name
    parts = name_str.split()
    if len(parts) < 2:
        return name_str, ""
        
    # Check for multi-word surname prefixes (e.g. "St. John", "de Carteret")
    prefix_lower = parts[0].lower().rstrip('.')
    if prefix_lower in {'st', 'de', 'la', 'van', 'von', 'ap', 'mc', 'mac'} and len(parts) >= 3:
        surname = f"{parts[0]} {parts[1]}"
        forename = " ".join(parts[2:])
    else:
        surname = parts[0]
        forename = " ".join(parts[1:])
        
    return surname, forename

def clean_record(row):
    year = (row.get("year") or "").strip()
    street = clean_street_name(row.get("street") or "")
    
    # Special handle for mangled 1893 Park Square column merges
    if year == "1893" and street.lower().strip() == "park square":
        global INJECTED_1893_PARK_SQUARE
        if not globals().get('INJECTED_1893_PARK_SQUARE', False):
            globals()['INJECTED_1893_PARK_SQUARE'] = True
            return [
                # Park Square records
                {"year": "1893", "street": "Park Square", "house_number": "1", "building_name": "", "surname": "Fawckner", "forename": "J. F.", "trade": "architect"},
                {"year": "1893", "street": "Park Square", "house_number": "2", "building_name": "Peterstone Villa", "surname": "Grave", "forename": "Dd.", "trade": ""},
                {"year": "1893", "street": "Park Square", "house_number": "3", "building_name": "Lothian Villa", "surname": "Lang", "forename": "W. V.", "trade": ""},
                {"year": "1893", "street": "Park Square", "house_number": "4", "building_name": "Park Villa", "surname": "Watts", "forename": "Mrs L. V.", "trade": ""},
                {"year": "1893", "street": "Park Square", "house_number": "5", "building_name": "Sydenham Villa", "surname": "Richards", "forename": "J.", "trade": ""},
                {"year": "1893", "street": "Park Square", "house_number": "6", "building_name": "Alma Villa", "surname": "Long", "forename": "Mrs", "trade": ""},
                {"year": "1893", "street": "Park Square", "house_number": "7", "building_name": "Malvern Villa", "surname": "Jones", "forename": "C. H.", "trade": ""},
                {"year": "1893", "street": "Park Square", "house_number": "8", "building_name": "Richmond Villa", "surname": "Jones", "forename": "E. W.", "trade": ""},
                {"year": "1893", "street": "Park Square", "house_number": "9", "building_name": "Roslyn House", "surname": "Maddock", "forename": "Jas.", "trade": ""},
                {"year": "1893", "street": "Park Square", "house_number": "10", "building_name": "Thorntree House", "surname": "Davies", "forename": "B.", "trade": "M.D."},
                {"year": "1893", "street": "Park Square", "house_number": "11", "building_name": "The Mount", "surname": "Williams", "forename": "Herbt. Egerton", "trade": "surgeon"},
                {"year": "1893", "street": "Park Square", "house_number": "12", "building_name": "Prospect Villa", "surname": "Schofield", "forename": "Wm.", "trade": ""},
                {"year": "1893", "street": "Park Square", "house_number": "13", "building_name": "Balmoral Villa", "surname": "Stephens", "forename": "Mrs A. J.", "trade": ""},
                {"year": "1893", "street": "Park Square", "house_number": "13", "building_name": "Balmoral Villa", "surname": "Thomas", "forename": "Mrs Lloyd", "trade": ""},
                
                # Park Street records
                {"year": "1893", "street": "Park Street", "house_number": "1", "building_name": "", "surname": "Warner", "forename": "Chas.", "trade": "hobbler"},
                {"year": "1893", "street": "Park Street", "house_number": "2", "building_name": "", "surname": "Hanks", "forename": "Geo.", "trade": "labourer"},
                {"year": "1893", "street": "Park Street", "house_number": "3", "building_name": "", "surname": "Clarke", "forename": "Alfred", "trade": "labourer"},
                {"year": "1893", "street": "Park Street", "house_number": "4", "building_name": "", "surname": "Daley", "forename": "John", "trade": "engineman"},
                {"year": "1893", "street": "Park Street", "house_number": "5", "building_name": "", "surname": "Bishop", "forename": "Chas.", "trade": "labourer"},
                {"year": "1893", "street": "Park Street", "house_number": "6", "building_name": "", "surname": "Harris", "forename": "Benj.", "trade": "baker"},
                {"year": "1893", "street": "Park Street", "house_number": "7", "building_name": "", "surname": "Mansell", "forename": "Thos.", "trade": "labourer"},
                {"year": "1893", "street": "Park Street", "house_number": "8", "building_name": "", "surname": "Olsen", "forename": "Chas.", "trade": "labourer"},
                {"year": "1893", "street": "Park Street", "house_number": "9", "building_name": "", "surname": "Bath", "forename": "Thos.", "trade": "labourer"},
                {"year": "1893", "street": "Park Street", "house_number": "10", "building_name": "", "surname": "Jones", "forename": "Thos.", "trade": "labourer"},
                {"year": "1893", "street": "Park Street", "house_number": "11", "building_name": "", "surname": "Lewis", "forename": "Wm.", "trade": "labourer"},
                {"year": "1893", "street": "Park Street", "house_number": "12", "building_name": "", "surname": "Harris", "forename": "Thos.", "trade": "tailor"},
                {"year": "1893", "street": "Park Street", "house_number": "13", "building_name": "", "surname": "Taylor", "forename": "Wm.", "trade": "labourer"},
                {"year": "1893", "street": "Park Street", "house_number": "14", "building_name": "", "surname": "Woodrow", "forename": "Chas.", "trade": "engineer"},
                {"year": "1893", "street": "Park Street", "house_number": "15", "building_name": "", "surname": "Haswell", "forename": "Johnson", "trade": "nailmaker"},
                {"year": "1893", "street": "Park Street", "house_number": "16", "building_name": "", "surname": "Powell", "forename": "Wm.", "trade": "signal fitter"},
                {"year": "1893", "street": "Park Street", "house_number": "17", "building_name": "", "surname": "Curthoys", "forename": "Henry", "trade": "G.W.R."},

                # Portland Street records
                {"year": "1893", "street": "Portland Street", "house_number": "25", "building_name": "", "surname": "Gearing", "forename": "Cor.", "trade": "labourer"},
                {"year": "1893", "street": "Portland Street", "house_number": "26", "building_name": "", "surname": "Collins", "forename": "Jasper", "trade": "coal trimmer"},
                {"year": "1893", "street": "Portland Street", "house_number": "27", "building_name": "", "surname": "Hughes", "forename": "Ll.", "trade": "pipemaker"},
                {"year": "1893", "street": "Portland Street", "house_number": "28", "building_name": "", "surname": "Vowell", "forename": "Jno.", "trade": "timekeeper"},
                {"year": "1893", "street": "Portland Street", "house_number": "", "building_name": "", "surname": "Chas. Jordan & Sons, Ltd", "forename": "", "trade": "Pillgwenlly Iron Foundry"},
                {"year": "1893", "street": "Portland Street", "house_number": "30", "building_name": "", "surname": "Cashman", "forename": "Mrs Hannah", "trade": ""},
                {"year": "1893", "street": "Portland Street", "house_number": "31", "building_name": "", "surname": "Void", "forename": "", "trade": ""},
                {"year": "1893", "street": "Portland Street", "house_number": "32", "building_name": "", "surname": "Johns", "forename": "Jno.", "trade": "engine driver"},
                {"year": "1893", "street": "Portland Street", "house_number": "33", "building_name": "", "surname": "Dunstan", "forename": "James", "trade": "rigger"},
                {"year": "1893", "street": "Portland Street", "house_number": "34", "building_name": "", "surname": "Rumsey", "forename": "George", "trade": "fitter"},
                {"year": "1893", "street": "Portland Street", "house_number": "35", "building_name": "", "surname": "Cowling", "forename": "Wm.", "trade": "sailor"},
                {"year": "1893", "street": "Portland Street", "house_number": "", "building_name": "", "surname": "Evans", "forename": "John", "trade": "seaman"}
            ]
        return None
    
    # Reject coordinates like 'B 5 & 6', 'C 4 17', 'D 5 58', single letters, and fragments
    st_low = street.lower().strip()
    if len(st_low) <= 1 or re.match(r'^[a-z]\s+\d+.*$', st_low) or st_low in {'c o. (', 'c.o.', 'l.d.'}:
        return None
        
    # Reject layout street names
    if (st_low in {"newport street list", "newport street", "left side", "right side", "left hand side", "right hand side", "east side", "west side", "north side", "south side", "directories"} or
        st_low.startswith("here is") or 
        st_low.startswith("rt.-hand") or 
        st_low.startswith("lt.-hand") or 
        st_low.startswith("right-hand") or 
        st_low.startswith("left-hand") or 
        "street list" in st_low or 
        "(from" in st_low or 
        st_low.startswith("from ") or 
        st_low.startswith("to ") or 
        st_low.startswith("off ") or 
        "road to " in st_low or 
        "street to " in st_low or 
        "avenue to " in st_low or
        st_low.startswith("east side") or
        st_low.startswith("west side") or
        st_low.startswith("north side") or
        st_low.startswith("south side") or
        st_low.startswith("right side") or
        st_low.startswith("left side")
    ):
        return None

    house_num = (row.get("house_number") or "").replace("\\t", "").replace("\\n", "").strip().strip(',"-~\'')
    bldg_name = (row.get("building_name") or "").replace("\\t", "").replace("\\n", "").strip().strip(',"-~\'')
    
    # Clear layout artifacts like '0' or duplicate numbers in building name
    if bldg_name.isdigit():
        if bldg_name == "0" or bldg_name == "00" or house_num:
            bldg_name = ""

    surname = (row.get("surname") or "").replace("\\t", "").replace("\\n", "").strip().strip(',"-~\'')
    forename = (row.get("forename") or "").replace("\\t", "").replace("\\n", "").strip().strip(',"-~\'')
    trade = (row.get("trade") or "").replace("\\t", "").replace("\\n", "").strip().strip(',"-~\'')

    # Reassign sub-terrace section headers to physical parent street while preserving terrace section in building_name
    st_raw_low = street.lower().strip()
    if st_raw_low in ["highweek terrace", "belle vue terrace"]:
        terrace_label = "Highweek Terrace" if st_raw_low == "highweek terrace" else "Belle Vue Terrace"
        street = "Morden Road"
        if not bldg_name:
            bldg_name = terrace_label
        elif terrace_label.lower() not in bldg_name.lower():
            bldg_name = f"{terrace_label} ({bldg_name})"
    elif st_raw_low in ["auckland", "auckland terrace", "auckland villas"]:
        terrace_label = "Auckland Villas" if st_raw_low == "auckland villas" else "Auckland Terrace"
        street = "Christchurch Road"
        if not bldg_name:
            bldg_name = terrace_label
        elif terrace_label.lower() not in bldg_name.lower():
            bldg_name = f"{terrace_label} ({bldg_name})"
    elif st_raw_low in ["eseswell terrace", "esveswell terrace"]:
        terrace_label = "Eveswell Terrace"
        street = "Chepstow Road"
        if not bldg_name:
            bldg_name = terrace_label
        elif terrace_label.lower() not in bldg_name.lower():
            bldg_name = f"{terrace_label} ({bldg_name})"

    # Auto-realign records where a business name or entity was placed in the trade field without a surname or house number
    if not house_num and not bldg_name and not surname and not forename and trade:
        surname = trade
        trade = ""

    # Realign shifted 1971 records and strip school/layout parentheticals
    if year == "1971":
        # Realign 1971 records where the entire line was parsed into the surname column (no tabs)
        if not house_num and not forename and surname:
            parts = surname.strip().split()
            if parts:
                first_word = parts[0]
                if first_word.isdigit() or re.match(r'^\d+[a-zA-Z]?$', first_word):
                    house_num = first_word
                    remaining_name = parts[1:]
                    if remaining_name:
                        surname = remaining_name[0]
                        forename = " ".join(remaining_name[1:])
                    else:
                        surname = ""
                        forename = ""

        # First clean off parenthetical layout noise in house_number
        h_low = house_num.lower()
        if "no thoroughfare" in h_low or "junior" in h_low or "infants" in h_low or "mixed &" in h_low:
            house_num = ""
            if surname.isdigit() or re.match(r'^\d+[a-zA-Z]?$', surname) or surname.lower() == "la":
                # Realign shifted columns
                if surname.lower() == "la":
                    house_num = "1a"
                else:
                    house_num = surname
                surname = forename
                forename = bldg_name
                bldg_name = ""
                
        # If the record is still shifted (e.g. house number in surname)
        if not house_num and surname:
            sur_strip = surname.strip()
            if sur_strip.isdigit() or re.match(r'^\d+[a-zA-Z]?$', sur_strip) or sur_strip.lower() == "la":
                if sur_strip.lower() == "la":
                    house_num = "1a"
                else:
                    house_num = sur_strip
                
                full_name = forename.strip()
                if full_name:
                    name_parts = full_name.split()
                    if len(name_parts) >= 2:
                        surname = name_parts[0]
                        forename = " ".join(name_parts[1:])
                    else:
                        surname = full_name
                        forename = ""
                        
        # Post-processing name split if surname contains space (e.g. "Phillips Bernard")
        # but house_num is correctly set.
        if house_num and surname and not forename:
            name_parts = surname.strip().split()
            if len(name_parts) >= 2 and not name_parts[0].isdigit():
                surname = name_parts[0]
                forename = " ".join(name_parts[1:])

    # Realign specific scrambled Baneswell Road entries
    if street.lower().strip() == "baneswell road":
        # Discard 1902 long Reynolds advertising banner
        if "reynolds" in f"{house_num} {bldg_name} {surname} {forename} {trade}".lower():
            return None
            
        # 1893 Baneswell Road column shifts (Smith's porter stores, Monmouthshire Club, Barfoot, S. Wales Daily News)
        if year == "1893":
            if house_num.lower() == "smith's" and surname.lower() == "porter stores":
                house_num = ""
                bldg_name = "Smith's Porter Stores"
                surname = ""
                forename = ""
                trade = "porter stores"
            elif house_num.lower() == "monmouthshire" and "club" in surname.lower():
                house_num = ""
                bldg_name = "Monmouthshire Club"
                surname = "Andrews"
                forename = "George"
                trade = "steward"
            elif house_num.lower() == "barfoot" and "tobacconist" in surname.lower():
                house_num = "14"
                bldg_name = ""
                surname = "Barfoot"
                forename = "T. A."
                trade = "tobacconist"
            elif house_num.lower().startswith("s. wales"):
                house_num = ""
                bldg_name = "South Wales Daily News & Echo Office"
                surname = "Williams"
                forename = "E."
                trade = "agent"

        # 1938 & 1936 Canterbury Lamb Store 6-6A fixes
        if year in ["1938", "1936"] and (house_num in ["6 - 6", "6-6A"] or "canterbury" in f"{surname} {forename} {trade}".lower()):
            house_num = "6-6A"
            bldg_name = ""
            surname = "Woodley H. & Co. Ltd."
            forename = ""
            trade = "Canterbury Lamb Store, butchers"

    # Realign specific scrambled 1938 Brynglas Avenue entries
    if year == "1938" and street.lower().strip() == "brynglas avenue" and not house_num:
        b_low = bldg_name.lower().strip()
        s_low = surname.lower().strip()
        f_low = forename.lower().strip()
        
        if b_low == "smith e" and s_low == "g.w.r" and f_low == "bradley house":
            bldg_name = "Bradley house"
            surname = "Smith"
            forename = "E"
            trade = "G.W.R"
        elif b_low == "colbourne f. h" and s_low == "hairdsr" and f_low == "overdale":
            bldg_name = "Overdale"
            surname = "Colbourne"
            forename = "F. H."
            trade = "hairdresser"
        elif b_low == "west geo. f" and s_low == "g.w.r" and f_low == "corbiere":
            bldg_name = "Corbiere"
            surname = "West"
            forename = "Geo. F."
            trade = "G.W.R"
        elif b_low == "jones harold" and s_low == "furnaceman" and f_low == "beech dale":
            bldg_name = "Beech Dale"
            surname = "Jones"
            forename = "Harold"
            trade = "furnaceman"
        elif b_low == "smith f. h" and s_low == "clk" and f_low == "dairy":
            bldg_name = "Dairy"
            surname = "Smith"
            forename = "F. H."
            trade = "clerk"

    # Realign specific scrambled 1927 Brynglas Crescent entry
    if year == "1927" and street.lower().strip() == "brynglas crescent" and house_num == "8":
        if surname.lower().strip() == "j":
            surname = "Hicks"
            forename = "Thomas J."
            trade = "tailor"
            bldg_name = ""

    # Discard records that are purely layout artifacts
    combined_fields = f"{house_num} {bldg_name} {surname} {forename} {trade}".lower().strip()
    if LAYOUT_ONLY_REGEX.search(combined_fields):
        return None

    # Discard records that are just "continued" street headers or location descriptions
    if "continued" in combined_fields or "—continued" in combined_fields or "-continued" in combined_fields:
        return None
    if "top of upper" in combined_fields or "top of" in combined_fields or "road to" in combined_fields:
        return None

    # Discard records that contain parenthetical former-name markers like "(late ...)"
    if "(late" in bldg_name.lower() or "(late" in surname.lower() or "(late" in forename.lower() or "(late" in trade.lower():
        return None

    # Discard records where surname is just a number (drifted house numbers)
    if surname.isdigit() and not forename and not trade:
        return None

    # Discard records where surname or building_name is just a coordinate reference (e.g. "E 9", "E 8, E 9, D 10")
    if (re.match(r'^[A-Za-z]{1,2}[\s\.,\d&and]*$', surname) and any(c.isdigit() for c in surname) and not forename and not trade) or \
       (re.match(r'^[A-Za-z]{1,2}[\s\.,\d&and]*$', bldg_name) and any(c.isdigit() for c in bldg_name) and not surname and not forename and not trade):
        return None

    # Discard rows that are just cross-street headers (e.g. surname="Vancouver drive" with no other fields)
    if surname and not forename and not house_num and not trade and not bldg_name:
        s_low = surname.lower()
        suffixes = {'street', 'road', 'lane', 'place', 'terrace', 'crescent', 'square', 'avenue', 'drive', 'hill', 'parade', 'gardens', 'walk', 'close', 'view', 'grove', 'way', 'rise', 'arcade'}
        if any(f" {suff}" in s_low or s_low.endswith(f" {suff}") for suff in suffixes):
            return None

    # Strip map references from all fields (e.g. "Map E 9.", "Map F 7, G 7.", "Map E 4")
    map_ref_pat = re.compile(r'\bMap\s+[A-Za-z0-9\s,\.&-]*\d+[A-Za-z0-9\s,\.&-]*\b\.?', re.I)
    house_num = map_ref_pat.sub('', house_num).strip(' ,"-~.\\/')
    bldg_name = map_ref_pat.sub('', bldg_name).strip(' ,"-~.\\/')
    surname = map_ref_pat.sub('', surname).strip(' ,"-~.\\/')
    forename = map_ref_pat.sub('', forename).strip(' ,"-~.\\/')
    trade = map_ref_pat.sub('', trade).strip(' ,"-~.\\/')

    # Reject records that consist only of backslashes / empty placeholders
    if not house_num and not bldg_name and not surname and not forename and not trade:
        return None
    if not surname and not forename and not trade and not bldg_name:
        return None

    # Strip specific layout prefixes from surname (e.g. "And Albert-avenue Hall William" -> "Hall William")
    layout_prefix_pat = re.compile(r'^\s*(?:and|off|entrance\s+to)?\s*(?:a\s*lbert[\s\-]*avenue|duckpool[\s\-]*road|gibbs[\s\-]*road)\s*', re.I)
    surname = layout_prefix_pat.sub('', surname).strip(' ,"-~.')

    # Fix corrupted Japanese katakana characters and column alignment in names
    if "grットン" in house_num.lower() or "grットン" in bldg_name.lower() or "grットン" in surname.lower():
        house_num = ""
        surname = "Gretton"
        forename = "Chas"
        trade = "labourer"

    # Discard records that are layout artifacts / description residues in names
    noise_words = {
        "orc", "par", "road", "que", "s", "w", "h", "st", "gery)", "newport", "yard",
        "street directory", "close & wye cres", "off corporation", "no thoroughfare",
        "no thoroughfare.", "(no thoroughfare.)", "house building", "map e.4", "map e4",
        "map e. 4", "void", "vacant", "nil", "queens", "queen's", "queens buildings",
        "+queens", "+queen's", "bolton", "bolton terrace", "bolton terrace—", "ban"
    }
    
    # Check if there is no other identifying info and fields contain only noise
    if not house_num and not forename and not trade:
        sur_clean = surname.lower().strip(" ,.-—_")
        bldg_clean = bldg_name.lower().strip(" ,.-—_")
        if sur_clean in noise_words or bldg_clean in noise_words or len(sur_clean) == 1:
            return None
        if "street directory" in sur_clean or "street directory" in bldg_clean:
            return None

    # Discard cross-reference layout artifacts under Parkfield Place
    if street.lower().strip() == "parkfield place" and not house_num and not surname and not forename and not trade:
        b_low = bldg_name.lower().strip()
        if any(kw in b_low for kw in {"clytha", "pembroke", "penllyn", "risca", "pentonville", "penylan"}):
            return None

    # Strip layout substrings from individual fields
    surname = LAYOUT_STRIP_REGEX.sub('', surname).strip(' ,"-~.')
    forename = LAYOUT_STRIP_REGEX.sub('', forename).strip(' ,"-~.')
    bldg_name = LAYOUT_STRIP_REGEX.sub('', bldg_name).strip(' ,"-~.')
    trade = LAYOUT_STRIP_REGEX.sub('', trade).strip(' ,"-~.')

    # 1. Filter out Directory Header Artifacts, Cross-street Headings & (return) Markers
    if surname.lower() in HEADER_SURNAMES and (forename.isdigit() or not trade):
        return None

    combined_name = f"{surname} {forename}".strip()
    is_chambers_street = any(term in street.lower() for term in ["chambers", "cottages", "villas", "arcade"])
    if not is_chambers_street:
        if CROSS_STREET_REGEX.search(combined_name) or CROSS_STREET_REGEX.search(bldg_name) or CROSS_STREET_REGEX.search(surname):
            return None

    # Strip district headers (e.g. MaindeeFrom, NewportFrom)
    surname = re.sub(r'^(maindee|newport|pill)from\s*', '', surname, flags=re.I).strip()
    forename = re.sub(r'^(maindee|newport|pill)from\s*', '', forename, flags=re.I).strip()

    # Strip (right hand), [left hand side.], etc. attached to real resident fields
    pat_side_strip = re.compile(r'[\(\[]?\s*\b(right|left)\s+hand(\s+side)?\b\s*[\)\]]?', re.I)
    surname = pat_side_strip.sub('', surname).strip(' ,"-~.')
    forename = pat_side_strip.sub('', forename).strip(' ,"-~.')
    bldg_name = pat_side_strip.sub('', bldg_name).strip(' ,"-~.')
    trade = pat_side_strip.sub('', trade).strip(' ,"-~.')

    # Strip telephone numbers (e.g. "Tel. Newport 66092 & 67834", "Telephone 62861")
    phone_pattern = re.compile(r'\b(?:tel|phone|telephone)\.?,?\s*(?:newport\s*)?\d+(?:\s*(?:&|and)\s*\d+)?\b', re.I)
    surname = phone_pattern.sub('', surname).strip(' ,"-~.')
    forename = phone_pattern.sub('', forename).strip(' ,"-~.')
    bldg_name = phone_pattern.sub('', bldg_name).strip(' ,"-~.')
    trade = phone_pattern.sub('', trade).strip(' ,"-~.')

    # Split reversed "Surname Forename" names if forename is empty and surname contains space
    if surname and not forename and " " in surname:
        sn_split, fn_split = split_surname_forename(surname)
        if fn_split:
            surname = title_case_name(sn_split)
            forename = title_case_name(fn_split)

    # Fix Ty Dedwydd split (where the house name is split as a resident name)
    s_low = surname.lower()
    f_low = forename.lower()
    if (s_low == "ty" and f_low in {"dedwydd", "edwydd"}) or (not surname and f_low in {"dedwydd", "edwydd"} and bldg_name.lower() == "ty"):
        bldg_name = "Ty Dedwydd"
        surname = ""
        forename = ""

    # Aid post fix (e.g. surname='First', forename='aid post')
    if surname.lower() == "first" and forename.lower() == "aid post":
        surname = "First Aid Post"
        forename = ""
        trade = "First Aid Post"

    # Standardize Ld -> Ltd for company names (e.g. 'Newport Labour Hall Ld')
    bldg_name = re.sub(r'\bLd\.?\b', 'Ltd', bldg_name)
    surname = re.sub(r'\bLd\.?\b', 'Ltd', surname)
    trade = re.sub(r'\bLd\.?\b', 'Ltd', trade)

    # Merge split business names (e.g. surname='Indian', forename='Rampore Tea Co.')
    if surname and forename:
        f_low = forename.lower()
        if any(suffix in f_low for suffix in ['tea co', 'ltd', 'limited', 'co. ltd', 'company', '& co', '& sons']):
            surname = f"{surname} {forename}".strip()
            forename = ""

    # Realign cases where the surname is a business/company and the forename is actually the trade
    # e.g., surname="Newman & Sons'", forename="music warehouse"
    if surname and forename and not trade:
        f_low = forename.lower()
        s_low = surname.lower()
        is_business = any(suffix in s_low for suffix in ['& sons', '& co', 'ltd', 'limited', 'company', ' co.', ' tea co'])
        trade_keywords = [
            'music warehouse', 'warehouse', 'provision', 'dealer', 'merchant', 'store',
            'agent', 'inn', 'hotel', 'tavern', 'publican', 'shop', 'office', 'depot',
            'works', 'foundry', 'brewery', 'chapel', 'church', 'school', 'hall',
            'baker', 'butcher', 'draper', 'tailor', 'hairdresser', 'shoemaker', 'bootmaker',
            'printer', 'stationer', 'chemist', 'tobacconist', 'fruiterer', 'fishmonger',
            'builder', 'cabinet maker', 'upholsterer', 'ironmonger', 'cooper', 'smith'
        ]
        if is_business and any(kw in f_low for kw in trade_keywords):
            trade = forename
            forename = ""

    # Standardize directory cross-reference entries (e.g. surname='NewportSee', forename='Stow Hill', street='Lamb Cottages')
    raw_all_fields = f"{bldg_name} {surname} {forename}".strip()
    cross_ref_match = re.search(r'\[?\b(?:newport\s*)?see\s+(?:also\s+)?(?:under\s+|no\.\s*\d+\s+)?([A-Za-z\s]+)', raw_all_fields, re.I)
    if cross_ref_match:
        target_dest = cross_ref_match.group(1).strip(']. ')
        target_dest = re.sub(r'^(?:under\s+|no\.\s*\d+\s+)', '', target_dest, flags=re.I).strip()
        target_dest = re.sub(r'(\b(?:street|road|lane|hill|place|terrace|avenue|square|parade|chambers|cottages)\b).*', r'\1', target_dest, flags=re.I).strip()
        surname = f"See {target_dest}"
        forename = ""
        bldg_name = street
        trade = "Directory Cross-Reference"

    # 2. Fix shifted surname/forename/trade in building_name (e.g. bldg='Bennett', surname='AG', forename='brewery hand')
    if bldg_name and bldg_name[0].isupper() and not any(w in bldg_name.lower() for w in ['house', 'villa', 'villas', 'cottage', 'cottages', 'chambers', 'works', 'inn', 'arms', 'hotel', 'building', 'buildings', 'school', 'lodge', 'place', 'hall', 'terrace', 'view', 'court', 'gardens', 'flat', 'flats', 'store', 'stores', 'shop', 'office', 'offices', 'bank', 'vaults', 'laundry', 'chapel', 'church', 'depot', 'yard', 'mills']):
        # If building_name contains a person name that overlaps with forename or surname, clean building_name
        b_low = bldg_name.lower().strip()
        s_low = surname.lower().strip()
        f_low = forename.lower().strip()
        if f_low in b_low or s_low in b_low or f_low in TRADE_KEYWORDS or any(w in f_low for w in ['hand', 'worker', 'labourer', 'sorter', 'fitter', 'carpenter', 'driver', 'grocer', 'draper', 'mason', 'butcher', 'bootmaker', 'shoemaker', 'painter', 'plumber', 'tailor', 'baker', 'signalman', 'postman', 'shunter', 'timekeeper', 'tobacconist', 'waterman', 'greengrocer']):
            if not trade and (is_trade_word(forename) or is_trade_word(surname)):
                trade = title_case_name(forename if is_trade_word(forename) else surname)
            bldg_name = ""

    # 3. Handle Crindau Glass / Gas Works company titles
    if "Glass Manufacturing" in combined_name or "Glass Manufacturing" in trade or "Glass Manufacturing" in surname:
        surname = "South Wales Glass Manufacturing Co. Office & Works"
        forename = ""
        trade = "glass manufacturers"
    elif surname == "Crindau" and forename == "Gas Works":
        surname = "Crindau Gas Works"
        forename = ""

    # 4. Extract trade trapped in forename or surname (e.g. 'Thos. chimney sweep', 'S. W. butcher', 'Stanley & beer retailer')
    TRAPPED_TRADE_PAT = (
        r'chimney\s+sweeps?|chimney\s+sweeper|wholesale\s+tobacconist|tobacconist|'
        r'cab\s+proprietor|beer\s+retailer|general\s+dealer|greengrocer|'
        r'pork\s+butcher|butcher|plumber|draper|grocer|mason|'
        r'carpenter|blacksmith|shoemaker|bootmaker|ironmonger|'
        r'haulier|painter|tinman|tinsmith|marine\s+stores|'
        r'stationer|newsagent|fruiterer|fishmonger|baker|'
        r'confectioner|tailor|outfitter|hairdresser|upholsterer|'
        r'dairyman|cowkeeper|builder|wheelwright|saddler|'
        r'watchmaker|jeweller|pawnbroker|house\s+agent|coal\s+merchant|'
        r'wine\s+merchant|spirit\s+merchant|chemist|druggist|'
        r'milliner|wine|cabinet\s+maker|professor\s+of\s+\w+|registry\s+office|'
        r'auctioneer|dressmaker|gardener|solicitor|surgeon|dentist|'
        r'architect|engineer|broker|accountant|merchant|agent|'
        r'licensed\s+victualler|publican|storekeeper|store\s+keeper|timekeeper|gatekeeper'
    )
    if forename:
        match_t_f = re.match(r"^(.*?)\s+\b(" + TRAPPED_TRADE_PAT + r")\b$", forename, re.I)
        if match_t_f:
            c_fn = match_t_f.group(1).strip()
            extra_t = match_t_f.group(2).strip()
            if c_fn and (c_fn[0].isupper() or c_fn.endswith('.')):
                forename = c_fn
                trade = f"{extra_t}, {trade}".strip(", ") if trade else extra_t

    if surname:
        match_t_s = re.match(r"^(.*?)\s*&\s*\b(" + TRAPPED_TRADE_PAT + r")\b$", surname, re.I)
        if match_t_s:
            c_sn = match_t_s.group(1).strip()
            extra_t = match_t_s.group(2).strip()
            if c_sn and c_sn[0].isupper():
                surname = c_sn
                trade = f"{extra_t}, {trade}".strip(", ") if trade else extra_t

    # 5. Fix institution names split across surname & forename (e.g. 'Conservative' + 'Association', 'Baptist' + 'chapel')
    if forename and INSTITUTION_WORD.search(forename.strip()):
        surname = title_case_name(f"{surname} {forename}".strip())
        forename = ""

    # 5c. Extract shifted villa lines where house number, resident surname & forename are trapped in trade (e.g. trade='31, Foden, Thos', surname='Shaldon House')
    m_shifted_villa = re.match(r'^\s*(\d+[a-zA-Z]?)\s*,\s*([A-Za-z\x27\s\-]+?)\s*,\s*([A-Za-z\.\s]+)\s*$', trade, re.I)
    if m_shifted_villa:
        extracted_hno = m_shifted_villa.group(1).strip()
        extracted_surname = m_shifted_villa.group(2).strip()
        extracted_forename = m_shifted_villa.group(3).strip()

        villa_parts = [p for p in [bldg_name, surname, forename] if p and not p.isdigit()]
        combined_villa = " ".join(villa_parts).strip()

        if extracted_hno and not house_num:
            house_num = extracted_hno
        surname = title_case_name(extracted_surname)
        forename = extracted_forename
    # 5d. Clean numeric / misplaced building unit numbers in trade (e.g. trade='1', trade='2', trade='1 The Hollies', trade='fitter, 2 Blewitt cot')
    if trade.isdigit():
        if trade == house_num:
            trade = ""
        elif not house_num:
            house_num = trade
            trade = ""
        else:
            bldg_name = title_case_name(f"{trade} {bldg_name}".strip()) if bldg_name else bldg_name
            trade = ""
    else:
        m_num_villa_trade = re.search(r'^(?:(.*?),\s*)?(\d+\s+[A-Za-z\s\x27\-]*?\b(?:villa|villas|cottage|cottages|cot|place|house|terrace|view|chambers|buildings?|inn|hotel|lodge|hall)\b[A-Za-z\s]*)$', trade, re.I)
        if m_num_villa_trade:
            extra_t = (m_num_villa_trade.group(1) or "").strip()
            extracted_bldg = m_num_villa_trade.group(2).strip()
            bldg_name = title_case_name(f"{extracted_bldg} {bldg_name}".strip()) if bldg_name else title_case_name(extracted_bldg)
            trade = extra_t

    if "St. Marks Vicarage" in trade or "St. Mark's Vicarage" in trade:
        bldg_name = "St. Mark's Vicarage"
        trade = re.sub(r'[\s,]*St\.\s*Marks?\s*Vicarage', '', trade, flags=re.I).strip(" ,.-")

    if "bryn tegid" in trade.lower():
        bldg_name = "Bryn Tegid"
        trade = re.sub(r'[\s,]*bryn\s+tegid', '', trade, flags=re.I).strip(" ,.-")
        if trade.lower() == "ladies school":
            trade = "Ladies School"

    # 6. Extract building/villa names from trade or forename (e.g. trade='Stow gate villa', forename='R. H. Belmont villa')
    if not bldg_name:
        v_match_f = VILLA_WORD.search(forename)
        if v_match_f and not any(w in forename.lower() for w in ['customs', 'commercial', 'auctioneer', 'draper']):
            bldg_name = title_case_name(v_match_f.group(1))
            forename = forename.replace(v_match_f.group(1), '').strip()

        v_match_t = VILLA_WORD.search(trade)
        if v_match_t and not any(w in trade.lower() for w in ['customs', 'commercial', 'auctioneer', 'house,', 'estate', 'repairer']):
            bldg_name = title_case_name(v_match_t.group(1))
            trade = trade.replace(v_match_t.group(1), '').strip()

    # 7. Extract telephone numbers misparsed into house_number column (e.g. 45876, 41609)
    if house_num.isdigit() and (int(house_num) >= 40000 or (int(house_num) >= 1000 and street != "Corporation Road")):
        tel_num = house_num
        house_num = ""
        # Restore known house numbers if applicable
        if "King's Head" in trade or "King's Head" in surname:
            house_num = "1"
        elif "WE Evans" in surname or "W. E. Evans" in surname:
            house_num = "12-13"
        elif "Burton" in surname:
            house_num = "31-33"
        
        if f"Tel. {tel_num}" not in trade:
            trade = f"{trade} (Tel. {tel_num})".strip()

    # 8. Fix split ampersand forenames (e.g. surname='Dutfield', forename='& Frost' -> surname='Dutfield & Frost')
    if forename.startswith("& "):
        surname = f"{surname} {forename}".strip()
        forename = ""

    # 9. Fix building_name that contains house number and resident name (e.g. '35-35A Smith W. H. & Son')
    if bldg_name:
        match_b_num = re.match(r"^(\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?)\s*(.*)$", bldg_name)
        if match_b_num:
            ext_num = match_b_num.group(1).upper()
            rest_name = match_b_num.group(2).strip()
            if not house_num:
                house_num = ext_num
            elif house_num != ext_num and not house_num.endswith(ext_num):
                house_num = f"{house_num}-{ext_num}"
            bldg_name = ""
            if rest_name:
                surname = f"{rest_name} {surname}".strip()

    # 10. Extract house numbers merged into surname or forename (e.g. '35a &', '35A Smith W. H. & Son Ltd.')
    match_s_num = re.match(r"^(\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?)\s*(?:&|\s)\s*(.*)$", surname)
    if match_s_num:
        ext_num = match_s_num.group(1).upper()
        surname = match_s_num.group(2).strip()
        if house_num and house_num != ext_num and not house_num.endswith(ext_num):
            house_num = f"{house_num}-{ext_num}"
        elif not house_num:
            house_num = ext_num

    match_f_num = re.match(r"^(\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?)\s*(?:&|\s)\s*(.*)$", forename)
    if match_f_num:
        ext_num = match_f_num.group(1).upper()
        forename = match_f_num.group(2).strip()
        if house_num and house_num != ext_num and not house_num.endswith(ext_num):
            house_num = f"{house_num}-{ext_num}"
        elif not house_num:
            house_num = ext_num

    # 11. Fix bad ampersand surname rows (e.g. surname='&', forename='13 Evans W. E. & Co.')
    if surname == "&" and forename:
        match = re.match(r"^(\d+(?:-\d+)?)\s+(.*)$", forename)
        if match:
            house_num = match.group(1)
            forename = match.group(2)
        parts = forename.split(" ", 1)
        if len(parts) == 2:
            surname = parts[0]
            forename = f"{parts[1]} &"

    # 12. Handle surnames ending with Ltd / Co (e.g. surname='Dean Ltd', forename='John H' -> surname='John H Dean Ltd', forename='')
    corp_match = re.match(r"^(.*?)\s+(Ltd\.?|Co\.?|& Co\.?|Co\.? Ltd\.?)$", surname, re.I)
    if corp_match and forename and not re.match(r"^\d", forename):
        base_s = corp_match.group(1)
        corp_suf = corp_match.group(2)
        is_person = re.match(r"^[A-Z][a-zA-Z\.]*(?:\s+[A-Z][a-zA-Z\.]*)*$", forename) and not any(w in forename.lower() for w in NON_PERSON_WORDS)
        if is_person:
            surname = f"{forename} {base_s} {corp_suf}".strip()
            forename = ""
        else:
            surname = f"{base_s} {corp_suf}".strip()
            forename = ""

    # 13. Fix cases where forename is initials and surname contains company suffix (e.g. surname='Lovell & Co Ltd', forename='GF')
    if forename and re.match(r"^[A-Z]\.?(?:\s*[A-Z]\.?)*$", forename) and re.search(r"\b(&|ltd|limited|co|company|sons|bros|brothers)\b", surname, re.I):
        surname = f"{forename} {surname}".strip()
        forename = ""

    # 14. Handle location-suffix forenames (e.g. surname='Bollom', forename='of Bristol' -> 'Bollom of Bristol')
    if re.match(r"^of\s+[A-Za-z]", forename, re.I):
        surname = f"{surname} {forename}".strip()
        forename = ""

    # 15. Handle initials + company suffix forenames (e.g. surname='Lovell', forename='GF & Co Ltd' -> surname='GF Lovell & Co Ltd', forename='')
    init_biz_match = re.match(r"^([A-Z]\.?(?:\s*[A-Z]\.?)*)\s+(&(?:.*)|ltd.*|co.*|sons.*|bros.*|limited.*)$", forename, re.I)
    if init_biz_match:
        initials = init_biz_match.group(1).strip()
        biz_suffix = init_biz_match.group(2).strip()
        surname = f"{initials} {surname} {biz_suffix}".strip()
        forename = ""

    # 16. Handle hyphenated trade trapped in forename (e.g. '& Son - cycle factors')
    if " - " in forename:
        parts = forename.split(" - ", 1)
        forename = parts[0].strip()
        extra_trade = parts[1].strip()
        trade = f"{extra_trade}, {trade}".strip(", ") if trade else extra_trade

    # 17. Fix pure business / organization name ordering (e.g. 'Taylor' + '& Son' -> 'Taylor & Son')
    if forename and BUSINESS_SUFFIX_REGEX.search(forename.strip()):
        surname = title_case_name(f"{surname} {forename}".strip())
        forename = ""

    # 18. Extract middle initials trapped in trade (e.g. 'T. mechanic')
    if trade:
        initial_match = re.match(r"^([A-Z]\.)\s+(.*)$", trade)
        if initial_match:
            mid_init = initial_match.group(1)
            trade = initial_match.group(2)
            forename = f"{forename} {mid_init}".strip()

    # 19. Expand Journeyman (j.) / (j) tags
    if "(j.)" in forename.lower() or "(j)" in forename.lower() or "(j.)" in trade.lower() or "(j)" in trade.lower():
        forename = re.sub(r"\s*\([jJ]\.?\)\s*", " ", forename).strip()
        if "(j.)" in trade.lower() or "(j)" in trade.lower():
            trade = re.sub(r"\s*\([jJ]\.?\)\s*", " Journeyman ", trade).strip()
        else:
            trade = f"Journeyman {trade}".strip()

    # 20. Split remaining trades trapped in forenames
    if forename:
        match = re.match(r"^(.*?)\s+([a-z].*)$", forename)
        if match:
            f_part = match.group(1).strip()
            t_part = match.group(2).strip()
            if any(kw in t_part.lower() for kw in TRADE_KEYWORDS) or t_part.startswith("("):
                forename = f_part
                trade = f"{t_part}, {trade}".strip(", ") if trade else t_part

    # 21. Fix non-trade values (company suffixes, house names, forenames, titles, initials, trapped resident names) misparsed into trade column
    if trade:
        if surname in {'&', 'and'} and forename.isdigit() and ',' in trade:
            house_num = f"{house_num}-{forename}".strip("-") if house_num else forename
            surname = ""
            forename = ""
        elif surname in {'&', 'and'} and ',' in trade:
            surname = ""

        # 21a. Extract full name + trade + institution (e.g. "Hitchings, G, steward, Coronation Club & Working Men's Institute")
        m_full = PAT_FULL_CORONATION.match(trade)
        if m_full:
            s_part, fn_part, trade_part, inst_part = m_full.groups()
            if s_part:
                surname = s_part.strip()
            if fn_part:
                forename = fn_part.strip()
            trade = trade_part.strip()
            if not bldg_name or bldg_name == f"{surname} {forename}".strip():
                bldg_name = inst_part.strip()

        # 21b. Extract trapped name + trade (e.g. "Poole, Henry - painter", "Limbrick, Percival Cliff - fish merchant", "Price, Benj")
        else:
            m_name = PAT_NAME_TRADE.match(trade)
            if m_name:
                s_part, fn_part, trade_part = m_name.groups()
                if surname and not bldg_name and surname not in {'&', 'and'}:
                    bldg_name = f"{surname} {forename}".strip()
                surname = s_part.strip()
                forename = fn_part.strip()
                trade = trade_part.strip() if trade_part else ""

                m_sub = PAT_TRADE_INST.match(trade) if trade else None
                if m_sub:
                    sub_trade, sub_inst = m_sub.groups()
                    trade = sub_trade.strip()
                    if not bldg_name or bldg_name == f"{surname} {forename}".strip():
                        bldg_name = sub_inst.strip()

            # 21c. Extract trade + institution (e.g. "steward, Coronation Club & Working Men's Institute", "agent, Powell Duffryn Steam Coal Co")
            else:
                m_inst = PAT_TRADE_INST.match(trade)
                if m_inst:
                    trade_part, inst_part = m_inst.groups()
                    trade = trade_part.strip()
                    if not bldg_name:
                        bldg_name = inst_part.strip()

        # 21c2. Extract trade merged with Villa Name (e.g. "fitter, Springfield", "secretary., Font Burn", "accountant, Harlesden")
        if trade:
            m_tv = PAT_TRADE_VILLA.match(trade)
            if m_tv:
                trade_part, villa_part = m_tv.groups()
                trade_part = trade_part.strip(' .,-')
                villa_part = villa_part.strip(' .,-')
                v_low = villa_part.lower()

                if is_trade_word(trade_part) and villa_part[0].isupper() and len(villa_part) < 40 and not any(nw in v_low for nw in NON_VILLA_WORDS):
                    if any(vw in v_low for vw in VILLA_WORDS) or re.match(r'^[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?$', villa_part):
                        trade = trade_part
                        if not bldg_name:
                            bldg_name = villa_part

        # 21c3. Extract trailing house/building name attached to trade (e.g. "fish merch., High Bank")
        if trade and ("," in trade or " - " in trade):
            m_trail = re.search(r'[\-,]\s*([A-Z][a-zA-Z\s\x27\-]+?\b(?:villa|cottage|house|inn|arms|hotel|chambers|lodge|court|hall|chapel|bank|nook|grove|oaks|limes|firs|laurels|knoll|bungalow|ferns|gables|mount|view|haven|lawn|dingle))\s*$', trade, re.I)
            if m_trail:
                trail_bldg = m_trail.group(1).strip()
                trade = trade[:m_trail.start()].strip(" ,-")
                if not bldg_name:
                    bldg_name = title_case_name(trail_bldg)

        # 21c4. Programmatically move trapped Villa / House names from trade to building_name
        # (e.g. Morthoe, Arbaland, Jpgwyniryn, Caerews, Wembley, Glenbrook, Ridgebourn, Wimborne, St Deniols, Linda Vista, Clevedon V, Hampton V, Helston Vil, Brinley Ho., Cartref, etc.)
        if trade and trade[0].isupper() and not is_trade_word(trade) and not is_person_name_or_title(trade):
            t_low = trade.lower().strip(' ,.-')
            if t_low not in {'g.w.r.', 'g.p.o.', 'p.o.', 'p.c.', 'jp', 'post office', 'general post office', 'hmc', 'h.m.c.', 'customs', 'royal oak'} and not re.search(r'\b(g\.?w\.?r\.?|g\.?p\.?o\.?|p\.?o\.?|p\.?c\.?|j\.?p\.?)\b', t_low):
                if not CROSS_STREET_REGEX.search(trade) and not re.search(r'\b(?:ltd|limited|co|company|works|docks|depot|stores|factory|association|society|hospital|asylum|school|schools|station|railway)\b', t_low) and not re.search(r'\d{2,}', trade) and len(trade) <= 45:
                    if re.search(r'\b(?:villa|villas|vil|v|cottage|cottages|cott|house|ho|inn|arms|hotel|chambers|chamb|cham|lodge|lod|court|hall|chapel|bank|nook|grove|oaks|limes|firs|laurels|knoll|bungalow|ferns|gables|mount|view|haven|lawn|dingle|burn|park|croft)\.?$', t_low) or (1 <= len(t_low.split()) <= 3 and all(w[0].isalpha() for w in t_low.split())):
                        if not bldg_name:
                            bldg_name = title_case_name(trade)
                        trade = ""

        # 21c5. Extract Person Forename/Initials attached via dash to trade
        # (e.g. "Clifford - Carpenter", "Arthur F - Traveller", "Ivor S - Painter", "Walter Hs - Motor Engineer", "Wf - Great Western Railway")
        if trade and "-" in trade:
            m_ndt = re.match(r'^\s*([A-Za-z\.\s]+?)\s*[\-\–]\s*(.*)$', trade)
            if m_ndt:
                left_n = m_ndt.group(1).strip()
                right_t = m_ndt.group(2).strip()

                if left_n and right_t and not is_trade_word(left_n.lower()) and left_n.lower() not in {'surgeon', 'ex', 'holder', 'brewers', 'corn stores', 'docks'}:
                    if is_person_name_or_title(left_n) or (1 <= len(left_n.split()) <= 3 and all(w.lower() in TITLES_AND_FORENAMES or len(w.strip('.')) <= 3 or w[0].isupper() for w in left_n.split())):
                        if forename:
                            forename = f"{forename} {left_n}".strip()
                        else:
                            forename = left_n
                        trade = right_t

        # 21c6. Handle standalone "etc." or "&c." trade entries where occupation is trapped in forename
        # (e.g. forename="L. pawnbroker", trade="etc." -> forename="L.", trade="pawnbroker, etc.")
        if trade and trade.lower().strip(' ,.-') in {'etc', '&c'}:
            if forename and ' ' in forename:
                tokens = forename.split()
                fn_tokens = []
                trade_tokens = []
                for tok in tokens:
                    clean_tok = tok.strip('.,')
                    if clean_tok.lower() in TITLES_AND_FORENAMES or (len(clean_tok) <= 3 and clean_tok[0].isupper()):
                        if not trade_tokens:
                            fn_tokens.append(tok)
                        else:
                            trade_tokens.append(tok)
                    else:
                        trade_tokens.append(tok)
                if trade_tokens:
                    forename = " ".join(fn_tokens)
                    trade = f"{' '.join(trade_tokens)}, etc."

        # 21d. Company Suffix in trade
        if trade and COMPANY_SUFFIX_TRADE_REGEX.match(trade):
            if forename:
                surname = f"{forename} {surname} {trade}".strip()
                forename = ""
            else:
                surname = f"{surname} {trade}".strip()
            trade = ""

        # 21b. Building Name in trade
        elif BUILDING_NAME_TRADE_REGEX.match(trade):
            if not bldg_name:
                bldg_name = trade
            trade = ""

        # 21c. Shifted house name in surname + surname in forename + forename/initials in trade
        elif (is_person_name_or_title(trade) or not trade) and forename and (HOUSE_SUFX.search(surname) or surname in {'Cartref', 'Wynberg', 'Hollybush', 'Arendal', 'Ceinfan', 'Lavengro', 'Blue House Cottage Taylor', 'Belmont House Hilton'}):
            if not bldg_name:
                bldg_name = surname
            surname = forename
            forename = trade
            trade = ""

        # 21d. Person name / title / initials in trade
        elif is_person_name_or_title(trade):
            if not surname and forename:
                surname = forename
                forename = trade
                trade = ""
            elif surname and not forename:
                forename = trade
                trade = ""
            elif surname and forename:
                forename = f"{forename} {trade}".strip()
                trade = ""

        # 21e. Person prefix in trade with embedded trade (e.g. 'Mrs Mary S - fruiterer')
        elif re.match(r'^(mrs|miss|mr)\.?\s+([A-Za-z\.\s]+)\s*[\-,]\s*(.*)$', trade, re.I):
            m = re.match(r'^(mrs|miss|mr)\.?\s+([A-Za-z\.\s]+)\s*[\-,]\s*(.*)$', trade, re.I)
            person_part = f"{m.group(1)} {m.group(2)}".strip()
            real_trade = m.group(3).strip()
            if forename:
                forename = f"{forename} ({person_part})"
            else:
                forename = person_part
            trade = real_trade

    # Extract standalone trade titles mistakenly stored in surname or building_name
    # (e.g. surname="Hairdresser" or building_name="Hairdresser", building_name="Watchmaker", building_name="Butcher")
    TRADES_STANDALONE = {
        "hairdresser", "hairdr'sr", "hairdsr", "butcher", "bchrs", "pork butcher", "porkbutcher",
        "watchmaker", "greengrocer", "grocer", "draper", "baker", "confectioner", "solicitor",
        "fruiterer", "fish bar", "bootmaker", "bootmakers", "tailor", "printer", "stationer",
        "chemist", "dairyman", "builder", "plumber", "painter", "mason", "haulier"
    }

    if surname and surname.strip().lower() in TRADES_STANDALONE:
        if not trade:
            trade = title_case_name(surname)
        surname = ""

    if bldg_name and bldg_name.strip().lower() in TRADES_STANDALONE:
        if not trade:
            trade = title_case_name(bldg_name)
        bldg_name = ""

        # 21f. Normalize trade abbreviations
        if trade:
            if re.search(r'\bg[\.\s]*w[\.\s]*r', trade, re.I):
                trade = re.sub(r'\bG[\.\s]*W[\.\s]*R[\.\s]*', 'G.W.R. ', trade, flags=re.I)
                trade = re.sub(r'G\.W\.R\.\s*[\.,]+', 'G.W.R. ', trade)
                trade = re.sub(r'\s+', ' ', trade).strip()
                trade = re.sub(r'G\.W\.R\.\s*$', 'G.W.R.', trade)
            if re.search(r'\birnwrkr\b', trade, re.I):
                trade = re.sub(r'\birnwrkr\b', 'Ironworker', trade, flags=re.I)
            if re.search(r'\bboot\s+repr\b', trade, re.I):
                trade = re.sub(r'\bboot\s+repr\b', 'Boot Repairer', trade, flags=re.I)
            if re.search(r'\bmtr\s+driver\b', trade, re.I):
                trade = re.sub(r'\bmtr\s+driver\b', 'Motor Driver', trade, flags=re.I)
            if re.search(r'\blabrer\b', trade, re.I):
                trade = re.sub(r'\blabrer\b', 'Labourer', trade, flags=re.I)
            if re.search(r'\btravlr\b', trade, re.I):
                trade = re.sub(r'\btravlr\b', 'Traveller', trade, flags=re.I)
            if re.search(r'\bmachnst\b', trade, re.I):
                trade = re.sub(r'\bmachnst\b', 'Machinist', trade, flags=re.I)
            if re.search(r'\bcaretkr\b', trade, re.I):
                trade = re.sub(r'\bcaretkr\b', 'Caretaker', trade, flags=re.I)
            if re.search(r'\belectcn\b', trade, re.I):
                trade = re.sub(r'\belectcn\b', 'Electrician', trade, flags=re.I)
            if re.search(r'\binsur\.?\s+agent\b', trade, re.I) or re.search(r'\bins\.?\s+agent\b', trade, re.I):
                trade = re.sub(r'\b(insur|ins)\.?\s+agent\b', 'Insurance Agent', trade, flags=re.I)
            if re.search(r'\blorry\s+(drvr|dr)\b', trade, re.I):
                trade = re.sub(r'\blorry\s+(drvr|dr)\b', 'Lorry Driver', trade, flags=re.I)
            if re.search(r'\birn\s+worker\b', trade, re.I):
                trade = re.sub(r'\birn\s+worker\b', 'Iron Worker', trade, flags=re.I)
            if re.search(r'\bstorekpr\b', trade, re.I):
                trade = re.sub(r'\bstorekpr\b', 'Storekeeper', trade, flags=re.I)
            if re.search(r'\bcoal\s+trimr\b', trade, re.I):
                trade = re.sub(r'\bcoal\s+trimr\b', 'Coal Trimmer', trade, flags=re.I)
            if re.search(r'\bgreengrcr\b', trade, re.I):
                trade = re.sub(r'\bgreengrcr\b', 'Greengrocer', trade, flags=re.I)
            if re.search(r'\bbootmkr\b', trade, re.I):
                trade = re.sub(r'\bbootmkr\b', 'Bootmaker', trade, flags=re.I)
            if re.search(r'\bblksmith\b', trade, re.I):
                trade = re.sub(r'\bblksmith\b', 'Blacksmith', trade, flags=re.I)
            if re.search(r'\bmotor\s+mech\b', trade, re.I):
                trade = re.sub(r'\bmotor\s+mech\b', 'Motor Mechanic', trade, flags=re.I)
            if re.search(r'\bshop\s+asst\b', trade, re.I):
                trade = re.sub(r'\bshop\s+asst\b', 'Shop Assistant', trade, flags=re.I)
            if re.search(r'\bwatchmkr\b', trade, re.I):
                trade = re.sub(r'\bwatchmkr\b', 'Watchmaker', trade, flags=re.I)
            if re.search(r'\bengine\s+(drvr|drivr)\b', trade, re.I):
                trade = re.sub(r'\bengine\s+(drvr|drivr)\b', 'Engine Driver', trade, flags=re.I)
            if re.search(r'\bcranedvr\b', trade, re.I):
                trade = re.sub(r'\bcranedvr\b', 'Cranedriver', trade, flags=re.I)
            if re.search(r'\bstlwrkr\b', trade, re.I):
                trade = re.sub(r'\bstlwrkr\b', 'Steelworker', trade, flags=re.I)
            if re.search(r'\b(ironwrkr|ironworkr|iworker|irn\s+worker)\b', trade, re.I):
                trade = re.sub(r'\b(ironwrkr|ironworkr|iworker|irn\s+worker)\b', 'Ironworker', trade, flags=re.I)

            # Acronym dot cleanups
            if re.search(r'\bg[\.\s]*p[\.\s]*o', trade, re.I):
                trade = re.sub(r'\bG[\.\s]*P[\.\s]*O[\.\s]*', 'G.P.O. ', trade, flags=re.I)
                trade = re.sub(r'G\.P\.O\.\s*[\.,]+', 'G.P.O. ', trade)
                trade = re.sub(r'\s+', ' ', trade).strip()
                trade = re.sub(r'G\.P\.O\.\s*$', 'G.P.O.', trade)

            if re.search(r'\bp[\.\s]*o\b', trade, re.I) and not re.search(r'g\.?p\.?o', trade, re.I):
                trade = re.sub(r'\bP[\.\s]*O[\.\s]*', 'P.O. ', trade, flags=re.I)
                trade = re.sub(r'P\.O\.\s*[\.,]+', 'P.O. ', trade)
                trade = re.sub(r'\s+', ' ', trade).strip()
                trade = re.sub(r'P\.O\.\s*$', 'P.O.', trade)

            if re.search(r'\bp[\.\s]*c\b', trade, re.I):
                trade = re.sub(r'\bP[\.\s]*C[\.\s]*', 'P.C. ', trade, flags=re.I)
                trade = re.sub(r'P\.C\.\s*[\.,]+', 'P.C. ', trade)
                trade = re.sub(r'\s+', ' ', trade).strip()
                trade = re.sub(r'P\.C\.\s*$', 'P.C.', trade)

            if re.search(r'\bj[\.\s]*p\b', trade, re.I):
                trade = re.sub(r'\bJ[\.\s]*P[\.\s]*', 'JP ', trade, flags=re.I)
                trade = re.sub(r'JP\s*[\.,]+', 'JP ', trade)
                trade = re.sub(r'\s+', ' ', trade).strip()
                trade = re.sub(r'JP\s*$', 'JP', trade)

            if re.search(r'\b(eng\.?\s+driver|engine\s+(drvr|drivr))\b', trade, re.I):
                trade = re.sub(r'\b(eng\.?\s+driver|engine\s+(drvr|drivr))\b', 'Engine Driver', trade, flags=re.I)
            if re.search(r'\b(engnr|engr)\b', trade, re.I):
                trade = re.sub(r'\b(engnr|engr)\b', 'Engineer', trade, flags=re.I)
            if re.search(r'\bgov\.?\s+offcl\b', trade, re.I):
                trade = re.sub(r'\bgov\.?\s+offcl\b', 'Government Official', trade, flags=re.I)
            if re.search(r'\bdk\s+police\b', trade, re.I):
                trade = re.sub(r'\bdk\s+police\b', 'Dock Police', trade, flags=re.I)
            if re.search(r'\bldg\s+ho\b', trade, re.I):
                trade = re.sub(r'\bldg\s+ho\b', 'Lodging House', trade, flags=re.I)
            if re.search(r'\bdrapers\s+collctr\b', trade, re.I):
                trade = re.sub(r'\bdrapers\s+collctr\b', 'Drapers Collector', trade, flags=re.I)
            if re.search(r'\bgas\s+inspct\b', trade, re.I):
                trade = re.sub(r'\bgas\s+inspct\b', 'Gas Inspector', trade, flags=re.I)
            if re.search(r'\bblrmr\b', trade, re.I):
                trade = re.sub(r'\bblrmr\b', 'Boilermaker', trade, flags=re.I)
            if re.search(r'\bcustom\s+offr\b', trade, re.I):
                trade = re.sub(r'\bcustom\s+offr\b', 'Custom Officer', trade, flags=re.I)
            if re.search(r'\bglass\s+(wrkr|wk)\b', trade, re.I):
                trade = re.sub(r'\bglass\s+(wrkr|wk)\b', 'Glass Worker', trade, flags=re.I)
            if re.search(r'\bice\s+cream\s+vendr\b', trade, re.I):
                trade = re.sub(r'\bice\s+cream\s+vendr\b', 'Ice Cream Vendor', trade, flags=re.I)
            if re.search(r'\bcoal\s+tipr\b', trade, re.I):
                trade = re.sub(r'\bcoal\s+tipr\b', 'Coal Tipper', trade, flags=re.I)
            if re.search(r'\bdentst\b', trade, re.I):
                trade = re.sub(r'\bdentst\b', 'Dentist', trade, flags=re.I)
            if re.search(r'\bbus\s+drvi\b', trade, re.I):
                trade = re.sub(r'\bbus\s+drvi\b', 'Bus Driver', trade, flags=re.I)
            if re.search(r'\bwagon\s+rp\b', trade, re.I):
                trade = re.sub(r'\bwagon\s+rp\b', 'Wagon Repairer', trade, flags=re.I)
            if re.search(r'\b(electcn|electrn|elect|elct)\b', trade, re.I) and not re.search(r'\belectrician\b', trade, re.I):
                trade = re.sub(r'\b(electcn|electrn|elect|elct)\b', 'Electrician', trade, flags=re.I)
            if re.search(r'\bflour\s+packr\b', trade, re.I):
                trade = re.sub(r'\bflour\s+packr\b', 'Flour Packer', trade, flags=re.I)
            if re.search(r'\broad\s+swp\b', trade, re.I):
                trade = re.sub(r'\broad\s+swp\b', 'Road Sweeper', trade, flags=re.I)
            if re.search(r'\b(ironwor|ironwrkr|ironworkr|iworker|irn\s+worker)\b', trade, re.I):
                trade = re.sub(r'\b(ironwor|ironwrkr|ironworkr|iworker|irn\s+worker)\b', 'Ironworker', trade, flags=re.I)
            if re.search(r'\bbuilding\s+contr\s*&\s*engnrs\b', trade, re.I):
                trade = re.sub(r'\bbuilding\s+contr\s*&\s*engnrs\b', 'Building Contractors and Engineers', trade, flags=re.I)
            if re.search(r'\bsales\s+drvr\b', trade, re.I):
                trade = re.sub(r'\bsales\s+drvr\b', 'Sales Driver', trade, flags=re.I)
            if re.search(r'\btbeworker\b', trade, re.I):
                trade = re.sub(r'\btbeworker\b', 'Tubeworker', trade, flags=re.I)
            if re.search(r'\bshoe\s+repr\b', trade, re.I):
                trade = re.sub(r'\bshoe\s+repr\b', 'Shoe Repairer', trade, flags=re.I)
            if re.search(r'\bsteehvorkr\b', trade, re.I):
                trade = re.sub(r'\bsteehvorkr\b', 'Steelworker', trade, flags=re.I)
            if re.search(r'\bcrane\s+dr\b', trade, re.I):
                trade = re.sub(r'\bcrane\s+dr\b', 'Crane Driver', trade, flags=re.I)
            if re.search(r'\belec\s+engineer\b', trade, re.I):
                trade = re.sub(r'\belec\s+engineer\b', 'Electrical Engineer', trade, flags=re.I)
            if re.search(r'\bstl\s+worker\b', trade, re.I):
                trade = re.sub(r'\bstl\s+worker\b', 'Steel Worker', trade, flags=re.I)
            if re.search(r'\bmotor\s+(drvr|dr)\b', trade, re.I):
                trade = re.sub(r'\bmotor\s+(drvr|dr)\b', 'Motor Driver', trade, flags=re.I)
            if re.search(r'\bins\s+agt\b', trade, re.I):
                trade = re.sub(r'\bins\s+agt\b', 'Insurance Agent', trade, flags=re.I)
            if re.search(r'\bpostmn\b', trade, re.I):
                trade = re.sub(r'\bpostmn\b', 'Postman', trade, flags=re.I)
            if re.search(r'\bcivil\s+serv(t|nt)\b', trade, re.I):
                trade = re.sub(r'\bcivil\s+serv(t|nt)\b', 'Civil Servant', trade, flags=re.I)
            if re.search(r'\bdk\s+worker\b', trade, re.I):
                trade = re.sub(r'\bdk\s+worker\b', 'Dock Worker', trade, flags=re.I)
            if re.search(r'\btrmr\b', trade, re.I) and not re.search(r'trimmer', trade, re.I):
                trade = re.sub(r'\btrmr\b', 'Trimmer', trade, flags=re.I)
            if re.search(r'\bbricklayr\b', trade, re.I):
                trade = re.sub(r'\bbricklayr\b', 'Bricklayer', trade, flags=re.I)
            if re.search(r'\bsupt\.?\b', trade, re.I) and not re.search(r'superintendent', trade, re.I):
                trade = re.sub(r'\bsupt\.?\b', 'Superintendent', trade, flags=re.I)
            if re.search(r'\bupholstr\b', trade, re.I):
                trade = re.sub(r'\bupholstr\b', 'Upholsterer', trade, flags=re.I)
            if re.search(r'\bloco\s+driver\b', trade, re.I):
                trade = re.sub(r'\bloco\s+driver\b', 'Locomotive Driver', trade, flags=re.I)
            if re.search(r'\bclrk\b', trade, re.I):
                trade = re.sub(r'\bclrk\b', 'Clerk', trade, flags=re.I)
            if re.search(r'\b(steelworkr|steehvorkr|stlwrkr)\b', trade, re.I):
                trade = re.sub(r'\b(steelworkr|steehvorkr|stlwrkr)\b', 'Steelworker', trade, flags=re.I)
            if re.search(r'\bship\s+brkr\b', trade, re.I):
                trade = re.sub(r'\bship\s+brkr\b', 'Ship Broker', trade, flags=re.I)
            if re.search(r'\bfitters\s+hlpr\b', trade, re.I):
                trade = re.sub(r'\bfitters\s+hlpr\b', 'Fitters Helper', trade, flags=re.I)
            if re.search(r'\beng\s+dr\b', trade, re.I):
                trade = re.sub(r'\beng\s+dr\b', 'Engine Driver', trade, flags=re.I)
            if re.search(r'\b(trvlr|travlr)\b', trade, re.I):
                trade = re.sub(r'\b(trvlr|travlr)\b', 'Traveller', trade, flags=re.I)
            if re.search(r'\bmarbl\s+polshr\b', trade, re.I):
                trade = re.sub(r'\bmarbl\s+polshr\b', 'Marble Polisher', trade, flags=re.I)
            if re.search(r'\bcab\s+proprtr\b', trade, re.I):
                trade = re.sub(r'\bcab\s+proprtr\b', 'Cab Proprietor', trade, flags=re.I)
            if re.search(r'\bmonu\.?\s+mason\b', trade, re.I):
                trade = re.sub(r'\bmonu\.?\s+mason\b', 'Monumental Mason', trade, flags=re.I)
            if re.search(r'\brailwymn\b', trade, re.I):
                trade = re.sub(r'\brailwymn\b', 'Railwayman', trade, flags=re.I)
            if re.search(r'\brly\s+foreman\b', trade, re.I):
                trade = re.sub(r'\brly\s+foreman\b', 'Railway Foreman', trade, flags=re.I)
            if re.search(r'\brly\s+inspt\b', trade, re.I):
                trade = re.sub(r'\brly\s+inspt\b', 'Railway Inspector', trade, flags=re.I)
            if re.search(r'\btram\s+inspt\b', trade, re.I):
                trade = re.sub(r'\btram\s+inspt\b', 'Tram Inspector', trade, flags=re.I)
            if re.search(r'\binspt\b', trade, re.I) and not re.search(r'inspector', trade, re.I):
                trade = re.sub(r'\binspt\b', 'Inspector', trade, flags=re.I)
            if re.search(r'\bironw6rker\b', trade, re.I):
                trade = re.sub(r'\bironw6rker\b', 'Ironworker', trade, flags=re.I)
            if re.search(r'\bgeneral\s+grocr\b', trade, re.I):
                trade = re.sub(r'\bgeneral\s+grocr\b', 'General Grocer', trade, flags=re.I)
            if re.search(r'\blaborr\b', trade, re.I):
                trade = re.sub(r'\blaborr\b', 'Labourer', trade, flags=re.I)
            if re.search(r'\bpier\s+mastr\b', trade, re.I):
                trade = re.sub(r'\bpier\s+mastr\b', 'Pier Master', trade, flags=re.I)
            if re.search(r'\bhouse\s+fur\b', trade, re.I):
                trade = re.sub(r'\bhouse\s+fur\b', 'House Furnisher', trade, flags=re.I)
            if re.search(r'\bhatter\s*,\s*,\s*etc\b', trade, re.I):
                trade = re.sub(r'\bhatter\s*,\s*,\s*etc\b', 'Hatter, etc.', trade, flags=re.I)
            if re.search(r'\bboot\s+manuftrs\b', trade, re.I):
                trade = re.sub(r'\bboot\s+manuftrs\b', 'Boot Manufacturers', trade, flags=re.I)
            if re.search(r'\bphotogrpr\b', trade, re.I):
                trade = re.sub(r'\bphotogrpr\b', 'Photographer', trade, flags=re.I)
            if re.search(r'\bmotormn\b', trade, re.I):
                trade = re.sub(r'\bmotormn\b', 'Motorman', trade, flags=re.I)
            if re.search(r'\btug\s+drvr\b', trade, re.I):
                trade = re.sub(r'\btug\s+drvr\b', 'Tug Driver', trade, flags=re.I)
            if re.search(r'\belec\.?\s+eng\b', trade, re.I) and not re.search(r'electrical engineer', trade, re.I):
                trade = re.sub(r'\belec\.?\s+eng\b', 'Electrical Engineer', trade, flags=re.I)
            if re.search(r'\bcoachmn\b', trade, re.I):
                trade = re.sub(r'\bcoachmn\b', 'Coachman', trade, flags=re.I)
            if re.search(r'\brway\s+ganger\b', trade, re.I):
                trade = re.sub(r'\brway\s+ganger\b', 'Railway Ganger', trade, flags=re.I)
            if re.search(r'\beng\.?\s+drvr\.?\s+g\.?w\.?r\.?\b', trade, re.I):
                trade = re.sub(r'\beng\.?\s+drvr\.?\s+g\.?w\.?r\.?\b', 'Engine Driver G.W.R.', trade, flags=re.I)
            if re.search(r'\bwoodtrnr\b', trade, re.I):
                trade = re.sub(r'\bwoodtrnr\b', 'Woodturner', trade, flags=re.I)
            if re.search(r'\btel\.?\s+clerk\b', trade, re.I):
                trade = re.sub(r'\btel\.?\s+clerk\b', 'Telephone Clerk', trade, flags=re.I)
            if re.search(r'\bstrkr\b', trade, re.I):
                trade = re.sub(r'\bstrkr\b', 'Striker', trade, flags=re.I)
            if re.search(r'\b(l;ab|labour[\x27\x22\x60]?r)\b', trade, re.I):
                trade = re.sub(r'\b(l;ab|labour[\x27\x22\x60]?r)\b', 'Labourer', trade, flags=re.I)
            if re.search(r'\btail;ors\b', trade, re.I):
                trade = re.sub(r'\btail;ors\b', 'Tailors', trade, flags=re.I)
            if re.search(r'\bbrewerr\b', trade, re.I):
                trade = re.sub(r'\bbrewerr\b', 'Brewer', trade, flags=re.I)
            if re.search(r'\bprovision\s+merchanty\b', trade, re.I):
                trade = re.sub(r'\bprovision\s+merchanty\b', 'Provision Merchant', trade, flags=re.I)
            if re.search(r'\bglass\s+blr\b', trade, re.I):
                trade = re.sub(r'\bglass\s+blr\b', 'Glassblower', trade, flags=re.I)
            if re.search(r'\btransp[\x27\x22\x60]?t\s+w[\x27\x22\x60]?r\b', trade, re.I):
                trade = re.sub(r'\btransp[\x27\x22\x60]?t\s+w[\x27\x22\x60]?r\b', 'Transport Worker', trade, flags=re.I)
            if re.search(r'\bcr\.?\s*driver\b', trade, re.I):
                trade = re.sub(r'\bcr\.?\s*driver\b', 'Crane Driver', trade, flags=re.I)
            if re.search(r'\btr[\x27\x22\x60]?mmer\b', trade, re.I):
                trade = re.sub(r'\btr[\x27\x22\x60]?mmer\b', 'Trimmer', trade, flags=re.I)
            if re.search(r'\bhse\s+craft\s+mistress\b', trade, re.I):
                trade = re.sub(r'\bhse\s+craft\s+mistress\b', 'House Craft Mistress', trade, flags=re.I)
            if re.search(r'\bcanteen\s+stwd\b', trade, re.I):
                trade = re.sub(r'\bcanteen\s+stwd\b', 'Canteen Steward', trade, flags=re.I)
            if re.search(r'\biron\s*&\s*metal\s+mcht\s+and\s+marine\s+stores\b', trade, re.I):
                trade = re.sub(r'\biron\s*&\s*metal\s+mcht\s+and\s+marine\s+stores\b', 'Iron & Metal Merchant and Marine Stores', trade, flags=re.I)
            if trade.strip().lower() in {'i.w', 'i.w.'}:
                trade = 'Ironworker'
            if re.search(r'\biworker\s*&\s*shop\b', trade, re.I):
                trade = re.sub(r'\biworker\s*&\s*shop\b', 'Ironworker and Shop', trade, flags=re.I)
            if re.search(r'\bnews\s*&\s*hairdr\b', trade, re.I):
                trade = re.sub(r'\bnews\s*&\s*hairdr\b', 'News and Hairdresser', trade, flags=re.I)
            if re.search(r'\bturf\s+acnt\b', trade, re.I):
                trade = re.sub(r'\bturf\s+acnt\b', 'Turf Accountant', trade, flags=re.I)
            if re.search(r'\bauct[\x27\x22\x60]?nr\b', trade, re.I):
                trade = re.sub(r'\bauct[\x27\x22\x60]?nr\b', 'Auctioneer', trade, flags=re.I)
            if re.search(r'\bship\s+firem[\x27\x22\x60]?n\b', trade, re.I):
                trade = re.sub(r'\bship\s+firem[\x27\x22\x60]?n\b', 'Ship Fireman', trade, flags=re.I)
            if re.search(r'\btubewk\b', trade, re.I):
                trade = re.sub(r'\btubewk\b', 'Tubeworker', trade, flags=re.I)
            if re.search(r'\bdock\s+hnd\b', trade, re.I):
                trade = re.sub(r'\bdock\s+hnd\b', 'Dock Hand', trade, flags=re.I)
            if re.search(r'\bsailr\b', trade, re.I):
                trade = re.sub(r'\bsailr\b', 'Sailor', trade, flags=re.I)
            if re.search(r'\bcellrmn\b', trade, re.I):
                trade = re.sub(r'\bcellrmn\b', 'Cellarman', trade, flags=re.I)
            if re.search(r'\bstewrd\b', trade, re.I):
                trade = re.sub(r'\bstewrd\b', 'Steward', trade, flags=re.I)
            if re.search(r'\bplatelayer\]\b', trade, re.I):
                trade = re.sub(r'\bplatelayer\]\b', 'Platelayer', trade, flags=re.I)
            if re.search(r'\bglass\s+blwr\b', trade, re.I):
                trade = re.sub(r'\bglass\s+blwr\b', 'Glassblower', trade, flags=re.I)
            if re.search(r'\bahopkeeper\b', trade, re.I):
                trade = re.sub(r'\bahopkeeper\b', 'Shopkeeper', trade, flags=re.I)
            if re.search(r'\btime\s+kp\b', trade, re.I):
                trade = re.sub(r'\btime\s+kp\b', 'Timekeeper', trade, flags=re.I)
            if re.search(r'\bpump\s+attd?t\b', trade, re.I):
                trade = re.sub(r'\bpump\s+attd?t\b', 'Pump Attendant', trade, flags=re.I)
            if re.search(r'\bcoal\s+tmr\b', trade, re.I):
                trade = re.sub(r'\bcoal\s+tmr\b', 'Coal Trimmer', trade, flags=re.I)
            if re.search(r'\bblksth\b', trade, re.I):
                trade = re.sub(r'\bblksth\b', 'Blacksmith', trade, flags=re.I)
            if re.search(r'\bschool\s+teach\b', trade, re.I):
                trade = re.sub(r'\bschool\s+teach\b', 'School Teacher', trade, flags=re.I)
            if re.search(r'\bshop\s+ft[\x27\x22\x60]?rs\b', trade, re.I):
                trade = re.sub(r'\bshop\s+ft[\x27\x22\x60]?rs\b', 'Shop Fitters', trade, flags=re.I)
            if re.search(r'\binsurnc\s+agt\b', trade, re.I):
                trade = re.sub(r'\binsurnc\s+agt\b', 'Insurance Agent', trade, flags=re.I)
            if re.search(r'\bhead\s+waitr\b', trade, re.I):
                trade = re.sub(r'\bhead\s+waitr\b', 'Head Waiter', trade, flags=re.I)
            if re.search(r'\brailwaymn\b', trade, re.I):
                trade = re.sub(r'\brailwaymn\b', 'Railwayman', trade, flags=re.I)
            if re.search(r'\bbootmkrs\b', trade, re.I):
                trade = re.sub(r'\bbootmkrs\b', 'Bootmakers', trade, flags=re.I)
            if re.search(r'\bgreengrcrs\b', trade, re.I):
                trade = re.sub(r'\bgreengrcrs\b', 'Greengrocers', trade, flags=re.I)
            if re.search(r'\bpolice\s+sgt\b', trade, re.I):
                trade = re.sub(r'\bpolice\s+sgt\b', 'Police Sergeant', trade, flags=re.I)
            if re.search(r'\btobacnst\b', trade, re.I):
                trade = re.sub(r'\btobacnst\b', 'Tobacconist', trade, flags=re.I)
            if re.search(r'\bbuilders\s+yd\b', trade, re.I):
                trade = re.sub(r'\bbuilders\s+yd\b', 'Builders Yard', trade, flags=re.I)
            if re.search(r'\bsecty\b', trade, re.I):
                trade = re.sub(r'\bsecty\b', 'Secretary', trade, flags=re.I)
            if trade.strip().lower() in {'agt', 'agt.'}:
                trade = 'Agent'
            if re.search(r'\bgenl\s+dealer\b', trade, re.I):
                trade = re.sub(r'\bgenl\s+dealer\b', 'General Dealer', trade, flags=re.I)
            if re.search(r'\bcellarmn\b', trade, re.I):
                trade = re.sub(r'\bcellarmn\b', 'Cellarman', trade, flags=re.I)
            if re.search(r'\btravellr\b', trade, re.I):
                trade = re.sub(r'\btravellr\b', 'Traveller', trade, flags=re.I)
            if re.search(r'\bcycle\s+repr\b', trade, re.I):
                trade = re.sub(r'\bcycle\s+repr\b', 'Cycle Repairer', trade, flags=re.I)
            if re.search(r'\benginemn\b', trade, re.I):
                trade = re.sub(r'\benginemn\b', 'Engineman', trade, flags=re.I)
            if re.search(r'\bpipe\s+fittr\b', trade, re.I):
                trade = re.sub(r'\bpipe\s+fittr\b', 'Pipe Fitter', trade, flags=re.I)
            if re.search(r'\bstocktkr\b', trade, re.I):
                trade = re.sub(r'\bstocktkr\b', 'Stocktaker', trade, flags=re.I)
            if re.search(r'\bwheelwgt\b', trade, re.I):
                trade = re.sub(r'\bwheelwgt\b', 'Wheelwright', trade, flags=re.I)
            if re.search(r'\bwardrobe\s+dlr\b', trade, re.I):
                trade = re.sub(r'\bwardrobe\s+dlr\b', 'Wardrobe Dealer', trade, flags=re.I)
            if re.search(r'\bdecor[\x27\x22\x60]?tr\b', trade, re.I):
                trade = re.sub(r'\bdecor[\x27\x22\x60]?tr\b', 'Decorator', trade, flags=re.I)
            if re.search(r'\bboilermk\b', trade, re.I):
                trade = re.sub(r'\bboilermk\b', 'Boilermaker', trade, flags=re.I)
            if re.search(r'\bpltlyr\b', trade, re.I):
                trade = re.sub(r'\bpltlyr\b', 'Platelayer', trade, flags=re.I)
            if re.search(r'\bi[\x27\x22\x60]?wrkr\b', trade, re.I) or re.search(r'\bi[\x27\x22\x60]worker\b', trade, re.I):
                trade = re.sub(r'\bi[\x27\x22\x60]?wrkr\b', 'Ironworker', trade, flags=re.I)
                trade = re.sub(r'\bi[\x27\x22\x60]worker\b', 'Ironworker', trade, flags=re.I)
            if re.search(r'\bfurnacem\b', trade, re.I):
                trade = re.sub(r'\bfurnacem\b', 'Furnaceman', trade, flags=re.I)
            if re.search(r'\bglass\s+wks\b', trade, re.I):
                trade = re.sub(r'\bglass\s+wks\b', 'Glass Works', trade, flags=re.I)
            if re.search(r'\bins\.?\s+superintendent\b', trade, re.I):
                trade = re.sub(r'\bins\.?\s+superintendent\b', 'Insurance Superintendent', trade, flags=re.I)
            if re.search(r'\bgenl\.?\s+shop\b', trade, re.I):
                trade = re.sub(r'\bgenl\.?\s+shop\b', 'General Shop', trade, flags=re.I)
            if re.search(r'\bwatermn\b', trade, re.I):
                trade = re.sub(r'\bwatermn\b', 'Waterman', trade, flags=re.I)
            if re.search(r'\bshoemkr\b', trade, re.I):
                trade = re.sub(r'\bshoemkr\b', 'Shoemaker', trade, flags=re.I)
            if re.search(r'\b(tubewrkr|tbeworker)\b', trade, re.I):
                trade = re.sub(r'\b(tubewrkr|tbeworker)\b', 'Tubeworker', trade, flags=re.I)
            if re.search(r'\bcarpentr\b', trade, re.I):
                trade = re.sub(r'\bcarpentr\b', 'Carpenter', trade, flags=re.I)
            if re.search(r'\bsec\.?\b', trade, re.I) and not trade.lower().startswith('sec.'):
                trade = re.sub(r'\bsec\.?\b', 'Secretary', trade, flags=re.I)
            elif trade.strip().lower() in {'sec', 'sec.'}:
                trade = 'Secretary'
            if re.search(r'\bmech\b', trade, re.I) and not re.search(r'\bmotor\s+mech\b', trade, re.I):
                trade = re.sub(r'\bmech\b', 'Mechanic', trade, flags=re.I)
            if re.search(r'\belectrn\b', trade, re.I):
                trade = re.sub(r'\belectrn\b', 'Electrician', trade, flags=re.I)
            if re.search(r'\s*&\s*c\.?$', trade, re.I):
                trade = re.sub(r'\s*&\s*c\.?$', ', etc.', trade, flags=re.I)

            trade = re.sub(r'([a-zA-Z]{3,})\.\s*$', r'\1', trade)

            t_low = trade.lower().strip(' ,"-~.')
            
            # Acronyms casing
            acronyms = {
                'p.c.': 'P.C.',
                'p.o. clerk': 'P.O. Clerk',
                'h.m.c': 'H.M.C.',
            }
            if t_low in acronyms:
                trade = acronyms[t_low]
            else:
                changed_words = False
                val = t_low
                if val in TRADE_TYPO_MAP:
                    val = TRADE_TYPO_MAP[val]
                    changed_words = True
                if val in TRADE_EXACT_MAP:
                    val = TRADE_EXACT_MAP[val]
                    changed_words = True
                if val in TRADE_ABBREV_MAP:
                    val = TRADE_ABBREV_MAP[val]
                    changed_words = True

                case_insensitive_standards = {
                    'engine driver', 'coal trimmer', 'motor driver', 'lorry driver',
                    'crane driver', 'insurance agent', 'boot repairer', 'dock labourer',
                    'civil servant', 'police sergeant', 'linotype operator',
                    'inspector of works', 'travelling draper', 'wine and spirit merchant',
                    'junior scale maker', 'ex-police inspector', 'insurance manager',
                    'painter and decorator', 'chemical worker', 'commercial agent',
                    'window cleaner'
                }
                if val in case_insensitive_standards:
                    trade = val
                elif not changed_words and val == trade.strip(' ,"-~.').lower():
                    # Keep original casing if we didn't change the actual text content
                    trade = trade.strip(' ,"-~.')
                else:
                    trade = val

    # Standardize G.p.o. / G.p.o / GPO / G.P.O -> G.P.O.
    pat_gpo = re.compile(r'\b(g\.?p\.?o\.?)\b\.?', re.I)
    surname = pat_gpo.sub('G.P.O.', surname)
    forename = pat_gpo.sub('G.P.O.', forename)
    bldg_name = pat_gpo.sub('G.P.O.', bldg_name)
    trade = pat_gpo.sub('G.P.O.', trade)

    # Expand common forename abbreviations (Thos, Wm, Benj, Geo, Chas, Rbt, Robt, Fredk)
    if forename:
        forename = re.sub(r'\bThos?\.?\b', 'Thomas', forename)
        forename = re.sub(r'\bWm\.?\b', 'William', forename)
        forename = re.sub(r'\bBenj\.?\b', 'Benjamin', forename)
        forename = re.sub(r'\bGeo\.?\b', 'George', forename)
        forename = re.sub(r'\bChas\.?\b', 'Charles', forename)
        forename = re.sub(r'\bRobt?\.?\b', 'Robert', forename)
        forename = re.sub(r'\bFredk?\.?\b', 'Frederick', forename)

    # Clean trailing commas, quotes & spaces
    surname = surname.strip(' ,"-~')
    forename = forename.strip(' ,"-~')
    trade = trade.strip(' ,"-~')

    # 21g. Clean 'void' and 'vacant site' property entries
    comb_sv = f"{surname} {forename}".strip().lower()
    if comb_sv in {"vacant site", "site vacant", "vacant sites", "sites vacant", "site (allotments) vacant", "vacant site (allotments)"} or comb_sv.startswith("vacant site") or comb_sv.startswith("site vacant"):
        surname = ""
        forename = ""
        bldg_name = "Vacant Site"

    if trade.lower() in {'void', 'void.'}:
        trade = ""
        if surname and not is_person_name_or_title(surname) and not bldg_name:
            bldg_name = title_case_name(surname)
            surname = ""

    if surname.lower() in {'void', 'void.'}:
        surname = ""

    if forename.lower() in {'void', 'void.', 'villa void'}:
        forename = ""
        if surname and not is_person_name_or_title(surname) and not bldg_name:
            bldg_name = title_case_name(surname)
            surname = ""

    # Neston Road specific cleanup for reversed names & shifted fields
    if street.strip().lower() == "neston road":
        comb = f"{bldg_name} {surname} {forename}".strip().lower()
        if "building" in comb and "site" in comb:
            bldg_name, surname, forename, trade = "Building Sites", "", "", ""
        elif bldg_name == "Dade R" and surname == "coppersmith" and forename == "Woodville":
            bldg_name, surname, forename, trade = "Woodville", "Dade", "R.", "Coppersmith"
        elif surname == "Nash" and forename == "Jack" and "inglenook" in trade.lower():
            bldg_name, surname, forename, trade = "Inglenook", "Nash", "Jack", "clerk"
        elif bldg_name == "The Gables" and surname == "Elliott" and forename == "Edward":
            bldg_name, surname, forename = "The Gables", "Elliott", "Edward"
        elif bldg_name == "Kenneth H" and surname == "Belvoir" and forename == "Moore":
            bldg_name, surname, forename = "Belvoir", "Moore", "Kenneth H."
        elif bldg_name == "Meadow View" and surname == "Hayward" and forename in ["Robert J", "Robt. J"]:
            bldg_name, surname = "Meadow View", "Hayward"
        elif bldg_name == "Graig Haven" and surname == "Cowmeadow" and forename == "Hector":
            bldg_name, surname, forename = "Graig Haven", "Cowmeadow", "Hector"
        elif bldg_name == "Woodville" and surname == "Dade":
            bldg_name, surname = "Woodville", "Dade"
        else:
            m_rev_50 = re.match(r'^([A-Z][a-zA-Z\x27\-]+)\s+([A-Za-z\.\s]+)$', forename)
            if m_rev_50 and surname and not bldg_name:
                bldg_name, surname, forename = surname, m_rev_50.group(1), m_rev_50.group(2)
            else:
                m_shift_46 = re.match(r'^([A-Z][a-zA-Z\x27\-]+)\s+([A-Za-z\.\s]+)$', bldg_name)
                if m_shift_46 and surname and forename:
                    sn = m_shift_46.group(1)
                    fn = m_shift_46.group(2)
                    if forename.lower() in ['polisher', 'hand']:
                        bldg_name, surname, forename, trade = "", sn, fn, f"{surname} {forename}".strip()
                    else:
                        bldg_name, surname, forename, trade = forename, sn, fn, surname

    # General Shifted Villa Pattern across ALL streets (227 records):
    # bldg_name holds 'Surname Forename', surname holds a trade, forename holds house name
    if bldg_name and surname and forename and not house_num and not trade:
        s_low = surname.lower().strip()
        if s_low in TRADE_KEYWORDS or any(tr in s_low for tr in ['fitter', 'electrician', 'boilermaker', 'labourer', 'postman', 'coppersmith', 'shearer', 'mechanic', 'carpenter', 'painter', 'plumber', 'grocer', 'draper', 'mason', 'butcher', 'baker', 'tailor', 'joiner', 'shunter', 'signalman', 'dairyman', 'builder', 'haulier']):
            m_shift = re.match(r'^([A-Z][a-zA-Z\x27\-]+)\s+([A-Za-z\.\s]+)$', bldg_name)
            if m_shift and not any(k in bldg_name.lower() for k in ['house', 'villa', 'cottage', 'chambers', 'works', 'inn', 'arms', 'hotel', 'building', 'school', 'lodge', 'place', 'hall', 'terrace', 'view', 'court', 'gardens', 'crescent', 'square', 'parade', 'street', 'road', 'lane', 'hill', 'avenue', 'farm', 'dene', 'haven', 'knoll', 'gables', 'bungalow', 'mount', 'wood', 'crest', 'bank', 'grange', 'manor', 'croft', 'retreat']):
                sn = m_shift.group(1)
                fn_real = m_shift.group(2)
                bldg_name = forename
                surname = sn
                forename = fn_real
                trade = title_case_name(s_low)

    # Swapped Forename & Surname Detection & Swap Logic
    # (e.g. forename='Jones', surname='John' -> forename='John', surname='Jones')
    if surname and forename:
        strict_surnames = {"smith", "jones", "williams", "davies", "evans", "roberts", "lewis", "hughes", "morgan", "griffiths", "edwards", "hill", "moore", "clark", "wright"}
        common_forenames = {"john", "william", "thomas", "james", "george", "charles", "henry", "david", "richard", "joseph", "edward", "frederick", "alfred", "arthur", "walter", "frank", "samuel", "robert", "harry", "albert", "ernest", "herbert", "edwin", "benjamin", "daniel"}
        
        sn_low = surname.strip().lower()
        fn_low = forename.strip().lower()
        
        if sn_low in common_forenames and fn_low in strict_surnames:
            surname, forename = title_case_name(forename), title_case_name(surname)

    # Extract trade keywords trapped in forename when trade is empty or incomplete
    if forename and (not trade or len(trade) < 3):
        fn_tokens = forename.split()
        fn_keep = []
        extracted_trades = []
        for tok in fn_tokens:
            tok_clean = tok.strip('.,()')
            tok_low = tok_clean.lower()
            if tok_low in {"mechanic", "clerk", "grocer", "mariner", "driver", "fitter", "carpenter", "platelayer", "labourer", "shoemaker", "draper", "baker", "mason", "rigger", "tailor", "painter", "smith", "builder", "haulier", "fireman", "guard", "joiner", "dealer", "assistant", "manager", "plasterer", "engineer", "inspector", "agent", "blacksmith", "ironworker", "steelworker", "trimmer", "pilot", "brewer", "porter", "dressmaker", "gardener", "milliner", "butcher", "chemist", "solicitor", "accountant", "auctioneer", "surgeon", "dairyman", "newsagent", "decorator", "salesman", "electrician", "hairdresser", "weighman", "fruiterer", "warehouseman", "watchman", "patternmaker", "cabinetmaker", "shunter", "upholsterer"}:
                extracted_trades.append(title_case_name(tok_clean))
            else:
                fn_keep.append(tok)
        if extracted_trades and fn_keep:
            forename = " ".join(fn_keep)
            trade = ", ".join(extracted_trades) if not trade else f"{', '.join(extracted_trades)}, {trade}"

    # Deduplicate repeated identical tokens in surname, forename, and trade
    # (e.g. surname="Dix John Hy", forename="Dix John Hy" -> surname="Dix", forename="John Hy")
    # (e.g. trade="labourer, labourer, labourer" -> trade="Labourer")
    if surname and forename and surname.strip().lower() == forename.strip().lower():
        parts = surname.strip().split()
        if len(parts) >= 2:
            surname = parts[0]
            forename = " ".join(parts[1:])

    def dedupe_field(text):
        if not text: return ""
        parts = [p.strip() for p in text.replace(',', ' ').split() if p.strip()]
        seen = []
        for p in parts:
            if not seen or p.lower() != seen[-1].lower():
                seen.append(p)
        return " ".join(seen)

    if trade and ("," in trade or " " in trade):
        trade_items = [t.strip() for t in trade.split(",") if t.strip()]
        unique_trades = []
        for ti in trade_items:
            if not unique_trades or ti.lower() != unique_trades[-1].lower():
                unique_trades.append(ti)
        trade = ", ".join(unique_trades)

    rec = {
        "year": year,
        "street": street,
        "house_number": house_num,
        "building_name": bldg_name,
        "surname": surname,
        "forename": forename,
        "trade": trade,
    }

    # 21. Apply Structured Edge-Case Overrides from edge_cases.json
    rec = apply_edge_cases(rec)
    if rec is None:
        return None

    if not rec["surname"] and not rec["forename"] and not rec["trade"] and not rec["building_name"]:
        return None

    return rec

def parse_resident_line(text):
    text = text.strip(' ,.-')

    # Case 1: "Brown Lorenzo, mariner" or "Heaven Hy., Weigher"
    if ',' in text:
        name_part, trade_part = text.split(',', 1)
        trade_part = trade_part.strip(' ,.-')
        name_tokens = name_part.strip().split()
        if len(name_tokens) >= 2:
            sub_s = name_tokens[0]
            sub_fn = " ".join(name_tokens[1:])
        elif len(name_tokens) == 1:
            sub_s = name_tokens[0]
            sub_fn = ""
        else:
            sub_s, sub_fn = text, ""
        return sub_s, sub_fn, trade_part

    # Case 2: "Rees Jno. Truck Mender" or "Upstone Wm. Carpenter"
    m_dot = re.match(r'^([A-Z][a-zA-Z\x27\-]+)\s+([A-Z][a-zA-Z\.]*?\.?)\s+(.*)$', text)
    if m_dot:
        sub_s = m_dot.group(1)
        sub_fn = m_dot.group(2)
        sub_t = m_dot.group(3).strip(' ,.-')
        return sub_s, sub_fn, sub_t

    tokens = text.split()
    if len(tokens) == 1:
        return tokens[0], "", ""
    elif len(tokens) == 2:
        return tokens[0], tokens[1], ""
    else:
        return tokens[0], tokens[1], " ".join(tokens[2:])

def unpack_row_if_concatenated(row):
    trade = row.get("trade", "").strip()
    if not trade or not re.search(r'[a-zA-Z\.]\d{1,3}\s+[A-Z][a-zA-Z]', trade):
        return [row]

    m_first = re.search(r'^([^\d]*?)(\d{1,3})\s+([A-Z].*)$', trade)
    if not m_first:
        return [row]

    initial_trade = m_first.group(1).strip(' ,.-')
    rem = m_first.group(2) + " " + m_first.group(3)

    unpacked = []
    r_first = dict(row)
    r_first["trade"] = initial_trade
    unpacked.append(r_first)

    parts = re.findall(r'(\d{1,3})\s+([A-Z][^\d]+?)(?=\d{1,3}\s+[A-Z]|$)', rem)
    for sub_hno, sub_text in parts:
        sub_text = sub_text.strip(' ,.-')
        sub_s, sub_fn, sub_t = parse_resident_line(sub_text)
        unpacked.append({
            "year": row.get("year", ""),
            "street": row.get("street", ""),
            "house_number": sub_hno,
            "building_name": row.get("building_name", ""),
            "surname": sub_s,
            "forename": sub_fn,
            "trade": sub_t
        })
    return unpacked

def main():
    rows = []
    skipped_count = 0
    
    with open(INPUT_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for raw_row in reader:
            # Unpack 1886 Crindau Gas Works run-on blob
            if raw_row.get("street") == "Crindau Road" and raw_row.get("year") == "1886" and "Williams Joseph" in raw_row.get("trade", ""):
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "1", "building_name": "Workmen's Cottage", "surname": "Manley", "forename": "Michael", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "2", "building_name": "Workmen's Cottage", "surname": "Williams", "forename": "Joseph", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "3", "building_name": "Workmen's Cottage", "surname": "Gane", "forename": "Joshua", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "4", "building_name": "Workmen's Cottage", "surname": "Sweet", "forename": "Robert", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "5", "building_name": "Workmen's Cottage", "surname": "Murphy", "forename": "Michael", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "6", "building_name": "Workmen's Cottage", "surname": "Hiscocks", "forename": "Henry", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "", "building_name": "Crindau Gas Works", "surname": "Crindau Gas Works", "forename": "", "trade": "gas works"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "", "building_name": "Glass Works", "surname": "South Wales Glass Manufacturing Co.", "forename": "", "trade": "glass works"})
                continue
                
            # Unpack 1899 Crindau Road clean records to bypass horizontal column-merging glitches
            if raw_row.get("street") == "Crindau Road" and raw_row.get("year") == "1899":
                if not hasattr(main, "crindau_1899_done"):
                    main.crindau_1899_done = True
                    blob_crindau = [
                        {"year": "1899", "street": "Crindau Road", "house_number": "", "building_name": "Crindau House", "surname": "Evans", "forename": "T. L.", "trade": ""},
                        {"year": "1899", "street": "Crindau Road", "house_number": "", "building_name": "Crindau House", "surname": "Hutchins", "forename": "John", "trade": ""},
                        {"year": "1899", "street": "Crindau Road", "house_number": "1", "building_name": "", "surname": "Void", "forename": "", "trade": ""},
                        {"year": "1899", "street": "Crindau Road", "house_number": "2", "building_name": "Hill Side Villa", "surname": "May", "forename": "George", "trade": ""},
                        {"year": "1899", "street": "Crindau Road", "house_number": "3", "building_name": "", "surname": "Young", "forename": "George", "trade": "timekeeper"},
                        {"year": "1899", "street": "Crindau Road", "house_number": "4", "building_name": "", "surname": "Uzzell", "forename": "A. H.", "trade": "fruiterer"},
                        {"year": "1899", "street": "Crindau Road", "house_number": "5", "building_name": "", "surname": "Bishop", "forename": "Joseph", "trade": "foreman"},
                        {"year": "1899", "street": "Crindau Road", "house_number": "6", "building_name": "", "surname": "Smith", "forename": "Luke", "trade": "labourer"},
                        {"year": "1899", "street": "Crindau Road", "house_number": "", "building_name": "Crindau Gas Works", "surname": "", "forename": "", "trade": ""},
                        {"year": "1899", "street": "Crindau Road", "house_number": "", "building_name": "South Wales Glass Works", "surname": "South Wales Glass Manufacturing Co.", "forename": "", "trade": "glass manufacturers"},
                        {"year": "1899", "street": "Crindau Road", "house_number": "", "building_name": "Glass Works House", "surname": "Hyslop", "forename": "Robert", "trade": "manager"}
                    ]
                    for r in blob_crindau:
                        cleaned_r = clean_record(r)
                        if cleaned_r:
                            rows.append(cleaned_r)
                continue

            # Unpack Fair Oak Avenue 1886 multi-resident run-on blob
            if raw_row.get("year") == "1886" and "Torquay villasTeale" in raw_row.get("trade", ""):
                blob1 = [
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "5", "building_name": "", "surname": "Watkins", "forename": "William", "trade": "milkman"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "6", "building_name": "", "surname": "Pugsley", "forename": "Miss", "trade": "ladies school"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Fair Oak Nursery", "surname": "Jones", "forename": "W.", "trade": "nurseryman"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "1", "building_name": "Torquay Villas", "surname": "Dixon", "forename": "H.", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "2", "building_name": "Torquay Villas", "surname": "Teale", "forename": "E. H.", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Seaton House", "surname": "Happerfield", "forename": "D.", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Lynton Villa", "surname": "Winson", "forename": "Alfred", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Clyde Villa", "surname": "Lewis", "forename": "W. H.", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Dan Y Rhiw", "surname": "Clarke", "forename": "John", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Wilks", "forename": "Alfd.", "trade": "engineer"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "White", "forename": "Fredk.", "trade": "carpenter"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Gundy", "forename": "James", "trade": "labourer"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Newman", "forename": "George", "trade": "signal fitter"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Reeve", "forename": "John", "trade": "bricklayer"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Cambria Cottages", "surname": "Wilks", "forename": "Mrs. Rebecca", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Parsons", "forename": "Ivor", "trade": "gardener"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Short", "forename": "Charles", "trade": "master mariner"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Clifton Terrace", "surname": "Blackman", "forename": "Mrs.", "trade": ""}
                ]
                for r in blob1:
                    rows.append(clean_record(r))
                continue

            # Unpack Fair Oak Terrace 1886 multi-resident run-on blob
            if raw_row.get("year") == "1886" and "PRIMROSE COTTAGES-James" in raw_row.get("trade", ""):
                blob2 = [
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "13", "building_name": "", "surname": "Morgan", "forename": "Mat.", "trade": "milkman"},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "James", "forename": "Edwd.", "trade": "plasterer"},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "Edwards", "forename": "Chas.", "trade": "labourer"},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "Taverner", "forename": "Mrs. Emma", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "George", "forename": "Thos.", "trade": "pork butcher"},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "Morgan", "forename": "John", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "Warren", "forename": "James", "trade": "labourer"}
                ]
                for r in blob2:
                    rows.append(clean_record(r))
                continue

            # Unpack James Street 1886 multi-resident run-on blob
            if raw_row.get("year") == "1886" and "From Marion street-Anstee" in raw_row.get("trade", ""):
                blob3 = [
                    {"year": "1886", "street": "James Street", "house_number": "11", "building_name": "", "surname": "Corbin", "forename": "John", "trade": "hobbler"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Anstee", "forename": "Charles", "trade": "greengrocer"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Carpenter", "forename": "John", "trade": "plasterer"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Casey", "forename": "Thomas", "trade": "coal trimmer"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Betts", "forename": "Edward", "trade": "blockmaker"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Hunt", "forename": "James", "trade": "labourer"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Charles", "forename": "Maria", "trade": "widow"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Briscoll", "forename": "Peter", "trade": "labourer"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Lewis", "forename": "Eleanor", "trade": "widow"}
                ]
                for r in blob3:
                    rows.append(clean_record(r))
                continue

            # Unpack Rodney Parade 1886 multi-resident run-on blob
            if raw_row.get("year") == "1886" and "French Consul, Bridge house" in raw_row.get("trade", ""):
                blob4 = [
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "London Wharf", "surname": "Davies Bros.", "forename": "", "trade": "builders' merchants"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Bridge House", "surname": "Bellaguet", "forename": "Leon", "trade": "French Consul"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Thomas Job & Co.", "forename": "", "trade": "marble slate & monumental works"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Newport Cricket Ground", "surname": "Newport Cricket Ground", "forename": "", "trade": "cricket ground"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Williams' Aerated Water Works", "forename": "", "trade": "aerated water works"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Dunning", "forename": "H. A.", "trade": ""},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Williams", "forename": "Henry L.", "trade": ""},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Price", "forename": "J.", "trade": "weighing machine"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Norman", "forename": "John", "trade": "seaman"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Gridiron Wharf", "surname": "Cheeseman", "forename": "G.", "trade": "gridiron keeper"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Gridiron Wharf", "surname": "Ball", "forename": "Wm.", "trade": "gridiron keeper"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Spittle's Boiler Works", "surname": "Spittle's Boiler Works", "forename": "", "trade": "boiler works"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Rodney Wharf", "surname": "Johns", "forename": "Matthew", "trade": "lime kilns"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Rodney Wharf", "surname": "Fothergill", "forename": "J. C.", "trade": "timber yard and steam saw mills"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Radford", "forename": "George", "trade": "labourer"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Cording", "forename": "Charles", "trade": "sawyer"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Welsh", "forename": "P.", "trade": "berthing master"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Great Western Wharf", "surname": "Happerfield", "forename": "D.", "trade": "manager"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Usk Chemical Works", "surname": "Morris and Griffin", "forename": "", "trade": "chemical works"}
                ]
                for r in blob4:
                    rows.append(clean_record(r))
                continue
            sub_rows = unpack_row_if_concatenated(raw_row)
            for row in sub_rows:
                cleaned = clean_record(row)
                if cleaned is None:
                    skipped_count += 1
                elif isinstance(cleaned, list):
                    rows.extend(cleaned)
                else:
                    st_lower = cleaned.get("street", "").strip().lower()
                    if st_lower in {"newport street list", "newport street"}:
                        skipped_count += 1
                        continue
                        
                    # (1899 Crindau Road is now fully handled via direct raw row injection)
                        
                    # Filter out incorrect 1971 Crindau Road records resulting from Cromwell Road drifts
                    if cleaned.get("year") == "1971" and st_lower == "crindau road":
                        h_num = cleaned.get("house_number", "").strip()
                        first_num_match = re.search(r'\d+', h_num)
                        if first_num_match:
                            val = int(first_num_match.group())
                            if val > 14:
                                skipped_count += 1
                                continue
                        else:
                            # Drop Cromwell Road landmarks
                            sur_low = cleaned.get("surname", "").strip().lower()
                            if any(kw in sur_low for kw in {"watkins", "garage", "methodist", "patrick", "presbytery", "foley", "bosco", "hall", "lavin"}):
                                skipped_count += 1
                                continue
                        
                    # Clear building_name if it mistakenly repeats the street name
                    bldg_val = cleaned.get("building_name", "").strip()
                    if bldg_val and st_lower:
                        bldg_low = bldg_val.lower()
                        if bldg_low == st_lower or bldg_low == st_lower + "s":
                            cleaned["building_name"] = ""

                    rows.append(cleaned)

    # Global deduplication: remove exact identical duplicate rows
    unique_rows = []
    seen_keys = set()
    deduped_count = 0
    for r in rows:
        key = (r.get("year", ""), r.get("street", ""), r.get("house_number", ""), r.get("building_name", ""), r.get("surname", ""), r.get("forename", ""), r.get("trade", ""), r.get("source_type", ""))
        if key in seen_keys:
            deduped_count += 1
        else:
            seen_keys.add(key)
            unique_rows.append(r)
    rows = unique_rows
    if deduped_count > 0:
        print(f"Deduplicated {deduped_count} exact duplicate records.")

    # 1. Group street names by lowercase value to resolve casing variations automatically
    street_casings = defaultdict(list)
    for row in rows:
        st = row.get("street", "").strip()
        if st:
            street_casings[st.lower()].append(st)
            
    # For each group, find the best casing (mixed case preferred over all-caps)
    casing_map = {}
    for lower_name, variations in street_casings.items():
        variations = list(set(variations))
        if len(variations) == 1:
            continue
            
        mixed = [v for v in variations if any(c.islower() for c in v)]
        uppers = [v for v in variations if not any(c.islower() for c in v)]
        
        # Pick the one with mixed case if available, else pick longest/first
        candidates = mixed if mixed else uppers
        candidates.sort(key=lambda v: (len(v), v), reverse=True)
        best = candidates[0]
        
        for v in variations:
            if v != best:
                casing_map[v] = best
                
    if casing_map:
        print(f"Automatically resolving {len(casing_map)} casing variations...")
        auto_case_count = 0
        for row in rows:
            st = row.get("street", "").strip()
            if st in casing_map:
                row["street"] = casing_map[st]
                auto_case_count += 1
        print(f"Auto-cased {auto_case_count} records.")

    # Apply manual street amendments from review TSV if it exists
    tsv_file = "streets_review_v17.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v16.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v15.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v14.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v13.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v12.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v11.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v10.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v9.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v8.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v7.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v6.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "streets_review_v5.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "Street Amendments v2 - streets_review_v2.tsv"
    if not os.path.exists(tsv_file):
        tsv_file = "Street Amendments - streets_review.tsv"
        
    if os.path.exists(tsv_file):
        amendments = {}
        with open(tsv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for r in reader:
                raw_name = r.get("Street Name", "").strip()
                amended = r.get("Amendment", "").strip()
                if raw_name and amended:
                    amendments[raw_name] = amended
        
        if amendments:
            print(f"Applying {len(amendments)} manual street amendments from {tsv_file}...")
            amended_count = 0
            for row in rows:
                st = row.get("street", "").strip()
                if st in amendments:
                    row["street"] = amendments[st]
                    amended_count += 1
            print(f"Applied manual amendments to {amended_count} records.")

    # Append newly added secondary/gap-year historical research records from edge_cases.json
    added_gap_count = 0
    for edge in EDGE_CASES:
        match = edge.get("match", {})
        apply = edge.get("apply", {})
        # If edge case is a standalone newly added record (has street, year, apply fields but no match criteria except street/year)
        if match.get("street") and match.get("year") and apply.get("surname") and not match.get("surname") and not match.get("surname_contains") and not match.get("house_number"):
            # Check if this exact record is already in rows
            exists = any(r.get("street") == match["street"] and r.get("year") == match["year"] and r.get("surname") == apply.get("surname") for r in rows)
            if not exists:
                new_row = {
                    "year": match["year"],
                    "street": match["street"],
                    "house_number": apply.get("house_number", ""),
                    "building_name": apply.get("building_name", ""),
                    "surname": apply.get("surname", ""),
                    "forename": apply.get("forename", ""),
                    "trade": apply.get("trade", ""),
                    "source_type": apply.get("source_type", "Secondary")
                }
                rows.append(new_row)
                added_gap_count += 1

    if added_gap_count > 0:
        print(f"Appended {added_gap_count} supplemental gap-year historical research records into dataset.")

    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done! Cleaned and normalized {len(rows)} records in {OUTPUT_CSV}. Filtered {skipped_count} header/cross-street/return rows.")

if __name__ == "__main__":
    main()