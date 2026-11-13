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

---

## ⚡ Recent UI & Data Pipeline Enhancements (Sep 2026)

### 1. Occupations Audit (`trades.html`) & Record Inspector Modal
* **Person Links & Record Inspector**: Clicking any sample person's name on `trades.html` opens the **Record Inspector Modal** showing full entry metadata (Year, Street, House No, Building Name, Forename, Surname, Raw Occupation).
* **Single-Record vs Bulk Rules**:
  * **`✏️ Edit This Entry Only`**: Updates the occupation for *that specific person's record* (`single:year:street:house:forename:surname:trade`), bypassing bulk rules without affecting other records sharing the same raw trade title.
  * **`Edit Rule`**: Updates canonical mapping across *all* matching raw entries in the dataset.
* **Original Scan & Timeline Cross-Linking**: Includes direct launchers for `openScanInspectorModal(...)` (view printed directory scan page) and `index.html#house=...` (property timeline view).

### 2. High-Performance Live Search & DOM Rendering
* **Search Autocomplete Debouncing & Capping**: Live search input in `src/js/app.js` is debounced to 300ms, and search loop iterations across the 129,000-entry `search_index.json` cap at 200 items per category for near-instant rendering without UI lag.
* **DocumentFragment Batching**: `trades.html` renders all ~1,000+ occupation rows offscreen in memory using a `DocumentFragment`, preventing layout thrashing and reflow bottlenecks.
* **Standalone Page Guards**: `app.js` event listeners check for `#street-nav` before initializing SPA routing, allowing standalone pages like `trades.html` to run cleanly without `TypeError` exceptions.

### 3. OCR Street Name Header Spillover Fixes
* **Risca Road / "39 Prosser T"**: Reassigned 1898 records where house #39 (*"39 Prosser T. M., Clytha view"*) was OCR-parsed into the street column.
* **Dewstow Street / Dock Street**: Reassigned 24 records from 1925 where *DOCK (THE TOWN)* page headers spilled under *Dewstow Street*.
* **Commercial Road / Post Office Header**: Reassigned 62 records from 1920 where the header *"COMMERCIAL ROAD POST OFFICE..."* was misparsed as a street name.

---

## 🛠️ Occupations & Trade Data Pipeline (October 2026)

### 1. Split Trades & Fragment Repair (`scripts/fix_split_trades.py`)
Addresses historical OCR and column alignment failures where occupational words were split across `forename`, `surname`, and `trade` columns:
* **Prefix / Fragment Splicing**: Repairs prefixes severed by OCR whitespace (e.g. `Ca / rpenter`, `Dr / aper`, `Ha / ulier`).
* **1936 'Co' Surname Anomaly**: In the 1936 directory, company/trade names spilled into `surname` with trailing `Co` while `forename` was left empty. Normalized surname, forename, and trade cleanly.
* **Building & Villa Name Extraction**: Identified house and villa names erroneously placed in the `trade` column and relocated them to `building_name`.
* **Dynamic Fragment Reconciliation**: Employs English dictionary vocabulary, occupational suffixes (`-maker`, `-worker`, `-driver`, `-smith`), and historical Newport trade glossaries.

### 2. Embedded House Numbers in Trades (Section 8 of `fix_split_trades.py`)
In multi-column directories (notably 1915 double-column layouts, and selected 1882–1927 directories), horizontal OCR scanning caused house numbers to bleed into the trade column:
* **Preserving Valid House Numbers (496+ records)**: When a resident already has their true house number in `house_number` (e.g. `44 Neale Aldwyn | eng driver, 14` on Walford Street 1915), the trailing number is an adjacent column bleed. Strip the trailing number and canonicalize the occupation (`Engine Driver`) without overwriting the resident's valid house number (`44`).
* **Populating Empty House Numbers (54 records)**: When `house_number` is blank and a leading/trailing number is attached to a recognized trade (e.g. `grocer 74` or `30, draper`), move the number into `house_number` and clean the trade.
* **Regex Patterns Used**:
  * `pat_comma_lead`: `^(\d+[a-zA-Z]?),\s*(.+)$` (e.g., `3, Labourer`)
  * `pat_comma_trail`: `^(.+?),\s*(\d+[a-zA-Z]?)$` (e.g., `eng driver, 14`)
  * `pat_sep_trail`: `^([a-zA-Z\s\.\'\-]+?)[\s\-]+(\d+[a-zA-Z]?)$` (e.g., `grocer 74`, `ironworker-24`)
  * `pat_attached_trail`: `^([a-zA-Z\s\.\'\-]+?)(\d+[a-zA-Z]?)$` (e.g., `ironworker21`, `labourer37`)
* **Trade Normalization Map**: Historical abbreviations (`eng driver`, `eng dvr`, `labr`, `boilermkr`, `shoeng smth`, `ironwkr`, `fitter`, `platelyr`, etc.) are mapped to canonical title-cased occupations.

### 3. Casing Twin Deduplication (`scripts/merge_casing_twins.py`)
* Automatically detects trade variants that differ only by case (e.g., `stone mason` vs `Stone Mason`, `Physician and Surgeon` vs `Physician And Surgeon`).
* Merges to the dominant canonical form across `data.csv`, bringing casing variant twins down to **0**.

### 4. Occupations Audit Verification & Import Workflows
* **Export / Import Loop**: Verifications and manual corrections performed in `trades.html` can be exported via **Export All** and ingested into `data.csv` via `scripts/apply_trade_audit.py`.
* **Auto-Cleanup**: Import script cleans up the exported JSON audit file once applied.
* **Standard Rebuild Pipeline**:
  ```bash
  python3 scripts/fix_split_trades.py
  python3 scripts/merge_casing_twins.py
  ```
  *(Automatically rebuilds `data/trades.json`, `data/streets/*.json`, and `data/search_index.json`)*.

---

## 📚 Johns Directory 1924 Ingestion (October 2026)
* **Raw Transcription**: `raw_tsvs/1924.tsv` generated from 135 scan pages via `scripts/ocr_directory_gemini.py 1924`.
* **Parser (`scripts/parse_1924.py`)**:
  * **Recurring Page Banner Rejections**: Filtered recurring margin banner advertisements (`HERBERT EDWARDS LTD`, `THE NEWPORT STEAM LAUNDRY`, `FRANCIS' DYE WORKS`, `FOR CARPET BEATING...`, `BOY SCOUTS OUTFITTERS`).
  * **Page 398 Multi-Column Unpacking**: Explicitly unpacked page 398's 3 side-by-side columns into clean listings for `Charles Street`, `Charlotte Street`, `Chelston Place`, and `Chepstow Road`.
  * **Typo Standardizations**: Corrected OCR street typos such as `Wednesday Street` $\rightarrow$ `Wednesbury Street` (confirmed via 1920/1925 resident matches like Stephen Cheadle at No. 2), `Camperdown St` $\rightarrow$ `Camperdown Street`, `Fair Oak Terrace` $\rightarrow$ `Fairoak Terrace`, etc.
* **Master Merge (`scripts/merge_1924.py`)**:
  * Added **18,841 clean resident records** to `data.csv` (bringing master count to 286,886).
  * Executed `fix_split_trades.py` and `merge_casing_twins.py` to canonicalize occupations and retain **0 casing twins**.

---

## 📚 Johns Directory 1892 Ingestion (October 2026)
* **Raw Transcription**: `raw_tsvs/1892.tsv` generated from 77 scan pages via `scripts/ocr_directory_gemini.py 1892`.
  * Enhanced with `ImageOps.exif_transpose` for portrait orientation correction.
  * Increased resolution ceiling (`max_size = 2000`) and added tight-binding curvature prompt directives.
  * Preserved `Up.` $\rightarrow$ `Upper` street name prefix expansion across all headings.
* **Parser (`scripts/parse_1892.py`)**:
  * Cleaned 2-column columnar layout mapping Forenames (`col1`), Surnames (`col2`), and Trades (`col3`).
  * Converted titles (`Rev`, `Mrs`, `Miss`, `Dr`) where forenames appeared in trade column.
  * Filtered out banner ads (`Trapnell & Gane`).
  * Standardized all street names (expanding `Up.` to `Upper`, e.g. `Upper Marion Street`, `Upper Lime Street`).
* **Master Merge (`scripts/merge_1892.py`)**:
  * Added **9,824 clean resident records** to `data.csv` (bringing master count to 296,710).
  * Executed `fix_split_trades.py` and `merge_casing_twins.py` to canonicalize occupations and retain **0 casing twins**.

---

## 📚 Johns Directory 1895 Ingestion (October 2026)
* **Raw Transcription**: `raw_tsvs/1895.tsv` generated from 85 scan pages via `scripts/ocr_directory_gemini.py 1895`.
  * Applied tight binding curvature rules, paper glare / specular reflection handling, portrait orientation transposition, and `Up.` $\rightarrow$ `Upper` expansion.
* **Parser (`scripts/parse_1895.py`)**:
  * Mapped columns for 1895: `Number` (`col0`), `Surname` (`col1`), `Forenames` (`col2`), `Trade` (`col3`), `Building` (`col4`).
  * Converted titles (`Mrs`, `Miss`, `Rev`, `Dr`) when forename appeared in trade column.
  * Filtered out banner advertisements (`Trapnell & Gane`).
  * Removed non-street landmarks (`Town Hall`, `Union`) from known streets list so listings stay attributed to their true streets (`Commercial Street`, `Stow Hill`, etc.).
  * Expanded street abbreviations (`Up.` $\rightarrow$ `Upper `, e.g. `Upper Durham Road`).
  * Normalized street names against master catalog, standardizing apostrophes (`'S` $\rightarrow$ `'s`), fixing typos (`Chepstable Road` $\rightarrow$ `Chepstow Road`, `St. Woollos Rd` $\rightarrow$ `St. Woolos Road`, `Alteryn Road` $\rightarrow$ `Allt-yr-yn Road`, `Stow Hill` $\rightarrow `Stow hill`, etc.).
* **Master Merge (`scripts/merge_1895.py`)**:
  * Added **11,668 clean resident records** to `data.csv` (bringing master count from 296,710 to 308,378).
  * Executed `fix_split_trades.py` and `merge_casing_twins.py` to canonicalize occupations and maintain **0 casing twins**.
  * Rebuilt `data/trades.json`, `data/search_index.json` (306,881 entries), and all per-street JSON files across 1,430 streets in `data/streets/`.

---

## 🏛️ High Street & Cross-Street Comprehensive Audit & Repair (October 2026)
* **Context**: High Street is one of Newport's primary thoroughfares with a fixed historical range of properties (numbers 1 through 84, from the Old Green / Bridge to Commercial Street). An audit revealed significant cross-street bleed and header misattribution in several volumes:
* **1901 (`scripts/parse_1901.py`)**:
  * Root Cause: Mid-page advertisement banner for *P. E. GANE / 27 Greenhouse & Scrivener, HIGH STREET* at line 2192 caused Caerleon Road properties #249–#373 to bleed into High Street (elevating numbers into the 300s).
  * Fix: Filtered inline advertisement banner. High Street restored to **139 clean commercial records** (range 3–84). Caerleon Road properties correctly retained under Caerleon Road (121 records, max #323).
* **1902 (`scripts/parse_1902.py`)**:
  * Root Cause: High Street was fragmented because building/arcade headers (*Beaufort Chambers*, *Queen's Chambers*, *Carlton Chambers*, *The Newport Arcade*) were parsed as street headers.
  * Fix: Filtered chamber and arcade headers so High Street remains unbroken. High Street records increased from 61 to **133 clean records** (range 3–84).
* **1903 (`scripts/parse_1903.py`)**:
  * Root Cause: High Street header at line 7922 had a split tab `\tHigh\tStreet.\tFrom the Bridge...`, causing the first half of High Street (properties 78–84 and 3–23) to remain trapped under `Hewertson Street`.
  * Fix: Fixed split header recognition and filtered chamber subheadings. High Street restored from 15 to **80 records** (range 3–84); Hewertson Street returned from 190 to its true **95 records**.
* **1910 (`scripts/parse_1910.py` & `scripts/clean_csv.py`)**:
  * Root Cause: 1) Midland Bank Chambers / Bridge Street listings were erroneously mapped to High Street; 2) The true High Street header at line 9727 had a map grid coordinate `HIGH STREET, C 4`, which failed street matching and dumped the real High Street into `Shaftesbury Street`.
  * Fix: Stripped map grid references (`C 4`, etc.), corrected `midland bank chambers` mapping to `Bridge Street`, and unpacked right-column High Street entries. High Street restored from Shaftesbury Street with **86 records** (range 3–82); Bridge Street restored with **317 records** (#1–#85).
* **1913 (`scripts/parse_1913.py`)**:
  * Root Cause: Recurring margin banner advertisements (*LANGMAID, WESTERN MAIL CHAMBERS, HIGH STREET, NEWPORT*) caused the parser to switch into High Street, pulling in residential cottages from Magor Street, Cambria Street, and Church Road.
  * Fix: Filtered `LANGMAID` recurring banner ads and unpacked space-delimited OCR lines. High Street corrected from 325 residential cottages down to **206 commercial shop records** (range 3–84), restoring cottages to their proper streets.
* **1920 (`scripts/parse_1920.py` & `scripts/clean_csv.py`)**:
  * Root Cause: 1) Multi-line layout where house numbers appeared on their own lines; 2) Floor headers and `G.W.R.` parsed as street names, bleeding Durham Road; 3) `HOLY TRINITY CHURCH` on Potter Street (line 15069) was erroneously mapped in `clean_csv.py` to High Street, dumping Potter Street residents into High Street.
  * Fix: Added pending house number buffer, ignored floor/railway/church headers, mapped `POT` page header to `Potter Street`, and removed church mapping. High Street corrected to **113 clean records** (range 3–84); Durham Road restored to **151 records** (range 73–203); Potter Street restored to **40 records**.
* **Master Merge & Site Rebuild**:
  * Master records: **319,838**.
  * Casing variants in `data/trades.json`: **0**.
  * Rebuilt search index and 1,738 per-street JSON files in `data/streets/`.

---

## 🌐 Macro Topological Diagnostic Scanner & 4-Stage Automated Dataset Healing (October 2026)

Rather than repairing streets one by one, a global cross-year topological audit and automated 4-stage healing pipeline were engineered and executed across all 26 directory years (1876–1971):

### 1. Phase 1: Macro Topological Diagnostic Scanner (`scripts/macro_dataset_scanner.py`)
Scans `data.csv`, `master_streets.json`, and `raw_tsvs/*.tsv` against 6 global invariants and outputs structured TSV reports in `reports/`:
* **Invariant 1 (`reports/street_outliers.tsv`)**: Street upper-bound house number violations compared against each street's 26-year historical ceiling ($\max(\text{median}\times 1.25, P_{80}\times 1.15, \text{median}+15)$), with automated cross-year resident attribution.
* **Invariant 2 (`reports/coverage_gaps.tsv`)**: Year-over-year volumetric plunges ($>75\%$ drop compared to adjacent years).
* **Invariant 3 (`reports/false_streets.tsv`)**: Automated classification of all unverified street names into `AD_OR_LAYOUT_ARTIFACT`, `BUILDING_OR_INSTITUTION_HEADER`, `SUB_TERRACE_OR_VILLAS_ON_PARENT_ROAD`, `OCR_STREET_TYPO`, and `MISATTRIBUTED_BLOCK_OR_SUBTERRACE`.
* **Invariant 4 (`reports/column_wrap_intrusions.tsv`)**: Contiguous cross-street bleed block detection powered by a global `(normalized_surname, house_int)` Cross-Year Resident Index.
* **Invariant 5 (`reports/field_contaminations.tsv`)**: Field-level structural anomalies (`EMPTY_SURNAME_AND_BUILDING`, `COMMA_UNSPLIT_IN_NAME`, `DIGITS_IN_SURNAME`, `TRADE_BLEED_IN_FORENAME`, `PURE_TRADE_IN_SURNAME`, `LAYOUT_MARKER_IN_RECORD`, `HOUSE_NUMBER_RANGE_IN_SURNAME`).
* **Invariant 6 (`reports/raw_tsv_architecture.tsv`)**: Multi-column structural profiles across all 24 raw TSV files.

### 2. Automated 4-Stage Dataset Healing Pipeline (`scripts/execute_macro_healing.py`)
* **Stage 1: Global Street Name Normalization & Verified OCR Typo Unification (13,969 records healed)**:
  * Unifies casing variants (`Stow hill` $\rightarrow$ `Stow Hill`, `Woodland park` $\rightarrow$ `Woodland Park`), expands 1910 hyphenated street names (`Corporation-Road` $\rightarrow$ `Corporation Road`), expands abbreviated suffixes (`St.`, `Rd.`, `Ave.`, `Ter.`, `Pl.`, `Cres.`, `Sq.`), strips trailing map grid coordinates (`D 5/60`, `(307)`), and resolves 130+ resident-verified OCR street typos (`Vicarage Avenue` $\rightarrow$ `Victoria Avenue`, `Caeru Road` $\rightarrow$ `Caerleon Road`, `Dewstreet Street` $\rightarrow$ `Devon Place`, `Llanthamthi Street` $\rightarrow$ `Llanarth Street`, `Hewerton Street` $\rightarrow$ `Hewertson Street`, etc.).
  * Synced into Step 11 of `scripts/clean_csv.py`.
* **Stage 2: Surgical Field-Level Contamination, Column-Shift & Inversion Repair (36,447 field repairs)**:
  * Executed **before** Cross-Street Splicing so newly restored surnames immediately enrich the Cross-Year Resident Index:
    * **Surname $\leftrightarrow$ Forename Un-Inversion (16,418 records)**: Repairs inverted `(Forename, Surname)` records across 1927, 1892, 1895, 1971, 1924, and 1878 (`Geo. H | Toomer` $\rightarrow$ `Toomer | Geo. H`, `Benj. labourer | Shakesheff` $\rightarrow$ `Shakesheff | Benj. | Labourer`, `Elizabeth | Mrs Stockwell` $\rightarrow$ `Stockwell | Mrs Elizabeth`).
    * **Left-Shifted Unnumbered Resident Repair (5,473 records)**: Repairs unnumbered residents where the Surname was shifted into `house_number` and the Forename into `surname` (`#Edwards | T | S | Solicitor` $\rightarrow$ `# | Edwards | T S | Solicitor`).
    * **Forename Trade Extraction & Field Realignment (12,808 records)**: Extracts embedded lowercase trades from `forename` (4,325 records), restores surnames from `forename` when `surname` was blank (4,315 records), realigns house numbers stuck in `surname` (1,926 records), swaps pure trades in `surname` (1,414 records), and cleans literal `NaN`/`NULL` extraction artifacts (1,748 records).
* **Stage 3: False Street Resolution (8,947 records healed)**:
  * Resolves recurring margin ad banners (*The Newport Steam Laundry*, *P. E. Gane*, *Francis' Dye Works*, *R. H. Johns*, *Edwards Ltd*), map grid headers (`D 5 97`, `C 5`), 3-letter running page headers (`Cor`, `Can`), and non-street landmarks (schools, churches, post offices, hospitals) back to their true parent streets.
  * Resolves 45+ Chambers, Buildings, Halls, and Arcades (*Austin Friars Chambers*, *Westgate Chambers*, *Victoria Chambers*, *Highbury Chambers*, *The Newport Arcade*, etc.) to their parent thoroughfares while preserving the building name in `building_name` for genuine chamber tenants.
* **Stage 4: Contiguous Cross-Street Bleed Splicing (1,623 blocks / 35,987 records restored)**:
  * Uses the enriched Cross-Year Resident Index (excluding placeholder tokens like `Void`, `Vacant`, `House`, `NULL`, `NaN`, `Flat`) and historical street house-number ceilings to splice contiguous misplaced column blocks back to their true streets (including splicing all `#44–#206` Shaftesbury Street records out of `High Street 1927`, eliminating 100% of `High Street` upper-bound violations across all 24 years).

### 3. Before vs. After Macro Verification Summary
* **Unique Street Slugs (`data/streets.json`)**: Consolidated from **1,738 $\rightarrow$ 1,385** (-353 fake/typo/ad/chamber street slugs eliminated).
* **Contiguous Cross-Street Bleed Blocks**: Reduced from **2,663 $\rightarrow$ 754** (**-1,909 blocks spliced**, a **71.7% reduction**).
* **Major Street-Year Coverage Plunges**: Reduced from **1,270 $\rightarrow$ 786** (**-484 missing street-years recovered**).
* **False / Unverified Streets**: Reduced from **693 $\rightarrow$ 245** (**-448 false/unverified streets resolved**).
* **Street Upper-Bound Violations**: Reduced from **417 $\rightarrow$ 327** (**0 violations remaining on High Street across all 24 years**).
* **Empty Surname & Building Rows**: Reduced from **7,106 $\rightarrow$ 2,105** (**-5,001 resident names restored**).
* **Casing Variants in `data/trades.json`**: **0** (across 318,761 total records and 158,797 trade entries).






