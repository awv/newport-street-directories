#!/usr/bin/env python3
import csv
import shutil
from pathlib import Path

DATA_CSV = Path("/Users/robgale/Documents/Newport Street Directory Project/data.csv")
BACKUP_CSV = Path("/Users/robgale/Documents/Newport Street Directory Project/data.csv.bak_before_user_four_fixes")

def main():
    print(f"Backing up {DATA_CSV} -> {BACKUP_CSV}...")
    shutil.copy2(DATA_CSV, BACKUP_CSV)

    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

    modified_319 = 0
    modified_adeline = 0
    modified_agincourt = 0
    modified_alb = 0

    for r in reader:
        st = r.get("street", "").strip()
        yr = r.get("year", "").strip()

        # 1. 319 -> Caerleon Road
        if st == "319" and yr == "1895":
            r["street"] = "Caerleon Road"
            if not r.get("house_number"):
                r["house_number"] = "319"
            modified_319 += 1

        # 2. Adeline street continued -> Adeline Street
        elif st.lower() == "adeline street continued":
            r["street"] = "Adeline Street"
            modified_adeline += 1

        # 3. Agincourt Street (continued) -> Agincourt Street
        elif st.lower() in ["agincourt street (continued)", "agincourt street continued"]:
            r["street"] = "Agincourt Street"
            modified_agincourt += 1

        # 4. Alb -> Albert Avenue (1886), Albion Street (1893, 1900), Albert Terrace (1895)
        elif st == "Alb":
            if yr == "1886":
                r["street"] = "Albert Avenue"
            elif yr == "1893":
                r["street"] = "Albion Street"
            elif yr == "1895":
                r["street"] = "Albert Terrace"
            elif yr == "1900":
                r["street"] = "Albion Street"
            modified_alb += 1

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)

    print(f"Fixes applied successfully to {DATA_CSV}:")
    print(f"  - 319: {modified_319} records moved to Caerleon Road")
    print(f"  - Adeline street continued: {modified_adeline} records merged into Adeline Street")
    print(f"  - Agincourt Street (continued): {modified_agincourt} records merged into Agincourt Street")
    print(f"  - Alb: {modified_alb} records disentangled (1886->Albert Avenue, 1893/1900->Albion Street, 1895->Albert Terrace)")

if __name__ == "__main__":
    main()
