#!/usr/bin/env python3
"""
Normalize 1914 & 1917 Vision-extracted page CSVs:
1. Resolve 3-letter running headers (e.g. LIM, BAL, CHE) and 'NEWPORT STREET DIRECTORY'
   using the previous page's trailing street in sorted IMG_XXXX.csv order.
2. Strip '(continued)', '—continued', trailing map grid codes ('E 5', 'C 3'), and punctuation.
3. Map street names to canonical names in master_streets.json (or clean Title Case).
4. Rewrite volume_csvs/{year}_cleaned.csv and replace {year} rows in data.csv.
"""
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"
MASTER_STREETS_JSON = ROOT / "master_streets.json"

EXPLICIT_STREET_MAP = {
    "fair oak avenue": "Fairoak Avenue",
    "mendalgiff road": "Mendalgief Road",
    "market (provision)": "Provision Market",
    "arcades. market arcade": "Market Arcade",
    "edward vii. avenue": "Edward VII Avenue",
    "edward vii avenue": "Edward VII Avenue",
    "watchhouse par": "Watchhouse Parade",
    "watchhouse par.": "Watchhouse Parade",
    "alteryn": "Allt-yr-yn",
    "alteryn road": "Allt-yr-yn Road",
    "glo'ster place": "Gloster Place",
    "glo'ster street": "Gloster Street",
    "dudly street": "Dudley Street",
    "merriott's place": "Merriot's Place",
    "wharves (the) &c": "Wharves (The)",
    "wharves (the) &c.": "Wharves (The)",
    "wharves c": "Wharves (The)",
    "wharves &c": "Wharves (The)",
    "commercial-street": "Commercial Street",
    "shaftesbury st": "Shaftesbury Street",
    "southmarket st": "South Market Street",
    "st. mark's cres": "St. Mark's Crescent",
    "st. mark's cres.": "St. Mark's Crescent",
    "market bearing provision": "Provision Market",
    "bryngas crescent": "Brynglas Crescent",
    "oswalal road": "Oswald Road",
    "clytha park road clytha park": "Clytha Park Road",
    "clytha park road, clytha park": "Clytha Park Road",
}

RUNNING_HEADER_RE = re.compile(
    r"^(?:[A-Z]{2,4}\.?|\d+|NEWPORT STREET DIRECTORY.*|NEWPORT STREET LIST.*)$"
)


def load_canonical_map():
    with open(MASTER_STREETS_JSON, encoding="utf-8") as f:
        ms = json.load(f).get("streets", {})
    canon_by_lower = {}
    for info in ms.values():
        cn = info["canonical_name"]
        canon_by_lower[cn.lower()] = cn
        for al in info.get("aliases", []):
            canon_by_lower[al.lower()] = cn
    return canon_by_lower


def smart_title(s):
    words = s.split()
    out = []
    small = {"of", "the", "and", "in", "on", "at", "to", "for", "by"}
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in ("vii", "vi", "iv", "iii", "ii"):
            out.append(w.upper())
        elif i > 0 and lw in small:
            out.append(lw)
        elif "'" in w:
            parts = w.split("'")
            out.append("'".join(p.capitalize() if idx == 0 else p.lower() for idx, p in enumerate(parts)))
        elif "-" in w:
            out.append("-".join(p.capitalize() for p in w.split("-")))
        else:
            out.append(w.capitalize())
    return " ".join(out)


def clean_street_name(raw, canon_by_lower):
    s = (raw or "").strip()
    if not s or RUNNING_HEADER_RE.match(s):
        return None
    # Strip trailing (continued) / —continued / continued
    s = re.sub(r"\s*\(?[—–-]?\s*continued\)?\.?$", "", s, flags=re.I).strip()
    # Strip trailing map grid codes like '. E 5', ' C 6', ', D 3'
    s = re.sub(r"[.,]?\s+[A-G]\s*[1-9]\.?$", "", s).strip()
    s = s.rstrip(".,;:").strip()
    s = re.sub(r"\s+", " ", s)
    if not s or RUNNING_HEADER_RE.match(s):
        return None

    low = s.lower()
    if low in EXPLICIT_STREET_MAP:
        return EXPLICIT_STREET_MAP[low]
    if low in canon_by_lower:
        return canon_by_lower[low]

    low_sp = low.replace("-", " ")
    if low_sp in EXPLICIT_STREET_MAP:
        return EXPLICIT_STREET_MAP[low_sp]
    if low_sp in canon_by_lower:
        return canon_by_lower[low_sp]

    exp = re.sub(r"\bst\.?$", "street", low_sp)
    exp = re.sub(r"\brd\.?$", "road", exp)
    exp = re.sub(r"\bave\.?$", "avenue", exp)
    exp = re.sub(r"\bpl\.?$", "place", exp)
    exp = re.sub(r"\bter\.?$", "terrace", exp)
    exp = re.sub(r"\bcres\.?$", "crescent", exp)
    exp = re.sub(r"\bsq\.?$", "square", exp)
    exp = re.sub(r"\bln\.?$", "lane", exp)
    exp = re.sub(r"\bpar\.?$", "parade", exp)
    if exp in canon_by_lower:
        return canon_by_lower[exp]

    return smart_title(s)


def process_year(year, canon_by_lower):
    page_dir = ROOT / "scratch" / f"{year}_vision_rebuild"
    page_csvs = sorted(page_dir.glob("*.csv"))
    rows_out = []
    last_street = ""
    resolved_headers = 0
    matched_canon = 0

    canon_set = set(canon_by_lower.values())

    for p in page_csvs:
        with open(p, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if (r.get("street") or "").strip().lower() == "street" and (r.get("house_number") or "").strip().lower() == "house_number":
                    continue
                st = clean_street_name(r.get("street", ""), canon_by_lower)
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

                rows_out.append({
                    "year": str(year),
                    "street": st,
                    "house_number": (r.get("house_number") or "").strip(),
                    "building_name": (r.get("building_name") or "").strip(),
                    "surname": (r.get("surname") or "").strip(),
                    "forename": (r.get("forename") or "").strip(),
                    "trade": (r.get("trade") or "").strip(),
                    "source_type": (r.get("source_type") or "vision_ocr").strip(),
                })

    vol_csv = ROOT / "volume_csvs" / f"{year}_cleaned.csv"
    fieldnames = ["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"]
    with open(vol_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)

    print(
        f"[{year}] {len(rows_out)} rows across {len(set(r['street'] for r in rows_out))} streets "
        f"(resolved {resolved_headers} running headers; {matched_canon}/{len(rows_out)} "
        f"({matched_canon/len(rows_out)*100:.1f}%) in master_streets.json)"
    )
    return rows_out


def main():
    canon_by_lower = load_canonical_map()
    by_year = {}
    for y in (1914, 1917):
        by_year[str(y)] = process_year(y, canon_by_lower)

    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        kept = [r for r in reader if r.get("year") not in by_year]

    all_rows = kept + by_year["1914"] + by_year["1917"]
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)
    print(f"Updated {DATA_CSV.name}: {len(all_rows)} total rows.")


if __name__ == "__main__":
    main()
