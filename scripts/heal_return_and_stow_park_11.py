#!/usr/bin/env python3
"""
1. Dataset-wide (all years): strip stray `(return)` / `(return.)` markers from
   `surname` and `forename`, recovering the surname from `trade` when `(return)`
   occupied `surname` (e.g. 1903 & 1927 11 Stow Park Avenue).
2. 11 Stow Park Avenue sweep:
   - Un-swap 1902 `LeBrasseur Henry` -> `Henry LeBrasseur`.
   - Standardise `Le Brasseur` -> `LeBrasseur` (1908, 1910) and `Woolner` -> `Woolmer` (1910).
   - Move `Woolmer` from `trade` to `building_name` (1898, 1925).
   - Reassign 1920 `Ocean Accident & Guarantee Corporation` (`hn='11'`) from
     `Stow Park Avenue` to `Stow Hill` (where 11 Stow Hill's commercial block belongs).
"""

import csv
import os
import re
from collections import Counter

RETURN_RE = re.compile(r"\s*\(return\.?\)\s*", re.I)


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data.csv")

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    stats = Counter()
    for r in rows:
        sn = (r["surname"] or "").strip()
        fn = (r["forename"] or "").strip()
        tr = (r["trade"] or "").strip()
        bn = (r["building_name"] or "").strip()
        st = (r["street"] or "").strip()
        hn = (r["house_number"] or "").strip()
        yr = (r["year"] or "").strip()

        # 1. Dataset-wide (return) / (return.) cleanup
        if RETURN_RE.search(sn):
            cleaned_sn = RETURN_RE.sub(" ", sn).strip()
            if not cleaned_sn and tr and r["street"] == "Stow Park Avenue" and hn == "11":
                r["surname"] = "LeBrasseur"
                r["trade"] = ""
            elif not cleaned_sn and tr and re.fullmatch(r"[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?", tr):
                r["surname"] = tr
                r["trade"] = ""
            else:
                r["surname"] = cleaned_sn
            stats["return_in_sn"] += 1

        if RETURN_RE.search(fn):
            cleaned_fn = RETURN_RE.sub(" ", fn).strip()
            r["forename"] = cleaned_fn
            if not cleaned_fn and r["surname"].strip().lower() == "void":
                r["surname"] = ""
                r["trade"] = "Void"
            stats["return_in_fn"] += 1

        # 2. 11 Stow Park Avenue sweep
        if st == "Stow Park Avenue" and hn == "11":
            if yr == "1902" and fn == "LeBrasseur Henry" and not sn:
                r["forename"] = "Henry"
                r["surname"] = "LeBrasseur"
                stats["stow_park_11"] += 1
            if r["surname"].strip() == "Le Brasseur":
                r["surname"] = "LeBrasseur"
                stats["stow_park_11"] += 1
            if bn == "Woolner":
                r["building_name"] = "Woolmer"
                stats["stow_park_11"] += 1
            if not bn and tr == "Woolmer":
                r["building_name"] = "Woolmer"
                r["trade"] = ""
                stats["stow_park_11"] += 1
            if yr == "1920" and "Ocean Accident" in fn:
                r["street"] = "Stow Hill"
                stats["stow_park_11_reassigned"] += 1

    print("Stats:", dict(stats), "Total:", sum(stats.values()))
    if sum(stats.values()) > 0:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {csv_path}")


if __name__ == "__main__":
    main()
