#!/usr/bin/env python3
r"""
Heal 1936 directory parsing fragments across data.csv (and 1936 Stow Hill
multi-column splits):
1. `—Void` / `-Void` in surname (e.g. `Glengariff—void`, `St. Malo—Void`) ->
   move property name to `building_name`, clear `surname`, set `trade='Void'`.
2. Merge 1936 split continuation rows (`And Physician | Surgeon`,
   `merchants and | Porter`, `Secretary And | Agent`, `and Ship | Pilot`,
   `And | Decorator, Plumber`, `and | tobacconist Confectioner`, orphan `Ltd`,
   orphan `Manager`, orphan `Accountants`, `(Lond.) B.S`, `(Lond.) D P. H M.R.C.P`,
   `(Eng.) R.C.S`, `Dental | Surgeon`, `\d+ Tel`, `F.S.I`, `M.i.mar.e`) back into
   the preceding entry's `surname`/`trade` and clean medical degree tokens
   (`M. B`, `D C H. B`, `L D`) out of `forename`/`building_name`.
3. Clean `Mrs —` -> `Mrs` in `forename` across 1936.
4. Fix Stow Hill 1936 specific multi-column splits (No. 12, 13, 14, 26, 32,
   Central Chambers / No. 40 block).
r"""

import argparse
import csv
import os
import re
from collections import Counter

ORPHAN_FRAG_SURNAMES = {
    "ltd", "ltd.", "manager", "accountants", "f.s.i", "f.s.i.",
    "m.i.mar.e", "m.i.mar.e.", "b.s", "b.s.", "m.r.c.p", "m.r.c.p.",
    "r.c.s", "r.c.s.", "m.i.s.ch", "m.i.s.ch.", "dental",
    "and valuers auctioneers & estate agents",
    "proprietors colliery", "architects and chartered surveyors",
    "rennie", "secretary and",
}


def is_1936_fragment(row: dict) -> bool:
    if row["year"] != "1936":
        return False
    sn = (row["surname"] or "").strip()
    fn = (row["forename"] or "").strip()
    tr = (row["trade"] or "").strip()
    sn_low = sn.lower()

    if sn_low in ORPHAN_FRAG_SURNAMES:
        return True
    if fn.lower() == "and" and sn_low in {"physician", "phys", "ship"}:
        return True
    if sn_low == "and" and tr:
        return True
    if re.match(r"^\((?:Lond|Eng|Edin|Dub|Glas|Wales|Cantab|Oxon)\.?\)", fn, re.I):
        return True
    if re.fullmatch(r"\d+\s+Tel\.?", sn, re.I) and not fn and not tr:
        return True
    if fn.lower() == "merchants" and sn_low == "and" and tr.lower() == "porter":
        return True
    if fn.lower() == "john price" and sn_low == "secretary;" and tr.lower() == "steward":
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data.csv")

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    stats = Counter()
    out_rows = []
    i = 0
    while i < len(rows):
        r = rows[i]
        if r["year"] != "1936":
            out_rows.append(r)
            i += 1
            continue

        sn = (r["surname"] or "").strip()
        fn = (r["forename"] or "").strip()
        bn = (r["building_name"] or "").strip()
        tr = (r["trade"] or "").strip()
        hn = (r["house_number"] or "").strip()
        st = (r["street"] or "").strip()

        # 1. Clean 'Mrs —' -> 'Mrs'
        if fn == "Mrs —":
            r["forename"] = "Mrs"
            stats["mrs_dash"] += 1

        # 2. Clean '<Property>—Void' in surname
        m_void = re.match(r"^(.+?)[—\-]\s*void$", sn, re.I)
        if m_void:
            prop = m_void.group(1).strip()
            if not bn:
                r["building_name"] = prop
            r["surname"] = ""
            r["trade"] = "Void"
            stats["void_dash_surname"] += 1
            out_rows.append(r)
            i += 1
            continue

        # 3. Clean trades trapped in building_name (e.g. Fruit'Er on Stow Hill 14)
        if bn.lower() in {"fruit'er", "fruiterer"} and not tr:
            r["building_name"] = ""
            r["trade"] = "Fruiterer"
            stats["trade_in_bn"] += 1

        # 4. Clean trailing medical degree tokens trapped in forename
        m_deg = re.match(r"^(Dr\.?\s+.+?)\s+(M\.?\s*B\.?|D\.?\s*C\.?\s*H\.?\s*B\.?)$", fn)
        if m_deg:
            r["forename"] = m_deg.group(1).strip()
            deg = m_deg.group(2).strip()
            r["trade"] = f"{deg}, {tr}".strip(", ") if tr else deg
            stats["degree_in_fn"] += 1
        elif fn == "F. G. D C H. B" and sn == "Kerr":
            r["forename"] = "F. G."
            r["trade"] = "D.Ch., M.B."
            stats["degree_in_fn"] += 1
        elif bn == "S" and fn == "C. H L D" and sn == "Wilson":
            r["building_name"] = ""
            r["forename"] = "C. H."
            r["trade"] = "L.D.S."
            stats["degree_in_fn"] += 1

        # 5. Stow Hill specific fixes
        if st == "Stow Hill":
            if hn == "13" and not fn and sn == "Revelstoke" and not tr:
                r["building_name"] = "Revelstoke"
                r["surname"] = ""
                stats["stow_hill_specific"] += 1
            elif hn == "13" and bn == "Davies Sidney House" and fn == "Mrs Sarah" and sn == "Polden":
                r["building_name"] = ""
                r["forename"] = "Mrs Sarah"
                r["surname"] = "Polden"
                out_rows.append(r)
                out_rows.append({
                    "year": "1936", "street": "Stow Hill", "house_number": "13",
                    "building_name": "", "surname": "Davies", "forename": "Sidney H.",
                    "trade": "", "source_type": r["source_type"],
                })
                stats["stow_hill_specific"] += 1
                i += 1
                continue
            elif hn == "12" and sn == "Conservative Association offices" and tr == "Justice of the Peace":
                r["surname"] = "Conservative Association Offices"
                r["trade"] = "C. T. Clissitt, J.P."
                stats["stow_hill_specific"] += 1
            elif hn == "12" and fn == "Constitutional Club—W D. G. Wilson" and sn == "Tredegar":
                r["building_name"] = "Tredegar Constitutional Club"
                r["forename"] = "W. D. G."
                r["surname"] = "Wilson"
                r["trade"] = "Secretary"
                stats["stow_hill_specific"] += 1
            elif hn == "25" and not fn and sn == "Eversley" and not tr:
                r["building_name"] = "Eversley"
                r["surname"] = ""
                stats["stow_hill_specific"] += 1
            elif hn == "26" and fn == "Ivor 'J" and sn == "Morgan":
                r["forename"] = "Ivor J."
                stats["stow_hill_specific"] += 1
            elif hn == "26" and fn == "Melus" and sn == "Cartref" and not tr:
                r["building_name"] = "Melus Cartref"
                r["forename"] = ""
                r["surname"] = ""
                stats["stow_hill_specific"] += 1
            elif bn == "—I. F. L. Johns" and "Boy Scouts" in fn:
                r["building_name"] = ""
                r["forename"] = ""
                r["surname"] = "Newport Boy Scouts' Local Assoc."
                r["trade"] = "Hon. Secretary: I. F. L. Johns"
                stats["stow_hill_specific"] += 1
            elif not hn and not fn and sn == "Taylor And Till":
                r["surname"] = "Rennie, Taylor & Till"
                stats["stow_hill_specific"] += 1
            elif not hn and not fn and sn == "and Valuers Auctioneers & Estate Agents":
                if out_rows and out_rows[-1]["surname"] == "Rennie, Taylor & Till":
                    out_rows[-1]["trade"] = "Auctioneers, Valuers & Estate Agents"
                    stats["merged_fragment"] += 1
                    i += 1
                    continue

        # 6. Merge 1936-wide split fragment rows into the preceding row
        if out_rows and out_rows[-1]["year"] == "1936" and out_rows[-1]["street"] == st and is_1936_fragment(r):
            prev = out_rows[-1]
            sn_low = sn.lower()
            if sn_low in {"ltd", "ltd."}:
                if "ltd" not in prev["surname"].lower():
                    prev["surname"] = f"{prev['surname']} {sn}".strip()
                stats["merged_fragment"] += 1
                i += 1
                continue
            if sn_low == "rennie":
                # Drop standalone 'Rennie' before 'Taylor And Till'
                stats["merged_fragment"] += 1
                i += 1
                continue
            if fn.lower() == "and" and sn_low in {"physician", "phys"}:
                frag = f"Physician & {tr}".strip()
                prev["trade"] = f"{prev['trade']}, {frag}".strip(", ") if prev["trade"] else frag
                stats["merged_fragment"] += 1
                i += 1
                continue
            if fn.lower() == "and" and sn_low == "ship" and tr.lower() == "pilot":
                prev["trade"] = f"{prev['trade']} & Ship Pilot".strip() if prev["trade"] else "Ship Pilot"
                stats["merged_fragment"] += 1
                i += 1
                continue
            if sn_low == "and" and tr:
                if fn.lower() == "merchants":
                    prev["trade"] = f"{prev['trade']} & {tr} Merchants".strip()
                else:
                    prev["trade"] = f"{prev['trade']} & {tr}".strip() if prev["trade"] else tr
                stats["merged_fragment"] += 1
                i += 1
                continue
            if sn_low == "secretary and" and tr:
                frag = f"Secretary & {tr}"
                prev["trade"] = f"{prev['trade']}, {frag}".strip(", ") if prev["trade"] else frag
                stats["merged_fragment"] += 1
                i += 1
                continue
            if fn.lower() == "john price" and sn_low == "secretary;" and tr.lower() == "steward":
                prev["trade"] = f"{prev['trade']}; John Price, Steward".strip("; ")
                stats["merged_fragment"] += 1
                i += 1
                continue
            # General trailing qualification/trade/tel fragment
            parts = [p for p in (fn, sn, tr) if p]
            frag = " ".join(parts)
            prev["trade"] = f"{prev['trade']}, {frag}".strip(", ") if prev["trade"] else frag
            stats["merged_fragment"] += 1
            i += 1
            continue

        out_rows.append(r)
        i += 1

    print("Dry-run:" if args.dry_run else "Applied:", dict(stats), "Total actions:", sum(stats.values()))
    if args.dry_run:
        print("\nSample Stow Hill 1936 rows after fix:")
        for r in out_rows:
            if r["year"] == "1936" and r["street"] == "Stow Hill" and r["house_number"] in {"10", "12", "13", "14", "18", "24", "25", "26", "29", "40", "56", ""}:
                if any(k in (r["surname"] + r["forename"] + r["building_name"] + r["trade"]) for k in ["Sprod", "Polden", "Davies", "Revelstoke", "Bryant", "Kerr", "Morgan", "Forsyth", "Wilson", "Smith H. A.", "Conservative", "Tredegar", "Pullin", "Glengariff", "Rennie", "Boy Scouts", "Midland", "Vaughan"]):
                    print(f"  hn={r['house_number']!r} bn={r['building_name']!r} fn={r['forename']!r} sn={r['surname']!r} tr={r['trade']!r}")
    else:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Updated {csv_path} ({len(rows)} -> {len(out_rows)} rows)")


if __name__ == "__main__":
    main()
