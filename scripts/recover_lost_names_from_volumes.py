#!/usr/bin/env python3
"""
recover_lost_names_from_volumes.py
==================================
Recovers personal surnames and forenames (such as 'Miller', 'Smith', 'Mason', 'Carpenter',
'Baker', 'Taylor', etc.) that were accidentally stripped from `data.csv` by earlier
trade-cleaning passes, by cross-referencing single-name records against `volume_csvs/*_cleaned.csv`.

Excludes dash placeholders ('————', '——', '--') and trade duplicates.
Rebuilds site data, trades data, and stats data (unless --dry-run is passed).
"""

import os
import sys
import csv
import glob
import re
import shutil
import subprocess
from collections import defaultdict, Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
BACKUP_CSV = os.path.join(PROJECT_ROOT, "data.csv.bak_before_recover_names")
MAX_YEAR = 1936

# Same expansion map so "John" in data.csv matches "Jno." in volume_csvs
ABBR_TO_FULL = {
    "wm.": "william", "willm.": "william", "wilm.": "william",
    "thos.": "thomas", "geo.": "george", "hy.": "henry", "chas.": "charles",
    "jas.": "james", "fredk.": "frederick", "fdk.": "frederick", "fred.": "frederick",
    "jno.": "john", "jn.": "john", "jhn.": "john", "jos.": "joseph",
    "edwd.": "edward", "edw.": "edward", "ed.": "edward", "robt.": "robert",
    "saml.": "samuel", "dd.": "david", "benj.": "benjamin", "richd.": "richard",
    "rd.": "richard", "alfd.": "alfred", "alf.": "alfred", "albt.": "albert",
    "herbt.": "herbert", "hbt.": "herbert", "alex.": "alexander", "danl.": "daniel",
    "dl.": "daniel", "arth.": "arthur", "ll.": "llewellyn", "fk.": "frank",
    "mich.": "michael", "michl.": "michael", "reg.": "reginald", "regnld.": "reginald",
    "jere.": "jeremiah", "cor.": "cornelius", "chris.": "christopher", "christr.": "christopher",
    "walt.": "walter", "patk.": "patrick", "nathl.": "nathaniel", "matth.": "matthew",
    "steph.": "stephen", "fras.": "francis", "abrm.": "abraham", "archbld.": "archibald",
    "ebenzr.": "ebenezer", "phlp.": "philip", "phil.": "philip",
    "eliz.": "elizabeth", "margt.": "margaret", "mgt.": "margaret", "cath.": "catherine",
    "harrt.": "harriet", "charl.": "charlotte", "aug.": "augustus", "reub.": "reuben",
    "tim.": "timothy", "nich.": "nicholas", "lawr.": "lawrence"
}

FULL_TO_ABBR = defaultdict(set)
for k, v in ABBR_TO_FULL.items():
    FULL_TO_ABBR[v].add(k)

DASH_OR_EMPTY_RE = re.compile(r"^[\-\—\_\.\s]*$|^void$|^vacant$|^empty$|^and$|^&$", re.I)

# Known occupational surnames that were commonly stripped by earlier trade filters
OCCUPATIONAL_SURNAMES = {
    "smith", "miller", "carpenter", "baker", "taylor", "mason", "clark", "clarke",
    "cooper", "turner", "butler", "cook", "carter", "parker", "fowler", "wright",
    "fisher", "walker", "hunter", "gardner", "gardiner", "potter", "shepherd",
    "weaver", "dyer", "glover", "skinner", "tanner", "chapman", "merchant", "brewer",
    "saddler", "barber", "fletcher", "thatcher", "bowyer", "archer", "sawyer",
    "slater", "painter", "plumber", "porter", "driver", "miner", "collier",
    "farmer", "bailiff", "steward", "ward", "clerk", "mercer", "draper", "butcher",
    "grocer", "chandler", "webb", "webster", "marshall", "spencer", "stewart",
    "stuart", "forrester", "forester", "woodward", "hayward", "page", "knight",
    "bishop", "king", "prince", "duke", "earl", "baron", "pope", "priest", "deacon",
    "monk", "prior", "abbott", "parson", "parsons", "vicar", "curate", "sexton",
    "chamberlain", "trusler", "fuller", "tucker", "harper", "piper", "fiddler",
    "singer", "dancer", "wheeler", "wright", "wainwright", "boatwright", "shipwright"
}

def norm_name_toks(s):
    toks = s.lower().split()
    return " ".join(ABBR_TO_FULL.get(t, t) for t in toks)

def expand_forename(s):
    out = []
    for t in s.split():
        tl = t.lower()
        if tl in ABBR_TO_FULL:
            out.append(ABBR_TO_FULL[tl].capitalize())
        else:
            out.append(t)
    return " ".join(out)

def main():
    dry_run = "--dry-run" in sys.argv

    # Load all volume_csvs into lookup: (yr, street_l, hn) -> list of (sn, fn, tr)
    vol_lookup = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(PROJECT_ROOT, "volume_csvs", "*_cleaned.csv"))):
        yr_base = os.path.basename(path).split("_")[0]
        if not yr_base.isdigit() or int(yr_base) > MAX_YEAR:
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                yr = (r.get("year") or yr_base).strip()
                st = (r.get("street") or "").strip().lower().rstrip(".")
                hn = (r.get("house_number") or "").strip().lower()
                sn = (r.get("surname") or "").strip()
                fn = (r.get("forename") or "").strip()
                tr = (r.get("trade") or "").strip()
                if sn and fn and not DASH_OR_EMPTY_RE.match(sn) and not DASH_OR_EMPTY_RE.match(fn):
                    vol_lookup[(yr, st, hn)].append((sn, fn, tr))

    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not dry_run:
        print(f"Creating backup: {BACKUP_CSV}...")
        shutil.copyfile(DATA_CSV, BACKUP_CSV)

    recovered = []
    yr_counts = Counter()
    restored_names = Counter()

    for r in rows:
        yr = (r.get("year") or "").strip()
        if yr.isdigit() and int(yr) > MAX_YEAR:
            continue
        st = (r.get("street") or "").strip()
        hn = (r.get("house_number") or "").strip()
        sn = (r.get("surname") or "").strip()
        fn = (r.get("forename") or "").strip()
        tr = (r.get("trade") or "").strip()

        if not hn:
            continue
        if not ((fn and not sn) or (sn and not fn)):
            continue

        present = fn if fn else sn
        present_norm = norm_name_toks(present)

        cands = vol_lookup.get((yr, st.lower().rstrip("."), hn.lower()), [])
        for vsn, vfn, vtr in cands:
            vsn_norm = norm_name_toks(vsn)
            vfn_norm = norm_name_toks(vfn)

            # Skip if vfn/vsn equals the trade (e.g. Gait, Draper, '')
            if tr and (vfn.lower() == tr.lower() or vsn.lower() == tr.lower()):
                continue
            if vtr and (vfn.lower() == vtr.lower() or vsn.lower() == vtr.lower()):
                continue

            matched = False
            new_sn, new_fn = None, None

            if present_norm == vfn_norm and not DASH_OR_EMPTY_RE.match(vsn):
                # vsn is the missing part (check if vsn is an abbreviated first name or initial because volume was swapped!)
                if vsn.lower() in ABBR_TO_FULL or re.match(r"^[A-Z]\.(?:\s*[A-Z]\.)?$", vsn):
                    new_sn = vfn
                    new_fn = expand_forename(vsn)
                elif vsn.lower() in OCCUPATIONAL_SURNAMES or vfn_norm not in OCCUPATIONAL_SURNAMES:
                    new_sn = vsn
                    new_fn = expand_forename(vfn)
                matched = True
            elif present_norm == vsn_norm and not DASH_OR_EMPTY_RE.match(vfn):
                # vfn is the missing part! Check if volume was swapped (e.g., vsn='Jno.', vfn='Miller', or vsn='J.', vfn='Smith')
                if vsn.lower() in ABBR_TO_FULL or re.match(r"^[A-Z]\.(?:\s*[A-Z]\.)?$", vsn) or (vfn.lower() in OCCUPATIONAL_SURNAMES and vsn_norm not in OCCUPATIONAL_SURNAMES):
                    new_sn = vfn
                    new_fn = expand_forename(vsn)
                else:
                    new_sn = vsn
                    new_fn = expand_forename(vfn)
                matched = True

            if matched and new_sn and new_fn:
                # Extra guard: ensure we didn't grab a non-name like 'Motor' 'Mechanic'
                if new_sn.lower() == "motor" and new_fn.lower() == "mechanic":
                    continue
                recovered.append((yr, st, hn, (sn, fn), (new_sn, new_fn), tr))
                yr_counts[yr] += 1
                restored_names[new_sn] += 1
                if not dry_run:
                    r["surname"] = new_sn
                    r["forename"] = new_fn
                    # Clean trailing ", Smith" / ", Cooper" if an old script appended the stripped surname to trade
                    if tr and tr.lower().endswith(", " + new_sn.lower()):
                        r["trade"] = tr[: -(len(new_sn) + 2)].strip()
                break

    print(f"Records {'matched' if dry_run else 'recovered'}: {len(recovered):,}")
    print("Top 20 restored surnames:")
    for k, v in restored_names.most_common(20):
        print(f"  {v:4d} | {k}")
    print("\nSample 20 recoveries:")
    for x in recovered[:20]:
        print(f"  {x[0]} {x[1]} No.{x[2]}: {x[3]} -> {x[4]} (trade={x[5]!r})")

    if dry_run:
        return

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

    print("\n[SUCCESS] Lost names recovered and site rebuilt!")

if __name__ == "__main__":
    main()
