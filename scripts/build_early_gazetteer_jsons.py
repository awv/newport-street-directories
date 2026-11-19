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

        # Capture narrative paragraphs (long prose sentences)
        if len(non_empty) == 1 and len(non_empty[0]) > 140 and not is_heading(non_empty[0]):
            narrative_parts.append(non_empty[0])
            continue

        # Check standalone heading
        if len(set(non_empty)) == 1 and is_heading(non_empty[0]):
            h = non_empty[0].strip(" .:")
            if any(k in h.upper() for k in ("NOBILITY", "GENTRY", "CLERGY")):
                in_gentry = True
            else:
                in_gentry = False
                cur_cat = h.title()
            continue

        # Trim leading blanks
        trimmed = cells[:]
        while trimmed and trimmed[0] == "":
            trimmed.pop(0)

        # Check inline category in trimmed (e.g. 1844: ['Thomas', 'David', 'GROCERS & TEA DEALERS.', '', 'Skinner st'] or 1850: ['Bakers & Flour Dealers', 'Clunn Charles', 'Commercial st'])
        row_cat = None
        cleaned = []
        for pos, c in enumerate(trimmed):
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

        # 1850 pattern: ['Bakers & Flour Dealers', 'Clunn Charles', 'Commercial st']
        if year == 1850 and len(cleaned) >= 2 and re.search(r"(?:&|Dealers|Makers|Agents|Grocers|Tailors|Builders|Butchers|Merchants|Schools|Inns|Taverns|Chemists|Drapers|Printers|Surgeons|Solicitors)", cleaned[0]) and not STREET_HINT_RE.search(cleaned[0]):
            row_cat = cleaned[0].strip(" .:")
            cur_cat = row_cat
            cleaned = cleaned[1:]

        if not cleaned:
            continue

        # Early gentry rows (top of 1844/1850/1858 before first trade section)
        if in_gentry or (idx <= 95 and year in (1844, 1850) and cur_cat == "General Trades & Residents"):
            text_all = " ".join(cleaned)
            if len(cleaned) >= 2 and not STREET_HINT_RE.search(cleaned[0]):
                if len(cleaned) >= 3 and not STREET_HINT_RE.search(cleaned[1]):
                    name = f"{cleaned[0]}, {cleaned[1]}".strip(", ")
                    fmt = f"{cleaned[1]} {cleaned[0]}".strip()
                    res = ", ".join(cleaned[2:])
                else:
                    name = cleaned[0]
                    fmt = cleaned[0]
                    res = ", ".join(cleaned[1:])
            else:
                name = cleaned[0].split(",")[0].strip()
                fmt = name
                res = cleaned[0][len(name):].strip(" ,")
            if name:
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
                idx_st = line_txt.lower().find(num_note.replace("No. ", "").lower()) if num_note else -1
                name_part = line_txt[:idx_st].strip(" ,.;:-") if idx_st > 0 else line_txt
            elif "," in line_txt and STREET_HINT_RE.search(line_txt.rsplit(",", 1)[1]):
                name_part, street = [p.strip() for p in line_txt.rsplit(",", 1)]
            else:
                name_part = line_txt
            name = clean_case(name_part)
            fmt = name
        else:
            # Multi-column: find last cell with street hint or number+street
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
                    street = addr_blob
                left = [c for c in cleaned[:addr_idx] if c]
            else:
                left = [c for c in cleaned if c]

            if len(left) >= 2 and left[1] and left[1][0].islower():
                name = clean_case(left[0])
                fmt = name
                trade = left[1]
            elif len(left) >= 2:
                name = f"{clean_case(left[0])}, {left[1]}".strip(", ")
                fmt = f"{left[1]} {clean_case(left[0])}".strip()
                if len(left) >= 3:
                    trade = "; ".join(left[2:])
            elif left:
                name = clean_case(left[0])
                fmt = name

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

    for idx, raw in enumerate(lines, 1):
        if idx == 1:
            continue
        cells = [clean_cell(c) for c in raw.split("\t")]
        non_empty = [c for c in cells if c]
        if not non_empty:
            continue

        # Capture narrative paragraphs
        if idx < gentry_end and len(non_empty) == 1 and len(non_empty[0]) > 140 and not is_heading(non_empty[0]):
            narrative_parts.append(non_empty[0])
            continue

        trimmed = cells[:]
        while trimmed and trimmed[0] == "":
            trimmed.pop(0)

        if idx < comm_start:
            # Gentry / Private Residents
            if len(non_empty) == 1 and is_heading(non_empty[0]):
                continue
            blob = " | ".join(trimmed)
            if len(blob) > 140 and idx < 234 and year == 1865:
                continue
            if len(trimmed) >= 2:
                if "," in trimmed[0]:
                    name = trimmed[0]
                    fmt = trimmed[0]
                    res = ", ".join(trimmed[1:])
                else:
                    name = f"{trimmed[1]}, {trimmed[0]}".strip(", ")
                    fmt = f"{trimmed[0]} {trimmed[1]}".strip()
                    res = ", ".join(trimmed[2:]) if len(trimmed) > 2 else ""
                if name and len(name) <= 90:
                    gentry.append({"name": clean_case(name), "formatted_name": fmt, "residence": res or "Newport", "notes": ""})
            continue

        # Commercial alphabetical entries
        if len(set(non_empty)) == 1 and is_heading(non_empty[0]):
            continue

        full_text = " ".join(trimmed)
        num_note, st = extract_num_and_street(full_text)
        if not st:
            for c in reversed(trimmed):
                if c and STREET_HINT_RE.search(c) and len(c) < 60:
                    st = c
                    break

        if year == 1862:
            c0 = trimmed[0] if len(trimmed) > 0 else ""
            c1 = trimmed[1] if len(trimmed) > 1 else ""
            c2 = trimmed[2] if len(trimmed) > 2 else ""
            if c0 and c1 and c1[0].islower():
                name = clean_case(c0)
                fmt = name
                trade = c1
            elif c0 and c1:
                name = f"{clean_case(c0)}, {c1}".strip(", ")
                fmt = f"{c1} {clean_case(c0)}".strip()
                trade = c2
            else:
                name = clean_case(c0)
                fmt = name
                trade = c1
        else:
            # 1865: Forenames | Surname | Trade | ...
            c0 = trimmed[0] if len(trimmed) > 0 else ""
            c1 = trimmed[1] if len(trimmed) > 1 else ""
            c2 = trimmed[2] if len(trimmed) > 2 else ""
            if "," in c0 and not c1:
                parts = [p.strip() for p in c0.split(",", 2)]
                name = f"{clean_case(parts[0])}, {parts[1]}" if len(parts) > 1 else clean_case(parts[0])
                fmt = f"{parts[1]} {clean_case(parts[0])}" if len(parts) > 1 else clean_case(parts[0])
                trade = parts[2] if len(parts) > 2 else c2
            elif c0 and c1:
                name = f"{clean_case(c1)}, {c0}".strip(", ")
                fmt = f"{c0} {clean_case(c1)}".strip()
                trade = c2
            else:
                name = clean_case(c0 or c1)
                fmt = name
                trade = c2

        if st:
            trade = trade.replace(st, "").strip(" ,.;:-")
        if num_note:
            trade = trade.replace(num_note.replace("No. ", ""), "").strip(" ,.;:-")

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
