import csv
import os
import shutil

CSV_PATH = "data.csv"
BACKUP_PATH = "data.csv.bak_streets_nov12_part2"

def clean_row(r):
    street = r.get("street", "").strip()
    yr = r.get("year", "").strip()
    hn = r.get("house_number", "").strip()
    bld = r.get("building_name", "").strip()
    sn = r.get("surname", "").strip()
    fn = r.get("forename", "").strip()
    tr = r.get("trade", "").strip()

    # 1. Central Chambers -> Stow Hill
    if street == "Central Chambers":
        r["street"] = "Stow Hill"
        if "3" in tr:
            r["house_number"] = "3"
        elif "4" in tr:
            r["house_number"] = "4"
        r["building_name"] = "Central Chambers"
        return r

    # 2. Corn Exchange -> High Street
    if street == "Corn Exchange":
        r["street"] = "High Street"
        if not bld:
            r["building_name"] = "Corn Exchange"
        return r

    # 3. Court-y-Bella Terrace -> Courtybella Terrace
    if street == "Court-y-Bella Terrace":
        r["street"] = "Courtybella Terrace"
        return r

    # 4. Crown Chambers -> Cambrian Road
    if street == "Crown Chambers":
        r["street"] = "Cambrian Road"
        if not bld:
            r["building_name"] = "Crown Chambers"
        return r

    # 5. Emlyn Chambers -> High Street (38 High Street)
    if street == "Emlyn Chambers":
        r["street"] = "High Street"
        r["house_number"] = "38"
        r["building_name"] = "Emlyn Chambers"
        return r

    # 6. NEWPORT STREET DIRECTORY -> Corporation Road (1906 continuation)
    if street == "NEWPORT STREET DIRECTORY":
        r["street"] = "Corporation Road"
        return r

    # 7. Newport (single 1900 row: 161 and 162 Commercial Street Newport.) -> Commercial Street
    if street == "Newport":
        r["street"] = "Commercial Street"
        return r

    # 8. Pottery Terrace (Old) -> Pottery Terrace
    if street in ("Pottery Terrace (Old)", "Pottery Terrace (old)"):
        r["street"] = "Pottery Terrace"
        return r

    # 9. Queen's Chambers -> High Street (41 High Street)
    if street == "Queen's Chambers":
        r["street"] = "High Street"
        r["house_number"] = "41"
        r["building_name"] = "Queen's Chambers"
        return r

    # 10. Rhymney whf -> Rhymney Wharf
    if street == "Rhymney whf":
        r["street"] = "Rhymney Wharf"
        return r

    # 11. Severn view -> Severn View
    if street == "Severn view":
        r["street"] = "Severn View"
        return r

    # 12. Slipway Cottages -> Nash Road
    if street == "Slipway Cottages":
        r["street"] = "Nash Road"
        if not bld:
            r["building_name"] = "Slipway Cottages"
        return r

    # 13. St. George's Buildings -> Jeddo Street
    if street == "St. George's Buildings":
        r["street"] = "Jeddo Street"
        if not bld:
            r["building_name"] = "St. George's Buildings"
        return r

    # 14. St. Woolos Schools -> Stow Hill
    if street == "St. Woolos Schools":
        r["street"] = "Stow Hill"
        return r

    # 15. Stow Park Post Office -> Stow Park Terrace
    if street == "Stow Park Post Office":
        r["street"] = "Stow Park Terrace"
        return r

    # 16. Temperance Cottages -> Christchurch Road
    if street == "Temperance Cottages":
        r["street"] = "Christchurch Road"
        if not bld:
            r["building_name"] = "Temperance Cottages"
        return r

    # 17. The Drill Hall -> Stow Hill
    if street == "The Drill Hall":
        r["street"] = "Stow Hill"
        if not bld and not any(k in tr.lower() for k in ["presbytery", "st. mary"]):
            r["building_name"] = "The Drill Hall"
        return r

    # 18. Town Hall -> Commercial Street
    if street == "Town Hall":
        r["street"] = "Commercial Street"
        if not bld:
            r["building_name"] = "Town Hall"
        return r

    # 19. Union Workhouse -> Stow Hill
    if street == "Union Workhouse":
        r["street"] = "Stow Hill"
        if not bld and not hn:
            r["building_name"] = "Union Workhouse"
        return r

    return r

def run():
    print("Reading", CSV_PATH)
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

    changes = {}
    new_rows = []
    for r in reader:
        old_st = r.get("street")
        nr = clean_row(dict(r))
        new_st = nr.get("street")
        if old_st != new_st:
            changes[f"{old_st} -> {new_st}"] = changes.get(f"{old_st} -> {new_st}", 0) + 1
        new_rows.append(nr)

    print("Change summary:")
    for k, v in sorted(changes.items()):
        print(f"  {k}: {v} rows")

    if not os.path.exists(BACKUP_PATH):
        shutil.copyfile(CSV_PATH, BACKUP_PATH)
        print("Created backup at", BACKUP_PATH)

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_rows)
    print("Successfully wrote updated", CSV_PATH)

if __name__ == "__main__":
    run()
