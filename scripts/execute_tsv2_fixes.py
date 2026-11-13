import csv
import json
import os
import shutil

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_ROOT)

DATA_CSV = "data.csv"
BACKUP_CSV = "data.csv.bak_before_tsv2_fixes"
MASTER_FILE = "master_streets.json"
TSV_FILE = "/Users/robgale/.gemini/antigravity/brain/6f1cd8f4-71e4-497a-af55-adcc01760bb1/.user_uploaded/media_1793999559040_94ad6a84.tsv"

# 1. Safety Backup
if not os.path.exists(BACKUP_CSV):
    print(f"Creating safety backup: {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)
else:
    print(f"Backup {BACKUP_CSV} already exists.")

# 2. Define Renames and Removals
DELETE_STREETS = {
    "home of very inexpensive reliable furniture".lower()
}

EXACT_REMAP = {
    "brodawel gardens": "Brodawell Gardens",
    "brynderwyn road": "Brynderwen Road",
    "brynderyn road": "Brynderwen Road",
    "clevedon": "Clevedon Terrace",
    "clifford crescent": "Clyffard Crescent",
    "g. w. wharf road": "Wharf Road",
    "garte terrace": "Garth Terrace",
    "glos'ter street": "Gloucester Street",
    "hoobein road": "Holbein Road",
    "hopfield": "Hopefield",
    "jed street": "Jeddo Street",
    "jon street": "Jones Street",
    "kensington pl": "Kensington Place",
    "keyse's buidings": "Keyes's Buildings",
    "keyse's buildings": "Keyes's Buildings",
    "kingsmill ter": "Kingsmill Terrace",
    "macarthys court": "Macarthy's Court",
    "manchester st.-b": "Manchester Street",
    "mansell street": "Mansel Street",
    "mendalgief": "Mendalgief Road",
    "mendalgiel road": "Mendalgief Road",
    "mendalgier road": "Mendalgief Road",
    "mendalgiff road": "Mendalgief Road",
    "mendalglef road": "Mendalgief Road",
    "palmyra": "Palmyra Place",
    "phillips street": "Phillip Street",
    "roberts street": "Robert Street",
    "st. mary's street": "St. Mary Street",
    "summerhill av": "Summerhill Avenue",
    "victoria street": "Victoria Avenue",
    "walis street": "Wallis Street",
    "washhouse parade": "Watchhouse Parade",
    "water's lane": "Waters's Lane",
    "william street": "Williams Street",
    "woodland": "Woodland Road",
    "woodland park": "Woodland Park Road",
    "marrowbone lane": "Marshfield Street",
    "kin street": "King's Parade",
    "maple crescent": "Maple Avenue",
    "shaftsbury park": "Shaftesbury Park",
    "pillgwenlly post office t. & m.o., s.b., and a. and i. office": "Commercial Road"
}

# 3. Process data.csv
print("Processing data.csv...")
rows_kept = []
stats = {
    "deleted": 0,
    "remapped": 0,
    "special_bolt": 0,
    "special_holmes": 0,
    "special_ivor": 0
}

with open(DATA_CSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        st = (row.get("street") or "").strip()
        st_lower = st.lower()
        yr = (row.get("year") or "").strip()

        # Check deletion
        if st_lower in DELETE_STREETS:
            stats["deleted"] += 1
            continue

        # Check Bolt Road conditional split
        if st_lower == "bolt road":
            stats["special_bolt"] += 1
            if yr == "1892":
                row["street"] = "Bolton Road"
            elif yr == "1924":
                row["street"] = "Bolt Street"
            else:
                row["street"] = "Bolt Street"
            rows_kept.append(row)
            continue

        # Check Holmes view
        if st_lower == "holmes view":
            stats["special_holmes"] += 1
            row["street"] = "Crescent Road"
            if not row.get("building_name"):
                row["building_name"] = "Holmes View"
            rows_kept.append(row)
            continue

        # Check Ivor Place
        if st_lower == "ivor place":
            stats["special_ivor"] += 1
            row["street"] = "Victoria Avenue"
            if not row.get("building_name"):
                row["building_name"] = "Ivor Place"
            rows_kept.append(row)
            continue

        # Check exact remappings
        if st_lower in EXACT_REMAP:
            stats["remapped"] += 1
            row["street"] = EXACT_REMAP[st_lower]
            rows_kept.append(row)
            continue

        # Keep row unchanged
        rows_kept.append(row)

# Write back data.csv
with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows_kept)

print("data.csv update complete:")
print(f"  Rows deleted: {stats['deleted']}")
print(f"  Rows remapped: {stats['remapped']}")
print(f"  Bolt Road remapped: {stats['special_bolt']}")
print(f"  Holmes view remapped: {stats['special_holmes']}")
print(f"  Ivor Place remapped: {stats['special_ivor']}")
print(f"  Total remaining records: {len(rows_kept)}")

# 4. Update master_streets.json
if os.path.exists(MASTER_FILE):
    print("Updating master_streets.json...")
    with open(MASTER_FILE, "r", encoding="utf-8") as f:
        master_data = json.load(f)
    
    streets_dict = master_data.get("streets", {})

    # Read verified statuses and notes from TSV
    verified_from_tsv = {}
    with open(TSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            canon = r.get("Canonical Name", "").strip()
            status = r.get("Audit Status", "").strip()
            notes = r.get("Review Notes / Distinctions", "").strip()
            if status == "NAME_VERIFIED" or canon in ("Carlisle Road",):
                verified_from_tsv[canon.lower()] = {
                    "name": canon,
                    "notes": notes
                }

    # Mark verified in master_streets
    verified_count = 0
    for slug, s_data in streets_dict.items():
        s_name = s_data.get("canonical_name", "").strip().lower()
        if s_name in verified_from_tsv:
            v_info = verified_from_tsv[s_name]
            s_data["audit_status"] = "NAME_VERIFIED"
            if "audit" not in s_data:
                s_data["audit"] = {}
            s_data["audit"]["status"] = "NAME_VERIFIED"
            s_data["audit"]["verified_by"] = "Rob Gale"
            if v_info["notes"]:
                s_data["audit"]["notes"] = v_info["notes"]
                s_data["notes"] = v_info["notes"]
            verified_count += 1

    # Remove remapped streets if present as separate entries
    all_remapped_names = set(EXACT_REMAP.keys()) | {"bolt road", "holmes view", "ivor place", "home of very inexpensive reliable furniture"}
    removed_slugs = []
    for slug, s_data in list(streets_dict.items()):
        s_name = s_data.get("canonical_name", "").strip().lower()
        if s_name in all_remapped_names:
            del streets_dict[slug]
            removed_slugs.append(s_name)

    master_data["streets"] = streets_dict
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(master_data, f, indent=2, ensure_ascii=False)

    print(f"master_streets.json updated: {verified_count} marked NAME_VERIFIED, {len(removed_slugs)} defunct entries removed.")
