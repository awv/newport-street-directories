import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

TERRACE_MAP = {
    "Duckpool Road M. - Auckland Terrace": "Auckland Terrace",
    "Duckpool Road M. - Duckpool Terrace": "Duckpool Terrace",
    "Duckpool Road M. - Easton Place": "Easton Place",
    "Duckpool Road M. - Hampton Place": "Hampton Place",
    "Duckpool Road M. - Melton Terrace": "Melton Terrace",
    "Duckpool Road M. - Richmond Terrace": "Richmond Terrace",
    "Duckpool Road M. - Seamoor Terrace": "Seamoor Terrace",
    "Duckpool Road M. - Vine Place": "Vine Place",
    "Duckpool Terrace": "Duckpool Terrace",
    "DUCKPOOL TERRACE": "Duckpool Terrace"
}

OTHER_VARIANTS = [
    "Duckpool Road—continued",
    "DUCKPOOL ROAD",
    "Duckpool-road"
]

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

            if st in TERRACE_MAP:
                inc(st)
                r["street"] = "Duckpool Road"
                if not r.get("building_name"):
                    r["building_name"] = TERRACE_MAP[st]

            elif st in OTHER_VARIANTS:
                inc(st)
                r["street"] = "Duckpool Road"

            rows.append(r)

    print("Replacements made in data.csv:")
    for k, v in sorted(counts.items()):
        print(f"  {k} -> Duckpool Road: {v}")

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

    all_aliases = list(TERRACE_MAP.keys()) + OTHER_VARIANTS
    for a in all_aliases:
        add_alias("duckpool-road", a)

    # Remove obsolete standalone duckpool-terrace key
    if "duckpool-terrace" in streets:
        del streets["duckpool-terrace"]
        print("Removed deprecated key 'duckpool-terrace' from master_streets.json")

    # Clean up any potential orphan sub-terrace keys
    for a in all_aliases:
        slug = a.lower().replace(" ", "-").replace(".", "").replace("—", "-")
        if slug in streets and slug != "duckpool-road":
            del streets[slug]
            print(f"Removed orphan key '{slug}' from master_streets.json")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json saved.")

if __name__ == "__main__":
    run()
