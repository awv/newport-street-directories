#!/usr/bin/env python3
import json
import os
import time
import urllib.request
import urllib.parse
import ssl

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

if not API_KEY:
    # Optional local fallback / placeholder
    print("Warning: GOOGLE_MAPS_API_KEY environment variable not set.")
MASTER_JSON_PATH = "master_streets.json"
OUTPUT_DIR = "assets/images/streetview"

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def download_streetviews(force=False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(MASTER_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    streets = data.get("streets", {})
    total = len(streets)
    downloaded = 0
    skipped = 0
    failed = 0
    no_coords = 0

    print(f"Starting Street View tune-up download for {total} streets (fov=110, pitch=5, auto-heading, radius=50)...")

    for i, (slug, entry) in enumerate(streets.items(), 1):
        lat = entry.get("latitude")
        lng = entry.get("longitude")
        heading = entry.get("heading")  # Optional override if set in registry

        if not lat or not lng:
            no_coords += 1
            continue

        output_file = os.path.join(OUTPUT_DIR, f"{slug}.jpg")
        
        # Build optimized API URL
        # fov=110 for ultra wide streetscape
        # pitch=5 for building facade tilt
        # radius=50 to snap to clean public road panorama
        # Omit heading=0 so Google automatically faces down the street line unless explicitly set
        url = f"https://maps.googleapis.com/maps/api/streetview?size=640x400&location={lat},{lng}&fov=110&pitch=5&radius=50&key={API_KEY}"
        if heading is not None and str(heading).strip() != "":
            url += f"&heading={heading}"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ssl_context) as response:
                img_data = response.read()
                if len(img_data) > 1000:
                    with open(output_file, "wb") as img_f:
                        img_f.write(img_data)
                    downloaded += 1
                    print(f"[{i}/{total}] Tuned & Saved {slug}.jpg ({len(img_data)} bytes)")
                else:
                    failed += 1
                    print(f"[{i}/{total}] Skipping {slug}: Response too small")
        except Exception as e:
            failed += 1
            print(f"[{i}/{total}] Failed {slug}: {e}")

        time.sleep(0.08)

    print("\n--- Tune-Up Download Complete ---")
    print(f"Downloaded: {downloaded}")
    print(f"No coordinates: {no_coords}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    download_streetviews(force=True)
