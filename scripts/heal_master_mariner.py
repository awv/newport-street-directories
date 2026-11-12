#!/usr/bin/env python3
"""
scripts/heal_master_mariner.py

Expands Master Mariner contractions and related Master/Mariner abbreviations:
- Mstr Marinr -> Master Mariner (and Mas. Mar'Nr, Mas.Marinr, Mstr Mrinr, Mstr. Mariner, Mastr Marinr)
- Marinr -> Mariner
- Schoolmstr / Schlmstr / Schmstr -> Schoolmaster
- Assist. Schoolmstr / Asst. Schlmstr -> Assistant Schoolmaster
- Berthing Mstr -> Berthing Master
- Station Mstr / Asst Station Mstr -> Station Master / Assistant Station Master
- Ballast Mstr -> Ballast Master
- Tug Mstr -> Tug Master
+ Disentangles trapped names in Master Mariner listings.
"""

import csv
import re
import shutil
from pathlib import Path
from collections import Counter

DATA_CSV = Path("data.csv")
BACKUP_CSV = Path("data.csv.bak_before_master_mariner")

def clean_trade(trade: str) -> str:
    if not trade:
        return trade
    s = trade.strip()

    # Master Mariner contractions
    s = re.sub(r'\bmas\.\s*mar\.,?\s*Note:\s*mas\.\s*mar\.\s*=\s*master\s*mariner\b', 'Master Mariner', s, flags=re.I)
    s = re.sub(r'\bMaster Mariner, Note: Master Mariner = master mariner\b', 'Master Mariner', s, flags=re.I)
    s = re.sub(r'\b(?:Mstr\.?|Mas\.?|Mastr)\s*(?:\.|\s+)?(?:Marinr|Mrinr|Mar\'?Nr|Mariner|Marnr|Mar\.?)\b\.?', 'Master Mariner', s, flags=re.I)
    s = re.sub(r'\bMas\.Marinr\b', 'Master Mariner', s, flags=re.I)

    # Standalone Mariner
    s = re.sub(r'\bMarinr\b', 'Mariner', s, flags=re.I)

    # Master contractions (Schoolmaster, Berthing Master, etc.)
    s = re.sub(r'\bBerthing\s+Mstr\b', 'Berthing Master', s, flags=re.I)
    s = re.sub(r'\b(?:Assist\.?|Asst\.?|ast\.?)\s*(?:Schoolmstr|Schlmstr)\b', 'Assistant Schoolmaster', s, flags=re.I)
    s = re.sub(r'\b(?:Schoolmstr|Schlmstr|Sch\'?Mstr|Schmstr)\b', 'Schoolmaster', s, flags=re.I)
    s = re.sub(r'\b(?:Asst\.?|Assist\.?)\s*Station\s+Mstr\b', 'Assistant Station Master', s, flags=re.I)
    s = re.sub(r'\bStation\s+Mstr\b', 'Station Master', s, flags=re.I)
    s = re.sub(r'\bBallast\s+Mstr\b', 'Ballast Master', s, flags=re.I)
    s = re.sub(r'\bTug\s+Mstr\b', 'Tug Master', s, flags=re.I)

    return s

def handle_trapped_names(row: dict) -> bool:
    tr = row.get('trade', '')
    yr = row.get('year', '')
    st = row.get('street', '')
    no = row.get('house_number', '')

    # 1887 Caerau Road 11: P. | Rowlands, master mar
    if yr == '1887' and 'Caerau Road' in st and no == '11' and 'Rowlands' in tr:
        row['surname'] = 'Rowlands'
        row['forename'] = 'P.'
        row['trade'] = 'Master Mariner'
        return True

    # 1887 Robert Street 32: Jas. | Kirby, master mar
    if yr == '1887' and 'Robert Street' in st and no == '32' and 'Kirby' in tr:
        row['surname'] = 'Kirby'
        row['forename'] = 'Jas.'
        row['trade'] = 'Master Mariner'
        return True

    # 1892 Victoria Avenue 86: Grant John | master mar., Alma cottage
    if yr == '1892' and 'Victoria Avenue' in st and no == '86' and 'Grant' in row.get('surname', ''):
        row['building_name'] = 'Alma Cottage'
        row['trade'] = 'Master Mariner'
        return True

    # 1894 Williams Street 81: Thos. | Griffiths, mas. mar.
    if yr == '1894' and 'Williams Street' in st and no == '81' and 'Griffiths' in tr:
        row['surname'] = 'Griffiths'
        row['forename'] = 'Thos.'
        row['trade'] = 'Master Mariner'
        return True

    # 1900 Alma Street 50: Thos. | mas. mariner, Lewis
    if yr == '1900' and 'Alma Street' in st and no == '50' and 'Lewis' in tr:
        row['surname'] = 'Lewis'
        row['forename'] = 'Thos.'
        row['trade'] = 'Master Mariner'
        return True

    # 1900 Alma Street 74: S. | master mariner, Evans
    if yr == '1900' and 'Alma Street' in st and no == '74' and 'Evans' in tr:
        row['surname'] = 'Evans'
        row['forename'] = 'S.'
        row['trade'] = 'Master Mariner'
        return True

    # 1900 Alma Street 82: Thos. | mas. mariner, James
    if yr == '1900' and 'Alma Street' in st and no == '82' and 'James' in tr:
        row['surname'] = 'James'
        row['forename'] = 'Thos.'
        row['trade'] = 'Master Mariner'
        return True

    # 1900 Alma Street 108: J M. | mas. mariner, Evans
    if yr == '1900' and 'Alma Street' in st and no == '108' and 'Evans' in tr:
        row['surname'] = 'Evans'
        row['forename'] = 'J. M.'
        row['trade'] = 'Master Mariner'
        return True

    # 1902 Herbert Street 17: Jas. | Witheridge, Master Mariner
    if yr == '1902' and 'Herbert Street' in st and no == '17' and 'Witheridge' in tr:
        row['surname'] = 'Witheridge'
        row['forename'] = 'Jas.'
        row['trade'] = 'Master Mariner'
        return True

    # 1908 Christchurch Road 4: Lander Francis | Schoolmaster, Penylan terrace
    if yr == '1908' and 'Christchurch' in st and no == '4' and 'Penylan' in tr:
        row['building_name'] = 'Penylan Terrace'
        row['trade'] = 'Schoolmaster'
        return True

    return False

def main():
    if not DATA_CSV.exists():
        print(f"Error: {DATA_CSV} not found.")
        return

    # Backup data.csv
    print(f"Backing up {DATA_CSV} to {BACKUP_CSV}...")
    shutil.copy2(DATA_CSV, BACKUP_CSV)

    rows = []
    fieldnames = []
    with open(DATA_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows)} rows from {DATA_CSV}.")

    modified_count = 0
    trade_changes = Counter()

    for r in rows:
        old_trade = r.get("trade", "")
        old_sur = r.get("surname", "")
        old_fore = r.get("forename", "")
        old_bld = r.get("building_name", "")

        # 1. Handle trapped names
        handle_trapped_names(r)

        # 2. Clean trade string
        cur_trade = r.get("trade", "")
        new_trade = clean_trade(cur_trade)
        if new_trade != cur_trade:
            r["trade"] = new_trade

        if (r["trade"] != old_trade or r["surname"] != old_sur or
            r["forename"] != old_fore or r.get("building_name", "") != old_bld):
            modified_count += 1
            if r["trade"] != old_trade:
                trade_changes[f"{old_trade}  ->  {r['trade']}"] += 1

    print(f"\nTotal rows modified: {modified_count}")
    print("\nTop 40 Trade Expansions Applied:")
    for change, count in trade_changes.most_common(40):
        print(f"  {count:4d}: {change}")

    print(f"\nWriting updated records back to {DATA_CSV}...")
    with open(DATA_CSV, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Successfully wrote healed data.csv!")

if __name__ == "__main__":
    main()
