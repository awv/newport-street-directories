#!/usr/bin/env python3
import csv
import shutil
from collections import defaultdict, Counter
from pathlib import Path

DATA_CSV = Path("/Users/robgale/Documents/Newport Street Directory Project/data.csv")
BACKUP_CSV = Path("/Users/robgale/Documents/Newport Street Directory Project/data.csv.bak_before_all_short_fixes")

PREFIX_MAP = {
    'wha': ['Wharves'],
    'dos': ['Dos Road'],
    'rai': ['Railway Street'],
    'exe': ['Exeter Road'],
    'ski': ['Skinner Street'],
    'rup': ['Ruperra Street'],
    'ron': ['Ronald Road'],
    'sut': ['Sutton Road'],
    'dea': ['Dean Street'],
    'dol': ['Dolphin Street'],
    'duc': ['Duckpool Road'],
    'fie': ['Fields Road'],
    'pre': ['Preston Avenue'],
    'rob': ['Robert Street'],
    'cov': ['Coventry Road'],
    'hew': ['Hewertson Street'],
    'gor': ['Gordon Street'],
    'dan': ['Daniel Street'],
    'pow': ['Powell\'s Place'],
    'jon': ['Jones Street'],
    'wil': ['Williams Street'],
    'cha': ['Charles Street'],
    'eas': ['East Street'],
    'lam': ['Lambert Street'],
    'rud': ['Rudry Street'],
    'god': ['Godfrey Road'],
    'uni': ['Union Street'],
    'lyn': ['Lyne Road'],
    'whi': ['Whitehead Street'],
    'joh': ['John Street'],
    'cap': ['Capel Street'],
    'her': ['Herbert Street'],
    'tun': ['Tunnel Terrace'],
    'eto': ['Eton Road'],
    'ebe': ['Ebenezer Terrace'],
    'omb': ['Ombersley Road'],
    'fre': ['Frederick Street'],
    'ris': ['Risca Road'],
    'qui': ['Quintila Street'],
    'cre': ['Crescent Road'],
    'wat': ['Waterloo Road'],
    'woo': ['Woodland Road'],
    'sta': ['Station Street'],
    'som': ['Somerton Road'],
    'gol': ['Gold Tops'],
    'con': ['Constance Street'],
    'sha': ['Shaftesbury Street'],
    'pri': ['Price Street'],
    'tre': ['Tredegar Street'],
    'tho': ['Thomas Street'],
    'hub': ['Hubert Road'],
    'tro': ['Troddan Street'],
    'geo': ['George Street'],
    'mel': ['Melrose Way'],
    'win': ['Winmill Street'],
    'scr': ['Scranton Road'],
    'mac': ['Machen Street'],
    'dav': ['Davies Street'],
    'lie': ['Lilleshall Street'],
    'hal': ['Halstead Street'],
    'jun': ['Junction Road'],
    'loc': ['Locke Street'],
    'ber': ['Beresford Road'],
    'gre': ['Green Street'],
    'bel': ['Bellevue Street'],
    'spr': ['Spring Gardens'],
    'fra': ['Francis Street'],
    'coo': ['Coomassie Street'],
    'rod': ['Rodney Parade'],
    'bro': ['Broadway'],
    'bas': ['Bassaleg Road'],
    'alb': ['Albion Street'],
    'nel': ['Nelson Street'],
    'spe': ['Spencer Road'],
    'goo': ['Goodrich Crescent'],
    'sai': ['St. Woolos Road'],
    'mou': ['Mountjoy Road'],
    'cri': ['Courtybella Terrace'],
    'edw': ['Edward Street']
}

# Manual overrides for specific (slug, year) edge cases verified
SPECIAL_OVERRIDES = {
    ('ST', '1925'): 'St. Mary Street',
    ('Cae', '1887'): 'Caerau Road',
    ('Bar', '1895'): 'Barrack Hill',
    ('SAI', '1878'): 'St. Woolos Road',
    ('Sai', '1882'): 'St. Woolos Road',
    ('Mou', '1895'): 'Mountjoy Road',
    ('Cri', '1893'): 'Courtybella Terrace',
    ('Edw', '1910'): 'Edward Street',
    ('GOO', '1913'): 'Goodrich Crescent',
    ('GOO', '1915'): 'Goodrich Crescent',
}

def main():
    print(f"Backing up {DATA_CSV} -> {BACKUP_CSV}...")
    shutil.copy2(DATA_CSV, BACKUP_CSV)

    with open(DATA_CSV, 'r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

    # Index clean residents
    clean_resident_index = defaultdict(list)
    all_clean_streets = set()
    for r in reader:
        st = r.get('street', '').strip()
        if len(st) > 4:
            all_clean_streets.add(st)
            sname = r.get('surname', '').strip().lower()
            if sname and len(sname) > 2:
                clean_resident_index[sname].append(r)

    # Group records by (slug, yr)
    slug_groups = defaultdict(list)
    for idx, r in enumerate(reader):
        st = r.get('street', '').strip()
        if len(st) <= 3 and not st.isdigit() and st.lower() not in ['oak', 'usk']:
            yr = r.get('year', '')
            slug_groups[(st, yr)].append((idx, r))

    print(f"Resolving {len(slug_groups)} (slug, year) groups across {sum(len(v) for v in slug_groups.values()):,} records...")

    reassigned_count = 0
    resolved_summary = Counter()

    for (slug, yr), indexed_rows in slug_groups.items():
        if (slug, yr) in SPECIAL_OVERRIDES:
            target_st = SPECIAL_OVERRIDES[(slug, yr)]
        else:
            prefix = slug.lower()
            if prefix in PREFIX_MAP:
                candidates = PREFIX_MAP[prefix]
            else:
                candidates = [cs for cs in all_clean_streets if cs.lower().startswith(prefix)]
            
            votes = Counter()
            for idx, r in indexed_rows:
                sname = r.get('surname', '').strip().lower()
                hnum = r.get('house_number', '').strip()
                if sname in clean_resident_index:
                    for cand in clean_resident_index[sname]:
                        if cand['street'] in candidates:
                            diff = abs(int(yr) - int(cand['year']))
                            w = max(1, 6 - diff)
                            if hnum and cand.get('house_number') == hnum: w *= 5
                            votes[cand['street']] += w

            if votes:
                target_st = votes.most_common(1)[0][0]
            elif candidates:
                target_st = candidates[0]
            else:
                print(f"Warning: could not resolve ({slug}, {yr}), skipping.")
                continue

        # Canonicalize target street casing if in ALL CAPS
        if target_st.isupper() and len(target_st) > 3:
            target_st = target_st.title()

        for idx, r in indexed_rows:
            reader[idx]['street'] = target_st
            reassigned_count += 1
        resolved_summary[target_st] += len(indexed_rows)

    with open(DATA_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)

    print(f"\nExecution Complete! Reassigned {reassigned_count:,} records.")
    print("Top reassigned streets:")
    for st, count in resolved_summary.most_common(20):
        print(f"  - {st}: {count:,} records")

if __name__ == '__main__':
    main()
