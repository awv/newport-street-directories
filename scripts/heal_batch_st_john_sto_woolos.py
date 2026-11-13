import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

SIMPLE_MAPPINGS = {
    "ST. JOHN'S ROAD (continued)": "St. John's Road",
    "St. John's-rd": "St. John's Road",
    "ST. STEPHENS ROAD (contd.)": "St. Stephen's Road",
    "St. Woolos Pl": "St. Woolos Place",
    "Summerhill Aven": "Summerhill Avenue",
}

def run():
    print("Reading data.csv...")
    rows = []
    counts = {k: 0 for k in SIMPLE_MAPPINGS}
    sto_crescent_count = 0
    sto_summerhill_count = 0

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for idx, r in enumerate(reader):
            st = r.get("street")
            if st in SIMPLE_MAPPINGS:
                r["street"] = SIMPLE_MAPPINGS[st]
                counts[st] += 1
            elif st == "Sto":
                if idx <= 366050:
                    r["street"] = "Stow Park Crescent"
                    sto_crescent_count += 1
                else:
                    r["street"] = "Summerhill Avenue"
                    sto_summerhill_count += 1
            rows.append(r)

    print("Simple mappings applied:")
    for k, v in counts.items():
        print(f"  {k} -> {SIMPLE_MAPPINGS[k]}: {v}")
    print(f"Sto -> Stow Park Crescent: {sto_crescent_count}")
    print(f"Sto -> Summerhill Avenue: {sto_summerhill_count}")

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

    add_alias("st-john-s-road", "ST. JOHN'S ROAD (continued)")
    add_alias("st-john-s-road", "St. John's-rd")
    add_alias("st-stephen-s-road", "ST. STEPHENS ROAD (contd.)")
    add_alias("st-woolos-place", "St. Woolos Pl")
    add_alias("summerhill-avenue", "Summerhill Aven")
    add_alias("summerhill-avenue", "Sto")
    add_alias("stow-park-crescent", "Sto")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json saved.")

if __name__ == "__main__":
    run()
