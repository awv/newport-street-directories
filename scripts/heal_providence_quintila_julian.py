import csv
import json
import os

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

print("Starting healing script for Providence Place, Quintila Street, and St. Julian's Street...")

with open("data.csv", "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))
    fieldnames = reader[0].keys() if reader else []

count_prov = 0
count_quin = 0
count_jul = 0

for r in reader:
    st = r.get("street", "").strip()
    
    # 1. Provident Place / Providende Place -> Providence Place
    if st in ["Provident Place", "Providende Place"]:
        r["street"] = "Providence Place"
        count_prov += 1
        continue

    # 2. Quintila Street -> Quiet Woman's Row
    if st == "Quintila Street":
        r["street"] = "Quiet Woman's Row"
        count_quin += 1
        continue

    # 3. St. Julian's Street -> St. Julian Street
    if st == "St. Julian's Street":
        r["street"] = "St. Julian Street"
        count_jul += 1
        continue

print(f"Healed: {count_prov} Providence Place rows, {count_quin} Quiet Woman's Row rows, {count_jul} St. Julian Street rows.")

# Write data.csv
with open("data.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(reader)
print("Updated data.csv successfully.")

# Update master_streets.json
with open("master_streets.json", "r", encoding="utf-8") as f:
    ms = json.load(f)

streets = ms.get("streets", {})

# Add aliases
if "providence-place" in streets:
    for a in ["Provident Place", "Providende Place"]:
        if a not in streets["providence-place"].get("aliases", []):
            streets["providence-place"].setdefault("aliases", []).append(a)

if "quiet-woman-s-row" in streets:
    if "Quintila Street" not in streets["quiet-woman-s-row"].get("aliases", []):
        streets["quiet-woman-s-row"].setdefault("aliases", []).append("Quintila Street")

if "st-julian-street" in streets:
    if "St. Julian's Street" not in streets["st-julian-street"].get("aliases", []):
        streets["st-julian-street"].setdefault("aliases", []).append("St. Julian's Street")

# Remove stale slugs
stale_slugs = ["provident-place", "providende-place", "quintila-street", "st-julian-s-street"]
for s in stale_slugs:
    if s in streets:
        del streets[s]
        print(f"Removed stale slug from master_streets.json: {s}")
    p = os.path.join("data", "streets", f"{s}.json")
    if os.path.exists(p):
        os.remove(p)
        print(f"Removed stale json file: {p}")

with open("master_streets.json", "w", encoding="utf-8") as f:
    json.dump(ms, f, indent=2, ensure_ascii=False)
print("Updated master_streets.json successfully.")
