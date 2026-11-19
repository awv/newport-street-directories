#!/usr/bin/env python3
"""Expand abbreviated/OCR trade strings in data.csv and volume_csvs/."""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"
VOL_DIR = ROOT / "volume_csvs"

REPLACEMENTS = [
    (re.compile(r"\bi['’]worker\b", re.I), "Ironworker"),
    (re.compile(r"\bi,\s*worker\b", re.I), "Ironworker"),
    (re.compile(r"\bcochbldr\b", re.I), "Coachbuilder"),
    (re.compile(r"\bcachbldr\b", re.I), "Coachbuilder"),
    (re.compile(r"\bcarp['’]tr\b", re.I), "Carpenter"),
    (re.compile(r"\bcoal\s+f['’]man\b", re.I), "Coal Foreman"),
    (re.compile(r"\bmac['’]st\b", re.I), "Machinist"),
    (re.compile(r"\btrav['’]lr\b", re.I), "Traveller"),
    (re.compile(r"\brlyman\b", re.I), "Railwayman"),
]


def fix_trade(trade: str) -> str:
    t = trade
    for pat, rep in REPLACEMENTS:
        t = pat.sub(rep, t)
    return t


def process_csv(path: Path) -> int:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    changed = 0
    for r in rows:
        old = r.get("trade") or ""
        new = fix_trade(old)
        if new != old:
            r["trade"] = new
            changed += 1

    if changed:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
    return changed


def main() -> None:
    total = process_csv(DATA_CSV)
    print(f"Updated {total} rows in {DATA_CSV.name}.")

    for vol_csv in sorted(VOL_DIR.glob("*_cleaned.csv")):
        vc = process_csv(vol_csv)
        if vc:
            print(f"Updated {vc} rows in {vol_csv.name}.")


if __name__ == "__main__":
    main()
