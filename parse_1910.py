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
        
    s_clean = s
    s_clean = re.sub(r'[\s\-—]+continued\b', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
    
    # Strip trailing grid references
    s_clean = re.sub(r'[\.\s]+[A-Z][\s\.,\d]*$', '', s_clean, flags=re.I).strip(' ,.-')
    
    if len(s_clean) <= 1:
        return False
        
    ignored_streets = {
        "left hand side", "right hand side", "east side", "west side", "north side", "south side",
        "acronyms", "abbreviations", "newport street directory", "the block",
        "temperance hall", "wharf", "windsor castle", "york house"
    }
    if s_clean.lower() in ignored_streets:
        return False
        
    if CROSS_STREET_PAT.search(s_clean):
        return False
        
    # 1. Matches a known street from other years (case-insensitive)
    if s_clean.lower() in known_streets:
        return True
        
    # 2. Must be uppercase (no lowercase letters allowed)
    if not any(c.islower() for c in s_clean):
        return True
        
    # 3. Contains a street suffix and doesn't look like a resident listing
    suffixes = {'street', 'road', 'avenue', 'place', 'terrace', 'hill', 'lane', 'crescent', 'cres', 'cres.', 'parade', 'way', 'drive', 'grove', 'villas', 'gardens', 'walk', 'square', 'court', 'close', 'view', 'park', 'green', 'st', 'rd', 'av', 'pl', 'ln', 'sq', 'ct', 'cl', 'pk'}
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


def parse_tsv(input_path, output_path):
    records = []
    current_street = ""
    prev_surname = ""
    prev_trade = ""
    
    with open(input_path, "r", encoding="utf-8") as f_in:
        reader = csv.reader(f_in, delimiter="\t")
        next(reader, None) # skip header
        
        for row_idx, row in enumerate(reader, start=2):
            if not row or all(not val.strip() for val in row):
                continue
                
            # If the row has no tabs and is all caps, it's a street header
            if len(row) == 1 or (len(row) > 1 and all(not val.strip() for val in row[1:]) and row[0].strip()):
                val = row[0].strip()
                if is_valid_street_name(val):
                    current_street = clean_street_name(val)
                continue
                
            if not current_street:
                continue
                
            # Pad row if shorter than 6 columns
            while len(row) < 6:
                row.append("")
                
            number_val = row[0].strip()
            forenames_val = row[1].strip()
            surname_val = row[2].strip()
            job_val = row[3].strip()
            business_val = row[4].strip()
            notes_val = row[5].strip()
            
            # Skip if this is a cross street or layout marker row
            combined_fields = " ".join([number_val, forenames_val, surname_val, job_val, business_val, notes_val]).strip()
            if CROSS_STREET_PAT.search(combined_fields):
                continue
                
            # Handle return markers
            if "return" in number_val.lower() or "return" in forenames_val.lower() or "return" in surname_val.lower():
                continue
                
            # Clean up fields
            h_num = number_val.strip(' ,.-')
            bldg = business_val.strip(' ,.-')
            
            # Real names mapping
            surname = clean_name_abbr(surname_val)
            forename = clean_name_abbr(forenames_val)
            trade = clean_trade(job_val)
            
            # Carry over ditto / same-surname values
            if (surname_val == '"' or surname_val.lower() == 'do' or surname_val.lower() == 'ditto') and prev_surname:
                surname = prev_surname
            if (job_val == '"' or job_val.lower() == 'do' or job_val.lower() == 'ditto') and prev_trade:
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
                
                # Check for multiple names packed in notes
                raw_parts_for_extra = [notes_val]
                if "/" in notes_val:
                    raw_parts_for_extra = notes_val.split("/")
                
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
                                "year": "1910",
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
    parse_tsv("1910.tsv", "1910_cleaned.csv")
