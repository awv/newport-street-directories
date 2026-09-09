#!/usr/bin/env python3
import csv
import os

DATA_CSV = "data.csv"
TEMP_CSV = "data_temp.csv"

count_fixed = 0

with open(DATA_CSV, "r", encoding="utf-8") as infile, open(TEMP_CSV, "w", encoding="utf-8", newline="") as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    in_target_block = False
    
    for row in reader:
        if len(row) >= 2 and row[0] == "1903" and row[1] == "Herbert Street":
            if "Liverpool-street" in row:
                in_target_block = True
            
            if in_target_block:
                row[1] = "Hereford Street"
                count_fixed += 1
                if len(row) >= 3 and row[2] == "25":
                    in_target_block = False

        writer.writerow(row)

os.replace(TEMP_CSV, DATA_CSV)
print(f"Successfully re-attributed {count_fixed} rows from 'Herbert Street' to 'Hereford Street' in 1903 directory data.")
