import csv
import json
import os

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

print("Starting healing script for Batch 38...")

with open("data.csv", "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))
    fieldnames = reader[0].keys() if reader else []

# Step 1: Pre-calculate Newport Street Directory blocks and their preceding streets
# A block of 'Newport Street Directory' inherits the street of the immediate previous non-NSD row.
nsd_replacements = {}
last_valid_street = None
for i, r in enumerate(reader):
    st = r.get("street", "").strip()
    if st == "Newport Street Directory":
        if last_valid_street:
            nsd_replacements[i] = last_valid_street
    else:
        last_valid_street = st

print(f"Mapped {len(nsd_replacements)} 'Newport Street Directory' rows to their parent streets.")

# Step 2: Iterate and heal rows
healed_rows = []

for i, r in enumerate(reader):
    st = r.get("street", "").strip()
    yr = r.get("year", "").strip()
    hn = r.get("house_number", "").strip()
    bldg = r.get("building_name", "").strip()
    fn = r.get("forename", "").strip()
    sn = r.get("surname", "").strip()
    tr = r.get("trade", "").strip()

    # 1. Aberbeeg whf -> Aberbeeg Wharf
    if st == "Aberbeeg whf":
        r["street"] = "Aberbeeg Wharf"
        healed_rows.append(r)
        continue

    # 2. Cambrian whf -> Cambrian Wharf
    if st == "Cambrian whf":
        r["street"] = "Cambrian Wharf"
        healed_rows.append(r)
        continue

    # 3. Cattle Market
    if st == "Cattle Market":
        if yr == "1890":
            r["street"] = "Tredegar Street"
            r["building_name"] = "Cattle Market"
        elif yr == "1895":
            if hn in ["33", "34", "35", "36", "37", "38", "39"] and int(hn) <= 39 and fn in ["Fredk.", "Wm.", "C. R.", "Ed.", "F.", "Samuel", "Mrs Susan"]:
                r["street"] = "Ruperra Street"
            else:
                r["street"] = "St. Edward Street"
        healed_rows.append(r)
        continue

    # 4. Charwood Road -> Charnwood Road
    if st == "Charwood Road":
        r["street"] = "Charnwood Road"
        healed_rows.append(r)
        continue

    # 5. Christchurch Cemetery -> Chepstow Road
    if st == "Christchurch Cemetery":
        r["street"] = "Chepstow Road"
        if not bldg:
            r["building_name"] = "Christchurch Cemetery"
        else:
            r["building_name"] = f"Christchurch Cemetery, {bldg}"
        healed_rows.append(r)
        continue

    # 6. Clarance Place -> Clarence Place
    if st == "Clarance Place":
        r["street"] = "Clarence Place"
        healed_rows.append(r)
        continue

    # 7. Commercial Buildings -> Commercial Street
    if st == "Commercial Buildings":
        r["street"] = "Commercial Street"
        if not bldg:
            r["building_name"] = "Commercial Buildings"
        else:
            r["building_name"] = f"Commercial Buildings, {bldg}"
        healed_rows.append(r)
        continue

    # 8. Corpus Christi Street -> Corporation Road
    if st == "Corpus Christi Street":
        r["street"] = "Corporation Road"
        healed_rows.append(r)
        continue

    # 9. Cross Hands Cottages -> Chepstow Road
    if st == "Cross Hands Cottages":
        r["street"] = "Chepstow Road"
        if not bldg:
            r["building_name"] = "Cross Hands Cottages"
        else:
            r["building_name"] = f"Cross Hands Cottages, {bldg}"
        healed_rows.append(r)
        continue

    # 10. Dock Street Chambers -> Dock Street
    if st == "Dock Street Chambers":
        r["street"] = "Dock Street"
        if not bldg:
            r["building_name"] = "Dock Street Chambers"
        else:
            r["building_name"] = f"Dock Street Chambers, {bldg}"
        healed_rows.append(r)
        continue

    # 11. Dock Street continued -> Dock Street
    if st.lower() in ["dock street continued", "dock street-continued"]:
        r["street"] = "Dock Street"
        healed_rows.append(r)
        continue

    # 12. Ebenezer Terrace (Chapel) -> Ebenezer Terrace
    if st == "Ebenezer Terrace (Chapel)":
        r["street"] = "Ebenezer Terrace"
        if not bldg:
            r["building_name"] = "Ebenezer Chapel"
        healed_rows.append(r)
        continue

    # 13. Farmwood Cottages -> Farm Cottages
    if st == "Farmwood Cottages":
        r["street"] = "Farm Cottages"
        healed_rows.append(r)
        continue

    # 14. Fulford'S Cottages -> Victoria Avenue
    if st == "Fulford'S Cottages":
        r["street"] = "Victoria Avenue"
        if hn in ["1", "2", "3", "4", "5"]:
            r["building_name"] = "Fulford's Cottages"
        healed_rows.append(r)
        continue

    # 15. Gasens Street -> Gaskell Street
    if st == "Gasens Street":
        r["street"] = "Gaskell Street"
        healed_rows.append(r)
        continue

    # 16. Geo Street -> George Street
    if st == "Geo Street":
        r["street"] = "George Street"
        healed_rows.append(r)
        continue

    # 17. Highbury Chambers -> Skinner Street
    if st == "Highbury Chambers":
        r["street"] = "Skinner Street"
        r["building_name"] = "Highbury Chambers"
        healed_rows.append(r)
        continue

    # 18. Lansdowne Cottages -> Stow Hill
    if st == "Lansdowne Cottages":
        r["street"] = "Stow Hill"
        r["building_name"] = "Lansdowne Cottages"
        healed_rows.append(r)
        continue

    # 19. Jayne's Buildings -> Union Lane
    if st == "Jayne's Buildings":
        r["street"] = "Union Lane"
        r["building_name"] = "Jayne's Buildings"
        healed_rows.append(r)
        continue

    # 20. Llwnyderi Road -> Llwynderi Road
    if st == "Llwnyderi Road":
        r["street"] = "Llwynderi Road"
        healed_rows.append(r)
        continue

    # 21. Lyn Street -> Lyne Road
    if st == "Lyn Street":
        r["street"] = "Lyne Road"
        healed_rows.append(r)
        continue

    # 22. Maindee Board Schools -> Chepstow Road
    if st == "Maindee Board Schools":
        r["street"] = "Chepstow Road"
        healed_rows.append(r)
        continue

    # 23. Maindee Municipal Bldgs / MAINDEE MUNICIPAL BLDGS -> Chepstow Road
    if st.lower() == "maindee municipal bldgs":
        r["street"] = "Chepstow Road"
        if not bldg:
            r["building_name"] = "Maindee Municipal Buildings"
        else:
            r["building_name"] = f"Maindee Municipal Buildings, {bldg}"
        healed_rows.append(r)
        continue

    # 24. Maindee Street List -> London Street
    if st == "Maindee Street List":
        r["street"] = "London Street"
        healed_rows.append(r)
        continue

    # 25. Merriot's Place -> Merriott's Place
    if st == "Merriot's Place":
        r["street"] = "Merriott's Place"
        healed_rows.append(r)
        continue

    # 26. Metropolitan Bank Chambers -> Commercial Street
    if st == "Metropolitan Bank Chambers":
        r["street"] = "Commercial Street"
        r["building_name"] = "Metropolitan Bank Chambers"
        healed_rows.append(r)
        continue

    # 27. Midland Bank Chambers -> Bridge Street
    if st == "Midland Bank Chambers":
        r["street"] = "Bridge Street"
        r["building_name"] = "Midland Bank Chambers"
        healed_rows.append(r)
        continue

    # 28. Mill Parade continued -> Mill Parade
    if st.lower() in ["mill parade continued", "mill parade-continued"]:
        r["street"] = "Mill Parade"
        healed_rows.append(r)
        continue

    # 29. Monmouth Chambers -> Commercial Street
    if st == "Monmouth Chambers":
        r["street"] = "Commercial Street"
        if not hn:
            r["house_number"] = "139"
        r["building_name"] = "Monmouth Chambers"
        healed_rows.append(r)
        continue

    # 30. Mount Pleasant Cottages -> Stow Hill
    if st in ["Mount Pleasant Cottages", "Mt. Pleasant Cottages"]:
        r["street"] = "Stow Hill"
        r["building_name"] = "Mount Pleasant Cottages"
        healed_rows.append(r)
        continue

    # 31. Nelson St. (Upper) -> Upper Nelson Street
    if st == "Nelson St. (Upper)":
        r["street"] = "Upper Nelson Street"
        healed_rows.append(r)
        continue

    # 32. New Buildings -> Christchurch Road
    if st == "New Buildings":
        r["street"] = "Christchurch Road"
        r["building_name"] = "New Buildings"
        healed_rows.append(r)
        continue

    # 33. Newport Street Directory -> inherit preceding street
    if st == "Newport Street Directory":
        parent = nsd_replacements.get(i, "Newport")
        r["street"] = parent
        healed_rows.append(r)
        continue

    # 34. Orchard Buildings -> Orchard Terrace
    if st == "Orchard Buildings":
        r["street"] = "Orchard Terrace"
        r["building_name"] = "Orchard Buildings"
        healed_rows.append(r)
        continue

    # 35. Pembroke Chambers -> High Street
    if st == "Pembroke Chambers":
        r["street"] = "High Street"
        r["house_number"] = "30"
        r["building_name"] = "Pembroke Chambers"
        healed_rows.append(r)
        continue

    # 36. Presbyterian Church -> Chepstow Road
    if st == "Presbyterian Church":
        r["street"] = "Chepstow Road"
        healed_rows.append(r)
        continue

    # 37. Primrose Cottages -> Fair Oak Terrace
    if st == "Primrose Cottages":
        r["street"] = "Fair Oak Terrace"
        r["building_name"] = "Primrose Cottages"
        healed_rows.append(r)
        continue

    # 38. Pyne's Cottages -> Potter Street
    if st == "Pyne's Cottages":
        r["street"] = "Potter Street"
        if fn == "HOLY TRINITY CHURCH":
            r["building_name"] = "Holy Trinity Church"
            r["forename"] = ""
            r["surname"] = ""
        elif "Excelsior" in fn or "Plummer" in fn:
            r["forename"] = "T."
            r["surname"] = "Plummer"
            r["trade"] = "Excelsior Wagon & Carriage Works"
        elif "re-building" in fn or "re-building" in sn:
            r["forename"] = ""
            r["surname"] = ""
            r["trade"] = "Re-building"
        else:
            if not bldg:
                r["building_name"] = "Pyne's Cottages"
        healed_rows.append(r)
        continue

    healed_rows.append(r)

print(f"Total rows processed: {len(healed_rows)}")

# Write data.csv
with open("data.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(healed_rows)
print("Updated data.csv successfully.")

# Update master_streets.json
with open("master_streets.json", "r", encoding="utf-8") as f:
    ms = json.load(f)

streets = ms.get("streets", {})

# Add/ensure canonical entries
def add_alias(canonical_slug, alias):
    if canonical_slug in streets:
        aliases = streets[canonical_slug].setdefault("aliases", [])
        if alias not in aliases:
            aliases.append(alias)

def add_subsection(canonical_slug, subsection):
    if canonical_slug in streets:
        sub_sections = streets[canonical_slug].setdefault("sub_sections", [])
        if subsection not in sub_sections:
            sub_sections.append(subsection)

# 1. Aberbeeg Wharf
if "aberbeeg-wharf" not in streets:
    streets["aberbeeg-wharf"] = {
        "canonical_name": "Aberbeeg Wharf",
        "slug": "aberbeeg-wharf",
        "district": "River Bank",
        "parish": "",
        "former_names": [],
        "sub_sections": [],
        "numbering_scheme": {"type": "UNNUMBERED"},
        "cross_streets": [],
        "aliases": ["Aberbeeg whf"],
        "audit": {"status": "NAME_VERIFIED", "verified_by": "Rob Gale", "notes": ""},
        "coordinates": {"lat": None, "lng": None},
        "audit_status": "NAME_VERIFIED",
        "notes": "",
        "latitude": "",
        "longitude": ""
    }
else:
    add_alias("aberbeeg-wharf", "Aberbeeg whf")

# 2. Cambrian Wharf
if "cambrian-wharf" not in streets:
    streets["cambrian-wharf"] = {
        "canonical_name": "Cambrian Wharf",
        "slug": "cambrian-wharf",
        "district": "River Bank",
        "parish": "",
        "former_names": [],
        "sub_sections": [],
        "numbering_scheme": {"type": "UNNUMBERED"},
        "cross_streets": [],
        "aliases": ["Cambrian whf"],
        "audit": {"status": "NAME_VERIFIED", "verified_by": "Rob Gale", "notes": ""},
        "coordinates": {"lat": None, "lng": None},
        "audit_status": "NAME_VERIFIED",
        "notes": "",
        "latitude": "",
        "longitude": ""
    }
else:
    add_alias("cambrian-wharf", "Cambrian whf")

# 4. Charnwood Road
add_alias("charnwood-road", "Charwood Road")

# 5, 9, 22, 23, 36. Chepstow Road
for a in ["Christchurch Cemetery", "Cross Hands Cottages", "Maindee Board Schools", "Maindee Municipal Buildings", "Maindee Municipal Bldgs", "Presbyterian Church"]:
    add_alias("chepstow-road", a)
    add_subsection("chepstow-road", a)

# 6. Clarence Place
add_alias("clarence-place", "Clarance Place")

# 7, 26, 29. Commercial Street
for a in ["Commercial Buildings", "Metropolitan Bank Chambers", "Monmouth Chambers"]:
    add_alias("commercial-street", a)
    add_subsection("commercial-street", a)

# 8. Corporation Road
add_alias("corporation-road", "Corpus Christi Street")

# 10, 11. Dock Street
add_alias("dock-street", "Dock Street Chambers")
add_alias("dock-street", "Dock Street continued")
add_subsection("dock-street", "Dock Street Chambers")

# 12. Ebenezer Terrace
add_alias("ebenezer-terrace", "Ebenezer Terrace (Chapel)")

# 13. Farm Cottages
if "farm-cottages" not in streets:
    streets["farm-cottages"] = {
        "canonical_name": "Farm Cottages",
        "slug": "farm-cottages",
        "district": "Somerton",
        "parish": "",
        "former_names": ["Farmwood Cottages"],
        "sub_sections": [],
        "numbering_scheme": {"type": "CONSECUTIVE"},
        "cross_streets": ["Somerton Place"],
        "aliases": ["Farmwood Cottages"],
        "audit": {"status": "NAME_VERIFIED", "verified_by": "Rob Gale", "notes": "Unified Farmwood Cottages & Farm Cottages"},
        "coordinates": {"lat": None, "lng": None},
        "audit_status": "NAME_VERIFIED",
        "notes": "",
        "latitude": "",
        "longitude": ""
    }
else:
    add_alias("farm-cottages", "Farmwood Cottages")

# 14. Victoria Avenue
add_alias("victoria-avenue", "Fulford's Cottages")
add_alias("victoria-avenue", "Fulford'S Cottages")
add_subsection("victoria-avenue", "Fulford's Cottages")

# 15. Gaskell Street
add_alias("gaskell-street", "Gasens Street")

# 16. George Street
add_alias("george-street", "Geo Street")

# 17. Skinner Street
add_alias("skinner-street", "Highbury Chambers")
add_subsection("skinner-street", "Highbury Chambers")

# 18, 30. Stow Hill
for a in ["Lansdowne Cottages", "Mount Pleasant Cottages", "Mt. Pleasant Cottages"]:
    add_alias("stow-hill", a)
    add_subsection("stow-hill", a)

# 19. Union Lane
add_alias("union-lane", "Jayne's Buildings")
add_subsection("union-lane", "Jayne's Buildings")

# 20. Llwynderi Road
add_alias("llwynderi-road", "Llwnyderi Road")

# 21. Lyne Road
add_alias("lyne-road", "Lyn Street")

# 25. Merriott's Place
add_alias("merriott-s-place", "Merriot's Place")

# 27. Bridge Street
add_alias("bridge-street", "Midland Bank Chambers")
add_subsection("bridge-street", "Midland Bank Chambers")

# 28. Mill Parade
add_alias("mill-parade", "Mill Parade continued")

# 31. Upper Nelson Street
if "upper-nelson-street" not in streets:
    streets["upper-nelson-street"] = {
        "canonical_name": "Upper Nelson Street",
        "slug": "upper-nelson-street",
        "district": "",
        "parish": "",
        "former_names": ["Nelson St. (Upper)"],
        "sub_sections": [],
        "numbering_scheme": {"type": "CONSECUTIVE"},
        "cross_streets": [],
        "aliases": ["Nelson St. (Upper)", "Nelson Street (Upper)"],
        "audit": {"status": "NAME_VERIFIED", "verified_by": "Rob Gale", "notes": ""},
        "coordinates": {"lat": None, "lng": None},
        "audit_status": "NAME_VERIFIED",
        "notes": "",
        "latitude": "",
        "longitude": ""
    }
else:
    add_alias("upper-nelson-street", "Nelson St. (Upper)")

# 32. Christchurch Road
add_alias("christchurch-road", "New Buildings")
add_subsection("christchurch-road", "New Buildings")

# 34. Orchard Terrace
add_alias("orchard-terrace", "Orchard Buildings")
add_subsection("orchard-terrace", "Orchard Buildings")

# 35. High Street
add_alias("high-street", "Pembroke Chambers")
add_subsection("high-street", "Pembroke Chambers")

# 37. Fair Oak Terrace
add_alias("fair-oak-terrace", "Primrose Cottages")
add_subsection("fair-oak-terrace", "Primrose Cottages")

# 38. Potter Street
add_alias("potter-street", "Pyne's Cottages")
add_subsection("potter-street", "Pyne's Cottages")

# Remove stale slugs from master_streets
stale_slugs = [
    "aberbeeg-whf", "cambrian-whf", "cattle-market", "charwood-road",
    "christchurch-cemetery", "clarance-place", "commercial-buildings",
    "corpus-christi-street", "cross-hands-cottages", "dock-street-chambers",
    "dock-street-continued", "ebenezer-terrace-chapel", "farmwood-cottages",
    "fulford-s-cottages", "gasens-street", "geo-street", "highbury-chambers",
    "lansdowne-cottages", "jayne-s-buildings", "llwnyderi-road", "lyn-street",
    "maindee-board-schools", "maindee-municipal-bldgs", "maindee-street-list",
    "merriot-s-place", "metropolitan-bank-chambers", "midland-bank-chambers",
    "mill-parade-continued", "monmouth-chambers", "mount-pleasant-cottages",
    "nelson-st-upper", "new-buildings", "newport-street-directory",
    "orchard-buildings", "pembroke-chambers", "presbyterian-church",
    "primrose-cottages", "pyne-s-cottages"
]

removed_count = 0
for s in stale_slugs:
    if s in streets:
        del streets[s]
        removed_count += 1
        # Also check and remove data/streets/{s}.json
        p = os.path.join("data", "streets", f"{s}.json")
        if os.path.exists(p):
            os.remove(p)

print(f"Removed {removed_count} stale street slugs from master_streets.json.")

with open("master_streets.json", "w", encoding="utf-8") as f:
    json.dump(ms, f, indent=2, ensure_ascii=False)
print("Updated master_streets.json successfully.")
