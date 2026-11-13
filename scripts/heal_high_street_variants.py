import csv
import json
import os
import shutil

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_high_street_variants"
MASTER_FILE = "master_streets.json"

if not os.path.exists(BACKUP_CSV):
    print(f"Creating backup {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)
else:
    print(f"Backup {BACKUP_CSV} already exists.")

# 1. Update data.csv
rows = []
counts = {
    "High Street-continued": 0,
    "High Street Directory": 0,
    "High street (from the Bridge to Commercial street)": 0,
    "High-street": 0,
    "High Street (Return)": 0
}

with open(DATA_CSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for r in reader:
        st = r.get("street")
        if st in counts:
            counts[st] += 1
            if st == "High Street (Return)":
                r["street"] = "Clarence Street"
            else:
                r["street"] = "High Street"
        rows.append(r)

print("Replacement counts in data.csv:")
for k, v in counts.items():
    print(f"  {k}: {v}")

with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("data.csv updated successfully.")

# 2. Update master_streets.json
with open(MASTER_FILE, "r", encoding="utf-8") as f:
    master_data = json.load(f)

streets_dict = master_data.get("streets", {})

# High Street aliases
if "high-street" in streets_dict:
    hs = streets_dict["high-street"]
    hs_aliases = set(hs.get("aliases", []))
    new_hs_aliases = [
        "High Street-continued",
        "High Street Directory",
        "High street (from the Bridge to Commercial street)",
        "High-street"
    ]
    for a in new_hs_aliases:
        hs_aliases.add(a)
    hs["aliases"] = sorted(list(hs_aliases))
    print("high-street aliases:", hs["aliases"])

# Clarence Street aliases
if "clarence-street" in streets_dict:
    cs = streets_dict["clarence-street"]
    cs_aliases = set(cs.get("aliases", []))
    cs_aliases.add("High Street (Return)")
    cs["aliases"] = sorted(list(cs_aliases))
    print("clarence-street aliases:", cs["aliases"])

# Clean up any leftover slugs if they exist
for orphan_slug in ["high-street-continued", "high-street-directory", "high-street-from-the-bridge-to-commercial-street", "high-street-return"]:
    if orphan_slug in streets_dict:
        del streets_dict[orphan_slug]
        print(f"Removed orphan slug {orphan_slug} from master_streets.json")

with open(MASTER_FILE, "w", encoding="utf-8") as f:
    json.dump(master_data, f, indent=2, ensure_ascii=False)

print("master_streets.json updated successfully.")
