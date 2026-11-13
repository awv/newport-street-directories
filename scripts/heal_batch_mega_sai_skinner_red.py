import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

SIMPLE_MAPPINGS = {
    "NEWPORT STREET DIRECTORY - COMMERCIAL STREET (continued)": "Commercial Street",
    "NEWPORT STREET DIRECTORY - Sto": "Stow Hill",
    "Newport Liberal Association": "Hill Street",
    "Pen (continued)": "Penllyn Avenue",
    "Park Street (North side of Park-square)": "Park Street",
    "PENTONVILLE (continued)": "Pentonville",
    "Philip Street": "Phillip Street",
    "Phillips Street": "Phillip Street",
    "Red Street": "Redland Street",
    "Princes Street": "Prince Street",
    "RIVER BANKS (continued)": "River Banks",
    "Risca Road (continued)": "Risca Road",
    "S. Market Street": "South Market Street",
    "Skinner Street—continued": "Skinner Street",
}

def run():
    print("Reading data.csv...")
    rows = []
    counts = {k: 0 for k in SIMPLE_MAPPINGS}
    sai_counts = {"St. Mary Street": 0, "St. Michael Street": 0, "St. Vincent's Road": 0}

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for idx, r in enumerate(reader):
            st = r.get("street")
            if st in SIMPLE_MAPPINGS:
                r["street"] = SIMPLE_MAPPINGS[st]
                counts[st] += 1
            elif st == "Sai":
                if 365050 <= idx <= 365079:
                    r["street"] = "St. Mary Street"
                    sai_counts["St. Mary Street"] += 1
                elif 365096 <= idx <= 365118:
                    r["street"] = "St. Michael Street"
                    sai_counts["St. Michael Street"] += 1
                elif 365141 <= idx <= 365171:
                    r["street"] = "St. Vincent's Road"
                    sai_counts["St. Vincent's Road"] += 1
                else:
                    print(f"WARNING: Unexpected Sai row at {idx}: {r}")
            rows.append(r)

    print("Simple mappings applied:")
    for k, v in counts.items():
        print(f"  {k} -> {SIMPLE_MAPPINGS[k]}: {v}")
    print("Sai sections healed:")
    for k, v in sai_counts.items():
        print(f"  Sai -> {k}: {v}")

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("data.csv updated successfully.")

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

    add_alias("commercial-street", "NEWPORT STREET DIRECTORY - COMMERCIAL STREET (continued)")
    add_alias("stow-hill", "NEWPORT STREET DIRECTORY - Sto")
    add_alias("hill-street", "Newport Liberal Association")
    add_alias("penllyn-avenue", "Pen (continued)")
    add_alias("park-street", "Park Street (North side of Park-square)")
    add_alias("pentonville", "PENTONVILLE (continued)")
    add_alias("phillip-street", "Philip Street")
    add_alias("phillip-street", "Phillips Street")
    add_alias("redland-street", "Red Street")
    add_alias("prince-street", "Princes Street")
    add_alias("river-banks", "RIVER BANKS (continued)")
    add_alias("risca-road", "Risca Road (continued)")
    add_alias("south-market-street", "S. Market Street")
    add_alias("skinner-street", "Skinner Street—continued")
    add_alias("st-mary-street", "Sai")
    add_alias("st-michael-street", "Sai")
    add_alias("st-vincent-s-road", "Sai")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json updated successfully.")

if __name__ == "__main__":
    run()
