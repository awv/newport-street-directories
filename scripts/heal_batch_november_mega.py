import csv
import json
import os
import shutil

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_nov_mega"
MASTER_FILE = "master_streets.json"

if not os.path.exists(BACKUP_CSV):
    print(f"Creating backup {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)
else:
    print(f"Backup {BACKUP_CSV} already exists.")

# Read rows
rows = []
counts = {}

def track(name):
    counts[name] = counts.get(name, 0) + 1

with open(DATA_CSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for idx, r in enumerate(reader):
        st = r.get("street", "")
        yr = r.get("year", "")
        hn = r.get("house_number", "")
        bn = r.get("building_name", "")
        fn = r.get("forename", "")
        sn = r.get("surname", "")
        tr = r.get("trade", "")

        # 1. Dock Street-continued -> Dock Street
        if st == "Dock Street-continued":
            r["street"] = "Dock Street"
            track("Dock Street-continued -> Dock Street")

        # 2. Dud Street -> Dudley Street
        elif st == "Dud Street":
            r["street"] = "Dudley Street"
            track("Dud Street -> Dudley Street")

        # 3. Eaglescliffe -> Brynhyfryd Road
        elif st == "Eaglescliffe":
            r["street"] = "Brynhyfryd Road"
            track("Eaglescliffe -> Brynhyfryd Road")

        # 4. Elton Road -> Eton Road
        elif st == "Elton Road":
            r["street"] = "Eton Road"
            track("Elton Road -> Eton Road")

        # 5. Factory Cottages -> Queen's Hill
        elif st == "Factory Cottages":
            r["street"] = "Queen's Hill"
            if not bn:
                r["building_name"] = "Factory Cottages"
            track("Factory Cottages -> Queen's Hill")

        # 6. Fire Station Cottages -> Llanarth Street
        elif st == "Fire Station Cottages":
            r["street"] = "Llanarth Street"
            r["building_name"] = f"Fire Station Cottages {hn}".strip()
            track("Fire Station Cottages -> Llanarth Street")

        # 7. Glos'ter Street -> Gloster Street
        elif st == "Glos'ter Street":
            r["street"] = "Gloster Street"
            track("Glos'ter Street -> Gloster Street")

        # 8. Henry St. (Upper.) -> Henry Street
        elif st == "Henry St. (Upper.)":
            r["street"] = "Henry Street"
            track("Henry St. (Upper.) -> Henry Street")

        # 9. Henry Street (Herbert Street) -> Henry Street (with note)
        elif st == "Henry Street (Herbert Street)":
            r["street"] = "Henry Street"
            r["building_name"] = "Corner of Herbert Street"
            track("Henry Street (Herbert Street) -> Henry Street")

        # 10. Hereford Place (from Clarence place to Church road) -> Hereford Place
        elif st == "Hereford Place (from Clarence place to Church road)":
            r["street"] = "Hereford Place"
            track("Hereford Place (...) -> Hereford Place")

        # 11. Keen Street -> Keene Street
        elif st == "Keen Street":
            r["street"] = "Keene Street"
            track("Keen Street -> Keene Street")

        # 12. Higher Grade Schools -> Stow Hill
        elif st == "Higher Grade Schools":
            r["street"] = "Stow Hill"
            track("Higher Grade Schools -> Stow Hill")

        # 13. Lliswerry Board School -> Nash Road
        elif st == "Lliswerry Board School":
            r["street"] = "Nash Road"
            track("Lliswerry Board School -> Nash Road")

        # 14. Lloyds Bank Cham's -> Commercial Street
        elif st == "Lloyds Bank Cham's":
            r["street"] = "Commercial Street"
            r["building_name"] = "Lloyds Bank Chambers"
            track("Lloyds Bank Cham's -> Commercial Street")

        # 15. Llwern Street -> Llanwern Street
        elif st == "Llwern Street":
            r["street"] = "Llanwern Street"
            track("Llwern Street -> Llanwern Street")

        # 16. Llwyderi Road -> Lliswerry Road
        elif st == "Llwyderi Road":
            r["street"] = "Lliswerry Road"
            track("Llwyderi Road -> Lliswerry Road")

        # 17. Lock Street & Loch Street -> Locke Street
        elif st in ["Lock Street", "Loch Street"]:
            r["street"] = "Locke Street"
            track(f"{st} -> Locke Street")

        # 18. Ebe Street:
        # In 1913: doors 23 to 33 -> Ebenezer Terrace
        # In 1908: doors 30 to 33 + Ebenezer Chapel -> Ebenezer Terrace
        # In 1908: doors 5 to 60 (Emlyn works, Three Salmons, etc.) -> Emlyn Street
        elif st == "Ebe Street":
            if yr == "1913":
                r["street"] = "Ebenezer Terrace"
                track("Ebe Street (1913) -> Ebenezer Terrace")
            elif yr == "1908":
                # Check house number / landmark
                if hn in ["30", "31", "32", "33"] or "EBENEZER" in bn.upper() or "EBENEZER" in fn.upper() or "EBENEZER" in tr.upper() or fn in ["Greenslade George", "Anthony John"]:
                    r["street"] = "Ebenezer Terrace"
                    track("Ebe Street (1908 doors 30-33) -> Ebenezer Terrace")
                else:
                    r["street"] = "Emlyn Street"
                    track("Ebe Street (1908 doors 5-60) -> Emlyn Street")

        # 19. George's Buildings -> George Street (with building_name George's Buildings)
        elif st == "George's Buildings":
            r["street"] = "George Street"
            if not bn:
                r["building_name"] = "George's Buildings"
            track("George's Buildings -> George Street")

        # 20. Fulford's Cottages:
        # In 1890: Victoria Avenue (building_name Fulford's Cottages)
        # In 1899: Victoria Avenue (building_name Fulford's Cottages)
        # In 1915: doors 1-4 are Fulford's Cottages on Victoria Avenue; doors 23-49B are Victoria Avenue!
        # In 1920: doors 7-57 are George Street!
        elif st == "Fulford's Cottages":
            if yr in ["1890", "1899"]:
                r["street"] = "Victoria Avenue"
                r["building_name"] = "Fulford's Cottages"
                track(f"Fulford's Cottages ({yr}) -> Victoria Avenue")
            elif yr == "1915":
                r["street"] = "Victoria Avenue"
                if hn in ["1", "2", "3", "4"]:
                    r["building_name"] = "Fulford's Cottages"
                    track("Fulford's Cottages (1915 1-4) -> Victoria Avenue (Fulford's Cottages)")
                else:
                    track("Fulford's Cottages (1915 23-49) -> Victoria Avenue")
            elif yr == "1920":
                r["street"] = "George Street"
                track("Fulford's Cottages (1920) -> George Street")

        # 21. East Side wharves:
        # Unify East Side, East Side of River, East side of Usk from Bridge, Gridiron wharf -> East Usk Wharves
        elif st in ["East Side", "East Side of River", "East side of Usk from Bridge", "Gridiron wharf"]:
            r["street"] = "East Usk Wharves"
            track(f"{st} -> East Usk Wharves")

        rows.append(r)

print("\nReplacement counts:")
for k, v in sorted(counts.items()):
    print(f"  {k}: {v}")

with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("\ndata.csv written successfully.")

# 2. Update master_streets.json
with open(MASTER_FILE, "r", encoding="utf-8") as f:
    master_data = json.load(f)

streets_dict = master_data.get("streets", {})

# Add aliases to canonical entries
def add_alias(canonical_slug, alias):
    if canonical_slug in streets_dict:
        aliases = set(streets_dict[canonical_slug].get("aliases", []))
        aliases.add(alias)
        streets_dict[canonical_slug]["aliases"] = sorted(list(aliases))

add_alias("dock-street", "Dock Street-continued")
add_alias("dudley-street", "Dud Street")
add_alias("brynhyfryd-road", "Eaglescliffe")
add_alias("eton-road", "Elton Road")
add_alias("queen-s-hill", "Factory Cottages")
add_alias("llanarth-street", "Fire Station Cottages")
add_alias("gloster-street", "Glos'ter Street")
add_alias("henry-street", "Henry St. (Upper.)")
add_alias("henry-street", "Henry Street (Herbert Street)")
add_alias("hereford-place", "Hereford Place (from Clarence place to Church road)")
add_alias("keene-street", "Keen Street")
add_alias("stow-hill", "Higher Grade Schools")
add_alias("nash-road", "Lliswerry Board School")
add_alias("commercial-street", "Lloyds Bank Cham's")
add_alias("llanwern-street", "Llwern Street")
add_alias("lliswerry-road", "Llwyderi Road")
add_alias("locke-street", "Lock Street")
add_alias("locke-street", "Loch Street")
add_alias("ebenezer-terrace", "Ebe Street")
add_alias("george-street", "George's Buildings")
add_alias("victoria-avenue", "Fulford's Cottages")

# Create or update East Usk Wharves in master_streets
if "east-usk-wharves" not in streets_dict:
    streets_dict["east-usk-wharves"] = {
        "canonical_name": "East Usk Wharves",
        "slug": "east-usk-wharves",
        "district": "Corporation Road / River Usk East Bank",
        "parish": "",
        "former_names": ["East Side of River", "East side of Usk from Bridge", "Gridiron wharf", "East Side"],
        "sub_sections": ["London Wharf", "Rodney Wharf", "The Gridiron", "Clarence Wharf", "Great Western Wharf", "Orb Works"],
        "numbering_scheme": {"type": "UNNUMBERED"},
        "cross_streets": ["Corporation Road", "Wharf Road"],
        "aliases": ["East Side", "East Side of River", "East side of Usk from Bridge", "Gridiron wharf", "Gridiron Wharf"],
        "audit": {"status": "NAME_VERIFIED", "verified_by": "Rob Gale", "notes": "Unified East Side River Usk wharves."},
        "audit_status": "NAME_VERIFIED",
        "notes": "Historical industrial wharves, sawmills, ship repair gridiron, and works along the eastern bank of the River Usk.",
        "latitude": "51.5865",
        "longitude": "-2.9840"
    }
else:
    for a in ["East Side", "East Side of River", "East side of Usk from Bridge", "Gridiron wharf", "Gridiron Wharf"]:
        add_alias("east-usk-wharves", a)

# Clean up any leftover slugs
stale_slugs = [
    "dock-street-continued",
    "dud-street",
    "eaglescliffe",
    "elton-road",
    "factory-cottages",
    "fire-station-cottages",
    "glos-ter-street",
    "henry-st-upper",
    "henry-street-herbert-street",
    "hereford-place-from-clarence-place-to-church-road",
    "keen-street",
    "higher-grade-schools",
    "lliswerry-board-school",
    "lloyds-bank-cham-s",
    "llwern-street",
    "llwyderi-road",
    "lock-street",
    "loch-street",
    "ebe-street",
    "george-s-buildings",
    "fulford-s-cottages",
    "east-side",
    "east-side-of-river",
    "east-side-of-usk-from-bridge",
    "gridiron-wharf"
]

for s in stale_slugs:
    if s in streets_dict:
        del streets_dict[s]
        print(f"Deleted stale slug {s} from master_streets.json")

with open(MASTER_FILE, "w", encoding="utf-8") as f:
    json.dump(master_data, f, indent=2, ensure_ascii=False)

print("master_streets.json updated successfully.")
