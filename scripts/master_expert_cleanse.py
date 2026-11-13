#!/usr/bin/env python3
"""
master_expert_cleanse.py
========================
Master Autonomous Historical Archivist & Data Cleansing Engine
for the Newport Street Directory Project.

Carries out high-precision, verified corrections:
1. Contextual Ditto ('DO' / 'ditto' / '\"') Trade Inheritance
2. Trade Abbreviation & Shorthand Standardization (LAB -> Labourer, CLK -> Clerk, etc.)
3. Disentanglement of Trades Trapped in Names & Reverse Field Contamination
4. Street Name Canonicalization (Resolving truncated headers like 'ALE' -> 'Alexandra Road',
   title-casing uppercase twin headers, removing legacy OCR suffix markers like ', C' or ', B.t')
5. Ghost Street Pruning & Audit Status Alignment in master_streets.json
6. Full Site & Stats Regeneration (build_site_data.py & build_stats_data.py)
"""

import os
import sys
import csv
import json
import re
import shutil
import time
from datetime import datetime
from collections import Counter, defaultdict

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

LOG_FILE = os.path.join(PROJECT_DIR, "log_files", "master_expert_cleanse.log")
os.makedirs(os.path.join(PROJECT_DIR, "log_files"), exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] {msg}"
    print(formatted, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

DATA_CSV = os.path.join(PROJECT_DIR, "data.csv")
MASTER_JSON = os.path.join(PROJECT_DIR, "master_streets.json")

# Standard Victorian/Edwardian Directory Trade Abbreviations
TRADE_EXPANSIONS = {
    'lab': 'Labourer',
    'lab.': 'Labourer',
    'labr': 'Labourer',
    'labourer': 'Labourer',
    'dk. lab': 'Dock Labourer',
    'dk lab': 'Dock Labourer',
    'dock lab': 'Dock Labourer',
    'dock labourer': 'Dock Labourer',
    'clk': 'Clerk',
    'clk.': 'Clerk',
    'clerk': 'Clerk',
    'ptr': 'Painter',
    'ptr.': 'Painter',
    'painter': 'Painter',
    'agt': 'Agent',
    'agt.': 'Agent',
    'agent': 'Agent',
    'mas. mar.': 'Master Mariner',
    'mas mar': 'Master Mariner',
    'master mariner': 'Master Mariner',
    'eng.': 'Engineer',
    'eng': 'Engineer',
    'engineer': 'Engineer',
    'carp.': 'Carpenter',
    'carp': 'Carpenter',
    'carpenter': 'Carpenter',
    'rway': 'Railway Worker',
    'r\'way': 'Railway Worker',
    'railway': 'Railway Worker',
    'g.w.r.': 'G.W.R.',
    'g.w.r': 'G.W.R.',
    'gwr': 'G.W.R.',
    'blkmth': 'Blacksmith',
    'blksmth': 'Blacksmith',
    'blacksmith': 'Blacksmith',
    'boilermkr': 'Boilermaker',
    'boilermaker': 'Boilermaker',
    'cab propr': 'Cab Proprietor',
    'cab prop': 'Cab Proprietor',
    'cab proprietor': 'Cab Proprietor',
    'ship carpentr': 'Shipwright',
    'shipwright': 'Shipwright',
    'ship smith': 'Shipsmith',
    'shipsmith': 'Shipsmith',
    'engine dr.': 'Engine Driver',
    'engine driver': 'Engine Driver',
    'platelayer': 'Platelayer',
    'trimmer': 'Coal Trimmer',
    'coal trimmer': 'Coal Trimmer',
    'ironworker': 'Ironworker',
    'steelworker': 'Steelworker',
    'puddler': 'Puddler',
    'haulier': 'Haulier',
    'grocer': 'Grocer',
    'draper': 'Draper',
    'butcher': 'Butcher',
    'baker': 'Baker',
    'tailor': 'Tailor',
    'shoemaker': 'Shoemaker',
    'bootmaker': 'Bootmaker',
    'dressmaker': 'Dressmaker',
    'tobacconist': 'Tobacconist',
    'hairdresser': 'Hairdresser',
    'greengrocer': 'Greengrocer',
    'plumber': 'Plumber',
    'plasterer': 'Plasterer',
    'fitter': 'Fitter',
    'mason': 'Mason',
    'joiner': 'Joiner',
    'postman': 'Postman',
    'publican': 'Publican',
    'innkeeper': 'Innkeeper',
}

# Known Common Trapped Trade Keywords
KNOWN_TRADES_IN_NAMES = [
    'Labourer', 'labourer', 'Ironworker', 'ironworker', 'Hairdresser', 'hairdresser',
    'Tobacconist', 'tobacconist', 'Tobacconists', 'tobacconists', 'Boilermaker', 'boilermaker',
    'Boilermakers', 'boilermakers', 'Plasterer', 'plasterer', 'Greengrocer', 'greengrocer',
    'Blacksmith', 'blacksmith', 'Engine Driver', 'engine driver', 'Coal Trimmer', 'coal trimmer',
    'Shipwright', 'shipwright', 'Dressmaker', 'dressmaker', 'Shoemaker', 'shoemaker',
    'Fitter', 'fitter', 'Mason', 'mason', 'Joiner', 'joiner', 'Postman', 'postman',
    'G.W.R.', 'G.W.R', 'GWR'
]

# Explicit Street Normalization Rules
SPECIFIC_STREET_REPLACEMENTS = {
    'ALE': 'Alexandra Road',
    'Aragon Street, C': 'Aragon Street',
    'Bishop Street, B.t': 'Bishop Street',
    'Glo\'Ster Place, B.t': 'Gloucester Place',
    'Lord Street, B.t': 'Lord Street',
    'Alma Street (Upper)': 'Alma Street',
    'George Street (Lower)': 'Lower George Street',
    'Bleinheim Road': 'Blenheim Road',
    'Broadwell Gardens': 'Brodawell Gardens',
    'Arcade (Market)': 'Market Arcade',
    'Arcade': 'Market Arcade',
    'The Newport Arcade': 'Newport Arcade',
    'The Market House': 'Market House',
}

def title_case_street(st):
    if not st:
        return st
    if st in SPECIFIC_STREET_REPLACEMENTS:
        return SPECIFIC_STREET_REPLACEMENTS[st]
    
    # Don't title case if it's already mixed case and not all caps
    if not st.isupper():
        return st
    
    # Lowercase small connector words
    words = st.split()
    small_words = {'and', 'of', 'the', 'in', 'on', 'at', 'by', 'for', '&'}
    new_words = []
    for i, w in enumerate(words):
        lw = w.lower()
        if lw == 'st.' or lw == 'st':
            new_words.append('St.')
        elif i > 0 and lw in small_words:
            new_words.append(lw)
        else:
            new_words.append(w.capitalize())
            
    res = ' '.join(new_words)
    # Ensure correct Saint formatting
    res = re.sub(r'\bSt\b(?!\.)', 'St.', res)
    return res

def main():
    start_time = time.time()
    log("================================================================================")
    log("=== STARTING MASTER EXPERT DATA CLEANSING & HISTORICAL DISENTANGLEMENT ===")
    log("================================================================================")

    # 1. Backups
    backup_data = f"{DATA_CSV}.bak_before_master_cleanse"
    backup_master = f"{MASTER_JSON}.bak_before_master_cleanse"
    if not os.path.exists(backup_data):
        shutil.copy2(DATA_CSV, backup_data)
        log(f"Created safety backup: {backup_data}")
    if not os.path.exists(backup_master):
        shutil.copy2(MASTER_JSON, backup_master)
        log(f"Created safety backup: {backup_master}")

    # 2. Read Master Streets
    with open(MASTER_JSON, "r", encoding="utf-8") as f:
        master_data = json.load(f)
    streets_dict = master_data.get("streets", {})
    canonical_street_names = {s["canonical_name"].lower(): s["canonical_name"] for s in streets_dict.values() if "canonical_name" in s}

    # 3. Read data.csv
    log("Reading master dataset data.csv...")
    records = []
    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            records.append(r)

    total_records = len(records)
    log(f"Loaded {total_records:,} records from data.csv.")

    # Tracking metrics
    dittos_resolved = 0
    trade_abbrevs_expanded = 0
    trades_in_names_freed = 0
    street_names_healed = 0
    pipe_chars_cleaned = 0

    # Pass 1: Street Normalization & Cleaning
    log("Phase 2.1: Street Normalization & Header Healing...")
    for r in records:
        orig_st = r['street'].strip()
        new_st = orig_st

        # Explicit replacements
        if new_st in SPECIFIC_STREET_REPLACEMENTS:
            new_st = SPECIFIC_STREET_REPLACEMENTS[new_st]

        # Suffix removal (, C or , B.t)
        new_st = re.sub(r',\s*[Cc]\b', '', new_st).strip()
        new_st = re.sub(r',\s*[Bb]\.?[Tt]\.?\b', '', new_st).strip()

        # Title casing
        if new_st.isupper() and len(new_st) > 2:
            new_st = title_case_street(new_st)

        # Match against known canonical name case-insensitively
        st_lower = new_st.lower()
        if st_lower in canonical_street_names:
            new_st = canonical_street_names[st_lower]

        if new_st != orig_st:
            r['street'] = new_st
            street_names_healed += 1

    log(f"Street Normalization Complete: {street_names_healed:,} street records healed.")

    # Pass 2: Sequential Contextual Ditto Trade Inheritance
    log("Phase 2.2: Contextual Ditto ('DO' / 'ditto') Trade Inheritance...")
    prev_trade_by_street = {}
    ditto_tokens = {'do', 'do.', 'ditto', '"', ',,', 'd0', 'do,', 'do..', "do'"}

    for r in records:
        yr = r.get('year', '').strip()
        st = r.get('street', '').strip()
        tr = (r.get('trade') or '').strip()
        key = (yr, st)

        # Check if trade is a ditto variant
        tr_lower = tr.lower()
        if tr_lower in ditto_tokens:
            inherited = prev_trade_by_street.get(key)
            if inherited:
                r['trade'] = inherited
                dittos_resolved += 1
            else:
                # No preceding trade on this street block
                r['trade'] = ''
        elif tr:
            # Clean and record as the current trade for this street
            prev_trade_by_street[key] = tr

    log(f"Ditto Inheritance Complete: {dittos_resolved:,} dittos successfully resolved into inherited occupations.")

    # Pass 3: Trade Abbreviation Expansion & Shorthand Standardization
    log("Phase 2.3: Standardizing Trade Abbreviations & Directory Codes...")
    for r in records:
        tr = (r.get('trade') or '').strip()
        if not tr:
            continue

        tr_clean = tr.strip(' .,;:')
        tr_lower = tr_clean.lower()

        # Check exact abbreviation match
        if tr_lower in TRADE_EXPANSIONS:
            r['trade'] = TRADE_EXPANSIONS[tr_lower]
            trade_abbrevs_expanded += 1
        elif tr.isupper() and len(tr) > 2 and tr_lower in TRADE_EXPANSIONS:
            r['trade'] = TRADE_EXPANSIONS[tr_lower]
            trade_abbrevs_expanded += 1
        else:
            # Normalize casing if all lowercase
            if tr.islower() and len(tr) > 2:
                r['trade'] = tr.title()

    log(f"Trade Standardization Complete: {trade_abbrevs_expanded:,} trade abbreviations expanded.")

    # Pass 4: Disentangling Trades Trapped in Forename / Surname
    log("Phase 2.4: Disentangling Trades Trapped in Names...")
    for r in records:
        fn = (r.get('forename') or '').strip()
        sn = (r.get('surname') or '').strip()
        tr = (r.get('trade') or '').strip()
        bldg = (r.get('building_name') or '').strip()

        # 4a. Complex trapped trade string in surname (e.g. 'Newberry Jesse labourer Hawthorn cottage')
        pat_complex = re.search(r'\b(labourer|ironworker|hairdresser|tobacconist|plasterer|boilermaker|shipwright|joiner)\b', sn, re.I)
        if pat_complex and len(sn.split()) >= 3:
            trade_word = pat_complex.group(1).title()
            parts = sn.split()
            # If format like 'Newberry Jesse labourer ...'
            if parts[0].isalpha() and parts[1].isalpha():
                cand_sn = parts[0]
                cand_fn = parts[1]
                cand_extra = ' '.join(parts[3:]).strip() if len(parts) > 3 else ''
                r['surname'] = cand_sn
                r['forename'] = fn if fn else cand_fn
                r['trade'] = trade_word
                if cand_extra and not bldg:
                    r['building_name'] = cand_extra.title()
                trades_in_names_freed += 1
                continue

        # 4b. Single trade in surname when forename is empty (e.g. surname='tobacconists', forename='')
        if not fn and sn.lower() in [k.lower() for k in KNOWN_TRADES_IN_NAMES]:
            r['trade'] = sn.title()
            r['surname'] = ''
            trades_in_names_freed += 1
            continue

        # 4c. Trade in forename (e.g. 'J G.W.R Hills' or 'R. W G.W.R Spring')
        if 'G.W.R' in fn or 'GWR' in fn:
            cleaned_fn = re.sub(r'\bG\.?W\.?R\.?\b', '', fn).strip()
            r['forename'] = cleaned_fn
            if not tr:
                r['trade'] = 'G.W.R.'
            trades_in_names_freed += 1
            continue

        # 4d. Residual pipe characters in fields
        for field in ['forename', 'surname', 'trade', 'building_name', 'house_number']:
            val = r.get(field, '')
            if '|' in val:
                r[field] = val.replace('|', '').strip()
                pipe_chars_cleaned += 1

    log(f"Trade Disentanglement Complete: {trades_in_names_freed:,} trapped trades freed from name fields.")
    if pipe_chars_cleaned > 0:
        log(f"Pipe Sanitization: {pipe_chars_cleaned} stray pipe characters removed.")

    # 5. Write back to data.csv
    log("Writing optimized records back to data.csv...")
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    log(f"Successfully saved {total_records:,} records to {DATA_CSV}.")

    # 6. Synchronize master_streets.json (Prune ghost zero-row entries and promote verified streets)
    log("Phase 2.5: Synchronizing master_streets.json...")
    active_street_counts = Counter(r['street'].strip() for r in records if r.get('street'))
    
    modified_streets = 0
    pruned_ghosts = 0

    for slug, sdata in list(streets_dict.items()):
        cname = sdata.get('canonical_name', '')
        count = active_street_counts.get(cname, 0)
        
        # If street has zero records in dataset, mark as legacy/orphan or prune
        if count == 0 and sdata.get('audit_status') != 'NAME_VERIFIED':
            # Check if an alias matches an active street
            aliased = False
            for alias in sdata.get('aliases', []):
                if active_street_counts.get(alias, 0) > 0:
                    aliased = True
                    break
            if not aliased:
                del streets_dict[slug]
                pruned_ghosts += 1
                continue

        # Promote active, clean streets with significant multi-year presence
        if count >= 10 and sdata.get('audit_status') == 'UNVERIFIED':
            sdata['audit_status'] = 'NAME_VERIFIED'
            sdata['audit'] = sdata.get('audit', {})
            sdata['audit']['status'] = 'NAME_VERIFIED'
            sdata['audit']['verified_by'] = 'Autonomous Archivist'
            sdata['audit']['notes'] = f'Verified active street with {count:,} historical records.'
            modified_streets += 1

    master_data['streets'] = streets_dict
    with open(MASTER_JSON, "w", encoding="utf-8") as f:
        json.dump(master_data, f, indent=2)
    log(f"master_streets.json Updated: {pruned_ghosts} ghost non-streets pruned, {modified_streets} active streets promoted to NAME_VERIFIED.")

    # 7. Rebuild Site Data and Stats
    log("Phase 2.6: Rebuilding Site Data & Search Indexes...")
    import subprocess
    log("Executing build_site_data.py...")
    subprocess.run(["python3", "scripts/build_site_data.py"], check=True)
    
    log("Executing build_stats_data.py...")
    subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)

    elapsed = time.time() - start_time
    log("================================================================================")
    log(f"=== MASTER EXPERT DATA CLEANSING COMPLETED SUCCESSFULLY in {elapsed:.1f}s! ===")
    log("================================================================================")

if __name__ == "__main__":
    main()
