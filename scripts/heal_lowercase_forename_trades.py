#!/usr/bin/env python3
"""
Heal rows (`year <= 1936`) where `forename` starts with a lowercase trade/facility
phrase (e.g., 1925 Lloyd Street: `bottled beer stores` / `Whitbread & Co.` / `Ltd.`),
moving the trade into `trade` and keeping/merging the business or resident name cleanly.
"""
import argparse
import csv
import os
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "data.csv")

SKIP_LOWER_FN = {
    "the misses", "de louis", "and law", "at cheltenham lt d", "for oaths",
    "to above firms", "of", "and",
}

SPLIT_TRADE_PREFIXES = {
    "coal", "insur", "fruit", "builders", "hardware", "mineral", "cabinet",
    "haulage", "motor", "hair", "chief", "harness", "ice", "lock", "shop",
    "oph", "music", "comm", "dental", "managing", "iron", "putty", "general",
    "hay", "colliery", "provision", "commissioners", "road", "boot", "corp",
}


def title_trade(s: str) -> str:
    s = s.strip(" ,;")
    words = s.split()
    out = []
    for i, w in enumerate(words):
        if i > 0 and w.lower() in {"and", "&", "of", "for", "the", "in"}:
            out.append(w.lower())
        else:
            out.append(w.capitalize())
    return " ".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Build known forenames for un-swapping "Artess Albert" -> "Albert Artess"
    known_forenames = set()
    for r in rows:
        if int(r["year"]) <= 1936:
            fn = r["forename"].strip()
            if fn and fn[0].isupper() and " " not in fn and fn.isalpha() and len(fn) >= 3:
                known_forenames.add(fn)

    stats = Counter()
    samples = []

    for r in rows:
        if int(r["year"]) > 1936:
            continue
        fn = r["forename"].strip()
        sur = r["surname"].strip()
        tr = r["trade"].strip()

        if not fn or not fn[0].islower() or not sur:
            continue
        if tr not in ("", "Ltd.", "Ltd", "Co.", "Co", "& Co."):
            continue
        if fn.lower() in SKIP_LOWER_FN:
            continue

        # Handle "Grouville- | void" -> building_name + Void
        if fn.lower() == "void" and sur.endswith("-"):
            r["building_name"] = sur.rstrip("-").strip()
            r["surname"] = ""
            r["forename"] = ""
            r["trade"] = "Void"
            stats["void_in_fn"] += 1
            continue

        # Handle "the Misses" -> move to forename titlecase
        if fn.lower() == "the misses":
            r["forename"] = "The Misses"
            stats["misses_fixed"] += 1
            continue

        # Handle 1936 split two-word trades like surname="coal" + forename="merchants"
        if r["year"] == "1936" and sur.lower().rstrip(".") in SPLIT_TRADE_PREFIXES:
            r["trade"] = title_trade(f"{sur} {fn}")
            r["surname"] = ""
            r["forename"] = ""
            stats["split_trade_combined"] += 1
            if len(samples) < 30:
                samples.append((r["year"], r["street"], r["house_number"], f"{sur} + {fn} -> trade: {r['trade']}"))
            continue

        # Standard case: forename is trade, surname is business or person
        # Merge trailing Ltd./Co. from trade onto surname
        if tr in ("Ltd.", "Ltd", "Co.", "Co", "& Co."):
            sur_clean = sur.rstrip(" ,")
            if not sur_clean.lower().endswith(("ltd", "ltd.")):
                sur = f"{sur_clean} {tr}".strip()

        # Check if surname is actually "Surname Forename" (e.g. "Cleverly Frederick")
        sur_parts = sur.split()
        new_fn = ""
        new_sur = sur.rstrip(" ,")
        if (
            len(sur_parts) == 2
            and sur_parts[0][0].isupper()
            and sur_parts[1] in known_forenames
            and not re.search(r"(&|Co|Ltd|Bros|Sons)", sur, re.I)
        ):
            new_sur = sur_parts[0]
            new_fn = sur_parts[1]

        r["surname"] = new_sur
        r["forename"] = new_fn
        r["trade"] = title_trade(fn)
        stats["trade_moved_from_fn"] += 1
        if len(samples) < 35 or (r["year"] == "1925" and r["street"] == "Lloyd Street"):
            samples.append((r["year"], r["street"], r["house_number"], f"{new_fn} {new_sur} | {r['trade']}"))

    print("Stats:", dict(stats))
    for s in samples:
        print(" ", s)

    if not args.dry_run:
        with open(DATA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print("Saved updated data.csv!")


if __name__ == "__main__":
    main()
