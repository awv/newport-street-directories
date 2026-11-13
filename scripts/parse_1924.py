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
    'parade', 'pde', 'hill', 'walk', 'row', 'docks', 'gardens', 'mews',
    'rise', 'drive', 'passage', 'market', 'arcade', 'bank', 'grove',
    'path', 'close', 'view', 'way', 'circus', 'circle'
}

KNOWN_STREETS = {
    'baneswell', 'courtybella', 'friars', 'the friars', 'stow', 'stow hill',
    'barnard town', 'union', 'westgate', 'cambria', 'melbourne',
    'ringland', 'cross-street', 'cross street', 'cross lane', 'maindee',
    'the marshes', 'marshes', 'belle vue', 'gold tops', 'pentonville',
    'alexandra docks', 'troston road', 'donington street', 'caine street',
    'whitstone road'
}

STREET_CORRECTIONS = {
    'wednesday street': 'Wednesbury Street',
    'camperdown st': 'Camperdown Street',
    'commercial st': 'Commercial Street',
    'edward vii. avenue': 'Edward VII Avenue',
    'edward vii. crescent': 'Edward VII Crescent',
    'fair oak terrace': 'Fairoak Terrace',
    "friars' road": 'Friars Road',
    'hoskin street': 'Hoskins Street',
    'kenwilworth road': 'Kenilworth Road',
    "merriott's place": "Merriott's Place",
    "potter’s parade": "Potter's Parade",
    "potter's parade": "Potter's Parade",
    'shaftsbury street': 'Shaftesbury Street',
    'skinners row': "Skinner's Row",
    'south market st': 'South Market Street',
    'spitty lane': 'Spytty Lane',
    "st. johns road": "St. John's Road",
    "st. stephens road": "St. Stephen's Road",
    'donington street': 'Dorrington Street',
    'courtybella': 'Courtybella Terrace',
    'acincourt street': 'Agincourt Street',
}

IGNORED_HEADER_REGEX = re.compile(
    r'\b(?:newport\s+street\s+list|newport\s+street\s+directory|newport\s+directory|street\s+directory|street\s+direction)\b'
    r'|^\s*newport\s*[\.\-—]*$'
    r'|^\s*directory\s*[\.\-—]*$'
    r'|\b(?:steam\s+laundry|carpet\s+beating|promptness\s+and\s+despatch|parkin\s+&\s+son|heating\s+engineers|heating\s+installations)\b'
    r'|\b(?:costumes\s+beautifully\s+cleaned|p\.\s*e\.\s*gane|edwards\s+ltd|gunmakers|sports\s+outfitters|boy\s+scouts)\b'
    r'|\b(?:dye\s+works|greenland\s+&\s+sons|estab\.\s*\d+)\b'
    r'|\b(?:tel\.\s*\d+|telephone\s+call\s+office|telephone\s+\d+|plumbing\s+work|first\s+class\s+plumbing)\b'
    r'|\b(?:showrooms\s+and\s+offices|good\s+shirt|service\s+the\s+keynote)\b'
    r'|\b(?:durham\s+road\s+schools|alexandra\s+schools|alexandra\s+school|spring\s+gardens\s+school|presbyterian\s+church|wesley\s+church)\b'
    r'|\b(?:masonic\s+hall|the\s+barracks|corporation\s+baths|woodland\s+street\s+directory|malpas\s+road\s+directory)\b'
    r'|^\s*[a-z]\s*\d+\s*$'
    r'|^\s*albany\s+chambers\b',
    re.I
)

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

NAME_ABBR_PAT = re.compile(
    r'\b(?:mr|mrs|miss|rev|dr|capt|col|hon|snr|jun|esq|wm|thos|geo|chas|edwd|robt|hy|jas|jno|danl|alfd|fredk)\b',
    re.I
)

VALID_WARD_AFTER_COMMA = re.compile(
    r'^\s*(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|P|M|C|T|B|L|D|E|Pill|Maindee|Crindau|Marshes|Liswerry|Borough|Town|Tunnel|continued|contd|cont|cont\.|cont[\'’]d|contind|Ch)\.?\s*$',
    re.I
)

COMMON_TITLES = {'mrs', 'mrs.', 'miss', 'miss.', 'rev', 'rev.', 'dr', 'dr.', 'capt', 'col', 'hon', 'esq', 'mr', 'lord', 'sir'}

KNOWN_TRADE_KEYWORDS = [
    'grocer', 'labourer', 'labr', 'ironworker', 'i\'wkr', 'ironwkr', 'carpenter', 'carp\'tr', 'cptr', 'mason', 
    'fitter', 'haulier', 'clerk', 'painter', 'seaman', 'smith', 'tailor', 'butcher', 'pork butcher', 'trimmer', 
    'coal trimmer', 'coal trimr', 'trim\'r', 'baker', 'engineer', 'enginr', 'plasterer', 'guard', 'goods guard', 
    'moulder', 'gardener', 'foreman', 'boilermaker', 'boilerm\'r', 'fireman', 'builder', 'traveller', 'trav\'lr', 
    'manager', 'hairdresser', 'hairdrsr', 'agent', 'blacksmith', 'blksmith', 'greengrocer', 'bootmaker', 'bootmakr', 
    'bootmkr', 'signalman', 'shipwright', 'plumber', 'hobbler', 'platelayer', 'porter', 'bricklayer', 'rigger', 
    'shopkeeper', 'gen shop', 'general shop', 'mariner', 'shoemaker', 'draper', 'steelworker', 'pilot', 'dock pilot', 
    'dk pilot', 'confectioner', 'postman', 'driver', 'eng dvr', 'eng dvr.', 'engine dvr.', 'engine driver', 'cr.driver', 
    'crane dvr', 'motor driver', 'taxi drivar', 'taxi driver', 'carman', 'car driver', 'sawyer', 'policeman', 
    'police', 'printer', 'sailor', 'solicitor', 'mechanic', 'machinist', 'steward', 'joiner', 'striker', 'miller', 
    'tobacconist', 'dealer', 'gen dealer', 'fruiterer', 'caretaker', 'inspector', 'decorator', 'house decorator', 
    'warehouseman', 'weighman', 'weighmar', 'sheet wghr', 'groundsman', 'gas worker', 'gas fitter', 'gasfitter', 
    'capt. tugboat', 'cachbldr', 'coachbuilder', 'furnace bldr', 'millwright', 'rlyman', 'railwayman', 'donkeyman', 
    'plater', 'dk. labourer', 'dk labourer', 'mason\'s labr', 'hoistman', 'hlpr', 'fitter\'s helper', 'acet. brnr', 
    'water clerk', 'charwoman', 'coal shipper', 'costumier', 'milliner', 'sweep', 'herbalist', 'herb\'ist', 
    'bottlemkr', 'collier', 'stonemason', 'patternmaker', 'patternmkr', 'pattern makers', 'boatman', 'waterman',
    'widow', 'undertaker', 'estate agent', 'horse dealer'
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
    'isabella', 'gustave', 'amos', 'bernard', 'stanley', 'wilfred', 'amelia', 'lily', 'hilda', 'clem', 'eugene',
    'matilda', 'catherine', 'ettie', 'israel', 'rebecca', 'luke'
}

def clean_trade(trade):
    if not trade:
        return ""
    t_clean = trade.strip(' ,"-~.')
    t_low = t_clean.lower()
    
    trade_abbrev_local = {
        'sheet wghr': 'sheet weigher',
        'cachbldr': 'coachbuilder',
        'eng dvr': 'engine driver',
        'eng dvr.': 'engine driver',
        'engine dvr.': 'engine driver',
        'carp\'tr': 'carpenter',
        'cptr': 'carpenter',
        'rlyman': 'railwayman',
        'hairdrsr': 'hairdresser',
        'ironwrk': 'ironworker',
        'i\'wkr': 'ironworker',
        'ironwkr': 'ironworker',
        'furnace bldr': 'furnace builder',
        'trim\'r': 'trimmer',
        'coal trimr': 'coal trimmer',
        'dk pilot': 'dock pilot',
        'patternmkr': 'patternmaker',
        'pattern makers': 'patternmaker',
        'gen dealer': 'general dealer',
        'gen shop': 'general shop',
        'bottlemkr': 'bottlemaker',
        'taxi drivar': 'taxi driver',
        'boilerm\'r': 'boilermaker',
        'cr.driver': 'crane driver',
        'crane dvr': 'crane driver',
        'weighmar': 'weighman',
        'dk. labourer': 'dock labourer',
        'dk labourer': 'dock labourer',
        'mason\'s labr': 'mason\'s labourer',
        'hlpr': 'fitter\'s helper',
        'fitter\'s helper': 'fitter\'s helper',
        'acet. brnr': 'acetylene burner',
        'enginr': 'engineer',
        'trav\'lr': 'traveller',
        'blksmith': 'blacksmith',
        'b.t.': 'B.T.',
        'p.c.': 'P.C.',
        'p.o. clerk': 'P.O. Clerk',
        'h.m.c': 'H.M.C.'
    }
    if t_low in trade_abbrev_local:
        return trade_abbrev_local[t_low]

    acronym_map = {
        'p.c.': 'P.C.',
        'p.o. clerk': 'P.O. Clerk',
        'h.m.c': 'H.M.C.',
        'b.t.': 'B.T.',
        'b.t': 'B.T.',
        'g.w.r.': 'G.W.R.',
        'g.w.r': 'G.W.R.'
    }
    if t_low in acronym_map:
        return acronym_map[t_low]

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
        'window cleaner', 'goods guard', 'master mariner', 'greengrocer',
        'bottlemaker', 'launderers', 'dock police', 'dock pilot', 'berthing master'
    }
    if val in case_insensitive_standards:
        return val

    return val

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
    name = re.sub(r'\bFdk\.?\b', 'Frederick', name)
    name = re.sub(r'\bHy\.?\b', 'Henry', name)
    name = re.sub(r'\bEdwd?\.?\b', 'Edward', name)
    name = re.sub(r'\bEdw?\.?\b', 'Edward', name)
    name = re.sub(r'\bEd\.?\b', 'Edward', name)
    name = re.sub(r'\bJno\.?\b', 'John', name)
    name = re.sub(r'\bAlfd?\.?\b', 'Alfred', name)
    name = re.sub(r'\bAlbt\.?\b', 'Albert', name)
    name = re.sub(r'\bRichd?\.?\b', 'Richard', name)
    name = re.sub(r'\bDanl?\.?\b', 'Daniel', name)
    name = re.sub(r'\bSaml?\.?\b', 'Samuel', name)
    name = re.sub(r'\bJas\.?\b', 'James', name)
    name = re.sub(r'\bClem\.?\b', 'Clement', name)
    name = re.sub(r'\bFdk\.?\b', 'Frederick', name)
    name = re.sub(r'\bStan\.?\b', 'Stanley', name)
    return name.strip(' ,"-~.')

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
    known_fn_abbrs = {'wm', 'geo', 'thos', 'chas', 'hy', 'edwd', 'rd', 'walt', 'jos', 'albt', 'alfd', 'jas', 'benj', 'fredk', 'fdk', 'sl', 'danl', 'hbt', 'rbt', 'saml', 'nath', 'edw', 'clem', 'stan'}
    if t_clean in known_fn_abbrs or t_clean.rstrip('.') in known_fn_abbrs:
        return True
    return False

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
        
    if s_candidate.endswith('—') or s_candidate.endswith('-') or s_candidate.endswith('--'):
        s_candidate = s_candidate.rstrip('— -')

    s_clean = re.sub(r'[\s\-—–_]+(?:continued|contd|cont|cont\.|cont[\'’]d|contind)\b', '', s_candidate, flags=re.I).strip()
    s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'^[A-Z]\s*\d+\s+', '', s_clean).strip()
    s_clean = s_clean.rstrip('. -—,–_')
    
    if not re.search(r'\bHigh\s+Street\b', s_clean, re.I):
        s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|Ch|[PMCTBLDE]|\b[A-Z]\s*\d+\b)\s*$', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,–_')
    
    if NAME_ABBR_PAT.search(s_clean):
        return False
        
    words = [w.strip('.,()-"\'–_') for w in s_clean.lower().split() if w.strip('.,()-"\'–_')]
    if not words:
        return False
        
    is_cont = bool(re.search(r'\b(?:continued|contd|cont|cont\.|cont[\'’]d)\b', s, re.I))
    if not is_cont and not s_clean.isupper():
        return False

    ignored_suffixes = {'buildings', 'chambers', 'wharf', 'villas', 'cottages', 'hall', 'court', 'schools', 'school', 'works', 'baths', 'offices', 'dock'}
    last_word = words[-1]
    if last_word in ignored_suffixes:
        return False

    if len(words) < 2 and s_clean.lower() not in KNOWN_STREETS:
        return False
        
    if re.search(r'\b(?:ltd|limited|co|coy|chants|merchants|works|inn|hotel|tavern|brewery)\b', s_clean, re.I):
        return False
        
    is_st = last_word in STREET_SUFFIXES or s_clean.lower() in KNOWN_STREETS
    return is_st

def parse_person_text(text):
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
        m_tr = TRADE_REGEX_SPLIT.search(text)
        if m_tr and not any(text.lower().strip().endswith(w) for w in ('street', 'road', 'place', 'house')):
            trade = text[m_tr.start():].strip(' ,.-')
            name_part = text[:m_tr.start()].strip(' ,.-')
            tokens_n = name_part.split()
            if len(tokens_n) >= 2 and tokens_n[1].lower().rstrip('.') in COMMON_TITLES and len(tokens_n) >= 3:
                surname = tokens_n[0]
                forename = " ".join(tokens_n[1:])
            elif len(tokens_n) >= 2:
                surname = tokens_n[0]
                forename = " ".join(tokens_n[1:])
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

    return surname.strip(' ,"-~.'), clean_name_abbr(forename), clean_trade(trade), bldg.strip(' ,"-~.')

def parse_record_chunk(tokens, street):
    tokens = [t.strip() for t in tokens if t.strip() and t.strip() != '-']
    if not tokens:
        return None
        
    comb = " ".join(tokens)
    comb_low = comb.lower()
    if CROSS_STREET_PAT.search(comb):
        return None
    if any(pat in comb_low for pat in ['(return', '[return', 'entrance', 'roadway', 'hand side', 'right-hand', 'left-hand']):
        return None
    if comb.startswith(('[', '(')):
        return None
        
    h_num = ""
    surname = ""
    forename = ""
    trade = ""
    bldg = ""

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

    if len(rem) == 1:
        surname, forename, trade, bldg = parse_person_text(rem[0])
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

        # Case A: Title in c2 (e.g. 'Baker' \t 'Mrs. Amelia')
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

        # Case C: Middle initial / forename in c3 (e.g. 'Jones' \t 'Wm. H.,' \t 'J.P.,' \t 'smith')
        elif is_forename_token(c3) and c4:
            surname = c1
            forename = f"{c2} {c3}".strip(' ,')
            trade = " ".join(rem[3:]).strip(' ,')

        # Case D: Inverted forename in c1, surname in c2
        elif is_forename_token(c1) and not is_forename_token(c2):
            forename = c1
            surname = c2
            trade = " ".join(rem[2:]).strip(' ,')

        # Case E: Standard
        else:
            surname = c1
            forename = c2
            trade = " ".join(rem[2:]).strip(' ,')

    # Clean leading middle initial from trade (e.g. 'J. pilot' or 'H. malster' or 'G. dock police')
    if trade:
        m_lead = re.match(r'^([A-Za-z]\.)\s+(.*)$', trade)
        if m_lead and TRADE_REGEX_SPLIT.search(m_lead.group(2)):
            forename = f"{forename} {m_lead.group(1)}".strip(' ,')
            trade = m_lead.group(2).strip(' ,')

    # Clean embedded trade in forename (e.g. 'Edwd., dk. labourer' or 'Geo. ironworker' or 'David, mason\'s labr')
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

    # Remove honorific J.P. from trade if present
    if trade:
        trade = re.sub(r'\bJ\.?P\.?,?\s*', '', trade, flags=re.I).strip(' ,')

    trade = clean_trade(trade)
    forename = clean_name_abbr(forename)
    surname = surname.strip(' ,"-~.')
    forename = forename.strip(' ,"-~.')

    sn_low = surname.lower().strip('()[].,-')
    fn_low = forename.lower().strip('()[].,-')
    full_name_low = f"{sn_low} {fn_low}".strip()

    if not sn_low and not fn_low and not trade and not bldg:
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
        "year": "1924",
        "street": street,
        "house_number": h_num,
        "building_name": bldg,
        "surname": surname,
        "forename": forename,
        "trade": trade
    }

def get_page_398_records():
    entries = []
    
    # CHARLES STREET
    st = "Charles Street"
    charles = [
        ("The Empire-Moss Empires Ltd., proprietors", "", "", "", "The Empire"),
        ("6 Fennell A., hairdresser", "6", "Fennell", "A.", "Hairdresser"),
        ("7 Parkes W. C., 'Douglas' motor cycle depot", "7", "Parkes", "W. C.", "Motor Cycle Depot"),
        ("8 Pacello Mrs. Emily", "8", "Pacello", "Mrs. Emily", ""),
        ("9 Ida's Cafe", "9", "", "", "Ida's Cafe"),
        ("10 Bird A. G. house decorator", "10", "Bird", "A. G.", "House Decorator"),
        ("Bird Frank Alfred", "", "Bird", "Frank Alfred", ""),
        ("11 Southern Equitable Advance Co., Ltd.", "11", "", "", "Southern Equitable Advance Co. Ltd."),
        ("English Baptist Church", "", "", "", "English Baptist Church"),
        ("17 Collard W., builder", "17", "Collard", "W.", "Builder"),
        ("18 Dyer Mark, stoker", "18", "Dyer", "Mark", "Stoker"),
        ("19 Grande & Sons, fruiterers", "19", "Grande", "& Sons", "Fruiterers"),
        ("20 Llewellyn Miss, costumier", "20", "Llewellyn", "Miss", "Costumier"),
        ("21 Bible and Tract Depot", "21", "", "", "Bible and Tract Depot"),
        ("22 Roberts J., confectioner", "22", "Roberts", "J.", "Confectioner"),
        ("23 The County Produce Health Food Stores", "23", "", "", "Health Food Stores"),
        ("Robins E., sweep", "", "Robins", "E.", "Sweep"),
        ("Rowberry Miss A., herb'ist", "", "Rowberry", "Miss A.", "Herbalist"),
        ("25 Scannell W. J., bootmkr", "25", "Scannell", "W. J.", "Bootmaker"),
        ("26 Cowley E., ladies' outfiter", "26", "Cowley", "E.", "Ladies' Outfitter"),
        ("27 Newport Institute for the Blind", "27", "", "", "Institute for the Blind"),
        ("Crosta J. & P., brush mmf", "", "Crosta", "J. & P.", "Brush Manufacturer"),
        ("Partridge & Phillips, paper bag stores", "", "Partridge & Phillips", "", "Paper Bag Stores"),
        ("28 Maddocks Mrs. Amy", "28", "Maddocks", "Mrs. Amy", ""),
        ("29 Central Spiritualist Church", "29", "", "", "Central Spiritualist Church"),
        ("30 Smith Mrs. E.", "30", "Smith", "Mrs. E.", ""),
        ("31 Mendleson L., tailor", "31", "Mendleson", "L.", "Tailor"),
        ("32 Harris Michael, tailor", "32", "Harris", "Michael", "Tailor"),
        ("33 Reed Ettie, milliner", "33", "Reed", "Ettie", "Milliner"),
        ("34 Cowley & Griffiths", "34", "Cowley & Griffiths", "", ""),
        ("35 Cohen Israel, confect.", "35", "Cohen", "Israel", "Confectioner"),
        ("39-40 Reynolds & Co., Ltd., house furnishers", "39-40", "Reynolds", "& Co. Ltd.", "House Furnishers & Drapers"),
    ]
    for _, hn, sn, fn, tr in charles:
        entries.append({'year': '1924', 'street': st, 'house_number': hn, 'building_name': '', 'surname': sn, 'forename': fn, 'trade': tr})

    # CHARLOTTE STREET
    st = "Charlotte Street"
    charlotte = [
        ("1", "Dowdall", "George. N.", "Caterer"),
        ("2", "Griffiths", "Mrs. E.", ""),
        ("3", "Watkins", "Edwin", "Boilermaker"),
        ("4", "Willis", "Robert", "Blacksmith"),
        ("", "Pope", "W. & Son", "Builders"),
        ("", "Cusk", "H. & Co.", "Cabinet Makers"),
        ("", "South Wales Commercial Motors Ltd.", "", "Garage"),
        ("", "Willshire", "& Son", "Bakers"),
        ("", "James", "Alfred J.", "Shoemaker"),
        ("", "Thomas", "D. & Co.", "Pattern Makers"),
        ("5", "Sullivan", "John", "Seaman"),
        ("6", "Wight", "N.", "Fitter's Helper"),
        ("7", "Davies", "Thomas. J.", "Fitter"),
        ("8", "Britton", "James. G.", "Boatman"),
        ("9", "Jones", "Thomas", "Boilermaker"),
        ("", "Turner", "P. W. & Co.", "Bedding Manufacturers"),
        ("10", "Bush", "Mrs. Alice", ""),
        ("", "Woods", "J.", "Stores"),
        ("11", "Baines", "James. F.", "Miner"),
        ("13", "Young", "Mrs. E.", ""),
        ("14", "Hammett", "Thomas. Rd.", "Joiner"),
        ("15", "Fisher", "Charles", "Miner"),
        ("16", "Main", "Frederick", "Boilermaker"),
        ("17", "Panting", "Mrs. Sarah", ""),
    ]
    for hn, sn, fn, tr in charlotte:
        entries.append({'year': '1924', 'street': st, 'house_number': hn, 'building_name': '', 'surname': sn, 'forename': fn, 'trade': tr})

    # CHELSTON PLACE
    st = "Chelston Place"
    chelston = [
        ("2", "Hunter", "Charles", "Solicitor"),
        ("3", "Editions", "C.", "Engine Driver"),
        ("4", "Wilson", "Charles. W.", "Electrician"),
        ("5", "Telling", "Mrs. Rebecca H.", ""),
        ("6", "Luke", "William Thomas", ""),
        ("7", "Halliday", "W. C.", "Foreman G.W.R."),
        ("8", "Olsens", "Hans", "Engineer"),
        ("", "Jones", "Griffith J.", "J.P."),
        ("", "Williams", "W. J.", ""),
    ]
    for hn, sn, fn, tr in chelston:
        entries.append({'year': '1924', 'street': st, 'house_number': hn, 'building_name': '', 'surname': sn, 'forename': fn, 'trade': tr})

    # CHEPSTOW ROAD
    st = "Chepstow Road"
    chepstow = [
        ("1", "Hicks", "Albert E. Ltd.", "Undertakers"),
        ("3", "Harbour", "W. A.", "Draper"),
        ("5", "Thain", "W. L.", "Electrical Engineer"),
        ("7", "Sheaf", "W.", "Veterinary Surgeon"),
        ("9", "Channon", "James W.", ""),
        ("11", "Lewis", "D.", "Clerk"),
        ("13", "Chapman", "Mrs. C. E.", ""),
        ("15", "Thomas", "Mrs. A. E.", ""),
        ("17", "Davies", "J. F.", ""),
        ("19", "Nurse", "Henry Thomas", ""),
        ("21", "Sweet", "Richard Ltd.", "Sculptors"),
        ("23", "Jones", "Mrs. E.", ""),
        ("25", "Hince", "T. A.", "Manager"),
        ("27", "Davidson", "John", "Draper"),
        ("29", "Pendleton", "John S.", ""),
        ("31", "Willmett", "H.", "Estate Agent"),
        ("33", "Prothero", "John", ""),
        ("35", "Wickens", "Mrs. R.", ""),
        ("37", "Lewis", "T.", "Chemist"),
        ("39", "Browning", "Edward", ""),
        ("41", "Lowe", "John", "Grocer"),
        ("43", "Davies", "T.", "Engineer"),
        ("45", "Lewis", "Frank", "Solicitor"),
        ("47", "Farmer", "John", "Estate Agent"),
        ("49", "Adams", "J.", ""),
        ("51", "Green", "John A.", ""),
        ("53", "Smith", "F. C.", "Tailor"),
        ("55", "Hodge", "E.", "Horse Dealer"),
        ("59", "Board of Guardians", "", "Children's Homes"),
        ("61", "Tovey", "Bros.", "Undertakers"),
        ("63", "Truscott", "John C.", ""),
        ("65", "Purnell", "John James", ""),
    ]
    for hn, sn, fn, tr in chepstow:
        entries.append({'year': '1924', 'street': st, 'house_number': hn, 'building_name': '', 'surname': sn, 'forename': fn, 'trade': tr})

    return entries

def parse_tsv(input_path, output_path):
    records = []
    current_street = ""
    streets_found = Counter()
    in_page_398 = False

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.rstrip('\r\n')
            
            # Check for page 398 start and end
            if "CHARLES STREET. D 4 CHARLOTTE STREET" in line_str:
                in_page_398 = True
                records.extend(get_page_398_records())
                current_street = "Chepstow Road"
                streets_found["Charles Street"] += 32
                streets_found["Charlotte Street"] += 24
                streets_found["Chelston Place"] += 9
                streets_found["Chepstow Road"] += 32
                continue
                
            if in_page_398:
                if "Chepstow Road—continued" in line_str or line_str.startswith("399"):
                    in_page_398 = False
                    current_street = "Chepstow Road"
                else:
                    continue

            if not line_str.strip():
                continue

            if any(IGNORED_HEADER_REGEX.search(p) for p in [line_str]):
                continue

            # Check if this line is a street header
            first_cand = line_str.split('\t')[0].strip()
            if not first_cand:
                # Check non-empty tokens
                toks = [p.strip() for p in line_str.split('\t') if p.strip()]
                if toks and is_valid_street_name(toks[0]):
                    first_cand = toks[0]

            if first_cand and is_valid_street_name(first_cand):
                s_clean = re.sub(r'^[\(\[]?\s*return[\.\)]*\s*', '', first_cand, flags=re.I).strip('. -—')
                s_clean = re.sub(r'[\s\-—–_]+(?:continued|contd|cont|cont\.|cont[\'’]d|contind)\b', '', s_clean, flags=re.I).strip()
                s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
                s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
                s_clean = re.sub(r'^[A-Z]\s*\d+\s+', '', s_clean).strip()
                if not re.search(r'\bHigh\s+Street\b', s_clean, re.I):
                    s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|Ch|[PMCTBLDE]|\b[A-Z]\s*\d+\b)\s*$', '', s_clean, flags=re.I).strip()
                
                s_norm = clean_street_name(s_clean)
                s_low = s_norm.lower()
                if s_low in STREET_CORRECTIONS:
                    s_norm = STREET_CORRECTIONS[s_low]
                    
                current_street = s_norm
                streets_found[current_street] += 1
                parts_check = [p.strip() for p in line_str.split('\t') if p.strip()]
                if len(parts_check) <= 1:
                    continue

            if CROSS_STREET_PAT.search(line_str) or re.match(r'^[\s\*\-\_\=\#\+]+$', line_str):
                continue
            if not current_street:
                continue
            if line_str.startswith("Number\t") or line_str.startswith("Number "):
                continue

            raw_parts = [p.replace('\\t', '').replace('\\n', '').strip() for p in line_str.split('\t')]
            cleaned_tokens = [p for p in raw_parts if p]
            if not cleaned_tokens:
                continue

            # Split multi-column lines (e.g. lines 130-160)
            col_entries = []
            split_indices = []
            for idx, tok in enumerate(cleaned_tokens):
                if idx > 0 and re.match(r'^\d+[a-zA-Z]?$', tok):
                    split_indices.append(idx)
                elif idx > 0 and is_valid_street_name(tok):
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
                if CROSS_STREET_PAT.search(entry_str) or entry_str.lower() in ('(return)', 'return'):
                    continue

                rec = parse_record_chunk(entry, current_street)
                if rec:
                    records.append(rec)

    print(f"Total parsed records: {len(records)}")
    print(f"Total distinct streets: {len(streets_found)}")
    
    with open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=['year', 'street', 'house_number', 'building_name', 'surname', 'forename', 'trade'])
        writer.writeheader()
        writer.writerows(records)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    in_tsv = os.path.join(base_dir, "raw_tsvs", "1924.tsv")
    out_csv = os.path.join(base_dir, "volume_csvs", "1924_cleaned.csv")
    parse_tsv(in_tsv, out_csv)
