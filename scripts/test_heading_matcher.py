import re

def is_category_heading(row):
    tokens = [c.strip() for c in row if c.strip() and c.strip().lower() not in ('nan', '--', '-', '')]
    if not tokens:
        return False, ""
    
    # Check if any token is an obvious trade classification header
    for tok in tokens:
        c_tok = tok.strip(' .:[];()')
        if (c_tok.isupper() and len(c_tok) > 4) or any(kw in c_tok.lower() for kw in [
            'attorneys', 'grocers', 'drapers', 'bakers', 'boot & shoe', 'cabinet makers',
            'carpenters', 'blacksmiths', 'milliners', 'painters', 'surgeons', 'tailors',
            'taverns & public houses', 'retailers of beer', 'spirit dealers', 'stone masons',
            'iron founders', 'coal owners', 'lime burners', 'marine stores'
        ]):
            # Ensure it is not an address or personal name
            if not any(sw in tok.lower() for sw in [' high st', ' commercial st', ' stow hill', ' cardiff rd']):
                # Return cleaned heading
                return True, c_tok.title()
                
    return False, ""

test_rows = [
    ['', '', '--', '--', 'LINEN & WOOLLEN DRAPERS.', '--', '[st', '\n'],
    ['', '', '', 'Attorneys.', '', '\n'],
    ['', '', 'NaN', 'MILLINERS AND DRESS MAKERS', 'NaN', 'Daw Ann, Commercial st\n'],
    ['Baker', 'Daniel', '--', '--', 'High st\n'],
    ['Frost', 'John', '--', '--', 'High st\n']
]

for r in test_rows:
    is_head, head_name = is_category_heading(r)
    print("Row:", [x.strip() for x in r if x.strip()])
    print("  -> Is Heading:", is_head, "| Heading Name:", head_name)
