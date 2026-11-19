#!/usr/bin/env python3
"""Parse numbered Newport entries from raw_tsvs/1865.tsv, write volume_csvs/1865_cleaned.csv, and merge into data.csv."""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_TSV = ROOT / "raw_tsvs" / "1865.tsv"
DATA_CSV = ROOT / "data.csv"
VOL_CSV = ROOT / "volume_csvs" / "1865_cleaned.csv"

NEWPORT_END_LINE = 1818  # Line 1819+ is Caerleon / Christchurch / Maindee

OUT_OF_TOWN = {
    "birmingham", "bristol", "london", "cardiff", "abergavenny", "swansea",
    "gloucester", "pontypool", "chepstow", "monmouth", "usk", "caerleon",
    "merthyr", "hereford", "bath", "exeter", "liverpool", "manchester",
}

OCR_STREET_FIXES = {
    "ruperta street": "ruperra street",
    "cla rence place": "clarence place",
    "tregedar place": "tredegar place",
    "lansdowne place": "lansdown place",
    "uppercross street": "upper cross street",
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

STREET_SUFFIX_RE = r"(?:Street|St\.?|Road|Rd\.?|Hill|Place|Pl\.?|Parade|Row|Terrace|Ter\.?|Lane|Ln\.?|Square|Sq\.?|Wharf|Court|Passage|Buildings|Villas?)"

# Matches either "4 and 5 Commercial street" or "5 Commercial street"
ADDR_RE = re.compile(
    r"(?<![\w/])(\d+(?:½|[a-zA-Z])?(?:\s*(?:and|&)\s*\d+(?:½|[a-zA-Z])?)?),?\s+"
    r"([A-Z][a-zA-Z'\-]+(?:\s+[A-Z]?[a-zA-Z'\-]+){0,3}\s+" + STREET_SUFFIX_RE + r")"
    r"(?=\b|[,.;:\s]|$)",
    re.I,
)


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
    s = re.sub(r"\s+", " ", s).strip().strip(",")
    if s.isupper() and len(s) > 2:
        return s.title()
    return s


def clean_name_part(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip().strip(",")
    if s.isupper() and len(s) > 3:
        s = s.title()
    return s


def split_entry_string(text: str) -> tuple[str, str, str]:
    """Split 'SURNAME, Forename, trade and address...' into (surname, forename, rest)."""
    text = text.strip()
    m = re.match(r"^([A-Z][A-Za-z'\-\s&]+?),\s*([^,]+?)(?:,\s*(.*))?$", text)
    if not m:
        return clean_case(text), "", ""
    sur = clean_case(m.group(1))
    fore = clean_name_part(m.group(2))
    rest = (m.group(3) or "").strip()
    # Handle "HARRIS, GEORGE, OLD GREEN" -> sur=Harris, fore=George, rest=OLD GREEN
    return sur, fore, rest


def clean_trade(trade: str) -> str:
    t = trade.replace("\\N", " ").strip()
    t = re.sub(r"\bPriv\.?\s*res\.?[^;.]*", "", t, flags=re.I)
    t = re.sub(r"\(see advt\.[^)]*\)", "", t, flags=re.I)
    t = re.sub(r"\s*,\s*,+", ", ", t)
    t = re.sub(r"\s+", " ", t).strip(" ,.;:-")
    return t


def parse_private_resident_half(name_cell: str, rest_cell: str) -> tuple[str, str, str, list[tuple[str, str, str]]]:
    combined = f"{name_cell} {rest_cell}".strip()
    addrs = []
    for m in ADDR_RE.finditer(combined):
        if not is_out_of_town(combined, m.end()):
            for n in expand_nums(m.group(1)):
                addrs.append((n, m.group(2), m.group(0)))
    if not addrs:
        return "", "", "", []
    sur, fore, _ = split_entry_string(name_cell)
    return sur, fore, "", addrs


def extract_rows(canonical_streets: dict[str, str]) -> tuple[list[dict], list[tuple]]:
    with open(RAW_TSV, encoding="utf-8", errors="replace") as f:
        lines = [l.rstrip("\n") for l in f][:NEWPORT_END_LINE]

    rows = []
    unmatched = []
    seen = set()

    for line_no, raw in enumerate(lines, 1):
        if line_no == 1:
            continue
        cells = [("" if c.strip() == "\\N" else c.strip()) for c in raw.split("\t")]

        # 2-column Private Residents rows (L234..352)
        if 234 <= line_no <= 352:
            padded = cells + [""] * max(0, 6 - len(cells))
            if padded[1] and "," in padded[1] and padded[3] and "," in padded[3]:
                for n_cell, r_cell in [(padded[1], padded[2]), (padded[3], padded[4])]:
                    s, fn, tr, addrs = parse_private_resident_half(n_cell, r_cell)
                    for num, raw_st, _ in addrs:
                        _add_match(rows, unmatched, seen, canonical_streets, line_no, num, raw_st, s, fn, tr)
                continue
            if padded[1] and "," in padded[1] and len(padded) >= 5 and padded[4] and "," in padded[4]:
                for n_cell, r_cell in [(padded[1], f"{padded[2]} {padded[3]}"), (padded[4], padded[5])]:
                    s, fn, tr, addrs = parse_private_resident_half(n_cell, r_cell)
                    for num, raw_st, _ in addrs:
                        _add_match(rows, unmatched, seen, canonical_streets, line_no, num, raw_st, s, fn, tr)
                continue
            if padded[1] and "," in padded[1] and padded[2] and "," in padded[2] and not ADDR_RE.search(padded[2]):
                first_name = ", ".join(padded[1].split(",", 2)[:2]) if padded[1].count(",") >= 2 else padded[1]
                for n_cell, r_cell in [(first_name, padded[1]), (padded[2], padded[3])]:
                    s, fn, tr, addrs = parse_private_resident_half(n_cell, r_cell)
                    for num, raw_st, _ in addrs:
                        _add_match(rows, unmatched, seen, canonical_streets, line_no, num, raw_st, s, fn, tr)
                continue

        # Normalize 7-column shifted rows (e.g. ['', '', 'Henry', 'Mullock', 'bookseller...', 'Mullock, Henry', ''])
        if len(cells) >= 7 and cells[0] == "" and cells[1] == "" and cells[2] and cells[3] and not ADDR_RE.search(cells[3]) and len(cells[3]) < 30:
            cells = cells[1:]

        while len(cells) < 6:
            cells.append("")

        c_num, c_fore, c_sur, c_trade, c_biz, c_notes = cells[:6]

        # Extract all numbered addresses in the row
        addrs = []
        seen_addr_in_row = set()
        for blob in (c_notes, c_biz, c_trade, c_fore, c_sur):
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

        if 234 <= line_no <= 352:
            if c_fore and c_sur:
                if c_sur.startswith(("Mr", "Mrs", "Miss", "Rev", "Esq")) or "Esq." in c_sur:
                    surname = clean_case(c_fore)
                    forename = clean_name_part(c_sur)
                else:
                    surname = clean_case(c_sur)
                    forename = clean_name_part(c_fore)
            elif c_fore and "," in c_fore:
                surname, forename, _ = split_entry_string(c_fore)
            elif c_sur:
                surname = clean_case(c_sur)
        else:
            # Check for packed full entry in c_fore or c_sur (e.g. L1287, L410, L878)
            if c_fore and not c_sur and "," in c_fore:
                surname, forename, extra = split_entry_string(c_fore)
                trade = f"{extra} {c_trade}".strip() if extra else c_trade
            elif c_sur and not c_fore and "," in c_sur:
                surname, forename, extra = split_entry_string(c_sur)
                trade = f"{extra} {c_trade}".strip() if extra else c_trade
                # Fix "William, Clarke" OCR swap where forename is actually surname
                if surname in {"William", "John", "Thomas", "James", "George", "Henry", "Charles", "Edward"} and forename and not " " in forename:
                    surname, forename = forename, surname
            elif c_sur and c_fore:
                if c_sur.startswith("(") and "firm of" in c_sur.lower():
                    surname = clean_case(c_fore)
                    forename = ""
                elif "," in c_fore and not any(t in c_fore.lower() for t in ["esq", "mr.", "mrs.", "miss", "rev."]):
                    parts = [p.strip() for p in c_fore.split(",", 1)]
                    forename = clean_name_part(parts[0])
                    if parts[1]:
                        trade = parts[1]
                    surname = clean_case(c_sur)
                else:
                    surname = clean_case(c_sur)
                    forename = clean_name_part(c_fore)
            elif c_sur and not c_fore:
                surname = clean_case(c_sur)
            elif c_trade and re.match(r"^[A-Z]{2,}[A-Z\s'\-\.&]*,\s*[a-zA-Z]", c_trade):
                # e.g. "BOWMAN, JOHN FREDk., ..." or "PICKFORD AND CO., agents for..."
                first_part, rest_part = c_trade.split(",", 1)
                # Check if rest_part starts with a forename (Capitalized word/title) vs lowercase trade
                if re.match(r"^(?:Mr\.|Mrs\.|Miss|Rev\.|[A-Z][a-zA-Z\.]+\b)", rest_part.strip()):
                    surname, forename, trade = split_entry_string(c_trade)
                else:
                    surname = clean_case(first_part)
                    trade = rest_part.strip()
            elif c_biz and not c_sur and not c_fore:
                surname = clean_case(c_biz.split(",")[0])

            if forename.lower() == surname.lower():
                forename = ""

            raw_trade = trade or c_trade or ""
            for _, _, full_match in addrs:
                raw_trade = re.sub(re.escape(full_match) + r"(?:\s*\([^)]*\))?", "", raw_trade, flags=re.I)
            if c_biz and c_biz != c_trade and not ADDR_RE.fullmatch(c_biz.strip()):
                if not raw_trade and c_biz.lower() != surname.lower():
                    raw_trade = c_biz
            trade = clean_trade(raw_trade)

        if not surname and not trade:
            continue

        for num, raw_st, _ in addrs:
            _add_match(rows, unmatched, seen, canonical_streets, line_no, num, raw_st, surname, forename, trade)

    return rows, unmatched


def _add_match(rows, unmatched, seen, canonical_streets, line_no, num, raw_st, surname, forename, trade):
    nst = normalize_street(raw_st)
    canonical = canonical_streets.get(nst.lower())
    if not canonical:
        unmatched.append((line_no, num, nst, surname, forename, trade))
        return

    dedup_key = (canonical, num, surname.lower(), forename.lower())
    if dedup_key in seen:
        return
    seen.add(dedup_key)

    m_num = re.match(r"^(\d+)(.*)$", num)
    sort_num = int(m_num.group(1)) if m_num else 0
    sort_suf = (m_num.group(2) if m_num else "").lower()

    rows.append({
        "year": "1865",
        "street": canonical,
        "house_number": num,
        "building_name": "",
        "surname": surname.strip().rstrip(","),
        "forename": forename.strip().rstrip(","),
        "trade": trade,
        "source_type": "commercial_directory",
        "_sort_num": sort_num,
        "_sort_suf": sort_suf,
        "_line": line_no,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print stats and samples without writing files")
    args = parser.parse_args()

    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        existing_rows = [r for r in reader if r.get("year") != "1865"]

    canonical_streets = {}
    for r in existing_rows:
        st = (r.get("street") or "").strip()
        if st and st.lower() not in canonical_streets:
            canonical_streets[st.lower()] = st

    rows, unmatched = extract_rows(canonical_streets)
    rows.sort(key=lambda r: (r["street"].lower(), r["_sort_num"], r["_sort_suf"], r["surname"].lower()))

    print(f"Extracted {len(rows)} numbered 1865 rows across {len({r['street'] for r in rows})} streets.")
    print(f"Unmatched numbered occurrences: {len(unmatched)}")

    if args.dry_run:
        print("\nSample High Street rows:")
        for r in [x for x in rows if x["street"] == "High Street"][:20]:
            print(f"  L{r['_line']:4d} | No.{r['house_number']:4s} | {r['surname']}, {r['forename']} | {r['trade']}")
        print("\nSample Commercial Street rows (first 15):")
        for r in [x for x in rows if x["street"] == "Commercial Street"][:15]:
            print(f"  L{r['_line']:4d} | No.{r['house_number']:4s} | {r['surname']}, {r['forename']} | {r['trade']}")
        print("\nCheck for empty surnames or weird names:")
        weird = [r for r in rows if not r["surname"] or r["surname"].startswith("(") or len(r["surname"]) <= 1]
        print(f"  Weird/empty surnames: {len(weird)}")
        for r in weird[:10]:
            print(f"    L{r['_line']:4d} | {r['street']} {r['house_number']} | {r['surname']!r} / {r['forename']!r} | {r['trade']}")
        return

    clean_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    with open(VOL_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(clean_rows)

    rows_1848 = [r for r in existing_rows if r.get("year") == "1848"]
    rows_later = [r for r in existing_rows if r.get("year") != "1848"]
    merged = rows_1848 + clean_rows + rows_later

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(merged)

    print(f"Wrote {VOL_CSV.name} ({len(clean_rows)} rows) and merged into {DATA_CSV.name} ({len(merged):,} total rows).")


if __name__ == "__main__":
    main()
