#!/usr/bin/env python3
"""Heal verified contiguous column-wrap / missing-header street blocks in data.csv."""
import csv
import shutil
from pathlib import Path

DATA_CSV = Path(__file__).resolve().parent.parent / "data.csv"
BACKUP_CSV = Path(__file__).resolve().parent.parent / "data.csv.bak_before_intrusion_heal"

# Verified contiguous (year, wrong_street, target_street, start_idx, end_idx_inclusive)
# All indices are 0-based data row indices in data.csv at commit 8212797f.
BLOCK_FIXES = [
    ("1894", "Raglan Street", "Railway Street", 86270, 86292),
    ("1901", "St. Mary Street", "St. Julian Street", 145624, 145653),
    ("1902", "Dock Street", "Dolphin Street", 152633, 152681),
    ("1925", "Duckpool Road", "Dudley Street", 232128, 232154),
    ("1899", "Portland Street", "Potter Street", 119660, 119671),
    ("1899", "Portland Street", "Pottery Terrace", 119704, 119713),
    ("1920", "Fair Oak Avenue", "Fair Oak Terrace", 251455, 251488),
    ("1890", "Caroline Street", "Cardiff Road", 51451, 51490),
    ("1890", "St. Julian Street", "St. Woolos Place", 57041, 57054),
    ("1920", "Llanthewy Road", "Livingstone Place", 254492, 254502),
    ("1924", "Evans Street", "Eveswell Street", 268964, 268997),
    ("1925", "Marion Street", "Market (provision)", 237246, 237360),
    ("1920", "West Street", "West Park Road", 260272, 260300),
    # 1910 #10 swap between Charles Street and Charlotte Street
    ("1910", "Charlotte Street", "Charles Street", 177389, 177389),
    ("1910", "Charles Street", "Charlotte Street", 177430, 177430),
]

def main():
    with open(DATA_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Validate every block before modifying
    total_reassigned = 0
    for year, wrong_st, target_st, start_i, end_i in BLOCK_FIXES:
        for i in range(start_i, end_i + 1):
            r = rows[i]
            if r["year"] != year or r["street"] != wrong_st:
                raise ValueError(
                    f"Mismatch at idx {i}: expected ({year}, {wrong_st}), got ({r['year']}, {r['street']})"
                )

    shutil.copy2(DATA_CSV, BACKUP_CSV)
    for year, wrong_st, target_st, start_i, end_i in BLOCK_FIXES:
        cnt = end_i - start_i + 1
        for i in range(start_i, end_i + 1):
            rows[i]["street"] = target_st
        total_reassigned += cnt
        print(f"  {year}: {wrong_st} -> {target_st} ({cnt} rows, idx {start_i}..{end_i})")

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total rows reassigned: {total_reassigned}")
    print(f"Backup written to: {BACKUP_CSV}")

if __name__ == "__main__":
    main()
