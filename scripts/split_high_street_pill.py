import csv
import json
import os
import shutil
import re

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_high_street_pill"
MASTER_FILE = "master_streets.json"

if not os.path.exists(BACKUP_CSV):
    print(f"Creating backup {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)
else:
    print(f"Backup {BACKUP_CSV} already exists.")

# Read all rows
rows = []
with open(DATA_CSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

print(f"Total rows read: {len(rows)}")

new_rows = []
stats = {
    "1878_renamed": 0,
    "1882_fixed": 0,
    "1886_unpacked": 0,
    "1887_fixed": 0,
    "1890_fixed": 0,
    "1892_fixed": 0,
    "1893_fixed": 0
}

# Pre-filter: We can process row by row, tracking context
i = 0
while i < len(rows):
    r = rows[i]
    yr = r.get("year", "")
    st = r.get("street", "")
    hn = r.get("house_number", "")
    bn = r.get("building_name", "")
    fn = r.get("forename", "")
    sn = r.get("surname", "")
    tr = r.get("trade", "")

    # 1. 1878: High Street Pill
    if yr == "1878" and st.lower() == "high street pill":
        r["street"] = "High Street, Pill"
        new_rows.append(r)
        stats["1878_renamed"] += 1
        i += 1
        continue

    # 2. 1882: Pill High Street sequence
    if yr == "1882" and st == "High Street" and hn == "Pill":
        # Transform this row
        r["street"] = "High Street, Pill"
        door = bn.strip()
        r["house_number"] = door
        r["building_name"] = ""

        # Surnames and Forenames were swapped in 1882
        # Special pub / institution handling
        if fn == "Rising Sun":
            r["building_name"] = "Rising Sun"
            r["forename"] = "Philip"
            r["surname"] = "May"
            r["trade"] = ""
        elif fn == "Orange Tree":
            r["building_name"] = "Orange Tree"
            r["forename"] = "Timothy"
            r["surname"] = "Foley"
            r["trade"] = ""
        elif "St. Michael" in fn:
            r["house_number"] = "13-15"
            r["building_name"] = "St. Michael's Catholic schools"
            r["forename"] = ""
            r["surname"] = ""
            r["trade"] = ""
        elif fn == "Fussey" and sn == "Richard":
            r["house_number"] = ""
            r["forename"] = "Richard"
            r["surname"] = "Fussey"
        elif not fn and not sn and "void" in tr.lower():
            r["forename"] = ""
            r["surname"] = ""
        else:
            # Standard swap: in 1882 fn was surname and sn was forename
            actual_forename = sn
            actual_surname = fn
            r["forename"] = actual_forename
            r["surname"] = actual_surname

        new_rows.append(r)
        stats["1882_fixed"] += 1
        i += 1
        continue

    # 3. 1886: Unpack Nat. Provincial Bank Ltd multiline row
    if yr == "1886" and st == "High Street" and fn == "Nat. Provincial Bank" and "resident,High street-continued" in tr:
        # Keep Nat Provincial Bank row clean
        r["trade"] = "National Provincial Bank of England"
        new_rows.append(r)

        # Parse multiline CSV lines in trade
        trade_text = tr
        lines = trade_text.split("\n")
        current_street = "High Street"

        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip().replace(r"\,", ",") for p in re.split(r'(?<!\\),', line)]
            # ensure parts length
            while len(parts) < 8:
                parts.append("")

            rec_type = parts[0]
            if rec_type == "street":
                s_name = parts[1]
                if "P." in s_name or "Pill" in s_name:
                    current_street = "High Street, Pill"
                elif "Hill" in s_name:
                    current_street = "Hill Street"
                else:
                    current_street = "High Street"
                continue

            if rec_type == "cross_street":
                continue

            if rec_type == "resident":
                # fields: rec_type, street, house_number, building_name, forename, surname, trade, ...
                p_hn = parts[2]
                p_bn = parts[3]
                p_fn = parts[4]
                p_sn = parts[5]
                p_tr = parts[6]

                new_rows.append({
                    "year": "1886",
                    "street": current_street,
                    "house_number": p_hn,
                    "building_name": p_bn,
                    "surname": p_sn,
                    "forename": p_fn,
                    "trade": p_tr,
                    "source_type": ""
                })
                stats["1886_unpacked"] += 1

        i += 1
        continue

    # 4. 1887: Pill High Street sequence
    # Starts at Richd. Fursey (row 82) through Jere. Barnett (row 116)
    if yr == "1887" and st == "High Street":
        # Check if we are in the Pill sequence
        # We know it starts at Fursey and runs through door 43 Barnett
        if (fn == "Richd." and sn == "Fursey") or (fn == "Jere." and sn == "Creamer" and hn == "1"):
            # Mark all following 1887 High Street rows until Barnett as High Street, Pill
            r["street"] = "High Street, Pill"
            new_rows.append(r)
            stats["1887_fixed"] += 1
            i += 1
            while i < len(rows):
                nxt = rows[i]
                if nxt.get("year") != "1887" or nxt.get("street") != "High Street":
                    break
                nxt["street"] = "High Street, Pill"
                # Fix Thomas Roach row 103
                if nxt.get("building_name") == "Roach Thomas" and not nxt.get("surname"):
                    nxt["house_number"] = "30"
                    nxt["building_name"] = ""
                    nxt["forename"] = "Thomas"
                    nxt["surname"] = "Roach"
                new_rows.append(nxt)
                stats["1887_fixed"] += 1
                if nxt.get("surname") == "Barnett" and nxt.get("house_number") == "43":
                    i += 1
                    break
                i += 1
            continue

    # 5. 1890: Pill High Street sequence
    if yr == "1890" and st == "High Street":
        if (bn == "Fursey Richd." or (fn == "Patrick" and sn == "Whelton" and hn == "1")):
            r["street"] = "High Street, Pill"
            if bn == "Fursey Richd.":
                r["building_name"] = ""
                r["forename"] = "Richd."
                r["surname"] = "Fursey"
                r["trade"] = "ship smith"
            new_rows.append(r)
            stats["1890_fixed"] += 1
            i += 1
            while i < len(rows):
                nxt = rows[i]
                if nxt.get("year") != "1890" or nxt.get("street") != "High Street":
                    break
                nxt["street"] = "High Street, Pill"
                if nxt.get("trade") == "Rising Sun":
                    nxt["building_name"] = "Rising Sun"
                    nxt["trade"] = ""
                new_rows.append(nxt)
                stats["1890_fixed"] += 1
                if nxt.get("surname") == "Shiles" and nxt.get("house_number") == "8":
                    i += 1
                    break
                i += 1
            continue

    # 6. 1892: Pill High Street sequence
    if yr == "1892" and st == "High Street":
        if fn == "Richd." and sn == "Fursey":
            r["street"] = "High Street, Pill"
            new_rows.append(r)
            stats["1892_fixed"] += 1
            i += 1
            while i < len(rows):
                nxt = rows[i]
                if nxt.get("year") != "1892" or nxt.get("street") != "High Street":
                    break
                nxt["street"] = "High Street, Pill"
                new_rows.append(nxt)
                stats["1892_fixed"] += 1
                if nxt.get("surname") == "Barnett" and nxt.get("house_number") == "43":
                    i += 1
                    break
                i += 1
            continue

    # 7. 1893: Pill High Street sequence
    if yr == "1893" and st == "High Street" and hn == "Pill.":
        r["street"] = "High Street, Pill"
        door = bn.strip()
        r["house_number"] = door
        r["building_name"] = ""

        # Special rows in 1893
        if sn == "Fursey":
            r["house_number"] = ""
        elif sn == "McCarthy" and fn == "Rising Sun":
            r["house_number"] = "4"
            r["building_name"] = "Rising Sun"
            r["forename"] = "D."
            r["surname"] = "McCarthy"
            r["trade"] = ""
        elif "St. Michael" in sn:
            r["house_number"] = ""
            r["building_name"] = "St. Michael's Catholic Church and Schools"
            r["forename"] = ""
            r["surname"] = ""
        elif sn == "Foley" and fn == "Orange Tree":
            r["house_number"] = "21"
            r["building_name"] = "Orange Tree"
            r["forename"] = "Tim"
            r["surname"] = "Foley"
            r["trade"] = ""
        elif fn == "Archer" and sn == "John":
            r["house_number"] = "24"
            r["forename"] = "John"
            r["surname"] = "Archer"
            r["trade"] = "labourer"
        elif fn == "Carey" and sn == "Flohrence":
            r["house_number"] = "42"
            r["forename"] = "Florence"
            r["surname"] = "Carey"

        new_rows.append(r)
        stats["1893_fixed"] += 1
        i += 1
        continue

    # Default: keep row as is
    new_rows.append(r)
    i += 1

print("Summary of actions:")
for k, v in stats.items():
    print(f"  {k}: {v}")
print(f"Total rows after processing: {len(new_rows)}")

# Write back data.csv
with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(new_rows)

print("data.csv saved successfully!")

# Update master_streets.json
with open(MASTER_FILE, "r", encoding="utf-8") as f:
    master = json.load(f)

streets = master.get("streets", {})
slug = "high-street-pill"
streets[slug] = {
    "canonical_name": "High Street, Pill",
    "slug": slug,
    "district": "Pillgwenlly",
    "parish": "",
    "former_names": [],
    "renamed_to": "St. Michael's Street",
    "sub_sections": [],
    "numbering_scheme": {
        "type": "CONSECUTIVE",
        "approx_change_year": None
    },
    "cross_streets": [
        "Church Street",
        "Clarence Street",
        "Castle Street"
    ],
    "aliases": ["High Street Pill", "High Street (Pill)"],
    "audit": {
        "status": "NAME_VERIFIED",
        "verified_by": "Rob Gale",
        "notes": "Historical High Street in Pillgwenlly (from Church Street to Castle Street). Renamed to St. Michael's Street in 1894."
    },
    "audit_status": "NAME_VERIFIED",
    "notes": "Historical High Street in Pillgwenlly (from Church Street to Castle Street). Renamed to St. Michael's Street in 1894.",
    "latitude": "51.5795",
    "longitude": "-2.9880"
}

# Cross-reference in St. Michael's Street
sm_slug = "st-michaels-street"
if sm_slug in streets:
    fn_list = streets[sm_slug].get("former_names", [])
    if "High Street, Pill" not in fn_list:
        fn_list.append("High Street, Pill")
        streets[sm_slug]["former_names"] = fn_list

master["streets"] = streets
with open(MASTER_FILE, "w", encoding="utf-8") as f:
    json.dump(master, f, indent=2, ensure_ascii=False)

print("master_streets.json updated with High Street, Pill!")
