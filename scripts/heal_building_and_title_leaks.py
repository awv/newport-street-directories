#!/usr/bin/env python3
"""Heal Title+Initials+Surname trapped in forename and building-name vs surname/trade column rotations."""

import csv
import re
import shutil
from collections import Counter

CSV_PATH = "data.csv"
BACKUP_PATH = "data.csv.bak_before_building_and_title_leaks"

TITLE_FN_RE = re.compile(
    r"^((?:Rev|Dr|Mrs|Miss|Mr|Capt|Col|Maj|Sergt|Insp)\.?\s+(?:[A-Z]\.?\s+)+)([A-Z][a-z'\-]{2,})$"
)
WELSH_SURNAMES = {
    "williams", "jones", "davies", "evans", "lewis", "thomas", "llewellyn", "james"
}
BLDG_RE = re.compile(
    r"\b(villa|villas|vils|house|ho|cot|cottage|cottages|arms|inn|tavern|hotel|ferns|mount|park|place|crescent|terrace|lodge|hall)\b|\[|^the\s",
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
        bldg = row["building_name"].strip()
        sn = row["surname"].strip()
        fn = row["forename"].strip()
        tr = row["trade"].strip()
        tr_l = tr.strip(". ,").lower()

        # 1. Blank surname + Title/Initials/Surname in forename
        if not sn and fn:
            m = TITLE_FN_RE.match(fn)
            if m:
                row["forename"] = m.group(1).strip()
                row["surname"] = m.group(2).strip()
                counts["1_title_surname_split_from_forename"] += 1
                continue

        # 2. Building in surname/forename + Welsh surname in trade
        if not bldg and tr_l in WELSH_SURNAMES:
            if BLDG_RE.search(sn):
                row["building_name"] = sn
                row["surname"] = tr
                row["trade"] = ""
                counts["2a_bldg_in_surname_rotated"] += 1
                continue
            if BLDG_RE.search(fn):
                row["building_name"] = fn
                row["forename"] = sn
                row["surname"] = tr
                row["trade"] = ""
                counts["2b_bldg_in_forename_rotated"] += 1
                continue

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total rows healed: {sum(counts.values())}")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
