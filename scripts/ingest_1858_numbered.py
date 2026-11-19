#!/usr/bin/env python3
"""Parse numbered Newport entries from raw_tsvs/1858.tsv, write volume_csvs/1858_cleaned.csv, and merge into data.csv."""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_TSV = ROOT / "raw_tsvs" / "1858.tsv"
DATA_CSV = ROOT / "data.csv"
VOL_CSV = ROOT / "volume_csvs" / "1858_cleaned.csv"

NEWPORT_END_LINE = 1630  # Caerleon starts after Newport places of worship / conveyance

OUT_OF_TOWN = {
    "birmingham", "bristol", "london", "cardiff", "abergavenny", "swansea",
    "gloucester", "pontypool", "chepstow", "monmouth", "usk", "caerleon",
    "merthyr", "hereford", "bath", "exeter", "liverpool", "manchester",
}

OCR_STREET_FIXES = {
    "south mar ket street": "south market street",
    "dunfries place": "dumfries place",
    "ruperta street": "ruperra street",
    "tregedar place": "tredegar place",
    "st. woollo's house, stow hill": "stow hill",
}

ABBREV_RULES = [
    (re.compile(r"\bst\.?\b", re.I), "Street"),
    (re.compile(r"\brd\.?\b", re.I), "Road"),
    (re.compile(r"\bpl\.?\b", re.I), "Place"),
    (re.compile(r"\bter\.?\b", re.I), "Terrace"),
    (re.compile(r"\bsq\.?\b", re.I), "Square"),
    (re.compile(r"\bln\.?\b", re.I), "Lane"),
    (re.compile(r"\bpk\.?\b", re.I), "Park"),
]

STREET_SUFFIX_RE = r"(?:[Ss]treet|[Ss]t\.?|[Rr]oad|[Rr]d\.?|[Hh]ill|[Pp]lace|[Pp]l\.?|[Pp]arade|[Rr]ow|[Tt]errace|[Tt]er\.?|[Ll]ane|[Ll]n\.?|[Ss]quare|[Ss]q\.?|[Ww]harf|[Cc]ourt|[Pp]assage|[Bb]uildings|[Vv]illas?)"

ADDR_RE = re.compile(
    r"(?<![a-zA-Z0-9/])(\d+(?:½|[a-zA-Z])?(?:\s*(?:and|&)\s*\d+(?:½|[a-zA-Z])?)?),?\s*"
    r"([A-Z][a-zA-Z'\-]+(?:\s+[A-Z]?[a-zA-Z'\-]+){0,3}\s+" + STREET_SUFFIX_RE + r")"
    r"(?=\b|[,.;:\s]|$)",
)

NON_TRADE_HEADINGS = {
    "NOBILITY, GENTRY AND CLERGY",
    "PLACES OF WORSHIP AND THEIR MINISTERS",
    "PUBLIC BUILDINGS, OFFICES, &C",
    "POST OFFICE",
    "COACHES, OMNIBUSES, &C",
    "CONVEYANCE BY RAILWAY",
    "CARRIERS",
}


def normalize_street(raw_st: str) -> str:
    s = raw_st.strip().rstrip(".,;:")
    s = s.replace("-", " ")
    for pat, rep in ABBREV_RULES:
        s = pat.sub(rep, s)
    s = re.sub(r"\s+", " ", s).strip()
    low = s.lower()
    if low in OCR_STREET_FIXES:
        s = OCR_STREET_FIXES[low]
    return s


def is_out_of_town(text: str, match_end: int) -> bool:
    tail = text[match_end:match_end + 40].lstrip(" ,.;:(").lower()
    for town in OUT_OF_TOWN:
        if tail.startswith(town):
            return True
    return False


def expand_nums(num_expr: str) -> list[str]:
    parts = re.split(r"\s*(?:and|&)\s*", num_expr.strip(), flags=re.I)
    return [p.strip() for p in parts if p.strip()]


def clean_case(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip().strip(",*")
    if s.isupper() and len(s) > 2:
        return s.title()
    return s


def clean_name_part(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip().strip(",")
    if s.isupper() and len(s) > 3:
        s = s.title()
    return s


def heading_to_trade(heading: str) -> str:
    h = heading.strip().rstrip(".:").strip()
    if not h or any(h.upper().startswith(nt) for nt in NON_TRADE_HEADINGS):
        return ""
    h = re.sub(r"\s*\([^)]*\)", "", h).strip()
    h = re.sub(r"\s*--Continued$", "", h, flags=re.I).strip()
    return h.title()


def is_all_caps_heading(cell: str) -> bool:
    c = cell.strip().replace("&c.", "&C.").replace("&c", "&C")
    if len(c) < 4 or ADDR_RE.search(c):
        return False
    if any(ch.islower() for ch in c):
        return False
    return bool(re.match(r"^[A-Z][A-Z\s,&'\-\.]+$", c))


def split_surname_first(name_str: str) -> tuple[str, str]:
    """Split 'Ewins James & Son' or 'Thomas Mr. Benjamin' into (surname, forename)."""
    s = name_str.strip().strip(",*")
    if not s:
        return "", ""
    if re.search(r"(?:\bCompany\b|\bSociety\b|\bBank\b|\bWorks\b)", s, re.I) or "&" in s and "," not in s and len(s.split()) <= 3:
        return clean_case(s), ""
    if " " in s:
        first_w, rest_w = s.split(" ", 1)
        return clean_case(first_w), clean_name_part(rest_w)
    return clean_case(s), ""


def split_forename_first(name_str: str) -> tuple[str, str]:
    """Split 'Henry John Davis' or 'William Christophers' into (surname, forename)."""
    s = name_str.strip().strip(",*")
    if not s:
        return "", ""
    if " and " in s.lower() or " & " in s.lower() or re.search(r"(?:\bCo\.?\b|\bSon\b|\bBrothers\b)", s, re.I):
        return clean_case(s), ""
    parts = s.rsplit(" ", 1)
    if len(parts) == 2:
        return clean_case(parts[1]), clean_name_part(parts[0])
    return clean_case(s), ""


def extract_rows(canonical_streets: dict[str, str]) -> tuple[list[dict], list[tuple]]:
    with open(RAW_TSV, encoding="utf-8", errors="replace") as f:
        lines = [l.rstrip("\n") for l in f][:NEWPORT_END_LINE]

    rows = []
    unmatched = []
    seen = set()
    cur_heading = ""

    for line_no, raw in enumerate(lines, 1):
        if line_no == 1:
            continue
        cells = [("" if c.strip() == "\\N" else c.strip()) for c in raw.split("\t")]
        non_empty = [c for c in cells if c]
        if not non_empty:
            continue

        # Standalone ALL-CAPS section heading (including duplicated cells like ['INNS', '', 'INNS'])
        if len(set(non_empty)) == 1 and is_all_caps_heading(non_empty[0]):
            cur_heading = non_empty[0]
            continue
        if len(cells) >= 3 and cells[2].startswith("NOBILITY, GENTRY"):
            cur_heading = "NOBILITY, GENTRY AND CLERGY"

        # Strip leading empty cells, then extract any inline ALL-CAPS section heading (e.g. L415, L832, L892)
        trimmed = cells[:]
        while trimmed and trimmed[0] == "":
            trimmed.pop(0)

        cleaned_trimmed = []
        for idx, c in enumerate(trimmed):
            if idx > 0 and is_all_caps_heading(c):
                cur_heading = c
                continue
            cleaned_trimmed.append(c)
        trimmed = cleaned_trimmed
        while len(trimmed) < 5:
            trimmed.append("")

        # Extract all numbered addresses across the row
        addrs = []
        seen_addr_in_row = set()
        for blob in trimmed:
            if not blob:
                continue
            for m in ADDR_RE.finditer(blob):
                if is_out_of_town(blob, m.end()):
                    continue
                raw_st = m.group(2)
                for num in expand_nums(m.group(1)):
                    key = (num.lower(), normalize_street(raw_st).lower())
                    if key not in seen_addr_in_row:
                        seen_addr_in_row.add(key)
                        addrs.append((num, raw_st, m.group(0)))

        if not addrs:
            continue

        surname = ""
        forename = ""
        trade = ""
        building_name = ""

        # Case 0: Packed "Surname, Forename" in trimmed[0], empty trimmed[1], trade in trimmed[2] (e.g. L1567, L1580)
        if trimmed[0] and "," in trimmed[0] and not ADDR_RE.search(trimmed[0]) and not trimmed[1] and trimmed[2]:
            p1, p2 = trimmed[0].split(",", 1)
            surname = clean_case(p1)
            forename = clean_name_part(p2)
            trade = trimmed[2]
            for _, _, full_match in addrs:
                trade = re.sub(re.escape(full_match), "", trade, flags=re.I)

        # Case 1: Single packed string in trimmed[0] (e.g. "Ewins James & Son, 13 High st", "Carpenters' Arms, ... 9 High st")
        elif trimmed[0] and not trimmed[1]:
            entry_text = trimmed[0]
            name_part = entry_text
            for _, _, full_match in addrs:
                idx = name_part.lower().find(full_match.lower())
                if idx != -1:
                    name_part = name_part[:idx].strip(" ,.;:-")
                    break

            m_paren = re.search(r"\(([^)]+)\)", name_part)
            paren_note = ""
            if m_paren:
                paren_note = m_paren.group(1).strip()
                name_part = (name_part[:m_paren.start()] + " " + name_part[m_paren.end():]).strip(" ,.;:-")

            # Special sections where first comma-part is Pub or Insurance Company and second is Person
            h_up = cur_heading.upper()
            if ("TAVERN" in h_up or "PUBLIC-HOUSE" in h_up or h_up.startswith("INN")) and "," in name_part:
                pub, landlord = name_part.split(",", 1)
                building_name = clean_case(pub)
                surname, forename = split_forename_first(landlord.strip())
                trade = building_name
            elif "INSURANCE" in h_up or "FIRE" in h_up or "ASSURANCE" in h_up:
                if "," in name_part:
                    ins_co, agent = name_part.split(",", 1)
                    surname, forename = split_forename_first(agent.strip())
                    co_clean = clean_case(ins_co)
                    trade = f"Agent for {co_clean}" + (f" ({paren_note})" if paren_note else "")
                else:
                    surname = clean_case(name_part)
                    trade = paren_note or heading_to_trade(cur_heading)
            elif "," in name_part:
                p1, p2 = name_part.split(",", 1)
                p2_s = p2.strip()
                if re.match(r"^(?:jun\.?|sen\.?|esq\.?|mr\.?|mrs\.?|miss|rev\.?|bart\.?)", p2_s, re.I):
                    surname, forename = split_surname_first(p1)
                    forename = f"{forename}, {p2_s}".strip(", ")
                else:
                    surname, forename = split_surname_first(p1)
                    trade = p2_s
                if paren_note:
                    trade = f"{trade} ({paren_note})".strip() if trade else paren_note
            else:
                surname, forename = split_surname_first(name_part)
                if paren_note:
                    trade = paren_note

        # Case 2: Multi-column row: ['Constable', 'grocer & sundries', '109 Commercial rd'] or ['Jones', 'Thomas Jacob', '5 High st']
        else:
            c0, c1, c2, c3 = trimmed[0], trimmed[1], trimmed[2], trimmed[3]
            if c1 and c1[0].islower() and not c1.startswith(("the ", "jun", "sen")):
                surname = clean_case(c0)
                trade = c1
            elif c0 and c1:
                surname = clean_case(c0)
                forename = clean_name_part(c1)
                # Drop repeated surname in c2 (e.g. L1298: Evans | David Lawford | Evans)
                if c2 and c2.rstrip(",").lower() == c0.rstrip(",").lower():
                    c2 = c3
                    c3 = ""
                # Handle middle name in c2 before address (e.g. L157: Davis | Henry | John, 7 High st)
                if c2 and ADDR_RE.search(c2):
                    before_addr = c2
                    for _, _, full_match in addrs:
                        idx = before_addr.lower().find(full_match.lower())
                        if idx != -1:
                            before_addr = before_addr[:idx].strip(" ,.;:-")
                            break
                    if before_addr and re.match(r"^[A-Z][a-z'\-\.]+$", before_addr) and not before_addr.startswith("("):
                        forename = f"{forename} {clean_name_part(before_addr)}".strip()
                    else:
                        trade = before_addr
                elif c2 and not c2.startswith("(") and len(c2) < 20 and not any(ch.isdigit() for ch in c2):
                    forename = f"{forename} {clean_name_part(c2)}".strip()
                    rest = c3
                    if rest:
                        r_clean = rest
                        for _, _, full_match in addrs:
                            r_clean = re.sub(re.escape(full_match), "", r_clean, flags=re.I)
                        r_clean = re.sub(r"-\s*\(See advertisement\)", "", r_clean, flags=re.I).strip(" ,.;:-()")
                        if r_clean:
                            trade = r_clean
                elif c2:
                    r_clean = c2
                    for _, _, full_match in addrs:
                        r_clean = re.sub(re.escape(full_match), "", r_clean, flags=re.I)
                    r_clean = re.sub(r"-\s*\(See advertisement\)", "", r_clean, flags=re.I).strip(" ,.;:-()")
                    if r_clean:
                        trade = r_clean

        if not trade:
            trade = heading_to_trade(cur_heading)

        trade = re.sub(r"\s+", " ", trade).strip(" ,.;:-")
        if trade and trade.lower() in {
            f"{forename} {surname}".strip().lower(),
            f"{surname} {forename}".strip().lower(),
            surname.lower(),
        }:
            trade = ""

        for _, _, full_match in addrs:
            surname = re.sub(re.escape(full_match), "", surname, flags=re.I)
            forename = re.sub(re.escape(full_match), "", forename, flags=re.I)
        surname = re.sub(r"\s+", " ", surname).strip(" ,.;:-")
        forename = re.sub(r"\s+", " ", forename).strip(" ,.;:-")

        if not surname:
            continue

        for num, raw_st, _ in addrs:
            nst = normalize_street(raw_st)
            canonical = canonical_streets.get(nst.lower())
            if not canonical:
                unmatched.append((line_no, num, nst, surname, forename, trade))
                continue

            dedup_key = (canonical, num, surname.lower(), forename.lower())
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            m_num = re.match(r"^(\d+)(.*)$", num)
            sort_num = int(m_num.group(1)) if m_num else 0
            sort_suf = (m_num.group(2) if m_num else "").lower()

            rows.append({
                "year": "1858",
                "street": canonical,
                "house_number": num,
                "building_name": building_name,
                "surname": surname.strip().rstrip(","),
                "forename": forename.strip().rstrip(","),
                "trade": trade,
                "source_type": "commercial_directory",
                "_sort_num": sort_num,
                "_sort_suf": sort_suf,
                "_line": line_no,
            })

    return rows, unmatched


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print stats and samples without writing files")
    args = parser.parse_args()

    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        existing_rows = [r for r in reader if r.get("year") != "1858"]

    canonical_streets = {}
    for r in existing_rows:
        st = (r.get("street") or "").strip()
        if st and st.lower() not in canonical_streets:
            canonical_streets[st.lower()] = st

    rows, unmatched = extract_rows(canonical_streets)
    rows.sort(key=lambda r: (r["street"].lower(), r["_sort_num"], r["_sort_suf"], r["surname"].lower()))

    print(f"Extracted {len(rows)} numbered 1858 rows across {len({r['street'] for r in rows})} streets.")
    print(f"Unmatched numbered occurrences: {len(unmatched)}")

    if args.dry_run:
        print("\nSample High Street rows (first 20):")
        for r in [x for x in rows if x["street"] == "High Street"][:20]:
            print(f"  L{r['_line']:4d} | No.{r['house_number']:4s} | {r['surname']}, {r['forename']} | {r['trade']}")
        print("\nSample Commercial Street rows (first 15):")
        for r in [x for x in rows if x["street"] == "Commercial Street"][:15]:
            print(f"  L{r['_line']:4d} | No.{r['house_number']:4s} | {r['surname']}, {r['forename']} | {r['trade']}")
        return

    clean_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    with open(VOL_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(clean_rows)

    rows_pre = [r for r in existing_rows if r.get("year") == "1848"]
    rows_post = [r for r in existing_rows if r.get("year") != "1848"]
    merged = rows_pre + clean_rows + rows_post

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(merged)

    print(f"Wrote {VOL_CSV.name} ({len(clean_rows)} rows) and merged into {DATA_CSV.name} ({len(merged):,} total rows).")


if __name__ == "__main__":
    main()
