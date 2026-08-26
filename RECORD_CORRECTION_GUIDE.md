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

### B. Inn, Pub & Hotel Listings (e.g. Lamb Inn, Queen's Hotel)
- **`house_number`**: `"5"` (or leave blank if unnumbered)
- **`building_name`**: `"Lamb Inn"`
- **`entry_type`**: `"Person"` (if licensee named) OR `"Business"`
- **`surname`**: `"Wood"`
- **`forename`**: `"Mrs. Mary"`
- **`trade`**: `"Licensed Victualler"` (or `Innkeeper`)

---

### C. Directory Cross-References (e.g. "See Stow Hill")
- **`entry_type`**: `"Cross-Reference"`
- **`surname`**: `"See Stow Hill"`
- **`trade`**: `"Directory Cross-Reference"`

---

## 4. How to Use the Form Editor in the Browser

1. **Open any Street**: Navigate to any street view in your browser (e.g., `#street=Albany%20Street`).
2. **Click "✏️ Edit Record"**: Hover over any property card or timeline item and click the **Edit** button.
3. **Modify Fields**: Select the **Entry Type** (`Person` vs `Business`) and update any shifted fields.
4. **Instant Live Preview**: Click **"Apply Preview"** to inspect how the card looks immediately.
5. **Export Overrides**: Click **"Export All Overrides (`edge_cases.json`)"** to copy or download the exact JSON rules for the build pipeline.

---

## 5. Build Pipeline Integration

Once override JSON blocks are copied into `edge_cases.json`, run the standard build pipeline from your terminal:

```bash
python3 clean_csv.py && python3 build_site_data.py
```

This applies your manual corrections cleanly across the entire site without regressing other streets.
