#!/usr/bin/env python3
"""
Detect records in data.csv (all years) that likely "jumped ship" to another
street due to street-header OCR misreads, casing variants, or missed street
boundaries.

Signals:
1. Sandwiched Identity Match: (house_number, forename, surname) or
   (building_name, surname) appears in `target_street` in >= 3 years both
   before and after `year`, but appears under `current_street` in `year`.
2. Cluster Context: groups hits by (year, current_street, target_street) and
   records:
   - total_in_current_yr: total rows in (year, current_street)
   - target_count_in_yr: total rows already in (year, target_street)
   - contiguous_span: whether the matched rows form a contiguous block in
     data.csv row order
   - tier: Tier1_WholeStreet_OCR_Or_Casing / Tier2_Boundary_Block / Tier3_Isolated

Outputs:
  reports/street_jumps_audit.tsv
"""

import csv
import os
from collections import Counter, defaultdict

COMMON_SURNAMES = {
    "void", "vacant", "smith", "jones", "williams", "davies", "evans",
    "thomas", "lewis", "morgan", "roberts", "james", "phillips", "hughes",
    "edwards", "jenkins", "griffiths", "brown", "baker",
}


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data.csv")
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    out_path = os.path.join(reports_dir, "street_jumps_audit.tsv")

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    yr_st_counts = Counter((r["year"].strip(), r["street"].strip()) for r in rows)
    sig_streets = defaultdict(lambda: defaultdict(set))

    for idx, r in enumerate(rows):
        st = r["street"].strip()
        yr = r["year"].strip()
        hn = r["house_number"].strip()
        sn = r["surname"].strip().lower()
        fn = r["forename"].strip().lower()
        bn = r["building_name"].strip().lower()
        if not yr.isdigit() or not sn or len(sn) < 4 or sn in COMMON_SURNAMES:
            continue
        if bn and len(bn) >= 5:
            sig_streets[("bn+sn", bn, sn)][st].add(yr)
        if hn and fn and len(fn) >= 3:
            sig_streets[("hn+fn+sn", hn, fn, sn)][st].add(yr)

    # Map each (year, current_street, target_street) -> list of (row_idx, hn, bn, fn, sn)
    clusters = defaultdict(list)
    seen_row_target = set()

    for idx, r in enumerate(rows):
        st = r["street"].strip()
        yr = r["year"].strip()
        hn = r["house_number"].strip()
        sn = r["surname"].strip().lower()
        fn = r["forename"].strip().lower()
        bn = r["building_name"].strip().lower()
        if not yr.isdigit() or not sn or len(sn) < 4 or sn in COMMON_SURNAMES:
            continue

        sigs = []
        if bn and len(bn) >= 5:
            sigs.append(("bn+sn", bn, sn))
        if hn and fn and len(fn) >= 3:
            sigs.append(("hn+fn+sn", hn, fn, sn))

        for sig in sigs:
            st_map = sig_streets[sig]
            if len(st_map) < 2:
                continue
            ranked = sorted(st_map.items(), key=lambda x: -len(x[1]))
            main_st, main_yrs = ranked[0]
            if main_st == st:
                continue
            cur_yrs = st_map.get(st, set())
            if len(main_yrs) >= 3 and len(cur_yrs) == 1:
                y_int = int(yr)
                has_before = any(int(y) < y_int for y in main_yrs)
                has_after = any(int(y) > y_int for y in main_yrs)
                if has_before and has_after:
                    key = (idx, main_st)
                    if key not in seen_row_target:
                        seen_row_target.add(key)
                        clusters[(yr, st, main_st)].append(
                            (idx, hn, r["building_name"].strip(), r["forename"].strip(), r["surname"].strip())
                        )

    summary_rows = []
    for (yr, cur_st, tgt_st), hits in clusters.items():
        n_hits = len(hits)
        cur_total = yr_st_counts[(yr, cur_st)]
        tgt_total = yr_st_counts[(yr, tgt_st)]
        indices = sorted(h[0] for h in hits)
        span = indices[-1] - indices[0] + 1 if indices else 0
        density = n_hits / span if span > 0 else 0

        if cur_st.lower() == tgt_st.lower():
            tier = "Tier1_Casing_Mismatch"
        elif tgt_total == 0 and n_hits >= 5 and n_hits >= cur_total * 0.4:
            tier = "Tier1_WholeStreet_OCR_Or_Missed"
        elif n_hits >= 3 and (tgt_total == 0 or density >= 0.2):
            tier = "Tier2_Boundary_Block"
        else:
            tier = "Tier3_Isolated"

        sample = "; ".join(
            f"No.{h[1]} {h[3]} {h[4]}".strip() for h in hits[:3]
        )
        summary_rows.append({
            "tier": tier,
            "year": yr,
            "current_street": cur_st,
            "target_street": tgt_st,
            "matched_rows": n_hits,
            "current_street_total_in_year": cur_total,
            "target_street_total_in_year": tgt_total,
            "row_span": f"{indices[0]}-{indices[-1]}" if indices else "",
            "sample_records": sample,
        })

    tier_order = {
        "Tier1_Casing_Mismatch": 0,
        "Tier1_WholeStreet_OCR_Or_Missed": 1,
        "Tier2_Boundary_Block": 2,
        "Tier3_Isolated": 3,
    }
    summary_rows.sort(key=lambda x: (tier_order.get(x["tier"], 9), -x["matched_rows"], x["year"]))

    fieldnames = [
        "tier", "year", "current_street", "target_street", "matched_rows",
        "current_street_total_in_year", "target_street_total_in_year",
        "row_span", "sample_records",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        w.writerows(summary_rows)

    tier_counts = Counter(r["tier"] for r in summary_rows)
    tier_row_sums = Counter()
    for r in summary_rows:
        tier_row_sums[r["tier"]] += r["matched_rows"]

    print(f"Wrote {len(summary_rows)} clusters to {out_path}")
    for t in sorted(tier_counts, key=lambda k: tier_order.get(k, 9)):
        print(f"  {t}: {tier_counts[t]} clusters ({tier_row_sums[t]} matched rows)")

    print("\nTop Tier 1 & Tier 2 clusters:")
    for r in [x for x in summary_rows if x["tier"] != "Tier3_Isolated"][:35]:
        print(
            f"  [{r['tier']}] {r['year']} {r['current_street']} ({r['current_street_total_in_year']} rows) "
            f"-> {r['target_street']} (currently {r['target_street_total_in_year']} rows) | "
            f"matched={r['matched_rows']}"
        )


if __name__ == "__main__":
    main()
