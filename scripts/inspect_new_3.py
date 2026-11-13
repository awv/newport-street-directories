import csv
import json
import os

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

with open("data.csv", "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))

targets = ["Provident Place", "Providende Place", "Providence Place", "Quintila Street", "St. Julian's Street", "St. Julian Street"]

for t in targets:
    rows = [(i, r) for i, r in enumerate(reader) if r.get("street") == t]
    print(f"\n=== {t} ({len(rows)} rows) ===")
    years = sorted(list(set(r.get("year", "") for idx, r in rows)))
    print(f"Years: {years}")
    for idx, r in rows[:8]:
        print(f"  [{idx}] {r.get('year')} | #{r.get('house_number')} | {r.get('forename')} {r.get('surname')} | {r.get('trade')} | {r.get('building_name')}")
    if rows:
        first_i = rows[0][0]
        last_i = rows[-1][0]
        print(f"  Surrounding before [{first_i}]:")
        for j in range(max(0, first_i - 3), first_i):
            print(f"    [{j}] {reader[j].get('year')} | {reader[j].get('street')} | #{reader[j].get('house_number')} | {reader[j].get('forename')} {reader[j].get('surname')}")
        print(f"  Surrounding after [{last_i}]:")
        for j in range(last_i + 1, min(len(reader), last_i + 4)):
            print(f"    [{j}] {reader[j].get('year')} | {reader[j].get('street')} | #{reader[j].get('house_number')} | {reader[j].get('forename')} {reader[j].get('surname')}")
