import csv
import re
from collections import Counter

KNOWN_ABBREVS = {
    'p.o': 'Post Office',
    'p.o.': 'Post Office',
    'eng': 'Engineer',
    'p.c': 'Police Constable',
    'p.c.': 'Police Constable',
    'agt': 'Agent',
    'wkr': 'Worker',
    'j.p': 'Justice of the Peace',
    'j.p.': 'Justice of the Peace',
    'mcht': 'Merchant',
    'labr': 'Labourer',
    'lbr': 'Labourer',
    'clk': 'Clerk',
    'ptr': 'Painter',
    'dvr': 'Driver',
    'drvr': 'Driver',
    'trm': 'Trimmer',
}

KNOWN_NAME_LEAKS = {
    'nry', 'hn', 'mes', 'ria', 'cot', 'yn', 'id', 'ma', 'ho', 'es', 'nes', 'sh', 'op'
}

TEST_FORENAMES = re.compile(
    r'^(?:(?:Wm|Hy|Thos|Geo|Chas|John|Jas|Saml|Fred|Edwd|Arth|Walt|Danl|Richd|Robt|David|James|William|Thomas|Henry|George|Charles|Alfred)\b\.?),?\s+([A-Za-z].*)$',
    re.I
)

TRAILING_NOISE = re.compile(r'[\s,]+(?:etc|&c|\(return\)|return)\.?$', re.I)

with open('data.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

total_records = len(rows)
stats = Counter()
replacements = Counter()

for i, r in enumerate(rows):
    raw = (r.get('trade') or '').strip()
    if not raw:
        continue
    
    t_low = raw.lower()
    new_t = raw

    # 1. Compound dittos
    m_bracket = re.match(r'^(?:do\.?|ditto)\s*[\.,\-]?\s*\[(.*?)\]', raw, re.I)
    m_sep = re.match(r'^(?:do\.?|ditto)\s*[,]\s*([a-zA-Z].*)$', raw, re.I)
    if m_bracket:
        sub = m_bracket.group(1).strip()
        new_t = sub.capitalize() if len(sub) > 1 else sub.upper()
        stats['compound_ditto'] += 1
    elif m_sep:
        sub = m_sep.group(1).strip()
        if sub.lower() in ('ironworker', 'ironwrkr', 'ironwrk', 'irworker'):
            new_t = 'Ironworker'
        elif sub.lower() in ('labourer',):
            new_t = 'Labourer'
        elif sub.lower() in ('plasterer',):
            new_t = 'Plasterer'
        elif sub.lower() in ('stoker',):
            new_t = 'Stoker'
        elif sub.lower() in ('g.w.r',):
            new_t = 'G.W.R'
        else:
            new_t = sub.capitalize()
        stats['compound_ditto'] += 1

    # 2. Standalone dittos (unbroken chain resolution)
    elif t_low in ('do', 'ditto', 'do.', 'ditto.'):
        yr = r.get('year')
        st = r.get('street')
        found_trade = ''
        chain_broken = False
        
        for dist in range(1, 50):
            idx = i - dist
            if idx < 0:
                chain_broken = True
                break
            prev = rows[idx]
            if prev.get('year') != yr or prev.get('street') != st:
                chain_broken = True
                break
            prev_t = (prev.get('trade') or '').strip()
            prev_t_low = prev_t.lower()
            if prev_t_low in ('do', 'ditto', 'do.', 'ditto.'):
                continue
            elif prev_t:
                found_trade = prev_t
                break
            else:
                chain_broken = True
                break
                
        if found_trade and not chain_broken:
            lead = found_trade
            if lead.lower() in ('glass', 'glass works', 'glass workr'): lead = 'Glass Worker'
            elif lead.lower() in ('ironwrk', 'ironwrkr', 'ironworkr'): lead = 'Ironworker'
            elif lead.lower() in ('factory hd', 'hd'): lead = 'Factory Hand'
            elif lead.lower() in ('gas works',): lead = 'Gas Worker'
            elif lead.lower().startswith('do, '):
                lead = lead[4:].strip().capitalize()
            elif lead.lower().startswith('do. '):
                lead = lead[4:].strip().capitalize()
            elif lead[0].islower(): lead = lead.capitalize()
            new_t = lead
            stats['ditto_inherited'] += 1
        else:
            new_t = ''
            stats['ditto_cleared'] += 1

    # 3. Pure punctuation & rule line artifacts
    elif re.fullmatch(r'[-—_\|~`.,:;!?\'\"\\/\[\]{}()<>\s]+', raw):
        new_t = ''
        stats['pure_symbols_cleared'] += 1

    # 4. Floating suffixes & code artifacts
    elif re.fullmatch(r'(?:&c|etc\.?|nan|\(return\)|return\.?)', raw, re.I):
        new_t = ''
        stats['floating_suffixes_cleared'] += 1

    # 5. Street waypoints & cross-streets
    elif re.search(r'^(?:here is|here are|from \d+|the roundabout|\(?flat \d+|tel\.?|telephone)\b', raw, re.I):
        new_t = ''
        stats['waypoints_cleared'] += 1

    # 6. Known standard abbreviations
    elif t_low in KNOWN_ABBREVS:
        new_t = KNOWN_ABBREVS[t_low]
        stats['abbrev_expanded'] += 1

    # 7. Known clipped name endings
    elif t_low in KNOWN_NAME_LEAKS:
        new_t = ''
        stats['name_leaks_cleared'] += 1

    # 8. Trailing etc / &c / (return) on clean trades (e.g. 'Grocer, etc' -> 'Grocer')
    elif TRAILING_NOISE.search(raw):
        sub = TRAILING_NOISE.sub('', raw).strip()
        if sub and len(sub) > 2:
            new_t = sub.capitalize() if sub[0].islower() else sub
            stats['trailing_noise_stripped'] += 1

    # 9. Clean trade wrapped in symbol noise (trailing pipes, brackets, underscores)
    elif re.search(r'[,\;\|\s]+[\[\]_\-\|]+$', raw) or re.search(r'^[\[\(\]\)]+', raw):
        sub = re.sub(r'[,\;\|\s]+[\[\]_\-\|]+$', '', raw).strip()
        sub = re.sub(r'^[\[\(\]\)]+', '', sub).strip()
        if sub and len(sub) > 2 and sub.lower() not in ('house', 'villa', 'cottage'):
            new_t = sub.capitalize() if sub[0].islower() else sub
            stats['symbols_stripped_from_trade'] += 1

    # 10. Leaked forenames on clean trades: e.g. 'Wm. Labourer', 'Hy. clerk', 'John, fitter'
    elif TEST_FORENAMES.match(raw):
        m_name = TEST_FORENAMES.match(raw)
        sub = m_name.group(1).strip()
        if sub and len(sub) > 2 and not re.search(r'\d', sub) and not re.search(r'[;_\{\}\[\]\\\|]', sub):
            new_t = sub.capitalize() if sub[0].islower() else sub
            stats['name_prefix_stripped'] += 1

    if new_t != raw:
        replacements[(raw, new_t)] += 1

print('Phase 1 Refined Dry Run Summary:')
for k, v in sorted(stats.items()):
    print(f'  {k:30s}: {v:,} records')

total_updates = sum(stats.values())
print(f'\nTotal directory records that will be cleaned/updated: {total_updates:,}')
print(f'Total distinct trade strings repaired or cleared: {len(replacements):,}')

print('\nTop 25 repairs & cleanups:')
for (old, new), cnt in replacements.most_common(25):
    print(f'  {cnt:4d}: {repr(old)} -> {repr(new)}')
