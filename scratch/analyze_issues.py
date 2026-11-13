import json
import re
from collections import Counter

with open("data/trades.json", "r") as f:
    data = json.load(f)

issues = [item for item in data["trades"] if item["iss"] == 1]
print(f"Total issue trade strings: {len(issues)}")
total_records = sum(item["c"] for item in issues)
print(f"Total affected directory records: {total_records:,}")

cat_counts = Counter()
cat_trade_counts = Counter()
samples = {}

for item in issues:
    t = item["t"].strip()
    c = item["c"]
    
    # 1. Pure punctuation / blanks
    if re.fullmatch(r"[-—_\|~`.,:;!?\'\"\\/\[\]{}()<>\s]+", t):
        cat = "1. Pure Punctuation & Rule Lines (|, _, -, etc.)"
    # 2. Ditto / do
    elif re.fullmatch(r"(?:do\.?|ditto|do\s+do|ditto\s+ditto)", t, re.I):
        cat = "2. Ditto / do Lines (ditto, do)"
    # 3. Floating suffixes / artifacts
    elif re.fullmatch(r"(?:&c|etc\.?|nan|\(return\)|return\.?|ditto\.?)", t, re.I):
        cat = "3. Floating Suffixes & Artifacts (etc, &c, nan, return)"
    # 4. Civic titles / Honorifics
    elif re.fullmatch(r"(?:j\.?p\.?|rev\.?|d\.?l\.?|m\.?p\.?|o\.?b\.?e\.?|c\.?b\.?e\.?|k\.?c\.?|bart\.?|esq\.?)", t, re.I):
        cat = "4. Civic Titles & Honorifics (J.P., Rev, Esq)"
    # 5. Short valid abbreviations
    elif re.fullmatch(r"(?:p\.?o\.?|eng\.?|ry\.?|clk\.?|ptr\.?|dvr\.?|drvr\.?|wkr\.?|labr\.?|lbr\.?|mcht\.?|agt\.?)", t, re.I):
        cat = "5. Valid Short Abbreviations (Eng, P.O, Ry, Labr)"
    # 6. Waypoints / Address / Navigational
    elif re.search(r"^(?:here is|here are|from \d+|the roundabout|\(?flat \d+|tel\.?|telephone)\b", t, re.I):
        cat = "6. Street Waypoints & Addresses (here is..., from...)"
    # 7. Name / Company prefix leaks
    elif re.search(r"^(?:mrs\.?|miss\.?|mr\.?|thos\.?|jas\.?|wm\.?|saml\.?|ltd\.?|limited|& co\.?|co\.?)\b", t, re.I):
        cat = "7. Name / Company Prefix Leaks (Mrs, Miss, Ltd, Co)"
    # 8. Contains numbers / house numbers
    elif re.search(r"\d", t):
        cat = "8. Contains Digits (house numbers, phone numbers, years)"
    # 9. Punctuation noise mixed with trade text
    elif re.search(r"[;\/:_\{\}\[\]\\\|]", t):
        cat = "9. Trade Names with Symbol Noise (pipes, brackets, semicolons)"
    elif len(t) <= 3:
        cat = "10. Short Unrecognized 1-3 Letter Tokens (op, de, bl)"
    else:
        cat = "11. Other Miscellaneous Issues"

    cat_counts[cat] += c
    cat_trade_counts[cat] += 1
    if cat not in samples:
        samples[cat] = []
    if len(samples[cat]) < 6:
        samples[cat].append((t, c))

for cat in sorted(cat_counts.keys()):
    print(f"\n{cat}")
    print(f"   Unique trade strings: {cat_trade_counts[cat]:,} | Total records: {cat_counts[cat]:,}")
    print(f"   Examples: {samples[cat]}")
