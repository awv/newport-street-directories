#!/usr/bin/env python3
"""
Heal house/building names trapped in `trade` (`year <= 1936`), learned from
Lawn Terrace (1910/1925) and generalized across the dataset:
1. Same-(street, house_number) cross-year building_name match:
   When `building_name` is empty and `trade` matches (after normalizing Ho/H/Villa/V/Cot)
   a `building_name` recorded at the same `(street, house_number)` in another year
   (and is not a known trade or personal name), move it to `building_name` and clear `trade`.
2. Trailing ` H` / ` h` / ` H.` / ` V` / ` V.` house/villa abbreviations in `trade`:
   - Commercial `Boarding H`, `Bordng H`, `Coffee H`, `Refreshment H` -> expand to `... House` in `trade`.
   - Residential `<Name> H` / `<Name> h` (when not a known trade or personal name) -> move to
     `building_name` as `<Name> House` and clear `trade`.
"""
import argparse
import csv
import os
import re
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "data.csv")

NOT_A_HOUSE_RE = re.compile(
    r"\b(?:lodging|eating|boarding|bordng|bdg|coffee|cocoa|public|beer|ale|"
    r"refreshment|dining|temperance|station|police|customs|workhouse|poor\s*law|"
    r"warehouse|wareho|wharf|wf|works|wks|yard|yd|depot|office|offices|shop|"
    r"stores|store|factory|mill|mills|foundry|brewery|bakery|dairy|laundry|"
    r"garage|club|institute|school|college|hospital|infirmary|dispensary|"
    r"church|chapel|mission|theatre|cinema|bank|exchange|repository|"
    r"mason|masons|builder|builders|carpenter|smith|engineer|driver|dvr|"
    r"clerk|agent|manager|managers|collector|dealer|merchant|trimmer|shipper|"
    r"maker|mkr|worker|labourer|junr|senr|jr|sr|void|vacant|apartments|"
    r"lodgings|private|retired|widow|spinster|gentleman|tailor|draper|grocer|"
    r"butcher|baker|photographer|chemist|druggist|plumber|painter|plasterer|"
    r"fitter|turner|boilermaker|ironmonger|tobacconist|confectioner|"
    r"newsagent|fruiterer|greengrocer|fishmonger|hairdresser|watchmaker|"
    r"bootmaker|shoemaker|saddler|printer|solicitor|accountant|surgeon|dentist|"
    r"architect|surveyor|auctioneer|coachbuilder|wheelwright|blacksmith|"
    r"shipwright|mariner|seaman|haulier|carter|carman|porter|guard|signalman|"
    r"platelayer|stoker|fireman|ostler|groom|gardener|coachman|domestic|"
    r"nurse|teacher|schoolmistress|schoolmaster|dressmaker|milliner|charwoman|"
    r"caretaker|watchman|policeman|constable|postman|inspector|foreman)\b",
    re.I,
)


def norm_bldg_key(b: str) -> str:
    b = b.strip().lower().rstrip(".")
    b = re.sub(r"\b(ho|h|house|villa|villas|vil|v|cot|cottage|cottages|lodge|l)\b", "", b)
    return re.sub(r"[^a-z0-9]+", "", b)


def expand_building_display(b: str) -> str:
    b = b.strip().rstrip(".")
    b = re.sub(r"\b(?:ho|h)$", "House", b, flags=re.I)
    b = re.sub(r"\b(?:vil|v)$", "Villa", b, flags=re.I)
    b = re.sub(r"\bcot$", "Cottage", b, flags=re.I)
    b = re.sub(r"\bl$", "Lodge", b, flags=re.I)
    words = b.split()
    out = []
    for w in words:
        if w.lower() in {"of", "the", "and", "&", "on", "in", "y", "yr"} and out:
            out.append(w.lower())
        elif "-" in w:
            out.append("-".join(p.capitalize() for p in w.split("-")))
        else:
            out.append(w[0].upper() + w[1:] if len(w) > 1 else w.upper())
    return " ".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    bldg_by_addr = defaultdict(list)
    trade_counts = Counter()
    personal_names = set()

    for r in rows:
        if int(r["year"]) > 1936:
            continue
        t = r["trade"].strip()
        if t:
            trade_counts[t.lower()] += 1
        fn = r["forename"].strip().lower()
        sur = r["surname"].strip().lower()
        if fn and fn.isalpha() and len(fn) >= 3:
            personal_names.add(fn)
        if sur and sur.isalpha() and len(sur) >= 3:
            personal_names.add(sur)

        b = r["building_name"].strip()
        hn = r["house_number"].strip()
        st = r["street"].strip().lower()
        if b and hn and not NOT_A_HOUSE_RE.search(b):
            nb = norm_bldg_key(b)
            if len(nb) >= 4:
                bldg_by_addr[(st, hn)].append((nb, b))

    stats = Counter()
    samples = []

    for r in rows:
        if int(r["year"]) > 1936:
            continue
        if r["building_name"].strip():
            continue
        t = r["trade"].strip()
        if not t:
            continue

        # Normalize commercial "<X> H" first
        if re.match(r"^(?:boarding|bordng)\s+h\.?$", t, re.I):
            r["trade"] = "Boarding House"
            stats["commercial_h_expanded"] += 1
            continue
        if re.match(r"^coffee\s+h\.?$", t, re.I):
            r["trade"] = "Coffee House"
            stats["commercial_h_expanded"] += 1
            continue
        if re.match(r"^refreshment\s+h\.?$", t, re.I):
            r["trade"] = "Refreshment House"
            stats["commercial_h_expanded"] += 1
            continue

        if NOT_A_HOUSE_RE.search(t):
            continue

        st = r["street"].strip().lower()
        hn = r["house_number"].strip()
        nt = norm_bldg_key(t)

        # Rule 1: Same (street, house_number) building_name match
        matched_bldg = None
        if hn and (st, hn) in bldg_by_addr and len(nt) >= 4:
            # Skip if trade is a frequent real occupation or pure single-word forename/surname without house suffix
            has_suffix = bool(re.search(r"\b(?:ho|h|house|villa|vil|v|cot|cottage|lodge|l)\.?$", t, re.I))
            is_common_trade = trade_counts[t.lower()] >= 10 and not has_suffix
            if not is_common_trade:
                for nb, orig_b in bldg_by_addr[(st, hn)]:
                    if nt == nb:
                        orig_has_suffix = bool(re.search(r"\b(?:ho|h|house|villa|vil|v|cot|cottage|lodge|l)\.?$", orig_b, re.I))
                        if t.lower() in personal_names and not has_suffix and not orig_has_suffix:
                            continue
                        # Prefer the more complete form between t and orig_b
                        cand = orig_b if len(orig_b) > len(t) and not orig_b.lower().endswith("-void") else t
                        matched_bldg = expand_building_display(cand)
                        stats["rule1_same_addr_bldg"] += 1
                        break

        # Rule 2: Unambiguous trailing ` H` / ` h` / ` H.` (2+ words, not a personal name)
        if not matched_bldg and re.match(r"^[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*\s+[Hh]\.?$", t):
            first_word = t.split()[0].lower()
            if first_word not in personal_names or len(t.split()) >= 2:
                # Avoid "Keppel H." (where Keppel is surname) if only 2 words and no building match
                if len(t.split()) == 2 and first_word in personal_names and first_word not in {"grove", "hope", "olive", "winters", "st"}:
                    pass
                else:
                    matched_bldg = expand_building_display(t)
                    stats["rule2_trailing_h"] += 1

        if matched_bldg:
            r["building_name"] = matched_bldg
            r["trade"] = ""
            if len(samples) < 40 or "lawn terrace" in st:
                samples.append((r["year"], r["street"], hn, t, "=> building_name:", matched_bldg))

    print("Stats:", dict(stats))
    print("\nSamples (including Lawn Terrace):")
    for s in samples:
        print(" ", s)

    if not args.dry_run:
        with open(DATA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print("\nSaved updated data.csv!")


if __name__ == "__main__":
    main()
