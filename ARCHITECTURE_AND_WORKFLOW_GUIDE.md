# Newport Street Directory Project: Architecture, Pipeline & Workflow Guide

This document is a comprehensive guide to the **Newport Street Directory Archive** codebase, data pipeline, normalization rules, and web application architecture. It serves as a persistent technical manual for future maintainers and agentic pair-programmers.

---

## 1. Project Architecture Overview

The **Newport Street Directory Archive** is a high-performance, static, client-rendered web application designed to explore, search, and visualize historical resident and business directory data for Newport, South Wales spanning 1876–1971.

```mermaid
flowchart TD
    A["Original Scans (/original_scans)"] -->|Gemini Flash Vision OCR| B["Raw TSV Files (1882.tsv, 1900.tsv...)"]
    B -->|Volume Parsers (parse_YYYY.py)| C["Clean Volume CSVs (1882_cleaned.csv...)"]
    C -->|Merger Scripts (merge_YYYY.py)| D["Master CSV (data.csv)"]
    D -->|Global Normalizer (clean_csv.py)| D
    D -->|Site Builder (build_site_data.py)| E["Public Site Data (/data)"]
    E -->|Static Fetch| F["Web App (index.html)"]
    G["Web UI Editor (Cmd+Shift+E)"] -->|Export JSON Overrides| H["merge_overrides.py"]
    H -->|Append Rule| I["edge_cases.json"]
    I -->|Override Filter| D
```

---

## 2. Directory Layout & Key Files

| Path / File | Purpose & Description |
| :--- | :--- |
| **`index.html`** | Single Page Application (SPA) built with Vanilla HTML5, CSS3, and JavaScript. Features interactive timelines, house modals, global search, and built-in editor mode. |
| **`data.csv`** | The authoritative master CSV containing **209,000+ historical records** across all imported directory years. |
| **`edge_cases.json`** | Persistent rule store for manual data overrides, exclusions, and layout fixes exported from the Web Editor. |
| **`clean_csv.py`** | Global normalization engine. Standardizes street names, cleans trades, resolves casing, applies `edge_cases.json` overrides, and generates `streets_review_v17.tsv`. |
| **`build_site_data.py`** | Compiles `data.csv` into individual street JSON files (`/data/streets/*.json`), master street index (`/data/streets.json`), and global search index (`/data/search_index.json`). Includes `MAX_PUBLIC_YEAR` filter. |
| **`merge_overrides.py`** | CLI tool that ingests user-exported `user_overrides.json` files, appends new rules to `edge_cases.json`, and triggers a clean dataset rebuild. |
| **`ocr_directory_gemini.py`** | Automated vision-based OCR pipeline utilizing the Google Gemini API to transcribe scanned JPEG pages into 6-column raw TSV files. |
| **`parse_YYYY.py`** | Volume-specific python parsers tuned to extract records from raw TSVs, handling single-column vs 3-column printed layouts, title case headers, and sub-units. |
| **`merge_YYYY.py`** | Merges cleaned volume CSVs into `data.csv` while safely purging older revisions of that specific year to prevent duplicate accumulation. |
| **`RECORD_CORRECTION_GUIDE.md`** | Quick-reference manual for UI-based editing, schema specifications, and override file merging. |

---

## 3. Data Pipeline & Normalization Rules

### A. The 100-Year Rolling Window Policy (Newport Library Agreement)
Per agreement with Newport Library, public web builds restrict accessible directory records to **100 years old or older** ($\le 1925$).
- Controlled via `MAX_PUBLIC_YEAR = 1925` in `build_site_data.py`.
- Raw data for post-1925 years (1927, 1936, 1971) remains safe in `data.csv` for private local research.
- Annual rollover: When a new year reaches the 100-year mark (e.g. 1926 in 2027), incrementing `MAX_PUBLIC_YEAR` releases that year in a single build step.

### B. Distinguishing Sub-districts (e.g., High Street vs High Street, Pill)
In early Newport directories, town center streets and Pillgwenlly (Pill) streets share identical base names:
- **`clean_csv.py`** enforces strict distinction:
  - Header variants like `High Street, Pill`, `High Street, Pillgwenlly`, `HIGH STREET, P.` are protected from comma-stripping and map cleanly to **`High Street, Pill`** (`high-street-pill.json`).
  - Town center headers map to **`High Street`** (`high-street.json`).

### C. Standard Street Name Normalization (`clean_street_name`)
`clean_csv.py` applies a deterministic 6-stage cleanup:
1. **District Code Stripping**: Removes trailing district codes (e.g., `.T`, `.P`, `.M`, `.C`).
2. **Grid Reference Stripping**: Removes trailing grid refs (e.g., `. E 5`, ` B 4`).
3. **Saint Standardization**: Normalizes `Street Saint...` $\rightarrow$ `St. ...` (e.g., `St. Mark's Crescent`).
4. **Possessive Apostrophes**: Fixes possessives like `' S` or `'S` $\rightarrow$ `'s`.
5. **Abbreviation Expansion**: Expands common abbreviations (`Rd.` $\rightarrow$ `Road`, `St.` $\rightarrow$ `Street`, `Ter.` $\rightarrow$ `Terrace`, `Ave.` $\rightarrow$ `Avenue`).
6. **Alias & Typo Map**: Hardcoded `street_map` dictionary that maps OCR fragments, paid ad headers, chapel/school headers, and OCR typos directly to their authentic master street names.

---

## 4. Multi-Column TSV Parsing Logic (`parse_1882.py` / `parse_1913.py`)

Historical volumes frequently switch between 1-column and 3-column side-by-side vertical page printing.
- **3-Column TSV Layout Unpacking**: `parse_1882.py` splits each raw TSV line into 3-cell column chunks (`[house_num, surname, forename/trade/building]`) before extracting records.
- **Fused Building/Hotel Extraction**: Handles fused building names like `Hy. Bridgehotel` by splitting into:
  - `house_number`: `"1"`
  - `surname`: `"Duckham"`
  - `forename`: `"Hy."`
  - `building_name`: `"Bridge Hotel"`

### C. Master Street Registry & Verification Locks (`master_streets.json`)
The project maintains a 2-tier **Master Street Registry** (`master_streets.json`) tracking all 900+ historical streets.
- **Audit Lock Status**: Streets can be flagged as `"status": "VERIFIED"` (locked) or `"status": "UNVERIFIED"` (raw/unreviewed).
- **Automated Protection**: When a street is flagged as `VERIFIED`, python cleanup scripts (`clean_csv.py` and `build_site_data.py`) preserve all manually assigned canonical names, former names, sub-sections, and numbering schemes without overwriting them during global automated regex sweeps.
- **Master Street Schema**:
  ```json
  "jackson-place": {
    "canonical_name": "Jackson Place",
    "slug": "jackson-place",
    "district": "Baneswell",
    "parish": "St. Woolos",
    "former_names": ["Jackson's Row"],
    "sub_sections": ["Victoria Terrace"],
    "numbering_scheme": { "type": "ODDS_EVENS", "approx_change_year": 1895 },
    "coordinates": { "lat": 51.5882, "lng": -2.9977 },
    "audit": { "status": "VERIFIED", "notes": "Verified against 1891 OS Map" }
  }
  ```

---

## 6. Web Application Architecture (`index.html`)

### A. SPA Hash Navigation & Routing
Navigation is driven by URL fragment hashes:
- **`#home`**: Master home search view with quick pills and site stats.
- **`#streets`**: All Streets index featuring the **Master Street Audit Dashboard** (with filters for `All`, `🔒 Verified`, and `⚠️ Unverified`).
- **`#street={StreetName}`**: Street profile view with history notes, sub-terrace groupings, house list, and timeline.
- **`#house={StreetName}%7C{HouseNumber}`**: Detailed property modal showing all historical residents across all directory years.
- **`#trades`**: Interactive occupation audit page categorizing historic trades.

### B. Interactive Editor Mode & Master Street Audit
- **Toggle Editor Mode**: Press **`Cmd + Shift + E`** (Mac) or **`Ctrl + Shift + E`** (Windows) to enable/disable Editor Mode.
- **Master Registry Modal**: Clicking **`🏛️ Registry Settings`** on any street page allows live editing of canonical names, audit lock status, former street names, sub-sections, numbering schemes, and pinpoint coordinates (`lat` / `lng`).
- **Batch CSV Export & Import Workflow**:
  - Click **`📥 Export Master CSV`** on the `#streets` page to download a complete spreadsheet containing all 901 historical street entries.
  - Edit the CSV in Excel, Google Sheets, or a text editor.
  - Click **`📤 Import Master CSV`** to re-upload the spreadsheet. All changes immediately populate into your active session queue for review and commit.
- **Persistence & Merging**: Session edits are saved in browser `localStorage`. Clicking **`📥 Download user_overrides.json`** exports edits for python ingestion into `edge_cases.json` and `master_streets.json`.

---

## 6. Standard Data Import Workflow (Adding a New Volume)

To import a new scanned directory volume (e.g., Year `YYYY`):

1. **OCR Processing**:
   ```bash
   python3 ocr_directory_gemini.py
   ```
   *Generates `YYYY.tsv` in root.*

2. **Parser Creation**:
   - Create `parse_YYYY.py` based on `parse_1882.py` or `parse_1900.py`.
   - Run `python3 parse_YYYY.py` to produce `YYYY_cleaned.csv`.

3. **Merger Creation**:
   - Create `merge_YYYY.py` to purge old `YYYY` records from `data.csv` and append `YYYY_cleaned.csv`.
   - Run `python3 merge_YYYY.py`.

4. **Global Rebuild**:
   ```bash
   python3 clean_csv.py && python3 build_site_data.py
   ```

5. **Verification & Git Commit**:
   - Verify on local dev server (`http://127.0.0.1:5500`).
   - Commit changes and push to `main` branch on GitHub.
