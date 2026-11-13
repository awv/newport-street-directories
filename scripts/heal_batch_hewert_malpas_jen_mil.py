import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

MAPPINGS = {
    "Hewertson-st": "Hewertson Street",
    "Hewert Street": "Hewertson Street",
    "Hollingdale W": "Clarence Place",
    "James Street continued": "James Street",
    "Jen": "Jenkins Street",
    "Macarthys's Court": "Macarthy's Court",
    "Llandaf Street": "Llandaff Street",
    "Llandafe Street": "Llandaff Street",
    "Lambert Street (continued)": "Lambert Street",
    "Kingsmill Ter": "Kingsmill Terrace",
    "Kensington Pl": "Kensington Place",
    "malpas Road": "Malpas Road",
    "Malpas Road continued": "Malpas Road",
    "Malpas Road Recreation Ground": "Malpas Road",
    "Mil": "Milner Street",
}

def run():
    print("Reading data.csv...")
    rows = []
    counts = {k: 0 for k in MAPPINGS}

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            st = r.get("street")
            if st in MAPPINGS:
                r["street"] = MAPPINGS[st]
                counts[st] += 1
            rows.append(r)

    print("Rows updated per street:")
    for k, v in counts.items():
        print(f"  {k} -> {MAPPINGS[k]}: {v}")

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

    add_alias("hewertson-street", "Hewertson-st")
    add_alias("hewertson-street", "Hewert Street")
    add_alias("clarence-place", "Hollingdale W")
    add_alias("james-street", "James Street continued")
    add_alias("jenkins-street", "Jen")
    add_alias("macarthy-s-court", "Macarthys's Court")
    add_alias("llandaff-street", "Llandaf Street")
    add_alias("llandaff-street", "Llandafe Street")
    add_alias("lambert-street", "Lambert Street (continued)")
    add_alias("kingsmill-terrace", "Kingsmill Ter")
    add_alias("kensington-place", "Kensington Pl")
    add_alias("milner-street", "Mil")

    if "malpas-road" in streets:
        streets["malpas-road"]["canonical_name"] = "Malpas Road"
        add_alias("malpas-road", "malpas Road")
        add_alias("malpas-road", "Malpas Road continued")
        add_alias("malpas-road", "Malpas Road Recreation Ground")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json saved.")

if __name__ == "__main__":
    run()
