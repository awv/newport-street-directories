#!/usr/bin/env python3
"""
run_phase1_cleanup.py
---------------------
Executes Phase 1 automated bulk cleanup on data.csv:
1. Safe consecutive ditto forward-fill & compound ditto resolution
2. Pure symbols & rule lines wiping (|, _, —, etc.)
3. Floating suffixes, code leaks, and (return) wiping (nan, etc, &c, (return))
4. Waypoints and street cross-junction markers wiping (here is..., from...)
5. Standard abbreviations expansion (P.O -> Post Office, Eng -> Engineer, etc.)
6. Clipped name syllable wiping (nry, hn, mes, ria, cot, yn, op, id, ma)
7. Trailing noise stripping from valid trades ('Grocer, etc' -> 'Grocer')
8. Symbol noise stripping from clean trades ('labourer [ ] [ ] [ ]' -> 'Labourer')
9. Leaked forename initials stripping ('Wm. Labourer' -> 'Labourer')

Automatically rebuilds data/trades.json and the site search index.
"""

import csv
import json
import os
import re
import shutil
import sys
import time
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "scripts" else SCRIPT_DIR
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")

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
    'nry', 'hn', 'mes', 'ria', 'cot', 'yn', 'id', 'ma', 'ho', 'es', 'nes', 'sh', 'op', 'bl', 'de'
}

TEST_FORENAMES = re.compile(
    r'^(?:(?:Wm|Hy|Thos|Geo|Chas|John|Jas|Saml|Fred|Edwd|Arth|Walt|Danl|Richd|Robt|David|James|William|Thomas|Henry|George|Charles|Alfred)\b\.?),?\s+([A-Za-z].*)$',
    re.I
)

TRAILING_NOISE = re.compile(r'[\s,]+(?:etc|&c|\(?return\)?)\.?$', re.I)
PURE_SUFFIX_REGEX = re.compile(r'^(?:&c|etc\.?|nan|\(?return\)?\.?)$', re.I)

def main():
    t0 = time.time()
    print(f"Reading {DATA_CSV} for Phase 1 automated cleanup...")
    
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    fieldnames = list(rows[0].keys()) if rows else []
    total_records = len(rows)
    stats = Counter()
    replacements = Counter()

    for i, r in enumerate(rows):
        raw = (r.get("trade") or "").strip()
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
        elif PURE_SUFFIX_REGEX.fullmatch(raw):
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
            r['trade'] = new_t
            replacements[(raw, new_t)] += 1

    # Write updated CSV
    temp_csv = DATA_CSV + ".tmp"
    with open(temp_csv, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    shutil.move(temp_csv, DATA_CSV)
    print(f"Successfully updated {sum(stats.values()):,} records across {DATA_CSV}!")
    print(f"Cleaned {len(replacements):,} distinct trade strings.")

    print("\nBreakdown of actions:")
    for k, v in sorted(stats.items()):
        print(f"  {k:30s}: {v:,} records")

    # Rebuild trades data
    print("\nRebuilding data/trades.json...")
    try:
        import build_trades_data
        build_trades_data.build()
    except Exception as e:
        print(f"Warning: Could not rebuild trades data: {e}")

    # Rebuild site data and search index
    print("\nRebuilding site data and search index...")
    try:
        import build_site_data
        build_site_data.main()
    except Exception as e:
        print(f"Warning: Could not rebuild site data: {e}")

    print(f"\nPhase 1 cleanup complete in {time.time() - t0:.2f}s!")

if __name__ == "__main__":
    main()
