#!/usr/bin/env python3
"""
apply_trade_audit.py
--------------------
Applies trade overrides exported from trades.html (or stored in trade_overrides.json)
to data.csv and integrates new mappings into scripts/clean_csv.py.

Usage:
    python3 scripts/apply_trade_audit.py [path_to_overrides.json]
"""

import csv
import json
import os
import re
import sys
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "scripts" else SCRIPT_DIR
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
DEFAULT_RULES_FILE = os.path.join(PROJECT_ROOT, "trade_overrides.json")
CLEAN_CSV_PATH = os.path.join(PROJECT_ROOT, "scripts", "clean_csv.py")

VERIFIED_FILE = os.path.join(PROJECT_ROOT, "data", "verified_trades.json")

def main():
    import glob
    import time
    rules_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RULES_FILE
    if not os.path.exists(rules_file):
        patterns = [
            "~/Downloads/trade_audit*.json",
            "~/Downloads/trade_overrides*.json",
            "~/Downloads/verified_trades*.json"
        ]
        dl_matches = []
        for p in patterns:
            dl_matches.extend(glob.glob(os.path.expanduser(p)))

        if dl_matches:
            # Sort all matches by newest modified time
            dl_matches.sort(key=lambda f: os.path.getmtime(f), reverse=True)
            rules_file = dl_matches[0]
            print(f"Found latest exported file: {rules_file} (modified {time.ctime(os.path.getmtime(rules_file))})")
        else:
            print(f"Error: Rules or verification file '{rules_file}' not found.")
            print(f"\nTo generate this file:")
            print(f"1. In trades.html, make your merges or mark trades verified.")
            print(f"2. Click the '⚙️ Rules & Verified' button in the top right header.")
            print(f"3. Click '💾 Export All (Rules + Verified JSON)'.")
            print(f"4. Then re-run this command: python3 scripts/apply_trade_audit.py\n")
            sys.exit(1)

    with open(rules_file, "r", encoding="utf-8") as f:
        raw_input = json.load(f)

    overrides = {}
    imported_verified = []

    if isinstance(raw_input, dict):
        if "overrides" in raw_input or "verified" in raw_input:
            overrides = raw_input.get("overrides", {})
            imported_verified = raw_input.get("verified", [])
        else:
            overrides = raw_input
    elif isinstance(raw_input, list):
        imported_verified = raw_input

    # Check also if there's a separate verified_trades file in Downloads if not passed
    verified_dl = glob.glob(os.path.expanduser("~/Downloads/verified_trades*.json"))
    if verified_dl:
        verified_dl.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        try:
            with open(verified_dl[0], "r", encoding="utf-8") as vf:
                v_content = json.load(vf)
                if isinstance(v_content, list):
                    imported_verified.extend(v_content)
        except Exception:
            pass

    # Separate global rules vs single-record overrides
    global_rules = {}
    single_record_rules = {}

    for k, v in overrides.items():
        v = v.strip()
        if not v:
            continue
        if k.startswith("single:"):
            parts = k.split(":", 6)
            if len(parts) == 7:
                single_record_rules[k] = v
        else:
            global_rules[k.lower().strip()] = v

    # Update verified trades file
    existing_verified = set()
    if os.path.exists(VERIFIED_FILE):
        try:
            with open(VERIFIED_FILE, "r", encoding="utf-8") as f:
                v_list = json.load(f)
                if isinstance(v_list, list):
                    existing_verified.update(v_list)
        except Exception as e:
            print(f"Warning reading {VERIFIED_FILE}: {e}")

    # Add any explicitly imported verified trades
    for v in imported_verified:
        if isinstance(v, str) and v.strip():
            existing_verified.add(v.strip())

    # Also automatically add any targets of valid global rules (except non-trades)
    for target in global_rules.values():
        if target and target not in ("Residence / Private", "Private", "None", "-"):
            existing_verified.add(target)

    # Save sorted verified trades
    sorted_verified = sorted(list(existing_verified), key=lambda s: s.lower())
    with open(VERIFIED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_verified, f, indent=2)
    print(f"Verified occupations updated in {VERIFIED_FILE} ({len(sorted_verified)} total verified).")

    # Save master overrides
    master_overrides_file = os.path.join(PROJECT_ROOT, "data", "trade_overrides_master.json")
    master_overrides = {}
    if os.path.exists(master_overrides_file):
        try:
            with open(master_overrides_file, "r", encoding="utf-8") as f:
                master_overrides = json.load(f)
        except Exception:
            pass
    master_overrides.update(global_rules)
    with open(master_overrides_file, "w", encoding="utf-8") as f:
        json.dump(master_overrides, f, indent=2)

    print(f"Loaded {len(global_rules)} global trade rules and {len(single_record_rules)} single-record overrides.")

    # Read data.csv and apply replacements
    temp_csv = DATA_CSV + ".tmp"
    modified_rows = 0
    total_rows = 0

    with open(DATA_CSV, "r", encoding="utf-8") as f_in, open(temp_csv, "w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for r in reader:
            total_rows += 1
            yr = r.get("year", "").strip()
            st = r.get("street", "").strip()
            hn = r.get("house_number", "").strip()
            fn = r.get("forename", "").strip()
            sn = r.get("surname", "").strip()
            tr = r.get("trade", "").strip()

            rec_key = f"single:{yr}:{st}:{hn}:{fn}:{sn}:{tr}"
            new_trade = None

            if rec_key in single_record_rules:
                new_trade = single_record_rules[rec_key]
            elif tr.lower() in global_rules:
                new_trade = global_rules[tr.lower()]

            if new_trade is not None and new_trade != tr:
                # If mapped to "Residence / Private", clear or blank trade
                if new_trade in ("Residence / Private", "Private", "None", "-"):
                    r["trade"] = ""
                else:
                    r["trade"] = new_trade
                modified_rows += 1

            writer.writerow(r)

    shutil.move(temp_csv, DATA_CSV)
    print(f"Applied trade corrections to {modified_rows:,} records across data.csv ({total_rows:,} total).")

    # Rebuild trades data index
    try:
        import build_trades_data
        build_trades_data.build()
    except Exception as e:
        print(f"Could not rebuild trades data: {e}")

    print("Trade audit applied successfully! Rebuilding search index...")
    try:
        import build_site_data
        build_site_data.main()
    except Exception as e:
        print(f"Could not run build_site_data: {e}")

    # Clean up processed audit export files from ~/Downloads
    try:
        downloads_dir = os.path.realpath(os.path.expanduser("~/Downloads"))
        dl_to_clean = (
            glob.glob(os.path.join(downloads_dir, "trade_audit*.json")) +
            glob.glob(os.path.join(downloads_dir, "trade_overrides*.json")) +
            glob.glob(os.path.join(downloads_dir, "verified_trades*.json"))
        )
        cleaned = []
        for f_path in set(dl_to_clean):
            try:
                os.remove(f_path)
                cleaned.append(os.path.basename(f_path))
            except Exception:
                pass
        if cleaned:
            print(f"🗑️ Cleaned up imported file(s) from ~/Downloads: {', '.join(cleaned)}")
    except Exception as e:
        print(f"Note: Could not clean up Downloads: {e}")

if __name__ == "__main__":
    main()
