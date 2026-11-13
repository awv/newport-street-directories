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
    'ST.': 'St.'
}

def to_title_case_street(st):
    st_clean = st.strip()
    if st_clean in SPECIAL_CASES:
        return SPECIAL_CASES[st_clean]
    
    # Check if string is indeed all uppercase (at least one letter and all letters are uppercase)
    letters = [c for c in st_clean if c.isalpha()]
    if not (letters and all(c.isupper() for c in letters)):
        return st_clean # Already mixed/title case
    
    # Process tokens split by space
    words = st_clean.split(' ')
    title_tokens = []
    
    for i, w in enumerate(words):
        if not w:
            continue
        
        # Check Roman numerals
        w_upper = w.upper().rstrip('.,;:')
        punct = w[len(w_upper):]
        if w_upper in ROMAN_NUMERALS:
            title_tokens.append(w_upper + punct)
            continue
            
        # Check hyphenated parts
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
                    # Title case part
                    if "'" in p:
                        ap = p.split("'")
                        titled_parts.append(ap[0].capitalize() + "'" + ap[1].lower())
                    else:
                        titled_parts.append(p.capitalize())
            title_tokens.append('-'.join(titled_parts))
            continue
            
        # Check apostrophes e.g. QUEEN'S, KING'S, ST. MARY'S
        if "'" in w or "’" in w:
            delim = "'" if "'" in w else "’"
            parts = w.split(delim)
            titled = parts[0].capitalize() + delim + parts[1].lower()
            title_tokens.append(titled)
            continue
            
        # Check lowercase joiners (unless first word)
        if w.lower() in LOWERCASE_WORDS and i > 0:
            title_tokens.append(w.lower())
            continue
            
        # Handle St. or S.
        if w.upper() in ['ST.', 'S.']:
            title_tokens.append('St.')
            continue
            
        # Standard capitalization
        title_tokens.append(w.capitalize())
        
    result = ' '.join(title_tokens)
    # Ensure first letter is capitalized
    if result:
        result = result[0].upper() + result[1:]
    return result

def main():
    with open('data.csv', 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    upper_streets = {}
    for r in rows:
        st = r.get('street', '').strip()
        letters = [c for c in st if c.isalpha()]
        if letters and all(c.isupper() for c in letters):
            upper_streets[st] = upper_streets.get(st, 0) + 1

    print(f"Total ALL CAPS streets found: {len(upper_streets)} ({sum(upper_streets.values()):,} records)")
    print("\nSample title-casing transformations:")
    for orig, cnt in sorted(upper_streets.items(), key=lambda x: x[1], reverse=True)[:50]:
        targ = to_title_case_street(orig)
        print(f"{cnt:5d}  \"{orig}\"  ==>  \"{targ}\"")

if __name__ == '__main__':
    main()
