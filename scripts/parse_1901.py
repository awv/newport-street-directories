import csv
import re
import os
import sys

# Add scripts directory to path for imports
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'scripts'))

try:
    from clean_csv import clean_street_name, TRADE_TYPO_MAP, TRADE_EXACT_MAP, TRADE_ABBREV_MAP
except ImportError:
    clean_street_name = lambda x: x.strip()
    TRADE_TYPO_MAP = {}
    TRADE_EXACT_MAP = {}
    TRADE_ABBREV_MAP = {}

# Custom helper to standardize trade casing and mappings
def clean_trade(trade):
    if not trade:
        return ""
    t_clean = trade.strip(' ,"-~.')
    t_low = t_clean.lower()

    trade_abbrev_local = {
        'coachmn': 'coachman',
        'weighmn': 'weighman',
        'watchmn': 'watchman',
        'eng. driver': 'engine driver',
        'eng, driver': 'engine driver',
        'eng. drvr.': 'engine driver',
        'eng. drvr': 'engine driver',
        'eng.drvrr.': 'engine driver',
        'crane drvr': 'crane driver',
        'goodszuard': 'goods guard',
        'mas. mariner': 'master mariner',
        'mas. mai.': 'master mariner',
        'mas. mar.': 'master mariner',
        'master mar': 'master mariner',
        'music t\'ch\'r': 'music teacher',
        'music teachr': 'music teacher',
        'dk. police': 'dock police',
        'dock police': 'dock police',
        'carptr. &c.': 'carpenter',
        'carptr': 'carpenter',
        'carpntr': 'carpenter',
        'hairdrsr': 'hairdresser',
        'hairdr\'ser': 'hairdresser',
        'shipcarptr': 'shipwright',
        'shipcarpr': 'shipwright',
        'ship\'s pntr': "ship's painter",
        'greengr\'r': 'greengrocer',
        'greeng\'rs': 'greengrocer',
        'greengroer': 'greengrocer',
        'general dlr.': 'general dealer',
        'railway insp': 'railway inspector',
        'boots\'lr': 'boot seller',
        'bootsellr': 'boot seller',
        'boot dlrs': 'boot dealers',
        'potato merc.': 'potato merchant',
        'potato merch': 'potato merchant',
        'boarding ho.': 'boarding house',
        'boarding ho': 'boarding house',
        'p.c.': 'P.C.',
        'p.o. clerk': 'P.O. Clerk',
        'h.m.c': 'H.M.C.',
        'glass wks': 'glass works',
        'glass wrks': 'glass works',
        'glassblwr': 'glass blower',
        'stonecut\'r': 'stonecutter',
        'ironf\'d\'r': 'ironfounder',
        'boilermkr': 'boilermaker',
        'wagon repairr': 'wagon repairer',
        'bottlemkr': 'bottlemaker',
        'laundrs': 'launderers',
        'dressnkr': 'dressmaker',
        'slate workr': 'slate worker',
        'lathrendr': 'lathrender',
        'rly. foreman': 'railway foreman',
        'brassfitr': 'brass fitter',
        'dockman': 'dockman',
        'ast. d\'km\'str': 'assistant dockmaster',
        'dock-master': 'dockmaster',
        'coal trimr': 'coal trimmer',
        'shippr': 'shipper',
        'shipchand\'er': 'ship chandler',
        'shipcarpt': 'shipwright',
        'cab propr\'tor': 'cab proprietor'
    }
    if t_low in trade_abbrev_local:
        return trade_abbrev_local[t_low]

    acronym_map = {
        'p.c.': 'P.C.',
        'p.o. clerk': 'P.O. Clerk',
        'h.m.c': 'H.M.C.',
    }
    if t_low in acronym_map:
        return acronym_map[t_low]

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
        'window cleaner', 'goods guard', 'master mariner', 'greengrocer',
        'bottlemaker', 'launderers', 'dock police', 'dock pilot'
    }
    if val in case_insensitive_standards:
        return val

    if not changed_words and val == t_clean.lower():
        return t_clean
    return val

# Common acronyms/abbreviations for names
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
    name = re.sub(r'\bEdw?\.?\b', 'Edward', name)
    name = re.sub(r'\bEd\.?\b', 'Edward', name)
    name = re.sub(r'\bJno\.?\b', 'John', name)
    name = re.sub(r'\bAlfd?\.?\b', 'Alfred', name)
    name = re.sub(r'\bAlbt\.?\b', 'Albert', name)
    name = re.sub(r'\bRichd?\.?\b', 'Richard', name)
    name = re.sub(r'\bRich\.?\b', 'Richard', name)
    name = re.sub(r'\bDanl?\.?\b', 'Daniel', name)
    name = re.sub(r'\bSaml?\.?\b', 'Samuel', name)
    name = re.sub(r'\bJas\.?\b', 'James', name)
    name = re.sub(r'\bAb\.?\b', 'Abraham', name)
    name = re.sub(r'\bAbram\b', 'Abraham', name)
    name = re.sub(r'\bDd\.?\b', 'David', name)
    name = re.sub(r'\bOct\.?\b', 'Octavius', name)
    name = re.sub(r'\bFdk\.?\b', 'Frederick', name)
    name = re.sub(r'\bNath\.?\b', 'Nathaniel', name)
    name = re.sub(r'\bCor\b', 'Cornelius', name)
    name = re.sub(r'\bSl\.?\b', 'Samuel', name)
    return name.strip(' ,"-~.')

CROSS_STREET_PAT = re.compile(
    r'\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.)\b.*?\bto\b.*?\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.|square)\b'
    r'|^\s*\[?(?:here\s+are|here\s+is|here\s+cross|\[?return\]?|\(return\.?\)|return\.?)\]?\b'
    r'|^\s*[\(\[]?\s*return\.?\s*[\)\]]?\s*$'
    r'|\bsee\b'
    r'|\bsee\s+also\b'
    r'|^\s*now\s+[a-z0-9\s\.\-|\(\)]+'
    r'|^\s*(?:maindee|newport|pill)from\b'
    r'|^\s*from\s+[A-Za-z0-9\s]+'
    r'|^\s*[A-Za-z0-9\s]+street\s+from\b'
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
    'barnard town', 'town hall', 'union', 'westgate', 'cambria', 'melbourne',
    'ringland', 'cross-street', 'cross street', 'cross lane', 'maindee',
    'the marshes', 'marshes', 'belle vue', 'gold tops', 'pentonville'
}

IGNORED_HEADER_REGEX = re.compile(
    r'\b(?:newport\s+street\s+list|newport\s+street\s+directory|newport\s+directory|street\s+directory)\b'
    r'|^\s*newport\s*[\.\-—]*$'
    r'|^\s*directory\s*[\.\-—]*$'
    r'|\b(?:p\.\s*e\.\s*gane|trapnell\s+&\s+gane|house\s+furnisher)\b',
    re.I
)

NAME_ABBR_PAT = re.compile(
    r'\b(?:mr|mrs|miss|rev|dr|capt|col|hon|snr|jun|esq|wm|thos|geo|chas|edwd|robt|hy|jas|jno|danl|alfd|fredk)\b',
    re.I
)

VALID_WARD_AFTER_COMMA = re.compile(
    r'^\s*(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|P|M|C|T|B|L|D|E|Pill|Maindee|Crindau|Marshes|Liswerry|Borough|Town|Tunnel|continued|contd|cont|cont[\'’]d|contind|Ch)\.?\s*$',
    re.I
)

COMMON_TITLES = {'mrs', 'mrs.', 'miss', 'miss.', 'rev', 'rev.', 'dr', 'dr.', 'capt', 'col', 'hon', 'esq', 'mr', 'lord', 'sir'}

KNOWN_TRADE_KEYWORDS = [
    'grocer', 'labourer', 'ironworker', 'ironwrkr', 'ironwkr', 'carpenter', 'mason', 'fitter', 'haulier', 
    'clerk', 'painter', 'seaman', 'smith', 'tailor', 'tailoress', 'butcher', 'pork butcher', 'trimmer', 'baker', 
    'engineer', 'plasterer', 'guard', 'goods guard', 'moulder', 'gardener', 'gard\'nr', 'foreman', 'boilermaker', 
    'boilermakr', 'fireman', 'builder', 'traveller', 'manager', 'hairdresser', 'hairdrsr', 'agent', 'blacksmith', 
    'blksmith', 'greengrocer', 'greengroer', 'bootmaker', 'bootmkr', 'bootseller', 'bootsellr', 'signalman', 'shipwright', 'plumber', 'hobbler', 
    'platelayer', 'porter', 'bricklayer', 'rigger', 'shopkeeper', 'shopk\'p\'r', 'mariner', 'shoemaker', 
    'draper', 'steelworker', 'pilot', 'dock pilot', 'confectioner', 'postman', 'driver', 'sawyer', 
    'policeman', 'printer', 'sailor', 'solicitor', 'mechanic', 'machinist', 'steward', 
    'joiner', 'striker', 'miller', 'tobacconist', 'dealer', 'general dealer', 'fruiterer', 'caretaker', 
    'inspector', 'decorator', 'warehouseman', 'saddler', 'shunter', 'boatman', 'waterman',
    'hoistman', 'milkman', 'cooper', 'dairyman', 'watchmaker', 'electrician', 'accountant', 
    'hawker', 'fish hawker', 'dressmaker', 'dressnkr', 'cabinetmaker', 'cabinetmkr', 'wheelwright', 'docker', 'roller', 
    'furnaceman', 'chemist', 'motor driver', 'motorman', 'weighman', 'weighmn', 'gasfitter', 'gas fitter', 'puddler', 
    'timekeeper', 'newsagent', 'checker', 'sailmaker', 'coachman', 'coachmn', 'stevedore', 
    'storekeeper', 'storeman', 'packer', 'outfitter', 'pawnbroker', 'tinsmith', 'carman', 'cabman', 'cab propr\'tor', 'surgeon', 'ostler', 
    'watchman', 'watchmn', 'shearer', 'patternmaker', 'patternmakr', 'architect', 'surveyor', 'dentist', 'shipper', 
    'weigher', 'sheet wghr', 'groundsman', 'mason\'s labr', 'glass worker', 'glass blowr', 
    'glass blower', 'glass wkr', 'glass works', 'glass sorter', 'glassblower', 'brick bnr', 'brick burner', 'brickburner',
    'brick works', 'brickmkr', 'gas worker', 'gas stoker', 'bottle blowr', 'bottle works', 'bottle hand', 'bottle sorter',
    'bottle maker', 'bottlemkr', 'tinplate worker', 'ironfounder', 'sculptor', 'hoopmaker',
    'telegraph linesman', 'tel. linesman', 'lamplighter', 'coach builder', 'cr.driver', 'crane driver', 
    'dock police', 'dockpolice', 'dockman', 'assistant dockmaster', 'dockmaster', 'ship chandler',
    'brass finisher', 'brass fitter', 'rivetter', 'riveter', 'horseshoer', 'wood turner', 'optician',
    'fishmonger', 'beer retailer', 'publican', 'innkeeper', 'waiter', 'sugar boiler',
    'telegraphist', 'typewriter', 'nurse', 'midwife', 'cinematograph operator',
    'taxi drivr', 'brewery hd', 'fish bar', 'marine stores',
    'brklayer', 'laundress', 'launderers', 'laundrs', 'bookkeeper', 'driller', 'brushmaker', 'quarryman', 'potter', 'stoker',
    'maltster', 'hammerman', 'tile layer', 'potato merchant'
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
    'humphrey', 'octavius', 'cornelius', 'dan', 'fred', 'tom', 'rob', 'archi', 'catherine', 'nichol', 'jesse',
    'stephen', 'nugent', 'clara', 'helen', 'nathaniel', 'abram', 'abraham', 'augustus', 'leonard'
}

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
    known_fn_abbrs = {'wm', 'geo', 'thos', 'chas', 'hy', 'edwd', 'rd', 'walt', 'jos', 'albt', 'alfd', 'jas', 'benj', 'fredk', 'sl', 'danl', 'hbt', 'rbt', 'saml', 'fdk', 'nath', 'edw', 'hum', 'oct', 'cor', 'archi', 'fred', 'dan', 'margt', 'ab'}
    if t_clean in known_fn_abbrs or t_clean.rstrip('.') in known_fn_abbrs:
        return True
    return False

def parse_person_text(text):
    """
    Parses a combined person string like 'Jones William, mason' or 'Hughes R. O., outfitter' or 'Wilmott J. labourer'.
    Returns (surname, forename, trade, bldg)
    """
    text = text.strip()
    if not text:
        return "", "", "", ""
        
    surname = ""
    forename = ""
    trade = ""
    bldg = ""

    if ',' in text:
        parts = text.split(',', 1)
        name_part = parts[0].strip()
        tr_part = parts[1].strip()
        trade = tr_part
        tokens = name_part.split()
        if len(tokens) >= 2 and tokens[1].lower().rstrip('.') in COMMON_TITLES and len(tokens) >= 3:
            surname = tokens[0]
            forename = " ".join(tokens[1:])
        elif len(tokens) >= 2 and tokens[0].lower().rstrip('.') in COMMON_TITLES:
            forename = tokens[0]
            surname = " ".join(tokens[1:])
        elif len(tokens) >= 2:
            surname = tokens[0]
            forename = " ".join(tokens[1:])
        else:
            surname = name_part
    else:
        # Check if trade word is at the end of the text
        m_tr = TRADE_REGEX_SPLIT.search(text)
        if m_tr and not any(text.lower().strip().endswith(w) for w in ('street', 'road', 'place', 'house')):
            tr_found = m_tr.group(0)
            trade = text[m_tr.start():].strip(' ,.-')
            name_part = text[:m_tr.start()].strip(' ,.-')
            tokens = name_part.split()
            if len(tokens) >= 2 and tokens[1].lower().rstrip('.') in COMMON_TITLES and len(tokens) >= 3:
                surname = tokens[0]
                forename = " ".join(tokens[1:])
            elif len(tokens) >= 2:
                surname = tokens[0]
                forename = " ".join(tokens[1:])
            else:
                surname = name_part
        else:
            tokens = text.split()
            if len(tokens) >= 2 and tokens[1].lower().rstrip('.') in COMMON_TITLES and len(tokens) >= 3:
                surname = tokens[0]
                forename = " ".join(tokens[1:])
            elif len(tokens) >= 2 and tokens[0].lower().rstrip('.') in COMMON_TITLES:
                forename = tokens[0]
                surname = " ".join(tokens[1:])
            elif len(tokens) >= 2:
                surname = tokens[0]
                forename = " ".join(tokens[1:])
            else:
                surname = text

    # Building check
    bldg_keywords = {'house', 'villa', 'cottage', 'cot', 'hotel', 'chambers', 'hall', 'buildings', 'school', 'church', 'chapel', 'inn', 'arms'}
    if trade and any(kw in trade.lower() for kw in bldg_keywords) and not TRADE_REGEX_SPLIT.search(trade):
        bldg = trade
        trade = ""

    return surname.strip(' ,"-~.'), clean_name_abbr(forename), clean_trade(trade), bldg.strip(' ,"-~.')

def is_valid_street_name(s):
    if not s:
        return False
    s = s.strip()
    s = re.sub(r'^[\(\[]?\s*return[\.\)]*\s*', '', s, flags=re.I).strip('. -—')
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
        s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|Ch|[PMCTBLDE])\s*$', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,–_')
    
    if NAME_ABBR_PAT.search(s_clean):
        return False
        
    words = [w.strip('.,()-"\'–_') for w in s_clean.lower().split() if w.strip('.,()-"\'–_')]
    if not words:
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
    prev_surname = ""
    prev_trade = ""

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            raw_line = line.rstrip('\r\n')
            if not raw_line or not raw_line.strip():
                continue
                
            line_str = raw_line.strip()
            
            # Skip page headers
            if any(IGNORED_HEADER_REGEX.search(p) for p in [line_str]):
                continue

            # Check if this line is a street header
            first_candidate = line_str.split('\t')[0].strip()
            matched_street = ""
            if first_candidate and is_valid_street_name(first_candidate):
                if first_candidate.strip().upper() == "HIGH STREET" and line_num < 5000:
                    matched_street = ""
                else:
                    matched_street = first_candidate
            else:
                parts_cand = [p.strip() for p in line_str.split('\t')]
                if len(parts_cand) >= 2 and parts_cand[0] and parts_cand[1].strip('., -—').lower() in STREET_SUFFIXES:
                    cand = parts_cand[0] + " " + parts_cand[1]
                    if len(parts_cand) >= 3 and VALID_WARD_AFTER_COMMA.match(parts_cand[2]):
                        cand += ", " + parts_cand[2]
                    if is_valid_street_name(cand):
                        matched_street = cand

            if matched_street:
                s_clean = re.sub(r'^[\(\[]?\s*return[\.\)]*\s*', '', matched_street, flags=re.I).strip('. -—')
                s_clean = re.sub(r'[\s\-—–_]+(?:continued|contd|cont|cont\.|cont[\'’]d|contind)\b', '', s_clean, flags=re.I).strip()
                s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
                s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
                if not re.search(r'\bHigh\s+Street\b', s_clean, re.I):
                    s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|Ch|[PMCTBLDE])\s*$', '', s_clean, flags=re.I).strip()
                current_street = clean_street_name(s_clean)
                parts_check = [p.strip() for p in line_str.split('\t')]
                if not any(parts_check[1:]) or (len(parts_check) >= 2 and parts_check[1].strip('., -—').lower() in STREET_SUFFIXES):
                    continue

            # Skip cross streets & layouts
            if CROSS_STREET_PAT.search(line_str) or re.match(r'^[\s\*\-\_\=\#\+]+$', line_str):
                continue
            if line_str.lower() in ('(return.)', '(return)', 'return'):
                continue
            if not current_street:
                continue
            if line_str.startswith("Number\t") or line_str.startswith("Number "):
                continue

            raw_parts = [p.replace('\\t', '').replace('\\n', '').strip() for p in raw_line.split('\t')]
            
            # Check for two-column rows (e.g. lines 435-490)
            # Pattern 1: Two house numbers present, e.g. ['', '11', 'Quinn Samuel, dockman', '17', 'Doun Thomas']
            # Pattern 2: Side-by-side separated by empty tab or mid-line house number
            col_entries = []
            
            # Strip leading empty tab if line started with \t
            cleaned_tokens = [p for p in raw_parts if p]
            if not cleaned_tokens:
                continue

            # Check if this row represents multiple entries (e.g. Col 1 and Col 2 side-by-side)
            # Find indices of house numbers or street markers
            split_indices = []
            for idx, tok in enumerate(cleaned_tokens):
                if idx > 0 and re.match(r'^\d+[a-zA-Z]?$', tok):
                    split_indices.append(idx)
            
            if split_indices:
                last_idx = 0
                for s_idx in split_indices:
                    col_entries.append(cleaned_tokens[last_idx:s_idx])
                    last_idx = s_idx
                col_entries.append(cleaned_tokens[last_idx:])
            else:
                col_entries.append(cleaned_tokens)

            for entry in col_entries:
                if not entry:
                    continue
                entry_str = " ".join(entry).strip()
                if is_valid_street_name(entry_str):
                    current_street = clean_street_name(entry_str)
                    continue
                if CROSS_STREET_PAT.search(entry_str) or entry_str.lower() in ('(return.)', '(return)', 'return', 'vacant sites', 'void'):
                    continue

                h_num = ""
                bldg = ""
                surname = ""
                forename = ""
                trade = ""

                # Format 1: First token is house number, second token is combined person string
                # e.g. ['1', 'Jones William, mason'] or ['3', 'Hughes R. O., outfitter']
                if re.match(r'^\d+[-—\d\/]*[a-zA-Z]?$', entry[0]):
                    h_num = entry[0]
                    rem = entry[1:]
                    if len(rem) == 1:
                        surname, forename, trade, bldg = parse_person_text(rem[0])
                    elif len(rem) >= 2:
                        # Check if rem follows ['Surname', 'Forename', 'Trade', ...]
                        c1 = rem[0]
                        c2 = rem[1]
                        c3 = rem[2] if len(rem) > 2 else ""
                        c4 = rem[3] if len(rem) > 3 else ""

                        # Case A: Title in c2 (e.g. 'Lewis' \t 'Mrs' \t 'Mary Ann')
                        if c2.lower().rstrip('.') in COMMON_TITLES:
                            surname = c1
                            if c3:
                                if TRADE_REGEX_SPLIT.search(c3) and not any(w in c3.lower() for w in NAME_TOKENS):
                                    forename = c2
                                    trade = c3
                                else:
                                    forename = f"{c2} {c3}".strip()
                                    trade = c4
                            else:
                                forename = c2
                        # Case B: Title in c1 (e.g. 'Mrs.' \t 'Miller' \t 'Harriet')
                        elif c1.lower().rstrip('.') in COMMON_TITLES and not is_forename_token(c2):
                            surname = c2
                            forename = f"{c1} {c3}".strip() if c3 else c1
                            trade = c4
                        # Case C: Middle initial in c3 (e.g. 'Rees' \t 'William' \t 'J. mason' or 'Evans' \t 'William' \t 'J. pilot')
                        elif c3 and re.match(r'^[A-Za-z]\.\s+.*$', c3):
                            surname = c1
                            m_lead = re.match(r'^([A-Za-z]\.)\s+(.*)$', c3)
                            forename = f"{c2} {m_lead.group(1)}".strip()
                            trade = m_lead.group(2).strip()
                        # Case D: Inverted forename in c1, surname in c2 (e.g. 'Wm.' \t 'Henker' \t 'butcher')
                        elif is_forename_token(c1) and not is_forename_token(c2):
                            forename = c1
                            surname = c2
                            trade = c3
                        # Case E: Middle initial as its own column (e.g. 'Gray' \t 'Jas.' \t 'Wm.' \t 'tinsmith')
                        elif c3 and is_forename_token(c3) and c4:
                            surname = c1
                            forename = f"{c2} {c3}".strip()
                            trade = c4
                        # Case F: Standard
                        else:
                            surname = c1
                            forename = c2
                            trade = c3
                            if c4 and not bldg:
                                bldg = c4
                else:
                    # Non-numeric first token, e.g. ['Customs', 'Watchhouse'] or ['Charles', 'John,', "builders'", 'yard']
                    entry_text = " ".join(entry).strip()
                    surname, forename, trade, bldg = parse_person_text(entry_text)

                # Clean middle initial from trade
                if trade:
                    m_lead = re.match(r'^([A-Za-z]\.)\s+(.*)$', trade)
                    if m_lead and TRADE_REGEX_SPLIT.search(m_lead.group(2)):
                        forename = f"{forename} {m_lead.group(1)}".strip()
                        trade = m_lead.group(2).strip()

                # Clean embedded trade in forename
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

                # Building keywords in trade
                bldg_keywords = {'house', 'villa', 'cottage', 'cot', 'hotel', 'chambers', 'hall', 'buildings', 'school', 'church', 'chapel', 'inn', 'arms'}
                if trade:
                    tr_low = trade.lower()
                    if (any(kw in tr_low for kw in bldg_keywords) or tr_low.endswith((' ho', ' cot', ' villa', ' lodge', ' ct', ' h'))) and not TRADE_REGEX_SPLIT.search(trade):
                        if not bldg:
                            bldg = trade
                        trade = ""

                # Ditto resolution
                if (surname == '"' or surname.lower() in ('do', 'ditto')) and prev_surname:
                    surname = prev_surname
                if (trade == '"' or trade.lower() in ('do', 'ditto')) and prev_trade:
                    trade = prev_trade

                surname = surname.strip(' ,"-~.')
                forename = clean_name_abbr(forename)
                trade = clean_trade(trade)
                bldg = bldg.strip(' ,"-~.')

                if surname or forename or trade or bldg or h_num:
                    records.append({
                        "year": "1901",
                        "street": current_street,
                        "house_number": h_num,
                        "building_name": bldg,
                        "surname": surname,
                        "forename": forename,
                        "trade": trade
                    })
                    if surname:
                        prev_surname = surname
                    if trade:
                        prev_trade = trade

    # Write output
    with open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["year", "street", "house_number", "building_name", "surname", "forename", "trade"])
        writer.writeheader()
        writer.writerows(records)
        
    print(f"Parsed {len(records)} records from {input_path} into {output_path}.")

if __name__ == "__main__":
    parse_tsv("raw_tsvs/1901.tsv", "volume_csvs/1901_cleaned.csv")
