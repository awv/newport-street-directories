import csv
import json
import os

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

with open("data.csv", "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))

def inspect_details(title, filter_expr):
    rows = [(i, r) for i, r in enumerate(reader) if filter_expr(r)]
    print(f"\n==================== {title} ({len(rows)} rows) ====================")
    if not rows:
        return
    years = sorted(list(set(r.get("year", "") for idx, r in rows)))
    print(f"Years: {years}")
    for idx, r in rows[:8]:
        print(f"  [{idx}] {r.get('year')} | #{r.get('house_number')} | {r.get('forename')} {r.get('surname')} | {r.get('trade')} | {r.get('building_name')}")
    # Show before and after for each year block
    year_blocks = {}
    for idx, r in rows:
        year_blocks.setdefault(r.get("year"), []).append(idx)
    for yr, idxs in year_blocks.items():
        first_i = idxs[0]
        last_i = idxs[-1]
        print(f"  --- Year {yr} (rows {first_i}..{last_i}) ---")
        print("    Before:")
        for j in range(max(0, first_i - 3), first_i):
            print(f"      [{j}] {reader[j].get('year')} | {reader[j].get('street')} | #{reader[j].get('house_number')} | {reader[j].get('forename')} {reader[j].get('surname')}")
        print("    After:")
        for j in range(last_i + 1, min(len(reader), last_i + 4)):
            print(f"      [{j}] {reader[j].get('year')} | {reader[j].get('street')} | #{reader[j].get('house_number')} | {reader[j].get('forename')} {reader[j].get('surname')}")

# 3. Cattle Market
inspect_details("Cattle Market", lambda r: r.get("street") == "Cattle Market")

# 5. Christchurch Cemetery
inspect_details("Christchurch Cemetery", lambda r: r.get("street") == "Christchurch Cemetery")

# 8. Corpus Christi Street
inspect_details("Corpus Christi Street", lambda r: r.get("street") == "Corpus Christi Street")

# 13. Farmwood Cottages vs Farm Cottages
inspect_details("Farmwood Cottages", lambda r: r.get("street") == "Farmwood Cottages")
inspect_details("Farm Cottages", lambda r: r.get("street") == "Farm Cottages")

# 14. Fulford'S Cottages
inspect_details("Fulford'S Cottages", lambda r: r.get("street") == "Fulford'S Cottages")

# 15. Gasens Street
inspect_details("Gasens Street", lambda r: r.get("street") == "Gasens Street")

# 16. Geo Street
inspect_details("Geo Street", lambda r: r.get("street") == "Geo Street")

# 18. Lansdowne Cottages
inspect_details("Lansdowne Cottages", lambda r: r.get("street") == "Lansdowne Cottages")

# 19. Jayne's Buildings
inspect_details("Jayne's Buildings", lambda r: r.get("street") == "Jayne's Buildings")

# 20. Llwnyderi Road vs Llwynderi Road
inspect_details("Llwnyderi Road", lambda r: r.get("street") == "Llwnyderi Road")
inspect_details("Llwynderi Road", lambda r: r.get("street") == "Llwynderi Road")

# 21. Lyn Street
inspect_details("Lyn Street", lambda r: r.get("street") == "Lyn Street")

# 22. Maindee Board Schools
inspect_details("Maindee Board Schools", lambda r: r.get("street") == "Maindee Board Schools")

# 23. Maindee Municipal Bldgs
inspect_details("Maindee Municipal Bldgs", lambda r: r.get("street") == "Maindee Municipal Bldgs")

# 24. Maindee Street List
inspect_details("Maindee Street List", lambda r: r.get("street") == "Maindee Street List")

# 26. Metropolitan Bank Chambers
inspect_details("Metropolitan Bank Chambers", lambda r: r.get("street") == "Metropolitan Bank Chambers")

# 27. Midland Bank Chambers
inspect_details("Midland Bank Chambers", lambda r: r.get("street") == "Midland Bank Chambers")

# 29. Monmouth Chambers
inspect_details("Monmouth Chambers", lambda r: r.get("street") == "Monmouth Chambers")

# 30. Mount Pleasant Cottages
inspect_details("Mount Pleasant Cottages", lambda r: r.get("street") in ["Mount Pleasant Cottages", "Mt. Pleasant Cottages"])

# 32. New Buildings
inspect_details("New Buildings", lambda r: r.get("street") == "New Buildings")

# 33. Newport Street Directory
inspect_details("Newport Street Directory", lambda r: r.get("street") == "Newport Street Directory")
