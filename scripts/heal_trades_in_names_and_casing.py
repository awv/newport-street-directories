#!/usr/bin/env python3
"""Heal remaining Trades-in-Names forename leaks and normalize trade casing variants across all years."""

import csv
import re
import shutil
from collections import Counter, defaultdict

CSV_PATH = "data.csv"
BACKUP_PATH = "data.csv.bak_before_trades_in_names_and_casing"

FN_INIT_TRADE_RE = re.compile(r"^([A-Z]\.(?:\s*[A-Z]\.)?)\s*([a-z][a-z\s]{3,})$")
NURSE_RE = re.compile(r"^Nurse(?:\s+(.*))?$")


def main() -> None:
    shutil.copy2(CSV_PATH, BACKUP_PATH)
    print(f"Backed up {CSV_PATH} -> {BACKUP_PATH}")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    counts = Counter()

    # Pass 1: Heal Trades-in-Names leaks
    for row in rows:
        sn = row["surname"].strip()
        fn = row["forename"].strip()
        tr = row["trade"].strip()
        bldg = row["building_name"].strip()

        if not tr and fn:
            m = FN_INIT_TRADE_RE.match(fn)
            if m:
                row["forename"] = m.group(1).strip()
                row["trade"] = m.group(2).strip().title()
                counts["1a_initial_plus_lowercase_trade"] += 1
                continue

            m_nurse = NURSE_RE.match(fn)
            if m_nurse:
                row["forename"] = (m_nurse.group(1) or "").strip()
                row["trade"] = "Nurse"
                counts["1b_nurse_in_forename"] += 1
                continue

        if sn == "welding" and fn == "engineer" and tr == "engineer Freeguard Bros":
            row["surname"] = "Freeguard Bros"
            row["forename"] = ""
            row["trade"] = "Welding Engineer"
            counts["1c_welding_engineer_freeguard"] += 1
            continue

        if sn == "Clothing" and fn == "Factory" and not tr:
            if not bldg:
                row["building_name"] = "Clothing Factory"
            row["surname"] = ""
            row["forename"] = ""
            counts["1d_clothing_factory"] += 1
            continue

    # Pass 2: Normalize trade casing variants across all years (incl. 1971)
    groups: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        tr = row["trade"].strip()
        if tr:
            groups[tr.lower()][tr] += 1

    canonical_map: dict[str, str] = {}
    for k, c in groups.items():
        if len(c) > 1:
            canonical = c.most_common(1)[0][0]
            if canonical.islower():
                mixed = [v for v, _ in c.most_common() if not v.islower() and not v.isupper()]
                canonical = mixed[0] if mixed else canonical.title()
            canonical_map[k] = canonical

    for row in rows:
        tr = row["trade"].strip()
        if tr:
            target = canonical_map.get(tr.lower())
            if target and tr != target:
                row["trade"] = target
                counts["2_trade_casing_normalized"] += 1

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total rows updated: {sum(counts.values())}")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
