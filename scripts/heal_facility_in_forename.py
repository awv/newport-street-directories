#!/usr/bin/env python3
"""
Heal directory rows (year <= 1936) where a facility/trade description and/or
company name is trapped in `forename`:
1. Maddox Close (1882) specific Dos Works entries:
   - `Dos Works | Nail Factory J. J. Cordes and Co.` -> `surname='J. J. Cordes and Co.'`, `trade='Nail Factory'`
   - `Dos Works | Schools` -> `trade='Schools'`
2. Combined facility + company in `forename` with empty `surname`/`trade` (e.g.
   `Maybury & Co. stone yard`, `Riverside Coal Yard (Kemp & Co.)`,
   `Dibble, J. O. & Co., oil & grease stores`).
3. Clean facility in `forename` + company in `surname` with empty `trade`
   (e.g. `Pillgwenlly Iron Foundry | Chas. Jordan & Sons`, `Victoria garage | Knowlton Bros.`,
   `Bangor Wharf | Newport Builders' Supply Ltd.`, `Tillery wharf | Clapp & Co.`).
"""

import argparse
import csv
import os
import re
from collections import Counter

FAC_WORDS = (
    r"(?:Factory|Works|Stores|Yard|Office|Offices|Warehouse|Depot|Garage|"
    r"Stables|Bakery|Foundry|Brewery|Mill|Mills|Shop|Shed|Wharf|Bank|Hotel|Tavern|Inn)"
)
CO_WORDS = r"(?:&\s*Co\.?|and\s+Co\.?|Ltd\.?|Bros\.?|Sons)"


def title_facility(text: str) -> str:
    """Capitalize facility words cleanly while preserving existing caps/acronyms."""
    if not text:
        return text
    words = text.split()
    out = []
    minor = {"and", "of", "the", "for", "&"}
    for i, w in enumerate(words):
        if i > 0 and w.lower() in minor:
            out.append(w.lower())
        elif w.islower():
            out.append(w.capitalize())
        else:
            out.append(w)
    return " ".join(out)


def heal_row(row: dict) -> tuple[bool, str]:
    fn = (row["forename"] or "").strip()
    sn = (row["surname"] or "").strip()
    tr = (row["trade"] or "").strip()
    bn = (row["building_name"] or "").strip()

    if not fn:
        return False, ""

    # 1. Maddox Close (1882) Dos Works Schools
    if (
        row["year"] == "1882"
        and row["street"] == "Maddox Close"
        and fn == "Schools"
        and not sn
        and not tr
    ):
        row["forename"] = ""
        row["trade"] = "Schools"
        return True, "maddox_schools"

    # 2. Combined facility prefix + company in forename (no surname/trade)
    if not sn and not tr:
        if fn == "Nail Factory J. J. Cordes and Co.":
            row["forename"] = ""
            row["surname"] = "J. J. Cordes and Co."
            row["trade"] = "Nail Factory"
            return True, "combined_facility_company"
        if fn == "Riverside Coal Yard (Kemp & Co.)":
            row["forename"] = ""
            row["surname"] = "Kemp & Co."
            row["trade"] = "Riverside Coal Yard"
            return True, "combined_facility_company"
        if fn == "Maybury & Co. stone yard":
            row["forename"] = ""
            row["surname"] = "Maybury & Co."
            row["trade"] = "Stone Yard"
            return True, "combined_facility_company"
        if fn == "Dibble, J. O. & Co., oil & grease stores":
            row["forename"] = ""
            row["surname"] = "Dibble, J. O. & Co."
            row["trade"] = "Oil & Grease Stores"
            return True, "combined_facility_company"

    # 3. Clean facility in forename + company in surname (empty trade)
    if (
        sn
        and not tr
        and re.search(rf"\b{FAC_WORDS}\b", fn, re.I)
        and re.search(CO_WORDS, sn, re.I)
        and "—" not in fn
        and "--" not in fn
        and not re.search(r"Co\.?'s|Co's", fn, re.I)
        and not re.search(r"Co\.?'s|Co's", sn, re.I)
        and "—" not in sn
        and "--" not in sn
        and " - " not in fn
        and " -" not in fn
        and "- " not in fn
        and not re.search(r"wharf-", fn, re.I)
        and not fn.lower().endswith("slipway")
    ):
        # Skip compound "Star Mills -Smiths Newport Ltd." etc.
        if " -" in sn or "- " in sn or "—" in sn:
            return False, ""
        # Wharf names go cleanly into building_name if building_name is empty
        if re.search(r"\bwharf\b$", fn, re.I) and not bn:
            row["building_name"] = title_facility(fn)
            row["forename"] = ""
            return True, "wharf_to_building"
        row["trade"] = title_facility(fn)
        row["forename"] = ""
        return True, "facility_to_trade"

    return False, ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing data.csv")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data.csv")

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    stats = Counter()
    for row in rows:
        changed, reason = heal_row(row)
        if changed:
            stats[reason] += 1
            if args.dry_run:
                print(
                    f"[{reason}] {row['year']} {row['street']} | "
                    f"bn={row['building_name']!r} sn={row['surname']!r} "
                    f"fn={row['forename']!r} tr={row['trade']!r}"
                )

    print("Stats:", dict(stats))
    if not args.dry_run and sum(stats.values()) > 0:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {csv_path}")


if __name__ == "__main__":
    main()
