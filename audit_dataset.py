import csv
import re

CSV_FILE = "data.csv"

# Anomaly Detection Patterns
CROSS_STREET_REGEX = re.compile(
    r'\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|parade|pde|av|av\.)\b.*?\bto\b.*?\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|parade|pde|av|av\.)\b'
    r'|^\s*(?:here\s+are|here\s+is|here\s+cross|\[?return\]?|\(return\.?\)|return\.)\b'
    r'|^\s*(?:maindee|newport|pill)from\b',
    re.I
)

RUNON_OCR_REGEX = re.compile(r'[a-z]\.[A-Z][a-z]+.*[a-z]\.[A-Z][a-z]+')

def audit():
    anomalies = {
        "cross_street_headings": [],
        "runon_ocr_records": [],
        "telephone_house_numbers": [],
        "district_header_bleed": [],
        "split_ampersand_names": [],
    }

    with open(CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            line_no = idx + 2
            street = row.get("street") or ""
            house_num = row.get("house_number") or ""
            bldg = row.get("building_name") or ""
            surname = row.get("surname") or ""
            forename = row.get("forename") or ""
            trade = row.get("trade") or ""

            combined_name = f"{surname} {forename}".strip()
            full_text = f"{bldg} {surname} {forename} {trade}".strip()

            # 1. Detect Cross-street Headings
            if CROSS_STREET_REGEX.search(combined_name) or CROSS_STREET_REGEX.search(bldg):
                anomalies["cross_street_headings"].append((line_no, street, house_num, combined_name))

            # 2. Detect Run-on OCR Smashed Records
            if len(trade) > 100 or RUNON_OCR_REGEX.search(trade):
                anomalies["runon_ocr_records"].append((line_no, street, house_num, surname, trade[:60] + "..."))

            # 3. Detect Misparsed Telephone Numbers in house_number
            if house_num.isdigit() and int(house_num) >= 1000 and street != "Corporation Road":
                anomalies["telephone_house_numbers"].append((line_no, street, house_num, surname))

            # 4. Detect District Header Bleed (e.g. MaindeeFrom)
            if re.match(r'^(maindee|newport|pill)from', surname, re.I) or re.match(r'^(maindee|newport|pill)from', forename, re.I):
                anomalies["district_header_bleed"].append((line_no, street, surname, forename))

            # 5. Detect Split Ampersand Names
            if forename.startswith("& "):
                anomalies["split_ampersand_names"].append((line_no, street, house_num, surname, forename))

    print("=== DATASET ANOMALY AUDIT SUMMARY ===")
    for key, items in anomalies.items():
        print(f"[{key.upper()}]: {len(items)} records found")
        for sample in items[:3]:
            print(f"   Line {sample[0]} ({sample[1]}): {sample[2:]}")
        print()

if __name__ == "__main__":
    audit()
