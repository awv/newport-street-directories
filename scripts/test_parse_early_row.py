import re

def parse_early_tsv_row(row):
    # Filter empty tokens
    tokens = [c.strip() for c in row if c.strip() and c.strip().lower() != 'nan']
    if not tokens:
        return None
        
    combined = " ".join(tokens)
    
    # Check if heading
    if len(tokens) == 1 and tokens[0].isupper() and len(tokens[0]) > 3:
        return {"type": "heading", "text": tokens[0].title()}
        
    # Check if typical 1844 row: ['', '', 'Clark', '& Westbury', 'GROCERS & TEA DEALERS.', '', 'High st']
    # Or: ['', '', 'Brewer', 'Marmaduke', 'GROCERS & TEA DEALERS.', '', 'Commercial st']
    # Or 1835 row: ['', '', 'Reed', 'Samuel', 'Booksellers & Stationers, (and trunk maker) High street', ...]
    # Or 1844 attorney: ['', '', '', 'Farr Henry', 'High st']
    
    surname = ""
    forename = ""
    trade = ""
    address = ""
    
    # Let's inspect length of tokens
    print("Tokens:", tokens)

