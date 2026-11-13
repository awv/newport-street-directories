import csv
import json
import os

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

print("Starting healing script for Panteg, Lower Orchard Street, Pemrose/Penrose Cottages, Pembroke Terrace, Pillgwenlly Foundry, and Pillgwenlly...")

# Read data.csv
with open("data.csv", "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))
    fieldnames = reader[0].keys() if reader else []

new_rows = []
inserted_portland_1894 = False

for r in reader:
    st = r.get("street", "").strip()
    yr = r.get("year", "").strip()
    
    # 1. Panteg -> Chepstow Road
    if st == "Panteg":
        r["street"] = "Chepstow Road"
        trade = r.get("trade", "").strip()
        # Fix villas in trade field
        if trade.lower() in ["llan wallis", "bath villa", "stafford villa"]:
            r["building_name"] = trade.title()
            r["trade"] = ""
        new_rows.append(r)
        continue

    # 2. Orchard (Lower) Street -> Lower Orchard Street
    if st == "Orchard (Lower) Street":
        r["street"] = "Lower Orchard Street"
        new_rows.append(r)
        continue

    # 3 & 5. Pemrose Cottages / Penrose Cottages -> Arthur Street
    if st in ["Pemrose Cottages", "Penrose Cottages"]:
        r["street"] = "Arthur Street"
        r["building_name"] = "Penrose Cottages"
        new_rows.append(r)
        continue

    # 4. Pembroke Terrace -> Crescent Road
    if st == "Pembroke Terrace":
        r["street"] = "Crescent Road"
        existing_bldg = r.get("building_name", "").strip()
        if existing_bldg:
            r["building_name"] = f"Pembroke Terrace, {existing_bldg}"
        else:
            r["building_name"] = "Pembroke Terrace"
        new_rows.append(r)
        continue

    # 6. Pillgwenlly Foundry (1910) -> Potter Street
    if st == "Pillgwenlly Foundry":
        r["street"] = "Potter Street"
        bldg = r.get("building_name", "").strip()
        fn = r.get("forename", "").strip()
        sn = r.get("surname", "").strip()
        tr = r.get("trade", "").strip()

        if bldg == "Jordan's Ltd.":
            r["building_name"] = "Jordan's Ltd., Pillgwenlly Foundry"
        elif fn == "HOLY TRINITY CHURCH":
            r["building_name"] = "Holy Trinity Church"
            r["forename"] = ""
            r["surname"] = ""
            r["trade"] = ""
        elif fn == "Void":
            r["forename"] = ""
            r["surname"] = ""
            r["trade"] = "Void"
        elif sn == "Trinity h":
            r["building_name"] = "Trinity House"
            r["trade"] = ""
            fn_parts = fn.split(" ", 1)
            r["surname"] = fn_parts[0]
            r["forename"] = fn_parts[1] if len(fn_parts) > 1 else ""
        elif sn.lower() in ["milkman", "labourer", "trimmr", "trimmer", "engine driver", "labr", "pilotsman"]:
            trade_norm = {
                "milkman": "Milkman",
                "labourer": "Labourer",
                "trimmr": "Trimmer",
                "trimmer": "Trimmer",
                "engine driver": "Engine Driver",
                "labr": "Labourer",
                "pilotsman": "Pilotsman"
            }.get(sn.lower(), sn.title())
            r["trade"] = trade_norm
            fn_parts = fn.split(" ", 1)
            r["surname"] = fn_parts[0]
            r["forename"] = fn_parts[1] if len(fn_parts) > 1 else ""
        elif fn == "Plummer T.":
            r["surname"] = "Plummer"
            r["forename"] = "T."
            r["trade"] = "Excelsior Wagon & Carriage Works"
        elif fn == "Burke Mrs. Catherine":
            r["surname"] = "Burke"
            r["forename"] = "Mrs. Catherine"
        elif fn == "Roach Lawrence":
            r["surname"] = "Roach"
            r["forename"] = "Lawrence"
        elif fn == "Mahoney Mrs. Mary Ann":
            r["surname"] = "Mahoney"
            r["forename"] = "Mrs. Mary Ann"
        elif fn == "Card Henry":
            r["surname"] = "Card"
            r["forename"] = "Henry"
        new_rows.append(r)
        continue

    # 7. Pillgwenlly (1894) -> Portland Street
    if st == "Pillgwenlly":
        if not inserted_portland_1894:
            # Insert doors 1 to 14 of Portland Street from raw_tsvs/1894.tsv
            missing_1894_doors = [
                {"year": "1894", "street": "Portland Street", "house_number": "", "building_name": "Kerslake's Steam Flour Mill", "surname": "", "forename": "", "trade": "", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "1", "building_name": "", "surname": "Giblin", "forename": "Jas.", "trade": "Labourer", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "2", "building_name": "", "surname": "Evans", "forename": "Chas.", "trade": "Foreman", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "3", "building_name": "Stores", "surname": "", "forename": "", "trade": "", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "", "building_name": "Meth. Free Church", "surname": "", "forename": "", "trade": "", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "4", "building_name": "", "surname": "Miller", "forename": "James", "trade": "Carpenter", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "5", "building_name": "", "surname": "Maher", "forename": "Patrick", "trade": "Hobbler", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "6", "building_name": "", "surname": "Huish", "forename": "Hy.", "trade": "Labourer", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "7", "building_name": "", "surname": "Davies", "forename": "Ann", "trade": "Shopkeeper", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "8", "building_name": "", "surname": "Robinson", "forename": "John", "trade": "", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "9", "building_name": "", "surname": "Barnard", "forename": "Rachel", "trade": "Widow", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "10", "building_name": "", "surname": "Lovett", "forename": "Geo.", "trade": "Seaman", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "11", "building_name": "", "surname": "Hedge", "forename": "Harry", "trade": "Confectioner", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "12", "building_name": "", "surname": "Hignell", "forename": "Miss", "trade": "Sextoness", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "13", "building_name": "", "surname": "Bernier", "forename": "Alfred", "trade": "Shopkeeper", "source_type": ""},
                {"year": "1894", "street": "Portland Street", "house_number": "14", "building_name": "Church Ho.", "surname": "Milton", "forename": "Benj.", "trade": "", "source_type": ""},
            ]
            new_rows.extend(missing_1894_doors)
            inserted_portland_1894 = True
            print(f"Inserted {len(missing_1894_doors)} missing Portland Street (doors 1-14) rows from 1894.tsv")

        r["street"] = "Portland Street"
        if r.get("trade"):
            r["trade"] = r["trade"].strip().title()
        new_rows.append(r)
        continue

    new_rows.append(r)

print(f"Original data.csv rows: {len(reader)}, New data.csv rows: {len(new_rows)}")

# Write updated data.csv
with open("data.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(new_rows)
print("Updated data.csv successfully.")

# Update master_streets.json
with open("master_streets.json", "r", encoding="utf-8") as f:
    ms = json.load(f)

streets = ms.get("streets", {})

# 1. Chepstow Road alias Panteg
if "chepstow-road" in streets:
    if "Panteg" not in streets["chepstow-road"].get("aliases", []):
        streets["chepstow-road"].setdefault("aliases", []).append("Panteg")

# 2. Crescent Road alias and sub_section Pembroke Terrace
if "crescent-road" in streets:
    if "Pembroke Terrace" not in streets["crescent-road"].get("aliases", []):
        streets["crescent-road"].setdefault("aliases", []).append("Pembroke Terrace")
    if "Pembroke Terrace" not in streets["crescent-road"].get("sub_sections", []):
        streets["crescent-road"].setdefault("sub_sections", []).append("Pembroke Terrace")

# 3. Potter Street alias Pillgwenlly Foundry
if "potter-street" in streets:
    if "Pillgwenlly Foundry" not in streets["potter-street"].get("aliases", []):
        streets["potter-street"].setdefault("aliases", []).append("Pillgwenlly Foundry")

# 4. Portland Street alias Pillgwenlly
if "portland-street" in streets:
    if "Pillgwenlly" not in streets["portland-street"].get("aliases", []):
        streets["portland-street"].setdefault("aliases", []).append("Pillgwenlly")

# 5. Arthur Street alias and sub_section Penrose Cottages
if "arthur-street" in streets:
    for a in ["Pemrose Cottages", "Penrose Cottages"]:
        if a not in streets["arthur-street"].get("aliases", []):
            streets["arthur-street"].setdefault("aliases", []).append(a)
    if "Penrose Cottages" not in streets["arthur-street"].get("sub_sections", []):
        streets["arthur-street"].setdefault("sub_sections", []).append("Penrose Cottages")

# 6. Lower Orchard Street entry
if "lower-orchard-street" not in streets:
    streets["lower-orchard-street"] = {
        "canonical_name": "Lower Orchard Street",
        "slug": "lower-orchard-street",
        "district": "",
        "parish": "",
        "former_names": [],
        "sub_sections": [],
        "numbering_scheme": {
            "type": "ODDS_EVENS",
            "approx_change_year": None
        },
        "cross_streets": [],
        "aliases": ["Orchard (Lower) Street"],
        "audit": {
            "status": "NAME_VERIFIED",
            "verified_by": "Rob Gale",
            "notes": "Renamed from Orchard (Lower) Street"
        },
        "coordinates": {"lat": None, "lng": None},
        "audit_status": "NAME_VERIFIED",
        "notes": "",
        "latitude": "",
        "longitude": ""
    }
else:
    if "Orchard (Lower) Street" not in streets["lower-orchard-street"].get("aliases", []):
        streets["lower-orchard-street"].setdefault("aliases", []).append("Orchard (Lower) Street")

# Remove stale slugs
stale_slugs = ["pembroke-terrace", "pillgwenlly", "pemrose-cottages", "panteg", "penrose-cottages", "pillgwenlly-foundry"]
for s in stale_slugs:
    if s in streets:
        del streets[s]
        print(f"Removed stale slug: {s}")

with open("master_streets.json", "w", encoding="utf-8") as f:
    json.dump(ms, f, indent=2, ensure_ascii=False)
print("Updated master_streets.json successfully.")
