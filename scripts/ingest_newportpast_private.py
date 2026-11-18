#!/usr/bin/env python3
"""
Ingest the 2 post-1936 private Newport Past directories (stored in data.csv & volume_csvs/,
kept excluded from public data/ by MAX_PUBLIC_YEAR = 1936):
- 1946 (johns1946): verbatim <td> lines
- 1950 (johns1950): '[num, ]Surname, Forename, trade ~ [Building, ]Street'
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalize_1914_1917 as n14
import ingest_newportpast_1933_1938 as np33
import ingest_newportpast_public as np_pub

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"


def parse_1950_line(line, street_canon, canon_by_lower):
    if line.lower().startswith("from ") or re.match(r"^\(?(?:left|right)\s+hand\s+side", line, re.I):
        return None
    if re.match(r"^\(?return\.?\)?$", line, re.I):
        return None

    bldg = ""
    left = line
    street_out = street_canon
    if " ~ " in line:
        left, right = line.rsplit(" ~ ", 1)
        right = right.strip()
        if "," in right:
            bldg_part, st_part = right.rsplit(",", 1)
            bldg = bldg_part.strip().title()
            st_raw = re.sub(r"^St\s+", "St. ", st_part.strip(), flags=re.I)
            street_out = n14.clean_street_name(st_raw, canon_by_lower) or street_canon

    hn = ""
    m_hn = re.match(r"^(\d+[A-Za-z]?(?:\s*[-–&/,]\s*\d+[A-Za-z]?)*)\s*,\s*(.+)$", left.strip())
    if m_hn:
        hn = np33.fix_excel_serial_hn(m_hn.group(1).strip())
        left = m_hn.group(2).strip()

    if "here is " in left.lower():
        return {
            "year": "1950", "street": street_out, "house_number": "", "building_name": "",
            "surname": left.strip(), "forename": "", "trade": "", "source_type": "newportpast_html",
        }

    parts = [p.strip() for p in left.split(",", 2)]
    sn = parts[0] if len(parts) >= 1 else ""
    fn = parts[1] if len(parts) >= 2 else ""
    tr = parts[2] if len(parts) >= 3 else ""
    if tr == "-":
        tr = ""
    if np33.CORP_WORDS_RE.search(f"{sn} {fn}") and fn and not re.match(r"^(Mrs|Miss|Mr|Rev|Dr)\b", fn, re.I):
        sn = f"{sn} {fn}".strip() if fn.startswith("&") else f"{fn} {sn}".strip()
        fn = ""

    return {
        "year": "1950",
        "street": street_out,
        "house_number": hn,
        "building_name": bldg,
        "surname": sn,
        "forename": fn,
        "trade": tr,
        "source_type": "newportpast_html",
    }


def main():
    canon_by_lower = n14.load_canonical_map()
    fieldnames = ["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"]
    all_new = {}

    for year, slug in (("1946", "johns1946"), ("1950", "johns1950")):
        print(f"=== Fetching {year} ({slug}) from newportpast.com ===")
        streets = np_pub.fetch_list(slug)
        print(f"[{year}] Found {len(streets)} streets. Downloading/checking cache...")
        files = np_pub.fetch_pages(year, slug, streets)

        year_rows = []
        for (raw_param, label), html_file in zip(streets, files):
            if not html_file.exists():
                continue
            st_label = label.rsplit(",", 1)[-1].strip() if (year == "1950" and "," in label) else label
            st_label = re.sub(r"[.,]?\s+(?:B\.?\s*T\.?|M|P|C|L|Ll|Ch|B)\.?$", "", st_label.strip().rstrip(".")).strip()
            st_label = re.sub(r"^St\s+", "St. ", st_label, flags=re.I)
            st_canon = n14.clean_street_name(st_label, canon_by_lower) or st_label.title()
            html_text = html_file.read_text(encoding="utf-8", errors="ignore")
            lines = np33.extract_td_lines(html_text)
            if year == "1946":
                # Drop leading street+grid header line like 'HIGH STREET. D 6'
                filtered = [ln for ln in lines if not re.match(r"^[A-Z0-9'’.\-& ]+\.\s+[A-G]\s*\d\.?$", ln)]
                parsed = np33.parse_1938_lines(filtered, st_canon)
                for r in parsed:
                    r["year"] = "1946"
                year_rows.extend(parsed)
            else:
                for ln in lines:
                    row = parse_1950_line(ln, st_canon, canon_by_lower)
                    if row and any(row[k] for k in ("house_number", "building_name", "surname", "forename", "trade")):
                        year_rows.append(row)

        vol_csv = ROOT / "volume_csvs" / f"{year}_cleaned.csv"
        with open(vol_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(year_rows)
        all_new[year] = year_rows
        print(f"[{year}] Parsed {len(year_rows)} rows across {len(set(r['street'] for r in year_rows))} streets -> {vol_csv.name}")

    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        data_fn = reader.fieldnames
        kept = [r for r in reader if r.get("year") not in ("1946", "1950")]

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=data_fn)
        w.writeheader()
        w.writerows(kept + all_new["1946"] + all_new["1950"])

    print(f"Merged 1946 ({len(all_new['1946'])}) & 1950 ({len(all_new['1950'])}) into data.csv.")


if __name__ == "__main__":
    main()
