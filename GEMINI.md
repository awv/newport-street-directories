# Newport Street Directory Project Guidelines & Memory

This file serves as the memory and guidelines for the Newport Street Directory Project. It preserves the workflows, layout patterns, and cleaning rules discovered during development.

---

## 📋 Project Overview
The project parses, cleans, and builds a web interface for historical street directories of Newport, Wales across various years (e.g., 1878 to 1971).
* **Source Files**: Raw OCR-transcribed TSV files (e.g., `1899.tsv`, `1971.tsv`).
* **Normalized Database**: `data.csv` (contains all cleaned and parsed resident records).
* **Frontend Data**: Compact JSONs in `data/` and `data/streets/` loaded dynamically by the frontend (`index.html`).

---

## 🛠️ Build Pipeline
Whenever CSV cleaning rules or parsed records are modified, run the following pipeline:
```bash
python3 clean_csv.py && python3 build_site_data.py
```
* `clean_csv.py`: Applies global cleaning rules, filters out layout artifacts, runs name/trade normalizations, and merges manually reviewed street name mappings from `streets_review_v17.tsv`.
* `build_site_data.py`: Generates the master street catalog, compact search indexes, and individual JSON files for the website.

---

## ⚠️ Layout & OCR Anomalies (Key Learnings)

### 1. Horizontal Column Merging (Drifts)
Historical directories were printed in multi-column formats. The OCR transcribes them horizontally row-by-row, which causes:
* **Name/Trade Merging**: Surnames/forenames from different columns get combined (e.g., `5-11 Thomas Bishop` instead of `5 Bishop` and `11 Thomas`).
* **Street Header Drift**: Missing column headers cause residents from subsequent columns to drift under the active street.
* **Landmarks drifting**: Landmark names or cross-street descriptions (e.g., `"Corporation-road to Riverside"`) get misparsed into the `building_name` or `trade` fields of actual residents.

### 2. Fake Street Names
OCR often transcribes layout text, running page headers, or cross-street directions as standalone street names.
* **Global Filter**: `clean_record` in `clean_csv.py` filters out names starting with `here is`, `rt.-hand`, `lt.-hand`, containing `street list`, or indicating cross-street directions like `road to`.

### 3. Hardcoded Unpacking & Bypasses
For extremely distorted/complex layout anomalies, use direct array/dict injection block in `clean_csv.py` to bypass OCR errors cleanly:
* **1886 Crindau Gas Works**: Manually unpacked run-on trade fields.
* **1899 Crindau Road**: Replaced with 100% hand-verified clean records to eliminate column-merging remnants (`5-11`, `23`, `52`, `8`).
* **1971 Crindau Road**: Restricted to properties 1–14 to remove Cromwell Road's drifted listings.

---

## 🌐 Local Development & Cache
* Frontend assets are served at `http://127.0.0.1:5500/`.
* Since data is loaded via `fetch` requests, browsers cache the JSON files aggressively. **Always perform a hard reload (`Cmd+Shift+R` or empty caches)** when verifying database cleanups.
