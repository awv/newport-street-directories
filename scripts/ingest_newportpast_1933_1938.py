#!/usr/bin/env python3
"""
Scrape, cache, parse, and merge Johns' 1933 and 1938 Newport Directories from newportpast.com.
- 1933 (666 streets): '[num, ]Surname, Forename - trade ~ [Building, ]Street'
- 1938 (708 streets): verbatim directory lines
Writes volume_csvs/1933_cleaned.csv, volume_csvs/1938_cleaned.csv, and merges into data.csv.
"""
import csv
import html as html_lib
import re
import subprocess
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalize_1914_1917 as n14

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"

CORP_WORDS_RE = re.compile(
    r"(&|\bLtd\b|\bLimited\b|\bCo\.?\b|\bBros\b|\bSons?\b|\bSociety\b|\bCorp\b|\bWorks\b|\bBank\b|\bHotel\b|\bInn\b|\bStores?\b|\bInstitute\b|\bBoard\b|\bAssociation\b|\bService\b|\bClub\b|\bCouncil\b)",
    re.IGNORECASE,
)
BLDG_HDR_RE = re.compile(
    r"^(?:[A-Z0-9'’.\-& ]+(?:CHAMBERS|BUILDINGS|FLATS|ARCADE|MANSIONS|TERRACE|COURT)|(?:1st|2nd|3rd|4th|First|Second|Third|Ground)\s+Floor)\s*[-—–]*$",
    re.IGNORECASE,
)


def curl_get(url, retries=3):
    for attempt in range(retries):
        try:
            out = subprocess.check_output(["curl", "-sL", "--max-time", "20", url])
            return out.decode("utf-8", "ignore")
        except Exception:
            if attempt == retries - 1:
                return ""
            time.sleep(1.0 + attempt)
    return ""


def fetch_street_list(year):
    streets = []
    seen = set()

    def get_letter(ch):
        url = f"https://www.newportpast.com/records/directories/johns{year}/roads.php?letter={ch}"
        h = curl_get(url)
        return re.findall(r'href=["\']search\.php\?road=([^"\']+)["\'][^>]*>([^<]+)<', h, re.I)

    with ThreadPoolExecutor(max_workers=6) as ex:
        for batch in ex.map(get_letter, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            for raw_param, label in batch:
                key = raw_param.strip()
                if key not in seen:
                    seen.add(key)
                    streets.append((key, html_lib.unescape(label).strip()))
    return streets


def fetch_all_pages(year, streets):
    cache_dir = ROOT / "scratch" / f"newportpast_{year}"
    cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_one(idx_item):
        idx, (raw_param, label) = idx_item
        slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or f"st_{idx}"
        out_file = cache_dir / f"{idx:04d}_{slug}.html"
        if out_file.exists() and out_file.stat().st_size > 200:
            return out_file
        encoded = urllib.parse.quote(raw_param, safe="")
        url = f"https://www.newportpast.com/records/directories/johns{year}/search.php?road={encoded}"
        h = curl_get(url)
        if h:
            out_file.write_text(h, encoding="utf-8")
        return out_file

    with ThreadPoolExecutor(max_workers=6) as ex:
        files = list(ex.map(fetch_one, enumerate(streets)))
    return files


def extract_td_lines(html_text):
    tds = re.findall(r"<td[^>]*>([\s\S]*?)</td>", html_text, re.I)
    lines = []
    for td in tds:
        txt = re.sub(r"<[^>]+>", " ", td)
        txt = html_lib.unescape(txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        if txt:
            lines.append(txt)
    return lines


def fix_excel_serial_hn(hn):
    if re.fullmatch(r"4[4-6]\d{3}", hn):
        dt = datetime(1899, 12, 30) + timedelta(days=int(hn))
        return f"{dt.day}-{dt.month}"
    return hn


def parse_1933_line(line, street_canon):
    if line.lower().startswith("from ") or re.match(r"^\(?(?:left|right)\s+hand\s+side", line, re.I):
        return None
    if re.match(r"^\(?return\.?\)?$", line, re.I):
        return None

    bldg = ""
    left = line
    street_out = street_canon
    if " ~ " in line:
        left, right = line.rsplit(" ~ ", 1)
        right = right.strip()
        if "," in right:
            bldg_part, st_part = right.rsplit(",", 1)
            bldg = bldg_part.strip().title()
            street_out = st_part.strip()

    hn = ""
    m_hn = re.match(r"^(\d+[A-Za-z]?(?:\s*[-–&/,]\s*\d+[A-Za-z]?)*)\s*,\s*(.+)$", left.strip())
    if m_hn:
        hn = fix_excel_serial_hn(m_hn.group(1).strip())
        left = m_hn.group(2).strip()

    if "here is " in left.lower():
        return {
            "year": "1933", "street": street_out, "house_number": "", "building_name": "",
            "surname": left.strip(), "forename": "", "trade": "", "source_type": "newportpast_html"
        }

    name_part = left
    trade = ""
    if " - " in left:
        name_part, trade = left.split(" - ", 1)
        name_part = name_part.strip()
        trade = trade.strip()

    sn = ""
    fn = ""
    if "," in name_part:
        p1, p2 = name_part.split(",", 1)
        p1, p2 = p1.strip(), p2.strip()
        if CORP_WORDS_RE.search(name_part):
            # e.g. 'Fletcher, J Kyrle Ltd' -> 'J Kyrle Fletcher Ltd', 'Hall, John Ltd' -> 'John Hall Ltd'
            if p2.startswith("&"):
                sn = f"{p1} {p2}".strip()
            else:
                sn = f"{p2} {p1}".strip()
        else:
            sn = p1
            fn = p2
    else:
        sn = name_part.strip()

    return {
        "year": "1933",
        "street": street_out,
        "house_number": hn,
        "building_name": bldg,
        "surname": sn,
        "forename": fn,
        "trade": trade,
        "source_type": "newportpast_html",
    }


def parse_1938_lines(lines, street_canon):
    rows = []
    current_bldg = ""
    for line in lines:
        low = line.lower()
        if low.startswith("from ") or re.match(r"^\(?(?:left|right)\s+hand\s+side", line, re.I):
            continue
        if re.match(r"^\(?return\.?\)?$", line, re.I):
            current_bldg = ""
            continue
        if "here is " in low:
            current_bldg = ""
            rows.append({
                "year": "1938", "street": street_canon, "house_number": "", "building_name": "",
                "surname": line.strip(), "forename": "", "trade": "", "source_type": "newportpast_html"
            })
            continue
        if BLDG_HDR_RE.match(line.strip()) and "," not in line:
            hdr = line.strip().rstrip("-—– ").title()
            if "Floor" in hdr and current_bldg and "Floor" not in current_bldg:
                current_bldg = f"{current_bldg.split(' — ')[0]} — {hdr}"
            else:
                current_bldg = hdr
            continue

        hn = ""
        rest = line.strip()
        m_hn = re.match(r"^(\d+[A-Za-z]?(?:\s*(?:[-–&/]|and|to)\s*\d+[A-Za-z]?)*)\s+(.+)$", rest)
        if m_hn:
            hn = fix_excel_serial_hn(m_hn.group(1).strip())
            rest = m_hn.group(2).strip()
            if current_bldg and not re.match(r"^(?:1st|2nd|3rd|Room)", rest, re.I):
                current_bldg = ""

        # Split name and trade carefully (don't split right before Ltd./Co./Inc.)
        name_part = rest
        trade = ""
        m_split = re.match(
            r"^(.+?(?:,\s*(?:Ltd\.?|Limited|Inc\.?|Co\.?))?),\s+(.+)$",
            rest,
            re.IGNORECASE,
        )
        if m_split:
            name_part = m_split.group(1).strip()
            trade = m_split.group(2).strip()

        sn = ""
        fn = ""
        if CORP_WORDS_RE.search(name_part):
            sn = name_part
        else:
            m_per = re.match(r"^([A-Z][a-z'’-]+)\s+((?:[A-Z][a-z]*\.?(?:\s+[A-Z][a-z]*\.?)*)|(?:Mrs\.?|Miss|Rev\.?|Dr\.?)\s+.+)$", name_part)
            if m_per:
                sn = m_per.group(1).strip()
                fn = m_per.group(2).strip()
            else:
                sn = name_part

        rows.append({
            "year": "1938",
            "street": street_canon,
            "house_number": hn,
            "building_name": current_bldg,
            "surname": sn,
            "forename": fn,
            "trade": trade,
            "source_type": "newportpast_html",
        })
    return rows


def main():
    canon_by_lower = n14.load_canonical_map()
    fieldnames = ["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"]
    all_new = {}

    for year in ("1933", "1938"):
        print(f"=== Fetching {year} street list from newportpast.com ===")
        streets = fetch_street_list(year)
        print(f"[{year}] Found {len(streets)} streets. Downloading/checking cache...")
        files = fetch_all_pages(year, streets)

        year_rows = []
        for (raw_param, label), html_file in zip(streets, files):
            if not html_file.exists():
                continue
            # If 1933 sub-page is 'CASTLE CHAMBERS, HIGH ST', resolve street from the part after ','
            st_label = label.rsplit(",", 1)[-1].strip() if (year == "1933" and "," in label) else label
            st_label = re.sub(r"^St\s+", "St. ", st_label, flags=re.I)
            st_canon = n14.clean_street_name(st_label, canon_by_lower) or st_label.title()
            lines = extract_td_lines(html_file.read_text(encoding="utf-8", errors="ignore"))
            if year == "1933":
                for ln in lines:
                    row = parse_1933_line(ln, st_canon)
                    if row and any(row[k] for k in ("house_number", "building_name", "surname", "forename", "trade")):
                        # Canonicalize any street_out extracted from ' ~ Building, Street'
                        raw_st = re.sub(r"^St\s+", "St. ", row["street"], flags=re.I)
                        row["street"] = n14.clean_street_name(raw_st, canon_by_lower) or st_canon
                        year_rows.append(row)
            else:
                year_rows.extend(parse_1938_lines(lines, st_canon))

        vol_csv = ROOT / "volume_csvs" / f"{year}_cleaned.csv"
        with open(vol_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(year_rows)
        all_new[year] = year_rows
        print(f"[{year}] Parsed {len(year_rows)} rows across {len(set(r['street'] for r in year_rows))} streets -> {vol_csv.name}")

    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        data_fn = reader.fieldnames
        kept = [r for r in reader if r.get("year") not in ("1933", "1938")]

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=data_fn)
        w.writeheader()
        w.writerows(kept + all_new["1933"] + all_new["1938"])

    print(f"Merged 1933 ({len(all_new['1933'])}) & 1938 ({len(all_new['1938'])}) into data.csv.")


if __name__ == "__main__":
    main()
