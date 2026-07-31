import csv
import json
import os
import re

DATA_CSV = "data.csv"
OUTPUT_DIR = "data"
STREETS_DIR = os.path.join(OUTPUT_DIR, "streets")

def clean_slug(text):
    if not text:
        return ""
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug or "unnamed"

def main():
    os.makedirs(STREETS_DIR, exist_ok=True)
    
    print(f"Reading {DATA_CSV}...")
    records_by_street = {}
    street_stats = {}
    dedup_search = {}

    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            st = row["street"].strip()
            if not st:
                continue

            slug = clean_slug(st)
            if slug not in records_by_street:
                records_by_street[slug] = []
                street_stats[slug] = {
                    "displayName": st,
                    "slug": slug,
                    "recordsCount": 0,
                    "years": set(),
                    "houses": set(),
                    "namedBuildings": set()
                }

            records_by_street[slug].append(row)
            
            stats = street_stats[slug]
            stats["recordsCount"] += 1
            if row.get("year"):
                stats["years"].add(row["year"])
            if row.get("house_number"):
                stats["houses"].add(row["house_number"])
            if row.get("building_name"):
                stats["namedBuildings"].add(row["building_name"])

            # Search Indexing (Deduplicated by name & street)
            surname = (row.get("surname") or "").strip()
            forename = (row.get("forename") or "").strip()
            trade = (row.get("trade") or "").strip()
            bldg = (row.get("building_name") or "").strip()
            h_num = (row.get("house_number") or "").strip()

            if surname or forename or trade or bldg:
                full_n = f"{forename} {surname}".strip() if forename else surname
                target_key = h_num or bldg or full_n

                # Group by (full_n, slug, target_key)
                search_key = (full_n.lower(), slug, target_key.lower())
                if search_key not in dedup_search:
                    dedup_search[search_key] = {
                        "n": full_n,
                        "s": st,
                        "g": slug,
                        "k": target_key,
                        "t": trade
                    }

    print(f"Writing per-street JSON files for {len(records_by_street)} streets into {STREETS_DIR}...")
    streets_summary = []

    for slug, records in records_by_street.items():
        stats = street_stats[slug]
        years_sorted = sorted(list(stats["years"]), key=lambda y: int(y) if y.isdigit() else 0)
        first_yr = int(years_sorted[0]) if years_sorted and years_sorted[0].isdigit() else 1876
        last_yr = int(years_sorted[-1]) if years_sorted and years_sorted[-1].isdigit() else 1950

        summary = {
            "displayName": stats["displayName"],
            "slug": slug,
            "recordsCount": stats["recordsCount"],
            "houseCount": len(stats["houses"]),
            "buildingCount": len(stats["namedBuildings"]),
            "earliestYear": first_yr,
            "latestYear": last_yr,
            "yearsSpan": f"{first_yr}–{last_yr}" if first_yr != last_yr else str(first_yr)
        }
        streets_summary.append(summary)

        # Save street-specific JSON
        street_file_path = os.path.join(STREETS_DIR, f"{slug}.json")
        with open(street_file_path, "w", encoding="utf-8") as sf:
            json.dump({
                "street": stats["displayName"],
                "slug": slug,
                "summary": summary,
                "records": records
            }, sf, indent=None, separators=(',', ':'))

    # Sort master streets index alphabetically
    streets_summary.sort(key=lambda s: s["displayName"].lower())

    master_file = os.path.join(OUTPUT_DIR, "streets.json")
    print(f"Saving master street list ({len(streets_summary)} streets) to {master_file}...")
    with open(master_file, "w", encoding="utf-8") as mf:
        json.dump(streets_summary, mf, indent=None, separators=(',', ':'))

    # Save compact global search index
    search_list = list(dedup_search.values())
    search_file = os.path.join(OUTPUT_DIR, "search_index.json")
    print(f"Saving compact global search index ({len(search_list)} entries) to {search_file}...")
    with open(search_file, "w", encoding="utf-8") as scf:
        json.dump(search_list, scf, indent=None, separators=(',', ':'))

    print("Site data build complete! Output saved in /data/.")

if __name__ == "__main__":
    main()
