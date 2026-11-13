#!/usr/bin/env python3
import csv
from collections import defaultdict, Counter

def load_data():
    with open('data.csv', 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def main():
    rows = load_data()
    print(f"Loaded {len(rows):,} total records.")

    # Index residents by surname and forename across years for clean streets
    clean_resident_index = defaultdict(list)
    for r in rows:
        st = r.get('street', '').strip()
        if len(st) > 4 and st.lower() not in ['dock', 'stow']:
            sname = r.get('surname', '').strip().lower()
            fname = r.get('forename', '').strip().lower()
            bname = r.get('building_name', '').strip().lower()
            if sname and len(sname) > 2:
                clean_resident_index[sname].append(r)

    # Group records with short street names
    short_slugs = defaultdict(lambda: defaultdict(list))
    for idx, r in enumerate(rows):
        st = r.get('street', '').strip()
        if len(st) <= 3 and not st.isdigit() and st.lower() not in ['oak', 'usk']:
            yr = r.get('year', '')
            short_slugs[st][yr].append((idx, r))

    print(f"Found {len(short_slugs)} short street slugs to investigate.\n")

    resolution_plan = {} # (slug, yr) -> best_street

    for slug, yr_dict in sorted(short_slugs.items(), key=lambda x: sum(len(v) for v in x[1].values()), reverse=True):
        print(f"=== Slug: \"{slug}\" ({sum(len(v) for v in yr_dict.values())} records) ===")
        for yr, indexed_rows in sorted(yr_dict.items()):
            street_votes = Counter()
            matched_residents = 0
            
            for idx, r in indexed_rows:
                sname = r.get('surname', '').strip().lower()
                hnum = r.get('house_number', '').strip()
                bname = r.get('building_name', '').strip().lower()
                
                if sname in clean_resident_index:
                    for cand in clean_resident_index[sname]:
                        cand_yr = int(cand['year'])
                        diff = abs(int(yr) - cand_yr)
                        if diff <= 5: # Within 5 years
                            weight = 5 - diff
                            cand_st = cand['street']
                            # Bonus if house number matches
                            if hnum and cand.get('house_number') == hnum:
                                weight *= 3
                            # Bonus if building name matches
                            if bname and cand.get('building_name', '').lower() == bname:
                                weight *= 5
                            # Bonus if trade matches
                            if r.get('trade') and cand.get('trade', '').lower() == r.get('trade', '').lower():
                                weight *= 2
                                
                            street_votes[cand_st] += weight
                    matched_residents += 1
            
            top_streets = street_votes.most_common(3)
            best_st = top_streets[0][0] if top_streets else "UNKNOWN"
            best_score = top_streets[0][1] if top_streets else 0
            
            print(f"  [{yr}] ({len(indexed_rows)} rows, {matched_residents} matched): Best -> \"{best_st}\" (Score: {best_score})")
            if len(top_streets) > 1:
                print(f"       Alternatives: {top_streets[1:]}")
            resolution_plan[(slug, yr)] = best_st

if __name__ == '__main__':
    main()
