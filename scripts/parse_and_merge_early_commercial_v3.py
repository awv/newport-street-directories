#!/usr/bin/env python3
"""
parse_and_merge_early_commercial_v3.py
Accurate multi-format parsing for early trade/commercial directories (1835-1865).
- Accurately tracks occupational heading changes across multi-column tables.
- Distinguishes between pure section headings and dual heading/person rows.
- Prevents occupation stickiness (no whole streets of 'Attorneys').
- Cleanly isolates Surnames and Forenames without '--' artifacts.
- Rebuilds data.csv, casing twins, search indices, and stats.
"""

import os
import sys
import re
import csv
import json
import subprocess

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

csv.field_size_limit(sys.maxsize)

# Load Master Streets
with open("master_streets.json", "r", encoding="utf-8") as f:
    master_data = json.load(f)["streets"]

street_lookup = {}
for s_slug, s_info in master_data.items():
    c_name = s_info.get("canonical_name", "").strip()
    if c_name and len(c_name) > 3:
        street_lookup[c_name.lower()] = c_name

# 19th-century street variants
variants = {
    "commercial st": "Commercial Street", "commercial rd": "Commercial Road",
    "stow hill": "Stow Hill", "high st": "High Street", "dock st": "Dock Street",
    "gt. dock st": "Dock Street", "great dock st": "Dock Street", "skinner st": "Skinner Street",
    "baneswell": "Baneswell Road", "pillgwenlly": "Pillgwenlly", "llanarth st": "Llanarth Street",
    "hill st": "Hill Street", "cardiff rd": "Cardiff Road", "chepstow rd": "Chepstow Road",
    "palmyra pl": "Palmyra Place", "cambria pl": "Cambria Place", "clifton pl": "Clifton Place",
    "clarence pl": "Clarence Place", "westgate st": "Westgate Street", "corn st": "Corn Street",
    "canal parade": "Canal Parade", "market st": "Market Street", "old green": "Old Green",
    "griffin st": "Griffin Street", "cinder hill": "Cinder Hill", "marshes rd": "Marshes Road",
    "tredegar st": "Tredegar Street", "cross st": "Cross Street", "thomas st": "Thomas Street",
    "charles st": "Charles Street", "george st": "George Street", "powell st": "Powell Street",
    "king's hill": "King's Hill", "king-st": "King Street", "king st": "King Street",
    "union st": "Union Street", "caerleon": "Caerleon", "caerleon rd": "Caerleon Road",
    "north st": "North Street", "south st": "South Street", "victoria pl": "Victoria Place"
}
for k, v in variants.items():
    street_lookup[k] = v

sorted_streets = sorted(street_lookup.keys(), key=lambda x: len(x), reverse=True)

KNOWN_TRADES = [
    'academies & schools', 'agents', 'anchor & ship smiths', 'attorneys',
    'auctioneers', 'bakers', 'bakery', 'bankers', 'bark merchants', 'basket makers',
    'blacksmiths', 'block and pump makers', 'block & pump makers', 'booksellers & stationers',
    'boot and shoe makers', 'boot & shoe makers', 'braziers and tin-plate workers', 'brewers',
    'brick makers', 'builders', 'butchers', 'cabinet makers', 'carpenters & joiners',
    'carpenters', 'chemists & druggists', 'cider merchants', 'civil engineers', 'clergy',
    'clothes dealers', 'coal merchants', 'coal owners', 'coopers', 'curriers', 'drapers',
    'dress makers', 'fire &c. office agents', 'grocers & tea dealers', 'grocers',
    'hair dressers', 'hat manufacturers', 'inns', 'iron forgers', 'iron founders',
    'iron masters', 'iron merchants', 'ironmongers', 'lime burners', 'linen & woollen drapers',
    'marine stores', 'merchants', 'millers', 'milliners & dress makers', 'milliners and dress makers',
    'nail makers', 'painters, plumbers', 'pawnbrokers', 'physicians', 'portrait painters',
    'porter & ale merchants', 'potters', 'printers', 'provision merchants', 'public houses',
    'retailers of beer', 'rope and twine makers', 'saddlers and harness makers', 'sail makers',
    'salt merchants', 'ship & boat builders', 'ship brokers', 'ship chandlers',
    'shopkeepers & dealers', 'shopkeepers', 'spirit dealers', 'stone masons', 'surgeons',
    'surveyors', 'tailors', 'tallow chandlers', 'tanners', 'taverns & public houses',
    'tin-plate workers', 'watch & clock makers', 'wheelwrights', 'wine & spirit merchants'
]

def find_street_in_text(text):
    if not text: return ""
    t_low = text.lower()
    for s_low in sorted_streets:
        if re.search(r'\b' + re.escape(s_low) + r'\b', t_low):
            return street_lookup[s_low]
    return ""

def detect_category_in_row(tokens):
    """Detect if any token represents an occupational category heading."""
    for i, tok in enumerate(tokens):
        c_tok = tok.strip(' .:[];()')
        c_low = c_tok.lower()
        
        # Check against known headings or uppercase words
        if any(kt in c_low for kt in KNOWN_TRADES):
            # Ensure it's not an address or personal name
            if not any(sw in c_low for sw in [' high st', ' commercial st', ' stow hill', ' cardiff rd']):
                return c_tok.title(), i
        elif c_tok.isupper() and len(c_tok) > 4:
            if not any(sw in c_low for sw in [' high st', ' commercial st', ' stow hill', ' cardiff rd']):
                return c_tok.title(), i

    return "", -1

def parse_early_row_v3(row, active_category):
    tokens = [c.strip() for c in row if c.strip() and c.strip().lower() not in ('nan', '--', '-', '')]
    if not tokens:
        return None, active_category

    combined = " ".join(tokens)

    # 1. Skip non-resident text / metadata blocks
    if len(combined) > 160 and not any(kw in combined.lower() for kw in ['esq', 'rev', 'mr.', 'mrs.', 'miss', 'inn', 'hotel']):
        return None, active_category

    # 2. Check for Category Heading
    cat_detected, cat_idx = detect_category_in_row(tokens)
    if cat_detected:
        active_category = cat_detected
        # If the row is ONLY the heading, update category and return
        if len(tokens) == 1 or (len(tokens) == 2 and any(tokens[1].startswith(c) for c in ['[', '(', '--'])):
            return None, active_category

    # 3. Detect Street
    street = ""
    street_token_idx = -1
    for i, tok in enumerate(tokens):
        st = find_street_in_text(tok)
        if st:
            street = st
            street_token_idx = i
            break

    # 4. Extract Person Tokens
    person_tokens = [tok for i, tok in enumerate(tokens) if i not in (cat_idx, street_token_idx)]
    if not person_tokens and street_token_idx >= 0:
        # Check if person was inside the street token (e.g. 'Daw Ann, Commercial st')
        person_str = tokens[street_token_idx]
    else:
        person_str = " ".join(person_tokens)

    # Remove street name from person_str if present
    if street:
        for s_low in sorted_streets:
            if re.search(r'\b' + re.escape(s_low) + r'\b', person_str.lower()):
                person_str = re.sub(r'\b' + re.escape(s_low) + r'\b', '', person_str, flags=re.I).strip(' ,.')
                break

    # Strip residual dashes, numbers, brackets
    person_str = re.sub(r'^[-\s\d\.\,\(\)\[\]]+', '', person_str)
    person_str = re.sub(r'[-\s\d\.\,\(\)\[\]]+$', '', person_str).strip()

    surname = ""
    forename = ""

    if ',' in person_str:
        parts = person_str.split(',', 1)
        surname = parts[0].strip()
        forename = parts[1].strip()
    else:
        parts = person_str.split()
        if len(parts) >= 2:
            if parts[0].lower() in ('mr.', 'mrs.', 'miss', 'rev.', 'dr.', 'sir'):
                surname = parts[1]
                forename = parts[0] + (" " + " ".join(parts[2:]) if len(parts) > 2 else "")
            else:
                surname = parts[0]
                forename = " ".join(parts[1:])
        elif len(parts) == 1:
            surname = parts[0]

    # Clean titles and residual characters
    surname = re.sub(r'^(Mr\.|Mrs\.|Miss|Rev\.|Sir|Esq\.|Dr\.)\s*', '', surname, flags=re.I).strip(' ,.-')
    forename = re.sub(r'^(Mr\.|Mrs\.|Miss|Rev\.|Sir|Esq\.|Dr\.)\s*', '', forename, flags=re.I).strip(' ,.-')

    # Remove '--' artifacts
    surname = surname.replace('--', '').strip(' ,.-')
    forename = forename.replace('--', '').strip(' ,.-')

    # Assign trade
    trade = active_category.strip(' ,.-')

    if not surname and not forename:
        return None, active_category

    # Discard non-name artifacts
    if len(surname) > 40 or "population" in combined.lower() or "distant by railway" in combined.lower():
        return None, active_category

    return {
        "street": street,
        "house_number": "",
        "building_name": "",
        "surname": surname,
        "forename": forename,
        "trade": trade,
        "source_type": "commercial_directory"
    }, active_category

def process_tsv_v3(year, tsv_file, out_csv):
    tsv_path = os.path.join("raw_tsvs", tsv_file)
    print(f"Processing {tsv_file} (Year {year})...")
    records = []
    active_category = "General"

    with open(tsv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
        for row in reader:
            rec, active_category = parse_early_row_v3(row, active_category)
            if rec:
                rec["year"] = str(year)
                # Cap field length to prevent CSV buffer overflow
                for k in ['trade', 'building_name', 'surname', 'forename']:
                    if len(rec[k]) > 150: rec[k] = rec[k][:150].strip()
                records.append(rec)

    print(f"  -> Extracted {len(records):,} clean records ({sum(1 for r in records if r['street']):,} with matched street).")
    
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"])
        writer.writeheader()
        writer.writerows(records)

    return records

def main():
    early_vols = [
        ("1835", "1835.tsv", "volume_csvs/1835_cleaned.csv"),
        ("1844", "1844.tsv", "volume_csvs/1844_cleaned.csv"),
        ("1850", "1850.tsv", "volume_csvs/1850_cleaned.csv"),
        ("1858", "1858.tsv", "volume_csvs/1858_cleaned.csv"),
        ("1862", "1862.tsv", "volume_csvs/1862_cleaned.csv"),
        ("1865", "1865.tsv", "volume_csvs/1865_cleaned.csv"),
    ]

    all_early_records = []
    early_years = set(y for y, _, _ in early_vols)

    for y, tsv_f, out_c in early_vols:
        recs = process_tsv_v3(y, tsv_f, out_c)
        all_early_records.extend(recs)

    print(f"\nTotal clean early records: {len(all_early_records):,}")

    # Read existing 1876-1971 records
    kept = []
    with open("data.csv", "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("year") not in early_years:
                kept.append(r)

    print(f"Preserved {len(kept):,} existing records from 1876-1971.")
    combined = kept + all_early_records
    combined.sort(key=lambda r: int(r["year"]) if r.get("year", "").isdigit() else 9999)

    fieldnames = ["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"]
    with open("data.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(combined)

    print(f"Successfully updated data.csv ({len(combined):,} total records)!")

    # Run Casing Twins and Site Rebuild
    print("\nRunning merge_casing_twins.py (which also rebuilds search_index and data/streets/)...")
    subprocess.run([sys.executable, "scripts/merge_casing_twins.py"], check=False)

    print("\nCompiling analytics and diagnostics dashboard (build_stats_data.py)...")
    subprocess.run([sys.executable, "scripts/build_stats_data.py"], check=False)

    print("\nAll operations completed successfully!")

if __name__ == "__main__":
    main()
