import csv
import json

CSV_PATH = "data.csv"
MASTER_PATH = "master_streets.json"

TARGETS = [
    "Barnard Town Schools",
    "Barnard Town T.S.O. M.O. S.B. & A. & I. Office",
    "St. Matthew'S Church",
    "Temple of Health",
]

def run():
    print("Reading data.csv...")
    rows = []
    counts = {k: 0 for k in TARGETS}

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            st = r.get("street")
            if st in counts:
                r["street"] = "Church Road"
                counts[st] += 1
            rows.append(r)

    print("Subheaders merged into Church Road:")
    for k, v in counts.items():
        print(f"  {k} -> Church Road: {v}")

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("data.csv updated.")

    with open(MASTER_PATH, "r", encoding="utf-8") as f:
        master = json.load(f)
    streets = master.setdefault("streets", {})

    if "church-road" in streets:
        aliases = streets["church-road"].setdefault("aliases", [])
        for t in TARGETS:
            if t not in aliases:
                aliases.append(t)
                print(f"Added alias '{t}' to 'church-road'")

    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("master_streets.json updated.")

if __name__ == "__main__":
    run()
