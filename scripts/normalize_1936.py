#!/usr/bin/env python3
"""
Normalize all 184 Vision-extracted 1936 page CSVs in scratch/1936_vision_rebuild/:
1. Resolve 3-letter running headers (e.g. HEW, COM, CHE, CON) using the previous page's trailing street.
2. Strip '(continued)', '[continued]', '-cont.', trailing map grid codes ('E. 2', 'C 5'), etc.
3. Fix IMG_4656.csv (Commercial Street mislabeled COMMERCIAL ROAD) and High Street row splits.
4. Rewrite volume_csvs/1936_cleaned.csv and replace 1936 rows in data.csv.
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalize_1914_1917 as n14
import merge_1936_high_street as mhs

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"
PAGE_DIR = ROOT / "scratch" / "1936_vision_rebuild"


def clean_1936_street(raw, canon_by_lower):
    s = (raw or "").strip()
    if not s:
        return None
    s = re.sub(r"\s*\[(?:—–-)?\s*continued\]\.?$", "", s, flags=re.I).strip()
    s = re.sub(r"\s*[-—–]\s*cont\.?$", "", s, flags=re.I).strip()
    s = re.sub(r"[.,]?\s+[A-G]\.\s*[1-9]\.?$", "", s).strip()
    if s.lower() == "edward vii. crescent":
        return "Edward VII Crescent"
    if s.lower() == "bassalleg road":
        return "Bassaleg Road"
    return n14.clean_street_name(s, canon_by_lower)


def non_empty(r):
    return any((r.get(k) or "").strip() for k in ("house_number", "building_name", "surname", "forename", "trade"))


def main():
    canon_by_lower = n14.load_canonical_map()
    canon_set = set(canon_by_lower.values())
    page_csvs = sorted(PAGE_DIR.glob("*.csv"))

    rows_out = []
    last_street = ""
    resolved_headers = 0
    matched_canon = 0

    for p in page_csvs:
        with open(p, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if (r.get("street") or "").strip().lower() == "street" and (r.get("house_number") or "").strip().lower() == "house_number":
                    continue
                if not non_empty(r):
                    continue

                if p.name == "IMG_4656.csv":
                    st = "Commercial Street"
                else:
                    st = clean_1936_street(r.get("street", ""), canon_by_lower)

                if st is None:
                    if last_street:
                        st = last_street
                        resolved_headers += 1
                    else:
                        continue
                else:
                    last_street = st

                if st in canon_set:
                    matched_canon += 1

                if st == "High Street":
                    rows_out.append(mhs.clean_high_row(r))
                else:
                    rows_out.append({
                        "year": "1936",
                        "street": st,
                        "house_number": (r.get("house_number") or "").strip(),
                        "building_name": (r.get("building_name") or "").strip(),
                        "surname": (r.get("surname") or "").strip(),
                        "forename": (r.get("forename") or "").strip(),
                        "trade": (r.get("trade") or "").strip(),
                        "source_type": (r.get("source_type") or "vision_ocr").strip(),
                    })

    vol_csv = ROOT / "volume_csvs" / "1936_cleaned.csv"
    fieldnames = ["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"]
    with open(vol_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)

    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        data_fn = reader.fieldnames
        kept = [r for r in reader if r.get("year") != "1936"]

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=data_fn)
        w.writeheader()
        w.writerows(kept + rows_out)

    streets_cnt = len(set(r["street"] for r in rows_out))
    print(
        f"[1936] {len(rows_out)} rows across {streets_cnt} streets "
        f"(resolved {resolved_headers} running headers; {matched_canon}/{len(rows_out)} "
        f"({matched_canon/len(rows_out)*100:.1f}%) in master_streets.json)"
    )


if __name__ == "__main__":
    main()
