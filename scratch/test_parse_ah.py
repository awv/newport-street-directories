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
        'music t\'ch\'r': 'music teacher',
        'dk. police': 'dock police',
        'dock police': 'dock police',
        'carptr. &c.': 'carpenter',
        'carptr': 'carpenter',
        'carpntr': 'carpenter',
        'hairdrsr': 'hairdresser',
        'shipcarptr': 'shipwright',
        'ship\'s pntr': "ship's painter",
        'greengr\'r': 'greengrocer',
        'greeng\'rs': 'greengrocer',
        'general dlr.': 'general dealer',
        'railway insp': 'railway inspector',
        'boots\'lr': 'boot seller',
        'boot dlrs': 'boot dealers',
        'potato merc.': 'potato merchant',
        'boarding ho.': 'boarding house',
        'p.c.': 'P.C.',
        'p.o. clerk': 'P.O. Clerk',
        'h.m.c': 'H.M.C.',
        'glass wks': 'glass works',
        'glass wrks': 'glass works',
        'stonecut\'r': 'stonecutter',
        'ironf\'d\'r': 'ironfounder',
        'boilermkr': 'boilermaker',
        'wagon repairr': 'wagon repairer',
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
        'window cleaner', 'goods guard', 'master mariner', 'greengrocer'
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
    name = re.sub(r'\bDd\.?\b', 'David', name)
    name = re.sub(r'\bOct\.?\b', 'Octavius', name)
    name = re.sub(r'\bFdk\.?\b', 'Frederick', name)
    return name.strip(' ,"-~.')

CROSS_STREET_PAT = re.compile(
    r'\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.)\b.*?\bto\b.*?\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.|square)\b'
    r'|^\s*\[?(?:here\s+are|here\s+is|here\s+cross|\[?return\]?|\(return\.?\)|return\.?)\]?\b'
    r'|^\s*[\(\[]?\s*return\.?\s*[\)\]]?\s*$'
    r'|\bsee\b'
    r'|\bsee\s+also\b'
    r'|^\s*now\s+[a-z0-9\s\.\-|\(\)]+'
    r'|^\s*(?:maindee|newport|pill)from\b'
    r'|^\s*from\s+[A-Za-z\s0-9,\.\-]+'
    r'|^\s*[A-Za-z\s]+street\s+from\b'
    r'|^\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s*(?:side)?\s*[\)\]]?\s*$'
    r'|^\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s+side\b'
    r'|^\s*(?:from\s+)?[a-z0-9\s\.\-]+\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s*[\)\]]?\s*(?:opposite\s+[a-z0-9\s\.\-]+)?\s*$'
    r'|^\s*opposite\s+[a-z0-9\s\.\-]+'
    r'|^\s*last\s+corporation[\s\-]*road\s+street\s+on\s+left[\s\-]+hand\s+side'
    r'|^\s*(?:west|east|north|south)\s+side\s+of\b'
    r'|\bcontinuation\b'
    r'|\btowards\b',
    re.I
)

IGNORED_DIRECTORY_HEADERS = {
    'NEWPORT STREET LIST', 'MAINDEE STREET LIST', 'NEWPORT STREET DIRECTORY', 
    'MAINDEE STREET DIRECTORY', 'MAINDEE', 'NEWPORT', 'STREET DIRECTORY', 'DIRECTORY',
    'MAINDEE STREETS', 'WOODLAND STREET DIRECTORY', 'ALEXANDRA SCHOOLS',
    'SPRING GARDENS SCHOOL', 'THE BARRACKS', 'TEMPERANCE COTTAGES',
    'BANESWELL', 'BAN', 'ART', 'COM', 'CRI', 'BIS', 'FAI', 'HEN', 'HIG', 'ALE', 'ALI', 'ARC', 'ALT',
    'FOR GOOD SHIRT AND COLLAR DRESSING', 'KINDLY SERVICE THE KEYNOTE OF THIS ESTABLISHMENT'
}

STREET_SUFFIXES = {
    'STREET', 'ST', 'ST.', 'ROAD', 'RD', 'RD.', 'LANE', 'PLACE', 'PL', 'PL.', 
    'TERRACE', 'TER', 'TER.', 'AVENUE', 'AVE', 'AVE.', 'CRESCENT', 'CRES', 'CRES.', 
    'PARADE', 'PAR', 'PAR.', 'SQUARE', 'SQ', 'SQ.', 'HILL', 'WALK', 'GARDENS', 
    'DOCK', 'DOCKS', 'WHARF', 'PASSAGE', 'ROW', 'RISE', 'GROVE', 'COURT', 'BANK', 
    'VIEW', 'GREEN', 'ALLEY', 'COTTAGES', 'VILLAS', 'BUILDINGS', 'CHAMBERS', 'ARCADE', 
    'CIRCUS', 'PARK', 'TOPS', 'CRINDAU'
}

COMMON_SURNAMES_NOT_STREETS = {'HILL', 'GREEN', 'LANE', 'GARDENS', 'PARK', 'VIEW', 'GROVE', 'BANK', 'CROSS', 'WEST', 'STREET'}
NAME_ABBREVIATIONS = {'WM', 'WM.', 'JNO', 'JNO.', 'GEO', 'GEO.', 'THOS', 'THOS.', 'HY', 'HY.', 'CHAS', 'CHAS.', 'EDW', 'EDW.', 'RICHD', 'RICHD.', 'ALFD', 'ALFD.', 'BENJ', 'BENJ.', 'JAS', 'JAS.', 'FREDK', 'FREDK.', 'SAML', 'SAML.', 'DL', 'DL.', 'DANL', 'DANL.'}

def is_valid_street_header(s):
    if not s:
        return None
    s = s.strip()
    s_clean = re.sub(r'[\s\-—]+continued\b', '', s, flags=re.I).strip()
    s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean).strip()
    
    # Expand "Up." / "Upp." prefix to "Upper "
    s_clean = re.sub(r'^(?:Up|Upp)[\.\s]+', 'Upper ', s_clean, flags=re.I).strip()

    # Strip ward markers: C. / P. / B.T. / M. / W. / T. (except High Street, Pill)
    if not re.search(r'\bHigh\s+Street\b', s_clean, flags=re.I):
        s_clean = re.sub(r'[\s,\.]+(?:P\.|B\.T\.|B\.|P|B\.T|BT|B|M\.|M|C\.|C|W\.|W|T\.|T)\s*$', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,')

    if not s_clean or len(s_clean) <= 3:
        return None

    # Bare suffixes like "Road" or "Street" are not valid
    if s_clean.lower() in {'road', 'street', 'lane', 'avenue', 'place', 'terrace', 'hill', 'drive', 'crescent', 'parade', 'square', 'walk', 'gardens'}:
        return None

    s_low = s_clean.lower()
    if s_low.startswith(('here is', 'here are', 'from ', 'to ', 'opposite ', 'see ', 'now ')):
        return None

    # Must not contain commercial/entity indicators
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
        'OFFICE', 'TELEPHONE', 'SUPER TUNE', 'ST. WOOLOS SCHOOLS', 'ASSEMBLY ROOMS'
    ]):
        return None
    if re.match(r'^[A-Z]\s*\d+$', s_upper) or re.match(r'^\d+', s_upper):
        return None

    words = s_upper.split()
    if not words:
        return None

    # Reject if all words are single letters / initials
    if all(len(w.strip('.,')) <= 1 for w in words):
        return None

    # Must not start with forename abbreviation or digits
    first_w = words[0].strip('.,()-"')
    if first_w in NAME_ABBREVIATIONS or re.match(r'^[A-Za-z]+\d+$', first_w) or ',' in words[0]:
        return None

    # Check if single word is just a surname like "Hill"
    if len(words) == 1 and words[0] in COMMON_SURNAMES_NOT_STREETS:
        return None

    last_word = words[-1].strip('.,()-"')
    if last_word in STREET_SUFFIXES:
        if last_word in {'HILL', 'COTTAGES', 'VILLAS', 'BUILDINGS', 'CHAMBERS'} and len(words) == 1:
            return None
        if last_word in {'RD', 'RD.'} and len(words) == 2 and words[0] in {'POPHAM', 'RIDGE', 'BUSH', 'JONES', 'EVANS', 'THOMAS', 'DAVIES'}:
            return None
        # Canonical mappings
        if s_clean.upper().startswith("COMMERCIAL BUILDINGS"):
            return "Commercial Street"
        if s_clean.upper().startswith("DOCK ROAD CHAMBERS"):
            return "Dock Street"
        return clean_street_name(s_clean)

    return None

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
        
        # Detect multi-column split points when p starts with house number
        if current_chunk:
            p_first = p.split()[0].strip('.,()')
            if p_first.isdigit() and len(p_first) <= 3:
                chunks.append(current_chunk)
                current_chunk = [p]
                continue
            # Also check if p is a valid street header
            if is_valid_street_header(p):
                chunks.append(current_chunk)
                current_chunk = [p]
                continue
        
        current_chunk.append(p)
    
    if current_chunk:
        chunks.append(current_chunk)

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

    # Check if tokens[0] is house number
    if re.match(r'^\d+[A-Za-z]?$', tokens[0]) or re.match(r'^\d+-\d+$', tokens[0]):
        h_num = tokens[0]
        rem = tokens[1:]
    else:
        m_num = re.match(r'^(\d+[A-Za-z]?)\s+(.*)$', tokens[0])
        if m_num:
            h_num = m_num.group(1)
            rem = [m_num.group(2)] + tokens[1:]
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
            # e.g. ['Rothwell Ab.', 'contractor'] or ['Lovelock Henry', 'weigher']
            surname = r0_parts[0]
            forename = " ".join(r0_parts[1:])
            trade = r1
        else:
            surname = r0
            if ',' in r1:
                fn, tr = r1.split(',', 1)
                forename = fn.strip()
                trade = tr.strip()
            else:
                forename = r1
    elif len(rem) >= 3:
        surname = rem[0]
        forename = rem[1]
        trade = " ".join(rem[2:]).strip()

    if ',' in forename and not trade:
        fn, tr = forename.split(',', 1)
        forename = fn.strip()
        trade = tr.strip()
    if ',' in surname and not trade:
        sn, tr = surname.split(',', 1)
        surname = sn.strip()
        trade = tr.strip()

    if trade.lower().startswith(('mrs.', 'mrs ', 'miss ', 'mr.', 'mr ', 'rev.', 'rev ')):
        if not forename:
            forename = trade
            trade = ""

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
            else:
                for k, c in enumerate(chunks[:3]):
                    st = is_valid_street_header(c[0]) if len(c) > 0 else None
                    if st:
                        current_streets[k] = st
                    else:
                        target_st = current_streets[k] or current_streets[0]
                        if target_st:
                            rec = parse_record_chunk(c, target_st)
                            if rec:
                                records.append(rec)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["year", "street", "house_number", "building_name", "surname", "forename", "trade"])
        writer.writeheader()
        writer.writerows(records)
        
    print(f"Parsed {len(records)} records from {input_path} into {output_path}")

if __name__ == "__main__":
    tsv_in = "raw_tsvs/1903.tsv"
    csv_out = "volume_csvs/1903_cleaned.csv"
    parse_tsv(tsv_in, csv_out)
