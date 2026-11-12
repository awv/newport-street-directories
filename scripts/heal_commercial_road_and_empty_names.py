import csv
import os
import re
import shutil

CSV_PATH = "data.csv"
BACKUP_PATH = "data.csv.bak_before_empty_name_healing"

TRADE_EXPANSIONS = {
    'boardg ho': 'Boarding House',
    'board house': 'Boarding House',
    'lodging ho': 'Lodging House',
    'lodgings': 'Lodgings',
    'restrnt': 'Restaurant',
    'restaurant': 'Restaurant',
    'conf & tobac': 'Confectioner & Tobacconist',
    'comf & tobac': 'Confectioner & Tobacconist',
    'conf': 'Confectioner',
    'confectioner': 'Confectioner',
    'confectioners': 'Confectioners',
    'tobac': 'Tobacconist',
    'tobacn': 'Tobacconist',
    'tobacnst': 'Tobacconist',
    'tobacconist': 'Tobacconist',
    'butcher': 'Butcher',
    'btchr': 'Butcher',
    'btchrs': 'Butchers',
    'pk btcher and bacon curer': 'Pork Butcher & Bacon Curer',
    'pork btchi': 'Pork Butcher',
    'pork butcher': 'Pork Butcher',
    'grocer': 'Grocer',
    'grocers': 'Grocers',
    'draper': 'Draper',
    'drapers': 'Drapers',
    'hairdr': 'Hairdresser',
    'hairdsr': 'Hairdresser',
    'hairdresser': 'Hairdresser',
    'chemist': 'Chemist',
    'chemists': 'Chemists',
    'chmst': 'Chemist',
    'chmsts': 'Chemists',
    'statnr': 'Stationer',
    'greengrocer': 'Greengrocer',
    'greengrocers': 'Greengrocers',
    'grngcr': 'Greengrocer',
    'gngrc': 'Greengrocer',
    'fruiterer': 'Fruiterer',
    'fruiterers': 'Fruiterers',
    'tailor': 'Tailor',
    'tailors': 'Tailors',
    'bootmakers': 'Bootmakers',
    'bootmaker': 'Bootmaker',
    'boot dlr': 'Boot Dealer',
    'boot dlrs': 'Boot Dealers',
    'dry cln\'rs, boot dlrs': 'Dry Cleaners & Boot Dealers',
    'wrdrb dlr': 'Wardrobe Dealer',
    'outfitters': 'Outfitters',
    'purveyors': 'Purveyors',
    'house furn': 'House Furnisher',
    'house furnisher': 'House Furnisher',
    'fish bar': 'Fish Bar',
    'fishmonger': 'Fishmonger',
    'miller': 'Miller',
    'laundry': 'Laundry',
    'dairy': 'Dairy',
    'clothier': 'Clothier',
    'fancy dealer': 'Fancy Dealer',
    'funeral director': 'Funeral Director',
    'engineer': 'Engineer',
    'labourer': 'Labourer',
    'crane dvr': 'Crane Driver',
    'physician and surgeon': 'Physician & Surgeon',
}

def clean_trade_text(tr):
    # Fix stray commas in initials like 'S., D.' -> 'S. D.'
    tr = re.sub(r'\b([A-Z]\.),\s*([A-Z]\.)\b', r'\1 \2', tr)
    return tr

def standardize_trade(tr):
    t = tr.strip(' ,.')
    t_lower = t.lower()
    if t_lower in TRADE_EXPANSIONS:
        return TRADE_EXPANSIONS[t_lower]
    # Check if capitalized nicely
    if t.islower():
        return t.title()
    return t

def parse_empty_name_trade(trade_str, bld_str=''):
    tr = clean_trade_text(trade_str.strip())
    if not tr or tr.lower() in ('void', 'unoccupied', 'vacant', 'building', 'empty', 'site', 'vacant site', 'vacant sites', 'shop void', 'house void', 'two houses void', 'three houses void'):
        return None

    # Handle dash separator e.g. 'Decorator Supply—C. A. Smith'
    if '—' in tr or ' - ' in tr:
        sep = '—' if '—' in tr else ' - '
        left, right = tr.split(sep, 1)
        left, right = left.strip(), right.strip()
        m = re.match(r'^((?:(?:Mrs|Mr|Miss|Rev|Dr)\.?\s*)?[A-Z][a-z]*\.?(?:\s+[A-Z]\.?)*)\s+([A-Z][a-z]+)(?:\s+(manager|mgr|agent|sec|secretary))?$', right, re.IGNORECASE)
        if m:
            fn_val, sn_val, role = m.groups()
            trade_val = role.title() if role else ''
            bld_val = f'{bld_str}, {left}'.strip(', ') if bld_str else left
            return {'surname': sn_val, 'forename': fn_val, 'building_name': bld_val, 'trade': trade_val}
        elif any(k in left.lower() for k in ['supply', 'works', 'stores', 'depot', 'ltd']):
            return {'surname': left, 'forename': '', 'building_name': bld_str, 'trade': standardize_trade(right)}

    # Handle 'Half-price Shop, Ludzker B., clothier'
    m_shop = re.match(r'^([A-Za-z\s\'-]+(?:Shop|Stores|Hotel|Inn|Depot|Bazaar|Rooms|Works)),\s*([A-Z][a-z]+)\s+([A-Z]\.?),\s*(.*)$', tr)
    if m_shop:
        bld_val, sn_val, fn_val, tr_val = m_shop.groups()
        bld_val = f'{bld_str}, {bld_val}'.strip(', ') if bld_str else bld_val
        return {'surname': sn_val, 'forename': fn_val, 'building_name': bld_val, 'trade': standardize_trade(tr_val)}

    # Handle manager pattern with business: 'X.L., wine, spirit and beer stores, W. C. Hacker, mgr'
    m_mgr = re.match(r'^(.*?),\s*((?:[A-Z]\.?\s*)+)\s+([A-Z][a-z]+),\s*(mgr|manager|sec|secretary)$', tr, re.IGNORECASE)
    if m_mgr:
        bld_entity, fn_val, sn_val, role = m_mgr.groups()
        bld_entity = bld_entity.strip(' ,')
        return {'surname': sn_val, 'forename': fn_val.strip(), 'building_name': bld_entity, 'trade': 'Manager' if 'm' in role.lower() else 'Secretary'}

    # Category A: Inverted pattern: [Forename/Initials/Title/Co], [Surname], [Trade/Optional]
    parts = [p.strip() for p in tr.split(',')]
    if len(parts) >= 2:
        p0, p1 = parts[0], parts[1]
        rest = ', '.join(parts[2:]).strip() if len(parts) > 2 else ''
        
        fn_pattern = r'^(?:(?:Mrs|Mr|Miss|Rev|Dr)\.?\s*)?(?:[A-Z][a-z]*\.?|[A-Z]\.)(?:\s*(?:&|and)\s*(?:[A-Z][a-z]*\.?|[A-Z]\.))?(?:\s+(?:[A-Z][a-z]*\.?|[A-Z]\.))*$'
        is_p0_fn = bool(re.match(fn_pattern, p0)) or ('&' in p0 or 'Sons' in p0 or 'Bros' in p0 or 'Co' in p0 or p0.lower() in ('bob', 'tom', 'john', 'richard', 'arthur', 'alfred', 'william', 'douglas', 'sidney', 'demesthenes', 'jas', 'chas', 'hy', 'wm', 'thos', 'geo', 'edwd', 'fredk'))
        
        if re.match(r'^[A-Z][a-z]+$', p1) and is_p0_fn:
            return {'surname': p1, 'forename': p0, 'building_name': bld_str, 'trade': standardize_trade(rest)}

    # Category B: Standard: Surname Forenames, Trade
    m_std = re.match(r'^([A-Z][a-z]+)\s+((?:(?:Mrs|Mr|Miss|Rev|Dr)\.?\s*)?[A-Z]\.(?:\s*[A-Z]\.?)*(?:\s*&\s*[A-Z]\.(?:\s*[A-Z]\.?)*)?),\s*(.*)$', tr)
    if m_std:
        sn_val, fn_val, tr_val = m_std.groups()
        return {'surname': sn_val, 'forename': fn_val, 'building_name': bld_str, 'trade': standardize_trade(tr_val)}

    # Category C: Company with comma: 'Boots, cash chemist', 'Eastman\'s Ltd., purveyors'
    if ',' in tr:
        co, tr_val = [x.strip() for x in tr.split(',', 1)]
        if any(k in co.lower() for k in ['ltd', 'limited', 'bros', 'sons', 'co.', 'society', 'bank', 'stores', 'bazaar', 'works', 'depot', 'boots']):
            return {'surname': co, 'forename': '', 'building_name': bld_str, 'trade': standardize_trade(tr_val)}

    # Known business entity without comma
    if any(k in tr.lower() for k in ['ltd', 'limited', 'co.', 'stores', 'bazaar', 'society', 'mission', 'church', 'salvation']):
        return {'surname': tr, 'forename': '', 'building_name': bld_str, 'trade': ''}

    return None

def heal_forename_buildings(fn, bld):
    # Extract building e.g. 'G. H. Falcon Inn' -> 'G. H.', 'Falcon Inn'
    m = re.match(r'^((?:(?:Mrs|Mr|Miss|Rev|Dr)\.?\s*)?(?:[A-Z]\.?(?:\s+[A-Z]\.?)*|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?))\s+((?:[A-Z][a-z\'-]+(?:\s+[A-Z][a-z\'-]+)*\s+)?(?:Inn|Hotel|Arms|Tavern|House|Villa|Cottage|Lodge|Vaults))$', fn)
    if m:
        new_fn = m.group(1).strip()
        new_bld_part = m.group(2).strip()
        new_bld = f'{bld}, {new_bld_part}'.strip(', ') if bld else new_bld_part
        return new_fn, new_bld
    return fn, bld

def run():
    print(f"Reading {CSV_PATH}...")
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

    if not os.path.exists(BACKUP_PATH):
        shutil.copyfile(CSV_PATH, BACKUP_PATH)
        print(f"Created backup at {BACKUP_PATH}")

    healed_names_count = 0
    healed_bld_count = 0
    comm_1927_healed = 0
    new_rows = []

    for r in reader:
        row = dict(r)
        st = row.get("street", "").strip()
        yr = row.get("year", "").strip()
        hn = row.get("house_number", "").strip()
        bld = row.get("building_name", "").strip()
        sn = row.get("surname", "").strip()
        fn = row.get("forename", "").strip()
        tr = row.get("trade", "").strip()

        # 1. Building extraction from forename
        new_fn, new_bld = heal_forename_buildings(fn, bld)
        if new_fn != fn or new_bld != bld:
            row["forename"] = new_fn
            row["building_name"] = new_bld
            healed_bld_count += 1
            bld = new_bld
            fn = new_fn

        # 2. Empty-name trade parsing
        if not sn and not fn and tr:
            res = parse_empty_name_trade(tr, bld)
            if res:
                row["surname"] = res["surname"]
                row["forename"] = res.get("forename", "")
                row["building_name"] = res.get("building_name", "")
                row["trade"] = res.get("trade", "")
                healed_names_count += 1
                if st == "Commercial Road" and yr == "1927":
                    comm_1927_healed += 1

        new_rows.append(row)

    print(f"Total empty-name records healed across dataset: {healed_names_count}")
    print(f"Commercial Road (1927) records healed: {comm_1927_healed}")
    print(f"Total building names extracted from forenames: {healed_bld_count}")

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_rows)

    print(f"Successfully wrote updated {CSV_PATH}")

if __name__ == "__main__":
    run()
