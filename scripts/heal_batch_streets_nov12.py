import csv
import os
import shutil

CSV_PATH = "data.csv"
BACKUP_PATH = "data.csv.bak_streets_nov12"

def clean_row(r, baneswell_sq_idx):
    street = r.get("street", "").strip()
    yr = r.get("year", "").strip()
    hn = r.get("house_number", "").strip()
    bld = r.get("building_name", "").strip()
    sn = r.get("surname", "").strip()
    fn = r.get("forename", "").strip()
    tr = r.get("trade", "").strip()

    # 1. Acadia Terrace & Arcadia Terrace -> Morden Road
    if street in ("Acadia Terrace", "Arcadia Terrace"):
        r["street"] = "Morden Road"
        if not bld:
            r["building_name"] = "Arcadia Terrace"
        return r

    # 2. Albany Chambers -> Commercial Street (1 Commercial Street)
    if street == "Albany Chambers":
        r["street"] = "Commercial Street"
        r["house_number"] = "1"
        r["building_name"] = "Albany Chambers"
        return r

    # 3. Albert Hall Chambers -> Stow Hill
    if street == "Albert Hall Chambers":
        r["street"] = "Stow Hill"
        if not bld and not any(k in tr.lower() for k in ["school", "hall", "church"]):
            r["building_name"] = "Albert Hall Chambers"
        return r

    # 4. Albion Chambers -> Commercial Street (21 Commercial Street)
    if street == "Albion Chambers":
        r["street"] = "Commercial Street"
        if not hn or "see" in hn.lower():
            r["house_number"] = "21"
        r["building_name"] = "Albion Chambers"
        return r

    # 5. Alma Street-continued -> Alma Street
    if street == "Alma Street-continued":
        r["street"] = "Alma Street"
        return r

    # 6. Alteryn variations -> Allt-yr-yn
    if street in ("Alteryh", "Alteryu", "Altryn", "Alteryn"):
        r["street"] = "Allt-yr-yn"
        return r
    if street == "Alteryn Road":
        r["street"] = "Allt-yr-yn Road"
        return r
    if street == "Alteryn View":
        r["street"] = "Allt-yr-yn View"
        return r

    # 7. Baneswell Chambers -> Bridge Street (13 Bridge Street)
    if street == "Baneswell Chambers":
        r["street"] = "Bridge Street"
        r["house_number"] = "13"
        r["building_name"] = "Baneswell Chambers"
        return r

    # 8. Baneswell-square (corrupted 1890 block)
    if street == "Baneswell-square":
        # Invert sn and fn back if inverted (e.g. sn='Wm.', fn='Lawrence')
        def swap_names(row):
            s = row.get("surname", "")
            f = row.get("forename", "")
            # If s looks like initials or forename and f looks like surname
            if s and f and (s in ("W.", "Ann", "Chas.", "Chris. C.", "Jane", "Thos.", "Rachel", "Hy.", "John", "Lydia", "Wm.", "Charles", "Martin", "Mary", "Charlotte", "L.", "Herbert", "James", "Jas.", "Llwyn.", "Benjamin", "Thomas", "T. jun.", "Job", "E. F.", "Alfred", "F.", "E.", "Mich.", "George", "Isaac", "J.", "Geo.", "Albert") or s.startswith("Miss ") or s.startswith("Mrs. ")):
                row["surname"] = f
                row["forename"] = s

        # Indices 0..37: Barrack Hill (38 rows)
        if baneswell_sq_idx < 38:
            r["street"] = "Barrack Hill"
            swap_names(r)
            return r
        # Indices 38..63: Baneswell Road (26 rows)
        elif baneswell_sq_idx < 64:
            r["street"] = "Baneswell Road"
            swap_names(r)
            return r
        # Indices 64..77: Victoria Square (14 rows)
        else:
            r["street"] = "Victoria Square"
            swap_names(r)
            return r

    # Victoria Square variants
    if street in ("Baneswell Square", "Victoria (Baneswell) Square", "Victoria. Square"):
        r["street"] = "Victoria Square"
        return r

    return r

def run():
    print("Reading from backup", BACKUP_PATH)
    with open(BACKUP_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

    changes = {}
    new_rows = []
    bs_counter = 0
    for r in reader:
        old_st = r.get("street")
        if old_st == "Baneswell-square":
            nr = clean_row(dict(r), bs_counter)
            bs_counter += 1
        else:
            nr = clean_row(dict(r), -1)
        new_st = nr.get("street")
        if old_st != new_st:
            changes[f"{old_st} -> {new_st}"] = changes.get(f"{old_st} -> {new_st}", 0) + 1
        new_rows.append(nr)

    print("Change summary:")
    for k, v in sorted(changes.items()):
        print(f"  {k}: {v} rows")

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_rows)
    print("Successfully wrote updated", CSV_PATH)

if __name__ == "__main__":
    run()
