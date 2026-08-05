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
    if not s.isupper():
        return False
    if s.startswith('(') or s.startswith('[') or s.startswith('*') or s.endswith(')'):
        return False
    if s.lower() in {'(return)', 'return', 'continued', 'tregare street—continued'}:
        return False
    if s.startswith("OFF ") or s.startswith("FROM ") or s.startswith("TO "):
        return False
    if s in {"LEFT HAND SIDE", "RIGHT HAND SIDE", "EAST SIDE", "WEST SIDE"}:
        return False
    return True

def parse_tsv(input_path, output_path):
    records = []
    current_street = ""
    
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            parts = [p.strip() for p in line.split('\t')]
            while len(parts) < 6:
                parts.append('')
            parts = parts[:6]
            
            # Skip empty lines
            if not any(p for p in parts):
                continue
                
            # Combine all non-empty columns with a space to check cross-street descriptions
            combined_row = " ".join([p for p in parts if p]).strip()
            
            # Check for divider patterns (like **, ***, ---)
            if re.match(r'^[\s\*\-\_\=\#\+]+$', combined_row):
                continue
                
            # Check for cross-street descriptions on the combined row and its symbol-stripped version
            combined_row_stripped = combined_row.strip(' *-_~()[]')
            combined_row_lower = combined_row_stripped.lower()
            if (CROSS_STREET_PAT.search(combined_row) or 
                CROSS_STREET_PAT.search(combined_row_stripped) or
                combined_row_lower.startswith("from ") or 
                combined_row_lower.startswith("to ") or 
                combined_row_lower.startswith("opposite ") or 
                combined_row_lower.startswith("here is ") or 
                combined_row_lower.startswith("here are ")):
                continue
                
            col0 = parts[0]
            other_cols_empty = all(not p for p in parts[1:])
            
            # Identify street header
            is_street = False
            if col0 and other_cols_empty:
                if is_valid_street_name(col0):
                    is_street = True
                    
            if is_street:
                current_street = clean_street_name(col0)
                continue
                
            # If we don't have an active street name, skip records
            if not current_street:
                continue
                
            # Skip CSV/TSV headers
            if col0 == "Number" and parts[1] == "Forenames":
                continue
                
            h_num = parts[0]
            forename = parts[1]
            surname = parts[2]
            trade = parts[3]
            bldg = parts[4]
            notes = parts[5]
            
            # Post-process: If the row has no surname and no trade, but has a forename,
            # it means the model did not separate columns with tabs. Let's split it.
            if not surname and not trade and forename:
                combined = forename.strip()
                if ',' in combined:
                    name_part, trade_part = combined.split(',', 1)
                    trade = trade_part.strip()
                    name_parts = name_part.strip().split(maxsplit=1)
                    if len(name_parts) == 2:
                        surname = name_parts[0]
                        forename = name_parts[1]
                    else:
                        surname = name_part.strip()
                        forename = ""
                else:
                    name_parts = combined.split(maxsplit=1)
                    if len(name_parts) == 2:
                        surname = name_parts[0]
                        forename = name_parts[1]
                    else:
                        surname = combined
                        forename = ""
                    trade = ""
            
            # General cleanup: If there is a comma in forename or surname, extract the trade
            if forename and ',' in forename:
                forename_part, trade_part = forename.split(',', 1)
                forename = forename_part.strip()
                if not trade:
                    trade = trade_part.strip()
                else:
                    trade = f"{trade}, {trade_part.strip()}".strip(' ,')
                    
            if surname and ',' in surname:
                surname_part, trade_part = surname.split(',', 1)
                surname = surname_part.strip()
                if not trade:
                    trade = trade_part.strip()
                else:
                    trade = f"{trade}, {trade_part.strip()}".strip(' ,')
            
            # Shift misaligned titles/forenames in the 'Business / Entity' or 'Job / Trade' columns to 'Forenames'
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

            # Check if this row is purely a cross-street or return indicator in Layout/Notes
            if not h_num and not forename and not surname and not trade and not bldg and notes:
                if CROSS_STREET_PAT.search(notes):
                    continue
                # If it's a descriptor like "ALEXANDRA SCHOOLS", store it
                if notes.isupper() and len(notes) > 4:
                    bldg = notes
                    notes = ""
            
            # Filter out non-resident landmark/institution note rows (e.g. churches, gas works, football grounds)
            # that do not have any associated person name or house number
            if not h_num and not forename and not surname:
                comb_val = f"{trade} {bldg} {notes}".lower()
                landmark_keywords = {
                    'church', 'ch.', 'chapel', 'grounds', 'gas works', 'gasworks', 
                    'see also', 'school', 'schools', 'hall', 'chambers', 'depot', 'works'
                }
                if any(kw in comb_val for kw in landmark_keywords):
                    continue
            
            # Standardize trades
            trade = clean_trade(trade)
            
            # Expand names
            forename = clean_name_abbr(forename)
            
            # Build record
            if forename or surname or trade or bldg:
                records.append({
                    "year": "1927",
                    "street": current_street,
                    "house_number": h_num,
                    "building_name": bldg,
                    "surname": surname,
                    "forename": forename,
                    "trade": trade
                })
                
    # Write to output
    with open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["year", "street", "house_number", "building_name", "surname", "forename", "trade"])
        writer.writeheader()
        writer.writerows(records)
        
    print(f"Parsed {len(records)} records from {input_path} into {output_path}.")

if __name__ == "__main__":
    parse_tsv("1927.tsv", "1927_cleaned.csv")
