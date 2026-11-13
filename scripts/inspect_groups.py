import csv
import json
import os

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

with open("data.csv", "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))

def inspect_group(name, filter_func):
    matches = [(i, r) for i, r in enumerate(reader) if filter_func(r)]
    print(f"\n==================== {name} ({len(matches)} rows) ====================")
    years = sorted(list(set(r.get("year", "") for idx, r in matches)))
    print(f"Years: {years}")
    for idx, r in matches[:10]:
        print(f"  [{idx}] {r.get('year')} | {r.get('street')} | #{r.get('house_number')} | {r.get('forename')} {r.get('surname')} | {r.get('trade')} | {r.get('building_name')}")
    if matches:
        first_idx = matches[0][0]
        print(f"  Surrounding before [{first_idx}]:")
        for j in range(max(0, first_idx - 3), first_idx):
            print(f"    [{j}] {reader[j].get('year')} | {reader[j].get('street')} | #{reader[j].get('house_number')} | {reader[j].get('forename')} {reader[j].get('surname')}")
        last_idx = matches[-1][0]
        print(f"  Surrounding after [{last_idx}]:")
        for j in range(last_idx + 1, min(len(reader), last_idx + 4)):
            print(f"    [{j}] {reader[j].get('year')} | {reader[j].get('street')} | #{reader[j].get('house_number')} | {reader[j].get('forename')} {reader[j].get('surname')}")

inspect_group("Commercial Buildings", lambda r: r.get("street") == "Commercial Buildings")
inspect_group("Corpus Christi Street", lambda r: "corpus" in r.get("street", "").lower())
inspect_group("Cross Hands Cottages", lambda r: "cross hands cottages" in r.get("street", "").lower())
inspect_group("Dock Street Chambers", lambda r: "dock street chambers" in r.get("street", "").lower())
inspect_group("Dock Street continued", lambda r: "dock street continued" in r.get("street", "").lower())
inspect_group("Ebenezer Terrace (Chapel)", lambda r: "ebenezer" in r.get("street", "").lower() and "chapel" in r.get("street", "").lower())
inspect_group("Farmwood Cottages vs Farm Cottages", lambda r: r.get("street") in ["Farmwood Cottages", "Farm Cottages"])
inspect_group("Fulford'S Cottages", lambda r: "fulford" in r.get("street", "").lower())
inspect_group("Gasens Street", lambda r: "gasens" in r.get("street", "").lower())
inspect_group("Geo Street", lambda r: r.get("street") == "Geo Street")
inspect_group("Highbury Chambers", lambda r: "highbury" in r.get("street", "").lower())
inspect_group("Lansdowne Cottages", lambda r: "lansdowne cottages" in r.get("street", "").lower())
inspect_group("Jayne's Buildings", lambda r: "jayne" in r.get("street", "").lower())
inspect_group("Llwnyderi Road", lambda r: "llwnyderi" in r.get("street", "").lower() or "llwynderi" in r.get("street", "").lower())
inspect_group("Lyn Street", lambda r: r.get("street") == "Lyn Street")
inspect_group("Maindee Board Schools", lambda r: "maindee board" in r.get("street", "").lower())
inspect_group("Maindee Municipal Bldgs", lambda r: "maindee municipal" in r.get("street", "").lower())
inspect_group("Maindee Street List", lambda r: "maindee street list" in r.get("street", "").lower())
inspect_group("Merriot's Place", lambda r: "merriot" in r.get("street", "").lower())
inspect_group("Metropolitan Bank Chambers", lambda r: "metropolitan bank" in r.get("street", "").lower())
inspect_group("Midland Bank Chambers", lambda r: "midland bank" in r.get("street", "").lower())
inspect_group("Mill Parade continued", lambda r: "mill parade continued" in r.get("street", "").lower())
inspect_group("Monmouth Chambers", lambda r: "monmouth chambers" in r.get("street", "").lower())
inspect_group("Mount Pleasant Cottages", lambda r: "mount pleasant cottages" in r.get("street", "").lower() or "mt. pleasant cottages" in r.get("street", "").lower())
inspect_group("Nelson St. (Upper)", lambda r: "nelson" in r.get("street", "").lower() and "upper" in r.get("street", "").lower())
inspect_group("New Buildings", lambda r: r.get("street") == "New Buildings")
inspect_group("Newport Street Directory", lambda r: r.get("street") == "Newport Street Directory")
inspect_group("Cattle Market", lambda r: r.get("street") == "Cattle Market")
