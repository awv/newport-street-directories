#!/usr/bin/env python3
"""Heal title-only surnames with surname-like trades and clean pure-text/noise house_numbers."""

import csv
import re
import shutil
from collections import Counter

CSV_PATH = "data.csv"
BACKUP_PATH = "data.csv.bak_before_title_sn_and_hn_noise"

SURNAME_LIKE_TRADES = {
    "smith", "cook", "baker", "taylor", "carter", "mason", "porter", "miller",
    "cooper", "carpenter", "butcher", "packer", "hawker", "seaman", "foreman",
    "gardener", "gardner", "turner", "clark", "clarke", "driver", "weaver",
    "walker", "hall", "ward", "wood", "woods", "bell", "cole", "day", "king",
    "knight", "page", "stone", "webb", "wells", "young", "brooks", "butler",
    "chapman", "foster", "fowler", "glover", "harper", "hunter", "marshall",
    "palmer", "parker", "shepherd", "slater", "spencer", "tanner", "webster", "wright",
}

HN_JUNK = {"newport.", "newport", "the.", "(the)", "(no thoroughfare.)"}
BLDG_HN_RE = re.compile(
    r"\b(villa|villas|hotel|house|inn|tavern|ferns|park|terrace|kilns|tennis|cottages|lodge|hall)\b",
    re.I,
)


def main() -> None:
    shutil.copy2(CSV_PATH, BACKUP_PATH)
    print(f"Backed up {CSV_PATH} -> {BACKUP_PATH}")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    counts = Counter()

    for row in rows:
        st = row["street"].strip()
        hn = row["house_number"].strip()
        bldg = row["building_name"].strip()
        sn = row["surname"].strip()
        fn = row["forename"].strip()
        tr = row["trade"].strip()

        # 1. Title-only surname + surname-like trade (skip Market stalls)
        if (
            sn.rstrip(".").lower() in ("mrs", "miss", "mr", "dr", "rev")
            and tr.lower() in SURNAME_LIKE_TRADES
            and "market" not in st.lower()
            and "school" not in fn.lower()
        ):
            title = sn.rstrip(".") + "."
            row["surname"] = tr
            row["forename"] = f"{title} {fn}".strip() if fn else title
            row["trade"] = ""
            counts["1_title_surname_swapped"] += 1

        # 2. Pure noise in house_number
        if hn:
            if hn.lower() in HN_JUNK or all(not c.isalnum() for c in hn):
                row["house_number"] = ""
                counts["2_hn_noise_cleared"] += 1
            elif not bldg and not any(c.isdigit() for c in hn) and BLDG_HN_RE.search(hn):
                row["building_name"] = hn.rstrip(".- ")
                row["house_number"] = ""
                counts["3_hn_building_moved"] += 1

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total rows updated: {sum(counts.values())}")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
