import csv

with open("data.csv") as f:
    rows = list(csv.DictReader(f))

by_street = {}
for r in rows:
    st = r["street"]
    by_street.setdefault(st, []).append(r)

def sample_street(name):
    recs = by_street.get(name, [])
    print(f"=== {name} ({len(recs)} recs) ===")
    years = sorted(list(set(r["year"] for r in recs)))
    print("Years:", years)
    for r in recs[:5]:
        yr = r["year"]
        num = r["house_number"]
        bldg = r["building_name"]
        sur = r["surname"]
        fore = r["forename"]
        tr = r["trade"]
        print(f"  {yr}: #{num} {bldg} | {sur}, {fore} ({tr})")

targets = [
    "Arlington Street", "Arlington Terrace", "All Saints' Road", "Dawley Street", "Chesterfield Street",
    "Calne", "Caxton Street", "Clytha Council", "Clythrough Road", "Rock Dale",
    "Llanthamthi Street", "Llanthanthi", "Line Street", "Courtybella", "Price", "Prince"
]

for t in targets:
    sample_street(t)
