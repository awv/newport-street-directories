#!/usr/bin/env python3
"""
clean_phase2_noise.py
---------------------
Targeted cleanup pass to eliminate remaining OCR non-trade noise:
1. Clears single-character noise: 'n', '&', 'S', 'l', 'v', 'y', etc.
2. Clears return footnote marks: 'Return.)', '(return.)', etc.
3. Rescues trades wrapped in brackets: 'Labourer [ ] [ ] [' -> 'Labourer'
4. Expands valid abbreviations: 'lab' -> 'Labourer', 'sec' -> 'Secretary', etc.
5. Clears ward/district polling codes: 'D 3', 'C 4', 'C 5', 'D 5', etc.
6. Clears house numbers & unbuilt tags in trade column: '18-20', '35a', 'to 8 Unbuilt'
7. Clears clipped OCR syllables from name splits: 'ne', 'll', 'er', 'st', 'rd', 'od', 'le', etc.

Rebuilds data/trades.json and updates the site search index.
"""

import csv
import json
import os
import re
import shutil
import sys
import time
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "scripts" else SCRIPT_DIR
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")

KNOWN_EXPANSIONS = {
    'lab': 'Labourer',
    'sec': 'Secretary',
    'dvr': 'Driver',
    'drvr': 'Driver',
    'ptr': 'Painter',
    'clk': 'Clerk',
    'trm': 'Trimmer',
    'mcht': 'Merchant',
    'agt': 'Agent',
    'wkr': 'Worker',
    'gas': 'Gas Worker',
    'cab': 'Cab Driver',
    'dk': 'Dock Worker',
    'gen': 'General Dealer',
    'mer': 'Merchant',
    'ins': 'Insurance Agent',
    'i.w': 'Ironworker',
}

KNOWN_OCR_SYLLABLES = {
    'ne', 'll', 'er', 'st', 'rd', 'od', 'le', 'cy', 'ch', 'les', 'ook',
    'von', 'mas', 'lda', 'lyn', 'wen', 'eep', 'wis', 'ith', 'mo', 'ans',
    'ner', 'iry', 'nny', 'an', 'en', 'ria', 'cot', 'yn', 'id', 'ma', 'ho',
    'es', 'nes', 'sh', 'op', 'bl', 'de'
}

RETURN_PURE_PAT = re.compile(r'^[\(\[]?return[\.\)\]\s]*$', re.I)
RETURN_WRAP_PAT = re.compile(r'[\(\[]?return[\.\)\]\s]*', re.I)

def main():
    t0 = time.time()
    print(f"Reading {DATA_CSV} for targeted noise cleanup...")

    with open(DATA_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    fieldnames = list(rows[0].keys()) if rows else []
    cleaned_counts = Counter()
    replacements = Counter()

    for r in rows:
        raw = (r.get("trade") or "").strip()
        if not raw:
            continue
        
        t_low = raw.lower()
        new_t = raw

        # 1. Single characters (len == 1)
        if len(raw) == 1:
            new_t = ""
            cleaned_counts["single_character"] += 1

        # 2. Return footnote marks
        elif RETURN_PURE_PAT.fullmatch(raw):
            new_t = ""
            cleaned_counts["return_footnote"] += 1
        elif RETURN_WRAP_PAT.search(raw):
            sub = RETURN_WRAP_PAT.sub("", raw).strip(" ,-")
            if sub and len(sub) > 2:
                new_t = sub.capitalize() if sub[0].islower() else sub
                cleaned_counts["return_rescued"] += 1

        # 3. Trailing empty brackets on clean trades (e.g. 'Labourer [ ] [ ] [')
        elif re.search(r'\s*\[[\s\[\]]*$', raw):
            sub = re.sub(r'\s*\[[\s\[\]]*$', '', raw).strip()
            if sub and len(sub) > 2:
                new_t = sub.capitalize() if sub[0].islower() else sub
                cleaned_counts["brackets_stripped"] += 1

        # 4. Known abbreviations to expand
        elif t_low in KNOWN_EXPANSIONS:
            new_t = KNOWN_EXPANSIONS[t_low]
            cleaned_counts["abbrev_expanded"] += 1

        # 5. District/ward polling codes (D 3, C 4, C 5, D 5, etc.)
        elif re.fullmatch(r'[A-Za-z]\s*\d+', raw):
            new_t = ""
            cleaned_counts["district_code"] += 1

        # 6. House numbers / unbuilt spills
        elif re.fullmatch(r'\(?\d+[-\d]*[a-zA-Z]?\)?', raw) or re.fullmatch(r'to \d+ unbuilt', raw, re.I):
            new_t = ""
            cleaned_counts["house_number_leak"] += 1

        # 7. Clipped OCR name syllables
        elif t_low in KNOWN_OCR_SYLLABLES:
            new_t = ""
            cleaned_counts["syllables_cleared"] += 1

        if new_t != raw:
            r["trade"] = new_t
            replacements[(raw, new_t)] += 1

    temp_csv = DATA_CSV + ".tmp"
    with open(temp_csv, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    shutil.move(temp_csv, DATA_CSV)
    print(f"Successfully cleaned {sum(cleaned_counts.values()):,} records in {DATA_CSV}!")
    print(f"Repaired or cleared {len(replacements):,} distinct non-trade noise strings.")

    print("\nAction breakdown:")
    for k, v in sorted(cleaned_counts.items()):
        print(f"  {k:25s}: {v:,} records")

    print("\nSample top cleanups:")
    for (old, new), cnt in replacements.most_common(20):
        print(f"  {cnt:3d}: {repr(old)} -> {repr(new)}")

    # Re-merge casing twins if any were produced
    try:
        import merge_casing_twins
        merge_casing_twins.main()
    except Exception as e:
        print(f"Warning: Could not run merge_casing_twins: {e}")

    # Rebuild trades data
    print("\nRebuilding data/trades.json...")
    try:
        import build_trades_data
        build_trades_data.build()
    except Exception as e:
        print(f"Warning: Could not rebuild trades data: {e}")

    # Rebuild search index
    print("\nRebuilding site data and search index...")
    try:
        import build_site_data
        build_site_data.main()
    except Exception as e:
        print(f"Warning: Could not rebuild site data: {e}")

    print(f"\nCleanup pass completed in {time.time() - t0:.2f}s!")

if __name__ == "__main__":
    main()
