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

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
EDGE_CASES_FILE = os.path.join(PROJECT_DIR, "edge_cases.json")
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")

def find_user_overrides_file(arg_path=None):
    if arg_path and os.path.exists(arg_path):
        return arg_path
    
    local_path = os.path.join(PROJECT_DIR, "user_overrides.json")
    if os.path.exists(local_path):
        return local_path

    downloads_path = os.path.join(DOWNLOADS_DIR, "user_overrides.json")
    if os.path.exists(downloads_path):
        return downloads_path

    return None

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

    existing_list = master_data.get("overrides", [])
    added_count = 0

    for new_item in new_list:
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

    print(f"✅ Successfully merged {added_count} new override rule(s) from '{source_file}' into '{EDGE_CASES_FILE}'.")
    return True

def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    source = find_user_overrides_file(arg)
    if not source:
        print("No 'user_overrides.json' file found in current directory or ~/Downloads.")
        print("Please export your overrides from the browser first or specify file path.")
        sys.exit(1)

    if merge_overrides(source):
        # Trigger rebuild
        print("\nRebuilding dataset with new merged edge cases...")
        os.system("python3 clean_csv.py && python3 build_site_data.py")

if __name__ == "__main__":
    main()
