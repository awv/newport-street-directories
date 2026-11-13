import csv
import re
import os

try:
    import sys
    sys.path.append(os.getcwd())
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

    acronym_map = {
        'p.c.': 'P.C.',
        'p.o. clerk': 'P.O. Clerk',
        'h.m.c': 'H.M.C.',
        'g.w.r.': 'G.W.R.',
        'g.w.r': 'G.W.R.',
        'b.t.': 'B.T.',
        'b.t': 'B.T.',
        'b. & m.r.': 'B. & M.R.',
        'b. & m.r': 'B. & M.R.'
    }
    if t_low in acronym_map:
        return acronym_map[t_low]

    local_abbrev = {
        'eng. driver': 'engine driver',
        'eng.driver': 'engine driver',
        'eng. dvr': 'engine driver',
        'eng.dvr': 'engine driver',
        'eng. dvr.': 'engine driver',
        'dk. labourer': 'dock labourer',
        'dk.labourer': 'dock labourer',
        'dk labourer': 'dock labourer',
        'dk police': 'dock police',
        'dk.police': 'dock police',
        'mas. mar.': 'master mariner',
        'mas. mar': 'master mariner',
        'boilermakr': 'boilermaker',
        'boilerm\'r': 'boilermaker',
        'bottlemkr': 'bottlemaker',
        'bottle wkr': 'bottle worker',
        'bottle blr': 'bottle blower',
        'bottle blowr': 'bottle blower',
        'glass wkr': 'glass worker',
        'glassworker': 'glass worker',
        'glassblower': 'glass blower',
        'carpntr': 'carpenter',
        'carptr': 'carpenter',
        'carptr, &c.': 'carpenter',
        'carptr,&c.': 'carpenter',
        'carpntr&joiner': 'carpenter and joiner',
        'carpntr & joiner': 'carpenter and joiner',
        'carpenter\'s asst': 'carpenter\'s assistant',
        'shopk\'p\'r': 'shopkeeper',
        'shopkpr': 'shopkeeper',
        'l\'ndress': 'laundress',
        'ins. agent': 'insurance agent',
        'wareh\'sem\'n': 'warehouseman',
        'coal trmr': 'coal trimmer',
        'sheet wghr': 'sheet weigher',
        'fitter\'s hlpr': 'fitter\'s helper',
        'blksmith': 'blacksmith',
        'inspectr': 'inspector',
        'hairdres\'r': 'hairdresser',
        'paint\'r': 'painter',
        'paint\'r & dectr': 'painter and decorator',
        'conductr': 'conductor',
        'coal tipr': 'coal tipper',
        'tug-boatman': 'tug boatman'
    }
    if t_low in local_abbrev:
        return local_abbrev[t_low]

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
        'window cleaner', 'dock police', 'master mariner', 'gas worker',
        'glass blower', 'glass worker'
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
    name = re.sub(r'\bEdwd?\.?\b', 'Edward', name)
    name = re.sub(r'\bJno\.?\b', 'John', name)
    name = re.sub(r'\bAlfd?\.?\b', 'Alfred', name)
    name = re.sub(r'\bAlbt\.?\b', 'Albert', name)
    name = re.sub(r'\bDanl?\.?\b', 'Daniel', name)
    name = re.sub(r'\bJas\.?\b', 'James', name)
    name = re.sub(r'\bRichd?\.?\b', 'Richard', name)
    name = re.sub(r'\bSaml?\.?\b', 'Samuel', name)
    name = re.sub(r'\bWalt\.?\b', 'Walter', name)
    name = re.sub(r'\bRd\.?\b', 'Richard', name)
    name = re.sub(r'\bJos\.?\b', 'Joseph', name)
    name = re.sub(r'\bSl\.?\b', 'Samuel', name)
    name = re.sub(r'\bHbt\.?\b', 'Herbert', name)
    name = re.sub(r'\bRbt\.?\b', 'Robert', name)
    name = re.sub(r'\bEdw\.?\b', 'Edward', name)
    name = re.sub(r'\bFdk\.?\b', 'Frederick', name)
    name = re.sub(r'\bNath\.?\b', 'Nathaniel', name)
    return name.strip(' ,"-~.')

COMMON_TITLES = {'mrs', 'mrs.', 'miss', 'miss.', 'rev', 'rev.', 'dr', 'dr.', 'capt', 'col', 'hon', 'lady', 'sir'}

KNOWN_TRADE_KEYWORDS = [
    'grocer', 'labourer', 'ironworker', 'ironwrkr', 'ironwkr', 'carpenter', 'mason', 'fitter', 'haulier', 
    'clerk', 'painter', 'seaman', 'smith', 'tailor', 'tailoress', 'butcher', 'trimmer', 'baker', 
    'engineer', 'plasterer', 'guard', 'moulder', 'gardener', 'gard\'nr', 'foreman', 'boilermaker', 
    'boilermakr', 'fireman', 'builder', 'traveller', 'manager', 'hairdresser', 'agent', 'blacksmith', 
    'blksmith', 'greengrocer', 'bootmaker', 'bootmkr', 'signalman', 'shipwright', 'plumber', 'hobbler', 
    'platelayer', 'porter', 'bricklayer', 'rigger', 'shopkeeper', 'shopk\'p\'r', 'mariner', 'shoemaker', 
    'draper', 'steelworker', 'pilot', 'confectioner', 'postman', 'driver', 'sawyer', 
    'policeman', 'printer', 'sailor', 'solicitor', 'mechanic', 'machinist', 'steward', 
    'joiner', 'striker', 'miller', 'tobacconist', 'dealer', 'fruiterer', 'caretaker', 
    'inspector', 'decorator', 'warehouseman', 'saddler', 'shunter', 'boatman', 
    'hoistman', 'milkman', 'cooper', 'dairyman', 'watchmaker', 'electrician', 'accountant', 
    'hawker', 'dressmaker', 'cabinetmaker', 'cabinetmkr', 'wheelwright', 'docker', 'roller', 
    'furnaceman', 'chemist', 'motor driver', 'motorman', 'weighman', 'gasfitter', 'puddler', 
    'timekeeper', 'newsagent', 'checker', 'sailmaker', 'coachman', 'stevedore', 
    'storekeeper', 'packer', 'outfitter', 'tinsmith', 'carman', 'cabman', 'surgeon', 'ostler', 
    'watchman', 'shearer', 'patternmaker', 'architect', 'surveyor', 'dentist', 'shipper', 
    'weigher', 'sheet wghr', 'groundsman', 'mason\'s labr', 'glass worker', 'glass blowr', 
    'glass blower', 'glass wkr', 'glassworker', 'glassblower', 'brick bnr', 'gas worker', 'gas stoker', 
    'bottle blowr', 'coach builder', 'cr.driver', 'crane driver', 
    'boilerm\'r', 'trim\'r', 'bootmakr', 'blksmith', 'engine dvr.', 'engine dvr', 'engine driver', 
    'dock police', 'dockpolice', 'glasswkr', 'ironmkr', 'collier', 'miners\' agent', 'p.c.', 'b.t.',
    'brass finisher', 'rivetter', 'riveter', 'horseshoer', 'wood turner', 'optician',
    'fishmonger', 'beer retailer', 'publican', 'innkeeper', 'waiter', 'sugar boiler',
    'telegraphist', 'typewriter', 'nurse', 'midwife', 'cinematograph operator',
    'taxi drivr', 'brewery hd', 'brewery hd.', 'fish bar', 'marine stores',
    'brklayer', 'bottlemaker', 'dk. labourer', 'dk.labourer', 's. mechanic', 'wireman',
    'laundress', 'l\'ndress', 'bookkeeper', 'driller', 'brushmaker', 'quarryman'
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
    'eli', 'clement', 'patrick', 'dennis', 'jeremiah', 'reuben', 'hannibal', 'danl', 'rd', 'walt', 'jos', 'sl'
}

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
    r'|^\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s*(?:side|sidr)?\s*[\)\]]?\s*$'
    r'|^\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s+(?:side|sidr)\b'
    r'|^\s*(?:from\s+)?[a-z0-9\s\.\-]+\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s*[\)\]]?\s*(?:opposite\s+[a-z0-9\s\.\-]+)?\s*$'
    r'|^\s*opposite\s+(?:maindee\s+schools|board\s+schools|st\.\s*woolos\s+church|malpas\s+school|kensington\s+place|stow\s+park|stow-park)'
    r'|^\s*last\s+corporation[\s\-]*road\s+street\s+on\s+left[\s\-]+hand\s+side'
    r'|^\s*(?:west|east|north|south)\s+side\s+of\b'
    r'|\bcontinuation\b'
    r'|\btowards\b',
    re.I
)

# Load known street names from data.csv (excluding 1910) for validation reference
known_streets = set()
if os.path.exists("data.csv"):
    with open("data.csv", "r", encoding="utf-8") as f_data:
        reader_data = csv.DictReader(f_data)
        for row_data in reader_data:
            if row_data.get("year") != "1910":
                st_val = row_data.get("street", "").strip().lower()
                if st_val:
                    known_streets.add(st_val)

def is_valid_street_name(s):
    s = s.strip()
    if not s:
        return False
        
    if re.search(r'\b(?:from|to|off)\b', s, re.I):
        return False

    s_clean = s
    s_clean = re.sub(r'[\s\-—]+continued\b', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
    
    # Strip trailing grid references like ", E 2", " B 4"
    s_clean = re.sub(r'[\.\s,]+[A-Z][\s\.,\d]*$', '', s_clean, flags=re.I).strip(' ,.-')
    
    if s_clean.isdigit() or re.match(r'^\d+[-—\d\s]*[a-zA-Z]?$', s_clean):
        return False
    
    if len(s_clean) <= 1:
        return False
        
    ignored_streets = {
        "left hand side", "right hand side", "east side", "west side", "north side", "south side",
        "acronyms", "abbreviations", "newport street directory", "the block",
        "temperance hall", "wharf", "windsor castle", "york house",
        "midland bank chambers", "victoria chambers", "stow-hill to railway bridge", "london city & midland bank",
        "vacant sites"
    }
    if s_clean.lower() in ignored_streets:
        return False
        
    if CROSS_STREET_PAT.search(s_clean):
        return False
        
    if re.search(r'\bto\b', s_clean, re.I):
        return False

    if any(b in s_clean.lower() for b in ['chambers', 'bank', 'hotel', 'inn', 'chapel', 'church']):
        return False
        
    if s_clean.lower() in known_streets:
        return True
        
    if not any(c.islower() for c in s_clean):
        return True
        
    suffixes = {'street', 'road', 'avenue', 'place', 'terrace', 'hill', 'lane', 'crescent', 'cres', 'cres.', 'parade', 'pde', 'par', 'par.', 'way', 'drive', 'grove', 'villas', 'gardens', 'walk', 'square', 'court', 'close', 'view', 'park', 'green', 'st', 'rd', 'av', 'pl', 'ln', 'sq', 'ct', 'cl', 'pk'}
    tokens = re.findall(r'[a-zA-Z\.]+', s_clean)
    if tokens:
        last_word = tokens[-1].lower().strip('.')
        if last_word in suffixes:
            if re.match(r'^\d', s):
                return False
            resident_pattern = r'\b(?:mrs|mr|miss|rev|dr|doctor|nurse|junior|senior|widow|son|sons|bros|brothers|co|ltd|limited|labourer|labr|carpenter|clerk|mason|fitter|builder|haulier|fireman|guard|shoemaker|draper|baker|rigger|tailor|painter|smith|engineer|mechanic|driver|steelworker|platelayer|porter|agent|merchant|hairdresser|dressmaker|postman|seaman|watchman|butcher)\b'
            if re.search(resident_pattern, s, re.I):
                return False
            return True
            
    return False

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
    if re.match(r'^[a-zA-Z]\.$', t_raw):
        return True
    if token.endswith(','):
        return True
    known_fn_abbrs = {'wm', 'geo', 'thos', 'chas', 'hy', 'edwd', 'rd', 'walt', 'jos', 'albt', 'alfd', 'jas', 'benj', 'fredk', 'sl', 'danl', 'hbt', 'rbt', 'saml', 'fdk', 'nath', 'edw'}
    if t_clean in known_fn_abbrs or t_clean.rstrip('.') in known_fn_abbrs:
        return True
    return False

def parse_resident_chunk(tokens):
    """
    Parses a sequence of resident tokens (e.g. ['4', 'Rosser', 'Henry E.'] or ['8', 'Boucher', 'George,', 'packer']).
    Returns (h_num, bldg, surname, forename, trade)
    """
    tokens = [t.strip() for t in tokens if t.strip()]
    if not tokens:
        return "", "", "", "", ""
        
    h_num = ""
    # Check if first token is a house number (digits, e.g. '1', '12a', '12-14')
    if re.match(r'^\d+[-—\d\/]*[a-zA-Z]?$', tokens[0]):
        h_num = tokens[0]
        rem = tokens[1:]
    else:
        rem = tokens
        
    if not rem:
        return h_num, "", "", "", ""
        
    # Check if rem is 'Void' or layout marker
    if rem[0].lower() in ('void', 'vacant', 'return', '(return)'):
        return h_num, "", "", "", ""

    surname = ""
    forename = ""
    trade = ""
    bldg = ""

    # Case A: Title in rem[1] or rem[0] (e.g. ['Palmer', 'Mrs. M.', 'shopk\'p\'r'] or ['Mrs.', 'Palmer'])
    if len(rem) >= 2 and is_forename_token(rem[1]) and (rem[1].lower().rstrip('.') in COMMON_TITLES):
        surname = rem[0]
        fn_parts = [rem[1]]
        idx = 2
        while idx < len(rem):
            tok = rem[idx]
            tok_low = tok.lower().rstrip('.,')
            if TRADE_REGEX_SPLIT.search(tok) and tok_low not in NAME_TOKENS:
                trade = " ".join(rem[idx:])
                break
            elif is_forename_token(tok):
                fn_parts.append(tok)
                idx += 1
            else:
                trade = " ".join(rem[idx:])
                break
        forename = " ".join(fn_parts)

    # Case B: First token in rem is a forename/title, second is surname (inverted header, e.g. ['Rd.', 'Richards', 'haulier'])
    elif len(rem) >= 2 and is_forename_token(rem[0]) and not is_forename_token(rem[1]):
        forename = rem[0]
        surname = rem[1]
        if len(rem) > 2:
            trade = " ".join(rem[2:])

    # Case C: Standard ['Surname', 'Forename', ...]
    else:
        surname = rem[0]
        if len(rem) >= 2:
            fn_parts = [rem[1]]
            idx = 2
            while idx < len(rem):
                tok = rem[idx]
                tok_low = tok.lower().rstrip('.,')
                if TRADE_REGEX_SPLIT.search(tok) and tok_low not in NAME_TOKENS:
                    trade = " ".join(rem[idx:])
                    break
                elif is_forename_token(tok):
                    fn_parts.append(tok)
                    idx += 1
                else:
                    trade = " ".join(rem[idx:])
                    break
            forename = " ".join(fn_parts)

    # Clean embedded trades in forename (e.g. 'Wm.gard\'nr' or 'George, labourer')
    if forename:
        if ',' in forename:
            fo_p, tr_p = forename.split(',', 1)
            forename = fo_p.strip()
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

    # Clean trade prefixes like 'G., taxi drivr' or 'H. weighman'
    if trade and ',' in trade:
        p_init, p_tr = [x.strip() for x in trade.split(',', 1)]
        if is_forename_token(p_init):
            forename = f"{forename} {p_init}".strip()
            trade = p_tr
    elif trade:
        m_lead = re.match(r'^([A-Za-z]\.)\s+(.*)$', trade)
        if m_lead and TRADE_REGEX_SPLIT.search(m_lead.group(2)):
            forename = f"{forename} {m_lead.group(1)}".strip()
            trade = m_lead.group(2).strip()

    # Check if surname contains comma separated trade (e.g. 'Charles, steam joinery')
    if surname and ',' in surname:
        s_p, tr_p = surname.split(',', 1)
        surname = s_p.strip()
        if not trade:
            trade = tr_p.strip()

    # Check building keywords
    bldg_keywords = {'house', 'villa', 'cottage', 'cot', 'hotel', 'chambers', 'hall', 'buildings', 'school', 'church', 'chapel', 'arms'}
    if trade and any(kw in trade.lower() for kw in bldg_keywords) and not TRADE_REGEX_SPLIT.search(trade):
        bldg = trade
        trade = ""

    surname = surname.strip(' ,"-~.')
    forename = clean_name_abbr(forename)
    trade = clean_trade(trade)
    bldg = bldg.strip(' ,"-~.')

    return h_num, bldg, surname, forename, trade

def parse_tsv(input_path, output_path):
    records = []
    current_street = ""
    prev_surname = ""
    prev_trade = ""
    
    with open(input_path, "r", encoding="utf-8") as f_in:
        for row_idx, raw_line in enumerate(f_in, start=1):
            line = raw_line.rstrip('\r\n')
            if not line or not line.strip():
                continue
                
            line_str = line.strip()
            line_upper = line_str.upper()

            # Skip table headers & directory banners
            if "NEWPORT STREET DIRECTORY" in line_upper:
                continue
            if any(ad in line_upper for ad in ["THE NEWPORT STEAM LAUNDRY", "LANGMAID", "STAR MONEY SOCIETY"]):
                continue
            if line_str.startswith("Number\t") or line_str.startswith("Number "):
                continue

            # Check if row contains a street header
            if is_valid_street_name(line_str):
                s_clean = line_str
                s_clean = re.sub(r'[\.\s,]+[A-Z][\s\.,\d]*$', '', s_clean, flags=re.I).strip(' ,.-')
                current_street = clean_street_name(s_clean)
                continue

            # Explicit street headers
            if line_upper.startswith("FACTORY ROAD") or line_upper.startswith("FACTORY-ROAD"):
                current_street = "Factory Road"
                continue
            if "BISHOPSGATE PAR" in line_upper:
                current_street = "Bishopsgate Parade"
                continue
            if line_upper.startswith("HIGH STREET") or line_upper.startswith("HIGH-STREET"):
                current_street = "High Street"
                if "DOBELL" in line_upper:
                    records.append({
                        "year": "1910",
                        "street": "High Street",
                        "house_number": "9",
                        "building_name": "",
                        "surname": "Dobell",
                        "forename": "John & Co. Ltd.",
                        "trade": "wine and spirit merchants"
                    })
                continue

            # High Street right-hand column entries from Shaftesbury Street rows 9720-9725
            if row_idx == 9720 and "Old Green Hotel" in line:
                records.append({"year": "1910", "street": "High Street", "house_number": "3", "building_name": "Old Green Hotel", "surname": "Hayden", "forename": "E. P.", "trade": ""})
            elif row_idx == 9721 and "Bristol Dining Rooms" in line:
                records.append({"year": "1910", "street": "High Street", "house_number": "4", "building_name": "Bristol Dining Rooms", "surname": "James", "forename": "Mrs. S.", "trade": ""})
            elif row_idx == 9722 and "Smith Albert" in line:
                records.append({"year": "1910", "street": "High Street", "house_number": "5", "building_name": "", "surname": "Smith", "forename": "Albert", "trade": "chemist and surgeon dentist"})
            elif row_idx == 9723 and "Great Western" in line:
                records.append({"year": "1910", "street": "High Street", "house_number": "6", "building_name": "Great Western Dining Rooms", "surname": "Dowdall", "forename": "Hy.", "trade": ""})
            elif row_idx == 9724 and "County Club" in line:
                records.append({"year": "1910", "street": "High Street", "house_number": "7", "building_name": "Newport & County Club", "surname": "Newport & County Club", "forename": "", "trade": ""})
            elif row_idx == 9725 and "King's Head" in line:
                records.append({"year": "1910", "street": "High Street", "house_number": "8", "building_name": "King's Head Hotel", "surname": "Blackburn & Co.", "forename": "", "trade": "hotel proprietors"})

            # Cross street and layout markers
            if CROSS_STREET_PAT.search(line_str) or re.match(r'^[\s\*\-\_\=\#\+]+$', line_str):
                continue
            if line_str.lower() in ('(return)', 'return', '[left hand side.]', '[left hand sidr.]', '[right hand side.]'):
                continue

            # Factory Road clean entries
            if current_street.lower() in ["factory road", "factory-road"]:
                if "Gas Works" in line_str:
                    records.append({
                        "year": "1910",
                        "street": "Factory Road",
                        "house_number": "",
                        "building_name": "",
                        "surname": "",
                        "forename": "Newport Gas Works",
                        "trade": ""
                    })
                elif "Dos lodge" in line_str or "Evans" in line_str:
                    records.append({
                        "year": "1910",
                        "street": "Factory Road",
                        "house_number": "",
                        "building_name": "Dos Lodge",
                        "surname": "Evans",
                        "forename": "Mrs. E.",
                        "trade": ""
                    })
                elif "Cordes" in line_str or "Dos Works" in line_str:
                    records.append({
                        "year": "1910",
                        "street": "Factory Road",
                        "house_number": "",
                        "building_name": "Dos Works",
                        "surname": "Cordes (Dos Works) Ltd.",
                        "forename": "",
                        "trade": "Nail, spike, etc. manufacturers"
                    })
                continue

            if not current_street:
                continue

            # Check if line is single-string (no tabs)
            if '\t' not in line:
                m_lead_num = re.match(r'^(\d+[-—\d\/]*[a-zA-Z]?)\s+(.*)$', line_str)
                if m_lead_num:
                    hn = m_lead_num.group(1)
                    rest = m_lead_num.group(2).strip()
                    tokens = [hn] + rest.split()
                    h_num, bldg, surname, forename, trade = parse_resident_chunk(tokens)
                    if surname or forename or trade or bldg:
                        records.append({
                            "year": "1910",
                            "street": current_street,
                            "house_number": h_num,
                            "building_name": bldg,
                            "surname": surname,
                            "forename": forename,
                            "trade": trade
                        })
                continue

            # Tab-delimited row processing
            parts = [p.strip() for p in line.split('\t')]
            
            # Check for two-column layout on directory page (e.g. line 271 with 2+ consecutive empty tabs)
            chunks = []
            cur_chunk = []
            empty_count = 0
            for p in parts:
                if not p:
                    empty_count += 1
                    if empty_count >= 2 and cur_chunk:
                        chunks.append(cur_chunk)
                        cur_chunk = []
                else:
                    empty_count = 0
                    cur_chunk.append(p)
            if cur_chunk:
                chunks.append(cur_chunk)

            if not chunks:
                continue

            for chunk in chunks:
                if not chunk:
                    continue
                # If first token of chunk is a street header (e.g. PROVIDENCE PLACE or ALBANY TERRACE)
                chunk_str = " ".join(chunk).strip()
                if is_valid_street_name(chunk_str):
                    current_street = clean_street_name(chunk_str)
                    continue
                if CROSS_STREET_PAT.search(chunk_str) or chunk_str.lower() in ('(return)', 'return'):
                    continue

                h_num, bldg, surname, forename, trade = parse_resident_chunk(chunk)
                
                # Carry over ditto values
                if (surname == '"' or surname.lower() in ('do', 'ditto')) and prev_surname:
                    surname = prev_surname
                if (trade == '"' or trade.lower() in ('do', 'ditto')) and prev_trade:
                    trade = prev_trade

                if surname or forename or trade or bldg or h_num:
                    records.append({
                        "year": "1910",
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

    with open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["year", "street", "house_number", "building_name", "surname", "forename", "trade"])
        writer.writeheader()
        writer.writerows(records)
    print(f"Parsed {len(records)} records from {input_path} into {output_path}.")

if __name__ == "__main__":
    parse_tsv("raw_tsvs/1910.tsv", "volume_csvs/1910_cleaned.csv")
