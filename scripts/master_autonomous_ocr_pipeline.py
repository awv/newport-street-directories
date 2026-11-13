#!/usr/bin/env python3
"""
master_autonomous_ocr_pipeline.py
Autonomous end-to-end OCR ingestion, gap recovery, volume rebuilding, 
and stats regeneration across the Newport Street Directory archive.
"""

import os
import sys
import glob
import time
import json
import subprocess
from PIL import Image

PROJECT_DIR = "/Users/robgale/Documents/Newport Street Directory Project"
os.chdir(PROJECT_DIR)

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
    print("ERROR: GEMINI_API_KEY not found in environment or .env!")
    sys.exit(1)

os.environ["GEMINI_API_KEY"] = api_key

from google import genai

client = genai.Client(api_key=api_key)

OCR_PROMPT = """You are an expert archive researcher and transcript specialist digitizing historical British trade and street directories (1835-1971).

Your task is to transcribe the attached image with 100% verbatim accuracy into a structured table.

CRITICAL RULES:
1. Extract entries sequentially line-by-line exactly as printed on the page.
2. For street directories, maintain columns:
   Number\tForenames\tSurname\tJob / Trade\tBusiness / Entity\tLayout / Notes
3. If an entry is an alphabetical commercial/trade listing (common in 1835-1865 directories), extract:
   Resident or Business Name in Surname/Forenames, the trade in Job / Trade, the street/address in Layout / Notes.
4. House numbers MUST stay in Number. Surnames in Surname. Trades in Job / Trade.
5. Capture junctions ("here is Commercial-street") or headings in Layout / Notes.
6. Do NOT invent data. Transcribe top-to-bottom, column by column.

Return ONLY the TSV rows (or markdown code block with TSV rows) with NO commentary:
Number\tForenames\tSurname\tJob / Trade\tBusiness / Entity\tLayout / Notes
"""

def ocr_single_image(img_path, output_tsv, log_file):
    filename = os.path.basename(img_path)
    print(f"  [OCR] Processing {filename} -> {os.path.basename(output_tsv)}...")
    
    # Check if already processed
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as lf:
            logged = {l.strip() for l in lf if l.strip()}
        if filename in logged:
            print(f"  [SKIP] {filename} already processed.")
            return True

    try:
        pil_img = Image.open(img_path)
        # Convert RGBA/P to RGB if necessary
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        # Call Gemini Vision Model
        response = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents=[pil_img, OCR_PROMPT]
        )
        text = response.text or ""
        
        # Extract TSV lines
        lines = []
        in_block = False
        for line in text.splitlines():
            if line.strip().startswith("```"):
                in_block = not in_block
                continue
            if line.strip():
                if line.startswith("Number\tForenames"):
                    continue
                lines.append(line)

        # Write to TSV
        os.makedirs(os.path.dirname(output_tsv), exist_ok=True)
        if not os.path.exists(output_tsv) or os.path.getsize(output_tsv) == 0:
            with open(output_tsv, "w", encoding="utf-8") as out:
                out.write("Number\tForenames\tSurname\tJob / Trade\tBusiness / Entity\tLayout / Notes\n")

        with open(output_tsv, "a", encoding="utf-8") as out:
            for l in lines:
                out.write(l + "\n")

        # Log completion
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(filename + "\n")

        print(f"  [SUCCESS] {filename}: transcribed {len(lines)} rows.")
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"  [ERROR] Failed {filename}: {e}")
        return False

def run_early_directories():
    print("\n" + "="*70)
    print("STEP 1: INGESTING EARLY DIRECTORIES (1835-1865)")
    print("="*70)
    early_dirs = [
        ("1835", "Pigot's Directory 1835 Original"),
        ("1844", "Pigot's Monmouthshire Directory  1844"),
        ("1850", "Slater Monmouthshire 1850"),
        ("1858", "Slater Monmouthshire Directory 1858-59"),
        ("1862", "Morris Directory of Monmouthshire 1862"),
        ("1865", "Websters Postal and Commercial Directory 1865")
    ]
    for year, folder_name in early_dirs:
        folder_path = os.path.join(PROJECT_DIR, "original_scans", folder_name)
        if not os.path.exists(folder_path):
            print(f"Directory not found: {folder_path}")
            continue
        imgs = sorted(glob.glob(os.path.join(folder_path, "*.jpeg")) + glob.glob(os.path.join(folder_path, "*.jpg")) + glob.glob(os.path.join(folder_path, "*.png")))
        print(f"\nProcessing {folder_name} ({len(imgs)} scans)...")
        output_tsv = os.path.join(PROJECT_DIR, "raw_tsvs", f"{year}.tsv")
        log_file = os.path.join(PROJECT_DIR, "log_files", f"processed_images_{year}.txt")
        
        for img in imgs:
            ocr_single_image(img, output_tsv, log_file)

def run_missing_gaps():
    print("\n" + "="*70)
    print("STEP 2: INGESTING MISSING GAPS IN JOHNS DIRECTORIES")
    print("="*70)
    # 1903 gaps
    p1903 = os.path.join(PROJECT_DIR, "original_scans", "Johns Directory 1903")
    for fname in ['IMG_6915-0.jpeg', 'IMG_6915-1.jpeg', 'IMG_6915-2.jpeg']:
        fpath = os.path.join(p1903, fname)
        if os.path.exists(fpath):
            ocr_single_image(fpath, os.path.join(PROJECT_DIR, "raw_tsvs", "1903.tsv"), os.path.join(PROJECT_DIR, "log_files", "processed_images_1903.txt"))

    # 1927 gaps
    p1927 = os.path.join(PROJECT_DIR, "original_scans", "Johns Directory 1927")
    for fname in ['IMG_4493.jpeg', 'IMG_4565.jpeg']:
        fpath = os.path.join(p1927, fname)
        if os.path.exists(fpath):
            ocr_single_image(fpath, os.path.join(PROJECT_DIR, "raw_tsvs", "1927.tsv"), os.path.join(PROJECT_DIR, "log_files", "processed_images_1927.txt"))

def rebuild_and_verify():
    print("\n" + "="*70)
    print("STEP 3: REBUILDING PIPELINE & FRONTEND ASSETS")
    print("="*70)
    
    # 1. Run merge casing twins
    print("Merging casing twin trades...")
    subprocess.run([sys.executable, "scripts/merge_casing_twins.py"], check=False)
    
    # 2. Run build stats data
    print("Compiling analytics and diagnostics dashboard (build_stats_data.py)...")
    subprocess.run([sys.executable, "scripts/build_stats_data.py"], check=False)
    
    print("\nMaster pipeline executed successfully!")

if __name__ == "__main__":
    run_early_directories()
    run_missing_gaps()
    rebuild_and_verify()
