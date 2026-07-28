import csv
import re

INPUT_CSV = "data.csv"
OUTPUT_CSV = "data.csv"

# Dictionary of standard street suffix expansions
ABBREVIATIONS = {
    r"\bRd\b\.?": "Road",
    r"\bSt\b\.?": "Street",
    r"\bAve\b\.?": "Avenue",
    r"\bTer\b\.?": "Terrace",
    r"\bPl\b\.?": "Place",
    r"\bSq\b\.?": "Square",
    r"\bCres\b\.?": "Crescent",
    r"\bPde\b\.?": "Parade",
    r"\bGdns\b\.?": "Gardens",
}

def clean_street_name(name):
    if not name:
        return ""
    
    # 1. Strip surrounding quotes
    clean = name.replace('"', '').strip()
    
    # 2. Strip ward codes/district references (e.g. ", C", ", W", ", E 7")
    clean = re.sub(r",\s*[A-Za-z0-9\s]+\b", "", clean)
    
    # 3. Expand abbreviations (e.g. "Crindau Rd" -> "Crindau Road")
    for pattern, replacement in ABBREVIATIONS.items():
        clean = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)
        
    # 4. Clean trailing dots and spaces
    clean = clean.rstrip(".")
    
    # 5. Title-case for consistent output
    return clean.title().strip()

def main():
    rows = []
    with open(INPUT_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            row["street"] = clean_street_name(row["street"])
            rows.append(row)

    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done! Cleaned and normalized {len(rows)} records in data.csv.")

if __name__ == "__main__":
    main()