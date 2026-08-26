# Interactive Data Correction Guide & Schema Specification

This document details the standardization rules, schema specifications, and workflow for reviewing and correcting property records in the **Newport Street Directory Archive**.

---

## 1. Overview & Goal

Historical directory datasets derived from OCR (Optical Character Recognition) scans often contain layout shifts, merged column data, or misplaced occupation titles.

The **Interactive Data Correction Editor** allows editors to:
- Directly edit records in the browser with immediate visual feedback.
- Maintain a standardized structure across all 1,462+ streets.
- Generate clean JSON overrides compatible with `edge_cases.json` without altering source CSVs or causing unintended programmatic side-effects elsewhere.

---

## 2. Standardized Record Schema

Every property record in the archive follows this standardized 9-field structure:

| Field Name | Type | Description & Standardization Rules | Example |
| :--- | :--- | :--- | :--- |
| **`street`** | String | Master street name (Title Case). | `"Albany Street"`, `"Stow Hill"` |
| **`year`** | String | 4-digit directory year. | `"1938"`, `"1971"` |
| **`house_number`** | String | Primary street number or range. Numbers/letters only (no building/house names here). | `"14"`, `"14A"`, `"12-13"` |
| **`sub_unit`** | String | Secondary unit/floor for multi-tenant chambers, offices, or rear premises. | `"Flat 2"`, `"Room 4"`, `"Rear of 14"` |
| **`building_name`** | String | Genuine building, villa, cottage, hotel, or pub name. *No resident names or trades.* | `"Westgate Chambers"`, `"Lamb Inn"` |
| **`entry_type`** | Enum | Category: `Person`, `Business`, or `Cross-Reference`. | `"Person"` |
| **`surname`** | String | Occupant surname (if Person) OR Full Commercial Name (if Business). | `"Dunn"`, `"W.H. Smith & Son Ltd."` |
| **`forename`** | String | Resident given name(s) or initials (if Person). *Leave blank for Business.* | `"Edward A."`, `"John T."` |
| **`trade`** | String | Occupation, trade description, or official role. | `"Steward"`, `"Grocer"`, `"Solicitor"` |

---

## 3. Handling Special Directory Scenarios

### A. Multi-Tenant Chambers & Commercial Buildings (e.g. Westgate Chambers)
When multiple businesses or professionals occupy rooms in a single numbered building:
- **`house_number`**: `"40"`
- **`building_name`**: `"Westgate Chambers"`
- **`sub_unit`**: `"Room 1"`, `"Suite 2"`, `"Office 3"`
- **`surname`**: `"Newport Land Society"` (Business Name)
- **`trade`**: `"Land Agents & Valuers"`

> **System Behavior**: The street view merges all entries for house `40` into a single card (**`40 — Westgate Chambers`**) with a sub-count tag. Clicking the card opens the detailed property page listing all suites and tenants chronologically.

---

### B. Commercial & Business Entities (e.g. Universal Dental Laboratory, W.H. Smith & Son)
For commercial companies, shops, institutions, or laboratories without a named individual person:
- **`entry_type`**: `"Business"`
- **`surname`**: `"Universal Dental Laboratory"` *(Put full commercial title here as the primary display name!)*
- **`forename`**: `""` *(Leave empty)*
- **`trade`**: `"Dental Laboratory"` *(Optional industry description)*
- **`building_name`**: `""` *(Unless located in a named building like King's Chambers)*

> **Why Commercial Titles Belong in `surname`**: The `surname` field serves as the primary occupant title in the database schema. Placing the business title in `surname` ensures it displays in **bold white text** on property cards and registers properly in global search.

---

### C. Inn, Pub & Hotel Listings (e.g. Lamb Inn, Queen's Hotel)
- **`house_number`**: `"5"` (or leave blank if unnumbered)
- **`building_name`**: `"Lamb Inn"`
- **`entry_type`**: `"Person"` (if licensee named) OR `"Business"`
- **`surname`**: `"Wood"`
- **`forename`**: `"Mrs. Mary"`
- **`trade`**: `"Licensed Victualler"` (or `Innkeeper`)

---

### D. Directory Cross-References (e.g. "See Stow Hill")
- **`entry_type`**: `"Cross-Reference"`
- **`surname`**: `"See Stow Hill"`
- **`trade`**: `"Directory Cross-Reference"`

---

## 4. Complete Editing & Merging Workflow

### Step 1: Edit Records in the Browser
1. Navigate to any street view in your browser (e.g. `http://127.0.0.1:5500/index.html#street=Albany%20Street` or `#house=High%20Street%7C1`).
2. Hover over any property card or timeline entry and click the **`✏️ Edit`** button.
3. Modify the fields in the pop-up form (e.g., separate building names from occupant surnames, select `Person` or `Business`, add sub-unit details like `Room 4`).
4. Click **"Save & Preview Correction"**.
   - Your change will immediately render in the browser.
   - **LocalStorage Persistence**: Edits are automatically saved in your browser cache, so refreshing the page or restarting your browser **will NOT lose your active session edits**.

---

### Step 2: Download Your Overrides File
When you are finished reviewing a street (or multiple streets):
1. Look at the gold **Session Edits Active** drawer docked at the bottom of your screen.
2. Click **"📥 Download user_overrides.json"**.
3. The downloaded `user_overrides.json` file can be placed into:
   - **`overrides_inbox/`** directory inside the project (recommended for neat organization), **OR**
   - Left in your default **`~/Downloads/`** folder (the script checks both automatically!).

---

### Step 3: Run the Automatic Merge Script
Open your terminal in the project directory and run:

```bash
python3 merge_overrides.py
```

#### What `python3 merge_overrides.py` Does:
1. **Locates the file(s)**: Automatically checks `overrides_inbox/`, the project root, and your `~/Downloads/` folder for exported JSON override files.
2. **Merges cleanly**: Appends your new rules into `edge_cases.json` while skipping any duplicate entries.
3. **Rebuilds dataset**: Runs `python3 clean_csv.py && python3 build_site_data.py` to regenerate all street JSON files automatically.

---

### Folder Structure Summary:
```
Newport Street Directory Project/
├── edge_cases.json           <-- Master overrides database (automatically updated)
├── merge_overrides.py         <-- Run this script in terminal
├── overrides_inbox/          <-- (Optional) Drop your downloaded JSON files here!
│   └── user_overrides.json
└── RECORD_CORRECTION_GUIDE.md
```

### Optional Commands:
- Merge a specific custom file path:
  ```bash
  python3 merge_overrides.py /path/to/my_overrides.json
  ```
- Clear browser session edits manually:
  Click **"Clear All"** in the bottom drawer.
