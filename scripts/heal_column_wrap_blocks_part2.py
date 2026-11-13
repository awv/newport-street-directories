#!/usr/bin/env python3
"""Heal Part 2 column-wrap / missing-header street blocks and 1971 OCR street typos in data.csv."""
import csv
import shutil
from pathlib import Path

DATA_CSV = Path(__file__).resolve().parent.parent / "data.csv"
BACKUP_CSV = Path(__file__).resolve().parent.parent / "data.csv.bak_before_intrusion_heal_part2"

# Verified (year, wrong_street, target_street, start_idx, end_idx_inclusive)
# Only rows matching (year, wrong_street) inside [start_idx..end_idx_inclusive] are updated.
BLOCK_FIXES = [
    ("1925", "Northumberland Road", "North Street", 238097, 238146),
    ("1906", "River Side", "Robert Street", 328238, 328282),
    ("1927", "Windsor Road", "Williams Street", 300306, 300364),
    ("1890", "Dolphin Street", "Dos Road", 53605, 53647),
    ("1927", "Kensington Place", "Keynsham Avenue", 291606, 291641),
    ("1892", "Livingstone Place", "Llanarth Street", 64527, 64593),
    ("1882", "Blewitt Street", "Bolt Street", 29841, 29884),
    ("1902", "Potter Street", "Pottery Terrace", 157292, 157299),
    ("1902", "Potter Street", "Power Street", 157300, 157353),
]

STREET_TYPO_1971 = {
    "Capet Street": "Capel Street",
    "Brynhfryd Avenue": "Brynhyfryd Avenue",
}


def main():
    with open(DATA_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    shutil.copy2(DATA_CSV, BACKUP_CSV)
    total = 0

    for year, wrong_st, target_st, start_i, end_i in BLOCK_FIXES:
        cnt = 0
        for i in range(start_i, end_i + 1):
            if rows[i]["year"] == year and rows[i]["street"] == wrong_st:
                rows[i]["street"] = target_st
                cnt += 1
        total += cnt
        print(f"  {year}: {wrong_st} -> {target_st} ({cnt} rows, idx {start_i}..{end_i})")

    for wrong_st, target_st in STREET_TYPO_1971.items():
        cnt = 0
        for r in rows:
            if r["year"] == "1971" and r["street"] == wrong_st:
                r["street"] = target_st
                cnt += 1
        total += cnt
        print(f"  1971: {wrong_st} -> {target_st} ({cnt} rows)")

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total rows reassigned: {total}")


if __name__ == "__main__":
    main()
