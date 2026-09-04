import csv
import json
import os
import re

DATA_CSV = "data.csv"
OUTPUT_DIR = "data"
STREETS_DIR = os.path.join(OUTPUT_DIR, "streets")

# Maximum year permitted for public distribution (100-year rolling rule requested by Newport Library).
# Set to None to include all historical years.
MAX_PUBLIC_YEAR = 1925

# Load Master Streets Registry
MASTER_STREETS_FILE = "master_streets.json"
MASTER_STREETS = {}
if os.path.exists(MASTER_STREETS_FILE):
    with open(MASTER_STREETS_FILE, "r", encoding="utf-8") as mf:
        try:
            MASTER_STREETS = json.load(mf).get("streets", {})
        except Exception as e:
            print(f"Warning: Could not load {MASTER_STREETS_FILE}: {e}")

def clean_slug(text):
    if not text:
        return ""
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug or "unnamed"

def parse_street_content(slug):
    content_path = os.path.join("street_content", slug)
    md_file = os.path.join(content_path, "index.md")
    
    data = {
        "description": "",
        "latitude": "",
        "longitude": "",
        "map_query": "",
        "images": []
    }
    
    if not os.path.isdir(content_path):
        return data
        
    # List images
    valid_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    try:
        for f in os.listdir(content_path):
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                data["images"].append(f"street_content/{slug}/{f}")
    except Exception as e:
        print(f"Warning: Could not list files in {content_path}: {e}")
            
    if os.path.exists(md_file):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            frontmatter = {}
            body = []
            in_fm = False
            fm_count = 0
            
            for line in lines:
                stripped = line.strip()
                if stripped == "---":
                    in_fm = not in_fm
                    fm_count += 1
                    continue
                    
                if in_fm and fm_count == 1:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        frontmatter[k.strip().lower()] = v.strip().strip('"\'')
                else:
                    body.append(line)
                    
            data["description"] = "".join(body).strip()
            data["latitude"] = frontmatter.get("latitude", "")
            data["longitude"] = frontmatter.get("longitude", "")
            data["map_query"] = frontmatter.get("map_query", "")
        except Exception as e:
            print(f"Warning: Could not parse {md_file}: {e}")
        
    return data

def main():
    os.makedirs(STREETS_DIR, exist_ok=True)
    
    if MAX_PUBLIC_YEAR:
        print(f"Reading {DATA_CSV} (Restricting build to years <= {MAX_PUBLIC_YEAR} per 100-year policy)...")
    else:
        print(f"Reading {DATA_CSV} (Including all historical years)...")

    records_by_street = {}
    street_stats = {}
    dedup_search = {}

    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            st = row["street"].strip()
            if not st:
                continue

            yr_str = (row.get("year") or "").strip()
            if MAX_PUBLIC_YEAR and yr_str.isdigit() and int(yr_str) > MAX_PUBLIC_YEAR:
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

        # Load custom street content (description, images, coordinates override)
        content = parse_street_content(slug)

        # Attach master_streets.json metadata (former names, sub-sections, verification lock)
        m_info = MASTER_STREETS.get(slug, {})
        former_names = [f.get("name") for f in m_info.get("former_names", []) if f.get("name")]
        sub_sections = m_info.get("sub_sections", [])
        is_verified = m_info.get("audit", {}).get("status") == "VERIFIED"

        summary = {
            "displayName": stats["displayName"],
            "slug": slug,
            "recordsCount": stats["recordsCount"],
            "houseCount": len(stats["houses"]),
            "buildingCount": len(stats["namedBuildings"]),
            "earliestYear": first_yr,
            "latestYear": last_yr,
            "yearsSpan": f"{first_yr}–{last_yr}" if first_yr != last_yr else str(first_yr),
            "latitude": content["latitude"],
            "longitude": content["longitude"],
            "hasContent": bool(content["description"] or content["images"]),
            "formerNames": former_names,
            "subSections": sub_sections,
            "isVerified": is_verified
        }
        streets_summary.append(summary)

        # Save street-specific JSON
        street_file_path = os.path.join(STREETS_DIR, f"{slug}.json")
        with open(street_file_path, "w", encoding="utf-8") as sf:
            json.dump({
                "street": stats["displayName"],
                "slug": slug,
                "summary": summary,
                "records": records,
                "description": content["description"],
                "images": content["images"],
                "mapQuery": content["map_query"]
            }, sf, indent=None, separators=(',', ':'))

    # Clean up stale per-street JSON files
    for existing_file in os.listdir(STREETS_DIR):
        if existing_file.endswith(".json"):
            file_slug = existing_file[:-5]
            if file_slug not in records_by_street:
                os.remove(os.path.join(STREETS_DIR, existing_file))

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
