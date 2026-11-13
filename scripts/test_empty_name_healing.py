import csv
import re

def clean_trade_text(tr):
    # Fix stray commas in initials like 'S., D.' -> 'S. D.'
    tr = re.sub(r'\b([A-Z]\.),\s*([A-Z]\.)\b', r'\1 \2', tr)
    return tr

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
            trade_val = role if role else ''
            bld_val = f'{bld_str}, {left}'.strip(', ') if bld_str else left
            return {'surname': sn_val, 'forename': fn_val, 'building_name': bld_val, 'trade': trade_val}
        elif any(k in left.lower() for k in ['supply', 'works', 'stores', 'depot', 'ltd']):
            return {'surname': left, 'forename': '', 'building_name': bld_str, 'trade': right}

    # Handle 'Half-price Shop, Ludzker B., clothier'
    m_shop = re.match(r'^([A-Za-z\s\'-]+(?:Shop|Stores|Hotel|Inn|Depot|Bazaar|Rooms|Works)),\s*([A-Z][a-z]+)\s+([A-Z]\.?),\s*(.*)$', tr)
    if m_shop:
        bld_val, sn_val, fn_val, tr_val = m_shop.groups()
        bld_val = f'{bld_str}, {bld_val}'.strip(', ') if bld_str else bld_val
        return {'surname': sn_val, 'forename': fn_val, 'building_name': bld_val, 'trade': tr_val}

    # Handle manager pattern with business: 'X.L., wine, spirit and beer stores, W. C. Hacker, mgr'
    # or '... — J. O. Cresswell manager'
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
            return {'surname': p1, 'forename': p0, 'building_name': bld_str, 'trade': rest}

    # Category B: Standard: Surname Forenames, Trade
    m_std = re.match(r'^([A-Z][a-z]+)\s+((?:(?:Mrs|Mr|Miss|Rev|Dr)\.?\s*)?[A-Z]\.(?:\s*[A-Z]\.?)*(?:\s*&\s*[A-Z]\.(?:\s*[A-Z]\.?)*)?),\s*(.*)$', tr)
    if m_std:
        sn_val, fn_val, tr_val = m_std.groups()
        return {'surname': sn_val, 'forename': fn_val, 'building_name': bld_str, 'trade': tr_val}

    # Category C: Company with comma: 'Boots, cash chemist', 'Eastman\'s Ltd., purveyors'
    if ',' in tr:
        co, tr_val = [x.strip() for x in tr.split(',', 1)]
        if any(k in co.lower() for k in ['ltd', 'limited', 'bros', 'sons', 'co.', 'society', 'bank', 'stores', 'bazaar', 'works', 'depot', 'boots']):
            return {'surname': co, 'forename': '', 'building_name': bld_str, 'trade': tr_val}

    # Known business entity without comma
    if any(k in tr.lower() for k in ['ltd', 'limited', 'co.', 'stores', 'bazaar', 'society', 'mission', 'church', 'salvation']):
        return {'surname': tr, 'forename': '', 'building_name': bld_str, 'trade': ''}

    return None

def heal_forename_buildings(fn, bld):
    # Extract 'Falcon Inn' from 'G. H. Falcon Inn'
    m = re.match(r'^((?:(?:Mrs|Mr|Miss|Rev|Dr)\.?\s*)?(?:[A-Z]\.?(?:\s+[A-Z]\.?)*|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?))\s+((?:[A-Z][a-z\'-]+(?:\s+[A-Z][a-z\'-]+)*\s+)?(?:Inn|Hotel|Arms|Tavern|House|Villa|Cottage|Lodge|Vaults))$', fn)
    if m:
        new_fn = m.group(1).strip()
        new_bld_part = m.group(2).strip()
        new_bld = f'{bld}, {new_bld_part}'.strip(', ') if bld else new_bld_part
        return new_fn, new_bld
    return fn, bld

with open('data.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

healed_empty_names = 0
healed_buildings = 0
by_year = {}

for r in rows:
    sn = r.get('surname', '').strip()
    fn = r.get('forename', '').strip()
    bld = r.get('building_name', '').strip()
    tr = r.get('trade', '').strip()

    # Check building in forename
    new_fn, new_bld = heal_forename_buildings(fn, bld)
    if new_fn != fn:
        healed_buildings += 1

    # Check empty name
    if not sn and not fn and tr:
        res = parse_empty_name_trade(tr, bld)
        if res:
            healed_empty_names += 1
            yr = r['year']
            by_year[yr] = by_year.get(yr, 0) + 1

print(f"Total empty-name records healed: {healed_empty_names}")
print(f"Total buildings extracted from forenames: {healed_buildings}")
print("Yearly breakdown of name healings:")
for yr, cnt in sorted(by_year.items()):
    print(f"  {yr}: {cnt} healed")
