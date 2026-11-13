#!/usr/bin/env python3
"""
merge_casing_twins.py
---------------------
Auto-merges all trade entries that are identical except for capitalization
(e.g., merging 'labourer' into 'Labourer', 'ironworker' into 'Ironworker',
'engine driver' into 'Engine Driver', 'g.w.r' into 'G.W.R').

Applies changes directly to data.csv and rebuilds data/trades.json and the search index.
"""

import csv
import json
import os
import re
import sys
import shutil
import time
from collections import defaultdict, Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "scripts" else SCRIPT_DIR
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")

ACRONYMS = {'G.W.R.', 'G.W.R', 'G.P.O.', 'G.P.O', 'GPO', 'P.C.', 'H.M.C.', 'B.S.C.'}

def get_canonical(variants, counts):
    # 1. Check for standard acronyms
    for v in variants:
        if v.upper() in ACRONYMS:
            return v.upper()
    
    # 2. Check if a clean Title Case variant already exists
    title_candidates = []
    for v in variants:
        words = v.split()
        if all(w[0].isupper() and (len(w) == 1 or w[1:].islower() or w.endswith('.') or not w.isalpha()) for w in words if w):
            title_candidates.append(v)
    
    if title_candidates:
        return max(title_candidates, key=lambda x: counts[x])
    
    # 3. Otherwise generate standard Title Case from the most frequent variant
    base = max(variants, key=lambda x: counts[x])
    words = base.split()
    clean_words = []
    for i, w in enumerate(words):
        if w.upper() in ACRONYMS:
            clean_words.append(w.upper())
        elif i > 0 and w.lower() in ('and', 'of', '&', 'for', 'the', 'in', 'at', 'etc', '&c'):
            clean_words.append(w.lower())
        else:
            clean_words.append(w.capitalize())
    return ' '.join(clean_words)

def main():
    t0 = time.time()
    print(f"Scanning {DATA_CSV} for casing duplicates...")
    
    trades = Counter()
    total_records = 0
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            total_records += 1
            t = (r.get("trade") or "").strip()
            if t:
                trades[t] += 1

    lower_map = defaultdict(set)
    for t in trades:
        lower_map[t.lower()].add(t)

    casing_twins = {k: v for k, v in lower_map.items() if len(v) > 1}
    print(f"Found {len(casing_twins):,} distinct occupation groups with multiple casing variants.")

    # Build mapping
    mapping = {}
    for k, variants in casing_twins.items():
        canon = get_canonical(variants, trades)
        for v in variants:
            if v != canon:
                mapping[v] = canon

    records_to_update = sum(trades[k] for k in mapping)
    print(f"Generated {len(mapping):,} variant-to-canonical mappings.")
    print(f"Total records in data.csv to update: {records_to_update:,} (out of {total_records:,}).\n")

    print("Sample top merges:")
    sorted_mappings = sorted(mapping.items(), key=lambda x: -trades[x[0]])
    for old, new in sorted_mappings[:15]:
        print(f"  {trades[old]:5d} records: {repr(old)} -> {repr(new)}")
    print("  ...\n")

    # Apply to data.csv
    temp_csv = DATA_CSV + ".tmp"
    updated_count = 0
    with open(DATA_CSV, "r", encoding="utf-8") as f_in, open(temp_csv, "w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for r in reader:
            t = (r.get("trade") or "").strip()
            if t in mapping:
                r["trade"] = mapping[t]
                updated_count += 1
            writer.writerow(r)

    shutil.move(temp_csv, DATA_CSV)
    print(f"Successfully updated {updated_count:,} records in data.csv!")

    # Rebuild trades data
    print("\nRebuilding data/trades.json...")
    try:
        import build_trades_data
        build_trades_data.build()
    except Exception as e:
        print(f"Warning: Could not run build_trades_data: {e}")

    # Rebuild site data and search index
    print("\nRebuilding site data and global search index...")
    try:
        import build_site_data
        build_site_data.main()
    except Exception as e:
        print(f"Warning: Could not run build_site_data: {e}")

    print(f"\nAll operations completed successfully in {time.time() - t0:.2f}s!")

if __name__ == "__main__":
    main()
