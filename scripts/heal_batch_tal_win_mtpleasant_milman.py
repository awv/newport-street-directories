import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

def clean_win(r):
    fn = r.get("forename", "").strip()
    sn = r.get("surname", "").strip()
    tr = r.get("trade", "").strip()

    # Cases in Win
    if fn == "Rowe Jos." and sn == "drawing master":
        r["forename"], r["surname"], r["trade"] = "Jos.", "Rowe", "drawing master"
    elif fn == "Chambers T.":
        r["forename"], r["surname"] = "T.", "Chambers"
    elif fn == "Nott Mrs.":
        r["forename"], r["surname"] = "Mrs.", "Nott"
    elif fn == "Nott Geo." and sn == "music teacher":
        r["forename"], r["surname"], r["trade"] = "Geo.", "Nott", "music teacher"
    elif fn == "George Mrs. A.":
        r["forename"], r["surname"] = "Mrs. A.", "George"
    elif fn == "Nichols J. A." and sn == "printer":
        r["forename"], r["surname"], r["trade"] = "J. A.", "Nichols", "printer"
    elif fn == "Edwards T. B.":
        r["forename"], r["surname"] = "T. B.", "Edwards"
    elif fn == "Jacobs I.":
        r["forename"], r["surname"] = "I.", "Jacobs"
    elif fn == "Pritchard J.":
        r["forename"], r["surname"] = "J.", "Pritchard"
    elif fn == "Watkins Mrs. P.":
        r["forename"], r["surname"] = "Mrs. P.", "Watkins"
    elif fn == "Wilson Geo.":
        r["forename"], r["surname"] = "Geo.", "Wilson"
    elif fn == "Williams A. E.":
        r["forename"], r["surname"] = "A. E.", "Williams"

def clean_tal(r):
    fn = r.get("forename", "").strip()
    sn = r.get("surname", "").strip()
    tr = r.get("trade", "").strip()

    if r.get("house_number") == "39" and sn == "Sydney" and "Lewis" in tr:
        r["forename"], r["surname"], r["trade"] = "Sydney", "Lewis", "Sheetweigher"
    elif r.get("house_number") == "54" and "Thos." in tr:
        r["forename"], r["trade"] = "Jas. Thos.", "Guard"
    elif r.get("house_number") == "24" and "Sid." in tr:
        r["forename"], r["trade"] = "Jas. Sid.", "Clerk"

def run():
    print("Reading data.csv...")
    rows = []
    counts = {
        "Tal": 0,
        "Win": 0,
        "Mt. Pleasant Cottages": 0,
        "Millman Street": 0,
    }

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            st = r.get("street")
            if st == "Tal":
                r["street"] = "Sutton Road"
                clean_tal(r)
                counts["Tal"] += 1
            elif st == "Win":
                r["street"] = "Windsor Terrace"
                clean_win(r)
                counts["Win"] += 1
            elif st == "Mt. Pleasant Cottages":
                r["street"] = "Mount Pleasant Cottages"
                counts["Mt. Pleasant Cottages"] += 1
            elif st == "Millman Street":
                r["street"] = "Milman Street"
                counts["Millman Street"] += 1
            rows.append(r)

    print("Updated counts:")
    for k, v in counts.items():
        print(f"  {k}: {v}")

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("data.csv saved.")

    with open(MASTER_PATH, "r", encoding="utf-8") as f:
        master = json.load(f)
    streets = master.setdefault("streets", {})

    def add_alias(key, alias):
        if key in streets:
            aliases = streets[key].setdefault("aliases", [])
            if alias not in aliases:
                aliases.append(alias)
                print(f"Added alias '{alias}' to '{key}'")
        else:
            print(f"WARNING: key '{key}' not in master_streets!")

    add_alias("sutton-road", "Tal")
    add_alias("windsor-terrace", "Win")
    add_alias("milman-street", "Millman Street")

    if "mount-pleasant-cottages" not in streets:
        streets["mount-pleasant-cottages"] = {
            "canonical_name": "Mount Pleasant Cottages",
            "slug": "mount-pleasant-cottages",
            "district": "",
            "parish": "",
            "former_names": [],
            "sub_sections": [],
            "numbering_scheme": {"type": "CONSECUTIVE", "approx_change_year": None},
            "cross_streets": [],
            "aliases": ["Mt. Pleasant Cottages"],
            "audit": {"status": "NAME_VERIFIED", "verified_by": "Rob Gale", "notes": "Unified Mount Pleasant Cottages & Mt. Pleasant Cottages"},
            "coordinates": {"lat": None, "lng": None},
            "audit_status": "NAME_VERIFIED",
            "notes": "",
            "latitude": "",
            "longitude": ""
        }
        print("Created mount-pleasant-cottages in master_streets.json")
    else:
        add_alias("mount-pleasant-cottages", "Mt. Pleasant Cottages")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json updated.")

if __name__ == "__main__":
    run()
