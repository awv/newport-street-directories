#!/usr/bin/env python3
"""
parse_and_merge_early_commercial.py
Parse 1835-1865 early directories, write volume_csvs, merge into data.csv,
and rebuild all site indices and stats.
"""

import os
import sys
import re
import csv
import json
import subprocess
from collections import defaultdict

# Allow arbitrarily large fields in historical OCR files
csv.field_size_limit(sys.maxsize)

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

# 1. Load Master Streets for Fuzzy / Substring Matching
with open("master_streets.json", "r", encoding="utf-8") as f:
    master_data = json.load(f)["streets"]

# Build lookup of lower street name -> canonical street name, sorted longest first
street_lookup = {}
for s_slug, s_info in master_data.items():
    c_name = s_info.get("canonical_name", "").strip()
    if c_name and len(c_name) > 3:
        street_lookup[c_name.lower()] = c_name

# Add common 19th-century street abbreviations & variants
common_variants = {
    "commercial st": "Commercial Street",
    "commercial rd": "Commercial Road",
    "commercial-st": "Commercial Street",
    "commercial-rd": "Commercial Road",
    "stow hill": "Stow Hill",
    "stow-hill": "Stow Hill",
    "high st": "High Street",
    "high-st": "High Street",
    "dock st": "Dock Street",
    "dock-st": "Dock Street",
    "gt. dock st": "Dock Street",
    "skinner st": "Skinner Street",
    "skinner-st": "Skinner Street",
    "baneswell": "Baneswell Road",
    "pillgwenlly": "Pillgwenlly",
    "llanarth st": "Llanarth Street",
    "llanarth-st": "Llanarth Street",
    "hill st": "Hill Street",
    "hill-st": "Hill Street",
    "cardiff rd": "Cardiff Road",
    "cardiff-rd": "Cardiff Road",
    "chepstow rd": "Chepstow Road",
    "chepstow-rd": "Chepstow Road",
    "palmyra pl": "Palmyra Place",
    "palmyra place": "Palmyra Place",
    "cambria pl": "Cambria Place",
    "clifton pl": "Clifton Place",
    "clarence pl": "Clarence Place"
}
for v_low, v_canon in common_variants.items():
    street_lookup[v_low] = v_canon

sorted_streets = sorted(street_lookup.keys(), key=lambda x: len(x), reverse=True)

def extract_street_and_hno(text):
    """Attempt to extract street and house number from text / address snippet."""
    if not text:
        return "", ""
    t_clean = text.strip()
    t_low = t_clean.lower()
    
    h_num = ""
    num_match = re.search(r'\b(\d+[a-zA-Z]?)\b', t_clean)
    if num_match:
        h_num = num_match.group(1)
        
    for s_low in sorted_streets:
        pattern = r'\b' + re.escape(s_low) + r'\b'
        if re.search(pattern, t_low):
            return street_lookup[s_low], h_num
            
    return "", h_num

def parse_early_tsv(year, tsv_filename, output_csv):
    print(f"\nParsing {tsv_filename} (Year {year})...")
    tsv_path = os.path.join("raw_tsvs", tsv_filename)
    if not os.path.exists(tsv_path):
        print(f"File not found: {tsv_path}")
        return []

    records = []
    current_category = ""
    
    with open(tsv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
        
        for row in reader:
            if not row or not any(row):
                continue
                
            col0 = row[0].strip() if len(row) > 0 else ""
            col1 = row[1].strip() if len(row) > 1 else ""
            col2 = row[2].strip() if len(row) > 2 else ""
            col3 = row[3].strip() if len(row) > 3 else ""
            col4 = row[4].strip() if len(row) > 4 else ""
            col5 = row[5].strip() if len(row) > 5 else ""

            combined_line = " ".join([c for c in row if c.strip()])

            # Heading detection (e.g. "ACADEMIES & SCHOOLS", "BOOT & SHOE MAKERS", "NOBILITY, GENTRY")
            if (col0.isupper() or col5.isupper()) and not col1 and not col2:
                heading = col0 if col0.isupper() else col5
                if len(heading) > 3 and not re.search(r'\b(street|road|lane|place|wharf|quay)\b', heading.lower()):
                    current_category = heading.title()
                    continue

            # Skip descriptive text paragraphs
            if len(combined_line) > 150 and not any(kw in combined_line.lower() for kw in ['esq', 'rev', 'mr.', 'mrs.', 'miss', 'inn', 'hotel']):
                continue

            surname = ""
            forename = ""
            trade = col3 if col3 else current_category
            bldg = col4
            address_text = col5 if col5 else combined_line

            # Name splitting
            if col2 and col1:
                surname = col2
                forename = col1
            elif col1 and not col2:
                tokens = col1.split(",", 1)
                surname = tokens[0].strip()
                forename = tokens[1].strip() if len(tokens) > 1 else ""
            elif col0 and not col1 and not col2:
                # E.g. "Jones Mrs. Rebecca, Stow hill"
                parts = col0.split(",", 1)
                tokens = parts[0].strip().split()
                if len(tokens) >= 2:
                    surname = tokens[0]
                    forename = " ".join(tokens[1:])
                else:
                    surname = parts[0].strip()
                if len(parts) > 1:
                    address_text = parts[1].strip()

            # Clean Titles & Formatting
            surname = re.sub(r'^(Mr\.|Mrs\.|Miss|Rev\.|Sir|Esq\.)\s*', '', surname, flags=re.I).strip(' ,.')
            forename = forename.strip(' ,.')
            
            # Extract street and house number
            street, h_num = extract_street_and_hno(address_text)
            if not street:
                street, _ = extract_street_and_hno(combined_line)
                
            # Default trade if empty
            if not trade and current_category:
                trade = current_category

            # Clean trade formatting
            trade = trade.strip(' ,.')
            if trade.lower() in ('nan', 'none', 'null'):
                trade = ""

            # Truncate any accidental large OCR narrative dumps in fields
            if len(bldg) > 150: bldg = bldg[:150].strip()
            if len(trade) > 150: trade = trade[:150].strip()
            if len(surname) > 50: surname = surname[:50].strip()
            if len(forename) > 50: forename = forename[:50].strip()

            # Check if valid record
            if surname or forename or trade or street:
                # Basic noise filter
                if len(surname) > 40 or "population" in combined_line.lower() or "distant by railway" in combined_line.lower():
                    continue
                    
                records.append({
                    "year": str(year),
                    "street": street,
                    "house_number": h_num,
                    "building_name": bldg,
                    "surname": surname,
                    "forename": forename,
                    "trade": trade,
                    "source_type": "commercial_directory"
                })

    print(f"Extracted {len(records)} records for year {year} (Streets identified for {sum(1 for r in records if r['street']):,} records).")
    
    # Save to volume_csvs
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"])
        writer.writeheader()
        writer.writerows(records)
        
    return records

def main():
    early_volumes = [
        ("1835", "1835.tsv", "volume_csvs/1835_cleaned.csv"),
        ("1844", "1844.tsv", "volume_csvs/1844_cleaned.csv"),
        ("1850", "1850.tsv", "volume_csvs/1850_cleaned.csv"),
        ("1858", "1858.tsv", "volume_csvs/1858_cleaned.csv"),
        ("1862", "1862.tsv", "volume_csvs/1862_cleaned.csv"),
        ("1865", "1865.tsv", "volume_csvs/1865_cleaned.csv"),
    ]

    new_early_records = []
    early_years_set = set(y for y, _, _ in early_volumes)

    for year, tsv_file, out_csv in early_volumes:
        recs = parse_early_tsv(year, tsv_file, out_csv)
        new_early_records.extend(recs)

    print(f"\nTotal early directory records parsed: {len(new_early_records):,}")

    # Merge into data.csv safely
    print("\nMerging into data.csv...")
    backup_file = f"data.csv.bak_before_early_merge"
    if not os.path.exists(backup_file):
        import shutil
        shutil.copyfile("data.csv", backup_file)
        print(f"Created safety backup {backup_file}")

    existing_kept_records = []
    with open("data.csv", "r", encoding="utf-8", errors="replace") as f_in:
        reader = csv.DictReader(f_in)
        for row in reader:
            if row.get("year", "") not in early_years_set:
                existing_kept_records.append(row)

    print(f"Preserved {len(existing_kept_records):,} existing records from 1876-1971.")

    all_combined = existing_kept_records + new_early_records
    # Sort chronologically by year
    all_combined.sort(key=lambda r: int(r["year"]) if r.get("year", "").isdigit() else 9999)

    fieldnames = ["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"]
    with open("data.csv", "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_combined)

    print(f"Wrote {len(all_combined):,} total records to data.csv!")

    # Run Casing Twins & Site Rebuild
    print("\nRunning merge_casing_twins.py...")
    subprocess.run([sys.executable, "scripts/merge_casing_twins.py"], check=False)

    print("\nCompiling analytics and diagnostics dashboard (build_stats_data.py)...")
    subprocess.run([sys.executable, "scripts/build_stats_data.py"], check=False)

    print("\nEarly directories merge and pipeline execution complete!")

if __name__ == "__main__":
    main()
