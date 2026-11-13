#!/usr/bin/env python3
"""Heal high-confidence 'Names in Trades' column shifts in data.csv."""

import csv
import re
import shutil
from collections import Counter

CSV_PATH = "data.csv"
BACKUP_PATH = "data.csv.bak_before_names_in_trades_heal"

WELSH_SURNAMES = {
    "williams", "jones", "evans", "davies", "thomas", "lewis", "james",
    "llewellyn", "edwards", "roberts", "hughes", "morgan", "griffiths",
    "jenkins", "richards", "powell", "price", "phillips", "owen", "morris",
}

PURE_FORENAMES = {
    "john", "william", "thomas", "james", "george", "henry", "charles",
    "edward", "joseph", "robert", "arthur", "alfred", "albert", "frederick",
    "walter", "samuel", "david", "richard", "frank", "herbert", "harold",
    "ernest", "harry", "edwin", "benjamin", "mary", "elizabeth", "sarah",
    "jane", "ann", "anne", "margaret", "martha", "emma", "alice", "ellen",
    "florence", "rose", "clara", "emily", "edith", "eliza", "louisa",
    "catherine", "hannah", "susan", "harriet", "charlotte", "absolam",
    "edgar", "hy", "geo", "thos", "jas", "wm", "chas",
}

BLDG_WORDS_RE = re.compile(
    r"\b(villa|villas|vils|house|ho|cot|cottage|cottages|arms|inn|tavern|hotel|ferns|mount|park|place|crescent|terrace)\b|\[|^the\s",
    re.I,
)


def load_common_forenames() -> set[str]:
    with open("scripts/build_stats_data.py", encoding="utf-8") as f:
        code = f.read()
    m = re.search(r"COMMON_FORENAMES\s*=\s*\{(.*?)\}", code, re.S)
    pairs = re.findall(r'"([^"]+)"|\'([^\']+)\'', m.group(1))
    return {a or b for a, b in pairs} - {"widow"}


def main() -> None:
    common_names = load_common_forenames()
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

        if not tr or tr_l not in common_names:
            continue

        # 1. Title in forename (Mrs., Miss, Mr., Rev., Dr.) + forename in trade
        if fn and fn.rstrip(".").lower() in ("mrs", "miss", "mr", "rev", "dr"):
            row["forename"] = f"{fn} {tr}"
            row["trade"] = ""
            counts["1_title_forename_plus_trade"] += 1
            continue

        # 2. Empty surname + non-empty forename + name in trade -> trade is surname
        if not sn and fn and not BLDG_WORDS_RE.search(fn):
            row["surname"] = tr
            row["trade"] = ""
            counts["2_empty_surname_trade_is_surname"] += 1
            continue

        # 3. Has building_name, surname is a pure forename, blank forename, trade is surname
        if bldg and sn and not fn and sn.rstrip(".").lower() in PURE_FORENAMES and tr_l in WELSH_SURNAMES:
            row["forename"] = sn
            row["surname"] = tr
            row["trade"] = ""
            counts["3_bldg_forename_in_surname"] += 1
            continue

        # 4. No building_name, clean surname only (blank forename), name in trade
        if not bldg and sn and not fn and "&" not in sn and "co." not in sn.lower() and not sn.islower() and not BLDG_WORDS_RE.search(sn):
            if sn.rstrip(".").lower() in PURE_FORENAMES and tr_l in WELSH_SURNAMES:
                row["forename"] = sn
                row["surname"] = tr
                row["trade"] = ""
                counts["4a_sn_only_swapped_forename_surname"] += 1
            else:
                row["forename"] = tr
                row["trade"] = ""
                counts["4b_sn_only_trade_is_forename"] += 1
            continue

        # 5. No building_name, clean surname + clean forename/initial, pure non-surname forename in trade -> middle name
        if (
            not bldg
            and sn
            and fn
            and "&" not in sn
            and not sn.islower()
            and not BLDG_WORDS_RE.search(sn)
            and not BLDG_WORDS_RE.search(fn)
            and tr_l in PURE_FORENAMES
            and tr_l not in WELSH_SURNAMES
        ):
            row["forename"] = f"{fn} {tr}"
            row["trade"] = ""
            counts["5_middle_forename_in_trade"] += 1
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
