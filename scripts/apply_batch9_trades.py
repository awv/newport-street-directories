#!/usr/bin/env python3
"""
Batch 9 trade normalizations (`year <= 1936`):
* Iwrkr / Ironwkr / Ironwrkr / Ironwkrr -> Ironworker
* Hairdr* variants (Hairdresser'Ser, Hairdrsr, Hairdres, Hairdrssr, etc.) -> Hairdresser / Hairdressers
"""
import csv
import os
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "data.csv")


def normalize_trade(t: str) -> str:
    orig = t.strip()
    if not orig:
        return orig
    out = orig

    # Iwrkr / Ironwkr / Ironwrkr / Ironwkrr -> Ironworker
    out = re.sub(r"\b(?:iwrkr|ironw(?:r)?kr(?:r)?)(?:\.(?!\w)|\b)", "Ironworker", out, flags=re.I)

    # Hairdresser variants
    out = re.sub(r"\bhairdr(?:srs|ssrs|s)(?:\.(?!\w)|\b)", "Hairdressers", out, flags=re.I)
    out = re.sub(
        r"\bhairdr(?:esser'sser|esser'ser|ess'r|essse|sser|ssr|ser|sr|es|)(?:\.(?!\w)|\b)",
        "Hairdresser",
        out,
        flags=re.I,
    )
    return out


def main():
    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    changes = Counter()
    for r in rows:
        if int(r["year"]) > 1936:
            continue
        old = r["trade"].strip()
        if not old:
            continue
        new = normalize_trade(old)
        if new != old:
            changes[(old, new)] += 1
            r["trade"] = new

    with open(DATA_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total rows updated: {sum(changes.values())}")
    for (o, n), c in changes.most_common():
        print(f"  {c:4d} | {o} -> {n}")


if __name__ == "__main__":
    main()
