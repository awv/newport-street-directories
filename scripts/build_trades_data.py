#!/usr/bin/env python3
"""
build_trades_data.py
--------------------
Scans data.csv and compiles a pre-aggregated, optimized trade index (data/trades.json)
for the Occupations Audit tool (trades.html).

Extracts:
- Raw trade occurrence counts
- Sample resident record and years active for each trade
- Family / occupational sector classification
- Issue detection (punctuation, digits, address spills, ditto)
- Case-twin detection (case-insensitive variants like 'labourer' vs 'Labourer')
"""

import csv
import json
import os
import re
import sys
import time
from collections import defaultdict, Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "scripts" else SCRIPT_DIR
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
OUTPUT_JSON = os.path.join(PROJECT_ROOT, "data", "trades.json")
VERIFIED_JSON = os.path.join(PROJECT_ROOT, "data", "verified_trades.json")

MAX_PUBLIC_YEAR = int(os.environ["MAX_PUBLIC_YEAR"]) if "MAX_PUBLIC_YEAR" in os.environ and os.environ["MAX_PUBLIC_YEAR"].isdigit() else 1936

NON_TRADE_PAT = re.compile(
    r'^(?:mrs\.?|miss\.?|mr\.?|thos\.?|jas\.?|wm\.?|saml\.?|john|geo\.?|chas\.?|hy\.?|richd\.?|'
    r'ltd\.?|limited|co\.?|& co\.?|co\.? ltd\.?|ld\.?|return\.?|junr?\.?|&|&c|etc|;;;|\(return\)|ditto|do\.?|'
    r'here is|here are|from \d+|the roundabout|\(?flat \d+.*?\)?|tel\.?|telephone)\b',
    re.I
)

def classify_family(trade):
    t = trade.lower().strip()
    if re.search(r'\b(labourer|labr|lbr|laborer)\b', t):
        return 'Labourers & Manual'
    if re.search(r'\b(driver|drvr|dvr|drivr|haulier|carter|coachman|chauffeur|motorman)\b', t):
        return 'Transport & Drivers'
    if re.search(r'\b(ironworker|steelworker|smith|moulder|boilermaker|fitter|roller|furnaceman|wire\s*drawer|puddler|striker|foundry|riveter|tubeworker)\b', t):
        return 'Metal & Iron Workers'
    if re.search(r'\b(carpenter|joiner|mason|bricklayer|painter|plasterer|plumber|builder|decorator|slater|glazier|stone\s*cutter)\b', t):
        return 'Building & Construction'
    if re.search(r'\b(seaman|mariner|docker|dock\s*labourer|coal\s*trimmer|trimmer|stevedore|rigger|waterman|pilot|boatman|tugs?|sailmaker|shipwright)\b', t):
        return 'Maritime & Docks'
    if re.search(r'\b(g\.?w\.?r|railway|guard|signalman|shunter|platelayer|porter|engine\s*driver|locomotive|ganger)\b', t):
        return 'Railway'
    if re.search(r'\b(grocer|butcher|baker|draper|confectioner|newsagent|tobacconist|greengrocer|outfitter|stationer|fishmonger|ironmonger|chemist|druggist|innkeeper|publican|beer\s*retailer|victualler)\b', t):
        return 'Shopkeepers & Retail'
    if re.search(r'\b(clerk|agent|traveller|manager|secretary|cashier|accountant|collector|broker|merchant|dealer)\b', t):
        return 'Clerical & Commercial'
    if re.search(r'\b(tailor|bootmaker|dressmaker|shoemaker|upholsterer|watchmaker|cooper|printer|bookbinder|saddler|milliner|brushmaker|wheelwright|basketmaker)\b', t):
        return 'Crafts & Artisans'
    if re.search(r'\b(gardener|caretaker|cook|waiter|housekeeper|laundress|charwoman|servant|domestic|nurse|cellarman)\b', t):
        return 'Service & Domestic'
    if re.search(r'\b(teacher|schoolmaster|schoolmistress|physician|surgeon|doctor|solicitor|barrister|police|constable|sergeant|inspector|civil\s*servant|minister|vicar|clergyman|curate|priest|artist|photographer|musician|journalist)\b', t):
        return 'Professional & Civic'
    if re.search(r'^(here is|here are|from \d+|the roundabout|\(?flat \d+|tel\.?|mrs\.?|miss\.?|mr\.?|return|ditto|do\.?|ltd|co\.)\b', t) or re.search(r'[;\/:_\{\}\[\]\\\|]', t):
        return 'Suspected Non-Trade / Spill'
    return 'Other Occupations'

def to_title_case(text):
    text = text.strip()
    if text.upper() in ('G.W.R.', 'G.W.R', 'G.P.O.', 'GPO', 'P.C.', 'H.M.C.'):
        return text.upper()
    words = text.split()
    clean_words = []
    for w in words:
        if w.upper() in ('G.W.R.', 'G.W.R', 'G.P.O.', 'GPO', 'P.C.', 'H.M.C.'):
            clean_words.append(w.upper())
        elif w.lower() in ('and', 'of', '&', 'for', 'the', 'in', 'at'):
            clean_words.append(w.lower() if clean_words else w.capitalize())
        else:
            clean_words.append(w.capitalize())
    return ' '.join(clean_words)

def get_issue_category(t):
    if re.fullmatch(r'[-—_\|~`.,:;!?\'\"\\/\[\]{}()<>\s]+', t):
        return 'Pure Symbols & Lines'
    if re.search(r'\d', t):
        return 'Contains Digits'
    if re.fullmatch(r'(?:do\.?|ditto)', t, re.I) or re.search(r'\b(?:do|ditto)\b', t, re.I):
        return 'Ditto Variants'
    if re.search(r'^(?:here is|here are|from \d+|the roundabout|\(?flat \d+|tel\.?|telephone)\b', t, re.I):
        return 'Street Waypoints'
    if re.fullmatch(r'(?:&c|etc\.?|nan|\(?return\)?\.?)', t, re.I):
        return 'Floating Suffixes'
    if re.match(r'^(?:[A-Z][a-z]*\.?|[A-Z]\.?|\b(?:Wm|Hy|Thos|Geo|Chas|John|Jas|Saml|Fred|Edwd|Arth|Walt)\b\.?),?\s+[A-Za-z]', t):
        return 'Name / Company Leaks'
    if re.search(r'[;\/:_\{\}\[\]\\\|]', t):
        return 'Symbol Noise'
    if len(t) <= 3:
        return 'Short Tokens (<=3)'
    return 'Other Issues'

def build():
    t0 = time.time()
    print(f"Reading {DATA_CSV}...")
    
    counts = Counter()
    samples = {}
    years_seen = defaultdict(set)
    total_rows = 0

    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            yr = (r.get("year") or "").strip()
            if MAX_PUBLIC_YEAR and yr.isdigit() and int(yr) > MAX_PUBLIC_YEAR:
                continue
            total_rows += 1
            t = (r.get("trade") or "").strip()
            if not t:
                continue
            counts[t] += 1
            yr = r.get("year", "")
            if yr:
                years_seen[t].add(yr)
            if t not in samples:
                samples[t] = [
                    r.get("year", ""),
                    r.get("street", ""),
                    r.get("house_number", ""),
                    r.get("building_name", ""),
                    r.get("forename", ""),
                    r.get("surname", "")
                ]

    lower_map = defaultdict(set)
    for t in counts:
        lower_map[t.lower()].add(t)

    verified_set = set()
    if os.path.exists(VERIFIED_JSON):
        try:
            with open(VERIFIED_JSON, "r", encoding="utf-8") as f:
                v_data = json.load(f)
                if isinstance(v_data, list):
                    verified_set = {x.lower().strip() for x in v_data if isinstance(x, str)}
                elif isinstance(v_data, dict):
                    verified_set = {x.lower().strip() for x in v_data.keys()}
        except Exception as e:
            print(f"Warning: could not read {VERIFIED_JSON}: {e}")

    trades_list = []
    fam_counts = Counter()
    issue_count = 0
    casing_twin_count = 0
    verified_count = 0

    for t, cnt in counts.most_common():
        s = samples[t]
        has_issue = bool(
            re.search(r'[;\/:_\{\}\[\]\\\|<>]', t) or
            re.search(r'\d', t) or
            t.lower() in ('do', 'ditto', 'do.', 'ditto.') or
            NON_TRADE_PAT.search(t) or
            (len(t) <= 3 and t.upper() not in ('G.W.R.', 'G.W.R', 'G.P.O.', 'GPO', 'P.C.', 'H.M.C.'))
        )
        has_case_twin = len(lower_map[t.lower()]) > 1
        fam = classify_family(t)
        fam_counts[fam] += 1
        if has_issue:
            issue_count += 1
        if has_case_twin:
            casing_twin_count += 1
        is_v = 1 if t.lower() in verified_set else 0
        if is_v:
            verified_count += 1

        trades_list.append({
            't': t,
            'c': cnt,
            'y': sorted(list(years_seen[t])),
            'r': s,
            'f': fam,
            'tc': to_title_case(t),
            'iss': 1 if has_issue else 0,
            'ic': get_issue_category(t) if has_issue else '',
            'ctw': 1 if has_case_twin else 0,
            'v': is_v
        })

    payload = {
        'total_rows': total_rows,
        'total_with_trade': sum(counts.values()),
        'unique_count': len(trades_list),
        'issue_count': issue_count,
        'casing_twin_count': casing_twin_count,
        'verified_count': verified_count,
        'families': dict(fam_counts),
        'trades': trades_list
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(',', ':'))

    print(f"Generated {OUTPUT_JSON} in {time.time() - t0:.2f}s:")
    print(f"  - Total records: {total_rows:,}")
    print(f"  - Records with trade: {sum(counts.values()):,}")
    print(f"  - Unique raw trades: {len(trades_list):,}")
    print(f"  - Suspected issues: {issue_count:,}")
    print(f"  - Trades with casing variants: {casing_twin_count:,}")

if __name__ == "__main__":
    build()
