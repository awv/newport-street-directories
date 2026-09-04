import csv

data_csv = "data.csv"
cleaned_csv = "volume_csvs/1910_cleaned.csv"

# 1. Read existing data.csv and filter out any existing 1910 records
header = None
records_to_keep = []
existing_count = 0

with open(data_csv, "r", encoding="utf-8") as f_data:
    reader = csv.reader(f_data)
    header = next(reader)
    for row in reader:
        if row and row[0] == "1910":
            existing_count += 1
            continue
        records_to_keep.append(row)

print(f"Found and removed {existing_count} old 1910 records from {data_csv}.")

# 2. Read new clean 1910 records
new_records = []
try:
    with open(cleaned_csv, "r", encoding="utf-8") as f_new:
        reader = csv.reader(f_new)
        new_header = next(reader) # Skip header
        for row in reader:
            new_records.append(row)
except FileNotFoundError:
    print(f"Warning: {cleaned_csv} not found. No new records merged.")

# 3. Write everything back to data.csv
with open(data_csv, "w", encoding="utf-8", newline="") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(header)
    writer.writerows(records_to_keep)
    if new_records:
        writer.writerows(new_records)

print(f"Successfully merged {len(new_records)} new clean 1910 records into {data_csv}.")
