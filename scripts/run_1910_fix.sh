#!/bin/bash
set -e
cd "/Users/robgale/Documents/Newport Street Directory Project"

echo "=== [1/5] Parsing 1910 Raw TSV ==="
python3 scripts/parse_1910.py

echo "=== [2/5] Merging Clean 1910 Records into data.csv ==="
python3 scripts/merge_1910.py

echo "=== [3/5] Rebuilding Site JSON Data ==="
python3 scripts/build_site_data.py

echo "=== [4/5] Merging Casing Twins ==="
python3 scripts/merge_casing_twins.py

echo "=== [5/5] Updating Stats Analytics ==="
python3 scripts/build_stats_data.py

echo "=== 1910 Volume Fix Completed Successfully ==="
