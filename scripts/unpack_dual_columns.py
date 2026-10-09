#!/usr/bin/env python3
"""
Unpack Dual-Column Merged Records for Newport Street Directory Project
======================================================================
Identifies dual-column horizontal OCR mergers in data.csv (discontinuous N1-N2)
and reconstructs them into two distinct, clean records using explicit
multi-column tab breaks preserved in raw_tsvs/*.tsv.
"""

import csv
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "scripts" else SCRIPT_DIR
os.chdir(PROJECT_ROOT)

DATA_CSV = "data.csv"
RAW_DIR = "raw_tsvs"

def parse_chunk(tokens):
    if not tokens:
        return ("", "", "", "", "")
    h_num = ""
    surname = ""
    forename = ""
    trade = ""
    bldg = ""
    
    t0 = tokens[0].strip()
    if re.match(r"^\d+[A-Za-z]?$", t0):
        h_num = t0
        rem = tokens[1:]
    else:
        rem = tokens
        
    if not rem:
        return (h_num, "", "", "", "")
        
    if len(rem) == 1:
        text = rem[0]
        if "," in text:
            name_p, trade_p = text.split(",", 1)
            trade = trade_p.strip(" .,")
            np_parts = name_p.strip().split(maxsplit=1)
            if len(np_parts) == 2:
                surname, forename = np_parts[0], np_parts[1]
            else:
                surname = name_p.strip()
        else:
            np_parts = text.strip().split(maxsplit=1)
            if len(np_parts) == 2:
                surname, forename = np_parts[0], np_parts[1]
            else:
                surname = text.strip()
    else:
        surname = rem[0].strip(" .,")
        rest = " ".join(rem[1:]).strip()
        if "," in rest:
            fn_p, tr_p = rest.split(",", 1)
            forename = fn_p.strip(" .,")
            trade = tr_p.strip(" .,")
        else:
            forename = rest.strip(" .,")
            
    return (h_num, surname, forename, trade, bldg)


def load_raw_tsv_cache():
    tsv_cache = {}
    years = [
        "1878", "1882", "1887", "1890", "1893", "1894", "1898", "1899",
        "1900", "1902", "1903", "1910", "1913", "1920", "1925", "1927", "1936", "1971"
    ]
    for yr in years:
        p = os.path.join(RAW_DIR, f"{yr}.tsv")
        if not os.path.exists(p):
            continue
        by_key = {}
        current_st = ""
        second_st = ""
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                tokens = [t.strip() for t in line.rstrip("\n").split("\t") if t.strip()]
                if not tokens:
                    continue
                t0 = tokens[0]
                if any(suf in t0.lower() for suf in ["street", "road", "lane", "place", "terrace", "avenue", "crescent", "parade", "square", "hill"]) and len(tokens) <= 2:
                    current_st = re.sub(r"[\s\-—]+continued\b", "", t0, flags=re.I).strip("., ").lower()
                    second_st = ""
                    continue

                # Detect secondary street headers on parallel column lines
                for tok in tokens[1:]:
                    if any(suf in tok.lower() for suf in ["street", "road", "lane", "place", "terrace", "avenue", "crescent", "parade", "square", "hill"]) and len(tok.split()) <= 3 and not any(c.isdigit() for c in tok):
                        second_st = re.sub(r"[\s\-—]+continued\b", "", tok, flags=re.I).strip("., ")
                        break

                if len(tokens) >= 3 and tokens[0].isdigit():
                    for idx in range(1, len(tokens)):
                        tok = tokens[idx]
                        n2 = ""
                        rem_tokens = []
                        if tok.isdigit() and int(tok) > 0 and len(tok) <= 3:
                            n2 = tok
                            rem_tokens = tokens[idx:]
                        else:
                            m_tok = re.match(r"^(\d+)\s+(.+)$", tok)
                            if m_tok and int(m_tok.group(1)) > 0 and len(m_tok.group(1)) <= 3:
                                n2 = m_tok.group(1)
                                rem_tokens = [n2, m_tok.group(2)] + tokens[idx+1:]
                        if n2:
                            n1 = tokens[0]
                            k1 = (yr, current_st, f"{n1}-{n2}")
                            k2 = (yr, f"{n1}-{n2}")
                            val = (tokens[:idx], rem_tokens, second_st)
                            by_key[k1] = val
                            if k2 not in by_key:
                                by_key[k2] = val
                            break
        tsv_cache[yr] = by_key
    return tsv_cache


def is_valid_property_range(hn):
    m = re.match(r"^(\d+)-(\d+)$", hn)
    if not m:
        return False
    n1, n2 = int(m.group(1)), int(m.group(2))
    diff = n2 - n1
    s1, s2 = str(n1), str(n2)
    # Contiguous ranges (e.g. 1-2, 16-17, 72-75)
    if 0 < diff <= 4:
        return True
    # Abbreviated ranges (e.g. 149-50 for 149-150)
    if n2 < n1 and len(s1) > len(s2) and 0 < int(s1[:-len(s2)] + s2) - n1 <= 4:
        return True
    return False


def unpack_dataset():
    tsv_cache = load_raw_tsv_cache()
    print("Loaded multi-column raw TSV lookup cache.")
    
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        records = list(reader)

    unpacked_rows = []
    unpacked_count = 0

    for r in records:
        hn = r.get("house_number", "").strip()
        yr = r.get("year", "").strip()
        st = r.get("street", "").strip()
        st_low = st.lower()

        # Check if record is a candidate for dual-column unpacking
        m = re.match(r"^(\d+)-(\d+)$", hn)
        if m and not is_valid_property_range(hn):
            pair_val = None
            if yr in tsv_cache:
                if (yr, st_low, hn) in tsv_cache[yr]:
                    pair_val = tsv_cache[yr][(yr, st_low, hn)]
                elif (yr, hn) in tsv_cache[yr]:
                    pair_val = tsv_cache[yr][(yr, hn)]
            
            if pair_val:
                tokens1 = pair_val[0]
                tokens2 = pair_val[1]
                sec_st = pair_val[2] if len(pair_val) > 2 and pair_val[2] else st
                p1 = parse_chunk(tokens1)
                p2 = parse_chunk(tokens2)
                if p1[1] and p2[1]:  # Both chunks contain valid surnames
                    row1 = {
                        "year": yr,
                        "street": st,
                        "house_number": p1[0] or m.group(1),
                        "building_name": p1[4] or r.get("building_name", ""),
                        "surname": p1[1],
                        "forename": p1[2],
                        "trade": p1[3],
                        "source_type": r.get("source_type", "")
                    }
                    row2 = {
                        "year": yr,
                        "street": sec_st,
                        "house_number": p2[0] or m.group(2),
                        "building_name": p2[4] or "",
                        "surname": p2[1],
                        "forename": p2[2],
                        "trade": p2[3],
                        "source_type": r.get("source_type", "")
                    }
                    unpacked_rows.append(row1)
                    unpacked_rows.append(row2)
                    unpacked_count += 1
                    continue

        unpacked_rows.append(r)

    print(f"Successfully unpacked {unpacked_count} dual-column rows into {unpacked_count * 2} separate records.")
    print(f"Total dataset size increased from {len(records)} to {len(unpacked_rows)} records.")

    # Write back to data.csv
    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(unpacked_rows)

    print(f"Saved updated master dataset to {DATA_CSV}.")

if __name__ == "__main__":
    unpack_dataset()
