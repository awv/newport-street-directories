#!/usr/bin/env python3
"""
execute_second_tsv_review_fixes.py
Applies the 41 new review notes from the user's latest TSV export
and executes bulk normalization for streets ending in full stops/punctuation.
"""

import csv
import re
import shutil
import subprocess

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_second_tsv"

DROP_STREETS = {
    "b 4 102", "b 4 36", "123 and 124", "166, 167", "23-23a", "23a",
    "27 phillips memorial hall", "29", "29 30 seamen's institute",
    "29 unitarian meeting rm", "35-35a", "414", "7", "71, 72",
    "82 newport forward movement central hall", "9 county council offices"
}

EXACT_STREET_REMAP = {
    "beaufort terrace": "Beaufort Terrace",
    "beaufort terrace-": "Beaufort Terrace",
    "bishop street": "Bishop Street",
    "bishopgate parade": "Bishopgate Parade",
    "bachelor-road": "Bachelor Road",
    "bailey street b": "Bailey Street",
    "bailey street, d 5": "Bailey Street",
    "bailey street.": "Bailey Street",
    "bal": "Baldwin Street",
    "baldwin street.": "Bailey Street",
    "baldwin-street": "Baldwin Street",
    "baldwin-street": "Baldwin Street",
    "ban": "Baneswell Road",
    "baneswell road.": "Baneswell Road",
    "baneswell square.": "Baneswell Square",
    "baneswell road": "Baneswell Road",
    "banewell road": "Baneswell Road",
    "bank street.": "Bank Street",
    "barrack hill (continued)": "Barrack Hill",
    "barrack hill.": "Barrack Hill",
    "barrack lane.": "Barrack Lane",
    "bassalleg road": "Bassaleg Road",
    "bassalleg road.": "Bassaleg Road",
    "bat": "Batchelor Road",
    "bath street.": "Bath Street",
    "beechwood road. ch.": "Beechwood Road",
    "belgave place": "Belgrave Place",
    "belvue-lane": "Belle Vue Lane",
    "bellevue-lane": "Belle Vue Lane",
    "belvedere terrace.": "Belvedere Terrace",
    "belvidere terrace": "Belvedere Terrace",
    "belvidere terrace.": "Belvedere Terrace",
    "beynon's court": "Beynon's Court",
    "bis": "Bishop Street",
    "bishop street.": "Bishop Street",
    "aberthaw road. c.": "Aberthaw Road",
    "adeline street.": "Adeline Street",
    "alexandra dock.": "Alexandra Docks",
    "alderney street b 4 (west-side.)": "Alderney Street"
}

def clean_street(st):
    s = st.strip()
    # 1. Drop district paragraph headers
    if "barnard town, a district lying between" in s.lower():
        return None
    if s.lower() in DROP_STREETS:
        return None
        
    # 2. Check exact remap table
    s_lower = s.lower()
    if s_lower in EXACT_STREET_REMAP:
        return EXACT_STREET_REMAP[s_lower]
        
    # 3. Bulk trailing punctuation & full stop stripping
    # e.g., "Bishop Street." -> "Bishop Street", "Stow Hill," -> "Stow Hill"
    s_clean = re.sub(r'[\s\.\,\:\;\-]+$', '', s).strip()
    
    # 4. Strip map grid reference suffix, e.g. "Bailey Street, D 5" -> "Bailey Street"
    s_clean = re.sub(r'[\s\.\,]+[A-F]\s*\d+[a-z]?$', '', s_clean, flags=re.I).strip()
    
    # 5. Strip district suffix, e.g. "B.T.", "(B.T.)", "P.", "C."
    s_clean = re.sub(r'[\s\.\,]+\(?B\.?\s*T\.?\)?$', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'[\s\.\,]+\(?T\.?\s*W\.?\)?$', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'[\s\.\,]+\.?[A-Z]\.?$', '', s_clean).strip()
    
    return s_clean if s_clean else s

def run():
    print(f"Reading {DATA_CSV} to apply second batch of review fixes...")
    shutil.copy2(DATA_CSV, BACKUP_CSV)
    print(f"Backup created at {BACKUP_CSV}")

    rows = []
    fieldnames = []
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            rows.append(r)

    cleaned_rows = []
    dropped = 0
    modified = 0

    for r in rows:
        st = r.get("street", "").strip()
        cleaned_st = clean_street(st)

        if cleaned_st is None:
            dropped += 1
            continue

        if cleaned_st != st:
            modified += 1
            r["street"] = cleaned_st

        cleaned_rows.append(r)

    print(f"Total rows dropped: {dropped}")
    print(f"Total street names modified: {modified:,}")
    print(f"Remaining valid rows: {len(cleaned_rows):,}")

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print("\nRebuilding search indexes and statistics...")
    subprocess.run(["python3", "scripts/build_site_data.py"], check=True)
    subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)
    print("Second TSV review fixes successfully applied!")

if __name__ == "__main__":
    run()
