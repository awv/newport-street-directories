#!/usr/bin/env python3
"""
fix_reverends_and_titles.py
===========================
1. Resolves Reverend column-shift anomalies across all years:
   - Specifically heals Rev. E. Lloyd Jones in York Place (1886, 1887, 1890, 1893)
     where 'Lloyd' was surname, 'Rev. E.' was forename, and 'Jones' was in trade.
   - Heals ~45 other clergymen where the surname was pushed into trade.
2. Heals ~157 titles/initials trapped in the trade field (e.g. Mrs., Wm., Miss).
3. Merges ~277 middle forenames pushed into trade into the forename field.
4. Normalizes remaining unverified street variants:
   - 'Price' (1893) -> 'Price Street'
   - 'St. Mark's Cres' -> 'St. Mark's Crescent'
   - 'St. Vincent's Road' -> 'St. Vincent Road'
   - 'Summer Hill Avenue' & 'Summer Hill Av' -> 'Summerhill Avenue'
   - 'Hoskin Street' -> 'Hoskins Street'
   - 'Court-y-bella Street' -> 'Courtybella Street'
5. Rebuilds site data and statistics.
"""

import os
import csv
import re
import shutil
import subprocess

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

DATA_CSV = os.path.join(PROJECT_DIR, "data.csv")

COMMON_FORENAMES = {
    'william', 'henry', 'george', 'thomas', 'james', 'charles', 'edward',
    'alfred', 'arthur', 'robert', 'david', 'richard', 'edmund', 'walter',
    'ernest', 'albert', 'frederick', 'john', 'francis', 'herbert', 'alexander'
}

STREET_FIXES = {
    'Price': 'Price Street',
    "St. Mark's Cres": "St. Mark's Crescent",
    "St. Vincent's Road": "St. Vincent Road",
    'Summer Hill Avenue': 'Summerhill Avenue',
    'Summer Hill Av': 'Summerhill Avenue',
    'Hoskin Street': 'Hoskins Street',
    'Court-y-bella Street': 'Courtybella Street',
}

def main():
    print("Reading data.csv...")
    records = []
    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            records.append(r)

    rev_fixes = 0
    title_fixes = 0
    middle_name_fixes = 0
    street_fixes = 0

    for r in records:
        st = r.get('street', '').strip()
        sn = r.get('surname', '').strip()
        fn = r.get('forename', '').strip()
        tr = r.get('trade', '').strip()
        bldg = r.get('building_name', '').strip()

        # 1. Street normalization
        if st in STREET_FIXES:
            r['street'] = STREET_FIXES[st]
            street_fixes += 1

        # 2. York Place Rev. E. Lloyd Jones
        if st == 'York Place' and sn == 'Lloyd' and 'Rev' in fn and 'Jones' in tr:
            r['surname'] = 'Jones'
            r['forename'] = 'Rev. E. Lloyd'
            if 'M.A.' in tr:
                r['trade'] = 'M.A.'
            else:
                r['trade'] = ''
            rev_fixes += 1
            continue

        # 3. Other Reverend column shifts
        if re.search(r'\bRev\b', sn, re.I) and tr and not any(w in tr.lower() for w in ['minister', 'vicar', 'curate', 'pastor', 'rector', 'baptist', 'methodist', 'congregational', 'priest', 'clergyman', 'wesleyan', 'chapel', 'church', 'b.a', 'm.a', 'd.d', 'b.d']):
            # tr contains the real surname (or surname + note)
            tr_parts = tr.split(',')
            real_sn = tr_parts[0].strip()
            extra_tr = ', '.join(tr_parts[1:]).strip() if len(tr_parts) > 1 else ''
            
            real_fn = sn # e.g. 'Rev. T. L.'
            real_bldg = fn if fn else bldg # e.g. "St. Mark's Vicarage" or "Seaton ldg"
            
            r['surname'] = real_sn
            r['forename'] = real_fn
            if real_bldg and not r.get('building_name'):
                r['building_name'] = real_bldg
            r['trade'] = extra_tr
            rev_fixes += 1
            continue

        # 4. Trapped titles/initials in trade (e.g. Mrs., Wm., Miss)
        tr_lower = tr.lower()
        if tr_lower in ['mrs', 'mrs.', 'wm', 'wm.', 'miss', 'mr', 'mr.', 'rev', 'rev.']:
            title = 'Mrs.' if 'mrs' in tr_lower else ('William' if 'wm' in tr_lower else tr.capitalize())
            if fn:
                if title == 'William':
                    r['forename'] = f"{fn} William".strip()
                elif not fn.startswith(title):
                    r['forename'] = f"{title} {fn}".strip()
            else:
                r['forename'] = title
            r['trade'] = ''
            title_fixes += 1
            continue

        # 5. Middle forenames pushed into trade
        if tr_lower in COMMON_FORENAMES and fn:
            trade_cap = tr.capitalize()
            if trade_cap not in fn:
                r['forename'] = f"{fn} {trade_cap}".strip()
            r['trade'] = ''
            middle_name_fixes += 1
            continue

    print(f"Applied fixes:")
    print(f"  Reverend column shifts resolved: {rev_fixes}")
    print(f"  Titles/initials healed: {title_fixes}")
    print(f"  Middle forenames merged: {middle_name_fixes}")
    print(f"  Streets normalized: {street_fixes}")

    # Write back
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print("Rebuilding site data and statistics...")
    subprocess.run(["python3", "scripts/build_site_data.py"], check=True)
    subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)
    print("Complete!")

if __name__ == "__main__":
    main()
