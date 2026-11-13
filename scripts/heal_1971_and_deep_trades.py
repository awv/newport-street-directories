#!/usr/bin/env python3
"""Phase B & C: 1971 structural/telephone/map repairs + deep trade anomaly sweep across all years."""
import csv
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

DATA_CSV = Path(__file__).resolve().parent.parent / "data.csv"
BACKUP_CSV = Path(__file__).resolve().parent.parent / "data.csv.bak_before_1971_and_deep_trades"

CROSS_STREET_1971_RE = re.compile(
    r"^(Road|Street|Lane|Avenue|Parade|Close|Drive|Crescent|Terrace|Place|Hill|Way)\.?(?:\s+Map\s+[A-Z0-9 ,]+)?\.?$"
)
TEL_SUFFIX_RE = re.compile(r"\.?\s*\b(?:Telephone|Tel\.?)(?:,\s*Newport)?\s+\d[\d/ ]*\.?$")
MAP_SUFFIX_RE = re.compile(r"\.?\s*\bMap\s+[A-Z]\s*\d+(?:,\s*[A-Z]\s*\d+)*\.?$")
ROOM_NUM_RE = re.compile(r"^(.+?),?\s*\((\d+(?:[-,&]\d+)*)\)$")
SINGLE_INIT_RE = re.compile(r"^[A-Z]\.$")
GIVEN_NAME_RE = re.compile(r"^[A-Z][a-z]+$")
ETC_RE = re.compile(r"^(?:&c\.?|etc\.?)$", re.IGNORECASE)


def main():
    with open(DATA_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    shutil.copy2(DATA_CSV, BACKUP_CSV)
    stats = Counter()

    for r in rows:
        y = r["year"]
        tr = r["trade"].strip()
        fn = r["forename"].strip()
        sn = r["surname"].strip()
        bn = r["building_name"].strip()
        hn = r["house_number"].strip()

        if not tr:
            continue

        # 1. 1971 cross-street waypoints in surname + trade
        if y == "1971" and not fn and sn and CROSS_STREET_1971_RE.match(tr):
            if not bn:
                r["building_name"] = f"{sn} {tr}".strip()
                r["surname"] = ""
            r["trade"] = ""
            stats["1971_cross_street_cleared"] += 1
            continue

        # 2. 1971 Telephone / Map suffixes on business trades
        if y == "1971":
            new_tr = TEL_SUFFIX_RE.sub("", tr).strip(" .,")
            new_tr = MAP_SUFFIX_RE.sub("", new_tr).strip(" .,")
            if new_tr != tr:
                r["trade"] = new_tr
                tr = new_tr
                stats["1971_tel_map_stripped"] += 1
                if not tr:
                    continue

        # 3. Trailing office room numbers in parentheses, e.g. "Architect (26)"
        if fn or sn or bn:
            m_rm = ROOM_NUM_RE.match(tr)
            if m_rm:
                r["trade"] = m_rm.group(1).strip()
                if not hn:
                    r["house_number"] = m_rm.group(2)
                stats["room_num_extracted"] += 1
                continue

        # 4. Single dotted initial in trade when surname is present
        if sn and SINGLE_INIT_RE.match(tr):
            if not fn:
                r["forename"] = tr
                r["trade"] = ""
                stats["init_moved_empty_fn"] += 1
                continue
            if fn == tr:
                r["trade"] = ""
                stats["init_dup_cleared"] += 1
                continue
            if (len(fn) <= 3 and fn.endswith(".")) or GIVEN_NAME_RE.match(fn):
                r["forename"] = f"{fn} {tr}"
                r["trade"] = ""
                stats["init_appended_fn"] += 1
                continue

        # 5. Standalone Etc. / &c.
        if ETC_RE.match(tr):
            r["trade"] = ""
            stats["etc_cleared"] += 1
            continue

    # 6. Unify any trade casing twins
    by_low = defaultdict(Counter)
    for r in rows:
        t = r["trade"].strip()
        if t:
            by_low[t.lower()][t] += 1
    canon = {low: cnts.most_common(1)[0][0] for low, cnts in by_low.items() if len(cnts) > 1}
    for r in rows:
        t = r["trade"].strip()
        if t and t.lower() in canon and t != canon[t.lower()]:
            r["trade"] = canon[t.lower()]
            stats["casing_unified"] += 1

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Phase B & C complete:")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print(f"Total adjustments: {sum(stats.values())}")


if __name__ == "__main__":
    main()
