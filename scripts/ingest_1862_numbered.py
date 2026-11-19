#!/usr/bin/env python3
"""Parse numbered Newport entries from raw_tsvs/1862.tsv, write volume_csvs/1862_cleaned.csv, and merge into data.csv."""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_TSV = ROOT / "raw_tsvs" / "1862.tsv"
DATA_CSV = ROOT / "data.csv"
VOL_CSV = ROOT / "volume_csvs" / "1862_cleaned.csv"

OUT_OF_TOWN = {
    "birmingham", "bristol", "london", "cardiff", "abergavenny", "swansea",
    "gloucester", "pontypool", "chepstow", "monmouth", "usk", "caerleon",
    "merthyr", "hereford", "bath", "exeter", "liverpool", "manchester",
}

OCR_STREET_FIXES = {
    "llallarth street": "llanarth street",
    "snow hill": "stow hill",
    "mercial road": "commercial road",
    "temp street": "temple street",
    "fredericks street": "frederick street",
    "mount joy street": "mountjoy street",
    "jones's street": "jones street",
    "cambric place": "cambria place",
    "ruperta street": "ruperra street",
    "tregedar place": "tredegar place",
    "commercial thad": "commercial road",
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

STREET_SUFFIX_RE = r"(?:Street|St\.?|Road|Rd\.?|Hill|Place|Pl\.?|Parade|Row|Terrace|Ter\.?|Lane|Ln\.?|Square|Sq\.?|Wharf|Court|Passage|Buildings|Villas?|Thad)"

ADDR_RE = re.compile(
    r"(?<![\w/])(\d+(?:½|[a-zA-Z])?(?:\s*(?:and|&)\s*\d+(?:½|[a-zA-Z])?)?),?\s+"
    r"([A-Z][a-zA-Z'\-]+(?:\s+[A-Z]?[a-zA-Z'\-]+){0,3}\s+" + STREET_SUFFIX_RE + r")"
    r"(?=\b|[,.;:\s]|$)",
    re.I,
)

COMMON_FORENAMES = {
    "william", "wm.", "john", "jno.", "thomas", "thos.", "james", "jas.",
    "george", "geo.", "henry", "hy.", "charles", "chas.", "edward", "edwd.",
    "samuel", "richard", "richd.", "robert", "robt.", "joseph", "benjamin",
    "alfred", "edwin", "frederick", "walter", "david", "daniel", "stephen",
    "margaret", "mary", "ann", "elizabeth", "jane", "sarah", "harriet", "maria",
    "mr.", "mrs.", "miss", "misses", "rev.", "dr.",
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
    s = re.sub(r"\s+", " ", s).strip().strip(",")
    if s.isupper() and len(s) > 2:
        return s.title()
    return s


def clean_name_part(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip().strip(",")
    if s.isupper() and len(s) > 3:
        s = s.title()
    return s


def clean_trade(trade: str) -> str:
    t = trade.replace("\\N", " ").strip()
    t = re.sub(r'^\{"business":\s*"(.*)"\}$', r"\1", t)
    t = t.replace('\\"', '"')
    t = re.sub(r"\(See [Aa]dvertisement[^)]*\)", "", t)
    t = re.sub(r"\bh\.,?\s*[^;.]*$", "", t, flags=re.I)
    t = re.sub(r"\s*,\s*,+", ", ", t)
    t = re.sub(r"\s+", " ", t).strip(" ,.;:-")
    if t.lower() in {"and", "&", "or", "at", "of"}:
        return ""
    return t


def looks_like_forename(s: str) -> bool:
    low = s.strip().lower()
    if not low:
        return False
    first = low.split()[0]
    if first in COMMON_FORENAMES:
        return True
    if re.match(r"^(?:[A-Z]\.\s*)+$", s.strip()):
        return True
    return False


def extract_rows(canonical_streets: dict[str, str]) -> tuple[list[dict], list[tuple]]:
    with open(RAW_TSV, encoding="utf-8", errors="replace") as f:
        lines = [l.rstrip("\n") for l in f]

    rows = []
    unmatched = []
    seen = set()
    cur_alpha = "A"

    for line_no, raw in enumerate(lines, 1):
        if line_no == 1:
            continue
        cells = [("" if c.strip() == "\\N" else c.strip()) for c in raw.split("\t")]

        # Normalize shifted rows where col 1 is empty (works for 5, 6, 7+ cols and when col 0 has house number)
        if len(cells) >= 5 and cells[1] == "" and cells[2] and cells[3]:
            cells = [cells[0]] + cells[2:]

        while len(cells) < 6:
            cells.append("")

        c_num, c_c1, c_c2, c_c3, c_c4, c_c5 = cells[:6]

        # Drop repeated forename in c_c3 (e.g. Richards | Richard | Richard | saddler...)
        if c_c2 and c_c3 and c_c3.rstrip(",").lower() == c_c2.rstrip(",").lower() and c_c4:
            c_c3 = c_c4
            c_c4 = c_c5
        # Merge middle name in c_c3 into forename when c_c4 holds trade/address (e.g. Pain | John | David | ...)
        elif c_c1 and c_c2 and c_c3 and c_c4 and re.match(r"^[A-Z][a-z'\-]+$", c_c3.rstrip(",")) and c_c3.lower() not in {"engineer", "accountant", "pilot", "grocer", "butcher", "tailor"}:
            c_c2 = f"{c_c2} {c_c3.rstrip(',')}"
            c_c3 = c_c4
            c_c4 = c_c5

        # Handle Clergy/Gentry (L5..125) where c_c1 ends with ", <num>" (e.g. ['Alfred, 3', 'Rose', 'Dorset place...'])
        if line_no <= 125 and c_c1 and re.search(r",\s*\d+$", c_c1):
            m_num_tail = re.search(r",\s*(\d+)$", c_c1)
            if m_num_tail:
                num_tail = m_num_tail.group(1)
                c_c1 = c_c1[:m_num_tail.start()].strip()
                if c_c3 and not re.match(r"^\d", c_c3):
                    c_c3 = f"{num_tail}, {c_c3}"
                elif c_c4 and not re.match(r"^\d", c_c4):
                    c_c4 = f"{num_tail}, {c_c4}"

        # Extract all numbered addresses in the row
        addrs = []
        seen_addr_in_row = set()
        for blob in (c_c5, c_c4, c_c3, c_c2, c_c1):
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

        if line_no <= 125:
            # Clergy, Gentry, etc.: c_c1 is Forename, c_c2 is Surname
            forename = clean_name_part(c_c1)
            surname = clean_case(c_c2)
            # Check if c_c3 has Esq./Rev. title rather than address
            if c_c3 and not ADDR_RE.search(c_c3) and any(t in c_c3.lower() for t in ["rev.", "esq.", "minister", "baptist", "wesleyan"]):
                if "esq" in c_c3.lower() or "rev" in c_c3.lower():
                    forename = f"{forename} {c_c3.split(',')[0].strip()}".strip()
        else:
            # Commercial / Trades section (L126..1893)
            # Pattern A: ['', 'Caldicott', 'Mrs., milliner and straw bonnet maker, 8, Commercial street']
            if c_c1 and c_c2 and "," in c_c2 and ADDR_RE.search(c_c2) and not c_c3:
                surname = clean_case(c_c1)
                parts = c_c2.split(",", 1)
                forename = clean_name_part(parts[0])
                trade = parts[1].strip()
            # Pattern B0: c_c2 is lowercase -> c_c2 is actually trade, and c_c1 is full name/firm (e.g. 'Matthews Jno. | corn and flour dealer')
            elif c_c1 and c_c2 and c_c2[0].islower() and not c_c2.startswith(("the ", "of ")):
                trade = c_c2
                if any(w in c_c1.lower() for w in [" & ", " and ", "co.", "son", "bros", "brothers"]):
                    surname = clean_case(c_c1)
                    forename = ""
                elif re.match(r"^(Mc\.?\s+[A-Z][a-z'\-]+)\s+(.+)$", c_c1):
                    m_mc = re.match(r"^(Mc\.?\s+[A-Z][a-z'\-]+)\s+(.+)$", c_c1)
                    surname = clean_case(m_mc.group(1))
                    forename = clean_name_part(m_mc.group(2))
                elif " " in c_c1:
                    first_w, rest_w = c_c1.split(" ", 1)
                    surname = clean_case(first_w)
                    forename = clean_name_part(rest_w)
                else:
                    surname = clean_case(c_c1)
                    forename = ""
            # Pattern B: Forename in c_c1, Surname in c_c2 (e.g. L629..639 'Margaret | Harris', L872 'James & Son | Lewis')
            elif c_c1 and c_c2 and (
                (looks_like_forename(c_c1) and not looks_like_forename(c_c2) and len(c_c2.split()) == 1)
                or (c_c2[0].isalpha() and c_c2[0].upper() == cur_alpha and c_c1[0].upper() != cur_alpha and len(c_c2.split()) == 1)
            ):
                forename = clean_name_part(c_c1)
                surname = clean_case(c_c2)
                trade = c_c3
            # Pattern C: Standard 1862.tsv (Surname in c_c1, Forename in c_c2, Trade in c_c3)
            elif c_c1 and c_c2:
                surname = clean_case(c_c1)
                forename = clean_name_part(c_c2)
                trade = c_c3
                # Check if c_c3 is '{"business": ""}' (e.g. L285 Chappell Mr. Daniel)
                if trade.startswith("{") and clean_trade(trade) == "":
                    trade = ""
                if surname and surname[0].isalpha() and surname[0].upper() >= cur_alpha:
                    if ord(surname[0].upper()) - ord(cur_alpha) <= 2:
                        cur_alpha = surname[0].upper()
            elif c_c1 and not c_c2:
                surname = clean_case(c_c1)
                trade = c_c3
            elif c_c2 and not c_c1:
                surname = clean_case(c_c2)
                trade = c_c3

            if not trade and c_c4 and not c_c4.startswith(surname):
                if not ADDR_RE.search(c_c4) and c_c4.strip().lower() not in {"pill", "baneswell", "pillgwenlly", "maindee"}:
                    trade = c_c4

            for _, _, full_match in addrs:
                trade = re.sub(re.escape(full_match) + r"(?:\s*\([^)]*\))?", "", trade, flags=re.I)
            trade = clean_trade(trade)

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
                "year": "1862",
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

    return rows, unmatched


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print stats and samples without writing files")
    args = parser.parse_args()

    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        existing_rows = [r for r in reader if r.get("year") != "1862"]

    canonical_streets = {}
    for r in existing_rows:
        st = (r.get("street") or "").strip()
        if st and st.lower() not in canonical_streets:
            canonical_streets[st.lower()] = st

    rows, unmatched = extract_rows(canonical_streets)
    rows.sort(key=lambda r: (r["street"].lower(), r["_sort_num"], r["_sort_suf"], r["surname"].lower()))

    print(f"Extracted {len(rows)} numbered 1862 rows across {len({r['street'] for r in rows})} streets.")
    print(f"Unmatched numbered occurrences: {len(unmatched)}")

    if args.dry_run:
        print("\nSample High Street rows:")
        for r in [x for x in rows if x["street"] == "High Street"][:20]:
            print(f"  L{r['_line']:4d} | No.{r['house_number']:4s} | {r['surname']}, {r['forename']} | {r['trade']}")
        print("\nSample Commercial Street rows (first 15):")
        for r in [x for x in rows if x["street"] == "Commercial Street"][:15]:
            print(f"  L{r['_line']:4d} | No.{r['house_number']:4s} | {r['surname']}, {r['forename']} | {r['trade']}")
        print("\nCheck single-capitalized-word trades:")
        for r in rows:
            t = r["trade"].strip()
            if t and len(t.split()) == 1 and t[0].isupper() and t.isalpha():
                print(f"  L{r['_line']:4d} | {r['street']} {r['house_number']} | {r['surname']} | {r['forename']} | {t}")
        print("\nTop 10 unmatched street names:")
        for st, cnt in Counter(u[2] for u in unmatched).most_common(10):
            print(f"  {cnt:3d} | {st}")
        return

    clean_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    with open(VOL_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(clean_rows)

    # Insert 1862 in chronological order (after 1848, before 1865)
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
