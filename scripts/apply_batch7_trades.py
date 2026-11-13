#!/usr/bin/env python3
"""
apply_batch7_trades.py
======================
Applies batch 7 trade normalizations and heals trapped occupations:
* Engrocer -> Greengrocer
* Insp. G.W.R. / Insp variants -> Inspector G.W.R. / Inspector
* Achsmith -> Coachsmith
* Al Merchant -> Coal Merchant
* Ntractor -> Contractor
* Bapt Minister -> Baptist Minister
* Ach Buildr / Coach Buildr / Coach Bldr -> Coach Builder / Coach Builders
* Shipwrgt -> Shipwright
* Wheelwrigh / Wheelwright variants -> Wheelwright / Wheelwrights
* Basket Mkr -> Basket Maker
* Hairdr -> Hairdresser
* Ins. Agnt -> Insurance Agent
* Dec't'rs / Dectrs -> Decorators (and heal trapped names)
* Ck Labourer -> Dock Labourer
* Al Trimmer -> Coal Trimmer (verify & ensure)
* Dghtmn -> Draughtsman
* Foremn -> Foreman
* Nfct / Confctr / Confctrs / Confctnrs -> Confectioner / Confectioners
* Insur Brkr -> Insurance Broker
"""

import os
import sys
import csv
import re
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
BACKUP_CSV = os.path.join(PROJECT_ROOT, "data.csv.bak_before_batch7_trades")
CLEAN_CSV_PY = os.path.join(PROJECT_ROOT, "scripts", "clean_csv.py")
APP_JS = os.path.join(PROJECT_ROOT, "src", "js", "app.js")

def clean_row(r):
    sn = (r.get("surname") or "").strip()
    fn = (r.get("forename") or "").strip()
    bn = (r.get("building_name") or "").strip()
    tr = (r.get("trade") or "").strip()
    changed = False

    # 1. Trapped dec't'rs in surname / forename
    # e.g. Fair Oak Terrace: sn="Collman & Coote, dec't'rs"
    if re.search(r",\s*dec[\x27\x22\x60]?t[\x27\x22\x60]?rs\.?$", sn, re.I):
        sn = re.sub(r",\s*dec[\x27\x22\x60]?t[\x27\x22\x60]?rs\.?$", "", sn, flags=re.I).strip()
        tr = "Decorators"
        changed = True

    # e.g. Fair Oak Terrace: sn="dec'trs", fn="Collman & Coote"
    if re.match(r"^dec[\x27\x22\x60]?t[\x27\x22\x60]?rs\.?$", sn, re.I):
        sn = fn
        fn = ""
        tr = "Decorators"
        changed = True

    # e.g. 1971 Morris Street: fn="& Son, dectrs"
    if re.search(r",\s*dectrs\.?$", fn, re.I):
        fn = re.sub(r",\s*dectrs\.?$", "", fn, flags=re.I).strip()
        tr = "Decorators"
        changed = True

    # 2. Trade Normalizations
    if tr:
        orig_tr = tr
        new_tr = tr

        # Engrocer -> Greengrocer
        if re.search(r"\bengrocer\b", new_tr, re.I):
            new_tr = re.sub(r"\bengrocer\b", "Greengrocer", new_tr, flags=re.I)

        # Insp. G.W.R. and Inspector contractions
        # e.g. Insp G.W.R, Insp. G.W.R., Insp Tr. G. W. R.
        new_tr = re.sub(r"\binsp[\x27\x22\x60]?(?:t[or]+r?)?\.?\s*(?:tr\.?\s*)?(g\.?w\.?r\.?)", r"Inspector \1", new_tr, flags=re.I)
        new_tr = re.sub(r"\binsp[\x27\x22\x60]?(?:t[or]+r?)?\.?\s*(?:tr\.?\s*)?(g\.?p\.?o\.?)", r"Inspector \1", new_tr, flags=re.I)
        new_tr = re.sub(r"\binsp[\x27\x22\x60]?(?:t[or]+r?)?\.?\s*(l\.?\s*&\s*n\.?w\.?)", r"Inspector \1", new_tr, flags=re.I)
        # standalone or trailing insp/insptr/insp'tr
        new_tr = re.sub(r"\b(?:rlwy|rly)\.?\s*insp[\x27\x22\x60]?(?:t[or]+r?)?\.?\b", "Railway Inspector", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:police)\.?\s*insp[\x27\x22\x60]?(?:t[or]+r?)?\.?\b", "Police Inspector", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:traffic)\.?\s*insp[\x27\x22\x60]?(?:t[or]+r?)?\.?\b", "Traffic Inspector", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:signal)\.?\s*insp[\x27\x22\x60]?(?:t[or]+r?)?\.?\b", "Signal Inspector", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:meter)\.?\s*insp[\x27\x22\x60]?(?:t[or]+r?)?\.?\b", "Meter Inspector", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:wagon)\.?\s*insp[\x27\x22\x60]?(?:t[or]+r?)?\.?\b", "Wagon Inspector", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:gas)\.?\s*insp[\x27\x22\x60]?(?:t[or]+r?)?\.?\b", "Gas Inspector", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:iron\s+ore)\.?\s*insp[\x27\x22\x60]?(?:t[or]+r?)?\.?\b", "Iron Ore Inspector", new_tr, flags=re.I)
        new_tr = re.sub(r"\bh\.?m\.?\s+insp\b", "H.M. Inspector", new_tr, flags=re.I)
        if re.match(r"^insp[\x27\x22\x60]?(?:t[or]+r?)?\.?$", new_tr, re.I):
            new_tr = "Inspector"

        # Achsmith -> Coachsmith
        new_tr = re.sub(r"\bachsmith\b", "Coachsmith", new_tr, flags=re.I)

        # Al Merchant -> Coal Merchant / Coal Merchants
        new_tr = re.sub(r"\b(?:al|al\.)\s+merch(?:an)?ts\b", "Coal Merchants", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:al|al\.)\s+merch(?:an)?t\.?\b", "Coal Merchant", new_tr, flags=re.I)

        # Ntractor -> Contractor
        new_tr = re.sub(r"\bntractors\b", "Contractors", new_tr, flags=re.I)
        new_tr = re.sub(r"\bntractor\b", "Contractor", new_tr, flags=re.I)

        # Bapt Minister -> Baptist Minister
        new_tr = re.sub(r"\bbapt\.?\s+minister\b", "Baptist Minister", new_tr, flags=re.I)

        # Ach Buildr / Coach Buildr / Coach Bldr -> Coach Builder / Coach Builders
        new_tr = re.sub(r"\b(?:coach|ach)\s+buildrs\.?\b", "Coach Builders", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:coach|ach)\s+bldrs\.?\b", "Coach Builders", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:coach|ach)\s+buildr\.?\b", "Coach Builder", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:coach|ach)\s+bldr\.?\b", "Coach Builder", new_tr, flags=re.I)
        new_tr = re.sub(r"\bcoach\s+build[\x27\x22\x60]r\.?\b", "Coach Builder", new_tr, flags=re.I)

        # Shipwrgt -> Shipwright
        new_tr = re.sub(r"\bshipwrgt\b", "Shipwright", new_tr, flags=re.I)

        # Wheelwrigh and wheelwright variants
        new_tr = re.sub(r"\bwheelwrgts\b", "Wheelwrights", new_tr, flags=re.I)
        new_tr = re.sub(r"\bwheelwrigts\b", "Wheelwrights", new_tr, flags=re.I)
        new_tr = re.sub(r"\bwheelwrigh\b", "Wheelwright", new_tr, flags=re.I)
        new_tr = re.sub(r"\bwheelwrigt\b", "Wheelwright", new_tr, flags=re.I)
        new_tr = re.sub(r"\bwheelwr[\x27\x22\x60]t\b", "Wheelwright", new_tr, flags=re.I)
        new_tr = re.sub(r"\bwheelwrrt\b", "Wheelwright", new_tr, flags=re.I)
        new_tr = re.sub(r"\bwheelwr[\x27\x22\x60]gt\b", "Wheelwright", new_tr, flags=re.I)
        new_tr = re.sub(r"\bwheelwrit\b", "Wheelwright", new_tr, flags=re.I)
        new_tr = re.sub(r"\bwheelwr\.\b", "Wheelwright", new_tr, flags=re.I)

        # Basket Mkr -> Basket Maker
        new_tr = re.sub(r"\bbasket\s*mkr\.?\b", "Basket Maker", new_tr, flags=re.I)

        # Hairdr -> Hairdresser
        new_tr = re.sub(r"\bhairdr\.?\b", "Hairdresser", new_tr, flags=re.I)

        # Ins. Agnt -> Insurance Agent
        new_tr = re.sub(r"\bins\.?\s*agnt\.?\b", "Insurance Agent", new_tr, flags=re.I)

        # Dec't'rs -> Decorators
        new_tr = re.sub(r"\bdec[\x27\x22\x60]?t[\x27\x22\x60]?rs\b", "Decorators", new_tr, flags=re.I)
        new_tr = re.sub(r"\bdectrs\b", "Decorators", new_tr, flags=re.I)

        # Ck Labourer -> Dock Labourer
        new_tr = re.sub(r"\bck\s+lab(?:ourer|r)?\.?\b", "Dock Labourer", new_tr, flags=re.I)

        # Al Trimmer -> Coal Trimmer
        new_tr = re.sub(r"\b(?:al|al\.)\s*trimm?er(?:\x27r)?\.?\b", "Coal Trimmer", new_tr, flags=re.I)
        new_tr = re.sub(r"\baltrimmer\b", "Coal Trimmer", new_tr, flags=re.I)
        new_tr = re.sub(r"\bcoal\s+trimer\.?\b", "Coal Trimmer", new_tr, flags=re.I)

        # Dghtmn -> Draughtsman
        new_tr = re.sub(r"\bdghtmn\b", "Draughtsman", new_tr, flags=re.I)

        # Foremn -> Foreman
        new_tr = re.sub(r"\bforemn\b", "Foreman", new_tr, flags=re.I)

        # Nfct / Confctr / Confctrs / Confctnrs -> Confectioner / Confectioners
        new_tr = re.sub(r"\b(?:co)?nfct(?:r|n)?s\b", "Confectioners", new_tr, flags=re.I)
        new_tr = re.sub(r"\b(?:co)?nfct(?:r|n)?\b", "Confectioner", new_tr, flags=re.I)

        # Insur Brkr -> Insurance Broker
        new_tr = re.sub(r"\binsur\s*brkr\.?\b", "Insurance Broker", new_tr, flags=re.I)

        # Strip accidental trailing dots if abbreviation had a dot
        if new_tr != orig_tr:
            new_tr = re.sub(r"\s+", " ", new_tr).strip(" ,")
            if new_tr.endswith(".") and not new_tr.upper() in ("H.M.C.", "G.W.R.", "G.P.O.", "J.P.", "P.C.", "R.A.", "R.N."):
                new_tr = new_tr.rstrip(".")
            tr = new_tr
            changed = True

    if changed:
        r["surname"] = sn
        r["forename"] = fn
        r["building_name"] = bn
        r["trade"] = tr

    return r, changed

def update_clean_csv():
    print("Updating scripts/clean_csv.py TRADE_ABBREV_MAP...")
    with open(CLEAN_CSV_PY, "r", encoding="utf-8") as f:
        content = f.read()

    new_entries = """    # Batch 7 User Additions:
    'engrocer': 'greengrocer',
    'insp. g.w.r.': 'inspector g.w.r.',
    'insp. g.w.r': 'inspector g.w.r.',
    'insp g.w.r': 'inspector g.w.r.',
    'insp gwr': 'inspector g.w.r.',
    'insp': 'inspector',
    'insp.': 'inspector',
    'insptr': 'inspector',
    'insptr.': 'inspector',
    'insp\\'tr': 'inspector',
    'rly. insp\\'tr': 'railway inspector',
    'rlwy insp': 'railway inspector',
    'signal insp': 'signal inspector',
    'meter insp': 'meter inspector',
    'wagon insp\\'tr': 'wagon inspector',
    'achsmith': 'coachsmith',
    'al merchant': 'coal merchant',
    'al merchants': 'coal merchants',
    'ntractor': 'contractor',
    'ntractors': 'contractors',
    'bapt minister': 'baptist minister',
    'bapt. minister': 'baptist minister',
    'ach buildr': 'coach builder',
    'ach buildrs': 'coach builders',
    'ach bldr': 'coach builder',
    'ach bldrs': 'coach builders',
    'coach buildr': 'coach builder',
    'coach buildrs': 'coach builders',
    'coach bldr': 'coach builder',
    'coach bldrs': 'coach builders',
    'coach bldr.': 'coach builder',
    'shipwrgt': 'shipwright',
    'wheelwrigh': 'wheelwright',
    'wheelwrigt': 'wheelwright',
    'wheelwrigts': 'wheelwrights',
    'wheelwr\\'t': 'wheelwright',
    'wheelwrrt': 'wheelwright',
    'wheelwr\\'gt': 'wheelwright',
    'wheelwrit': 'wheelwright',
    'wheelwrgts': 'wheelwrights',
    'basket mkr': 'basket maker',
    'basket mkr.': 'basket maker',
    'hairdr': 'hairdresser',
    'hairdr.': 'hairdresser',
    'ins. agnt': 'insurance agent',
    'ins agnt': 'insurance agent',
    'dec\\'t\\'rs': 'decorators',
    'dec\\'trs': 'decorators',
    'dectrs': 'decorators',
    'ck labourer': 'dock labourer',
    'dghtmn': 'draughtsman',
    'foremn': 'foreman',
    'coal foremn': 'coal foreman',
    'nfct': 'confectioner',
    'confctr': 'confectioner',
    'confctrs': 'confectioners',
    'confctnrs': 'confectioners',
    'insur brkr': 'insurance broker',
"""
    anchor = "    'butchrs': 'butchers',\n"
    if anchor in content and "'insp. g.w.r.'" not in content:
        content = content.replace(anchor, anchor + new_entries)

    with open(CLEAN_CSV_PY, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated clean_csv.py successfully.")

def update_app_js():
    print("Updating src/js/app.js formatTrade() rules...")
    with open(APP_JS, "r", encoding="utf-8") as f:
        js = f.read()

    # Add Batch 7 abbreviations to formatTrade()
    anchor = "      // Standard trade abbreviations\n      clean = clean\n"
    new_rules = """      // Standard trade abbreviations
      clean = clean
        .replace(/\\bengrocer\\b/gi, 'Greengrocer')
        .replace(/\\binsp[\\x27\\x22\\x60]?(?:t[or]+r?)?\\.?\\s*(g\\.?w\\.?r\\.?)/gi, 'Inspector G.W.R.')
        .replace(/\\bachsmith\\b/gi, 'Coachsmith')
        .replace(/\\b(?:al|al\\.)\\s+merch(?:an)?ts?\\b/gi, 'Coal Merchant')
        .replace(/\\bntractors?\\b/gi, 'Contractor')
        .replace(/\\bbapt\\.?\\s+minister\\b/gi, 'Baptist Minister')
        .replace(/\\b(?:coach|ach)\\s+(?:buildr|bldr)s?\\b/gi, 'Coach Builder')
        .replace(/\\bshipwrgt\\b/gi, 'Shipwright')
        .replace(/\\bwheelwr(?:igh|igt|rt|it|gts?|\\'[a-z]+)\\b/gi, 'Wheelwright')
        .replace(/\\bbasket\\s*mkr\\.?/gi, 'Basket Maker')
        .replace(/\\bhairdr\\.?/gi, 'Hairdresser')
        .replace(/\\bins\\.?\\s*agnt\\.?/gi, 'Insurance Agent')
        .replace(/\\bdec[\\x27\\x22\\x60]?t[\\x27\\x22\\x60]?rs\\b/gi, 'Decorators')
        .replace(/\\bdectrs\\b/gi, 'Decorators')
        .replace(/\\bck\\s+lab(?:ourer|r)?\\b/gi, 'Dock Labourer')
        .replace(/\\bdghtmn\\b/gi, 'Draughtsman')
        .replace(/\\bforemn\\b/gi, 'Foreman')
        .replace(/\\b(?:co)?nfct(?:r|n)?s\\b/gi, 'Confectioners')
        .replace(/\\b(?:co)?nfct(?:r|n)?\\b/gi, 'Confectioner')
        .replace(/\\binsur\\s*brkr\\.?/gi, 'Insurance Broker')\n"""

    if anchor in js and "'Greengrocer'" not in js:
        js = js.replace(anchor, new_rules)
        with open(APP_JS, "w", encoding="utf-8") as f:
            f.write(js)
        print("Updated app.js formatTrade() rules.")

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

    update_clean_csv()
    update_app_js()

    print("Rebuilding site data and JSON indexes...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_site_data.py")], check=True)

    print("Rebuilding trades data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_trades_data.py")], check=True)

    print("Rebuilding stats data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_stats_data.py")], check=True)

    print("\n[SUCCESS] Batch 7 trades successfully healed and rebuilt!")

if __name__ == "__main__":
    main()
