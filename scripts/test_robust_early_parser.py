import re
import json

with open("master_streets.json", "r", encoding="utf-8") as f:
    master_data = json.load(f)["streets"]

street_lookup = {}
for s_slug, s_info in master_data.items():
    c_name = s_info.get("canonical_name", "").strip()
    if c_name and len(c_name) > 3:
        street_lookup[c_name.lower()] = c_name

variants = {
    "commercial st": "Commercial Street", "commercial rd": "Commercial Road",
    "stow hill": "Stow Hill", "high st": "High Street", "dock st": "Dock Street",
    "gt. dock st": "Dock Street", "great dock st": "Dock Street", "skinner st": "Skinner Street",
    "baneswell": "Baneswell Road", "pillgwenlly": "Pillgwenlly", "llanarth st": "Llanarth Street",
    "hill st": "Hill Street", "cardiff rd": "Cardiff Road", "chepstow rd": "Chepstow Road",
    "palmyra pl": "Palmyra Place", "cambria pl": "Cambria Place", "clifton pl": "Clifton Place",
    "clarence pl": "Clarence Place", "westgate st": "Westgate Street", "corn st": "Corn Street",
    "canal parade": "Canal Parade", "market st": "Market Street", "old green": "Old Green",
    "griffin st": "Griffin Street", "cinder hill": "Cinder Hill", "marshes rd": "Marshes Road",
    "tredegar st": "Tredegar Street", "cross st": "Cross Street", "thomas st": "Thomas Street",
    "charles st": "Charles Street", "george st": "George Street", "powell st": "Powell Street",
    "king's hill": "King's Hill", "king-st": "King Street", "king st": "King Street",
    "union st": "Union Street", "caerleon": "Caerleon"
}
for k, v in variants.items():
    street_lookup[k] = v

sorted_streets = sorted(street_lookup.keys(), key=lambda x: len(x), reverse=True)

def find_street(text):
    if not text: return ""
    t_low = text.lower()
    for s_low in sorted_streets:
        if re.search(r'\b' + re.escape(s_low) + r'\b', t_low):
            return street_lookup[s_low]
    return ""

def parse_robust_row(row, active_category):
    # Filter empty / dash / nan tokens
    tokens = [c.strip() for c in row if c.strip() and c.strip().lower() not in ('nan', '--', '-', '')]
    if not tokens:
        return None, active_category

    combined = " ".join(tokens)

    # Check if category heading
    # In 1835: ['', '', '--', '--', 'LINEN & WOOLLEN DRAPERS.', '--', '[st'] -> tokens = ['LINEN & WOOLLEN DRAPERS.', '[st']
    # In 1844: ['', '', 'NaN', 'MILLINERS AND DRESS MAKERS', 'NaN', 'Daw Ann, Commercial st'] -> has person + trade!
    first_tok = tokens[0].strip(' .:')
    
    # Check if pure heading
    is_pure_heading = False
    if len(tokens) == 1 or (len(tokens) == 2 and any(tokens[1].startswith(c) for c in ['[', '('])):
        if first_tok.isupper() or any(kw in first_tok.lower() for kw in ['dealers', 'makers', 'attorneys', 'clergy', 'surgeons', 'inns', 'taverns', 'blacksmiths', 'bakers', 'butchers', 'carpenters', 'joiners', 'merchants']):
            is_pure_heading = True

    if is_pure_heading:
        new_cat = first_tok.title()
        return None, new_cat

    # Check for 1844 style: trade in col 3, person+street in col 5
    # e.g. ['', '', 'NaN', 'MILLINERS AND DRESS MAKERS', 'NaN', 'Daw Ann, Commercial st']
    # tokens = ['MILLINERS AND DRESS MAKERS', 'Daw Ann, Commercial st']
    trade = active_category
    street = ""
    surname = ""
    forename = ""

    # Check if trade is explicit in tokens
    trade_token_idx = -1
    for i, tok in enumerate(tokens):
        c_tok = tok.strip(' .:')
        if c_tok.isupper() and len(c_tok) > 4:
            trade = c_tok.title()
            trade_token_idx = i
            break

    # Remaining tokens to parse for person & address
    person_tokens = [tok for i, tok in enumerate(tokens) if i != trade_token_idx]

    # Combine person tokens to extract street and name
    person_str = " ".join(person_tokens)
    
    # Extract street
    street = find_street(person_str)

    # Remove street from person_str
    name_str = person_str
    if street:
        for s_low in sorted_streets:
            if re.search(r'\b' + re.escape(s_low) + r'\b', name_str.lower()):
                name_str = re.sub(r'\b' + re.escape(s_low) + r'\b', '', name_str, flags=re.I).strip(' ,.')
                break

    # Split name_str into surname and forename
    name_str = name_str.strip(' ,.')
    if ',' in name_str:
        parts = name_str.split(',', 1)
        surname = parts[0].strip()
        forename = parts[1].strip()
    else:
        parts = name_str.split()
        if len(parts) >= 2:
            # Check if parts[0] is title
            if parts[0].lower() in ('mr.', 'mrs.', 'miss', 'rev.', 'dr.', 'sir'):
                surname = parts[1]
                forename = parts[0] + " " + " ".join(parts[2:])
            else:
                # In 1835: ['Frost', 'John'] -> surname Frost, forename John
                # In 1844 Daw Ann: surname Daw, forename Ann
                surname = parts[0]
                forename = " ".join(parts[1:])
        elif len(parts) == 1:
            surname = parts[0]

    # Strip leftover titles or punctuation
    surname = surname.strip(' ,.-')
    forename = forename.strip(' ,.-')
    trade = trade.strip(' ,.-')

    if not surname and not forename:
        return None, trade

    return {
        "street": street,
        "surname": surname,
        "forename": forename,
        "trade": trade
    }, trade

test_cases = [
    # 1835 Frost John
    (['', '', 'Frost', 'John', '--', '--', 'High st', '\n'], "Attorneys"),
    # 1835 heading
    (['', '', '--', '--', 'LINEN & WOOLLEN DRAPERS.', '--', '[st', '\n'], "Attorneys"),
    # 1835 John Frost under Linen & Woollen Drapers
    (['', '', 'Frost', 'John', '--', '--', 'High st', '\n'], "Linen & Woollen Drapers"),
    # 1844 Milliners
    (['', '', 'NaN', 'MILLINERS AND DRESS MAKERS', 'NaN', 'Daw Ann, Commercial st\n'], "Attorneys"),
    (['', '', 'NaN', 'MILLINERS AND DRESS MAKERS', 'NaN', 'Holmes Mary & Ann, High st\n'], "Attorneys"),
    # 1844 Henry Farr
    (['', '', '', 'Farr Henry', 'High st', '\n'], "Attorneys")
]

cat = "Attorneys"
for row, c in test_cases:
    res, cat = parse_robust_row(row, cat)
    print("Row:", [x.strip() for x in row if x.strip()])
    print("  -> Result:", res)
    print("  -> Active Category now:", cat)
