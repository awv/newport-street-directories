#!/usr/bin/env python3
"""
fix_woodland_and_dashes.py
==========================
Fixes specific anomalies reported on Woodland Avenue & Woodland Road (1936):
1. Woodland Avenue vs Woodland Road disentanglement:
   - Woodland Avenue in 1936 only has doors 1 to 6 (from Malpas Road).
   - Doors 45 to 64 and 'The Woodlands' (Broadfoot J. M.) are the return side of
     Woodland Road (from 81 Victoria Avenue to Crescent Road) and are re-assigned there.
2. Removes long line / pure dash placeholders ('————', '——', '---') from forename across the dataset.
3. Consolidates phantom split rows:
   - 'J. M. Broadfoot' + 'The Woodlands' merged into: Forename: 'J. M.', Surname: 'Broadfoot', Building: 'The Woodlands'.
   - No. 50: Harold W. Reade + 'caretkr' merged into: Forename: 'Harold W.', Surname: 'Reade', Trade: 'Caretaker'.
   - No. 60: Gunstone Frederick C. (Merchant) and Mrs. E. A. Gunstone (Shopkeeper) cleanly formatted, removing ghost 'mchts' and 'shop' surname rows.
   - No. 64: Charles McDonagh (Labourer) and E. A. Brown (Greengrocer) cleanly formatted, fixing 'Engrocer'.
   - No. 49: Typo 'Saunsers' corrected to 'Saunders'.
4. Rebuilds site data and statistics.
"""

import os
import csv
import re
import subprocess

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

DATA_CSV = os.path.join(PROJECT_DIR, "data.csv")

def main():
    print("Reading data.csv...")
    records = []
    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            records.append(r)

    # 1. Clean pure dash forenames across all records
    dash_cleaned = 0
    for r in records:
        fn = r.get('forename', '').strip()
        if re.match(r'^[—\-–]+$', fn):
            r['forename'] = ''
            dash_cleaned += 1

    print(f"Cleaned {dash_cleaned} pure-dash forename placeholders across archive.")

    # 2. Filter and rebuild Woodland Avenue & Woodland Road for 1936
    new_records = []
    woodland_road_additions = [
        {"year": "1936", "street": "Woodland Road", "house_number": "", "building_name": "The Woodlands", "surname": "Broadfoot", "forename": "J. M.", "trade": "Contractor", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "45", "building_name": "Griffin", "surname": "Anning", "forename": "Henry", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "46", "building_name": "", "surname": "Bertera", "forename": "Geronzo", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "47", "building_name": "", "surname": "Lightwood", "forename": "H.", "trade": "Clerk", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "48", "building_name": "", "surname": "Argent", "forename": "Arthur", "trade": "Insurance Agent", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "49", "building_name": "", "surname": "Saunders", "forename": "", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "50", "building_name": "", "surname": "Reade", "forename": "Harold W.", "trade": "Caretaker", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "51", "building_name": "", "surname": "Poynton", "forename": "Edward", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "52", "building_name": "", "surname": "Poynton", "forename": "W. H.", "trade": "Pattern Maker", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "53", "building_name": "", "surname": "Sulway", "forename": "L. T.", "trade": "Butcher", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "54", "building_name": "", "surname": "Thomas", "forename": "Mrs. Amelia", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "55", "building_name": "", "surname": "Watson", "forename": "E. T.", "trade": "Chef", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "57", "building_name": "", "surname": "Trick", "forename": "Ernest G.", "trade": "Labourer", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "59", "building_name": "", "surname": "Bowen", "forename": "L. R.", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "60", "building_name": "", "surname": "Gunstone", "forename": "Frederick C.", "trade": "Merchant", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "60", "building_name": "", "surname": "Gunstone", "forename": "Mrs. E. A.", "trade": "Shopkeeper", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "61", "building_name": "", "surname": "Watkins", "forename": "Sidney", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "61", "building_name": "", "surname": "Evans", "forename": "Rees", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "62", "building_name": "", "surname": "Morris", "forename": "D. W.", "trade": "Carpenter", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "63", "building_name": "", "surname": "Underwood", "forename": "Arthur", "trade": "Labourer", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "64", "building_name": "", "surname": "McDonagh", "forename": "Charles", "trade": "Labourer", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "64", "building_name": "", "surname": "Brown", "forename": "E. A.", "trade": "Greengrocer", "source_type": ""},
    ]

    for r in records:
        st = r.get('street', '').strip()
        yr = r.get('year', '').strip()
        hn = r.get('house_number', '').strip()
        sn = r.get('surname', '').strip()

        # Handle 1936 Woodland Avenue
        if st == 'Woodland Avenue' and yr == '1936':
            # Keep only true Woodland Avenue doors (1 to 6)
            if hn in ['1', '2', '3', '4', '6']:
                if hn == '4':
                    r['forename'] = ''
                    r['surname'] = 'Dove'
                new_records.append(r)
            # All other doors / ghost rows from Woodland Avenue are skipped here because
            # their clean, consolidated versions are added to Woodland Road below.
            continue

        new_records.append(r)

    # Insert the additions into Woodland Road
    new_records.extend(woodland_road_additions)

    print(f"Total master records after Woodland Avenue & Woodland Road realignment: {len(new_records):,}")

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_records)

    print("Rebuilding site data and statistics...")
    subprocess.run(["python3", "scripts/build_site_data.py"], check=True)
    subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)
    print("Done!")

if __name__ == "__main__":
    main()
