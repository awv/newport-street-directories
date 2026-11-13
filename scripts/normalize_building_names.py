#!/usr/bin/env python3
"""
Normalize abbreviations and casing in `building_name` across `data.csv` (`year <= 1936`):
- Expand trailing `ho` / `ho.` / `h` / `h.` -> `House` (excluding `Westward Ho`)
- Expand trailing `vil` / `vil.` / `v` / `v.` -> `Villa`
- Expand trailing `cot` / `cot.` / `cott` / `cott.` -> `Cottage`
- Expand trailing `bldgs` / `bldgs.` -> `Buildings`
- Apply smart Title Case so `Grove house` -> `Grove House`, `Piermont house` -> `Piermont House`, etc.
"""
import argparse
import csv
import os
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "data.csv")

LOWER_WORDS = {"of", "the", "and", "&", "in", "at", "on", "for", "to", "by", "y", "yr"}


def normalize_building_name(b: str) -> str:
    orig = b.strip()
    if not orig:
        return orig

    # Preserve "Westward Ho" / "Westward Ho!"
    if re.fullmatch(r"westward\s+ho!?", orig, re.I):
        return "Westward Ho"

    out = orig.rstrip(".")
    # Expand trailing abbreviations (case-insensitive)
    out = re.sub(r"\b(?:ho|h)$", "House", out, flags=re.I)
    out = re.sub(r"\b(?:vil|v)$", "Villa", out, flags=re.I)
    out = re.sub(r"\b(?:cott?)$", "Cottage", out, flags=re.I)
    out = re.sub(r"\bbldgs$", "Buildings", out, flags=re.I)

    # Smart Title Case
    words = out.split(" ")
    res = []
    for i, w in enumerate(words):
        if not w:
            res.append(w)
            continue
        m = re.match(r"^([^A-Za-z0-9]*)(.*?)([^A-Za-z0-9]*)$", w)
        if not m:
            res.append(w)
            continue
        lead, core, trail = m.groups()
        if not core:
            res.append(w)
            continue
        if re.fullmatch(r"(?:[A-Z]\.){1,}[A-Z]?", core.upper()):
            res.append(lead + core.upper() + trail)
            continue
        cl = core.lower()
        if i > 0 and cl in LOWER_WORDS:
            res.append(lead + cl + trail)
        elif "-" in cl:
            parts = cl.split("-")
            res.append(lead + "-".join(p if (j > 0 and p in LOWER_WORDS) else p.capitalize() for j, p in enumerate(parts)) + trail)
        elif "'" in cl:
            parts = cl.split("'")
            if len(parts) == 2 and parts[1] in {"s", "t", "d", "ll", "re", "ve", "ster"}:
                res.append(lead + parts[0].capitalize() + "'" + parts[1] + trail)
            else:
                res.append(lead + "'".join(p.capitalize() for p in parts) + trail)
        else:
            res.append(lead + cl.capitalize() + trail)
    return " ".join(res)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    changes = Counter()
    for r in rows:
        old = r["building_name"].strip()
        if not old:
            continue
        new = normalize_building_name(old)
        if new != old:
            changes[(old, new)] += 1
            r["building_name"] = new

    print(f"Total rows updated: {sum(changes.values())} ({len(changes)} unique)")
    for (o, n), c in changes.most_common(30):
        print(f"  {c:4d} | {o} -> {n}")

    if not args.dry_run:
        with open(DATA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print("Saved updated data.csv!")


if __name__ == "__main__":
    main()
