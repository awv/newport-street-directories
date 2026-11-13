#!/usr/bin/env python3
"""
process_1908_vision.py
Autonomous, high-throughput vision extraction for Johns Newport Directory 1908.
Processes all scans using 5 parallel workers with Gemini 3.8 Flash (thinking_budget=0),
compiles page CSVs into volume_csvs/1908_cleaned.csv, merges into data.csv,
and rebuilds site data, search index, and statistics.
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

LOG_FILE = os.path.join(PROJECT_DIR, "log_files", "1908_vision_reprocess.log")
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

YEAR = 1908
SCANS_DIR = os.path.join(PROJECT_DIR, "original_scans", f"Johns Directory {YEAR}")
OUT_DIR = os.path.join(PROJECT_DIR, "scratch", f"{YEAR}_vision_rebuild")
os.makedirs(OUT_DIR, exist_ok=True)

PROMPT = f"""You are digitizing a historical British street directory page (Johns Newport Directory {YEAR}).

CRITICAL LAYOUT & COLUMN RULES:
1. VERTICAL COLUMNS: The page has 2 or 3 distinct vertical columns. You MUST transcribe Column 1 from TOP to BOTTOM. Only after Column 1 finishes, transcribe Column 2 from TOP to BOTTOM (and Column 3 if present). NEVER read horizontally across columns.
2. STREET HEADINGS: When a new street name appears (usually bold, uppercase, or centered, e.g. 'ALBERT STREET', 'ALBION STREET', 'BISHOP STREET'), emit a row with type='street'. Do NOT emit running headers like 'NEWPORT STREET DIRECTORY' as streets.
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

def process_single_image(img_path, max_retries=5):
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    out_csv = os.path.join(OUT_DIR, f"{base_name}.csv")

    if os.path.exists(out_csv) and os.path.getsize(out_csv) > 250:
        return True, base_name, "cached"

    for attempt in range(1, max_retries + 1):
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

def build_canonical_street_map():
    # Build a lookup dictionary of lower-case to canonical street names
    canonical = {}
    
    # 1. Read master_streets.json
    ms_path = os.path.join(PROJECT_DIR, "master_streets.json")
    if os.path.exists(ms_path):
        import json
        with open(ms_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            streets = data.get("streets", {})
            for slug, item in streets.items():
                cname = item.get("canonical_name")
                if cname:
                    canonical[cname.lower()] = cname
                    
    # 2. Read distinct streets from data.csv
    data_csv = os.path.join(PROJECT_DIR, "data.csv")
    if os.path.exists(data_csv):
        with open(data_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                st = (r.get("street") or "").strip()
                if st and st.lower() not in canonical:
                    # Prefer existing casing
                    canonical[st.lower()] = st

    return canonical

def clean_street_name(st, canonical_map):
    s = st.strip()
    # Strip common district/map grid suffixes: (B.T.), B.T, C 5, D 5, . M., . P., etc.
    s = re.sub(r'[\s\.\,]+(\(?B\.?\s*T\.?\)?|\(?T\.?\s*W\.?\)?)$', '', s, flags=re.I)
    s = re.sub(r'[\s\.\,]+[A-F]\s*\d+[a-z]?$', '', s, flags=re.I)
    sfx = r'(?:street|road|avenue|place|terrace|crescent|parade|lane|hill|park|row|square|view|cottages|drive|gardens|grove|mews|walk|way|par|st|rd|circus)'
    s = re.sub(rf'(\b{sfx})[\s\.\,]+[MPCB]\.?$', r'\1', s, flags=re.I)
    s = re.sub(r'[\.\,\:\;\-]+$', '', s).strip()

    low = s.lower()
    if low in canonical_map:
        return canonical_map[low]
    
    # Standard Title Case conversion if all upper
    if s.isupper():
        words = s.split()
        clean = []
        for i, w in enumerate(words):
            if i > 0 and w.lower() in ('and', 'of', '&', 'the', 'in', 'at'):
                clean.append(w.lower())
            else:
                clean.append(w.capitalize())
        return ' '.join(clean)
    return s

def main():
    start_time = time.time()
    log(f"=======================================================")
    log(f"=== Starting Johns Newport Directory {YEAR} Vision Digitization ===")
    log(f"=======================================================")

    images = sorted(glob.glob(os.path.join(SCANS_DIR, "IMG_*.jpeg")) +
                    glob.glob(os.path.join(SCANS_DIR, "IMG_*.jpg")) +
                    glob.glob(os.path.join(SCANS_DIR, "IMG_*.png")))

    if not images:
        log(f"CRITICAL ERROR: No scan images found in {SCANS_DIR}!")
        sys.exit(1)

    total_images = len(images)
    log(f"Found {total_images} scan pages in {SCANS_DIR}. Launching 5 parallel workers...")

    completed = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_single_image, img): img for img in images}
        for f in as_completed(futures):
            success, base_name, msg = f.result()
            completed += 1
            if completed % 15 == 0 or completed == total_images:
                log(f"[{YEAR}] Progress: {completed}/{total_images} scans processed ({completed/total_images*100:.1f}%)")

    log(f"\nAll {total_images} scans processed. Compiling volume CSV...")

    canonical_map = build_canonical_street_map()

    master_csv = os.path.join(PROJECT_DIR, "volume_csvs", f"{YEAR}_cleaned.csv")
    backup_csv = os.path.join(PROJECT_DIR, "volume_csvs", f"{YEAR}_cleaned.csv.bak_before_vision")
    if os.path.exists(master_csv) and not os.path.exists(backup_csv):
        shutil.copy2(master_csv, backup_csv)

    all_csvs = sorted(glob.glob(os.path.join(OUT_DIR, "IMG_*.csv")))
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
                        if street_cand and not any(k in street_cand.upper() for k in ["NEWPORT", "STREET DIRECTORY"]):
                            cleaned_st = clean_street_name(street_cand, canonical_map)
                            if cleaned_st:
                                current_street = cleaned_st
                                total_streets.add(current_street)
                    elif row_type in ("entry", "resident"):
                        st, hn, bldg, fn, sn, tr = parse_resident_row(row, current_street)

                        if not sn and not fn and not bldg and not tr:
                            continue

                        writer.writerow([str(YEAR), st, hn, bldg, sn, fn, tr, ""])
                        total_entries += 1

    log(f"Volume {YEAR} Compiled: {total_entries:,} vision residents across {len(total_streets)} streets.")

    if total_entries > 5000:
        log(f"Merging {YEAR} into master dataset data.csv via merge_{YEAR}.py...")
        subprocess.run(["python3", f"scripts/merge_{YEAR}.py"], check=True)
        
        log("Running clean_non_streets.py...")
        subprocess.run(["python3", "scripts/clean_non_streets.py"], check=True)

        log("Running merge_casing_twins.py...")
        subprocess.run(["python3", "scripts/merge_casing_twins.py"], check=True)

        log("Rebuilding site data and statistics...")
        subprocess.run(["python3", "scripts/build_site_data.py"], check=True)
        subprocess.run(["python3", "scripts/build_stats_data.py"], check=True)

        elapsed = time.time() - start_time
        log(f"=======================================================")
        log(f"=== {YEAR} VISION DIGITIZATION COMPLETE in {elapsed/60:.1f} minutes! ===")
        log(f"=======================================================")
    else:
        log(f"WARNING: Entry count ({total_entries}) lower than expected threshold. Please inspect {OUT_DIR}.")

if __name__ == "__main__":
    main()
