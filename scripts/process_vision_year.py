#!/usr/bin/env python3
"""
Generalized Vision OCR extraction & ingestion script for a Johns Newport Directory year.
Uses Gemini Flash with upright EXIF transposition, parallel workers, resumable per-page CSVs,
compilation to volume_csvs/{YEAR}_cleaned.csv, and safe merge into data.csv.
"""
import argparse
import csv
import glob
import os
import re
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image, ImageOps

PROJECT_DIR = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_DIR)

log_lock = threading.Lock()
PAT_DISTRICT = re.compile(r"^\s*\(?[A-Z]\.?(\s*[A-Z]\.?)?(\s*\d+[a-z]?)?\)?\.?\s*$", re.I)

PROMPT_TEMPLATE = """You are digitizing a historical British street directory page (Johns Newport Directory {year}).

CRITICAL LAYOUT & COLUMN RULES:
1. VERTICAL COLUMNS: The page has 2 or 3 distinct vertical columns. You MUST transcribe Column 1 from TOP to BOTTOM. Only after Column 1 finishes, transcribe Column 2 from TOP to BOTTOM (and Column 3 if present). NEVER read horizontally across columns.
2. STREET HEADINGS: When a new street name appears (usually bold, uppercase, or centered, e.g. 'ABERTHAW ROAD', 'ADELAIDE STREET', 'AGINCOURT STREET'), emit a row with type='street'.
3. CROSS-STREET NAVIGATION: Lines indicating intersections like 'here is Pottery-terrace', '[return]', or '(LEFT HAND SIDE)' are navigation markers. Emit them with type='cross_street'.
4. RESIDENTS / PROPERTIES:
   - house_number: door number (e.g. '1', '2', '14a', or '' if unnumbered)
   - building_name: pub/inn, hotel, villa, or named house (e.g. 'S. W. Railway Inn', 'Arcade Chambers', or '')
   - forename: given names, abbreviations, or titles (e.g. 'Andw. L.', 'Thos.', 'Wm.', 'Mrs. Sarah', 'Rev.')
   - surname: family surname (e.g. 'Chudleigh', 'Clisset', 'Morgan', 'Davies')
   - trade: occupation or trade (e.g. 'mate', 'chair mkr.', 'clerk', 'grocer', or '')
   - notes: extra notes or street location descriptions (e.g. 'From 35 Commercial road')

Format your response strictly as CSV enclosed in a ```csv ... ``` markdown block with columns:
type,street,house_number,building_name,forename,surname,trade,notes
"""


def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()
    env_file = PROJECT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GEMINI_API_KEY="):
                return line.strip().split("GEMINI_API_KEY=", 1)[1].strip()
    raise RuntimeError("GEMINI_API_KEY not found in environment or .env")


def log(log_file, msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with log_lock:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def parse_resident_row(row, current_street):
    if len(row) > 3 and PAT_DISTRICT.match(row[2]):
        row = [row[0], row[1]] + row[3:]
    st = row[1].strip() if len(row) > 1 and row[1].strip() else current_street
    hn = row[2].strip() if len(row) > 2 else ""
    bldg = row[3].strip() if len(row) > 3 else ""
    if len(row) >= 9 and row[4] == "" and row[5] != "" and row[6] != "":
        fn = row[5].strip()
        sn = row[6].strip()
        tr = ", ".join([c.strip() for c in row[7:] if c.strip()])
    else:
        fn = row[4].strip() if len(row) > 4 else ""
        sn = row[5].strip() if len(row) > 5 else ""
        tr = ", ".join([c.strip() for c in row[6:] if c.strip()])
    return st, hn, bldg, fn, sn, tr


def process_single_image(client, model_name, prompt, img_path, out_dir, log_file, max_retries=5):
    base_name = Path(img_path).stem
    out_csv = out_dir / f"{base_name}.csv"
    if out_csv.exists() and out_csv.stat().st_size > 250:
        return True

    for attempt in range(1, max_retries + 1):
        try:
            image = ImageOps.exif_transpose(Image.open(img_path))
            response = client.models.generate_content(
                model=model_name,
                contents=[image, prompt],
                config=types.GenerateContentConfig(
                    max_output_tokens=8192,
                    temperature=0.0,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
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

            out_csv.write_text(csv_content + "\n", encoding="utf-8")
            log(log_file, f"[{base_name}] Processed: extracted {len(lines)} lines.")
            return True
        except Exception as e:
            wait_time = attempt * 5
            log(log_file, f"[{base_name}] Attempt {attempt}/{max_retries} failed: {e}. Backing off {wait_time}s...")
            time.sleep(wait_time)

    log(log_file, f"[{base_name}] ERROR: Failed after {max_retries} attempts.")
    return False


def compile_and_merge(year, out_dir, log_file):
    master_csv = PROJECT_DIR / "volume_csvs" / f"{year}_cleaned.csv"
    all_csvs = sorted(out_dir.glob("IMG_*.csv"))
    log(log_file, f"Compiling {len(all_csvs)} page CSVs for {year} into {master_csv}...")

    total_entries = 0
    total_streets = set()
    current_street = "Unknown"
    new_rows = []

    for page_csv in all_csvs:
        if page_csv.stat().st_size <= 250:
            continue
        with open(page_csv, "r", encoding="utf-8", errors="ignore") as f_in:
            for row in csv.reader(f_in):
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
                    new_rows.append([str(year), st, hn, bldg, sn, fn, tr, ""])
                    total_entries += 1

    with open(master_csv, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"])
        writer.writerows(new_rows)

    log(log_file, f"{year} Compiled: {total_entries:,} residents across {len(total_streets)} streets.")

    if total_entries < 8000:
        log(log_file, f"WARNING: Entry count ({total_entries}) < 8000; skipping auto-merge into data.csv.")
        return

    data_csv = PROJECT_DIR / "data.csv"
    bak_csv = PROJECT_DIR / f"data.csv.bak_before_{year}_merge"
    shutil.copy2(data_csv, bak_csv)

    with open(data_csv, "r", encoding="utf-8-sig", newline="") as f_data:
        reader = csv.reader(f_data)
        header = next(reader)
        keep = [r for r in reader if not (r and r[0] == str(year))]

    with open(data_csv, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(header)
        writer.writerows(keep)
        writer.writerows(new_rows)

    log(log_file, f"Merged {total_entries:,} {year} records into data.csv (backup: {bak_csv.name}).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--model", default="gemini-3.8-flash")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--test-one", action="store_true")
    parser.add_argument("--compile-only", action="store_true")
    args = parser.parse_args()

    year = args.year
    scans_dir = PROJECT_DIR / "original_scans" / f"Johns Directory {year}"
    out_dir = PROJECT_DIR / "scratch" / f"{year}_vision_rebuild"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir = PROJECT_DIR / "log_files"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{year}_vision_reprocess.log"

    if args.compile_only:
        compile_and_merge(year, out_dir, log_file)
        return

    images = sorted(
        list(scans_dir.glob("IMG_*.jpeg"))
        + list(scans_dir.glob("IMG_*.jpg"))
        + list(scans_dir.glob("IMG_*.png"))
    )
    if not images:
        raise FileNotFoundError(f"No scan images found in {scans_dir}")

    client = genai.Client(api_key=get_api_key(), http_options=types.HttpOptions(timeout=90000))
    prompt = PROMPT_TEMPLATE.format(year=year)

    if args.test_one:
        log(log_file, f"Testing 1 image ({images[0].name}) with model {args.model}...")
        ok = process_single_image(client, args.model, prompt, images[0], out_dir, log_file)
        print("Test result:", ok)
        return

    log(log_file, f"=== Starting {year} Vision Extraction: {len(images)} scans ({args.workers} workers, {args.model}) ===")
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(process_single_image, client, args.model, prompt, img, out_dir, log_file)
            for img in images
        ]
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception as e:
                log(log_file, f"Worker exception: {e}")

    log(log_file, f"=== Finished scans for {year}. Compiling and merging... ===")
    compile_and_merge(year, out_dir, log_file)


if __name__ == "__main__":
    main()
