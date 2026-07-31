import csv
import json
import os
import re

INPUT_CSV = "data.csv"
OUTPUT_CSV = "data.csv"
EDGE_CASES_FILE = "edge_cases.json"

# Load Edge Cases Configuration
EDGE_CASES = []
if os.path.exists(EDGE_CASES_FILE):
    with open(EDGE_CASES_FILE, "r", encoding="utf-8") as ef:
        try:
            EDGE_CASES = json.load(ef).get("overrides", [])
            print(f"Loaded {len(EDGE_CASES)} historical edge cases from {EDGE_CASES_FILE}")
        except Exception as e:
            print(f"Warning: Could not load {EDGE_CASES_FILE}: {e}")

# Dictionary of standard street suffix expansions
ABBREVIATIONS = {
    r"\bRd\b\.?": "Road",
    r"\bSt\b\.?": "Street",
    r"\bAve\b\.?": "Avenue",
    r"\bTer\b\.?": "Terrace",
    r"\bPl\b\.?": "Place",
    r"\bSq\b\.?": "Square",
    r"\bCres\b\.?": "Crescent",
    r"\bPde\b\.?": "Parade",
    r"\bGdns\b\.?": "Gardens",
}

HEADER_SURNAMES = {"butcher's", "thompson's", "johns'", "johns's", "directory"}

CROSS_STREET_REGEX = re.compile(
    r'\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|parade|pde|av|av\.)\b.*?\bto\b.*?\b(?:avenue|st|street|rd|road|lane|place|terrace|hill|way|drive|crescent|parade|pde|av|av\.)\b'
    r'|^\s*\[?(?:here\s+are|here\s+is|here\s+cross|\[?return\]?|\(return\.?\)|return\.?)\]?\b'
    r'|^\s*[\(\[]?\s*return\.?\s*[\)\]]?\s*$'
    r'|^\s*see\s+also\s+[A-Za-z]+'
    r'|^\s*(?:maindee|newport|pill)from\b'
    r'|^\s*from\s+[A-Za-z\s]+'
    r'|^\s*[A-Za-z\s]+street\s+from\b',
    re.I
)

# Trade keywords to identify trade bleeding into forename
TRADE_KEYWORDS = [
    "mechanic", "clerk", "grocer", "mariner", "driver", "fitter", "carpenter",
    "platelayer", "labourer", "shoemaker", "draper", "baker", "mason", "rigger",
    "tailor", "painter", "smith", "builder", "haulier", "fireman", "guard",
    "boot", "joiner", "dealer", "assistant", "manager", "visitor", "shipper",
    "plasterer", "sail", "engineer", "inspector", "agent", "blacksmith",
    "ironworker", "steelworker", "trimmer", "pilot", "master", "brewer",
    "porter", "clerk", "nurse", "telegraph", "engine", "collector", "station",
    "booksellers", "stationers", "auctioneer", "dressmaker", "gardener",
    "milliner", "wine", "cabinet maker", "professor", "sorter"
]

BUSINESS_SUFFIX_REGEX = re.compile(
    r"^(?:&|and|ltd|limited|co\.?|company|sons|bros|brothers|school|academy|place\s+school|house|depot|works|chambers|stores|hotel|inn|arms|vaults)\b",
    re.I
)

INSTITUTION_WORD = re.compile(
    r"^(?:chapel|church|office|association|board office|houses|seminary|school|infirmary|hospital|bank|association offices|society|works|depot|hall|chambers)\b",
    re.I
)

VILLA_WORD = re.compile(
    r"\b([A-Z][a-zA-Z\s'\-]+?\b(?:villa|cottage|house|inn|arms|hotel|chambers|lodge|court|hall|chapel))\b",
    re.I
)

NON_PERSON_WORDS = ['wagon', 'coal', 'iron', 'colliery', 'docks', 'railway', 'supply', 'stores', 'drapery']

def clean_street_name(name):
    if not name:
        return ""
    
    clean = name.replace('"', '').strip()
    clean = re.sub(r",\s*[A-Za-z0-9\s]+\b", "", clean)
    
    for pattern, replacement in ABBREVIATIONS.items():
        clean = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)
        
    clean = clean.rstrip(".")
    return clean.title().strip()

def title_case_name(name):
    if not name:
        return ""
    return re.sub(r"\w\S*", lambda m: m.group(0).capitalize() if m.group(0).islower() else m.group(0), name).strip()

def apply_edge_cases(record):
    """Applies structured edge-case overrides from edge_cases.json."""
    st = record["street"]
    yr = record["year"]
    h_num = record["house_number"]
    bldg = record["building_name"]
    s = record["surname"]
    f = record["forename"]
    t = record["trade"]

    for rule in EDGE_CASES:
        match = rule.get("match", {})
        
        # Match street
        if match.get("street") and match["street"].lower() != st.lower():
            continue
        # Match year
        if match.get("year") and match["year"] != yr:
            continue
        # Match house_number
        if "house_number" in match and match["house_number"] != h_num:
            continue
        # Match surname
        if match.get("surname") and match["surname"].lower() != s.lower():
            continue
        if match.get("surname_contains") and match["surname_contains"].lower() not in s.lower():
            continue
        if match.get("forename_contains") and match["forename_contains"].lower() not in f.lower():
            continue
        if match.get("building_name") and match["building_name"].lower() != bldg.lower():
            continue

        # Apply direct override
        if "apply" in rule:
            for k, v in rule["apply"].items():
                record[k] = v

        # Apply conditional override
        if "apply_conditional" in rule:
            cond = rule["apply_conditional"]
            if cond.get("if_surname_contains") and cond["if_surname_contains"].lower() in s.lower():
                for k, v in cond["apply"].items():
                    record[k] = v

    return record

def clean_record(row):
    year = (row.get("year") or "").strip()
    street = clean_street_name(row.get("street") or "")
    house_num = (row.get("house_number") or "").strip().strip(',"-~')
    bldg_name = (row.get("building_name") or "").strip().strip(',"-~')
    surname = (row.get("surname") or "").strip().strip(',"-~')
    forename = (row.get("forename") or "").strip().strip(',"-~')
    trade = (row.get("trade") or "").strip().strip(',"-~')

    # 1. Filter out Directory Header Artifacts, Cross-street Headings & (return) Markers
    if surname.lower() in HEADER_SURNAMES and (forename.isdigit() or not trade):
        return None

    combined_name = f"{surname} {forename}".strip()
    if CROSS_STREET_REGEX.search(combined_name) or CROSS_STREET_REGEX.search(bldg_name) or CROSS_STREET_REGEX.search(surname):
        return None

    # Strip district headers (e.g. MaindeeFrom, NewportFrom)
    surname = re.sub(r'^(maindee|newport|pill)from\s*', '', surname, flags=re.I).strip()
    forename = re.sub(r'^(maindee|newport|pill)from\s*', '', forename, flags=re.I).strip()

    # 2. Fix shifted surname/forename/trade in building_name (e.g. bldg='Jones', surname='Geo', forename='labourer')
    if bldg_name and bldg_name[0].isupper() and not any(w in bldg_name.lower() for w in ['house', 'villa', 'cottage', 'chambers', 'works', 'inn', 'arms', 'hotel', 'building', 'school', 'lodge', 'place', 'hall']):
        if forename.lower() in TRADE_KEYWORDS or forename.lower() in ['labourer', 'sorter', 'fitter', 'carpenter', 'driver', 'grocer', 'draper', 'mason']:
            trade = forename
            forename = surname
            surname = bldg_name
            bldg_name = ""

    # 3. Handle Crindau Glass / Gas Works company titles
    if "Glass Manufacturing" in combined_name or "Glass Manufacturing" in trade or "Glass Manufacturing" in surname:
        surname = "South Wales Glass Manufacturing Co. Office & Works"
        forename = ""
        trade = "glass manufacturers"
    elif surname == "Crindau" and forename == "Gas Works":
        surname = "Crindau Gas Works"
        forename = ""

    # 4. Extract trade trapped in forename (e.g. 'H. A. wine', 'Mrs. milliner', 'J. F. professor of drawing', 'J. cabinet maker')
    if forename:
        match_t_f = re.match(r"^(.*?)\s+(milliner|wine|cabinet maker|professor of \w+|shopkeeper|registry office|auctioneer|dressmaker|gardener|grocer|chemist|draper|tailor|bootmaker|solicitor|surgeon|dentist|architect|engineer|builder|broker|accountant|merchant|agent|beer retailer|licensed victualler|publican)$", forename, re.I)
        if match_t_f:
            forename = match_t_f.group(1).strip()
            extra_t = match_t_f.group(2).strip()
            trade = f"{extra_t}, {trade}".strip(", ") if trade else extra_t

    # 5. Fix institution names split across surname & forename (e.g. 'Conservative' + 'Association', 'Baptist' + 'chapel')
    if forename and INSTITUTION_WORD.search(forename.strip()):
        surname = title_case_name(f"{surname} {forename}".strip())
        forename = ""

    # 6. Extract building/villa names from trade or forename (e.g. trade='Stow gate villa', forename='R. H. Belmont villa')
    if not bldg_name:
        v_match_f = VILLA_WORD.search(forename)
        if v_match_f and not any(w in forename.lower() for w in ['customs', 'commercial', 'auctioneer', 'draper']):
            bldg_name = title_case_name(v_match_f.group(1))
            forename = forename.replace(v_match_f.group(1), '').strip()

        v_match_t = VILLA_WORD.search(trade)
        if v_match_t and not any(w in trade.lower() for w in ['customs', 'commercial', 'auctioneer', 'house,', 'estate', 'repairer']):
            bldg_name = title_case_name(v_match_t.group(1))
            trade = trade.replace(v_match_t.group(1), '').strip()

    # 7. Extract telephone numbers misparsed into house_number column (e.g. 45876, 41609)
    if house_num.isdigit() and (int(house_num) >= 40000 or (int(house_num) >= 1000 and street != "Corporation Road")):
        tel_num = house_num
        house_num = ""
        # Restore known house numbers if applicable
        if "King's Head" in trade or "King's Head" in surname:
            house_num = "1"
        elif "WE Evans" in surname or "W. E. Evans" in surname:
            house_num = "12-13"
        elif "Burton" in surname:
            house_num = "31-33"
        
        if f"Tel. {tel_num}" not in trade:
            trade = f"{trade} (Tel. {tel_num})".strip()

    # 8. Fix split ampersand forenames (e.g. surname='Dutfield', forename='& Frost' -> surname='Dutfield & Frost')
    if forename.startswith("& "):
        surname = f"{surname} {forename}".strip()
        forename = ""

    # 9. Fix building_name that contains house number and resident name (e.g. '35-35A Smith W. H. & Son')
    if bldg_name:
        match_b_num = re.match(r"^(\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?)\s*(.*)$", bldg_name)
        if match_b_num:
            ext_num = match_b_num.group(1).upper()
            rest_name = match_b_num.group(2).strip()
            if not house_num:
                house_num = ext_num
            elif house_num != ext_num and not house_num.endswith(ext_num):
                house_num = f"{house_num}-{ext_num}"
            bldg_name = ""
            if rest_name:
                surname = f"{rest_name} {surname}".strip()

    # 10. Extract house numbers merged into surname or forename (e.g. '35a &', '35A Smith W. H. & Son Ltd.')
    match_s_num = re.match(r"^(\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?)\s*(?:&|\s)\s*(.*)$", surname)
    if match_s_num:
        ext_num = match_s_num.group(1).upper()
        surname = match_s_num.group(2).strip()
        if house_num and house_num != ext_num and not house_num.endswith(ext_num):
            house_num = f"{house_num}-{ext_num}"
        elif not house_num:
            house_num = ext_num

    match_f_num = re.match(r"^(\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?)\s*(?:&|\s)\s*(.*)$", forename)
    if match_f_num:
        ext_num = match_f_num.group(1).upper()
        forename = match_f_num.group(2).strip()
        if house_num and house_num != ext_num and not house_num.endswith(ext_num):
            house_num = f"{house_num}-{ext_num}"
        elif not house_num:
            house_num = ext_num

    # 11. Fix bad ampersand surname rows (e.g. surname='&', forename='13 Evans W. E. & Co.')
    if surname == "&" and forename:
        match = re.match(r"^(\d+(?:-\d+)?)\s+(.*)$", forename)
        if match:
            house_num = match.group(1)
            forename = match.group(2)
        parts = forename.split(" ", 1)
        if len(parts) == 2:
            surname = parts[0]
            forename = f"{parts[1]} &"

    # 12. Handle surnames ending with Ltd / Co (e.g. surname='Dean Ltd', forename='John H' -> surname='John H Dean Ltd', forename='')
    corp_match = re.match(r"^(.*?)\s+(Ltd\.?|Co\.?|& Co\.?|Co\.? Ltd\.?)$", surname, re.I)
    if corp_match and forename and not re.match(r"^\d", forename):
        base_s = corp_match.group(1)
        corp_suf = corp_match.group(2)
        is_person = re.match(r"^[A-Z][a-zA-Z\.]*(?:\s+[A-Z][a-zA-Z\.]*)*$", forename) and not any(w in forename.lower() for w in NON_PERSON_WORDS)
        if is_person:
            surname = f"{forename} {base_s} {corp_suf}".strip()
            forename = ""
        else:
            surname = f"{base_s} {corp_suf}".strip()
            forename = ""

    # 13. Fix cases where forename is initials and surname contains company suffix (e.g. surname='Lovell & Co Ltd', forename='GF')
    if forename and re.match(r"^[A-Z]\.?(?:\s*[A-Z]\.?)*$", forename) and re.search(r"\b(&|ltd|limited|co|company|sons|bros|brothers)\b", surname, re.I):
        surname = f"{forename} {surname}".strip()
        forename = ""

    # 14. Handle location-suffix forenames (e.g. surname='Bollom', forename='of Bristol' -> 'Bollom of Bristol')
    if re.match(r"^of\s+[A-Za-z]", forename, re.I):
        surname = f"{surname} {forename}".strip()
        forename = ""

    # 15. Handle initials + company suffix forenames (e.g. surname='Lovell', forename='GF & Co Ltd' -> surname='GF Lovell & Co Ltd', forename='')
    init_biz_match = re.match(r"^([A-Z]\.?(?:\s*[A-Z]\.?)*)\s+(&(?:.*)|ltd.*|co.*|sons.*|bros.*|limited.*)$", forename, re.I)
    if init_biz_match:
        initials = init_biz_match.group(1).strip()
        biz_suffix = init_biz_match.group(2).strip()
        surname = f"{initials} {surname} {biz_suffix}".strip()
        forename = ""

    # 16. Handle hyphenated trade trapped in forename (e.g. '& Son - cycle factors')
    if " - " in forename:
        parts = forename.split(" - ", 1)
        forename = parts[0].strip()
        extra_trade = parts[1].strip()
        trade = f"{extra_trade}, {trade}".strip(", ") if trade else extra_trade

    # 17. Fix pure business / organization name ordering (e.g. 'Taylor' + '& Son' -> 'Taylor & Son')
    if forename and BUSINESS_SUFFIX_REGEX.search(forename.strip()):
        surname = title_case_name(f"{surname} {forename}".strip())
        forename = ""

    # 18. Extract middle initials trapped in trade (e.g. 'T. mechanic')
    if trade:
        initial_match = re.match(r"^([A-Z]\.)\s+(.*)$", trade)
        if initial_match:
            mid_init = initial_match.group(1)
            trade = initial_match.group(2)
            forename = f"{forename} {mid_init}".strip()

    # 19. Expand Journeyman (j.) / (j) tags
    if "(j.)" in forename.lower() or "(j)" in forename.lower() or "(j.)" in trade.lower() or "(j)" in trade.lower():
        forename = re.sub(r"\s*\([jJ]\.?\)\s*", " ", forename).strip()
        if "(j.)" in trade.lower() or "(j)" in trade.lower():
            trade = re.sub(r"\s*\([jJ]\.?\)\s*", " Journeyman ", trade).strip()
        else:
            trade = f"Journeyman {trade}".strip()

    # 20. Split remaining trades trapped in forenames
    if forename:
        match = re.match(r"^(.*?)\s+([a-z].*)$", forename)
        if match:
            f_part = match.group(1).strip()
            t_part = match.group(2).strip()
            if any(kw in t_part.lower() for kw in TRADE_KEYWORDS) or t_part.startswith("("):
                forename = f_part
                trade = f"{t_part}, {trade}".strip(", ") if trade else t_part

    # Clean trailing commas, quotes & spaces
    surname = surname.strip(' ,"-~')
    forename = forename.strip(' ,"-~')
    trade = trade.strip(' ,"-~')

    rec = {
        "year": year,
        "street": street,
        "house_number": house_num,
        "building_name": bldg_name,
        "surname": surname,
        "forename": forename,
        "trade": trade,
    }

    # 21. Apply Structured Edge-Case Overrides from edge_cases.json
    rec = apply_edge_cases(rec)

    if not rec["surname"] and not rec["forename"] and not rec["trade"] and not rec["building_name"]:
        return None

    return rec

def main():
    rows = []
    skipped_count = 0
    
    with open(INPUT_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            # Unpack 1886 Crindau Gas Works run-on blob
            if row.get("street") == "Crindau Road" and row.get("year") == "1886" and "Williams Joseph" in row.get("trade", ""):
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "1", "building_name": "Workmen's Cottage", "surname": "Manley", "forename": "Michael", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "2", "building_name": "Workmen's Cottage", "surname": "Williams", "forename": "Joseph", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "3", "building_name": "Workmen's Cottage", "surname": "Gane", "forename": "Joshua", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "4", "building_name": "Workmen's Cottage", "surname": "Sweet", "forename": "Robert", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "5", "building_name": "Workmen's Cottage", "surname": "Murphy", "forename": "Michael", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "6", "building_name": "Workmen's Cottage", "surname": "Hiscocks", "forename": "Henry", "trade": "gas worker"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "", "building_name": "Crindau Gas Works", "surname": "Crindau Gas Works", "forename": "", "trade": "gas works"})
                rows.append({"year": "1886", "street": "Crindau Road", "house_number": "", "building_name": "Glass Works", "surname": "South Wales Glass Manufacturing Co.", "forename": "", "trade": "glass works"})
                continue

            cleaned = clean_record(row)
            if cleaned is None:
                skipped_count += 1
            else:
                rows.append(cleaned)

    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done! Cleaned and normalized {len(rows)} records in {OUTPUT_CSV}. Filtered {skipped_count} header/cross-street/return rows.")

if __name__ == "__main__":
    main()