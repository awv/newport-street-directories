#!/usr/bin/env python3
"""
Phase 1: Macro Topological Diagnostic Scanner for the Newport Street Directory Project.
Scans all 319,838+ records in data.csv, master_streets.json, and raw_tsvs/*.tsv to
systematically detect and prove:
  1. Street Upper-Bound & Outlier Violations (with cross-year resident attribution)
  2. Year-over-Year Volumetric Plunges & Missing Columns
  3. False Streets (Chambers, Sub-Terraces, Ad Banners, Institutions, OCR Street Typos)
  4. Contiguous Column-Wrap & Missed-Header Bleeds (via cross-year resident matching)
  5. Field Contaminations & Layout Artifacts in Resident Rows
  6. Raw TSV Multi-Column Architecture Profiles
"""

import csv
import difflib
import glob
import json
import os
import re
import statistics
from collections import Counter, defaultdict

PROJECT_ROOT = "/Users/robgale/Documents/Newport Street Directory Project"
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
MASTER_STREETS_JSON = os.path.join(PROJECT_ROOT, "master_streets.json")
RAW_TSVS_DIR = os.path.join(PROJECT_ROOT, "raw_tsvs")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")

os.makedirs(REPORTS_DIR, exist_ok=True)


def parse_house_int(h_str):
    """Extract primary integer house number if valid (e.g. '12' -> 12, '12A' -> 12, '12-14' -> 12)."""
    if not h_str:
        return None
    h_str = h_str.strip()
    m = re.match(r"^(\d+)[A-Za-z]?(?:\s*[\-&/]\s*\d+[A-Za-z]?)?$", h_str)
    if m:
        val = int(m.group(1))
        if 0 < val < 2000:
            return val
    return None


PLACEHOLDER_SURNAMES = {
    "void", "vacant", "house", "null", "nan", "ull", "flat", "flats", "do", "ditto",
    "shop", "office", "offices", "stores", "works", "building", "buildings", "unbuilt",
    "rebuilding", "return", "here", "left", "right", "side", "cross", "over", "ltd",
    "sons", "bros", "co", "the", "and", "from", "to"
}


def normalize_surname(s):
    if not s:
        return ""
    norm = re.sub(r"[^a-z]", "", s.lower())
    if norm in PLACEHOLDER_SURNAMES or len(norm) < 3:
        return ""
    return norm


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    print("=" * 80)
    print("NEWPORT STREET DIRECTORY: MACRO TOPOLOGICAL DIAGNOSTIC SCANNER (PHASE 1)")
    print("=" * 80)

    # 1. Load Master Streets Registry
    verified_streets = {}
    unverified_streets = {}
    all_master_streets = {}
    if os.path.exists(MASTER_STREETS_JSON):
        with open(MASTER_STREETS_JSON, "r", encoding="utf-8") as f:
            mdata = json.load(f).get("streets", {})
            for slug, info in mdata.items():
                cname = info.get("canonical_name", "")
                status = info.get("audit_status") or info.get("audit", {}).get("status", "UNVERIFIED")
                all_master_streets[cname] = status
                if status in ("VERIFIED", "NAME_VERIFIED", "FULLY_ENRICHED"):
                    verified_streets[cname.lower()] = cname
                else:
                    unverified_streets[cname.lower()] = cname
    print(f"Loaded master_streets.json: {len(verified_streets)} verified, {len(unverified_streets)} unverified.")

    # 2. Load all records from data.csv preserving order per (year, row_idx)
    print(f"Reading {DATA_CSV}...")
    rows = []
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, r in enumerate(reader):
            r["_idx"] = idx
            r["_h_int"] = parse_house_int(r.get("house_number", ""))
            r["_norm_sur"] = normalize_surname(r.get("surname", ""))
            rows.append(r)

    total_rows = len(rows)
    all_years = sorted({r["year"] for r in rows if r["year"].isdigit()}, key=int)
    print(f"Loaded {total_rows:,} records across {len(all_years)} directory years: {', '.join(all_years)}")

    # 3. Build Cross-Year Indexes
    # (norm_surname, house_int) -> Counter of streets across years
    resident_house_streets = defaultdict(lambda: defaultdict(set))  # (sur, h_int) -> street -> set(years)
    # building_name_lower -> Counter of streets
    bldg_street_counts = defaultdict(Counter)
    # street -> year -> list of rows
    street_year_rows = defaultdict(lambda: defaultdict(list))
    # year -> list of rows in file order
    year_rows = defaultdict(list)

    for r in rows:
        st = r["street"].strip()
        yr = r["year"].strip()
        h_int = r["_h_int"]
        sur = r["_norm_sur"]
        bldg = r.get("building_name", "").strip()

        street_year_rows[st][yr].append(r)
        year_rows[yr].append(r)

        if sur and len(sur) >= 3 and h_int is not None and sur not in {"void", "vacant", "house"}:
            resident_house_streets[(sur, h_int)][st].add(yr)

        if bldg and len(bldg) >= 4 and not bldg.isdigit():
            bldg_street_counts[bldg.lower()][st] += 1

    # =========================================================================
    # INVARIANT 1: STREET UPPER-BOUND & OUTLIER VIOLATIONS
    # =========================================================================
    print("\n[1/6] Scanning for Street Upper-Bound & Outlier Violations...")
    outlier_findings = []
    street_max_profiles = {}

    for st, yr_map in street_year_rows.items():
        if len(yr_map) < 3:
            continue
        # Calculate max house number per year where at least 3 numbered houses exist
        annual_maxes = {}
        annual_p95s = {}
        for yr, rlist in yr_map.items():
            nums = sorted(r["_h_int"] for r in rlist if r["_h_int"] is not None)
            if len(nums) >= 3:
                annual_maxes[yr] = nums[-1]
                p95_idx = min(len(nums) - 1, int(len(nums) * 0.95))
                annual_p95s[yr] = nums[p95_idx]

        if len(annual_maxes) < 3:
            continue

        # Use median of annual maxes (or 75th percentile of annual maxes) as historical ceiling
        sorted_maxes = sorted(annual_maxes.values())
        median_max = statistics.median(sorted_maxes)
        # Also compute 80th percentile of annual maxes to allow for gradual street growth
        p80_max = sorted_maxes[min(len(sorted_maxes) - 1, int(len(sorted_maxes) * 0.80))]
        # A street's true topological ceiling is typically stable; if a single year jumps way above p80_max:
        ceiling = max(median_max * 1.25, p80_max * 1.15, median_max + 15)

        street_max_profiles[st] = {
            "median_max": int(median_max),
            "p80_max": int(p80_max),
            "ceiling": int(ceiling),
            "years_present": len(yr_map),
        }

        for yr, rlist in yr_map.items():
            over_rows = [r for r in rlist if r["_h_int"] is not None and r["_h_int"] > ceiling]
            if over_rows:
                over_nums = sorted(r["_h_int"] for r in over_rows)
                # Try to attribute where these outlier rows actually belong using cross-year resident lookup!
                source_votes = Counter()
                sample_matches = []
                for r in over_rows:
                    key = (r["_norm_sur"], r["_h_int"])
                    if key in resident_house_streets:
                        for other_st, other_yrs in resident_house_streets[key].items():
                            if other_st != st and (len(other_yrs) >= 1):
                                source_votes[other_st] += 1
                                if len(sample_matches) < 3:
                                    sample_matches.append(
                                        f"#{r['house_number']} {r['surname']} -> {other_st} ({','.join(sorted(other_yrs))})"
                                    )
                likely_source = source_votes.most_common(1)[0][0] if source_votes else "Unknown"
                likely_votes = source_votes.most_common(1)[0][1] if source_votes else 0

                outlier_findings.append({
                    "street": st,
                    "year": yr,
                    "median_max": int(median_max),
                    "p80_max": int(p80_max),
                    "year_max": over_nums[-1],
                    "outlier_count": len(over_rows),
                    "outlier_range": f"{over_nums[0]}-{over_nums[-1]}",
                    "likely_true_street": likely_source,
                    "matched_residents": likely_votes,
                    "evidence": "; ".join(sample_matches),
                })

    outlier_findings.sort(key=lambda x: (-x["outlier_count"], -(x["year_max"] - x["p80_max"])))
    outliers_path = os.path.join(REPORTS_DIR, "street_outliers.tsv")
    with open(outliers_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "street", "year", "median_max", "p80_max", "year_max",
                "outlier_count", "outlier_range", "likely_true_street",
                "matched_residents", "evidence"
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(outlier_findings)
    print(f"  -> Found {len(outlier_findings)} street-year upper-bound violations. Saved to {outliers_path}")

    # =========================================================================
    # INVARIANT 2: YEAR-OVER-YEAR VOLUMETRIC PLUNGES & TRUNCATIONS
    # =========================================================================
    print("\n[2/6] Scanning for Year-over-Year Volumetric Coverage Plunges...")
    coverage_gaps = []
    for st, yr_map in street_year_rows.items():
        if len(yr_map) < 6:
            continue
        counts_by_yr = {int(yr): len(rlist) for yr, rlist in yr_map.items() if yr.isdigit()}
        if not counts_by_yr:
            continue
        med_count = statistics.median(counts_by_yr.values())
        if med_count < 25:
            continue

        min_yr = min(counts_by_yr.keys())
        max_yr = max(counts_by_yr.keys())

        for y_str in all_years:
            y = int(y_str)
            if min_yr < y < max_yr:
                c = counts_by_yr.get(y, 0)
                # Compare with neighbors (immediate prev and next available years for this street)
                prev_years = [py for py in counts_by_yr if py < y and counts_by_yr[py] >= med_count * 0.5]
                next_years = [ny for ny in counts_by_yr if ny > y and counts_by_yr[ny] >= med_count * 0.5]
                if prev_years and next_years:
                    prev_y = max(prev_years)
                    next_y = min(next_years)
                    neighbor_avg = (counts_by_yr[prev_y] + counts_by_yr[next_y]) / 2.0
                    if c < min(med_count * 0.25, neighbor_avg * 0.25):
                        coverage_gaps.append({
                            "street": st,
                            "year": y_str,
                            "count_in_year": c,
                            "median_count": int(med_count),
                            "prev_year_count": f"{prev_y}:{counts_by_yr[prev_y]}",
                            "next_year_count": f"{next_y}:{counts_by_yr[next_y]}",
                            "drop_pct": round((1.0 - (c / neighbor_avg)) * 100, 1),
                        })

    coverage_gaps.sort(key=lambda x: (-x["median_count"], -x["drop_pct"]))
    gaps_path = os.path.join(REPORTS_DIR, "coverage_gaps.tsv")
    with open(gaps_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "street", "year", "count_in_year", "median_count",
                "prev_year_count", "next_year_count", "drop_pct"
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(coverage_gaps)
    print(f"  -> Found {len(coverage_gaps)} major street-year coverage plunges. Saved to {gaps_path}")

    # =========================================================================
    # INVARIANT 3: FALSE STREETS (CHAMBERS, SUB-TERRACES, ADS, OCR TYPOS)
    # =========================================================================
    print("\n[3/6] Classifying All 1,738 Streets for False Headers, Chambers, Sub-Terraces & Typos...")
    false_streets = []
    verified_names_list = list(verified_streets.values())
    verified_lower_set = set(verified_streets.keys())

    # Pre-index where every street appears in year_rows so we know the immediately preceding street in each year!
    preceding_street_counter = defaultdict(Counter)
    for yr, rlist in year_rows.items():
        prev_st = None
        current_run_st = None
        for r in rlist:
            st = r["street"].strip()
            if st != current_run_st:
                if current_run_st is not None:
                    prev_st = current_run_st
                current_run_st = st
                if prev_st and prev_st != st:
                    preceding_street_counter[st][prev_st] += 1

    for st, yr_map in street_year_rows.items():
        st_low = st.lower()
        is_verified = st_low in verified_lower_set
        total_st_rows = sum(len(v) for v in yr_map.values())
        yrs_list = sorted(yr_map.keys(), key=lambda x: int(x) if x.isdigit() else 0)

        category = None
        suggested_target = ""
        confidence = ""
        reason = ""

        # Check 1: Explicit Chambers / Arcade / Buildings / Wharf / Hall / House (excluding verified streets and standard road/street suffixes)
        if (
            not is_verified
            and re.search(r"\b(chambers|arcade|buildings|hall|chapel|church|school|schools|club|hotel|works|wharf|office|offices|hospital|station|post office|exchange|bank)\b", st_low)
            and not re.search(r"\b(road|street|terrace|lane|place|row|crescent|avenue|square|parade|gardens|drive|way|close|walk|grove|hill|cottages|villas)\b$", st_low)
        ):
            category = "BUILDING_OR_INSTITUTION_HEADER"
            # Can we find which parent street this building belongs to?
            parent_votes = Counter()
            if st_low in bldg_street_counts:
                for p_st, cnt in bldg_street_counts[st_low].items():
                    if p_st != st:
                        parent_votes[p_st] += cnt * 3
            # Also check resident matches
            for yr, rlist in yr_map.items():
                for r in rlist:
                    key = (r["_norm_sur"], r["_h_int"])
                    if key in resident_house_streets:
                        for other_st in resident_house_streets[key]:
                            if other_st != st:
                                parent_votes[other_st] += 2
            # Also check preceding street in file order
            for prev_st, cnt in preceding_street_counter[st].items():
                parent_votes[prev_st] += cnt

            if parent_votes:
                best_parent, score = parent_votes.most_common(1)[0]
                suggested_target = f"Parent Street: {best_parent} (move '{st}' to building_name)"
                confidence = "HIGH" if score >= 2 else "MEDIUM"
            else:
                suggested_target = "Inspect preceding street in raw TSV"
                confidence = "MEDIUM"
            reason = f"Matches non-street building/institution keyword; appears in {len(yrs_list)} yr(s)"

        # Check 2: Ad Slogan / Layout / Routing / Numbered fragment
        elif (
            re.search(r"(\d+|ltd|limited|co\.|sons|bros|estab|tel\.|from |to |here is|return|continued|side|directory|see )", st_low)
            or len(st_low) <= 4
        ) and not is_verified:
            category = "AD_OR_LAYOUT_ARTIFACT"
            prev_candidates = preceding_street_counter[st].most_common(1)
            if prev_candidates:
                suggested_target = f"Preceding Street: {prev_candidates[0][0]}"
            confidence = "HIGH"
            reason = "Contains digits, commercial company tokens, or layout routing words"

        # Check 3: Unverified street appearing in <= 3 years — check if OCR typo of a Verified Street OR a Sub-Terrace
        elif not is_verified and len(yrs_list) <= 3:
            # First check if it's a sub-terrace/villas/cottages that appears in `bldg_street_counts` on a major street
            if st_low in bldg_street_counts:
                other_sts = {k: v for k, v in bldg_street_counts[st_low].items() if k != st}
                if other_sts:
                    best_parent = max(other_sts.items(), key=lambda x: x[1])[0]
                    category = "SUB_TERRACE_OR_VILLAS_ON_PARENT_ROAD"
                    suggested_target = f"Parent Street: {best_parent} (set building_name='{st}')"
                    confidence = "HIGH"
                    reason = f"Appears {other_sts[best_parent]} times as a building_name on {best_parent} in other years"

            # Next check if its residents live on another street in adjacent years!
            if not category:
                res_votes = Counter()
                for yr, rlist in yr_map.items():
                    for r in rlist:
                        key = (r["_norm_sur"], r["_h_int"])
                        if key in resident_house_streets:
                            for other_st in resident_house_streets[key]:
                                if other_st != st:
                                    res_votes[other_st] += 1
                if res_votes:
                    best_other, match_cnt = res_votes.most_common(1)[0]
                    # Check string similarity between `st` and `best_other`
                    sim = difflib.SequenceMatcher(None, st_low, best_other.lower()).ratio()
                    if sim >= 0.72:
                        category = "OCR_STREET_TYPO"
                        suggested_target = best_other
                        confidence = "HIGH"
                        reason = f"String similarity {sim:.2f} + {match_cnt} resident matches with '{best_other}'"
                    elif match_cnt >= 3 or (total_st_rows > 0 and match_cnt / total_st_rows >= 0.35):
                        category = "MISATTRIBUTED_BLOCK_OR_SUBTERRACE"
                        suggested_target = best_other
                        confidence = "HIGH" if match_cnt >= 5 else "MEDIUM"
                        reason = f"{match_cnt}/{total_st_rows} residents match '{best_other}' at same house numbers in other years"

            # Next check pure string similarity against verified streets
            if not category:
                close_matches = difflib.get_close_matches(st, verified_names_list, n=1, cutoff=0.82)
                if close_matches and close_matches[0].lower() != st_low:
                    category = "OCR_STREET_TYPO"
                    suggested_target = close_matches[0]
                    confidence = "MEDIUM"
                    reason = f"Close spelling match to verified street '{close_matches[0]}'"
                elif re.search(r"\b(terrace|cottages|villas|court|place|row|buildings)\b", st_low) and total_st_rows <= 25:
                    prev_candidates = preceding_street_counter[st].most_common(1)
                    prev_str = prev_candidates[0][0] if prev_candidates else "Unknown"
                    category = "UNVERIFIED_MICRO_TERRACE_OR_COURT"
                    suggested_target = f"Followed '{prev_str}' in text"
                    confidence = "LOW"
                    reason = f"Only {total_st_rows} records across {len(yrs_list)} yr(s) ({','.join(yrs_list)})"

        if category:
            false_streets.append({
                "street": st,
                "audit_status": all_master_streets.get(st, "NOT_IN_MASTER"),
                "category": category,
                "years_count": len(yrs_list),
                "years": ",".join(yrs_list[:8]) + ("..." if len(yrs_list) > 8 else ""),
                "total_records": total_st_rows,
                "suggested_target": suggested_target,
                "confidence": confidence,
                "reason": reason,
            })

    false_streets.sort(key=lambda x: (x["category"], -x["total_records"]))
    false_streets_path = os.path.join(REPORTS_DIR, "false_streets.tsv")
    with open(false_streets_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "street", "audit_status", "category", "years_count", "years",
                "total_records", "suggested_target", "confidence", "reason"
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(false_streets)
    print(f"  -> Classified {len(false_streets)} false/unverified streets & sub-terraces. Saved to {false_streets_path}")

    # =========================================================================
    # INVARIANT 4: CONTIGUOUS COLUMN-WRAP & MISSED-HEADER BLEEDS
    # =========================================================================
    print("\n[4/6] Scanning All Street-Years for Contiguous Column-Wrap & Missed-Header Bleeds...")
    bleed_blocks = []

    for st, yr_map in street_year_rows.items():
        for yr, rlist in yr_map.items():
            if len(rlist) < 5:
                continue
            # For each row in rlist, determine if (norm_sur, h_int) strongly matches ANOTHER street
            # and does NOT appear on `st` in any other year!
            row_attributions = []
            for idx_in_st, r in enumerate(rlist):
                key = (r["_norm_sur"], r["_h_int"])
                matched_other = None
                if key[0] and key[1] is not None and key in resident_house_streets:
                    st_Map = resident_house_streets[key]
                    # If this resident+house_num appears on `st` in another year, it's legitimately on `st`!
                    other_yrs_on_st = st_Map.get(st, set()) - {yr}
                    if not other_yrs_on_st:
                        # Find other streets where this exact (surname, house_number) lived
                        candidates = [
                            (ost, len(oyrs))
                            for ost, oyrs in st_Map.items()
                            if ost != st and ost.lower() != st.lower()
                        ]
                        if candidates:
                            candidates.sort(key=lambda x: -x[1])
                            matched_other = candidates[0][0]
                row_attributions.append(matched_other)

            # Group contiguous slices where `matched_other` points to the same target street
            # (allowing small gaps of 1-2 unmatched rows inside a block of same-street matches)
            i = 0
            n = len(rlist)
            while i < n:
                target_st = row_attributions[i]
                if not target_st:
                    i += 1
                    continue
                j = i + 1
                match_count = 1
                gap = 0
                while j < n:
                    if row_attributions[j] == target_st:
                        match_count += 1
                        gap = 0
                        j += 1
                    elif gap < 2:
                        gap += 1
                        j += 1
                    else:
                        break
                # Trim trailing unmatched gap rows
                while j > i and row_attributions[j - 1] != target_st:
                    j -= 1

                span_len = j - i
                # If at least 3 residents in a tight contiguous block match the exact same OTHER street
                if match_count >= 3 and target_st != st:
                    slice_rows = rlist[i:j]
                    nums = [r["house_number"] for r in slice_rows if r["house_number"]]
                    num_range = f"{nums[0]}..{nums[-1]}" if nums else "unnumbered"
                    samples = [
                        f"#{r['house_number']} {r['surname']}"
                        for r in slice_rows
                        if row_attributions[i + slice_rows.index(r)] == target_st
                    ][:4]
                    bleed_blocks.append({
                        "year": yr,
                        "assigned_street": st,
                        "true_street": target_st,
                        "slice_start_idx": i + 1,
                        "slice_end_idx": j,
                        "total_street_rows": n,
                        "span_rows": span_len,
                        "confirmed_resident_matches": match_count,
                        "house_number_span": num_range,
                        "sample_matches": "; ".join(samples),
                    })
                i = max(i + 1, j)

    bleed_blocks.sort(key=lambda x: (-x["confirmed_resident_matches"], -x["span_rows"]))
    bleeds_path = os.path.join(REPORTS_DIR, "column_wrap_intrusions.tsv")
    with open(bleeds_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "year", "assigned_street", "true_street", "slice_start_idx",
                "slice_end_idx", "total_street_rows", "span_rows",
                "confirmed_resident_matches", "house_number_span", "sample_matches"
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(bleed_blocks)
    print(f"  -> Found {len(bleed_blocks)} confirmed contiguous cross-street bleed blocks. Saved to {bleeds_path}")

    # =========================================================================
    # INVARIANT 5: FIELD CONTAMINATIONS & ROW-LEVEL ANOMALIES
    # =========================================================================
    print("\n[5/6] Scanning All 319,838 Records for Field Contaminations...")
    contamination_counts = Counter()
    contamination_samples = []

    pure_trade_words = {
        "labourer", "carpenter", "butcher", "grocer", "tailor", "draper", "bootmaker",
        "shoemaker", "painter", "plumber", "mason", "plasterer", "blacksmith", "fitter",
        "machinist", "ironworker", "steelworker", "haulier", "trimmer", "coal trimmer",
        "seaman", "mariner", "solicitor", "accountant", "architect", "builder", "confectioner",
        "fruiterer", "greengrocer", "hairdresser", "tobacconist", "newsagent", "chemist",
        "stationer", "printer", "watchmaker", "jeweller", "pawnbroker", "dairyman",
    }

    for r in rows:
        yr = r["year"]
        st = r["street"]
        h = r["house_number"].strip()
        bldg = r["building_name"].strip()
        sur = r["surname"].strip()
        fore = r["forename"].strip()
        tr = r["trade"].strip()

        issue = None
        # 1. Empty surname & building_name
        if not sur and not bldg:
            issue = "EMPTY_SURNAME_AND_BUILDING"
        # 2. Layout header in surname/forename
        elif re.search(r"\b(street directory|left hand side|right hand side|here is|here are|\(return\)|first floor|second floor|third floor|top floor)\b", f"{sur} {fore} {tr}", re.I):
            issue = "LAYOUT_MARKER_IN_RECORD"
        # 3. Surname is a pure lowercase trade or unsplit 'Surname, trade'
        elif sur.lower() in pure_trade_words and not tr:
            issue = "PURE_TRADE_IN_SURNAME"
        elif "," in sur or ("," in fore and not tr):
            issue = "COMMA_UNSPLIT_IN_NAME"
        # 4. Forename contains embedded lowercase occupation (e.g. "William. labourer")
        elif re.search(r"\b(labourer|ironworker|trimmer|haulier|carpenter|fitter|seaman|mason|painter|plumber|bootmaker|tailor|grocer|butcher|clerk|engine driver)\b", fore, re.I):
            issue = "TRADE_BLEED_IN_FORENAME"
        # 5. House number range stuck in surname (e.g. '12-13' or '31-32')
        elif re.match(r"^\d+[A-Za-z]?\s*[\-&/]\s*\d+[A-Za-z]?$", sur) and not h:
            issue = "HOUSE_NUMBER_RANGE_IN_SURNAME"
        # 6. Digits inside surname
        elif re.search(r"\d", sur) and not re.search(r"(1st|2nd|3rd|\bco\b)", sur, re.I):
            issue = "DIGITS_IN_SURNAME"

        if issue:
            contamination_counts[issue] += 1
            if len(contamination_samples) < 5000:
                contamination_samples.append({
                    "issue_type": issue,
                    "year": yr,
                    "street": st,
                    "house_number": h,
                    "building_name": bldg,
                    "surname": sur,
                    "forename": fore,
                    "trade": tr,
                })

    contam_path = os.path.join(REPORTS_DIR, "field_contaminations.tsv")
    with open(contam_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "issue_type", "year", "street", "house_number",
                "building_name", "surname", "forename", "trade"
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(contamination_samples)
    print("  -> Field contamination summary across 319,838 records:")
    for k, v in contamination_counts.most_common():
        print(f"     * {k:<32}: {v:,} records")

    # =========================================================================
    # INVARIANT 6: RAW TSV STRUCTURAL ARCHITECTURE PROFILE
    # =========================================================================
    print("\n[6/6] Profiling Raw TSV Files (Multi-Column Signatures & Extraction Ratios)...")
    tsv_profiles = []
    for tsv_file in sorted(glob.glob(os.path.join(RAW_TSVS_DIR, "*.tsv"))):
        yr = os.path.splitext(os.path.basename(tsv_file))[0]
        if not yr.isdigit():
            continue
        with open(tsv_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        total_lines = len(lines)
        multi_num_lines = 0  # Lines with >= 2 distinct house number columns (2-col or 3-col horizontal merge)
        three_col_lines = 0
        tab_counts = Counter()
        for l in lines:
            parts = [p.strip() for p in l.rstrip("\n").split("\t")]
            tab_counts[len(parts)] += 1
            num_cols = sum(1 for p in parts if re.match(r"^\d+[A-Za-z]?$", p))
            if num_cols >= 2:
                multi_num_lines += 1
            if num_cols >= 3 or len(parts) >= 9:
                three_col_lines += 1

        parsed_count = len(year_rows.get(yr, []))
        ratio = round(parsed_count / total_lines, 2) if total_lines else 0
        layout_type = "1-Col / Pre-Split"
        if three_col_lines > total_lines * 0.05:
            layout_type = "3-Col Horizontal Flattened"
        elif multi_num_lines > total_lines * 0.08:
            layout_type = "2-Col Horizontal Flattened"

        tsv_profiles.append({
            "year": yr,
            "raw_lines": total_lines,
            "parsed_records": parsed_count,
            "records_per_raw_line": ratio,
            "multi_num_lines": multi_num_lines,
            "three_col_lines": three_col_lines,
            "detected_layout": layout_type,
        })

    tsv_prof_path = os.path.join(REPORTS_DIR, "raw_tsv_architecture.tsv")
    with open(tsv_prof_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "year", "raw_lines", "parsed_records", "records_per_raw_line",
                "multi_num_lines", "three_col_lines", "detected_layout"
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(tsv_profiles)
    print(f"  -> Profiled {len(tsv_profiles)} raw TSV volumes. Saved to {tsv_prof_path}")
    print("\nPhase 1 Macro Diagnostic Scan Complete!")


if __name__ == "__main__":
    main()
