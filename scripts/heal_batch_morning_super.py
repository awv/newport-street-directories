import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

MAPPINGS = {
    "Royal Gwent Hospital": "Cardiff Road",
    "Potters Parade": "Potter's Parade",
    "Winnill Street": "Winmill Street",
    "WILLIAM STREET (continued)": "Williams Street",
    "WHITSTONE ROAD (cont.)": "Whitstone Road",
    "Whitestone Road -continued": "Whitstone Road",
    "Whitestone Road": "Whitstone Road",
    "WHITEHALL (cont.)": "Wheeler Street",
    "West Side—": "Wharves (The)",
    "West Park Post Office": "Stow Hill",
    "West Park": "West Park Road",
    "WELLINGTON Street": "Wellington Street",
    "Wednesday Street": "Wednesbury Street",
    "Victoria Road Congregational Church": "Hill Street",
    "TRINITY PLACE (continued)": "Trinity Place",
    "Street List": "St. Mary Street",
    "Stow Pk. Circus": "Stow Park Circus",
    "Stow Hill Pavilion": "Stow Hill",
    "Stow Hill Schools": "Stow Hill",
    "St. Michael's Catholic Church and Schools": "High Street, Pill",
    "St. Mark's Church": "Gold Tops",
    "St. Marie's Catholic Church": "Stow Hill",
    "St. Marie's Catholic Ch": "Stow Hill",
    "St. Paul's Mission room": "King Street",
    "St. Julian's Av": "St. Julian's Avenue",
    "St. Edward St.-continued": "St. Edward Street",
    "Spitty Lane": "Spytty Lane",
    "South Street": "Spencer Road",
    "St. Woolos Church": "Stow Hill",
}

def run():
    print("Reading data.csv...")
    rows = []
    counts = {k: 0 for k in MAPPINGS}
    walden_fixed = False

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            st = r.get("street")
            if st in MAPPINGS:
                r["street"] = MAPPINGS[st]
                counts[st] += 1
            elif st == "Walden":
                r["street"] = "Gibbs Road"
                r["house_number"] = ""
                r["building_name"] = "Walden"
                r["forename"] = "Joseph S."
                r["surname"] = "Kerslake"
                r["trade"] = ""
                walden_fixed = True
            rows.append(r)

    print("Mappings applied:")
    for k, v in counts.items():
        if v > 0:
            print(f"  {k} -> {MAPPINGS[k]}: {v}")
    if walden_fixed:
        print("  Walden -> Gibbs Road (building: Walden, resident: Joseph S. Kerslake)")

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

    add_alias("cardiff-road", "Royal Gwent Hospital")
    if "potters-parade" in streets:
        streets["potters-parade"]["canonical_name"] = "Potter's Parade"
        add_alias("potters-parade", "Potters Parade")
    add_alias("winmill-street", "Winnill Street")
    add_alias("williams-street", "WILLIAM STREET (continued)")
    add_alias("whitstone-road", "WHITSTONE ROAD (cont.)")
    add_alias("whitstone-road", "Whitestone Road -continued")
    add_alias("whitstone-road", "Whitestone Road")
    add_alias("wheeler-street", "WHITEHALL (cont.)")
    add_alias("wharves-the", "West Side—")
    add_alias("stow-hill", "West Park Post Office")
    add_alias("stow-hill", "Stow Hill Pavilion")
    add_alias("stow-hill", "Stow Hill Schools")
    add_alias("stow-hill", "St. Marie's Catholic Church")
    add_alias("stow-hill", "St. Marie's Catholic Ch")
    add_alias("stow-hill", "St. Woolos Church")
    add_alias("west-park-road", "West Park")

    if "wellington-street" not in streets:
        streets["wellington-street"] = {
            "canonical_name": "Wellington Street",
            "slug": "wellington-street",
            "district": "",
            "parish": "",
            "former_names": [],
            "sub_sections": [],
            "numbering_scheme": {"type": "ODDS_EVENS", "approx_change_year": None},
            "cross_streets": [],
            "aliases": ["WELLINGTON Street"],
            "audit": {"status": "NAME_VERIFIED", "verified_by": "Rob Gale", "notes": ""},
            "coordinates": {"lat": None, "lng": None},
            "audit_status": "NAME_VERIFIED",
            "notes": "",
            "latitude": "",
            "longitude": ""
        }
        print("Created wellington-street in master_streets.json")
    else:
        add_alias("wellington-street", "WELLINGTON Street")

    add_alias("wednesbury-street", "Wednesday Street")
    add_alias("gibbs-road", "Walden")
    add_alias("hill-street", "Victoria Road Congregational Church")
    add_alias("trinity-place", "TRINITY PLACE (continued)")
    add_alias("st-mary-street", "Street List")
    add_alias("stow-park-circus", "Stow Pk. Circus")
    add_alias("high-street-pill", "St. Michael's Catholic Church and Schools")
    add_alias("gold-tops", "St. Mark's Church")
    add_alias("king-street", "St. Paul's Mission room")
    add_alias("st-julian-s-avenue", "St. Julian's Av")
    add_alias("st-edward-street", "St. Edward St.-continued")
    add_alias("spytty-lane", "Spitty Lane")
    add_alias("spencer-road", "South Street")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json saved.")

if __name__ == "__main__":
    run()
