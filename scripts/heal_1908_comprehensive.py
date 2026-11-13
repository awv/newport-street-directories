#!/usr/bin/env python3
"""
heal_1908_comprehensive.py
Comprehensive healing for all remaining 1908 structural issues:
1. Williams Street (indices 366874-366962, 89 rows): Remapped from Whitstone Road -> Williams Street
2. Capel Crescent (indices 354728-354780, 53 rows): Remapped from Capel Street -> Capel Crescent
3. Newport Corporation Market (indices 362881-362992, 112 rows): Remapped from NEWPORT STREET DIRECTORY -> Newport Corporation Market
4. Stow Hill (indices 365673-365705, 33 rows): Remapped from NEWPORT STREET DIRECTORY -> Stow Hill
5. Normalize all 28 UPPERCASE streets in 1908 to their canonical title-case names (Dolphin Street, Church Road, Osborne Place, etc.)
"""

import csv
import shutil
import subprocess

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_1908_comprehensive"

print(f"Backing up {DATA_CSV} -> {BACKUP_CSV}...")
shutil.copyfile(DATA_CSV, BACKUP_CSV)

with open(DATA_CSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# 1. Williams Street block
for i in range(366874, 366963):
    r = rows[i]
    assert r["year"] == "1908" and r["street"] == "Whitstone Road", f"Row {i} unexpected: {r}"
    r["street"] = "Williams Street"
print("Repaired 89 rows for Williams Street.")

# 2. Capel Crescent block
for i in range(354728, 354781):
    r = rows[i]
    assert r["year"] == "1908" and r["street"] == "Capel Street", f"Row {i} unexpected: {r}"
    r["street"] = "Capel Crescent"
print("Repaired 53 rows for Capel Crescent.")

# 3. Newport Corporation Market block
for i in range(362881, 362993):
    r = rows[i]
    assert r["year"] == "1908" and r["street"] == "NEWPORT STREET DIRECTORY", f"Row {i} unexpected: {r}"
    r["street"] = "Newport Corporation Market"
print("Repaired 112 rows for Newport Corporation Market.")

# 4. Stow Hill block
for i in range(365673, 365706):
    r = rows[i]
    assert r["year"] == "1908" and r["street"] == "NEWPORT STREET DIRECTORY", f"Row {i} unexpected: {r}"
    r["street"] = "Stow Hill"
print("Repaired 33 rows for Stow Hill.")

# 5. Uppercase street normalization in 1908
UPPER_MAP = {
    'DOLPHIN STREET': 'Dolphin Street',
    'CHURCH ROAD': 'Church Road',
    'SUMMER HILL VILLAS': 'Summerhill Villas',
    'UNION WORKHOUSE': 'Union Workhouse',
    'CAERLEON ROAD (149)': 'Caerleon Road',
    'OSBORNE PLACE': 'Osborne Place',
    'CARLISLE PLACE': 'Carlisle Place',
    'DOS ROAD': 'Dos Road',
    'CHURCH STREET': 'Church Street',
    'CAMBRIAN ROAD': 'Cambrian Road',
    'CLARENCE PLACE': 'Clarence Place',
    'CAERLEON ROAD': 'Caerleon Road',
    'DOCK STREET': 'Dock Street',
    'NEWPORT ARCADE': 'Newport Arcade',
    'CANAL PARADE': 'Canal Parade',
    'CAMELOT PLACE': 'Camelot Place',
    'CAERLEON ROAD (307)': 'Caerleon Road',
    'THE DRILL HALL': 'The Drill Hall',
    'STOW PARK TERRACE': 'Stow Park Terrace',
    'CAMBRIDGE ROAD': 'Cambridge Road',
    'CLAREMONT TERRACE': 'Claremont Terrace',
    'TALBOT LANE': 'Talbot Lane',
    'CALDICOT STREET': 'Caldicot Street',
    'STOW PARK POST OFFICE': 'Stow Park Post Office',
    'STOW HILL SCHOOLS': 'Stow Hill Schools',
    'WEST PARK POST OFFICE': 'West Park Post Office',
    'S. MARIE\'S CATHOLIC CH': 'St. Marie\'s Catholic Church',
    'ALBERT HALL CHAMBERS': 'Albert Hall Chambers'
}

upper_fixed = 0
for r in rows:
    if r["year"] == "1908":
        st = r["street"].strip()
        if st in UPPER_MAP:
            r["street"] = UPPER_MAP[st]
            upper_fixed += 1

print(f"Normalized {upper_fixed} uppercase street rows in 1908.")

with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Saved updated data.csv! Rebuilding site data and statistics...")
subprocess.run(["python3", "scripts/build_site_data.py"], check=True)
subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)
print("Complete!")
