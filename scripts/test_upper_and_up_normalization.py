import csv
import re

ROMAN_NUMERALS = {'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'}
LOWERCASE_WORDS = {'and', 'of', 'the', '&', 'de', 'du', 'yr', 'y'}
SPECIAL_CASES = {
    'G.W.R.': 'G.W.R.',
    'GWR': 'G.W.R.',
    'ALLT-YR-YN': 'Allt-yr-yn',
    'ALLT-YR-YN ROAD': 'Allt-yr-yn Road',
    'ALLT-YR-YN AVENUE': 'Allt-yr-yn Avenue',
    'ALLT-YR-YN VIEW': 'Allt-yr-yn View',
    'COURT-Y-BELLA': 'Courtybella',
    'COURT-Y-BELLA STREET': 'Courtybella Street',
    'COURT-Y-BELLA TERRACE': 'Courtybella Terrace',
    'ST.': 'St.',
    'WHARVES (THE)': 'Wharves',
    'WHARVES': 'Wharves',
    'CLI (HIGH-STREET (RETURN))': 'High Street (Return)',
    'COMMERCIAL WHARF. E': 'Commercial Wharf',
    'GOTHIC VILLAS—': 'Gothic Villas'
}

def normalize_up_abbrev(st):
    s = st.strip()
    # Handle 'Up. ', 'Upp. ', 'Up ', 'Upp ' at the start of street names
    s = re.sub(r'^(?:up|upp)\.?\s+', 'Upper ', s, flags=re.IGNORECASE)
    # Handle Fair Oak Ter. (Upr.)
    if re.search(r'Fair Oak Ter\.?\s*\(Upr\.?\)', s, re.I) or re.search(r'F\.?\s*Oak Ter\.?\s*\(Upr\.?\)', s, re.I):
        return 'Upper Fair Oak Terrace'
    return s

def to_title_case_street(st):
    st_clean = st.strip()
    if st_clean in SPECIAL_CASES:
        return SPECIAL_CASES[st_clean]
    
    # Check if string is indeed all uppercase (has letters, and all letters are uppercase)
    letters = [c for c in st_clean if c.isalpha()]
    if not (letters and all(c.isupper() for c in letters)):
        return st_clean
    
    words = st_clean.split(' ')
    title_tokens = []
    
    for i, w in enumerate(words):
        if not w:
            continue
        
        # Roman numerals e.g. EDWARD VII. -> Edward VII
        w_upper = w.upper().rstrip('.,;:')
        punct = w[len(w_upper):]
        if w_upper in ROMAN_NUMERALS:
            # Drop trailing period on Roman numeral if followed by another word
            if punct == '.' and i < len(words) - 1:
                title_tokens.append(w_upper)
            else:
                title_tokens.append(w_upper + punct)
            continue
            
        # Hyphenated parts
        if '-' in w:
            parts = w.split('-')
            titled_parts = []
            for j, p in enumerate(parts):
                p_up = p.upper()
                if p_up in ROMAN_NUMERALS:
                    titled_parts.append(p_up)
                elif p_up.lower() in LOWERCASE_WORDS and j > 0:
                    titled_parts.append(p.lower())
                else:
                    if "'" in p or "’" in p:
                        delim = "'" if "'" in p else "’"
                        ap = p.split(delim)
                        titled_parts.append(ap[0].capitalize() + delim + ap[1].lower())
                    else:
                        titled_parts.append(p.capitalize())
            title_tokens.append('-'.join(titled_parts))
            continue
            
        # Apostrophes e.g. QUEEN'S, KING'S, ST. MARY'S
        if "'" in w or "’" in w:
            delim = "'" if "'" in w else "’"
            parts = w.split(delim)
            titled = parts[0].capitalize() + delim + parts[1].lower()
            title_tokens.append(titled)
            continue
            
        # Lowercase joiners
        if w.lower() in LOWERCASE_WORDS and i > 0:
            title_tokens.append(w.lower())
            continue
            
        # St. or S.
        if w.upper() in ['ST.', 'S.']:
            title_tokens.append('St.')
            continue
            
        title_tokens.append(w.capitalize())
        
    result = ' '.join(title_tokens)
    if result:
        result = result[0].upper() + result[1:]
    return result

def full_clean(st):
    s = normalize_up_abbrev(st)
    s = to_title_case_street(s)
    # Also if ends with period or comma, strip it
    s = re.sub(r'[\.\,\:\;\-]+$', '', s).strip()
    return s

def main():
    with open('data.csv', 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    modified_count = 0
    transformations = {}

    for r in rows:
        st = r.get('street', '').strip()
        cleaned = full_clean(st)
        if cleaned != st:
            modified_count += 1
            transformations[st] = (cleaned, transformations.get(st, (cleaned, 0))[1] + 1)

    print(f"Total records to be modified: {modified_count:,}")
    print(f"Total unique street transformations: {len(transformations)}")
    print("\nSample top transformations:")
    for orig, (targ, cnt) in sorted(transformations.items(), key=lambda x: x[1][1], reverse=True)[:50]:
        print(f"{cnt:5d}  \"{orig}\"  ==>  \"{targ}\"")

if __name__ == '__main__':
    main()
