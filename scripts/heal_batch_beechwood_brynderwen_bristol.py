import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

MAPPINGS = {
    "Barnard Hill": "Barrack Hill",
    "Beechwood Road. Ch": "Beechwood Road",
    "Bridge Street (continued)": "Bridge Street",
    "Bristol St. (new)": "Bristol Street",
    "Bryn derivation Road": "Brynderwen Road",
    "Bryn-derwen Road": "Brynderwen Road",
    "Bryn-derwyn Road": "Brynderwen Road",
}

def run():
    print("Reading data.csv...")
    rows = []
    counts = {k: 0 for k in MAPPINGS}
    counts["Beechwood Public Park"] = 0
    counts["Bellevue Street"] = 0

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            st = r.get("street", "").strip()

            # 1. Beechwood Public Park -> Christchurch Road with untangled fields
            if st == "Beechwood Public Park":
                counts["Beechwood Public Park"] += 1
                r["street"] = "Christchurch Road"
                trade = r.get("trade", "").strip()
                sn = r.get("surname", "").strip()
                fn = r.get("forename", "").strip()

                if trade == "Rickards":
                    r["building_name"] = "Myrtle villa"
                    r["surname"] = "Rickards"
                    r["forename"] = "Mrs."
                    r["trade"] = ""
                elif trade == "Kerslake":
                    r["building_name"] = "Southernwood villa"
                    r["surname"] = "Kerslake"
                    r["forename"] = "J."
                    r["trade"] = ""
                elif trade == "Waters":
                    r["building_name"] = "Viburnum villa"
                    r["surname"] = "Waters"
                    r["forename"] = "Thos."
                    r["trade"] = ""
                elif trade == "Kersey":
                    r["building_name"] = "Hill top"
                    r["surname"] = "Kersey"
                    r["forename"] = "W. H."
                    r["trade"] = ""
                elif trade == "Lupini":
                    r["building_name"] = "Overhill house"
                    r["surname"] = "Lupini"
                    r["forename"] = "J."
                    r["trade"] = ""
                elif trade == "Hill":
                    r["building_name"] = "High view"
                    r["surname"] = "Hill"
                    r["forename"] = "Henry"
                    r["trade"] = ""
                elif trade == "Perkins":
                    r["building_name"] = "Woodview"
                    r["surname"] = "Perkins"
                    r["forename"] = "John"
                    r["trade"] = ""
                elif sn == "Brown" and fn == "Joseph":
                    r["building_name"] = "Beechwood park"

            # 2. Bellevue Street -> Belvedere Terrace (and fix James Jones)
            elif st == "Bellevue Street":
                counts["Bellevue Street"] += 1
                r["street"] = "Belvedere Terrace"
                if r.get("house_number") == "28" and r.get("surname") == "James":
                    r["surname"] = "Jones"
                    r["forename"] = "James"

            # 3. Standard mappings
            elif st in MAPPINGS:
                counts[st] += 1
                r["street"] = MAPPINGS[st]

            rows.append(r)

    print("Replacements made in data.csv:")
    for k, v in counts.items():
        print(f"  {k} -> {MAPPINGS.get(k, 'Mapped')}: {v}")

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("data.csv updated successfully.")

    print("Updating master_streets.json...")
    with open(MASTER_PATH, "r", encoding="utf-8") as f:
        master = json.load(f)

    streets = master.get("streets", {})

    def add_alias(slug, alias):
        if slug in streets:
            aliases = streets[slug].get("aliases", [])
            if alias not in aliases:
                aliases.append(alias)
                streets[slug]["aliases"] = aliases
                print(f"Added alias '{alias}' to {slug}")
        else:
            print(f"WARNING: Slug {slug} not found in master_streets.json")

    add_alias("barrack-hill", "Barnard Hill")
    add_alias("christchurch-road", "Beechwood Public Park")
    add_alias("beechwood-road", "Beechwood Road. Ch")
    add_alias("belvedere-terrace", "Bellevue Street")
    add_alias("bridge-street", "Bridge Street (continued)")
    add_alias("bristol-street", "Bristol St. (new)")
    add_alias("brynderwen-road", "Bryn derivation Road")
    add_alias("brynderwen-road", "Bryn-derwen Road")
    add_alias("brynderwen-road", "Bryn-derwyn Road")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json saved.")

if __name__ == "__main__":
    run()
