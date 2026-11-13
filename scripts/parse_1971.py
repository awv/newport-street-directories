import csv
import re
import os
import sys

# Ensure scripts directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from clean_csv import clean_street_name, TRADE_TYPO_MAP, TRADE_EXACT_MAP, TRADE_ABBREV_MAP
except ImportError:
    clean_street_name = lambda x: x.strip()
    TRADE_TYPO_MAP = {}
    TRADE_EXACT_MAP = {}
    TRADE_ABBREV_MAP = {}

STREET_SUFFIXES = {
    'ROAD', 'STREET', 'AVENUE', 'CRESCENT', 'DRIVE', 'CLOSE', 'WAY', 
    'TERRACE', 'PLACE', 'LANE', 'GROVE', 'GARDENS', 'RISE', 'VILLAS', 
    'PARK', 'HILL', 'COURT', 'MEWS', 'WALK', 'PARADE', 'SQUARE', 'VIEW', 
    'GLADE', 'PASSAGE', 'PATH', 'ALLEY', 'ROW', 'PROMENADE', 'APPROACH',
    'GREEN', 'TOPS', 'WHARF', 'QUAY', 'VALE', 'CIRCUS', 'COPSE',
    'AV.', 'RD.', 'ST.', 'CRES.', 'TER.', 'PL.', 'CL.', 'AV', 'RD', 'ST', 'CRES', 'TER', 'PL', 'CL'
}

SPECIAL_STREETS = {
    'GOLD TOPS', 'BARBIROLLI GREEN', 'THE DOCKS', 'THE FRIARS', 'THE GROVE', 'THE HIGHWAY', 'THE MOORINGS'
}

IGNORED_HEADERS = {
    'NEWPORT STREET DIRECTORY', 'NEWPORT', 'STREET DIRECTORY', 'DIRECTORY',
    'ALEXANDRA SCHOOLS', 'SPRING GARDENS SCHOOL', 'WESLEYAN METH CHURCH',
    'WESLEYAN METHODIST CHAPEL', 'WESLEYAN METHODIST MISSION HALL',
    'THE BARRACKS', 'THE BARRACKS—', 'UNITED METHODIST CHURCH', 'PRESBYTERIAN CHURCH',
    'TEMPERANCE COTTAGES', 'NEW TERRITORIAL DRILL', 'MARSHES HALL',
    'NORTH STREET MEETING', 'PENYLAN MISSION ROOM', 'PILLGWENLLY WESLEYAN',
    'PUBLIC PARK', 'WOODLAND STREET DIRECTORY', 'CRINDAU PRIMARY SCHOOL',
    'FOR GOOD SHIRT AND COLLAR DRESSING', 'KINDLY SERVICE THE KEYNOTE OF THIS ESTABLISHMENT'
}

CROSS_STREET_PAT = re.compile(
    r'\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|parade|pde|close|av|sq)\b.*?\bto\b.*?\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|parade|pde|close|av|square)\b'
    r'|^\s*\[?(?:here\s+are|here\s+is|here\s+cross|\[?return\]?|\(return\.?\)|return\.?)\]?\b'
    r'|^\s*[\(\[]?\s*return\.?\s*[\)\]]?\s*$'
    r'|\bsee\b'
    r'|\bsee\s+also\b'
    r'|^\s*(?:left|right|east|west|north|south)\s+side\b'
    r'|^\s*\(?no\s+thoroughfare\.?\)?\s*$'
    r'|^\s*map\s+[a-z]\s*\d+\.?\s*$'
    r'|^\s*map\s+[a-z]\d+\.?\s*$'
    r'|^\s*from\s+.*'
    r'|^\s*to\s+.*'
    r'|^\s*\(formerly\s+.*?\)'
    r'|^\s*\(junior\s+mixed\s+&\s+infants\)'
    r'|^\s*fants\)'
    r'|^\s*primary\s+school\b',
    re.I
)

NAME_ABBR_MAP = {
    'Jas': 'James', 'Jn': 'John', 'Wm': 'William', 'Thos': 'Thomas',
    'Geo': 'George', 'Chas': 'Charles', 'Hy': 'Henry', 'Saml': 'Samuel',
    'Edwd': 'Edward', 'Robt': 'Robert', 'Rt': 'Robert', 'Jsph': 'Joseph',
    'Alfd': 'Alfred', 'Fredk': 'Frederick', 'Richd': 'Richard', 'Rd': 'Richard',
    'Danl': 'Daniel', 'Steph': 'Stephen', 'Walt': 'Walter', 'Wltr': 'Walter',
    'Benj': 'Benjamin', 'Arth': 'Arthur', 'Albt': 'Albert', 'Herbt': 'Herbert',
    'Alex': 'Alexander', 'Arch': 'Archibald', 'Reg': 'Reginald', 'Regnld': 'Reginald',
    'Kath': 'Kathleen', 'Margt': 'Margaret', 'Eliz': 'Elizabeth', 'Michl': 'Michael',
    'Christphr': 'Christopher', 'Dvd': 'David', 'Glyn': 'Glyndwr', 'Kenneth': 'Kenneth'
}

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

def clean_name_abbr(name):
    if not name:
        return ""
    words = name.split()
    expanded = []
    for w in words:
        w_strip = w.rstrip('.')
        if w_strip in NAME_ABBR_MAP:
            expanded.append(NAME_ABBR_MAP[w_strip])
        else:
            expanded.append(w)
    return " ".join(expanded)

def clean_ocr_line(text):
    if not text:
        return ""
    t = re.sub(r'^[\\\\/\s\|\.\-_]+', '', text)
    t = re.sub(r'[\\\\/\s\|\.\-_]+$', '', t)
    return t.strip()

def detect_street_header(text):
    t = clean_ocr_line(text)
    if not t or len(t) <= 3:
        return None
    # Strip running headers from OCR
    t = re.sub(r'^(?:THE\s+)?(?:NEWPORT\s+)?STREET\s+DIRECTORY[\.\s\t]*(?:\d{1,4}\s+)?', '', t, flags=re.I).strip()
    t = re.sub(r'^NEWPORT\s+(?:\d{1,4}\s+)?', '', t, flags=re.I).strip()
    t = re.sub(r'^VICTORIA\s+CHMBRS\.\s*', '', t, flags=re.I).strip()
    # Strip leading page numbers from street header (e.g. 262 BLACKWATER CLOSE or 141 QUANTOCK DRIVE)
    t = re.sub(r'^\d{1,4}\s+([A-Z])', r'\1', t)
    t_clean = re.sub(r'[\(\[].*?[\)\]]', '', t).strip()
    norm = re.sub(r'[^A-Z0-9\s]', '', t_clean.upper()).strip()
    if norm in {re.sub(r'[^A-Z0-9\s]', '', h) for h in IGNORED_HEADERS}:
        return None
    if norm in SPECIAL_STREETS:
        return clean_street_name(norm)
    if re.search(r'\b(?:CO\.?\s*LTD|LIMITED|GARAGE|FILLING\s*STATION|SERVICE\s*STATION|TRADING\s*ESTATE|PUBLIC\s*HOUSE|MOTOR|NEWPORT\s+\d+|TEL|PHONE|TELEPHONE)\b', t_clean, re.I):
        return None
    if re.search(r'\b(?:from|to|off|here\s+is|here\s+are|near|opp|corner|see|see\s+also)\b', t_clean, re.I):
        return None
    if not t_clean.isupper() and len([c for c in t_clean if c.isupper()]) < len(t_clean) * 0.65:
        return None
    words = t_clean.split()
    if len(words) < 2:
        return None
    if len(words[0]) == 1 and words[0].upper() not in {"ST.", "ST"}:
        return None
    if words[-1].upper().rstrip('.,-') in STREET_SUFFIXES:
        canonical = t_clean.rstrip(" ,.-")
        canonical = re.sub(r'\bAV\b\.?', 'Avenue', canonical, flags=re.I)
        canonical = re.sub(r'\bRD\b\.?', 'Road', canonical, flags=re.I)
        canonical = re.sub(r'\bST\b\.?$', 'Street', canonical, flags=re.I)
        canonical = re.sub(r'^\bST\b\.?\s+', 'St. ', canonical, flags=re.I)
        canonical = re.sub(r'\bCRES\b\.?', 'Crescent', canonical, flags=re.I)
        canonical = re.sub(r'\bCL\b\.?', 'Close', canonical, flags=re.I)
        canonical = re.sub(r'\bTER\b\.?', 'Terrace', canonical, flags=re.I)
        canonical = re.sub(r'\bPL\b\.?', 'Place', canonical, flags=re.I)
        
        words = canonical.split()
        titled = []
        for w in words:
            if w.upper() in {"ST.", "ST"}:
                titled.append("St.")
            elif "'" in w:
                parts = w.split("'")
                titled.append("'".join(p.capitalize() if p.lower() != 's' else 's' for p in parts))
            elif "-" in w:
                titled.append("-".join(p.capitalize() for p in w.split("-")))
            else:
                titled.append(w.capitalize())
        return clean_street_name(" ".join(titled))
    return None

def is_parallel_cell(text):
    t = clean_ocr_line(text)
    if not t:
        return False
    if detect_street_header(t):
        return True
    if t.upper().rstrip('.,-') in STREET_SUFFIXES and t.isupper():
        return True
    if any(k in t.lower() for k in ['left side', 'right side', 'here cross over', 'from ', 'to ', 'map ', 'no thoroughfare', 'formerly']):
        return True
    words = t.split()
    if words and (re.match(r'^\d+[a-zA-Z]?$', words[0]) and len(words) >= 2 and words[1][0].isupper()):
        return True
    return False

def is_line_parallel(parts):
    if len(parts) <= 1:
        return False
    for idx, p in enumerate(parts[1:], start=1):
        if is_parallel_cell(p):
            return True
        if idx + 1 < len(parts) and re.match(r'^\d+[a-zA-Z]?$', p.strip()) and parts[idx+1].strip() and parts[idx+1].strip()[0].isupper():
            return True
    return False

def merge_adjacent_header_tokens(parts):
    merged = list(parts)
    for i in range(len(merged) - 1):
        p1 = clean_ocr_line(merged[i])
        p2 = clean_ocr_line(merged[i+1])
        if p1 and p2:
            if p2.upper().rstrip('.,-') in STREET_SUFFIXES and p1.isupper() and p2.isupper():
                merged[i] = f'{merged[i]} {merged[i+1]}'
                merged[i+1] = ''
            elif p1.upper().startswith('CONSTA') and p2.upper().startswith('BLE'):
                merged[i] = f'CONSTABLE {p2[3:].strip()}'
                merged[i+1] = ''
            elif p1.upper().startswith('DEPO') and p2.upper().startswith('T'):
                merged[i] = f'DEPOT {p2[1:].strip()}'
                merged[i+1] = ''
    return merged

def unpack_raw_tsv_lines(raw_lines):
    unpacked = []
    i = 0
    n = len(raw_lines)

    while i < n:
        raw = raw_lines[i]
        
        # Skip dotted separator line (14516)
        if i == 14515:
            i += 1
            continue
            
        # Lines with huge number of tabs (like line 16963 with 276 tabs)
        if raw.count('\t') > 20:
            parts = [p.strip() for p in raw.split('\t') if p.strip()]
            for p in parts:
                unpacked.append(p)
            i += 1
            continue
            
        parts = merge_adjacent_header_tokens(raw.rstrip('\r\n').split('\t'))
        
        # Check if parallel block starts
        if is_line_parallel(parts):
            block = []
            j = i
            gap = 0
            while j < n and gap <= 2:
                p_j = merge_adjacent_header_tokens(raw_lines[j].rstrip('\r\n').split('\t'))
                if is_line_parallel(p_j):
                    block.append(raw_lines[j])
                    gap = 0
                else:
                    gap += 1
                    if gap <= 2:
                        block.append(raw_lines[j])
                j += 1
                
            while block:
                p_last = merge_adjacent_header_tokens(block[-1].rstrip('\r\n').split('\t'))
                if is_line_parallel(p_last):
                    break
                block.pop()
                j -= 1
                
            # Determine if 3-column
            has_col3 = any(len(b.rstrip('\r\n').split('\t')) > 6 and any(p.strip() for p in b.rstrip('\r\n').split('\t')[6:]) for b in block)
            
            # Find default split_k for 2-column block
            split_candidates = []
            for bl in block:
                bp = merge_adjacent_header_tokens(bl.rstrip('\r\n').split('\t'))
                for k in range(1, len(bp)):
                    if not bp[0].strip() and k == 1:
                        continue
                    if is_parallel_cell(bp[k]):
                        split_candidates.append(k)
                        break
            default_k = split_candidates[0] if split_candidates else 3
            
            c1, c2, c3 = [], [], []
            for bl in block:
                if bl.count('\t') > 20:
                    bp_parts = [p.strip() for p in bl.split('\t') if p.strip()]
                    unpacked.extend(bp_parts)
                    continue
                bp = merge_adjacent_header_tokens(bl.rstrip('\r\n').split('\t'))
                if has_col3:
                    p1 = '\t'.join([p.strip() for p in bp[:3] if p.strip()])
                    p2 = '\t'.join([p.strip() for p in bp[3:6] if p.strip()])
                    p3 = '\t'.join([p.strip() for p in bp[6:] if p.strip()])
                    if p1: c1.append(p1)
                    if p2: c2.append(p2)
                    if p3: c3.append(p3)
                else:
                    line_k = None
                    for k in range(1, len(bp)):
                        if not bp[0].strip() and k == 1:
                            continue
                        if is_parallel_cell(bp[k]):
                            line_k = k
                            break
                    k_use = line_k if line_k is not None else default_k
                    p1 = '\t'.join([p.strip() for p in bp[:k_use] if p.strip()])
                    p2 = '\t'.join([p.strip() for p in bp[k_use:] if p.strip()])
                    if p1: c1.append(p1)
                    if p2: c2.append(p2)
                    
            c1_text = ' '.join(c1).lower()
            c2_text = ' '.join(c2).lower()
            
            unpacked.extend(c1)
            if c2_text and c2_text not in c1_text:
                unpacked.extend(c2)
            if has_col3 and c3:
                unpacked.extend(c3)
                
            i = j
        else:
            clean_parts = [p.strip() for p in parts if p.strip()]
            unpacked.append('\t'.join(clean_parts))
            i += 1
            
    # Merge consecutive header lines (e.g. CASTLE PARK + CLOSE., DEWSLAND PARK + ROAD.)
    merged_unpacked = []
    idx_u = 0
    while idx_u < len(unpacked):
        line = unpacked[idx_u]
        if idx_u + 1 < len(unpacked):
            next_line = unpacked[idx_u+1].strip()
            next_words = next_line.split()
            # Case 1: next line is only a street suffix
            if len(next_words) == 1 and next_words[0].upper().rstrip('.,-') in STREET_SUFFIXES:
                curr_clean = clean_ocr_line(line)
                if curr_clean.isupper() and not CROSS_STREET_PAT.search(curr_clean):
                    merged_unpacked.append(f"{line.strip()} {next_line}")
                    idx_u += 2
                    continue
            # Case 2: split hyphenated words (CONSTA- / CONSTA + BLE DRIVE, DEPO- / DEPO + T STREET)
            if line.strip().endswith('-') or line.strip() in {"CONSTA", "DEPO"}:
                curr_strip = line.strip().rstrip('-')
                merged_unpacked.append(f"{curr_strip}{next_line}")
                idx_u += 2
                continue
        merged_unpacked.append(line)
        idx_u += 1
            
    return merged_unpacked
            
    return unpacked

def parse_line_to_resident(line_text):
    parts = [p.strip() for p in line_text.split('\t')]
    while len(parts) < 6:
        parts.append('')
        
    comb = " ".join([p for p in parts if p]).strip()
    if not comb or re.match(r'^[\s\*\-\_\=\#\.\+]+$', comb):
        return None
    if CROSS_STREET_PAT.search(comb):
        return None
        
    # If single token string (like "2 Burgess Derek R" or "3 (flat 1) Parry Gordon T")
    if not parts[1] and not parts[2] and not parts[3]:
        text = parts[0]
        m = re.match(r'^(\d+[a-zA-Z]?(?:\s*\([^\)]+\))?)\s+([A-Za-z\.\'\-]+)\s*(.*)', text)
        if m:
            h_num = m.group(1).strip()
            sur = m.group(2).strip()
            fn = m.group(3).strip()
            return h_num, sur, fn, "", ""
        else:
            return "", text, "", "", ""
            
    h_num = parts[0]
    surname = parts[1]
    forename = parts[2]
    trade = parts[3]
    bldg = parts[4]
    notes = parts[5]
    
    if not h_num and surname and re.match(r'^\d+[a-zA-Z]?$', surname):
        h_num = surname
        surname = forename
        forename = trade
        trade = ""
        
    for val in [trade, bldg]:
        if val:
            val_low = val.strip().lower()
            if val_low.startswith(("mrs", "miss", "mr", "dr", "rev")):
                if not forename:
                    forename = val
                    if val == trade: trade = ""
                    else: bldg = ""
                    break
                    
    trade = clean_trade(trade)
    forename = clean_name_abbr(forename)
    
    return h_num, surname, forename, trade, bldg

def parse_tsv(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()
        
    unpacked_lines = unpack_raw_tsv_lines(raw_lines)
    print(f"Unpacked {len(raw_lines)} raw lines into {len(unpacked_lines)} sequential lines.")
    
    records = []
    current_street = ""
    last_header_prefix = ""
    
    for line in unpacked_lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        tokens = [p.strip() for p in line.split('\t') if p.strip()]
        matched_street = None
        
        # Check split header from previous line (e.g. prefix was "CONSTA-", this line is "BLE DRIVE.")
        if last_header_prefix:
            if last_header_prefix.endswith('-'):
                combined = f"{last_header_prefix.rstrip('-')}{line_clean}"
            else:
                combined = f"{last_header_prefix} {line_clean}"
            st = detect_street_header(combined)
            if st:
                matched_street = st
                last_header_prefix = ""
                
        if not matched_street:
            # Check individual tokens first
            for tok in tokens:
                st = detect_street_header(tok)
                if st:
                    matched_street = st
                    break
                    
        if not matched_street:
            # Check adjacent token pairs
            for idx in range(len(tokens) - 1):
                combined = f"{tokens[idx]} {tokens[idx+1]}"
                st = detect_street_header(combined)
                if st:
                    matched_street = st
                    break
                    
        if not matched_street:
            st = detect_street_header(line_clean)
            if st:
                matched_street = st
                            
        if matched_street:
            current_street = matched_street
            last_header_prefix = ""
            continue
            
        # Check if line is an incomplete street prefix
        if line_clean.isupper() and len(line_clean) > 3 and not re.match(r'^(?:NEWPORT\s+)?\d+', line_clean) and not CROSS_STREET_PAT.search(line_clean):
            words = line_clean.split()
            if words and words[-1] not in STREET_SUFFIXES:
                last_header_prefix = line_clean
                continue
                
        last_header_prefix = ""
        
        if not current_street:
            continue
            
        res = parse_line_to_resident(line)
        if res:
            h_num, surname, forename, trade, bldg = res
            if surname or forename or trade or bldg:
                records.append({
                    "year": "1971",
                    "street": current_street,
                    "house_number": h_num,
                    "building_name": bldg,
                    "surname": surname,
                    "forename": forename,
                    "trade": trade
                })
                
    with open(output_path, 'w', encoding='utf-8', newline='') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["year", "street", "house_number", "building_name", "surname", "forename", "trade"])
        writer.writeheader()
        writer.writerows(records)
        
    print(f"Parsed {len(records)} records from {input_path} into {output_path}.")
    return records

if __name__ == "__main__":
    parse_tsv("raw_tsvs/1971.tsv", "volume_csvs/1971_cleaned.csv")
