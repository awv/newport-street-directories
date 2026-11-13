#!/usr/bin/env python3
"""
fix_reversed_names_global.py
-----------------------------
Corrects un-split / reversed personal names (e.g., 'Brown Sidney' -> 'Brown', 'Sidney'
and 'Merrett Mrs. Emma' -> 'Merrett', 'Mrs. Emma') across all historical directories.

Applies strict guards:
- Validates that forename parts are genuine forenames, abbreviations, or titles.
- Excludes businesses, institutions, partnerships, and streets.
- Preserves existing split names and initials.
"""

import csv
import re
import sys
import os
import shutil

csv.field_size_limit(sys.maxsize)

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_reversed_names_global"

TITLES = {
    'mr', 'mrs', 'miss', 'ms', 'dr', 'rev', 'capt', 'col', 'maj', 'major', 'sergt', 
    'father', 'fr', 'messrs', 'sir', 'lord', 'lady', 'prof', 'ald', 'alderman', 'councillor', 'cllr'
}

COMMON_FORENAMES = {
    'john', 'william', 'thomas', 'james', 'george', 'charles', 'henry', 'david', 'richard', 
    'robert', 'edward', 'frederick', 'albert', 'joseph', 'harry', 'frank', 'walter', 
    'harold', 'herbert', 'alfred', 'reginald', 'sidney', 'sydney', 'syd', 'leslie', 'horace', 
    'cyril', 'norman', 'stanley', 'clifford', 'ronald', 'leonard', 'victor', 'eric', 'kenneth', 
    'edwin', 'raymond', 'percival', 'percy', 'dennis', 'trevor', 'bernard', 'donald', 'brian', 
    'derek', 'gerald', 'graham', 'terence', 'anthony', 'alan', 'allan', 'colin', 'keith', 
    'gordon', 'malcolm', 'nevil', 'neville', 'stewart', 'stuart', 'barry', 'bryan', 'clive', 
    'douglas', 'geoffrey', 'jeffrey', 'nigel', 'peter', 'philip', 'roger', 'stephen', 'steven', 
    'ernest', 'arthur', 'samuel', 'benjamin', 'daniel', 'oscar', 'lawrence', 'francis', 
    'maurice', 'gilbert', 'godfrey', 'glyn', 'roy', 'desmond', 'valentine', 'ivan', 'ebenezer', 
    'michael', 'patrick', 'martin', 'clarence', 'russell', 'aubrey', 'lionel', 'rowland', 
    'laurence', 'julian', 'hubert', 'bertram', 'basil', 'wilfred', 'arnold', 'eynon', 'varney', 
    'sylgwyn', 'lyn', 'alun', 'bryn', 'ivor', 'gwilym', 'dillwyn', 'idris', 'hywel', 'geraint', 
    'rhys', 'gareth', 'emrys', 'tudor', 'mostyn', 'maldwyn', 'caradoc', 'wyn', 'wynne', 'wynford', 
    'arwyn', 'elvet', 'selwyn', 'owain', 'eirwyn', 'howard', 'bruce', 'doug', 'ian', 'neil', 
    'adrian', 'timothy', 'nicholas', 'paul', 'mark', 'simon', 'christopher', 'jonathan', 
    'andrew', 'matthew', 'adam', 'luke', 'gregory',
    # European / Italian forenames
    'vincenzo', 'luigi', 'antonio', 'giovanni', 'mario', 'carlo', 'giuseppe', 'domenico', 
    'francesco', 'salvatore', 'angelo', 'pietro', 'gaetano', 'gianni', 'renato', 'bruno', 
    'paolo', 'stefano', 'enrico', 'marco', 'massimo', 'alberto', 'roberto', 'sergio', 
    'andrea', 'luca', 'dino', 'aldo', 'enzo', 'giacomo', 'giorgio', 'claudio', 'vittorio', 
    'marcello', 'guido', 'silvio', 'franco', 'pasquale', 'raffaele', 'rocco', 'sandro', 'umberto',
    # Common abbreviations
    'thos', 'wm', 'jn', 'chas', 'edwd', 'geo', 'arth', 'hy', 'jas', 'albt', 'regnld', 'fredk', 
    'ernt', 'rt', 'rd', 'walt', 'herbt', 'alfd', 'sid', 'les', 'hor', 'cyr', 'norm', 
    'stan', 'cliff', 'ron', 'len', 'vic', 'ken', 'edw', 'ray', 'percevl', 'percev', 'den', 
    'trev', 'bern', 'don', 'bri', 'ger', 'gord', 'geoff', 'jeff', 'pete', 'phil', 'rog', 
    'steve', 'saml', 'fras', 'michl', 'danl', 'ebenzr', 'archbld', 'steph', 'christr', 'phlp', 
    'abrm', 'tim', 'dvd', 'stephn', 'reg', 'fred', 'bert', 'ern', 'davy', 'dave', 'bill', 
    'bob', 'jim', 'tom', 'dick', 'jack', 'ted', 'al', 'joe', 'jethro', 'eli', 'enoch', 'melbourne',
    # Female forenames & abbreviations
    'mary', 'elizabeth', 'florence', 'emily', 'margaret', 'doris', 'gladys', 'edith', 'alice', 
    'ethel', 'lilian', 'hilda', 'winifred', 'violet', 'mabel', 'ivy', 'rose', 'ellen', 'sarah', 
    'beatrice', 'dorothy', 'olive', 'gwen', 'blanche', 'vera', 'constance', 'marjorie', 
    'kathleen', 'eileen', 'phyllis', 'joan', 'marion', 'joyce', 'brenda', 'audrey', 'sheila', 
    'patricia', 'maureen', 'beryl', 'pamela', 'shirley', 'barbara', 'doreen', 'iris', 'norma', 
    'nellie', 'harriet', 'annie', 'dora', 'gwendoline', 'irene', 'sylvia', 'rhoda', 'evelyn', 
    'ann', 'jane', 'catherine', 'katharine', 'eunice', 'mair', 'megan', 'bronwen', 'olwen', 
    'gwyneth', 'rhiannon', 'carys', 'sian', 'dilys', 'eluned', 'myfanwy', 'ceinwen', 'eira', 
    'morfydd', 'enid', 'gwynedd', 'nesta', 'hettie', 'maggie', 'minnie', 'jessie', 'may', 
    'elsie', 'ada', 'grace', 'daisy', 'clara', 'laura', 'agnes', 'lottie', 'fanny', 'hannah', 
    'leah', 'rachel', 'ruth', 'susannah', 'martha', 'emma', 'madge', 'flossie', 'margt', 'mgt', 
    'dor', 'glad', 'eth', 'lil', 'win', 'vi', 'mabe', 'beatt', 'dot', 'ol', 'marj', 'kath', 
    'eil', 'phyl', 'pat', 'maur', 'pam', 'shirl', 'barb', 'dorn'
}

BUSINESS_EXTRA = {
    "&", " and ", "ltd", "limited", "co.", " co", "sons", "bros", "brothers", "club", "hotel", "inn", 
    "school", "hall", "presbytery", "market", "museum", "office", "yard", "depot", 
    "works", "proprietor", "secretary", "sec.", "trustees", "church", "chapel", 
    "hospital", "clinic", "wharf", "institute", "garage", "brewery", "bank", "corp", "corporation"
}

FORENAME_ABBRS = {
    "geo", "geo.", "jn", "jn.", "alfd", "alfd.", "wm", "wm.", "thos", "thos.", 
    "chas", "chas.", "edwd", "edwd.", "fredk", "fredk.", "arth", "arth.", "hy", "hy.", "jas", "jas.", "albt", "albt."
}

def is_forename_token(token):
    tok_clean = token.lower().rstrip('.,;')
    if tok_clean in COMMON_FORENAMES or tok_clean in TITLES:
        return True
    if re.match(r'^[A-Za-z]\.?$', token):
        return True
    return False

def is_initial(t):
    return bool(re.match(r'^[A-Za-z]\.?$', t))

def clean_token(t):
    return t.strip(' ,;')

def process_record(row):
    sn = (row.get("surname") or "").strip()
    fn = (row.get("forename") or "").strip()
    
    # Only process rows where forename is empty and surname contains multiple parts
    if fn or not sn or " " not in sn:
        return row, False
        
    low = sn.lower()
    if any(k in low for k in BUSINESS_EXTRA):
        return row, False
        
    parts = sn.split()
    if len(parts) < 2 or len(parts) > 5:
        return row, False
        
    # Ignore isolated forenames/initials (e.g. "Geo. A", "Jn. R")
    if parts[0].lower().rstrip(".,;") in FORENAME_ABBRS:
        return row, False

    # Case 1: Title first (e.g. "Mrs. Emma Merrett")
    if parts[0].lower().rstrip(".,;") in TITLES:
        if all(is_forename_token(p) for p in parts[:-1]):
            new_sn = clean_token(parts[-1])
            new_fn = clean_token(" ".join(parts[:-1]))
            if new_sn.lower() not in BUSINESS_EXTRA:
                row["surname"] = new_sn
                row["forename"] = new_fn
                return row, True
        return row, False

    # Case 2: Initials first (e.g. "W. H. Cowmeadow")
    if is_initial(parts[0]):
        split_idx = 1
        while split_idx < len(parts) and is_initial(parts[split_idx]):
            split_idx += 1
        rem = parts[split_idx:]
        if 1 <= len(rem) <= 2:
            new_sn = clean_token(" ".join(rem))
            new_fn = clean_token(" ".join(parts[:split_idx]))
            if not any(k in new_sn.lower() for k in BUSINESS_EXTRA):
                row["surname"] = new_sn
                row["forename"] = new_fn
                return row, True
        return row, False

    # Case 3: Surname first, all subsequent tokens are forename/initials/titles
    # (e.g. "Brown Sidney", "Merrett Mrs. Emma", "Davies T. G.", "Phillips Thos. J.")
    if all(is_forename_token(p) for p in parts[1:]):
        row["surname"] = clean_token(parts[0])
        row["forename"] = clean_token(" ".join(parts[1:]))
        return row, True

    return row, False

def main():
    if not os.path.exists(BACKUP_CSV):
        print(f"Creating safety backup: {BACKUP_CSV}...")
        shutil.copyfile(DATA_CSV, BACKUP_CSV)
    else:
        print(f"Backup already exists: {BACKUP_CSV}")

    print(f"Loading {DATA_CSV}...")
    rows = []
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            rows.append(r)

    print(f"Loaded {len(rows):,} records. Processing name splits & reversals...")
    
    fixed_count = 0
    by_year = {}
    
    for r in rows:
        r, changed = process_record(r)
        if changed:
            fixed_count += 1
            y = r.get("year", "UNKNOWN")
            by_year[y] = by_year.get(y, 0) + 1

    print(f"\nSuccessfully corrected {fixed_count:,} reversed/combined name records across the archive!")
    print("\nBreakdown by directory year:")
    for y in sorted(by_year.keys(), key=lambda x: int(x) if x.isdigit() else 9999):
        print(f"  {y}: {by_year[y]:,} records")

    print(f"\nWriting updated records back to {DATA_CSV}...")
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("data.csv update complete.")

if __name__ == "__main__":
    main()
