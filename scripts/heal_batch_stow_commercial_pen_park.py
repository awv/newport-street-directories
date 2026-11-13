import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

MAPPINGS = {
    "NEWPORT STREET DIRECTORY - COMMERCIAL STREET (continued)": "Commercial Street",
    "NEWPORT STREET DIRECTORY - Sto": "Stow Hill",
    "Newport Liberal Association": "Hill Street",
    "Pen (continued)": "Penllyn Avenue",
    "Park Street (North side of Park-square)": "Park Street",
    "PENTONVILLE (continued)": "Pentonville",
    "Philip Street": "Phillip Street",
    "Phillips Street": "Phillip Street",
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

    print("Rows updated:")
    for k, v in counts.items():
        print(f"  {k} -> {MAPPINGS[k]}: {v}")

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("data.csv updated.")

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
            print(f"WARNING: key '{key}' not found in master_streets!")

    add_alias("commercial-street", "NEWPORT STREET DIRECTORY - COMMERCIAL STREET (continued)")
    add_alias("stow-hill", "NEWPORT STREET DIRECTORY - Sto")
    add_alias("hill-street", "Newport Liberal Association")
    add_alias("penllyn-avenue", "Pen (continued)")
    add_alias("park-street", "Park Street (North side of Park-square)")
    add_alias("pentonville", "PENTONVILLE (continued)")
    add_alias("phillip-street", "Philip Street")
    add_alias("phillip-street", "Phillips Street")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json updated.")

if __name__ == "__main__":
    run()
