import csv
import json
import os

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

with open("data.csv", "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))

# Find all contiguous blocks of 'Newport Street Directory'
blocks = []
in_block = False
start_i = None

for i, r in enumerate(reader):
    st = r.get("street", "").strip()
    if st == "Newport Street Directory":
        if not in_block:
            in_block = True
            start_i = i
    else:
        if in_block:
            in_block = False
            blocks.append((start_i, i - 1))
if in_block:
    blocks.append((start_i, len(reader) - 1))

print(f"Found {len(blocks)} contiguous blocks of 'Newport Street Directory':\n")
for idx, (s, e) in enumerate(blocks):
    count = e - s + 1
    yr = reader[s].get("year")
    prev_st = reader[s - 1].get("street") if s > 0 else "NONE"
    prev_hn = reader[s - 1].get("house_number") if s > 0 else ""
    prev_fn = reader[s - 1].get("forename", "") + " " + reader[s - 1].get("surname", "")
    
    first_hn = reader[s].get("house_number")
    last_hn = reader[e].get("house_number")
    
    next_st = reader[e + 1].get("street") if e + 1 < len(reader) else "NONE"
    next_hn = reader[e + 1].get("house_number") if e + 1 < len(reader) else ""
    next_fn = reader[e + 1].get("forename", "") + " " + reader[e + 1].get("surname", "")

    print(f"Block #{idx + 1} ({yr}): rows {s}..{e} ({count} rows)")
    print(f"  Preceding row [{s-1}]: {prev_st} #{prev_hn} ({prev_fn.strip()})")
    print(f"  Block doors: #{first_hn} .. #{last_hn}")
    print(f"  Following row [{e+1}]: {next_st} #{next_hn} ({next_fn.strip()})\n")
