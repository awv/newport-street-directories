#!/usr/bin/env python3
"""
Scrape & parse Kelly's 1848 Newport Directory from newportpast.com into
data/early_directories/kelly_1848.json matching gazetteer.html's schema.
"""
import html as html_lib
import json
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ingest_newportpast_1933_1938 as np33

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "data" / "early_directories" / "kelly_1848.json"
CACHE_DIR = ROOT / "scratch" / "newportpast_1848"

STREET_HINT_RE = re.compile(
    r"\b(street|st\.?|road|rd\.?|hill|lane|place|terrace|wharf|quay|bridge|row|court|parade|market|square|green|pillgwenlly|pill|maindee|caerleon|baneswell|marshes|crindau|alteryn)\b",
    re.IGNORECASE,
)


def fetch_kelly_1848():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    intro_file = CACHE_DIR / "introduction.html"
    if not intro_file.exists():
        intro_html = np33.curl_get("https://www.newportpast.com/records/directories/kelly1848/introduction.php")
        intro_file.write_text(intro_html, encoding="utf-8")
    else:
        intro_html = intro_file.read_text(encoding="utf-8", errors="ignore")

    def query_term(term):
        f = CACHE_DIR / f"q_{term}.html"
        if f.exists() and f.stat().st_size > 200:
            return f.read_text(encoding="utf-8", errors="ignore")
        h = np33.curl_get(f"https://www.newportpast.com/records/directories/kelly1848/search.php?data={term}")
        if h:
            f.write_text(h, encoding="utf-8")
        return h

    def extract_entries_or_overflow(page_html):
        if "too many results" in page_html.lower():
            return None
        m_box = re.search(r'<div id="left_box">([\s\S]*?)</div>', page_html, re.I)
        body = m_box.group(1) if m_box else page_html
        out = []
        for p_raw in re.findall(r"<p[^>]*>([\s\S]*?)</p>", body, re.I):
            txt = re.sub(r"<[^>]+>", " ", p_raw)
            txt = html_lib.unescape(txt).replace("\xa0", " ")
            txt = re.sub(r"\s+", " ", txt).strip()
            if not txt or txt.lower().startswith("results for") or txt.lower().startswith("no results") or len(txt) < 6:
                continue
            out.append(txt)
        return out

    seen = set()
    entries = []
    # Query common 2-letter vowel/consonant pairs + subdivide any 1-letter or 2-letter overflow
    # Using adaptive queue starting from 'a'..'z' (max depth 3 to avoid infinite loops)
    queue = list("abcdefghijklmnopqrstuvwxyz")
    while queue:
        batch = queue[:30]
        queue = queue[30:]
        with ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(query_term, batch))
        for term, page in zip(batch, results):
            parsed = extract_entries_or_overflow(page)
            if parsed is None:
                if len(term) < 3:
                    queue.extend(term + ch for ch in "abcdefghijklmnopqrstuvwxyz")
            else:
                for txt in parsed:
                    if txt not in seen:
                        seen.add(txt)
                        entries.append(txt)

    # Extract narrative paragraphs from introduction.php
    m_intro = re.search(r"<h2[^>]*>INTRODUCTION\.?</h2>([\s\S]*?)</div>", intro_html, re.I)
    intro_body = m_intro.group(1) if m_intro else ""
    paras = []
    for p_raw in re.findall(r"<p[^>]*>([\s\S]*?)</p>", intro_body, re.I):
        t = re.sub(r"<[^>]+>", " ", p_raw)
        t = html_lib.unescape(t).replace("\xa0", " ")
        t = re.sub(r"\s+", " ", t).strip()
        if t and not t.startswith("(Extracted from"):
            paras.append(t)
    narrative = "\n\n".join(paras[:4])
    return narrative, sorted(entries)


def parse_entry(txt):
    clean = txt.rstrip(".").strip()
    parts = [p.strip() for p in clean.split(",") if p.strip()]
    if not parts:
        return None

    # Name: handle 'Surname, Forename' vs 'Firm Name'
    if len(parts) >= 2 and not re.search(r"\b(and|&|Co\.?)\b", parts[0], re.I) and len(parts[1].split()) <= 3 and not STREET_HINT_RE.search(parts[1]):
        sn, fn = parts[0], parts[1]
        formatted_name = f"{fn} {sn}"
        name = f"{sn}, {fn}"
        rest = parts[2:]
    else:
        formatted_name = parts[0]
        name = parts[0]
        rest = parts[1:]

    # Extract trailing district/street/house_number from the end
    street = ""
    house_no = ""
    if rest and rest[-1].lower() in ("pillgwenlly", "newport", "maindee", "crindau") and len(rest) >= 2:
        district = rest.pop()
        if STREET_HINT_RE.search(rest[-1]):
            street = f"{rest.pop()}, {district}"
        else:
            street = district
    elif rest and STREET_HINT_RE.search(rest[-1]):
        street = rest.pop()

    # Check if street has leading house number like '66 High street' or preceding token is a number '54'
    m_num_st = re.match(r"^(\d+[A-Za-z]?)\s+(.+)$", street)
    if m_num_st:
        house_no = m_num_st.group(1)
        street = m_num_st.group(2)
    elif rest and re.fullmatch(r"\d+[A-Za-z]?(?:\s*[-&]\s*\d+[A-Za-z]?)?", rest[-1]):
        house_no = rest.pop()

    # Strip trailing 'Esq.' from rest if it was part of name
    if rest and rest[0].lower().rstrip(".") == "esq":
        formatted_name += ", Esq."
        rest.pop(0)

    trade = ", ".join(rest).strip()
    notes = f"No. {house_no}" if house_no else ""
    is_gentry = ("esq" in formatted_name.lower() or "rev." in formatted_name.lower()) and not trade

    return {
        "name": name,
        "formatted_name": formatted_name,
        "street": street.title() if street else "",
        "trade": trade,
        "notes": notes,
        "is_gentry": is_gentry,
    }


def main():
    narrative, raw_entries = fetch_kelly_1848()
    gentry = []
    by_letter = defaultdict(list)

    for raw in raw_entries:
        parsed = parse_entry(raw)
        if not parsed:
            continue
        if parsed["is_gentry"]:
            gentry.append({
                "name": parsed["name"],
                "formatted_name": parsed["formatted_name"],
                "residence": parsed["street"] + (f" ({parsed['notes']})" if parsed["notes"] else ""),
                "notes": parsed["notes"],
            })
        else:
            ch = parsed["name"][0].upper() if parsed["name"] else "#"
            if not ch.isalpha():
                ch = "#"
            by_letter[ch].append({
                "name": parsed["name"],
                "formatted_name": parsed["formatted_name"],
                "street": parsed["street"],
                "trade": parsed["trade"],
                "notes": parsed["notes"],
            })

    sections = [
        {"category": f"Directory Listings — {ch}", "entries": by_letter[ch]}
        for ch in sorted(by_letter.keys())
    ]

    out = {
        "year": 1848,
        "title": "Kelly's Newport Directory for 1848",
        "county": "Monmouthshire",
        "town": "Newport (Gentry, Merchants, Professors & Tradesmen)",
        "narrative": narrative,
        "nobility_gentry_clergy": gentry,
        "sections": sections,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    total_dir = sum(len(s["entries"]) for s in sections)
    print(f"Wrote {OUT_JSON.name}: {total_dir} directory entries across {len(sections)} A-Z sections + {len(gentry)} gentry entries.")


if __name__ == "__main__":
    main()
