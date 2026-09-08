import csv

with open("data.csv") as f:
    rows = list(csv.DictReader(f))

gane_rows = [r for r in rows if "P. E. Gane" in r["street"]]

# Let's inspect house numbers and building names to identify what streets they belong to
print("Sample house numbers & names in 1913 P. E. Gane:")
for r in gane_rows[:25]:
    print(f"  #{r['house_number']} {r['building_name']} | {r['surname']} {r['forename']}")

print("\nSample house numbers & names in 1920 P. E. Gane:")
for r in gane_rows[202:227]:
    print(f"  #{r['house_number']} {r['building_name']} | {r['surname']} {r['forename']}")
