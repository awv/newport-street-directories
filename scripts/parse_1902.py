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
    s_clean = s
    s_clean = re.sub(r'[\s\-—]+continued\b', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,')
    
    if not s_clean:
        return False
        
    # Ignore non-street block headers (chambers, villas, buildings)
    words = s_clean.lower().split()
    if words:
        last_word = words[-1].strip('.,()-')
        ignored_suffixes = {'buildings', 'chambers', 'court', 'wharf', 'villas', 'cottages'}
        if last_word in ignored_suffixes or any(w in ignored_suffixes for w in words):
            return False
        
    suffixes = {
        'street', 'road', 'lane', 'place', 'terrace', 'crescent', 'square', 'avenue',
        'hill', 'parade', 'gardens', 'drive', 'walk', 'close', 'view', 'grove', 'way',
        'passage', 'row', 'rise', 'market', 'precincts', 'arcade', 'ch.'
    }
    words = s_clean.lower().split()
    if not words:
        return False
    last_word = words[-1].strip('.,()-')
    
    is_st = last_word in suffixes or any(w in suffixes for w in words)
    known_non_suffix = {
        'baneswell', 'friars', 'stow', 'courtybella', 'barnard town', 'town hall',
        'union', 'westgate', 'cambria', 'melbourne', 'ringland', 'cross-street', 'return'
    }
    if s_clean.lower() in known_non_suffix:
        is_st = True
        
    if not is_st:
        return False
        
    if len(s_clean) <= 4:
        return False
        
    if re.match(r'^[A-Z]\s*\d+$', s_clean):
        return False
        
    ignored_keywords = [
        r'\b(?:CO\.?\s+LTD|CO\b\s*LTD\b|LTD\b|LTD\.)',
        r'\bLIMITED\b',
        r'\bGARAGE\b',
        r'\bFILLING\s+STATION\b',
        r'\bSERVICE\s+STATION\b',
        r'\bTRADING\s+ESTATE\b',
        r'\bINDUSTRIAL\s+ESTATE\b',
        r'\bPUBLIC\s+HOUSE\b',
        r'\bMOTOR\s+CO\b',
        r'\bINSTALLATIONS\b',
        r'\bCOY\b',
        r'\bDISMANTLERS\b',
        r'\bNEWPORT\s+\d+\*?\b',
        r'\bPORT\s+\d+',
        r'\bT\s*N\s*\d+',
        r'\bTEL\b',
        r'\bPHONE\b',
        r'\bTELEPHONE\b',
        r'\bSUPER\s+TUNE\b',
        r'\bDOVEY\s+MOTOR\b',
        r'&'
    ]
    ignored_pat = re.compile('|'.join(ignored_keywords), re.I)
    if ignored_pat.search(s_clean):
        return False
        
    ignored_headers = {
        "NEWPORT STREET DIRECTORY", "NEWPORT", "STREET DIRECTORY", 
        "DIRECTORY", "ALEXANDRA SCHOOLS", "SPRING GARDENS SCHOOL",
        "WESLEYAN METH CHURCH", "WESLEYAN METHODIST CHAPEL", "WESLEYAN METHODIST MISSION HALL",
        "THE BARRACKS", "THE BARRACKS—", "UNITED METHODIST CHURCH", "PRESBYTERIAN CHURCH",
        "TEMPERANCE COTTAGES", "NEW TERRITORIAL DRILL", "MARSHES HALL", "NORTH STREET MEETING",
        "PENYLAN MISSION ROOM", "PILLGWENLLY WESLEYAN", "PUBLIC PARK", "FOR GOOD SHIRT AND COLLAR DRESSING",
        "KINDLY SERVICE THE KEYNOTE OF THIS ESTABLISHMENT", "WOODLAND STREET DIRECTORY"
    }
    norm_clean = re.sub(r'[^A-Z0-9\s]', '', s_clean).strip()
    if norm_clean in {re.sub(r'[^A-Z0-9\s]', '', h) for h in ignored_headers}:
        return False
        
    if s_clean.startswith('(') or s_clean.startswith('[') or s_clean.startswith('*') or s_clean.endswith(')'):
        return False
    if s_clean.lower() in {'(return)', 'return', 'continued'}:
        return False
    if s_clean.startswith("OFF ") or s_clean.startswith("FROM ") or s_clean.startswith("TO "):
        return False
    if s_clean in {"LEFT HAND SIDE", "RIGHT HAND SIDE", "EAST SIDE", "WEST SIDE"}:
        return False
    return True

def parse_tsv(input_path, output_path):
    records = []
    current_street = ""
    prev_surname = ""
    prev_trade = ""
    
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            parts = [p.strip() for p in line.split('\t')]
            raw_parts_for_extra = parts[5:]
            while len(parts) < 6:
                parts.append('')
            parts = parts[:6]
            
            if not any(p for p in parts):
                continue
                
            col0 = parts[0]
            
            is_street = False
            if col0 and is_valid_street_name(col0):
                is_street = True
                    
            if is_street:
                s_clean = col0.strip()
                s_clean = re.sub(r'[\s\-—]+continued\b', '', s_clean, flags=re.I).strip()
                s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
                s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
                current_street = clean_street_name(s_clean)
                continue
                
            combined_row = " ".join([p for p in parts if p]).strip()
            
            if re.match(r'^[\s\*\-\_\=\#\+]+$', combined_row):
                continue
                
            combined_row_stripped = combined_row.strip(' *-_~()[]')
            if CROSS_STREET_PAT.search(combined_row) or CROSS_STREET_PAT.search(combined_row_stripped):
                continue
                
            if not current_street:
                continue
                
            if col0 == "Number" and parts[1] == "Forenames":
                continue
                
            h_num = parts[0]
            surname = parts[1]
            forename = parts[2]
            trade = parts[3]
            bldg = parts[4]
            notes = parts[5]
            
            if not parts[1] and not parts[2] and not parts[3] and not parts[4] and not parts[5]:
                surname = parts[0]
                h_num = ""

            # Overrides for the torn page in Alfred Street
            if current_street == "Alfred Street" and h_num in {"2", "3", "4"}:
                if h_num == "2":
                    surname, forename, trade, bldg = "Wilmott", "William", "labourer", ""
                elif h_num == "3":
                    surname, forename, trade, bldg = "Greenhaff", "Mrs Clara", "", ""
                elif h_num == "4":
                    surname, forename, trade, bldg = "Hawkins", "Milsom", "labourer", ""

            # Resolve ditto
            if surname and surname.strip(' ,.-').lower() in {'do', 'ditto'}:
                surname = prev_surname
            if trade and trade.strip(' ,.-').lower() in {'do', 'ditto'}:
                trade = prev_trade
            
            for val in [trade, bldg]:
                if val:
                    val_low = val.strip().lower()
                    if val_low.startswith("mrs") or val_low.startswith("miss") or val_low.startswith("mr") or val_low.startswith("dr") or val_low.startswith("rev"):
                        if not forename:
                            forename = val
                            if val == trade:
                                trade = ""
                            else:
                                bldg = ""
                            break

            if not h_num and not forename and not surname and not trade and not bldg and notes:
                if CROSS_STREET_PAT.search(notes):
                    continue
                if notes.isupper() and len(notes) > 4:
                    bldg = notes
                    notes = ""
            
            if not h_num and not forename and not surname:
                comb_val = f"{trade} {bldg} {notes}".lower()
                landmark_keywords = {
                    'church', 'ch.', 'chapel', 'grounds', 'gas works', 'gasworks', 
                    'see also', 'school', 'schools', 'hall', 'chambers', 'depot', 'works'
                }
                if any(kw in comb_val for kw in landmark_keywords):
                    continue
            
            trade = clean_trade(trade)
            forename = clean_name_abbr(forename)
            
            if forename or surname or trade or bldg:
                records.append({
                    "year": "1902",
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
                
                extra_str = " / ".join([p for p in raw_parts_for_extra if p]).strip()
                if extra_str:
                    extra_parts = [ep.strip() for ep in extra_str.split('/')]
                    for ep in extra_parts:
                        if not ep:
                            continue
                        ep_low = ep.lower()
                        
                        is_bldg = False
                        bldg_keywords = {'house', 'villa', 'cottage', 'cot', 'hotel', 'chambers', 'hall', 'buildings', 'school', 'church', 'chapel'}
                        if any(kw in ep_low for kw in bldg_keywords) and len(ep.split()) <= 3:
                            if not records[-1]['building_name']:
                                records[-1]['building_name'] = ep
                            continue
                            
                        trade_keywords = {
                            'labourer', 'labr', 'carpenter', 'carpntr', 'steward', 'salesman', 'clerk', 
                            'mason', 'fitter', 'builder', 'haulier', 'fireman', 'guard', 'shoemaker',
                            'draper', 'baker', 'rigger', 'tailor', 'painter', 'smith', 'engineer',
                            'mechanic', 'machinist', 'bricklayer', 'conductor', 'plumber', 'driver',
                            'steelworker', 'platelayer', 'coal', 'trimmer', 'pilot', 'porter',
                            'agent', 'merchant', 'dentist', 'hairdresser', 'chiropodist', 'dressmaker'
                        }
                        if ep_low in trade_keywords or clean_trade(ep) != ep:
                            if records:
                                records[-1]['trade'] = clean_trade(ep)
                            continue
                            
                        tokens = ep.split()
                        if not tokens:
                            continue
                            
                        s_name = tokens[0]
                        f_name = ""
                        t_name = ""
                        
                        if len(tokens) == 2:
                            f_name = tokens[1]
                        elif len(tokens) >= 3:
                            last_low = tokens[-1].lower()
                            if last_low in trade_keywords:
                                if len(tokens) >= 4 and tokens[-2].lower() in {'ship', 'coal', 'crane', 'dock', 'goods', 'engine', 'motor', 'police', 'stone', 'shoe', 'wood'}:
                                    t_name = " ".join(tokens[-2:])
                                    f_name = " ".join(tokens[1:-2])
                                else:
                                    t_name = tokens[-1]
                                    f_name = " ".join(tokens[1:-1])
                            else:
                                f_name = " ".join(tokens[1:])
                                
                        s_name = s_name.strip(' ,"-~.')
                        f_name = f_name.strip(' ,"-~.')
                        t_name = clean_trade(t_name)
                        f_name = clean_name_abbr(f_name)
                        
                        if f_name and ',' in f_name:
                            f_name_part, trade_part = f_name.split(',', 1)
                            f_name = f_name_part.strip()
                            if not t_name:
                                t_name = clean_trade(trade_part)
                                
                        if s_name and ',' in s_name:
                            s_name_part, trade_part = s_name.split(',', 1)
                            s_name = s_name_part.strip()
                            if not t_name:
                                t_name = clean_trade(trade_part)
                                
                        if s_name or f_name or t_name:
                            records.append({
                                "year": "1902",
                                "street": current_street,
                                "house_number": h_num,
                                "building_name": bldg,
                                "surname": s_name,
                                "forename": f_name,
                                "trade": t_name
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
    parse_tsv("raw_tsvs/1902.tsv", "volume_csvs/1902_cleaned.csv")
