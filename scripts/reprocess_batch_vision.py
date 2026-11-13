#!/usr/bin/env python3
"""
reprocess_batch_vision.py
Autonomous vision extraction for Johns Newport Directories 1920, 1924, and 1927.
Processes each year using 5 parallel workers with Gemini 3.8 Flash (thinking_budget=0),
compiles page CSVs into volume_csvs/{YEAR}_cleaned.csv, auto-merges into data.csv,
and rebuilds site data and search indices.
"""

import os
import sys
import glob
import time
import csv
import re
import shutil
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from PIL import Image
from google import genai
from google.genai import types

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

LOG_FILE = os.path.join(PROJECT_DIR, "log_files", "reprocess_up_to_1927.log")
os.makedirs(os.path.join(PROJECT_DIR, "log_files"), exist_ok=True)
log_lock = threading.Lock()

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    with log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")

# Read API Key
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
    log("CRITICAL ERROR: GEMINI_API_KEY not found in environment or .env!")
    sys.exit(1)

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=90000)
)

PROMPT_TEMPLATE = """You are digitizing a historical British street directory page (Johns Newport Directory {YEAR}).

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

PAT_DISTRICT = re.compile(r'^\s*\(?[A-Z]\.?(\s*[A-Z]\.?)?(\s*\d+[a-z]?)?\)?\.?\s*$', re.I)

def parse_resident_row(row, current_street):
    if len(row) > 3 and PAT_DISTRICT.match(row[2]):
        row = [row[0], row[1]] + row[3:]
        
    st = row[1].strip() if len(row) > 1 and row[1].strip() else current_street
    hn = row[2].strip() if len(row) > 2 else ''
    bldg = row[3].strip() if len(row) > 3 else ''
    
    if len(row) >= 9 and row[4] == '' and row[5] != '' and row[6] != '':
        fn = row[5].strip()
        sn = row[6].strip()
        tr = ', '.join([c.strip() for c in row[7:] if c.strip()])
    else:
        fn = row[4].strip() if len(row) > 4 else ''
        sn = row[5].strip() if len(row) > 5 else ''
        tr = ', '.join([c.strip() for c in row[6:] if c.strip()])
        
    return st, hn, bldg, fn, sn, tr

def process_single_image(img_path, out_dir, prompt, max_retries=5):
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    out_csv = os.path.join(out_dir, f"{base_name}.csv")

    if os.path.exists(out_csv) and os.path.getsize(out_csv) > 250:
        return True, base_name, "cached"

    for attempt in range(1, max_retries + 1):
        try:
            image = Image.open(img_path)
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=[image, prompt],
                config=types.GenerateContentConfig(
                    max_output_tokens=8192,
                    temperature=0.0,
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )

            text = response.text.strip() if response and response.text else ""
            if "```csv" in text:
                csv_content = text.split("```csv", 1)[1].split("```", 1)[0].strip()
            elif "```" in text:
                csv_content = text.split("```", 1)[1].split("```", 1)[0].strip()
            else:
                csv_content = text

            lines = [l for l in csv_content.splitlines() if l.strip()]
            if len(lines) < 2:
                raise ValueError("Response produced empty or near-empty CSV")

            with open(out_csv, "w", encoding="utf-8") as f:
                f.write(csv_content + "\n")

            return True, base_name, f"extracted {len(lines)} lines"

        except Exception as e:
            wait_time = attempt * 5
            log(f"[{base_name}] Attempt {attempt}/{max_retries} failed: {e}. Backing off {wait_time}s...")
            time.sleep(wait_time)

    return False, base_name, "failed"

def process_year(year):
    scans_dir = os.path.join(PROJECT_DIR, "original_scans", f"Johns Directory {year}")
    out_dir = os.path.join(PROJECT_DIR, "scratch", f"{year}_vision_rebuild")
    os.makedirs(out_dir, exist_ok=True)

    images = sorted(glob.glob(os.path.join(scans_dir, "IMG_*.jpeg")) +
                    glob.glob(os.path.join(scans_dir, "IMG_*.jpg")) +
                    glob.glob(os.path.join(scans_dir, "IMG_*.png")))

    if not images:
        log(f"No scan images found for year {year} in {scans_dir}!")
        return False

    prompt = PROMPT_TEMPLATE.format(YEAR=year)
    log(f"\n=======================================================")
    log(f"=== Starting Year {year} Vision Reprocessing: {len(images)} scans (5 Workers) ===")
    log(f"=======================================================")

    completed = 0
    total = len(images)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_single_image, img, out_dir, prompt): img for img in images}
        for f in as_completed(futures):
            success, base_name, msg = f.result()
            completed += 1
            if completed % 15 == 0 or completed == total:
                log(f"[{year}] Progress: {completed}/{total} scans processed ({completed/total*100:.1f}%)")

    log(f"=== All {total} scans for {year} processed. Compiling volume CSV... ===")

    # Compile into volume_csvs/{year}_cleaned.csv
    master_csv = os.path.join(PROJECT_DIR, "volume_csvs", f"{year}_cleaned.csv")
    backup_csv = os.path.join(PROJECT_DIR, "volume_csvs", f"{year}_cleaned.csv.bak_before_vision")
    
    if os.path.exists(master_csv) and not os.path.exists(backup_csv):
        shutil.copy2(master_csv, backup_csv)

    all_csvs = sorted(glob.glob(os.path.join(out_dir, "IMG_*.csv")))
    total_entries = 0
    total_streets = set()
    current_street = "Unknown"

    with open(master_csv, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"])

        for page_csv in all_csvs:
            if os.path.getsize(page_csv) <= 250:
                continue
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
                        st, hn, bldg, fn, sn, tr = parse_resident_row(row, current_street)

                        if not sn and not fn and not bldg and not tr:
                            continue

                        writer.writerow([str(year), st, hn, bldg, sn, fn, tr, ""])
                        total_entries += 1

    log(f"Volume {year} Compiled: {total_entries:,} vision residents across {len(total_streets)} streets.")

    # Merge into data.csv if extraction was healthy (> 8,000 entries)
    if total_entries > 8000:
        log(f"Executing merge_{year}.py into data.csv...")
        subprocess.run(["python3", f"scripts/merge_{year}.py"], check=True)
        log(f"Year {year} successfully merged into data.csv!")
        return True
    else:
        log(f"WARNING: Entry count for {year} ({total_entries}) lower than expected threshold. Preserving existing records.")
        return False

def main():
    start_time = time.time()
    years = [1920, 1924, 1927]

    # Create safety backup of data.csv before batch run
    data_csv = os.path.join(PROJECT_DIR, "data.csv")
    master_backup = os.path.join(PROJECT_DIR, "data.csv.bak_before_batch_vision_1920_1927")
    if not os.path.exists(master_backup):
        log(f"Creating safety backup: {master_backup}...")
        shutil.copy2(data_csv, master_backup)

    for yr in years:
        success = process_year(yr)
        if not success:
            log(f"Year {yr} encountered an issue. Continuing to next year...")

    log("\n=======================================================")
    log("=== All batch volumes processed! Running post-processing and site build... ===")
    log("=======================================================")
    
    log("Running clean_non_streets.py...")
    subprocess.run(["python3", "scripts/clean_non_streets.py"], check=True)

    log("Running build_site_data.py...")
    subprocess.run(["python3", "scripts/build_site_data.py"], check=True)

    log("Running build_stats_data.py...")
    subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)

    elapsed = time.time() - start_time
    log(f"\nBATCH VISION REPROCESSING COMPLETE for {years} in {elapsed/60:.1f} minutes!")

if __name__ == "__main__":
    main()
