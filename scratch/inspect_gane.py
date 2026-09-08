import csv

with open("data.csv") as f:
    rows = list(csv.DictReader(f))

gane_rows = [r for r in rows if "P. E. Gane" in r["street"]]
print(f"Total rows in P. E. Gane: {len(gane_rows)}")

# Check distinct years and house numbers
by_year = {}
for r in gane_rows:
    by_year.setdefault(r["year"], []).append(r)

for yr, rlist in by_year.items():
    print(f"Year {yr}: {len(rlist)} rows. First 3: {rlist[:3]}")

