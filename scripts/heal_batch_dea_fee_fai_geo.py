import csv
import json
import os

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

def clean_name(s):
    return s.strip() if s else ""

def should_swap(fn, sn):
    fn_c = clean_name(fn)
    sn_c = clean_name(sn)
    if not fn_c or not sn_c:
        return False
    if fn_c.lower() in ["void", "vacant", "sites", "stables"]:
        return False
    if sn_c.lower() in ["void", "vacant", "sites", "stables", "-"]:
        return False
    # If sn starts with Mrs./Miss/Mr. or is a known given name / initials
    return True

def run():
    print("Reading data.csv...")
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            rows.append(r)

    total_rows = len(rows)
    print(f"Total rows: {total_rows}")

    # Track counts
    counts = {
        "Devon Place (Gold Tops)": 0,
        "Carisbrook Road": 0,
        "Fulford's Cottages (5)": 0,
        "Goodrich Crescent. B 4 (formerly Ross and Goodrich Streets)": 0,
        "Goodrich Crscnt": 0,
        "F. Oak Ter. (Lwr.)": 0,
        "Fair Oak Ter. (Lwr.)": 0,
        "Dea": 0,
        "Fai": 0,
        "Geo": 0,
        "Fee_FairOak": 0,
        "Fee_Faulkner": 0,
        "Fee_Feering": 0,
    }

    # Pass 1: Simple merges and Dea / Fai / Geo
    # For Fee, let's track the section based on row sequence
    in_fee_section = 0 # 0=not in fee, 1=fair oak doors 5-35, 2=faulkner doors 1-9, 3=feering
    for idx, r in enumerate(rows):
        st = r.get("street")

        if st == "Devon Place (Gold Tops)":
            r["street"] = "Devon Place"
            counts["Devon Place (Gold Tops)"] += 1

        elif st == "Carisbrook Road":
            r["street"] = "Carisbrooke Road"
            counts["Carisbrook Road"] += 1

        elif st == "Fulford's Cottages (5)":
            r["street"] = "Fulford's Cottages"
            counts["Fulford's Cottages (5)"] += 1

        elif st == "Goodrich Crescent. B 4 (formerly Ross and Goodrich Streets)":
            r["street"] = "Goodrich Crescent"
            counts["Goodrich Crescent. B 4 (formerly Ross and Goodrich Streets)"] += 1

        elif st == "Goodrich Crscnt":
            r["street"] = "Goodrich Crescent"
            counts["Goodrich Crscnt"] += 1

        elif st == "F. Oak Ter. (Lwr.)":
            r["street"] = "Lower Fair Oak Terrace"
            counts["F. Oak Ter. (Lwr.)"] += 1

        elif st == "Fair Oak Ter. (Lwr.)":
            r["street"] = "Lower Fair Oak Terrace"
            counts["Fair Oak Ter. (Lwr.)"] += 1

        elif st == "Dea":
            r["street"] = "Dean Street"
            counts["Dea"] += 1
            if should_swap(r.get("forename"), r.get("surname")):
                r["forename"], r["surname"] = r["surname"], r["forename"]

        elif st == "Fai":
            r["street"] = "Fair Oak Avenue"
            counts["Fai"] += 1
            if should_swap(r.get("forename"), r.get("surname")):
                r["forename"], r["surname"] = r["surname"], r["forename"]

        elif st == "Geo":
            r["street"] = "Gaskell Street"
            counts["Geo"] += 1
            # Geo already has correct forename / surname order: Mrs. Sarah Kenney, Andrew Rollason, Wm. Lawton

        elif st == "Fee":
            # Determine section by index or content
            # Row 359201 to 359232 (doors 5 to 35) -> Fair Oak Terrace
            # Row 359233 to 359242 (doors 1 to 9) -> Faulkner Road
            # Row 359243 to 359299 (odds 1..57, evens 60..12) -> Feering Street
            num = r.get("house_number", "")
            sn = r.get("surname", "")
            fn = r.get("forename", "")

            # If row index is between 359201 and 359232
            if idx <= 359232:
                r["street"] = "Fair Oak Terrace"
                counts["Fee_FairOak"] += 1
                if should_swap(fn, sn):
                    r["forename"], r["surname"] = sn, fn
            elif idx <= 359242:
                r["street"] = "Faulkner Road"
                counts["Fee_Faulkner"] += 1
                if should_swap(fn, sn):
                    r["forename"], r["surname"] = sn, fn
            else:
                r["street"] = "Feering Street"
                counts["Fee_Feering"] += 1
                if should_swap(fn, sn):
                    r["forename"], r["surname"] = sn, fn

    print("Merge counts:")
    for k, v in counts.items():
        print(f"  {k}: {v}")

    # Write data.csv
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("data.csv updated successfully.")

    # Update master_streets.json
    with open(MASTER_PATH, "r", encoding="utf-8") as f:
        master = json.load(f)
    streets = master.setdefault("streets", {})

    def add_alias(key, alias):
        if key in streets:
            aliases = streets[key].setdefault("aliases", [])
            if alias not in aliases:
                aliases.append(alias)
                print(f"Added alias '{alias}' to '{key}'")

    add_alias("devon-place", "Devon Place (Gold Tops)")
    add_alias("carisbrooke-road", "Carisbrook Road")
    add_alias("fulford-s-cottages", "Fulford's Cottages (5)")
    add_alias("goodrich-crescent", "Goodrich Crescent. B 4 (formerly Ross and Goodrich Streets)")
    add_alias("goodrich-crescent", "Goodrich Crscnt")
    add_alias("dean-street", "Dea")
    add_alias("fair-oak-terrace", "Fee")
    add_alias("faulkner-road", "Fee")
    add_alias("feering-street", "Fee")
    add_alias("gaskell-street", "Geo")

    if "lower-fair-oak-terrace" not in streets:
        streets["lower-fair-oak-terrace"] = {
            "canonical_name": "Lower Fair Oak Terrace",
            "slug": "lower-fair-oak-terrace",
            "district": "",
            "parish": "",
            "former_names": [],
            "sub_sections": [],
            "numbering_scheme": {"type": "ODDS_EVENS", "approx_change_year": None},
            "cross_streets": [],
            "aliases": ["F. Oak Ter. (Lwr.)", "Fair Oak Ter. (Lwr.)", "Lower Fairoak Terrace"],
            "audit": {"status": "NAME_VERIFIED", "verified_by": "Rob Gale", "notes": "Unified F. Oak Ter. (Lwr.) & Fair Oak Ter. (Lwr.)"},
            "coordinates": {"lat": None, "lng": None},
            "audit_status": "NAME_VERIFIED",
            "notes": "",
            "latitude": "",
            "longitude": ""
        }
        print("Created lower-fair-oak-terrace in master_streets.json")
    else:
        for al in ["F. Oak Ter. (Lwr.)", "Fair Oak Ter. (Lwr.)", "Lower Fairoak Terrace"]:
            add_alias("lower-fair-oak-terrace", al)

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json updated.")

if __name__ == "__main__":
    run()
