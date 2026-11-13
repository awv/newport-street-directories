#!/usr/bin/env python3
"""
heal_batch_trades_november.py
=============================
Normalizes trade abbreviations and heals associated anomalies:
1. Brick Mkr -> Brick Maker
2. M'ldr, Mldr, Mouldr -> Moulder (plus Brass Moulder, Iron Moulder, Pipe Moulder)
3. Alshpr, Coalshpr, Coal Shpr, Al Shpr -> Coal Shipper
4. Pattrn Mkr, Pattrn Mk, Pattn Mkr -> Pattern Maker (and heals swapped name at 1882 James St 4)
5. Phoenix F'dry -> Phoenix Foundry (heals building_name and trade)
6. Al Tr'inr, Coal Tr'Inr -> Coal Trimmer
7. Al Trimmer, Coal Trimmr, Coaltrimmer, Coaltrimr, Coal Trimme, Coaltrimmr, Coal Trim'R, Cl. Trimmer, Coal Trimr, Coal Trim'Mr -> Coal Trimmer
8. Milk Vendr, Milkvendor -> Milk Vendor (and heals 1887 Daniel St 21 trapped name)
9. Rebuilds site data, trades data, and stats data.
"""

import os
import sys
import csv
import re
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
BACKUP_CSV = os.path.join(PROJECT_ROOT, "data.csv.bak_before_nov_trades")

def heal_data():
    print(f"Creating backup: {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)

    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    healed_count = 0
    for r in rows:
        tr = r.get("trade", "")
        sn = r.get("surname", "")
        fn = r.get("forename", "")
        bn = r.get("building_name", "")
        orig = (tr, sn, fn, bn)

        # 1. Brick Mkr -> Brick Maker
        if re.search(r"\bbrick\s*mkr\.?\b", tr, re.I):
            tr = re.sub(r"\bbrick\s*mkr\.?\b", "Brick Maker", tr, flags=re.I)

        # 2. Mldr / M'ldr / Mouldr -> Moulder
        if re.search(r"\bbrass\s*m[\x27\’]?ldr\b", tr, re.I):
            tr = "Brass Moulder"
        elif re.search(r"\biron\s*mouldr\b|\bironmouldr\b", tr, re.I):
            tr = "Iron Moulder"
        elif re.search(r"\bpipe\s*mldr\b", tr, re.I):
            tr = "Pipe Moulder"
        elif re.match(r"^m[\x27\’]?ldr\.?$", tr, re.I) or re.match(r"^mouldr\.?$", tr, re.I):
            tr = "Moulder"

        # 3. Alshpr / Coalshpr / Coal Shpr -> Coal Shipper
        if re.search(r"\bcoal\s*shpr\.?\b|\bcoalshpr\.?\b|\bal\s*shpr\.?\b|\balshpr\.?\b|\bcoalshipper\b", tr, re.I):
            tr = "Coal Shipper"

        # 4. Pattrn Mkr / Pattrn Mk / Pattn Mkr -> Pattern Maker
        if re.search(r"\bpat+r?n\s*mk(?:r|\b)\.?\b", tr, re.I):
            tr = re.sub(r"\bpat+r?n\s*mk(?:r|\b)\.?\b", "Pattern Maker", tr, flags=re.I)
        if r.get("year") == "1882" and r.get("street") == "James Street" and r.get("house_number") == "4" and sn == "Benj." and fn == "Howells":
            sn = "Howells"
            fn = "Benj."

        # 5. Phoenix F'dry -> Phoenix Foundry
        if "phoenix f'dry" in tr.lower() or "phoenix f'dry" in sn.lower() or "phoenix f'dry" in bn.lower():
            bn = "Phoenix Foundry"
            if "ironfounder" in tr.lower() or "ironfounder" in sn.lower():
                tr = "Ironfounders"
                if sn == "Phoenix f'dry":
                    sn = "Rees and Thomas"
                    fn = ""
                elif fn == "Rees and Thomas":
                    sn = "Rees and Thomas"
                    fn = ""

        # 1893 James Street 18: coal shipper, Phoenix Foundry
        if r.get("year") == "1893" and r.get("street") == "James Street" and r.get("house_number") == "18" and "phoenix foundry" in tr.lower():
            bn = "Phoenix Foundry"
            tr = "Coal Shipper"

        # 1906 / 1913 James Street Snelling
        if "phoenix foundry" in tr.lower() and "snelling" in sn.lower():
            bn = "Phoenix Foundry"
            tr = "Engineman"

        # 6. Coal Tr'Inr -> Coal Trimmer
        if re.search(r"coal\s*tr[\x27\’]?inr", tr, re.I):
            tr = "Coal Trimmer"

        # 7. Trimmer abbreviations to Coal Trimmer
        if re.match(r"^(?:coal\s*trimm?r|coaltrimmer|coaltrimr|coal\s*trimme|coaltrimmr|coal\s*trim[\x27\’]?r|cl\.\s*trimmer|coal\s*trim[\x27\’]?mr|coal\s*trim,r)$", tr, re.I):
            tr = "Coal Trimmer"

        # 8. Milk Vendr / Milkvendor -> Milk Vendor
        if re.search(r"\bmilk\s*vendr\.?\b|\bmilkvendor\b", tr, re.I):
            tr = "Milk Vendor"
        if r.get("year") == "1887" and r.get("street") == "Daniel Street" and r.get("house_number") == "21" and "meredith" in tr.lower():
            sn = "Meredith"
            fn = "D."
            tr = "Milk Vendor"

        if (tr, sn, fn, bn) != orig:
            r["trade"] = tr
            r["surname"] = sn
            r["forename"] = fn
            r["building_name"] = bn
            healed_count += 1

    print(f"Healed {healed_count} records in data.csv.")

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    heal_data()

    print("\nRebuilding site data and JSON indexes...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_site_data.py")], check=True)

    print("\nRebuilding trades data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_trades_data.py")], check=True)

    print("\nRebuilding stats data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_stats_data.py")], check=True)

    if os.path.exists(BACKUP_CSV):
        os.remove(BACKUP_CSV)
        print("Removed temporary backup file.")

    print("\n[SUCCESS] Trades successfully normalized and site data rebuilt!")

if __name__ == "__main__":
    main()
