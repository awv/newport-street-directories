#!/usr/bin/env python3
"""
Heal directory rows (year <= 1936) where the surname was trapped at the start
of `trade` as `Surname, lowercase_trade` (e.g. 1901 Marion Street:
`fn='James', sn='', tr='Redman, greengrocer'` or `fn='', sn='Thomas', tr='Cox, pilot'`
or `fn='H.', sn='Wm', tr='Pring, coal trimr'`).
"""

import argparse
import csv
import os
import re
from collections import Counter

COMMON_FIRST = {
    "john", "william", "james", "thomas", "george", "henry", "charles", "richard",
    "robert", "edward", "frederick", "fred", "albert", "albt", "alfred", "samuel",
    "arthur", "walter", "joseph", "david", "benjamin", "evan", "morgan", "harry",
    "frank", "herbert", "ernest", "daniel", "francis", "stephen", "philip", "edwin",
    "edmund", "lewis", "elizabeth", "mary", "sarah", "jane", "ann", "ellen",
    "harriet", "emily", "clara", "mrs", "miss", "rev", "wm", "thos", "geo",
    "chas", "jas", "hy", "jabez", "alex", "alexander", "andrew", "annie",
    "archibald", "augustus", "bertram", "catherine", "cecil", "chris",
    "christopher", "clarence", "clifford", "cornelius", "cyril", "dennis",
    "donald", "edgar", "edith", "eliza", "emmanuel", "enoch", "ern", "ethel",
    "eugene", "florence", "gertrude", "gilbert", "grace", "harold", "hector",
    "horace", "howard", "hugh", "isaac", "israel", "jacob", "jennie", "jesse",
    "job", "jonathan", "joshua", "kate", "kenneth", "laurence", "lawrence",
    "leonard", "lillian", "louis", "louisa", "luke", "margaret", "martha",
    "martin", "matthew", "maud", "michael", "moses", "nathan", "nathaniel",
    "nicholas", "noah", "oliver", "oscar", "owen", "patrick", "paul", "percy",
    "peter", "ralph", "raymond", "rebecca", "reginald", "reuben", "rhys",
    "roger", "roland", "rose", "rowland", "rupert", "sam", "samson", "sidney",
    "simon", "solomon", "stanley", "susan", "sydney", "theodore", "timothy",
    "tom", "victor", "vincent", "wallace", "wilfred", "willie", "zachariah",
    "ednund", "nicholas",
}

NON_SURNAME_TRADE_WORDS = {
    "agent", "agents", "alexandra", "baker", "barber", "builder", "builders",
    "butcher", "butchers", "carpenter", "chemist", "clerk", "coal", "contractor",
    "contractors", "continued", "draper", "drapers", "engineer", "engineers",
    "grocer", "grocers", "hotel", "inn", "ironmonger", "joiner", "labourer",
    "manager", "mason", "merchant", "merchants", "newsagent", "office",
    "offices", "painter", "plumber", "printer", "saddler", "solicitor",
    "stationer", "tailor", "timber", "watchmaker",
}


def is_initial_or_first(token: str) -> bool:
    if not token:
        return False
    t = token.strip()
    if re.fullmatch(r"(?:[A-Za-z]\.?){1,2}", t):
        return True
    parts = [p.rstrip(".").lower() for p in t.split()]
    return all(
        p in COMMON_FIRST or re.fullmatch(r"[a-z]", p)
        for p in parts
    )


def cap_first(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def heal_row(row: dict) -> tuple[bool, str]:
    y = int(row["year"]) if row["year"].isdigit() else 9999
    if y > 1936:
        return False, ""

    tr = (row["trade"] or "").strip()
    sn = (row["surname"] or "").strip()
    fn = (row["forename"] or "").strip()

    m = re.match(r"^([A-Z][A-Za-z'\-]+),\s+([a-z].*)$", tr)
    if not m:
        return False, ""

    word, rest = m.group(1), m.group(2).strip()
    if rest.lower().startswith("continued") or rest.lower() in {"contd", "cont."}:
        return False, ""

    # Skip if the leading word in trade is actually a forename (e.g. sn='Davies', tr='Henry, grocer')
    if word.lower() in COMMON_FIRST and sn and not is_initial_or_first(sn):
        return False, ""

    # Skip unambiguous trade words unless we clearly have a forename-only person
    # (note: 'Baker' / 'Barber' can be real surnames like William Barber, labourer)
    strict_non_surnames = NON_SURNAME_TRADE_WORDS - {"baker", "barber", "mason", "tailor"}
    if word.lower() in strict_non_surnames:
        return False, ""

    if not sn and fn and not re.search(r"&|\bLtd\b|\bCo\b|\bBros\b", fn, re.I):
        row["forename"] = fn
        row["surname"] = word
        row["trade"] = cap_first(rest)
        return True, "fn_only"

    if sn and not fn and is_initial_or_first(sn):
        row["forename"] = sn
        row["surname"] = word
        row["trade"] = cap_first(rest)
        return True, "sn_was_fn"

    if sn and fn:
        if sn.lower() in {"jr.", "jr", "sr.", "sr"} and is_initial_or_first(fn):
            row["forename"] = fn
            row["surname"] = f"{word} {sn}"
            row["trade"] = cap_first(rest)
            return True, "jr_sr_split"
        if is_initial_or_first(sn) and is_initial_or_first(fn):
            row["forename"] = f"{sn} {fn}"
            row["surname"] = word
            row["trade"] = cap_first(rest)
            return True, "sn_fn_combined"

    return False, ""


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
    marion_1901_shown = 0
    for row in rows:
        changed, reason = heal_row(row)
        if changed:
            stats[reason] += 1
            if args.dry_run and row["year"] == "1901" and row["street"] == "Marion Street" and marion_1901_shown < 12:
                marion_1901_shown += 1
                print(
                    f"[{reason}] 1901 Marion St No.{row['house_number']} | "
                    f"fn={row['forename']!r} sn={row['surname']!r} tr={row['trade']!r}"
                )

    print("Stats:", dict(stats), "Total:", sum(stats.values()))
    if not args.dry_run and sum(stats.values()) > 0:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {csv_path}")


if __name__ == "__main__":
    main()
