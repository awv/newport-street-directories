import re
import csv
import sys
import os

sys.path.append(os.getcwd())
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
    'parade', 'pde', 'hill', 'walk', 'court', 'row', 'wharf', 'quay',
    'dock', 'docks', 'villas', 'gardens', 'mews', 'rise', 'drive',
    'passage', 'market', 'arcade', 'bank', 'grove', 'path', 'close',
    'view', 'way', 'circus', 'circle'
}

KNOWN_STREETS = {
    'baneswell', 'courtybella', 'friars', 'the friars', 'stow', 'stow hill',
    'barnard town', 'town hall', 'union', 'westgate', 'cambria', 'melbourne',
    'ringland', 'cross-street', 'cross street', 'cross lane', 'maindee',
    'the marshes', 'marshes', 'belle vue', 'gold tops', 'pentonville'
}

IGNORED_HEADER_REGEX = re.compile(
    r'\b(?:newport\s+street\s+list|newport\s+street\s+directory|newport\s+directory|street\s+directory)\b'
    r'|^\s*newport\s*[\.\-—]*$'
    r'|^\s*directory\s*[\.\-—]*$'
    r'|\b(?:steam\s+laundry|promptness\s+and\s+despatch|parkin\s+&\s+son|heating\s+engineers|heating\s+installations)\b'
    r'|\b(?:costumes\s+beautifully\s+cleaned|p\.\s*e\.\s*gane|edwards\s+ltd|gunmakers|sports\s+outfitters)\b'
    r'|\b(?:tel\.\s*\d+|telephone\s+call\s+office|plumbing\s+work|first\s+class\s+plumbing)\b'
    r'|\b(?:showrooms\s+and\s+offices|good\s+shirt|service\s+the\s+keynote)\b'
    r'|\b(?:durham\s+road\s+schools|alexandra\s+schools|spring\s+gardens\s+school|presbyterian\s+church|wesley\s+church)\b'
    r'|\b(?:masonic\s+hall|the\s+barracks|corporation\s+baths|woodland\s+street\s+directory)\b',
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
    r'^\s*(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|P|M|C|T|B|L|D|E|Pill|Maindee|Crindau|Marshes|Liswerry|Borough|Town|Tunnel|continued|contd|cont|cont[\'’]d|contind|Ch|[A-Z]\s*\d+)\.?\s*$',
    re.I
)

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
        
    s_clean = re.sub(r'[\s\-—–_]+(?:continued|contd|cont|cont\.|cont[\'’]d|contind)\b', '', s_candidate, flags=re.I).strip()
    s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,–_')
    
    if not re.search(r'\bHigh\s+Street\b', s_clean, re.I):
        s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|Ch|[PMCTBLDE]|\b[A-Z]\s*\d+\b)\s*$', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,–_')
    
    if NAME_ABBR_PAT.search(s_clean):
        return False
        
    words = [w.strip('.,()-"\'–_') for w in s_clean.lower().split() if w.strip('.,()-"\'–_')]
    if not words:
        return False
    is_cont = bool(re.search(r"(?:continued|contd|cont|cont\.|cont['’]d)", s, re.I))
    if not is_cont and not s_clean.isupper():
        return False
        
    if len(words) < 2 and s_clean.lower() not in KNOWN_STREETS:
        return False
        
    if re.search(r'\b(?:ltd|limited|co|coy|chants|merchants|works|inn|hotel|tavern|brewery)\b', s_clean, re.I):
        return False
        
    last_word = words[-1]
    is_st = last_word in STREET_SUFFIXES or s_clean.lower() in KNOWN_STREETS
    return is_st

def clean_trade(trade):
    if not trade:
        return ""
    t_clean = trade.strip(' ,"-~.')
    t_low = t_clean.lower()
    if t_low in {'p.c.', 'p.o. clerk', 'h.m.c'}:
        return t_low.upper()
    val = t_low
    if val in TRADE_TYPO_MAP:
        val = TRADE_TYPO_MAP[val]
    if val in TRADE_EXACT_MAP:
        val = TRADE_EXACT_MAP[val]
    if val in TRADE_ABBREV_MAP:
        val = TRADE_ABBREV_MAP[val]
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
    name = re.sub(r'\bHy\.?\b', 'Henry', name)
    name = re.sub(r'\bEdwd?\.?\b', 'Edward', name)
    name = re.sub(r'\bJno\.?\b', 'John', name)
    name = re.sub(r'\bAlfd?\.?\b', 'Alfred', name)
    name = re.sub(r'\bAlbt\.?\b', 'Albert', name)
    name = re.sub(r'\bRichd?\.?\b', 'Richard', name)
    name = re.sub(r'\bDanl?\.?\b', 'Daniel', name)
    name = re.sub(r'\bSaml?\.?\b', 'Samuel', name)
    name = re.sub(r'\bJas\.?\b', 'James', name)
    return name.strip(' ,"-~.')

# Test run on raw_tsvs/1915.tsv
streets_found = set()
records = []
current_street = ""

with open("raw_tsvs/1915.tsv", "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, start=1):
        parts = [p.replace('\\t', '').replace('\\n', '').strip() for p in line.rstrip('\r\n').split('\t')]
        while len(parts) < 6:
            parts.append('')
            
        if not any(parts):
            continue
            
        # Ignore running headers / banners
        if any(IGNORED_HEADER_REGEX.search(p) for p in parts if p):
            continue
            
        # Check if row is a street candidate
        first_candidate = next((p for p in parts[:3] if p), '')
        matched_street = ""
        if first_candidate and is_valid_street_name(first_candidate):
            matched_street = first_candidate
        elif parts[0] and parts[1] and parts[1].strip('., -—').lower() in STREET_SUFFIXES:
            candidate = parts[0] + " " + parts[1]
            if is_valid_street_name(candidate):
                matched_street = candidate
                
        if matched_street:
            s_clean = re.sub(r'^[\(\[]?\s*return[\.\)]*\s*', '', matched_street, flags=re.I).strip('. -—')
            s_clean = re.sub(r'[\s\-—–_]+(?:continued|contd|cont|cont\.|cont[\'’]d|contind)\b', '', s_clean, flags=re.I).strip()
            s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
            s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
            if not re.search(r'\bHigh\s+Street\b', s_clean, re.I):
                s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|Ch|[PMCTBLDE]|\b[A-Z]\s*\d+\b)\s*$', '', s_clean, flags=re.I).strip()
            current_street = clean_street_name(s_clean)
            streets_found.add(current_street)
            if not any(parts[2:]) or parts[1].strip('., -—').lower() in STREET_SUFFIXES:
                continue
            else:
                if parts[0] == matched_street:
                    parts[0] = ''

        combined_row = " ".join([p for p in parts if p]).strip()
        if re.match(r'^[\s\*\-\_\=\#\+]+$', combined_row):
            continue
        if CROSS_STREET_PAT.search(combined_row):
            continue
        if not current_street:
            continue
        if parts[0] == "Number" and parts[1] == "Forenames":
            continue

        # Extract resident from primary columns
        h_num = parts[0]
        surname = parts[1]
        forename = parts[2]
        trade = parts[3]
        bldg = parts[4]
        
        # If parts[0] has no digits and parts[1] is empty, but parts[0] has name+trade
        if not surname and not forename and not trade and h_num:
            raw_text = h_num.strip()
            m_num = re.match(r'^(\d+(?:[a-zA-Z]|\s*-\s*\d+)?)\s+(.*)$', raw_text)
            if m_num:
                h_num = m_num.group(1).replace(' ', '')
                rest = m_num.group(2).strip()
            else:
                h_num = ""
                rest = raw_text
            if ',' in rest:
                name_p, trade_p = rest.split(',', 1)
                np = name_p.strip().split(maxsplit=1)
                surname = np[0] if np else ""
                forename = np[1] if len(np) > 1 else ""
                trade = trade_p.strip()
            else:
                np = rest.strip().split(maxsplit=1)
                surname = np[0] if np else ""
                forename = np[1] if len(np) > 1 else ""

        if forename and ',' in forename:
            fn, tr = forename.split(',', 1)
            forename = fn.strip()
            if not trade:
                trade = tr.strip()
            else:
                trade = f"{trade}, {tr.strip()}".strip(' ,')

        if surname and ',' in surname:
            sn, tr = surname.split(',', 1)
            surname = sn.strip()
            if not trade:
                trade = tr.strip()
            else:
                trade = f"{trade}, {tr.strip()}".strip(' ,')

        trade = clean_trade(trade)
        forename = clean_name_abbr(forename)

        if forename or surname or trade or bldg:
            records.append({
                "year": "1915",
                "street": current_street,
                "house_number": h_num,
                "building_name": bldg,
                "surname": surname,
                "forename": forename,
                "trade": trade
            })

print(f"Total records parsed: {len(records):,}")
print(f"Total distinct streets: {len(streets_found):,}")
from collections import Counter
c = Counter(r['street'] for r in records)
print("Top 15 streets:")
for s, n in c.most_common(15):
    print(f"  {s}: {n}")
