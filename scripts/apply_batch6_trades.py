#!/usr/bin/env python3
"""
apply_batch6_trades.py
======================
Applies batch 6 trade normalizations and heals trapped occupations dataset-wide:
* Al Yard -> Coal Yard
* Al Trimmer / Altrimmer / Al Trimmer'r / Al Trimer. -> Coal Trimmer
* Grocer Bkr -> Grocer Baker
* Shoemk'r -> Shoemaker
* Shopk'per / Shop Kpr -> Shopkeeper
* Auction Rms -> Auction Rooms
* Machn. / Mechin -> Machinist
* Provn. Dealer -> Provisions Dealer
* Builders' Merct. -> Builders' Merchants
* Poulterer; -> Poulterer
* Yeast Merch -> Yeast Merchant
* Fish Br -> Fish Bar
* Auct'r -> Auctioneer
* Ckman -> Dockman
* Al Shipper -> Coal Shipper
* Boil. Mkr -> Boiler Maker
* Engine Driv / Engine Dri / Engine Driver. -> Engine Driver
* Ffee House -> Coffee House
* Boardng Ho -> Boarding House
* Ck Foundry -> Dock Foundry
* Engrocer -> Greengrocer
* Pat. Mkr. -> Pattern Maker
* Rope M'ftr -> Rope Manufacturer
* Pianoforte Wareho. -> Pianoforte Warehouse
* Carriage Bldrs -> Carriage Builders / Carriage Bldr -> Carriage Builder
* Music Tchr -> Music Teacher
* Nf'ct'nr -> Confectioner
* Sergt-major / Sgt.-major -> Sergeant Major
* H.m.c. -> H.M.C. (and disentangle H.M.C./Customs trapped in surname/forename/building)
* Asst. -> Assistant
* Formn Carpenter -> Foreman Carpenter
* Signal Lin'smn -> Signal Linesman
* Eng'nr / Engr -> Engineer
* Police Off -> Police Officer
* Lino Op -> Lino Operator
* Iron Mldr -> Iron Moulder
* Berth Mas. -> Berth Master
* Oper -> Operator
* Prudential Agt -> Prudential Agent
* Achman -> Coachman
* Ticket Collectr -> Ticket Collector
* Butchr -> Butcher / Butchers
"""

import os
import sys
import csv
import re
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
BACKUP_CSV = os.path.join(PROJECT_ROOT, "data.csv.bak_before_batch6_trades")
CLEAN_CSV_PY = os.path.join(PROJECT_ROOT, "scripts", "clean_csv.py")
APP_JS = os.path.join(PROJECT_ROOT, "src", "js", "app.js")

def clean_row(r):
    sn = (r.get("surname") or "").strip()
    fn = (r.get("forename") or "").strip()
    bn = (r.get("building_name") or "").strip()
    tr = (r.get("trade") or "").strip()
    changed = False

    # 1. H.M.C. and Customs trapped in name / building fields
    # e.g. Dewsland Park Road 64: fn="John H M. C", tr=""
    m_hmc_fn = re.match(r"^(.*?)\s+H\.?\s*M\.?\s*C\.?$", fn, re.I)
    if m_hmc_fn and not tr:
        fn = m_hmc_fn.group(1).strip()
        tr = "H.M.C."
        changed = True

    # e.g. Caerleon-road 228: sn="H.M.C.", fn="Jarvis Wm. A."
    if sn.upper() in ("H.M.C.", "HMC", "H.M.C"):
        if fn:
            parts = fn.split(" ", 1)
            sn = parts[0]
            fn = parts[1] if len(parts) > 1 else ""
            tr = "H.M.C."
            changed = True

    # e.g. Mountjoy Street 2: sn="John James", fn="H.M.C."
    if fn.upper() in ("H.M.C.", "HMC", "H.M.C"):
        parts = sn.split(" ", 1)
        sn = parts[0]
        fn = parts[1] if len(parts) > 1 else ""
        tr = "H.M.C."
        changed = True

    # e.g. Ronald Road 25 / St Julian's Road 8: bn="H.M.C."
    if bn.upper() in ("H.M.C.", "HMC", "H.M.C"):
        bn = ""
        tr = "H.M.C."
        changed = True

    # e.g. Gothic Villas 19/23: fn="H. M.'s Customs", sn="Gill H."
    if re.match(r"^H\.?\s*M\.?[\x27\x22\x60]?s?\s+Customs$", fn, re.I):
        parts = sn.split(" ", 1)
        sn = parts[0]
        fn = parts[1] if len(parts) > 1 else ""
        tr = "H.M. Customs"
        changed = True

    # e.g. Herbert Street 23: bn="H. M.'s Customs"
    if re.match(r"^H\.?\s*M\.?[\x27\x22\x60]?s?\s+Customs$", bn, re.I):
        bn = ""
        tr = "H.M. Customs"
        changed = True

    # e.g. Annesley Road 30: sn="Her Majesty's Customs", fn="R. C. W.", tr="Merrick"
    if sn.lower() == "her majesty's customs" and tr:
        sn = tr
        tr = "Her Majesty's Customs"
        changed = True

    # e.g. Somerton Lane: sn="customs", fn="Reg.", tr="Morris"
    if sn.lower() == "customs" and tr:
        sn = tr
        tr = "Customs"
        changed = True

    # e.g. Summerhill Avenue 29: fn="Customs R. J", tr="Mechanic"
    if fn.lower().startswith("customs "):
        fn = fn[8:].strip()
        tr = f"Customs {tr}".strip() if tr else "Customs"
        changed = True

    # e.g. Shaftesbury Street 184: tr="oper Albert J", fn=""
    if tr.lower().startswith("oper "):
        op_fn = tr[5:].strip()
        if not fn:
            fn = op_fn
            tr = "Operator"
            changed = True

    # 2. Trade Normalizations
    if tr:
        orig_tr = tr
        new_tr = tr

        # Strip trailing semicolon e.g. Poulterer;
        new_tr = re.sub(r";+$", "", new_tr).strip()

        # Al Yard -> Coal Yard
        new_tr = re.sub(r"\b(?:al|al\.)\s+yard\b", "Coal Yard", new_tr, flags=re.I)

        # Al Trimmer / Altrimmer / Al Trimmer'r / Al Trimer. -> Coal Trimmer
        new_tr = re.sub(r"\b(?:al|al\.)\s*trimm?er(?:\x27r)?\.?\b", "Coal Trimmer", new_tr, flags=re.I)
        new_tr = re.sub(r"\baltrimmer\b", "Coal Trimmer", new_tr, flags=re.I)
        new_tr = re.sub(r"\bcoal\s+trimer\.?\b", "Coal Trimmer", new_tr, flags=re.I)

        # Grocer Bkr -> Grocer Baker
        new_tr = re.sub(r"\bgrocer\s+bkr\.?\b", "Grocer Baker", new_tr, flags=re.I)

        # Shoemk'r -> Shoemaker
        new_tr = re.sub(r"\bshoemk[\x27\x22\x60]?[a-z]*\.?\b", "Shoemaker", new_tr, flags=re.I)

        # Shopk'per / Shop Kpr -> Shopkeeper
        new_tr = re.sub(r"\bshop\s*k[\x27\x22\x60]?[a-z]*\.?\b", "Shopkeeper", new_tr, flags=re.I)

        # Auction Rms -> Auction Rooms
        new_tr = re.sub(r"\bauction\s+rms\.?\b", "Auction Rooms", new_tr, flags=re.I)

        # Machn. / Mechin -> Machinist
        new_tr = re.sub(r"\b(?:machn|mechin)\.?\b", "Machinist", new_tr, flags=re.I)

        # Provn. Dealer -> Provisions Dealer
        new_tr = re.sub(r"\bprovn\.?\s+dealer\b", "Provisions Dealer", new_tr, flags=re.I)

        # Builders' Merct. -> Builders' Merchants
        new_tr = re.sub(r"\bbuilders[\x27\x22\x60]?\s+merct\.?\b", "Builders' Merchants", new_tr, flags=re.I)

        # Yeast Merch -> Yeast Merchant
        new_tr = re.sub(r"\byeast\s+merch(?:[\x27\x22\x60]?t|t)?\.?\b", "Yeast Merchant", new_tr, flags=re.I)

        # Fish Br -> Fish Bar
        new_tr = re.sub(r"\bfish\s+br\.?\b", "Fish Bar", new_tr, flags=re.I)

        # Auct'r -> Auctioneer
        new_tr = re.sub(r"\bauct[\x27\x22\x60]?r\b", "Auctioneer", new_tr, flags=re.I)

        # Ckman -> Dockman
        new_tr = re.sub(r"\bckman\b", "Dockman", new_tr, flags=re.I)

        # Al Shipper -> Coal Shipper
        new_tr = re.sub(r"\b(?:al|al\.)\s+shipper\b", "Coal Shipper", new_tr, flags=re.I)

        # Boil. Mkr -> Boiler Maker
        new_tr = re.sub(r"\bboil\.?\s+mkr\.?\b", "Boiler Maker", new_tr, flags=re.I)

        # Engine Driv / Dri / Driver. -> Engine Driver
        new_tr = re.sub(r"\bengine\s+dri(?:v|vr|we?r)?\.?\b", "Engine Driver", new_tr, flags=re.I)
        new_tr = re.sub(r"\bengine\s+driver\.\b", "Engine Driver", new_tr, flags=re.I)

        # Ffee House -> Coffee House
        new_tr = re.sub(r"\bffee\s+house\b", "Coffee House", new_tr, flags=re.I)

        # Boardng Ho -> Boarding House
        new_tr = re.sub(r"\bboardng\s+ho\.?\b", "Boarding House", new_tr, flags=re.I)

        # Ck Foundry -> Dock Foundry
        new_tr = re.sub(r"\bck\s+foundry\b", "Dock Foundry", new_tr, flags=re.I)

        # Engrocer -> Greengrocer
        new_tr = re.sub(r"\bengrocer\b", "Greengrocer", new_tr, flags=re.I)
        new_tr = re.sub(r"\bgreengr(?:er|or|[\x27\x22\x60]er|cretc)?\.?\b", "Greengrocer", new_tr, flags=re.I)

        # Pat. Mkr. -> Pattern Maker
        new_tr = re.sub(r"\bpat\.?\s+mkr\.?\b", "Pattern Maker", new_tr, flags=re.I)

        # Rope M'ftr -> Rope Manufacturer
        new_tr = re.sub(r"\brope\s+m[\x27\x22\x60]?ftr\.?\b", "Rope Manufacturer", new_tr, flags=re.I)

        # Pianoforte Wareho. -> Pianoforte Warehouse
        new_tr = re.sub(r"\bpianoforte\s+wareho\.?\b", "Pianoforte Warehouse", new_tr, flags=re.I)

        # Carriage Bldrs -> Carriage Builders / Carriage Bldr -> Carriage Builder
        new_tr = re.sub(r"\bcarriage\s+bldrs\.?\b", "Carriage Builders", new_tr, flags=re.I)
        new_tr = re.sub(r"\bcarriage\s+bldr\.?\b", "Carriage Builder", new_tr, flags=re.I)

        # Music Tchr -> Music Teacher
        new_tr = re.sub(r"\bmusic\s+tchr\.?\b", "Music Teacher", new_tr, flags=re.I)

        # Nf'ct'nr -> Confectioner
        new_tr = re.sub(r"\b(?:conf[\x27\x22\x60]?ct[\x27\x22\x60]?nr|nf[\x27\x22\x60]?ct[\x27\x22\x60]?nr)\b", "Confectioner", new_tr, flags=re.I)

        # Sergt-major / Sgt.-major -> Sergeant Major
        new_tr = re.sub(r"\b(?:sergt|sgt)\.?-major\b", "Sergeant Major", new_tr, flags=re.I)

        # H.m.c. -> H.M.C.
        if new_tr.lower().strip(". ") in ("hmc", "h.m.c", "h.m.c.", "h m. c"):
            new_tr = "H.M.C."

        # Asst. -> Assistant
        if new_tr.strip().lower() in ("asst", "asst."):
            new_tr = "Assistant"
        else:
            new_tr = re.sub(r"\basst\.\s*", "Assistant ", new_tr, flags=re.I)
            new_tr = re.sub(r"\basst\.overseer\b", "Assistant Overseer", new_tr, flags=re.I)
            new_tr = re.sub(r"\basst\.schoolmtr\b", "Assistant Schoolmaster", new_tr, flags=re.I)

        # Formn Carpenter -> Foreman Carpenter
        new_tr = re.sub(r"\bformn\s+carpenter\b", "Foreman Carpenter", new_tr, flags=re.I)

        # Signal Lin'smn -> Signal Linesman
        new_tr = re.sub(r"\bsignal\s+lin[\x27\x22\x60]?smn\b", "Signal Linesman", new_tr, flags=re.I)

        # Eng'nr / Engr -> Engineer
        new_tr = re.sub(r"\beng[\x27\x22\x60]?nr\b", "Engineer", new_tr, flags=re.I)
        if new_tr.strip().lower() in ("engr", "engr."):
            new_tr = "Engineer"
        else:
            new_tr = re.sub(r"\b([a-zA-Z]+)\s+engr\.?\b", r"\1 Engineer", new_tr, flags=re.I)
            new_tr = re.sub(r"\bengr\.?\s+&\s+mer\.?\b", "Engineer & Merchant", new_tr, flags=re.I)

        # Police Off -> Police Officer
        new_tr = re.sub(r"\bpolice\s+off\.?\b", "Police Officer", new_tr, flags=re.I)

        # Lino Op -> Lino Operator
        new_tr = re.sub(r"\blino\s+op(?:[\x27\x22\x60]?atr|[\x27\x22\x60]?tr|er|er-ator)?\.?\b", "Lino Operator", new_tr, flags=re.I)

        # Iron Mldr -> Iron Moulder
        new_tr = re.sub(r"\biron\s*mldr\b", "Iron Moulder", new_tr, flags=re.I)

        # Berth Mas. -> Berth Master
        new_tr = re.sub(r"\bberth\s+mas(?:tr)?\.?\b", "Berth Master", new_tr, flags=re.I)

        # Oper -> Operator
        if new_tr.strip().lower() == "oper":
            new_tr = "Operator"

        # Prudential Agt -> Prudential Agent
        new_tr = re.sub(r"\bprudential\s+agt\.?\b", "Prudential Agent", new_tr, flags=re.I)

        # Achman -> Coachman
        new_tr = re.sub(r"\bachman\b", "Coachman", new_tr, flags=re.I)

        # Ticket Collectr -> Ticket Collector
        new_tr = re.sub(r"\bticket\s+collectrr?\.?\b", "Ticket Collector", new_tr, flags=re.I)

        # Butchr -> Butcher / Butchers
        new_tr = re.sub(r"\bbutchrs\b", "Butchers", new_tr, flags=re.I)
        new_tr = re.sub(r"\bbutchr\.?\b", "Butcher", new_tr, flags=re.I)
        new_tr = re.sub(r"\bpork\s+butchrr?\b", "Pork Butcher", new_tr, flags=re.I)
        new_tr = re.sub(r"\bfamily\s+butchr\b", "Family Butcher", new_tr, flags=re.I)

        # Clean trailing dot if abbreviation was expanded and ended with a dot
        if new_tr != orig_tr:
            new_tr = re.sub(r"\s+", " ", new_tr).strip(" ,")
            # If the trade ends with a dot but isn't an acronym like H.M.C., strip it
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
    print("Updating scripts/clean_csv.py TRADE_ABBREV_MAP and acronyms...")
    with open(CLEAN_CSV_PY, "r", encoding="utf-8") as f:
        content = f.read()

    new_entries = """    # Batch 6 User Additions:
    'al yard': 'coal yard',
    'al trimmer': 'coal trimmer',
    'altrimmer': 'coal trimmer',
    'al trimmer\\'r': 'coal trimmer',
    'al trimer': 'coal trimmer',
    'al trimer.': 'coal trimmer',
    'grocer bkr': 'grocer baker',
    'shoemk\\'r': 'shoemaker',
    'shoemkr': 'shoemaker',
    'shoemkr.': 'shoemaker',
    'shoemker': 'shoemaker',
    'shopk\\'per': 'shopkeeper',
    'shopkper': 'shopkeeper',
    'shop kpr': 'shopkeeper',
    'shopkp\\'r': 'shopkeeper',
    'shopkpkr': 'shopkeeper',
    'auction rms': 'auction rooms',
    'machn.': 'machinist',
    'machn': 'machinist',
    'mechin': 'machinist',
    'provn. dealer': 'provisions dealer',
    'provn dealer': 'provisions dealer',
    'builders\\' merct.': 'builders\\' merchants',
    'builders\\' merct': 'builders\\' merchants',
    'poulterer;': 'poulterer',
    'yeast merch': 'yeast merchant',
    'yeast merch\\'t': 'yeast merchant',
    'yeast mercht': 'yeast merchant',
    'fish br': 'fish bar',
    'auct\\'r': 'auctioneer',
    'auct\\'r portr': 'auctioneer porter',
    'ckman': 'dockman',
    'al shipper': 'coal shipper',
    'boil. mkr': 'boiler maker',
    'boil mkr': 'boiler maker',
    'engine driv': 'engine driver',
    'engine driv.': 'engine driver',
    'engine dri': 'engine driver',
    'engine driver.': 'engine driver',
    'engine drivr.': 'engine driver',
    'ffee house': 'coffee house',
    'boardng ho': 'boarding house',
    'ck foundry': 'dock foundry',
    'pat. mkr.': 'pattern maker',
    'pat. mkr': 'pattern maker',
    'pat mkr': 'pattern maker',
    'rope m\\'ftr': 'rope manufacturer',
    'pianoforte wareho.': 'pianoforte warehouse',
    'carriage bldrs': 'carriage builders',
    'carriage bldr': 'carriage builder',
    'music tchr': 'music teacher',
    'music tchr.': 'music teacher',
    'nf\\'ct\\'nr': 'confectioner',
    'conf\\'ct\\'nr': 'confectioner',
    'sergt-major': 'sergeant major',
    'sgt.-major': 'sergeant major',
    'asst.': 'assistant',
    'formn carpenter': 'foreman carpenter',
    'signal lin\\'smn': 'signal linesman',
    'eng\\'nr': 'engineer',
    'engr': 'engineer',
    'engr.': 'engineer',
    'civil engr': 'civil engineer',
    'motor engr': 'motor engineer',
    'police off': 'police officer',
    'lino op': 'lino operator',
    'lino oper': 'lino operator',
    'lino op\\'atr': 'lino operator',
    'iron mldr': 'iron moulder',
    'ironmldr': 'iron moulder',
    'berth mas.': 'berth master',
    'berth mas': 'berth master',
    'berth mastr': 'berth master',
    'oper': 'operator',
    'prudential agt': 'prudential agent',
    'achman': 'coachman',
    'ticket collectr': 'ticket collector',
    'butchr': 'butcher',
    'butchr.': 'butcher',
    'butchrs': 'butchers',
"""
    anchor = "    'ironmongers & iron merct.': 'ironmongers and iron merchant',\n"
    if anchor in content and "'al yard'" not in content:
        content = content.replace(anchor, anchor + new_entries)

    # Ensure H.M.C. acronym handling
    if "'h.m.c': 'H.M.C.'" in content and "'h.m.c.': 'H.M.C.'" not in content:
        content = content.replace("'h.m.c': 'H.M.C.',", "'h.m.c': 'H.M.C.',\n                'h.m.c.': 'H.M.C.',\n                'hmc': 'H.M.C.',")

    with open(CLEAN_CSV_PY, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated clean_csv.py successfully.")

def update_app_js():
    print("Updating src/js/app.js to preserve H.M.C. / J.P. casing and format trades...")
    with open(APP_JS, "r", encoding="utf-8") as f:
        js = f.read()

    # 1. Remove 'tai' from non-trade regex so Tailor is never discarded as Residence
    js = js.replace("|si|tai|vw|", "|si|vw|")

    # 2. Add H.M.C. / J.P. preservation to formatTrade title-casing
    old_casing = """      clean = clean.replace(/\\w\\S*/g, (txt) => {
        if (txt.toUpperCase() === 'G.W.R.') return 'G.W.R.';
        if (txt.toUpperCase() === 'G.P.O.') return 'G.P.O.';
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
      });"""

    new_casing = """      clean = clean.replace(/\\b(g\\.?p\\.?o\\.?)\\b\\.?/gi, 'G.P.O.');
      clean = clean.replace(/\\b(h\\.?m\\.?c\\.?)\\b\\.?/gi, 'H.M.C.');
      clean = clean.replace(/\\b(j\\.?p\\.?)\\b\\.?/gi, 'J.P.');
      clean = clean.replace(/\\w\\S*/g, (txt) => {
        const u = txt.toUpperCase();
        if (u === 'G.W.R.' || u === 'G.W.R') return 'G.W.R.';
        if (u === 'G.P.O.' || u === 'G.P.O') return 'G.P.O.';
        if (u === 'H.M.C.' || u === 'H.M.C') return 'H.M.C.';
        if (u === 'J.P.' || u === 'J.P') return 'J.P.';
        if (u === 'R.A.' || u === 'R.A') return 'R.A.';
        if (u === 'R.N.' || u === 'R.N') return 'R.N.';
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
      });"""

    if old_casing in js:
        js = js.replace(old_casing, new_casing)
        print("Updated formatTrade() acronym casing in app.js.")

    with open(APP_JS, "w", encoding="utf-8") as f:
        f.write(js)
    print("Updated app.js successfully.")

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

    print("\n[SUCCESS] Batch 6 trades successfully healed and rebuilt!")

if __name__ == "__main__":
    main()
