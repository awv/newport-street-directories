import csv
import json
import os
import re
import sys

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_street_cleanup"

if not os.path.exists(BACKUP_CSV):
    import shutil
    shutil.copyfile(DATA_CSV, BACKUP_CSV)
    print(f"Created safety backup {BACKUP_CSV}")

rows = []
with open(DATA_CSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for r in reader:
        rows.append(r)

print(f"Total rows in data.csv: {len(rows):,}")

# Specific noisy street patterns to catch
noise_patterns = [
    r'^\(return\)',
    r'^\[left Hand Side',
    r'^\[LEFT HAND SIDE',
    r'^\[right Hand Side',
    r'^-\t-\tHere is',
    r'^\.\t\.\t486',
    r'^158\t\}',
    r'^170 Withers',
    r'^\t\t\t.+Court',
]

def is_noise_street(st):
    if not st: return True
    st_clean = st.strip()
    for p in noise_patterns:
        if re.search(p, st, flags=re.I):
            return True
    return False

# Re-assign noisy street records to their actual parent street
fixed_count = 0
last_good_street_by_year = {}

for i, r in enumerate(rows):
    yr = r.get("year", "")
    st = r.get("street", "").strip()
    
    # Specific known fixes
    if "(return.) . Salisbury Road" in st:
        r["street"] = "Salisbury Road"
        fixed_count += 1
        continue
    elif "EDWIN STREET. (return)" in st:
        r["street"] = "Edwin Street"
        fixed_count += 1
        continue
    elif "Jones' Court" in st:
        r["street"] = "Jones' Court"
        fixed_count += 1
        continue
    elif "Toombs' Court" in st:
        r["street"] = "Toombs' Court"
        fixed_count += 1
        continue
    elif st == "158\t}":
        # Belongs to Caerleon Road
        r["street"] = "Caerleon Road"
        fixed_count += 1
        continue
    elif st == "170 Withers F.a":
        # 170 Caerleon Road
        r["street"] = "Caerleon Road"
        r["house_number"] = "170"
        r["surname"] = "Withers"
        r["forename"] = "F. A."
        r["trade"] = "confectioner & stationer"
        fixed_count += 1
        continue
        
    if is_noise_street(st):
        # Look backwards in the same year for the previous valid street
        parent_street = ""
        for j in range(i-1, max(0, i-300), -1):
            cand = rows[j].get("street", "").strip()
            if rows[j].get("year") == yr and not is_noise_street(cand) and len(cand) > 3:
                # Clean up any trailing notes
                parent_street = cand.split("—")[0].split("\t")[0].strip()
                break
                
        if parent_street:
            r["street"] = parent_street
            fixed_count += 1
        else:
            # Fallback to last known good street for year
            if yr in last_good_street_by_year:
                r["street"] = last_good_street_by_year[yr]
                fixed_count += 1
    else:
        # Clean clean street name
        clean_st = st.split("—")[0].split("\t")[0].strip()
        r["street"] = clean_st
        last_good_street_by_year[yr] = clean_st

print(f"Re-assigned {fixed_count:,} records with noisy street headers to valid parent streets.")

# Save data.csv
with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Saved updated data.csv!")

# Clean out legacy orphaned json files in data/streets/
bad_slugs = [
    "return-market", "return", "return-salisbury-road", "here-is-albert-avenue",
    "here-is-oak-street", "486", "158", "170-withers-f-a", "left-hand-side",
    "left-hand-side-market", "left-hand-sidel", "right-hand-side", "right-hand-sidel",
    "t-t-tjones-court", "t-t-ttoombs-court"
]
for slug in bad_slugs:
    p = os.path.join("data", "streets", f"{slug}.json")
    if os.path.exists(p):
        os.remove(p)
        print(f"Removed orphaned file: {p}")

