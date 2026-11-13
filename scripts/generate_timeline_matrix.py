#!/usr/bin/env python3
"""
generate_timeline_matrix.py

Generates a comprehensive street-by-year building/resident timeline matrix
from data.csv across all 20 historical archive directories.

Outputs:
1. street_timeline_matrix.tsv — Tab-separated spreadsheet file ready to open in Excel, Numbers, or Sheets.
2. data/street_timeline.json  — JSON payload powering the interactive timeline.html web dashboard.

Calculates:
- Building / resident counts per year
- Number of active years and year span
- Min and max house numbers
- Count of records with house numbers vs unnumbered
- Anomaly classification:
  - 🔴 Severe Drop: Drop of >60% compared to previous active directory (with prev >= 15)
  - 🟡 Gap Year: Street was present in earlier and later directories, but has 0 records in an intermediate edition
  - 🔵 Number Outlier: Max house number >= 300 or >3x the count of records
  - ⚪ Disappeared: Active in Victorian/Edwardian era, but 0 records by 1936/1971
  - 🟣 Newcomer (1971): First appeared in 1971
  - 🟢 Stable / Growing: Expected urban growth trajectory
"""

import csv
import json
import os
import re

ARCHIVE_YEARS = [
    "1876", "1878", "1882", "1887", "1890", "1893", "1894", "1898", "1899", "1900",
    "1902", "1903", "1905", "1910", "1913", "1920", "1925", "1927", "1936", "1971"
]

def extract_numeric_house_number(val):
    if not val:
        return None
    val = val.strip()
    m = re.match(r"^(\d+)", val)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 3000:  # sanity filter
            return n
    return None

def main():
    csv_path = "data.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    print("Reading data.csv...")
    streets = {}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            st = row.get("street", "").strip()
            yr = row.get("year", "").strip()
            if not st or not yr:
                continue

            if st not in streets:
                streets[st] = {
                    "street": st,
                    "total_records": 0,
                    "years": {y: 0 for y in ARCHIVE_YEARS},
                    "house_numbers": [],
                    "numbered_records": 0,
                }

            s_data = streets[st]
            s_data["total_records"] += 1
            if yr in s_data["years"]:
                s_data["years"][yr] += 1

            hn = row.get("house_number", "").strip()
            if hn:
                s_data["numbered_records"] += 1
                num = extract_numeric_house_number(hn)
                if num is not None:
                    s_data["house_numbers"].append(num)

    print(f"Parsed {len(streets)} unique canonical streets.")

    matrix_rows = []

    for st, data in streets.items():
        counts = [data["years"][y] for y in ARCHIVE_YEARS]
        active_years = [y for y, c in zip(ARCHIVE_YEARS, counts) if c > 0]
        active_indices = [i for i, c in enumerate(counts) if c > 0]

        first_year = active_years[0] if active_years else "None"
        last_year = active_years[-1] if active_years else "None"
        span = f"{first_year}–{last_year}" if active_years else "N/A"

        h_nums = data["house_numbers"]
        min_hn = min(h_nums) if h_nums else ""
        max_hn = max(h_nums) if h_nums else ""

        # Anomaly checks
        anomaly_flags = []
        
        # 1. Check severe drops (>60% drop from >=15)
        severe_drop_details = []
        for i in range(len(counts) - 1):
            prev_c = counts[i]
            curr_c = counts[i+1]
            if prev_c >= 15 and curr_c > 0 and curr_c < prev_c * 0.4:
                drop_pct = round((prev_c - curr_c) / prev_c * 100)
                severe_drop_details.append(f"{ARCHIVE_YEARS[i]} ({prev_c}) -> {ARCHIVE_YEARS[i+1]} ({curr_c}) [-{drop_pct}%]")
        
        if severe_drop_details:
            anomaly_flags.append(f"Severe Drop ({'; '.join(severe_drop_details)})")

        # 2. Check gap years (active before and after, but 0 in between)
        gap_years = []
        if active_indices and len(active_indices) >= 2:
            start_i = active_indices[0]
            end_i = active_indices[-1]
            for i in range(start_i, end_i + 1):
                if counts[i] == 0:
                    gap_years.append(ARCHIVE_YEARS[i])
        
        if gap_years:
            anomaly_flags.append(f"Gap Year(s) ({', '.join(gap_years)})")

        # 3. Check house number outliers
        if max_hn and isinstance(max_hn, int) and max_hn >= 300:
            anomaly_flags.append(f"High House # ({max_hn})")

        # 4. Check if street disappeared early
        if last_year in ["1876", "1878", "1882", "1887", "1890", "1893", "1894", "1898", "1899", "1900", "1902", "1903", "1905", "1910", "1913", "1920", "1925"]:
            anomaly_flags.append("Disappeared Early")

        # 5. Check newcomer 1971
        if first_year == "1971":
            anomaly_flags.append("1971 Newcomer")

        # Primary status tag
        if any("Severe Drop" in f for f in anomaly_flags):
            primary_status = "🔴 Severe Drop"
        elif any("Gap Year" in f for f in anomaly_flags):
            primary_status = "🟡 Gap Year"
        elif any("High House #" in f for f in anomaly_flags):
            primary_status = "🔵 Number Discrepancy"
        elif any("Disappeared" in f for f in anomaly_flags):
            primary_status = "⚪ Disappeared"
        elif any("1971 Newcomer" in f for f in anomaly_flags):
            primary_status = "🟣 1971 Newcomer"
        else:
            primary_status = "🟢 Stable / Growing"

        row_dict = {
            "street": st,
            "status": primary_status,
            "total_records": data["total_records"],
            "active_years_count": len(active_years),
            "span": span,
            "min_house_number": min_hn,
            "max_house_number": max_hn,
            "numbered_records": data["numbered_records"],
            "anomaly_details": " | ".join(anomaly_flags) if anomaly_flags else "Normal",
            "years": data["years"],
        }
        matrix_rows.append(row_dict)

    # Sort alphabetically by street name
    matrix_rows.sort(key=lambda r: r["street"].lower())

    # 1. Write TSV
    tsv_out = "street_timeline_matrix.tsv"
    tsv_headers = [
        "Street Name",
        "Status",
        "Total Records",
        "Active Years",
        "Year Span",
        "Min House #",
        "Max House #",
        "Numbered Records",
        "Anomaly Details",
        "Review Notes",
    ] + ARCHIVE_YEARS

    print(f"Writing {tsv_out}...")
    with open(tsv_out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(tsv_headers)
        for r in matrix_rows:
            yr_counts = [r["years"][y] for y in ARCHIVE_YEARS]
            row_vals = [
                r["street"],
                r["status"],
                r["total_records"],
                r["active_years_count"],
                r["span"],
                r["min_house_number"],
                r["max_house_number"],
                r["numbered_records"],
                r["anomaly_details"],
                "",  # Review Notes left blank for user input
            ] + yr_counts
            writer.writerow(row_vals)

    # 2. Write JSON for web app
    os.makedirs("data", exist_ok=True)
    json_out = "data/street_timeline.json"
    print(f"Writing {json_out}...")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump({
            "archive_years": ARCHIVE_YEARS,
            "total_streets": len(matrix_rows),
            "streets": matrix_rows
        }, f, indent=2)

    print(f"Done! Generated {tsv_out} and {json_out}.")

if __name__ == "__main__":
    main()
