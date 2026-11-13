#!/usr/bin/env python3
"""
fix_split_trades.py
--------------------
Comprehensive repair tool for historical column-boundary splits where:
1. The first 2-4 letters of an occupation were cleaved off and appended to the resident's forename.
   e.g. Forename: 'James Fi', Trade: 'sh Shop' -> Forename: 'James', Trade: 'Fish Shop'
        Forename: 'H. D Fr', Trade: 'uit Merchant' -> Forename: 'H. D', Trade: 'Fruit Merchant'
        Forename: 'William L Bo', Trade: 'okbinder' -> Forename: 'William L', Trade: 'Bookbinder'
        Forename: 'William La', Trade: 'undryman' -> Forename: 'William', Trade: 'Laundryman'
        Forename: 'E. W Bu', Trade: 'rnerman' -> Forename: 'E. W', Trade: 'Burnerman'
        Forename: 'Reginald Lo', Trade: 'ckgateman' -> Forename: 'Reginald', Trade: 'Lockgateman'
2. Two-word compound trades where the qualifying first word ended up in forename.
   e.g. Forename: 'John Eng', Trade: 'Driver' -> Forename: 'John', Trade: 'Engine Driver'
        Forename: 'W. Engine', Trade: 'Driver' -> Forename: 'W.', Trade: 'Engine Driver'
        Forename: 'David coal', Trade: 'Trimmer' -> Forename: 'David', Trade: 'Coal Trimmer'
3. 1936 directory records where 'Co' was cleaved onto the surname with forename blank.
   e.g. Surname: 'Alfred J Poole Co', Forename: '', Trade: 'mpositor'
        -> Surname: 'Poole', Forename: 'Alfred J', Trade: 'Compositor'
4. Private house names incorrectly parsed into the trade column with initial letters in forename.
   e.g. Forename: 'Henry Hi', Trade: 'llside' -> Forename: 'Henry', Building: 'Hillside', Trade: ''
5. Forenames cleaved across columns:
   e.g. Forename: 'Vernon Wi', Trade: 'lliam' -> Forename: 'Vernon William', Trade: ''
"""

import csv
import os
import re
import shutil
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "scripts" else SCRIPT_DIR
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")


# 1. Single-word prefix repairs: (prefix, trade_pattern, target_canonical_trade)
REPAIR_SPECS = [
    ('To', r'^bacconist', 'Tobacconist'),
    ('to', r'^bacconist', 'Tobacconist'),
    ('St', r'^orekeeper', 'Storekeeper'),
    ('st', r'^orekeeper', 'Storekeeper'),
    ('Up', r'^[hH]olsterer', 'Upholsterer'),
    ('up', r'^[hH]olsterer', 'Upholsterer'),
    ('Wh', r'^eelwright', 'Wheelwright'),
    ('wh', r'^eelwright', 'Wheelwright'),
    ('Ca', r'^binetmaker', 'Cabinetmaker'),
    ('ca', r'^binetmaker', 'Cabinetmaker'),
    ('Gl', r'^ass\s*[bB]lower', 'Glassblower'),
    ('Gl', r'^assblower', 'Glassblower'),
    ('Bo', r'^ttlemaker', 'Bottlemaker'),
    ('Ba', r'^sket\s*[mM]aker', 'Basket Maker'),
    ('La', r'^bourer', 'Labourer'),
    ('Sh', r'^ipbroker', 'Shipbroker'),
    ('Sh', r"^ip['’]?s\s*[oO]fficer", "Ship's Officer"),
    ('De', r'^tective', 'Detective'),
    ('Os', r'^tler', 'Ostler'),
    ('Pu', r'^rveyor', 'Purveyor'),
    ('La', r'^mplighter', 'Lamplighter'),
    ('St', r'^ableman', 'Stableman'),
    ('St', r'^amper', 'Stamper'),
    ('Br', r'^akesman', 'Brakesman'),
    ('Br', r'^ickmaker', 'Brickmaker'),
    ('Br', r'^ickworker', 'Brickworker'),
    ('Br', r'^ickburner', 'Brickburner'),
    ('Br', r'^ick\s*[bB]urner', 'Brickburner'),
    ('Ma', r'^nager$', 'Manager'),
    ('Cl', r'^erk$', 'Clerk'),
    ('Op', r'^tician', 'Optician'),
    ('Bi', r'^llposter', 'Billposter'),
    ('Po', r'^tter$', 'Potter'),
    ('Ce', r'^llarman', 'Cellarman'),
    ('Ti', r'^mberman', 'Timberman'),
    ('Ha', r'^ycutter', 'Haycutter'),
    ('Si', r'^gn\s*writer', 'Signwriter'),
    ('Si', r'^gnwriter', 'Signwriter'),
    ('Ve', r'^rger$', 'Verger'),
    ('Pl', r"^aters['’]?\s*[hH]elper", "Platers' Helper"),
    ('St', r'^eelwk', 'Steelworker'),
    ('St', r'^eelwrkr', 'Steelworker'),
    ('Ba', r'^nk\s*[mM]ngr', 'Bank Manager'),
    ('Ca', r'^r\s*[rR]epr', 'Car Repairer'),
    ('Ca', r'^terer$', 'Caterer'),
    ('Re', r'^gistry\s*[oO]ffice', 'Registry Office'),
    ('Wi', r'^ne\s*and\s*spirit\s*merchants', 'Wine & Spirit Merchants'),
    ('Fr', r'^ied\s*[fF]ish\s*[sS]hop', 'Fried Fish Shop'),
    ('Li', r'^me\s*[bB]urner', 'Lime Burner'),
    ('Ru', r'^nner$', 'Runner'),
    ('Ch', r'^ef$', 'Chef'),
    ('Je', r'^wellers$', 'Jewellers'),
    ('Cl', r'^othier$', 'Clothier'),
    ('Na', r'^vvy$', 'Navvy'),
    ('Bu', r'^ilders$', 'Builders'),
    ('Pr', r'^inters$', 'Printers'),
    ('Re', r'^pairer$', 'Repairer'),
    ('Ca', r"^rp['’]tr$", 'Carpenter'),
    ('Ir', r'^on\s*[dD]resser', 'Iron Dresser'),
    ('Ci', r'^vil\s*[sS]ervant', 'Civil Servant'),
    ('In', r'^surance\s*[aA]gent', 'Insurance Agent'),
    ('In', r'^s\s*[sS]upt', 'Insurance Superintendent'),
    ('Ma', r'^rine\s*[oO]fficer', 'Marine Officer'),
    ('Sa', r'^ddler', 'Saddler'),
    ('Ar', r'^chitect', 'Architect'),
    ('Fi', r'^shmonger', 'Fishmonger'),
    ('Mi', r'^stress', 'Mistress'),
    ('Ph', r'^ysician\s*[aA]nd\s*[sS]urgeon', 'Physician and Surgeon'),
    ('phy', r'^sician\s*[aA]nd\s*[sS]urgeon', 'Physician and Surgeon'),
    ('So', r'^licitors?$', 'Solicitors'),
    ('Wa', r'^terman', 'Waterman'),
    ('Ga', r'^nger', 'Ganger'),
    ('Po', r'^lisher', 'Polisher'),
    ('Ra', r'^ilwayman', 'Railwayman'),
    ('Sh', r'^eetweigher', 'Sheetweigher'),
    ('Fa', r'^rrier', 'Farrier'),
    ('Jo', r'^urnalist', 'Journalist'),
    ('Sc', r'^affolder', 'Scaffolder'),
    ('Fu', r'^rnisher', 'Furnisher'),
    ('Su', r'^rveyor', 'Surveyor'),
    ('Do', r'^nkeyman', 'Donkeyman'),
    ('Sh', r'^opman', 'Shopman'),
    ('Li', r'^thographer', 'Lithographer'),
    ('Un', r'^dertaker', 'Undertaker'),
    ('Sc', r'^ulptor', 'Sculptor'),
    ('Pi', r'^ano\s*[tT]uner', 'Piano Tuner'),
    ('Jo', r'^inter', 'Jointer'),
    ('Gr', r'^ocers?$', 'Grocers'),
    ('Gr', r'^oom', 'Groom'),
    ('Ro', r'^ofer', 'Roofer'),
    ('Fo', r'^undryman', 'Foundryman'),
    ('St', r'^oreman', 'Storeman'),
    ('Bo', r'^okseller', 'Bookseller'),
    ('Gr', r'^oundsman', 'Groundsman'),
    ('St', r'^ocktaker', 'Stocktaker'),
    ('Ga', r'^s\s*[sS]toker', 'Gas Stoker'),
    ('Bo', r'^ttler', 'Bottler'),
    ('Pi', r'^pemaker', 'Pipemaker'),
    ('Ha', r'^mmerman', 'Hammerman'),
    ('Ca', r'^nvasser', 'Canvasser'),
    ('Ti', r'^n\s*[wW]orker', 'Tin Worker'),
    ('Mi', r'^ll\s*[hH]and', 'Mill Hand'),
    ('Po', r'^intsman', 'Pointsman'),
    ('Pi', r'^ckler', 'Pickler'),
    ('Ri', r'^vet\s*[mM]aker', 'Rivet Maker'),
    ('Sa', r'^mpler', 'Sampler'),
    ('Ma', r'^ltster', 'Maltster'),
    ('Ir', r'^onfounder', 'Ironfounder'),
    ('Sa', r'^lesman', 'Salesman'),
    ('Ho', r'^bbler', 'Hobbler'),
    ('pro', r'^fessor\s+of\s+music', 'Professor of Music'),
    ('mil', r'^[lL]iners', 'Milliners'),
    ('Wa', r'^tchman', 'Watchman'),
    ('St', r'^riker', 'Striker'),
    ('Ho', r'^istman', 'Hoistman'),
    ('Tr', r'^ansport\s*[wW]orker', 'Transport Worker'),
    ('Ca', r'^rgo\s*[wW]orker', 'Cargo Worker'),
    ('St', r'^oker', 'Stoker'),
    ('Tu', r'^beworker', 'Tubeworker'),
    ('Ti', r'^pper', 'Tipper'),
    ('Mi', r'^ller', 'Miller'),
    ('Wa', r'^gon\s*[rR]epairer', 'Wagon Repairer'),
    ('Ca', r'^retaker', 'Caretaker'),
    ('De', r'^ntist', 'Dentist'),
    ('Bo', r'^atman', 'Boatman'),
    ('Sa', r'^wyer', 'Sawyer'),
    ('Do', r'^ck\s*[wW]orker', 'Dock Worker'),
    ('Fu', r'^el\s*[wW]orker', 'Fuel Worker'),
    ('Fu', r'^elworker', 'Fuel Worker'),
    ('We', r'^lder', 'Welder'),
    ('Sh', r'^earer', 'Shearer'),
    ('Ir', r'^onmonger', 'Ironmonger'),
    ('Je', r'^weller', 'Jeweller'),
    ('Ca', r'^shier', 'Cashier'),
    ('Wi', r'^reman', 'Wireman'),
    ('Tu', r'^rner', 'Turner'),
    ('Mo', r'^torman', 'Motorman'),
    ('Ca', r'^rman', 'Carman'),
    ('Qu', r'^arryman', 'Quarryman'),
    ('Li', r'^no\s*[oO]perator', 'Lino Operator'),
    ('Fl', r'^[oO]rist', 'Florist'),
    ('Mu', r'^sician', 'Musician'),
    ('Bu', r'^s\s*[cC]onductor', 'Bus Conductor'),
    ('Su', r'^rgeon', 'Surgeon'),
    ('Pa', r'^cker', 'Packer'),
    ('Fi', r'^sh\s*Shop', 'Fish Shop'),
    ('Fr', r'^uit\s*Merchant', 'Fruit Merchant'),
    ('Fr', r'^uit\s*Salesm[ea]n', 'Fruit Salesman'),
    ('Bo', r'^okbinder', 'Bookbinder'),
    ('La', r'^undryman', 'Laundryman'),
    ('Ha', r'^ulage\s*Contractor', 'Haulage Contractor'),
]

# 2. Compound two-word trade repairs: (forename_pattern, trade_pattern, target_canonical_trade)
COMPOUND_REPAIRS = [
    (r"\b(?:eng|engr|engine)\b\.?$", r"^[dD]riv(?:er|r|[\x27\u2019]r)", "Engine Driver"),
    (r"\b(?:eng|engr|engine)\b\.?$", r"^[fF]itter", "Engine Fitter"),
    (r"\b(?:gas)\b\.?$", r"^[fF]itter", "Gasfitter"),
    (r"\b(?:tin)\b\.?$", r"^[sS]mith", "Tinsmith"),
    (r"\b(?:horse)\b\.?$", r"^[dD]ealer", "Horse Dealer"),
    (r"\b(?:toy)\b\.?$", r"^[dD]ealer", "Toy Dealer"),
    (r"\b(?:news)\b\.?$", r"^[aA]gent", "Newsagent"),
    (r"\b(?:coach)\b\.?$", r"^[pP]ainter", "Coach Painter"),
    (r"\b(?:coach)\b\.?$", r"^[bB]uilder[s]?", "Coach Builder"),
    (r"\b(?:coach)\b\.?$", r"^[sS]mith", "Coach Smith"),
    (r"\b(?:coal)\b\.?$", r"^[aA]gent", "Coal Agent"),
    (r"\b(?:coal)\b\.?$", r"^[mM]erchant", "Coal Merchant"),
    (r"\b(?:coal)\b\.?$", r"^[tT]rimmer", "Coal Trimmer"),
    (r"\b(?:coal)\b\.?$", r"^[lL]abourer", "Coal Labourer"),
    (r"\b(?:coal)\b\.?$", r"^[dD]ealer", "Coal Dealer"),
    (r"\b(?:coal)\b\.?$", r"^[sS]hipper", "Coal Shipper"),
    (r"\b(?:coal)\b\.?$", r"^[eE]xporter[s]?", "Coal Exporters"),
    (r"\b(?:coal)\b\.?$", r"^[tT]ipper", "Coal Tipper"),
    (r"\b(?:ship)\b\.?$", r"^[pP]ilot", "Ship Pilot"),
    (r"\b(?:ship)\b\.?$", r"^[sS]mith", "Ships Smith"),
    (r"\b(?:ship)\b\.?$", r"^[cC]arp(?:enter|t)", "Ship Carpenter"),
    (r"\b(?:ship)\b\.?$", r"^[pP]ainter", "Ship Painter"),
    (r"\b(?:ship)\b\.?$", r"^[aA]gent", "Ship Agent"),
    (r"\b(?:marine)\b\.?$", r"^[eE]ngineer", "Marine Engineer"),
    (r"\b(?:marine)\b\.?$", r"^[sS]urveyor", "Marine Surveyor"),
    (r"\b(?:marine)\b\.?$", r"^[sS]tores", "Marine Stores"),
    (r"\b(?:cab)\b\.?$", r"^[dD]river", "Cabdriver"),
    (r"\b(?:cab)\b\.?$", r"^[pP]rop(?:rietor|[\x27\u2019]?tr|r[\x27\u2019]?tr)", "Cab Proprietor"),
    (r"\b(?:railway)\b\.?$", r"^[gG]uard", "Railway Guard"),
    (r"\b(?:railway)\b\.?$", r"^[pP]orter", "Railway Porter"),
    (r"\b(?:railway)\b\.?$", r"^[pP]ol(?:ice)?", "Railway Police"),
    (r"\b(?:master)\b\.?$", r"^[mM]ariner", "Master Mariner"),
    (r"\b(?:police)\b\.?$", r"^[iI]nspector", "Police Inspector"),
    (r"\b(?:police)\b\.?$", r"^[cC]on(?:stable)?", "Police Constable"),
    (r"\b(?:general)\b\.?$", r"^[dD]ealer", "General Dealer"),
    (r"\b(?:general)\b\.?$", r"^[sS]mith", "General Smith"),
    (r"\b(?:timber)\b\.?$", r"^[mM]erchant", "Timber Merchant"),
    (r"\b(?:iron)\b\.?$", r"^[mM]oulder", "Iron Moulder"),
    (r"\b(?:iron)\b\.?$", r"^[wW]orker", "Iron Worker"),
    (r"(?<!estate & )\b(?:insurance)\b\.?$", r"^[aA]gent", "Insurance Agent"),
]

# 3. 1936 'Co' suffix in surname where forename is blank
CO_SURNAME_MAP = {
    "mpositor": "Compositor",
    "llier": "Collier",
    "ntractor": "Contractor",
    "nductor": "Conductor",
    "rporation Employee": "Corporation Employee",
    "al Tipper": "Coal Tipper",
    "al Porter": "Coal Porter",
}

# 4. House / Villa names erroneously in trade column
HOUSE_NAME_SPECS = [
    ("Ca", "rtref", "Cartref"),
    ("Hi", "llside", "Hillside"),
    ("Be", "lmont", "Belmont"),
    ("Hi", "llcrest", "Hillcrest"),
    ("Cl", "ovelly", "Clovelly"),
    ("Fe", "rndale", "Ferndale"),
    ("El", "lesmere", "Ellesmere"),
    ("Su", "nnyside", "Sunnyside"),
    ("Cl", "aremont", "Claremont"),
    ("Ma", "yfield", "Mayfield"),
    ("Hi", "ghfield", "Highfield"),
    ("Oa", "kfield", "Oakfield"),
    ("Pe", "nrhiw", "Penrhiw"),
    ("Ly", "nwood", "Lynwood"),
    ("Oa", "kdene", "Oakdene"),
    ("Th", "e Laurels", "The Laurels"),
    ("Pa", "rkfield", "Parkfield"),
    ("Be", "lle Vue", "Belle Vue"),
    ("Gl", "endale", "Glendale"),
    ("Fe", "rnside", "Fernside"),
    ("Sp", "ringfield", "Springfield"),
    ("Ly", "ndhurst", "Lyndhurst"),
    ("Av", "ondale", "Avondale"),
    ("Gw", "ynfa", "Gwynfa"),
    ("Ro", "thesay", "Rothesay"),
    ("Ro", "sedale", "Rosedale"),
    ("Ly", "ndale", "Lyndale"),
    ("Ov", "erdale", "Overdale"),
    ("El", "sinore", "Elsinore"),
    ("Pe", "ndennis", "Pendennis"),
    ("Th", "e Retreat", "The Retreat"),
    ("Pa", "rkdale", "Parkdale"),
    ("Th", "e Limes", "The Limes"),
    ("Ab", "botsford", "Abbotsford"),
    ("Fe", "rncliffe", "Ferncliffe"),
    ("Th", "e Grove", "The Grove"),
]

# Vocabulary and categories for dynamic algorithmic fragment repair
COMMON_FORENAMES = {
    "william", "george", "thomas", "charles", "edward", "arthur", "david",
    "henry", "francis", "james", "robert", "albert", "richard", "frederick",
    "herbert", "leonard", "harold", "alfred", "edwin", "ernest", "walter",
    "frank", "joseph", "samuel", "mary", "ann", "elizabeth", "jane", "ellen",
    "martha", "sarah", "florence", "alice", "edith", "emily", "beatrice"
}

HOUSE_INDICATORS = {
    "ho", "house", "cot", "cottage", "vil", "villa", "lawn", "glen", "knoll",
    "dene", "bryn", "ferns", "hill", "mount", "court", "lodge", "view", "bank",
    "lea", "farm", "park", "hall", "chambers", "place", "terrace", "crescent",
    "inn", "hotel", "tavern", "arms", "castle"
}

VALID_STANDALONE = {
    "labourer", "clerk", "tailor", "baker", "butcher", "mason", "painter", "fitter",
    "farmer", "grocer", "draper", "smith", "carpenter", "gardener", "porter",
    "driver", "ironworker", "steelworker", "miner", "collier", "boilermaker",
    "shoemaker", "seaman", "mariner", "waiter", "cook", "agent", "manager",
    "traveller", "cashier", "engineer", "plasterer", "moulder", "blacksmith",
    "bricklayer", "printer", "compositor", "hawker", "dealer", "contractor",
    "haulier", "carter", "joiner", "wheelwright", "cabinetmaker", "dressmaker",
    "milliner", "watchmaker", "jeweller", "builder", "optician", "chemist",
    "druggist", "decorator", "plumber", "glazier", "slater", "saddler",
    "tinsmith", "cooper", "sawyer", "patternmaker", "machinist", "salesman",
    "storekeeper", "warehouseman", "stevedore", "docker", "lighterman", "waterman",
    "boatman", "brakesman", "guard", "signalman", "shunter", "platelayer",
    "stoker", "furnaceman", "roller", "puddler", "founder", "striker",
    "turner", "cleaner", "caretaker", "attendant", "messenger", "collector",
    "inspector", "superintendent", "officer", "constable", "sergeant", "policeman",
    "soldier", "sailor", "pilot", "shipwright", "merchant", "surveyor",
    "architect", "accountant", "solicitor", "physician", "surgeon", "dentist",
    "teacher", "musician", "artist", "photographer", "journalist", "stationer",
    "newsagent", "tobacconist", "confectioner", "fruiterer", "fishmonger",
    "milkman", "outfitter", "undertaker", "ironmonger", "cooper", "carrier",
    "motorman", "conductor", "fireman", "watchman", "timekeeper", "shopkeeper",
    "labour'r", "boilermkr", "storekpr", "rivetter", "riveter", "electrician",
    "elect'n", "plumber", "puddler", "ganger", "sweep"
}

OCCUPATION_MAP = {
    'patternmakers': 'Patternmakers',
    'cafe': 'Cafe',
    'newsvendor': 'Newsvendor',
    'tinplate worker': 'Tinplate Worker',
    'boilemaker': 'Boilermaker',
    'boilermaker': 'Boilermaker',
    'nailmaker': 'Nailmaker',
    'nailcutter': 'Nailcutter',
    'woodturner': 'Woodturner',
    'rubberworker': 'Rubberworker',
    'sheetworker': 'Sheetworker',
    'scrapworker': 'Scrapworker',
    'baths attendant': 'Baths Attendant',
    'managing director': 'Managing Director',
    'chemist\'s asst': 'Chemist\'s Assistant',
    'terrazza worker': 'Terrazza Worker',
    'eton dairy': 'Dairy',
    'elec repairer': 'Electrical Repairer',
    'berthg mastr': 'Berthing Master',
    'builders\' merchant': 'Builders\' Merchant',
    'asst. supt. insurance': 'Assistant Superintendent Insurance',
    'attendan officer': 'Attendance Officer',
    'gent\'s outfitting': 'Gent\'s Outfitting',
    'chem. wk': 'Chemical Worker',
    'lending library': 'Lending Library',
    'crn str': 'Corn Stores',
    'ship\'s cook': 'Ship\'s Cook',
    'ships cook': 'Ship\'s Cook',
    'plater\'s helper': 'Plater\'s Helper',
    'ins super': 'Insurance Superintendent',
    'ins. mngr': 'Insurance Manager',
    'insp c.c': 'Inspector C.C.',
    'wghts. ins': 'Weights Inspector',
    'trav. laburn\'m': 'Commercial Traveller'
}

OCCUPATION_KEYWORDS = {
    'maker', 'makers', 'worker', 'workers', 'driver', 'drivers', 'man', 'men',
    'vendor', 'contractor', 'contractors', 'merchant', 'merchants', 'agent', 'agents',
    'clerk', 'clerks', 'smith', 'smiths', 'fitter', 'fitters', 'monger', 'mongers',
    'dealer', 'dealers', 'repairer', 'repairers', 'carrier', 'carriers',
    'keeper', 'keepers', 'cafe', 'tailor', 'tailors', 'mechanic', 'mechanics',
    'operator', 'operators', 'turner', 'turners', 'porter', 'porters',
    'attendant', 'attendants', 'inspector', 'inspectors', 'engineer', 'engineers',
    'builder', 'builders', 'painter', 'painters', 'cleaner', 'cleaners',
    'joiner', 'joiners', 'surveyor', 'surveyors', 'printer', 'printers',
    'layer', 'layers', 'cutter', 'cutters', 'dresser', 'dressers',
    'waiter', 'waiters', 'assistant', 'assistants', 'artist', 'artists',
    'setter', 'setters', 'weigher', 'weighers', 'trimmer', 'trimmers',
    'sawyer', 'sawyers', 'plater', 'platers', 'stoker', 'stokers',
    'miner', 'miners', 'collier', 'colliers', 'stevedore', 'stevedores',
    'haulier', 'hauliers', 'baker', 'bakers', 'butcher', 'butchers',
    'grocer', 'grocers', 'draper', 'drapers', 'chemist', 'chemists',
    'moulder', 'moulders', 'plasterer', 'plasterers', 'blacksmith', 'blacksmiths',
    'mason', 'masons', 'gardener', 'gardeners', 'shoemaker', 'shoemakers',
    'currier', 'curriers', 'cooper', 'coopers', 'machinist', 'machinists',
    'solicitor', 'solicitors', 'architect', 'architects', 'accountant', 'accountants',
    'officer', 'officers', 'constable', 'constables', 'collector', 'collectors',
    'salesman', 'salesmen', 'traveller', 'travellers', 'director', 'directors',
    'superintendent', 'supt', 'mastr', 'master', 'manufacturer', 'manufacturers', 'asst',
    'outfitting', 'dairy', 'library', 'g.w.r', 'ironworker', 'steelworker', 'stores',
    'seaman', 'mariner', 'cook', 'sweep', 'ganger', 'puddler', 'guard', 'signalman',
    'shunter', 'platelayer', 'furnaceman', 'roller', 'founder', 'striker', 'caretaker',
    'messenger', 'policeman', 'soldier', 'sailor', 'pilot', 'shipwright', 'physician',
    'surgeon', 'dentist', 'teacher', 'musician', 'photographer', 'journalist', 'stationer',
    'newsagent', 'tobacconist', 'confectioner', 'fruiterer', 'fishmonger', 'milkman',
    'outfitter', 'undertaker', 'ironmonger', 'motorman', 'conductor', 'fireman',
    'watchman', 'timekeeper', 'shopkeeper', 'rivetter', 'riveter', 'electrician',
    'elect\'n', 'fitter', 'boilermkr', 'labourer', 'labour\'r', 'storekpr',
    'hairdsr', 'hairdresser', 'miller', 'solic\'tr', 'shop', 'lodgings', 'steward',
    'sextoness', 'laundress', 'hobbler', 'rigger', 'beer retailer', 'shoemakr',
    'police-sergt', 'pro\'tr', 'foreman', 'warehouseman', 'boatman', 'hoistman'
}

COMMON_MIDDLE_NAMES = {
    'albert', 'edward', 'charles', 'henry', 'thomas', 'john', 'george', 'arthur',
    'herbert', 'william', 'percy', 'cecil', 'frederick', 'james', 'hnry', 'pritchard', 'mary'
}

BUILDING_WORDS = {
    'mill', 'mills', 'works', 'stores', 'office', 'offices', 'cott', 'cottage',
    'house', 'villa', 'club', 'hotel', 'inn', 'arms', 'tavern', 'depot', 'wharf',
    'yard', 'church', 'chapel', 'school', 'hospital', 'farm', 'brewery', 'ltd'
}

CANONICAL_TRADE_MAP = {
    'eng driver': 'Engine Driver', 'engine driver': 'Engine Driver', 'eng dvr': 'Engine Driver',
    'labr': 'Labourer', 'labourer': 'Labourer', 'mason': 'Mason',
    'chauffeur': 'Chauffeur', 'traveller': 'Traveller', 'signal fitter': 'Signal Fitter',
    'moulder': 'Moulder', 'porter': 'Porter', 'painter': 'Painter',
    'carpenter': 'Carpenter', 'boilermkr': 'Boilermaker', 'dock labr': 'Dock Labourer',
    'ironworker': 'Ironworker', 'ironwkr': 'Ironworker', 'ironwrk': 'Ironworker',
    'fitter': 'Fitter', 'fireman': 'Fireman', 'clerk': 'Clerk', 'grocer': 'Grocer',
    'haulier': 'Haulier', 'baker': 'Baker', 'striker': 'Striker', 'shoeng smth': 'Shoeing Smith',
    'shoemaker': 'Shoemaker', 'watchmkr': 'Watchmaker', 'watchmaker': 'Watchmaker',
    'tailor': 'Tailor', 'greengrocer': 'Greengrocer', 'hairdresser': 'Hairdresser',
    'g.w.r': 'G.W.R', 'g. w. r': 'G.W.R', 'g.w.r.': 'G.W.R', 'police con': 'Police Constable',
    'wine mercht': 'Wine Merchant', 'puddler': 'Puddler', 'smith': 'Smith',
    'whitesmith': 'Whitesmith', 'seaman': 'Seaman', 'policeman': 'Policeman',
    'stoker': 'Stoker', 'bricklyr': 'Bricklayer', 'foundryman': 'Foundryman',
    'boatman': 'Boatman', 'crane driver': 'Crane Driver', 'draper': 'Draper',
    'surgeon': 'Surgeon', 'gasfitter': 'Gasfitter', 'contractor': 'Contractor',
    'com. agent': 'Commission Agent', 'salesman': 'Salesman', 'platelyr': 'Platelayer',
    'guard': 'Guard', 'carrier': 'Carrier', 'collier': 'Collier', 'mariner': 'Mariner',
    'waterman': 'Waterman', 'stevedore': 'Stevedore', 'railway guard': 'Railway Guard',
    'engine cleaner': 'Engine Cleaner', 'railwayman': 'Railwayman', 'signalman': 'Signalman',
    'postman': 'Postman', 'wheelwright': 'Wheelwright', 'cabinet maker': 'Cabinet Maker',
    'fishmonger': 'Fishmonger', 'bootmaker': 'Bootmaker', 'shunter': 'Shunter',
    'timber merchant': 'Timber Merchant', 'coal merchant': 'Coal Merchant',
    'general dealer': 'General Dealer', 'ironfounder': 'Ironfounder',
    'engine dvr': 'Engine Driver', 'crane dvr': 'Crane Driver', 'dvr': 'Driver',
    'gardenar': 'Gardener', 'lamplightr': 'Lamplighter', 'hoisman': 'Hoistman'
}

pat_comma_lead = re.compile(r'^(\d+[a-zA-Z]?),\s*(.+)$')
pat_comma_trail = re.compile(r'^(.+?),\s*(\d+[a-zA-Z]?)$')
pat_sep_trail = re.compile(r'^([a-zA-Z\s\.\'\-]+?)[\s\-]+(\d+[a-zA-Z]?)$')
pat_attached_trail = re.compile(r'^([a-zA-Z\s\.\'\-]+?)(\d+[a-zA-Z]?)$')




def load_dict_words():
    words = set()
    if os.path.exists("/usr/share/dict/words"):
        with open("/usr/share/dict/words", "r", encoding="utf-8", errors="ignore") as f:
            words.update(w.strip().lower() for w in f)
    # Domain specific compound words & trades
    words.update([
        "lockgateman", "burnerman", "wholesaleman", "tugboatman", "tugman", "dockman",
        "glassworker", "hosemaker", "shoemaker", "boilermaker", "wheelwright", "cartman",
        "stevedore", "brickmaker", "bottlemaker", "basketmaker", "lamplighter", "stableman",
        "billposter", "cellarman", "timberman", "haycutter", "signwriter", "ironworker",
        "steelworker", "engine", "gasfitter", "tinsmith", "newsagent", "cabdriver",
        "tubeworker", "fuelworker", "quarryman", "linotype", "roadman", "milkman",
        "vanman", "millman", "tallyman", "gateman", "weighman", "railwayman", "motorman",
        "sheetweigher", "patternmaker", "coachbuilder", "coachsmith", "brakesman",
        "fruit", "fish", "bookbinder", "laundryman", "haulage", "deal", "scale",
        "frame", "boiler", "dental", "greaser", "plater", "scaler", "captain",
        "bailiff", "junior", "night", "barrister", "excavator", "wire", "hose"
    ])
    return words

def fix(dry_run=False):
    t0 = time.time()
    print(f"{'Simulating' if dry_run else 'Applying'} split trade fixes on {DATA_CSV}...")
    
    dict_words = load_dict_words()
    temp_csv = DATA_CSV + ".tmp"
    modified_count = 0
    total_count = 0
    counts_by_cat = {
        "prefix": 0, "compound": 0, "co_surname": 0, "house_name": 0,
        "name_bleed": 0, "dynamic_fragment": 0, "anomaly": 0,
        "comma_occupation": 0, "split_occupation": 0, "split_house_name": 0,
        "rutland_bleed": 0, "trade_numbers": 0
    }


    with open(DATA_CSV, "r", encoding="utf-8") as f_in, open(temp_csv, "w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for r in reader:
            total_count += 1
            sn = r.get("surname", "")
            fn = r.get("forename", "")
            tr = r.get("trade", "")
            changed = False

            # 1. RichardsC.H.telegraphist anomaly
            if sn == "RichardsC.H.telegraphist":
                r["surname"] = "Richards"
                r["forename"] = "C. H."
                r["trade"] = "Telegraphist"
                changed = True
                counts_by_cat["anomaly"] += 1

            # Marion Street 78 anomaly: Fruiturer Fi & + shmonger -> Fruiterer & Fishmonger
            elif "Fi &" in sn and tr == "shmonger":
                r["surname"] = ""
                r["forename"] = "Mrs Mary"
                r["trade"] = "Fruiterer & Fishmonger"
                changed = True
                counts_by_cat["anomaly"] += 1

            # 1898 Rutland Place bleed
            elif r.get("year") == "1898" and "ewellyn-Jones" in tr:
                if fn.endswith(" Llewellyn"):
                    r["forename"] = fn[:-10].strip()
                if "," in tr:
                    r["trade"] = tr.split(",", 1)[1].strip().title()
                else:
                    r["trade"] = ""
                changed = True
                counts_by_cat["rutland_bleed"] += 1

            # 2. 1936 'Co' in surname with forename blank
            elif not fn and sn.endswith(" Co") and tr in CO_SURNAME_MAP:
                name_clean = sn[:-3].strip()
                tokens = name_clean.split()
                if len(tokens) >= 2:
                    r["surname"] = tokens[-1]
                    r["forename"] = " ".join(tokens[:-1])
                else:
                    r["surname"] = name_clean
                    r["forename"] = ""
                r["trade"] = CO_SURNAME_MAP[tr]
                changed = True
                counts_by_cat["co_surname"] += 1

            elif fn and tr:
                tokens = fn.split()
                if tokens:
                    last_fn = tokens[-1].rstrip(".,")
                    
                    # 3. Single-word prefix repairs (explicit canonical list)
                    for pref, pat, target in REPAIR_SPECS:
                        if last_fn.lower() == pref.lower() and re.search(pat, tr, re.I):
                            if len(tokens) > 1:
                                r["forename"] = " ".join(tokens[:-1]).strip(" ,.")
                            else:
                                r["forename"] = ""
                            r["trade"] = re.sub(pat, target, tr, flags=re.I)
                            changed = True
                            counts_by_cat["prefix"] += 1
                            break

                    # 4. Compound two-word trade repairs
                    if not changed:
                        for fn_pat, tr_pat, target in COMPOUND_REPAIRS:
                            if re.search(fn_pat, fn, re.I) and re.search(tr_pat, tr, re.I):
                                r["forename"] = re.sub(fn_pat, "", fn, flags=re.I).strip(" ,.")
                                r["trade"] = target
                                changed = True
                                counts_by_cat["compound"] += 1
                                break

                    # 5. House / Villa names in trade column
                    if not changed:
                        for pref, suffix, house_name in HOUSE_NAME_SPECS:
                            if last_fn.lower() == pref.lower() and tr.strip().lower() == suffix.lower():
                                if len(tokens) > 1:
                                    r["forename"] = " ".join(tokens[:-1]).strip(" ,.")
                                else:
                                    r["forename"] = ""
                                if not r.get("building_name"):
                                    r["building_name"] = house_name
                                r["trade"] = ""
                                changed = True
                                counts_by_cat["house_name"] += 1
                                break

                    # 6. Dynamic algorithmic fragment repair (covers all remaining directory splits)
                    if not changed and tr and tr[0].islower():
                        tr_parts = tr.split()
                        first_word = tr_parts[0]
                        if first_word.lower() not in VALID_STANDALONE and 2 <= len(last_fn) <= 3 and last_fn.isalpha() and last_fn[0].isupper():
                            comb_first = (last_fn + first_word).lower()
                            if comb_first in dict_words or (len(tr_parts) > 1 and (last_fn + tr).lower() in dict_words):
                                full_comb = (comb_first.title() + (" " + " ".join(tr_parts[1:]) if len(tr_parts) > 1 else "")).strip()
                                new_fn = " ".join(tokens[:-1]).strip(" ,.") if len(tokens) > 1 else ""
                                
                                # A. Forename bleed: e.g. 'Vernon Wi' + 'lliam' -> 'Vernon William'
                                if comb_first in COMMON_FORENAMES and len(tr_parts) == 1:
                                    r["forename"] = f"{new_fn} {comb_first.title()}".strip()
                                    r["trade"] = ""
                                    counts_by_cat["name_bleed"] += 1
                                # B. House name: e.g. 'Albert E Th' + 'e Knoll' -> 'The Knoll'
                                elif any(w.lower().rstrip(".,") in HOUSE_INDICATORS for w in tr_parts) or comb_first.title() in ["The", "Cromer", "Cedar", "Rose", "Fairy", "Oak", "Elm"]:
                                    if not r.get("building_name"):
                                        r["building_name"] = full_comb
                                    r["trade"] = ""
                                    r["forename"] = new_fn
                                    counts_by_cat["house_name"] += 1
                                # C. Genuine occupation: e.g. 'James Fi' + 'sh Shop' -> 'Fish Shop'
                                else:
                                    r["trade"] = full_comb
                                    r["forename"] = new_fn
                                    counts_by_cat["dynamic_fragment"] += 1
                                changed = True

                    # 7. Systematic column boundary shift repair (1936 and historical directories)
                    if not changed and tr and tr[0].islower():
                        if len(tokens) >= 2 and 2 <= len(last_fn) <= 3 and last_fn.isalpha() and last_fn[0].isupper():
                            first_tr_word = tr.split()[0].rstrip('.,;')
                            if first_tr_word.lower() not in VALID_STANDALONE:
                                comb_full = (last_fn + tr)[0].upper() + (last_fn + tr)[1:]
                                new_fn = " ".join(tokens[:-1]).strip(" ,.")
                                c_lower = comb_full.lower()

                                # A. Comma cases: "Edgecote, Bus Driver", "Albert, Warehouseman", "Kerslake's Flour Mills, haulier"
                                if "," in comb_full:
                                    p1, p2 = [p.strip() for p in comb_full.split(",", 1)]
                                    p1_lower = p1.lower()
                                    p2_words = re.findall(r"[a-z']+", p2.lower())
                                    if any(w in OCCUPATION_KEYWORDS or w in VALID_STANDALONE or any(w.endswith(k) for k in ('maker', 'makers', 'worker', 'workers', 'driver', 'drivers', 'vendor', 'dealer', 'keeper', 'smith', 'man', 'men')) for w in p2_words) or any(bw in p1_lower.split() for bw in BUILDING_WORDS):
                                        # Format trade
                                        trade_clean = p2.title()

                                        if p2.lower() == 'g.w.r':
                                            trade_clean = 'G.W.R'
                                        elif 'ironworker' in p2.lower():
                                            trade_clean = 'Ironworker'
                                        elif 'steelworker' in p2.lower():
                                            trade_clean = 'Steelworker'
                                        elif 'wagon repairer' in p2.lower():
                                            trade_clean = 'Wagon Repairer'
                                        elif 'ins agent' in p2.lower():
                                            trade_clean = 'Insurance Agent'
                                        elif 'bus driver' in p2.lower():
                                            trade_clean = 'Bus Driver'
                                        elif 'commission agent' in p2.lower():
                                            trade_clean = 'Commission Agent'
                                        elif 'do. [ironworker]' in p2.lower():
                                            trade_clean = 'Ironworker'
                                        elif p2.lower() in ('labourer', "labour'r"):
                                            trade_clean = 'Labourer'
                                        
                                        r["trade"] = trade_clean
                                        if p1_lower in COMMON_MIDDLE_NAMES or p1_lower == 'hnry':
                                            r["forename"] = f"{new_fn} {'Henry' if p1_lower == 'hnry' else p1.title()}".strip()
                                        else:
                                            if not r.get("building_name"):
                                                bld = p1
                                                if 'urbe' in p1_lower:
                                                    bld = 'Rus-in-Urbe'
                                                elif 'brest' in p1_lower:
                                                    bld = 'Cae Brest'
                                                r["building_name"] = bld
                                            r["forename"] = new_fn
                                        changed = True
                                        counts_by_cat["comma_occupation"] += 1

                                # B. Direct known occupations: e.g. "Patternmakers", "Cafe", "Newsvendor", "Boilermaker"
                                elif not changed and c_lower in OCCUPATION_MAP:
                                    r["trade"] = OCCUPATION_MAP[c_lower]
                                    r["forename"] = new_fn
                                    changed = True
                                    counts_by_cat["split_occupation"] += 1

                                # C. General occupational words
                                elif not changed and any(w in OCCUPATION_KEYWORDS or w in VALID_STANDALONE or any(w.endswith(k) for k in ('maker', 'makers', 'worker', 'workers', 'driver', 'drivers', 'vendor', 'dealer', 'keeper', 'smith', 'man', 'men')) for w in re.findall(r"[a-z']+", c_lower)):
                                    r["trade"] = comb_full.title()
                                    r["forename"] = new_fn
                                    changed = True
                                    counts_by_cat["split_occupation"] += 1

                                # D. House / Villa names or private residences in trade column: clear trade!
                                elif not changed:
                                    if not r.get("building_name") and not any(t in comb_full.lower().split() for t in ('mrs', 'miss', 'dr', 'rev', 'colonel', 'capt', 'misses', 'residents')):
                                        r["building_name"] = comb_full
                                    r["trade"] = ""
                                    r["forename"] = new_fn
                                    changed = True
                                    counts_by_cat["split_house_name"] += 1

            # 8. Embedded house number repair
            if not changed and tr:
                for pat, is_lead in [(pat_comma_lead, True), (pat_comma_trail, False), (pat_sep_trail, False), (pat_attached_trail, False)]:
                    m = pat.match(tr)
                    if m:
                        num = m.group(1 if is_lead else 2).strip()
                        tp = m.group(2 if is_lead else 1).strip(' ,-')
                        tp_lower = tp.lower()
                        if tp_lower in CANONICAL_TRADE_MAP or tp_lower in VALID_STANDALONE or any(w in OCCUPATION_KEYWORDS for w in tp_lower.split()):
                            target_tr = CANONICAL_TRADE_MAP.get(tp_lower, tp.title())
                            if not r.get("house_number", "").strip():
                                r["house_number"] = num
                            r["trade"] = target_tr
                            changed = True
                            counts_by_cat["trade_numbers"] += 1
                            break

            if changed:
                modified_count += 1

            writer.writerow(r)

    if dry_run:
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
        print(f"Dry run complete: {modified_count:,} records would be fixed.")
        for cat, cnt in counts_by_cat.items():
            print(f"  - {cat:20}: {cnt:,} records")
    else:
        shutil.move(temp_csv, DATA_CSV)
        print(f"Successfully fixed {modified_count:,} records across {DATA_CSV} in {time.time() - t0:.2f}s.")
        for cat, cnt in counts_by_cat.items():
            print(f"  - {cat:20}: {cnt:,} records")
        
        # Rebuild indexes
        print("Rebuilding trades data index...")
        import build_trades_data
        build_trades_data.build()

        print("Rebuilding site data and search index...")
        import build_site_data
        build_site_data.main()

if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    fix(dry_run=dry)
