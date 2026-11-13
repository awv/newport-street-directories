import csv
import json
import os
import shutil
import re

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_pipe_cleanup"

if not os.path.exists(BACKUP_CSV):
    print(f"Creating backup {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)
else:
    print(f"Backup {BACKUP_CSV} already exists.")

rows = []
with open(DATA_CSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

cleaned_count = 0
deleted_count = 0
new_rows = []

for r in rows:
    raw_str = " ".join(str(v) for v in r.values())
    if "|" not in raw_str:
        new_rows.append(r)
        continue

    # Strip | from all fields
    for k in ("house_number", "building_name", "forename", "surname", "trade"):
        val = r.get(k, "")
        if "|" in val:
            val = val.replace("|", " ")
            val = re.sub(r"\s+", " ", val).strip()
            r[k] = val

    hn = r.get("house_number", "")
    bn = r.get("building_name", "")
    fn = r.get("forename", "")
    sn = r.get("surname", "")
    tr = r.get("trade", "")

    # Drop rows that have no resident name, building, or trade
    if not bn and not fn and not sn and not tr:
        deleted_count += 1
        continue

    # Special handling for tennis club / facilities
    if "Stow Park Lawn Tennis Club" in hn:
        r["building_name"] = "Stow Park Lawn Tennis Club"
        r["house_number"] = ""

    # Special handling for flat numbers in surname or forename
    flat_match = re.search(r"\(flat\s*(\d+[a-zA-Z]?)\)", sn, re.IGNORECASE) or re.search(r"\(flat\s*(\d+[a-zA-Z]?)\)", fn, re.IGNORECASE)
    if flat_match:
        flat_num = flat_match.group(1)
        r["building_name"] = f"Flat {flat_num}"
        sn = re.sub(r"\(flat\s*\d+[a-zA-Z]?\)", "", sn, flags=re.IGNORECASE).strip()
        fn = re.sub(r"\(flat\s*\d+[a-zA-Z]?\)", "", fn, flags=re.IGNORECASE).strip()

        # If forename has 'Surname Forename'
        if fn and not sn:
            parts = fn.split(" ")
            if len(parts) >= 2:
                r["surname"] = parts[0]
                r["forename"] = " ".join(parts[1:])
            else:
                r["surname"] = fn
                r["forename"] = ""
        else:
            r["surname"] = sn
            r["forename"] = fn

    # Special handling for named houses in Woodlands Drive
    if r.get("street") == "Woodlands Drive" and r.get("year") == "1971":
        bldg_match = re.search(r"\(([^)]+)\)", sn)
        if bldg_match:
            bldg_name = bldg_match.group(1).replace("(Shelby)", "").strip()
            r["building_name"] = bldg_name
            sn = re.sub(r"\([^)]+\)", "", sn).strip()
            if hn and not fn:
                r["forename"] = sn
                r["surname"] = hn
                r["house_number"] = ""
            else:
                r["surname"] = sn

    # Clean up multi-line gas/glass company rows in Milman Street / Mill Street
    if "Monmouthshire Glass" in fn and "Company" in sn:
        r["forename"] = ""
        r["surname"] = "Monmouthshire Glass Company"
        r["trade"] = "glass merchants"
    elif "Monmouthshire Glass" in fn:
        r["forename"] = ""
        r["surname"] = "Monmouthshire Glass Company"
        r["trade"] = "glass merchants"
    elif "Company, glass mers" in sn:
        # Part of the Monmouthshire Glass row
        deleted_count += 1
        continue

    if "WALES GAS" in sn and "NEW" in bn:
        r["building_name"] = ""
        r["forename"] = ""
        r["surname"] = "Wales Gas Board"
        r["trade"] = "office & works"
    elif "TAKING)" in fn or "Works). T 'N" in sn:
        deleted_count += 1
        continue
    elif "Co-operative Retail Ser" in sn:
        r["forename"] = ""
        r["surname"] = "Co-operative Retail Services Ltd"
        r["trade"] = "coal office"
    elif "vices Ltd (coal office)" in sn:
        deleted_count += 1
        continue
    elif "Automatic Car Park" in fn:
        r["building_name"] = "Automatic Car Park"
        r["forename"] = ""
        r["surname"] = ""
        r["house_number"] = ""

    cleaned_count += 1
    new_rows.append(r)

print(f"Summary: {cleaned_count} records cleaned, {deleted_count} phantom/split rows purged.")
print(f"Total rows remaining: {len(new_rows)}")

with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(new_rows)

print("data.csv updated successfully!")
