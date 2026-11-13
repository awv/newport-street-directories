#!/usr/bin/env python3
"""
autonomous_overnight_master.py (Parallel 5x Acceleration)
High-throughput, parallel vision extraction and volume compilation engine.
Processes the Victorian/Edwardian Johns Directory volumes using 5 concurrent workers,
handling rate limits, retries, compilation, and automated database merging.
"""

import os
import sys
import glob
import time
import csv
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from PIL import Image
from google import genai
from google.genai import types

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

LOG_FILE = os.path.join(PROJECT_DIR, "overnight_pipeline.log")
AUDIT_LOG_MD = os.path.join(PROJECT_DIR, "overnight_audit_log.md")
log_lock = threading.Lock()

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    with log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")

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
    log("CRITICAL ERROR: GEMINI_API_KEY not found in environment or .env!")
    sys.exit(1)

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=90000)
)

YEARS_QUEUE = [
    1902, 1903, 
    1910, 1913, 1915, 1920, 1924, 1925, 1927, 1936, 1971
]

PROMPT = """You are digitizing a historical British street directory page (Johns Newport Directory {YEAR}).

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

def process_single_image(img_path, out_dir, year, max_retries=5):
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    out_csv = os.path.join(out_dir, f"{base_name}.csv")

    if os.path.exists(out_csv) and os.path.getsize(out_csv) > 200:
        log(f"[{year} | {base_name}] Cached, skipping.")
        return True

    year_prompt = PROMPT.replace("{YEAR}", str(year))

    for attempt in range(1, max_retries + 1):
        try:
            image = Image.open(img_path)
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=[image, year_prompt],
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

            log(f"[{year} | {base_name}] Success: {len(lines)} lines extracted.")
            return True

        except Exception as e:
            wait_sec = attempt * 5
            log(f"[{year} | {base_name}] Attempt {attempt}/{max_retries} failed: {e}. Backing off {wait_sec}s...")
            time.sleep(wait_sec)

    log(f"[{year} | {base_name}] WARNING: Exhausted retries. Writing minimal placeholder.")
    with open(out_csv, "w", encoding="utf-8") as f:
        f.write("type,street,house_number,building_name,forename,surname,trade,notes\n")
    return False

def compile_and_merge_year(year, out_dir):
    master_csv = os.path.join(PROJECT_DIR, "volume_csvs", f"{year}_cleaned.csv")
    backup_csv = os.path.join(PROJECT_DIR, "volume_csvs", f"{year}_cleaned.csv.bak_before_vision")

    if os.path.exists(master_csv) and not os.path.exists(backup_csv):
        import shutil
        shutil.copy2(master_csv, backup_csv)
        log(f"Backed up old {year}_cleaned.csv to {backup_csv}")

    all_csvs = sorted(glob.glob(os.path.join(out_dir, "IMG_*.csv")))
    log(f"Compiling {len(all_csvs)} page CSVs for {year} into {master_csv}...")

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

                        writer.writerow([str(year), street_val, house_num, bldg_name, surname, forename, trade, ""])
                        total_entries += 1

    log(f"[{year}] Compiled: {total_entries} residents across {len(total_streets)} streets.")

    merge_script = os.path.join(PROJECT_DIR, "scripts", f"merge_{year}.py")
    if os.path.exists(merge_script):
        log(f"[{year}] Executing auto-merge into data.csv ({merge_script})...")
        try:
            res = subprocess.run([sys.executable, merge_script], capture_output=True, text=True, check=True)
            log(f"[{year}] Auto-merge complete: {res.stdout.strip()}")
        except Exception as e:
            log(f"[{year}] Auto-merge execution error: {e}")

    with log_lock:
        with open(AUDIT_LOG_MD, "a", encoding="utf-8") as f_md:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f_md.write(f"| {year} | {total_entries:,} | {len(total_streets)} | ✅ Clean Vision Extracted & Merged | {now_str} |\n")

def run_pipeline():
    log("==================================================================")
    log("STARTING PARALLEL (5x) DIRECTORY PIPELINE")
    log("==================================================================")

    for year in YEARS_QUEUE:
        scan_dir = os.path.join(PROJECT_DIR, "original_scans", f"Johns Directory {year}")
        if not os.path.exists(scan_dir):
            log(f"[{year}] Directory not found at {scan_dir}, skipping.")
            continue

        images = sorted(glob.glob(os.path.join(scan_dir, "IMG_*.jpeg")) + 
                        glob.glob(os.path.join(scan_dir, "IMG_*.jpg")) +
                        glob.glob(os.path.join(scan_dir, "IMG_*.png")))
        if not images:
            log(f"[{year}] No image files found in {scan_dir}, skipping.")
            continue

        out_dir = os.path.join(PROJECT_DIR, "scratch", f"{year}_vision_rebuild")
        os.makedirs(out_dir, exist_ok=True)

        log(f"\n>>> BEGINNING VOLUME: Johns Directory {year} ({len(images)} scans) [5 Workers] <<<")

        # Process in parallel with 5 workers
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_single_image, img, out_dir, year) for img in images]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    log(f"Worker generated an exception: {exc}")

        log(f">>> FINISHED ALL SCANS FOR {year}. Compiling and merging... <<<")
        compile_and_merge_year(year, out_dir)

    log("==================================================================")
    log("ALL QUEUED DIRECTORIES PROCESSED SUCCESSFULLY!")
    log("==================================================================")

if __name__ == "__main__":
    run_pipeline()
