#!/usr/bin/env python3
"""
Conservatively standardise safe forename formatting differences (year <= 1936)
when anchored to the exact same (street, house_number, surname):
1. Trailing dot on an already-full name: e.g. `Axel.` -> `Axel` when `Axel`
   also appears at the exact same address and surname.
2. Unique multi-letter abbreviation (>= 3 letters + '.'): e.g. `Jab.` -> `Jabez`
   when exactly one longer full forename at the same address and surname
   starts with that stem.

Leaves single-letter initials (`J.`), different initials (`S.` vs `J.`), and
fuzzy spelling differences (`Axelsen` vs `Axel`, `Gherbich` vs `Gherhich`) untouched.
"""

import argparse
import csv
import os
import re
from collections import Counter, defaultdict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing data.csv")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data.csv")

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    by_addr = defaultdict(list)
    for idx, r in enumerate(rows):
        hn = (r["house_number"] or "").strip()
        sn = (r["surname"] or "").strip()
        fn = (r["forename"] or "").strip()
        if hn and sn and fn:
            by_addr[(r["street"], hn, sn.lower())].append(idx)

    titles_and_abbrevs = {
        "mrs", "miss", "rev", "capt", "col", "dr", "sergt", "supt", "insp",
        "prof", "hon", "sml", "thos", "chas", "geo", "jas", "benj", "edw",
        "rob", "rich", "hy", "albt",
    }

    stats = Counter()
    samples = {"trailing_dot": [], "unique_abbrev": []}

    for key, indices in by_addr.items():
        full_fns = {}
        for idx in indices:
            fn = rows[idx]["forename"].strip()
            if len(fn) > 2 and not fn.endswith("."):
                full_fns[fn.lower()] = fn

        if not full_fns:
            continue

        for idx in indices:
            fn = rows[idx]["forename"].strip()
            if not fn.endswith(".") or len(fn) <= 2:
                continue

            # Never strip trailing dot from a single-letter initial (e.g. 'C. H.', 'Enoch S.')
            if re.search(r"(?:^|\s)[A-Za-z]\.$", fn):
                continue

            stem = fn[:-1].lower()
            if stem in titles_and_abbrevs:
                continue

            # Rule 1: exact dotless match at same address+surname (e.g. 'Axel.' -> 'Axel')
            if stem in full_fns:
                new_fn = full_fns[stem]
                if new_fn != fn:
                    stats["trailing_dot"] += 1
                    if len(samples["trailing_dot"]) < 15:
                        r = rows[idx]
                        samples["trailing_dot"].append(
                            f"{r['year']} {r['street']} No.{r['house_number']} ({r['surname']}): {fn!r} -> {new_fn!r}"
                        )
                    if not args.dry_run:
                        rows[idx]["forename"] = new_fn
                continue

            # Rule 2: >= 3 letter stem + '.' with unique longer prefix match
            if re.fullmatch(r"[A-Za-z]{3,}\.", fn):
                matches = [
                    orig for low, orig in full_fns.items()
                    if low.startswith(stem) and len(low) > len(stem)
                ]
                if len(matches) == 1:
                    new_fn = matches[0]
                    stats["unique_abbrev"] += 1
                    if len(samples["unique_abbrev"]) < 15:
                        r = rows[idx]
                        samples["unique_abbrev"].append(
                            f"{r['year']} {r['street']} No.{r['house_number']} ({r['surname']}): {fn!r} -> {new_fn!r}"
                        )
                    if not args.dry_run:
                        rows[idx]["forename"] = new_fn

    print("Dry-run:" if args.dry_run else "Applied:", dict(stats), "Total:", sum(stats.values()))
    if args.dry_run:
        print("\nSample Rule 1 (Trailing dot):")
        for s in samples["trailing_dot"]:
            print(" ", s)
        print("\nSample Rule 2 (Unique >=3-letter abbrev):")
        for s in samples["unique_abbrev"]:
            print(" ", s)
    elif sum(stats.values()) > 0:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {csv_path}")


if __name__ == "__main__":
    main()
