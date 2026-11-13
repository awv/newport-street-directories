import csv
import json
import os

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

print("Starting healing script for Rivers De -> Riverside...")

with open("data.csv", "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))
    fieldnames = reader[0].keys() if reader else []

fixed_count = 0
for r in reader:
    if r.get("street") == "Rivers De":
        r["street"] = "Riverside"
        hn = r.get("house_number", "").strip()
        fn = r.get("forename", "").strip()
        sn = r.get("surname", "").strip()
        tr = r.get("trade", "").strip()

        # Fix door 37 Jas. Wm. Percy Gunter (Percy was placed into trade)
        if hn == "37" and sn == "Gunter" and tr == "Percy":
            r["forename"] = "Jas. Wm. Percy"
            r["trade"] = ""

        # Fix door 39 Chas. Sheppard Engine Driver (eng. was placed into forename, Driver into trade)
        if hn == "39" and "Sheppard" in sn:
            r["forename"] = "Chas."
            r["surname"] = "Sheppard"
            r["trade"] = "Engine Driver"

        # Normalize abbreviations
        if r.get("trade") == "Ironwkr":
            r["trade"] = "Ironworker"
        elif r.get("trade") == "Carpmtr":
            r["trade"] = "Carpenter"
        elif r.get("trade") == "Coal Trmr":
            r["trade"] = "Coal Trimmer"
        elif r.get("trade") == "Wiredrwr":
            r["trade"] = "Wire Drawer"

        fixed_count += 1

print(f"Reunited {fixed_count} rows of Rivers De with Riverside.")

with open("data.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(reader)
print("Updated data.csv successfully.")

# Update master_streets.json
with open("master_streets.json", "r", encoding="utf-8") as f:
    ms = json.load(f)

streets = ms.get("streets", {})
if "riverside" in streets:
    if "Rivers De" not in streets["riverside"].get("aliases", []):
        streets["riverside"].setdefault("aliases", []).append("Rivers De")
        print("Added 'Rivers De' as alias to Riverside in master_streets.json")

# Clean up stale slug if present
if "rivers-de" in streets:
    del streets["rivers-de"]
    print("Deleted stale slug 'rivers-de' from master_streets.json")

with open("master_streets.json", "w", encoding="utf-8") as f:
    json.dump(ms, f, indent=2, ensure_ascii=False)

# Delete stale json if present
stale_json = "data/streets/rivers-de.json"
if os.path.exists(stale_json):
    os.remove(stale_json)
    print(f"Removed stale {stale_json}")
