#!/bin/bash
set -e
cd "/Users/robgale/Documents/Newport Street Directory Project"

echo "=== [1/5] Parsing 1902 Raw TSV ==="
python3 scripts/parse_1902.py

echo "=== [2/5] Merging Clean 1902 Records into data.csv ==="
python3 scripts/merge_1902.py

echo "=== [3/5] Rebuilding Site JSON Data ==="
python3 scripts/build_site_data.py

echo "=== [4/5] Merging Casing Twins ==="
python3 scripts/merge_casing_twins.py

echo "=== [5/5] Updating Stats Analytics ==="
python3 scripts/build_stats_data.py

echo "=== 1902 Volume Fix Completed Successfully ==="
