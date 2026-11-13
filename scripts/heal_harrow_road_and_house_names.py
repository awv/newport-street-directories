#!/usr/bin/env python3
"""
heal_harrow_road_and_house_names.py
===================================
1. Harrow Road 1927 anomalies (Image 1):
   - No. 54: Oak v -> building_name="Oak View", trade=""
   - No. 52: Mon Abria -> building_name="Mon Abria", trade=""
   - No. 50: Contractor (verified)
   - No. 46: Schmaster -> trade="Schoolmaster"
   - No. 32: Ivydene -> building_name="Ivydene", trade=""
   - No. 30: sign writer, Lorna Doone -> building_name="Lorna Doone", trade="Sign Writer"
   - No. 3-24: Walton house, Wellesley, Tyrone, Selsdon, St. Audries, Revelstoke, Lydbrook, Harrow ho -> building_name
   - Swapped unnumbered entries (Francis Gideon, Anderson, Jordan).
   - Reassigns Nos. 15-43 + Harrow Road Garage from Harry Street back to Harrow Road!

2. Harrow Road historical records (1898-1936) across all editions:
   - Disentangles house names trapped in trade, forename, or surname (1898, 1900, 1902, 1906, 1908, 1910, 1913, 1915, 1920, 1925, 1936).

3. Dataset-wide:
   - Expands Schmaster -> Schoolmaster.
   - Extracts Mon Abria, Ivydene, Lorna Doone, Oak View from trade into building_name dataset-wide.
   - Fixes swapped Pill / Robert in 1901 Locke Street.

4. Volume CSV fixes:
   - volume_csvs/1882_cleaned.csv: Fixes shifted "High Street, Pill" rows where missing quotes shifted columns (Image 2).
   - volume_csvs/1927_cleaned.csv: Fixes Nos. 15-43 Harrow Road misassigned to HARRY STREET.

5. Client-side app.js:
   - Expands cleanOccupation() regex with house names for robust defense-in-depth.
"""

import os
import sys
import csv
import re
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
BACKUP_CSV = os.path.join(PROJECT_ROOT, "data.csv.bak_before_harrow_heal")
VOL_1882_CSV = os.path.join(PROJECT_ROOT, "volume_csvs", "1882_cleaned.csv")
VOL_1927_CSV = os.path.join(PROJECT_ROOT, "volume_csvs", "1927_cleaned.csv")
APP_JS = os.path.join(PROJECT_ROOT, "src", "js", "app.js")

# House names map for Harrow Road
HARROW_HOUSE_PATTERNS = [
    (re.compile(r"^oak\s*v(?:iew|il|\.|\b)?\.?$", re.I), "Oak View"),
    (re.compile(r"^mon\s*abri?a?(?:,\s*hon)?\.?$", re.I), "Mon Abria"),
    (re.compile(r"^ivyd(?:ene|can)\.?$", re.I), "Ivydene"),
    (re.compile(r"^walton\s*(?:house|ho|h)\.?$", re.I), "Walton House"),
    (re.compile(r"^wellesley(?:\s+george)?\.?$", re.I), "Wellesley"),
    (re.compile(r"^tyrone(?:—\s*void)?\.?$", re.I), "Tyrone"),
    (re.compile(r"^selsdon\.?$", re.I), "Selsdon"),
    (re.compile(r"^st\.?\s*audries\.?$", re.I), "St. Audries"),
    (re.compile(r"^revelstoke\.?$", re.I), "Revelstoke"),
    (re.compile(r"^lydbrook\.?$", re.I), "Lydbrook"),
    (re.compile(r"^harrow\s*(?:house|ho|h)\.?$", re.I), "Harrow House"),
    (re.compile(r"^frome\s*vale\.?$", re.I), "Frome Vale"),
    (re.compile(r"^grove\s*(?:house|ho|h)\.?$", re.I), "Grove House"),
    (re.compile(r"^dean\s*(?:house|ho|h)\.?$", re.I), "Dean House"),
    (re.compile(r"^deanhouse\.?$", re.I), "Dean House"),
    (re.compile(r"^chertsey\.?$", re.I), "Chertsey"),
    (re.compile(r"^montevill(?:e|s)(?:\s+thomas)?\.?$", re.I), "Monteville"),
    (re.compile(r"^merridale(?:\s+thomas)?\.?$", re.I), "Merridale"),
    (re.compile(r"^pendre\.?$", re.I), "Pendre"),
    (re.compile(r"^watford\s*(?:house|ho|h)?\.?$", re.I), "Watford House"),
    (re.compile(r"^kilburn\s*(?:house|ho|h)\.?$", re.I), "Kilburn House"),
    (re.compile(r"^treloyhan\s*(?:house|ho|h)?\.?$", re.I), "Treloyhan House"),
    (re.compile(r"^treloynan\s*(?:house|ho|h)?\.?$", re.I), "Treloyhan House"),
    (re.compile(r"^minn?ett\s*(?:house|ho|h)\.?$", re.I), "Minett House"),
    (re.compile(r"^tregenna\s*(?:house|ho|h)?\.?$", re.I), "Tregenna House"),
    (re.compile(r"^seaton\s*(?:house|ho|h)(?:—\s*void)?\.?$", re.I), "Seaton House"),
    (re.compile(r"^home(?:meade|made|maede|stead)\s*(?:house|ho|h)?\.?$", re.I), "Homemeade House"),
    (re.compile(r"^chelsea\s*(?:house|ho|h)?\.?$", re.I), "Chelsea House"),
    (re.compile(r"^chelseah\.?$", re.I), "Chelsea House"),
    (re.compile(r"^elford\.?$", re.I), "Elford"),
    (re.compile(r"^dun(?:k|s)k?well\.?$", re.I), "Dunskwell"),
    (re.compile(r"^tranmere\.?$", re.I), "Tranmere"),
    (re.compile(r"^ryecroft(?:—\s*void)?\.?$", re.I), "Ryecroft"),
    (re.compile(r"^oswald\.?$", re.I), "Oswald"),
    (re.compile(r"^ff?ynonau\.?$", re.I), "Ffynnonau"),
    (re.compile(r"^ashley\s*(?:house|ho|h)\.?$", re.I), "Ashley House"),
    (re.compile(r"^lorna\s*doone\.?$", re.I), "Lorna Doone"),
]

def match_harrow_house(text):
    clean = text.strip()
    for pat, canon in HARROW_HOUSE_PATTERNS:
        if pat.match(clean):
            return canon
    return None

def heal_data_csv():
    print(f"Creating backup: {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)

    rows = []
    healed_count = 0
    harrow_reassigned = 0

    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            st = (r.get("street") or "").strip()
            yr = (r.get("year") or "").strip()
            hn = (r.get("house_number") or "").strip()
            sn = (r.get("surname") or "").strip()
            fn = (r.get("forename") or "").strip()
            bn = (r.get("building_name") or "").strip()
            tr = (r.get("trade") or "").strip()
            changed = False

            # Universal: Schmaster -> Schoolmaster
            if re.search(r"\bschmaster\b", tr, re.I):
                tr = re.sub(r"\bschmaster\b", "Schoolmaster", tr, flags=re.I)
                changed = True

            # 1901 Locke Street swapped name
            if yr == "1901" and st.lower() == "locke street" and hn == "10" and sn == "Robert" and fn == "Pill":
                sn = "Pill"
                fn = "Robert"
                changed = True

            # Reassign 1927 Harrow Road records misassigned to Harry Street
            if yr == "1927" and st.lower() == "harry street":
                if (sn in ["Hillman", "Jones", "Roderick", "Winn", "Parsons", "Watford", "Watkins", "Prendergast", "Hampton", "Payne", "Preece", "Matthews", "Newman", "Thomas", "Johnson", "Gilpin", "Butler"] and hn in ["15","17","19","21","23","25","27","29","31","33","35","37","39","41","43"]) or "harrow road garage" in fn.lower() or "harrow road garage" in sn.lower():
                    st = "Harrow Road"
                    harrow_reassigned += 1
                    changed = True

                    # Specific corrections for these return rows
                    if hn == "23" and "dean" in tr.lower():
                        bn = "Dean House"
                        tr = ""
                    elif hn == "25" and sn == "Watford" and "james rees" in fn.lower():
                        sn = "James"
                        fn = "Rees"
                        bn = "Watford House"
                        tr = ""
                    elif hn == "27" and "frome" in tr.lower():
                        bn = "Frome Vale"
                        tr = ""
                    elif hn == "31" and "grove" in tr.lower():
                        bn = "Grove House"
                        tr = ""
                    elif hn == "33" and "grocer" in tr.lower():
                        tr = "Grocer"
                    elif hn == "37" and "dunkswell" in tr.lower():
                        bn = "Dunskwell"
                        tr = ""
                    elif hn == "37" and "ryecroft" in tr.lower():
                        bn = "Ryecroft"
                        tr = ""
                    elif hn == "39" and "ffynonau" in tr.lower():
                        bn = "Ffynnonau"
                        tr = ""
                    elif "harrow road garage" in fn.lower() or "harrow road garage" in sn.lower():
                        hn = ""
                        bn = "Harrow Road Garage"
                        sn = "Harrow Road Garage"
                        fn = ""
                        tr = "Garage"

            # Harrow Road processing
            if st.lower() == "harrow road":
                # 1. Swapped unnumbered records in 1927
                if yr == "1927":
                    if sn.lower() == "engineer" and "francis gideon" in fn.lower():
                        sn = "Francis"
                        fn = "Gideon"
                        bn = ""
                        tr = "Engineer"
                        changed = True
                    elif sn.lower() == "dental surgeon" and fn.lower() == "anderson":
                        sn = "Anderson"
                        fn = "Charles W. N."
                        bn = ""
                        tr = "Dental Surgeon"
                        changed = True
                    elif "building contr" in sn.lower() and fn.lower() == "jordan":
                        sn = "Jordan"
                        fn = "(Ernest C.) & Son"
                        bn = ""
                        tr = "Building Contractors & Engineers"
                        changed = True

                # 2. Extract compound trades with house names
                if re.search(r"lorna\s*doone", tr, re.I):
                    bn = "Lorna Doone"
                    tr = re.sub(r",?\s*lorna\s*doone", "", tr, flags=re.I).strip(" ,")
                    changed = True
                elif re.search(r"frome\s*vale", tr, re.I):
                    bn = "Frome Vale"
                    tr = re.sub(r",?\s*frome\s*vale", "", tr, flags=re.I).strip(" ,")
                    changed = True
                elif re.search(r"dun(?:k|s)k?well", tr, re.I):
                    bn = "Dunskwell"
                    tr = re.sub(r",?\s*dun(?:k|s)k?well", "", tr, flags=re.I).strip(" ,")
                    changed = True
                elif re.search(r"oak\s*v\.?", tr, re.I) and "clerk" in tr.lower():
                    bn = "Oak View"
                    tr = "Clerk"
                    changed = True

                # 3. Direct house names in trade column
                house_match = match_harrow_house(tr)
                if house_match:
                    bn = house_match
                    if "void" in tr.lower():
                        tr = "Void"
                    else:
                        tr = ""
                    changed = True

                # 4. 1898 Harrow Road swapped entries
                if yr == "1898":
                    if sn == "John H." and fn == "Mon Abri" and tr == "Farrow":
                        sn, fn, bn, tr = "Farrow", "John H.", "Mon Abria", ""
                        changed = True
                    elif sn == "Wm." and "tregenna" in fn.lower() and tr == "Amor":
                        sn, fn, bn, tr = "Amor", "Wm.", "Tregenna House", ""
                        changed = True
                    elif sn == "Henry" and "merridale" in fn.lower():
                        sn, fn, bn, tr = "Thomas", "Henry", "Merridale", ""
                        changed = True
                    elif sn == "A. H." and "monteville" in fn.lower() and tr == "Shearn":
                        sn, fn, bn, tr = "Shearn", "A. H.", "Monteville", ""
                        changed = True
                    elif sn == "W. J." and "chertsey" in fn.lower() and tr == "Langmaid":
                        sn, fn, bn, tr = "Langmaid", "W. J.", "Chertsey", ""
                        changed = True
                    elif tr == "House Void":
                        sn, fn, bn, tr = "", "", "", "Void"
                        changed = True
                    elif sn == "A. F." and "wellesley" in fn.lower() and tr == "Moreton":
                        sn, fn, bn, tr = "Moreton", "A. F.", "Wellesley", ""
                        changed = True
                    elif tr == "Tyrone—void":
                        sn, fn, bn, tr = "", "", "Tyrone", "Void"
                        changed = True
                    elif sn == "Wm. J." and "selsdon" in fn.lower() and tr == "Ridley":
                        sn, fn, bn, tr = "Ridley", "Wm. J.", "Selsdon", ""
                        changed = True
                    elif sn == "Frederick J." and "pendre" in fn.lower() and tr == "Lewis":
                        sn, fn, bn, tr = "Lewis", "Frederick J.", "Pendre", ""
                        changed = True
                    elif sn == "C. F." and "watford" in bn.lower() and tr == "Holmes":
                        sn, fn, bn, tr = "Holmes", "C. F.", "Watford House", ""
                        changed = True
                    elif sn == "B." and "frome vale" in fn.lower() and tr == "Fussell":
                        sn, fn, bn, tr = "Fussell", "B.", "Frome Vale", ""
                        changed = True

                # 5. 1913 Harrow Road swapped entries
                if yr == "1913":
                    if sn == "Alf. E." and "tregenna" in fn.lower() and tr == "Pearce":
                        sn, fn, bn, tr = "Pearce", "Alf. E.", "Tregenna House", ""
                        changed = True
                    elif sn == "Leigh" and "minnett" in tr.lower():
                        sn, fn, bn, tr = "Leigh", "Tom", "Minett House", ""
                        changed = True
                    elif sn == "Evans" and "treloyhan" in fn.lower():
                        sn, fn, bn, tr = "Evans", "R. W.", "Treloyhan House", ""
                        changed = True
                    elif sn == "Robt." and "chelsea" in fn.lower() and tr == "Hodge":
                        sn, fn, bn, tr = "Hodge", "Robt.", "Chelsea House", ""
                        changed = True
                    elif "homemeade" in fn.lower() and tr == "Howells":
                        sn, fn, bn, tr = "Howells", "", "Homemeade House", ""
                        changed = True
                    elif sn == "John" and "monteville" in fn.lower():
                        sn, fn, bn, tr = "Thomas", "John", "Monteville", ""
                        changed = True
                    elif sn == "Morgan" and "chertsey" in fn.lower():
                        sn, fn, bn, tr = "Morgan", "Mrs. E.", "Chertsey", ""
                        changed = True
                    elif sn == "Chas." and "walton" in fn.lower() and tr == "Edwards":
                        sn, fn, bn, tr = "Edwards", "Chas.", "Walton House", ""
                        changed = True
                    elif sn == "C. E." and "wellesley" in fn.lower():
                        sn, fn, bn, tr = "George", "C. E.", "Wellesley", ""
                        changed = True
                    elif sn == "Samuel" and "tyrone" in fn.lower() and tr == "Abrahams":
                        sn, fn, bn, tr = "Abrahams", "Samuel", "Tyrone", ""
                        changed = True
                    elif sn == "G. T." and "selsdon" in fn.lower() and tr == "Wright":
                        sn, fn, bn, tr = "Wright", "G. T.", "Selsdon", ""
                        changed = True
                    elif sn == "Fredk. J." and "pendre" in fn.lower() and tr == "Lewis":
                        sn, fn, bn, tr = "Lewis", "Fredk. J.", "Pendre", ""
                        changed = True
                    elif sn == "Mark" and "deanhouse" in fn.lower() and tr == "Parsons":
                        sn, fn, bn, tr = "Parsons", "Mark", "Dean House", ""
                        changed = True
                    elif sn == "Rees" and "watford" in fn.lower():
                        sn, fn, bn, tr = "James", "Rees", "Watford House", ""
                        changed = True
                    elif sn == "Saunders" and "grove" in tr.lower():
                        sn, fn, bn, tr = "Saunders", "Harold", "Grove House", ""
                        changed = True
                    elif sn == "F. C." and "seaton" in fn.lower() and tr == "Parfitt":
                        sn, fn, bn, tr = "Parfitt", "F. C.", "Seaton House", ""
                        changed = True

                # 6. 1915 Harrow Road entries with name and house combined in trade
                if yr == "1915" and tr:
                    m = re.match(r"^([^,]+),\s*(.+)$", tr)
                    if m:
                        candidate_fn = m.group(1).strip()
                        candidate_house = m.group(2).strip()
                        h_match = match_harrow_house(candidate_house)
                        if h_match:
                            fn = candidate_fn
                            bn = h_match
                            tr = ""
                            changed = True

                # 7. 1936 Harrow Road specific entries
                if yr == "1936":
                    if hn == "24" and "harrow house" in bn.lower():
                        bn = "Harrow House"
                        tr = "Accountant"
                        changed = True
                    elif hn == "26" and "furnisher" in tr.lower():
                        tr = "Ironworker"
                        changed = True
                    elif hn == "28" and "aughtsman" in tr.lower():
                        fn = "John"
                        tr = "Draughtsman"
                        changed = True
                    elif hn == "31" and "grove house" in bn.lower():
                        bn = "Grove House"
                        tr = "Manager"
                        changed = True
                    elif hn == "32" and ("ydene" in tr.lower() or "iv" in fn.lower()):
                        fn = "S. H."
                        bn = "Ivydene"
                        tr = ""
                        changed = True

            # Dataset-wide extraction of Mon Abria, Ivydene, Lorna Doone, Oak View if trapped in trade
            else:
                if re.match(r"^mon\s*abri?a?$", tr, re.I):
                    bn = "Mon Abria"
                    tr = ""
                    changed = True
                elif re.match(r"^ivydene$", tr, re.I):
                    bn = "Ivydene"
                    tr = ""
                    changed = True
                elif re.match(r"^oak\s*v(?:iew)?$", tr, re.I):
                    bn = "Oak View"
                    tr = ""
                    changed = True
                elif re.match(r"^lorna\s*doone$", tr, re.I):
                    bn = "Lorna Doone"
                    tr = ""
                    changed = True

            if changed:
                healed_count += 1
                r["street"] = st
                r["house_number"] = hn
                r["surname"] = sn
                r["forename"] = fn
                r["building_name"] = bn
                r["trade"] = tr

            rows.append(r)

    print(f"Healed {healed_count:,} records in data.csv (including {harrow_reassigned} records restored to Harrow Road).")

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def heal_volume_1882():
    print("Fixing volume_csvs/1882_cleaned.csv High Street, Pill misalignment...")
    with open(VOL_1882_CSV, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    new_lines = []
    fixed_count = 0
    for line in lines:
        parts = line.strip().split(",")
        if len(parts) >= 8 and parts[0] == "1882" and parts[1] == "High Street" and parts[2] == "Pill":
            # line was: 1882,High Street,Pill,door,fn,sn,tr,src
            door = parts[3]
            actual_fn = parts[4]
            actual_sn = parts[5]
            actual_tr = parts[6]
            actual_src = parts[7]
            bldg = ""

            # Special pub / building handling
            if actual_sn == "Rising Sun":
                bldg = "Rising Sun"
                actual_sn = "May"
                actual_fn = "Philip"
                actual_tr = ""
            elif actual_sn == "Orange Tree":
                bldg = "Orange Tree"
                actual_sn = "Foley"
                actual_fn = "Timothy"
                actual_tr = ""
            elif "St. Michael" in actual_sn or "St. Michael" in actual_fn:
                door = "13-15"
                bldg = "St. Michael's Catholic schools"
                actual_sn = ""
                actual_fn = ""
                actual_tr = ""
            elif actual_fn == "Richard" and actual_sn == "Fussey":
                door = ""
                actual_sn = "Fussey"
                actual_fn = "Richard"
            elif not actual_fn and not actual_sn and "void" in actual_tr.lower():
                actual_sn = ""
                actual_fn = ""
                actual_tr = "Void"
            else:
                # In 1882 raw line: parts[4] was forename, parts[5] was surname
                actual_sn = parts[5]
                actual_fn = parts[4]

            new_line = f'1882,"High Street, Pill",{door},{bldg},{actual_sn},{actual_fn},{actual_tr},{actual_src}\n'
            new_lines.append(new_line)
            fixed_count += 1
        else:
            new_lines.append(line)

    print(f"Fixed {fixed_count} lines in {VOL_1882_CSV}.")
    with open(VOL_1882_CSV, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def heal_volume_1927():
    print("Fixing volume_csvs/1927_cleaned.csv Harrow Road records under HARRY STREET...")
    with open(VOL_1927_CSV, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    new_lines = []
    fixed_count = 0
    for line in lines:
        if "1927,HARRY STREET" in line:
            # Check if it belongs to Harrow Road (lines 15 to 43 or Harrow Road Garage)
            if re.search(r",HARRY STREET,(?:15|17|19|21|23|25|27|29|31|33|35|37|39|41|43),", line) or "Harrow Road Garage" in line:
                line = line.replace("1927,HARRY STREET,", "1927,HARROW ROAD,")
                fixed_count += 1
        new_lines.append(line)

    print(f"Fixed {fixed_count} lines in {VOL_1927_CSV}.")
    with open(VOL_1927_CSV, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def update_app_js():
    print("Updating src/js/app.js cleanOccupation() to recognize house names...")
    with open(APP_JS, "r", encoding="utf-8") as f:
        js = f.read()

    # Expand house names pattern in cleanOccupation()
    old_pat = """      // Filter house/villa/building names left in trade column (e.g., "The Woodlands", "Norwood", "Eversley", "Rosetta", "Brynholme", "Gasworks", "Woolmer")
      if (
        /^(the\\s+woodlands|norwood|eversley|rosetta|brynholme|gasworks|woolmer)$/i.test(clean) ||
        /^(bryn|villas?|cottage|house|lodge|manor|hall|court|view|terrace|gardens)\\b/i.test(clean)
      ) {"""

    new_pat = """      // Filter house/villa/building names left in trade column (e.g., "The Woodlands", "Norwood", "Eversley", "Rosetta", "Brynholme", "Gasworks", "Woolmer")
      if (
        /^(the\\s+woodlands|norwood|eversley|rosetta|brynholme|gasworks|woolmer|oak\\s*v(?:iew)?|mon\\s*abri?a?|ivydene|lorna\\s*doone|revelstoke|lydbrook|selsdon|tyrone|wellesley|chertsey|monteville|merridale|pendre|frome\\s*vale|tranmere|elford|dun(?:k|s)k?well|ryecroft|oswald|st\\.?\\s*audries|watford|grove|dean|ff?ynonau)$/i.test(clean) ||
        /^(bryn|villas?|cottage|house|lodge|manor|hall|court|view|terrace|gardens)\\b/i.test(clean)
      ) {"""

    if old_pat in js:
        js = js.replace(old_pat, new_pat)
        with open(APP_JS, "w", encoding="utf-8") as f:
            f.write(js)
        print("Updated app.js cleanOccupation() successfully.")
    else:
        print("Notice: old_pat not matched verbatim in app.js, checking if already updated...")

def main():
    heal_data_csv()
    heal_volume_1882()
    heal_volume_1927()
    update_app_js()

    print("\nRebuilding site data and JSON indexes...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_site_data.py")], check=True)

    print("\nRebuilding trades data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_trades_data.py")], check=True)

    print("\nRebuilding stats data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_stats_data.py")], check=True)

    print("\n[SUCCESS] Harrow Road and house names successfully healed!")

if __name__ == "__main__":
    main()
