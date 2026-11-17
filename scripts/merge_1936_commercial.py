#!/usr/bin/env python3
"""Merge recovered 1936 Commercial Road & Commercial Street scans (IMG_4651-4657) into data.csv."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"
FIX_DIR = ROOT / "scratch" / "1936_commercial_fix2"


def load_csv(name):
    with open(FIX_DIR / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def non_empty(r):
    return any((r.get(k) or "").strip() for k in ("house_number", "building_name", "surname", "forename", "trade"))


def clean_row(r, street_name):
    hn = (r.get("house_number") or "").strip()
    bn = (r.get("building_name") or "").strip()
    sn = (r.get("surname") or "").strip()
    fn = (r.get("forename") or "").strip()
    tr = (r.get("trade") or "").strip()

    if hn == "0200-1-2":
        hn = "200-1-2"
    if bn == "House Agents" and not sn and tr:
        bn = ""
        tr = f"House Agents, {tr}"
    if sn in ("Drapery And Outfitting", "Grocery And Provision Merchants") and not tr:
        tr = sn
        sn = ""
    if bn == "Tabernacle Schoolrm":
        bn = "Tabernacle Schoolroom"

    return {
        "year": "1936",
        "street": street_name,
        "house_number": hn,
        "building_name": bn,
        "surname": sn,
        "forename": fn,
        "trade": tr,
        "source_type": (r.get("source_type") or "vision_ocr").strip(),
    }


def main():
    road_rows = []
    for r in load_csv("IMG_4651.csv"):
        if "commercial road" in (r.get("street") or "").lower() and non_empty(r):
            road_rows.append(clean_row(r, "Commercial Road"))
    for r in load_csv("IMG_4652.csv"):
        if non_empty(r):
            road_rows.append(clean_row(r, "Commercial Road"))
    for r in load_csv("IMG_4653.csv"):
        if "commercial road" in (r.get("street") or "").lower() and non_empty(r):
            road_rows.append(clean_row(r, "Commercial Road"))

    street_rows = []
    for r in load_csv("IMG_4653.csv"):
        if "commercial st" in (r.get("street") or "").lower() and non_empty(r):
            street_rows.append(clean_row(r, "Commercial Street"))
    for fname in ("IMG_4654.csv", "IMG_4655.csv", "IMG_4656.csv"):
        for r in load_csv(fname):
            if non_empty(r):
                street_rows.append(clean_row(r, "Commercial Street"))
    for r in load_csv("IMG_4657.csv"):
        if "commercial street" in (r.get("street") or "").lower() and non_empty(r):
            street_rows.append(clean_row(r, "Commercial Street"))

    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        all_rows = list(reader)

    # Keep tail (>=176) of existing 1936 Commercial Street rows, cleaned
    tail_rows = []
    after_175 = False
    for r in all_rows:
        if r.get("year") == "1936" and r.get("street") == "Commercial Street":
            hn = (r.get("house_number") or "").strip()
            if hn in ("176", "177", "178", "179", "180", "181", "182", "183", "184", "185", "194"):
                after_175 = True
            if after_175:
                tail_rows.append(clean_row(r, "Commercial Street"))

    kept = [
        r for r in all_rows
        if not (r.get("year") == "1936" and r.get("street") in ("Commercial Road", "Commercial Street"))
    ]

    merged = kept + road_rows + street_rows + tail_rows
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(merged)

    print(f"Merged 1936 Commercial Road: {len(road_rows)} rows; Commercial Street: {len(street_rows)} + {len(tail_rows)} tail = {len(street_rows) + len(tail_rows)} rows.")


if __name__ == "__main__":
    main()
