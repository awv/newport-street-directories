#!/usr/bin/env python3
import csv
import subprocess

DATA_CSV = "/Users/robgale/Documents/Newport Street Directory Project/data.csv"

MAP = {
    'Chu': 'Church Street',
    'Ken': 'Kensington Place',
    'Mal': 'Malpas Road',
    'Mor': 'Morris Street',
    'Car': 'Carisbrooke Road',
    'Fai': 'Fairoak Terrace',
}

def main():
    records = []
    fixed = 0
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            st = r['street'].strip()
            if st in MAP:
                r['street'] = MAP[st]
                fixed += 1
            records.append(r)

    print(f"Fixed final {fixed} records across {list(MAP.keys())}!")
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print("Rebuilding site data and statistics...")
    subprocess.run(["python3", "scripts/build_site_data.py"], check=True)
    subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)
    print("Done!")

if __name__ == "__main__":
    main()
