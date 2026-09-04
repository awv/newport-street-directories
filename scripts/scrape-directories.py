import csv
import re
import string
import time
import urllib.parse
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

DIRECTORIES = [
    {"year": 1876, "slug": "butchers1876"},
    {"year": 1886, "slug": "johns1886"},
    {"year": 1897, "slug": "johns1897"},
    {"year": 1905, "slug": "johns1905"},
    {"year": 1914, "slug": "johns1914"},
    {"year": 1927, "slug": "johns1927"},
    {"year": 1933, "slug": "johns1933"},
    {"year": 1938, "slug": "johns1938"},
    {"year": 1946, "slug": "johns1946"},
    {"year": 1950, "slug": "johns1950"},
]

BASE_URL = "https://www.newportpast.com/records/directories/"
OUTPUT_CSV = "data.csv"

IGNORED_PHRASES = [
    "newport past", "search", "records", "maritime history", 
    "20th century", "19th century", "early history", "gallery", 
    "home", "back", "back to", "johns'", "directory", 
    "many thanks to", "transcribed", "butcher's", "butchers"s
]


def clean_street_title(street_name):
    """Strips quotes, ward codes (e.g. ', C'), grid references, and dots."""
    if not street_name:
        return ""
    clean = street_name.replace('"', '').strip()
    clean = re.sub(r",\s*[A-Za-z0-9\s]+\b", "", clean)
    clean = clean.rstrip(".")
    return clean.title().strip()


def is_ignorable_line(line_str, street_name):
    """Determines whether a line is navigation, junction info, or metadata."""
    clean = line_str.strip().lower()

    if not clean:
        return True

    # 1. Navigation / Credits
    if any(phrase in clean for phrase in IGNORED_PHRASES):
        return True

    # 2. Junction Markers ("here is Kirby-street")
    if "here is" in clean:
        return True

    # 3. Directional Markers ("(LEFT HAND SIDE.)", "(RIGHT HAND SIDE.)")
    if re.search(r"^\(.*\bside\b.*\)$", clean):
        return True

    # 4. Street Header Echoes / Grid References (e.g. "BAILEY STREET. E 7")
    clean_street = re.sub(r"[^a-z0-9]", "", street_name.lower())
    clean_line = re.sub(r"[^a-z0-9]", "", clean)
    
    if clean_line.startswith(clean_street):
        remainder = clean_line[len(clean_street):]
        if not remainder or re.match(r"^[a-z]?\d+$", remainder):
            return True

    return False


def clean_entry_text(text):
    """Strips unwanted inline markers like '~ ALMA ST' from the end of records."""
    text = re.sub(r"\s*~\s*.*$", "", text)
    return text.strip()


def parse_line(line_text):
    """Parses a single cleaned entry into constituent fields."""
    clean_text = line_text.replace('"', '').strip()
    if not clean_text or clean_text.startswith("From ") or clean_text.startswith("(From "):
        return None

    building_name = ""
    house_number = ""
    surname = ""
    forename = ""
    trade = ""

    # Extract leading house number
    num_match = re.match(r"^(\d+[A-Za-z]?(?:\s*-\s*\d+)?)[\.\s,]+(.*)", clean_text)
    if num_match:
        house_number = num_match.group(1).strip()
        remainder = num_match.group(2).strip()
    else:
        remainder = clean_text

    parts = [p.strip() for p in remainder.split(",") if p.strip()]

    # Extract building name if present before house number/names
    if not house_number and len(parts) >= 3:
        if not re.match(r"^(\d+[A-Za-z]?)$", parts[0]):
            building_name = parts[0]
            parts = parts[1:]
            if parts and re.match(r"^(\d+[A-Za-z]?)$", parts[0]):
                house_number = parts[0]
                parts = parts[1:]

    if len(parts) >= 1:
        name_words = parts[0].split()
        if name_words:
            surname = name_words[0]
            if len(name_words) > 1:
                forename = " ".join(name_words[1:])
    if len(parts) >= 2:
        if not forename and len(parts) >= 2:
            forename = parts[1]
            trade = ", ".join(parts[2:])
        else:
            trade = ", ".join(parts[1:])

    return {
        "building_name": building_name,
        "house_number": house_number,
        "surname": surname,
        "forename": forename,
        "trade": trade,
    }


def split_continuous_entries(text):
    """Splits un-formatted street blocks (like 1886) into individual entries."""
    text = re.sub(r"^From\s+.*?(?=\d+|\b[A-Z][a-z]+)", "", text)
    text = re.sub(r"here is .*?\.", " ", text)
    text = re.sub(r"\(return\)\.?", " ", text)
    tokens = re.split(r"(?=\b\d+[A-Za-z]?\s+[A-Z])", text)
    return [t.strip() for t in tokens if t.strip()]


def scrape_street(session, year, street_name, url):
    """Fetches and parses all resident entries for a single street."""
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    if "road" in query_params:
        raw_road = query_params["road"][0]
        safe_road = raw_road.replace(",", "%")
        encoded_road = urllib.parse.quote(safe_road)
        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?road={encoded_road}"
    else:
        clean_url = url

    try:
        resp = session.get(clean_url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching {clean_url}: {e}")
        return []

    soup = BeautifulSoup(resp.content, "html.parser")
    main_div = soup.find("div", id="content") or soup.body

    for br in main_div.find_all("br"):
        br.replace_with("\n")

    raw_text = main_div.get_text()
    lines = raw_text.split("\n")

    entries = []
    for line in lines:
        line_str = line.strip()

        if is_ignorable_line(line_str, street_name):
            continue

        line_str = clean_entry_text(line_str)

        if year == 1886 or len(line_str) > 200:
            sub_entries = split_continuous_entries(line_str)
            entries.extend(sub_entries)
        else:
            entries.append(line_str)

    records = []
    # Clean street title before attaching to records
    clean_street = clean_street_title(street_name)

    for entry in entries:
        parsed = parse_line(entry)
        if parsed and (parsed["surname"] or parsed["house_number"]):
            parsed["year"] = year
            parsed["street"] = clean_street
            records.append(parsed)

    return records


def scrape_directory(session, dir_info):
    year = dir_info["year"]
    slug = dir_info["slug"]
    print(f"\n--- Processing {year} ({slug}) ---")

    all_records = []

    for letter in string.ascii_uppercase:
        alphabet_url = f"{BASE_URL}{slug}/roads.php?letter={letter}"
        try:
            resp = session.get(alphabet_url, timeout=10)
            if resp.status_code != 200:
                continue
        except Exception as e:
            print(f"Failed loading letter {letter}: {e}")
            continue

        soup = BeautifulSoup(resp.content, "html.parser")
        street_links = soup.find_all("a", href=re.compile(r"search\.php\?road="))

        for link in street_links:
            street_name = link.get_text().strip()
            street_url = urljoin(alphabet_url, link["href"])

            print(f"[{year}] Scraping: {street_name}")
            records = scrape_street(session, year, street_name, street_url)
            all_records.extend(records)

            time.sleep(0.1)

    return all_records


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    fieldnames = [
        "year",
        "street",
        "house_number",
        "building_name",
        "surname",
        "forename",
        "trade",
    ]

    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for dir_info in DIRECTORIES:
            records = scrape_directory(session, dir_info)
            writer.writerows(records)
            print(f"Saved {len(records)} records for {dir_info['year']}.")


if __name__ == "__main__":
    main()