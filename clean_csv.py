import csv
import json
import os
import re

INPUT_CSV = "data.csv"
OUTPUT_CSV = "data.csv"
EDGE_CASES_FILE = "edge_cases.json"

# Load Edge Cases Configuration
EDGE_CASES = []
if os.path.exists(EDGE_CASES_FILE):
    with open(EDGE_CASES_FILE, "r", encoding="utf-8") as ef:
        try:
            EDGE_CASES = json.load(ef).get("overrides", [])
            print(f"Loaded {len(EDGE_CASES)} historical edge cases from {EDGE_CASES_FILE}")
        except Exception as e:
            print(f"Warning: Could not load {EDGE_CASES_FILE}: {e}")

# Dictionary of standard street suffix expansions
ABBREVIATIONS = {
    r"\bRd\b\.?": "Road",
    r"\bSt\b\.?": "Street",
    r"\bAve\b\.?": "Avenue",
    r"\bTer\b\.?": "Terrace",
    r"\bPl\b\.?": "Place",
    r"\bSq\b\.?": "Square",
    r"\bCres\b\.?": "Crescent",
    r"\bPde\b\.?": "Parade",
    r"\bGdns\b\.?": "Gardens",
}

HEADER_SURNAMES = {"butcher's", "thompson's", "johns'", "johns's", "directory"}

CROSS_STREET_REGEX = re.compile(
    r'\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.)\b.*?\bto\b.*?\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.|square)\b'
    r'|^\s*\[?(?:here\s+are|here\s+is|here\s+cross|\[?return\]?|\(return\.?\)|return\.?)\]?\b'
    r'|^\s*[\(\[]?\s*return\.?\s*[\)\]]?\s*$'
    r'|^\s*see\s+also\s+[A-Za-z]+'
    r'|^\s*now\s+(?:in|see)\s+[a-z0-9\s\.\-]+'
    r'|^\s*(?:maindee|newport|pill)from\b'
    r'|^\s*from\s+[A-Za-z\s]+'
    r'|^\s*[A-Za-z\s]+street\s+from\b'
    r'|^\s*[\(\[]?\s*(?:right|left)\s+hand\s*(?:side)?\s*[\)\]]?\s*$'
    r'|^\s*[\(\[]?\s*(?:right|left)\s+hand\s+side\b'
    r'|^\s*(?:from\s+)?[a-z0-9\s\.\-]+\s*[\(\[]?\s*(?:right|left)\s+hand\s*[\)\]]?\s*(?:opposite\s+[a-z0-9\s\.\-]+)?\s*$'
    r'|^\s*opposite\s+(?:maindee\s+schools|board\s+schools|st\.\s*woolos\s+church|malpas\s+school|kensington\s+place|stow\s+park|stow-park)'
    r'|^\s*last\s+corporation[\s\-]*road\s+street\s+on\s+left\s+hand\s+side'
    r'|\bderives\s+its\s+name\s+from\s+the\s+well\b'
    r'|\biron\s+ring\s+let\s+into\s+the\s+pavement\b'
    r'|\bembraces\s+the\s+numerous\s+streets\b'
    r'|\bis\s+a\s+district\s+lying\s+between\b'
    r'|\bcommonly\s+called\s+pill\b'
    r'|^\s*(?:newport\s*)?bottom\s+of\b'
    r'|\boff\s+[a-z0-9\s\.\-]+(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.|square|estate)\b',
    re.I
)

# Trade keywords to identify trade bleeding into forename
TRADE_KEYWORDS = [
    "mechanic", "clerk", "grocer", "mariner", "driver", "fitter", "carpenter",
    "platelayer", "labourer", "shoemaker", "draper", "baker", "mason", "rigger",
    "tailor", "painter", "smith", "builder", "haulier", "fireman", "guard",
    "boot", "joiner", "dealer", "assistant", "manager", "visitor", "shipper",
    "plasterer", "sail", "engineer", "inspector", "agent", "blacksmith",
    "ironworker", "steelworker", "trimmer", "pilot", "master", "brewer",
    "porter", "clerk", "nurse", "telegraph", "engine", "collector", "station",
    "booksellers", "stationers", "auctioneer", "dressmaker", "gardener",
    "milliner", "wine", "cabinet maker", "professor", "sorter"
]

BUSINESS_SUFFIX_REGEX = re.compile(
    r"^(?:&|and|ltd|limited|co\.?|company|sons|bros|brothers|school|academy|place\s+school|house|depot|works|chambers|stores|hotel|inn|arms|vaults)\b",
    re.I
)

INSTITUTION_WORD = re.compile(
    r"^(?:chapel|church|office|association|board office|houses|seminary|school|infirmary|hospital|bank|association offices|society|works|depot|hall|chambers)\b",
    re.I
)

VILLA_WORD = re.compile(
    r"\b([A-Z][a-zA-Z\s'\-]+?\b(?:villa|cottage|house|inn|arms|hotel|chambers|lodge|court|hall|chapel))\b",
    re.I
)

NON_PERSON_WORDS = ['wagon', 'coal', 'iron', 'colliery', 'docks', 'railway', 'supply', 'stores', 'drapery']

COMPANY_SUFFIX_TRADE_REGEX = re.compile(r'^\s*(ltd\.?|limited|co\.?|& co\.?|co\.? ltd\.?|ld\.?)\s*$', re.I)

PAT_NAME_TRADE = re.compile(
    r'^([A-Z][a-zA-Z\x27\-]+),\s+([A-Z][a-zA-Z\.\s\x27\-]+?)(?:(?:\s*[\-\x97\u2013\u2014]\s*|\s*,\s*)(.*))?$'
)

PAT_FULL_CORONATION = re.compile(
    r'^(?:([A-Z][a-zA-Z\x27\-]+),\s+)?([A-Z][a-zA-Z\.\s\x27\-]*?)\s*[\-,]\s*(steward|manager|secretary|caretaker|curator|matron|superintendent|keeper|clerk|agent|collector|officer|warden|headmaster|headmistress|master|teacher|governor|attendant|proprietor|propr)\s*,\s*(.*)$',
    re.I
)

PAT_TRADE_INST = re.compile(
    r'^(steward|manager|secretary|caretaker|curator|matron|superintendent|keeper|clerk|agent|collector|officer|warden|headmaster|headmistress|master|teacher|governor|attendant|proprietor|propr)\s*,\s*(.*)$',
    re.I
)

PAT_TRADE_VILLA = re.compile(
    r'^([a-zA-Z\s\(\)\/\&\x27\-]+?)\.?\s*[\-,]\s*([A-Z][a-zA-Z\s\x27\-]+)$'
)

VILLA_WORDS = {
    'villa', 'cottage', 'house', 'inn', 'arms', 'hotel', 'chambers', 'lodge', 'court',
    'hall', 'chapel', 'bank', 'nook', 'grove', 'oaks', 'limes', 'firs', 'laurels',
    'knoll', 'bungalow', 'ferns', 'gables', 'mount', 'view', 'haven', 'lawn', 'dingle',
    'burn', 'park', 'croft', 'springfield', 'denbury', 'harlesden', 'font burn',
    'greencroft', 'rose cottage', 'le quatre saisons', 'villas', 'cottages'
}

NON_VILLA_WORDS = {
    'journeyman', 'docks', 'works', 'depot', 'stores', 'factory', 'company', 'office',
    'railway', 'gwr', 'ltd', 'limited', 'co', 'bros', 'sons', 'dept', 'station', 'co-op',
    'association', 'society', 'hospital', 'asylum', 'infirmary', 'school', 'schools',
    'quay', 'wharf', 'dock', 'yard', 'mills', 'foundry', 'brewery'
}

def is_trade_word(text):
    if not text:
        return False
    t_low = text.lower()
    return any(kw in t_low for kw in TRADE_KEYWORDS) or t_low in {'fitter', 'wiredrawer', 'secretary', 'accountant', 'cranedriver', 'supervisor', 'joiner', 'clerk', 'painter', 'builder', 'driver', 'grocer', 'draper', 'mason', 'baker', 'tailor', 'agent', 'manager', 'salesman'}

BUILDING_NAME_TRADE_REGEX = re.compile(
    r'^\s*The\s+(?:Laurels|Firs|Knoll|Bungalow|Ferns|Nook|Grove|Oaks|Limes|Retreat|Woodlands|Mount|Hollies|Dell|Grange|Dingle|Beeches|Croft|Gables|Haven|Egg Market|Lawn|Poplars|Elms|Cedars|Willows|Pines|Vicarage|Rectory)\b',
    re.I
)

HOUSE_SUFX = re.compile(r'\b(?:villa|cottage|house|lodge|gables|mount|view|haven|knoll|lawn|dingle|house|home|place|court|hall|chambers)\b', re.I)

TITLES_AND_FORENAMES = {
    'mrs', 'mrs.', 'mr', 'mr.', 'miss', 'miss.', 'ms', 'dr', 'dr.', 'rev', 'rev.',
    'thos', 'thos.', 'jas', 'jas.', 'wm', 'wm.', 'john', 'geo', 'geo.', 'chas', 'chas.',
    'hy', 'hy.', 'richd', 'richd.', 'saml', 'saml.', 'robte', 'robt', 'robt.', 'harry',
    'ernest', 'fredk', 'fredk.', 'arthur', 'edwd', 'edwd.', 'edw', 'edw.', 'walt', 'walt.',
    'walter', 'david', 'danl', 'danl.', 'benj', 'benj.', 'stepn', 'stepn.',
    'iss e', 'mrs l', 'mrs elizabeth', 'mrs mizth', 'mrs nizth', 'mrs nizth.', 'mrs Elizth',
    'thos j', 'wm g', 'wm a', 'wm h', 'wm j', 'wm henry', 'john h', 'miss e', 'miss m',
    'mrs a', 'mrs e', 'mrs j', 'mrs m', 'mrs s', 'mrs ma', 'mrs lr', 'mrs af', 'mrs ee',
    'mrs mw', 'mrs fl', 'mrs ca', 'mrs gm', 'mrs ja', 'mrs maw', 'mrs gh', 'mrs aj',
    'mrs tj', 'mrs se', 'mrs hd', 'mrs mr', 'mrs hm', 'mrs mn', 'mrs ef', 'mrs ga',
    'mrs gw', 'mrs hl', 'mrs lf', 'mrs wm', 'mrs eb', 'mrs sm', 'mrs kl', 'mrs ad',
    'mrs lv', 'mrs mh', 'mrs aod', 'mrs ag', 'mrs eh', 'mrs sj', 'mrs dg', 'mrs wt',
    'mrs og', 'mrs js', 'mrs hw', 'mrs jw', 'mrs ms', 'mrs la', 'mrs tw', 'mrs ep',
    'mrs rh', 'mrs cd', 'mrs gf', 'mrs ew', 'mrs hg', 'mrs ee', 'mrs ft', 'mrs tg',
    'mrs hh', 'mrs we', 'mrs mg', 'mrs kc', 'mrs ke', 'mrs as', 'mrs te', 'mrs ec',
    'mrs be', 'mrs wa', 'miss ey', 'miss fl', 'miss emily e', 'miss s', 'miss i',
    'miss he', 'miss cj', 'miss lh', 'miss am', 'miss mab', 'miss ellen e', 'miss w',
    'miss gh', 'miss ei', 'miss mary o', 'miss phys', 'miss p', 'miss vm', 'miss ha',
    'miss dw', 'miss re', 'miss rem', 'miss fa', 'miss mb', 'miss ae', 'miss t',
    'miss eh', 'miss o', 'tom',
    'henry', 'joseph', 'albert', 'reginald', 'harold', 'william', 'thomas', 'james', 'george',
    'charles', 'frederick', 'fred', 'fredk', 'arthur', 'edward', 'edwd', 'edw', 'edwin',
    'walter', 'walt', 'david', 'daniel', 'danl', 'benjamin', 'benj', 'stephen', 'stepn',
    'robert', 'robt', 'robte', 'richard', 'richd', 'samuel', 'saml', 'harry', 'ernest',
    'alfred', 'alf', 'percy', 'herbert', 'hbt', 'sidney', 'sydney', 'leslie', 'norman',
    'stanley', 'victor', 'lewis', 'frank', 'clifford', 'cecil', 'horace', 'edgar', 'bernard',
    'leonard', 'raymond', 'gilbert', 'douglas', 'rowland', 'roland', 'arnold', 'reuben',
    'oscar', 'gordon', 'clarence', 'maurice', 'godfrey', 'hubert', 'wilfred', 'lionel',
    'perceval', 'percival', 'bertram', 'archibald', 'arch', 'montague', 'clement', 'hector',
    'algernon', 'basil', 'rupert', 'clive', 'evelyn', 'vivian', 'dennis', 'denys', 'eric',
    'ivor', 'trevor', 'brian', 'owen', 'john', 'jack', 'tom', 'jim', 'bill', 'bob', 'dick',
    'joe', 'bert', 'ted', 'charlie', 'willie', 'sammie', 'ben', 'dan', 'dave', 'sam',
    'freddie', 'archie', 'albie', 'ernie', 'alec', 'alander', 'alexander', 'abraham', 'abra',
    'alonsa', 'alonzo', 'ambrose', 'amur', 'anew', 'angus', 'anselm', 'anthony', 'antonio',
    'augustus', 'august', 'barnaby', 'bartholomew', 'benedic', 'benedict', 'bertrand', 'caleb',
    'mary', 'elizabeth', 'eliza', 'elizth', 'sarah', 'ann', 'anne', 'annie', 'jane',
    'florence', 'alice', 'edith', 'ellen', 'mabel', 'ethel', 'kate', 'clara', 'emily',
    'rose', 'maud', 'maude', 'ada', 'margaret', 'martha', 'hannah', 'caroline', 'grace',
    'violet', 'beatrice', 'daisy', 'amy', 'lilian', 'lily', 'linda', 'gladys', 'winifred',
    'dorothy', 'marjory', 'marjorie', 'ivy', 'phoebe', 'nora', 'norah', 'olive', 'dora',
    'hilda', 'elsie', 'may', 'marian', 'marion', 'eva', 'phyllis', 'gwladys', 'gwendoline',
    'gwen', 'megan', 'rhoda', 'celia', 'ruth', 'rachel', 'esther', 'naomi', 'leah', 'agnes',
    'harriet', 'harriett', 'frances', 'charlotte', 'louisa', 'louise', 'marianne', 'miriam',
    'selina', 'priscilla', 'susannah', 'susan', 'susie', 'maggie', 'katie', 'minnie',
    'jessie', 'bessie', 'nellie', 'flossie', 'lottie', 'tillie', 'dolly', 'winnie'
}

SINGLE_INITIALS = {'w', 'j', 'wh', 'h', 'jh', 'a', 'wj', 'e', 'ae', 't', 'r', 'we', 'aj', 'ej', 'hj', 'gh', 'jw', 'aw', 'fw', 'c', 'th', 'g', 'dj', 'he', 'hc', 'ew', 'd', 'rc', 'f', 'tg', 'wt', 'hb', 'm', 'jf', 'ta', 'cw', 'rs', 'jr', 'b', 'ed', 'ea', 'fj', 'ah', 'dw', 'jc', 'hs', 'am', 'wa', 'rj', 'ra', 'tj'}
VALID_ACRONYMS = {'gwr', 'g.w.r.', 'jp', 'j.p.', 'hmc', 'h.m.c.', 'gpo', 'g.p.o.', 'pc', 'p.c.', 'po', 'p.o.', 'rn', 'r.n.', 'ra', 'r.a.', 're', 'r.e.', 'alcm', 'a.l.c.m.', 'ba', 'b.a.', 'ma', 'm.a.', 'md', 'm.d.', 'bsc', 'b.sc.', 'ce', 'fc'}

def is_person_name_or_title(t):
    if not t:
        return False
    t_clean = t.strip()
    t_lower = t_clean.lower()

    if t_lower in VALID_ACRONYMS:
        return False

    if t_lower in TITLES_AND_FORENAMES:
        return True

    if t_lower in SINGLE_INITIALS:
        return True

    if re.match(r'^(mrs\.?|miss\.?|mr\.?)\s+[a-z\.\s]+$', t_lower):
        trade_keywords = {'grocer', 'draper', 'fruiterer', 'manageress', 'teacher', 'butcher', 'refreshments', 'school', 'midwife', 'chiropodist', 'grcr', 'stewardess', 'postmstrss', 'warden', 'secretary', 'baker', 'tailor', 'painter', 'smith', 'builder', 'agent', 'dealer', 'nurse', 'clerk'}
        if not any(kw in t_lower for kw in trade_keywords):
            return True

    return False

SAINT_STREET_MAP = {
    r'^St\.\s*Annes?\b.*': "St. Anne's Crescent",
    r'^St\.\s*Brides?\b.*': "St. Bride's Crescent",
    r'^St\.\s*Johns?\b.*': "St. John's Road",
    r'^St\.\s*Julians?\s*Ave.*': "St. Julian's Avenue",
    r'^St\.\s*Julians?\s*Rd.*': "St. Julian's Road",
    r'^St\.\s*Marks?\b.*': "St. Mark's Crescent",
    r'^St\.\s*Marys?\s*Rd.*': "St. Mary's Road",
    r'^St\.\s*Stephens?\b.*': "St. Stephen's Road",
    r'^St\.\s*Woollos?\s*Rd.*': "St. Woolos Road",
    r'^St\.\s*Woolos?\s*Pl.*': "St. Woolos Place"
}

def clean_street_name(name):
    if not name:
        return ""
    
    clean = name.replace('"', '').strip(' ,.-~')
    clean = re.sub(r",\s*[A-Za-z0-9\s]+\b", "", clean)

    # 1. Strip trailing district/ward letter codes (e.g. '.T', '. P', ' P', ' M', '. C', '. W', '.T,')
    clean = re.sub(r'[\.\s]+[A-Z][\.,\s]*$', '', clean, flags=re.IGNORECASE).rstrip(" ,.-")

    # 2. Expand 'Street [Saint Name]' -> 'St. [Saint Name]' (e.g. 'Street Anne's' -> 'St. Anne's')
    clean = re.sub(r'^Street\s+([A-Z])', r'St. \1', clean, flags=re.IGNORECASE)
    clean = re.sub(r'^St\b\.?\s*', 'St. ', clean, flags=re.IGNORECASE)

    # 3. Standardize possessive apostrophes & capital 'S (e.g. King'S -> King's, Protheroe's Row -> Protheroes Row)
    if 'protheroe' in clean.lower():
        clean = 'Protheroes Row'

    clean = re.sub(r"' S\b", "'s", clean)
    clean = re.sub(r"'S\b", "'s", clean)

    # 4. Standardize Saint street names with apostrophes
    for pat, rep in SAINT_STREET_MAP.items():
        if re.match(pat, clean, flags=re.IGNORECASE):
            clean = rep
            break
            
    # 5. Expand abbreviations
    for pattern, replacement in ABBREVIATIONS.items():
        clean = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)

    # 6. Fix OCR symbol typos & specific street name merges (e.g. 'Eveswel]' -> 'Eveswell', 'Malpas (Main) Road' -> 'Malpas Road')
    clean = re.sub(r'Eveswel\]', 'Eveswell', clean, flags=re.IGNORECASE)
    clean = re.sub(r'([a-z])\]', r'\1l', clean)
    clean = re.sub(r'\bMalpas\s*\(\s*Main\s*\)\s*Road\b', 'Malpas Road', clean, flags=re.IGNORECASE)
        
    return clean.strip(" ,.-")

def title_case_name(name):
    if not name:
        return ""
    return re.sub(r"\w\S*", lambda m: m.group(0).capitalize() if m.group(0).islower() else m.group(0), name).strip()

def apply_edge_cases(record):
    """Applies structured edge-case overrides from edge_cases.json."""
    st = record["street"]
    yr = record["year"]
    h_num = record["house_number"]
    bldg = record["building_name"]
    s = record["surname"]
    f = record["forename"]
    t = record["trade"]

    for rule in EDGE_CASES:
        match = rule.get("match", {})
        
        # Match street
        if match.get("street") and match["street"].lower() != st.lower():
            continue
        # Match year
        if match.get("year") and match["year"] != yr:
            continue
        # Match house_number
        if "house_number" in match and match["house_number"] != h_num:
            continue
        # Match surname
        if match.get("surname") and match["surname"].lower() != s.lower():
            continue
        if match.get("surname_contains") and match["surname_contains"].lower() not in s.lower():
            continue
        if match.get("forename_contains") and match["forename_contains"].lower() not in f.lower():
            continue
        if match.get("building_name") and match["building_name"].lower() != bldg.lower():
            continue

        # Apply direct override
        if "apply" in rule:
            for k, v in rule["apply"].items():
                record[k] = v

        # Apply conditional override
        if "apply_conditional" in rule:
            cond = rule["apply_conditional"]
            if cond.get("if_surname_contains") and cond["if_surname_contains"].lower() in s.lower():
                for k, v in cond["apply"].items():
                    record[k] = v

    return record

def clean_record(row):
    year = (row.get("year") or "").strip()
    street = clean_street_name(row.get("street") or "")
    house_num = (row.get("house_number") or "").strip().strip(',"-~')
    bldg_name = (row.get("building_name") or "").strip().strip(',"-~')
    surname = (row.get("surname") or "").strip().strip(',"-~')
    forename = (row.get("forename") or "").strip().strip(',"-~')
    trade = (row.get("trade") or "").strip().strip(',"-~')

    # 1. Filter out Directory Header Artifacts, Cross-street Headings & (return) Markers
    if surname.lower() in HEADER_SURNAMES and (forename.isdigit() or not trade):
        return None

    combined_name = f"{surname} {forename}".strip()
    if CROSS_STREET_REGEX.search(combined_name) or CROSS_STREET_REGEX.search(bldg_name) or CROSS_STREET_REGEX.search(surname):
        return None

    # Strip district headers (e.g. MaindeeFrom, NewportFrom)
    surname = re.sub(r'^(maindee|newport|pill)from\s*', '', surname, flags=re.I).strip()
    forename = re.sub(r'^(maindee|newport|pill)from\s*', '', forename, flags=re.I).strip()

    # Strip (right hand), [left hand side.], etc. attached to real resident fields
    pat_side_strip = re.compile(r'[\(\[]?\s*\b(right|left)\s+hand(\s+side)?\b\s*[\)\]]?', re.I)
    surname = pat_side_strip.sub('', surname).strip(' ,"-~.')
    forename = pat_side_strip.sub('', forename).strip(' ,"-~.')
    bldg_name = pat_side_strip.sub('', bldg_name).strip(' ,"-~.')
    trade = pat_side_strip.sub('', trade).strip(' ,"-~.')

    # Aid post fix (e.g. surname='First', forename='aid post')
    if surname.lower() == "first" and forename.lower() == "aid post":
        surname = "First Aid Post"
        forename = ""
        trade = "First Aid Post"

    # Standardize Ld -> Ltd for company names (e.g. 'Newport Labour Hall Ld')
    bldg_name = re.sub(r'\bLd\.?\b', 'Ltd', bldg_name)
    surname = re.sub(r'\bLd\.?\b', 'Ltd', surname)
    trade = re.sub(r'\bLd\.?\b', 'Ltd', trade)

    # Standardize directory cross-reference entries (e.g. surname='NewportSee', forename='Stow Hill', street='Lamb Cottages')
    raw_all_fields = f"{bldg_name} {surname} {forename}".strip()
    cross_ref_match = re.search(r'\[?\b(?:newport\s*)?see\s+(?:also\s+)?(?:under\s+|no\.\s*\d+\s+)?([A-Za-z\s]+)', raw_all_fields, re.I)
    if cross_ref_match:
        target_dest = cross_ref_match.group(1).strip(']. ')
        target_dest = re.sub(r'^(?:under\s+|no\.\s*\d+\s+)', '', target_dest, flags=re.I).strip()
        target_dest = re.sub(r'(\b(?:street|road|lane|hill|place|terrace|avenue|square|parade|chambers|cottages)\b).*', r'\1', target_dest, flags=re.I).strip()
        surname = f"See {target_dest}"
        forename = ""
        bldg_name = street
        trade = "Directory Cross-Reference"

    # 2. Fix shifted surname/forename/trade in building_name (e.g. bldg='Bennett', surname='AG', forename='brewery hand')
    if bldg_name and bldg_name[0].isupper() and not any(w in bldg_name.lower() for w in ['house', 'villa', 'cottage', 'chambers', 'works', 'inn', 'arms', 'hotel', 'building', 'school', 'lodge', 'place', 'hall', 'terrace', 'view', 'court', 'gardens']):
        f_low = forename.lower()
        if f_low in TRADE_KEYWORDS or any(w in f_low for w in ['hand', 'worker', 'labourer', 'sorter', 'fitter', 'carpenter', 'driver', 'grocer', 'draper', 'mason', 'butcher', 'bootmaker', 'shoemaker', 'painter', 'plumber', 'tailor', 'baker', 'signalman', 'postman', 'shunter', 'timekeeper', 'tobacconist', 'waterman', 'greengrocer']):
            trade = title_case_name(forename)
            forename = surname
            surname = bldg_name
            bldg_name = ""

    # 3. Handle Crindau Glass / Gas Works company titles
    if "Glass Manufacturing" in combined_name or "Glass Manufacturing" in trade or "Glass Manufacturing" in surname:
        surname = "South Wales Glass Manufacturing Co. Office & Works"
        forename = ""
        trade = "glass manufacturers"
    elif surname == "Crindau" and forename == "Gas Works":
        surname = "Crindau Gas Works"
        forename = ""

    # 4. Extract trade trapped in forename or surname (e.g. 'Thos. chimney sweep', 'S. W. butcher', 'Stanley & beer retailer')
    TRAPPED_TRADE_PAT = (
        r'chimney\s+sweeps?|chimney\s+sweeper|wholesale\s+tobacconist|tobacconist|'
        r'cab\s+proprietor|beer\s+retailer|general\s+dealer|greengrocer|'
        r'pork\s+butcher|butcher|plumber|draper|grocer|mason|'
        r'carpenter|blacksmith|shoemaker|bootmaker|ironmonger|'
        r'haulier|painter|tinman|tinsmith|marine\s+stores|'
        r'stationer|newsagent|fruiterer|fishmonger|baker|'
        r'confectioner|tailor|outfitter|hairdresser|upholsterer|'
        r'dairyman|cowkeeper|builder|wheelwright|saddler|'
        r'watchmaker|jeweller|pawnbroker|house\s+agent|coal\s+merchant|'
        r'wine\s+merchant|spirit\s+merchant|chemist|druggist|'
        r'milliner|wine|cabinet\s+maker|professor\s+of\s+\w+|registry\s+office|'
        r'auctioneer|dressmaker|gardener|solicitor|surgeon|dentist|'
        r'architect|engineer|broker|accountant|merchant|agent|'
        r'licensed\s+victualler|publican|storekeeper|store\s+keeper|timekeeper|gatekeeper'
    )
    if forename:
        match_t_f = re.match(r"^(.*?)\s+\b(" + TRAPPED_TRADE_PAT + r")\b$", forename, re.I)
        if match_t_f:
            c_fn = match_t_f.group(1).strip()
            extra_t = match_t_f.group(2).strip()
            if c_fn and (c_fn[0].isupper() or c_fn.endswith('.')):
                forename = c_fn
                trade = f"{extra_t}, {trade}".strip(", ") if trade else extra_t

    if surname:
        match_t_s = re.match(r"^(.*?)\s*&\s*\b(" + TRAPPED_TRADE_PAT + r")\b$", surname, re.I)
        if match_t_s:
            c_sn = match_t_s.group(1).strip()
            extra_t = match_t_s.group(2).strip()
            if c_sn and c_sn[0].isupper():
                surname = c_sn
                trade = f"{extra_t}, {trade}".strip(", ") if trade else extra_t

    # 5. Fix institution names split across surname & forename (e.g. 'Conservative' + 'Association', 'Baptist' + 'chapel')
    if forename and INSTITUTION_WORD.search(forename.strip()):
        surname = title_case_name(f"{surname} {forename}".strip())
        forename = ""

    # 5c. Extract shifted villa lines where house number, resident surname & forename are trapped in trade (e.g. trade='31, Foden, Thos', surname='Shaldon House')
    m_shifted_villa = re.match(r'^\s*(\d+[a-zA-Z]?)\s*,\s*([A-Za-z\x27\s\-]+?)\s*,\s*([A-Za-z\.\s]+)\s*$', trade, re.I)
    if m_shifted_villa:
        extracted_hno = m_shifted_villa.group(1).strip()
        extracted_surname = m_shifted_villa.group(2).strip()
        extracted_forename = m_shifted_villa.group(3).strip()

        villa_parts = [p for p in [bldg_name, surname, forename] if p and not p.isdigit()]
        combined_villa = " ".join(villa_parts).strip()

        if extracted_hno and not house_num:
            house_num = extracted_hno
        surname = title_case_name(extracted_surname)
        forename = extracted_forename
    # 5d. Clean numeric / misplaced building unit numbers in trade (e.g. trade='1', trade='2', trade='1 The Hollies', trade='fitter, 2 Blewitt cot')
    if trade.isdigit():
        if trade == house_num:
            trade = ""
        elif not house_num:
            house_num = trade
            trade = ""
        else:
            bldg_name = title_case_name(f"{trade} {bldg_name}".strip()) if bldg_name else bldg_name
            trade = ""
    else:
        m_num_villa_trade = re.search(r'^(?:(.*?),\s*)?(\d+\s+[A-Za-z\s\x27\-]*?\b(?:villa|villas|cottage|cottages|cot|place|house|terrace|view|chambers|buildings?|inn|hotel|lodge|hall)\b[A-Za-z\s]*)$', trade, re.I)
        if m_num_villa_trade:
            extra_t = (m_num_villa_trade.group(1) or "").strip()
            extracted_bldg = m_num_villa_trade.group(2).strip()
            bldg_name = title_case_name(f"{extracted_bldg} {bldg_name}".strip()) if bldg_name else title_case_name(extracted_bldg)
            trade = extra_t

    if "St. Marks Vicarage" in trade or "St. Mark's Vicarage" in trade:
        bldg_name = "St. Mark's Vicarage"
        trade = re.sub(r'[\s,]*St\.\s*Marks?\s*Vicarage', '', trade, flags=re.I).strip(" ,.-")

    if "bryn tegid" in trade.lower():
        bldg_name = "Bryn Tegid"
        trade = re.sub(r'[\s,]*bryn\s+tegid', '', trade, flags=re.I).strip(" ,.-")
        if trade.lower() == "ladies school":
            trade = "Ladies School"

    # 6. Extract building/villa names from trade or forename (e.g. trade='Stow gate villa', forename='R. H. Belmont villa')
    if not bldg_name:
        v_match_f = VILLA_WORD.search(forename)
        if v_match_f and not any(w in forename.lower() for w in ['customs', 'commercial', 'auctioneer', 'draper']):
            bldg_name = title_case_name(v_match_f.group(1))
            forename = forename.replace(v_match_f.group(1), '').strip()

        v_match_t = VILLA_WORD.search(trade)
        if v_match_t and not any(w in trade.lower() for w in ['customs', 'commercial', 'auctioneer', 'house,', 'estate', 'repairer']):
            bldg_name = title_case_name(v_match_t.group(1))
            trade = trade.replace(v_match_t.group(1), '').strip()

    # 7. Extract telephone numbers misparsed into house_number column (e.g. 45876, 41609)
    if house_num.isdigit() and (int(house_num) >= 40000 or (int(house_num) >= 1000 and street != "Corporation Road")):
        tel_num = house_num
        house_num = ""
        # Restore known house numbers if applicable
        if "King's Head" in trade or "King's Head" in surname:
            house_num = "1"
        elif "WE Evans" in surname or "W. E. Evans" in surname:
            house_num = "12-13"
        elif "Burton" in surname:
            house_num = "31-33"
        
        if f"Tel. {tel_num}" not in trade:
            trade = f"{trade} (Tel. {tel_num})".strip()

    # 8. Fix split ampersand forenames (e.g. surname='Dutfield', forename='& Frost' -> surname='Dutfield & Frost')
    if forename.startswith("& "):
        surname = f"{surname} {forename}".strip()
        forename = ""

    # 9. Fix building_name that contains house number and resident name (e.g. '35-35A Smith W. H. & Son')
    if bldg_name:
        match_b_num = re.match(r"^(\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?)\s*(.*)$", bldg_name)
        if match_b_num:
            ext_num = match_b_num.group(1).upper()
            rest_name = match_b_num.group(2).strip()
            if not house_num:
                house_num = ext_num
            elif house_num != ext_num and not house_num.endswith(ext_num):
                house_num = f"{house_num}-{ext_num}"
            bldg_name = ""
            if rest_name:
                surname = f"{rest_name} {surname}".strip()

    # 10. Extract house numbers merged into surname or forename (e.g. '35a &', '35A Smith W. H. & Son Ltd.')
    match_s_num = re.match(r"^(\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?)\s*(?:&|\s)\s*(.*)$", surname)
    if match_s_num:
        ext_num = match_s_num.group(1).upper()
        surname = match_s_num.group(2).strip()
        if house_num and house_num != ext_num and not house_num.endswith(ext_num):
            house_num = f"{house_num}-{ext_num}"
        elif not house_num:
            house_num = ext_num

    match_f_num = re.match(r"^(\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?)\s*(?:&|\s)\s*(.*)$", forename)
    if match_f_num:
        ext_num = match_f_num.group(1).upper()
        forename = match_f_num.group(2).strip()
        if house_num and house_num != ext_num and not house_num.endswith(ext_num):
            house_num = f"{house_num}-{ext_num}"
        elif not house_num:
            house_num = ext_num

    # 11. Fix bad ampersand surname rows (e.g. surname='&', forename='13 Evans W. E. & Co.')
    if surname == "&" and forename:
        match = re.match(r"^(\d+(?:-\d+)?)\s+(.*)$", forename)
        if match:
            house_num = match.group(1)
            forename = match.group(2)
        parts = forename.split(" ", 1)
        if len(parts) == 2:
            surname = parts[0]
            forename = f"{parts[1]} &"

    # 12. Handle surnames ending with Ltd / Co (e.g. surname='Dean Ltd', forename='John H' -> surname='John H Dean Ltd', forename='')
    corp_match = re.match(r"^(.*?)\s+(Ltd\.?|Co\.?|& Co\.?|Co\.? Ltd\.?)$", surname, re.I)
    if corp_match and forename and not re.match(r"^\d", forename):
        base_s = corp_match.group(1)
        corp_suf = corp_match.group(2)
        is_person = re.match(r"^[A-Z][a-zA-Z\.]*(?:\s+[A-Z][a-zA-Z\.]*)*$", forename) and not any(w in forename.lower() for w in NON_PERSON_WORDS)
        if is_person:
            surname = f"{forename} {base_s} {corp_suf}".strip()
            forename = ""
        else:
            surname = f"{base_s} {corp_suf}".strip()
            forename = ""

    # 13. Fix cases where forename is initials and surname contains company suffix (e.g. surname='Lovell & Co Ltd', forename='GF')
    if forename and re.match(r"^[A-Z]\.?(?:\s*[A-Z]\.?)*$", forename) and re.search(r"\b(&|ltd|limited|co|company|sons|bros|brothers)\b", surname, re.I):
        surname = f"{forename} {surname}".strip()
        forename = ""

    # 14. Handle location-suffix forenames (e.g. surname='Bollom', forename='of Bristol' -> 'Bollom of Bristol')
    if re.match(r"^of\s+[A-Za-z]", forename, re.I):
        surname = f"{surname} {forename}".strip()
        forename = ""

    # 15. Handle initials + company suffix forenames (e.g. surname='Lovell', forename='GF & Co Ltd' -> surname='GF Lovell & Co Ltd', forename='')
    init_biz_match = re.match(r"^([A-Z]\.?(?:\s*[A-Z]\.?)*)\s+(&(?:.*)|ltd.*|co.*|sons.*|bros.*|limited.*)$", forename, re.I)
    if init_biz_match:
        initials = init_biz_match.group(1).strip()
        biz_suffix = init_biz_match.group(2).strip()
        surname = f"{initials} {surname} {biz_suffix}".strip()
        forename = ""

    # 16. Handle hyphenated trade trapped in forename (e.g. '& Son - cycle factors')
    if " - " in forename:
        parts = forename.split(" - ", 1)
        forename = parts[0].strip()
        extra_trade = parts[1].strip()
        trade = f"{extra_trade}, {trade}".strip(", ") if trade else extra_trade

    # 17. Fix pure business / organization name ordering (e.g. 'Taylor' + '& Son' -> 'Taylor & Son')
    if forename and BUSINESS_SUFFIX_REGEX.search(forename.strip()):
        surname = title_case_name(f"{surname} {forename}".strip())
        forename = ""

    # 18. Extract middle initials trapped in trade (e.g. 'T. mechanic')
    if trade:
        initial_match = re.match(r"^([A-Z]\.)\s+(.*)$", trade)
        if initial_match:
            mid_init = initial_match.group(1)
            trade = initial_match.group(2)
            forename = f"{forename} {mid_init}".strip()

    # 19. Expand Journeyman (j.) / (j) tags
    if "(j.)" in forename.lower() or "(j)" in forename.lower() or "(j.)" in trade.lower() or "(j)" in trade.lower():
        forename = re.sub(r"\s*\([jJ]\.?\)\s*", " ", forename).strip()
        if "(j.)" in trade.lower() or "(j)" in trade.lower():
            trade = re.sub(r"\s*\([jJ]\.?\)\s*", " Journeyman ", trade).strip()
        else:
            trade = f"Journeyman {trade}".strip()

    # 20. Split remaining trades trapped in forenames
    if forename:
        match = re.match(r"^(.*?)\s+([a-z].*)$", forename)
        if match:
            f_part = match.group(1).strip()
            t_part = match.group(2).strip()
            if any(kw in t_part.lower() for kw in TRADE_KEYWORDS) or t_part.startswith("("):
                forename = f_part
                trade = f"{t_part}, {trade}".strip(", ") if trade else t_part

    # 21. Fix non-trade values (company suffixes, house names, forenames, titles, initials, trapped resident names) misparsed into trade column
    if trade:
        if surname in {'&', 'and'} and forename.isdigit() and ',' in trade:
            house_num = f"{house_num}-{forename}".strip("-") if house_num else forename
            surname = ""
            forename = ""
        elif surname in {'&', 'and'} and ',' in trade:
            surname = ""

        # 21a. Extract full name + trade + institution (e.g. "Hitchings, G, steward, Coronation Club & Working Men's Institute")
        m_full = PAT_FULL_CORONATION.match(trade)
        if m_full:
            s_part, fn_part, trade_part, inst_part = m_full.groups()
            if s_part:
                surname = s_part.strip()
            if fn_part:
                forename = fn_part.strip()
            trade = trade_part.strip()
            if not bldg_name or bldg_name == f"{surname} {forename}".strip():
                bldg_name = inst_part.strip()

        # 21b. Extract trapped name + trade (e.g. "Poole, Henry - painter", "Limbrick, Percival Cliff - fish merchant", "Price, Benj")
        else:
            m_name = PAT_NAME_TRADE.match(trade)
            if m_name:
                s_part, fn_part, trade_part = m_name.groups()
                if surname and not bldg_name and surname not in {'&', 'and'}:
                    bldg_name = f"{surname} {forename}".strip()
                surname = s_part.strip()
                forename = fn_part.strip()
                trade = trade_part.strip() if trade_part else ""

                m_sub = PAT_TRADE_INST.match(trade) if trade else None
                if m_sub:
                    sub_trade, sub_inst = m_sub.groups()
                    trade = sub_trade.strip()
                    if not bldg_name or bldg_name == f"{surname} {forename}".strip():
                        bldg_name = sub_inst.strip()

            # 21c. Extract trade + institution (e.g. "steward, Coronation Club & Working Men's Institute", "agent, Powell Duffryn Steam Coal Co")
            else:
                m_inst = PAT_TRADE_INST.match(trade)
                if m_inst:
                    trade_part, inst_part = m_inst.groups()
                    trade = trade_part.strip()
                    if not bldg_name:
                        bldg_name = inst_part.strip()

        # 21c2. Extract trade merged with Villa Name (e.g. "fitter, Springfield", "secretary., Font Burn", "accountant, Harlesden")
        if trade:
            m_tv = PAT_TRADE_VILLA.match(trade)
            if m_tv:
                trade_part, villa_part = m_tv.groups()
                trade_part = trade_part.strip(' .,-')
                villa_part = villa_part.strip(' .,-')
                v_low = villa_part.lower()

                if is_trade_word(trade_part) and villa_part[0].isupper() and len(villa_part) < 40 and not any(nw in v_low for nw in NON_VILLA_WORDS):
                    if any(vw in v_low for vw in VILLA_WORDS) or re.match(r'^[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?$', villa_part):
                        trade = trade_part
                        if not bldg_name:
                            bldg_name = villa_part

        # 21c3. Extract trailing house/building name attached to trade (e.g. "fish merch., High Bank")
        if trade and ("," in trade or " - " in trade):
            m_trail = re.search(r'[\-,]\s*([A-Z][a-zA-Z\s\x27\-]+?\b(?:villa|cottage|house|inn|arms|hotel|chambers|lodge|court|hall|chapel|bank|nook|grove|oaks|limes|firs|laurels|knoll|bungalow|ferns|gables|mount|view|haven|lawn|dingle))\s*$', trade, re.I)
            if m_trail:
                trail_bldg = m_trail.group(1).strip()
                trade = trade[:m_trail.start()].strip(" ,-")
                if not bldg_name:
                    bldg_name = title_case_name(trail_bldg)

        # 21c4. Programmatically move trapped Villa / House names from trade to building_name
        # (e.g. Morthoe, Arbaland, Jpgwyniryn, Caerews, Wembley, Glenbrook, Ridgebourn, Wimborne, St Deniols, Linda Vista, Clevedon V, Hampton V, Helston Vil, Brinley Ho., Cartref, etc.)
        if trade and trade[0].isupper() and not is_trade_word(trade) and not is_person_name_or_title(trade):
            t_low = trade.lower().strip(' ,.-')
            if t_low not in {'g.w.r.', 'g.p.o.', 'p.o.', 'p.c.', 'jp', 'post office', 'general post office', 'hmc', 'h.m.c.', 'customs', 'royal oak'} and not re.search(r'\b(g\.?w\.?r\.?|g\.?p\.?o\.?|p\.?o\.?|p\.?c\.?|j\.?p\.?)\b', t_low):
                if not CROSS_STREET_REGEX.search(trade) and not re.search(r'\b(?:ltd|limited|co|company|works|docks|depot|stores|factory|association|society|hospital|asylum|school|schools|station|railway)\b', t_low) and not re.search(r'\d{2,}', trade) and len(trade) <= 45:
                    if re.search(r'\b(?:villa|villas|vil|v|cottage|cottages|cott|house|ho|inn|arms|hotel|chambers|chamb|cham|lodge|lod|court|hall|chapel|bank|nook|grove|oaks|limes|firs|laurels|knoll|bungalow|ferns|gables|mount|view|haven|lawn|dingle|burn|park|croft)\.?$', t_low) or (1 <= len(t_low.split()) <= 3 and all(w[0].isalpha() for w in t_low.split())):
                        if not bldg_name:
                            bldg_name = title_case_name(trade)
                        trade = ""

        # 21c5. Extract Person Forename/Initials attached via dash to trade
        # (e.g. "Clifford - Carpenter", "Arthur F - Traveller", "Ivor S - Painter", "Walter Hs - Motor Engineer", "Wf - Great Western Railway")
        if trade and "-" in trade:
            m_ndt = re.match(r'^\s*([A-Za-z\.\s]+?)\s*[\-\–]\s*(.*)$', trade)
            if m_ndt:
                left_n = m_ndt.group(1).strip()
                right_t = m_ndt.group(2).strip()

                if left_n and right_t and not is_trade_word(left_n.lower()) and left_n.lower() not in {'surgeon', 'ex', 'holder', 'brewers', 'corn stores', 'docks'}:
                    if is_person_name_or_title(left_n) or (1 <= len(left_n.split()) <= 3 and all(w.lower() in TITLES_AND_FORENAMES or len(w.strip('.')) <= 3 or w[0].isupper() for w in left_n.split())):
                        if forename:
                            forename = f"{forename} {left_n}".strip()
                        else:
                            forename = left_n
                        trade = right_t

        # 21c6. Handle standalone "etc." or "&c." trade entries where occupation is trapped in forename
        # (e.g. forename="L. pawnbroker", trade="etc." -> forename="L.", trade="pawnbroker, etc.")
        if trade and trade.lower().strip(' ,.-') in {'etc', '&c'}:
            if forename and ' ' in forename:
                tokens = forename.split()
                fn_tokens = []
                trade_tokens = []
                for tok in tokens:
                    clean_tok = tok.strip('.,')
                    if clean_tok.lower() in TITLES_AND_FORENAMES or (len(clean_tok) <= 3 and clean_tok[0].isupper()):
                        if not trade_tokens:
                            fn_tokens.append(tok)
                        else:
                            trade_tokens.append(tok)
                    else:
                        trade_tokens.append(tok)
                if trade_tokens:
                    forename = " ".join(fn_tokens)
                    trade = f"{' '.join(trade_tokens)}, etc."

        # 21d. Company Suffix in trade
        if trade and COMPANY_SUFFIX_TRADE_REGEX.match(trade):
            if forename:
                surname = f"{forename} {surname} {trade}".strip()
                forename = ""
            else:
                surname = f"{surname} {trade}".strip()
            trade = ""

        # 21b. Building Name in trade
        elif BUILDING_NAME_TRADE_REGEX.match(trade):
            if not bldg_name:
                bldg_name = trade
            trade = ""

        # 21c. Shifted house name in surname + surname in forename + forename/initials in trade
        elif (is_person_name_or_title(trade) or not trade) and forename and (HOUSE_SUFX.search(surname) or surname in {'Cartref', 'Wynberg', 'Hollybush', 'Arendal', 'Ceinfan', 'Lavengro', 'Blue House Cottage Taylor', 'Belmont House Hilton'}):
            if not bldg_name:
                bldg_name = surname
            surname = forename
            forename = trade
            trade = ""

        # 21d. Person name / title / initials in trade
        elif is_person_name_or_title(trade):
            if not surname and forename:
                surname = forename
                forename = trade
                trade = ""
            elif surname and not forename:
                forename = trade
                trade = ""
            elif surname and forename:
                forename = f"{forename} {trade}".strip()
                trade = ""

        # 21e. Person prefix in trade with embedded trade (e.g. 'Mrs Mary S - fruiterer')
        elif re.match(r'^(mrs|miss|mr)\.?\s+([A-Za-z\.\s]+)\s*[\-,]\s*(.*)$', trade, re.I):
            m = re.match(r'^(mrs|miss|mr)\.?\s+([A-Za-z\.\s]+)\s*[\-,]\s*(.*)$', trade, re.I)
            person_part = f"{m.group(1)} {m.group(2)}".strip()
            real_trade = m.group(3).strip()
            if forename:
                forename = f"{forename} ({person_part})"
            else:
                forename = person_part
            trade = real_trade

        # 21f. Normalize trade abbreviations
        if trade:
            if re.search(r'\bg[\.\s]*w[\.\s]*r', trade, re.I):
                trade = re.sub(r'\bG[\.\s]*W[\.\s]*R[\.\s]*', 'G.W.R. ', trade, flags=re.I)
                trade = re.sub(r'G\.W\.R\.\s*[\.,]+', 'G.W.R. ', trade)
                trade = re.sub(r'\s+', ' ', trade).strip()
                trade = re.sub(r'G\.W\.R\.\s*$', 'G.W.R.', trade)
            if re.search(r'\birnwrkr\b', trade, re.I):
                trade = re.sub(r'\birnwrkr\b', 'Ironworker', trade, flags=re.I)
            if re.search(r'\bboot\s+repr\b', trade, re.I):
                trade = re.sub(r'\bboot\s+repr\b', 'Boot Repairer', trade, flags=re.I)
            if re.search(r'\bmtr\s+driver\b', trade, re.I):
                trade = re.sub(r'\bmtr\s+driver\b', 'Motor Driver', trade, flags=re.I)
            if re.search(r'\blabrer\b', trade, re.I):
                trade = re.sub(r'\blabrer\b', 'Labourer', trade, flags=re.I)
            if re.search(r'\btravlr\b', trade, re.I):
                trade = re.sub(r'\btravlr\b', 'Traveller', trade, flags=re.I)
            if re.search(r'\bmachnst\b', trade, re.I):
                trade = re.sub(r'\bmachnst\b', 'Machinist', trade, flags=re.I)
            if re.search(r'\bcaretkr\b', trade, re.I):
                trade = re.sub(r'\bcaretkr\b', 'Caretaker', trade, flags=re.I)
            if re.search(r'\belectcn\b', trade, re.I):
                trade = re.sub(r'\belectcn\b', 'Electrician', trade, flags=re.I)
            if re.search(r'\binsur\.?\s+agent\b', trade, re.I) or re.search(r'\bins\.?\s+agent\b', trade, re.I):
                trade = re.sub(r'\b(insur|ins)\.?\s+agent\b', 'Insurance Agent', trade, flags=re.I)
            if re.search(r'\blorry\s+(drvr|dr)\b', trade, re.I):
                trade = re.sub(r'\blorry\s+(drvr|dr)\b', 'Lorry Driver', trade, flags=re.I)
            if re.search(r'\birn\s+worker\b', trade, re.I):
                trade = re.sub(r'\birn\s+worker\b', 'Iron Worker', trade, flags=re.I)
            if re.search(r'\bstorekpr\b', trade, re.I):
                trade = re.sub(r'\bstorekpr\b', 'Storekeeper', trade, flags=re.I)
            if re.search(r'\bcoal\s+trimr\b', trade, re.I):
                trade = re.sub(r'\bcoal\s+trimr\b', 'Coal Trimmer', trade, flags=re.I)
            if re.search(r'\bgreengrcr\b', trade, re.I):
                trade = re.sub(r'\bgreengrcr\b', 'Greengrocer', trade, flags=re.I)
            if re.search(r'\bbootmkr\b', trade, re.I):
                trade = re.sub(r'\bbootmkr\b', 'Bootmaker', trade, flags=re.I)
            if re.search(r'\bblksmith\b', trade, re.I):
                trade = re.sub(r'\bblksmith\b', 'Blacksmith', trade, flags=re.I)
            if re.search(r'\bmotor\s+mech\b', trade, re.I):
                trade = re.sub(r'\bmotor\s+mech\b', 'Motor Mechanic', trade, flags=re.I)
            if re.search(r'\bshop\s+asst\b', trade, re.I):
                trade = re.sub(r'\bshop\s+asst\b', 'Shop Assistant', trade, flags=re.I)
            if re.search(r'\bwatchmkr\b', trade, re.I):
                trade = re.sub(r'\bwatchmkr\b', 'Watchmaker', trade, flags=re.I)
            if re.search(r'\bengine\s+(drvr|drivr)\b', trade, re.I):
                trade = re.sub(r'\bengine\s+(drvr|drivr)\b', 'Engine Driver', trade, flags=re.I)
            if re.search(r'\bcranedvr\b', trade, re.I):
                trade = re.sub(r'\bcranedvr\b', 'Cranedriver', trade, flags=re.I)
            if re.search(r'\bstlwrkr\b', trade, re.I):
                trade = re.sub(r'\bstlwrkr\b', 'Steelworker', trade, flags=re.I)
            if re.search(r'\b(ironwrkr|ironworkr|iworker|irn\s+worker)\b', trade, re.I):
                trade = re.sub(r'\b(ironwrkr|ironworkr|iworker|irn\s+worker)\b', 'Ironworker', trade, flags=re.I)

            # Acronym dot cleanups
            if re.search(r'\bg[\.\s]*p[\.\s]*o', trade, re.I):
                trade = re.sub(r'\bG[\.\s]*P[\.\s]*O[\.\s]*', 'G.P.O. ', trade, flags=re.I)
                trade = re.sub(r'G\.P\.O\.\s*[\.,]+', 'G.P.O. ', trade)
                trade = re.sub(r'\s+', ' ', trade).strip()
                trade = re.sub(r'G\.P\.O\.\s*$', 'G.P.O.', trade)

            if re.search(r'\bp[\.\s]*o\b', trade, re.I) and not re.search(r'g\.?p\.?o', trade, re.I):
                trade = re.sub(r'\bP[\.\s]*O[\.\s]*', 'P.O. ', trade, flags=re.I)
                trade = re.sub(r'P\.O\.\s*[\.,]+', 'P.O. ', trade)
                trade = re.sub(r'\s+', ' ', trade).strip()
                trade = re.sub(r'P\.O\.\s*$', 'P.O.', trade)

            if re.search(r'\bp[\.\s]*c\b', trade, re.I):
                trade = re.sub(r'\bP[\.\s]*C[\.\s]*', 'P.C. ', trade, flags=re.I)
                trade = re.sub(r'P\.C\.\s*[\.,]+', 'P.C. ', trade)
                trade = re.sub(r'\s+', ' ', trade).strip()
                trade = re.sub(r'P\.C\.\s*$', 'P.C.', trade)

            if re.search(r'\bj[\.\s]*p\b', trade, re.I):
                trade = re.sub(r'\bJ[\.\s]*P[\.\s]*', 'JP ', trade, flags=re.I)
                trade = re.sub(r'JP\s*[\.,]+', 'JP ', trade)
                trade = re.sub(r'\s+', ' ', trade).strip()
                trade = re.sub(r'JP\s*$', 'JP', trade)

            if re.search(r'\b(eng\.?\s+driver|engine\s+(drvr|drivr))\b', trade, re.I):
                trade = re.sub(r'\b(eng\.?\s+driver|engine\s+(drvr|drivr))\b', 'Engine Driver', trade, flags=re.I)
            if re.search(r'\b(engnr|engr)\b', trade, re.I):
                trade = re.sub(r'\b(engnr|engr)\b', 'Engineer', trade, flags=re.I)
            if re.search(r'\bgov\.?\s+offcl\b', trade, re.I):
                trade = re.sub(r'\bgov\.?\s+offcl\b', 'Government Official', trade, flags=re.I)
            if re.search(r'\bdk\s+police\b', trade, re.I):
                trade = re.sub(r'\bdk\s+police\b', 'Dock Police', trade, flags=re.I)
            if re.search(r'\bldg\s+ho\b', trade, re.I):
                trade = re.sub(r'\bldg\s+ho\b', 'Lodging House', trade, flags=re.I)
            if re.search(r'\bdrapers\s+collctr\b', trade, re.I):
                trade = re.sub(r'\bdrapers\s+collctr\b', 'Drapers Collector', trade, flags=re.I)
            if re.search(r'\bgas\s+inspct\b', trade, re.I):
                trade = re.sub(r'\bgas\s+inspct\b', 'Gas Inspector', trade, flags=re.I)
            if re.search(r'\bblrmr\b', trade, re.I):
                trade = re.sub(r'\bblrmr\b', 'Boilermaker', trade, flags=re.I)
            if re.search(r'\bcustom\s+offr\b', trade, re.I):
                trade = re.sub(r'\bcustom\s+offr\b', 'Custom Officer', trade, flags=re.I)
            if re.search(r'\bglass\s+(wrkr|wk)\b', trade, re.I):
                trade = re.sub(r'\bglass\s+(wrkr|wk)\b', 'Glass Worker', trade, flags=re.I)
            if re.search(r'\bice\s+cream\s+vendr\b', trade, re.I):
                trade = re.sub(r'\bice\s+cream\s+vendr\b', 'Ice Cream Vendor', trade, flags=re.I)
            if re.search(r'\bcoal\s+tipr\b', trade, re.I):
                trade = re.sub(r'\bcoal\s+tipr\b', 'Coal Tipper', trade, flags=re.I)
            if re.search(r'\bdentst\b', trade, re.I):
                trade = re.sub(r'\bdentst\b', 'Dentist', trade, flags=re.I)
            if re.search(r'\bbus\s+drvi\b', trade, re.I):
                trade = re.sub(r'\bbus\s+drvi\b', 'Bus Driver', trade, flags=re.I)
            if re.search(r'\bwagon\s+rp\b', trade, re.I):
                trade = re.sub(r'\bwagon\s+rp\b', 'Wagon Repairer', trade, flags=re.I)
            if re.search(r'\b(electcn|electrn|elect|elct)\b', trade, re.I) and not re.search(r'\belectrician\b', trade, re.I):
                trade = re.sub(r'\b(electcn|electrn|elect|elct)\b', 'Electrician', trade, flags=re.I)
            if re.search(r'\bflour\s+packr\b', trade, re.I):
                trade = re.sub(r'\bflour\s+packr\b', 'Flour Packer', trade, flags=re.I)
            if re.search(r'\broad\s+swp\b', trade, re.I):
                trade = re.sub(r'\broad\s+swp\b', 'Road Sweeper', trade, flags=re.I)
            if re.search(r'\b(ironwor|ironwrkr|ironworkr|iworker|irn\s+worker)\b', trade, re.I):
                trade = re.sub(r'\b(ironwor|ironwrkr|ironworkr|iworker|irn\s+worker)\b', 'Ironworker', trade, flags=re.I)
            if re.search(r'\bbuilding\s+contr\s*&\s*engnrs\b', trade, re.I):
                trade = re.sub(r'\bbuilding\s+contr\s*&\s*engnrs\b', 'Building Contractors and Engineers', trade, flags=re.I)
            if re.search(r'\bsales\s+drvr\b', trade, re.I):
                trade = re.sub(r'\bsales\s+drvr\b', 'Sales Driver', trade, flags=re.I)
            if re.search(r'\btbeworker\b', trade, re.I):
                trade = re.sub(r'\btbeworker\b', 'Tubeworker', trade, flags=re.I)
            if re.search(r'\bshoe\s+repr\b', trade, re.I):
                trade = re.sub(r'\bshoe\s+repr\b', 'Shoe Repairer', trade, flags=re.I)
            if re.search(r'\bsteehvorkr\b', trade, re.I):
                trade = re.sub(r'\bsteehvorkr\b', 'Steelworker', trade, flags=re.I)
            if re.search(r'\bcrane\s+dr\b', trade, re.I):
                trade = re.sub(r'\bcrane\s+dr\b', 'Crane Driver', trade, flags=re.I)
            if re.search(r'\belec\s+engineer\b', trade, re.I):
                trade = re.sub(r'\belec\s+engineer\b', 'Electrical Engineer', trade, flags=re.I)
            if re.search(r'\bstl\s+worker\b', trade, re.I):
                trade = re.sub(r'\bstl\s+worker\b', 'Steel Worker', trade, flags=re.I)
            if re.search(r'\bmotor\s+(drvr|dr)\b', trade, re.I):
                trade = re.sub(r'\bmotor\s+(drvr|dr)\b', 'Motor Driver', trade, flags=re.I)
            if re.search(r'\bins\s+agt\b', trade, re.I):
                trade = re.sub(r'\bins\s+agt\b', 'Insurance Agent', trade, flags=re.I)
            if re.search(r'\bpostmn\b', trade, re.I):
                trade = re.sub(r'\bpostmn\b', 'Postman', trade, flags=re.I)
            if re.search(r'\bcivil\s+serv(t|nt)\b', trade, re.I):
                trade = re.sub(r'\bcivil\s+serv(t|nt)\b', 'Civil Servant', trade, flags=re.I)
            if re.search(r'\bdk\s+worker\b', trade, re.I):
                trade = re.sub(r'\bdk\s+worker\b', 'Dock Worker', trade, flags=re.I)
            if re.search(r'\btrmr\b', trade, re.I) and not re.search(r'trimmer', trade, re.I):
                trade = re.sub(r'\btrmr\b', 'Trimmer', trade, flags=re.I)
            if re.search(r'\bbricklayr\b', trade, re.I):
                trade = re.sub(r'\bbricklayr\b', 'Bricklayer', trade, flags=re.I)
            if re.search(r'\bsupt\.?\b', trade, re.I) and not re.search(r'superintendent', trade, re.I):
                trade = re.sub(r'\bsupt\.?\b', 'Superintendent', trade, flags=re.I)
            if re.search(r'\bupholstr\b', trade, re.I):
                trade = re.sub(r'\bupholstr\b', 'Upholsterer', trade, flags=re.I)
            if re.search(r'\bloco\s+driver\b', trade, re.I):
                trade = re.sub(r'\bloco\s+driver\b', 'Locomotive Driver', trade, flags=re.I)
            if re.search(r'\bclrk\b', trade, re.I):
                trade = re.sub(r'\bclrk\b', 'Clerk', trade, flags=re.I)
            if re.search(r'\b(steelworkr|steehvorkr|stlwrkr)\b', trade, re.I):
                trade = re.sub(r'\b(steelworkr|steehvorkr|stlwrkr)\b', 'Steelworker', trade, flags=re.I)
            if re.search(r'\bship\s+brkr\b', trade, re.I):
                trade = re.sub(r'\bship\s+brkr\b', 'Ship Broker', trade, flags=re.I)
            if re.search(r'\bfitters\s+hlpr\b', trade, re.I):
                trade = re.sub(r'\bfitters\s+hlpr\b', 'Fitters Helper', trade, flags=re.I)
            if re.search(r'\beng\s+dr\b', trade, re.I):
                trade = re.sub(r'\beng\s+dr\b', 'Engine Driver', trade, flags=re.I)
            if re.search(r'\b(trvlr|travlr)\b', trade, re.I):
                trade = re.sub(r'\b(trvlr|travlr)\b', 'Traveller', trade, flags=re.I)
            if re.search(r'\bmarbl\s+polshr\b', trade, re.I):
                trade = re.sub(r'\bmarbl\s+polshr\b', 'Marble Polisher', trade, flags=re.I)
            if re.search(r'\bcab\s+proprtr\b', trade, re.I):
                trade = re.sub(r'\bcab\s+proprtr\b', 'Cab Proprietor', trade, flags=re.I)
            if re.search(r'\bmonu\.?\s+mason\b', trade, re.I):
                trade = re.sub(r'\bmonu\.?\s+mason\b', 'Monumental Mason', trade, flags=re.I)
            if re.search(r'\brailwymn\b', trade, re.I):
                trade = re.sub(r'\brailwymn\b', 'Railwayman', trade, flags=re.I)
            if re.search(r'\brly\s+foreman\b', trade, re.I):
                trade = re.sub(r'\brly\s+foreman\b', 'Railway Foreman', trade, flags=re.I)
            if re.search(r'\brly\s+inspt\b', trade, re.I):
                trade = re.sub(r'\brly\s+inspt\b', 'Railway Inspector', trade, flags=re.I)
            if re.search(r'\btram\s+inspt\b', trade, re.I):
                trade = re.sub(r'\btram\s+inspt\b', 'Tram Inspector', trade, flags=re.I)
            if re.search(r'\binspt\b', trade, re.I) and not re.search(r'inspector', trade, re.I):
                trade = re.sub(r'\binspt\b', 'Inspector', trade, flags=re.I)
            if re.search(r'\bironw6rker\b', trade, re.I):
                trade = re.sub(r'\bironw6rker\b', 'Ironworker', trade, flags=re.I)
            if re.search(r'\bgeneral\s+grocr\b', trade, re.I):
                trade = re.sub(r'\bgeneral\s+grocr\b', 'General Grocer', trade, flags=re.I)
            if re.search(r'\blaborr\b', trade, re.I):
                trade = re.sub(r'\blaborr\b', 'Labourer', trade, flags=re.I)
            if re.search(r'\bpier\s+mastr\b', trade, re.I):
                trade = re.sub(r'\bpier\s+mastr\b', 'Pier Master', trade, flags=re.I)
            if re.search(r'\bhouse\s+fur\b', trade, re.I):
                trade = re.sub(r'\bhouse\s+fur\b', 'House Furnisher', trade, flags=re.I)
            if re.search(r'\bhatter\s*,\s*,\s*etc\b', trade, re.I):
                trade = re.sub(r'\bhatter\s*,\s*,\s*etc\b', 'Hatter, etc.', trade, flags=re.I)
            if re.search(r'\bboot\s+manuftrs\b', trade, re.I):
                trade = re.sub(r'\bboot\s+manuftrs\b', 'Boot Manufacturers', trade, flags=re.I)
            if re.search(r'\bphotogrpr\b', trade, re.I):
                trade = re.sub(r'\bphotogrpr\b', 'Photographer', trade, flags=re.I)
            if re.search(r'\bmotormn\b', trade, re.I):
                trade = re.sub(r'\bmotormn\b', 'Motorman', trade, flags=re.I)
            if re.search(r'\btug\s+drvr\b', trade, re.I):
                trade = re.sub(r'\btug\s+drvr\b', 'Tug Driver', trade, flags=re.I)
            if re.search(r'\belec\.?\s+eng\b', trade, re.I) and not re.search(r'electrical engineer', trade, re.I):
                trade = re.sub(r'\belec\.?\s+eng\b', 'Electrical Engineer', trade, flags=re.I)
            if re.search(r'\bcoachmn\b', trade, re.I):
                trade = re.sub(r'\bcoachmn\b', 'Coachman', trade, flags=re.I)
            if re.search(r'\brway\s+ganger\b', trade, re.I):
                trade = re.sub(r'\brway\s+ganger\b', 'Railway Ganger', trade, flags=re.I)
            if re.search(r'\beng\.?\s+drvr\.?\s+g\.?w\.?r\.?\b', trade, re.I):
                trade = re.sub(r'\beng\.?\s+drvr\.?\s+g\.?w\.?r\.?\b', 'Engine Driver G.W.R.', trade, flags=re.I)
            if re.search(r'\bwoodtrnr\b', trade, re.I):
                trade = re.sub(r'\bwoodtrnr\b', 'Woodturner', trade, flags=re.I)
            if re.search(r'\btel\.?\s+clerk\b', trade, re.I):
                trade = re.sub(r'\btel\.?\s+clerk\b', 'Telephone Clerk', trade, flags=re.I)
            if re.search(r'\bstrkr\b', trade, re.I):
                trade = re.sub(r'\bstrkr\b', 'Striker', trade, flags=re.I)
            if re.search(r'\b(l;ab|labour[\x27\x22\x60]?r)\b', trade, re.I):
                trade = re.sub(r'\b(l;ab|labour[\x27\x22\x60]?r)\b', 'Labourer', trade, flags=re.I)
            if re.search(r'\btail;ors\b', trade, re.I):
                trade = re.sub(r'\btail;ors\b', 'Tailors', trade, flags=re.I)
            if re.search(r'\bbrewerr\b', trade, re.I):
                trade = re.sub(r'\bbrewerr\b', 'Brewer', trade, flags=re.I)
            if re.search(r'\bprovision\s+merchanty\b', trade, re.I):
                trade = re.sub(r'\bprovision\s+merchanty\b', 'Provision Merchant', trade, flags=re.I)
            if re.search(r'\bglass\s+blr\b', trade, re.I):
                trade = re.sub(r'\bglass\s+blr\b', 'Glassblower', trade, flags=re.I)
            if re.search(r'\btransp[\x27\x22\x60]?t\s+w[\x27\x22\x60]?r\b', trade, re.I):
                trade = re.sub(r'\btransp[\x27\x22\x60]?t\s+w[\x27\x22\x60]?r\b', 'Transport Worker', trade, flags=re.I)
            if re.search(r'\bcr\.?\s*driver\b', trade, re.I):
                trade = re.sub(r'\bcr\.?\s*driver\b', 'Crane Driver', trade, flags=re.I)
            if re.search(r'\btr[\x27\x22\x60]?mmer\b', trade, re.I):
                trade = re.sub(r'\btr[\x27\x22\x60]?mmer\b', 'Trimmer', trade, flags=re.I)
            if re.search(r'\bhse\s+craft\s+mistress\b', trade, re.I):
                trade = re.sub(r'\bhse\s+craft\s+mistress\b', 'House Craft Mistress', trade, flags=re.I)
            if re.search(r'\bcanteen\s+stwd\b', trade, re.I):
                trade = re.sub(r'\bcanteen\s+stwd\b', 'Canteen Steward', trade, flags=re.I)
            if re.search(r'\biron\s*&\s*metal\s+mcht\s+and\s+marine\s+stores\b', trade, re.I):
                trade = re.sub(r'\biron\s*&\s*metal\s+mcht\s+and\s+marine\s+stores\b', 'Iron & Metal Merchant and Marine Stores', trade, flags=re.I)
            if trade.strip().lower() in {'i.w', 'i.w.'}:
                trade = 'Ironworker'
            if re.search(r'\biworker\s*&\s*shop\b', trade, re.I):
                trade = re.sub(r'\biworker\s*&\s*shop\b', 'Ironworker and Shop', trade, flags=re.I)
            if re.search(r'\bnews\s*&\s*hairdr\b', trade, re.I):
                trade = re.sub(r'\bnews\s*&\s*hairdr\b', 'News and Hairdresser', trade, flags=re.I)
            if re.search(r'\bturf\s+acnt\b', trade, re.I):
                trade = re.sub(r'\bturf\s+acnt\b', 'Turf Accountant', trade, flags=re.I)
            if re.search(r'\bauct[\x27\x22\x60]?nr\b', trade, re.I):
                trade = re.sub(r'\bauct[\x27\x22\x60]?nr\b', 'Auctioneer', trade, flags=re.I)
            if re.search(r'\bship\s+firem[\x27\x22\x60]?n\b', trade, re.I):
                trade = re.sub(r'\bship\s+firem[\x27\x22\x60]?n\b', 'Ship Fireman', trade, flags=re.I)
            if re.search(r'\btubewk\b', trade, re.I):
                trade = re.sub(r'\btubewk\b', 'Tubeworker', trade, flags=re.I)
            if re.search(r'\bdock\s+hnd\b', trade, re.I):
                trade = re.sub(r'\bdock\s+hnd\b', 'Dock Hand', trade, flags=re.I)
            if re.search(r'\bsailr\b', trade, re.I):
                trade = re.sub(r'\bsailr\b', 'Sailor', trade, flags=re.I)
            if re.search(r'\bcellrmn\b', trade, re.I):
                trade = re.sub(r'\bcellrmn\b', 'Cellarman', trade, flags=re.I)
            if re.search(r'\bstewrd\b', trade, re.I):
                trade = re.sub(r'\bstewrd\b', 'Steward', trade, flags=re.I)
            if re.search(r'\bplatelayer\]\b', trade, re.I):
                trade = re.sub(r'\bplatelayer\]\b', 'Platelayer', trade, flags=re.I)
            if re.search(r'\bglass\s+blwr\b', trade, re.I):
                trade = re.sub(r'\bglass\s+blwr\b', 'Glassblower', trade, flags=re.I)
            if re.search(r'\bahopkeeper\b', trade, re.I):
                trade = re.sub(r'\bahopkeeper\b', 'Shopkeeper', trade, flags=re.I)
            if re.search(r'\btime\s+kp\b', trade, re.I):
                trade = re.sub(r'\btime\s+kp\b', 'Timekeeper', trade, flags=re.I)
            if re.search(r'\bpump\s+attd?t\b', trade, re.I):
                trade = re.sub(r'\bpump\s+attd?t\b', 'Pump Attendant', trade, flags=re.I)
            if re.search(r'\bcoal\s+tmr\b', trade, re.I):
                trade = re.sub(r'\bcoal\s+tmr\b', 'Coal Trimmer', trade, flags=re.I)
            if re.search(r'\bblksth\b', trade, re.I):
                trade = re.sub(r'\bblksth\b', 'Blacksmith', trade, flags=re.I)
            if re.search(r'\bschool\s+teach\b', trade, re.I):
                trade = re.sub(r'\bschool\s+teach\b', 'School Teacher', trade, flags=re.I)
            if re.search(r'\bshop\s+ft[\x27\x22\x60]?rs\b', trade, re.I):
                trade = re.sub(r'\bshop\s+ft[\x27\x22\x60]?rs\b', 'Shop Fitters', trade, flags=re.I)
            if re.search(r'\binsurnc\s+agt\b', trade, re.I):
                trade = re.sub(r'\binsurnc\s+agt\b', 'Insurance Agent', trade, flags=re.I)
            if re.search(r'\bhead\s+waitr\b', trade, re.I):
                trade = re.sub(r'\bhead\s+waitr\b', 'Head Waiter', trade, flags=re.I)
            if re.search(r'\brailwaymn\b', trade, re.I):
                trade = re.sub(r'\brailwaymn\b', 'Railwayman', trade, flags=re.I)
            if re.search(r'\bbootmkrs\b', trade, re.I):
                trade = re.sub(r'\bbootmkrs\b', 'Bootmakers', trade, flags=re.I)
            if re.search(r'\bgreengrcrs\b', trade, re.I):
                trade = re.sub(r'\bgreengrcrs\b', 'Greengrocers', trade, flags=re.I)
            if re.search(r'\bpolice\s+sgt\b', trade, re.I):
                trade = re.sub(r'\bpolice\s+sgt\b', 'Police Sergeant', trade, flags=re.I)
            if re.search(r'\btobacnst\b', trade, re.I):
                trade = re.sub(r'\btobacnst\b', 'Tobacconist', trade, flags=re.I)
            if re.search(r'\bbuilders\s+yd\b', trade, re.I):
                trade = re.sub(r'\bbuilders\s+yd\b', 'Builders Yard', trade, flags=re.I)
            if re.search(r'\bsecty\b', trade, re.I):
                trade = re.sub(r'\bsecty\b', 'Secretary', trade, flags=re.I)
            if trade.strip().lower() in {'agt', 'agt.'}:
                trade = 'Agent'
            if re.search(r'\bgenl\s+dealer\b', trade, re.I):
                trade = re.sub(r'\bgenl\s+dealer\b', 'General Dealer', trade, flags=re.I)
            if re.search(r'\bcellarmn\b', trade, re.I):
                trade = re.sub(r'\bcellarmn\b', 'Cellarman', trade, flags=re.I)
            if re.search(r'\btravellr\b', trade, re.I):
                trade = re.sub(r'\btravellr\b', 'Traveller', trade, flags=re.I)
            if re.search(r'\bcycle\s+repr\b', trade, re.I):
                trade = re.sub(r'\bcycle\s+repr\b', 'Cycle Repairer', trade, flags=re.I)
            if re.search(r'\benginemn\b', trade, re.I):
                trade = re.sub(r'\benginemn\b', 'Engineman', trade, flags=re.I)
            if re.search(r'\bpipe\s+fittr\b', trade, re.I):
                trade = re.sub(r'\bpipe\s+fittr\b', 'Pipe Fitter', trade, flags=re.I)
            if re.search(r'\bstocktkr\b', trade, re.I):
                trade = re.sub(r'\bstocktkr\b', 'Stocktaker', trade, flags=re.I)
            if re.search(r'\bwheelwgt\b', trade, re.I):
                trade = re.sub(r'\bwheelwgt\b', 'Wheelwright', trade, flags=re.I)
            if re.search(r'\bwardrobe\s+dlr\b', trade, re.I):
                trade = re.sub(r'\bwardrobe\s+dlr\b', 'Wardrobe Dealer', trade, flags=re.I)
            if re.search(r'\bdecor[\x27\x22\x60]?tr\b', trade, re.I):
                trade = re.sub(r'\bdecor[\x27\x22\x60]?tr\b', 'Decorator', trade, flags=re.I)
            if re.search(r'\bboilermk\b', trade, re.I):
                trade = re.sub(r'\bboilermk\b', 'Boilermaker', trade, flags=re.I)
            if re.search(r'\bpltlyr\b', trade, re.I):
                trade = re.sub(r'\bpltlyr\b', 'Platelayer', trade, flags=re.I)
            if re.search(r'\bi[\x27\x22\x60]?wrkr\b', trade, re.I) or re.search(r'\bi[\x27\x22\x60]worker\b', trade, re.I):
                trade = re.sub(r'\bi[\x27\x22\x60]?wrkr\b', 'Ironworker', trade, flags=re.I)
                trade = re.sub(r'\bi[\x27\x22\x60]worker\b', 'Ironworker', trade, flags=re.I)
            if re.search(r'\bfurnacem\b', trade, re.I):
                trade = re.sub(r'\bfurnacem\b', 'Furnaceman', trade, flags=re.I)
            if re.search(r'\bglass\s+wks\b', trade, re.I):
                trade = re.sub(r'\bglass\s+wks\b', 'Glass Works', trade, flags=re.I)
            if re.search(r'\bins\.?\s+superintendent\b', trade, re.I):
                trade = re.sub(r'\bins\.?\s+superintendent\b', 'Insurance Superintendent', trade, flags=re.I)
            if re.search(r'\bgenl\.?\s+shop\b', trade, re.I):
                trade = re.sub(r'\bgenl\.?\s+shop\b', 'General Shop', trade, flags=re.I)
            if re.search(r'\bwatermn\b', trade, re.I):
                trade = re.sub(r'\bwatermn\b', 'Waterman', trade, flags=re.I)
            if re.search(r'\bshoemkr\b', trade, re.I):
                trade = re.sub(r'\bshoemkr\b', 'Shoemaker', trade, flags=re.I)
            if re.search(r'\b(tubewrkr|tbeworker)\b', trade, re.I):
                trade = re.sub(r'\b(tubewrkr|tbeworker)\b', 'Tubeworker', trade, flags=re.I)
            if re.search(r'\bcarpentr\b', trade, re.I):
                trade = re.sub(r'\bcarpentr\b', 'Carpenter', trade, flags=re.I)
            if re.search(r'\bsec\.?\b', trade, re.I) and not trade.lower().startswith('sec.'):
                trade = re.sub(r'\bsec\.?\b', 'Secretary', trade, flags=re.I)
            elif trade.strip().lower() in {'sec', 'sec.'}:
                trade = 'Secretary'
            if re.search(r'\bmech\b', trade, re.I) and not re.search(r'\bmotor\s+mech\b', trade, re.I):
                trade = re.sub(r'\bmech\b', 'Mechanic', trade, flags=re.I)
            if re.search(r'\belectrn\b', trade, re.I):
                trade = re.sub(r'\belectrn\b', 'Electrician', trade, flags=re.I)
            if re.search(r'\s*&\s*c\.?$', trade, re.I):
                trade = re.sub(r'\s*&\s*c\.?$', ', etc.', trade, flags=re.I)

            trade = re.sub(r'([a-zA-Z]{3,})\.\s*$', r'\1', trade)

            t_low = trade.lower()
            if t_low in {'ptr', 'ptr.'}:
                trade = 'painter'
            elif t_low in {'clk', 'clk.'}:
                trade = 'clerk'
            elif t_low in {'dvr', 'dvr.'}:
                trade = 'driver'
            elif t_low in {'trm', 'trm.'}:
                trade = 'trimmer'

    # Standardize G.p.o. / G.p.o / GPO / G.P.O -> G.P.O.
    pat_gpo = re.compile(r'\b(g\.?p\.?o\.?)\b\.?', re.I)
    surname = pat_gpo.sub('G.P.O.', surname)
    forename = pat_gpo.sub('G.P.O.', forename)
    bldg_name = pat_gpo.sub('G.P.O.', bldg_name)
    trade = pat_gpo.sub('G.P.O.', trade)

    # Expand common forename abbreviations (Thos, Wm, Benj, Geo, Chas, Rbt, Robt, Fredk)
    if forename:
        forename = re.sub(r'\bThos?\.?\b', 'Thomas', forename)
        forename = re.sub(r'\bWm\.?\b', 'William', forename)
        forename = re.sub(r'\bBenj\.?\b', 'Benjamin', forename)
        forename = re.sub(r'\bGeo\.?\b', 'George', forename)
        forename = re.sub(r'\bChas\.?\b', 'Charles', forename)
        forename = re.sub(r'\bRobt?\.?\b', 'Robert', forename)
        forename = re.sub(r'\bFredk?\.?\b', 'Frederick', forename)

    # Clean trailing commas, quotes & spaces
    surname = surname.strip(' ,"-~')
    forename = forename.strip(' ,"-~')
    trade = trade.strip(' ,"-~')

    # 21g. Clean 'void' and 'vacant site' property entries
    comb_sv = f"{surname} {forename}".strip().lower()
    if comb_sv in {"vacant site", "site vacant", "vacant sites", "sites vacant", "site (allotments) vacant", "vacant site (allotments)"} or comb_sv.startswith("vacant site") or comb_sv.startswith("site vacant"):
        surname = ""
        forename = ""
        bldg_name = "Vacant Site"

    if trade.lower() in {'void', 'void.'}:
        trade = ""
        if surname and not is_person_name_or_title(surname) and not bldg_name:
            bldg_name = title_case_name(surname)
            surname = ""

    if surname.lower() in {'void', 'void.'}:
        surname = ""

    if forename.lower() in {'void', 'void.', 'villa void'}:
        forename = ""
        if surname and not is_person_name_or_title(surname) and not bldg_name:
            bldg_name = title_case_name(surname)
            surname = ""

    rec = {
        "year": year,
        "street": street,
        "house_number": house_num,
        "building_name": bldg_name,
        "surname": surname,
        "forename": forename,
        "trade": trade,
    }

    # 21. Apply Structured Edge-Case Overrides from edge_cases.json
    rec = apply_edge_cases(rec)

    if not rec["surname"] and not rec["forename"] and not rec["trade"] and not rec["building_name"]:
        return None

    return rec

def parse_resident_line(text):
    text = text.strip(' ,.-')

    # Case 1: "Brown Lorenzo, mariner" or "Heaven Hy., Weigher"
    if ',' in text:
        name_part, trade_part = text.split(',', 1)
        trade_part = trade_part.strip(' ,.-')
        name_tokens = name_part.strip().split()
        if len(name_tokens) >= 2:
            sub_s = name_tokens[0]
            sub_fn = " ".join(name_tokens[1:])
        elif len(name_tokens) == 1:
            sub_s = name_tokens[0]
            sub_fn = ""
        else:
            sub_s, sub_fn = text, ""
        return sub_s, sub_fn, trade_part

    # Case 2: "Rees Jno. Truck Mender" or "Upstone Wm. Carpenter"
    m_dot = re.match(r'^([A-Z][a-zA-Z\x27\-]+)\s+([A-Z][a-zA-Z\.]*?\.?)\s+(.*)$', text)
    if m_dot:
        sub_s = m_dot.group(1)
        sub_fn = m_dot.group(2)
        sub_t = m_dot.group(3).strip(' ,.-')
        return sub_s, sub_fn, sub_t

    tokens = text.split()
    if len(tokens) == 1:
        return tokens[0], "", ""
    elif len(tokens) == 2:
        return tokens[0], tokens[1], ""
    else:
        return tokens[0], tokens[1], " ".join(tokens[2:])

def unpack_row_if_concatenated(row):
    trade = row.get("trade", "").strip()
    if not trade or not re.search(r'[a-zA-Z\.]\d{1,3}\s+[A-Z][a-zA-Z]', trade):
        return [row]

    m_first = re.search(r'^([^\d]*?)(\d{1,3})\s+([A-Z].*)$', trade)
    if not m_first:
        return [row]

    initial_trade = m_first.group(1).strip(' ,.-')
    rem = m_first.group(2) + " " + m_first.group(3)

    unpacked = []
    r_first = dict(row)
    r_first["trade"] = initial_trade
    unpacked.append(r_first)

    parts = re.findall(r'(\d{1,3})\s+([A-Z][^\d]+?)(?=\d{1,3}\s+[A-Z]|$)', rem)
    for sub_hno, sub_text in parts:
        sub_text = sub_text.strip(' ,.-')
        sub_s, sub_fn, sub_t = parse_resident_line(sub_text)
        unpacked.append({
            "year": row.get("year", ""),
            "street": row.get("street", ""),
            "house_number": sub_hno,
            "building_name": row.get("building_name", ""),
            "surname": sub_s,
            "forename": sub_fn,
            "trade": sub_t
        })
    return unpacked

def main():
    rows = []
    skipped_count = 0
    
    with open(INPUT_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for raw_row in reader:
            # Unpack 1886 Crindau Gas Works run-on blob
            if raw_row.get("street") == "Crindau Road" and raw_row.get("year") == "1886" and "Williams Joseph" in raw_row.get("trade", ""):
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "1", "building_name": "Workmen's Cottage", "surname": "Manley", "forename": "Michael", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "2", "building_name": "Workmen's Cottage", "surname": "Williams", "forename": "Joseph", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "3", "building_name": "Workmen's Cottage", "surname": "Gane", "forename": "Joshua", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "4", "building_name": "Workmen's Cottage", "surname": "Sweet", "forename": "Robert", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "5", "building_name": "Workmen's Cottage", "surname": "Murphy", "forename": "Michael", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "6", "building_name": "Workmen's Cottage", "surname": "Hiscocks", "forename": "Henry", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "", "building_name": "Crindau Gas Works", "surname": "Crindau Gas Works", "forename": "", "trade": "gas works"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "", "building_name": "Glass Works", "surname": "South Wales Glass Manufacturing Co.", "forename": "", "trade": "glass works"})
                continue

            # Unpack Fair Oak Avenue 1886 multi-resident run-on blob
            if raw_row.get("year") == "1886" and "Torquay villasTeale" in raw_row.get("trade", ""):
                blob1 = [
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "5", "building_name": "", "surname": "Watkins", "forename": "William", "trade": "milkman"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "6", "building_name": "", "surname": "Pugsley", "forename": "Miss", "trade": "ladies school"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Fair Oak Nursery", "surname": "Jones", "forename": "W.", "trade": "nurseryman"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "1", "building_name": "Torquay Villas", "surname": "Dixon", "forename": "H.", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "2", "building_name": "Torquay Villas", "surname": "Teale", "forename": "E. H.", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Seaton House", "surname": "Happerfield", "forename": "D.", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Lynton Villa", "surname": "Winson", "forename": "Alfred", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Clyde Villa", "surname": "Lewis", "forename": "W. H.", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Dan Y Rhiw", "surname": "Clarke", "forename": "John", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Wilks", "forename": "Alfd.", "trade": "engineer"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "White", "forename": "Fredk.", "trade": "carpenter"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Gundy", "forename": "James", "trade": "labourer"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Newman", "forename": "George", "trade": "signal fitter"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Reeve", "forename": "John", "trade": "bricklayer"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Cambria Cottages", "surname": "Wilks", "forename": "Mrs. Rebecca", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Parsons", "forename": "Ivor", "trade": "gardener"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "", "surname": "Short", "forename": "Charles", "trade": "master mariner"},
                    {"year": "1886", "street": "Fair Oak Avenue", "house_number": "", "building_name": "Clifton Terrace", "surname": "Blackman", "forename": "Mrs.", "trade": ""}
                ]
                for r in blob1:
                    rows.append(clean_record(r))
                continue

            # Unpack Fair Oak Terrace 1886 multi-resident run-on blob
            if raw_row.get("year") == "1886" and "PRIMROSE COTTAGES-James" in raw_row.get("trade", ""):
                blob2 = [
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "13", "building_name": "", "surname": "Morgan", "forename": "Mat.", "trade": "milkman"},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "James", "forename": "Edwd.", "trade": "plasterer"},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "Edwards", "forename": "Chas.", "trade": "labourer"},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "Taverner", "forename": "Mrs. Emma", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "George", "forename": "Thos.", "trade": "pork butcher"},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "Morgan", "forename": "John", "trade": ""},
                    {"year": "1886", "street": "Fair Oak Terrace", "house_number": "", "building_name": "Primrose Cottages", "surname": "Warren", "forename": "James", "trade": "labourer"}
                ]
                for r in blob2:
                    rows.append(clean_record(r))
                continue

            # Unpack James Street 1886 multi-resident run-on blob
            if raw_row.get("year") == "1886" and "From Marion street-Anstee" in raw_row.get("trade", ""):
                blob3 = [
                    {"year": "1886", "street": "James Street", "house_number": "11", "building_name": "", "surname": "Corbin", "forename": "John", "trade": "hobbler"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Anstee", "forename": "Charles", "trade": "greengrocer"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Carpenter", "forename": "John", "trade": "plasterer"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Casey", "forename": "Thomas", "trade": "coal trimmer"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Betts", "forename": "Edward", "trade": "blockmaker"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Hunt", "forename": "James", "trade": "labourer"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Charles", "forename": "Maria", "trade": "widow"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Briscoll", "forename": "Peter", "trade": "labourer"},
                    {"year": "1886", "street": "James Street", "house_number": "", "building_name": "", "surname": "Lewis", "forename": "Eleanor", "trade": "widow"}
                ]
                for r in blob3:
                    rows.append(clean_record(r))
                continue

            # Unpack Rodney Parade 1886 multi-resident run-on blob
            if raw_row.get("year") == "1886" and "French Consul, Bridge house" in raw_row.get("trade", ""):
                blob4 = [
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "London Wharf", "surname": "Davies Bros.", "forename": "", "trade": "builders' merchants"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Bridge House", "surname": "Bellaguet", "forename": "Leon", "trade": "French Consul"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Thomas Job & Co.", "forename": "", "trade": "marble slate & monumental works"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Newport Cricket Ground", "surname": "Newport Cricket Ground", "forename": "", "trade": "cricket ground"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Williams' Aerated Water Works", "forename": "", "trade": "aerated water works"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Dunning", "forename": "H. A.", "trade": ""},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Williams", "forename": "Henry L.", "trade": ""},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Price", "forename": "J.", "trade": "weighing machine"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Norman", "forename": "John", "trade": "seaman"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Gridiron Wharf", "surname": "Cheeseman", "forename": "G.", "trade": "gridiron keeper"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Gridiron Wharf", "surname": "Ball", "forename": "Wm.", "trade": "gridiron keeper"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Spittle's Boiler Works", "surname": "Spittle's Boiler Works", "forename": "", "trade": "boiler works"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Rodney Wharf", "surname": "Johns", "forename": "Matthew", "trade": "lime kilns"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Rodney Wharf", "surname": "Fothergill", "forename": "J. C.", "trade": "timber yard and steam saw mills"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Radford", "forename": "George", "trade": "labourer"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Cording", "forename": "Charles", "trade": "sawyer"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "", "surname": "Welsh", "forename": "P.", "trade": "berthing master"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Great Western Wharf", "surname": "Happerfield", "forename": "D.", "trade": "manager"},
                    {"year": "1886", "street": "Rodney Parade", "house_number": "", "building_name": "Usk Chemical Works", "surname": "Morris and Griffin", "forename": "", "trade": "chemical works"}
                ]
                for r in blob4:
                    rows.append(clean_record(r))
                continue

            sub_rows = unpack_row_if_concatenated(raw_row)
            for row in sub_rows:
                cleaned = clean_record(row)
                if cleaned is None:
                    skipped_count += 1
                else:
                    rows.append(cleaned)

    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done! Cleaned and normalized {len(rows)} records in {OUTPUT_CSV}. Filtered {skipped_count} header/cross-street/return rows.")

if __name__ == "__main__":
    main()