#!/usr/bin/env python3
"""Merge recovered 1936 High Street scans (IMG_4702-4704) into data.csv."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"
FIX_DIR = ROOT / "scratch" / "1936_high_street_fix"


def non_empty(r):
    return any((r.get(k) or "").strip() for k in ("house_number", "building_name", "surname", "forename", "trade"))


def clean_high_row(r):
    hn = (r.get("house_number") or "").strip()
    bn = (r.get("building_name") or "").strip()
    sn = (r.get("surname") or "").strip()
    fn = (r.get("forename") or "").strip()
    tr = (r.get("trade") or "").strip()

    if bn.isupper() or "CHAMBERS" in bn:
        bn = bn.title().replace("—First", " — First").replace("—Second", " — Second").replace("—Third", " — Third")

    if hn == "79" and fn == "J. Kyrle" and sn == "Fletcher":
        fn = "J. Kyrle"
        sn = "Fletcher Ltd."
    elif hn == "81" and "John (Tools) Ltd." in fn and sn == "Hall":
        fn = ""
        sn = "John Hall (Tools) Ltd."
    elif hn == "10" and fn == "H. and Sons" and sn == "Thomas":
        fn = ""
        sn = "Thomas H. & Sons"
    elif hn.lower() == "11a" and fn == "Henry & Son" and sn == "Cordy":
        fn = ""
        sn = "Henry Cordy & Son"
    elif hn == "28" and fn == "Edward & Sons Ltd." and sn == "Hall":
        fn = ""
        sn = "Edward Hall & Sons Ltd."
    elif hn == "49" and bn == "Greyhound Hotel" and tr == "W. C. Carter":
        fn = "W. C."
        sn = "Carter"
        tr = "Hotel Proprietor"
    elif not sn and not fn and tr in ("Vacuums (Bustler) Ltd.", "Baltic Paper Mills Co."):
        sn = tr
        tr = ""

    return {
        "year": "1936",
        "street": "High Street",
        "house_number": hn,
        "building_name": bn,
        "surname": sn,
        "forename": fn,
        "trade": tr,
        "source_type": (r.get("source_type") or "vision_ocr").strip(),
    }


def main():
    new_rows = []
    for fname in ("IMG_4702.csv", "IMG_4703.csv", "IMG_4704.csv"):
        with open(FIX_DIR / fname, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if "high" in (r.get("street") or "").lower() and "highcroft" not in (r.get("street") or "").lower() and non_empty(r):
                    new_rows.append(clean_high_row(r))

    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        kept = [r for r in reader if not (r.get("year") == "1936" and r.get("street") == "High Street")]

    merged = kept + new_rows
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(merged)

    print(f"Replaced 1936 High Street with {len(new_rows)} clean Vision rows.")


if __name__ == "__main__":
    main()
