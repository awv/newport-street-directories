import json
import re

with open('data/trades.json', 'r') as f:
    data = json.load(f)

issues = [item for item in data['trades'] if item['iss'] == 1]

remaining = []
for item in issues:
    t = item['t'].strip()
    if re.fullmatch(r'[-—_\|~`.,:;!?\'\"\\/\[\]{}()<>\s]+', t): continue
    if re.fullmatch(r'(?:&c|etc\.?|nan|\(return\)|return\.?)', t, re.I): continue
    if re.search(r'^(?:here is|here are|from \d+|the roundabout|\(?flat \d+|tel\.?|telephone)\b', t, re.I): continue
    remaining.append(item)

print(f"Remaining: {len(remaining)}")
print("Top 35 by frequency:")
for item in sorted(remaining, key=lambda x: -x['c'])[:35]:
    print(f"  {item['c']:4d}: {repr(item['t'])}")
