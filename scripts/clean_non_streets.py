#!/usr/bin/env python3
"""
Comprehensive Street Normalization & Non-Street Triage
======================================================
1. Strips all map grid codes and district references:
   - 'Lord Street (B.T.)', 'Canon Street B.T' -> 'Lord Street', 'Canon Street'
   - 'Locke Street, C 5', 'Bailey Street, D 5', 'Clytha Park, C 5' -> 'Locke Street', etc.
   - 'London Street. M.', 'Alma Street. P', 'Aberthaw Road. C' -> 'London Street', etc.
2. Removes pure advertisement/running-header noise rows:
   - 'Send For Book Describing “little By Little” Purchasing Plan'
   - 'Suppliers Of Best Grade Office Stationery'
   - 'The Progressive Money Society'
3. Remaps misattributed running headers to parent streets:
   - 'The Newport Steam Laundry Co., Bath Street' (493 residents) -> merged to preceding streets
   - 'NEWPORT STREET LIST. - COMMERCIAL STREET' -> Commercial Street
   - 'NEWPORT STREET LIST. Lew' -> Lewis Street
   - 'NEWPORT STREET LIST. Luc - Mal' -> Lucas Street
   - 'NEWPORT STREET LIST' (1886) -> Commercial Wharf
4. Remaps institutions and split post offices to parent streets:
   - 't.s.o', 't.s.o., T. & M.o. S' -> Stow Hill
   - 'Primitive Meth. Mission Hall' -> Lyne Road
   - 'Wesleyan Mission Hall' -> Archibald Street
   - 'Thomas W. Calvin, local' -> High Street
   - 'S. JOHN EVANGELIST CHURCH' -> Kensington Place
   - 'S. John Baptist' -> Bassaleg Road
   - 'Summers Rev. J. F., Street' -> Waterloo Road
   - 'The Old Cemetery' -> Clifton Road
   - 'THE BARRACKS' / 'The Barracks' / 'Barracks' -> Barrack Hill
5. Rebuilds site data and statistics.
"""

import csv
import re
import shutil
import subprocess

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_screenshot_cleanup"

CANONICAL_LOOKUP = {
    "commercial st": "Commercial Street",
    "commercial rd": "Commercial Road",
    "high st": "High Street",
    "dock st": "Dock Street",
    "shaftesbury st": "Shaftesbury Street",
    "caerau rd": "Caerau Road",
    "cardiff rd": "Cardiff Road",
    "chepstow rd": "Chepstow Road",
    "christchurch rd": "Christchurch Road",
    "clarence st": "Clarence Street",
    "durham rd": "Durham Road",
    "george st": "George Street",
    "hill st": "Hill Street",
    "jones st": "Jones Street",
    "lewis st": "Lewis Street",
    "lime st": "Lime Street",
    "malpas rd": "Malpas Road",
    "marshes rd": "Marshes Road",
    "nelson st": "Nelson Street",
    "new st": "New Street",
    "oxford st": "Oxford Street",
    "portland st": "Portland Street",
    "potter st": "Potter Street",
    "prince st": "Prince Street",
    "raglan st": "Raglan Street",
    "robert st": "Robert Street",
    "temple st": "Temple Street",
    "tredegar st": "Tredegar Street",
    "victoria ave": "Victoria Avenue",
    "waterloo rd": "Waterloo Road",
    "woodland rd": "Woodland Road",
    "alexandra docks": "Alexandra Docks",
    "glo'ster st": "Gloucester Street",
    "glo'ster street": "Gloucester Street",
    "glo'ster place": "Gloucester Place",
    "watchhouse par": "Watchhouse Parade",
    "watchhouse parade": "Watchhouse Parade",
    "upper lime st": "Upper Lime Street",
    "upper lime street": "Upper Lime Street",
    "courtybella st": "Courtybella Street",
    "courtybella street": "Courtybella Street",
    "upper baldwin st": "Upper Baldwin Street",
    "upper baldwin street": "Upper Baldwin Street",
    "up. williams st": "Upper Williams Street",
    "up. lewis street": "Upper Lewis Street",
    "summer hill rd": "Summerhill Road",
    "manchester st": "Manchester Street"
}

def clean_map_references(st):
    s = st.strip()

    # 1. Strip Barnard Town / Tredegar Wharf / District initials: (B.T.), B.T., B. T., (B T), B.T, (T.W.), T.W.
    s = re.sub(r'[\s\.\,]+(\(?B\.?\s*T\.?\)?|\(?T\.?\s*W\.?\)?)$', '', s, flags=re.I)

    # 2. Strip Map grid references: , C 5, . C 5, C 5, D 5, B 4, F 2, E 4, etc.
    s = re.sub(r'[\s\.\,]+[A-F]\s*\d+[a-z]?$', '', s, flags=re.I)

    # 3. Strip district codes (. M., . P., . C., . B.) at the end of known street words
    sfx = r'(?:street|road|avenue|place|terrace|crescent|parade|lane|hill|park|row|square|view|cottages|drive|gardens|grove|mews|walk|way|par|st|rd|circus)'
    s = re.sub(rf'(\b{sfx})[\s\.\,]+[MPCB]\.?$', r'\1', s, flags=re.I)

    # 4. Strip trailing punctuation
    s = re.sub(r'[\.\,\:\;\-]+$', '', s).strip()

    # Canonical dictionary lookup
    lower_s = s.lower()
    if lower_s in CANONICAL_LOOKUP:
        s = CANONICAL_LOOKUP[lower_s]
    elif lower_s.endswith(' st'):
        root = s[:-3].strip()
        s = f"{root} Street"
    elif lower_s.endswith(' rd'):
        root = s[:-3].strip()
        s = f"{root} Road"
    elif lower_s.endswith(' par'):
        root = s[:-4].strip()
        s = f"{root} Parade"

    return s

def run():
    print(f"Backing up {DATA_CSV} -> {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)

    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        raw_rows = list(reader)

    print(f"Read {len(raw_rows):,} rows.")

    cleaned_rows = []
    current_context_street = "Commercial Street"

    dropped_count = 0
    modified_count = 0

    for idx, r in enumerate(raw_rows):
        st = r.get("street", "").strip()
        hnum = r.get("house_number", "").strip()
        bname = r.get("building_name", "").strip()
        sname = r.get("surname", "").strip()
        fname = r.get("forename", "").strip()
        tr = r.get("trade", "").strip()
        yr = r.get("year", "").strip()

        # Update running context street when valid street is seen
        if st and not any(k in st.upper() for k in ["STEAM LAUNDRY", "SEND FOR BOOK", "SUPPLIERS OF", "PROGRESSIVE MONEY", "NEWPORT STREET LIST"]):
            current_context_street = clean_map_references(st)

        # 1. Drop pure artifact / noise advertisement rows
        if any(ad in st for ad in [
            "Send For Book Describing",
            "Suppliers Of Best Grade Office Stationery",
            "The Progressive Money Society"
        ]):
            dropped_count += 1
            continue

        if "Steam Laundry" in st:
            is_artifact = (
                (bname in ["ALE", "ALM", "BRI", "CAE", "STOW"] and not sname) or
                ("NEWPORT" in bname and "STREET DIRECTORY" in sname) or
                ("NEWPORT" in sname and "STREET DIRECTORY" in fname) or
                (not hnum and not sname and not tr)
            )
            if is_artifact:
                dropped_count += 1
                continue
            # Merge resident to preceding street context
            r["street"] = current_context_street
            modified_count += 1
            cleaned_rows.append(r)
            continue

        # 2. Specific Non-Street Remappings
        if st == "NEWPORT STREET LIST":
            if yr == "1886":
                st = "Commercial Wharf"
            elif yr == "1899":
                st = "Commercial Road"
            else:
                st = current_context_street
        elif st == "NEWPORT STREET LIST. - COMMERCIAL STREET":
            st = "Commercial Street"
        elif st == "NEWPORT STREET LIST. Lew":
            st = "Lewis Street"
        elif st == "NEWPORT STREET LIST. Luc - Mal":
            st = "Lucas Street"
        elif st in ["t.s.o", "t.s.o., T. & M.o. S"]:
            st = "Stow Hill"
        elif st == "Primitive Meth. Mission Hall":
            st = "Lyne Road"
            bname = bname or "Primitive Methodist Mission Hall"
        elif st == "Wesleyan Mission Hall":
            st = "Archibald Street"
            bname = bname or "Wesleyan Mission Hall"
        elif st == "Thomas W. Calvin, local":
            st = "High Street"
            bname = bname or "Corn Exchange"
        elif st == "S. JOHN EVANGELIST CHURCH":
            st = "Kensington Place"
            bname = bname or "St. John Evangelist Church"
        elif st == "S. John Baptist":
            st = "Bassaleg Road"
        elif "Summers Rev. J. F" in st:
            st = "Waterloo Road"
        elif st == "The Old Cemetery":
            st = "Clifton Road"
        elif st in ["THE BARRACKS", "The Barracks", "Barracks"]:
            st = "Barrack Hill"
        elif st == "Office, M.o. & S.b. & A. &":
            st = "Penylan Road"
        elif st == "Commercial Road Post Office, M.o.,s.b., & A.& I. Office":
            st = "Commercial Road"
            bname = bname or "Post Office"
        elif st == "Dyes In All Art Shades. Blacks A Speciality":
            st = "High Street"
        else:
            # 3. Clean Map & District Reference Suffixes
            cleaned_st = clean_map_references(st)
            if cleaned_st != st:
                st = cleaned_st

        if st != r.get("street") or bname != r.get("building_name"):
            modified_count += 1
            r["street"] = st
            r["building_name"] = bname

        cleaned_rows.append(r)

    print(f"Total dropped artifact rows: {dropped_count}")
    print(f"Total modified rows: {modified_count:,}")
    print(f"Remaining clean rows: {len(cleaned_rows):,}")

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print("\nRunning trade-in-name disentanglement cleanup...")
    subprocess.run(["python3", "scripts/clean_trades_in_names.py"], check=True)
    print("\nComplete!")

if __name__ == "__main__":
    run()
