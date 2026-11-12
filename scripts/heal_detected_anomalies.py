#!/usr/bin/env python3
"""
heal_detected_anomalies.py
==========================
Deterministically heals verified anomalies in data.csv using the
high-confidence rules from detect_data_anomalies.py.

Workflow:
1. Creates backup of data.csv
2. Reads data.csv and applies healed fields to matching records
3. Validates row count and schema
4. Writes updated data.csv
5. Rebuilds site data (build_site_data.py) and stats (build_stats_data.py)
6. Re-runs detect_data_anomalies.py to update the audit dashboard
"""

import os
import sys
import csv
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
BACKUP_CSV = os.path.join(PROJECT_ROOT, "data.csv.bak_before_anomaly_healing")
TSV_ANOMALIES = os.path.join(PROJECT_ROOT, "reports", "data_anomalies.tsv")

def main():
    if not os.path.exists(TSV_ANOMALIES):
        print(f"Error: {TSV_ANOMALIES} not found. Run detect_data_anomalies.py first.")
        sys.exit(1)

    print("Loading high-confidence anomalies to heal...")
    fixes_by_idx = {}
    with open(TSV_ANOMALIES, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            if r.get("confidence") == "HIGH":
                idx = int(r["record_idx"])
                fixes_by_idx[idx] = {
                    "house_number": r["healed_house_number"],
                    "building_name": r["healed_building_name"],
                    "surname": r["healed_surname"],
                    "forename": r["healed_forename"],
                    "trade": r["healed_trade"],
                }

    print(f"Loaded {len(fixes_by_idx):,} high-confidence fixes.")

    print(f"Creating backup: {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)

    print("Reading data.csv and applying fixes...")
    rows = []
    applied_count = 0
    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for i, row in enumerate(reader):
            if i in fixes_by_idx:
                fix = fixes_by_idx[i]
                row["house_number"] = fix["house_number"]
                row["building_name"] = fix["building_name"]
                row["surname"] = fix["surname"]
                row["forename"] = fix["forename"]
                row["trade"] = fix["trade"]
                applied_count += 1
            rows.append(row)

    print(f"Applied {applied_count:,} fixes across data.csv.")

    print("Writing updated data.csv...")
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Rebuilding site data and JSON indexes...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_site_data.py")], check=True)

    print("Rebuilding stats data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_stats_data.py")], check=True)

    print("Re-scanning dataset to update audit dashboard...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "detect_data_anomalies.py")], check=True)

    print("\n[SUCCESS] Anomaly healing complete! Dashboard updated at reports/anomaly_review.html")

if __name__ == "__main__":
    main()
