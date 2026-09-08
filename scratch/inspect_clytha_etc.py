import csv

with open("data.csv") as f:
    rows = list(csv.DictReader(f))

by_street = {}
for r in rows:
    st = r["street"]
    by_street.setdefault(st, []).append(r)

print("=== Clytha Council ===")
for r in by_street.get("Clytha Council", []):
    print(r["year"], r["house_number"], r["building_name"], r["surname"], r["forename"])

print("\n=== Clythrough Road ===")
for r in by_street.get("Clythrough Road", []):
    print(r["year"], r["house_number"], r["building_name"], r["surname"], r["forename"])

print("\n=== All Saints' Road ===")
for r in by_street.get("All Saints' Road", []):
    print(r["year"], r["house_number"], r["building_name"], r["surname"], r["forename"])

print("\n=== Rock Dale ===")
for r in by_street.get("Rock Dale", []):
    print(r["year"], r["house_number"], r["building_name"], r["surname"], r["forename"])

