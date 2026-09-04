#!/usr/bin/env python3
"""
merge_overrides.py

Utility script to merge user-exported JSON override files (e.g. user_overrides.json)
into the master edge_cases.json configuration file.

Usage:
    python3 merge_overrides.py [path_to_overrides.json]

If no argument is given, it looks for user_overrides.json in the current working directory,
or automatically checks ~/Downloads/user_overrides.json.
"""

import json
import os
import sys

# Root project directory is parent of scripts directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
EDGE_CASES_FILE = os.path.join(PROJECT_DIR, "edge_cases.json")
MASTER_STREETS_FILE = os.path.join(PROJECT_DIR, "master_streets.json")
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")

INBOX_DIR = os.path.join(PROJECT_DIR, "overrides_inbox")

def find_user_overrides_file(arg_path=None):
    if arg_path and os.path.exists(arg_path):
        return [arg_path]

    found = []
    # Check overrides_inbox directory first
    if os.path.exists(INBOX_DIR):
        for fname in os.listdir(INBOX_DIR):
            if fname.endswith(".json"):
                found.append(os.path.join(INBOX_DIR, fname))

    # Check root project directory
    local_path = os.path.join(PROJECT_DIR, "user_overrides.json")
    if os.path.exists(local_path) and local_path not in found:
        found.append(local_path)

    # Check system Downloads folder
    downloads_path = os.path.join(DOWNLOADS_DIR, "user_overrides.json")
    if os.path.exists(downloads_path) and downloads_path not in found:
        found.append(downloads_path)

    return found

def merge_overrides(source_file):
    if not os.path.exists(EDGE_CASES_FILE):
        print(f"Error: Master file '{EDGE_CASES_FILE}' not found.")
        return False

    with open(EDGE_CASES_FILE, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    with open(source_file, "r", encoding="utf-8") as f:
        new_overrides = json.load(f)

    if isinstance(new_overrides, dict) and "overrides" in new_overrides:
        new_list = new_overrides["overrides"]
    elif isinstance(new_overrides, list):
        new_list = new_overrides
    else:
        print(f"Error: Invalid format in '{source_file}'. Expected list or object with 'overrides' key.")
        return False

    master_streets_data = {}
    if os.path.exists(MASTER_STREETS_FILE):
        with open(MASTER_STREETS_FILE, "r", encoding="utf-8") as f:
            master_streets_data = json.load(f)

    existing_list = master_data.get("overrides", [])
    added_count = 0
    registry_updated_count = 0

    for new_item in new_list:
        if isinstance(new_item, dict) and new_item.get("action") == "UPDATE_MASTER_REGISTRY":
            slug = new_item.get("slug")
            if slug and slug in master_streets_data.get("streets", {}):
                st = master_streets_data["streets"][slug]
                if "audit_status" in new_item: st["audit_status"] = new_item["audit_status"]
                if "former_names" in new_item: st["former_names"] = new_item["former_names"]
                if "sub_sections" in new_item: st["sub_sections"] = new_item["sub_sections"]
                if "numbering_scheme" in new_item: st["numbering_scheme"] = new_item["numbering_scheme"]
                if "district" in new_item: st["district"] = new_item["district"]
                if "parish" in new_item: st["parish"] = new_item["parish"]
                if "coordinates" in new_item: st["coordinates"] = new_item["coordinates"]
                if "notes" in new_item: st["notes"] = new_item["notes"]
                registry_updated_count += 1
            continue

        # Avoid duplicate match rules
        match_str = json.dumps(new_item.get("match"), sort_keys=True)
        apply_str = json.dumps(new_item.get("apply"), sort_keys=True)
        
        is_dup = False
        for ex in existing_list:
            ex_match = json.dumps(ex.get("match"), sort_keys=True)
            ex_apply = json.dumps(ex.get("apply"), sort_keys=True)
            if match_str == ex_match and apply_str == ex_apply:
                is_dup = True
                break
        
        if not is_dup:
            existing_list.append(new_item)
            added_count += 1

    master_data["overrides"] = existing_list

    with open(EDGE_CASES_FILE, "w", encoding="utf-8") as f:
        json.dump(master_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    if registry_updated_count > 0:
        with open(MASTER_STREETS_FILE, "w", encoding="utf-8") as f:
            json.dump(master_streets_data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"🏛️ Updated {registry_updated_count} street entry(ies) in '{MASTER_STREETS_FILE}'.")

    print(f"✅ Successfully merged {added_count} new override rule(s) from '{source_file}' into '{EDGE_CASES_FILE}'.")
    return True

def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    sources = find_user_overrides_file(arg)
    if not sources:
        print(f"No override JSON files found in:\n  - {INBOX_DIR}/\n  - {PROJECT_DIR}/\n  - {DOWNLOADS_DIR}/user_overrides.json")
        print("\nPlease save your exported 'user_overrides.json' into the 'overrides_inbox/' folder or specify a file path.")
        sys.exit(1)

    merged_any = False
    for src in sources:
        if merge_overrides(src):
            merged_any = True
            # Clean up merged file if inside overrides_inbox
            if src.startswith(INBOX_DIR) and os.path.exists(src):
                try:
                    os.remove(src)
                    print(f"🧹 Cleaned up inbox file: {os.path.basename(src)}")
                except Exception as e:
                    print(f"Notice: Could not auto-delete {src}: {e}")

    if merged_any:
        print("\nRebuilding dataset with new merged edge cases...")
        os.system(f"python3 '{os.path.join(SCRIPT_DIR, 'clean_csv.py')}' && python3 '{os.path.join(SCRIPT_DIR, 'build_site_data.py')}'")

if __name__ == "__main__":
    main()
