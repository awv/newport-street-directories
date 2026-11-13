#!/usr/bin/env python3
"""
heal_short_streets_batch.py
---------------------------
Heals 3-letter / truncated running header streets into their true canonical streets:
  - Ale (1906) -> Alexandra Road
  - Alm (1906) -> Allt-yr-yn
  - Alm Street (1895) -> Alma Street
  - Alt Street (1910) -> Allt-yr-yn (rural/un-numbered) & Annesley Road (numbered doors 35-48)
  - Arc (1906) -> Annesley Road (numbered doors 36-48) & Market Arcade (shops)
  - Art Street (1915) -> Arthur Street
  - Bal (1906) -> Baldwin Street
  - Ban (1906) -> Baneswell Road
  - Bas (1906) -> Bassaleg Road
  - Bri (1906) -> Bridge Street
  - Fre (1906) -> Frederick Street
  - Luc (1906) -> Lucas Street
"""

import csv
import sys
import os
import shutil
import subprocess

csv.field_size_limit(sys.maxsize)

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_short_streets_heal"

def map_row(r):
    st = r.get("street", "").strip()
    yr = r.get("year", "").strip()
    hn = r.get("house_number", "").strip()
    sn = r.get("surname", "").strip()

    if st == "Ale" and yr == "1906":
        return "Alexandra Road"
    if st == "Alm" and yr == "1906":
        return "Allt-yr-yn"
    if st == "Alm Street" and yr == "1895":
        return "Alma Street"
    if st == "Alt Street" and yr == "1910":
        if hn:
            return "Annesley Road"
        return "Allt-yr-yn"
    if st == "Arc" and yr == "1906":
        if hn or sn in ("Flint", "Cheeseman", "Webb", "Williams", "Brown", "Spicer", "Bevan", "Plumley", "Coate", "Smith", "French", "Davies", "Lewis"):
            return "Annesley Road"
        return "Market Arcade"
    if st == "Art Street" and yr == "1915":
        return "Arthur Street"
    if st == "Bal" and yr == "1906":
        return "Baldwin Street"
    if st == "Ban" and yr == "1906":
        return "Baneswell Road"
    if st == "Bas" and yr == "1906":
        return "Bassaleg Road"
    if st == "Bri" and yr == "1906":
        return "Bridge Street"
    if st == "Fre" and yr == "1906":
        return "Frederick Street"
    if st == "Luc" and yr == "1906":
        return "Lucas Street"
    return st

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

    print(f"Loaded {len(rows):,} rows. Applying canonical street healing...")
    changes = {}
    total_changed = 0

    for r in rows:
        old_st = r["street"]
        new_st = map_row(r)
        if old_st != new_st:
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

    print("\nRebuilding site data (data/streets/*.json, data/streets.json, data/search_index.json)...")
    import build_site_data
    build_site_data.main()

    print("\nBatch healing complete!")

if __name__ == "__main__":
    main()
