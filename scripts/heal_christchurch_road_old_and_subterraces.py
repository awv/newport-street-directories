import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

def run():
    print("Reading data.csv...")
    rows = []
    counts = {
        "Christchurch Rd. Old": 0,
        "Christchurch Road - Auckland Villas": 0,
        "Christchurch Road - Temperance Cottages": 0,
        "Christchurch Road Post Office": 0,
        "1890_old_fixes": 0
    }

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            st = r.get("street", "").strip()
            yr = r.get("year", "").strip()
            no = r.get("house_number", "").strip()

            # 1. Christchurch Rd. Old -> Christchurch Road
            if st == "Christchurch Rd. Old":
                counts["Christchurch Rd. Old"] += 1
                r["street"] = "Christchurch Road"

            # 2. Auckland Villas
            elif st == "Christchurch Road - Auckland Villas":
                counts["Christchurch Road - Auckland Villas"] += 1
                r["street"] = "Christchurch Road"
                if not r.get("building_name"):
                    r["building_name"] = "Auckland Villas"

            # 3. Temperance Cottages
            elif st == "Christchurch Road - Temperance Cottages":
                counts["Christchurch Road - Temperance Cottages"] += 1
                r["street"] = "Christchurch Road"
                if not r.get("building_name"):
                    r["building_name"] = "Temperance Cottages"

            # 4. Christchurch Road Post Office
            elif st == "Christchurch Road Post Office":
                counts["Christchurch Road Post Office"] += 1
                r["street"] = "Christchurch Road"
                r["house_number"] = ""

                sn = r.get("surname", "").strip()
                fn = r.get("forename", "").strip()
                tr = r.get("trade", "").strip()

                if sn == "Chas." and fn == "Mount view" and tr == "Tandy":
                    r["building_name"] = "Mount View"
                    r["surname"] = "Tandy"
                    r["forename"] = "Chas."
                    r["trade"] = ""
                elif sn == "Davies" and "Jessiman" in fn:
                    r["building_name"] = "Jessiman Villa"
                    r["surname"] = "Davies"
                    r["forename"] = "Mrs. H."
                    r["trade"] = ""
                elif sn == "Charles" and fn == "Malvern villa" and tr == "Grice":
                    r["building_name"] = "Malvern Villa"
                    r["surname"] = "Grice"
                    r["forename"] = "Charles"
                    r["trade"] = ""
                elif sn == "George" and fn == "Ashley house" and tr == "Evans":
                    r["building_name"] = "Ashley House"
                    r["surname"] = "Evans"
                    r["forename"] = "George"
                    r["trade"] = ""
                elif sn == "F." and fn == "Vandyke" and "Watkins" in tr:
                    r["building_name"] = "Vandyke"
                    r["surname"] = "Watkins"
                    r["forename"] = "F."
                    r["trade"] = "Carpenter"
                elif "Clarke" in tr and "The Bryn" in fn:
                    r["building_name"] = "The Bryn"
                    r["surname"] = "Clarke"
                    r["forename"] = "F. E. S."
                    r["trade"] = ""
                elif "Flannigan" in tr and "Jesmond" in fn:
                    r["building_name"] = "Jesmond Dene"
                    r["surname"] = "Flannigan"
                    r["forename"] = "F. P."
                    r["trade"] = ""
                elif sn == "Frank" and fn == "Oakhurst" and tr == "Eady":
                    r["building_name"] = "Oakhurst"
                    r["surname"] = "Eady"
                    r["forename"] = "Frank"
                    r["trade"] = ""
                elif sn == "Williams" and fn == "S.":
                    r["building_name"] = ""
                    r["surname"] = "Williams"
                    r["forename"] = "S."
                    r["trade"] = "Dairyman"
                elif fn == "Cherry Orchard":
                    r["building_name"] = "Cherry Orchard"
                    r["surname"] = ""
                    r["forename"] = ""
                    r["trade"] = ""

            # 5. Fix 1890 Christchurch Road bleeding 'Old.' in house_number
            elif st == "Christchurch Road" and yr == "1890" and no in ["Old.", "Old"]:
                counts["1890_old_fixes"] += 1
                bldg = r.get("building_name", "").strip()
                sn = r.get("surname", "").strip()
                fn = r.get("forename", "").strip()
                tr = r.get("trade", "").strip()

                r["house_number"] = ""
                r["building_name"] = ""

                if bldg == "6" and "Williams" in tr:
                    r["house_number"] = "6"
                    r["surname"] = "Williams"
                    r["forename"] = "A. G."
                    r["trade"] = "Chemist"
                elif "Loveridge" in tr:
                    r["house_number"] = "6"
                    r["surname"] = "Loveridge"
                    r["forename"] = "A. W."
                    r["trade"] = "Surgeon, daily from 4 to 5"
                elif bldg == "7 & 8" and "Stock" in tr:
                    r["house_number"] = "7 & 8"
                    r["surname"] = "Stock"
                    r["forename"] = "M. J."
                    r["trade"] = "Pork Butcher"
                elif bldg == "9" and "Fifoot, M." in tr:
                    r["house_number"] = "9"
                    r["surname"] = "Fifoot"
                    r["forename"] = "M."
                    r["trade"] = "Glass & China Dealer"
                elif "Fifoot & Son" in tr:
                    r["house_number"] = "9"
                    r["surname"] = "Fifoot & Son"
                    r["forename"] = ""
                    r["trade"] = "Undertakers"
                elif bldg == "10" and "Bate" in tr:
                    r["house_number"] = "10"
                    r["surname"] = "Bate"
                    r["forename"] = "Wm."
                    r["trade"] = "Builder, etc."
                elif bldg == "11" and "Harman" in tr:
                    r["house_number"] = "11"
                    r["surname"] = "Harman"
                    r["forename"] = "A."
                    r["trade"] = "Draper"
                elif bldg == "12 & 13":
                    r["house_number"] = "12 & 13"
                    r["surname"] = ""
                    r["forename"] = ""
                    r["trade"] = "Building"
                elif sn == "Lewis" and fn == "John B.":
                    r["surname"] = "Lewis"
                    r["forename"] = "John B."
                    r["trade"] = "Tobacconist"
                elif sn == "Truscott" and fn == "J. C.":
                    r["surname"] = "Truscott"
                    r["forename"] = "J. C."
                    r["trade"] = "Watchmaker"
                elif sn == "Palmer" and fn == "Miss":
                    r["surname"] = "Palmer"
                    r["forename"] = "Miss"
                    r["trade"] = ""
                elif sn == "Burgess" and fn == "Saml. E.":
                    r["surname"] = "Burgess"
                    r["forename"] = "Saml. E."
                    r["trade"] = "Grocer"
                elif "Gronow" in sn:
                    r["building_name"] = "Gronow's coal yard"
                    r["surname"] = ""
                    r["forename"] = ""
                    r["trade"] = ""
                elif sn == "Wall" and fn == "Henry":
                    r["surname"] = "Wall"
                    r["forename"] = "Henry"
                    r["trade"] = "Sculptor"
                elif "Moorfield Corn stores" in tr:
                    r["building_name"] = "Moorfield Corn stores"
                    r["surname"] = ""
                    r["forename"] = ""
                    r["trade"] = ""
                elif fn == "1 Oak vil" and tr == "Morgan":
                    r["building_name"] = "1 Oak villa"
                    r["surname"] = "Morgan"
                    r["forename"] = "Stephen"
                    r["trade"] = ""
                elif sn == "Lewis" and fn == "J. Nicholl":
                    r["surname"] = "Lewis"
                    r["forename"] = "J. Nicholl"
                    r["trade"] = "Physician And Surgeon"
                elif fn == "2 Oak v" and "Chapman" in tr:
                    r["building_name"] = "2 Oak villa"
                    r["surname"] = "Chapman"
                    r["forename"] = "U."
                    r["trade"] = "Builder"
                elif fn == "Austin villa" and tr == "Palmer":
                    r["building_name"] = "Austin villa"
                    r["surname"] = "Palmer"
                    r["forename"] = "James"
                    r["trade"] = ""
                elif fn == "Ormonde ho" and tr == "Little":
                    r["building_name"] = "Ormonde house"
                    r["surname"] = "Little"
                    r["forename"] = "Thos. M."
                    r["trade"] = ""
                elif "Oldham James" in tr:
                    r["surname"] = "Oldham"
                    r["forename"] = "James"
                    r["trade"] = ""
                elif fn == "Boundary ho" and tr == "Hopkins":
                    r["building_name"] = "Boundary house"
                    r["surname"] = "Hopkins"
                    r["forename"] = "G. H."
                    r["trade"] = ""
                elif "Vacant sites" in tr:
                    r["surname"] = "Vacant sites"
                    r["forename"] = ""
                    r["trade"] = ""
                elif fn == "Cosham vil" and tr == "Rochard":
                    r["building_name"] = "Cosham villa"
                    r["surname"] = "Rochard"
                    r["forename"] = "Peter"
                    r["trade"] = ""
                elif fn == "Brecknock vil" and tr == "Teale":
                    r["building_name"] = "Brecknock villa"
                    r["surname"] = "Teale"
                    r["forename"] = "Ernest"
                    r["trade"] = ""
                elif sn == "Walker" and fn == "Rev. F. A.":
                    r["building_name"] = "Llan Lian"
                    r["surname"] = "Walker"
                    r["forename"] = "Rev. F. A."
                    r["trade"] = ""

            rows.append(r)

    print("Replacements made in data.csv:")
    for k, v in counts.items():
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

    add_alias("christchurch-road", "Christchurch Rd. Old")
    add_alias("christchurch-road", "Christchurch Road - Auckland Villas")
    add_alias("christchurch-road", "Christchurch Road - Temperance Cottages")
    add_alias("christchurch-road", "Christchurch Road Post Office")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json saved.")

if __name__ == "__main__":
    run()
