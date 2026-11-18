#!/usr/bin/env python3
"""
Ingest the 4 remaining pre-1936 Newport Past public street directories:
- 1876 (butchers1876)
- 1897 (johns1897)
- 1904 (johns1904)
- 1905 (johns1905)
Caches raw HTML in scratch/newportpast_{year}/, writes volume_csvs/{year}_cleaned.csv,
and merges into data.csv.
"""
import csv
import html as html_lib
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalize_1914_1917 as n14
import ingest_newportpast_1933_1938 as np33

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"

VOLUMES = [
    ("1876", "butchers1876"),
    ("1897", "johns1897"),
    ("1904", "johns1904"),
    ("1905", "johns1905"),
]


def fetch_list(slug):
    streets = []
    seen = set()

    def get_letter(ch):
        url = f"https://www.newportpast.com/records/directories/{slug}/roads.php?letter={ch}"
        h = np33.curl_get(url)
        return re.findall(r'href=["\']search\.php\?road=([^"\']+)["\'][^>]*>([^<]+)<', h, re.I)

    with ThreadPoolExecutor(max_workers=6) as ex:
        for batch in ex.map(get_letter, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            for raw_param, label in batch:
                key = raw_param.strip()
                if key not in seen:
                    seen.add(key)
                    streets.append((key, html_lib.unescape(label).strip()))
    return streets


def fetch_pages(year, slug, streets):
    cache_dir = ROOT / "scratch" / f"newportpast_{year}"
    cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_one(idx_item):
        idx, (raw_param, label) = idx_item
        st_slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or f"st_{idx}"
        out_file = cache_dir / f"{idx:04d}_{st_slug}.html"
        if out_file.exists() and out_file.stat().st_size > 200:
            return out_file
        encoded = urllib.parse.quote(raw_param, safe="")
        url = f"https://www.newportpast.com/records/directories/{slug}/search.php?road={encoded}"
        h = np33.curl_get(url)
        if h:
            out_file.write_text(h, encoding="utf-8")
        return out_file

    with ThreadPoolExecutor(max_workers=6) as ex:
        return list(ex.map(fetch_one, enumerate(streets)))


def parse_1897_html(html_text, street_canon):
    m = re.search(r"<h2[^>]*>[\s\S]*?</h2>([\s\S]*?)(?:</div|$)", html_text, re.I)
    body = m.group(1) if m else html_text
    raw_lines = re.split(r"<br\s*/?>", body, flags=re.I)
    rows = []
    for raw in raw_lines:
        txt = re.sub(r"<[^>]+>", " ", raw)
        txt = html_lib.unescape(txt).replace("\xa0", " ")
        txt = re.sub(r"\s+", " ", txt).strip()
        if not txt or txt.startswith("(") and "side" in txt.lower():
            continue
        if "here is " in txt.lower():
            rows.append({
                "year": "1897", "street": street_canon, "house_number": "", "building_name": "",
                "surname": txt, "forename": "", "trade": "", "source_type": "newportpast_html",
            })
            continue
        # Format: [Building, ][Num, | - ]Surname, Forename, trade
        bldg = ""
        hn = ""
        rest = txt.lstrip("- ").strip()
        m_bhn = re.match(r"^([^,]+?),\s*(\d+[A-Za-z]?(?:\s*[-–&/,]\s*\d+[A-Za-z]?)*),\s*(.+)$", rest)
        if m_bhn and not re.match(r"^\d", m_bhn.group(1)):
            bldg = m_bhn.group(1).strip()
            hn = np33.fix_excel_serial_hn(m_bhn.group(2).strip())
            rest = m_bhn.group(3).strip()
        else:
            m_hn = re.match(r"^(\d+[A-Za-z]?(?:\s*[-–&/,]\s*\d+[A-Za-z]?)*),\s*(.+)$", rest)
            if m_hn:
                hn = np33.fix_excel_serial_hn(m_hn.group(1).strip())
                rest = m_hn.group(2).strip()

        parts = [p.strip() for p in rest.split(",", 2)]
        sn = parts[0] if len(parts) >= 1 else ""
        fn = parts[1] if len(parts) >= 2 else ""
        tr = parts[2] if len(parts) >= 3 else ""
        if np33.CORP_WORDS_RE.search(f"{sn} {fn}") and fn and not re.match(r"^(Mrs|Miss|Mr|Rev|Dr)\b", fn, re.I):
            sn = f"{sn} {fn}".strip() if fn.startswith("&") else f"{fn} {sn}".strip()
            fn = ""

        if any((hn, bldg, sn, fn, tr)):
            rows.append({
                "year": "1897",
                "street": street_canon,
                "house_number": hn,
                "building_name": bldg,
                "surname": sn,
                "forename": fn,
                "trade": tr,
                "source_type": "newportpast_html",
            })
    return rows


def main():
    canon_by_lower = n14.load_canonical_map()
    fieldnames = ["year", "street", "house_number", "building_name", "surname", "forename", "trade", "source_type"]
    all_new = {}

    for year, slug in VOLUMES:
        print(f"=== Fetching {year} ({slug}) from newportpast.com ===")
        streets = fetch_list(slug)
        print(f"[{year}] Found {len(streets)} streets. Downloading/checking cache...")
        files = fetch_pages(year, slug, streets)

        year_rows = []
        for (raw_param, label), html_file in zip(streets, files):
            if not html_file.exists():
                continue
            st_label = re.sub(r"^St\s+", "St. ", label.strip().rstrip("."), flags=re.I)
            st_canon = n14.clean_street_name(st_label, canon_by_lower) or st_label.title()
            html_text = html_file.read_text(encoding="utf-8", errors="ignore")
            if year == "1897":
                year_rows.extend(parse_1897_html(html_text, st_canon))
            else:
                lines = np33.extract_td_lines(html_text)
                # Strip optional comma right after leading house number in 1904/1905
                cleaned_lines = [re.sub(r"^(\d+[A-Za-z]?(?:\s*[-–&/]\s*\d+[A-Za-z]?)*),\s+", r"\1 ", ln) for ln in lines]
                parsed = np33.parse_1938_lines(cleaned_lines, st_canon)
                for r in parsed:
                    r["year"] = year
                year_rows.extend(parsed)

        vol_csv = ROOT / "volume_csvs" / f"{year}_cleaned.csv"
        with open(vol_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(year_rows)
        all_new[year] = year_rows
        print(f"[{year}] Parsed {len(year_rows)} rows across {len(set(r['street'] for r in year_rows))} streets -> {vol_csv.name}")

    target_years = set(all_new.keys())
    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        data_fn = reader.fieldnames
        kept = [r for r in reader if r.get("year") not in target_years]

    merged = kept
    for year, _ in VOLUMES:
        merged.extend(all_new[year])

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=data_fn)
        w.writeheader()
        w.writerows(merged)

    print("Merged 1876, 1897, 1904, 1905 into data.csv.")


if __name__ == "__main__":
    main()
