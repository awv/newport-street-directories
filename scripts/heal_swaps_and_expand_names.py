#!/usr/bin/env python3
"""
heal_swaps_and_expand_names.py
==============================
Phase 2A: Un-swaps all 7,500 verified Tier 1/2/3 reversed Surname <-> Forename records
          from reports/swapped_names_audit.tsv (year <= 1936).
Phase 2B: Expands all verified abbreviated forename tokens (e.g., Wm. -> William, Geo. -> George,
          Thos. -> Thomas, Hy. -> Henry, Chas. -> Charles, Jas. -> James, Jno. -> John, etc.)
          in `forename` (and compound forenames like "Mrs. Wm." -> "Mrs. William").
Rebuilds site data, trades data, and stats data.
"""

import os
import csv
import re
import shutil
import subprocess
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
SWAP_AUDIT = os.path.join(PROJECT_ROOT, "reports", "swapped_names_audit.tsv")
BACKUP_CSV = os.path.join(PROJECT_ROOT, "data.csv.bak_before_swaps_and_expansions")
MAX_YEAR = 1936

FORENAME_EXPANSIONS = {
    "wm.": "William",
    "willm.": "William",
    "wilm.": "William",
    "thos.": "Thomas",
    "geo.": "George",
    "hy.": "Henry",
    "chas.": "Charles",
    "jas.": "James",
    "fredk.": "Frederick",
    "fdk.": "Frederick",
    "fred.": "Frederick",
    "jno.": "John",
    "jn.": "John",
    "jhn.": "John",
    "jos.": "Joseph",
    "edwd.": "Edward",
    "edw.": "Edward",
    "ed.": "Edward",
    "robt.": "Robert",
    "saml.": "Samuel",
    "dd.": "David",
    "benj.": "Benjamin",
    "richd.": "Richard",
    "rd.": "Richard",
    "alfd.": "Alfred",
    "alf.": "Alfred",
    "albt.": "Albert",
    "herbt.": "Herbert",
    "hbt.": "Herbert",
    "alex.": "Alexander",
    "danl.": "Daniel",
    "dl.": "Daniel",
    "arth.": "Arthur",
    "ll.": "Llewellyn",
    "fk.": "Frank",
    "mich.": "Michael",
    "michl.": "Michael",
    "reg.": "Reginald",
    "regnld.": "Reginald",
    "jere.": "Jeremiah",
    "cor.": "Cornelius",
    "chris.": "Christopher",
    "christr.": "Christopher",
    "walt.": "Walter",
    "patk.": "Patrick",
    "nathl.": "Nathaniel",
    "matth.": "Matthew",
    "steph.": "Stephen",
    "fras.": "Francis",
    "abrm.": "Abraham",
    "archbld.": "Archibald",
    "ebenzr.": "Ebenezer",
    "phlp.": "Philip",
    "phil.": "Philip",
    "eliz.": "Elizabeth",
    "margt.": "Margaret",
    "mgt.": "Margaret",
    "cath.": "Catherine",
    "harrt.": "Harriet",
    "charl.": "Charlotte",
    "aug.": "Augustus",
    "reub.": "Reuben",
    "tim.": "Timothy",
    "nich.": "Nicholas",
    "lawr.": "Lawrence",
    "humph.": "Humphrey",
    "sol.": "Solomon",
    "zach.": "Zachariah",
    "jonath.": "Jonathan",
    "theoph.": "Theophilus",
    "bertd.": "Bertrand",
    "cliffd.": "Clifford",
    "leon.": "Leonard",
    "percevl.": "Percival",
    "gilb.": "Gilbert",
    "godf.": "Godfrey",
    "osw.": "Oswald",
    "raym.": "Raymond",
    "wilf.": "Wilfred",
    "gertr.": "Gertrude",
    "winif.": "Winifred",
    "flor.": "Florence",
}

CORP_GUARD_RE = re.compile(r"(?:&|\bltd\b|\blimited\b|\bco\.\b|\bbros\b|\bsons?\b|\bcompany\b|\bsociety\b|\bworks\b|\bgarage\b|\bhotel\b|\binn\b)", re.I)

def expand_tokens_in_str(s):
    if not s or CORP_GUARD_RE.search(s):
        return s, False
    toks = s.split()
    new_toks = []
    changed = False
    for t in toks:
        rep = FORENAME_EXPANSIONS.get(t.lower())
        if rep:
            new_toks.append(rep)
            changed = True
        else:
            new_toks.append(t)
    return " ".join(new_toks), changed

def main():
    # Load verified swapped targets from audit TSV
    swap_keys = set()
    with open(SWAP_AUDIT, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            swap_keys.add((r["year"], r["street"], r["house_number"], r["surname"], r["forename"]))

    print(f"Loaded {len(swap_keys):,} verified swapped-name keys.")
    print(f"Creating backup: {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)

    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    swapped_count = 0
    expanded_count = 0
    expanded_tokens = Counter()

    for r in rows:
        yr = (r.get("year") or "").strip()
        if yr.isdigit() and int(yr) > MAX_YEAR:
            continue
        st = (r.get("street") or "").strip()
        hn = (r.get("house_number") or "").strip()
        sn = (r.get("surname") or "").strip()
        fn = (r.get("forename") or "").strip()

        # Phase 2A: Un-swap verified pairs
        if (yr, st, hn, sn, fn) in swap_keys:
            r["surname"], r["forename"] = fn, sn
            sn, fn = fn, sn
            swapped_count += 1
        elif sn and not fn and sn.lower() in FORENAME_EXPANSIONS:
            # e.g., No. 7 James St 1882: sn='Jno.', fn='' -> fn='Jno.', sn=''
            r["forename"] = sn
            r["surname"] = ""
            fn = sn
            sn = ""
            swapped_count += 1

        # Phase 2B: Expand shortened forenames
        if fn:
            new_fn, ch = expand_tokens_in_str(fn)
            if ch:
                for old_t, new_t in zip(fn.split(), new_fn.split()):
                    if old_t != new_t:
                        expanded_tokens[f"{old_t} -> {new_t}"] += 1
                r["forename"] = new_fn
                expanded_count += 1

    print(f"Un-swapped {swapped_count:,} records.")
    print(f"Expanded shortened forenames in {expanded_count:,} records.")
    print("Top 20 expanded forename tokens:")
    for k, v in expanded_tokens.most_common(20):
        print(f"  {v:6d} | {k}")

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("\nRebuilding site data and JSON indexes...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_site_data.py")], check=True)
    print("\nRebuilding trades data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_trades_data.py")], check=True)
    print("\nRebuilding stats data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_stats_data.py")], check=True)

    if os.path.exists(BACKUP_CSV):
        os.remove(BACKUP_CSV)
        print("Removed temporary backup file.")

    print("\n[SUCCESS] Swapped names un-swapped, forenames expanded, and site rebuilt!")

if __name__ == "__main__":
    main()
