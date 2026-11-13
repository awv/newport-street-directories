#!/usr/bin/env python3
"""
Confidently detect and extract second/third residents trapped inside `trade`
into separate resident rows at the same (year, street, house_number, building_name),
swapping `Surname Forename` -> `forename`, `surname`, and normalize Sergeant Major
abbreviations.
"""
import argparse
import csv
import os
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "data.csv")

NON_NAME_WORDS = {
    "Dock", "Supply", "Girls", "News", "Chapel", "Ltd", "Co", "Sons", "Bros",
    "Mon", "Wales", "South", "East", "West", "North", "Road", "Street",
    "Square", "Place", "House", "Court", "Works", "Stores", "Office",
    "Branch", "Club", "School", "Schools", "Yard", "Bank", "Hotel", "Inn",
    "Tavern", "Wharf", "Post", "Union", "Soc", "Assn", "Inst", "Saloon",
    "Labourer", "Trimmer", "Docker", "Driver", "Clerk", "Manager", "Agent",
    "Vacant", "Sites", "Back", "Entrance", "Room", "Rooms", "Proprietor",
    "Sec", "G.W.R", "R.A", "V.A", "M.M", "F.F.I", "L.D.S", "R.C.S", "ENG",
    "Corporation", "Electricity", "Fish", "Ruperra", "Central", "Hall",
    "Forward", "Movement", "Telegraph", "Fire", "Station", "Newport", "The",
    "Redland", "Castle",
}

FORENAME_EXPANSIONS = {
    "Wm.": "William", "Wm": "William",
    "Geo.": "George", "Geo": "George",
    "Thos.": "Thomas", "Thos": "Thomas",
    "Chas.": "Charles", "Chas": "Charles",
    "Jno.": "John", "Jno": "John",
    "Jas.": "James", "Jas": "James",
    "Jos.": "Joseph", "Jos": "Joseph",
    "Robt.": "Robert", "Robt": "Robert",
    "Richd.": "Richard", "Richd": "Richard",
    "Edwd.": "Edward", "Edwd": "Edward",
    "Hy.": "Henry", "Hy": "Henry",
    "Albt.": "Albert", "Albt": "Albert",
    "Herbt.": "Herbert", "Herbt": "Herbert",
    "Reg.": "Reginald",
    "Stan.": "Stanley",
    "Fredk.": "Frederick", "Fredk": "Frederick",
    "Fred.": "Frederick",
    "Alex.": "Alexander",
    "Benj.": "Benjamin",
    "Danl.": "Daniel",
    "Saml.": "Samuel",
    "Nathl.": "Nathaniel",
}

TRADE_EXPANSIONS = {
    "plmr": "Plumber",
    "coaltrimmer": "Coal Trimmer",
    "drgtsmn": "Draughtsman",
    "eng dr": "Engine Driver",
    "com agent": "Commercial Agent",
    "belt repr": "Belt Repairer",
}


def expand_forename(fn: str) -> str:
    tokens = fn.split()
    out = []
    for tok in tokens:
        if tok in FORENAME_EXPANSIONS:
            out.append(FORENAME_EXPANSIONS[tok])
        elif tok + "." in FORENAME_EXPANSIONS and not tok.endswith("."):
            out.append(FORENAME_EXPANSIONS[tok + "."])
        else:
            out.append(tok)
    return " ".join(out)


def normalize_trade(t: str) -> str:
    t = t.strip(" ,;")
    if not t:
        return ""
    tl = t.lower()
    if tl in TRADE_EXPANSIONS:
        return TRADE_EXPANSIONS[tl]
    # Sergeant Major variants
    t = re.sub(r"\b(?:regt\.?\-?\s*|reg\.?\s+)sergeant\s+major\b", "Regimental Sergeant Major", t, flags=re.I)
    t = re.sub(r"\b(?:sergt|sgt)\.?\s*\-?\s*maj(?:or)?\.?", "Sergeant Major", t, flags=re.I)
    # Title-case if entirely lowercase
    if t == t.lower():
        t = " ".join(w.capitalize() for w in t.split())
    return t


def build_vocab(rows):
    surnames = set()
    forenames = set()
    trade_counts = Counter()

    for r in rows:
        if int(r["year"]) > 1936:
            continue
        s = r["surname"].strip()
        fn = r["forename"].strip()
        t = r["trade"].strip()
        if s and " " not in s and s.isalpha() and len(s) > 2 and s[0].isupper() and not s.isupper():
            surnames.add(s)
        if fn:
            for tok in fn.split():
                tc = tok.rstrip(".")
                if len(tc) >= 3 and tc.isalpha() and tc[0].isupper() and not tc.isupper():
                    forenames.add(tc)
        if t and len(t) <= 30 and not any(c.isdigit() for c in t) and " / " not in t:
            trade_counts[t.lower()] += 1

    forenames.update({
        "Wm", "Geo", "Thos", "Chas", "Jno", "Jas", "Jos", "Robt", "Richd",
        "Edwd", "Hy", "Albt", "Herbt", "Reg", "Stan", "Mrs", "Miss", "Rev",
        "Dr", "Nurse",
    })
    forenames -= NON_NAME_WORDS
    surnames -= NON_NAME_WORDS

    surnames_lower = {s.lower() for s in surnames}
    forenames_lower = {f.lower() for f in forenames}
    known_trades = {
        t for t, c in trade_counts.items()
        if c >= 5 and t not in surnames_lower and t not in forenames_lower
        and t not in {"the", "mrs.", "mr.", "miss", "newport", "forward movement"}
    }
    return surnames, forenames, known_trades


def is_valid_forename(fn_str: str, forenames: set) -> bool:
    toks = fn_str.split()
    if not toks:
        return False
    for tok in toks:
        if not tok[0].isupper() or (len(tok) > 2 and tok.isupper()):
            return False
        tc = tok.rstrip(".")
        if tc in NON_NAME_WORDS or tok in NON_NAME_WORDS:
            return False
        if re.match(r"^[A-Z]\.?$", tok):
            continue
        if tc in forenames:
            continue
        return False
    return True


def parse_surname_forename_trade(segment: str, surnames: set, forenames: set):
    """
    Parse `<Surname> <Forename(s)/Title/Initial> [<trade>]` from a slash segment.
    Returns (forename, surname, trade2) or None.
    """
    toks = segment.strip().split()
    if len(toks) < 2:
        return None
    sur = toks[0]
    if sur not in surnames or not sur[0].isupper():
        return None

    # Greedily consume valid forename/title/initial tokens (1 to 3 tokens)
    fn_toks = []
    idx = 1
    while idx < len(toks) and len(fn_toks) < 3:
        cand = toks[idx]
        if is_valid_forename(cand, forenames):
            fn_toks.append(cand)
            idx += 1
        else:
            break

    if not fn_toks:
        return None

    fn = expand_forename(" ".join(fn_toks))
    tr2 = normalize_trade(" ".join(toks[idx:]))
    return (fn, sur, tr2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    surnames, forenames, known_trades = build_vocab(rows)

    new_rows = []
    stats = Counter()
    samples = []

    for r in rows:
        year = int(r["year"])
        if year > 1936:
            new_rows.append(r)
            continue

        orig_t = r["trade"].strip()
        if not orig_t:
            new_rows.append(r)
            continue

        extracted_residents = []
        updated_trade = orig_t

        # Rule A: Slash-separated multi-resident lines (e.g. "Labourer / Bullock George labourer")
        if " / " in orig_t:
            parts = [p.strip() for p in orig_t.split(" / ")]
            kept_parts = [parts[0]]
            for p in parts[1:]:
                parsed = parse_surname_forename_trade(p, surnames, forenames)
                if parsed:
                    extracted_residents.append(parsed)
                    stats["rule_a_slash"] += 1
                else:
                    kept_parts.append(p)
            if extracted_residents:
                updated_trade = " / ".join(kept_parts)

        # Rule B: `<prefix> <Surname> <Forename/Initial.>` at end (e.g. "Sergt.-Maj. Harding E.")
        elif re.match(r"^(.+?)[,\s;]+([A-Z][a-z]{2,})\s+((?:[A-Z][a-z]+\s+)?[A-Z]\.)$", orig_t):
            m = re.match(r"^(.+?)[,\s;]+([A-Z][a-z]{2,})\s+((?:[A-Z][a-z]+\s+)?[A-Z]\.)$", orig_t)
            pref, sur, fn = m.group(1).strip(" ,;"), m.group(2), m.group(3)
            if (
                sur in surnames
                and is_valid_forename(fn, forenames)
                and pref.lower() not in ("mrs", "mrs.", "miss", "mr", "mr.", "rev", "dr", "the", "justice of the peace")
                and pref.rstrip(",.") not in surnames
                and not pref.endswith(("Mrs.", "Miss", "Mr."))
                and (
                    pref.lower() in known_trades
                    or "," in orig_t
                    or ";" in orig_t
                    or re.search(r"sergt|sgt", pref, re.I)
                )
            ):
                updated_trade = pref
                extracted_residents.append((expand_forename(fn), sur, ""))
                stats["rule_b_trailing_initial"] += 1

        # Rule C: `<known_trade> <Surname> <Forename> <lowercase_trade2>`
        if not extracted_residents and " / " not in updated_trade:
            m3 = re.match(
                r"^([A-Z][a-zA-Z\.\-\s]{2,25}?)\s+([A-Z][a-z]{2,})\s+((?:Mrs\.|Miss|Mr\.|Rev\.|Nurse|[A-Z][a-z]+\.?|[A-Z]\.)(?:\s+[A-Z]\.?)?)\s+([a-z][a-z\s\.\-\/]{2,})$",
                updated_trade,
            )
            if m3:
                t1, sur, fn, t2 = m3.groups()
                if (
                    t1.lower() in known_trades
                    and sur in surnames
                    and is_valid_forename(fn, forenames)
                ):
                    updated_trade = t1
                    extracted_residents.append((expand_forename(fn), sur, normalize_trade(t2)))
                    stats["rule_c_embedded_trade"] += 1

        # Normalize Sergeant Major and trade casing on primary row
        final_t = normalize_trade(updated_trade)
        if final_t != orig_t:
            stats["primary_trade_updated"] += 1
            if "Sergeant Major" in final_t and "Sergeant Major" not in orig_t:
                stats["sergeant_major_normalized"] += 1
            r["trade"] = final_t

        new_rows.append(r)

        for fn, sur, tr2 in extracted_residents:
            new_row = {
                "year": r["year"],
                "street": r["street"],
                "house_number": r["house_number"],
                "building_name": r["building_name"],
                "surname": sur,
                "forename": fn,
                "trade": tr2,
                "source_type": r["source_type"],
            }
            new_rows.append(new_row)
            samples.append((r["year"], r["street"], r["house_number"], orig_t, "=>", r["trade"], "+", f"{fn} {sur} ({tr2})"))

    print("Stats:", dict(stats))
    print(f"Total rows: {len(rows)} -> {len(new_rows)} (+{len(new_rows) - len(rows)})")
    print("\nExtracted resident samples:")
    for s in samples:
        print(" ", s)

    if not args.dry_run:
        with open(DATA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(new_rows)
        print("\nSaved updated data.csv!")


if __name__ == "__main__":
    main()
