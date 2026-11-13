#!/usr/bin/env python3
import csv
import shutil
from pathlib import Path

DATA_CSV = Path("/Users/robgale/Documents/Newport Street Directory Project/data.csv")
BACKUP_CSV = Path("/Users/robgale/Documents/Newport Street Directory Project/data.csv.bak_before_three_letter_sweep")

def main():
    print(f"Backing up {DATA_CSV} -> {BACKUP_CSV}...")
    shutil.copy2(DATA_CSV, BACKUP_CSV)

    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

    counts = {
        'Aru': 0,
        'Art_Arcade': 0,
        'Art_Bailey': 0,
        'Art_Baldwin': 0,
        'Arc_Annesley': 0,
        'Arc_Archibald': 0,
        'ARC_Arcade': 0,
        'Alt_Alma': 0,
        'Alm_Alltyryn': 0,
        'Alm_Alma': 0
    }

    # Tracking state for 1886 Art
    in_baldwin_1886 = False

    for idx, r in enumerate(reader):
        st = r.get("street", "").strip()
        yr = r.get("year", "").strip()
        sname = r.get("surname", "").strip()
        bname = r.get("building_name", "").strip()
        hnum = r.get("house_number", "").strip()

        # 1. Aru -> Arundel Road
        if st == "Aru":
            r["street"] = "Arundel Road"
            counts['Aru'] += 1

        # 2. Art (1886) -> Market Arcade (1-14), Bailey Street (15-55), Baldwin Street (56-105)
        elif st == "Art" and yr == "1886":
            if sname == "Gardner" and hnum == "7":
                in_baldwin_1886 = True
            
            if in_baldwin_1886:
                r["street"] = "Baldwin Street"
                counts['Art_Baldwin'] += 1
            elif any(x in sname for x in ["Edwards", "Rosser", "Taylor", "Gumm", "Tipton", "Sully", "Johns", "James", "Price", "Morkham", "Stubbs", "Smith", "Tamplin"]):
                r["street"] = "Market Arcade"
                counts['Art_Arcade'] += 1
            else:
                r["street"] = "Bailey Street"
                counts['Art_Bailey'] += 1

        # 3. Arc / ARC
        elif st == "ARC":
            r["street"] = "Market Arcade"
            counts['ARC_Arcade'] += 1

        elif st == "Arc":
            if yr == "1890":
                # Doors 31-48 from Toms to Osborne are Annesley Road
                if hnum in ["31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48"] and any(x in sname for x in ["Toms", "Hillier", "Stevens", "Patterson", "Whitrow", "Curgenven", "Ray", "Duncanson", "Williams", "Brown", "Wright", "Lander", "Naish", "Hando", "Fowler", "French", "Rendell", "Osborne"]):
                    r["street"] = "Annesley Road"
                    counts['Arc_Annesley'] += 1
                else:
                    r["street"] = "Archibald Street"
                    counts['Arc_Archibald'] += 1
            else:
                # 1898, 1900, 1901 are all Archibald Street
                r["street"] = "Archibald Street"
                counts['Arc_Archibald'] += 1

        # 4. Alt (1887) -> Alma Street
        elif st == "Alt":
            r["street"] = "Alma Street"
            counts['Alt_Alma'] += 1

        # 5. Alm -> Allt-yr-yn Road (1890) or Alma Street (1899, 1900)
        elif st == "Alm":
            if yr == "1890":
                r["street"] = "Allt-yr-yn Road"
                counts['Alm_Alltyryn'] += 1
            else:
                r["street"] = "Alma Street"
                counts['Alm_Alma'] += 1

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)

    print("Disentanglement complete! Summary of reassignments:")
    for k, v in counts.items():
        print(f"  - {k}: {v} records")

if __name__ == "__main__":
    main()
