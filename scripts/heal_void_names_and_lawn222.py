#!/usr/bin/env python3
"""
1. Move standalone `void` / `-void` / `vacant` / `empty` trapped in `forename` or
   `surname` (when the other name field is empty or also void/vacant/empty) into
   `trade` (`Void` / `Vacant`) across `data.csv` (`year <= 1936`).
2. Move `1910 Lawn Terrace No. 222` house name `Adoph` from `trade` to `building_name`.
"""
import argparse
import csv
import os
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "data.csv")

VOID_RE = re.compile(r"^[\-\s]*(void|vacant|empty)[\-\s]*$", re.I)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    stats = Counter()
    for r in rows:
        if int(r["year"]) > 1936:
            continue

        # 1. 1910 Lawn Terrace No. 222: Adoph -> building_name
        if (
            r["year"] == "1910"
            and r["street"].strip().lower() == "lawn terrace"
            and r["house_number"].strip() == "222"
            and r["trade"].strip().lower() == "adoph"
            and not r["building_name"].strip()
        ):
            r["building_name"] = "Adoph"
            r["trade"] = ""
            stats["lawn_222_adoph"] += 1

        # 2. Void / Vacant / Empty trapped in forename or surname
        fn = r["forename"].strip()
        sur = r["surname"].strip()
        tr = r["trade"].strip()

        fn_void = VOID_RE.match(fn)
        sur_void = VOID_RE.match(sur)

        if (fn_void and (not sur or sur_void)) or (sur_void and (not fn or fn_void)):
            label = (fn_void or sur_void).group(1).capitalize()
            if label == "Empty":
                label = "Void"
            r["forename"] = ""
            r["surname"] = ""
            if not tr:
                r["trade"] = label
            stats[f"moved_{label.lower()}_from_name"] += 1

    print("Stats:", dict(stats))
    if not args.dry_run:
        with open(DATA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print("Saved updated data.csv!")


if __name__ == "__main__":
    main()
