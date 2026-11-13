#!/usr/bin/env python3
"""
clean_trades_in_names.py
Comprehensive trade-in-name disentanglement script.
Cleans all occupational leaks in forenames and surnames across all directories.
"""

import csv
import re
import shutil
import subprocess

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_trade_cleanup"

ALL_HISTORICAL_TRADES = [
    'labourer', 'ironworker', 'carpenter', 'mason', 'g.w.r', 'gwr', 'fitter', 'haulier', 
    'clerk', 'painter', 'grocer', 'seaman', 'engine driver', 'tailor', 
    'butcher', 'trimmer', 'baker', 'engineer', 'plasterer', 'guard', 'moulder', 
    'gardener', 'foreman', 'boilermaker', 'fireman', 'builder', 'traveller', 
    'manager', 'hairdresser', 'coal trimmer', 'agent', 'blacksmith', 'greengrocer', 
    'bootmaker', 'signalman', 'shipwright', 'plumber', 'hobbler', 
    'platelayer', 'porter', 'bricklayer', 'rigger', 'shopkeeper', 'mariner', 
    'shoemaker', 'draper', 'steelworker', 'pilot', 'confectioner', 'postman', 
    'driver', 'sawyer', 'policeman', 'printer', 'sailor', 'solicitor', 'crane driver', 
    'mechanic', 'machinist', 'steward', 'assistant', 'stoker', 'joiner', 'striker', 
    'miller', 'tobacconist', 'dealer', 'salesman', 'fruiterer', 'caretaker', 
    'inspector', 'decorator', 'warehouseman', 'saddler', 'shunter', 'boatman', 
    'hoistman', 'milkman', 'insurance agent', 'cooper', 'dairyman', 
    'dock labourer', 'watchmaker', 'electrician', 'accountant', 'hawker', 
    'dressmaker', 'cabinetmaker', 'wheelwright', 'master mariner', 
    'docker', 'roller', 'furnaceman', 'chemist', 'engineman', 'motor driver', 
    'weighman', 'gasfitter', 'puddler', 'coal merchant', 'timekeeper', 'gasworker', 
    'newsagent', 'checker', 'sailmaker', 'coachman', 'compositor', 'stevedore', 
    'storekeeper', 'packer', 'outfitter', 'tinsmith', 'carman', 'surgeon', 
    'ostler', 'watchman', 'shearer', 'patternmaker', 'horseshoer',
    'fishmonger', 'upholsterer', 'nurse', 'currier', 'optician', 'stationer',
    'photographer', 'surveyor', 'dentist', 'ironmonger', 'pawnbroker',
    'auctioneer', 'milliner', 'publican', 'innkeeper', 'waiter', 'midwife',
    'telegraphist', 'typewriter', 'beer retailer', 'bottlemkr', 'bottle maker',
    'boot repairer', 'coal miner', 'collier', 'colliery worker', 'boot dealer'
]
ALL_HISTORICAL_TRADES.sort(key=len, reverse=True)

TRADE_EXACT_SET = {t.lower() for t in ALL_HISTORICAL_TRADES}
TRADE_SUFFIX_PATTERN = re.compile(
    r'^(.*?)[,.\s]+(' + '|'.join(re.escape(t) for t in ALL_HISTORICAL_TRADES) + r')$',
    re.IGNORECASE
)
TRADE_PREFIX_PATTERN = re.compile(
    r'^(' + '|'.join(re.escape(t) for t in ALL_HISTORICAL_TRADES) + r')[,.\s\—\-]+(.*?)$',
    re.IGNORECASE
)

# Protect legitimate surnames that happen to overlap with common occupational words
SURNAME_EXCLUSIONS = {
    'smith', 'cook', 'baker', 'taylor', 'carter', 'mason', 'gardner', 'gardener', 
    'miller', 'clark', 'clarke', 'turner', 'cooper', 'butler', 'shepherd', 
    'porter', 'fowler', 'potter', 'carpenter', 'driver', 'agent', 'guard'
}

def clean_record(row):
    fn = row.get("forename", "").strip()
    sn = row.get("surname", "").strip()
    tr = row.get("trade", "").strip()
    
    modified = False
    
    # --- 1. Forename is purely a trade word (e.g. fn='fishmonger', fn='upholsterer', fn='watchmaker') ---
    if fn.lower() in TRADE_EXACT_SET:
        trade_name = fn.title() if fn.lower() not in ('g.w.r', 'gwr') else 'G.W.R'
        # Check if surname contains multiple tokens, e.g. sn='Steel S' or sn='Lewis Thomas'
        sn_parts = sn.split()
        if len(sn_parts) >= 2:
            new_sn = sn_parts[0]
            new_fn = " ".join(sn_parts[1:])
            sn = new_sn
            fn = new_fn
        else:
            fn = ""
            
        if not tr:
            tr = trade_name
        elif trade_name.lower() not in tr.lower():
            tr = f"{trade_name} {tr}".strip()
            
        modified = True
        
    # --- 2. Forename ends with a trade suffix (e.g. 'Thomas Stoker', 'George Hoistman') ---
    elif fn:
        m_fn = TRADE_SUFFIX_PATTERN.match(fn)
        if m_fn:
            cand_fn = m_fn.group(1).strip(' ,.')
            cand_tr = m_fn.group(2).strip()
            if len(cand_fn) >= 2 and cand_fn.lower() not in ('the', 'and', 'for', 'mrs', 'miss'):
                if not tr:
                    tr = cand_tr.title() if cand_tr.lower() not in ('g.w.r', 'gwr') else 'G.W.R'
                elif cand_tr.lower() not in tr.lower():
                    tr = f"{tr}, {cand_tr}".strip(' ,')
                fn = cand_fn
                modified = True

    # --- 3. Surname line-bleed (suffix) (e.g. 'Rose Arthur J. platelayer', 'Cooke Wm. J. G.W.R') ---
    if sn and sn.lower() not in SURNAME_EXCLUSIONS:
        m_sn = TRADE_SUFFIX_PATTERN.match(sn)
        if m_sn:
            prefix = m_sn.group(1).strip(' ,.')
            cand_tr = m_sn.group(2).strip()
            parts = prefix.split()
            if len(parts) >= 2:
                new_sn = parts[0]
                new_fn = " ".join(parts[1:])
                if len(new_sn) >= 2 and new_sn.isalpha():
                    sn = new_sn
                    if not fn or fn == "—" or fn == new_fn or sn in fn:
                        fn = new_fn
                    if not tr:
                        tr = cand_tr.title() if cand_tr.lower() not in ('g.w.r', 'gwr') else 'G.W.R'
                    elif cand_tr.lower() not in tr.lower():
                        tr = f"{tr}, {cand_tr}".strip(' ,')
                    modified = True

        # --- 4. Surname line-bleed (prefix) (e.g. 'Cash & Co. bootmakers', 'Baker W. E., blacksmith Isitt') ---
        m_sn_pfx = TRADE_PREFIX_PATTERN.match(sn)
        if m_sn_pfx:
            cand_tr = m_sn_pfx.group(1).strip()
            remainder = m_sn_pfx.group(2).strip()
            # If cand_tr is not a protected surname (or preceded by words)
            if cand_tr.lower() not in SURNAME_EXCLUSIONS:
                if not tr:
                    tr = cand_tr.title() if cand_tr.lower() not in ('g.w.r', 'gwr') else 'G.W.R'
                elif cand_tr.lower() not in tr.lower():
                    tr = f"{cand_tr}, {tr}".strip(' ,')
                sn = remainder
                modified = True

    if modified:
        row["forename"] = fn
        row["surname"] = sn
        row["trade"] = tr
        
    return modified

def run():
    print(f"Reading {DATA_CSV} for trade-in-name disentanglement...")
    rows = []
    fieldnames = []
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            rows.append(r)
            
    print(f"Total rows read: {len(rows):,}")
    
    modified_count = 0
    for r in rows:
        if clean_record(r):
            modified_count += 1
            
    print(f"Total trade-in-name records repaired: {modified_count:,}")
    
    shutil.copy2(DATA_CSV, BACKUP_CSV)
    
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print("Updated data.csv successfully!")
    print("Rebuilding search indexes and statistics...")
    subprocess.run(["python3", "scripts/build_site_data.py"], check=True)
    subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)
    print("Trade-in-name cleanup complete!")

if __name__ == "__main__":
    run()
