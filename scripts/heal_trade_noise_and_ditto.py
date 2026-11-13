#!/usr/bin/env python3
"""Clean pure-symbol/digits-only trade noise, strip edge punctuation, and resolve Do/Ditto trades across all years."""

import csv
import shutil
from collections import Counter, defaultdict

CSV_PATH = "data.csv"
BACKUP_PATH = "data.csv.bak_before_trade_noise_and_ditto"

DITTO_TOKENS = {"do", "do.", "ditto", '"'}
NULL_TOKENS = {"nan", "none", "null", "n/a"}


def main() -> None:
    shutil.copy2(CSV_PATH, BACKUP_PATH)
    print(f"Backed up {CSV_PATH} -> {BACKUP_PATH}")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    counts = Counter()
    prev_key = None
    prev_trade = ""

    for row in rows:
        yr = row["year"].strip()
        st = row["street"].strip()
        tr = row["trade"].strip()
        cur_key = (yr, st)

        if tr:
            # 1. Null-like literals
            if tr.lower() in NULL_TOKENS:
                row["trade"] = ""
                counts["1_null_literal_cleared"] += 1
                tr = ""
            # 2. Pure symbol/punctuation noise
            elif all(not c.isalnum() for c in tr) and tr.lower() not in DITTO_TOKENS:
                row["trade"] = ""
                counts["2_pure_symbol_cleared"] += 1
                tr = ""
            # 3. Digits-only stray numbers
            elif tr.isdigit():
                row["trade"] = ""
                counts["3_digits_only_cleared"] += 1
                tr = ""
            # 4. Do / Ditto propagation from preceding row on same (year, street)
            elif tr.lower() in DITTO_TOKENS:
                if prev_key == cur_key and prev_trade and prev_trade.lower() != "void":
                    row["trade"] = prev_trade
                    tr = prev_trade
                    counts["4_ditto_propagated"] += 1
                else:
                    counts["4b_ditto_unresolved"] += 1
            else:
                # 5. Strip stray leading/trailing punctuation (-,;|/\)
                cleaned = tr.strip(" \t\r\n-,;|/\\`")
                if cleaned != tr:
                    row["trade"] = cleaned
                    tr = cleaned
                    counts["5_edge_punct_stripped"] += 1

        prev_key = cur_key
        if tr and tr.lower() not in DITTO_TOKENS:
            prev_trade = tr
        elif prev_key != cur_key:
            prev_trade = ""

    # 6. Re-normalize any newly exposed trade casing twins across all years
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
                counts["6_casing_normalized"] += 1

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total rows updated: {sum(counts.values())}")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
