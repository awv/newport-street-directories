#!/usr/bin/env python3
import csv
import re
import shutil
from pathlib import Path

DATA_CSV = Path("/Users/robgale/Documents/Newport Street Directory Project/data.csv")
BACKUP_CSV = Path("/Users/robgale/Documents/Newport Street Directory Project/data.csv.bak_before_continued_sweep")

pattern = re.compile(r'[\s\-—–_\[\(]+(cont(?:inued|[\'’]d|d|\.?))[\]\)]*[\.\s]*$', re.IGNORECASE)

KNOWN_OVERRIDES = {
    'newport street list. (continued)': 'Windsor Terrace',
    'altyn-continued': 'Allt-yr-yn',
    'wharves (the)—continued': 'Wharves',
    'wharves—continued': 'Wharves',
    'wharves-continued': 'Wharves',
    'wharves (continued)': 'Wharves',
    'dos-road continued': 'Dos Road',
    'dos road contd': 'Dos Road',
    'court-y-bella terrace (cont)': 'Courtybella Terrace',
    "alexandra docks (cont'd)": 'Alexandra Docks',
    "alexandra docks-cont'd": 'Alexandra Docks',
    'withey bed (continued)': 'Withey Bed',
    'crindau—continued': 'Crindau',
    'st edward street-cont': 'St. Edward Street',
    'tunnel terrace—continued': 'Tunnel Terrace'
}

def clean_continued_name(raw):
    raw_low = raw.strip().lower()
    if raw_low in KNOWN_OVERRIDES:
        return KNOWN_OVERRIDES[raw_low]
        
    cl = pattern.sub('', raw).strip()
    cl = re.sub(r'[\.\,\:\;\-]+$', '', cl).strip()
    
    # If hyphenated: e.g. Redland-street, Dolphin-street, Caerleon-road, Stow-hill
    if '-' in cl and any(cl.lower().endswith(x) for x in ['-street', '-road', '-place', '-terrace', '-lane', '-avenue', '-parade', '-hill']):
        parts = cl.split('-')
        cl = ' '.join(parts)
        
    # Expand abbreviations
    cl = re.sub(r'\bst\.?$', 'Street', cl, flags=re.I)
    cl = re.sub(r'\brd\.?$', 'Road', cl, flags=re.I)
    cl = re.sub(r'\bpar\.?$', 'Parade', cl, flags=re.I)
    cl = re.sub(r'\bave\.?$', 'Avenue', cl, flags=re.I)

    # Clean title case
    words = cl.split()
    title_words = []
    for w in words:
        if w.lower() in ['and', '&', 'of', 'the']:
            title_words.append(w.lower())
        elif "'" in w:
            p = w.split("'")
            title_words.append(p[0].capitalize() + "'" + p[1].lower())
        elif '-' in w:
            p = w.split('-')
            title_words.append('-'.join(x.capitalize() for x in p))
        else:
            title_words.append(w.capitalize())
    res = ' '.join(title_words)
    if res:
        res = res[0].upper() + res[1:]
    return res

def main():
    print(f"Backing up {DATA_CSV} -> {BACKUP_CSV}...")
    shutil.copy2(DATA_CSV, BACKUP_CSV)

    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

    modified_count = 0
    unique_replacements = {}

    for r in reader:
        st = r.get("street", "").strip()
        if "cont" in st.lower():
            target = clean_continued_name(st)
            if target != st:
                r["street"] = target
                modified_count += 1
                unique_replacements[st] = target

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)

    print(f"Sweep complete!")
    print(f"  - Total records updated: {modified_count:,}")
    print(f"  - Unique header variants cleaned: {len(unique_replacements)}")

if __name__ == "__main__":
    main()
