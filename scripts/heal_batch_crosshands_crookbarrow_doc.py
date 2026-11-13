import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

MAPPINGS = {
    "Cross Hands Post Office": "Chepstow Road",
    "Dan Street": "Daniel Street",
    "Devonshire place": "Devon Place",
    "Dewsdland Park Road": "Dewsland Park Road",
    "Dewston Street": "Dewstow Street",
    "Doc": "Dewstow Street",
    "Crookbarrow Road": "Cromwell Road",
    "Courtybella. Ter": "Courtybella Terrace",
    "Corporation road—continued": "Corporation Road",
    "Corelli Street continued": "Corelli Street",
    "Court": "Charles Street",
    "Commercial-rd": "Commercial Road",
}

def run():
    print("Reading data.csv...")
    rows = []
    counts = {k: 0 for k in MAPPINGS}
    doc_swaps = 0

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            st = r.get("street", "").strip()
            if st == "Doc":
                # Swap inverted surname/forename if not Void
                if r.get("surname") != "Void":
                    r["surname"], r["forename"] = r.get("forename", ""), r.get("surname", "")
                    doc_swaps += 1

            if st in MAPPINGS:
                counts[st] += 1
                r["street"] = MAPPINGS[st]

            rows.append(r)

    print(f"Doc name swaps: {doc_swaps}")
    print("Replacements made in data.csv:")
    for k, v in counts.items():
        print(f"  {k} -> {MAPPINGS[k]}: {v}")

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

    add_alias("chepstow-road", "Cross Hands Post Office")
    add_alias("daniel-street", "Dan Street")
    add_alias("devon-place", "Devonshire place")
    add_alias("dewsland-park-road", "Dewsdland Park Road")
    add_alias("dewstow-street", "Dewston Street")
    add_alias("dewstow-street", "Doc")
    add_alias("cromwell-road", "Crookbarrow Road")
    add_alias("courtybella-terrace", "Courtybella. Ter")
    add_alias("corporation-road", "Corporation road—continued")
    add_alias("corelli-street", "Corelli Street continued")
    add_alias("charles-street", "Court")
    add_alias("commercial-road", "Commercial-rd")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json saved.")

if __name__ == "__main__":
    run()
