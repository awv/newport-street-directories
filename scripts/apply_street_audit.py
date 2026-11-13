#!/usr/bin/env python3
"""
scripts/apply_street_audit.py

Convenience utility to ingest exported audit files from the Street Master Registry Audit tool (streets_audit.html).
It automatically detects:
  1. ~/Downloads/master_streets.json OR ./master_streets.json
  2. ~/Downloads/user_overrides.json OR ./user_overrides.json OR overrides_inbox/*.json

Applies changes directly into the project master files and re-runs build_site_data.py.
"""

import os
import sys
import shutil
import json
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")

def main():
    print("=" * 60)
    print("🏛️ Newport Street Master Registry Audit Sync")
    print("=" * 60)

    # Check for direct master_streets.json in Downloads
    dl_master = os.path.join(DOWNLOADS_DIR, "master_streets.json")
    proj_master = os.path.join(PROJECT_DIR, "master_streets.json")

    applied_master = False
    if os.path.exists(dl_master):
        try:
            with open(dl_master, "r", encoding="utf-8") as f:
                data = json.load(f)
            streets_cnt = len(data.get("streets", {}))
            print(f"📥 Found exported master_streets.json in Downloads ({streets_cnt} streets).")
            # Create a backup of current master_streets.json
            backup_path = os.path.join(PROJECT_DIR, "master_streets.backup.json")
            if os.path.exists(proj_master):
                shutil.copy2(proj_master, backup_path)
            shutil.copy2(dl_master, proj_master)
            os.remove(dl_master)
            print(f"✅ Successfully updated '{proj_master}' from Downloads (Backup saved to master_streets.backup.json).")
            applied_master = True
        except Exception as e:
            print(f"⚠️ Error reading '{dl_master}': {e}")

    # Also check if merge_overrides needs to run
    merge_script = os.path.join(PROJECT_DIR, "scripts", "merge_overrides.py")
    if os.path.exists(merge_script):
        res = subprocess.run([sys.executable, merge_script], capture_output=True, text=True, cwd=PROJECT_DIR)
        if "Successfully merged" in res.stdout or "Updated" in res.stdout:
            print(res.stdout)
            applied_master = True

    if applied_master:
        print("\n🔨 Rebuilding site data with updated master registry...")
        build_script = os.path.join(PROJECT_DIR, "scripts", "build_site_data.py")
        subprocess.run([sys.executable, build_script], check=True, cwd=PROJECT_DIR)
        print("\n✨ Done! Your audit changes are live across the archive.")
    else:
        print("ℹ️ No new downloaded audit files found in ~/Downloads.")
        print("👉 In 'streets_audit.html', click 'Download master_streets.json' or 'Download user_overrides.json', then run this command again.")

if __name__ == "__main__":
    main()
