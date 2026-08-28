import csv
import re
import os

# Import the clean_street_name from clean_csv if possible, otherwise define helper
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
    return name.strip(' ,"-~')

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

def is_valid_street_name(s):
    s = s.strip()
    if not s:
        return False
        
    is_continued_marker = "continued" in s.lower()
    
    # Clean common suffixes and trailing punctuation from street name candidates
    s_clean = s
    s_clean = re.sub(r'[\s\-—]+continued\b', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,')
    
    # Ignore non-street block headers (chambers, villas, buildings)
    words = s_clean.lower().split()
    if words:
        last_word = words[-1].strip('.,()-')
        ignored_suffixes = {'buildings', 'chambers', 'wharf', 'villas', 'cottages'}
        if last_word in ignored_suffixes or any(w in ignored_suffixes for w in words):
            return False
    
    if not s_clean:
        return False
        
    # Ignore short stray page headers (like ARC, ALB, STO)
    if len(s_clean) <= 4:
        return False
        
    # Ignore grid reference patterns (e.g. "D 5", "E 12")
    if re.match(r'^[A-Z]\s*\d+$', s_clean):
        return False
        
    # Ignore generic page directory titles and institution/church headers
    ignored_headers = {
        "NEWPORT STREET DIRECTORY", "NEWPORT", "STREET DIRECTORY", 
        "DIRECTORY", "ALEXANDRA SCHOOLS", "SPRING GARDENS SCHOOL",
        "WESLEYAN METH CHURCH", "WESLEYAN METHODIST CHAPEL", "WESLEYAN METHODIST MISSION HALL",
        "THE BARRACKS", "THE BARRACKS—", "UNITED METHODIST CHURCH", "PRESBYTERIAN CHURCH",
        "TEMPERANCE COTTAGES", "NEW TERRITORIAL DRILL", "MARSHES HALL", "NORTH STREET MEETING",
        "PENYLAN MISSION ROOM", "PILLGWENLLY WESLEYAN", "PUBLIC PARK", "FOR GOOD SHIRT AND COLLAR DRESSING",
        "KINDLY SERVICE THE KEYNOTE OF THIS ESTABLISHMENT", "WOODLAND STREET DIRECTORY",
        "CALL OFFICE", "TELEPHONE CALL OFFICE"
    }
    norm_clean = re.sub(r'[^A-Z0-9\s]', '', s_clean).strip()
    if norm_clean in {re.sub(r'[^A-Z0-9\s]', '', h) for h in ignored_headers}:
        return False
        
    if s_clean.startswith('(') or s_clean.startswith('[') or s_clean.startswith('*') or s_clean.endswith(')'):
        return False
    if s_clean.lower() in {'(return)', 'return', 'continued'}:
        return False
    if s_clean.upper().startswith("OFF ") or s_clean.upper().startswith("FROM ") or s_clean.upper().startswith("TO ") or s_clean.upper().startswith("HERE IS ") or s_clean.upper().startswith("HERE ARE "):
        return False
    if s_clean.upper() in {"LEFT HAND SIDE", "RIGHT HAND SIDE", "EAST SIDE", "WEST SIDE"}:
        return False

    valid_suffixes = {
        "STREET", "ROAD", "LANE", "AVENUE", "PLACE", "SQUARE", "TERRACE",
        "PARADE", "HILL", "ROW", "WAY", "CRESCENT", "DRIVE", "GARDENS",
        "COURT", "GROVE", "WALK", "CLOSE", "RISE", "MEWS", "BANK",
        "QUAY", "WHARF", "PIER", "DOCK", "DOCKS", "PARK", "SLIP", "STEPS",
        "PROMENADE", "VILLAS", "COTTAGES", "BUILDINGS", "CHAMBERS", "ARCADE", "CIRCUS"
    }
    
    words_upper = s_clean.upper().split()
    last_word_upper = words_upper[-1].strip(".,;:()")
    
    if last_word_upper in valid_suffixes or any(w.strip(".,;:()") in valid_suffixes for w in words_upper):
        return True

    return False

def process_3col_chunk(chunk, current_street):
    col0 = chunk[0].strip()
    col1 = chunk[1].strip()
    col2 = chunk[2].strip()
    
    comb = f"{col0} {col1} {col2}".strip()
    if not comb:
        return None
        
    # Skip cross-street, return, or divider lines
    comb_low = comb.lower()
    if (CROSS_STREET_PAT.search(comb) or 
        comb_low.startswith("from ") or 
        comb_low.startswith("to ") or 
        comb_low.startswith("opposite ") or 
        comb_low.startswith("here is ") or 
        comb_low.startswith("here are ") or
        re.match(r'^[\s\*\-\_\=\#\+]+$', comb)):
        return None
        
    h_num = ""
    surname = ""
    forename = ""
    trade = ""
    bldg = ""
    
    # Is col0 a house number? (e.g. "1", "1A", "32-3", "40A")
    if re.match(r"^\d+[A-Za-z]?$", col0) or re.match(r"^\d+-\d+$", col0):
        h_num = col0
        surname = col1
        rest = col2
    else:
        surname = col0
        rest = f"{col1} {col2}".strip()
        
    if not surname and not rest:
        return None
        
    # Extract forename, building_name, and trade from rest
    if rest:
        # Check if rest contains hotel/inn/tavern/arms/club at the end
        words = rest.split()
        bldg_idx = -1
        for idx in range(len(words)-1, -1, -1):
            w_low = words[idx].lower().strip(".,()")
            if w_low in {"bridgehotel", "hotel", "inn", "tav", "tav.", "tavern", "arms", "club", "chambers"}:
                bldg_idx = idx
                break
                
        if bldg_idx != -1:
            raw_b = " ".join(words[bldg_idx:])
            if raw_b.lower() == "bridgehotel":
                bldg = "Bridge Hotel"
            else:
                bldg = raw_b.capitalize()
            forename = " ".join(words[:bldg_idx])
        else:
            if "," in rest:
                fn, tr = rest.split(",", 1)
                forename = fn.strip()
                trade = tr.strip()
            else:
                forename = rest
                
    # Standardize trades and forenames
    trade = clean_trade(trade)
    forename = clean_name_abbr(forename)
    
    if surname or forename or trade or bldg:
        return {
            "year": "1882",
            "street": current_street,
            "house_number": h_num,
            "building_name": bldg,
            "surname": surname,
            "forename": forename,
            "trade": trade
        }
    return None

def parse_tsv(input_path, output_path):
    records = []
    current_street = ""
    
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            raw_tokens = [t.strip() for t in line.rstrip('\n').split('\t')]
            if not any(raw_tokens):
                continue
                
            col0 = raw_tokens[0]
            
            # Identify street header
            is_street = False
            matched_street_name = ""
            page_abbrev_map = {
                "FAI": "FAIROAK TERRACE",
            }
            
            col0_comb = " ".join([t for t in raw_tokens[:3] if t]).strip()
            col0_comb = re.sub(r'\s+', ' ', col0_comb)
            col0_upper = col0.upper().strip()
            
            if col0 and is_valid_street_name(col0):
                is_street = True
                matched_street_name = col0
            elif col0_comb and is_valid_street_name(col0_comb) and (col0_comb.isupper() or 'Street' in col0_comb or 'Road' in col0_comb or 'Terrace' in col0_comb or 'Lane' in col0_comb or 'Place' in col0_comb):
                is_street = True
                matched_street_name = col0_comb
            elif col0_upper in page_abbrev_map:
                is_street = True
                matched_street_name = page_abbrev_map[col0_upper]
                    
            if is_street:
                s_clean = matched_street_name.strip()
                s_clean = re.sub(r'[\s\-—]+continued\b', '', s_clean, flags=re.I).strip()
                s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
                s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
                current_street = clean_street_name(s_clean)
                continue
                
            if not current_street:
                continue
                
            if col0 == "Number" and len(raw_tokens) > 1 and raw_tokens[1] == "Forenames":
                continue
                
            # Parse 3-column TSV layout
            if len(raw_tokens) >= 6:
                for i in range(0, len(raw_tokens), 3):
                    chunk = raw_tokens[i:i+3]
                    while len(chunk) < 3:
                        chunk.append('')
                    rec = process_3col_chunk(chunk, current_street)
                    if rec:
                        records.append(rec)
            else:
                chunk = raw_tokens[:3]
                while len(chunk) < 3:
                    chunk.append('')
                rec = process_3col_chunk(chunk, current_street)
                if rec:
                    records.append(rec)
                
    # Write to output
    with open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["year", "street", "house_number", "building_name", "surname", "forename", "trade"])
        writer.writeheader()
        writer.writerows(records)
        
    print(f"Parsed {len(records)} records from {input_path} into {output_path}.")

if __name__ == "__main__":
    parse_tsv("1882.tsv", "1882_cleaned.csv")
