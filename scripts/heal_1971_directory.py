#!/usr/bin/env python3
"""
heal_1971_directory.py
======================
Comprehensive healing for the 1971 Newport Street Directory volume:
1. Discards layout noise, cross-street markers, and map routing descriptions.
2. Extracts parenthetical house/villa names into building_name.
3. Disentangles unsplit "Surname Forename/Initials" stored in surname.
4. Extracts inline occupations (e.g. shopkpr -> Shopkeeper, watchmkr -> Watchmaker).
5. Populates business names into surname and trades into trade (avoiding Residence / Vacant).
6. Resolves rotated columns (house numbers in surname, surnames in house numbers).
7. Corrects inverted initials, titles, and building entities.
"""

import os
import sys
import csv
import re
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOLUME_1971_CSV = os.path.join(PROJECT_ROOT, "volume_csvs", "1971_cleaned.csv")
BACKUP_1971_CSV = os.path.join(PROJECT_ROOT, "volume_csvs", "1971_cleaned.csv.bak_before_healing")

TITLES = {
    "mr", "mrs", "miss", "ms", "dr", "rev", "capt", "col", "maj", "major",
    "sir", "lord", "lady", "councillor", "cllr", "alderman", "prof"
}

LAYOUT_NOISE = re.compile(
    r"\b(here is|here are|here cross|right side|left side|see also|no thoroughfare|"
    r"north side|south side|east side|west side|north-east side|north-west side|south-east side|south-west side|"
    r"from .* to|map [a-z]\s*\d+|map [a-z]\d+|junior mixed|mixed &|infants|primary school|"
    r"to .* road|to .* street|to .* avenue)\b",
    re.I
)

BUILDING_REGEX = re.compile(
    r"\b(Inn|Hotel|Arms|Tavern|Vaults|Villa|Villas|Cottage|Cottages|Chambers|Lodge|House|Works|Foundry|Brewery|Depot|Institute|Club)\b",
    re.I
)

TRADES_PATTERN = re.compile(
    r"\b(shopkpr|shopkeeper|hairdrssr|hairdresser|watchmkr|watchmaker|dental technician|"
    r"teacher of music|butcher|grocer|draper|shoemaker|bootmaker|fitter|mason|painter|plumber|"
    r"ironworker|electrician|chemist|kehmst|tobacconist|confectioner|solicitor|accountant|"
    r"architect|newsagent|stationer|printer|tailor|clerk|proprietor|propr|manager|mgr|agent|surveyor)\b",
    re.I
)

BUSINESS_KEYWORDS = re.compile(
    r"\b(Ltd|Ld|Co\.|Co|Motors|Garage|Stores|Works|Brewery|Bank|Hotel|Inn|Arms|Canteen|"
    r"Hospital|School|Transport|Removals|Assurance|Society|Engineering|Supplies)\b",
    re.I
)

def clean_title_case(s):
    if not s:
        return ""
    words = s.split()
    return " ".join(w.capitalize() if not ('.' in w or w.isupper() or '-' in w) else w for w in words)

def expand_trade_abbrev(t):
    if not t:
        return ""
    t_low = t.lower().strip(" ,.-")
    mapping = {
        "shopkpr": "Shopkeeper",
        "hairdrssr": "Hairdresser",
        "watchmkr": "Watchmaker",
        "kehmst": "Chemist",
        "confctnr": "Confectioner",
        "confctnrs": "Confectioners",
        "mfng": "Manufacturing",
        "electrl": "Electrical",
        "contrctrs": "Contractors",
        "contrctr": "Contractor",
        "ship brkrs": "Ship Brokers",
        "ship bldrs": "Ship Builders",
        "propr": "Proprietor",
        "proprtrs": "Proprietors",
        "mgr": "Manager",
        "teacher of music": "Teacher of Music",
    }
    for k, v in mapping.items():
        if k in t_low:
            t = re.sub(r"\b" + re.escape(k) + r"\b", v, t, flags=re.I)
    return clean_title_case(t)

def clean_1971_record(r):
    sn = (r.get("surname") or "").strip()
    fn = (r.get("forename") or "").strip()
    tr = (r.get("trade") or "").strip()
    bd = (r.get("building_name") or "").strip()
    hn = (r.get("house_number") or "").strip()
    st = (r.get("street") or "").strip()

    full_line = f"{hn} {sn} {fn} {tr} {bd}".strip()
    if LAYOUT_NOISE.search(full_line) and not (fn and sn):
        return None

    if full_line in {"-", "- -", "--", "...", "·"}:
        return None

    # Step 1: Verbal house numbers (shifted columns)
    if hn and not re.search(r"\d", hn):
        if hn.lower() in {"...", "---", "--", "-", "·"}:
            hn = ""
        elif sn and BUSINESS_KEYWORDS.search(sn):
            sn = f"{hn} {sn}".strip()
            hn = ""
        elif sn and ("(" in sn or any(c.isupper() for c in sn)):
            real_sn = hn
            real_fn = sn
            hn = ""
            sn = real_sn
            fn = real_fn

    # Step 2: Parenthetical extraction from surname or forename
    for field_name in ["sn", "fn"]:
        val = sn if field_name == "sn" else fn
        m_paren = re.search(r"\(([^)]+)\)", val)
        if m_paren:
            content = m_paren.group(1).strip()
            if not re.match(r"^(?:j\.p|jp|snr|jnr|sr|jr|mrs|miss)$", content, re.I):
                if not bd:
                    bd = content
                val_clean = re.sub(r"\s*\([^)]+\)", "", val).strip()
                if field_name == "sn": sn = val_clean
                else: fn = val_clean

    # Step 3: Unsplit "Surname Forename/Initials" in sn (when fn is empty)
    if " " in sn and not fn:
        if BUSINESS_KEYWORDS.search(sn):
            m_biz_trade = re.match(
                r"^(.*?\b(?:Ltd|Ld|Co\.|Co|Motors|Garage|Stores|Works|Brewery|Hotel|Inn|Arms|Transport|Removals)\b[\.]?)\s*(?:,\s*)?(.*)$",
                sn, re.I
            )
            if m_biz_trade and m_biz_trade.group(2).strip():
                sn = m_biz_trade.group(1).strip()
                if not tr: tr = m_biz_trade.group(2).strip()
        else:
            parts = sn.split()
            if len(parts) >= 2:
                if parts[0].lower().rstrip(".") in TITLES:
                    sn = parts[-1]
                    fn = " ".join(parts[:-1])
                else:
                    sn = parts[0]
                    fn = " ".join(parts[1:])

    # Step 4: Extract inline occupations from forename
    if fn and TRADES_PATTERN.search(fn):
        m = TRADES_PATTERN.search(fn)
        job = m.group(1)
        fn = re.sub(r"\b" + re.escape(job) + r"\b", "", fn).strip(" ,.-")
        if not tr:
            tr = expand_trade_abbrev(job)

    # Step 5: Pure trade in surname
    if sn.lower() in {"chemist", "kehmst", "butcher", "grocer", "draper", "solicitor", "hairdresser"}:
        if not tr:
            tr = "Chemist" if sn.lower() in {"chemist", "kehmst"} else sn.capitalize()
        sn = ""

    # Step 6: Building/Inn/Hotel in surname
    if sn and not bd:
        m_pure_bldg = re.match(r"^(?:The\s+)?([A-Za-z0-9\s\']+\s+(?:Inn|Hotel|Arms|Tavern|Vaults|Brewery|Works|Foundry))\s*[\—\-]?$", sn, re.I)
        if m_pure_bldg:
            bd = m_pure_bldg.group(1).strip()
            sn = ""

    # Step 7: "Guest House" trapped in forename
    if fn and fn.lower() == "guest house":
        if not bd:
            bd = f"{sn} Guest House"
        fn = ""

    # Step 8: "Royal Oak Inn" split across sn and fn
    if sn.lower() == "royal" and fn.lower() == "oak inn":
        bd = "Royal Oak Inn"
        sn = ""
        fn = ""

    # Step 9: Single initial in surname with forename holding surname (swapped)
    if sn and len(sn) == 1 and sn.isalpha() and fn:
        fn_parts = fn.split()
        if len(fn_parts) >= 2:
            sn = fn_parts[-1]
            fn = " ".join(fn_parts[:-1]) + f" {sn}."
        elif len(fn_parts) == 1:
            real_sn = fn_parts[0]
            fn = f"{sn}."
            sn = real_sn

    # Step 10: Clean trades
    if tr:
        tr = expand_trade_abbrev(tr)

    # Strip stray dots/commas
    sn = sn.strip(" ,.-")
    fn = fn.strip(" ,-")
    bd = bd.strip(" ,.-")

    # If both sn and fn are empty, and trade has content, place business in sn
    if not sn and not fn and tr and not bd:
        if BUSINESS_KEYWORDS.search(tr):
            sn = tr
            tr = ""

    return {
        "year": "1971",
        "street": st,
        "house_number": hn,
        "building_name": bd,
        "surname": sn,
        "forename": fn,
        "trade": tr,
    }


def main():
    if not os.path.exists(VOLUME_1971_CSV):
        print(f"Error: {VOLUME_1971_CSV} not found.")
        sys.exit(1)

    print("Healing 1971 records...")
    cleaned_rows = []
    dropped_count = 0
    total_input = 0

    with open(VOLUME_1971_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_input += 1
            res = clean_1971_record(row)
            if res:
                cleaned_rows.append(res)
            else:
                dropped_count += 1

    print(f"\nProcessing summary:")
    print(f"  * Total input lines: {total_input:,}")
    print(f"  * Dropped layout markers & noise: {dropped_count:,}")
    print(f"  * Cleaned resident/business records: {len(cleaned_rows):,}")

    fieldnames = ["year", "street", "house_number", "building_name", "surname", "forename", "trade"]
    with open(VOLUME_1971_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print(f"\n[SUCCESS] Updated {VOLUME_1971_CSV} successfully!")

if __name__ == "__main__":
    main()
