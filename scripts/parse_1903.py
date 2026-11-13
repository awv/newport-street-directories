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

    # Known abbreviations in 1903
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
        'master mar': 'master mariner',
        'mas. mar.': 'master mariner',
        'mas. mar': 'master mariner',
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
        'grers.': 'grocer',
        'grers': 'grocer',
        'general dlr.': 'general dealer',
        'railway insp': 'railway inspector',
        'boots\'lr': 'boot seller',
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
        'stonecut\'r': 'stonecutter',
        'ironf\'d\'r': 'ironfounder',
        'boilermkr': 'boilermaker',
        'wagon repairr': 'wagon repairer',
        'bottlemkr': 'bottlemaker',
        'laundrs': 'launderers',
        'ringger': 'rigger',
        'malster': 'maltster',
        'berth\'g mas': 'berthing master',
        'berth\'g': 'berthing master',
        'enginr': 'engineer',
        'chronom mkr': 'chronometer maker'
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
        'bottlemaker', 'launderers', 'dock police', 'dock pilot', 'berthing master',
        'music teacher'
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
    name = re.sub(r'\bDanl?\.?\b', 'Daniel', name)
    name = re.sub(r'\bSaml?\.?\b', 'Samuel', name)
    name = re.sub(r'\bJas\.?\b', 'James', name)
    name = re.sub(r'\bAb\.?\b', 'Abraham', name)
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
    'STREET', 'ROAD', 'AVENUE', 'PLACE', 'TERRACE', 'LANE', 'CRESCENT', 
    'PARADE', 'HILL', 'WALK', 'COURT', 'ROW', 'WHARF', 'DOCKS', 'DOCK', 
    'VILLAS', 'GARDENS', 'DRIVE', 'GROVE', 'SQUARE', 'PASSAGE', 'WAY', 
    'CIRCUS', 'PARK', 'VIEW', 'PATH', 'CLOSE', 'RISE', 'ST', 'RD', 'PL', 
    'TER', 'CRES', 'PDE', 'SQ', 'AV', 'CHAMBERS', 'BUILDINGS', 'COTTAGES'
}

COMMON_SURNAMES_NOT_STREETS = {
    'HILL', 'GREEN', 'LANE', 'PARK', 'WOOD', 'CROSS', 'STREET', 'HALL', 'DOCK', 'GARDENS', 'GROVE', 'ROAD'
}

IGNORED_DIRECTORY_HEADERS = {
    'NEWPORT STREET DIRECTORY.', 'NEWPORT STREET DIRECTORY', 'NEWPORT DIRECTORY.', 'NEWPORT DIRECTORY',
    'STREET DIRECTORY.', 'STREET DIRECTORY', 'NEWPORT STREET LIST.', 'NEWPORT STREET LIST',
    'ALBANY STREET', 'COMMERCIAL STREET', 'HIGH STREET', 'CHEPSTOW ROAD'
}

NAME_ABBREVIATIONS = {
    'WM', 'GEO', 'THOS', 'CHAS', 'ROBT', 'HY', 'EDWD', 'EDW', 'ED', 'JNO', 
    'ALFD', 'ALBT', 'RICHD', 'DANL', 'SAML', 'JAS', 'AB', 'DD', 'OCT', 
    'FDK', 'NATH', 'COR', 'SL', 'MRS', 'MISS', 'MR', 'REV', 'DR', 'CAPT', 'COL'
}

COMMON_TITLES = {'mrs', 'mrs.', 'miss', 'miss.', 'rev', 'rev.', 'dr', 'dr.', 'capt', 'col', 'hon', 'esq', 'mr', 'lord', 'sir'}

KNOWN_TRADE_KEYWORDS = [
    'grocer', 'labourer', 'ironworker', 'ironwrkr', 'ironwkr', 'carpenter', 'mason', 'fitter', 'haulier', 
    'clerk', 'painter', 'seaman', 'smith', 'tailor', 'tailoress', 'butcher', 'pork butcher', 'trimmer', 'baker', 
    'engineer', 'plasterer', 'guard', 'goods guard', 'moulder', 'gardener', 'gard\'nr', 'foreman', 'boilermaker', 
    'boilermakr', 'fireman', 'builder', 'traveller', 'manager', 'hairdresser', 'hairdrsr', 'agent', 'blacksmith', 
    'blksmith', 'greengrocer', 'greengroer', 'bootmaker', 'bootmkr', 'bootseller', 'bootsellr', 'signalman', 'shipwright', 'plumber', 'hobbler', 
    'platelayer', 'porter', 'bricklayer', 'rigger', 'ringger', 'shopkeeper', 'shopk\'p\'r', 'mariner', 'shoemaker', 
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
    'maltster', 'malster', 'hammerman', 'tile layer', 'potato merchant', 'berthing master', 'music teacher', 'chronometer maker'
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
    'stephen', 'nugent', 'clara', 'helen', 'nathaniel', 'abram', 'abraham', 'augustus', 'leonard', 'morgan', 'elijah',
    'isabella', 'gustave', 'amos', 'bernard'
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

def is_valid_street_header(s):
    if not s:
        return None
    s_clean = s.strip()
    s_clean = re.sub(r'[\(\[]\s*return\s*[\)\]]', '', s_clean, flags=re.I).strip('., -—()[]')
    s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|Ch|[PMCTBLDE])\s*$', '', s_clean, flags=re.I).strip()
    
    if not s_clean or len(s_clean) <= 3:
        return None

    if s_clean.lower() in {'road', 'street', 'lane', 'avenue', 'place', 'terrace', 'hill', 'drive', 'crescent', 'parade', 'square', 'walk', 'gardens'}:
        return None

    s_low = s_clean.lower()
    if s_low.startswith(('here is', 'here are', 'from ', 'to ', 'opposite ', 'see ', 'now ')):
        return None

    if any(sym in s_clean for sym in ['&', 'ltd', 'limited', 'livery', 'brewery', 'foundry', 'inn', 'hotel', 'arms', 'tavern', 'stores', 'works', 'merchants', 'dealers', 'builders', 'manufacturers', 'agents', 'solicitors', 'bros']):
        return None

    s_upper = s_clean.upper()
    if s_upper in IGNORED_DIRECTORY_HEADERS:
        return None
    if any(h in s_upper for h in [
        'SEE ALSO', 'RETURN', 'LEFT HAND SIDE', 'RIGHT HAND SIDE', 
        'EAST SIDE', 'WEST SIDE', 'IS A DISTRICT', 'INCLUDING NORTH-STREET', 
        'FOR RESIDENT', 'SEE 21, COMMERCIAL-STREET', "DOCK MASTER'S OFFICE", 
        "CUSTOMS' WATCHHOUSE", 'ENGINE HOUSE', 'COUNTY COURT OFFICES',
        'OFFICE', 'TELEPHONE', 'SUPER TUNE', 'ST. WOOLOS SCHOOLS', 'ASSEMBLY ROOMS',
        'BEAUFORT CHAMBERS', "QUEEN'S CHAMBERS", 'CARLTON CHAMBERS',
        'ARCADE CHAMBERS', 'THE NEWPORT ARCADE', 'NEWPORT ARCADE'
    ]):
        return None
    if re.match(r'^[A-Z]\s*\d+$', s_upper) or re.match(r'^\d+', s_upper):
        return None

    words = s_upper.split()
    if not words:
        return None

    if all(len(w.strip('.,')) <= 1 for w in words):
        return None

    first_w = words[0].strip('.,()-"')
    if first_w in NAME_ABBREVIATIONS or re.match(r'^[A-Za-z]+\d+$', first_w) or ',' in words[0]:
        return None

    if len(words) == 1 and words[0] in COMMON_SURNAMES_NOT_STREETS:
        return None

    last_word = words[-1].strip('.,()-"')
    if last_word in STREET_SUFFIXES:
        if last_word in {'HILL', 'COTTAGES', 'VILLAS', 'BUILDINGS', 'CHAMBERS'} and len(words) == 1:
            return None
        if last_word in {'RD', 'RD.'} and len(words) == 2 and words[0] in {'POPHAM', 'RIDGE', 'BUSH', 'JONES', 'EVANS', 'THOMAS', 'DAVIES'}:
            return None
        if s_clean.upper().startswith("COMMERCIAL BUILDINGS"):
            return "Commercial Street"
        if s_clean.upper().startswith("DOCK ROAD CHAMBERS"):
            return "Dock Street"
        return clean_street_name(s_clean)

    return None

def is_duplicate_chunk(c1, c2):
    if c1 == c2:
        return True
    if len(c1) > 1 and c1[1:] == c2:
        return True
    return False

def split_1903_line(parts):
    while parts and not parts[-1]:
        parts.pop()
    if not parts:
        return []

    while parts and not parts[0]:
        parts.pop(0)
    if not parts:
        return []

    chunks = []
    current_chunk = []
    
    for i, p in enumerate(parts):
        if not p or p == '-':
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
            continue
        
        if current_chunk:
            p_first = p.split()[0].strip('.,()')
            if p_first.isdigit() and len(p_first) <= 3:
                chunks.append(current_chunk)
                current_chunk = [p]
                continue
            if is_valid_street_header(p):
                chunks.append(current_chunk)
                current_chunk = [p]
                continue
        
        current_chunk.append(p)
    
    if current_chunk:
        chunks.append(current_chunk)

    if len(chunks) > 1:
        deduped = [chunks[0]]
        for ch in chunks[1:]:
            if not is_duplicate_chunk(chunks[0], ch):
                deduped.append(ch)
        chunks = deduped

    return chunks

def parse_record_chunk(tokens, street):
    tokens = [t.strip() for t in tokens if t.strip() and t.strip() != '-']
    if not tokens:
        return None
        
    comb = " ".join(tokens)
    comb_low = comb.lower()
    if CROSS_STREET_PAT.search(comb):
        return None
    if any(pat in comb_low for pat in ['(return', '[return', 'entrance', 'roadway', 'hand side', 'right-hand', 'left-hand', 'reynolds & co', 'complete house', 'furnishers', 'hall stands', 'blankets, flannels', 'umbrellas from']):
        return None
    if comb.startswith(('[', '(')):
        return None
        
    h_num = ""
    surname = ""
    forename = ""
    trade = ""
    bldg = ""

    # Check if tokens[0] is house number or starts with house number
    m_num_embedded = re.match(r'^(\d+[A-Za-z]?)\s+(.*)$', tokens[0])
    if re.match(r'^\d+[A-Za-z]?$', tokens[0]) or re.match(r'^\d+-\d+$', tokens[0]):
        h_num = tokens[0]
        rem = tokens[1:]
    elif m_num_embedded:
        h_num = m_num_embedded.group(1)
        rem = [m_num_embedded.group(2)] + tokens[1:]
    else:
        h_num = ""
        rem = tokens

    if not rem:
        return None

    # Detect building names
    bldg_keywords = {'house', 'villa', 'cottage', 'cot', 'cot.', 'hotel', 'inn', 'tavern', 'arms', 'chambers', 'lodge', 'hall'}
    clean_rem = []
    for token in rem:
        t_low = token.lower()
        if any(kw in t_low for kw in bldg_keywords) and len(token.split()) <= 4:
            if not bldg and not any(tk in t_low for tk in ['public house', 'beerhouse', 'coffee house', 'eating house']):
                bldg = token
                continue
        clean_rem.append(token)
    rem = clean_rem

    if not rem:
        if bldg:
            return {
                "year": "1903",
                "street": street,
                "house_number": h_num,
                "building_name": bldg,
                "surname": "",
                "forename": "",
                "trade": ""
            }
        return None

    if len(rem) == 1:
        text = rem[0]
        if ',' in text:
            np, tp = text.split(',', 1)
            trade = tp.strip()
            name_parts = np.strip().split()
            if len(name_parts) >= 2:
                surname = name_parts[0]
                forename = " ".join(name_parts[1:])
            else:
                surname = np.strip()
        else:
            m_tr = TRADE_REGEX_SPLIT.search(text)
            if m_tr:
                trade = text[m_tr.start():].strip(' ,.-')
                name_part = text[:m_tr.start()].strip(' ,.-')
                tokens_n = name_part.split()
                if len(tokens_n) >= 2:
                    surname = tokens_n[0]
                    forename = " ".join(tokens_n[1:])
                else:
                    surname = name_part
            else:
                parts = text.strip().split()
                if len(parts) >= 2:
                    surname = parts[0]
                    forename = " ".join(parts[1:])
                else:
                    surname = text.strip()
    elif len(rem) == 2:
        r0 = rem[0].strip(' ,')
        r1 = rem[1].strip(' ,')
        r0_parts = r0.split()
        if len(r0_parts) >= 2:
            surname = r0_parts[0]
            forename = " ".join(r0_parts[1:])
            trade = r1
        elif is_forename_token(r0) and not is_forename_token(r1):
            forename = r0
            surname = r1
        else:
            surname = r0
            if ',' in r1:
                fn, tr = r1.split(',', 1)
                forename = fn.strip()
                trade = tr.strip()
            elif TRADE_REGEX_SPLIT.search(r1):
                trade = r1
            else:
                forename = r1
    elif len(rem) >= 3:
        c1 = rem[0]
        c2 = rem[1]
        c3 = rem[2]
        c4 = rem[3] if len(rem) > 3 else ""

        # Case A: Title in c2 (e.g. 'Morgan' \t 'Mrs.' \t 'Isabella' or 'Lewis' \t 'Mrs.' \t 'Mary Ann')
        if c2.lower().rstrip('.') in COMMON_TITLES:
            surname = c1
            if c3:
                if TRADE_REGEX_SPLIT.search(c3) and not any(w in c3.lower() for w in NAME_TOKENS):
                    forename = c2
                    trade = " ".join(rem[2:])
                else:
                    fn_parts = [c2, c3]
                    idx = 3
                    while idx < len(rem) and is_forename_token(rem[idx]):
                        fn_parts.append(rem[idx])
                        idx += 1
                    forename = " ".join(fn_parts)
                    trade = " ".join(rem[idx:])
            else:
                forename = c2

        # Case B: Title in c1 (e.g. 'Mrs.' \t 'Miller' \t 'Harriet')
        elif c1.lower().rstrip('.') in COMMON_TITLES and not is_forename_token(c2):
            surname = c2
            forename = f"{c1} {c3}".strip() if c3 else c1
            trade = " ".join(rem[3:])

        # Case C: Middle initial / forename in c3 (e.g. 'Jones' \t 'William' \t 'Hy.' \t 'smith' or 'Gould' \t 'J.' \t 'G.' \t 'pilot')
        elif is_forename_token(c3) and c4:
            surname = c1
            forename = f"{c2} {c3}".strip()
            trade = " ".join(rem[3:]).strip()

        # Case D: Inverted forename in c1, surname in c2
        elif is_forename_token(c1) and not is_forename_token(c2):
            forename = c1
            surname = c2
            trade = " ".join(rem[2:]).strip()

        # Case E: Standard
        else:
            surname = c1
            forename = c2
            trade = " ".join(rem[2:]).strip()

    # Clean leading middle initial from trade (e.g. 'H. pilot' or 'G. pilot' or 'J. ironf\'d\'r' or 'Hy. smith')
    if trade:
        m_lead = re.match(r'^([A-Za-z]\.)\s+(.*)$', trade)
        if m_lead and TRADE_REGEX_SPLIT.search(m_lead.group(2)):
            forename = f"{forename} {m_lead.group(1)}".strip()
            trade = m_lead.group(2).strip()

    # Clean embedded trade in forename
    if forename:
        if ',' in forename:
            fn_p, tr_p = forename.split(',', 1)
            forename = fn_p.strip()
            if not trade:
                trade = tr_p.strip()
            else:
                trade = f"{tr_p.strip()}, {trade}".strip(' ,')
        else:
            m_tr = TRADE_REGEX_SPLIT.search(forename)
            if m_tr and forename.lower().strip('. ') not in NAME_TOKENS:
                tr_found = m_tr.group(0)
                forename = forename[:m_tr.start()].strip(' ,.-')
                if not trade:
                    trade = tr_found
                else:
                    trade = f"{tr_found}, {trade}".strip(' ,')

    if ',' in surname and not trade:
        sn, tr = surname.split(',', 1)
        surname = sn.strip()
        trade = tr.strip()

    trade = clean_trade(trade)
    forename = clean_name_abbr(forename)
    surname = surname.strip(' ,"-~.')
    forename = forename.strip(' ,"-~.')

    # Strict junk filtering
    sn_low = surname.lower().strip('()[].,-')
    fn_low = forename.lower().strip('()[].,-')
    full_name_low = f"{sn_low} {fn_low}".strip()

    if surname.upper() in IGNORED_DIRECTORY_HEADERS:
        return None
    if not h_num and not forename and not trade and len(surname) <= 4:
        return None
    if surname.upper() in {'ALE', 'ALI', 'ALT', 'ARC', 'BAN', 'ART', 'COM', 'CRI', 'BIS', 'FAI', 'HEN', 'HIG', 'ALB', 'AGI'}:
        return None
    if sn_low in {'return', 'west side', 'east side', 'left hand side', 'right hand side', 'entrance', 'void', 'vacant sites', 'shop void'}:
        return None
    if fn_low in {'return', 'west side', 'east side', 'left hand side', 'right hand side', 'void'}:
        return None
    if 'entrance' in full_name_low or 'hand side' in full_name_low or 'roadway' in full_name_low:
        return None
    if (sn_low.endswith('-street') or sn_low.endswith('-road') or sn_low.endswith('-lane')) and not h_num and not trade:
        return None
    if surname.startswith(('[', '(')):
        return None

    return {
        "year": "1903",
        "street": street,
        "house_number": h_num,
        "building_name": bldg,
        "surname": surname,
        "forename": forename,
        "trade": trade
    }

def parse_tsv(input_path, output_path):
    records = []
    current_streets = ["", "", ""]
    
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.rstrip('\r\n')
            if not line_str.strip():
                continue
                
            parts = [p.strip() for p in line_str.split('\t')]
            if parts[0] == "Number" and len(parts) > 1 and parts[1] == "Forenames":
                continue

            non_empty_parts = [p for p in parts if p and p != '-']
            if len(non_empty_parts) == 1:
                st_single = is_valid_street_header(non_empty_parts[0])
                if st_single:
                    current_streets = [st_single, st_single, st_single]
                    continue

            chunks = split_1903_line(parts)
            if not chunks:
                continue

            if len(chunks) == 1:
                c = chunks[0]
                st = is_valid_street_header(c[0]) if len(c) > 0 else None
                if st:
                    current_streets = [st, st, st]
                else:
                    target_st = current_streets[0]
                    if target_st:
                        rec = parse_record_chunk(c, target_st)
                        if rec:
                            records.append(rec)
            elif len(chunks) == 2:
                for col_idx, c in enumerate(chunks):
                    st = is_valid_street_header(c[0]) if len(c) > 0 else None
                    if st:
                        current_streets[col_idx] = st
                    else:
                        target_st = current_streets[col_idx] or current_streets[0]
                        if target_st:
                            rec = parse_record_chunk(c, target_st)
                            if rec:
                                records.append(rec)
            else:
                for col_idx, c in enumerate(chunks[:3]):
                    st = is_valid_street_header(c[0]) if len(c) > 0 else None
                    if st:
                        current_streets[col_idx] = st
                    else:
                        target_st = current_streets[col_idx] or current_streets[0]
                        if target_st:
                            rec = parse_record_chunk(c, target_st)
                            if rec:
                                records.append(rec)

    with open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["year", "street", "house_number", "building_name", "surname", "forename", "trade"])
        writer.writeheader()
        writer.writerows(records)

    print(f"Parsed {len(records)} records from {input_path} into {output_path}.")

if __name__ == "__main__":
    parse_tsv("raw_tsvs/1903.tsv", "volume_csvs/1903_cleaned.csv")
