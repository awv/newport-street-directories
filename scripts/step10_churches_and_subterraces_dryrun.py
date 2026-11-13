#!/usr/bin/env python3
"""
step10_churches_and_subterraces_dryrun.py

Dry run for Step 10:
1. Church & Institution "St." Realignment:
   - Old Cardiff Road #17: St. Thomas's Church & St. Thomas' Church Hall
   - Alexandra Road: St. Stephen's Church & St. Stephen's Church Hall
   - Gaer Road: St. Martin's Church (purge #St house number)
   - Commercial Street 1894, Bridge Street 1899, Commercial Road 1900, Dock Street 1925
2. Purge Phantom Directory Page Headers & Ad Banners (39 records including Adeline St #240, Arthur St #405)
3. Purge Orphan Cross-Reference Street Pointers (including Old Cardiff Road OLD COTTAGES)
4. Propagate Mid-Street Sub-Terrace Names to subsequent house rows (e.g. Peartree Cottages, Dock Cottages)
"""

import csv
import re

def clean_terrace_name(name):
    # e.g. "PEARTREE COTTAGES—" -> "Peartree Cottages"
    name = re.sub(r"[\—\-\:\.\,]+$", "", name).strip()
    return name.title()

def main():
    rows = []
    with open("data.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows)} records from data.csv.")

    # 1. Church Realignments
    church_fixed = 0
    for r in rows:
        yr = r.get("year", "")
        st = r.get("street", "")
        hn = r.get("house_number", "")
        sn = r.get("surname", "")
        fn = r.get("forename", "")
        bldg = r.get("building_name", "")

        # Old Cardiff Road 1971 #17
        if yr == "1971" and st == "Old Cardiff Road" and hn == "17":
            r["forename"] = ""
            r["surname"] = "St. Thomas's Church"
            r["building_name"] = "St. Thomas' Church Hall"
            church_fixed += 1

        # Alexandra Road 1971
        elif yr == "1971" and st == "Alexandra Road" and "Stephen" in sn and "Church" in sn:
            r["building_name"] = "St. Stephen's Church Hall"
            church_fixed += 1

        # Gaer Road 1971
        elif yr == "1971" and st == "Gaer Road" and "Martin" in sn and "Church" in sn:
            r["house_number"] = ""
            r["surname"] = "St. Martin's Church"
            church_fixed += 1

        # Commercial Street 1894
        elif yr == "1894" and st == "Commercial Street" and sn == "St. Paul's Church":
            r["forename"] = ""
            church_fixed += 1

        # Bridge Street 1899
        elif yr == "1899" and st == "Bridge Street" and sn == "St. Luke's Church":
            r["forename"] = ""
            church_fixed += 1

        # Commercial Road 1900
        elif yr == "1900" and st == "Commercial Road" and "ANDREW'S CHURCH" in sn:
            r["house_number"] = ""
            r["forename"] = ""
            r["surname"] = "St. Andrew's Church"
            church_fixed += 1

        # Dock Street 1925
        elif yr == "1925" and st == "Dock Street" and sn == "St. James Church":
            r["forename"] = ""
            church_fixed += 1

    print(f"Church & Institution Realignments: {church_fixed} records fixed.")

    # 2. Directory Page Headers & Commercial Banner Records
    phantom_indices = set()
    for idx, r in enumerate(rows):
        hn = r.get("house_number", "")
        sn = r.get("surname", "").strip()
        fn = r.get("forename", "").strip()
        full = f"{fn} {sn}".strip()
        
        # Check running headers like "240 NEWPORT", "405 EDWARDS LTD..."
        if hn.isdigit() and int(hn) > 100:
            if full in ["NEWPORT", "NEWPORT DIRECTORY", "DIRECTORY", "STREET DIRECTORY"] or "LIMITED" in full or "LTD" in full or "TELEPHONE" in full or "TEL." in full:
                phantom_indices.add(idx)

    # 3. Cross-reference pointers & Sub-terrace headers
    subterrace_propagated = 0
    subterrace_headers_removed = 0
    
    i = 0
    while i < len(rows):
        r = rows[i]
        st = r.get("street", "")
        hn = r.get("house_number", "").strip()
        sn = r.get("surname", "").strip()
        fn = r.get("forename", "").strip()
        bldg = r.get("building_name", "").strip()
        trade = r.get("trade", "").strip()
        yr = r.get("year", "")

        # Check if row is an isolated all-caps header
        if sn.isupper() and len(sn) > 3 and not fn and not hn and not trade and not bldg:
            if any(w in sn for w in ["COTTAGES", "TERRACE", "PLACE", "ROAD", "STREET", "SQUARE", "VILLAS", "HOUSES", "BUILDINGS", "COURT", "ROW", "GARDENS", "AVENUE", "HILL"]):
                # Look ahead to see if subsequent rows belong to this sub-terrace
                terrace_title = clean_terrace_name(sn)
                matched_ahead = 0
                j = i + 1
                while j < len(rows) and j < i + 15:
                    next_r = rows[j]
                    if next_r.get("street") != st or next_r.get("year") != yr:
                        break
                    next_hn = next_r.get("house_number", "").strip()
                    next_sn = next_r.get("surname", "").strip()
                    # If next row is another header, break
                    if next_sn.isupper() and not next_r.get("forename") and not next_hn:
                        break
                    # If next row has a house number and no building name, it belongs to this terrace!
                    if next_hn and not next_r.get("building_name"):
                        next_r["building_name"] = terrace_title
                        matched_ahead += 1
                        subterrace_propagated += 1
                    j += 1

                # Whether it matched ahead (mid-street sub-terrace) or was an orphan pointer (like OLD COTTAGES),
                # the header row itself is NOT a human resident and should be removed!
                phantom_indices.add(i)
                subterrace_headers_removed += 1
        i += 1

    print(f"Phantom Headers / Banners / Pointers identified: {len(phantom_indices)} rows to remove.")
    print(f"Mid-Street Sub-Terrace Names Propagated to Residents: {subterrace_propagated} resident records enriched with building_name.")

    new_rows = [r for idx, r in enumerate(rows) if idx not in phantom_indices]
    print(f"Total dataset after Step 10: {len(new_rows)} clean records (down from {len(rows)}).")

    # Verify Old Cardiff Road
    print("\n--- Verification: Old Cardiff Road 1971 ---")
    ocr_1971 = [r for r in new_rows if r.get("street") == "Old Cardiff Road" and r.get("year") == "1971"]
    for r in ocr_1971:
        print(f"  #{r.get('house_number')} | {r.get('forename')} {r.get('surname')} | bldg: {r.get('building_name')}")

    # Verify Lliswerry Road Peartree Cottages
    print("\n--- Verification: Lliswerry Road 1936 (Peartree Cottages) ---")
    lwr_1936 = [r for r in new_rows if r.get("street") == "Lliswerry Road" and r.get("year") == "1936" and r.get("building_name") == "Peartree Cottages"]
    for r in lwr_1936:
        print(f"  #{r.get('house_number')} | {r.get('forename')} {r.get('surname')} | bldg: {r.get('building_name')}")

if __name__ == "__main__":
    main()
