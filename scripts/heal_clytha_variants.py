#!/usr/bin/env python3
"""
heal_clytha_variants.py
-----------------------
Consolidates all historical Clytha Park Road headings:
  - Clytha Park (1878-1890) -> Clytha Park Road
  - Clytha Park & Road (1892-1903) -> Clytha Park Road
  - Clytha Park and Road (1906) -> Clytha Park Road
  - Clytha Pk. & Road (1894) -> Clytha Park Road
  - Clytha Road (1903) -> Clytha Park Road
  - Clytha. Crescent (1886) -> Clytha Crescent
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
BACKUP_CSV = "data.csv.bak_before_clytha_heal"
MASTER_JSON = "master_streets.json"

CLYTHA_ROAD_VARIANTS = {
    "Clytha Park",
    "Clytha Park & Road",
    "Clytha Park and Road",
    "Clytha Pk. & Road",
    "Clytha Road",
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

    print(f"Loaded {len(rows):,} rows. Applying Clytha merges...")
    changes = {}
    total_changed = 0

    for r in rows:
        st = r.get("street", "").strip()
        if st in CLYTHA_ROAD_VARIANTS:
            r["street"] = "Clytha Park Road"
            total_changed += 1
            key = f"{st} -> Clytha Park Road"
            changes[key] = changes.get(key, 0) + 1
        elif st == "Clytha. Crescent":
            r["street"] = "Clytha Crescent"
            total_changed += 1
            key = "Clytha. Crescent -> Clytha Crescent"
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

    # Update master_streets.json metadata
    if os.path.exists(MASTER_JSON):
        print(f"\nUpdating {MASTER_JSON}...")
        with open(MASTER_JSON, "r", encoding="utf-8") as f:
            ms_data = json.load(f)
            streets = ms_data.get("streets", {})

        if "clytha-park-road" in streets:
            cpr = streets["clytha-park-road"]
            aliases = set(cpr.get("aliases", []))
            aliases.update(["Clytha Park", "Clytha Park & Road", "Clytha Park and Road", "Clytha Pk. & Road", "Clytha Road"])
            cpr["aliases"] = sorted(list(aliases))
            cpr["notes"] = "Victorian villa estate and thoroughfare laid out between Caerau and Fields Road. Originally listed as Clytha Park & Road, encompassing both detached park villas (Ivybank, Fernside, Cardigan Villa, The Limes) and numbered street properties."
            print("  Updated clytha-park-road notes and aliases.")

        if "clytha-park" in streets:
            del streets["clytha-park"]
            print("  Removed redundant clytha-park entry from master_streets.json.")

        with open(MASTER_JSON, "w", encoding="utf-8") as f:
            json.dump(ms_data, f, indent=2)

    print("\nRebuilding site data (data/streets/*.json, data/streets.json, data/search_index.json)...")
    import build_site_data
    build_site_data.main()

    print("\nBatch healing and site rebuild complete!")

if __name__ == "__main__":
    main()
