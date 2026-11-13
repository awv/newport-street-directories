#!/usr/bin/env python3
import csv
import re
import shutil
from pathlib import Path

DATA_CSV = Path("/Users/robgale/Documents/Newport Street Directory Project/data.csv")
BACKUP_CSV = Path("/Users/robgale/Documents/Newport Street Directory Project/data.csv.bak_before_upper_and_up_normalization")

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
    s = re.sub(r'^(?:up|upp)\.?\s+', 'Upper ', s, flags=re.IGNORECASE)
    if re.search(r'Fair Oak Ter\.?\s*\(Upr\.?\)', s, re.I) or re.search(r'F\.?\s*Oak Ter\.?\s*\(Upr\.?\)', s, re.I):
        return 'Upper Fair Oak Terrace'
    return s

def to_title_case_street(st):
    st_clean = st.strip()
    if st_clean in SPECIAL_CASES:
        return SPECIAL_CASES[st_clean]
    
    letters = [c for c in st_clean if c.isalpha()]
    if not (letters and all(c.isupper() for c in letters)):
        return st_clean
    
    words = st_clean.split(' ')
    title_tokens = []
    
    for i, w in enumerate(words):
        if not w:
            continue
        
        w_upper = w.upper().rstrip('.,;:')
        punct = w[len(w_upper):]
        if w_upper in ROMAN_NUMERALS:
            if punct == '.' and i < len(words) - 1:
                title_tokens.append(w_upper)
            else:
                title_tokens.append(w_upper + punct)
            continue
            
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
            
        if "'" in w or "’" in w:
            delim = "'" if "'" in w else "’"
            parts = w.split(delim)
            titled = parts[0].capitalize() + delim + parts[1].lower()
            title_tokens.append(titled)
            continue
            
        if w.lower() in LOWERCASE_WORDS and i > 0:
            title_tokens.append(w.lower())
            continue
            
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
    s = re.sub(r'[\.\,\:\;\-]+$', '', s).strip()
    return s

def main():
    print(f"Backing up {DATA_CSV} -> {BACKUP_CSV}...")
    shutil.copy2(DATA_CSV, BACKUP_CSV)

    with open(DATA_CSV, 'r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

    modified_count = 0
    unique_map = {}

    for r in reader:
        st = r.get('street', '').strip()
        cleaned = full_clean(st)
        if cleaned != st:
            r['street'] = cleaned
            modified_count += 1
            unique_map[st] = cleaned

    with open(DATA_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)

    print(f"Update complete! {modified_count:,} records updated across {len(unique_map)} unique street forms.")

if __name__ == '__main__':
    main()
