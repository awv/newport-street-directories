import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

SIMPLE_MAPPINGS = {
    "SPRING STREET—continued": "Spring Street",
    "South Market Street. (e)": "South Market Street",
    "Southville Road. (c 6)": "Southville Road",
    "Somerton Road—continued": "Somerton Road",
}

def run():
    print("Reading data.csv...")
    rows = []
    counts = {k: 0 for k in SIMPLE_MAPPINGS}
    spencer_count = 0

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for idx, r in enumerate(reader):
            st = r.get("street")
            if st in SIMPLE_MAPPINGS:
                r["street"] = SIMPLE_MAPPINGS[st]
                counts[st] += 1
            # Row 169662 to 169714 in 1900: Spencer Road residents mislabeled as S. Market Street
            elif r.get("year") == "1900" and 169662 <= idx <= 169714 and st == "South Market Street":
                r["street"] = "Spencer Road"
                spencer_count += 1
            rows.append(r)

    print("Simple mappings applied:")
    for k, v in counts.items():
        print(f"  {k} -> {SIMPLE_MAPPINGS[k]}: {v}")
    print(f"Restored 1900 Spencer Road records: {spencer_count}")

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

    add_alias("spring-street", "SPRING STREET—continued")
    add_alias("south-market-street", "South Market Street. (e)")
    add_alias("southville-road", "Southville Road. (c 6)")
    add_alias("somerton-road", "Somerton Road—continued")
    add_alias("spencer-road", "S. Market Street")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json updated.")

if __name__ == "__main__":
    run()
