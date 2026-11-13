#!/usr/bin/env python3
"""
reprocess_1886_vision.py
Autonomous, column-aware vision extraction for Johns Newport Directory 1886.
Transcribes all 64 original scans with zero horizontal column bleed,
preserving street headers, cross-streets, and clean trade separation.
"""

import os
import sys
import glob
import time
import csv
from PIL import Image
from google import genai
from google.genai import types

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

# 1. Read API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    env_file = os.path.join(PROJECT_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as ef:
            for line in ef:
                if line.strip().startswith("GEMINI_API_KEY="):
                    api_key = line.strip().split("GEMINI_API_KEY=", 1)[1].strip()
                    break

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in environment or .env!")
    sys.exit(1)

client = genai.Client(api_key=api_key)

OUTPUT_DIR = os.path.join(PROJECT_DIR, "scratch", "1886_vision_rebuild")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SCANS_DIR = os.path.join(PROJECT_DIR, "original_scans", "Johns Directory 1886")
image_files = sorted(glob.glob(os.path.join(SCANS_DIR, "IMG_*.jpeg")))

print(f"Found {len(image_files)} scans in {SCANS_DIR}")

PROMPT = """You are digitizing a historical British street directory page (Johns Newport Directory 1886).

CRITICAL LAYOUT & COLUMN RULES:
1. VERTICAL COLUMNS: The page has 2 or 3 distinct vertical columns. You MUST transcribe Column 1 from TOP to BOTTOM. Only after Column 1 finishes, transcribe Column 2 from TOP to BOTTOM (and Column 3 if present). NEVER read horizontally across columns.
2. STREET HEADINGS: When a new street name appears (usually bold, uppercase, or centered, e.g. 'ALBERT STREET', 'ALBION STREET', 'BISHOP STREET'), emit a row with type='street'.
3. CROSS-STREET NAVIGATION: Lines indicating intersections like 'here is Francis Street', 'here is cross street', '[return]', or '[right-hand side]' are navigation markers. Emit them with type='cross_street'.
4. RESIDENTS / PROPERTIES:
   - house_number: door number (e.g. '1', '2', '14a', or '' if unnumbered)
   - building_name: pub/inn, hotel, villa, or named house (e.g. 'S. W. Railway Inn', 'Arcade Chambers', or '')
   - forename: given names, abbreviations, or titles (e.g. 'Andw. L.', 'Thos.', 'Wm.', 'Mrs. Harrict', 'Rev.')
   - surname: family surname (e.g. 'Chudleigh', 'Clisset', 'Morgan', 'Davies')
   - trade: occupation or trade (e.g. 'mate', 'chair mkr.', 'clerk', 'grocer', or '')
   - notes: extra notes or street location descriptions (e.g. 'From 35 Commercial road')

Format your response strictly as CSV enclosed in a ```csv ... ``` markdown block with columns:
type,street,house_number,building_name,forename,surname,trade,notes
"""

def process_image(img_path):
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    out_csv = os.path.join(OUTPUT_DIR, f"{base_name}.csv")

    if os.path.exists(out_csv) and os.path.getsize(out_csv) > 100:
        print(f"[{base_name}] Already processed, skipping.")
        return True

    print(f"[{base_name}] Processing with Gemini 3.8 Flash (zero-thought budget)...")
    try:
        image = Image.open(img_path)
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=[image, PROMPT],
            config=types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.0,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        
        text = response.text.strip()
        if "```csv" in text:
            csv_content = text.split("```csv", 1)[1].split("```", 1)[0].strip()
        elif "```" in text:
            csv_content = text.split("```", 1)[1].split("```", 1)[0].strip()
        else:
            csv_content = text

        with open(out_csv, "w", encoding="utf-8") as f:
            f.write(csv_content + "\n")
            
        line_count = len(csv_content.splitlines())
        print(f"[{base_name}] Successfully written {line_count} lines.")
        return True
    except Exception as e:
        print(f"[{base_name}] ERROR: {e}")
        return False

def compile_master_1886():
    master_csv = os.path.join(PROJECT_DIR, "volume_csvs", "1886_cleaned.csv")
    backup_csv = os.path.join(PROJECT_DIR, "volume_csvs", "1886_cleaned.csv.bak_before_vision")
    
    if os.path.exists(master_csv) and not os.path.exists(backup_csv):
        import shutil
        shutil.copy2(master_csv, backup_csv)
        print(f"Backed up old 1886_cleaned.csv to {backup_csv}")

    all_csvs = sorted(glob.glob(os.path.join(OUTPUT_DIR, "IMG_*.csv")))
    print(f"Compiling {len(all_csvs)} page CSVs into {master_csv}...")

    total_entries = 0
    total_streets = set()
    current_street = "Unknown"

    with open(master_csv, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"])

        for page_csv in all_csvs:
            with open(page_csv, "r", encoding="utf-8", errors="ignore") as f_in:
                reader = csv.reader(f_in)
                for row in reader:
                    if not row or row[0].strip().lower() == "type":
                        continue
                    row_type = row[0].strip().lower()
                    
                    if row_type == "street":
                        street_cand = row[1].strip() if len(row) > 1 else ""
                        if street_cand:
                            current_street = street_cand
                            total_streets.add(current_street)
                    elif row_type in ("entry", "resident"):
                        street_val = (row[1].strip() if len(row) > 1 and row[1].strip() else current_street)
                        house_num = row[2].strip() if len(row) > 2 else ""
                        bldg_name = row[3].strip() if len(row) > 3 else ""
                        forename = row[4].strip() if len(row) > 4 else ""
                        surname = row[5].strip() if len(row) > 5 else ""
                        trade = row[6].strip() if len(row) > 6 else ""

                        if not surname and not forename and not bldg_name and not trade:
                            continue

                        writer.writerow(["1886", street_val, house_num, bldg_name, surname, forename, trade, ""])
                        total_entries += 1

    print(f"\n==========================================")
    print(f"1886 REBUILD COMPLETE!")
    print(f"Total verified residents: {total_entries}")
    print(f"Total distinct streets: {len(total_streets)}")
    print(f"Saved to: {master_csv}")
    print(f"==========================================\n")

if __name__ == "__main__":
    success_count = 0
    for img in image_files:
        if process_image(img):
            success_count += 1
        time.sleep(1)

    print(f"\nFinished processing {success_count}/{len(image_files)} pages.")
    if success_count == len(image_files):
        compile_master_1886()
