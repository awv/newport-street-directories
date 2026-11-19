#!/usr/bin/env python3
"""Build Early Trade Gazetteer JSON files for 1844, 1850, 1858, 1862, and 1865 from raw_tsvs/."""

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "raw_tsvs"
OUT_DIR = ROOT / "data" / "early_directories"

STREET_HINT_RE = re.compile(
    r"\b(?:street|st\.?|road|rd\.?|hill|place|pl\.?|parade|row|terrace|ter\.?|lane|ln\.?|square|sq\.?|wharf|court|pillgwenlly|pill|baneswell|maindee|pentonville)\b",
    re.I,
)
NUM_STREET_RE = re.compile(
    r"(?<![a-zA-Z0-9/])(\d+(?:½|[a-zA-Z])?(?:\s*(?:and|&)\s*\d+(?:½|[a-zA-Z])?)?),?\s*"
    r"([A-Z][a-zA-Z'\-]+(?:\s+[A-Z]?[a-zA-Z'\-]+){0,3}\s+"
    r"(?:[Ss]treet|[Ss]t\.?|[Rr]oad|[Rr]d\.?|[Hh]ill|[Pp]lace|[Pp]l\.?|[Pp]arade|[Rr]ow|[Tt]errace|[Tt]er\.?|[Ll]ane|[Ll]n\.?|[Ss]quare|[Ss]q\.?|[Ww]harf|[Cc]ourt))",
)

FIRM_RE = re.compile(
    r"(?:\bCompany\b|\bCompy\b|\bSociety\b|\bBank\b|\bWorks\b|\bHotel\b|\bInn\b|\bTavern\b|\bOffice\b|\bRailway\b|\bSchool\b|\bCo\.?\b|\bBros\.?\b|\bBrothers\b|\bSons?\b|\band\b|&)",
    re.I,
)
TITLE_PREFIX_RE = re.compile(r"^(?:Mr\.?|Mrs\.?|Miss|Misses|Rev\.?|Dr\.?|Sir|Capt\.?|Captain|Major|Col\.?|Colonel|Gen\.?|The)\b", re.I)
INITIALS_RE = re.compile(r"^(?:[A-Z]\.\s*)+$")
SUFFIX_ONLY_RE = re.compile(r"^(?:Esq\.?|J\.?P\.?|M\.?D\.?|M\.?A\.?|C\.?E\.?|jun\.?|sen\.?|Bart\.?)(?:[,\s]+(?:Esq\.?|J\.?P\.?|M\.?D\.?|M\.?A\.?|C\.?E\.?|jun\.?|sen\.?|Bart\.?))*$", re.I)
COMMON_FORENAMES = {
    "william", "wm.", "john", "jno.", "thomas", "thos.", "james", "jas.",
    "george", "geo.", "henry", "hy.", "charles", "chas.", "edward", "edwd.",
    "samuel", "richard", "richd.", "robert", "robt.", "joseph", "benjamin",
    "alfred", "edwin", "frederick", "walter", "david", "daniel", "stephen",
    "arthur", "alexander", "adam", "amelia", "alice", "margaret", "mary", "ann",
    "elizabeth", "jane", "sarah", "harriet", "maria", "eliza", "catherine", "ellen",
    "cornelius", "caleb", "jacob", "isaac", "abraham", "moses", "elijah", "enoch",
    "reuben", "solomon", "susan", "sophia", "emma", "louisa", "augusta", "fanny",
    "rebecca", "rachel", "emily", "charlotte", "caroline", "anne", "hannah",
    "mrs.", "mr.", "miss", "misses", "rev.", "dr.",
}

FORENAME_EXPANSIONS = {
    "Wm.": "William", "Wm": "William",
    "Geo.": "George", "Geo": "George",
    "Thos.": "Thomas", "Thos": "Thomas",
    "Chas.": "Charles", "Chas": "Charles",
    "Jno.": "John", "Jno": "John",
    "Jas.": "James", "Jas": "James",
    "Jos.": "Joseph", "Jos": "Joseph",
    "Robt.": "Robert", "Robt": "Robert",
    "Richd.": "Richard", "Richd": "Richard",
    "Edwd.": "Edward", "Edwd": "Edward",
    "Hy.": "Henry", "Hy": "Henry",
    "Albt.": "Albert", "Albt": "Albert",
    "Herbt.": "Herbert", "Herbt": "Herbert",
    "Reg.": "Reginald",
    "Stan.": "Stanley",
    "Fredk.": "Frederick", "Fredk": "Frederick",
    "Fred.": "Frederick",
    "Alex.": "Alexander", "Alex": "Alexander",
    "Benj.": "Benjamin", "Benj": "Benjamin",
    "Danl.": "Daniel", "Danl": "Daniel",
    "Saml.": "Samuel", "Saml": "Samuel",
    "Nathl.": "Nathaniel", "Nathl": "Nathaniel",
    "Eliz.": "Elizabeth", "Elizh.": "Elizabeth",
}


def expand_forenames(text: str) -> str:
    tokens = text.split()
    out = []
    for tok in tokens:
        clean_tok = tok.rstrip(",")
        trail = "," if tok.endswith(",") else ""
        rep = FORENAME_EXPANSIONS.get(clean_tok) or FORENAME_EXPANSIONS.get(clean_tok.title())
        out.append((rep + trail) if rep else tok)
    return " ".join(out)


def clean_cell(c: str) -> str:
    c = c.strip()
    if c in {"\\N", "NaN", "nan", "-"}:
        return ""
    c = re.sub(r'^\{"business":\s*"(.*)"\}$', r"\1", c)
    return c.replace('\\"', '"').strip()


def clean_case(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip(" ,.;:-*")
    if s.isupper() and len(s) > 3:
        return s.title()
    return s


def is_heading(c: str) -> bool:
    c = c.strip().replace("&c.", "&C.").replace("&c", "&C")
    if len(c) < 4 or any(ch.islower() for ch in c) or any(ch.isdigit() for ch in c):
        return False
    return bool(re.match(r"^[A-Z][A-Z\s,&'\-\.]+$", c))


def extract_num_and_street(text: str) -> tuple[str, str]:
    m = NUM_STREET_RE.search(text)
    if m:
        return f"No. {m.group(1)}", m.group(2).strip(" ,.;:")
    return "", ""


def format_person(raw_name: str, surname_first: bool = True) -> tuple[str, str]:
    """Return (name, formatted_name) with formatted_name in Forename Surname order."""
    s = re.sub(r"\s+", " ", raw_name).strip(" ,.;:-*")
    if not s:
        return "", ""

    # Handle "Surname, Forename" (e.g. "Allen, Rev. William"), but do NOT flip suffixes like "George, Esq."
    if "," in s:
        p1, p2 = [p.strip() for p in s.split(",", 1)]
        if p1 and p2 and not FIRM_RE.search(p1) and not SUFFIX_ONLY_RE.match(p2):
            sur = clean_case(p1)
            fore = expand_forenames(clean_case(p2) if p2.isupper() else p2)
            return f"{sur}, {fore}", f"{fore} {sur}".strip()
        expanded = expand_forenames(clean_case(s))
        return expanded, expanded

    # Do not flip firms, companies, already-titled names ("Sir Charles G. Morgan"), or initial-prefixed names ("C. T. Wood", "C. Lyne")
    if FIRM_RE.search(s) or TITLE_PREFIX_RE.match(s) or re.match(r"^(?:[A-Z]\.\s+)+", s):
        expanded = expand_forenames(clean_case(s))
        return expanded, expanded

    if surname_first and " " in s:
        # Handle "Mc Lean Alexander" / "Mc. Bean James"
        m_mc = re.match(r"^(Mc\.?\s+[A-Z][a-z'\-]+)\s+(.+)$", s)
        if m_mc:
            sur = clean_case(m_mc.group(1))
            fore = expand_forenames(clean_case(m_mc.group(2)) if m_mc.group(2).isupper() else m_mc.group(2))
            return f"{sur}, {fore}", f"{fore} {sur}".strip()
        first_w, rest_w = s.split(" ", 1)
        sur = clean_case(first_w)
        fore = expand_forenames(clean_case(rest_w) if rest_w.isupper() else rest_w)
        return f"{sur}, {fore}", f"{fore} {sur}".strip()

    expanded = expand_forenames(clean_case(s))
    return expanded, expanded


def strip_addr_from_text(text: str, num_note: str, street: str) -> str:
    t = text
    if num_note and street:
        num = num_note.replace("No. ", "")
        t = re.sub(re.escape(num) + r",?\s*" + re.escape(street), "", t, flags=re.I)
    if street:
        t = re.sub(r",?\s*" + re.escape(street) + r".*$", "", t, flags=re.I)
    return t.strip(" ,.;:-")


def build_trade_gazetteer(year: int, title: str, tsv_name: str, max_line: int | None = None, default_narrative: str = "") -> dict:
    """Parse trade-classified directories (1844, 1850, 1858)."""
    with open(RAW_DIR / tsv_name, encoding="utf-8", errors="replace") as f:
        lines = [l.rstrip("\n") for l in f]
    if max_line:
        lines = lines[:max_line]

    gentry = []
    sections_map: dict[str, list[dict]] = defaultdict(list)
    narrative_parts = []
    cur_cat = "General Trades & Residents"
    in_gentry = False

    for idx, raw in enumerate(lines, 1):
        if idx == 1:
            continue
        cells = [clean_cell(c) for c in raw.split("\t")]
        non_empty = [c for c in cells if c]
        if not non_empty:
            continue

        if len(non_empty) == 1 and len(non_empty[0]) > 140 and not is_heading(non_empty[0]):
            narrative_parts.append(non_empty[0])
            continue

        if len(set(non_empty)) == 1 and is_heading(non_empty[0]):
            h = non_empty[0].strip(" .:")
            if any(k in h.upper() for k in ("NOBILITY", "GENTRY", "CLERGY")):
                in_gentry = True
            else:
                in_gentry = False
                cur_cat = h.title()
            continue

        trimmed = cells[:]
        while trimmed and trimmed[0] == "":
            trimmed.pop(0)

        row_cat = None
        cleaned = []
        for c in trimmed:
            if is_heading(c):
                h = c.strip(" .:")
                if any(k in h.upper() for k in ("NOBILITY", "GENTRY", "CLERGY")):
                    in_gentry = True
                else:
                    in_gentry = False
                    row_cat = h.title()
                    cur_cat = row_cat
                continue
            cleaned.append(c)

        if not cleaned:
            continue

        if year == 1850 and len(cleaned) >= 2 and re.search(r"(?:&|Dealers|Makers|Agents|Grocers|Tailors|Builders|Butchers|Merchants|Schools|Inns|Taverns|Chemists|Drapers|Printers|Surgeons|Solicitors)", cleaned[0]) and not STREET_HINT_RE.search(cleaned[0]):
            row_cat = cleaned[0].strip(" .:")
            cur_cat = row_cat
            cleaned = cleaned[1:]

        if not cleaned:
            continue

        if in_gentry or (idx <= 95 and year in (1844, 1850) and cur_cat == "General Trades & Residents"):
            if len(cleaned) >= 2 and not STREET_HINT_RE.search(cleaned[0]):
                if len(cleaned) >= 3 and not STREET_HINT_RE.search(cleaned[1]):
                    name, fmt = format_person(f"{cleaned[0]}, {cleaned[1]}", surname_first=True)
                    res = ", ".join(cleaned[2:])
                else:
                    name, fmt = format_person(cleaned[0], surname_first=True)
                    res = ", ".join(cleaned[1:])
            else:
                # e.g. "Allen, Rev. William, Hillst" or "Rowland Mrs. Decima, Gt. Dock st"
                raw_line = cleaned[0]
                parts = [p.strip() for p in raw_line.split(",")]
                if len(parts) >= 3 and re.match(r"^(?:Rev|Mr|Mrs|Miss|Esq|Dr)", parts[1], re.I):
                    name, fmt = format_person(f"{parts[0]}, {parts[1]}", surname_first=True)
                    res = ", ".join(parts[2:])
                elif len(parts) >= 2 and STREET_HINT_RE.search(parts[-1]):
                    name, fmt = format_person(", ".join(parts[:-1]), surname_first=True)
                    res = parts[-1]
                else:
                    name, fmt = format_person(parts[0], surname_first=True)
                    res = ", ".join(parts[1:])
            if name and len(name) <= 100:
                gentry.append({"name": name, "formatted_name": fmt, "residence": res or "Newport", "notes": ""})
            continue

        cat = row_cat or cur_cat
        street = ""
        notes = ""
        trade = ""
        name = ""
        fmt = ""

        if len(cleaned) == 1:
            line_txt = cleaned[0]
            num_note, st = extract_num_and_street(line_txt)
            if st:
                notes = num_note
                street = st
                name_part = strip_addr_from_text(line_txt, num_note, st)
            elif "," in line_txt and STREET_HINT_RE.search(line_txt.rsplit(",", 1)[1]):
                name_part, raw_st = [p.strip() for p in line_txt.rsplit(",", 1)]
                street = raw_st[:35].strip(" .;") if len(raw_st) > 35 else raw_st.strip(" .;")
            else:
                m_tail_st = re.search(
                    r"\s+((?:(?:Gt\.?|Great|Upper|Lower|Old|New)\s+)?[A-Z][a-zA-Z'\-]+(?:\s+[A-Z]?[a-zA-Z'\-]+){0,2}\s+"
                    r"(?:street|st\.?|road|rd\.?|hill|place|pl\.?|parade|row|terrace|ter\.?|lane|ln\.?|square|sq\.?|wharf|court))\.?$",
                    line_txt, re.I,
                )
                if m_tail_st:
                    street = m_tail_st.group(1).strip(" .;")
                    name_part = line_txt[:m_tail_st.start()].strip(" ,.;:-")
                else:
                    name_part = line_txt

            m_par = re.search(r"\(([^)]+)\)", name_part)
            if m_par:
                trade = m_par.group(1).strip()
                name_part = (name_part[:m_par.start()] + " " + name_part[m_par.end():]).strip(" ,.;:-")

            name, fmt = format_person(name_part, surname_first=True)
        else:
            addr_idx = None
            for i in range(len(cleaned) - 1, 0, -1):
                if cleaned[i] and (STREET_HINT_RE.search(cleaned[i]) or NUM_STREET_RE.search(cleaned[i])):
                    addr_idx = i
                    break
            if addr_idx is not None:
                addr_blob = cleaned[addr_idx]
                num_note, st = extract_num_and_street(addr_blob)
                if st:
                    notes = num_note
                    street = st
                else:
                    last_seg = addr_blob.rsplit(",", 1)[-1].strip(" .;")
                    street = last_seg if len(last_seg) <= 35 else ""
                    if "," in addr_blob and not trade:
                        prefix_note = addr_blob.rsplit(",", 1)[0].strip(" .;-()")
                        if prefix_note:
                            trade = prefix_note
                left = [c for c in cleaned[:addr_idx] if c]
            else:
                left = [c for c in cleaned if c]

            if len(left) >= 2 and left[1] and re.match(r"^(?:and|&)\s+[A-Z]", left[1]):
                firm_str = f"{clean_case(left[0])} {left[1]}"
                name, fmt = firm_str, firm_str
                if len(left) >= 3:
                    trade = "; ".join(left[2:])
            elif len(left) >= 2 and left[1] and left[1][0].islower():
                name, fmt = format_person(left[0], surname_first=True)
                trade = left[1]
            elif len(left) >= 2:
                name, fmt = format_person(f"{left[0]}, {left[1]}", surname_first=True)
                if len(left) >= 3:
                    trade = "; ".join(left[2:])
            elif left:
                name, fmt = format_person(left[0], surname_first=True)

        if not name or len(name) > 120:
            continue

        sections_map[cat].append({
            "name": name,
            "formatted_name": fmt,
            "street": street,
            "trade": trade or cat,
            "notes": notes,
        })

    sections = [{"category": cat, "entries": ents} for cat, ents in sections_map.items() if ents]
    return {
        "year": year,
        "title": title,
        "county": "Monmouthshire",
        "town": "Newport",
        "narrative": "\n\n".join(narrative_parts) if narrative_parts else default_narrative,
        "nobility_gentry_clergy": gentry,
        "sections": sections,
    }


def build_alphabetical_gazetteer(year: int, title: str, tsv_name: str, gentry_end: int, comm_start: int, max_line: int | None, default_narrative: str) -> dict:
    """Parse alphabetical directories (1862 Morris, 1865 Webster)."""
    with open(RAW_DIR / tsv_name, encoding="utf-8", errors="replace") as f:
        lines = [l.rstrip("\n") for l in f]
    if max_line:
        lines = lines[:max_line]

    gentry = []
    alpha_map: dict[str, list[dict]] = defaultdict(list)
    narrative_parts = []
    cur_alpha = "A"

    for idx, raw in enumerate(lines, 1):
        if idx == 1:
            continue
        cells = [clean_cell(c) for c in raw.split("\t")]
        non_empty = [c for c in cells if c]
        if not non_empty:
            continue

        if idx < gentry_end and len(non_empty) == 1 and len(non_empty[0]) > 140 and not is_heading(non_empty[0]):
            narrative_parts.append(non_empty[0])
            continue

        trimmed = cells[:]
        while trimmed and trimmed[0] == "":
            trimmed.pop(0)

        if idx < comm_start:
            if len(non_empty) == 1 and is_heading(non_empty[0]):
                continue
            blob = " | ".join(trimmed)
            if len(blob) > 140 and idx < 234 and year == 1865:
                continue
            if len(trimmed) >= 2:
                if "," in trimmed[0]:
                    name, fmt = format_person(trimmed[0], surname_first=True)
                    res = ", ".join(trimmed[1:])
                elif year == 1865 and len(trimmed[0].split()) >= 2 and not TITLE_PREFIX_RE.match(trimmed[0]):
                    # 1865 gentry sometimes has "Cole John Thos." in trimmed[0] or "Rev. Wm." in trimmed[0]
                    name, fmt = format_person(f"{trimmed[1]}, {trimmed[0]}" if len(trimmed[1].split()) == 1 and not STREET_HINT_RE.search(trimmed[1]) else trimmed[0], surname_first=True)
                    res = ", ".join(trimmed[2:]) if len(trimmed) > 2 else trimmed[1]
                else:
                    # Forename in trimmed[0], Surname in trimmed[1] (e.g. "Thos. Esq. | Woollett")
                    if SUFFIX_ONLY_RE.match(trimmed[1]):
                        name, fmt = format_person(trimmed[0], surname_first=True)
                        res = ", ".join(trimmed[2:]) if len(trimmed) > 2 else ""
                    else:
                        name, fmt = format_person(f"{trimmed[1]}, {trimmed[0]}", surname_first=True)
                        res = ", ".join(trimmed[2:]) if len(trimmed) > 2 else ""
                if name and len(name) <= 90:
                    gentry.append({"name": name, "formatted_name": fmt, "residence": res or "Newport", "notes": ""})
            continue

        if len(set(non_empty)) == 1 and is_heading(non_empty[0]):
            continue

        full_text = " ".join(trimmed)
        num_note, st = extract_num_and_street(full_text)
        if not st:
            for c in reversed(trimmed):
                if not c:
                    continue
                last_seg = c.rsplit(",", 1)[-1].strip(" .;")
                if STREET_HINT_RE.search(last_seg) and len(last_seg) < 35:
                    st = last_seg
                    break

        trade = ""
        if year == 1862:
            c0 = trimmed[0] if len(trimmed) > 0 else ""
            c1 = trimmed[1] if len(trimmed) > 1 else ""
            c2 = trimmed[2] if len(trimmed) > 2 else ""
            if c0 and c1 and re.match(r"^(?:and|&)\s+[A-Z]", c1):
                if "," in c1:
                    c1_tail, c1_tr = [p.strip() for p in c1.split(",", 1)]
                    name = f"{clean_case(c0)} {c1_tail}"
                    trade = c1_tr
                else:
                    name = f"{clean_case(c0)} {c1}"
                    trade = c2
                fmt = name
            elif c0 and c1 and c1[0].islower():
                name, fmt = format_person(c0, surname_first=True)
                trade = c1
            elif c0 and c1 and "," in c1 and not SUFFIX_ONLY_RE.match(c1.split(",", 1)[1].strip()):
                # Packed "Forename, trade, address" in c1 (e.g. "Bevan | John, agent", "Beynon | Morgan, shipping agent, 71, Commercial road")
                fore_part, rest_part = [p.strip() for p in c1.split(",", 1)]
                name, fmt = format_person(f"{c0}, {fore_part}", surname_first=True)
                trade = rest_part
            elif c0 and c1:
                if "," in c0 and re.search(r",\s*[a-z]", c0) and len(c1.split()) <= 2:
                    f_part, tr_part = c0.split(",", 1)
                    name, fmt = format_person(f"{c1}, {f_part}", surname_first=True)
                    trade = tr_part.strip()
                elif INITIALS_RE.match(c0):
                    # e.g. "C. | Hawkins", "C. | Higley", "C. | Folk Henry"
                    c1_parts = c1.split(" ", 1)
                    if len(c1_parts) == 2:
                        name = f"{clean_case(c1_parts[0])}, {c1_parts[1]} {c0}".strip()
                        fmt = f"{c1_parts[1]} {c0} {clean_case(c1_parts[0])}".strip()
                    else:
                        name = f"{clean_case(c1)}, {c0}".strip()
                        fmt = f"{c0} {clean_case(c1)}".strip()
                    trade = c2
                else:
                    c0_first = c0.split()[0].lower()
                    c1_is_alpha = c1[0].isalpha() and c1[0].upper() == cur_alpha and c0[0].upper() != cur_alpha
                    if (c0_first in COMMON_FORENAMES or TITLE_PREFIX_RE.match(c0) or c1_is_alpha) and len(c1.split()) == 1:
                        name, fmt = format_person(f"{c1}, {c0}", surname_first=True)
                    else:
                        name, fmt = format_person(f"{c0}, {c1}", surname_first=True)
                        if name and name[0].isalpha() and name[0].upper() >= cur_alpha and ord(name[0].upper()) - ord(cur_alpha) <= 2:
                            cur_alpha = name[0].upper()
                    if c2 and re.match(r"^(?:and|&)\s+(?:Co\.?|Sons?|Bros\.?|Brothers)\b", c2, re.I):
                        fmt = f"{fmt} {c2}".strip()
                        name = f"{name} {c2}".strip()
                        trade = trimmed[3] if len(trimmed) > 3 else ""
                    else:
                        trade = c2
            else:
                name, fmt = format_person(c0, surname_first=True)
                trade = c1
        else:
            # 1865: Forenames | Surname | Trade | ... OR "Surname, Forename trade..." in c0
            c0 = trimmed[0] if len(trimmed) > 0 else ""
            c1 = trimmed[1] if len(trimmed) > 1 else ""
            c2 = trimmed[2] if len(trimmed) > 2 else ""
            if "," in c0 and not c1:
                parts = [p.strip() for p in c0.split(",", 2)]
                raw_n = f"{parts[0]}, {parts[1]}" if len(parts) > 1 else parts[0]
                # Check if trailing lowercase trade stuck to parts[1] (e.g. "Hazell, George agent")
                m_tr = re.match(r"^(.+?)\s+([a-z].*)$", raw_n)
                if m_tr:
                    raw_n = m_tr.group(1)
                    trade = m_tr.group(2)
                name, fmt = format_person(raw_n, surname_first=True)
                if len(parts) > 2 and not trade:
                    trade = parts[2]
            elif c0 and c1:
                if re.match(r"^(?:and|&)\s+[A-Z]", c1):
                    if "," in c1:
                        c1_tail, c1_tr = [p.strip() for p in c1.split(",", 1)]
                        name = f"{clean_case(c0)} {c1_tail}"
                        trade = c1_tr
                    else:
                        name = f"{clean_case(c0)} {c1}"
                        trade = c2
                    fmt = name
                elif c1[0].islower():
                    name, fmt = format_person(c0, surname_first=True)
                    trade = c1
                else:
                    # Check if c0 has trailing lowercase trade (e.g. "James, grocer | Abbott")
                    if "," in c0 and re.search(r",\s*[a-z]", c0):
                        f_part, tr_part = c0.split(",", 1)
                        name, fmt = format_person(f"{c1}, {f_part}", surname_first=True)
                        trade = tr_part.strip()
                    else:
                        name, fmt = format_person(f"{c1}, {c0}", surname_first=True)
                        trade = c2
            else:
                name, fmt = format_person(c0 or c1, surname_first=True)
                trade = c2

        # Reattach partner/company suffix if it landed in trade (e.g. "and Co.", "& Sons", "& Taylor")
        m_partner_tr = re.match(r"^((?:and|&)\s+(?:Co\.?|Sons?|Bros\.?|Brothers|[A-Z][a-z'\-]+))(?:\s*,\s*(.*))?$", trade, re.I)
        if m_partner_tr and not trade.lower().startswith(("and at ", "and in ", "and civil ", "and town", "and land", "and portrait", "and house", "and free", "and library", "and wine")):
            suffix_part = m_partner_tr.group(1).strip()
            rest_tr = (m_partner_tr.group(2) or "").strip()
            if suffix_part.lower() not in fmt.lower():
                fmt = f"{fmt} {suffix_part}".strip()
                name = f"{name} {suffix_part}".strip()
            trade = rest_tr
        if st:
            trade = strip_addr_from_text(trade, num_note, st)
            st = st.lstrip("”\"' ").strip()
        if num_note:
            trade = trade.replace(num_note.replace("No. ", ""), "").strip(" ,.;:-")
        # Strip trailing "h.," or empty "h." from trade
        trade = re.sub(r",?\s*\bh\.?$", "", trade).strip(" ,.;:-")
        if trade.startswith(("“", '"')) and not trade.endswith(("”", '"')):
            trade = trade + "”"

        if not name or len(name) > 100:
            continue
        letter = name[0].upper() if name[0].isalpha() else "Other"
        alpha_map[letter].append({
            "name": name,
            "formatted_name": fmt,
            "street": st,
            "trade": trade,
            "notes": num_note,
        })

    sections = [{"category": k, "entries": alpha_map[k]} for k in sorted(alpha_map.keys()) if alpha_map[k]]
    return {
        "year": year,
        "title": title,
        "county": "Monmouthshire",
        "town": "Newport",
        "narrative": "\n\n".join(narrative_parts) if narrative_parts else default_narrative,
        "nobility_gentry_clergy": gentry,
        "sections": sections,
    }


def main() -> None:
    configs = [
        ("pigot_1844.json", build_trade_gazetteer(
            1844, "Pigot's Monmouthshire Directory 1844", "1844.tsv",
            default_narrative="Pigot & Co.'s Royal National and Commercial Directory for Newport, Monmouthshire (1844). Organized by classified trades, banking, clergy, and gentry prior to systematic street numbering.",
        )),
        ("slater_1850.json", build_trade_gazetteer(
            1850, "Slater's Monmouthshire Directory 1850", "1850.tsv",
            default_narrative="Slater's (late Pigot & Co.) Royal National and Commercial Directory of Monmouthshire (1850), covering Newport's clergy, gentry, merchants, and trades.",
        )),
        ("slater_1858.json", build_trade_gazetteer(
            1858, "Slater's Monmouthshire Directory 1858–59", "1858.tsv", max_line=1630,
            default_narrative="Slater's Commercial Directory of Newport, Monmouthshire (1858–59). Organized by trade classification; entries with printed street numbers are also cross-linked into the main street views.",
        )),
        ("morris_1862.json", build_alphabetical_gazetteer(
            1862, "Morris's Directory of Monmouthshire 1862", "1862.tsv",
            gentry_end=4, comm_start=126, max_line=None,
            default_narrative="Morris & Co.'s Commercial Directory & Gazetteer of Monmouthshire (1862), listing Newport's clergy, gentry, and commercial traders.",
        )),
        ("webster_1865.json", build_alphabetical_gazetteer(
            1865, "Webster's Postal & Commercial Directory 1865", "1865.tsv",
            gentry_end=233, comm_start=353, max_line=1818,
            default_narrative="Webster's Postal and Commercial Directory of Newport, with Pillgwenlly and St. Woollos (1865).",
        )),
    ]

    for fname, data in configs:
        out_path = OUT_DIR / fname
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        total_entries = sum(len(s["entries"]) for s in data["sections"])
        print(f"Wrote {fname}: {total_entries} trade entries across {len(data['sections'])} sections, {len(data['nobility_gentry_clergy'])} gentry")


if __name__ == "__main__":
    main()
