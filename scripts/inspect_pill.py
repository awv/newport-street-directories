import csv

with open('data.csv', 'r', encoding='utf-8') as f:
    reader = list(csv.DictReader(f))

targets = ['panteg', 'orchard', 'pemrose', 'pembroke terrace', 'penrose', 'pillgwenlly']

for t in targets:
    matches = [r for r in reader if t in r.get('street', '').lower()]
    names = set(r.get('street') for r in matches)
    print(f"Target '{t}': {len(matches)} rows across street names: {names}")

print("\n--- Pillgwenlly Foundry rows ---")
pf = [r for r in reader if 'foundry' in r.get('street', '').lower()]
for r in pf:
    print(r.get('year'), '|', r.get('street'), '|', r.get('house_number'), '|', r.get('forename'), r.get('surname'), '|', r.get('trade'), '|', r.get('building_name'))

print("\n--- Pillgwenlly rows ---")
pg = [r for r in reader if r.get('street') == 'Pillgwenlly']
for r in pg:
    print(r.get('year'), '|', r.get('street'), '|', r.get('house_number'), '|', r.get('forename'), r.get('surname'), '|', r.get('trade'), '|', r.get('building_name'))
