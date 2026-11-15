#!/usr/bin/env python3
"""Normalize Dk/Dock, *mkr/*Maker, and *Hd/*Hand trade abbreviations across data.csv."""
import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"

EXACT_MAP = {
    "dk labr": "Dock Labourer",
    "dk. labr": "Dock Labourer",
    "dk lbr": "Dock Labourer",
    "dk. lbr": "Dock Labourer",
    "dk. lbr.": "Dock Labourer",
    "dk.labourer": "Dock Labourer",
    "dk wrkr": "Dock Worker",
    "dk wkr": "Dock Worker",
    "dk. employe": "Dock Employee",
    "dk boatmn": "Dock Boatman",
    "dk wghmn": "Dock Weighman",
    "insp.alex.dk": "Inspector Alexandra Dock",
    "alex. dk": "Alexandra Dock",
    "blrmkr": "Boilermaker",
    "boilrmkr": "Boilermaker",
    "btmkr": "Bootmaker",
    "hd gardener": "Head Gardener",
    "hd. gardener": "Head Gardener",
    "hd. gardner": "Head Gardener",
    "facty hd": "Factory Hand",
    "fac. hd": "Factory Hand",
    "fac. hd.": "Factory Hand",
    "fact'y hd": "Factory Hand",
    "fact hd": "Factory Hand",
    "factry hd": "Factory Hand",
    "brew'ry hd": "Brewery Hand",
    "brewy hd": "Brewery Hand",
    "rlwy hd": "Railway Hand",
    "rlwy. hd.": "Railway Hand",
    "railwy hd": "Railway Hand",
    "rlway hd": "Railway Hand",
    "rlway hd.": "Railway Hand",
    "bo'tle hd": "Bottle Hand",
}


def normalize_trade(raw: str) -> str:
    t = (raw or "").strip()
    if not t:
        return t
    low = t.lower()
    if low in EXACT_MAP:
        return EXACT_MAP[low]

    out = t
    # 1. Dk. / Dk -> Dock
    out = re.sub(r"\bDk\.?\s*", "Dock ", out, flags=re.I)
    out = re.sub(r"\bDock\s+Labr\.?\b", "Dock Labourer", out, flags=re.I)
    out = re.sub(r"\bDock\s+Lbr\.?\b", "Dock Labourer", out, flags=re.I)
    out = re.sub(r"\bDock\s+W(?:r)?kr\.?\b", "Dock Worker", out, flags=re.I)

    # 2. mkr / Mkr -> maker / Maker
    out = re.sub(r"([A-Za-z]+)mkr\.?\b", r"\1maker", out, flags=re.I)
    out = re.sub(r"\bmkr\.?\b", "Maker", out, flags=re.I)

    # 3. Trailing Hd. / Hd -> Hand (Head Gardener already handled by EXACT_MAP)
    out = re.sub(r"\bHd\.?$", "Hand", out, flags=re.I)
    out = re.sub(r"\bHd\.?\s+", "Hand ", out, flags=re.I)

    out = re.sub(r"\s+", " ", out).strip()
    return out


def main():
    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    changed = Counter()
    for r in rows:
        old = (r.get("trade") or "").strip()
        new = normalize_trade(old)
        if new != old:
            r["trade"] = new
            changed[(old, new)] += 1

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Normalized {sum(changed.values())} trade rows across {len(changed)} distinct patterns.")
    for (o, n), cnt in changed.most_common(25):
        print(f"  {cnt:4d}: {o!r} -> {n!r}")


if __name__ == "__main__":
    main()
