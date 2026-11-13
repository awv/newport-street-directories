#!/usr/bin/env bash
set -e
cd "/Users/robgale/Documents/Newport Street Directory Project"

echo "=== Step 1: Parsing 1915 with column-drift resolution ==="
python3 scripts/parse_1915.py

echo "=== Step 2: Merging 1915 cleaned records into data.csv ==="
python3 scripts/merge_1915.py

echo "=== Step 3: Rebuilding per-street JSONs and search index ==="
python3 scripts/build_site_data.py

echo "=== Step 4: Normalizing casing twins in trades.json ==="
python3 scripts/merge_casing_twins.py

echo "=== Step 5: Updating Archive Statistics & Diagnostics ==="
python3 scripts/build_stats_data.py

echo "=== 1915 Resolution & Site Rebuild Completed Successfully! ==="
