#!/usr/bin/env python3
"""
recompile_cached_volumes.py
Universal recompiler for all vision-extracted directories (1878–1910)
from cached scan CSVs in scratch/*_vision_rebuild.
Handles all split district/grid references (C., P., B.T., E 5, C 5, etc.)
and multi-comma trades cleanly.
"""

import os
import glob
import csv
import re
import shutil
import subprocess

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

PAT_DISTRICT = re.compile(r'^\s*\(?[A-Z]\.?(\s*[A-Z]\.?)?(\s*\d+[a-z]?)?\)?\.?\s*$', re.I)

def parse_resident_row(row, current_street):
    # 1. Strip off split district/grid code from street column if present in row[2]
    if len(row) > 3 and PAT_DISTRICT.match(row[2]):
        row = [row[0], row[1]] + row[3:]
        
    st = row[1].strip() if len(row) > 1 and row[1].strip() else current_street
    hn = row[2].strip() if len(row) > 2 else ''
    bldg = row[3].strip() if len(row) > 3 else ''
    
    # 2. Check for extra blank columns before forename (e.g. 1878 unnumbered rows)
    if len(row) >= 9 and row[4] == '' and row[5] != '' and row[6] != '':
        fn = row[5].strip()
        sn = row[6].strip()
        tr = ', '.join([c.strip() for c in row[7:] if c.strip()])
    else:
        fn = row[4].strip() if len(row) > 4 else ''
        sn = row[5].strip() if len(row) > 5 else ''
        tr = ', '.join([c.strip() for c in row[6:] if c.strip()])
        
    return st, hn, bldg, fn, sn, tr

def recompile_year(year):
    out_dir = os.path.join(PROJECT_DIR, "scratch", f"{year}_vision_rebuild")
    if not os.path.isdir(out_dir):
        return None, 0
        
    csvs = sorted(glob.glob(os.path.join(out_dir, "IMG_*.csv")))
    valid_csvs = [f for f in csvs if os.path.getsize(f) > 250]
    if not valid_csvs:
        return None, 0

    master_csv = os.path.join(PROJECT_DIR, "volume_csvs", f"{year}_cleaned.csv")
    backup_csv = os.path.join(PROJECT_DIR, "volume_csvs", f"{year}_cleaned.csv.bak_before_shift_fix")
    if os.path.exists(master_csv) and not os.path.exists(backup_csv):
        shutil.copy2(master_csv, backup_csv)

    total_entries = 0
    current_street = "Unknown"

    with open(master_csv, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"])

        for page in valid_csvs:
            with open(page, "r", encoding="utf-8", errors="ignore") as f_in:
                reader = csv.reader(f_in)
                for row in reader:
                    if not row or row[0].strip().lower() == "type":
                        continue
                    rtype = row[0].strip().lower()

                    if rtype == "street":
                        cand = row[1].strip() if len(row) > 1 else ""
                        if cand:
                            current_street = cand
                    elif rtype in ("entry", "resident"):
                        st, hn, bldg, fn, sn, tr = parse_resident_row(row, current_street)

                        if not sn and not fn and not bldg and not tr:
                            continue

                        writer.writerow([str(year), st, hn, bldg, sn, fn, tr, ""])
                        total_entries += 1

    print(f"[{year}] Compiled {total_entries:,} entries cleanly.")
    return master_csv, total_entries

def run():
    print("=== Recompiling All Cached Vision Directories with Universal Alignment ===")
    
    backup_data = "data.csv.bak_before_recompile"
    if os.path.exists("data.csv") and not os.path.exists(backup_data):
        shutil.copy2("data.csv", backup_data)
        print(f"Backed up data.csv -> {backup_data}")

    cached_dirs = sorted(glob.glob("scratch/*_vision_rebuild"))
    years_processed = []
    
    for cdir in cached_dirs:
        bname = os.path.basename(cdir)
        year_str = bname.split("_")[0]
        if year_str.isdigit():
            yr = int(year_str)
            m_csv, tot = recompile_year(yr)
            if tot > 0:
                years_processed.append(yr)

    print(f"\nRecompiled {len(years_processed)} directories: {years_processed}")

    print("\nMerging recompiled records into data.csv...")
    header = None
    other_rows = []
    
    recompiled_years_set = {str(y) for y in years_processed}
    with open("data.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row and row[0] not in recompiled_years_set:
                other_rows.append(row)

    print(f"Preserved {len(other_rows):,} rows from non-recompiled years.")

    all_rows = list(other_rows)
    for yr in years_processed:
        cleaned_csv = os.path.join("volume_csvs", f"{yr}_cleaned.csv")
        if os.path.exists(cleaned_csv):
            with open(cleaned_csv, "r", encoding="utf-8") as cf:
                creader = csv.reader(cf)
                next(creader) # skip header
                for r in creader:
                    if len(r) < len(header):
                        r.extend([""] * (len(header) - len(r)))
                    all_rows.append(r[:len(header)])

    print(f"Total rows to write to data.csv: {len(all_rows):,}")
    with open("data.csv", "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(header)
        writer.writerows(all_rows)

    print("data.csv updated successfully!")

    print("\nRunning canonical normalization and trade cleanup...")
    subprocess.run(["python3", "scripts/clean_non_streets.py"], check=True)
    print("\n=== RECOMPILE AND REPAIR COMPLETE! ===")

if __name__ == "__main__":
    run()
