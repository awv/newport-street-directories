import csv
import json
import os

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

with open("data.csv", "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))

targets = [
    "Aberbeeg whf",
    "Cambrian whf",
    "Cattle Market",
    "Charwood Road",
    "Charnwood Road",
    "Christchurch Cemetery",
    "Clarance Place",
    "Commercial Buildings",
    "Corpus Christi Street",
    "Cross Hands Cottages",
    "Dock Street Chambers",
    "Dock Street continued",
    "Ebenezer Terrace (Chapel)",
    "Farmwood Cottages",
    "Farm Cottages",
    "Fulford'S Cottages",
    "Fulford's Cottages",
    "Gasens Street",
    "Geo Street",
    "Highbury Chambers",
    "Lansdowne Cottages",
    "Jayne's Buildings",
    "Llwnyderi Road",
    "Llwynderi Road",
    "Lyn Street",
    "Maindee Board Schools",
    "Maindee Municipal Bldgs",
    "Maindee Street List",
    "Merriot's Place",
    "Merriott's Place",
    "Metropolitan Bank Chambers",
    "Midland Bank Chambers",
    "Mill Parade continued",
    "Monmouth Chambers",
    "Mount Pleasant Cottages",
    "Nelson St. (Upper)",
    "New Buildings",
    "Newport Street Directory",
    "Orchard Buildings",
    "Pembroke Chambers",
    "Presbyterian Church",
    "Primrose Cottages",
    "Pyne's Cottages"
]

target_lower = {t.lower(): t for t in targets}

by_target = {}
for i, r in enumerate(reader):
    st = r.get("street", "").strip()
    st_low = st.lower()
    if st_low in target_lower:
        orig = target_lower[st_low]
        by_target.setdefault(orig, []).append((i, r))

print(f"Total targets matched: {len(by_target)} of {len(targets)}")
for t in targets:
    if t in by_target:
        rows = by_target[t]
        years = sorted(list(set(r.get("year", "") for idx, r in rows)))
        print(f"\n=== {t} ({len(rows)} rows, years: {years}) ===")
        # Print first few rows
        for idx, r in rows[:6]:
            print(f"  [{idx}] {r.get('year')} | #{r.get('house_number')} | {r.get('forename')} {r.get('surname')} | {r.get('trade')} | {r.get('building_name')}")
        # Print surrounding for the first row
        first_idx = rows[0][0]
        print(f"  Surrounding before row {first_idx}:")
        for j in range(max(0, first_idx - 3), first_idx):
            print(f"    [{j}] {reader[j].get('year')} | {reader[j].get('street')} | #{reader[j].get('house_number')} | {reader[j].get('forename')} {reader[j].get('surname')}")
        last_idx = rows[-1][0]
        print(f"  Surrounding after row {last_idx}:")
        for j in range(last_idx + 1, min(len(reader), last_idx + 4)):
            print(f"    [{j}] {reader[j].get('year')} | {reader[j].get('street')} | #{reader[j].get('house_number')} | {reader[j].get('forename')} {reader[j].get('surname')}")
    else:
        print(f"\n=== {t} (0 rows found) ===")
