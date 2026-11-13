#!/usr/bin/env python3
"""Normalize apostrophe-contraction trade abbreviations (e.g. M'gress -> Manageress) across all years."""
import csv
import shutil
from collections import Counter, defaultdict
from pathlib import Path

DATA_CSV = Path(__file__).resolve().parent.parent / "data.csv"
BACKUP_CSV = Path(__file__).resolve().parent.parent / "data.csv.bak_before_apostrophe_contractions"

# Lowercased exact-match map -> canonical trade
CONTRACTION_MAP = {
    "m'gress": "Manageress",
    "man'gr": "Manager",
    "mangr": "Manager",
    "managr": "Manager",
    "assistant managr": "Assistant Manager",
    "mill mangr": "Mill Manager",
    "forge mangr": "Forge Manager",
    "ins mangr": "Insurance Manager",
    "shop mangr": "Shop Manager",
    "grocer's mangr": "Grocer's Manager",
    "ironm'gr": "Ironmonger",
    "furnishing & general ironm'ger": "Furnishing & General Ironmonger",
    "account't": "Accountant",
    "account'nt": "Accountant",
    "ac'nt": "Accountant",
    "eng. d'vr": "Engine Driver",
    "engine drv'r": "Engine Driver",
    "eng. drv'r": "Engine Driver",
    "trim'r": "Trimmer",
    "trimm'r": "Trimmer",
    "trm'r": "Trimmer",
    "coal trm'r": "Coal Trimmer",
    "coal trim'r": "Coal Trimmer",
    "labour'r": "Labourer",
    "lab'er": "Labourer",
    "labr'r": "Labourer",
    "dock lab'r": "Dock Labourer",
    "dock lab'rer": "Dock Labourer",
    "farm lab'r": "Farm Labourer",
    "confect'ner": "Confectioner",
    "conf'ner": "Confectioner",
    "confection'r": "Confectioner",
    "confectio'r": "Confectioner",
    "confec'r": "Confectioner",
    "i'wkr": "Ironworker",
    "upholst'r": "Upholsterer",
    "upholster'r": "Upholsterer",
    "engin'r": "Engineer",
    "eng'eer": "Engineer",
    "eng'r": "Engineer",
    "sanitary engin'r": "Sanitary Engineer",
    "shipcarp'tr": "Ship Carpenter",
    "ship carp'tr": "Ship Carpenter",
    "shipcarpt'r": "Ship Carpenter",
    "shipwr't": "Shipwright",
    "crane dr'vr": "Crane Driver",
    "dr'vr": "Driver",
    "forem'n": "Foreman",
    "elect'n": "Electrician",
    "electric'n": "Electrician",
    "electr'cn": "Electrician",
    "carpn'tr": "Carpenter",
    "lamplig'tr": "Lamplighter",
    "purvey'rs": "Purveyors",
    "shopkeeper'r": "Shopkeeper",
    "decor'tr": "Decorator",
    "storek'pr": "Storekeeper",
    "cab't mkr": "Cabinetmaker",
    "cab'ntmkr": "Cabinetmaker",
    "cab'tmkr": "Cabinetmaker",
    "assist't": "Assistant",
    "plaster'r": "Plasterer",
    "wagon rep'r": "Wagon Repairer",
    "wagon repair'r": "Wagon Repairer",
    "wagon rep'er": "Wagon Repairer",
    "wagon ex'r": "Wagon Examiner",
    "cycle rep'r": "Cycle Repairer",
    "rail'y guard": "Railway Guard",
    "r'lway guard": "Railway Guard",
    "r'lway porter": "Railway Porter",
    "rail'y foreman": "Railway Foreman",
    "rail'y auditor": "Railway Auditor",
    "rl'wy clerk": "Railway Clerk",
    "sig'lmn": "Signalman",
    "sig'lman": "Signalman",
    "boilerm'r": "Boilermaker",
    "boiler cov'r": "Boiler Coverer",
    "garden'r": "Gardener",
    "gardn'r": "Gardener",
    "landscape gard'r": "Landscape Gardener",
    "ticket col'tr": "Ticket Collector",
    "butc'r": "Butcher",
    "berth'g mas": "Berthing Master",
    "coach trim'er": "Coach Trimmer",
    "auction'r": "Auctioneer",
    "cattle d'lr": "Cattle Dealer",
    "wardrobe d'lr": "Wardrobe Dealer",
    "soli'trs": "Solicitors",
    "solic'tr": "Solicitor",
    "photo'phr": "Photographer",
    "lithog'r": "Lithographer",
    "corn st're": "Corn Store",
    "factory h'd": "Factory Hand",
    "mould'r": "Moulder",
    "wheelw'ght": "Wheelwright",
    "com. trav'lr": "Commercial Traveller",
    "hobl'r": "Hobbler",
    "boot manuf'tr": "Boot Manufacturer",
    "boot rep'rs": "Boot Repairers",
}


def main():
    with open(DATA_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    shutil.copy2(DATA_CSV, BACKUP_CSV)
    stats = Counter()

    for r in rows:
        tr = r["trade"].strip()
        if not tr:
            continue
        low = tr.lower()
        if low in CONTRACTION_MAP:
            r["trade"] = CONTRACTION_MAP[low]
            stats["contraction_normalized"] += 1

    # Unify any trade casing twins
    by_low = defaultdict(Counter)
    for r in rows:
        t = r["trade"].strip()
        if t:
            by_low[t.lower()][t] += 1
    canon = {low: cnts.most_common(1)[0][0] for low, cnts in by_low.items() if len(cnts) > 1}
    for r in rows:
        t = r["trade"].strip()
        if t and t.lower() in canon and t != canon[t.lower()]:
            r["trade"] = canon[t.lower()]
            stats["casing_unified"] += 1

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Apostrophe contraction normalization complete:")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
