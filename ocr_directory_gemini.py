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
from PIL import Image

def main():
    import re
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = getpass.getpass("Please enter your Gemini API Key: ")
        
    # Strictly strip all newlines, control characters, quotes, and whitespace (preserving dots)
    api_key = re.sub(r'[^a-zA-Z0-9_\-\.]', '', api_key)
    if not api_key:
        print("API Key is required to proceed.")
        sys.exit(1)
    os.environ["GEMINI_API_KEY"] = api_key

    # Initialize the new Google GenAI client (forcing standard Developer API gateway)
    client = genai.Client(
        api_key=api_key,
        http_options={
            'api_version': 'v1beta',
            'base_url': 'https://generativelanguage.googleapis.com'
        }
    )

    image_dir = "/Users/robgale/Documents/Newport Street Directory Project/assets/Johns Directory 1927"
    image_paths = sorted(glob.glob(os.path.join(image_dir, "*.jpeg")) + glob.glob(os.path.join(image_dir, "*.jpg")))

    if not image_paths:
        print(f"No JPEG images found in {image_dir}")
        sys.exit(1)

    print(f"Found {len(image_paths)} images to process.")
    output_tsv = "1927.tsv"
    processed_log = "processed_images_1927.txt"

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
            processed_files = set(line.strip() for line in f if line.strip())

    prompt = """You are an expert OCR transcription assistant specializing in historical street directories.
Transcribe the columns of the directory on this page into a clean tab-separated (TSV) table.

Use exactly these six columns:
Number	Forenames	Surname	Job / Trade	Business / Entity	Layout / Notes

Rules:
1. Output ONLY the raw TSV lines inside a markdown code block starting with ```tsv. No introductory or concluding text.
2. When a new street name header is listed, put it in ALL CAPS on its own line without any tab characters (e.g. "ACACIA AVENUE").
3. For individual resident lines, map them to the TSV columns. Separate the names into Forenames and Surnames.
4. Align business names, trades, and numbers correctly.
5. If there are notes like "(return)", "(left hand side)", or cross-streets like "here is Myrtle-grove", put them in the appropriate column (e.g., Layout/Notes or Job/Trade if it represents a listing note) to match the standard layout.
6. Transcribe the entire page faithfully. Do not skip any lines.
"""

    for i, img_path in enumerate(image_paths, start=1):
        filename = os.path.basename(img_path)
        if filename in processed_files:
            print(f"[{i}/{len(image_paths)}] {filename} already processed. Skipping.")
            continue

        print(f"[{i}/{len(image_paths)}] Processing {filename}...")
        
        try:
            img = Image.open(img_path)
            
            # Resize image if it's too large to save bandwidth and prevent TPM rate limits
            max_size = 1600
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
            
            # Base sleep delay between pages to keep under the 15 RPM rate limit
            time.sleep(6)
        except Exception as e:
            print(f"Error processing {os.path.basename(img_path)}: {e}")
            print("Skipping to next page...")

    print(f"\nProcessing complete! All output saved to {output_tsv}")

if __name__ == "__main__":
    main()
