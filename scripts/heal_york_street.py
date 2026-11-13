import csv
import json
import os
import shutil

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_york_street"
MASTER_FILE = "master_streets.json"

if not os.path.exists(BACKUP_CSV):
    print(f"Creating backup {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)

rows = []
count = 0
with open(DATA_CSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for r in reader:
        if r.get("street") == "York Street":
            r["street"] = "York Place"
            count += 1
        rows.append(r)

print(f"Updated {count} rows from York Street -> York Place in data.csv")

with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

with open(MASTER_FILE, "r", encoding="utf-8") as f:
    master_data = json.load(f)

streets_dict = master_data.get("streets", {})
if "york-place" in streets_dict:
    yp = streets_dict["york-place"]
    aliases = set(yp.get("aliases", []))
    aliases.add("York Street")
    yp["aliases"] = sorted(list(aliases))
    print("york-place aliases:", yp["aliases"])

if "york-street" in streets_dict:
    del streets_dict["york-street"]
    print("Deleted york-street from master_streets.json")

with open(MASTER_FILE, "w", encoding="utf-8") as f:
    json.dump(master_data, f, indent=2, ensure_ascii=False)

print("master_streets.json updated successfully.")
