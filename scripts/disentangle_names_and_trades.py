#!/usr/bin/env python3
"""
disentangle_names_and_trades.py
===============================
Resolves legacy column-shift anomalies where forenames or surnames spilled
into the trade field, and where business names/trades were misassigned to personal names.

1. Pattern A: Rotated Surnames in Trade (e.g. Surname: 'Mrs', Forename: 'T. J', Trade: 'Smith' -> Surname: 'Smith', Forename: 'Mrs T. J', Trade: '')
2. Pattern B: Middle Forenames Pushed to Trade (e.g. Surname: 'Bladon', Forename: 'Francis', Trade: 'Henry' -> Forename: 'Francis Henry', Trade: '')
3. Pattern C: Business / Institute Names in Personal Fields (e.g. Forename: 'INSTITUTE', Surname: 'BOILERMAKERS' -> Building: "Boilermakers' Institute")
"""

import os
import csv
import re
import shutil
import subprocess

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

DATA_CSV = os.path.join(PROJECT_DIR, "data.csv")

COMMON_SURNAMES = {
    'Davies', 'Jones', 'Williams', 'Evans', 'Thomas', 'Lewis', 'Morgan', 'Smith',
    'Phillips', 'Griffiths', 'Jenkins', 'Owen', 'Rees', 'Edwards', 'Harris',
    'Richards', 'Powell', 'Price', 'Hughes', 'Collins', 'Baker', 'Clark', 'Allen'
}

COMMON_FORENAMES = {
    'Henry', 'George', 'William', 'Thomas', 'James', 'John', 'Charles', 'Edward',
    'Alfred', 'Arthur', 'Frederick', 'Robert', 'David', 'Francis', 'Ernest',
    'Albert', 'Herbert', 'Walter', 'Alexander', 'Sidney', 'Edwin', 'Frank'
}

def main():
    print("Reading data.csv...")
    records = []
    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            records.append(r)

    count_a = 0
    count_b = 0
    count_c = 0

    for r in records:
        sn = r.get('surname', '').strip()
        fn = r.get('forename', '').strip()
        tr = r.get('trade', '').strip()
        bldg = r.get('building_name', '').strip()

        # Pattern A: Column rotation (sn has initials/title, fn has remainder or building, tr has surname)
        if tr in COMMON_SURNAMES and (any(sn.startswith(title) for title in ['Mrs', 'Mr', 'Rev', 'Miss', 'Dr', 'Capt', 'Major', 'Col']) or re.match(r'^[A-Z]\.?(\s+[A-Z]\.?)*$', sn)):
            real_surname = tr
            real_forename = f"{sn} {fn}".strip()
            r['surname'] = real_surname
            r['forename'] = real_forename
            r['trade'] = ''
            count_a += 1

        # Pattern B: Middle forename pushed to trade
        elif tr in COMMON_FORENAMES and fn in COMMON_FORENAMES and sn and sn not in COMMON_FORENAMES:
            r['forename'] = f"{fn} {tr}".strip()
            r['trade'] = ''
            count_b += 1

        # Pattern C: Boilermakers Institute & similar institutional headings
        elif sn.upper() == 'BOILERMAKERS' and fn.upper() == 'INSTITUTE':
            r['building_name'] = "Boilermakers' Institute"
            r['surname'] = ''
            r['forename'] = ''
            r['trade'] = ''
            count_c += 1

    print(f"Applied fixes:")
    print(f"  Pattern A (Rotated Surnames): {count_a}")
    print(f"  Pattern B (Middle Forenames): {count_b}")
    print(f"  Pattern C (Institutes & Trade Clubs): {count_c}")

    # Write back
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print("Rebuilding site data and stats...")
    subprocess.run(["python3", "scripts/build_site_data.py"], check=True)
    subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)
    print("Done!")

if __name__ == "__main__":
    main()
