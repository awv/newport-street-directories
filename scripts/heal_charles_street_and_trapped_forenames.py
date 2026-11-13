#!/usr/bin/env python3
"""
1. Dataset-wide (all years including 1971): fix unambiguous
   `Surname + Title/Initials` trapped in `forename` when `surname == ''`
   (e.g. `Harrhy D.` -> `forename='D.', surname='Harrhy'`,
   `Thomas Mrs. J. Felix` -> `forename='Mrs. J. Felix', surname='Thomas'`).
2. Charles Street (1908): un-swap all remaining `Surname Forename` rows in
   `forename` (`Platt John`, `Watts Frederick`, `Shewring Joseph`, etc.) and
   move business/institution names (`Foslett & Co.`, `Rogers G. E. & Co.`,
   `Unitarian Meeting Room`, etc.) into `surname`.
3. Charles Street (1925): fix `& Griffiths | Cowley` -> `Cowley & Griffiths`,
   `W. & Son | Collard` -> `Collard W. & Son`, and `Eaves T. Arthur`.
"""

import csv
import os
import re
from collections import Counter

TRAPPED_PAT = re.compile(
    r"^([A-Z][A-Za-z'\-]+)\s+((?:Mrs\.?|Miss\.?|Rev\.?|Dr\.?)(?:\s+(?:[A-Z]\.?|[A-Z][a-z]+))*|(?:[A-Z]\.\s*){1,3})$"
)
NON_SURNAME_PREFIXES = {
    "st", "st.", "rev", "dr", "mrs", "miss", "the", "new", "old",
    "mount", "park", "east", "west", "north", "south",
}

CHARLES_1908_SWAPS = {
    "Thomas Albert", "Squire Caleb", "Lefcovitch Israel", "Blunt Alexander",
    "Rowberry William", "Coxon John", "Platt John", "Watts Frederick",
    "Shewring Joseph", "Maddocks Joseph", "Snelgrove Henry", "Quick William",
    "Mendelsohn Louis", "Fennell Albert", "Cohen Israel",
}

CHARLES_1908_BUS = {
    "Foslett & Co.", "English Baptist Chapel", "Newport Education",
    "P.T. Centre", "Rogers G. E. & Co.", "Bible and Tract Depôt",
    "Unitarian Meeting Room",
}


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data.csv")

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    stats = Counter()
    for r in rows:
        fn = (r["forename"] or "").strip()
        sn = (r["surname"] or "").strip()
        st = (r["street"] or "").strip()
        yr = (r["year"] or "").strip()

        # 1. Dataset-wide unambiguous Surname + Title/Initials in forename
        if fn and not sn:
            m = TRAPPED_PAT.match(fn)
            if m and m.group(1).lower() not in NON_SURNAME_PREFIXES:
                r["surname"] = m.group(1).strip()
                r["forename"] = re.sub(r"\s+", " ", m.group(2).strip())
                stats["trapped_surname_title_init"] += 1
                continue

        # 2. Charles Street 1908 remaining two-word swaps & businesses
        if st == "Charles Street" and yr == "1908" and fn and not sn:
            if fn in CHARLES_1908_SWAPS:
                s_part, f_part = fn.split(" ", 1)
                r["surname"] = s_part
                r["forename"] = f_part
                stats["charles_1908_swap"] += 1
            elif fn in CHARLES_1908_BUS:
                r["surname"] = fn
                r["forename"] = ""
                stats["charles_1908_bus"] += 1

        # 3. Charles Street 1925 reversed business/name entries
        if st == "Charles Street" and yr == "1925":
            if fn == "& Griffiths" and sn == "Cowley":
                r["forename"] = ""
                r["surname"] = "Cowley & Griffiths"
                stats["charles_1925_fix"] += 1
            elif fn == "W. & Son" and sn == "Collard":
                r["forename"] = ""
                r["surname"] = "Collard W. & Son"
                stats["charles_1925_fix"] += 1
            elif fn == "Eaves T. Arthur" and sn.startswith("secretary"):
                r["forename"] = "T. Arthur"
                r["surname"] = "Eaves"
                r["trade"] = "Secretary (Moores G. W., Assistant Secretary)"
                stats["charles_1925_fix"] += 1

    print("Stats:", dict(stats), "Total:", sum(stats.values()))
    if sum(stats.values()) > 0:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {csv_path}")


if __name__ == "__main__":
    main()
