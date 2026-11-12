#!/usr/bin/env python3
"""
apply_batch5_trades.py
======================
Applies batch 5 trade normalizations and heals trapped occupations:
* Mou.mas. -> Monumental Mason
* Gen. Shop -> General Shop
* Muffin Bkr -> Muffin Baker
* Tai. -> Tailor
* Engrocer -> Greengrocer
* Wardrbs. -> Wardrobes / Wardrb Dl -> Wardrobe Dealer
* Shop Kr / Shopkr -> Shopkeeper
* Sadlr / Sadlrs -> Saddler / Saddlers
* Mar Stor / Mar Stores -> Marine Stores
* Pattern Mkr. -> Pattern Maker
* Clothes D'lr -> Clothes Dealer
* Plaster'm'ldr And Tobacconjst -> Plaster Moulder and Tobacconist
* Nfec'tr / nfectionr -> Confectioner
* Ironmongers & Iron Merct -> Ironmongers and Iron Merchant
"""

import os
import sys
import csv
import re
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
BACKUP_CSV = os.path.join(PROJECT_ROOT, "data.csv.bak_before_batch5_trades")
CLEAN_CSV_PY = os.path.join(PROJECT_ROOT, "scripts", "clean_csv.py")

TRADE_EXACT_MAP = [
    (re.compile(r"^mou[\.\s]*mas\.?$", re.I), "Monumental Mason"),
    (re.compile(r"^gen[\.\s]+shop\.?$", re.I), "General Shop"),
    (re.compile(r"^muffin\s*bk[\x27\.]?r\.?$", re.I), "Muffin Baker"),
    (re.compile(r"^tai\.?$", re.I), "Tailor"),
    (re.compile(r"^engrocer$", re.I), "Greengrocer"),
    (re.compile(r"^wardrbs?\.?$", re.I), "Wardrobes"),
    (re.compile(r"^wardrb\s*dl\.?$", re.I), "Wardrobe Dealer"),
    (re.compile(r"^shop\s*k[\x27\.]?r\.?$", re.I), "Shopkeeper"),
    (re.compile(r"^sadlr$", re.I), "Saddler"),
    (re.compile(r"^sadlrs$", re.I), "Saddlers"),
    (re.compile(r"^mar\s*stor(?:es?)?\.?$", re.I), "Marine Stores"),
    (re.compile(r"^pattern\s*mkr\.?$", re.I), "Pattern Maker"),
    (re.compile(r"^clothes\s*d[\x27\.]?lr\.?$", re.I), "Clothes Dealer"),
    (re.compile(r"^plaster[\x27\s]*m[\x27\.]*ldr\s+and\s+tobaccon[ij]st$", re.I), "Plaster Moulder and Tobacconist"),
    (re.compile(r"^nfe[c\x27\.]*tr\.?$", re.I), "Confectioner"),
    (re.compile(r"^nfectionr?\.?$", re.I), "Confectioner"),
    (re.compile(r"^ironmongers\s*&\s*iron\s*merct\.?$", re.I), "Ironmongers and Iron Merchant"),
]

def clean_row(r):
    sn = (r.get("surname") or "").strip()
    fn = (r.get("forename") or "").strip()
    tr = (r.get("trade") or "").strip()
    st = (r.get("street") or "").strip()
    hn = (r.get("house_number") or "").strip()
    yr = (r.get("year") or "").strip()
    changed = False

    # 1. Trapped pattern mkr / gen shop in forename
    m_pat = re.match(r"^(.*?)\s+pattern\s*mkr\.?$", fn, re.I)
    if m_pat:
        fn = m_pat.group(1).strip()
        tr = "Pattern Maker"
        changed = True

    m_gen_fn = re.match(r"^(.*?),\s*gen[\.\s]*shop.*$", fn, re.I)
    if m_gen_fn:
        fn = m_gen_fn.group(1).strip()
        tr = "General Shop"
        changed = True

    # 2. Compound record: Perkins Hy. gen. shop
    if tr.lower() == "perkins hy. gen. shop":
        sn = "Perkins"
        fn = "Hy."
        tr = "General Shop"
        changed = True

    # 3. Compound record: gen shop, John Frederick C.
    if tr.lower().startswith("gen shop, john"):
        tr = "General Shop"
        changed = True

    # 4. Compound record: Ironworker Swimbourne Mrs. C. gen shop
    if "swimbourne" in tr.lower() and "gen shop" in tr.lower():
        tr = "Ironworker"
        changed = True

    # 5. Direct trade exact mappings
    for pat, repl in TRADE_EXACT_MAP:
        if pat.search(tr):
            tr = repl
            changed = True
            break

    if changed:
        r["surname"] = sn
        r["forename"] = fn
        r["trade"] = tr
    return r, changed

def main():
    print(f"Creating backup: {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)

    print("Reading and updating data.csv...")
    rows = []
    updated_count = 0
    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            r, changed = clean_row(r)
            if changed:
                updated_count += 1
            rows.append(r)

    print(f"Applied trade expansions and disentanglements to {updated_count:,} records.")

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Synchronize clean_csv.py TRADE_ABBREV_MAP
    print("Updating scripts/clean_csv.py TRADE_ABBREV_MAP...")
    with open(CLEAN_CSV_PY, "r", encoding="utf-8") as f:
        content = f.read()

    new_entries = """    # Batch 5 User Additions:
    'mou.mas.': 'monumental mason',
    'mou. mas.': 'monumental mason',
    'mou mas': 'monumental mason',
    'gen. shop': 'general shop',
    'gen shop': 'general shop',
    'muffin bkr': 'muffin baker',
    'muffin bkr.': 'muffin baker',
    'tai.': 'tailor',
    'engrocer': 'greengrocer',
    'wardrbs.': 'wardrobes',
    'wardrbs': 'wardrobes',
    'wardrb dl': 'wardrobe dealer',
    'wardrb dl.': 'wardrobe dealer',
    'shop kr': 'shopkeeper',
    'shopkr': 'shopkeeper',
    'shopkr.': 'shopkeeper',
    'sadlr': 'saddler',
    'sadlrs': 'saddlers',
    'mar stor': 'marine stores',
    'mar stores': 'marine stores',
    'pattern mkr.': 'pattern maker',
    'pattern mkr': 'pattern maker',
    'clothes d\\'lr': 'clothes dealer',
    'clothes d\\'lr.': 'clothes dealer',
    'clothes dlr': 'clothes dealer',
    'plaster\\'m\\'ldr and tobacconjst': 'plaster moulder and tobacconist',
    'plaster m\\'ldr and tobacconist': 'plaster moulder and tobacconist',
    'nfec\\'tr': 'confectioner',
    'nf\\'tr': 'confectioner',
    'nfectionr': 'confectioner',
    'ironmongers & iron merct': 'ironmongers and iron merchant',
    'ironmongers & iron merct.': 'ironmongers and iron merchant',
"""
    anchor = "    'rn merchant': 'corn merchant',\n"
    if anchor in content and "'mou.mas.'" not in content:
        content = content.replace(anchor, anchor + new_entries)
        with open(CLEAN_CSV_PY, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated clean_csv.py with Batch 5 trade mappings.")

    print("Rebuilding site data and JSON indexes...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_site_data.py")], check=True)

    print("Rebuilding stats data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_stats_data.py")], check=True)

    print("\n[SUCCESS] Batch 5 trades successfully healed!")

if __name__ == "__main__":
    main()
