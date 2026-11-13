import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

def run():
    print("Reading data.csv...")
    rows = []
    counts = {}

    def inc(key):
        counts[key] = counts.get(key, 0) + 1

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            st = r.get("street", "").strip()
            yr = r.get("year", "").strip()
            no = r.get("house_number", "").strip()

            # 1. Chepstow road - West End Buildings -> Chepstow Road
            if st == "Chepstow road - West End Buildings":
                inc("Chepstow road - West End Buildings")
                r["street"] = "Chepstow Road"
                if not r.get("building_name"):
                    r["building_name"] = "West End Buildings"

            # 2. Cambria Cottages (15) -> Cambria Place
            elif st == "Cambria Cottages (15)":
                inc("Cambria Cottages (15)")
                r["street"] = "Cambria Place"

            # 3. Constables' Lane / Constables' Lane. E -> Constable's Lane
            elif st in ["Constables' Lane", "Constables' Lane. E"]:
                inc(st)
                r["street"] = "Constable's Lane"

            # 4. Crindau ho / Crindau / Crindau Cottages -> Crindau Road
            elif st == "Crindau ho":
                inc("Crindau ho")
                r["street"] = "Crindau Road"
                if r.get("surname") == "Hutchins" and r.get("forename") == "John":
                    r["building_name"] = "Crindau House"
            elif st == "Crindau":
                inc("Crindau")
                r["street"] = "Crindau Road"
            elif st == "Crindau Cottages":
                inc("Crindau Cottages")
                r["street"] = "Crindau Road"
                if not r.get("building_name"):
                    r["building_name"] = "Crindau Cottages"

            # 5. DOCK STREET (continued) -> Dock Street
            elif st == "DOCK STREET (continued)":
                inc("DOCK STREET (continued)")
                r["street"] = "Dock Street"

            # 6. Alexandra Dock -> Alexandra Docks
            elif st == "Alexandra Dock":
                inc("Alexandra Dock")
                r["street"] = "Alexandra Docks"

            # 7. Docks (1878: Dock Street doors 44-122; other years: Town Dock)
            elif st == "Docks":
                if yr == "1878":
                    inc("Docks (1878 -> Dock Street)")
                    r["street"] = "Dock Street"
                else:
                    inc("Docks (other -> Town Dock)")
                    r["street"] = "Town Dock"
                    if no in ["(The.)", "(The)", "The", "The."]:
                        r["house_number"] = ""

            # 8. All other Town/Old Dock listings -> Town Dock
            elif st in [
                "Dock (The Old)",
                "Dock (The Town)",
                "Dock (Town)",
                "Dock (the Town)",
                "Docks (The)",
                "Docks. (The)",
                "Docks (s)"
            ]:
                inc(st)
                r["street"] = "Town Dock"
                if no in ["(The.)", "(The)", "The", "The."]:
                    r["house_number"] = ""

            rows.append(r)

    print("Replacements made in data.csv:")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")

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

    add_alias("chepstow-road", "Chepstow road - West End Buildings")
    add_alias("cambria-place", "Cambria Cottages (15)")
    add_alias("constables-lane", "Constables' Lane")
    add_alias("constables-lane", "Constables' Lane. E")
    add_alias("crindau-road", "Crindau ho")
    add_alias("crindau-road", "Crindau")
    add_alias("crindau-road", "Crindau Cottages")
    add_alias("dock-street", "DOCK STREET (continued)")
    add_alias("alexandra-docks", "Alexandra Dock")

    # Ensure town-dock exists
    if "town-dock" not in streets:
        streets["town-dock"] = {
            "canonical_name": "Town Dock",
            "slug": "town-dock",
            "district": "Pillgwenlly",
            "parish": "St. Woolos",
            "former_names": ["The Old Dock", "The Docks"],
            "sub_sections": [],
            "numbering_scheme": {"type": "UNNUMBERED"},
            "cross_streets": ["Dock Street", "Commercial Road", "Alexander Dock"],
            "aliases": [
                "Dock (The Old)",
                "Dock (The Town)",
                "Dock (Town)",
                "Dock (the Town)",
                "Docks",
                "Docks (The)",
                "Docks. (The)",
                "Docks (s)"
            ],
            "audit": {"status": "NAME_VERIFIED", "verified_by": "Rob Gale", "notes": "Historical Newport Town Dock (1842-1930)."},
            "coordinates": {"lat": 51.5815, "lng": -2.9875},
            "audit_status": "NAME_VERIFIED",
            "notes": "Historical Newport Town Dock, opened in 1842 as Newport's first floating dock, later called The Old Dock following the opening of Alexandra Dock in 1875. Infilled in 1930.",
            "latitude": "51.5815",
            "longitude": "-2.9875"
        }
        print("Created town-dock in master_streets.json")
    else:
        for a in [
            "Dock (The Old)",
            "Dock (The Town)",
            "Dock (Town)",
            "Dock (the Town)",
            "Docks",
            "Docks (The)",
            "Docks. (The)",
            "Docks (s)"
        ]:
            add_alias("town-dock", a)

    # Remove obsolete unverified/orphan dock keys
    for old_key in ["docks", "docks-the"]:
        if old_key in streets:
            del streets[old_key]
            print(f"Removed deprecated key '{old_key}' from master_streets.json")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json saved.")

if __name__ == "__main__":
    run()
