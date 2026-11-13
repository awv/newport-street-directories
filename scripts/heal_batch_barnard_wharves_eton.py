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
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

        for idx, r in enumerate(reader):
            st = r.get("street", "").strip()
            yr = r.get("year", "").strip()
            no = r.get("house_number", "").strip()
            tr = r.get("trade", "").strip()

            # 1. Barnard Town -> Barrack Hill (1887, 1902, 1903) or Church Road (1915, 1924, 1927)
            if st == "Barnard Town":
                if yr in ["1887", "1902", "1903"]:
                    inc("Barnard Town -> Barrack Hill")
                    r["street"] = "Barrack Hill"
                else:
                    inc("Barnard Town -> Church Road")
                    r["street"] = "Church Road"

            # 2. Barnard Town Post Office (1924) -> Church Road doors 36-38
            elif st == "Barnard Town Post Office":
                inc("Barnard Town Post Office -> Church Road")
                r["street"] = "Church Road"
                r["building_name"] = ""
                fn = r.get("forename", "").strip()

                if "Howells" in tr:
                    r["house_number"] = "36"
                    r["surname"] = "Howells"
                    r["forename"] = "Jas."
                    r["trade"] = "Baker"
                elif "Evans" in tr:
                    r["house_number"] = "36a"
                    r["surname"] = "Evans"
                    r["forename"] = "Charles"
                    r["trade"] = "Butcher"
                elif "Odell" in tr:
                    r["house_number"] = "37"
                    r["surname"] = "Odell"
                    r["forename"] = "A. M."
                    r["trade"] = "Ironmonger"
                elif "Allen" in tr:
                    r["house_number"] = "38"
                    r["surname"] = "Allen"
                    r["forename"] = "Aug. Jas."
                    r["trade"] = "Crane Driver"

            # 3. Clarence Street-continued -> Clarence Street
            elif st == "Clarence Street-continued":
                inc("Clarence Street-continued -> Clarence Street")
                r["street"] = "Clarence Street"

            # 4. Clyfford Crescent & Clyffa Terrace -> Clyffard Crescent
            elif st in ["Clyfford Crescent", "Clyffa Terrace"]:
                inc(f"{st} -> Clyffard Crescent")
                r["street"] = "Clyffard Crescent"

            # 5. Commercial Wharf misassigned 1886 Dock Street block (rows 74109 to 74204)
            elif st == "Commercial Wharf" and yr == "1886" and 74109 <= idx <= 74204:
                inc("Commercial Wharf (1886 block) -> Dock Street")
                r["street"] = "Dock Street"

            # 6. Commerc'l Wharf & Commercial Wharf. E -> Commercial Wharf
            elif st in ["Commerc'l Wharf", "Commercial Wharf. E"]:
                inc(f"{st} -> Commercial Wharf")
                r["street"] = "Commercial Wharf"

            # 7. Rodney Wharf (1913 doors 1-39) -> Ross Street
            elif st == "Rodney Wharf":
                inc("Rodney Wharf -> Ross Street")
                r["street"] = "Ross Street"

            # 8. Wharves: 1890 West Street block (rows 94853 to 94861)
            elif st == "Wharves" and yr == "1890" and 94853 <= idx <= 94861:
                inc("Wharves (1890 block) -> West Street")
                r["street"] = "West Street"

            # 9. Wharves: 1915 Wharf Road block (rows 260295 to 260320)
            elif st == "Wharves" and yr == "1915" and 260295 <= idx <= 260320:
                inc("Wharves (1915 block) -> Wharf Road")
                r["street"] = "Wharf Road"

            # 10. EVESWELL SCHOOLS -> Chepstow Road
            elif st == "EVESWELL SCHOOLS":
                inc("EVESWELL SCHOOLS -> Chepstow Road")
                r["street"] = "Chepstow Road"

            # 11. ETON ROAD (continued) & Eto Street -> Eton Road
            elif st in ["ETON ROAD (continued)", "Eto Street"]:
                inc(f"{st} -> Eton Road")
                r["street"] = "Eton Road"

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

    add_alias("barrack-hill", "Barnard Town")
    add_alias("church-road", "Barnard Town Post Office")
    add_alias("clarence-street", "Clarence Street-continued")
    add_alias("clyffard-crescent", "Clyfford Crescent")
    add_alias("clyffard-crescent", "Clyffa Terrace")
    add_alias("commercial-wharf", "Commerc'l Wharf")
    add_alias("commercial-wharf", "Commercial Wharf. E")
    add_alias("ross-street", "Rodney Wharf")
    add_alias("chepstow-road", "EVESWELL SCHOOLS")
    add_alias("eton-road", "ETON ROAD (continued)")
    add_alias("eton-road", "Eto Street")

    # Clean up orphan entries if any exist
    orphans = [
        "barnard-town-post-office",
        "barnard-town",
        "clarence-street-continued",
        "clyfford-crescent",
        "clyffa-terrace",
        "commercial-wharf-e",
        "commerc-l-wharf",
        "rodney-wharf",
        "eveswell-schools",
        "eton-road-continued",
        "eto-street"
    ]
    for o in orphans:
        if o in streets:
            del streets[o]
            print(f"Removed orphan key '{o}' from master_streets.json")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json saved.")

if __name__ == "__main__":
    run()
