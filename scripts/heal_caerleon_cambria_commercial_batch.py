#!/usr/bin/env python3
"""
heal_caerleon_cambria_commercial_batch.py
-----------------------------------------
Heals 14 street header variants and page-bleed artifacts into canonical streets:
  - Caerleon Road (149), Caerleon Road (262), CAERLEON ROAD continued, Caerleon Road. [OSBORNE PLACE] -> Caerleon Road
  - Commercial-st, Commercial Street (continued), Commercial St. continued -> Commercial Street
  - Can Street -> Canal Terrace
  - Cli (High-Street (Return)) -> Clarence Street
  - Carpenter's A. Lane -> Carpenter's Arms Lane
  - CAMBRIA PLACE--to No. 64, CAMBRIA PLACE--to No. 140, Cambria cottages (15), Cambria Cottages -> Cambria Place
"""

import csv
import sys
import os
import shutil
import json

csv.field_size_limit(sys.maxsize)

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_caerleon_cambria_commercial_heal"
MASTER_JSON = "master_streets.json"

STREET_MAP = {
    "Caerleon Road (149)": "Caerleon Road",
    "Caerleon Road (262)": "Caerleon Road",
    "CAERLEON ROAD continued": "Caerleon Road",
    "Caerleon Road. [OSBORNE PLACE]": "Caerleon Road",
    "Commercial-st": "Commercial Street",
    "Commercial Street (continued)": "Commercial Street",
    "Commercial St. continued": "Commercial Street",
    "Can Street": "Canal Terrace",
    "Cli (High-Street (Return))": "Clarence Street",
    "Carpenter's A. Lane": "Carpenter's Arms Lane",
    "CAMBRIA PLACE--to No. 64": "Cambria Place",
    "CAMBRIA PLACE--to No. 140": "Cambria Place",
    "Cambria cottages (15)": "Cambria Place",
    "Cambria Cottages": "Cambria Place",
}

def main():
    if not os.path.exists(BACKUP_CSV):
        print(f"Creating safety backup: {BACKUP_CSV}...")
        shutil.copyfile(DATA_CSV, BACKUP_CSV)
    else:
        print(f"Backup already exists: {BACKUP_CSV}")

    print(f"Reading {DATA_CSV}...")
    rows = []
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            rows.append(r)

    print(f"Loaded {len(rows):,} rows. Applying canonical street merges...")
    changes = {}
    total_changed = 0

    for r in rows:
        old_st = r.get("street", "").strip()
        if old_st in STREET_MAP:
            new_st = STREET_MAP[old_st]
            r["street"] = new_st
            total_changed += 1
            key = f"{old_st} -> {new_st}"
            changes[key] = changes.get(key, 0) + 1

    print(f"\nHealed {total_changed} total records into canonical streets:")
    for k, v in sorted(changes.items()):
        print(f"  {k}: {v} records")

    print(f"\nWriting updated records back to {DATA_CSV}...")
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("data.csv updated successfully.")

    # Update master_streets.json metadata for Cambria Place
    if os.path.exists(MASTER_JSON):
        print(f"\nUpdating {MASTER_JSON}...")
        with open(MASTER_JSON, "r", encoding="utf-8") as f:
            ms_data = json.load(f)
            streets = ms_data.get("streets", {})

        if "cambria-place" in streets:
            cp = streets["cambria-place"]
            aliases = set(cp.get("aliases", []))
            aliases.update(["Cambria Cottages", "CAMBRIA PLACE--to No. 64", "CAMBRIA PLACE--to No. 140"])
            cp["aliases"] = sorted(list(aliases))
            cp["notes"] = "Historical terrace located along the upper spine of Stow Hill opposite the Union Workhouse / Infirmary (St. Woolos). Renumbered from 54–64 in Victorian era, to 120–146 in Edwardian/Interwar era, and 216–226 by 1936."
            print("  Updated cambria-place notes and aliases.")

        if "cambria-cottages" in streets:
            del streets["cambria-cottages"]
            print("  Removed redundant cambria-cottages entry from master_streets.json.")

        with open(MASTER_JSON, "w", encoding="utf-8") as f:
            json.dump(ms_data, f, indent=2)

    print("\nRebuilding site data (data/streets/*.json, data/streets.json, data/search_index.json)...")
    import build_site_data
    build_site_data.main()

    print("\nBatch healing and site rebuild complete!")

if __name__ == "__main__":
    main()
