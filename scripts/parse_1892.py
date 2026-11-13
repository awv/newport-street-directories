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
    'parade', 'pde', 'hill', 'walk', 'court', 'row', 'wharf', 'quay',
    'dock', 'docks', 'villas', 'gardens', 'mews', 'rise', 'drive',
    'passage', 'market', 'arcade', 'bank', 'grove', 'path', 'close',
    'view', 'way', 'circus', 'circle'
}

KNOWN_STREETS = {
    'baneswell', 'courtybella', 'friars', 'the friars', 'stow', 'stow hill',
    'barnard town', 'town hall', 'union', 'westgate', 'cambria', 'melbourne',
    'ringland', 'cross-street', 'cross street', 'cross lane', 'maindee',
    'the marshes', 'marshes', 'belle vue', 'gold tops', 'pentonville',
    'acadia terrace', 'alteryn road', 'alexandra docks'
}

STREET_CORRECTIONS = {
    'carlisle st': 'Carlisle Street',
    'commercial rd': 'Commercial Road',
    'commercial st': 'Commercial Street',
    'courtybella st': 'Courtybella Street',
    'courtybella': 'Courtybella Terrace',
    'manchester st': 'Manchester Street',
    'nelson st': 'Nelson Street',
    'ridge rd': 'Ridge Road',
    'bishopgate parade': 'Bishopsgate Parade',
    'clytha park & road': 'Clytha Park Road',
    'esveswell terrace': 'Eveswell Terrace',
    'fair oak terrace': 'Fairoak Terrace',
    "friar's road": 'Friars Road',
    "friars' road": 'Friars Road',
    "glo'ster street": 'Gloster Street',
    "st john's road": "St. John's Road",
    "queen’s hill terrace": "Queen's Hill Terrace",
    "queen's hill terrace": "Queen's Hill Terrace",
    "queen’s place": "Queen's Place",
    "queen's place": "Queen's Place",
    "waters' lane": 'Waters Lane',
    "moulder's arms ter": "Moulders Arms Terrace",
    "county police court": "Police Court",
    "upper baldwin st": "Upper Baldwin Street",
    "hiley's court": "Hiley's Court",
    "merriott's place": "Merriott's Place",
    "upper marion street": "Upper Marion Street",
    "west side old dock": "West-side of Old Dock",
}

IGNORED_HEADER_REGEX = re.compile(
    r'\b(?:newport\s+street\s+list|newport\s+street\s+directory|newport\s+directory|street\s+directory|street\s+direction)\b'
    r'|^\s*newport\s*[\.\-—]*$'
    r'|^\s*directory\s*[\.\-—]*$'
    r'|^\s*newport\s+street\s+list[\.\s]*$'
    r'|\b(?:trapnell\s+&\s+gane|house\s+furnishers)\b',
    re.I
)

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

NAME_ABBR_PAT = re.compile(
    r'\b(?:mr|mrs|miss|rev|dr|capt|col|hon|snr|jun|esq|wm|thos|geo|chas|edwd|robt|hy|jas|jno|danl|alfd|fredk)\b',
    re.I
)

VALID_WARD_AFTER_COMMA = re.compile(
    r'^\s*(?:P\.|B\.T\.?|B\.t|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|P|M|C|T|B|L|D|E|Pill|Maindee|Crindau|Marshes|Liswerry|Borough|Town|Tunnel|continued|contd|cont|cont[\'’]d|contind)\.?\s*$',
    re.I
)

TITLES = {'mrs', 'miss', 'rev', 'dr', 'capt', 'col', 'hon', 'esq', 'mr', 'lord', 'sir'}

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

def is_valid_street_name(s):
    if not s:
        return False
    s = s.strip()
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
        s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.?|B\.t|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|[PMCTBLDE])\s*$', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,–_')
    
    if NAME_ABBR_PAT.search(s_clean):
        return False
        
    words = [w.strip('.,()-"\'–_') for w in s_clean.lower().split() if w.strip('.,()-"\'–_')]
    if not words:
        return False

    # Filter out resident names with initials ending in view (e.g. "Adams J. H. Channel view")
    if any(re.match(r'^[a-z]\.?$', w) for w in words[:-1]):
        return False
        
    if len(words) < 2 and s_clean.lower() not in KNOWN_STREETS:
        return False
        
    if re.search(r'\b(?:ltd|limited|co|coy|chants|merchants|works|inn|hotel|tavern|brewery)\b', s_clean, re.I):
        return False
        
    last_word = words[-1]
    is_st = last_word in STREET_SUFFIXES or s_clean.lower() in KNOWN_STREETS
    return is_st

def parse_tsv(input_path, output_path):
    records = []
    current_street = ""
    streets_found = Counter()

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            parts = [p.replace('\\t', '').replace('\\n', '').strip() for p in line.rstrip('\r\n').split('\t')]
            while len(parts) < 6:
                parts.append('')
                
            if not any(parts):
                continue
                
            if any(IGNORED_HEADER_REGEX.search(p) for p in parts if p):
                continue

            first_cand = next((p for p in parts[:3] if p), '')
            is_street = False
            matched_street = ""

            if first_cand and is_valid_street_name(first_cand):
                is_street = True
                matched_street = first_cand
            elif first_cand and first_cand.strip().upper() in {"HIGH STREET, P.", "HIGH STREET, P"}:
                is_street = True
                matched_street = "HIGH STREET, PILL"
            else:
                for p in parts[:2]:
                    p_clean = p.strip(' .,-_~()[]')
                    if p_clean.lower() in {"cross lane", "cross street"}:
                        is_street = True
                        matched_street = p_clean.upper()
                        break

            if is_street:
                s_clean = re.sub(r'^[\(\[]?\s*return[\.\)]*\s*', '', matched_street, flags=re.I).strip('. -—')
                s_clean = re.sub(r'[\s\-—–_]+(?:continued|contd|cont|cont\.|cont[\'’]d|contind)\b', '', s_clean, flags=re.I).strip()
                s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
                s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
                if not re.search(r'\bHigh\s+Street\b', s_clean, re.I):
                    s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.?|B\.t|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|[PMCTBLDE])\s*$', '', s_clean, flags=re.I).strip()
                
                # Expand "Up." or "Up " to "Upper "
                s_clean = re.sub(r'^(?:Up|Upp)[\.\s]+', 'Upper ', s_clean, flags=re.I).strip()
                if s_clean.lower().startswith('upper '):
                    s_clean = 'Upper ' + ' '.join(w.capitalize() for w in s_clean[6:].split())
                
                s_norm = clean_street_name(s_clean)
                s_low = s_norm.lower()
                if s_low in STREET_CORRECTIONS:
                    s_norm = STREET_CORRECTIONS[s_low]

                current_street = s_norm
                streets_found[current_street] += 1
                if not any(parts[1:]):
                    continue
                else:
                    if parts[0] == matched_street:
                        parts[0] = ''

            combined_row = ' '.join([p for p in parts if p]).strip()
            if re.match(r'^[\s\*\-\_\=\#\+]+$', combined_row):
                continue
            if CROSS_STREET_PAT.search(combined_row):
                continue
            if not current_street:
                continue
            if parts[0] == 'Number' and parts[1] == 'Forenames':
                continue

            # In 1892.tsv:
            # parts[0]: Number
            # parts[1]: Forenames (e.g. "M. A.", "W.", "David", "Mrs")
            # parts[2]: Surname (e.g. "Shillabeer", "Parsons", "Phillips", "Miller")
            # parts[3]: Trade (or Forename if parts[1] was Title)
            # parts[4]: Business / Entity
            # parts[5]: Layout / Notes

            h_num = parts[0]
            col1 = parts[1]
            col2 = parts[2]
            col3 = parts[3]
            bldg = parts[4]

            # Skip ad row: e.g. 0 Trapnell & Gane
            if h_num == '0' and not col1 and 'Trapnell' in col2:
                continue

            surname = col2
            forename = col1
            trade = col3

            # Check if col1 was a Title and col3 was a Forename (e.g. "Rev", "Davies", "Joshua")
            col1_low = col1.lower().strip('.')
            if col1_low in TITLES and col3 and not any(k in col3.lower() for k in ['maker', 'driver', 'worker', 'labourer', 'smith', 'fitter', 'clerk', 'grocer', 'tailor', 'agent', 'dealer', 'inn', 'hotel', 'works']):
                forename = f"{col1} {col3}".strip()
                trade = ""

            # If col0 has house number and resident text combined (e.g. "4 Wm. H. Shute")
            if not surname and not forename and not trade and h_num:
                raw_text = h_num.strip()
                m_num = re.match(r'^(\d+(?:[a-zA-Z]|\s*-\s*\d+)?)\s+(.*)$', raw_text)
                if m_num:
                    h_num = m_num.group(1).replace(' ', '')
                    rest = m_num.group(2).strip()
                else:
                    h_num = ''
                    rest = raw_text
                # Split rest
                tokens = rest.split(maxsplit=1)
                surname = tokens[0] if tokens else ""
                forename = tokens[1] if len(tokens) > 1 else ""

            trade = clean_trade(trade)
            forename = clean_name_abbr(forename)

            if forename or surname or trade or bldg:
                records.append({
                    'year': '1892',
                    'street': current_street,
                    'house_number': h_num,
                    'building_name': bldg,
                    'surname': surname,
                    'forename': forename,
                    'trade': trade
                })

    print(f"Total parsed records: {len(records)}")
    print(f"Total distinct streets: {len(streets_found)}")

    with open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=['year', 'street', 'house_number', 'building_name', 'surname', 'forename', 'trade'])
        writer.writeheader()
        writer.writerows(records)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    in_tsv = os.path.join(base_dir, "raw_tsvs", "1892.tsv")
    out_csv = os.path.join(base_dir, "volume_csvs", "1892_cleaned.csv")
    parse_tsv(in_tsv, out_csv)
