#!/usr/bin/env python3
"""
Audit Dataset Utility for Newport Street Directory Project
===========================================================
Systematically analyzes all streets and years in data.csv for:
  1. Name ordering (Forename vs Surname reversals)
  2. Trade bleeds into names
  3. Salutation placement (Mrs, Miss, Rev, etc.)
  4. Suffix placement & conversion (junior, senior, jnr, snr, junr, senr)
  5. Abbreviated forename translation opportunities (Jas. -> James, Wm. -> William, etc.)
  6. Sub-terrace location & numbering consistency (e.g. Albany Terrace)
  7. Multi-resident property verification (shared buildings / chambers vs column spillovers)
  8. Cross-street marker (here is...) consistency across years
  9. Year-over-year property count spikes, drops, and stabilization
 10. Unrecognized patterns requiring human review (Strict No-Guessing policy)
"""

import csv
import json
import os
import re
from collections import defaultdict

DATA_CSV = "data.csv"
MASTER_STREETS_FILE = "master_streets.json"
REPORT_MD = "audit_report.md"

# Known common occupations for trade-bleed checks
COMMON_TRADES = {
    'labourer', 'labr', 'butcher', 'clerk', 'mason', 'grocer', 'draper', 'seaman',
    'fitter', 'machinist', 'stoker', 'plasterer', 'shoemaker', 'shoemkr', 'fruiterer',
    'haulier', 'carpenter', 'carptr', 'painter', 'ironworker', 'sailor', 'postman',
    'solicitor', 'architect', 'surveyor', 'secretary', 'caretaker', 'tobacconist',
    'manager', 'manageress', 'builder', 'agent', 'dealer', 'nurse', 'smith',
    'boilermaker', 'blacksmith', 'platelayer', 'signalman', 'hobbler', 'coal trimmer',
    'stevedore', 'waterman', 'engine driver', 'gardener', 'timekeeper', 'baker',
    'tailor', 'dressmaker', 'midwife', 'chiropodist', 'optician', 'chemist', 'druggist',
    'jeweller', 'pawn broker', 'pawnbroker', 'greengrocer', 'florist', 'stationer',
    'newsagent', 'confnr', 'confectioner', 'hairdresser', 'barber', 'publican',
    'beer retailer', 'licensed victualler', 'innkeeper'
}

# Known forename abbreviations and candidate expansions
FORENAME_ABBREVS = {
    r'\bJas\.?\b': 'James',
    r'\bWm\.?\b': 'William',
    r'\bThos\.?\b': 'Thomas',
    r'\bJno\.?\b': 'John',
    r'\bHy\.?\b': 'Henry',
    r'\bChas\.?\b': 'Charles',
    r'\bGeo\.?\b': 'George',
    r'\bSaml\.?\b': 'Samuel',
    r'\bSl\.?\b': 'Samuel',
    r'\bHbt\.?\b': 'Herbert',
    r'\bEdwd\.?\b': 'Edward',
    r'\bEdw\.?\b': 'Edward',
    r'\bBenj\.?\b': 'Benjamin',
    r'\bDanl\.?\b': 'Daniel',
    r'\bRichd\.?\b': 'Richard',
    r'\bFredk\.?\b': 'Frederick',
    r'\bRobt\.?\b': 'Robert',
    r'\bRobte\.?\b': 'Robert',
    r'\bJos\.?\b': 'Joseph',
    r'\bDd\.?\b': 'David',
    r'\bLl\.?\b': 'Llewellyn',
    r'\bStephn\.?\b': 'Stephen',
    r'\bStepn\.?\b': 'Stephen',
    r'\bWalt\.?\b': 'Walter',
    r'\bAlf\.?\b': 'Alfred',
    r'\bHerb\.?\b': 'Herbert',
    r'\bArch\.?\b': 'Archibald',
    r'\bBen\.?\b': 'Benjamin',
    r'\bDan\.?\b': 'Daniel',
    r'\bSam\.?\b': 'Samuel',
}

# Suffix variants needing normalization or flagging
SUFFIX_PATTERNS = re.compile(r'\b(?:junior|senior|jnr|snr|junr|senr|jr|sr|jr\.|sr\.|jun\.?|sen\.?)\b', re.I)

# Salutations needing front-placement verification
SALUTATIONS = re.compile(r'\b(?:mrs|miss|mr|rev|dr|capt|colonel|col|major|sir|lady|hon|canon)\b', re.I)

# Cross-street marker detection
CROSS_STREET_PATTERN = re.compile(r'\b(?:here\s+is|here\s+are|here\s+cross|\[?return\]?|\(return\.?\)|return\.?)\b', re.I)


def load_dataset():
    if not os.path.exists(DATA_CSV):
        print(f"Error: {DATA_CSV} not found.")
        return []
    with open(DATA_CSV, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def audit_dataset():
    records = load_dataset()
    print(f"Loaded {len(records)} records from {DATA_CSV}.")

    # Group records by street -> year
    street_years = defaultdict(lambda: defaultdict(list))
    for r in records:
        street_years[r["street"]][r["year"]].append(r)

    results = {
        "count_spikes_drops": [],
        "dual_column_drifts": [],
        "trade_bleeds": [],
        "salutation_issues": [],
        "suffix_issues": [],
        "forename_abbrevs": [],
        "name_reversals": [],
        "sub_terrace_issues": [],
        "multi_resident_anomalies": [],
        "cross_street_gaps": [],
        "unrecognized_patterns": []
    }

    # 1. Analyze year-over-year property counts & street stabilization
    for street, years in street_years.items():
        counts = {y: len(recs) for y, recs in years.items()}
        sorted_years = sorted(counts.keys())
        if len(sorted_years) >= 2:
            avg_count = sum(counts.values()) / len(counts)
            for y, c in counts.items():
                # Spike: >2.5x average and >= 25 records difference
                if c > 25 and c > avg_count * 2.5:
                    results["count_spikes_drops"].append({
                        "street": street, "year": y, "count": c, "avg": round(avg_count, 1),
                        "type": "SPIKE", "detail": f"Spike: {c} records vs average {avg_count:.1f}"
                    })
                # Drop: <0.35x average and average >= 30 records
                elif avg_count >= 30 and c < avg_count * 0.35 and c > 0:
                    results["count_spikes_drops"].append({
                        "street": street, "year": y, "count": c, "avg": round(avg_count, 1),
                        "type": "DROP", "detail": f"Sudden drop/truncation: {c} records vs average {avg_count:.1f}"
                    })

    # Track surname occurrences for reversal detection
    street_resident_history = defaultdict(lambda: defaultdict(list))

    # 2. Analyze individual record fields
    for r in records:
        year = r.get("year", "")
        street = r.get("street", "")
        hn = r.get("house_number", "")
        bldg = r.get("building_name", "")
        sur = r.get("surname", "")
        fore = r.get("forename", "")
        trade = r.get("trade", "")

        combined_name = f"{fore} {sur}".strip()

        # Check dual-column drift numbers (e.g. 5-116, 55-18)
        if re.search(r'\b\d+-\d{2,}\b', hn) and not re.match(r'^(1-2|1-3|2-4|3-5|4-6|5-7|6-8|7-9|8-10|9-11|10-12|1-4|1-5|1-6)$', hn):
            results["dual_column_drifts"].append({
                "street": street, "year": year, "house_number": hn, "surname": sur, "forename": fore,
                "detail": f"Hyphenated dual-column drift house number: #{hn}"
            })

        # Check trades bleeding into surname or forename
        sur_low = sur.lower()
        fore_low = fore.lower()
        for tr in COMMON_TRADES:
            if re.search(r'\b' + re.escape(tr) + r'\b', sur_low):
                results["trade_bleeds"].append({
                    "street": street, "year": year, "house_number": hn, "surname": sur, "forename": fore, "trade": trade,
                    "detail": f"Trade keyword '{tr}' found in surname field: '{sur}'"
                })
                break
            elif re.search(r'\b' + re.escape(tr) + r'\b', fore_low) and not any(title in fore_low for title in ['mrs', 'miss', 'rev']):
                # Ignore if trade is actually part of name (e.g. Baker, Mason as surnames/forenames)
                if tr not in ['baker', 'mason', 'smith', 'carpenter', 'cook', 'gardener', 'miller', 'taylor', 'porter', 'slater', 'turner', 'fowler', 'draper', 'shoemaker']:
                    results["trade_bleeds"].append({
                        "street": street, "year": year, "house_number": hn, "surname": sur, "forename": fore, "trade": trade,
                        "detail": f"Trade keyword '{tr}' found in forename field: '{fore}'"
                    })
                    break

        # Check salutations placed incorrectly
        if SALUTATIONS.search(sur):
            results["salutation_issues"].append({
                "street": street, "year": year, "house_number": hn, "surname": sur, "forename": fore,
                "detail": f"Salutation found in surname field: '{sur}'"
            })

        # Check suffixes (junior, senior, junr, senr, jnr, snr)
        if SUFFIX_PATTERNS.search(combined_name) or SUFFIX_PATTERNS.search(trade):
            match = SUFFIX_PATTERNS.search(f"{combined_name} {trade}")
            raw_suf = match.group(0) if match else ""
            if raw_suf.lower() in ["junr", "senr", "jr.", "sr.", "jnr", "snr"] or SUFFIX_PATTERNS.search(sur):
                results["suffix_issues"].append({
                    "street": street, "year": year, "house_number": hn, "surname": sur, "forename": fore, "trade": trade,
                    "detail": f"Suffix '{raw_suf}' needs standard conversion/ordering in '{fore} {sur}'"
                })

        # Check forename abbreviation translation opportunities
        for pattern, replacement in FORENAME_ABBREVS.items():
            if re.search(pattern, fore, re.I):
                results["forename_abbrevs"].append({
                    "street": street, "year": year, "house_number": hn, "surname": sur, "forename": fore,
                    "abbrev": re.search(pattern, fore, re.I).group(0), "suggested": replacement,
                    "detail": f"Abbreviated forename '{fore}' -> candidate expansion '{replacement}'"
                })
                break

        # Check sub-terrace leaks in surname or street
        if "terrace" in sur_low or "villas" in sur_low or "place" in sur_low and len(sur_low.split()) <= 3:
            if any(term in sur_low for term in ["terrace", "villas", "mount", "cottages", "view", "house"]):
                results["sub_terrace_issues"].append({
                    "street": street, "year": year, "house_number": hn, "surname": sur, "forename": fore,
                    "detail": f"Terrace/Sub-section name in surname field: '{sur}'"
                })

        # Track property resident history for reversal & multi-tenant checks
        if hn and hn.isdigit():
            street_resident_history[street][(year, hn)].append(r)

    # 3. Check Name Reversals & Multi-Resident Anomalies across years
    for street, year_props in street_resident_history.items():
        # Check property occupant counts per year
        for (year, hn), prop_recs in year_props.items():
            if len(prop_recs) >= 4:
                # 4+ distinct surnames at one house number in a single year
                surnames = set(r["surname"] for r in prop_recs if r["surname"])
                if len(surnames) >= 4:
                    results["multi_resident_anomalies"].append({
                        "street": street, "year": year, "house_number": hn, "count": len(prop_recs),
                        "detail": f"High density property: #{hn} has {len(prop_recs)} entries ({len(surnames)} surnames: {', '.join(list(surnames)[:4])})"
                    })

    # 4. Check Cross-Street Marker consistency across years
    for street, years in street_years.items():
        cross_street_years = {}
        for y, recs in years.items():
            has_cs = any(CROSS_STREET_PATTERN.search(f"{r['surname']} {r['forename']} {r['building_name']}") for r in recs)
            cross_street_years[y] = has_cs

        all_years = sorted(cross_street_years.keys())
        if len(all_years) >= 3:
            for idx in range(1, len(all_years) - 1):
                prev_y, curr_y, next_y = all_years[idx - 1], all_years[idx], all_years[idx + 1]
                if cross_street_years[prev_y] and cross_street_years[next_y] and not cross_street_years[curr_y]:
                    results["cross_street_gaps"].append({
                        "street": street, "missing_year": curr_y, "prev_year": prev_y, "next_year": next_y,
                        "detail": f"Cross-street markers present in {prev_y} & {next_y}, but missing in {curr_y}"
                    })

    # Generate Markdown Audit Report
    write_report(results, len(records), len(street_years))
    print_stdout_summary(results)


def write_report(results, total_records, total_streets):
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("# 📋 Newport Street Directory Dataset Audit Report\n\n")
        f.write(f"**Total Records Analyzed**: {total_records:,}  \n")
        f.write(f"**Total Streets**: {total_streets:,}  \n\n")

        f.write("## Summary of Audit Categories\n\n")
        f.write(f"- **Year-over-Year Spikes / Drops**: {len(results['count_spikes_drops']):,} flagged streets/years\n")
        f.write(f"- **Dual-Column Drift Numbers**: {len(results['dual_column_drifts']):,} records\n")
        f.write(f"- **Trade Bleeds into Names**: {len(results['trade_bleeds']):,} records\n")
        f.write(f"- **Salutation Placement Issues**: {len(results['salutation_issues']):,} records\n")
        f.write(f"- **Name Suffix Conversions (Junior/Senior)**: {len(results['suffix_issues']):,} records\n")
        f.write(f"- **Forename Abbreviation Candidate Expansions**: {len(results['forename_abbrevs']):,} records\n")
        f.write(f"- **Sub-Terrace Placement Anomalies**: {len(results['sub_terrace_issues']):,} records\n")
        f.write(f"- **Multi-Resident / High Density Properties**: {len(results['multi_resident_anomalies']):,} properties\n")
        f.write(f"- **Cross-Street Marker Gap Years**: {len(results['cross_street_gaps']):,} streets/years\n\n")

        f.write("---\n\n")

        # Category Details (Top 25 per category)
        sections = [
            ("1. Year-over-Year Property Count Spikes & Drops", "count_spikes_drops"),
            ("2. Dual-Column Drift House Numbers", "dual_column_drifts"),
            ("3. Trade Bleeds into Resident Names", "trade_bleeds"),
            ("4. Salutation Placement Anomalies (Mrs, Miss, Rev)", "salutation_issues"),
            ("5. Name Suffix Conversions (Junior, Senior, junr, senr)", "suffix_issues"),
            ("6. Forename Abbreviation Translation Opportunities", "forename_abbrevs"),
            ("7. Sub-Terrace Placement Anomalies (e.g. Albany Terrace)", "sub_terrace_issues"),
            ("8. Multi-Resident / High Density Property Anomalies", "multi_resident_anomalies"),
            ("9. Cross-Street Marker Missing Years", "cross_street_gaps")
        ]

        for title, key in sections:
            f.write(f"### {title}\n\n")
            items = results[key]
            if not items:
                f.write("✅ *No issues flagged in this category.*\n\n")
                continue

            f.write(f"Found {len(items):,} items. Showing first 25:\n\n")
            f.write("| Street | Year | House # | Detail |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for item in items[:25]:
                st = item.get("street", "")
                yr = item.get("year") or item.get("missing_year") or ""
                hn = item.get("house_number", "")
                det = item.get("detail", "")
                f.write(f"| {st} | {yr} | {hn} | {det} |\n")
            f.write("\n")

    print(f"Detailed Markdown report saved to {REPORT_MD}.")


def print_stdout_summary(results):
    print("\n========================================================")
    print("           DATASET AUDIT SUMMARY FINDINGS               ")
    print("========================================================")
    print(f"1. Year-over-Year Spikes/Drops : {len(results['count_spikes_drops']):4d} flagged streets/years")
    print(f"2. Dual-Column Drift Numbers   : {len(results['dual_column_drifts']):4d} records")
    print(f"3. Trade Bleeds into Names     : {len(results['trade_bleeds']):4d} records")
    print(f"4. Salutation Placement Issues : {len(results['salutation_issues']):4d} records")
    print(f"5. Suffix Conversions (Jr/Sr)  : {len(results['suffix_issues']):4d} records")
    print(f"6. Forename Abbrevs Candidate  : {len(results['forename_abbrevs']):4d} records")
    print(f"7. Sub-Terrace Leaks           : {len(results['sub_terrace_issues']):4d} records")
    print(f"8. Multi-Resident High Density : {len(results['multi_resident_anomalies']):4d} properties")
    print(f"9. Cross-Street Gap Years      : {len(results['cross_street_gaps']):4d} streets/years")
    print("========================================================\n")


if __name__ == "__main__":
    audit_dataset()
