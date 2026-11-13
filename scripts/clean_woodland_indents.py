#!/usr/bin/env python3
"""
clean_woodland_indents.py
=========================
Applies verified corrections for Woodland Avenue & Woodland Road (1936)
grounded directly in the camera scan of the physical directory page.

Resolves directory indent conventions:
1. Indented single words under a resident entry are HOUSE / VILLA NAMES:
   - Door 1: 'Norwood' -> Building name of Leslie Dowden (Builder)
   - Door 2: 'Sundown' -> Building name of Bertie Burgess
   - Door 6: 'Perome'  -> Building name of Lionel Watkins (Secretary)
   - Door 3 (Road): 'The Laurels' -> Building name of William J. Seer (G.W.R.)
   - Door 5 (Road): 'Allt-wen'    -> Building name of A. E. Oakey (Draper)
   - Door 6 (Road): 'Summerhill'  -> Building name of Miss Jennie Pritchard & Edgar O. Wood (Ironworker)
   - Door 19 (Road): 'Boro' + 'eng\'eer\'s asst' -> Trade: 'Borough Engineer\'s Assistant'
   - Door 22 (Road): 'Woodland house' -> Building name of Cyril F. Pugsley
   - After Door 25: E. R. J. Goddard, Decorator
   - J. M. Broadfoot, The Woodlands
"""

import os
import csv
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

    # Cleaned entries for 1936 Woodland Avenue
    clean_woodland_avenue = [
        {"year": "1936", "street": "Woodland Avenue", "house_number": "1", "building_name": "Norwood", "surname": "Dowden", "forename": "Leslie", "trade": "Builder", "source_type": ""},
        {"year": "1936", "street": "Woodland Avenue", "house_number": "2", "building_name": "Sundown", "surname": "Burgess", "forename": "Bertie", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Avenue", "house_number": "3", "building_name": "", "surname": "Thomas", "forename": "A. E.", "trade": "Dental Mech", "source_type": ""},
        {"year": "1936", "street": "Woodland Avenue", "house_number": "4", "building_name": "", "surname": "Dove", "forename": "", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Avenue", "house_number": "6", "building_name": "Perome", "surname": "Watkins", "forename": "Lionel", "trade": "Secretary", "source_type": ""},
    ]

    # Cleaned entries for 1936 Woodland Road (Doors 1 to 25 + return)
    clean_woodland_road_doors = [
        {"year": "1936", "street": "Woodland Road", "house_number": "1", "building_name": "", "surname": "Armstead", "forename": "G. W.", "trade": "Leather Merchant", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "2", "building_name": "Brighton Villa", "surname": "Dix", "forename": "Mrs. M. L.", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "3", "building_name": "The Laurels", "surname": "Seer", "forename": "William J.", "trade": "G.W.R.", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "4", "building_name": "Coedpant", "surname": "Keene", "forename": "Miss", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "5", "building_name": "Allt-wen", "surname": "Oakey", "forename": "A. E.", "trade": "Draper", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "6", "building_name": "Summerhill", "surname": "Pritchard", "forename": "Miss Jennie", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "6", "building_name": "Summerhill", "surname": "Wood", "forename": "Edgar O.", "trade": "Ironworker", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "7", "building_name": "", "surname": "Smith", "forename": "Robert H. & Co.", "trade": "Landscape Gardeners", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "8", "building_name": "", "surname": "White", "forename": "A. L.", "trade": "Bricklayer", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "9", "building_name": "", "surname": "Perkins", "forename": "E. S.", "trade": "G.W.R.", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "10", "building_name": "", "surname": "Evans", "forename": "E. J.", "trade": "G.W.R.", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "11", "building_name": "", "surname": "Johnson", "forename": "George W.", "trade": "Fitter", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "12", "building_name": "", "surname": "Dudley", "forename": "Mrs. W. E.", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "13", "building_name": "", "surname": "Loftus", "forename": "Miss Florence", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "14", "building_name": "", "surname": "Richards", "forename": "Mrs. L. M.", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "15", "building_name": "", "surname": "Thomas", "forename": "Gwyn", "trade": "Salesman", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "16", "building_name": "", "surname": "Alexander", "forename": "H.", "trade": "Shop Assistant", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "17", "building_name": "", "surname": "Birden", "forename": "Alphonso D.", "trade": "Saddler", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "18", "building_name": "", "surname": "Jenkins", "forename": "Andrew H. S.", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "19", "building_name": "", "surname": "Nash", "forename": "Frederick", "trade": "Borough Engineer's Assistant", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "20", "building_name": "", "surname": "Robson", "forename": "Lennard Evan", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "21", "building_name": "", "surname": "Clift", "forename": "Albert", "trade": "Manager", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "21a", "building_name": "", "surname": "Davies", "forename": "A. W.", "trade": "Nurseryman", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "22", "building_name": "Woodland House", "surname": "Pugsley", "forename": "Cyril F.", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "23", "building_name": "Woodland Cottage", "surname": "Moore", "forename": "C. F.", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "24", "building_name": "", "surname": "Williams", "forename": "Ifor", "trade": "Electrician", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "25", "building_name": "", "surname": "Pucknell", "forename": "Albert", "trade": "", "source_type": ""},
        {"year": "1936", "street": "Woodland Road", "house_number": "", "building_name": "", "surname": "Goddard", "forename": "E. R. J.", "trade": "Decorator", "source_type": ""},
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

    # Filter out existing 1936 Woodland Avenue & Woodland Road entries
    filtered_records = []
    for r in records:
        st = r.get('street', '').strip()
        yr = r.get('year', '').strip()
        if yr == '1936' and st in ['Woodland Avenue', 'Woodland Road']:
            continue
        filtered_records.append(r)

    # Add back the clean records
    filtered_records.extend(clean_woodland_avenue)
    filtered_records.extend(clean_woodland_road_doors)

    print(f"Total dataset records: {len(filtered_records):,}")

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_records)

    print("Rebuilding site data and statistics...")
    subprocess.run(["python3", "scripts/build_site_data.py"], check=True)
    subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)
    print("Done!")

if __name__ == "__main__":
    main()
