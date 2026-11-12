#!/usr/bin/env python3
"""
detect_data_anomalies.py
========================
Automated anomaly detector across Newport Street Directory dataset (<= 1936).
Detects:
  1. SHIFTED_NAME_IN_TRADE: Personal names or person+trade trapped in trade column with blank/vacant surname.
  2. BUSINESS_ENTITY_IN_TRADE: Pure business/shop/inn trapped in trade column; heals to surname + trade.
  3. ROTATED_COLUMNS: Tabular offsets (e.g. house_number holds surname, surname holds trade, forename holds initials).
  4. TRADE_BLEED_IN_FORENAME: Forename holds inline occupation tokens (e.g. 'Arthur, mason', 'Jas., insur agent').
  5. BUILDING_IN_NAME: Inn, hotel, house, arms, villa trapped in forename or surname.
  6. NAME_SPLIT_IN_TRADE: Surnames/initials embedded before trade (e.g. 'Pitchford J. B., pk btcher').
  7. SPLIT_1936_NAMES: 1936 layout split where surname holds initial, forename holds initial + surname + trade.

Outputs:
  - reports/data_anomalies.tsv
  - reports/anomaly_review.html (Interactive Dashboard)
"""

import os
import sys
import csv
import re
import json
from collections import Counter, defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

TSV_OUT = os.path.join(REPORTS_DIR, "data_anomalies.tsv")
HTML_OUT = os.path.join(REPORTS_DIR, "anomaly_review.html")

MAX_ALLOWED_YEAR = 1936

BUILDING_WORDS = {
    "inn", "hotel", "arms", "tavern", "vaults", "villa", "villas", "cottage", "cottages",
    "chambers", "lodge", "house", "works", "foundry", "brewery", "depot", "hall", "institute",
    "club", "church", "chapel", "barracks", "station", "shed", "sheds", "mills", "wharf"
}
BUILDING_REGEX = re.compile(r"\b(Inn|Hotel|Arms|Tavern|Vaults|Villa|Villas|Cottage|Cottages|Chambers|Lodge|House|Works|Foundry|Brewery|Depot|Institute|Club)\b", re.I)

KNOWN_TRADES_REGEX = re.compile(
    r"\b(mason|labourer|fitter|carpenter|engine driver|dock police|insurance agent|insur agent|"
    r"seaman|trimmer|porter|clerk|solicitor|draper|shoemaker|bootmaker|blacksmith|musician|"
    r"hairdresser|tobacconist|confectioner|butcher|grocer|painter|plumber|ironworker|steelworker|"
    r"haulier|boilermaker|shipwright|ship wt|riveter|carptr|machinist|platelayer|electrician|"
    r"chemist|stationmaster|manager|mgr|proprietor|propr|agent|cashier|teacher of music|trunkmaker)\b",
    re.I
)

COMMON_FORENAMES = {
    "william", "thomas", "john", "james", "david", "charles", "george", "edward",
    "alfred", "arthur", "frederick", "robert", "richard", "henry", "joseph", "samuel",
    "walter", "albert", "herbert", "francis", "ernest", "edwin", "frank", "sidney",
    "mary", "elizabeth", "sarah", "ann", "annie", "laura", "ada", "emily"
}

COMMON_SURNAMES = {
    'davies', 'jones', 'williams', 'evans', 'thomas', 'lewis', 'morgan', 'smith',
    'phillips', 'griffiths', 'jenkins', 'owen', 'rees', 'edwards', 'harris',
    'richards', 'powell', 'price', 'hughes', 'collins', 'baker', 'clark', 'allen',
    'martin', 'england', 'hacker', 'gibson', 'cole', 'norman', 'pitchford', 'bloom',
    'thorne', 'ensins', 'palmer', 'witts', 'aston', 'hart', 'bennett', 'stephens',
    'tovey', 'sheppard', 'stead', 'stone', 'huggins', 'marsh', 'gething', 'hurford',
    'deer', 'gritton', 'west', 'langford', 'pitt', 'davis', 'howell'
}

HONORIFICS = {'mr', 'mrs', 'miss', 'rev', 'dr', 'capt', 'major', 'col', 'sir', 'lord', 'j.p.', 'jp'}

def is_valid_house_number(h):
    if not h:
        return False
    # Valid house numbers: 12, 12a, 6-7, 37 & 39, 4a-5A, 100-98, 12/14, 1st floor, etc.
    if re.search(r"\d", h):
        return True
    return False

def clean_title_case(s):
    if not s:
        return ""
    words = s.split()
    return " ".join(w.capitalize() if not ('.' in w or w.isupper() or '-' in w) else w for w in words)

def analyze_record(idx, r):
    yr_str = r.get("year", "").strip()
    if yr_str.isdigit() and int(yr_str) > MAX_ALLOWED_YEAR:
        return None

    yr = yr_str
    st = r.get("street", "").strip()
    hn = r.get("house_number", "").strip()
    bd = r.get("building_name", "").strip()
    sn = r.get("surname", "").strip()
    fn = r.get("forename", "").strip()
    tr = r.get("trade", "").strip()

    # Normalize blanks
    if sn.lower() in {"void", "vacant", "residence", "null", "nan"}:
        sn = ""
    if fn.lower() in {"void", "vacant", "residence", "null", "nan"}:
        fn = ""

    findings = []

    # -------------------------------------------------------------
    # 1. ROTATED_COLUMNS: Tabular offset where house_number is surname,
    #    surname is trade, and forename is initials / forename
    # -------------------------------------------------------------
    if hn and not is_valid_house_number(hn):
        # hn looks like a word/surname (e.g. 'Kelson', 'Moss', 'Price', 'Davies')
        if sn.lower() in {"builder", "bakers", "baker", "ironworker", "shoemaker", "cachbldr", "plumber", "furnaceman", "trimmer"}:
            findings.append({
                "category": "ROTATED_COLUMNS",
                "confidence": "HIGH",
                "explanation": f"Column rotation: house_number '{hn}' is surname, surname '{sn}' is trade",
                "proposed": {
                    "house_number": "",
                    "building_name": bd,
                    "surname": hn,
                    "forename": fn,
                    "trade": clean_title_case(sn)
                }
            })

    # -------------------------------------------------------------
    # 2. SPLIT_1936_NAMES: In 1936 OCR, initial in surname + initial/surname/trade in forename
    #    e.g. sn='H', fn='B. Smith', tr='Dock Manager' -> sn='Smith', fn='H. B.', tr='Dock Manager'
    # -------------------------------------------------------------
    if sn and len(sn) == 1 and sn.isalpha() and fn:
        m = re.match(r"^([A-Z]\.?\s+)?([A-Z][a-z]+)(?:\s+(.*))?$", fn)
        if m:
            init2 = (m.group(1) or "").strip()
            p_surname = m.group(2).strip()
            extra = (m.group(3) or "").strip()
            full_fn = f"{sn}. {init2}".strip() if init2 else f"{sn}."
            full_tr = tr if tr else clean_title_case(extra)
            findings.append({
                "category": "SPLIT_1936_NAMES",
                "confidence": "HIGH",
                "explanation": f"1936 split name: initial '{sn}' and '{fn}'",
                "proposed": {
                    "house_number": hn,
                    "building_name": bd,
                    "surname": p_surname,
                    "forename": full_fn,
                    "trade": full_tr
                }
            })

    # -------------------------------------------------------------
    # 3. TRADE_BLEED_IN_FORENAME: Forename holds inline occupation
    #    e.g. 'Jas., insur agent', 'Arthur, mason', 'Ralph, musician'
    # -------------------------------------------------------------
    if fn and "," in fn:
        parts = [p.strip() for p in fn.split(",", 1)]
        if len(parts) == 2 and KNOWN_TRADES_REGEX.search(parts[1]):
            new_fn = parts[0]
            new_tr = clean_title_case(parts[1]) if not tr else f"{tr}, {clean_title_case(parts[1])}"
            findings.append({
                "category": "TRADE_BLEED_IN_FORENAME",
                "confidence": "HIGH",
                "explanation": f"Occupation '{parts[1]}' trapped in forename '{fn}'",
                "proposed": {
                    "house_number": hn,
                    "building_name": bd,
                    "surname": sn,
                    "forename": new_fn,
                    "trade": new_tr
                }
            })

    # -------------------------------------------------------------
    # 4. BUILDING_IN_NAME: Building/Inn/Hotel trapped in forename/surname
    # -------------------------------------------------------------
    if fn and BUILDING_REGEX.search(fn):
        bldg_match = re.search(r"^(.*?)\s*([A-Z][a-zA-Z\s\']*(?:Inn|Hotel|Arms|Tavern|Vaults|Villa|Cottage|House|Brewery|Works|Chambers|Lodge))\s*(.*?)$", fn, re.I)
        if bldg_match:
            prefix, bname, suffix = bldg_match.groups()
            cleaned_fn = f"{prefix.strip()} {suffix.strip()}".strip()
            findings.append({
                "category": "BUILDING_IN_NAME",
                "confidence": "HIGH",
                "explanation": f"Building '{bname}' trapped in forename '{fn}'",
                "proposed": {
                    "house_number": hn,
                    "building_name": bname.strip() if not bd else f"{bd}, {bname.strip()}",
                    "surname": sn,
                    "forename": cleaned_fn,
                    "trade": tr
                }
            })
    elif sn and BUILDING_REGEX.search(sn) and not bd:
        pure_bldg = re.match(r"^(?:The\s+)?([A-Za-z\s\']+\s+(?:Inn|Hotel|Arms|Tavern|Vaults|Brewery|Works|Foundry|House))\s*[\—\-]?$", sn, re.I)
        if pure_bldg:
            bname = pure_bldg.group(1).strip()
            # If trade has a person name (e.g. 'Witts Miss Laura L'), extract person!
            m_tr_person = re.match(r"^([A-Z][a-z]+)\s+((?:Miss|Mrs|Mr|Rev)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$", tr)
            if m_tr_person:
                p_sn, p_fn = m_tr_person.groups()
                findings.append({
                    "category": "BUILDING_IN_NAME",
                    "confidence": "HIGH",
                    "explanation": f"Building '{bname}' in surname with resident '{p_sn} {p_fn}' in trade",
                    "proposed": {
                        "house_number": hn,
                        "building_name": bname,
                        "surname": p_sn,
                        "forename": p_fn,
                        "trade": ""
                    }
                })
            else:
                findings.append({
                    "category": "BUILDING_IN_NAME",
                    "confidence": "HIGH",
                    "explanation": f"Building entity '{bname}' placed in surname",
                    "proposed": {
                        "house_number": hn,
                        "building_name": bname,
                        "surname": "",
                        "forename": fn,
                        "trade": tr
                    }
                })

    # -------------------------------------------------------------
    # 5. SHIFTED_NAME_IN_TRADE & BUSINESS_ENTITY_IN_TRADE:
    # -------------------------------------------------------------
    if not sn and tr:
        # Check 5A: Compound Business with Person e.g. "Decorator Supply—C. A. Smith"
        m_bldg_person = re.match(r"^([A-Za-z\s\.,&]+)[\—\-]\s*([A-Z\.\s]+)\s+([A-Z][a-z]+)$", tr)
        if m_bldg_person:
            bname, p_fn, p_sn = m_bldg_person.groups()
            findings.append({
                "category": "NAME_SPLIT_IN_TRADE",
                "confidence": "HIGH",
                "explanation": f"Split business and person: '{bname}' and '{p_fn} {p_sn}' in trade",
                "proposed": {
                    "house_number": hn,
                    "building_name": bname.strip(),
                    "surname": p_sn.strip(),
                    "forename": p_fn.strip(),
                    "trade": ""
                }
            })

        # Check 5B: Person with trade e.g. "Haggett T. P., Butcher" or "Williams Alfred, tailor" or "W. West, manager"
        elif "," in tr:
            parts = tr.split(",", 1)
            left = parts[0].strip()
            right = parts[1].strip()

            # Is left "Boots" and right "Cash Chemist"?
            if left.lower() == "boots" and "chemist" in right.lower():
                findings.append({
                    "category": "BUSINESS_ENTITY_IN_TRADE",
                    "confidence": "HIGH",
                    "explanation": f"Business entity '{left}' and trade '{right}' in trade column",
                    "proposed": {
                        "house_number": hn,
                        "building_name": bd if bd else "Boots",
                        "surname": "Boots",
                        "forename": "",
                        "trade": clean_title_case(right)
                    }
                })
            else:
                # Check for "Surname Initials" e.g. "Haggett T. P."
                m_sn_init = re.match(r"^([A-Z][a-z]+)\s+([A-Z\.\s]+)$", left)
                # Check for "Initials/Forename Surname" e.g. "W. West", "Tom Pitt", "Williams Alfred"
                m_two_words = re.match(r"^([A-Z][a-z\.]*(?:\s+[A-Z][a-z\.]*)*)\s+([A-Z][a-z]+)$", left)

                if m_sn_init and all(len(p) <= 2 or p.isupper() for p in m_sn_init.group(2).split()):
                    t_sn = m_sn_init.group(1).strip()
                    t_fn = m_sn_init.group(2).strip()
                    findings.append({
                        "category": "SHIFTED_NAME_IN_TRADE",
                        "confidence": "HIGH",
                        "explanation": f"Shifted resident '{t_sn} {t_fn}' and trade '{right}' in trade column",
                        "proposed": {
                            "house_number": hn,
                            "building_name": bd,
                            "surname": t_sn,
                            "forename": t_fn,
                            "trade": clean_title_case(right)
                        }
                    })
                elif m_two_words:
                    p1 = m_two_words.group(1).strip()
                    p2 = m_two_words.group(2).strip()
                    if p2.lower() in COMMON_FORENAMES or p1.lower() in COMMON_SURNAMES:
                        t_sn, t_fn = p1, p2
                    else:
                        t_sn, t_fn = p2, p1
                    findings.append({
                        "category": "SHIFTED_NAME_IN_TRADE",
                        "confidence": "HIGH",
                        "explanation": f"Shifted resident '{t_fn} {t_sn}' and trade '{right}' in trade column",
                        "proposed": {
                            "house_number": hn,
                            "building_name": bd,
                            "surname": t_sn,
                            "forename": t_fn,
                            "trade": clean_title_case(right)
                        }
                    })

        # Check 5C: Business entity with suffix (Ltd, Co., Works, Brewery, Stores)
        elif re.search(r"\b(Ltd|Ld|Co|Stores|Works|Brewery|Bazaar|Foundry)\b", tr, re.I):
            findings.append({
                "category": "BUSINESS_ENTITY_IN_TRADE",
                "confidence": "HIGH",
                "explanation": f"Pure business entity '{tr}' in trade column",
                "proposed": {
                    "house_number": hn,
                    "building_name": bd if bd else tr,
                    "surname": tr,
                    "forename": "",
                    "trade": "" if bd else tr
                }
            })

    if not findings:
        return None

    best = findings[0]
    return {
        "record_idx": idx,
        "year": yr,
        "street": st,
        "category": best["category"],
        "confidence": best["confidence"],
        "explanation": best["explanation"],
        "raw_house_number": hn,
        "raw_building_name": bd,
        "raw_surname": sn,
        "raw_forename": fn,
        "raw_trade": tr,
        "healed_house_number": best["proposed"]["house_number"],
        "healed_building_name": best["proposed"]["building_name"],
        "healed_surname": best["proposed"]["surname"],
        "healed_forename": best["proposed"]["forename"],
        "healed_trade": best["proposed"]["trade"],
    }


def generate_html_report(anomalies, stats):
    """Generate self-contained interactive audit dashboard."""
    cat_counts = stats["by_category"]
    conf_counts = stats["by_confidence"]
    total = len(anomalies)

    records_json = json.dumps(anomalies)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Newport Directory Anomaly Audit Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      --bg: #F9F8F6;
      --card-bg: #FFFFFF;
      --border: #E5E0D8;
      --text: #2C2825;
      --muted: #6B655F;
      --primary: #8C2522;
      --primary-hover: #731E1B;
      --accent: #2B547E;
      --success: #2E7D32;
      --warning: #ED6C02;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }}
    header {{
      max-width: 1400px;
      margin: 0 auto 24px auto;
      border-bottom: 2px solid var(--border);
      padding-bottom: 16px;
    }}
    h1 {{
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 6px;
    }}
    .subtitle {{
      color: var(--muted);
      font-size: 0.95rem;
    }}
    .metrics-bar {{
      display: flex;
      gap: 16px;
      margin: 20px 0;
      flex-wrap: wrap;
    }}
    .metric-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 18px;
      min-width: 150px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    .metric-card .label {{
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--muted);
      font-weight: 600;
    }}
    .metric-card .val {{
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--primary);
    }}
    .controls {{
      max-width: 1400px;
      margin: 0 auto 20px auto;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      background: var(--card-bg);
      padding: 16px;
      border-radius: 8px;
      border: 1px solid var(--border);
    }}
    .control-group {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .control-group label {{
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
    }}
    input, select {{
      padding: 8px 12px;
      border: 1px solid var(--border);
      border-radius: 6px;
      font-size: 0.9rem;
      background: #FFF;
      color: var(--text);
    }}
    input:focus, select:focus {{
      outline: none;
      border-color: var(--primary);
    }}
    .table-container {{
      max-width: 1400px;
      margin: 0 auto;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow-x: auto;
      box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      text-align: left;
    }}
    th {{
      background: #F3EFEA;
      color: var(--text);
      font-weight: 600;
      position: sticky;
      top: 0;
      z-index: 2;
    }}
    tr:hover td {{
      background: #FAF7F2;
    }}
    .tag {{
      display: inline-block;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.72rem;
      font-weight: 600;
    }}
    .tag-category {{ background: #E8EEF5; color: var(--accent); }}
    .tag-high {{ background: #E8F5E9; color: var(--success); }}
    .tag-med {{ background: #FFF3E0; color: var(--warning); }}
    .diff-box {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      font-size: 0.8rem;
    }}
    .raw-view {{
      background: #FFF0F0;
      padding: 6px 8px;
      border-radius: 4px;
      border: 1px solid #FFCDD2;
      color: #900;
    }}
    .healed-view {{
      background: #F0FFF4;
      padding: 6px 8px;
      border-radius: 4px;
      border: 1px solid #C8E6C9;
      color: #060;
    }}
    .field-lbl {{
      font-size: 0.68rem;
      font-weight: 600;
      text-transform: uppercase;
      color: var(--muted);
      margin-right: 4px;
    }}
    .pagination-bar {{
      max-width: 1400px;
      margin: 16px auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.85rem;
      color: var(--muted);
    }}
    .btn {{
      padding: 6px 14px;
      border: 1px solid var(--border);
      background: #FFF;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
    }}
    .btn:hover {{
      background: #F0EAE1;
    }}
    .btn:disabled {{
      opacity: 0.4;
      cursor: not-allowed;
    }}
  </style>
</head>
<body>

  <header>
    <h1>Newport Street Directory Anomaly Audit</h1>
    <div class="subtitle">
      Automated layout diagnostic scanning 319k+ historical records (1835–1936).
      Zero-screenshot review for column shifts, trapped buildings, trades in names, and split entities.
    </div>

    <div class="metrics-bar">
      <div class="metric-card">
        <div class="label">Total Detected</div>
        <div class="val">{total:,}</div>
      </div>
      <div class="metric-card">
        <div class="label">Shifted Trades</div>
        <div class="val">{cat_counts.get("SHIFTED_NAME_IN_TRADE", 0):,}</div>
      </div>
      <div class="metric-card">
        <div class="label">Business Entities</div>
        <div class="val">{cat_counts.get("BUSINESS_ENTITY_IN_TRADE", 0):,}</div>
      </div>
      <div class="metric-card">
        <div class="label">Trapped Buildings</div>
        <div class="val">{cat_counts.get("BUILDING_IN_NAME", 0):,}</div>
      </div>
      <div class="metric-card">
        <div class="label">1936 Split Names</div>
        <div class="val">{cat_counts.get("SPLIT_1936_NAMES", 0):,}</div>
      </div>
      <div class="metric-card">
        <div class="label">Rotated Columns</div>
        <div class="val">{cat_counts.get("ROTATED_COLUMNS", 0):,}</div>
      </div>
      <div class="metric-card">
        <div class="label">High Confidence</div>
        <div class="val">{conf_counts.get("HIGH", 0):,}</div>
      </div>
    </div>
  </header>

  <div class="controls">
    <div class="control-group" style="flex: 2;">
      <label>Search Text / Resident / Street</label>
      <input type="text" id="searchInput" placeholder="Filter by street, name, or occupation...">
    </div>
    <div class="control-group" style="flex: 1;">
      <label>Category Filter</label>
      <select id="catSelect">
        <option value="">All Categories ({total:,})</option>
        <option value="SHIFTED_NAME_IN_TRADE">Shifted Name in Trade ({cat_counts.get("SHIFTED_NAME_IN_TRADE", 0)})</option>
        <option value="BUSINESS_ENTITY_IN_TRADE">Business Entity in Trade ({cat_counts.get("BUSINESS_ENTITY_IN_TRADE", 0)})</option>
        <option value="BUILDING_IN_NAME">Building in Name ({cat_counts.get("BUILDING_IN_NAME", 0)})</option>
        <option value="SPLIT_1936_NAMES">1936 Split Names ({cat_counts.get("SPLIT_1936_NAMES", 0)})</option>
        <option value="ROTATED_COLUMNS">Rotated Columns ({cat_counts.get("ROTATED_COLUMNS", 0)})</option>
        <option value="TRADE_BLEED_IN_FORENAME">Trade Bleed in Forename ({cat_counts.get("TRADE_BLEED_IN_FORENAME", 0)})</option>
        <option value="NAME_SPLIT_IN_TRADE">Name Split in Trade ({cat_counts.get("NAME_SPLIT_IN_TRADE", 0)})</option>
      </select>
    </div>
    <div class="control-group">
      <label>Confidence</label>
      <select id="confSelect">
        <option value="">All Confidence</option>
        <option value="HIGH">High ({conf_counts.get("HIGH", 0)})</option>
        <option value="MEDIUM">Medium ({conf_counts.get("MEDIUM", 0)})</option>
      </select>
    </div>
    <div class="control-group">
      <label>Directory Year</label>
      <input type="text" id="yearInput" placeholder="e.g. 1927" style="width: 100px;">
    </div>
  </div>

  <div class="pagination-bar">
    <div id="statusText">Showing 1–50 of {total} records</div>
    <div>
      <button class="btn" id="prevBtn" onclick="prevPage()">Previous</button>
      <button class="btn" id="nextBtn" onclick="nextPage()">Next</button>
    </div>
  </div>

  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th style="width: 60px;">Year</th>
          <th style="width: 180px;">Street & House</th>
          <th style="width: 160px;">Category</th>
          <th>Raw Extracted Record vs Proposed Cleaned Record</th>
          <th style="width: 240px;">Diagnostic Note</th>
        </tr>
      </thead>
      <tbody id="tableBody"></tbody>
    </table>
  </div>

  <script>
    const anomalies = {records_json};
    let filtered = [...anomalies];
    let currentPage = 1;
    const pageSize = 50;

    const searchInput = document.getElementById('searchInput');
    const catSelect = document.getElementById('catSelect');
    const confSelect = document.getElementById('confSelect');
    const yearInput = document.getElementById('yearInput');
    const tableBody = document.getElementById('tableBody');
    const statusText = document.getElementById('statusText');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    function applyFilter() {{
      const q = searchInput.value.toLowerCase().trim();
      const cat = catSelect.value;
      const conf = confSelect.value;
      const yr = yearInput.value.trim();

      filtered = anomalies.filter(r => {{
        if (cat && r.category !== cat) return false;
        if (conf && r.confidence !== conf) return false;
        if (yr && r.year !== yr) return false;
        if (q) {{
          const str = (r.street + ' ' + r.raw_surname + ' ' + r.raw_forename + ' ' + r.raw_trade + ' ' + r.explanation).toLowerCase();
          if (!str.includes(q)) return false;
        }}
        return true;
      }});

      currentPage = 1;
      render();
    }}

    function render() {{
      const start = (currentPage - 1) * pageSize;
      const end = Math.min(start + pageSize, filtered.length);
      const slice = filtered.slice(start, end);

      statusText.innerText = `Showing ${{filtered.length ? start + 1 : 0}}–${{end}} of ${{filtered.length}} matching anomalies (Total: ${{anomalies.length}})`;
      prevBtn.disabled = currentPage === 1;
      nextBtn.disabled = end >= filtered.length;

      let html = '';
      for (const r of slice) {{
        const confClass = r.confidence === 'HIGH' ? 'tag-high' : 'tag-med';
        html += `<tr>
          <td><strong>${{r.year}}</strong></td>
          <td>
            <strong>${{r.street}}</strong><br>
            <span style="color: var(--muted);">${{r.raw_house_number ? 'No. ' + r.raw_house_number : 'Unnumbered'}}</span>
          </td>
          <td>
            <span class="tag tag-category">${{r.category}}</span><br>
            <span class="tag ${{confClass}}" style="margin-top: 4px;">${{r.confidence}} CONFIDENCE</span>
          </td>
          <td>
            <div class="diff-box">
              <div class="raw-view">
                <div><span class="field-lbl">Building:</span> ${{r.raw_building_name || '—'}}</div>
                <div><span class="field-lbl">Surname:</span> ${{r.raw_surname || '<em style="color:#888;">(blank / vacant)</em>'}}</div>
                <div><span class="field-lbl">Forename:</span> ${{r.raw_forename || '—'}}</div>
                <div><span class="field-lbl">Trade:</span> ${{r.raw_trade || '—'}}</div>
              </div>
              <div class="healed-view">
                <div><span class="field-lbl">Building:</span> ${{r.healed_building_name || '—'}}</div>
                <div><span class="field-lbl">Surname:</span> <strong>${{r.healed_surname || '—'}}</strong></div>
                <div><span class="field-lbl">Forename:</span> ${{r.healed_forename || '—'}}</div>
                <div><span class="field-lbl">Trade:</span> ${{r.healed_trade || '—'}}</div>
              </div>
            </div>
          </td>
          <td style="font-size: 0.8rem; color: #4A443F;">${{r.explanation}}</td>
        </tr>`;
      }}

      if (!slice.length) {{
        html = '<tr><td colspan="5" style="text-align: center; padding: 40px; color: var(--muted);">No matching anomalies found.</td></tr>';
      }}
      tableBody.innerHTML = html;
    }}

    function prevPage() {{
      if (currentPage > 1) {{ currentPage--; render(); }}
    }}
    function nextPage() {{
      if ((currentPage * pageSize) < filtered.length) {{ currentPage++; render(); }}
    }}

    searchInput.addEventListener('input', applyFilter);
    catSelect.addEventListener('change', applyFilter);
    confSelect.addEventListener('change', applyFilter);
    yearInput.addEventListener('input', applyFilter);

    render();
  </script>
</body>
</html>
"""
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Interactive Audit Dashboard generated at: {HTML_OUT}")


def main():
    print("Reading data.csv and scanning for anomalies (year <= 1936)...")
    anomalies = []
    category_counts = Counter()
    confidence_counts = Counter()

    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            res = analyze_record(i, row)
            if res:
                anomalies.append(res)
                category_counts[res["category"]] += 1
                confidence_counts[res["confidence"]] += 1

    print(f"\n[DONE] Scan finished. Found {len(anomalies):,} anomalies across the dataset.")
    print("Breakdown by Category:")
    for cat, c in category_counts.most_common():
        print(f"  * {cat:<28}: {c:,}")
    print("\nBreakdown by Confidence:")
    for conf, c in confidence_counts.most_common():
        print(f"  * {conf:<12}: {c:,}")

    # Write TSV
    fieldnames = [
        "record_idx", "year", "street", "category", "confidence", "explanation",
        "raw_house_number", "raw_building_name", "raw_surname", "raw_forename", "raw_trade",
        "healed_house_number", "healed_building_name", "healed_surname", "healed_forename", "healed_trade"
    ]
    with open(TSV_OUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(anomalies)
    print(f"\nSummary TSV written to: {TSV_OUT}")

    # Generate HTML Dashboard
    stats = {
        "by_category": dict(category_counts),
        "by_confidence": dict(confidence_counts)
    }
    generate_html_report(anomalies, stats)


if __name__ == "__main__":
    main()
