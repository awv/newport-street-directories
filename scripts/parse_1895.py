import os
import sys
import re
import csv
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from clean_csv import clean_street_name, TRADE_TYPO_MAP, TRADE_EXACT_MAP, TRADE_ABBREV_MAP
except ImportError:
    clean_street_name = lambda x: x.strip()
    TRADE_TYPO_MAP = {}
    TRADE_EXACT_MAP = {}
    TRADE_ABBREV_MAP = {}

STREET_SUFFIXES = {
    'street', 'st', 'road', 'rd', 'avenue', 'ave', 'av', 'place', 'pl',
    'terrace', 'ter', 'lane', 'crescent', 'cres', 'square', 'sq',
    'parade', 'pde', 'hill', 'walk', 'court', 'row', 'wharf', 'quay',
    'dock', 'docks', 'villas', 'gardens', 'mews', 'rise', 'drive',
    'passage', 'market', 'arcade', 'bank', 'grove', 'path', 'close',
    'view', 'way', 'circus', 'circle'
}

KNOWN_STREETS = {
    'baneswell', 'courtybella', 'friars', 'the friars', 'stow', 'stow hill',
    'barnard town', 'cambria', 'melbourne', 'ringland', 'cross-street',
    'cross street', 'cross lane', 'maindee', 'the marshes', 'marshes',
    'belle vue', 'gold tops', 'pentonville', 'alexandra docks'
}

STREET_CORRECTIONS = {
    'carlisle st': 'Carlisle Street',
    'commercial rd': 'Commercial Road',
    'commercial st': 'Commercial Street',
    'courtybella st': 'Courtybella Street',
    'courtybella': 'Courtybella Terrace',
    'manchester st': 'Manchester Street',
    'nelson st': 'Nelson Street',
    'ridge rd': 'Ridge Road',
    'alexandra rd': 'Alexandra Road',
    'alexandra dry dock': 'Alexandra dry dock',
    'alteryn road': 'Allt-yr-yn Road',
    'bishopgate parade': 'Bishopsgate Parade',
    'cambrian wharf': '& Cambrian wharf',
    'clytha park & road': 'Clytha Park Road',
    'chepstable road': 'Chepstow Road',
    'christchurch rd': 'Christchurch Road',
    'constable\'s lane': 'Constable’s Lane',
    'county police court': 'Police Court',
    'esveswell terrace': 'Eveswell Terrace',
    'fair oak terrace': 'Fairoak Terrace',
    'fields  park rd': 'Fields Park Road',
    'fields crescent (rd': 'Fields Crescent Road',
    "friar's road": 'Friars Road',
    "friars' road": 'Friars Road',
    "glo'ster street": 'Gloster Street',
    "hiley's court": "Hiley’s Court",
    "macarthy’s court": "Macarthy's Court",
    "macarthy's court": "Macarthy's Court",
    "mellon square": "Mellon's Square",
    "merriott's place": "Merriott’s Place",
    "merriott’s place": "Merriott’s Place",
    "milbrook terrace": "Millbrook Terrace",
    "moulder's arms ter": "Moulders Arms Terrace",
    "phillips street": "Phillip Street",
    "quiet woman's row": "Quiet Womans Row",
    "queen’s hill terrace": "Queen's Hill Terrace",
    "queen's hill terrace": "Queen's Hill Terrace",
    "queen’s place": "Queen's Place",
    "queen's place": "Queen's Place",
    "rhos llantwit wharf": "Rhos Llantwrt wharf",
    "st john's road": "St. John's Road",
    "st. michael’s st": "St. Michael's St",
    "st. michael's street": "St. Michael's St",
    "st. woollos rd": "St. Woolos Road",
    "stow hill": "Stow hill",
    "stow pk. circus": "Stow Park Circus",
    "the new arcade": "New Arcade",
    "provision market": "Provision Market",
    "upper baldwin st": "Upper Baldwin Street",
    "upper marion street": "Upper Marion Street",
    "vivian street": "Vivian Road",
    "waters' lane": 'Waters Lane',
    "water’s lane": 'Waters Lane',
    "waters lane": 'Waters Lane',
    "west side old dock": "West-side of Old Dock",
}

IGNORED_HEADER_REGEX = re.compile(
    r'\b(?:newport\s+street\s+list|newport\s+street\s+directory|newport\s+directory|street\s+directory|street\s+direction)\b'
    r'|^\s*newport\s*[\.\-—]*$'
    r'|^\s*directory\s*[\.\-—]*$'
    r'|^\s*newport\s+street\s+list[\.\s]*$'
    r'|\b(?:trapnell\s+&\s+gane|house\s+furnishers)\b',
    re.I
)

CROSS_STREET_PAT = re.compile(
    r'\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.)\b.*?\bto\b.*?\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.|square)\b'
    r'|^\s*\[?(?:here\s+are|here\s+is|here\s+cross|\[?return\]?|\(return\.?\)|return\.?)\]?\b'
    r'|^\s*[\(\[]?\s*return\.?\s*[\)\]]?\s*$'
    r'|\bsee\b'
    r'|\bsee\s+also\b'
    r'|\b[a-zA-Z]+see\b'
    r'|^\s*now\s+[a-z0-9\s\.\-|\(\)]+'
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
    r'|\btowards\b',
    re.I
)

NAME_ABBR_PAT = re.compile(
    r'\b(?:mr|mrs|miss|rev|dr|capt|col|hon|snr|jun|esq|wm|thos|geo|chas|edwd|robt|hy|jas|jno|danl|alfd|fredk)\b',
    re.I
)

VALID_WARD_AFTER_COMMA = re.compile(
    r'^\s*(?:P\.|B\.T\.?|B\.t|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|P|M|C|T|B|L|D|E|Pill|Maindee|Crindau|Marshes|Liswerry|Borough|Town|Tunnel|continued|contd|cont|cont\.|cont[\'’]d|contind)\.?\s*$',
    re.I
)

COMMON_TITLES = {'mrs', 'mrs.', 'miss', 'miss.', 'rev', 'rev.', 'dr', 'dr.', 'capt', 'col', 'hon', 'esq', 'mr', 'lord', 'sir'}

KNOWN_TRADE_KEYWORDS = [
    'grocer', 'labourer', 'ironworker', 'ironwrkr', 'ironwkr', 'carpenter', 'mason', 'fitter', 'haulier', 
    'clerk', 'painter', 'seaman', 'smith', 'tailor', 'tailoress', 'butcher', 'trimmer', 'baker', 
    'engineer', 'plasterer', 'guard', 'moulder', 'gardener', 'gard\'nr', 'foreman', 'boilermaker', 
    'boilermakr', 'fireman', 'builder', 'traveller', 'manager', 'hairdresser', 'agent', 'blacksmith', 
    'blksmith', 'greengrocer', 'bootmaker', 'bootmkr', 'signalman', 'shipwright', 'plumber', 'hobbler', 
    'platelayer', 'porter', 'bricklayer', 'rigger', 'shopkeeper', 'shopk\'p\'r', 'mariner', 'shoemaker', 
    'draper', 'steelworker', 'pilot', 'dock pilot', 'confectioner', 'postman', 'driver', 'sawyer', 
    'policeman', 'printer', 'sailor', 'solicitor', 'mechanic', 'machinist', 'steward', 
    'joiner', 'striker', 'miller', 'tobacconist', 'dealer', 'fruiterer', 'caretaker', 
    'inspector', 'decorator', 'warehouseman', 'saddler', 'shunter', 'boatman', 'waterman',
    'hoistman', 'milkman', 'cooper', 'dairyman', 'watchmaker', 'electrician', 'accountant', 
    'hawker', 'fish hawker', 'dressmaker', 'cabinetmaker', 'cabinetmkr', 'wheelwright', 'docker', 'roller', 
    'furnaceman', 'chemist', 'motor driver', 'motorman', 'weighman', 'gasfitter', 'gas fitter', 'puddler', 
    'timekeeper', 'newsagent', 'checker', 'sailmaker', 'coachman', 'stevedore', 
    'storekeeper', 'storeman', 'packer', 'outfitter', 'tinsmith', 'carman', 'cabman', 'cab prop\'rs', 'surgeon', 'ostler', 
    'watchman', 'shearer', 'patternmaker', 'patternmakr', 'architect', 'surveyor', 'dentist', 'shipper', 
    'weigher', 'sheet wghr', 'groundsman', 'mason\'s labr', 'glass worker', 'glass blowr', 
    'glass blower', 'glass wkr', 'glass works', 'glass sorter', 'glassblower', 'brick bnr', 'brick burner', 'brickburner',
    'brick works', 'brickmkr', 'gas worker', 'gas stoker', 'bottle blowr', 'bottle works', 'bottle hand', 'bottle sorter',
    'bottle maker', 'bot\'le blowr', 'bo\'tlehd', 'tinplate w\'k\'r', 'ironf\'d\'r', 'sculptor', 'hoopmaker',
    'tel. linesman', 'lamplighter', 'c.e.', 'coach builder', 'cr.driver', 'crane driver', 
    'boilerm\'r', 'trim\'r', 'bootmakr', 'blksmith', 'engine dvr.', 'engine dvr', 'engine drivr', 'engine driver', 
    'dock police', 'dockpolice', 'glasswkr', 'ironmkr', 'collier', 'miners\' agent', 'p.c.', 'b.t.',
    'brass finisher', 'rivetter', 'riveter', 'horseshoer', 'wood turner', 'optician',
    'fishmonger', 'beer retailer', 'publican', 'innkeeper', 'waiter', 'sugar boiler',
    'telegraphist', 'typewriter', 'nurse', 'midwife', 'cinematograph operator',
    'taxi drivr', 'brewery hd', 'brewery hd.', 'fish bar', 'marine stores',
    'brklayer', 'bottlemaker', 'dk. labourer', 'dk.labourer', 's. mechanic', 'wireman',
    'laundress', 'l\'ndress', 'bookkeeper', 'driller', 'brushmaker', 'quarryman', 'potter', 'stoker'
]

TRADE_REGEX_SPLIT = re.compile(
    r'\b(' + '|'.join(re.escape(t) for t in sorted(KNOWN_TRADE_KEYWORDS, key=len, reverse=True)) + r')\b',
    re.I
)

NAME_TOKENS = {
    'john', 'mary', 'elizabeth', 'james', 'ann', 'anne', 'george', 'william', 
    'thomas', 'david', 'henry', 'sarah', 'jane', 'charles', 'margaret', 'robert', 
    'edward', 'arthur', 'richard', 'joseph', 'samuel', 'frederick', 'alfred', 
    'ellen', 'alice', 'hannah', 'emma', 'martha', 'florence', 'annie', 'edith', 
    'walter', 'albert', 'frank', 'herbert', 'ernest', 'harry', 'harold', 'percy', 
    'sidney', 'sydney', 'edgar', 'clarence', 'emily', 'louisa', 'jno', 'hy', 'wm', 'thos', 'chas', 'edwd', 'geo',
    'e.', 'a.', 'j.', 'h.', 'w.', 'c.', 'g.', 'm.', 'r.', 't.', 'f.', 's.', 'lydia', 'albt', 'eleanor',
    'susan', 'jeannette', 'jeanette', 'selina', 'mercy', 'elisha', 'alfonso', 'enoch', 'capel', 'worthy',
    'eli', 'clement', 'patrick', 'dennis', 'jeremiah', 'reuben', 'hannibal', 'danl', 'rd', 'walt', 'jos', 'sl',
    'harriet', 'minnie', 'maud', 'margt', 'lorenzo', 'ephraim', 'abner', 'hans', 'maurice', 'eliza', 'stephen',
    'humphrey', 'hum', 'oct', 'octavius', 'cor', 'cornelius', 'dan', 'fred', 'tom', 'rob', 'archi', 'archibald'
}

def clean_name_abbr(name):
    if not name:
        return ""
    name = re.sub(r'\bThos?\.?\b', 'Thomas', name)
    name = re.sub(r'\bWm\.?\b', 'William', name)
    name = re.sub(r'\bBenj\.?\b', 'Benjamin', name)
    name = re.sub(r'\bGeo\.?\b', 'George', name)
    name = re.sub(r'\bChas\.?\b', 'Charles', name)
    name = re.sub(r'\bRobt?\.?\b', 'Robert', name)
    name = re.sub(r'\bFredk?\.?\b', 'Frederick', name)
    name = re.sub(r'\bHy\.?\b', 'Henry', name)
    name = re.sub(r'\bEdwd?\.?\b', 'Edward', name)
    name = re.sub(r'\bJno\.?\b', 'John', name)
    name = re.sub(r'\bAlfd?\.?\b', 'Alfred', name)
    name = re.sub(r'\bAlbt\.?\b', 'Albert', name)
    name = re.sub(r'\bRichd?\.?\b', 'Richard', name)
    name = re.sub(r'\bDanl?\.?\b', 'Daniel', name)
    name = re.sub(r'\bSaml?\.?\b', 'Samuel', name)
    name = re.sub(r'\bJas\.?\b', 'James', name)
    name = re.sub(r'\bWalt\.?\b', 'Walter', name)
    name = re.sub(r'\bRd\.?\b', 'Richard', name)
    name = re.sub(r'\bJos\.?\b', 'Joseph', name)
    name = re.sub(r'\bSl\.?\b', 'Samuel', name)
    name = re.sub(r'\bHbt\.?\b', 'Herbert', name)
    name = re.sub(r'\bRbt\.?\b', 'Robert', name)
    name = re.sub(r'\bEdw\.?\b', 'Edward', name)
    name = re.sub(r'\bFdk\.?\b', 'Frederick', name)
    name = re.sub(r'\bNath\.?\b', 'Nathaniel', name)
    name = re.sub(r'\bHum\.?\b', 'Humphrey', name)
    name = re.sub(r'\bOct\.?\b', 'Octavius', name)
    name = re.sub(r'\bCor\.?\b', 'Cornelius', name)
    name = re.sub(r'\bArchi\.?\b', 'Archibald', name)
    name = re.sub(r'\bFred\.?\b', 'Frederick', name)
    name = re.sub(r'\bDan\.?\b', 'Daniel', name)
    name = re.sub(r'\bMargt\.?\b', 'Margaret', name)
    return name.strip(' ,"-~.')

def clean_trade(trade):
    if not trade:
        return ""
    t_clean = trade.strip(' ,"-~.')
    t_low = t_clean.lower()
    
    acronym_map = {
        'p.c.': 'P.C.',
        'p.o. clerk': 'P.O. Clerk',
        'h.m.c': 'H.M.C.',
        'c.e.': 'C.E.',
        'c.e': 'C.E.'
    }
    if t_low in acronym_map:
        return acronym_map[t_low]

    local_abbrev = {
        'engine drivr': 'engine driver',
        'engine dvr': 'engine driver',
        'engine dvr.': 'engine driver',
        'tinplate w\'k\'r': 'tinplate worker',
        'ironf\'d\'r': 'ironfounder',
        'patternmakr': 'patternmaker',
        'mas. mar.': 'master mariner',
        'mas. mar': 'master mariner',
        'c.e.': 'C.E.',
        'bot\'le blowr': 'bottle blower',
        'bo\'tlehd': 'bottle hand',
        'bottle hand': 'bottle hand',
        'bottle sorter': 'bottle sorter',
        'bottle maker': 'bottle maker',
        'lab\'r': 'labourer',
        'lab\'rer': 'labourer',
        'labour\'r': 'labourer',
        'glass works': 'glass worker',
        'glass wks': 'glass worker',
        'brick works': 'brick worker',
        'brickburner': 'brick burner',
        'brickmkr': 'brickmaker',
        'cabinetmkr': 'cabinetmaker',
        'tel. linesman': 'telegraph linesman',
        'cab prop\'rs': 'cab proprietor',
        'm. mason': 'monumental mason',
        'r. clerk': 'railway clerk'
    }
    if t_low in local_abbrev:
        return local_abbrev[t_low]

    val = t_low
    if val in TRADE_TYPO_MAP:
        val = TRADE_TYPO_MAP[val]
    if val in TRADE_EXACT_MAP:
        val = TRADE_EXACT_MAP[val]
    if val in TRADE_ABBREV_MAP:
        val = TRADE_ABBREV_MAP[val]

    case_insensitive_standards = {
        'engine driver', 'coal trimmer', 'motor driver', 'lorry driver',
        'crane driver', 'insurance agent', 'boot repairer', 'dock labourer',
        'civil servant', 'police sergeant', 'linotype operator',
        'inspector of works', 'travelling draper', 'wine and spirit merchant',
        'junior scale maker', 'ex-police inspector', 'insurance manager',
        'painter and decorator', 'chemical worker', 'commercial agent',
        'window cleaner', 'dock police', 'master mariner', 'gas worker',
        'glass blower', 'glass worker', 'dock pilot'
    }
    if val in case_insensitive_standards:
        return val

    return val

def is_forename_token(token):
    if not token:
        return False
    t_clean = token.strip(' ,"-~.').lower()
    t_raw = token.strip(' ,"-~')
    if t_clean in COMMON_TITLES or t_clean.rstrip('.') in COMMON_TITLES:
        return True
    if t_clean in NAME_TOKENS or t_clean.rstrip('.') in NAME_TOKENS:
        return True
    if len(t_clean) == 1 and t_clean.isalpha():
        return True
    if re.match(r'^[a-zA-Z]\.$', t_raw) or re.match(r'^[a-zA-Z]\.\s*[a-zA-Z]\.?$', t_raw):
        return True
    if token.endswith(','):
        return True
    known_fn_abbrs = {'wm', 'geo', 'thos', 'chas', 'hy', 'edwd', 'rd', 'walt', 'jos', 'albt', 'alfd', 'jas', 'benj', 'fredk', 'sl', 'danl', 'hbt', 'rbt', 'saml', 'fdk', 'nath', 'edw', 'hum', 'oct', 'cor', 'archi', 'fred', 'dan', 'margt'}
    if t_clean in known_fn_abbrs or t_clean.rstrip('.') in known_fn_abbrs:
        return True
    return False

def is_valid_street_name(s):
    if not s:
        return False
    s = s.strip()
    if IGNORED_HEADER_REGEX.search(s):
        return False
    if re.match(r'^\d+', s):
        return False
    if CROSS_STREET_PAT.search(s):
        return False
    if s.lower().startswith(('and ', 'or ', 'of ', 'at ', 'in ', 'near ', 'behind ', 'opposite ', 'with ', 'see ')):
        return False
        
    if ',' in s:
        parts = s.split(',', 1)
        before_comma = parts[0].strip()
        after_comma = parts[1].strip()
        if not VALID_WARD_AFTER_COMMA.match(after_comma):
            return False
        s_candidate = before_comma
    else:
        s_candidate = s
        
    s_clean = re.sub(r'[\s\-—–_]+(?:continued|contd|cont|cont\.|cont[\'’]d|contind)\b', '', s_candidate, flags=re.I).strip()
    s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,–_')
    
    if not re.search(r'\bHigh\s+Street\b', s_clean, re.I):
        s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.?|B\.t|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|[PMCTBLDE])\s*$', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,–_')
    
    if NAME_ABBR_PAT.search(s_clean):
        return False
        
    words = [w.strip('.,()-"\'–_') for w in s_clean.lower().split() if w.strip('.,()-"\'–_')]
    if not words:
        return False

    if any(re.match(r'^[a-z]\.?$', w) for w in words[:-1]):
        return False
        
    if len(words) < 2 and s_clean.lower() not in KNOWN_STREETS:
        return False
        
    if re.search(r'\b(?:ltd|limited|co|coy|chants|merchants|works|inn|hotel|tavern|brewery)\b', s_clean, re.I):
        return False
        
    last_word = words[-1]
    is_st = last_word in STREET_SUFFIXES or s_clean.lower() in KNOWN_STREETS
    return is_st

def parse_tsv(input_path, output_path):
    records = []
    current_street = ""
    streets_found = Counter()

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, start=1):
        parts = [p.replace('\\t', '').replace('\\n', '').strip() for p in line.rstrip('\r\n').split('\t')]
        while len(parts) < 6:
            parts.append('')
            
        if not any(parts):
            continue
            
        if any(IGNORED_HEADER_REGEX.search(p) for p in parts if p):
            continue

        first_cand = next((p for p in parts[:3] if p), '')
        is_street = False
        matched_street = ""

        if first_cand and is_valid_street_name(first_cand):
            is_street = True
            matched_street = first_cand
        elif first_cand and first_cand.strip().upper() in {"HIGH STREET, P.", "HIGH STREET, P"}:
            is_street = True
            matched_street = "HIGH STREET, PILL"
        else:
            for p in parts[:2]:
                p_clean = p.strip(' .,-_~()[]')
                if p_clean.lower() in {"cross lane", "cross street"}:
                    is_street = True
                    matched_street = p_clean.upper()
                    break

        if is_street:
            s_clean = re.sub(r'^[\(\[]?\s*return[\.\)]*\s*', '', matched_street, flags=re.I).strip('. -—')
            s_clean = re.sub(r'[\s\-—–_]+(?:continued|contd|cont|cont\.|cont[\'’]d|contind)\b', '', s_clean, flags=re.I).strip()
            s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
            s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
            if not re.search(r'\bHigh\s+Street\b', s_clean, re.I):
                s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.?|B\.t|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|[PMCTBLDE])\s*$', '', s_clean, flags=re.I).strip()
            
            s_clean = re.sub(r'^(?:Up|Upp)[\.\s]+', 'Upper ', s_clean, flags=re.I).strip()
            if s_clean.lower().startswith('upper '):
                s_clean = 'Upper ' + ' '.join(w.capitalize() for w in s_clean[6:].split())
            
            s_norm = clean_street_name(s_clean)
            s_norm = re.sub(r"'([A-Z])\b", lambda m: f"'{m.group(1).lower()}", s_norm)
            
            s_low = s_norm.lower()
            if s_low in STREET_CORRECTIONS:
                s_norm = STREET_CORRECTIONS[s_low]

            current_street = s_norm
            streets_found[current_street] += 1
            if not any(parts[1:]):
                continue
            else:
                if parts[0] == matched_street:
                    parts[0] = ''

        combined_row = ' '.join([p for p in parts if p]).strip()
        if re.match(r'^[\s\*\-\_\=\#\+]+$', combined_row):
            continue
        if CROSS_STREET_PAT.search(combined_row):
            continue
        if not current_street:
            continue
        if parts[0] == 'Number' and parts[1] == 'Forenames':
            continue

        h_num = parts[0]
        col1 = parts[1]
        col2 = parts[2]
        col3 = parts[3]
        bldg = parts[4]

        # Skip ad row: e.g. 0 Trapnell & Gane
        if h_num == '0' and not col2 and 'Trapnell' in col1:
            continue

        # If col0 has house number and resident text combined (e.g. "4 Wm. H. Shute")
        if not col1 and not col2 and not col3 and h_num:
            raw_text = h_num.strip()
            m_num = re.match(r'^(\d+(?:[a-zA-Z]|\s*-\s*\d+)?)\s+(.*)$', raw_text)
            if m_num:
                h_num = m_num.group(1).replace(' ', '')
                rest = m_num.group(2).strip()
            else:
                h_num = ''
                rest = raw_text
            tokens = rest.split(maxsplit=1)
            col1 = tokens[0] if tokens else ""
            col2 = tokens[1] if len(tokens) > 1 else ""

        # Skip empty lines or pure layout notes
        if not col1 and not col2 and not col3 and not bldg:
            continue
        if col1.lower() in ('void', 'vacant', 'return', '(return)', '(return.)', '}') and not col2 and not col3:
            continue

        surname = ""
        forename = ""
        trade = ""

        # Smart Alignment Logic for 1895:
        # Case A: Title in col1 and Surname in col2 (e.g. 'Mrs.' \t 'Miller' \t 'Harriet' or 'Miss' \t 'Davies' \t 'Minnie')
        if col1.lower().rstrip('.') in COMMON_TITLES and col2 and not is_forename_token(col2):
            surname = col2
            if col3:
                forename = f"{col1} {col3}".strip()
                trade = ""
            else:
                forename = col1

        # Case B: Title in col2 (e.g. 'Kenny' \t 'Mrs' \t 'Sarah')
        elif col2.lower().rstrip('.') in COMMON_TITLES:
            surname = col1
            if col3:
                forename = f"{col2} {col3}".strip()
                trade = ""
            else:
                forename = col2

        # Case C: Title + Initial in col1 (e.g. 'Mrs. H.' \t 'Jones' \t 'Royal Albert')
        elif col1.lower().startswith(('mrs', 'miss', 'rev', 'dr', 'capt', 'col', 'hon', 'mr')) and col2:
            surname = col2
            forename = col1
            trade = col3

        # Case D: Inverted columns (Forename in col1, Surname in col2, e.g. 'Wm.' \t 'Henker' \t 'butcher')
        elif is_forename_token(col1) and not is_forename_token(col2):
            forename = col1
            surname = col2
            trade = col3

        # Case E: Standard columns (Surname in col1, Forename in col2, e.g. 'Barker' \t 'Wm.' \t 'tinplate w\'k\'r')
        elif not is_forename_token(col1) and is_forename_token(col2):
            surname = col1
            forename = col2
            trade = col3

        # Case F: Default fallback
        else:
            surname = col1
            forename = col2
            trade = col3

        # Clean middle initials dumped into trade (e.g. 'J. pilot' or 'R. clerk' or 'M. mason')
        if trade:
            m_lead = re.match(r'^([A-Za-z]\.)\s+(.*)$', trade)
            if m_lead and TRADE_REGEX_SPLIT.search(m_lead.group(2)):
                forename = f"{forename} {m_lead.group(1)}".strip()
                trade = m_lead.group(2).strip()

        # Clean trade prefix with comma (e.g. 'G., fish hawker')
        if trade and ',' in trade:
            p_init, p_tr = [x.strip() for x in trade.split(',', 1)]
            if is_forename_token(p_init):
                forename = f"{forename} {p_init}".strip()
                trade = p_tr

        # Clean embedded trade in forename (e.g. 'Mrs Elizabeth, grocer' or 'John, potter')
        if forename and ',' in forename:
            fo_p, tr_p = [x.strip() for x in forename.split(',', 1)]
            forename = fo_p
            if not trade:
                trade = tr_p
            else:
                trade = f"{tr_p}, {trade}".strip(' ,')
        elif forename:
            m_tr = TRADE_REGEX_SPLIT.search(forename)
            if m_tr and forename.lower().strip('. ') not in NAME_TOKENS:
                tr_found = m_tr.group(0)
                forename = forename[:m_tr.start()].strip(' ,.-')
                if not trade:
                    trade = tr_found
                else:
                    trade = f"{tr_found}, {trade}".strip(' ,')

        # Clean building names from trade
        bldg_keywords = {'house', 'villa', 'cottage', 'cot', 'hotel', 'chambers', 'hall', 'buildings', 'school', 'church', 'chapel', 'arms', 'inn'}
        if trade:
            tr_low = trade.lower()
            if (any(kw in tr_low for kw in bldg_keywords) or tr_low.endswith((' ho', ' cot', ' villa', ' lodge'))) and not TRADE_REGEX_SPLIT.search(trade):
                if not bldg:
                    bldg = trade
                trade = ""

        # Standardize trade & names
        trade = clean_trade(trade)
        forename = clean_name_abbr(forename)
        surname = surname.strip(' ,"-~.')
        bldg = bldg.strip(' ,"-~.')

        if forename or surname or trade or bldg:
            records.append({
                'year': '1895',
                'street': current_street,
                'house_number': h_num,
                'building_name': bldg,
                'surname': surname,
                'forename': forename,
                'trade': trade
            })

    print(f"Total parsed records: {len(records)}")
    print(f"Total distinct streets: {len(streets_found)}")

    with open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=['year', 'street', 'house_number', 'building_name', 'surname', 'forename', 'trade'])
        writer.writeheader()
        writer.writerows(records)

if __name__ == "__main__":
    parse_tsv("/Users/robgale/Documents/Newport Street Directory Project/raw_tsvs/1895.tsv",
              "/Users/robgale/Documents/Newport Street Directory Project/volume_csvs/1895_cleaned.csv")
