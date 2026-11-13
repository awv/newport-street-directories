#!/usr/bin/env python3
"""Heal high-confidence name/trade column shifts and truncations in data.csv."""

import csv
import re
import shutil
from collections import Counter

CSV_PATH = "data.csv"
BACKUP_PATH = "data.csv.bak_before_names_trades_heal"

EXPLICIT_TRADES = {
    "labourer", "ironworker", "engine driver", "boilermaker", "blacksmith",
    "greengrocer", "coal trimmer", "shipwright", "platelayer", "hairdresser",
    "shoemaker", "railway guard", "postman", "tobacconist", "plasterer",
    "furnaceman", "carpenter", "butcher", "baker", "grocer", "draper",
    "tailor", "painter", "plumber", "mason", "fitter", "machinist",
    "bootmaker", "dressmaker", "clerk", "inspector", "surveyor", "brewer",
    "builder",
}

INITIAL_RE = re.compile(r"^[A-Za-z]\.$")


def split_person_name(text: str) -> tuple[str, str]:
    """Split a full name string like 'Henry Sims', 'J. W. Green', or 'May T.' into (surname, forename)."""
    parts = text.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        tok = parts[0]
        if INITIAL_RE.match(tok):
            return "", tok
        return tok, ""
    # Pattern like "May T." or "Taylor J." (surname first, initial last)
    if INITIAL_RE.match(parts[-1]) and not INITIAL_RE.match(parts[0]):
        return parts[0], " ".join(parts[1:])
    # Pattern like "Henry Sims" or "J. W. Green" (forename(s) first, surname last)
    return parts[-1], " ".join(parts[:-1])


def main() -> None:
    shutil.copy2(CSV_PATH, BACKUP_PATH)
    print(f"Backed up {CSV_PATH} -> {BACKUP_PATH}")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    counts = Counter()

    for row in rows:
        yr = row["year"].strip()
        sn = row["surname"].strip()
        fn = row["forename"].strip()
        tr = row["trade"].strip()

        # Bucket A: 1971 single-letter middle initial shifted into trade
        if yr == "1971" and len(tr) == 1 and tr.isalpha() and fn:
            row["forename"] = f"{fn} {tr}."
            row["trade"] = ""
            counts["A_1971_middle_initial"] += 1
            continue

        # Bucket B: lowercase explicit trade in surname, name in forename, blank trade
        if sn and sn.islower() and sn in EXPLICIT_TRADES and not tr and fn:
            new_sn, new_fn = split_person_name(fn)
            row["surname"] = new_sn
            row["forename"] = new_fn
            row["trade"] = sn.title()
            counts["B_lowercase_trade_in_surname"] += 1
            continue

        # Bucket C: Ditto + [Trade] in forename
        if sn.lower() == "ditto" and fn.startswith("[") and fn.endswith("]") and not tr:
            row["forename"] = ""
            row["trade"] = fn[1:-1].strip()
            counts["C_ditto_bracketed_trade"] += 1
            continue

        # Bucket D: trade == Ltd / Ltd.
        if tr in ("Ltd", "Ltd."):
            if sn and sn.islower() and fn:
                row["surname"] = fn if fn.rstrip(".").endswith("Ltd") else f"{fn} Ltd."
                row["forename"] = ""
                row["trade"] = sn.title()
            elif sn:
                row["surname"] = sn if sn.rstrip(".").endswith("Ltd") else f"{sn} Ltd."
                row["trade"] = ""
            else:
                row["trade"] = ""
            counts["D_ltd_in_trade"] += 1
            continue

        # Bucket E: trade == Lab / Lab.
        if tr in ("Lab", "Lab."):
            row["trade"] = "Labourer"
            counts["E_lab_to_labourer"] += 1
            continue

        # Bucket F: eng/engine + Dvr
        if sn.lower() in ("eng", "engine", "engin") and tr.lower() in ("dvr", "drvr", "driver"):
            row["surname"] = ""
            row["trade"] = "Engine Driver"
            counts["F_eng_dvr"] += 1
            continue

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = sum(counts.values())
    print(f"Total rows healed: {total}")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
