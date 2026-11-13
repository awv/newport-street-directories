import os
import sys
import glob
import time
import getpass

def install_and_import(package_name, import_name=None):
    if import_name is None:
        import_name = package_name
    import importlib
    try:
        importlib.import_module(import_name)
    except ImportError:
        import subprocess
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

# Ensure unified new google-genai library and pillow are installed
install_and_import("google-genai", "google.genai")
install_and_import("pillow", "PIL")

from google import genai
from PIL import Image, ImageOps

def main():
    import re
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as ef:
                for line in ef:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("GEMINI_API_KEY=", 1)[1].strip()
                        break
    if not api_key:
        api_key = getpass.getpass("Please enter your Gemini API Key: ")
        
    # Strictly strip all newlines, control characters, quotes, and whitespace (preserving dots)
    api_key = re.sub(r'[^a-zA-Z0-9_\-\.]', '', api_key)
    if not api_key:
        print("API Key is required to proceed.")
        sys.exit(1)
    os.environ["GEMINI_API_KEY"] = api_key

    client = genai.Client(api_key=api_key)

    year = sys.argv[1] if len(sys.argv) > 1 else "1915"
    possible_dirs = [
        f"/Users/robgale/Documents/Newport Street Directory Project/original_scans/Johns Directory {year}",
        f"/Users/robgale/Documents/Newport Street Directory Project/original_scans/John's Directory {year}",
        f"original_scans/Johns Directory {year}",
        f"original_scans/John's Directory {year}"
    ]
    image_dir = None
    for p in possible_dirs:
        if os.path.exists(p):
            image_dir = p
            break
    if not image_dir:
        image_dir = possible_dirs[0]

    image_paths = sorted(glob.glob(os.path.join(image_dir, "*.jpeg")) + glob.glob(os.path.join(image_dir, "*.jpg")) + glob.glob(os.path.join(image_dir, "*.png")))

    if not image_paths:
        print(f"No JPEG/PNG images found in {image_dir}")
        sys.exit(1)

    print(f"Directory {year}: Found {len(image_paths)} images to process in {image_dir}.")
    os.makedirs("raw_tsvs", exist_ok=True)
    os.makedirs("log_files", exist_ok=True)
    output_tsv = f"raw_tsvs/{year}.tsv"
    processed_log = f"log_files/processed_images_{year}.txt"

    # Header for the TSV
    header = "Number\tForenames\tSurname\tJob / Trade\tBusiness / Entity\tLayout / Notes\n"
    
    # If the file doesn't exist or is empty, write the header
    if not os.path.exists(output_tsv) or os.path.getsize(output_tsv) == 0:
        with open(output_tsv, "w", encoding="utf-8") as f:
            f.write(header)

    # Load processed images to enable resuming
    processed_files = set()
    if os.path.exists(processed_log):
        with open(processed_log, "r", encoding="utf-8") as f:
            processed_files = {line.strip() for line in f if line.strip()}

    prompt = """
You are an expert OCR transcription assistant. Your task is to transcribe the attached image of a historical Newport Street Directory page.

CRITICAL HOUSE NUMBER RULE:
- WARNING: These house numbers are often printed in a very narrow column right up against the vertical dividing lines or deep into the gutter.
- You MUST capture these numbers and put them in the 'Number' column. Do NOT skip them, and do NOT merge them into the surname. They are critical!

CRITICAL TIGHT BINDING, CURVED TEXT & ANGLE RULE:
- The physical book has tight binding causing the page to curve sharply into the inner margin/gutter, and some pages are held or photographed at a slight angle.
- Text, house numbers, or initials near the curved inner edge may appear compressed, warped, or angled into the shadow of the binding.
- Follow the angled baseline of each text line naturally across the columns. Take extra care to look deep into the curve and transcribe every house number, surname, and forename completely. Do NOT truncate or skip text where the page bends or angles into the gutter.

CRITICAL PAPER GLARE & REFLECTION RULE:
- The paper in this volume is semi-glossy/shiny, so some pages exhibit bright specular glare reflections or light washouts.
- You MUST examine faint ink shapes, character strokes, and surrounding context visible through or around the glare reflections to transcribe the text accurately and completely. Do NOT skip or omit lines because of glare.

CRITICAL STREET PREFIX RULE ("UP." -> "UPPER"):
- Whenever a street heading contains "Up." or "Up " (e.g. "UP. LEWIS STREET", "UP. DOCK STREET", "UP. GEORGE STREET"), you MUST ALWAYS expand "Up." to "UPPER " (e.g. "UPPER LEWIS STREET", "UPPER DOCK STREET", "UPPER GEORGE STREET"). Never leave it as "Up.".

CRITICAL LAYOUT RULE:
The directory page is printed in side-by-side vertical columns (typically TWO columns in this era, or three depending on the volume).
You MUST transcribe each column top-to-bottom from left to right (transcribe Column 1 first completely top-to-bottom, then Column 2 top-to-bottom) so they form a single continuous list of rows.
Do NOT merge side-by-side column entries into the same row. Each resident/listing must be on its own separate row.
Do NOT append any extra columns, labels, or indicators like "Left Column", "Right Column", or "Column 1" to the rows.

CRITICAL CROSSED-OUT TEXT RULE:
- Some entries or whole sections of text might have been crossed out or marked through in pencil (light or dark gray lines).
- You MUST still transcribe these crossed-out entries exactly as they were printed. Do NOT skip or ignore text because it has a pencil line drawn through it.

CRITICAL INK SMUDGE RULE:
- Some pages contain ink splatters, blots, or smudges.
- You MUST make every effort to read the text under or around the ink smudges and transcribe it completely.
- Do NOT skip or omit lines just because they have ink on them. Use the surrounding context and faint visible shapes to transcribe them accurately.

Use exactly these six columns:
Number	Forenames	Surname	Job / Trade	Business / Entity	Layout / Notes

Special Instructions for Paid Advertisements:
- This directory contains random "paid advertisements" in larger bold font with descriptions inline (e.g. "WILDINGS LIMITED", "CAINES (NEWPORT) LTD").
- Treat them as normal resident listings at their respective street numbers.
- Map the business name (e.g., "Wildings Limited", "Reynolds of Newport") to the 'Business / Entity' column.
- Map the main description/trade (e.g., "departmental store", "outfitters") to the 'Job / Trade' column.
- Put any extra info or extended blurbs into the 'Layout / Notes' column, but **omit telephone numbers entirely** (do not transcribe references like "Tel. 62861" or "Telephone, Newport 64897/8").

Special Instructions for Flats & Sub-units:
- If a listing features a flat number next to the house number (e.g. "568 (flat 11) Lowe S. E"), put the base house number (e.g., "568") in the 'Number' column, and put the flat name (e.g., "Flat 11") in the 'Business / Entity' column.

General Rules:
1. Output ONLY the raw TSV lines inside a markdown code block starting with ```tsv. No introductory or concluding text.
2. CRITICAL TAB DELIMITER RULE: Ensure EVERY single data row uses strict TAB characters ('\t') to separate the 6 columns: Number<tab>Forenames<tab>Surname<tab>Job / Trade<tab>Business / Entity<tab>Layout / Notes. Do NOT merge fields using spaces.
3. When a new street name header is listed, put it in ALL CAPS on its own line without any tab characters (e.g. "ACACIA AVENUE").
4. Street Name Prefixes: Expand abbreviations in street names such as "Up." to "UPPER " (e.g. "UP. LEWIS STREET" -> "UPPER LEWIS STREET", "UP. DOCK STREET" -> "UPPER DOCK STREET").
5. Area Markers: Ignore and omit random area markers like "P.", "B.T.", "(P.)", or "(B.T.)" attached to street headings (e.g., "WOLSELEY STREET, P." -> "WOLSELEY STREET").
6. Separate Districts (e.g. Maindee): If a section begins with a district header like "MAINDEE" or "MAINDEE STREET LIST", do NOT treat "MAINDEE" as a street name. Simply transcribe each individual street within that section under its own ALL CAPS header (e.g. "ALBERT AVENUE", "CHEPSTOW ROAD").
7. For individual resident lines, map them to the TSV columns. Separate the names into Forenames and Surnames.
8. Align business names, trades, and numbers correctly.
9. Transcribe the entire page faithfully. Do not skip any lines.
"""

    for i, img_path in enumerate(image_paths, start=1):
        filename = os.path.basename(img_path)
        if filename in processed_files:
            print(f"[{i}/{len(image_paths)}] {filename} already processed. Skipping.")
            continue

        print(f"[{i}/{len(image_paths)}] Processing {filename}...")
        
        try:
            img = Image.open(img_path)
            # Correct orientation from EXIF before resizing
            img = ImageOps.exif_transpose(img)
            
            # Resize image if it's too large to save bandwidth and prevent TPM rate limits
            max_size = 2000
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                print(f"  Resized image to {img.size[0]}x{img.size[1]} for token efficiency")
            
            # Retry loop with exponential backoff for handling rate limits (429)
            max_retries = 8
            backoff_delay = 10
            response = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    response = client.models.generate_content(
                        model='gemini-flash-lite-latest',
                        contents=[img, prompt]
                    )
                    break # Success! Break out of the retry loop.
                except Exception as e:
                    # Check if it is a 429 rate limit or 503 temporary server error
                    err_str = str(e).lower()
                    if "429" in err_str or "503" in err_str or "exhausted" in err_str or "limit" in err_str or "unavailable" in err_str:
                        print(f"  [Temporary Error/Rate Limited] Spikes in demand or rate limit. Attempt {attempt}/{max_retries}. Waiting {backoff_delay} seconds...")
                        time.sleep(backoff_delay)
                        backoff_delay = min(backoff_delay * 2, 120) # Exponential backoff capped at 2 minutes
                    else:
                        raise e # Re-raise if it's not a retryable error
            
            if response is None:
                print(f"Error: Failed to process {filename} after {max_retries} attempts due to rate limits.")
                print("Stopping execution to prevent gaps in the TSV. Please run the script again to resume.")
                sys.exit(1)
                
            text = response.text
            
            # Extract the TSV code block content
            tsv_lines = []
            in_code_block = False
            for line in text.splitlines():
                if line.strip().startswith("```tsv"):
                    in_code_block = True
                    continue
                elif line.strip().startswith("```") and in_code_block:
                    in_code_block = False
                    continue
                
                if in_code_block:
                    tsv_lines.append(line)
            
            # If no code block found, fall back to clean text lines that don't look like markdown
            if not tsv_lines:
                tsv_lines = [l for l in text.splitlines() if not l.strip().startswith("```")]

            # Append the TSV lines to the output file
            cleaned_lines = []
            for line in tsv_lines:
                # Strip the header if it got generated by the model again
                if line.startswith("Number\tForenames"):
                    continue
                if line.strip():
                    cleaned_lines.append(line)

            with open(output_tsv, "a", encoding="utf-8") as f:
                for line in cleaned_lines:
                    f.write(line + "\n")
            
            # Record progress
            with open(processed_log, "a", encoding="utf-8") as f:
                f.write(filename + "\n")
            processed_files.add(filename)
                    
            print(f"Successfully appended {len(cleaned_lines)} lines from {filename}")
            
            # Base sleep delay between pages (practically instant on paid tier)
            time.sleep(0.2)
        except Exception as e:
            print(f"Error processing {os.path.basename(img_path)}: {e}")
            print("Skipping to next page...")

    print(f"\nProcessing complete! All output saved to {output_tsv}")

if __name__ == "__main__":
    main()
