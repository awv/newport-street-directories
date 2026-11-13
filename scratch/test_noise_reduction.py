import json
import re

with open("data/trades.json", "r") as f:
    data = json.load(f)

issues = [item for item in data["trades"] if item["iss"] == 1]
print(f"Starting issue trade strings: {len(issues)}")

cleaned_blank = 0
cleaned_fixed = 0
unhandled = []

for item in issues:
    t = item["t"].strip()
    c = item["c"]

    # 1. Pure punctuation or blank line artifacts
    if re.fullmatch(r"[-—_\|~`.,:;!?\'\"\\/\[\]{}()<>\s]+", t):
        cleaned_blank += 1
        continue

    # 2. Floating suffixes / nan
    if re.fullmatch(r"(?:&c|etc\.?|nan|\(return\)|return\.?)", t, re.I):
        cleaned_blank += 1
        continue

    # 3. Waypoint / street navigation lines
    if re.search(r"^(?:here is|here are|from \d+|the roundabout|\(?flat \d+|tel\.?|telephone)\b", t, re.I):
        cleaned_blank += 1
        continue

    # 4. Leaked name prefix before known trade: e.g. 'Wm. Labourer', 'John, fitter', 'Hy. clerk'
    m_name = re.match(r"^(?:[A-Z][a-z]*\.?|[A-Z]\.?|\b(?:Wm|Hy|Thos|Geo|Chas|John|Jas|Saml|Fred|Edwd|Arth|Walt)\b\.?),?\s+([A-Za-z].*)$", t)
    if m_name:
        sub_trade = m_name.group(1).strip()
        if len(sub_trade) > 3 and not re.search(r"\d", sub_trade):
            cleaned_fixed += 1
            continue

    # 5. Symbol noise trailing a clean trade: e.g. 'labourer [ ] [ ] [ ]', 'Surgeon, |', 'butcher, |'
    clean_sub = re.sub(r"[\s,\|\;_\{\}\[\]\(\)]+$", "", t).strip()
    clean_sub = re.sub(r"^(?:do\.?|ditto)\s*\[(.*?)\]", r"\1", clean_sub, flags=re.I).strip()
    if clean_sub != t and len(clean_sub) > 2 and clean_sub.isalpha():
        cleaned_fixed += 1
        continue

    # 6. Standard short abbreviations
    if t.lower() in ("eng", "p.o", "ry", "agt", "wkr", "lbr", "labr", "clk"):
        cleaned_fixed += 1
        continue

    unhandled.append((t, c))

print(f"Can automatically blank (pure noise/spills): {cleaned_blank} trade strings")
print(f"Can automatically repair into valid trade: {cleaned_fixed} trade strings")
print(f"Remaining for manual review: {len(unhandled)} trade strings (down from {len(issues)})")
