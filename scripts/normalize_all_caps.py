#!/usr/bin/env python3
"""
Sweep `data.csv` (`year <= 1936`) for entries that are ALL CAPS (containing >= 3
consecutive uppercase letters, excluding standalone acronyms/Roman numerals)
and convert them to smart Title Case across `street`, `building_name`,
`surname`, `forename`, and `trade`.
"""
import argparse
import csv
import os
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "data.csv")

COLS = ["street", "building_name", "surname", "forename", "trade"]

PRESERVE_UPPER = {
    "G.W.R.", "G.W.R", "GWR",
    "G.P.O.", "G.P.O", "GPO",
    "H.M.C.", "H.M.C", "HMC",
    "H.M.", "H.M", "HMS", "H.M.S.",
    "L.D.S.", "R.C.S.", "M.B.", "B.S.", "M.D.", "F.R.C.S.",
    "S.B.", "M.O.", "P.O.", "J.P.", "M.P.", "R.N.", "R.N.R.", "R.A.",
    "Y.M.C.A.", "Y.W.C.A.", "YMCA", "YWCA",
    "N.S.P.C.C.", "R.S.P.C.A.", "U.D.C.", "R.D.C.",
    "L.N.E.R.", "L.M.S.", "B.B.C.",
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII",
}

LOWER_WORDS = {"of", "the", "and", "in", "at", "on", "for", "to", "by", "or", "with"}


def is_all_caps_entry(s: str) -> bool:
    if not s or not any(ch.isalpha() for ch in s):
        return False
    if s != s.upper():
        return False
    if not re.search(r"[A-Z]{3,}", s):
        return False
    if s.strip().upper().rstrip(".") in {x.rstrip(".") for x in PRESERVE_UPPER}:
        return False
    return True


def smart_title_word(w: str, is_first: bool) -> str:
    # Preserve punctuation wrappers like (ENG.) or quotes
    m = re.match(r"^([^A-Za-z0-9]*)(.*?)([^A-Za-z0-9]*)$", w)
    if not m:
        return w
    lead, core, trail = m.groups()
    if not core:
        return w

    core_u = core.upper()
    if core_u in PRESERVE_UPPER or (core_u + trail) in PRESERVE_UPPER:
        return lead + core_u + trail

    # Dotted initialisms like S.B., A., M.O., L.D.S.
    if re.fullmatch(r"(?:[A-Z]\.){1,}[A-Z]?", core_u):
        return lead + core_u + trail

    # Handle H.M.'S -> H.M.'s
    if core_u in {"H.M.'S", "H.M'S"}:
        return lead + "H.M.'s" + trail

    core_l = core.lower()
    if not is_first and core_l in LOWER_WORDS:
        return lead + core_l + trail

    # Hyphenated words: PEN-Y-LAN -> Pen-y-Lan
    if "-" in core_l:
        parts = core_l.split("-")
        out_parts = []
        for idx, p in enumerate(parts):
            if idx > 0 and p in {"y", "yr", "of", "the", "and", "in", "on", "at"}:
                out_parts.append(p)
            elif p.upper() in PRESERVE_UPPER:
                out_parts.append(p.upper())
            else:
                out_parts.append(p.capitalize())
        return lead + "-".join(out_parts) + trail

    # Apostrophe words: QUEEN'S -> Queen's, GLO'STER -> Glo'ster, O'LEARY -> O'Leary
    if "'" in core_l:
        parts = core_l.split("'")
        if len(parts) == 2:
            p0, p1 = parts
            if p0 in {"o", "d", "mc"}:
                return lead + p0.capitalize() + "'" + p1.capitalize() + trail
            if p1 in {"s", "t", "d", "ll", "re", "ve", "ster"}:
                return lead + p0.capitalize() + "'" + p1 + trail
            return lead + p0.capitalize() + "'" + p1.capitalize() + trail

    # Mc prefix: MCKINLEY -> McKinley
    if core_l.startswith("mc") and len(core_l) >= 4:
        return lead + "Mc" + core_l[2:].capitalize() + trail

    return lead + core_l.capitalize() + trail


def smart_title_case(s: str) -> str:
    tokens = s.split(" ")
    out = []
    for i, tok in enumerate(tokens):
        if not tok:
            out.append(tok)
        else:
            out.append(smart_title_word(tok, is_first=(i == 0)))
    return " ".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    stats = Counter()
    samples = {c: [] for c in COLS}

    for r in rows:
        if int(r["year"]) > 1936:
            continue
        for c in COLS:
            val = r[c].strip()
            if is_all_caps_entry(val):
                new_val = smart_title_case(val)
                if new_val != val:
                    r[c] = new_val
                    stats[c] += 1
                    if len(samples[c]) < 15:
                        samples[c].append((val, "->", new_val))

    print("Rows updated per column:", dict(stats), "Total:", sum(stats.values()))
    for c in COLS:
        if samples[c]:
            print(f"\n=== {c} samples ===")
            for o, _, n in samples[c]:
                print(f"  {o} -> {n}")

    if not args.dry_run:
        with open(DATA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print("\nSaved updated data.csv!")


if __name__ == "__main__":
    main()
