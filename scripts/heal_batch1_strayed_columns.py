#!/usr/bin/env python3
"""
heal_batch1_strayed_columns.py
==============================
Batch 1 of Strayed Column Healing (year <= 1936):
1. COMPOUND_TRADE_AND_HOUSE (~559 records):
   Splits "[Trade], [House/Chambers]" from `trade` into `trade` and `building_name`.
   Normalizes suffixes (ho -> House, vil -> Villa, cot -> Cottage) and casing.
2. TRADE_IN_BUILDING (~408 records):
   Moves explicit occupations & void/vacant tokens trapped in `building_name` into `trade`.
3. Rebuilds site data, trades data, and stats data.
"""

import os
import csv
import re
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
AUDIT_TSV = os.path.join(PROJECT_ROOT, "reports", "strayed_columns_audit.tsv")
BACKUP_CSV = os.path.join(PROJECT_ROOT, "data.csv.bak_before_batch1_strayed")

MAX_YEAR = 1936

EXPLICIT_TRADES_IN_BN = {
    "void", "vacant", "vacant sites", "vacant site", "shop void", "house void",
    "labourer", "clerk", "ironworker", "steelworker", "carpenter", "joiner",
    "builder", "gardener", "engineer", "guard", "painter", "quarryman",
    "enameller", "collector", "decorator", "coachbuilder", "coachman",
    "fitter", "turner", "machinist", "mason", "stonemason", "plumber",
    "plasterer", "slater", "bricklayer", "tailor", "baker", "butcher",
    "grocer", "greengrocer", "draper", "printer", "miner", "collier",
    "seaman", "sailor", "mariner", "trimmer", "coal trimmer", "shipper",
    "porter", "waiter", "driver", "engine driver", "postman", "police",
    "policeman", "constable", "foreman", "manager", "agent", "insurance agent",
    "traveller", "commercial traveller", "salesman", "solicitor", "accountant",
    "architect", "surveyor", "chemist", "dentist", "surgeon", "watchmaker",
    "blacksmith", "boilermaker", "shipwright", "wheelwright", "patternmaker",
    "moulder", "shoemaker", "bootmaker", "hairdresser", "tobacconist",
    "confectioner", "fruiterer", "fishmonger", "ironmonger", "stationer",
    "bookseller", "newsagent", "apartments", "lodgings", "widow", "spinster",
    "fireman", "stoker", "shunter", "platelayer", "signalman", "pointsman",
    "checkweigher", "checker", "weighman", "timekeeper", "packer", "roller",
    "puddler", "smelter", "annealer", "galvanizer", "cooper", "saddler",
    "upholsterer", "cabinetmaker", "charwoman", "laundress", "dressmaker",
    "milliner", "nurse", "housekeeper", "cook", "groom", "ostler", "carter",
    "haulier", "carrier", "drayman", "cabman", "boatman", "waterman",
    "pilot", "hobbler", "rigger", "stevedore", "lighterman", "electrician",
    "ganger", "sculptor", "brewer", "schoolmaster", "schoolmistress",
    "stationmaster", "postmaster", "teacher", "music teacher", "minister",
    "clergyman", "assistant", "steward", "storekeeper", "shopkeeper"
}

COMPOUND_EXCLUDE_RE = re.compile(
    r"\b(?:association|society|union|company|co\.|ltd|limited|district|board|committee|council|church|chapel|hospital|infirmary|dispensary|school|college|club|institute|depot|yard|works|foundry|brewery|mill|mills|railway|g\.w\.r\.|station|office|offices|exchange|bank)\b",
    re.I
)

def normalize_building_name(b):
    b = b.strip().rstrip(".")
    # Expand common directory building abbreviations
    b = re.sub(r"\bho$", "House", b, flags=re.I)
    b = re.sub(r"\bvil$", "Villa", b, flags=re.I)
    b = re.sub(r"\bcot$", "Cottage", b, flags=re.I)
    b = re.sub(r"\bbldgs$", "Buildings", b, flags=re.I)
    b = re.sub(r"\bchmbrs$", "Chambers", b, flags=re.I)
    # Clean Title Case while preserving apostrophes and St.
    words = b.split()
    out = []
    for w in words:
        if re.match(r"^[a-z]+'[a-z]+$", w, re.I):
            parts = w.split("'")
            out.append(parts[0].capitalize() + "'" + parts[1].lower())
        elif w.lower() in {"of", "the", "and", "in", "on", "at", "y", "yr"} and out:
            out.append(w.lower())
        else:
            out.append(w.capitalize())
    return " ".join(out)

def normalize_trade(t):
    t = t.strip()
    if not t:
        return ""
    if t.isupper() or t.islower():
        return " ".join(w.capitalize() if w.lower() not in {"and", "of", "&"} else w.lower() for w in t.split())
    return t[0].upper() + t[1:] if len(t) > 1 else t.upper()

def main():
    # Load approved targets from audit TSV for exact matching
    comp_targets = set()
    tib_targets = set()
    with open(AUDIT_TSV, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            key = (r["year"], r["street"], r["house_number"], r["building_name"], r["surname"], r["forename"], r["trade"])
            if r["category"] == "COMPOUND_TRADE_AND_HOUSE":
                parts = [p.strip() for p in r["trade"].split(",", 1)]
                if len(parts) == 2 and not COMPOUND_EXCLUDE_RE.search(parts[1]) and not r["building_name"]:
                    comp_targets.add(key)
            elif r["category"] == "TRADE_IN_BUILDING":
                if r["building_name"].strip().lower() in EXPLICIT_TRADES_IN_BN:
                    tib_targets.add(key)

    print(f"Loaded {len(comp_targets)} COMPOUND_TRADE_AND_HOUSE targets and {len(tib_targets)} TRADE_IN_BUILDING targets.")
    print(f"Creating backup: {BACKUP_CSV}...")
    shutil.copyfile(DATA_CSV, BACKUP_CSV)

    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    comp_healed = 0
    tib_healed = 0

    for r in rows:
        yr = (r.get("year") or "").strip()
        if yr.isdigit() and int(yr) > MAX_YEAR:
            continue
        st = (r.get("street") or "").strip()
        hn = (r.get("house_number") or "").strip()
        bn = (r.get("building_name") or "").strip()
        sn = (r.get("surname") or "").strip()
        fn = (r.get("forename") or "").strip()
        tr = (r.get("trade") or "").strip()
        key = (yr, st, hn, bn, sn, fn, tr)

        if key in comp_targets:
            parts = [p.strip() for p in tr.split(",", 1)]
            r["trade"] = normalize_trade(parts[0])
            r["building_name"] = normalize_building_name(parts[1])
            comp_healed += 1
        elif key in tib_targets:
            new_tr = normalize_trade(bn)
            r["building_name"] = ""
            if not tr:
                r["trade"] = new_tr
            elif tr.lower() != new_tr.lower():
                r["trade"] = f"{new_tr}, {tr}"
            tib_healed += 1

    print(f"Healed {comp_healed} COMPOUND_TRADE_AND_HOUSE records and {tib_healed} TRADE_IN_BUILDING records.")

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

    print("\n[SUCCESS] Batch 1 strayed columns healed and site rebuilt!")

if __name__ == "__main__":
    main()
