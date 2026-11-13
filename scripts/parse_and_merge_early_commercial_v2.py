#!/usr/bin/env python3
"""
parse_and_merge_early_commercial_v2.py
Precision parsing for early commercial directories (1835-1865).
Corrects column bleed, separates surnames from forenames and trades,
identifies streets accurately, and compiles into data.csv.
"""

import os
import sys
import re
import csv
import json
import subprocess

# Allow reading large historical text fields
csv.field_size_limit(sys.maxsize)

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

# Load Master Streets
with open("master_streets.json", "r", encoding="utf-8") as f:
    master_data = json.load(f)["streets"]

street_lookup = {}
for s_slug, s_info in master_data.items():
    c_name = s_info.get("canonical_name", "").strip()
    if c_name and len(c_name) > 3:
        street_lookup[c_name.lower()] = c_name

# Common 19th-century street variants
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
    "king's hill": "King's Hill", "king-st": "King Street", "king st": "King Street"
}
for k, v in variants.items():
    street_lookup[k] = v

sorted_streets = sorted(street_lookup.keys(), key=lambda x: len(x), reverse=True)

def find_street_in_text(text):
    if not text: return ""
    t_low = text.lower()
    for s_low in sorted_streets:
        if re.search(r'\b' + re.escape(s_low) + r'\b', t_low):
            return street_lookup[s_low]
    return ""

def parse_early_row(row, active_category):
    tokens = [c.strip() for c in row if c.strip() and c.strip().lower() != 'nan']
    if not tokens:
        return None, active_category

    combined = " ".join(tokens)

    # 1. Skip non-resident text / metadata blocks
    if len(combined) > 160 and not any(kw in combined.lower() for kw in ['esq', 'rev', 'mr.', 'mrs.', 'miss', 'inn', 'hotel']):
        return None, active_category

    # 2. Check if Category Heading (e.g. ['GROCERS & TEA DEALERS.'], ['Attorneys.'], ['BOOT & SHOE MAKERS'])
    if len(tokens) == 1:
        tok = tokens[0].strip(' .:')
        if tok.isupper() or any(kw in tok.lower() for kw in ['dealers', 'makers', 'attorneys', 'clergy', 'surgeons', 'inns', 'taverns', 'blacksmiths', 'bakers', 'butchers', 'carpenters', 'joiners']):
            return None, tok.title()

    # 3. Detect Street in any token
    street = ""
    street_token_idx = -1
    for i, tok in enumerate(tokens):
        st = find_street_in_text(tok)
        if st:
            street = st
            street_token_idx = i
            break

    # 4. Detect Category / Trade in tokens if present
    trade = active_category
    trade_token_idx = -1
    for i, tok in enumerate(tokens):
        if i == street_token_idx: continue
        clean_tok = tok.strip(' .:')
        if clean_tok.isupper() and len(clean_tok) > 4:
            trade = clean_tok.title()
            trade_token_idx = i
            break
        elif any(clean_tok.lower().startswith(kw) for kw in ['cabinet makers', 'booksellers', 'boot & shoe', 'coal owners', 'iron founders', 'artists', 'tailors', 'drapers']):
            # Found inline trade string (e.g. "Booksellers & Stationers, (and trunk maker) High street")
            parts = clean_tok.split(',', 1)
            trade = parts[0].strip().title()
            trade_token_idx = i
            break

    # 5. Extract Names from remaining tokens
    name_tokens = [tok for i, tok in enumerate(tokens) if i not in (street_token_idx, trade_token_idx)]
    
    surname = ""
    forename = ""

    if len(name_tokens) >= 2:
        surname = name_tokens[0]
        forename = " ".join(name_tokens[1:])
    elif len(name_tokens) == 1:
        tok = name_tokens[0]
        if "," in tok:
            parts = tok.split(",", 1)
            surname = parts[0].strip()
            forename = parts[1].strip()
        else:
            parts = tok.split()
            if len(parts) >= 2:
                # E.g. "Farr Henry"
                surname = parts[0]
                forename = " ".join(parts[1:])
            else:
                surname = tok

    # Clean surname and forename of address spillovers or titles
    surname = re.sub(r'^(Mr\.|Mrs\.|Miss|Rev\.|Sir|Esq\.|Dr\.)\s*', '', surname, flags=re.I).strip(' ,.')
    forename = re.sub(r'^(Mr\.|Mrs\.|Miss|Rev\.|Sir|Esq\.|Dr\.)\s*', '', forename, flags=re.I).strip(' ,.')

    # If street name ended up inside forename or surname, strip it
    for s_low in sorted_streets:
        s_canon = street_lookup[s_low]
        if s_low in forename.lower():
            street = s_canon
            forename = re.sub(re.escape(s_low), '', forename, flags=re.I).strip(' ,.')
        if s_low in surname.lower():
            street = s_canon
            surname = re.sub(re.escape(s_low), '', surname, flags=re.I).strip(' ,.')

    # Clean punctuation
    surname = surname.strip(' ,.')
    forename = forename.strip(' ,.')
    trade = trade.strip(' ,.')

    if not surname and not forename and not trade:
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

def process_tsv(year, tsv_file, out_csv):
    tsv_path = os.path.join("raw_tsvs", tsv_file)
    print(f"Processing {tsv_file} (Year {year})...")
    records = []
    active_category = "General"

    with open(tsv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
        for row in reader:
            rec, active_category = parse_early_row(row, active_category)
            if rec:
                rec["year"] = str(year)
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
        recs = process_tsv(y, tsv_f, out_c)
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
