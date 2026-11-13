#!/usr/bin/env python3
"""
Heal 1936 continuation rows where a trailing lowercase trade/department word
(e.g. 'bakery', 'outfitters', 'seaman', 'printers', 'caretkr') landed in
`surname` with empty `forename` and `trade` right after a same-address row
(such as 1936 Livingstone Place No. 46: Mrs Mary Willis / Withers Bros / bakery).
"""
import argparse
import csv
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "data.csv")

TRADE_EXPAND = {
    "caretkr": "Caretaker",
    "libn": "Librarian",
    "transwkr": "Transport Worker",
    "bilrmaker": "Boilermaker",
}


def expand_word(w: str) -> str:
    wl = w.lower()
    if wl in TRADE_EXPAND:
        return TRADE_EXPAND[wl]
    return w.capitalize()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    out_rows = []
    merged_count = 0
    split_biz_count = 0

    for r in rows:
        is_orphan_lc = (
            int(r["year"]) == 1936
            and out_rows
            and r["year"] == out_rows[-1]["year"]
            and r["street"] == out_rows[-1]["street"]
            and r["house_number"].strip()
            and r["house_number"] == out_rows[-1]["house_number"]
            and not r["forename"].strip()
            and not r["trade"].strip()
            and r["surname"].strip()
            and r["surname"].strip() == r["surname"].strip().lower()
            and r["surname"].strip().isalpha()
        )

        if not is_orphan_lc:
            out_rows.append(r)
            continue

        prev = out_rows[-1]
        tr_word = expand_word(r["surname"].strip())
        prev_tr = prev["trade"].strip()

        # Special case: person in prev name, business name in prev trade (e.g. Mrs Mary Willis | Withers Bros + bakery)
        if prev["forename"].strip() and prev["surname"].strip() and re.search(r"\b(?:Bros|Sons|Co|Ltd)\b", prev_tr):
            biz_name = prev_tr
            prev["trade"] = ""
            out_rows.append({
                "year": r["year"],
                "street": r["street"],
                "house_number": r["house_number"],
                "building_name": r["building_name"],
                "surname": biz_name,
                "forename": "",
                "trade": tr_word,
                "source_type": r["source_type"],
            })
            split_biz_count += 1
            print(f"  [BIZ SPLIT] {r['year']} {r['street']} {r['house_number']}: {prev['forename']} {prev['surname']} + {biz_name} ({tr_word})")
        else:
            prev["trade"] = f"{prev_tr}, {tr_word}" if prev_tr else tr_word
            merged_count += 1
            if merged_count <= 25 or "livingstone" in r["street"].lower():
                print(f"  [MERGED] {r['year']} {r['street']} {r['house_number']}: {prev['forename']} {prev['surname']} -> {prev['trade']}")

    print(f"\nMerged: {merged_count}, Business-split: {split_biz_count}, Rows: {len(rows)} -> {len(out_rows)}")
    if not args.dry_run:
        with open(DATA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(out_rows)
        print("Saved updated data.csv!")


if __name__ == "__main__":
    main()
