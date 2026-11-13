import csv
from collections import defaultdict

def main():
    with open('data.csv') as f:
        rows = list(csv.DictReader(f))

    short_streets = defaultdict(lambda: defaultdict(list))
    for r in rows:
        st = r.get('street', '').strip()
        # Look for 3-letter strings (or 2-letter uppercase codes), excluding legitimate words like 'Oak', 'Usk'
        if len(st) <= 3 and not st.isdigit() and st.lower() not in ['oak', 'usk']:
            yr = r.get('year', '')
            short_streets[st][yr].append(r)

    print(f"Found {len(short_streets)} unique short street names.")
    for st, yr_dict in sorted(short_streets.items(), key=lambda x: sum(len(v) for v in x[1].values()), reverse=True):
        total_recs = sum(len(v) for v in yr_dict.values())
        years_list = sorted(yr_dict.keys())
        print(f"\n==========================================")
        print(f"SLUG: \"{st}\" | Total records: {total_recs} | Years: {years_list}")
        for yr in years_list:
            sample = yr_dict[yr][:4]
            sample_str = "; ".join(f"#{r['house_number']} {r['forename']} {r['surname']} ({r['building_name']}) - {r['trade']}" for r in sample)
            print(f"  [{yr}] ({len(yr_dict[yr])} rows): {sample_str[:160]}")

if __name__ == '__main__':
    main()
