import csv

with open("data.csv") as f:
    rows = list(csv.DictReader(f))

by_street = {}
for r in rows:
    st = r["street"]
    by_street.setdefault(st, []).append(r)

def inspect_street(st):
    recs = by_street.get(st, [])
    print(f"\n--- {st} --- ({len(recs)} recs)")
    years = sorted(list(set(r["year"] for r in recs)))
    print("Years present:", years)
    for yr in years:
        sub = [r for r in recs if r["year"] == yr]
        print(f"  Year {yr}: {len(sub)} recs")
        for r in sub[:3]:
            print(f"    #{r['house_number']} {r['building_name']} | {r['surname']}, {r['forename']} | {r['trade']}")

inspect_street("Arlington Street")
inspect_street("Arlington Terrace")
inspect_street("All Saints' Road")
inspect_street("Dawley Street")
inspect_street("Chesterfield Street")
inspect_street("Calne")
inspect_street("Clytha Council")
inspect_street("Clythrough Road")
inspect_street("Rock Dale")
inspect_street("Llanthamthi Street")
inspect_street("Llanthanthi")
inspect_street("Line Street")
inspect_street("Courtybella")
inspect_street("Price")
inspect_street("Prince")
inspect_street("Eveswell Park")
inspect_street("Eseswell Park")
inspect_street("Eswewell Park")

