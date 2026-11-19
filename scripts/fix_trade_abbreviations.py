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
    (re.compile(r"railwy['’]?yman", re.I), "Railwayman"),
    (re.compile(r"\bbus\s+cond\.?(?=\b|\s|$)", re.I), "Bus Conductor"),
    (re.compile(r"\bplastr['’]?r?\b", re.I), "Plasterer"),
    (re.compile(r"\bice\s+crm\s+vr\.?(?=\b|\s|$)", re.I), "Ice Cream Vendor"),
    (re.compile(r"\bacet\.?\s+br(?:nr)?\.?(?=\b|\s|$)", re.I), "Acetylene Burner"),
    (re.compile(r"\bglass\s+worker\.", re.I), "Glass Worker"),
    (re.compile(r"\bblr\.?\s+cleaner\b", re.I), "Boiler Cleaner"),
    (re.compile(r"\btrss\.?(?=\b|\s|$)", re.I), "Tailoress"),
    (re.compile(r"\bcom\.?\s+agent\b", re.I), "Commercial Agent"),
    (re.compile(r"\bbrklr\.?(?=\b|\s|$)", re.I), "Bricklayer"),
    (re.compile(r"\bgas\s+wks\.?(?=\b|\s|$)", re.I), "Gas Works"),
    (re.compile(r"\btram\s+dr\.?(?=\b|\s|$)", re.I), "Tram Driver"),
    (re.compile(r"\btram\s+con\.?(?=\b|\s|$)", re.I), "Tram Conductor"),
    (re.compile(r"\bballast\s+grd\.?(?=\b|\s|$)", re.I), "Ballast Guard"),
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
        row_changed = False
        sur = (r.get("surname") or "").strip()
        fore = (r.get("forename") or "").strip()
        tr = (r.get("trade") or "").strip()

        # Fix "senr." / "junr." in surname with "<RealSurname>, <Trade>" (or "<RealSurname>") in trade
        if sur.lower().rstrip(".") in {"senr", "junr", "jr", "sr"} and tr:
            m = re.match(r"^([A-Z][a-z'\-]+)(?:,\s*(.*))?$", tr)
            if m:
                r["surname"] = m.group(1)
                r["forename"] = f"{fore} {sur}".strip()
                r["trade"] = (m.group(2) or "").strip()
                row_changed = True
        elif tr.lower().startswith("senr. ") or tr.lower().startswith("junr. "):
            parts = tr.split(" ", 1)
            r["forename"] = f"{fore} {parts[0]}".strip()
            r["trade"] = parts[1].strip()
            row_changed = True

        old = r.get("trade") or ""
        new = fix_trade(old)
        if new != old:
            r["trade"] = new
            row_changed = True

        if row_changed:
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
