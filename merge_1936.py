import csv

# We read 1936_cleaned.csv and append to data.csv
records_to_append = []
with open("1936_cleaned.csv", "r", encoding="utf-8") as f_in:
    reader = csv.DictReader(f_in)
    for r in reader:
        records_to_append.append(r)

# Read the header of data.csv to ensure we keep fields in correct order
with open("data.csv", "r", encoding="utf-8") as f_data:
    reader = csv.DictReader(f_data)
    fieldnames = reader.fieldnames

# Append to data.csv
with open("data.csv", "a", encoding="utf-8", newline="") as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writerows(records_to_append)

print(f"Appended {len(records_to_append)} records to data.csv successfully.")
