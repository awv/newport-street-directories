import csv
import json
import os
import shutil

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_macarthy_fix"
shutil.copyfile(DATA_CSV, BACKUP_CSV)
print(f"Created safety backup {BACKUP_CSV}")

rows = []
with open(DATA_CSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for r in reader:
        rows.append(r)

print(f"Loaded {len(rows):,} records from {DATA_CSV}")

# 1. Fix 1906 Magor Street records that were mislabelled as Macarthy's Court
# In 1906, rows 362180 to 362189 were Nos 50-68 of Magor Street (between Magor St 70 and Magor St 48)
magor_fixed = 0
for r in rows:
    if r.get("year") == "1906" and r.get("street") == "Macarthy's Court":
        h_no = r.get("house_number", "").strip()
        # Macarthy's Court only has houses 1 to 6. Numbers 50, 52, 54, 56, 58, 60, 62, 64, 66, 68 belong to Magor Street
        if h_no in {"50", "52", "54", "56", "58", "60", "62", "64", "66", "68"}:
            r["street"] = "Magor Street"
            magor_fixed += 1

print(f"Fix 1: Re-assigned {magor_fixed} records from Macarthy's Court back to Magor Street in 1906.")

# Also normalize any 1906 records where street is "Mag" to "Magor Street"
mag_count = 0
for r in rows:
    if r.get("year") == "1906" and r.get("street") == "Mag":
        r["street"] = "Magor Street"
        mag_count += 1
print(f"Fix 1b: Normalized {mag_count} truncated 'Mag' street names to 'Magor Street' in 1906.")

# 2. Fix reversed names in 1886 Macarthy's Court and general surname/forename splits
# Common forenames or forename abbreviations in historical records
common_forenames = {
    'edwd': 'Edward', 'edw': 'Edward', 'edward': 'Edward',
    'thos': 'Thomas', 'tho': 'Thomas', 'thomas': 'Thomas',
    'wm': 'William', 'william': 'William',
    'john': 'John', 'jno': 'John',
    'elizabeth': 'Elizabeth', 'mary': 'Mary', 'ellen': 'Ellen', 'louisa': 'Louisa',
    'george': 'George', 'geo': 'George',
    'charles': 'Charles', 'chas': 'Charles',
    'henry': 'Henry', 'hy': 'Henry',
    'robert': 'Robert', 'robt': 'Robert',
    'alfred': 'Alfred', 'alfd': 'Alfred',
    'james': 'James', 'jas': 'James',
    'richard': 'Richard', 'richd': 'Richard',
    'daniel': 'Daniel', 'danl': 'Daniel',
    'samuel': 'Samuel', 'saml': 'Samuel',
    'david': 'David',
    'arthur': 'Arthur', 'joseph': 'Joseph', 'benjamin': 'Benjamin', 'benj': 'Benjamin',
    'peter': 'Peter', 'frederick': 'Frederick', 'fredk': 'Frederick',
    'walter': 'Walter', 'edwin': 'Edwin', 'herbert': 'Herbert',
    'albert': 'Albert', 'frank': 'Frank', 'ernest': 'Ernest',
    'c': 'C.', 'l': 'L.', 'j': 'J.', 'w': 'W.', 'h': 'H.', 'g': 'G.',
    'a': 'A.', 'b': 'B.', 'd': 'D.', 'e': 'E.', 'f': 'F.', 'm': 'M.',
    'p': 'P.', 'r': 'R.', 's': 'S.', 't': 'T.'
}

reversed_fixed = 0
for r in rows:
    sn = r.get("surname", "").strip()
    fn = r.get("forename", "").strip()
    
    # Check if surname contains "Surname Forename" (with empty forename)
    if not fn and " " in sn:
        # Exclude institutions / companies / multi-word entities
        if any(kw in sn.lower() for kw in ['works', 'limited', 'ltd', 'company', 'co.', '&', 'brewery', 'inn', 'hotel', 'arms', 'house', 'office', 'court', 'wharf', 'society', 'chapel', 'church', 'school']):
            continue
            
        parts = sn.split()
        if len(parts) == 2:
            w1, w2 = parts
            w2_clean = w2.rstrip('.,').lower()
            if w2_clean in common_forenames:
                r["surname"] = w1.strip('.,')
                r["forename"] = common_forenames[w2_clean]
                reversed_fixed += 1
        elif len(parts) == 3 and parts[0].lower() in ('mrs.', 'mrs', 'miss', 'mr.', 'mr'):
            # e.g. "Mrs. Mary A."
            pass

print(f"Fix 2: Corrected {reversed_fixed:,} reversed or combined 'Surname Forename' records across data.csv.")

# Save data.csv
with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Saved updated data.csv!")

