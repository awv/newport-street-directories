#!/usr/bin/env python3
"""
scripts/heal_trade_abbreviations_batch3.py

Expands trade abbreviations (Batch 3) while preserving authenticity:
1. Tobaccon'st -> Tobacconist
2. Gas-meter Mkr -> Gas-meter Maker
3. Build'g Inspector -> Building Inspector
4. Building Inspector. -> Building Inspector (remove trailing full stop)
5. J.p. -> Justice of the Peace
6. Engr -> Engineer (and Engrs -> Engineers, Motor Engr, etc.)
7. Rivettr -> Rivettor (and Rivetr, Rivet Mkr, etc.)
8. Wheelw't -> Wheelwright (and Wheelwrt, Wheelwght, Wheelwgts, etc.)
9. Marine Enginr -> Marine Engineer (and all Mar. Engr, Marine Engn'R variants)
+ Disentangles trapped names/honorifics in J.P. and Rivetter entries.
"""

import csv
import re
import shutil
from pathlib import Path
from collections import Counter

DATA_CSV = Path("data.csv")
BACKUP_CSV = Path("data.csv.bak_before_trades_batch3")

def clean_trade(trade: str) -> str:
    if not trade:
        return trade
    s = trade.strip()

    # 1. Tobaccon'st
    s = re.sub(r'\bTobaccon[\'’]st\b', 'Tobacconist', s, flags=re.I)

    # 2. Gas-meter Mkr
    s = re.sub(r'\bGas-Meter\s+Mkr\b', 'Gas-meter Maker', s, flags=re.I)
    s = re.sub(r'\bGas\s+Meter\s+Mkr\b', 'Gas-meter Maker', s, flags=re.I)

    # 3 & 4. Building Inspector
    s = re.sub(r'\b(?:Build\'?g|Building|Bldg\.?|B\'?Lding)\s+Inspt(?:r)?\.?\b', 'Building Inspector', s, flags=re.I)
    if s.endswith('Building Inspector.'):
        s = s[:-1]
    if s == 'Building Inspector.':
        s = 'Building Inspector'

    # 5. J.P. -> Justice of the Peace
    if s.rstrip(',').upper() == 'J.P.':
        s = 'Justice of the Peace'
    elif re.match(r'^M\.D\.,?\s*J\.P\.?$', s, re.I):
        s = 'M.D., Justice of the Peace'
    elif re.match(r'^J\.P\.,?\s*physician(?:\s*and|\s*&)?\s*surgeon$', s, re.I):
        s = 'Justice of the Peace, Physician & Surgeon'
    elif re.match(r'^J\.P\.,?\s*physician$', s, re.I):
        s = 'Justice of the Peace, Physician'
    else:
        s = re.sub(r'^J\.P\.,\s*', 'Justice of the Peace, ', s)

    # 6 & 9. Engineer / Marine Engineer
    s = re.sub(r'\bMar(?:ine|\.)?\s+Eng[a-z\'\.\s]*\b', 'Marine Engineer', s, flags=re.I)
    if s.startswith('Marine Engineer.'):
        s = s.replace('Marine Engineer.', 'Marine Engineer')

    s = re.sub(r'\bMotor\s+Engrs\b', 'Motor Engineers', s, flags=re.I)
    s = re.sub(r'\bMotor\s+Engin?r\b', 'Motor Engineer', s, flags=re.I)
    s = re.sub(r'\bSanitary\s+Engin?r\b', 'Sanitary Engineer', s, flags=re.I)
    s = re.sub(r'\bElectrical\s+Engin?r\b', 'Electrical Engineer', s, flags=re.I)
    s = re.sub(r'\belec\.\s+engr\.?\b', 'Electrical Engineer', s, flags=re.I)
    s = re.sub(r'\bCivil\s+Engin?r\b', 'Civil Engineer', s, flags=re.I)
    s = re.sub(r'\bAgric\'?T\'?L\s+Engr\b', 'Agricultural Engineer', s, flags=re.I)
    s = re.sub(r'\bHot\s+Wtr\s+Engr\b', 'Hot Water Engineer', s, flags=re.I)
    s = re.sub(r'\bForge\s+Engr\b', 'Forge Engineer', s, flags=re.I)
    s = re.sub(r'\bMch\.?\s*Engr\b', 'Mechanical Engineer', s, flags=re.I)
    s = re.sub(r'\bRly\s+Engr\b', 'Railway Engineer', s, flags=re.I)
    s = re.sub(r'\bEngrs\b', 'Engineers', s, flags=re.I)
    s = re.sub(r'\bEngin?r\b', 'Engineer', s, flags=re.I)

    # 7. Rivettor / Rivetter
    s = re.sub(r'\bChina\s+Rivetr\b', 'China Rivetter', s, flags=re.I)
    s = re.sub(r'\bRivettr\b', 'Rivettor', s, flags=re.I)
    s = re.sub(r'\bRivetr\b', 'Rivetter', s, flags=re.I)
    s = re.sub(r'\bRivet\s+Mkr\b', 'Rivet Maker', s, flags=re.I)
    s = re.sub(r'\brivetmaker\b', 'Rivet Maker', s, flags=re.I)
    s = re.sub(r'\bRivet\s+Wkr\b', 'Rivet Worker', s, flags=re.I)

    # 8. Wheelwright
    s = re.sub(r'\bWheelw\'?g(?:h)?ts\b', 'Wheelwrights', s, flags=re.I)
    s = re.sub(r'\bWheelw(?:r|g)?(?:i|h)?(?:g)?ht\b', 'Wheelwright', s, flags=re.I)
    s = re.sub(r'\bWheelw\'?t\b', 'Wheelwright', s, flags=re.I)
    s = re.sub(r'\bWheelwt\b', 'Wheelwright', s, flags=re.I)
    s = re.sub(r'\bWheelwrt\b', 'Wheelwright', s, flags=re.I)

    # Cleanup trailing dots on target nouns
    if s.endswith('.'):
        for target in ['Building Inspector.', 'Marine Engineer.', 'Wheelwright.', 'Engineer.', 'Justice of the Peace.']:
            if s.endswith(target):
                s = s[:-1]
                break

    return s

def handle_trapped_names_batch3(row: dict) -> bool:
    tr = row.get('trade', '')
    yr = row.get('year', '')
    st = row.get('street', '')
    no = row.get('house_number', '')

    # 1887 & 1890 Clytha Square 12: Beynon, J.P.
    if yr in ('1887', '1890') and 'Clytha Square' in st and no == '12' and 'Beynon' in tr:
        row['surname'] = 'Beynon'
        row['forename'] = 'Theophilus'
        row['building_name'] = 'Richmond House'
        row['trade'] = 'Justice of the Peace'
        return True

    # 1893, 1894, 1900, 1903 Stow Hill: Brewer Hy. | Melville, J.P.
    if yr in ('1893', '1894', '1900', '1903') and 'Stow Hill' in st and 'Melville' in tr:
        row['surname'] = 'Brewer'
        row['forename'] = 'Hy. Melville'
        row['trade'] = 'Justice of the Peace'
        return True

    # 1882 & 1887 Clarence Place: Evans Hy. | Russell J.P.
    if yr in ('1882', '1887') and 'Clarence Place' in st and 'Russell' in tr:
        row['surname'] = 'Russell'
        row['forename'] = 'Hy. Evans'
        row['trade'] = 'Justice of the Peace'
        return True

    # 1913 Kenilworth Road 3: Henry | Waters, rivet mkr
    if yr == '1913' and 'Kenilworth' in st and no == '3' and 'Waters' in tr:
        row['surname'] = 'Waters'
        row['forename'] = 'Henry'
        row['trade'] = 'Rivet Maker'
        return True

    # 1913 Kenilworth Road 11: William | Nicholls, rivetter
    if yr == '1913' and 'Kenilworth' in st and no == '11' and 'Nicholls' in tr:
        row['surname'] = 'Nicholls'
        row['forename'] = 'William'
        row['trade'] = 'Rivetter'
        return True

    # 1915 Lloyd Street 34: Tom | Pitson, rivetter
    if yr == '1915' and 'Lloyd' in st and no == '34' and 'Pitson' in tr:
        row['surname'] = 'Pitson'
        row['forename'] = 'Tom'
        row['trade'] = 'Rivetter'
        return True

    # 1915 Llewellin Street 12: Thomas | Savigar, rivet mkr
    if yr == '1915' and 'Llewellin' in st and no == '12' and 'Savigar' in tr:
        row['surname'] = 'Savigar'
        row['forename'] = 'Thomas'
        row['trade'] = 'Rivet Maker'
        return True

    # 1900 Alma Street 45: Geo James | rivetter, Bishop
    if yr == '1900' and 'Alma' in st and no == '45' and 'Bishop' in tr:
        row['surname'] = 'Bishop'
        row['forename'] = 'Geo. James'
        row['trade'] = 'Rivetter'
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
        handle_trapped_names_batch3(r)

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
