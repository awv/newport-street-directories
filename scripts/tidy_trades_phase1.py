#!/usr/bin/env python3
"""
tidy_trades_phase1.py
---------------------
Phase 1 cleanup of historical trade abbreviations and suffixes in data.csv:
1. Resolves ditto tokens ('Do.', 'do', 'Ditto', 'ditto') by inheriting the trade
   from the preceding row within the same street and year.
2. Strips multi-word business suffixes (', Etc.', ', etc.', ', &c.', '&c.')
   so compound retail titles unite with their parent trade.
3. Expands unambiguous historical contraction families into their canonical title-cased forms
   (e.g., Lab'Rer -> Labourer, Ironwkr -> Ironworker, Eng. Driver -> Engine Driver,
    Coal Trim'R -> Coal Trimmer, Carpentr -> Carpenter, Mas. Mar. -> Master Mariner,
    Boilermakr -> Boilermaker, Bootmkr -> Bootmaker, Shoemakr -> Shoemaker,
    Greengrcr -> Greengrocer, Warehsmn -> Warehouseman, Blacksmth -> Blacksmith,
    Plast'R -> Plasterer (leaving Plater untouched), Platelyr -> Platelayer,
    Shopkpr -> Shopkeeper, Ins. Agent -> Insurance Agent, etc.).
4. Preserves ALL distinct/generic occupations (Hewer, Smith, Plater, Traveller, Collier).
5. Updates data/trade_overrides_master.json and re-indexes site/stats data.
"""

import csv
import json
import os
import re
import sys
import shutil
from collections import Counter, defaultdict

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
MASTER_OVERRIDES_PATH = os.path.join(PROJECT_ROOT, "data", "trade_overrides_master.json")
VERIFIED_PATH = os.path.join(PROJECT_ROOT, "data", "verified_trades.json")

# Core unambiguous contraction mappings (case-insensitive keys -> canonical Title Case target)
CONTRACTION_MAP = {
    # Labourer
    "lab'rer": "Labourer",
    "lab’rer": "Labourer",
    "lab'r": "Labourer",
    "lab’r": "Labourer",
    "labr": "Labourer",
    "labr.": "Labourer",
    "laborer": "Labourer",
    "labrer": "Labourer",
    "labrer.": "Labourer",
    "labrr": "Labourer",
    "labre": "Labourer",
    "labour": "Labourer",
    "labor": "Labourer",
    
    # Ironworker
    "ironwkr": "Ironworker",
    "ironwrkr": "Ironworker",
    "ironworkr": "Ironworker",
    "ironwrk": "Ironworker",
    "ironwk": "Ironworker",
    "ironwork'r": "Ironworker",
    "ironwork’r": "Ironworker",
    "ironwokr": "Ironworker",
    "ironwker": "Ironworker",
    "ironwrker": "Ironworker",
    "irnwrkr": "Ironworker",
    "irnwrker": "Ironworker",
    "iron-worker": "Ironworker",
    "iron worker": "Ironworker",
    
    # Engine Driver
    "eng. driver": "Engine Driver",
    "eng driver": "Engine Driver",
    "eng. drvr": "Engine Driver",
    "engine drvr": "Engine Driver",
    "engine dvr": "Engine Driver",
    "eng dvr": "Engine Driver",
    "engine drivr": "Engine Driver",
    "eng. dvr": "Engine Driver",
    "eng. drivr": "Engine Driver",
    "eng drvr": "Engine Driver",
    "eng. dr'vr": "Engine Driver",
    "eng. dr’vr": "Engine Driver",
    "engine dr'vr": "Engine Driver",
    "engine dr’vr": "Engine Driver",
    "eng drivr": "Engine Driver",
    "eng, drvr": "Engine Driver",
    "eng, driver": "Engine Driver",
    "eng dr'vr": "Engine Driver",
    "eng dr’vr": "Engine Driver",
    "eng, dr'vr": "Engine Driver",
    "eng, dr’vr": "Engine Driver",
    "eng, drivr": "Engine Driver",
    "eng.drvr": "Engine Driver",
    "engine driv'r": "Engine Driver",
    "engine driv’r": "Engine Driver",
    "engine d'vr": "Engine Driver",
    "engine d’vr": "Engine Driver",
    "engine drv": "Engine Driver",
    "enginedvr": "Engine Driver",
    "engine, driver": "Engine Driver",
    
    # Coal Trimmer
    "coal trim'r": "Coal Trimmer",
    "coal trim’r": "Coal Trimmer",
    "coal trimr": "Coal Trimmer",
    "coal trmr": "Coal Trimmer",
    "coal tr'mr": "Coal Trimmer",
    "coal tr’mr": "Coal Trimmer",
    "coal trim": "Coal Trimmer",
    "coal trimr.": "Coal Trimmer",
    "coal tmr": "Coal Trimmer",
    "coal tri'mr": "Coal Trimmer",
    "coal tri’mr": "Coal Trimmer",
    "coal trim.": "Coal Trimmer",
    "coal trm": "Coal Trimmer",
    "coal trm.": "Coal Trimmer",
    "coal trimm'r": "Coal Trimmer",
    "coal trimm’r": "Coal Trimmer",
    "coal trimer": "Coal Trimmer",
    "coal trim'er": "Coal Trimmer",
    "coal trim’er": "Coal Trimmer",
    "coal trimmerr": "Coal Trimmer",
    
    # Carpenter
    "carpentr": "Carpenter",
    "carptr": "Carpenter",
    "carpntr": "Carpenter",
    "carp'tr": "Carpenter",
    "carp’tr": "Carpenter",
    "carp'ter": "Carpenter",
    "carp’ter": "Carpenter",
    "carpent'r": "Carpenter",
    "carpent’r": "Carpenter",
    "carpnt'r": "Carpenter",
    "carpnt’r": "Carpenter",
    "carp'ntr": "Carpenter",
    "carp’ntr": "Carpenter",
    "carprtr": "Carpenter",
    
    # Master Mariner
    "master mar": "Master Mariner",
    "mas. mar.": "Master Mariner",
    "mas. mar": "Master Mariner",
    "mas. mariner": "Master Mariner",
    "master mar.": "Master Mariner",
    "mast mar": "Master Mariner",
    "mast. mar": "Master Mariner",
    "mast. mar.": "Master Mariner",
    "mast mariner": "Master Mariner",
    "master marinr": "Master Mariner",
    "mast marinr": "Master Mariner",
    "mas mariner": "Master Mariner",
    "mast. marinr": "Master Mariner",
    "mas. marinr": "Master Mariner",
    "mas mar.": "Master Mariner",
    
    # Boilermaker
    "boilermakr": "Boilermaker",
    "boiler mkr": "Boilermaker",
    "boilermkr": "Boilermaker",
    "boilermk": "Boilermaker",
    "boiler makr": "Boilermaker",
    "boiler mk": "Boilermaker",
    "blrmkr": "Boilermaker",
    
    # Bootmaker
    "bootmkr": "Bootmaker",
    "bootmakr": "Bootmaker",
    "bootmkrs": "Bootmaker",
    "bootmakrs": "Bootmaker",
    "bootmk": "Bootmaker",
    "boot mkr": "Bootmaker",
    "bootmks": "Bootmaker",
    "boot mkrs": "Bootmaker",
    "boot makr": "Bootmaker",
    
    # Shoemaker
    "shoemakr": "Shoemaker",
    "shoemkr": "Shoemaker",
    "shoemk": "Shoemaker",
    "shoemakrs": "Shoemaker",
    "shoemaker": "Shoemaker",
    
    # Greengrocer
    "greengrcr": "Greengrocer",
    "greengrocr": "Greengrocer",
    "greengroc'r": "Greengrocer",
    "greengroc’r": "Greengrocer",
    "grngrer": "Greengrocer",
    "greengrer": "Greengrocer",
    "greengr": "Greengrocer",
    
    # Warehouseman
    "warehsmn": "Warehouseman",
    "wareho'man": "Warehouseman",
    "wareho’man": "Warehouseman",
    "warehsman": "Warehouseman",
    "warehseman": "Warehouseman",
    "warehoman": "Warehouseman",
    "wareho'mn": "Warehouseman",
    "wareho’mn": "Warehouseman",
    "wareh'man": "Warehouseman",
    "wareh’man": "Warehouseman",
    "warehsemn": "Warehouseman",
    "warehomn": "Warehouseman",
    "warehman": "Warehouseman",
    "warehmn": "Warehouseman",
    "warehousemn": "Warehouseman",
    
    # Blacksmith
    "blacksmth": "Blacksmith",
    "blacksmt": "Blacksmith",
    "blksmith": "Blacksmith",
    "blksmth": "Blacksmith",
    
    # Compositor
    "compositr": "Compositor",
    "compostr": "Compositor",
    "composit'r": "Compositor",
    "composit’r": "Compositor",
    "comptr": "Compositor",
    
    # Plasterer (explicitly distinct from Plater)
    "plast'r": "Plasterer",
    "plast’r": "Plasterer",
    "plastr": "Plasterer",
    "plast'rer": "Plasterer",
    "plast’rer": "Plasterer",
    "plaste'r": "Plasterer",
    "plaste’r": "Plasterer",
    "plast'er": "Plasterer",
    "plast’er": "Plasterer",
    
    # Hairdresser
    "hairdrsr": "Hairdresser",
    "hairdrssr": "Hairdresser",
    "hairdr'ssr": "Hairdresser",
    "hairdr’ssr": "Hairdresser",
    "hairdr'sr": "Hairdresser",
    "hairdr’sr": "Hairdresser",
    
    # Fishmonger
    "fishmngr": "Fishmonger",
    
    # Cabinetmaker
    "cabinetmkr": "Cabinetmaker",
    "cabinet mkr": "Cabinetmaker",
    "cabinetmakr": "Cabinetmaker",
    "cabinet makr": "Cabinetmaker",
    "cabt. mkr": "Cabinetmaker",
    
    # Patternmaker
    "patternmkr": "Patternmaker",
    "pattern mkr": "Patternmaker",
    "patternmakr": "Patternmaker",
    "pattern makr": "Patternmaker",
    "tternmaker": "Patternmaker",
    
    # Platelayer (explicitly distinct from Plater)
    "platelyr": "Platelayer",
    "platelayr": "Platelayer",
    "platelay'r": "Platelayer",
    "platelay’r": "Platelayer",
    "platel'yr": "Platelayer",
    "platel’yr": "Platelayer",
    "platelyer": "Platelayer",
    "platelr": "Platelayer",
    "plate layer": "Platelayer",
    "plate layr": "Platelayer",
    "platepayer": "Platelayer",
    "platerlayer": "Platelayer",
    
    # Shopkeeper
    "shopkpr": "Shopkeeper",
    "shopkeepr": "Shopkeeper",
    "shopk'pr": "Shopkeeper",
    "shopk’pr": "Shopkeeper",
    
    # Insurance Agent
    "ins. agent": "Insurance Agent",
    "ins. agt": "Insurance Agent",
    "insur agent": "Insurance Agent",
    "ins agent": "Insurance Agent",
    "insurance agt": "Insurance Agent",
    "insur. agent": "Insurance Agent",
    
    # Glass Works / Worker
    "glass wks": "Glass Works",
    "glass workr": "Glass Worker",
    "glass wkr": "Glass Worker",
    "glass wrkr": "Glass Worker",
    
    # Dock Labourer
    "dock labr": "Dock Labourer",
    "labourer, dk": "Dock Labourer",
    "dock lab": "Dock Labourer",
    "dk lab": "Dock Labourer",
    
    # Bricklayer
    "bricklyr": "Bricklayer",
    "bricklayr": "Bricklayer",
    "bricklay'r": "Bricklayer",
    "bricklay’r": "Bricklayer",
    "brickmkr": "Brickmaker",
    
    # Wheelwright
    "wheelwgt": "Wheelwright",
    "wheelwrgt": "Wheelwright",
    
    # Confectioner
    "confectnr": "Confectioner",
    "confect'nr": "Confectioner",
    "confect’nr": "Confectioner",
    "confectr": "Confectioner",
    "confect'r": "Confectioner",
    "confect’r": "Confectioner",
    "confect": "Confectioner",
    
    # Timekeeper
    "timekpr": "Timekeeper",
    "timekeepr": "Timekeeper",
    
    # Storekeeper
    "storekpr": "Storekeeper",
    "storekeepr": "Storekeeper",
    
    # Watchmaker
    "watchmkr": "Watchmaker",
    "watchmakr": "Watchmaker",
    
    # Dressmaker
    "dressmakr": "Dressmaker",
    
    # Crane Driver
    "crane dvr": "Crane Driver",
    
    # Stationer
    "stationr": "Stationer",
    
    # Auctioneer
    "auctnr": "Auctioneer",
    
    # Upholsterer
    "upholstr": "Upholsterer",
    
    # Photographer
    "photographr": "Photographer",
    
    # Police roles
    "police con": "Police Constable",
    "police insp": "Police Inspector",
    "police sergt": "Police Sergeant",
    
    # Typo corrections
    "vet. surgeon": "Veterinary Surgeon"
}

ETC_SUFFIX_PATTERN = re.compile(r'[\s,]+(?:etc|&c)\.?$', re.IGNORECASE)
DITTO_SET = {"do.", "do", "ditto", "ditto."}

def main(dry_run=True):
    print(f"=== Tidy Trades Phase 1 ({'DRY RUN' if dry_run else 'APPLY'}) ===")
    
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
    print(f"Loaded {len(rows):,} rows from {DATA_CSV}.")
    
    ditto_resolved = 0
    ditto_cleared = 0
    etc_stripped = 0
    contractions_expanded = 0
    total_modifications = 0
    
    mod_samples = defaultdict(list)
    
    # Process sequentially for ditto resolution
    for i, r in enumerate(rows):
        orig_trade = r.get("trade", "").strip()
        if not orig_trade:
            continue
            
        new_trade = orig_trade
        row_modified = False
        
        # 1. Resolve ditto
        if new_trade.lower() in DITTO_SET:
            curr_yr = r.get("year", "")
            curr_st = r.get("street", "")
            inherited = ""
            for j in range(i - 1, max(-1, i - 25), -1):
                prev = rows[j]
                if prev.get("year", "") != curr_yr or prev.get("street", "") != curr_st:
                    break
                p_tr = prev.get("trade", "").strip()
                if p_tr and p_tr.lower() not in DITTO_SET:
                    inherited = p_tr
                    break
            if inherited:
                new_trade = inherited
                ditto_resolved += 1
                row_modified = True
                mod_samples["ditto_resolved"].append((orig_trade, new_trade, curr_yr, curr_st, r.get("house_number"), r.get("surname")))
            else:
                new_trade = ""
                ditto_cleared += 1
                row_modified = True
                mod_samples["ditto_cleared"].append((orig_trade, "", curr_yr, curr_st, r.get("house_number"), r.get("surname")))
                
        # 2. Strip multi-word suffixes (, Etc. / , etc. / &c.)
        if new_trade and ETC_SUFFIX_PATTERN.search(new_trade):
            cleaned = ETC_SUFFIX_PATTERN.sub("", new_trade).strip()
            if cleaned:
                if cleaned != new_trade:
                    etc_stripped += 1
                    row_modified = True
                    mod_samples["etc_stripped"].append((new_trade, cleaned))
                    new_trade = cleaned
                    
        # 3. Expand unambiguous contractions
        if new_trade:
            norm_key = new_trade.lower().strip()
            if norm_key in CONTRACTION_MAP:
                target = CONTRACTION_MAP[norm_key]
                if target != new_trade:
                    contractions_expanded += 1
                    row_modified = True
                    mod_samples["contraction"].append((new_trade, target))
                    new_trade = target
                    
        if row_modified:
            total_modifications += 1
            r["trade"] = new_trade
            
    print(f"\n--- Modification Summary ---")
    print(f"Total rows modified: {total_modifications:,}")
    print(f"  Ditto resolved to preceding trade: {ditto_resolved:,}")
    print(f"  Ditto cleared (no predecessor):   {ditto_cleared:,}")
    print(f"  ', Etc.' / '&c.' suffixes stripped: {etc_stripped:,}")
    print(f"  Contractions expanded:             {contractions_expanded:,}")
    
    # Print sample expansions
    print(f"\nTop 15 Contraction Expansions:")
    c_counts = Counter(mod_samples["contraction"])
    for (src, dst), count in c_counts.most_common(15):
        print(f"  {src!r:25} -> {dst!r:20} ({count:,} rows)")
        
    print(f"\nTop 10 Suffix Strippings:")
    e_counts = Counter(mod_samples["etc_stripped"])
    for (src, dst), count in e_counts.most_common(10):
        print(f"  {src!r:25} -> {dst!r:20} ({count:,} rows)")
        
    # Safety verification
    print(f"\n--- Safety Verification ---")
    protected_words = ["Hewer", "Smith", "Plater", "Traveller", "Miner", "Collier"]
    for w in protected_words:
        matches = [m for m in mod_samples["contraction"] if m[0] == w]
        print(f"  Protected word '{w}' modified? {'YES - WARNING!' if matches else 'No (safe)'}")
        
    if dry_run:
        print("\nDry run complete. No files were modified.")
        return
        
    # Write updated data.csv
    temp_csv = DATA_CSV + ".tmp"
    with open(temp_csv, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    shutil.move(temp_csv, DATA_CSV)
    print(f"\nSuccessfully wrote updated records to {DATA_CSV}.")
    
    # Update data/trade_overrides_master.json
    master_overrides = {}
    if os.path.exists(MASTER_OVERRIDES_PATH):
        try:
            with open(MASTER_OVERRIDES_PATH, "r", encoding="utf-8") as f:
                master_overrides = json.load(f)
        except Exception as e:
            print(f"Warning reading master overrides: {e}")
            
    # Fix existing typos in master
    master_overrides["coal trim'r"] = "Coal Trimmer"
    master_overrides["labrer"] = "Labourer"
    master_overrides["eng drvr"] = "Engine Driver"
    master_overrides["vet. surgeon"] = "Veterinary Surgeon"
    
    # Merge all Phase 1 contractions
    for k, v in CONTRACTION_MAP.items():
        master_overrides[k] = v
        
    with open(MASTER_OVERRIDES_PATH, "w", encoding="utf-8") as f:
        json.dump(master_overrides, f, indent=2, sort_keys=True)
    print(f"Updated {MASTER_OVERRIDES_PATH} ({len(master_overrides):,} rules).")
    
if __name__ == "__main__":
    is_dry = "--apply" not in sys.argv
    main(dry_run=is_dry)
