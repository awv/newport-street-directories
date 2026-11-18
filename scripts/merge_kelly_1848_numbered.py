#!/usr/bin/env python3
"""Merge numbered Kelly's 1848 entries matching existing streets into data.csv."""

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KELLY_JSON = ROOT / "data" / "early_directories" / "kelly_1848.json"
DATA_CSV = ROOT / "data.csv"
VOL_CSV = ROOT / "volume_csvs" / "1848_cleaned.csv"

NUM_RE = re.compile(r"^No\.\s*(\d+)([a-zA-Z]?)$")


def split_name(raw_name: str) -> tuple[str, str]:
    name = (raw_name or "").strip()
    if "," in name:
        surname, forename = name.split(",", 1)
        return surname.strip(), forename.strip()
    return name, ""


def main() -> None:
    with open(KELLY_JSON, encoding="utf-8") as f:
        kelly = json.load(f)

    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        existing_rows = [r for r in reader if r.get("year") != "1848"]

    # Map lowercase street name -> canonical street name from data.csv
    canonical_streets = {}
    for r in existing_rows:
        st = (r.get("street") or "").strip()
        if st and st.lower() not in canonical_streets:
            canonical_streets[st.lower()] = st

    rows_1848 = []
    seen = set()
    for section in kelly.get("sections", []):
        for entry in section.get("entries", []):
            st_raw = (entry.get("street") or "").strip()
            notes = (entry.get("notes") or "").strip()
            m = NUM_RE.match(notes)
            if not st_raw or not m:
                continue
            canonical_st = canonical_streets.get(st_raw.lower())
            if not canonical_st:
                continue

            house_num = f"{m.group(1)}{m.group(2)}"
            surname, forename = split_name(entry.get("name", ""))
            trade = (entry.get("trade") or "").strip()

            dedup_key = (canonical_st, house_num, surname, forename, trade)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            rows_1848.append({
                "year": "1848",
                "street": canonical_st,
                "house_number": house_num,
                "building_name": "",
                "surname": surname,
                "forename": forename,
                "trade": trade,
                "source_type": "newportpast_html",
                "_sort_num": int(m.group(1)),
                "_sort_suf": m.group(2).lower(),
            })

    rows_1848.sort(key=lambda r: (r["street"].lower(), r["_sort_num"], r["_sort_suf"], r["surname"].lower(), r["forename"].lower()))
    for r in rows_1848:
        del r["_sort_num"]
        del r["_sort_suf"]

    VOL_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(VOL_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_1848)

    merged = rows_1848 + existing_rows
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(merged)

    streets_count = len({r["street"] for r in rows_1848})
    print(f"Wrote {len(rows_1848)} numbered 1848 rows across {streets_count} streets -> {VOL_CSV.name}")
    print(f"Merged into {DATA_CSV.name}: {len(merged):,} total rows.")


if __name__ == "__main__":
    main()
