import csv
import re
import os
import sys

# Import the clean_street_name from clean_csv if possible, otherwise define helper
try:
    sys.path.append(os.getcwd())
    sys.path.append(os.path.join(os.getcwd(), 'scripts'))
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

    # Acronyms mapping
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

    # Standardize casing of standard multi-word names to lowercase
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
    name = re.sub(r'\bJno\.?\b', 'John', name)
    name = re.sub(r'\bAlfd?\.?\b', 'Alfred', name)
    name = re.sub(r'\bRichd?\.?\b', 'Richard', name)
    name = re.sub(r'\bDanl?\.?\b', 'Daniel', name)
    name = re.sub(r'\bSaml?\.?\b', 'Samuel', name)
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
    'BANESWELL', 'BAN', 'ART', 'COM', 'CRI', 'BIS', 'FAI', 'HEN', 'HIG',
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

    # Strip ward markers: , P. / , B.T. / . B. / P. / B.T. / B. / M. / M (except High Street, Pill)
    if not re.search(r'\bHigh\s+Street\b', s_clean, flags=re.I):
        s_clean = re.sub(r'[\s,\.]+(?:P\.|B\.T\.|B\.|P|B\.T|BT|B|M\.|M)\s*$', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,')

    if not s_clean or len(s_clean) <= 3:
        return None

    # Bare suffixes like "Road" or "Street" are not valid
    if s_clean.lower() in {'road', 'street', 'lane', 'avenue', 'place', 'terrace', 'hill', 'drive', 'crescent', 'parade', 'square', 'walk', 'gardens'}:
        return None

    # Reject pointer / cross-street words at start
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
    if re.match(r'^[A-Z]\s*\d+$', s_upper):
        return None

    words = s_upper.split()
    if not words:
        return None

    # Reject if all words are single letters / initials (e.g. "W. E")
    if all(len(w.strip('.,')) <= 1 for w in words):
        return None

    # Must not start with forename abbreviation or digits
    first_w = words[0].strip('.,()-"')
    if first_w in NAME_ABBREVIATIONS or re.match(r'^[A-Za-z]+\d+$', first_w) or ',' in words[0]:
        return None

    # Check if single word is just a surname like "Hill"
    if len(words) == 1 and words[0] in COMMON_SURNAMES_NOT_STREETS:
        return None

    last_word = words[-1].strip('.,()-\"')
    if last_word in STREET_SUFFIXES:
        if last_word in {'HILL', 'COTTAGES', 'VILLAS', 'BUILDINGS', 'CHAMBERS'} and len(words) == 1:
            return None
        if last_word in {'RD', 'RD.'} and len(words) == 2 and words[0] in {'RIDGE', 'BUSH', 'JONES', 'EVANS', 'THOMAS', 'DAVIES'}:
            return None
        # Canonical mappings for inline blocks
        if s_clean.upper().startswith("COMMERCIAL BUILDINGS"):
            return "Commercial Street"
        if s_clean.upper().startswith("DOCK ROAD CHAMBERS"):
            return "Dock Street"
        return clean_street_name(s_clean)

    return None

def split_any_line(parts):
    while parts and not parts[-1]:
        parts.pop()
    if not parts:
        return []

    # Two-part split street header (e.g. ["Friar's", "Road."])
    if len(parts) == 2 and parts[1].lower().rstrip('.') in {'road', 'street', 'terrace', 'lane', 'place', 'avenue'}:
        comb = f"{parts[0]} {parts[1]}"
        if is_valid_street_header(comb):
            return [[comb]]

    # Special handling for Maindee lines starting with empty string
    if parts[0] == '':
        if len(parts) >= 4 and parts[3]:
            return [parts[1:3], parts[3:]]
        else:
            return [parts[1:]]

    # Handle lone number bleed: e.g. ['13', 'Martin', 'G. J.', 'master mar', '34']
    if len(parts) == 5 and parts[4].isdigit() and not parts[3].isdigit():
        return [parts[:4]]
    if len(parts) == 6 and parts[4].isdigit() and not parts[3].isdigit() and not parts[5]:
        return [parts[:4]]

    # Detect multi-column split points
    split_indices = [0]
    for i in range(1, len(parts)):
        p = parts[i]
        if not p or p == '-':
            continue
        p_low = p.lower()
        
        # Check if p is street header or cross-street
        if is_valid_street_header(p):
            split_indices.append(i)
            continue
            
        if (p_low.startswith(('here is', 'here are', 'from ')) or ' to ' in p_low) and len(p.split()) <= 5:
            if not any(b in p_low for b in ['&', 'livery', 'brewery']):
                split_indices.append(i)
                continue
                
        # Check if p is a house number
        if p.isdigit() and len(p) <= 3 and i > split_indices[-1] + 1:
            if not parts[i-1].isdigit():
                split_indices.append(i)
                continue

    split_indices = sorted(list(set(split_indices)))
    chunks = []
    for j in range(len(split_indices)):
        start = split_indices[j]
        end = split_indices[j+1] if j+1 < len(split_indices) else len(parts)
        chunk = [x for x in parts[start:end] if x and x != '-']
        if chunk:
            chunks.append(chunk)
    return chunks

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

    # Detect building names in tokens
    bldg_keywords = {'house', 'villa', 'cottage', 'cot', 'cot.', 'hotel', 'inn', 'tavern', 'arms', 'chambers', 'lodge', 'hall'}
    clean_rem = []
    for tok in rem:
        tok_low = tok.lower().strip('.,()')
        words = tok_low.split()
        if any(kw in words for kw in bldg_keywords) and len(words) <= 4:
            if not bldg:
                bldg = tok.strip(' .,')
            continue
        clean_rem.append(tok)
    rem = clean_rem

    if not rem:
        if bldg:
            return {
                "year": "1886", "street": street, "house_number": h_num,
                "building_name": bldg, "surname": "", "forename": "", "trade": ""
            }
        return None

    # Parse remaining name and trade
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
        surname = rem[0]
        r1 = rem[1]
        if ',' in r1:
            fn, tr = r1.split(',', 1)
            forename = fn.strip()
            trade = tr.strip()
        else:
            forename = r1.strip()
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

    if trade.lower().startswith(('mrs.', 'mrs ', 'miss ', 'mr.', 'mr ')):
        if not forename:
            forename = trade
            trade = ""

    trade = clean_trade(trade)
    forename = clean_name_abbr(forename)
    surname = surname.strip(' ,"-~.')
    forename = forename.strip(' ,"-~.')

    # Strict junk filtering on parsed surname and forename
    sn_low = surname.lower().strip('()[].,-')
    fn_low = forename.lower().strip('()[].,-')
    full_name_low = f"{sn_low} {fn_low}".strip()

    if not sn_low and not fn_low and not trade and not bldg:
        return None
    if (sn_low == 'newport' and fn_low == 'street list') or (sn_low == 'maindee' and fn_low == 'street list'):
        return None
    if sn_low in {'return', 'west side', 'east side', 'left hand side', 'right hand side', 'entrance', 'void'}:
        return None
    if fn_low in {'return', 'west side', 'east side', 'left hand side', 'right hand side'}:
        return None
    if 'entrance' in full_name_low or 'hand side' in full_name_low or 'roadway' in full_name_low:
        return None
    if (sn_low.endswith('-street') or sn_low.endswith('-road') or sn_low.endswith('-lane')) and not h_num and not trade:
        return None
    if surname.startswith(('[', '(')):
        return None

    return {
        "year": "1886",
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

            # Special case for Baldwin Street start at line 325
            if line_num == 325:
                current_streets = ["Baldwin Street", "Baldwin Street", "Baldwin Street"]

            # Single item line check
            non_empty_parts = [p for p in parts if p and p != '-']
            if len(non_empty_parts) == 1:
                st_single = is_valid_street_header(non_empty_parts[0])
                if st_single:
                    current_streets = [st_single, st_single, st_single]
                    continue

            chunks = split_any_line(parts)
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

    # Write output CSV
    with open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["year", "street", "house_number", "building_name", "surname", "forename", "trade"])
        writer.writeheader()
        writer.writerows(records)

    print(f"Parsed {len(records)} records from {input_path} into {output_path}.")

if __name__ == "__main__":
    parse_tsv("raw_tsvs/1886.tsv", "volume_csvs/1886_cleaned.csv")
