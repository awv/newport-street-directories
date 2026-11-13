#!/usr/bin/env python3
"""Detect cross-year column-wrap intrusions: 1-year occupant on Street A sandwiched by consistent occupant Q, while occupant P is a multi-year resident on Street B."""

import csv
from collections import defaultdict, Counter

CSV_PATH = "data.csv"


def norm_person(r: dict) -> tuple[str, str]:
    sn = r["surname"].strip().lower()
    fn = r["forename"].strip().lower()
    return sn, fn


def main() -> None:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Index by (street, house_number) -> {year: [rows]}
    addr_years: dict[tuple[str, str], dict[int, list[tuple[int, dict]]]] = defaultdict(lambda: defaultdict(list))
    # Index by (surname_lower, forename_lower) -> Counter of street
    person_streets: dict[tuple[str, str], Counter] = defaultdict(Counter)
    # Also index by (surname_lower, forename_lower, street) -> list of (year, house_number)
    person_street_years: dict[tuple[str, str, str], list[tuple[int, str]]] = defaultdict(list)

    for idx, r in enumerate(rows):
        yr_s = r["year"].strip()
        if not yr_s.isdigit():
            continue
        yr = int(yr_s)
        st = r["street"].strip()
        hn = r["house_number"].strip()
        sn, fn = norm_person(r)
        if not st or not sn or len(sn) < 3 or sn in ("ditto", "void", "empty", "vacant"):
            continue
        if hn:
            addr_years[(st, hn)][yr].append((idx, r))
        if fn:
            person_streets[(sn, fn)][st] += 1
            person_street_years[(sn, fn, st)].append((yr, hn))

    intrusions = []

    for (st_a, hn), ymap in addr_years.items():
        years = sorted(ymap.keys())
        if len(years) < 3:
            continue
        for i in range(1, len(years) - 1):
            y_prev, y_cur, y_next = years[i - 1], years[i], years[i + 1]
            # Check if there is a consistent sandwich occupant Q in y_prev and y_next
            prev_surnames = {r["surname"].strip().lower() for _, r in ymap[y_prev] if r["surname"].strip()}
            next_surnames = {r["surname"].strip().lower() for _, r in ymap[y_next] if r["surname"].strip()}
            sandwich_q = prev_surnames & next_surnames
            if not sandwich_q:
                continue

            # Check each occupant P in y_cur
            for idx, r in ymap[y_cur]:
                sn, fn = norm_person(r)
                if not fn or sn in sandwich_q:
                    continue
                # Ensure P does NOT appear at (st_a, hn) in any other year
                other_yrs_here = [y for y in years if y != y_cur and any(norm_person(rr)[0] == sn for _, rr in ymap[y])]
                if other_yrs_here:
                    continue

                # Check if P is a multi-year resident on another street B
                st_counts = person_streets.get((sn, fn), Counter())
                other_streets = [(st_b, cnt) for st_b, cnt in st_counts.items() if st_b != st_a and cnt >= 2]
                if not other_streets:
                    continue
                other_streets.sort(key=lambda x: x[1], reverse=True)
                best_st_b, best_cnt = other_streets[0]
                b_details = sorted(person_street_years[(sn, fn, best_st_b)])
                # Check if y_cur is missing from best_st_b for this person
                b_years = {y for y, _ in b_details}
                if y_cur in b_years:
                    continue
                # Also check if P is sandwiched around y_cur on best_st_b
                has_before = any(y < y_cur for y in b_years)
                has_after = any(y > y_cur for y in b_years)
                confidence = "HIGH" if (has_before and has_after and best_cnt >= 3) else "MEDIUM"
                intrusions.append({
                    "confidence": confidence,
                    "idx": idx,
                    "year": y_cur,
                    "current_street": st_a,
                    "current_hn": hn,
                    "target_street": best_st_b,
                    "target_hn": Counter(h for _, h in b_details if h).most_common(1)[0][0] if any(h for _, h in b_details) else "",
                    "person": f"{r['forename']} {r['surname']}".strip(),
                    "trade": r["trade"].strip(),
                    "sandwich_q": sorted(sandwich_q)[0],
                    "target_years_count": best_cnt,
                })

    intrusions.sort(key=lambda x: (0 if x["confidence"] == "HIGH" else 1, -x["target_years_count"], x["year"]))
    high = [x for x in intrusions if x["confidence"] == "HIGH"]
    med = [x for x in intrusions if x["confidence"] == "MEDIUM"]
    print(f"Total column-wrap intrusion candidates: {len(intrusions)} (HIGH: {len(high)}, MEDIUM: {len(med)})")
    print("\n--- TOP 25 HIGH-CONFIDENCE CANDIDATES ---")
    for x in high[:25]:
        print(
            f"  {x['year']} | {x['person']} ({x['trade']}) | "
            f"WRONG: {x['current_street']} #{x['current_hn']} (sandwiched by {x['sandwich_q']}) -> "
            f"HOME: {x['target_street']} #{x['target_hn']} ({x['target_years_count']} yrs)"
        )


if __name__ == "__main__":
    main()
