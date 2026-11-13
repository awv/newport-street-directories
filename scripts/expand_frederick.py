#!/usr/bin/env python3
"""
Expand historical abbreviations for Frederick (`F'k.`, `F'k`, `Fk.`, `Fk`,
`Fred'k.`, `Fred'k`, `Fredk.`, `Fredk`) to `Frederick` across `forename` and
`surname` in `data.csv` (all years including 1971).
"""

import csv
import os
import re
from collections import Counter

FRED_RE = re.compile(r"\b(?:F'k|Fk|Fred'k|Fredk)\.?(?!\w)")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data.csv")

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    stats = Counter()
    for r in rows:
        for col in ("forename", "surname"):
            val = r[col] or ""
            if not val:
                continue
            new_val, n = FRED_RE.subn("Frederick", val)
            if n > 0 and new_val != val:
                r[col] = new_val
                stats[col] += n

    print("Replaced:", dict(stats), "Total:", sum(stats.values()))
    if sum(stats.values()) > 0:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {csv_path}")


if __name__ == "__main__":
    main()
