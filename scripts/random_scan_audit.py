#!/usr/bin/env python3
"""
Generate a stratified random sample of records from data.csv across all
Johns Directory years (1878-1971) for visual cross-referencing against
original_scans/.
"""

import csv
import json
import os
import random
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(ROOT, "data.csv")
SCANS_DIR = os.path.join(ROOT, "original_scans")
OUT_JSON = os.path.join(ROOT, "reports", "scan_audit_sample.json")

SEED = 42

ERA_TARGETS = [
    ("1878-1895", lambda y: 1878 <= y <= 1895, 12),
    ("1898-1913", lambda y: 1898 <= y <= 1913, 13),
    ("1915-1936", lambda y: 1915 <= y <= 1936, 15),
    ("1971", lambda y: y == 1971, 10),
]


def get_scan_files(year: int) -> list[str]:
    folder = os.path.join(SCANS_DIR, f"Johns Directory {year}")
    if not os.path.isdir(folder):
        return []
    files = [
        f for f in os.listdir(folder)
        if f.lower().endswith((".jpeg", ".jpg", ".png")) and not f.startswith(".")
    ]
    files.sort()
    return files


def main():
    rng = random.Random(SEED)
    by_year = defaultdict(list)
    streets_by_year = defaultdict(set)

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):  # 1-based CSV line number
            try:
                year = int(row["year"])
            except (ValueError, TypeError):
                continue
            row_with_meta = dict(row)
            row_with_meta["csv_line"] = idx
            by_year[year].append(row_with_meta)
            streets_by_year[year].add(row["street"])

    scan_cache = {y: get_scan_files(y) for y in by_year}
    sorted_streets = {y: sorted(s, key=lambda x: x.lower()) for y, s in streets_by_year.items()}

    sample = []
    for era_name, pred, count in ERA_TARGETS:
        pool = []
        for y, rows in by_year.items():
            if pred(y) and scan_cache.get(y):
                pool.extend(rows)
        chosen = rng.sample(pool, count)
        for row in chosen:
            y = int(row["year"])
            scans = scan_cache[y]
            st_list = sorted_streets[y]
            st_idx = st_list.index(row["street"])
            frac = st_idx / max(1, len(st_list) - 1)
            est_idx = min(len(scans) - 1, max(0, round(frac * (len(scans) - 1))))
            sample.append({
                "id": len(sample) + 1,
                "era": era_name,
                "csv_line": row["csv_line"],
                "year": y,
                "street": row["street"],
                "house_number": row["house_number"],
                "building_name": row["building_name"],
                "surname": row["surname"],
                "forename": row["forename"],
                "trade": row["trade"],
                "scan_folder": f"original_scans/Johns Directory {y}",
                "total_scans": len(scans),
                "est_scan_index": est_idx,
                "est_scan_file": scans[est_idx],
                "all_scans": scans,
            })

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2)

    print(f"Generated {len(sample)} stratified random records -> {OUT_JSON}")
    for item in sample:
        print(
            f"#{item['id']:02d} [{item['era']}] {item['year']} | {item['street']} | "
            f"No.{item['house_number']} {item['building_name']} | "
            f"{item['forename']} {item['surname']} | {item['trade']} "
            f"-> est {item['est_scan_file']} ({item['est_scan_index']+1}/{item['total_scans']})"
        )


if __name__ == "__main__":
    main()
