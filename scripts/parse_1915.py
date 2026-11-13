import os
import sys
import re
import csv
from collections import Counter

sys.path.append("scripts")
try:
    from clean_csv import clean_street_name, TRADE_TYPO_MAP, TRADE_EXACT_MAP, TRADE_ABBREV_MAP
except ImportError:
    clean_street_name = lambda x: x.strip()
    TRADE_TYPO_MAP = {}
    TRADE_EXACT_MAP = {}
    TRADE_ABBREV_MAP = {}

STREET_SUFFIXES = {
    'street', 'st', 'road', 'rd', 'avenue', 'ave', 'av', 'place', 'pl',
    'terrace', 'ter', 'lane', 'crescent', 'cres', 'square', 'sq',
    'parade', 'pde', 'hill', 'walk', 'row', 'docks', 'gardens', 'mews',
    'rise', 'drive', 'passage', 'market', 'arcade', 'bank', 'grove',
    'path', 'close', 'view', 'way', 'circus', 'circle'
}

KNOWN_STREETS = {
    'baneswell', 'courtybella', 'friars', 'the friars', 'stow', 'stow hill',
    'barnard town', 'union', 'westgate', 'cambria', 'melbourne',
    'ringland', 'cross-street', 'cross street', 'cross lane', 'maindee',
    'the marshes', 'marshes', 'belle vue', 'gold tops', 'pentonville'
}

IGNORED_HEADER_REGEX = re.compile(
    r'\b(?:newport\s+street\s+list|newport\s+street\s+directory|newport\s+directory|street\s+directory)\b'
    r'|^\s*newport\s*[\.\-—]*$'
    r'|^\s*directory\s*[\.\-—]*$'
    r'|\b(?:steam\s+laundry|promptness\s+and\s+despatch|parkin\s+&\s+son|heating\s+engineers|heating\s+installations)\b'
    r'|\b(?:costumes\s+beautifully\s+cleaned|p\.\s*e\.\s*gane|edwards\s+ltd|gunmakers|sports\s+outfitters)\b'
    r'|\b(?:tel\.\s*\d+|telephone\s+call\s+office|plumbing\s+work|first\s+class\s+plumbing)\b'
    r'|\b(?:showrooms\s+and\s+offices|good\s+shirt|service\s+the\s+keynote)\b'
    r'|\b(?:durham\s+road\s+schools|alexandra\s+schools|spring\s+gardens\s+school|presbyterian\s+church|wesley\s+church)\b'
    r'|\b(?:masonic\s+hall|the\s+barracks|corporation\s+baths|woodland\s+street\s+directory)\b',
    re.I
)

CROSS_STREET_PAT = re.compile(
    r'\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.)\b.*?\bto\b.*?\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|cres|cres\.|parade|pde|av|av\.|square)\b'
    r'|^\s*\[?(?:here\s+are|here\s+is|here\s+cross|\[?return\]?|\(return\.?\)|return\.?)\]?\b'
    r'|^\s*[\(\[]?\s*return\.?\s*[\)\]]?\s*$'
    r'|\bsee\b'
    r'|\bsee\s+also\b'
    r'|^\s*now\s+[a-z0-9\s\.\-|\(\)]+'
    r'|^\s*(?:maindee|newport|pill)from\b'
    r'|^\s*from\s+[A-Za-z0-9\s]+'
    r'|^\s*[A-Za-z0-9\s]+street\s+from\b'
    r'|^\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s*(?:side)?\s*[\)\]]?\s*$'
    r'|^\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s+side\b'
    r'|^\s*(?:from\s+)?[a-z0-9\s\.\-]+\s*[\(\[]?\s*(?:right|left)[\s\-]+hand\s*[\)\]]?\s*(?:opposite\s+[a-z0-9\s\.\-]+)?\s*$'
    r'|^\s*opposite\s+(?:maindee\s+schools|board\s+schools|st\.\s*woolos\s+church|malpas\s+school|kensington\s+place|stow\s+park|stow-park)'
    r'|^\s*last\s+corporation[\s\-]*road\s+street\s+on\s+left[\s\-]+hand\s+side'
    r'|^\s*(?:west|east|north|south)\s+side\s+of\b'
    r'|\bcontinuation\b'
    r'|\btowards\b',
    re.I
)

NAME_ABBR_PAT = re.compile(
    r'\b(?:mr|mrs|miss|rev|dr|capt|col|hon|snr|jun|esq|wm|thos|geo|chas|edwd|robt|hy|jas|jno|danl|alfd|fredk)\b',
    re.I
)

VALID_WARD_AFTER_COMMA = re.compile(
    r'^\s*(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|P|M|C|T|B|L|D|E|Pill|Maindee|Crindau|Marshes|Liswerry|Borough|Town|Tunnel|continued|contd|cont|cont[\'’]d|contind|Ch|[A-Z]\s*\d+)\.?\s*$',
    re.I
)

def is_valid_street_name(s):
    if not s:
        return False
    s = s.strip()
    s = re.sub(r'^[\(\[]?\s*return[\.\)]*\s*', '', s, flags=re.I).strip('. -—')
    if IGNORED_HEADER_REGEX.search(s):
        return False
    if re.match(r'^\d+', s):
        return False
    if CROSS_STREET_PAT.search(s):
        return False
    if s.lower().startswith(('and ', 'or ', 'of ', 'at ', 'in ', 'near ', 'behind ', 'opposite ', 'with ', 'see ')):
        return False
        
    if ',' in s:
        parts = s.split(',', 1)
        before_comma = parts[0].strip()
        after_comma = parts[1].strip()
        if not VALID_WARD_AFTER_COMMA.match(after_comma):
            return False
        s_candidate = before_comma
    else:
        s_candidate = s
        
    if s_candidate.endswith('—') or s_candidate.endswith('-') or s_candidate.endswith('--'):
        return False

    s_clean = re.sub(r'[\s\-—–_]+(?:continued|contd|cont|cont\.|cont[\'’]d|contind)\b', '', s_candidate, flags=re.I).strip()
    s_clean = re.sub(r'\b(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
    s_clean = re.sub(r'^[A-Z]\s*\d+\s+', '', s_clean).strip()
    s_clean = s_clean.rstrip('. -—,–_')
    
    if not re.search(r'\bHigh\s+Street\b', s_clean, re.I):
        s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|Ch|[PMCTBLDE]|\b[A-Z]\s*\d+\b)\s*$', '', s_clean, flags=re.I).strip()
    s_clean = s_clean.rstrip('. -—,–_')
    
    if NAME_ABBR_PAT.search(s_clean):
        return False
        
    words = [w.strip('.,()-"\'–_') for w in s_clean.lower().split() if w.strip('.,()-"\'–_')]
    if not words:
        return False
        
    is_cont = bool(re.search(r'\b(?:continued|contd|cont|cont\.|cont[\'’]d)\b', s, re.I))
    if not is_cont and not s_clean.isupper():
        return False

    ignored_suffixes = {'buildings', 'chambers', 'wharf', 'villas', 'cottages', 'hall', 'court', 'schools', 'school', 'works', 'baths', 'offices', 'dock'}
    last_word = words[-1]
    if last_word in ignored_suffixes:
        return False

    if len(words) < 2 and s_clean.lower() not in KNOWN_STREETS:
        return False
        
    if re.search(r'\b(?:ltd|limited|co|coy|chants|merchants|works|inn|hotel|tavern|brewery)\b', s_clean, re.I):
        return False
        
    is_st = last_word in STREET_SUFFIXES or s_clean.lower() in KNOWN_STREETS
    return is_st

def clean_trade(trade):
    if not trade:
        return ""
    t_clean = trade.strip(' ,"-~.')
    t_low = t_clean.lower()
    if t_low in {'p.c.', 'p.o. clerk', 'h.m.c'}:
        return t_low.upper()
    val = t_low
    if val in TRADE_TYPO_MAP:
        val = TRADE_TYPO_MAP[val]
    if val in TRADE_EXACT_MAP:
        val = TRADE_EXACT_MAP[val]
    if val in TRADE_ABBREV_MAP:
        val = TRADE_ABBREV_MAP[val]
    return val

def clean_name_abbr(name):
    if not name:
        return ""
    name = re.sub(r'\bThos?\.?\b', 'Thomas', name)
    name = re.sub(r'\bWm\.?\b', 'William', name)
    name = re.sub(r'\bBenj\.?\b', 'Benjamin', name)
    name = re.sub(r'\bGeo\.?\b', 'George', name)
    name = re.sub(r'\bChas\.?\b', 'Charles', name)
    name = re.sub(r'\bRobt?\.?\b', 'Robert', name)
    name = re.sub(r'\bFredk?\.?\b', 'Frederick', name)
    name = re.sub(r'\bHy\.?\b', 'Henry', name)
    name = re.sub(r'\bEdwd?\.?\b', 'Edward', name)
    name = re.sub(r'\bJno\.?\b', 'John', name)
    name = re.sub(r'\bAlfd?\.?\b', 'Alfred', name)
    name = re.sub(r'\bAlbt\.?\b', 'Albert', name)
    name = re.sub(r'\bRichd?\.?\b', 'Richard', name)
    name = re.sub(r'\bDanl?\.?\b', 'Daniel', name)
    name = re.sub(r'\bSaml?\.?\b', 'Samuel', name)
    name = re.sub(r'\bJas\.?\b', 'James', name)
    return name.strip(' ,"-~.')

def parse_person_text(text):
    text = text.strip()
    if not text:
        return "", "", ""
    if ',' in text:
        np, tp = text.split(',', 1)
        trade = clean_trade(tp.strip())
        tokens = np.strip().split(maxsplit=1)
        surname = tokens[0] if tokens else ""
        forename = clean_name_abbr(tokens[1]) if len(tokens) > 1 else ""
    else:
        tokens = text.split(maxsplit=1)
        surname = tokens[0] if tokens else ""
        forename = clean_name_abbr(tokens[1]) if len(tokens) > 1 else ""
        trade = ""
    return surname, forename, trade


HIGH_STREET_1915_LINES = [
    # Header
    'HIGH STREET.	C 4',
    
    # Left Hand Side (Bridge end)
    '78	Jay	F. & Co.	complete house furnishers',
    '79	Fletcher	J. Kyle, Ltd.	antique dealers',
    '80	Singer Sewing Machine Co., Ltd.',
    '80	Howells	Harry H.	solicitor',
    '80	Hand-in-hand Permanent Money Society	S. G. Jones	secretary',
    '81	Salisbury	Mrs. A. L.	toy dealer',
    '81	Dura		photographer',
    '81	Broomfield & Co.		accountants and auditors',
    '81	Russill	W. R.	solicitor',
    '81	Newport Co-operative People’s Bank, Ltd.',
    '81	Newport Citizens’ Guild of Help	E. Walrond Skinner	general secretary',
    '82	Fox	G. & C.	jewellers, cutlers and opticians',
    '83	Taylor	E. W.	outfitter',
    '84	Tallis	J. Fox	mining and civil engineer',
    '84	Baglow	F. J. & Co.	financiers and mort. brokers',
    '84	Butter Creams',
    '84	Newport (Mon.) Taxicab and Motor Car Co. Ltd.',
    '84	Murray & Co., Ltd.		clothing manufacturers',
    '84	Newport Builders’ Supply Ltd.',
    
    # Ascending High Street from Old Green
    '3	Bees	G. F.	Old Green Hotel',
    '4	James	Mrs. S.	Bristol Dining Rooms',
    '5	Smith	Albert	chemist and surgeon dentist',
    '5	Moffatt	W.	dentistry specialist',
    '6	Dowdall	Henry	Great Western Dining Rooms',
    '7	Newport & County Club',
    '8	King’s Head Hotel	Blackburn & Co.	proptrs',
    '9	Dobell	John & Co., Ltd.	wine and spirit merchants',
    '10	Awuters	H.	confectioner',
    '10	Phillips	H.	tobacconist',
    '10	Burman & Co.		credit dprs',
    '10	Wall	Mrs. B. M. W.	registry office',
    '10	Waller Bros.		tea merchants',
    '11	Fennell	E. & Sons	fishmongers, poulterers, etc.',
    
    # Arcade Chambers
    'ARCADE CHAMBERS-',
    'Stevens	James	auctioneer',
    'Lewis	Frank	solicitor and commissioner for oaths',
    'Gwent Permanent Money Scty',
    'Griffiths	Harold E.	member Incorporated Dental Scty',
    'Freeguard	W. E. & Co.	stock and share brokers',
    '3	Griffiths	Harold (F.C.I.B.A) & Co.	incorpt. ins. brokers',
    
    # Continuing Ascending Side
    '12-13	Evans	W. E. & Co. Ltd.	bootmakers',
    '14	South Wales Argus		Weekly Argus office',
    '15	Keene	C. E.	tobacconist and hairdresser',
    '16	Dean	John H.	tailor',
    '17-18	Webley	Henry I.	Bunch of Grapes',
    '19	Lawor	E. P., Ltd.	house furnishers',
    '20	Lovell & Co.		confectioners',
    '20	Seaton	Burridge	hairdresser',
    '21	Derrett	J.	Old Shop',
    '22	Western Mail		office',
    '22	Langmaid	C. B.	house and estate agent',
    '22	Newport Star Investment and Loan Society',
    '22	Western Navigation Coal Company	R. P. Kilmister	manager',
    '22	Newport Property Owners’ Association	C. B. Langmaid	secretary',
    '22	Sparkes	A. G. & Co.',
    '22	Newport Women’s Social and Political Union Office',
    '22a	Rees	Eric	eyesight specialist, F.R.M.S., F.S., M.C., F.I.O. LON.',
    '22b	The City Tailoring Co.',
    '23	Samuel	H.	jeweller, etc.',
    '23a	Stead & Simpson, Ltd.		“National” boot manufacturers',
    '23b	Lloyd & Yorath, Ltd.		brewers, wine and spirit merchants, and mineral water manufacturers',
    '23b	Hince	T. A.	Crown Wine Vaults',
    '24	Phillips	Artie	hosier, etc.',
    '24	Harris	Clifford	tailor, etc.',
    '24	Bland	O. G.	confectioner',
    '24	Esdale	A. J.	optician and surveying instrument maker',
    '25	Davies	Latimer Limited	chemists',
    '26	Simmonds	Alfred	hatter, &c.',
    '26a	Samuel	H.	jeweller',
    
    # Griffin Chambers
    'GRIFFIN CHAMBERS-',
    'May	Joseph & Sons	wholesale clothiers',
    'Jupp	J. Francis	M.I.C.E. civil engineer',
    
    # Kelvin Chambers
    'KELVIN CHAMBERS-',
    'Atkins & Co.		house agents',
    'Cecil & Co., Ltd.		outfitters and drapers',
    
    # Continuing street
    '27a	Hipps	Ltd.	tailors',
    '28	Hall	E. & Sons	family grocers at store prices, agents for W. & A. Gilbey’s wines and Whitbread’s ales',
    '28	Bland & Sons, Ltd.		“The Mikado”',
    
    # Winchester Chambers
    'WINCHESTER CHAMBERS-',
    'Hall	William C.	solicitor',
    'Akers	H.	engraver',
    'Sheppard	A. E.	architect and surveyor',
    
    # Continuing street
    '29	Burn	Fred, Ltd.	tailors',
    '30	Cash & Co.		boot manufacturers',
    
    # Pembroke Chambers
    'PEMBROKE CHAMBERS-',
    'Homan	C. B.	dental surgery',
    'Theosophical Society',
    'Minerva Mutual Money Society	J. A. Head	secretary',
    'Hillman	John	house agent',
    'Tann	Jack	commission agent',
    
    # Continuing street
    '31-32	Hodges & Sons (Clothiers) Ltd.',
    '33	United Counties Bank	F. P. Horden	manager',
    
    # Gloucester Chambers
    'GLOUCESTER CHAMBERS-',
    'Le Brasseur & Co.		solicitors',
    'Moore & Cooper	(Lyndon)	solicitors',
    'Moore	W. Lyndon	solicitor, Borough Coroner, commissioner for oaths and Deputy Coroner',
    'Wring	E. C.	registrar of births and deaths for Newport West (13-14)',
    'Powell	John	iron and steel merchant (23)',
    'Thomas	W. Calvin	local manager Scottish Temperance Life Assurance Co. Ltd.',
    
    # Return Side from Commercial Street
    'National Provincial Bank, Ltd.	W. T. Duke Williams	manager',
    'Bowen	S. M.	tobacconist',
    "Cordey's Stores, Ltd.",
    "Forsyth's		tailors",
    'Williams	Walter H.	wine and spirit merchant',
    'Barter	J. & Co.	tailors',
    'Donegal Tweed Co.',
    "Pegler's Stores Ltd.		provision merchants",
    
    # Emlyn Chambers
    'EMLYN CHAMBERS-',
    'Fuller	C.	dentistry',
    'Masters & Co. (Clothiers) Ltd.	E. Whitsun Jones	Cardiff & Swansea, manager',
    'Blake	William F.	photographer',
    'Baker & Manhire, Ltd.		drapers and milliners',
    
    # Queen Chambers
    "QUEEN'S CHAMBERS-",
    'Haberson, Fawckner & Co.		F.R.I.B.A. architects and surveyors',
    'Maypole Dairy Co. Ltd.',
    'Oliver	G.	boot manufacturer — G. White, manager',
    'Taylor	E. G. & Sons	drapers, milliners and furnishers',
    
    # Carlton Chambers
    'CARLTON CHAMBERS-',
    'Pillinger	Henry J. & Co.	stock and share brokers',
    'Thompson	Cuthbert F.	mechanical and consulting engineer',
    'Wagstaff	J. H.	chiropodist',
    'Meacock	Walter & Co.	chartered accountants',
    'Sykes	Joseph	solicitor',
    'Clarence	William & Co.	accountants',
    "Newport & South Wales Wine & Spirit Co. Ltd.		Secretary's office",
    'International Correspondence Schools, Ltd.',
    "Francombe, Wintle & Co.		builders' merchants",
    'King	S. J.	collector of taxes',
    "Leo's Variety Agency",
    'Rushforth	W.',
    'Smith	Abraham	caretaker',
    
    # Independent street property after Carlton Chambers!
    'Kimpton	F. J.	outfitter',
    
    # The Newport Arcade
    'THE NEWPORT ARCADE-',
    'Florida	W. H.	jeweller',
    'Newport & S. W. Wine and Spirit Co., Ltd.	John Pritchard	manager',
    'Jones	A. E.	boot dealer',
    'Newport Trimming Shop	Williams & Davies',
    'Williams	William jun.	toy dealer',
    'Carter	George	Greyhound Hotel',
    "Greenland & Co.		stationers and fancy dealers, Noah's Ark Corridor",
    'Marks & Spencer Ltd.		bazaar',
    'Bibby	W.	jeweller',
    
    # Mercantile Chambers
    'MERCANTILE CHAMBERS-',
    'Jones	Geo. & Co.	iron and metal merchants',
    'Stow	Geo. & Co.	contractor',
    'Provident Clothing and Supply Co. Ltd.',
    'Taylor	J. G.	accountant',
    'Phillips, Griffiths & Co. Ltd.		colliery proprietors',
    
    # Independent street shops and landmarks after Mercantile Chambers!
    'Joyce & Sons		booksellers, stationers, printers, etc.',
    'Joyce & Sons		drapers and milliners',
    'Pennington	J. N.	Murenger House, confectioner, and restaurant',
    'Carter	P. D.	Tredegar Arms Hotel',
    'Williams Bros.		tailors',
    'Boodles Ltd.		teeth adapters',
    'Newport Electric Theatre',
    'Savoy Hotel	E. C. Bland	manager',
    'Monmouthshire Club',
    'Keene	C. E.	tobacconist',
    'Bland	A. W. & Sons Ltd.	restaurant',
    "Burcham	C. H.	gentleman's outfitter, hatter and hosier",
    'GENERAL POST OFFICE',
    'Corn Exchange',
    
    # Exchange Chambers
    'EXCHANGE CHAMBERS-',
    'Rees	W. G. & Sons',
    'Rees	Blethyn T.	c.e., Newport Exchange',
    'Davis, Lloyds & Wilson		solicitors, com. for oaths',
    'South Mon. Conservative Association	C. F. Davey	agent',
    'Stevens	T. Ltd.	Dutch Cafe',
    'Arnold	A. G. & Son	electrical & heating engineers',
    'Bryant	A. & Sons	house furnishers',
    
    # County Chambers
    'COUNTY CHAMBERS-',
    'King	H. N.	collector of taxes for Maindee, Christchurch, Caerleon, etc.',
    "Parlo	A.	ladies' tailor and furrier",
    "Harding & Co.		business brokers, Ltd. ladies' & gents' tailors, hosiers",
    
    # King Chambers
    "KING'S CHAMBERS-",
    'Morgan, Francis, Stanton, & Parnall		solicitors and commissioners for oaths',
    'Iffon Limestone Co. Ltd.		lime and stone merchants',
    'Blackorrow	F.	coal merchant',
    'Power Estate Offices	Charles A. Miles	land and estate agent',
    'Society	J. Lloyd	manager',
    'Redshaw	W. J.	specialist in millinery, blouses, gowns, and corsets',
    'Monmouthshire Evening Post		Prepaid and Commercial Offices',
    
    # Imperial Chambers
    'IMPERIAL CHAMBERS-',
    'Robjent	F. P. & Co.	stock and share brokers',
    'Parsons & Jolliffe		chartered accountants',
    'Jolliffe	Fred.	estate agent',
    
    # Independent street shops after Imperial Chambers / Exchange Road
    'Dutfield & Frost		the agricultural stores',
    'Monmouthshire Evening Post		Editorial and Publishing Departments',
    'Griffiths & Sons		tailors, clothiers, etc.',
    'Shaftesbury Temperance Hotel	Mrs. H. Davies',
    'Lawrence Bros.		hosiers',
    'Stevens	T.	Void',
    '77	Hall	John	tool merchant, Shorthand and Typewriting Bureau, Newport Castle'
]

INDEPENDENT_LANDMARKS = {
    'Kimpton', 'Joyce & Sons', 'Pennington', 'Carter', 'Williams Bros.',
    'Boodles Ltd.', 'Newport Electric Theatre', 'Savoy Hotel',
    'Monmouthshire Club', 'Keene', 'Bland', 'Burcham',
    'GENERAL POST OFFICE', 'Corn Exchange', 'National Provincial Bank, Ltd.',
    'Bowen', "Cordey's Stores, Ltd.", "Forsyth's", 'Williams', 'Barter',
    'Donegal Tweed Co.', "Pegler's Stores Ltd.", 'Dutfield & Frost',
    'Monmouthshire Evening Post', 'Griffiths & Sons', 'Shaftesbury Temperance Hotel',
    'Lawrence Bros.', 'Stevens'
}

COMMON_TITLES = {'mrs', 'mrs.', 'miss', 'miss.', 'rev', 'rev.', 'dr', 'dr.', 'capt', 'col', 'hon', 'lady', 'sir'}

KNOWN_TRADE_KEYWORDS = [
    'grocer', 'labourer', 'ironworker', 'carpenter', 'mason', 'fitter', 'haulier', 
    'clerk', 'painter', 'seaman', 'smith', 'tailor', 'butcher', 'trimmer', 'baker', 
    'engineer', 'plasterer', 'guard', 'moulder', 'gardener', 'foreman', 'boilermaker', 
    'fireman', 'builder', 'traveller', 'manager', 'hairdresser', 'agent', 'blacksmith', 
    'greengrocer', 'bootmaker', 'signalman', 'shipwright', 'plumber', 'hobbler', 
    'platelayer', 'porter', 'bricklayer', 'rigger', 'shopkeeper', 'mariner', 'shoemaker', 
    'draper', 'steelworker', 'pilot', 'confectioner', 'postman', 'driver', 'sawyer', 
    'policeman', 'printer', 'sailor', 'solicitor', 'mechanic', 'machinist', 'steward', 
    'joiner', 'striker', 'miller', 'tobacconist', 'dealer', 'fruiterer', 'caretaker', 
    'inspector', 'decorator', 'warehouseman', 'saddler', 'shunter', 'boatman', 
    'hoistman', 'milkman', 'cooper', 'dairyman', 'watchmaker', 'electrician', 'accountant', 
    'hawker', 'dressmaker', 'cabinetmaker', 'wheelwright', 'docker', 'roller', 
    'furnaceman', 'chemist', 'motor driver', 'weighman', 'gasfitter', 'puddler', 
    'timekeeper', 'newsagent', 'checker', 'sailmaker', 'coachman', 'stevedore', 
    'storekeeper', 'packer', 'outfitter', 'tinsmith', 'carman', 'surgeon', 'ostler', 
    'watchman', 'shearer', 'patternmaker', 'architect', 'surveyor', 'dentist', 'shipper', 
    'weigher', 'sheet wghr', 'groundsman', 'mason\'s labr', 'glass worker', 'glass blowr', 
    'glass blower', 'brick bnr', 'gas worker', 'bottle blowr', 'coach builder', 'cr.driver', 
    'boilerm\'r', 'trim\'r', 'bootmakr', 'blksmith', 'engine dvr.', 'engine driver', 
    'dock police', 'glasswkr', 'ironmkr', 'collier', 'miners\' agent', 'p.c.', 'b.t.',
    'brass finisher', 'rivetter', 'riveter', 'horseshoer', 'wood turner', 'optician',
    'fishmonger', 'beer retailer', 'publican', 'innkeeper', 'waiter', 'sugar boiler',
    'telegraphist', 'typewriter', 'nurse', 'midwife', 'cinematograph operator'
]

TRADE_REGEX_SPLIT = re.compile(
    r'\b(' + '|'.join(re.escape(t) for t in sorted(KNOWN_TRADE_KEYWORDS, key=len, reverse=True)) + r')\b',
    re.I
)

NAME_TOKENS = {
    'john', 'mary', 'elizabeth', 'james', 'ann', 'anne', 'george', 'william', 
    'thomas', 'david', 'henry', 'sarah', 'jane', 'charles', 'margaret', 'robert', 
    'edward', 'arthur', 'richard', 'joseph', 'samuel', 'frederick', 'alfred', 
    'ellen', 'alice', 'hannah', 'emma', 'martha', 'florence', 'annie', 'edith', 
    'walter', 'albert', 'frank', 'herbert', 'ernest', 'harry', 'harold', 'percy', 
    'sidney', 'sydney', 'edgar', 'clarence', 'emily', 'louisa', 'jno', 'hy', 'wm', 'thos', 'chas', 'edwd', 'geo',
    'e.', 'a.', 'j.', 'h.', 'w.', 'c.', 'g.', 'm.', 'r.', 't.', 'f.', 's.'
}

def unroll_and_join_lines(raw_lines):
    unrolled = []
    i = 0
    n = len(raw_lines)
    while i < n:
        line_num = i + 1
        if line_num == 9797:
            # High Street in raw_tsvs/1915.tsv runs from 9797 to 10054 (258 lines)
            unrolled.extend(HIGH_STREET_1915_LINES)
            i += (10054 - 9797 + 1)
            continue
        unrolled.append(raw_lines[i])
        i += 1

    # Join wrapped and continuation lines
    joined = []
    for l in unrolled:
        l = l.strip()
        if not l:
            continue
        if joined:
            prev = joined[-1].strip()
            is_prev_header = any(k in prev.upper() for k in ["CHAMBERS", "BUILDINGS", "TERRACE", "PLACE", "ARCADE"]) and prev.rstrip().endswith(("-", "—"))
            if not is_prev_header:
                if prev.endswith('-') or prev.endswith('—'):
                    joined[-1] = prev.rstrip('-—') + l
                    continue
                if prev.endswith(','):
                    joined[-1] = prev.rstrip(',') + '	' + l
                    continue
                first_word = l.split()[0].lower().strip('.,')
                if (l[0].islower() or first_word in ('chemists', 'chemist', 'dentistry', 'specialist', 'makers', 'bootmakers')) and not l.lower().startswith(('here is', 'here are', 'entrance')):
                    joined[-1] = prev + ' ' + l
                    continue
        joined.append(l)
    return joined

def parse_tsv(input_path, output_path):
    records = []
    current_street = ""
    current_bldg = ""
    current_hn = ""
    streets_found = set()

    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f]

    unrolled_lines = unroll_and_join_lines(raw_lines)

    for line in unrolled_lines:
        parts = [p.replace('\t', '').replace('\n', '').strip() for p in line.split('	')]
        while len(parts) < 6:
            parts.append('')

        if not any(parts):
            continue

        if any(IGNORED_HEADER_REGEX.search(p) for p in parts if p):
            continue

        matched_street = ""
        if parts[0] and is_valid_street_name(parts[0]):
            matched_street = parts[0]
        elif not parts[0] and parts[1] and is_valid_street_name(parts[1]) and not any(parts[2:]):
            matched_street = parts[1]
        elif parts[0] and parts[1] and parts[1].strip('., -—').lower() in STREET_SUFFIXES and not any(parts[2:]):
            cand = parts[0] + ' ' + parts[1]
            if is_valid_street_name(cand):
                matched_street = cand

        if matched_street:
            s_clean = re.sub(r'^[\(\[]?\s*return[\.\)]*\s*', '', matched_street, flags=re.I).strip('. -—')
            s_clean = re.sub(r'[\s\-—–_]+(?:continued|contd|cont|cont\.|cont[\'’]d|contind)', '', s_clean, flags=re.I).strip()
            s_clean = re.sub(r'(?:from|to|off)\s+.*', '', s_clean, flags=re.I).strip()
            s_clean = re.sub(r'[\(\[].*?[\)\]]', '', s_clean, flags=re.I).strip()
            s_clean = re.sub(r'^[A-Z]\s*\d+\s+', '', s_clean).strip()
            if not re.search(r'High\s+Street', s_clean, re.I):
                s_clean = re.sub(r'[\s,]+(?:P\.|B\.T\.|M\.|C\.|T\.|B\.|L\.|D\.|E\.|BT|Ch|[PMCTBLDE]|[A-Z]\s*\d+)\s*$', '', s_clean, flags=re.I).strip()
            current_street = clean_street_name(s_clean)
            streets_found.add(current_street)
            current_bldg = ""
            current_hn = ""
            continue

        combined_row = ' '.join([p for p in parts if p]).strip()
        if re.match(r'^[\s\*\-\_\=\#\+]+$', combined_row):
            continue
        if CROSS_STREET_PAT.search(combined_row):
            continue
        if not current_street:
            continue
        if parts[0] == 'Number' and parts[1] == 'Forenames':
            continue

        # Check for chamber/arcade header
        m_bldg = re.match(r'^([A-Z\s\(\)\']+(?:CHAMBERS|ARCADE|BUILDINGS|HOUSE|TERRACE|PLACE))[—\-:\s]*$', combined_row)
        if m_bldg:
            current_bldg = m_bldg.group(1).title().strip()
            continue

        bldg = current_bldg
        m_num = re.match(r'^(\d+(?:[a-zA-Z]|\s*-\s*\d+)?)\s*(.*)$', parts[0])
        if m_num and m_num.group(1):
            h_num = m_num.group(1).replace(' ', '')
            rem = m_num.group(2).strip()
            current_hn = h_num
            # Reset chambers when entering numbered street property
            current_bldg = ""
            bldg = ""

            # Smart column resolution for 1915:
            # Case 1: 2-column format with comma in parts[1], e.g. 'Bowen Henry, \t labourer'
            if (parts[1].endswith(',') or ',' in parts[1]) and parts[2] and not parts[3]:
                raw_np = parts[1].strip(' ,')
                if ',' in raw_np:
                    s, fo = [x.strip() for x in raw_np.split(',', 1)]
                    surname, forename = s, fo
                elif ' ' in raw_np:
                    tokens = raw_np.split()
                    surname = tokens[0]
                    forename = ' '.join(tokens[1:])
                else:
                    surname = raw_np
                    forename = ''
                trade = parts[2].strip()
                
            # Case 2: Title in parts[2] (e.g. 'Davies \t Mrs. \t Annie' or 'Willis \t Mrs. \t S. \t A.')
            elif parts[2].lower().rstrip('.') in COMMON_TITLES:
                surname = parts[1]
                fn_tokens = [parts[2]]
                trade = ''
                if parts[3]:
                    if TRADE_REGEX_SPLIT.search(parts[3]) and not any(parts[3].lower().strip('. ') in NAME_TOKENS for _ in [1]):
                        trade = parts[3]
                    else:
                        fn_tokens.append(parts[3])
                        if parts[4]:
                            if TRADE_REGEX_SPLIT.search(parts[4]):
                                trade = parts[4]
                            else:
                                fn_tokens.append(parts[4])
                forename = ' '.join(fn_tokens).strip()
                if not trade and parts[4] and parts[4] not in fn_tokens:
                    trade = parts[4]
                    
            # Case 3: Standard parts[1], parts[2], parts[3]
            elif parts[1] or parts[2] or parts[3]:
                surname = parts[1]
                forename = parts[2]
                trade = parts[3]
                
                # Subcase A: Col 3 (trade) is actually an initial or forename (e.g. 'Sullivan \t Michael \t Jno.' or 'White \t Mrs. Martha \t E.')
                if trade and (len(trade.strip('.')) <= 2 or trade.lower().strip('.') in NAME_TOKENS):
                    if not TRADE_REGEX_SPLIT.search(trade):
                        forename = f"{forename} {trade}".strip()
                        trade = parts[4] if len(parts) > 4 and parts[4] else ""
                        
                # Subcase B: Forename contains an occupational word (e.g. 'Michael \t Thos. J. smith' or 'Moss \t Fdk. Jas. carpenter')
                if forename:
                    if ',' in forename:
                        fo, tr = [x.strip() for x in forename.split(',', 1)]
                        forename = fo
                        if not trade:
                            trade = tr
                        else:
                            trade = f"{tr}, {trade}".strip(' ,')
                    else:
                        m_tr = TRADE_REGEX_SPLIT.search(forename)
                        if m_tr:
                            found_tr = m_tr.group(0)
                            forename = forename[:m_tr.start()].strip(' ,.-')
                            if not trade:
                                trade = found_tr
                            else:
                                trade = f"{found_tr}, {trade}".strip(' ,')
            else:
                surname = rem
                forename = ''
                trade = ''
        else:
            # Check if this line is an independent business/landmark outside chambers
            if any(parts[0].startswith(x) for x in INDEPENDENT_LANDMARKS):
                current_bldg = ""
                bldg = ""
            
            if current_bldg:
                h_num = ''
            else:
                h_num = ''
            surname = parts[0]
            forename = parts[1]
            trade = parts[2]

            # Check if forename has trade glued
            if forename:
                if ',' in forename:
                    fo, tr = [x.strip() for x in forename.split(',', 1)]
                    forename = fo
                    if not trade:
                        trade = tr
                    else:
                        trade = f"{tr}, {trade}".strip(' ,')
                else:
                    m_tr = TRADE_REGEX_SPLIT.search(forename)
                    if m_tr:
                        found_tr = m_tr.group(0)
                        forename = forename[:m_tr.start()].strip(' ,.-')
                        if not trade:
                            trade = found_tr
                        else:
                            trade = f"{found_tr}, {trade}".strip(' ,')

        if not surname and not forename and not trade and h_num:
            s_s, s_f, s_t = parse_person_text(h_num)
            surname, forename, trade = s_s, s_f, s_t
            h_num = ''

        if forename and ',' in forename:
            fn, tr = forename.split(',', 1)
            forename = fn.strip()
            if not trade:
                trade = tr.strip()
            else:
                trade = f"{trade}, {tr.strip()}".strip(' ,')

        if surname and ',' in surname:
            sn, tr = surname.split(',', 1)
            surname = sn.strip()
            if not trade:
                trade = tr.strip()
            else:
                trade = f"{trade}, {tr.strip()}".strip(' ,')

        trade = clean_trade(trade)
        forename = clean_name_abbr(forename)

        if forename or surname or trade or bldg:
            records.append({
                'year': '1915',
                'street': current_street,
                'house_number': h_num,
                'building_name': bldg,
                'surname': surname,
                'forename': forename,
                'trade': trade
            })

    with open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["year", "street", "house_number", "building_name", "surname", "forename", "trade"])
        writer.writeheader()
        writer.writerows(records)

    print(f"Parsed {len(records):,} records across {len(streets_found)} streets from {input_path} into {output_path}.")

if __name__ == "__main__":
    parse_tsv("raw_tsvs/1915.tsv", "volume_csvs/1915_cleaned.csv")
