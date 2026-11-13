#!/usr/bin/env python3
"""
heal_1908_misassigned_blocks.py
Surgically repairs the 11 contiguous resident blocks in 1908 where Gemini
transcribed residents under the wrong street column due to:
1. Cross-reference street names in notes (e.g. Ailesbury Street 'From 11 Albany-street')
2. Page-top continuation headers overriding the current street (e.g. George Street -> Gaer Street)
3. Street truncation (e.g. Oakley Street -> Oak Street)
"""

import csv
import shutil
import subprocess

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_1908_block_healing"

print(f"Backing up {DATA_CSV} -> {BACKUP_CSV}...")
shutil.copyfile(DATA_CSV, BACKUP_CSV)

with open(DATA_CSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# Verification assertions for each block slice
BLOCKS = [
    # (start_idx, end_idx_inclusive, expected_year, expected_old_street, new_street, desc)
    (352084, 352122, "1908", "Albany Street", "Ailesbury Street", "Ailesbury Street (doors 3-44)"),
    (352523, 352552, "1908", "Alma", "Alice Street", "Alice Street (doors 23-44)"),
    (353343, 353345, "1908", "Bishop Street", "Bilston Street", "Bilston Street (doors 4, 6, 8)"),
    (359121, 359199, "1908", "Gaer Street", "George Street", "George Street (doors 4-82a)"),
    (359823, 359849, "1908", "Hamilton Street", "Halstead Street", "Halstead Street (doors 54-2)"),
    (360511, 360514, "1908", "Hoskins street", "Ivor Street", "Ivor Street (doors 6-9)"),
    (360552, 360599, "1908", "Hoskins street", "Jeddo Street", "Jeddo Street (doors 9-99)"),
    (362661, 362712, "1908", "Milton Road", "Morden Road", "Morden Road (doors 28-79)"),
    (363100, 363116, "1908", "Oak Street", "Oakley Street", "Oakley Street (doors 33-1)"),
    (363933, 363955, "1908", "Redland Street", "Railway Street", "Railway Street (doors 4-29)"),
    (365514, 365517, "1908", "Stafford Road", "Stanley Road", "Stanley Road (villas)"),
]

total_repaired = 0

for start_idx, end_idx, yr, old_st, new_st, desc in BLOCKS:
    block_len = end_idx - start_idx + 1
    # Check boundaries
    for i in range(start_idx, end_idx + 1):
        r = rows[i]
        assert r["year"] == yr, f"Row {i} year mismatch: {r['year']} != {yr}"
        assert r["street"] == old_st, f"Row {i} street mismatch: {r['street']} != {old_st}"
        r["street"] = new_st
        total_repaired += 1
    print(f"Repaired {block_len:2d} rows for {desc} -> {new_st}")

print(f"\nTotal rows successfully healed: {total_repaired}")

with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Saved updated data.csv! Rebuilding site data and statistics...")
subprocess.run(["python3", "scripts/build_site_data.py"], check=True)
subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)
print("Complete!")
